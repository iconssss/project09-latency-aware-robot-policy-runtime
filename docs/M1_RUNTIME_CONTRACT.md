# M1 Runtime Contract

M1 uses standard-library threads and shared FIFO queues to decouple the producer, policy worker, and fixed-rate controller. All interval timestamps, including action age, use the `time.perf_counter()` monotonic clock domain.

Action chunks preserve source observation and policy start/end. Execution records preserve chunk/action indices, policy latency, and action age.

Runtime summaries distinguish production window, controller execution window, shutdown window, and total wall/runtime. The action buffer reports maximum queued chunks. No queue drain occurs at shutdown: remaining observations and action chunks are discarded. FIFO behavior, stale dropping, adaptive chunking, and queue optimization remain deferred.
