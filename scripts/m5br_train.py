import json, time
from pathlib import Path
import gymnasium as gym
import numpy as np
import mujoco
from stable_baselines3 import SAC

root=Path('/root/shared-nvme/project09-latency-vla'); out=root/'results'; art=root/'artifacts'; out.mkdir(exist_ok=True); art.mkdir(exist_ok=True)
env=gym.make('Reacher-v5')
t=time.time(); model=SAC('MlpPolicy',env,device='cpu',seed=7,verbose=0)
model.learn(total_timesteps=100000); model.save(art/'m5b_reacher_sac')
ds=[]; rs=[]
for seed in range(100):
 e=gym.make('Reacher-v5'); o,_=e.reset(seed=seed); ret=0
 for _ in range(50):
  a,_=model.predict(o,deterministic=True); o,r,_,_,_=e.step(a); ret+=r
 u=e.unwrapped; fi=mujoco.mj_name2id(u.model,mujoco.mjtObj.mjOBJ_BODY,'fingertip'); ti=mujoco.mj_name2id(u.model,mujoco.mjtObj.mjOBJ_BODY,'target'); ds.append(float(np.linalg.norm(u.data.xpos[fi][:2]-u.data.xpos[ti][:2]))); rs.append(float(ret)); e.close()
x={'episodes':100,'success':float(np.mean(np.array(ds)<.1)),'mean_return':float(np.mean(rs)),'mean_final_distance':float(np.mean(ds)),'p50_final_distance':float(np.percentile(ds,50)),'p95_final_distance':float(np.percentile(ds,95)),'steps':100000,'wall_seconds':time.time()-t}
(out/'m5b_sac_eval.json').write_text(json.dumps(x,indent=2)); print(json.dumps(x))
