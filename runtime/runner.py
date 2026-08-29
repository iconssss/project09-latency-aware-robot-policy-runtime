import statistics,threading,time
from policies.synthetic_policy import SyntheticPolicy
from runtime.buffers import FifoBuffer
from runtime.control_worker import ControlWorker
from runtime.messages import Observation
from runtime.policy_worker import PolicyWorker
def percentile(values,p):
 if not values:return 0
 ordered=sorted(values);position=(len(ordered)-1)*p/100;lo,hi=int(position),min(int(position)+1,len(ordered)-1)
 return ordered[lo]+(ordered[hi]-ordered[lo])*(position-lo)
def run_synthetic_runtime(duration_s,observation_hz,control_hz,inference_latency_ms,chunk_size):
 run_start=time.perf_counter();observations,actions=FifoBuffer(),FifoBuffer();policy=PolicyWorker(observations,actions,SyntheticPolicy(inference_latency_ms,chunk_size));controller=ControlWorker(actions,control_hz);produced_count=0;timing={}
 def produce():
  nonlocal produced_count
  period=1/observation_hz;start=next_tick=time.perf_counter();timing['production_start_timestamp']=start
  while time.perf_counter()-start<duration_s:
   now=time.perf_counter()
   if now<next_tick:time.sleep(next_tick-now);continue
   observations.put(Observation(produced_count,time.perf_counter(),float(produced_count)));produced_count+=1;next_tick+=period
  timing['production_end_timestamp']=time.perf_counter()
 producer=threading.Thread(target=produce,name='observation-producer');policy.start();controller.start();producer.start();producer.join();observations.close();policy.stop();policy.join(timeout=2);actions.close();controller.stop();controller.join(timeout=2);run_end=time.perf_counter()
 if policy.is_alive() or controller.is_alive():raise RuntimeError('worker shutdown timed out')
 latencies=[r.policy_latency_ms for r in controller.records];ages=[r.action_age_ms for r in controller.records]
 return controller.records,{'duration_s':duration_s,'actual_runtime_s':run_end-run_start,'production_duration_s':timing['production_end_timestamp']-timing['production_start_timestamp'],'shutdown_duration_s':run_end-timing['production_end_timestamp'],'max_action_queue_depth_chunks':actions.max_depth,'observation_count':produced_count,'produced_chunk_count':policy.produced_chunks,'executed_action_count':len(controller.records),'mean_policy_latency_ms':statistics.mean(latencies) if latencies else 0,'p50_policy_latency_ms':percentile(latencies,50),'p95_policy_latency_ms':percentile(latencies,95),'mean_action_age_ms':statistics.mean(ages) if ages else 0,'p50_action_age_ms':percentile(ages,50),'p95_action_age_ms':percentile(ages,95),'achieved_controller_rate_hz':controller.achieved_rate_hz}
