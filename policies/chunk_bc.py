import torch
from torch import nn
class ChunkBC(nn.Module):
 def __init__(self,h=16):
  super().__init__();self.h=h;self.net=nn.Sequential(nn.Linear(9,128),nn.ReLU(),nn.Linear(128,128),nn.ReLU(),nn.Linear(128,h*3))
 def forward(self,x):return self.net(x).view(-1,self.h,3)
