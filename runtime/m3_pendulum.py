import math, queue, threading, time, statistics
import numpy as np
import gymnasium as gym
PERIOD=0.05; H=4; KP=6.0; KD=2.0; STEPS=200
def wrap(theta): return (theta+math.pi)%(2*math.pi)-math.pi
def control(obs):
 theta=math.atan2(float(obs[1]),float(obs[0])); return float(np.clip(-KP*wrap(theta)-KD*float(obs[2]),-2,2))
class Chunk:
 def __init__(self,oid,ts,start,end,u): self.oid,self.ts,self.start,self.end,self.actions=oid,ts,start,end,[u]*H
class Worker(threading.Thread):
 def __init__(self,latency,latest):
  super().__init__();self.latency=latency/1000;self.latest=latest;self.obs=queue.Queue();self.fifo=queue.Queue();self.lock=threading.Lock();self.pending=None;self.index=0;self.stop_event=threading.Event();self.produced=0;self.replaced=0;self.dropped=0;self.max_depth=0
 def submit(self,oid,ts,obs): self.obs.put((oid,ts,obs.copy()))
 def run(self):
  while not self.stop_event.is_set():
   try: oid,ts,obs=self.obs.get(timeout=.02)
   except queue.Empty: continue
   start=time.perf_counter();time.sleep(self.latency);chunk=Chunk(oid,ts,start,time.perf_counter(),control(obs));self.produced+=1
   if self.latest:
    with self.lock:
     if self.pending is not None:
      self.replaced+=1;self.dropped+=H-self.index
     self.pending=chunk;self.index=0;self.max_depth=max(self.max_depth,1)
   else:
    self.fifo.put(chunk);self.max_depth=max(self.max_depth,self.fifo.qsize())
 def take(self):
  if self.latest:
   with self.lock:
    if self.pending is None:return None,None
    c,i=self.pending,self.index;self.index+=1
    if self.index==H:self.pending=None;self.index=0
    return c,i
  if not hasattr(self,'current'):self.current=None;self.current_i=0
  if self.current is None or self.current_i==H:
   try:self.current=self.fifo.get_nowait();self.current_i=0
   except queue.Empty:return None,None
  i=self.current_i;self.current_i+=1;return self.current,i
 def finish(self):
  self.stop_event.set();self.join(timeout=1)
  if self.latest:
   with self.lock:return 1 if self.pending else 0
  return self.fifo.qsize()
def episode(mode,latency,seed):
 env=gym.make('Pendulum-v1');obs,_=env.reset(seed=seed);ret=0;rows=[];angles=[];maxvel=0;started=time.perf_counter();next_tick=started
 if mode=='SYNC':
  oid=0;steps=0
  while steps<STEPS:
   ts=time.perf_counter();start=ts;time.sleep(latency/1000);end=time.perf_counter();u=control(obs);c=Chunk(oid,ts,start,end,u);oid+=1
   for i,a in enumerate(c.actions):
    if steps>=STEPS:break
    execution=time.perf_counter();obs,r,term,trunc,_=env.step(np.array([a],np.float32));ret+=r;theta=abs(wrap(math.atan2(obs[1],obs[0])));angles.append(theta);maxvel=max(maxvel,abs(float(obs[2])));rows.append({'seed':seed,'step':steps,'source_observation_id':c.oid,'source_observation_timestamp':c.ts,'execution_timestamp':execution,'policy_latency_ms':(c.end-c.start)*1000,'action_age_ms':(execution-c.ts)*1000,'action':a});steps+=1;next_tick+=PERIOD;time.sleep(max(0,next_tick-time.perf_counter()))
  meta={'produced':oid,'replaced':0,'dropped':0,'max_depth':0,'final_depth':0}
 else:
  w=Worker(latency,mode=='ASYNC_LATEST');w.start();steps=0
  while steps<STEPS:
   now=time.perf_counter();w.submit(steps,now,obs);c,i=w.take()
   if c is None:a=0.;row={'source_observation_id':-1,'source_observation_timestamp':now,'policy_latency_ms':0.,'action_age_ms':0.}
   else:a=c.actions[i];execution=time.perf_counter();row={'source_observation_id':c.oid,'source_observation_timestamp':c.ts,'policy_latency_ms':(c.end-c.start)*1000,'action_age_ms':(execution-c.ts)*1000}
   execution=time.perf_counter();obs,r,term,trunc,_=env.step(np.array([a],np.float32));ret+=r;theta=abs(wrap(math.atan2(obs[1],obs[0])));angles.append(theta);maxvel=max(maxvel,abs(float(obs[2])));row.update({'seed':seed,'step':steps,'execution_timestamp':execution,'action':a});rows.append(row);steps+=1;next_tick+=PERIOD;time.sleep(max(0,next_tick-time.perf_counter()))
  final=w.finish();meta={'produced':w.produced,'replaced':w.replaced,'dropped':w.dropped,'max_depth':w.max_depth,'final_depth':final}
 elapsed=time.perf_counter()-started;env.close();valid=[r for r in rows if r['source_observation_id']>=0];ages=[r['action_age_ms'] for r in valid];lats=[r['policy_latency_ms'] for r in valid];tail=angles[-40:]
 def pct(x,p):
  if not x:return 0.
  x=sorted(x);z=(len(x)-1)*p/100;lo=int(z);hi=min(lo+1,len(x)-1);return x[lo]+(x[hi]-x[lo])*(z-lo)
 m={'episode_return':ret,'mean_abs_angle_error':statistics.mean(angles),'final_abs_angle_error':angles[-1],'upright_fraction':sum(x<.2 for x in angles)/len(angles),'max_abs_angular_velocity':maxvel,'success':sum(tail)/len(tail)<.2,'achieved_control_rate_hz':STEPS/elapsed,'action_age_mean_ms':statistics.mean(ages) if ages else 0,'action_age_p50_ms':pct(ages,50),'action_age_p95_ms':pct(ages,95),'action_age_max_ms':max(ages) if ages else 0,'policy_latency_mean_ms':statistics.mean(lats) if lats else 0,'executed_policy_actions':len(valid)};m.update(meta);return rows,m
