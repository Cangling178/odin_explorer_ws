# Laboratory exploration assignments

Names remain unassigned. A fourth person owns system integration. These are tasks, not implementation claims.

| Role | Scope | Deliverables |
| --- | --- | --- |
| Person 1: base/F4 | firmware, explorer_hardware, electrical specifications | protocol, wheel loops/feedback, host adapter, independent watchdog, calibration |
| Person 2: ODIN/Jetson | vendor_ws, explorer_odin, extrinsics | validated versions, clouds/pose/clocks/TF, manual mapping, save/relocalization reports and bags |
| Person 3: localization/navigation | explorer_localization, explorer_navigation | occupancy integration, obstacles, Nav2, exploration goals and failure handling |
| Lead: integration | explorer_bringup, shared model/config | TF ownership, arbitration/stop gate, integration and independent acceptance |

A: validate laboratory mapping alongside motor bench work and mapping/navigation contracts.
B: integrate teleoperation, continuous odometry, obstacle visualization and fail-stop.
C: implement goal navigation while mapping; investigate sensor, localization and execution failures.
D: add frontier goals, bounds, completion/save, then waypoint patrol.

Agree units, rates/timeouts, clocks, real topics, TF publishers, map coordinates, command types and thresholds. Each stage hands over revision, configuration, reproduction instructions, data index and limitations. Unmeasured values remain TBD.
