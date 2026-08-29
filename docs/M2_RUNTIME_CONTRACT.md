# M2 Runtime Contract

SYNC: each observation is inferred synchronously, then its four-action chunk executes at 20 Hz before the next observation. It intentionally cannot maintain 20 Hz when inference blocks the cycle.

ASYNC_FIFO: observations arrive at 20 Hz; a policy worker emits FIFO chunks; the controller consumes at 20 Hz. At the production-window end no queue drain occurs: remaining actions are reported as unexecuted and discarded.

Action age is execution timestamp minus source-observation timestamp in the same `perf_counter()` clock domain. Deadline miss rate is a staleness proxy: fraction of executed actions with age greater than the 50 ms control period; it is not a hard-real-time deadline metric.
