from queue import Queue,Empty
class FifoBuffer:
 def __init__(self):self.queue,self.closed,self.max_depth=Queue(),False,0
 def put(self,item):
  if not self.closed:
   self.queue.put(item);self.max_depth=max(self.max_depth,self.queue.qsize())
 def get(self,timeout=.05):
  try:return self.queue.get(timeout=timeout)
  except Empty:return None
 def get_nowait(self):
  try:return self.queue.get_nowait()
  except Empty:return None
 def close(self):self.closed=True
