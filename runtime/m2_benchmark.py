import statistics, threading, time
from policies.synthetic_policy import SyntheticPolicy
from runtime.buffers import FifoBuffer
from runtime.control_worker import ControlWorker
from runtime.messages import ExecutionRecord, Observation
from runtime.policy_worker import PolicyWorker
CONTROL_HZ=20.0
OBSERVATION_HZ=20.0
CHUNK_SIZE=4

def percentile(values,p):
 if not values:return 0.0
 ordered=sorted(values);pos=(len(ordered)-1)*p/100;lo,hi=int(pos),min(int(pos)+1,len(ordered)-1)
 return ordered[lo]+(ordered[hi]-ordered[lo])*(pos-lo)

def summarize(mode,latency_ms,records,actual_s,produced_chunks,maximum_depth,final_depth,unexecuted):
 latencies=[r.policy_latency_ms for r in records];ages=[r.action_age_ms for r in records]
 measured_rate=(produced_chunks*CHUNK_SIZE/actual_s) if actual_s else 0.0
 theoretical=None if latency_ms==0 else CHUNK_SIZE/(latency_ms/1000)
 comparison_rate=measured_rate if latency_ms==0 else theoretical
 expected='growing' if comparison_rate>CONTROL_HZ else ('under-producing' if comparison_rate<CONTROL_HZ else 'stable')
 return {'mode':mode,'configured_duration_s':5.0,'actual_runtime_s':actual_s,'configured_latency_ms':latency_ms,'policy_latency_mean_ms':statistics.mean(latencies) if latencies else 0.0,'policy_latency_p50_ms':percentile(latencies,50),'policy_latency_p95_ms':percentile(latencies,95),'executed_action_count':len(records),'achieved_control_rate_hz':len(records)/actual_s if actual_s else 0.0,'action_age_mean_ms':statistics.mean(ages) if ages else 0.0,'action_age_p50_ms':percentile(ages,50),'action_age_p95_ms':percentile(ages,95),'action_age_max_ms':max(ages) if ages else 0.0,'deadline_miss_rate':sum(a>50 for a in ages)/len(ages) if ages else 0.0,'max_action_queue_depth_chunks':maximum_depth,'final_action_queue_depth_chunks':final_depth,'unexecuted_action_count':unexecuted,'produced_chunk_count':produced_chunks,'produced_action_count':produced_chunks*CHUNK_SIZE,'measured_policy_action_rate':measured_rate,'theoretical_policy_action_rate':theoretical,'controller_action_rate':CONTROL_HZ,'rate_ratio':measured_rate/CONTROL_HZ,'expected_backlog_direction':expected}

def run_async_fifo(latency_ms,duration_s=5.0):
 started=time.perf_counter();obs,acts=FifoBuffer(),FifoBuffer();worker=PolicyWorker(obs,acts,SyntheticPolicy(latency_ms,CHUNK_SIZE));controller=ControlWorker(acts,CONTROL_HZ);count=0
 def produce():
  nonlocal count
  period=1/OBSERVATION_HZ;start=next_tick=time.perf_counter()
  while time.perf_counter()-start<duration_s:
   now=time.perf_counter()
   if now<next_tick:time.sleep(next_tick-now);continue
   obs.put(Observation(count,time.perf_counter(),float(count)));count+=1;next_tick+=period
 producer=threading.Thread(target=produce,name='observation-producer');worker.start();controller.start();producer.start();producer.join();obs.close();worker.stop();worker.join(timeout=2);acts.close();controller.stop();controller.join(timeout=2);ended=time.perf_counter()
 if worker.is_alive() or controller.is_alive():raise RuntimeError('worker shutdown timed out')
 return controller.records,summarize('ASYNC_FIFO',latency_ms,controller.records,ended-started,worker.produced_chunks,acts.max_depth,acts.queue.qsize(),worker.produced_chunks*CHUNK_SIZE-len(controller.records))

def run_sync(latency_ms,duration_s=5.0):
 policy=SyntheticPolicy(latency_ms,CHUNK_SIZE);records=[];started=time.perf_counter();chunk_index=0
 while time.perf_counter()-started<duration_s:
  obs=Observation(chunk_index,time.perf_counter(),float(chunk_index));chunk=policy.infer(obs);chunk_index+=1
  for action_index,value in enumerate(chunk.actions):
   execution=time.perf_counter();records.append(ExecutionRecord(chunk.source_observation_id,chunk.source_observation_timestamp,chunk.policy_start_timestamp,chunk.policy_end_timestamp,chunk_index,action_index,value,execution))
   if action_index<len(chunk.actions)-1:time.sleep(1/CONTROL_HZ)
 ended=time.perf_counter()
 return records,summarize('SYNC',latency_ms,records,ended-started,chunk_index,0,0,0)
