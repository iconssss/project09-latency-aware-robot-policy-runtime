import unittest
from runtime.m4 import pct
class T(unittest.TestCase):
 def test_pct(self):self.assertEqual(pct([1,2,3],50),2)
if __name__=='__main__':unittest.main()
