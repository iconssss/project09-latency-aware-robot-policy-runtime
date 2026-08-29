import time,queue,threading,statistics,math,numpy as np,torch
from envs.reaching_proxy import ReachingEnv
from policies.chunk_bc import ChunkBC
P=.05;H=16;K=4
def pct(x,p):
 if not x:return 0.
 x=sorted(x);q=(len(x)-1)*p/100;i=int(q);j=min(i+1,len(x)-1);return x[i]+(x[j]-x[i])*(q-i)
class Worker(threading.Thread):
 def __init__(self,mode,lat,model,norm):
  super().__init__();self.mode,self.lat,self.model,self.norm=mode,lat/1000,model,norm;self.q=queue.Queue();self.lock=threading.Lock();self.latest_obs=None;self.latest_chunk=None;self.ix=0;self.stop=threading.Event();self.prod=self.cons=self.drop_obs=self.replace=self.drop_actions=0;self.maxo=self.maxa=0
 def submit(self,item):
  if self.mode=='ASYNC_LATEST':
   with self.lock:
    if self.latest_obs is not None:self.drop_obs+=1
    self.latest_obs=item;self.maxo=max(self.maxo,1)
  else:self.q.put(item);self.maxo=max(self.maxo,self.q.qsize())
 def run(self):
  while not self.stop.is_set():
   if self.mode=='ASYNC_LATEST':
    with self.lock:o=self.latest_obs;self.latest_obs=None
    if o is None:time.sleep(.001);continue
   else:
    try:o=self.q.get(timeout=.02)
    except queue.Empty:continue
   oid,ts,obs=o;st=time.perf_counter();time.sleep(self.lat)
   with torch.no_grad():a=(self.model(torch.tensor((obs-self.norm['obs_mean'])/self.norm['obs_std']).float().unsqueeze(0))[0].numpy()*self.norm['act_std']+self.norm['act_mean']).clip(-4,4)
   c=(oid,ts,st,time.perf_counter(),a);self.prod+=1;self.cons+=1
   if self.mode=='ASYNC_LATEST':
    with self.lock:
     if self.latest_chunk is not None:self.replace+=1;self.drop_actions+=H-self.ix
     self.latest_chunk=c;self.ix=0;self.maxa=max(self.maxa,1)
   else:self.out.put(c);self.maxa=max(self.maxa,self.out.qsize())
 def start2(self):
  self.out=queue.Queue();self.start()
 def take(self):
  if self.mode=='ASYNC_LATEST':
   with self.lock:
    if self.latest_chunk is None:return None,None
    c,i=self.latest_chunk,self.ix;self.ix+=1
    if self.ix==H:self.latest_chunk=None;self.ix=0
    return c,i
  if not hasattr(self,'cur'):self.cur=None;self.ci=0
  if self.cur is None or self.ci==H:
   try:self.cur=self.out.get_nowait();self.ci=0
   except queue.Empty:return None,None
  i=self.ci;self.ci+=1;return self.cur,i
 def finish(self):
  self.stop.set();self.join(1)
  if self.mode=='ASYNC_LATEST':
   with self.lock:return int(self.latest_obs is not None),int(self.latest_chunk is not None)
  return self.q.qsize(),self.out.qsize()
def load():
 x=torch.load('artifacts/m3d_chunk_bc.pt',map_location='cpu',weights_only=False);m=ChunkBC();m.load_state_dict(x['model']);m.eval();return m,x['norm']
def run(mode,lat,seed,model,norm):
 e=ReachingEnv();o=e.reset(seed);rows=[];start=time.perf_counter();nextt=start
 if mode=='SYNC':
  steps=0;produced=0
  while steps<100:
   oid=steps;ts=time.perf_counter();st=ts;time.sleep(lat/1000)
   with torch.no_grad():a=(model(torch.tensor((o-norm['obs_mean'])/norm['obs_std']).float().unsqueeze(0))[0].numpy()*norm['act_std']+norm['act_mean']).clip(-4,4)
   end=time.perf_counter();produced+=1
   for i,u in enumerate(a[:K]):
    ex=time.perf_counter();o,r,s,d,info=e.step(u);rows.append([oid,ts,st,end,ex,i]);steps+=1;nextt+=P;time.sleep(max(0,nextt-time.perf_counter()))
    if s or d:break
   if s or d:break
  meta={'produced_observations':produced,'consumed_observations':produced,'dropped_observations':0,'produced_chunks':produced,'replaced_chunks':0,'dropped_actions':0,'max_observation_queue_depth':0,'max_action_queue_depth':0,'final_observation_queue_depth':0,'final_action_queue_depth':0}
 else:
  w=Worker(mode,lat,model,norm);w.start2();s=False
  for step in range(100):
   ts=time.perf_counter();w.submit((step,ts,o.copy()));c,i=w.take();ex=time.perf_counter()
   if c is None:u=np.zeros(3);rows.append([-1,ts,ex,ex,ex,-1])
   else:u=c[4][i];rows.append([c[0],c[1],c[2],c[3],ex,i])
   o,r,s,d,info=e.step(u);nextt+=P;time.sleep(max(0,nextt-time.perf_counter()))
   if s or d:break
  fo,fa=w.finish();meta={'produced_observations':step+1,'consumed_observations':w.cons,'dropped_observations':w.drop_obs,'produced_chunks':w.prod,'replaced_chunks':w.replace,'dropped_actions':w.drop_actions,'max_observation_queue_depth':w.maxo,'max_action_queue_depth':w.maxa,'final_observation_queue_depth':fo,'final_action_queue_depth':fa}
 valid=[x for x in rows if x[0]>=0];ow=[(x[2]-x[1])*1000 for x in valid];pa=[(x[4]-x[3])*1000 for x in valid];aa=[(x[4]-x[1])*1000 for x in valid]
 out={'success':bool(s),'steps':len(rows),'final_position_error':info['error'],'final_velocity_norm':float(np.linalg.norm(e.v)),'mean_position_error':-r,'max_position_error':0.,'achieved_control_rate_hz':len(rows)/(time.perf_counter()-start),'policy_latency_p95_ms':pct([(x[3]-x[2])*1000 for x in valid],95),'observation_wait_age_p95_ms':pct(ow,95),'plan_age_p95_ms':pct(pa,95),'action_age_p95_ms':pct(aa,95),'action_age_max_ms':max(aa) if aa else 0,'decomposition_error_ms':max([abs(a-(b+(d-c)*1000+e)) for a,b,c,d,e in zip(aa,ow,[x[2] for x in valid],[x[3] for x in valid],pa)] or [0])};out.update(meta);return rows,out
