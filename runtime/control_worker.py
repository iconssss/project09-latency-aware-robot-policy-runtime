import threading,time
from runtime.messages import ExecutionRecord
class ControlWorker(threading.Thread):
 def __init__(self,actions,control_hz):
  super().__init__(name="control-worker");self.actions,self.period_s=actions,1/control_hz;self.stop_event,self.records,self.tick_count=threading.Event(),[],0;self.started_timestamp=self.stopped_timestamp=0
 def stop(self):self.stop_event.set()
 @property
 def achieved_rate_hz(self):
  elapsed=self.stopped_timestamp-self.started_timestamp
  return self.tick_count/elapsed if elapsed else 0
 def run(self):
  self.started_timestamp=next_tick=time.perf_counter();chunk=None;action_index=chunk_index=0
  while not self.stop_event.is_set():
   now=time.perf_counter()
   if now<next_tick:time.sleep(next_tick-now);continue
   self.tick_count+=1
   if chunk is None or action_index>=len(chunk.actions):
    chunk=self.actions.get_nowait();action_index=0
    if chunk is not None:chunk_index+=1
   if chunk is not None:
    execution=time.perf_counter();self.records.append(ExecutionRecord(chunk.source_observation_id,chunk.source_observation_timestamp,chunk.policy_start_timestamp,chunk.policy_end_timestamp,chunk_index,action_index,chunk.actions[action_index],execution));action_index+=1
   next_tick+=self.period_s
  self.stopped_timestamp=time.perf_counter()
