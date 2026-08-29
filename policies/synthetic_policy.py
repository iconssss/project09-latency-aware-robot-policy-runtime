import time
from runtime.messages import ActionChunk
class SyntheticPolicy:
 def __init__(self,inference_latency_ms,chunk_size):self.inference_latency_s,self.chunk_size=inference_latency_ms/1000,chunk_size
 def infer(self,observation):
  start=time.perf_counter();time.sleep(self.inference_latency_s);end=time.perf_counter()
  return ActionChunk(observation.observation_id,observation.produced_timestamp,start,end,tuple(observation.payload*1000+i for i in range(self.chunk_size)))
