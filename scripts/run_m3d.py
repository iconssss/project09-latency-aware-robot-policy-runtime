import json,time
from pathlib import Path
import numpy as np,torch
from runtime.m3d import expert_eval,generate,train,learned_eval,H,K
root=Path(__file__).resolve().parents[1];res=root/'results';art=root/'artifacts';started=time.perf_counter()
expert=expert_eval();es={'episodes':100,'success_rate':float(np.mean([x['success'] for x in expert])),'mean_final_error':float(np.mean([x['final_error'] for x in expert]))};(res/'m3d_expert_summary.json').write_text(json.dumps(es,indent=2))
os,ac,ln=generate();np.savez_compressed(res/'m3d_dataset.npz',observations=os,actions=ac,lengths=ln)
model,norm,best=train(os,ac,ln);torch.save({'model':model.state_dict(),'norm':norm,'H':H,'k':K},art/'m3d_chunk_bc.pt')
ev=learned_eval(model,norm);summary={'architecture':'9-128-128-48','H':H,'k':K,'train_time_s':time.perf_counter()-started,'best_val_loss':best,'episodes':100,'success_rate':float(np.mean([x['success'] for x in ev])),'mean_final_error':float(np.mean([x['final_error'] for x in ev])),'mean_steps_to_success':float(np.mean([x['steps'] for x in ev])),'mean_return':float(np.mean([x['return'] for x in ev]))};(res/'m3d_bc_summary.json').write_text(json.dumps(summary,indent=2));print(json.dumps({'expert':es,'bc':summary},sort_keys=True))
