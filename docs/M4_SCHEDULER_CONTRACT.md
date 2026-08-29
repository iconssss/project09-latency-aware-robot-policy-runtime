# M4 Scheduler Contract

FIFO retains every observation and chunk. LATEST replaces an unstarted observation and every unexecuted action in its pending chunk; started inference and the action already taken for the current step are never cancelled. Timestamps use perf_counter. action_age equals observation_wait_age plus policy_latency plus plan_age.
