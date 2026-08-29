import csv,json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from runtime.m2_benchmark import run_async_fifo,run_sync
root=Path(__file__).resolve().parents[1];raw_dir=root/'results/m2_raw';fig_dir=root/'figures';raw_dir.mkdir(exist_ok=True);fig_dir.mkdir(exist_ok=True)
latencies=[0,25,50,100,200,400];all_summaries=[]
raw_fields=['source_observation_id','source_observation_timestamp','policy_start_timestamp','policy_end_timestamp','action_chunk_index','action_index_in_chunk','action_value','execution_timestamp','policy_latency_ms','action_age_ms']
def save_raw(mode,latency,records):
 with (raw_dir/f'{mode.lower()}_{latency}ms.csv').open('w',newline='') as h:
  w=csv.DictWriter(h,fieldnames=raw_fields);w.writeheader()
  for r in records:
   row=r.__dict__.copy();row['policy_latency_ms']=r.policy_latency_ms;row['action_age_ms']=r.action_age_ms;w.writerow(row)
for latency in latencies:
 for mode,runner in [('SYNC',run_sync),('ASYNC_FIFO',run_async_fifo)]:
  records,summary=runner(latency);save_raw(mode,latency,records);all_summaries.append(summary)
fields=list(all_summaries[0])
with (root/'results/m2_runs.csv').open('w',newline='') as h:
 w=csv.DictWriter(h,fieldnames=fields);w.writeheader();w.writerows(all_summaries)
(root/'results/m2_summary.json').write_text(json.dumps(all_summaries,indent=2)+'\n')
def series(mode,key):return [next(r[key] for r in all_summaries if r['mode']==mode and r['configured_latency_ms']==x) for x in latencies]
plt.figure();plt.plot(latencies,series('SYNC','achieved_control_rate_hz'),'o-',label='SYNC');plt.plot(latencies,series('ASYNC_FIFO','achieved_control_rate_hz'),'o-',label='ASYNC_FIFO');plt.xlabel('Inference latency (ms)');plt.ylabel('Achieved control rate (Hz)');plt.legend();plt.tight_layout();plt.savefig(fig_dir/'m2_control_rate_vs_latency.png');plt.close()
plt.figure();plt.plot(latencies,series('SYNC','action_age_p95_ms'),'o-',label='SYNC');plt.plot(latencies,series('ASYNC_FIFO','action_age_p95_ms'),'o-',label='ASYNC_FIFO');plt.xlabel('Inference latency (ms)');plt.ylabel('p95 action age (ms)');plt.legend();plt.tight_layout();plt.savefig(fig_dir/'m2_p95_action_age_vs_latency.png');plt.close()
plt.figure();plt.plot(latencies,series('ASYNC_FIFO','max_action_queue_depth_chunks'),'o-',label='max');plt.plot(latencies,series('ASYNC_FIFO','final_action_queue_depth_chunks'),'o-',label='final');plt.xlabel('Inference latency (ms)');plt.ylabel('Action queue depth (chunks)');plt.legend();plt.tight_layout();plt.savefig(fig_dir/'m2_queue_depth_vs_latency.png');plt.close()
print(json.dumps(all_summaries,sort_keys=True))
