import unittest,math
from runtime.m3_pendulum import wrap,control,Worker
import numpy as np
class M3Tests(unittest.TestCase):
 def test_wrap(self):self.assertAlmostEqual(wrap(3*math.pi),-math.pi)
 def test_bounds(self):self.assertLessEqual(abs(control(np.array([-1.,0.,20.]))),2)
 def test_latest_replacement(self):
  w=Worker(0,True);w.start();w.submit(1,1.,np.array([1.,0.,0.]));import time;time.sleep(.02);w.submit(2,2.,np.array([1.,0.,0.]));time.sleep(.02);c,i=w.take();w.finish();self.assertEqual(c.oid,2);self.assertEqual(i,0);self.assertGreaterEqual(w.replaced,1)
if __name__=='__main__':unittest.main()
