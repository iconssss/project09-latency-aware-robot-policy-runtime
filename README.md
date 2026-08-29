# Latency-Aware Robot Policy Runtime

> Freshness-aware scheduling for asynchronous closed-loop learned robot policies.

## Motivation

Neural robot policies can infer more slowly than the control loop. The central systems question is therefore not just *how long inference takes*, but what happens to observations and actions while it runs:

`policy latency → producer/consumer mismatch → backlog → stale decisions → closed-loop degradation`

This project instruments end-to-end provenance and compares three scheduling semantics:

- **SYNC**: infer on the current observation, then act. It preserves freshness but lowers real-time control throughput when inference blocks.
- **ASYNC_FIFO**: preserve every observation/action in order. It can retain nominal controller throughput while accumulating stale work.
- **ASYNC_LATEST**: retain only the newest pending observation and action. It bounds scheduler-induced staleness, but cannot remove intrinsic inference latency.

**Key insight: throughput is not freshness.**

## System

```text
Observation Producer → Observation Buffer → Policy Worker → Action Buffer → Controller → Robot/Dynamics
                         FIFO / LATEST                      FIFO / LATEST
```

Every executed policy action records observation ID/timestamp, inference start/end, action ID, and execution timestamp. Action age is decomposed as observation wait + policy latency + action wait.

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) and [docs/EXPERIMENT_PROTOCOL.md](docs/EXPERIMENT_PROTOCOL.md).

## Key results

### Controlled learned-policy benchmark (M4)

M4 uses a learned Chunk-BC reaching policy on a learned reaching proxy (`H=16`, `k=4`). Zero-latency SYNC and LATEST baselines reached 100% success; FIFO retained stale chunks and failed across the formal matrix. At 100 ms, FIFO action-age p95 was 4460 ms and success was 0%; LATEST kept both queues at depth 1, action-age p95 200 ms, and success 100%.

### MuJoCo external validation (M5C)

M5C uses a fixed deterministic SAC state policy on unmodified MuJoCo `Reacher-v5`; it is a **single-action** policy, not an action-chunk experiment. At 100 ms artificial policy latency:

| Scheduler | Success | Control rate | Obs-wait p95 | Action-age p95 | Final distance |
| --- | ---: | ---: | ---: | ---: | ---: |
| SYNC | 100% | 9.90 Hz | 0 ms | 102 ms | 0.012 |
| FIFO | 20% | 20.41 Hz | 1111 ms | 1243 ms | 0.178 |
| LATEST | 100% | 20.41 Hz | 19 ms | 150 ms | 0.017 |

LATEST reduced action-age p95 by about 88% versus FIFO while retaining nominal 20 Hz control. At 400 ms, LATEST still bounded queues but fell to 55% success with 450 ms action-age p95: freshness scheduling removes avoidable backlog, not intrinsic policy latency.

## Reproduction

The recorded formal artifacts are the source of truth. Runtime dependencies were intentionally isolated in the Project09 MuJoCo environment; no rendering is required.

```bash
cd <repository-root>
PYTHONPATH=.venv-mujoco/lib/python3.12/site-packages CUDA_VISIBLE_DEVICES=-1 \
OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 python scripts/m5c_scheduler.py --seeds 20
```

This command is documented for reproducibility only; the completed benchmark should not be rerun without explicit controller approval.

## Scope and limitations

- The runtime is for learned robot policies, action-chunk policies, and high-latency neural/VLA-like deployment settings; it does **not** integrate a real VLA.
- M5C is state-based MuJoCo validation, not physical-robot validation.
- Latency is deliberately injected with wall-clock sleep.
- ManiSkill/SAPIEN graphics and MuJoCo EGL/OSMesa rendering were unavailable in the cloud container; no RGB/vision validation claim is made.

Detailed engineering decisions are in [docs/ENGINEERING_NOTES.md](docs/ENGINEERING_NOTES.md). Full numerical results are in [RESULTS.md](RESULTS.md); concise interview material is in [INTERVIEW_GUIDE.md](INTERVIEW_GUIDE.md).
