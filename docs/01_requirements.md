# Requirements and acceptance

English | [Chinese](01_requirements_cn.md)

## Confirmed by the project owner

| ID | Requirement | Verification |
| --- | --- | --- |
| REQ-001 | Existing two-motor rear differential drive with two front passive casters | Inventory and photographs |
| REQ-002 | ROS 2 and Jetson Orin Nano | Target software inventory and build |
| REQ-003 | Integrate Manifold ODIN1 | Timestamped sensor capture and frame checks |
| REQ-004 | Follow the supplied marked course without a dedicated line module | Hardware inventory and full-route trial |
| REQ-005 | Evaluate both accuracy and speed | Error report plus timed valid completion |
| REQ-006 | Clear English workspace, local Git history and matching `_cn.md` Chinese documentation | Repository review |
| REQ-007 | Jetson host and a separate F4 lower-level controller | Board identification and transport test |
| REQ-008 | Treat prior mapping, preloaded routes and camera line recognition as allowed | Owner clarification; retain remaining judging questions |

## Course evidence

The supplied image labels the outer board as 200 cm by 150 cm and the red
reference extents as 161 cm horizontally and 120 cm vertically. These are
image annotations, not a certified survey or a complete route specification.
The line includes an intersection, tight bends, apparent sharp corners and a
sequence of lower S-bends. The image alone does not establish travel direction,
start/finish, required crossing order, line width or scoring tolerances.

## Questions that block final hardware or race settings

| ID | Unknown | Design consequence |
| --- | --- | --- |
| Q-01 | Exact rear-axle dimensions, front caster geometry and footprint? | Differential kinematics calibration and swept volume |
| Q-02 | Encoder resolution, gearing and motor/driver ratings? | Closed-loop wheel control and odometry |
| Q-03 | Camera ground coverage and exposure on the actual mount? | Visual feedback feasibility; camera use is allowed |
| Q-04 | Exact F4 board, firmware toolchain and motor-driver transport? | Lower-level implementation; prior routes are allowed |
| Q-05 | Start, direction, laps and crossing branch sequence? | Ordered route and completion logic |
| Q-06 | What point on the robot is judged; line width and allowed deviation? | Measurement reference and error thresholds |
| Q-07 | Penalties for stopping, reversing, leaving the line or cutting corners? | Controller feasibility and valid-run policy |
| Q-08 | Robot size limits, surface, lighting and obstacles? | Mounting, footprint and test matrix |
| Q-09 | Jetson carrier, RAM, installed JetPack and ODIN1 firmware? | Compatibility and power budget |

Unknowns remain `null` in templates. Never use guessed values as measured facts.
The owner explicitly allowed camera line recognition, advance mapping and preloaded
routes for this design on 2026-09-10. Do not reopen those as unresolved assumptions.

## Proposed internal acceptance gates

These are engineering goals, not competition rules or demonstrated performance.
Confirm or revise them after the first measured trials.

- G0: record remaining rules, measured drive geometry, electrical ratings and course survey.
- G1: command timeout and physical stop work; encoder signs and wheel speed agree.
- G2: ground line is visible over the required lookahead; calibration residuals and
  end-to-end latency are measured; invalid data cannot remain silently fresh.
- G3: complete the prescribed route without a wrong crossing branch at low speed.
- G4: provisional target: ten consecutive complete runs; RMS lateral error at most
  0.02 m and maximum absolute error at most 0.05 m, measured independently.
- G5: reduce median valid completion time while retaining G4 and reporting all
  failed trials. Revise limits to match the actual judging rules and robot size.

No target lap time is set before route length, turn feasibility and hardware
limits are measured. Do not combine speed and error into an invented official score.

## Deferred scope

Semantic navigation, language models, object recognition, cloud processing and
general-purpose exploration are outside the first competition milestone.
Obstacle handling initially means detecting a blocked route and stopping;
any permitted detour needs a separate rule decision.
