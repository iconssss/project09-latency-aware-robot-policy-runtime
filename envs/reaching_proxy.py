import numpy as np
class ReachingEnv:
 dt=.05; damping=.90; action_limit=4.; velocity_limit=2.; horizon=100
 def reset(self,seed):
  r=np.random.default_rng(seed);self.p=r.uniform(-1,1,3).astype('f');self.v=r.uniform(-.1,.1,3).astype('f');self.g=r.uniform(-1,1,3).astype('f');self.t=0;return self.obs()
 def obs(self):return np.r_[self.p,self.v,self.g].astype('f')
 def step(self,a):
  a=np.clip(np.asarray(a,'f'),-self.action_limit,self.action_limit);self.v=np.clip(self.damping*self.v+a*self.dt,-self.velocity_limit,self.velocity_limit);self.p=np.clip(self.p+self.v*self.dt,-1,1);self.t+=1;err=float(np.linalg.norm(self.g-self.p));success=err<.05 and np.linalg.norm(self.v)<.05;return self.obs(),-err,success,self.t>=self.horizon,{'error':err}
