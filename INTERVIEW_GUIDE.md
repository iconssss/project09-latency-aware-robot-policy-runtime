# Interview guide

## 30-second version

I built a latency-aware runtime for learned robot policies. Instead of treating inference latency as only a speed problem, I instrumented observation-to-action provenance and showed that FIFO asynchronous scheduling can keep a controller near 20 Hz while executing decisions over a second old. On MuJoCo Reacher at 100 ms policy latency, latest-observation scheduling reduced p95 action age from 1.24 s to 150 ms and improved success from 20% to 100%.

## 2-minute version

The systems issue is a producer/consumer mismatch: the control loop produces observations faster than a neural policy consumes them. FIFO looks attractive because it preserves work and nominal throughput, but its queue turns delay into stale closed-loop actions. I compared synchronous execution, FIFO async, and a freshness-aware LATEST scheduler that keeps only one pending observation/action. I measured every timestamp in one clock domain and checked the action-age decomposition.

I first validated the mechanism with learned action chunks (`H=16`, `k=4`) on a controlled reaching proxy. I then transferred it to a separate MuJoCo Reacher-v5 setup with a fixed SAC single-action policy. At 100 ms, FIFO and LATEST both ran at about 20.4 Hz; FIFO had 20% success and 1.24 s p95 action age, LATEST had 100% success and 150 ms. At 400 ms, LATEST still bounded queues but fell to 55% success, showing that scheduling removes avoidable backlog but not intrinsic inference latency.

## 5-minute technical deep dive

1. Define action age as execution time minus source-observation time.
2. Decompose it into observation wait, policy latency, and post-inference action wait/plan age.
3. Show why FIFO queues increase age even if control ticks continue.
4. Explain LATEST semantics: replace only pending work; do not cancel in-flight inference or executing actions.
5. Present M4 as controlled learned Chunk-BC evidence, and M5C as independent single-action MuJoCo validation.
6. Explain SYNC carefully: it remains fresh and succeeds in M5C, but its real-time rate collapses at high latency because wall-clock delay blocks the loop.
7. State limits: state-only simulator evidence, injected latency, no real VLA or physical robot.

## Frequent questions

**Why is async not always better than sync?** Async can preserve tick rate while making each decision stale. SYNC trades throughput for current-state decisions.

**What is action age?** The elapsed time from the observation used by a policy to the action's execution. It captures queue-induced staleness that inference latency alone misses.

**Why does FIFO fail?** It faithfully executes obsolete work after the system state has changed. At M5C 100 ms, its observation wait p95 was 1111 ms.

**Why does LATEST work?** It makes freshness an explicit policy: pending stale work is replaced, bounding both pending queues at one item.

**Why does LATEST degrade at 400 ms?** It cannot remove the policy's own 400 ms inference delay; p95 action age remains about 450 ms.

**Why does SYNC 400 ms still have 100% success?** The sleep slows wall-clock control to 2.49 Hz but does not change the simulator's state/action transition relation. It is fresh but not real-time fast.

**Why M4 Chunk-BC and M5 SAC?** M4 isolates action-chunk scheduling behavior; M5C tests whether the freshness mechanism transfers to a different policy class and dynamics.

**Why is MuJoCo validation meaningful?** It is an external, unmodified physics environment that verifies the scheduler effect is not confined to the learned proxy. It is not a real-robot claim.

**Why no real VLA?** This project is a learned-policy runtime study. The architecture is VLA-oriented, but no real VLA integration is claimed.

**Relation to ROS2 or production runtimes?** The same provenance, bounded-buffer, deadline, and safety-interface concepts apply; production needs middleware integration and validation.

**Is this just queue size one?** No: the contribution is the causal scheduling argument, explicit replacement semantics, end-to-end timestamps, decomposition checks, and cross-setting evidence.

**What if actions cannot be dropped?** Separate safety-critical commands from discretionary policy actions, use validity windows or cancellation protocols, and preserve an audited fallback controller.

**How would you extend it to chunks/VLA/temporal ensembles?** Track source timestamps per chunk/action, define replacement boundaries, and choose freshness policies per horizon/ensemble member.

**How does hard real-time safety fit?** Keep the learned-policy runtime outside the safety loop; a deterministic low-level controller enforces limits and safe fallback.

**Largest limitation?** State-only simulated validation with synthetic latency; no physical robot, real VLA, or vision/rendering evidence.

## Resume bullets

- Built a latency-aware asynchronous runtime for learned robot policies, instrumenting end-to-end observation/action provenance and comparing synchronous, FIFO, and freshness-aware scheduling.
- On MuJoCo Reacher at 100 ms policy latency, latest-observation scheduling reduced p95 action age from 1.24 s to 150 ms and improved success from 20% to 100% while maintaining about 20 Hz control.
- Designed controlled action-chunk and independent MuJoCo validation experiments showing that throughput alone does not guarantee closed-loop freshness.
