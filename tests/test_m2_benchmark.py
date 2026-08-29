import unittest
from runtime.m2_benchmark import run_async_fifo,run_sync
class M2Tests(unittest.TestCase):
 def test_sync_runs_and_exits(self):
  records,s=run_sync(0,.2);self.assertTrue(records);self.assertEqual(s['final_action_queue_depth_chunks'],0)
 def test_async_queue_metrics(self):
  records,s=run_async_fifo(50,.3);self.assertGreaterEqual(s['max_action_queue_depth_chunks'],s['final_action_queue_depth_chunks']);self.assertEqual(s['unexecuted_action_count'],s['produced_action_count']-s['executed_action_count'])
 def test_balance_and_schema(self):
  _,s=run_async_fifo(200,.5);self.assertEqual(s['expected_backlog_direction'],'stable');self.assertTrue({'actual_runtime_s','action_age_p95_ms','measured_policy_action_rate'}.issubset(s))
if __name__=='__main__':unittest.main()
