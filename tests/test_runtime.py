import unittest
from runtime.runner import run_synthetic_runtime
class RuntimeTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.records,cls.summary=run_synthetic_runtime(.45,20,40,5,3)
 def test_traceability_and_chunk_size(self):self.assertTrue(self.records);self.assertTrue(all(r.source_observation_id>=0 and 0<=r.action_index_in_chunk<3 for r in self.records))
 def test_timestamp_order_and_action_age(self):
  for r in self.records:
   self.assertLessEqual(r.source_observation_timestamp,r.policy_start_timestamp);self.assertLessEqual(r.policy_start_timestamp,r.policy_end_timestamp);self.assertLessEqual(r.policy_end_timestamp,r.execution_timestamp);self.assertAlmostEqual(r.action_age_ms,(r.execution_timestamp-r.source_observation_timestamp)*1000)
 def test_latency_shutdown_and_window_metrics(self):
  self.assertGreaterEqual(self.summary['mean_policy_latency_ms'],4);self.assertGreater(self.summary['achieved_controller_rate_hz'],20);self.assertGreaterEqual(self.summary['actual_runtime_s'],self.summary['production_duration_s']);self.assertGreaterEqual(self.summary['shutdown_duration_s'],0);self.assertGreaterEqual(self.summary['max_action_queue_depth_chunks'],0)
if __name__=='__main__':unittest.main()
