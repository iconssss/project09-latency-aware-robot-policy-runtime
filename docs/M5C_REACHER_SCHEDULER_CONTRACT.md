# M5C Reacher-v5 Scheduler External Validation Contract

- Policy: fixed `artifacts/m5b_reacher_sac.zip`; `SAC.predict(..., deterministic=True)`; no training or parameter changes.
- Environment: unmodified `Reacher-v5`, MuJoCo timestep `0.01 s`, `frame_skip=2`, effective native control dt `0.02 s`, native 50-step horizon.
- Scheduler: one action per inference. The external scheduler is paced at 20 Hz (`50 ms`). This differs from the native 50 Hz physics-control dt, but does not alter the environment or its horizon; each scheduler tick executes exactly one native `env.step`.
- Modes: `SYNC`, `ASYNC_FIFO`, and `ASYNC_LATEST`; artificial latency is wall-clock `time.sleep` at 0/100/400 ms.
- Async FIFO consumes in submission order. Async LATEST holds at most one pending observation and one pending action, replacing stale pending items.
- Success: final fingertip-target distance `< 0.10`.
- Every executed policy action records observation/source timestamps and IDs, inference start/end, action ID, execution timestamp, and the observation-wait + policy-latency + action-wait decomposition. The benchmark aborts if decomposition error exceeds 0.1 ms.
