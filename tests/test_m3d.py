import unittest,numpy as np
from envs.reaching_proxy import ReachingEnv
from policies.reaching_expert import action
from policies.chunk_bc import ChunkBC
class T(unittest.TestCase):
 def test_determinism(self):
  a=ReachingEnv();b=ReachingEnv();self.assertTrue(np.allclose(a.reset(1),b.reset(1)))
 def test_clip_direction(self):
  o=np.zeros(9);o[6]=10;self.assertTrue(np.all(action(o)<=4));self.assertGreater(action(o)[0],0)
 def test_model(self):self.assertEqual(tuple(ChunkBC()( __import__('torch').zeros(1,9)).shape),(1,16,3))
 def test_end(self):
  e=ReachingEnv();e.reset(0)
  for _ in range(100):o,r,s,d,i=e.step(np.zeros(3))
  self.assertTrue(d)
if __name__=='__main__':unittest.main()
