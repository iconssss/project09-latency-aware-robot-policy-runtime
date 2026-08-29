import csv,json,statistics
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from runtime.m3_pendulum import episode,KP,KD
root=Path(__file__).resolve().parents[1];raw=root/'results/m3_raw';raw.mkdir(exist_ok=True);fig=root/'figures';fig.mkdir(exist_ok=True)
allrows=[];aggregate=[]
for mode in ('SYNC','ASYNC_FIFO','ASYNC_LATEST'):
 for latency in (0,50,100,200,400):
  metrics=[];records=[]
  for seed in range(10):
   rows,m=episode(mode,latency,seed);metrics.append(m);records+=rows
  fields=list(records[0]);p=raw/f'{mode.lower()}_{latency}ms.csv'
  with p.open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(records)
  a={'mode':mode,'latency_ms':latency,'episodes':10}
  for k in metrics[0]:
   a[k]=statistics.mean(x[k] for x in metrics)
  aggregate.append(a)
with (root/'results/m3_runs.csv').open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=list(aggregate[0]));w.writeheader();w.writerows(aggregate)
(root/'results/m3_summary.json').write_text(json.dumps({'controller':{'Kp':KP,'Kd':KD,'chunk_size':4,'period_s':.05,'success_proxy':'final 20% mean abs(theta)<0.2 rad'},'runs':aggregate},indent=2)+'\n')
def s(mode,key):return [next(x[key] for x in aggregate if x['mode']==mode and x['latency_ms']==l) for l in (0,50,100,200,400)]
for key,name,ylabel,modes in [('episode_return','m3_return_vs_latency.png','mean return',('SYNC','ASYNC_FIFO','ASYNC_LATEST')),('upright_fraction','m3_upright_vs_latency.png','upright fraction',('SYNC','ASYNC_FIFO','ASYNC_LATEST')),('action_age_p95_ms','m3_p95_action_age_vs_latency.png','p95 age ms',('ASYNC_FIFO','ASYNC_LATEST')),('achieved_control_rate_hz','m3_control_rate_vs_latency.png','control rate Hz',('SYNC','ASYNC_FIFO','ASYNC_LATEST'))]:
 plt.figure()
 for mode in modes:plt.plot((0,50,100,200,400),s(mode,key),'o-',label=mode)
 plt.xlabel('inference latency ms');plt.ylabel(ylabel);plt.legend();plt.tight_layout();plt.savefig(fig/name);plt.close()
print(json.dumps(aggregate,sort_keys=True))
