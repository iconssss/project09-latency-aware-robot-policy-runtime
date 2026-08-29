# Engineering notes and bounded negative results

## Environment decisions

- ManiSkill/SAPIEN robot validation was not completed because the cloud container lacked usable Vulkan graphics capability. This was not pursued further.
- MuJoCo physics and Reacher-v5 state-based stepping passed. EGL and OSMesa rendering were unavailable, so M5C is deliberately state-based rather than visual validation.
- The analytical Jacobian-PD Reacher expert failed bounded gain tuning (2%, 9%, 12% success). It was recorded as a negative result and not tuned further.
- A lightweight SAC policy provided the reliable M5C robot-policy backend: 100 seeded evaluations, 100% success, mean final distance 0.01345.

## Scope boundaries

- No real VLA integration, physical robot, RGB/vision benchmark, or ManiSkill success claim is made.
- Artificial latency is a controlled `perf_counter()`/`sleep()` intervention, not a claim about a particular model's deployment latency.
- The project demonstrates runtime scheduling and provenance mechanisms, not a hard-real-time safety controller.
