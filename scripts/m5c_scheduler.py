import argparse, csv, json, queue, threading, time
from pathlib import Path

import gymnasium as gym
import mujoco
import numpy as np
from stable_baselines3 import SAC

ROOT = Path('/root/shared-nvme/project09-latency-vla')
CONTROL_PERIOD = 0.05
HORIZON = 50

def pct(xs, q):
    return float(np.percentile(xs, q)) if xs else 0.0

def fingertip_distance(env):
    u = env.unwrapped
    fi = mujoco.mj_name2id(u.model, mujoco.mjtObj.mjOBJ_BODY, 'fingertip')
    ti = mujoco.mj_name2id(u.model, mujoco.mjtObj.mjOBJ_BODY, 'target')
    return float(np.linalg.norm(u.data.xpos[fi][:2] - u.data.xpos[ti][:2]))

class PolicyWorker(threading.Thread):
    def __init__(self, model, mode, latency_s):
        super().__init__(daemon=True)
        self.model, self.mode, self.latency_s = model, mode, latency_s
        self.fifo, self.out, self.lock = queue.Queue(), queue.Queue(), threading.Lock()
        self.latest_obs = self.latest_action = None
        self.stop_event = threading.Event(); self.action_id = 0
        self.drop_obs = self.replace_actions = 0; self.max_obs = self.max_action = 0

    def submit(self, obs):
        if self.mode == 'ASYNC_FIFO':
            self.fifo.put(obs); self.max_obs = max(self.max_obs, self.fifo.qsize())
        else:
            with self.lock:
                if self.latest_obs is not None: self.drop_obs += 1
                self.latest_obs = obs; self.max_obs = max(self.max_obs, 1)

    def _take_obs(self):
        if self.mode == 'ASYNC_FIFO':
            try: return self.fifo.get(timeout=.01)
            except queue.Empty: return None
        with self.lock:
            x, self.latest_obs = self.latest_obs, None
            return x

    def run(self):
        while not self.stop_event.is_set():
            item = self._take_obs()
            if item is None:
                time.sleep(.001); continue
            oid, ots, obs = item; start = time.perf_counter(); time.sleep(self.latency_s)
            action, _ = self.model.predict(obs, deterministic=True); end = time.perf_counter()
            out = (self.action_id, oid, ots, start, end, np.asarray(action, dtype=np.float32))
            self.action_id += 1
            if self.mode == 'ASYNC_FIFO':
                self.out.put(out); self.max_action = max(self.max_action, self.out.qsize())
            else:
                with self.lock:
                    if self.latest_action is not None: self.replace_actions += 1
                    self.latest_action = out; self.max_action = max(self.max_action, 1)

    def take(self):
        if self.mode == 'ASYNC_FIFO':
            try: return self.out.get_nowait()
            except queue.Empty: return None
        with self.lock:
            x, self.latest_action = self.latest_action, None
            return x

    def finish(self):
        self.stop_event.set(); self.join(timeout=1)
        if self.mode == 'ASYNC_FIFO': return self.fifo.qsize(), self.out.qsize()
        with self.lock: return int(self.latest_obs is not None), int(self.latest_action is not None)

def run_episode(model, mode, latency_ms, seed):
    env = gym.make('Reacher-v5'); obs, _ = env.reset(seed=seed)
    rows, worker, ret = [], None, 0.0; start = time.perf_counter(); next_tick = start
    if mode != 'SYNC': worker = PolicyWorker(model, mode, latency_ms / 1000); worker.start()
    for step in range(HORIZON):
        now = time.perf_counter(); oid, ots = step, now
        if mode == 'SYNC':
            istart = time.perf_counter(); time.sleep(latency_ms / 1000)
            action, _ = model.predict(obs, deterministic=True); iend = time.perf_counter()
            item = (step, oid, ots, istart, iend, np.asarray(action, dtype=np.float32))
        else:
            worker.submit((oid, ots, obs.copy())); item = worker.take()
        execution = time.perf_counter()
        if item is None:
            aid = src_oid = -1; src_ts = istart = iend = None; action = np.zeros(env.action_space.shape, dtype=np.float32)
        else:
            aid, src_oid, src_ts, istart, iend, action = item
        obs, reward, term, trunc, _ = env.step(action); ret += float(reward)
        rows.append({'seed':seed, 'mode':mode, 'latency_ms':latency_ms, 'step':step,
            'observation_id':oid, 'observation_timestamp':ots, 'source_observation_id':src_oid,
            'source_observation_timestamp':src_ts, 'inference_start':istart, 'inference_end':iend,
            'action_id':aid, 'action_execution_timestamp':execution})
        if term or trunc: break
        next_tick += CONTROL_PERIOD; time.sleep(max(0.0, next_tick - time.perf_counter()))
    wall = time.perf_counter() - start; dist = fingertip_distance(env); env.close()
    valid = [r for r in rows if r['action_id'] >= 0]
    for r in valid:
        r['observation_wait_ms'] = (r['inference_start'] - r['source_observation_timestamp']) * 1000
        r['policy_latency_ms'] = (r['inference_end'] - r['inference_start']) * 1000
        r['action_wait_ms'] = (r['action_execution_timestamp'] - r['inference_end']) * 1000
        r['action_age_ms'] = (r['action_execution_timestamp'] - r['source_observation_timestamp']) * 1000
        r['decomposition_error_ms'] = abs(r['action_age_ms'] - r['observation_wait_ms'] - r['policy_latency_ms'] - r['action_wait_ms'])
    if worker:
        final_obs, final_action = worker.finish(); meta = dict(dropped_observations=worker.drop_obs, replaced_actions=worker.replace_actions, max_observation_queue_depth=worker.max_obs, max_action_queue_depth=worker.max_action, final_observation_queue_depth=final_obs, final_action_queue_depth=final_action)
    else: meta = dict(dropped_observations=0, replaced_actions=0, max_observation_queue_depth=0, max_action_queue_depth=0, final_observation_queue_depth=0, final_action_queue_depth=0)
    summary = dict(mode=mode, latency_ms=latency_ms, seed=seed, steps=len(rows), return_=ret, final_distance=dist, success=dist < .10, achieved_control_rate_hz=len(rows)/wall, valid_actions=len(valid), **meta)
    for key in ('observation_wait_ms','policy_latency_ms','action_wait_ms','action_age_ms','decomposition_error_ms'):
        values = [r[key] for r in valid]; summary[key + '_p95'] = pct(values,95); summary[key + '_max'] = max(values) if values else 0.0
    return rows, summary

def write_rows(path, rows):
    fields = ['seed','mode','latency_ms','step','observation_id','observation_timestamp','source_observation_id','source_observation_timestamp','inference_start','inference_end','action_id','action_execution_timestamp','observation_wait_ms','policy_latency_ms','action_wait_ms','action_age_ms','decomposition_error_ms']
    with path.open('w', newline='') as f:
        w = csv.DictWriter(f, fieldnames=fields); w.writeheader(); w.writerows(rows)

def aggregate(rows):
    out=[]
    for mode in ('SYNC','ASYNC_FIFO','ASYNC_LATEST'):
        for lat in (0,100,400):
            x=[r for r in rows if r['mode']==mode and r['latency_ms']==lat]
            d={k:float(np.mean([r[k] for r in x])) for k in ('success','final_distance','achieved_control_rate_hz','max_observation_queue_depth','max_action_queue_depth')}
            d.update(mode=mode, latency_ms=lat, episodes=len(x), final_distance_p95=pct([r['final_distance'] for r in x],95), action_age_p95_ms=pct([r['action_age_ms_p95'] for r in x],95), observation_wait_p95_ms=pct([r['observation_wait_ms_p95'] for r in x],95), decomposition_error_max_ms=max(r['decomposition_error_ms_max'] for r in x))
            out.append(d)
    return out

def figures(agg, directory):
    directory.mkdir(parents=True, exist_ok=True)
    for metric, name, ylabel in [('success','m5c_success_vs_latency.svg','Success rate'),('action_age_p95_ms','m5c_action_age_p95.svg','Action age p95 (ms)'),('final_distance','m5c_final_distance.svg','Final distance')]:
        w,h,left,right,top,bottom=720,440,80,30,35,65; vals=[r[metric] for r in agg]; lo,hi=min(0.,min(vals)),max(vals)
        if hi <= lo: hi=lo+1.
        def xy(lat,val): return left+(w-left-right)*lat/400, top+(h-top-bottom)*(1-(val-lo)/(hi-lo))
        colors={'SYNC':'#2563eb','ASYNC_FIFO':'#dc2626','ASYNC_LATEST':'#16a34a'}; parts=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}"><style>text{{font:14px sans-serif}}.s{{stroke:#334155;stroke-width:1}}</style><text x="{left}" y="20">{ylabel}</text><line class="s" x1="{left}" y1="{top}" x2="{left}" y2="{h-bottom}"/><line class="s" x1="{left}" y1="{h-bottom}" x2="{w-right}" y2="{h-bottom}"/>']
        for lat in (0,100,400):
            x,_=xy(lat,lo); parts.append(f'<text x="{x-12:.1f}" y="{h-bottom+24}">{lat}</text>')
        for mode in ('SYNC','ASYNC_FIFO','ASYNC_LATEST'):
            x=sorted((r for r in agg if r['mode']==mode),key=lambda r:r['latency_ms']); points=' '.join(f'{xy(r["latency_ms"],r[metric])[0]:.1f},{xy(r["latency_ms"],r[metric])[1]:.1f}' for r in x); parts.append(f'<polyline fill="none" stroke="{colors[mode]}" stroke-width="2" points="{points}"/><text fill="{colors[mode]}" x="{left+220*list(colors).index(mode)}" y="{h-15}">{mode}</text>')
        (directory/name).write_text(''.join(parts)+'</svg>')

def main():
    p=argparse.ArgumentParser(); p.add_argument('--smoke', action='store_true'); p.add_argument('--mode'); p.add_argument('--latency', type=int); p.add_argument('--seed', type=int, default=0); p.add_argument('--seeds', type=int, default=20); a=p.parse_args()
    model=SAC.load(ROOT/'artifacts/m5b_reacher_sac.zip', device='cpu')
    rawdir=ROOT/'results'/('m5c_smoke' if a.smoke else 'm5c_raw'); rawdir.mkdir(parents=True, exist_ok=True)
    cases=[(a.mode,a.latency,a.seed)] if a.smoke else [(m,l,s) for m in ('SYNC','ASYNC_FIFO','ASYNC_LATEST') for l in (0,100,400) for s in range(a.seeds)]
    summaries=[]
    for mode,lat,seed in cases:
        rows,summary=run_episode(model,mode,lat,seed); write_rows(rawdir/f'{mode.lower()}_{lat}ms_seed{seed:02d}.csv',rows); summaries.append(summary); print(json.dumps(summary), flush=True)
        if summary['decomposition_error_ms_max'] > .1: raise RuntimeError('provenance decomposition failed')
    if a.smoke: return
    agg=aggregate(summaries); results=ROOT/'results'
    with (results/'m5c_scheduler_aggregate.csv').open('w',newline='') as f: w=csv.DictWriter(f,fieldnames=agg[0].keys()); w.writeheader(); w.writerows(agg)
    payload={'controller':{'mujoco_timestep_s':.01,'frame_skip':2,'effective_control_dt_s':.02,'scheduler_rate_hz':20,'horizon_steps':50},'policy':{'checkpoint':'artifacts/m5b_reacher_sac.zip','deterministic':True,'retrained':False},'episodes':summaries,'aggregate':agg}
    (results/'m5c_scheduler_summary.json').write_text(json.dumps(payload,indent=2))
    figures(agg,results/'figures')
if __name__ == '__main__': main()
