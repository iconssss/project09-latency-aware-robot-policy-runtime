import csv,json
from pathlib import Path
from runtime.runner import run_synthetic_runtime
root=Path(__file__).resolve().parents[1];records,summary=run_synthetic_runtime(10,20,20,100,4)
with (root/"results/m1_async_smoke.csv").open("w",newline="") as handle:
 names=["source_observation_id","source_observation_timestamp","policy_start_timestamp","policy_end_timestamp","action_chunk_index","action_index_in_chunk","action_value","execution_timestamp","policy_latency_ms","action_age_ms"];writer=csv.DictWriter(handle,fieldnames=names);writer.writeheader()
 for record in records:
  row=record.__dict__.copy();row["policy_latency_ms"]=record.policy_latency_ms;row["action_age_ms"]=record.action_age_ms;writer.writerow(row)
(root/"results/m1_async_smoke_summary.json").write_text(json.dumps(summary,indent=2)+"\n");print(json.dumps(summary,sort_keys=True))
