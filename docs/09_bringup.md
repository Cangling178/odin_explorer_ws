# Bringup and operation plan

English | [Chinese](09_bringup_cn.md)

## Stage 0: foundation, available now

Build packages, run offline checks and launch the model preview. Inspect links,
wheel placement and units. Replace illustrative dimensions before using this
model for planning or footprint checks.

## Stage 1: electrical and motor bench, not implemented

Verify wiring/rating records and the physical motor stop. With wheels supported
off the surface, check each channel's direction, measured feedback and velocity
limit. Unplug communications and restart the host; the lower-level controller
must time out and require a deliberate re-arm. Record measured stopping behavior.

## Stage 2: ODIN1 and estimator bench, not implemented

Capture vendor data first. Audit frame directions, acquisition times and reset
behavior. Inspect static scenes, known translation and both rotations. Confirm
one TF publisher per edge and valid camera projection before fusing inputs.

## Stage 3: low-speed floor trials, not implemented

Start with a straight line and broad turn. Compare encoder/ODIN1/independent
motion measurements; calibrate wheel scales and effective track width if
applicable. Verify line visibility over the needed preview range. Stop on invalid
data before testing any degraded operating mode.

## Stage 4: full course accuracy, not implemented

Load the validated ordered route; the owner allows advance route preparation. Test the crossing and tight
bends independently, then the complete route. Verify checkpoint/finish semantics
and measure error using an external reference. Meet the agreed accuracy gate.

## Stage 5: speed trials, not implemented

Introduce bounded curvature speed limits and measured braking. Run repeated
paired trials, preserve raw evidence and report unsuccessful runs. Change one
setting at a time. Do not trade wrong-route shortcuts for faster completion.

## Diagnostic guide

| Symptom | First checks |
| --- | --- |
| Robot model absent | Source overlay; model topic; RViz fixed frame |
| Pose rotates in wrong direction | Frame convention, IMU axes, encoder signs |
| Duplicate/jumping TF | Competing vendor/estimator broadcasters, loop closure |
| Straight tracking oscillates | Timestamp delay, lookahead, wheel response, exposure |
| Wrong branch at crossing | Segment/progress association and exit hysteresis |
| Turns cut inside line | Feasible radius, preview distance, speed and footprint |
| Sensor disconnects under motion | Power sag, cable movement, USB and thermal logs |
| Excellent internal error but visible drift | Wrong reference, circular evaluation or calibration |

Record faults as reproducible backlog items with commit, parameters and evidence.
There is deliberately no race.launch.py until the dependent components exist.
