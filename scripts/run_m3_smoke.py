import json
from runtime.m3_pendulum import episode
out={}
for mode,latency in [('SYNC',0),('ASYNC_FIFO',100),('ASYNC_LATEST',100)]:
 _,out[f'{mode}_{latency}ms']=episode(mode,latency,0)
print(json.dumps(out,sort_keys=True))
