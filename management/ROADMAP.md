# Roadmap

Use evidence gates instead of fixed dates before the hardware and rules are known.
Only M0 is delivered by this foundation; later milestones are not started.

| Milestone | Deliverable | Exit evidence | Depends on |
| --- | --- | --- | --- |
| M0 Foundation | English workspace, buildable assets, local Git and offline metrics | Build/check report | None |
| M1 Requirements and inventory | Remaining rule answers, F4 model, ratings and dimensions | REQ/Q matrix and completed hardware forms | M0 |
| M2 Motor and sensor bench | Feedback control, watchdog, ODIN1 capture and calibration | Bench logs, measured timing and ground visibility | M1 |
| M3 Low-speed tracking | Simple-line control and valid metric pipeline | Independent error on straight/arcs | M2 |
| M4 Correct full course | Ordered route, correct crossing, feasible bends | Ten repeat attempts with failure log | M3, surveyed course |
| M5 Accuracy baseline | Repeatable accepted error limits | Calibration revision and acceptance report | M4 |
| M6 Speed optimization | Bounded speed profile and fair controller comparison | Reduced valid time at retained accuracy | M5 |
| M7 Competition release | Frozen parameters and reproducible startup | Full rehearsal and tagged evidence | M6 |
| M8 Optional navigation | Nav2/local environment integration | Separate navigation tests | M7 or explicit scope change |

The critical early decision is whether the existing chassis can negotiate this
course within the judged corridor and whether ODIN1's camera sees the line well
enough. Resolve those before advanced planner or GPU work.
