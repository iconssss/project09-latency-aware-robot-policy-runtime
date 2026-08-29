import csv,json,statistics
from pathlib import Path
from runtime.m4 import load,run
root=Path(__file__).resolve().parents[1];raw=root/'results/m4_raw';raw.mkdir(exist_ok=True);model,norm=load();out=[]
for mode in ('SYNC','ASYNC_FIFO','ASYNC_LATEST'):
 for lat in (0,25,50,100,200,400):
  ms=[];rs=[]
  for seed in range(20):
   r,m=run(mode,lat,seed,model,norm);ms.append(m);rs += [[seed]+x for x in r]
  with (raw/f'{mode.lower()}_{lat}ms.csv').open('w',newline='') as h:w=csv.writer(h);w.writerow(['seed','obs_id','obs_ts','policy_start','policy_end','execution','action_index']);w.writerows(rs)
  a={'mode':mode,'latency_ms':lat}
  for k in ms[0]:a[k]=statistics.mean(x[k] for x in ms)
  out.append(a)
with (root/'results/m4_runs.csv').open('w',newline='') as h:w=csv.DictWriter(h,fieldnames=list(out[0]));w.writeheader();w.writerows(out)
(root/'results/m4_summary.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
