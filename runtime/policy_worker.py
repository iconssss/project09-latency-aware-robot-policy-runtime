import threading
class PolicyWorker(threading.Thread):
 def __init__(self,observations,actions,policy):
  super().__init__(name="policy-worker");self.observations,self.actions,self.policy=observations,actions,policy;self.stop_event,self.produced_chunks=threading.Event(),0
 def stop(self):self.stop_event.set()
 def run(self):
  while not self.stop_event.is_set():
   observation=self.observations.get()
   if observation is None:continue
   chunk=self.policy.infer(observation)
   if not self.stop_event.is_set():self.actions.put(chunk);self.produced_chunks+=1
