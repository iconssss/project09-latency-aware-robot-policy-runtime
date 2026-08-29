import time, numpy as np, torch
from envs.reaching_proxy import ReachingEnv
from policies.reaching_expert import action
from policies.chunk_bc import ChunkBC
H=16;K=4
def rollout(policy,seed):
 e=ReachingEnv();o=e.reset(seed);obs=[];acts=[];ret=0
 while True:
  a=policy(o);obs.append(o);acts.append(a);o,r,s,d,info=e.step(a);ret+=r
  if s or d:return np.array(obs),np.array(acts),{'success':s,'final_error':info['error'],'steps':e.t,'return':ret}
def expert_eval(n=100):return [rollout(action,s)[2] for s in range(n)]
def generate(n=500):
 os=np.zeros((n,100,9),'f');ac=np.zeros((n,100,3),'f');ln=np.zeros(n,'i')
 for i in range(n):
  o,a,_=rollout(action,i);ln[i]=len(o);os[i,:len(o)]=o;ac[i,:len(a)]=a
 return os,ac,ln
def samples(os,ac,ln,ids):
 x=[];y=[];m=[]
 for i in ids:
  for t in range(ln[i]):
   end=min(t+H,ln[i]);z=np.zeros((H,3),'f');mask=np.zeros(H,'f');z[:end-t]=ac[i,t:end];mask[:end-t]=1;x.append(os[i,t]);y.append(z);m.append(mask)
 return np.array(x),np.array(y),np.array(m)
def train(os,ac,ln):
 rng=np.random.default_rng(0);ids=rng.permutation(len(ln));tr,va=ids[:400],ids[400:];x,y,m=samples(os,ac,ln,tr);vx,vy,vm=samples(os,ac,ln,va)
 mean,std=x.mean(0),x.std(0)+1e-6;amean,astd=y[m.astype(bool)].mean(0),y[m.astype(bool)].std(0)+1e-6
 dev='cuda:0' if torch.cuda.is_available() else 'cpu';model=ChunkBC().to(dev);opt=torch.optim.Adam(model.parameters(),lr=1e-3);xt=torch.tensor((x-mean)/std);yt=torch.tensor((y-amean)/astd);mt=torch.tensor(m)
 best=1e9
 for epoch in range(80):
  for j in torch.randperm(len(x)).split(512):
   p=model(xt[j].to(dev));loss=(((p-yt[j].to(dev))**2)*mt[j].to(dev).unsqueeze(-1)).sum()/(mt[j].sum()*3);opt.zero_grad();loss.backward();opt.step()
  with torch.no_grad():p=model(torch.tensor((vx-mean)/std).to(dev));v=(((p-torch.tensor((vy-amean)/astd).to(dev))**2)*torch.tensor(vm).to(dev).unsqueeze(-1)).sum()/(torch.tensor(vm).sum()*3);best=min(best,float(v))
 return model.cpu(),{'obs_mean':mean,'obs_std':std,'act_mean':amean,'act_std':astd},best
def learned_eval(model,norm,n=100):
 def pol(o):
  with torch.no_grad():return ((model(torch.tensor((o-norm['obs_mean'])/norm['obs_std']).float().unsqueeze(0))[0,0].numpy()*norm['act_std'])+norm['act_mean']).clip(-4,4)
 out=[]
 for seed in range(n):
  e=ReachingEnv();o=e.reset(seed);ret=0;steps=0
  while steps<100:
   chunk=[]
   with torch.no_grad():chunk=((model(torch.tensor((o-norm['obs_mean'])/norm['obs_std']).float().unsqueeze(0))[0].numpy()*norm['act_std'])+norm['act_mean']).clip(-4,4)
   for a in chunk[:K]:
    o,r,s,d,info=e.step(a);ret+=r;steps+=1
    if s or d:break
   if s or d:break
  out.append({'success':s,'final_error':info['error'],'steps':steps,'return':ret})
 return out
