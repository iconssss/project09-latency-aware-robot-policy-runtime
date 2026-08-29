# Experiment protocol

## Common principles

- Compare SYNC, ASYNC_FIFO, and ASYNC_LATEST under injected wall-clock latency.
- Record full observation/action provenance and verify timing decomposition.
- Use CPU-only execution; no rendering is required.
- Treat raw runs as immutable evidence. Formal aggregates and summaries are the reporting source of truth.

## M4 controlled learned-policy benchmark

- Learned Chunk-BC policy: `H=16`, execute `k=4` actions per control cycle.
- Learned reaching proxy, 20 Hz controller.
- Formal matrix: 0/25/50/100/200/400 ms × SYNC/FIFO/LATEST.
- Primary measures: success, controller rate, queue depths, observation wait, plan age, action age.

## M5C MuJoCo external validation

- Unmodified Gymnasium `Reacher-v5`; MuJoCo timestep 0.01 s, frame skip 2, native dt 0.02 s.
- Fixed `m5b_reacher_sac.zip`; `deterministic=True`; no fine-tuning or reward changes.
- Single action per inference, external scheduler at 20 Hz, native 50-step horizon.
- Formal matrix: 0/100/400 ms × SYNC/FIFO/LATEST × 20 seeds (`0..19`) = 180 episodes.
- Success: final fingertip-target distance `< 0.10`.
- Stop condition: provenance decomposition error above 0.1 ms. Observed maximum: 0.0 ms.

The M4 and M5C policies/dynamics differ; the intended comparison is scheduler mechanism transfer, not equality of raw metrics.
