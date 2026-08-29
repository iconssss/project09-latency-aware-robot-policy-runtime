# M3 Closed-Loop Contract

Pendulum-v1 is headless. The fixed controller period is 50 ms. The policy emits a repeated-action chunk H=4 using u=clip(-6*theta-2*theta_dot,-2,2), with theta=atan2(sin,cos) and target theta=0.

SYNC infers then executes a whole chunk. ASYNC_FIFO appends chunks. ASYNC_LATEST keeps one pending chunk: a newly produced chunk replaces all unexecuted actions in the pending chunk; an action already taken for the current environment step is never revoked. Action age is execution perf_counter minus source-observation perf_counter. Success is final 20 percent mean absolute angle below 0.2 rad.
