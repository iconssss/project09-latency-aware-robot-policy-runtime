# Results

## Experimental framing

M4 is a controlled learned-policy benchmark using Chunk-BC (`H=16`, `k=4`) on a learned reaching proxy. M5C is external validation on MuJoCo Reacher-v5 with a fixed deterministic SAC **single-action** policy. The experiments test scheduling and freshness mechanisms across different policy and dynamics settings; their absolute numerical results are not intended to match.

## Table 1 — M4 controlled learned-policy benchmark

Formal matrix: 3 schedulers × 6 latencies, CPU-only. `action age = observation wait + policy latency + plan age`; decomposition error was 0.

| Mode | Latency | Success | Control rate | Action-age p95 | Max obs/action queue |
| --- | ---: | ---: | ---: | ---: | ---: |
| SYNC | 0 ms | 100% | 20.00 Hz | 150 ms | 0 / 0 |
| SYNC | 100 ms | 100% | 19.85 Hz | 150 ms | 0 / 0 |
| SYNC | 400 ms | 100% | 9.60 Hz | 402 ms | 0 / 0 |
| FIFO | 0 ms | 0% | 19.96 Hz | 4455 ms | 1 / 93 |
| FIFO | 100 ms | 0% | 19.91 Hz | 4460 ms | 50 / 43 |
| FIFO | 400 ms | 0% | 19.20 Hz | 4475 ms | 87 / 7 |
| LATEST | 0 ms | 100% | 19.99 Hz | 50 ms | 1 / 1 |
| LATEST | 100 ms | 100% | 19.78 Hz | 200 ms | 1 / 1 |
| LATEST | 400 ms | 5% | 19.22 Hz | 800 ms | 1 / 1 |

FIFO can maintain controller throughput while executing obsolete action chunks. LATEST trades dropped/replaced pending work for bounded freshness and substantially better closed-loop behavior.

## Table 2 — M5C MuJoCo Reacher-v5 external validation

20 seeds per configuration; 50-step native horizon; success is final fingertip-target distance `< 0.10`. Values are configuration means; p95 columns are aggregate provenance metrics.

| Mode | Latency | Success | Return | Final distance | Control rate | Obs-wait p95 | Action-age p95 | Max obs/action queue |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| SYNC | 0 ms | 100% | -3.785 | 0.012 | 20.40 Hz | 0 ms | 1 ms | 0 / 0 |
| SYNC | 100 ms | 100% | -3.785 | 0.012 | 9.90 Hz | 0 ms | 102 ms | 0 / 0 |
| SYNC | 400 ms | 100% | -3.785 | 0.012 | 2.49 Hz | 0 ms | 401 ms | 0 / 0 |
| FIFO | 0 ms | 100% | -4.066 | 0.012 | 20.41 Hz | 0 ms | 50 ms | 1 / 1 |
| FIFO | 100 ms | 20% | -11.660 | 0.178 | 20.41 Hz | 1111 ms | 1243 ms | 25 / 1 |
| FIFO | 400 ms | 20% | -9.439 | 0.163 | 20.41 Hz | 1668 ms | 2113 ms | 43 / 1 |
| LATEST | 0 ms | 100% | -4.066 | 0.012 | 20.41 Hz | 1 ms | 50 ms | 1 / 1 |
| LATEST | 100 ms | 100% | -5.609 | 0.017 | 20.41 Hz | 19 ms | 150 ms | 1 / 1 |
| LATEST | 400 ms | 55% | -8.787 | 0.109 | 20.41 Hz | 7 ms | 450 ms | 1 / 1 |

At 100 ms, FIFO and LATEST both sustain about 20.41 Hz. Yet FIFO has 20% success and 1243 ms action-age p95, whereas LATEST has 100% success and 150 ms action-age p95—an approximately 88% freshness improvement. Thus nominal control throughput alone is insufficient.

At 400 ms, LATEST is still materially fresher than FIFO (450 vs 2113 ms action-age p95) but drops to 55% success. The bounded queue prevents scheduler-induced backlog; it cannot cancel the 400 ms intrinsic inference delay.

## SYNC interpretation

SYNC retains a current observation/action relation, so M5C success remains 100% at 0/100/400 ms. The injected wall-clock delay instead reduces real-time controller frequency from 20.40 to 2.49 Hz; it does not alter the simulator transition relation. SYNC is therefore fresh but slow, FIFO is high-throughput but stale, and LATEST retains high nominal throughput with bounded freshness until intrinsic latency dominates.

## Formal artifacts

- `results/m4_formal_aggregate.csv`, `results/m4_formal_verdict.json`
- `results/m5c_scheduler_aggregate.csv`, `results/m5c_scheduler_summary.json`, `results/m5c_raw/`
- `results/figures/m5c_success_vs_latency.svg`, `m5c_action_age_p95.svg`, `m5c_final_distance.svg`
