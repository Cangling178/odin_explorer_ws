# Work assignments for the first three real-robot development roles

English | [Chinese](TEAM_ASSIGNMENTS_cn.md)

Updated: 2026-09-21. Individual names remain unassigned. This document defines responsibilities and handoffs; it does not claim that real-robot capabilities are complete.

## Goal and existing baseline

The immediate shared goal is to connect Jetson, ODIN1, and F4, demonstrate repeatable low-speed straight and circular tracking, and then progress to correct complete laps and performance improvements.

C++ perception, single-branch tracking, prerecorded-route-assisted lap control, and simulation evaluation already exist. Simulation passed three independent laps at 0.05 m/s and one at 0.10 m/s. These results do not establish real-robot acceptance. F4 communication and physical chassis integration remain unimplemented. ODIN1 driver build and initial point-cloud display were recorded on a development laptop; the Jetson combination, real image projection, and calibration still require validation.

Person 4 owns overall coordination, system integration, and independent acceptance. Only that role's handoffs with the first three people are covered here.

## Person 1: F4 firmware, chassis actuation, and Jetson communication

### Responsibilities and code ownership

Own the complete chain from Jetson wheel-speed targets to physical wheel motion and returned feedback, including host-side hardware adaptation.

- Firmware and communication protocol: `firmware/`.
- Jetson hardware adaptation: `src/odin_racer/racer_hardware/`.
- Hardware parameters, wiring, and wheel calibration: `hardware/`.

### Prerequisites

Identify the exact F4 board, motors, drivers, encoders, gear ratio, supply, pins, and stopping wiring. Agree with the integration lead on serial or CAN and the host hardware interface. These details are not fully confirmed. Protocol drafting and simulated communication tests can start earlier, but assumed values must not replace measured specifications.

### Task sequence

1. Document hardware, wiring, encoder conversion, wheel direction, and physical units.
2. Implement encoder acquisition, motor output, and wheel-speed feedback control. Record step response, steady-state error, and low-speed behavior.
3. Freeze a protocol with the integration lead: version, framing, byte order, units, sequence numbers, integrity checks, enable, feedback, faults, and restart semantics.
4. Implement Jetson transport and F4 parsing. Return cumulative wheel position or counts, speed, device sample time, and status.
5. Implement explicit enable, target bounds, command timeout stopping, and recovery. Old packets must not re-enable motion.
6. Integrate with the host differential-drive controller. Measure wheel radius, separation, and speed conversion; validate straight motion, turning, and stopping.

### Interfaces and deliverables

| Item | Requirement |
| --- | --- |
| Targets | Left/right wheel angular velocity in rad/s, with explicit ordering, direction, and enable state |
| Feedback | Wheel position in rad or convertible cumulative counts, velocity in rad/s, sample time, fault and enable state |
| Kinematic boundary | The host differential-drive controller converts body velocity to wheel targets; F4 closes wheel-speed loops |
| Files | Firmware, reproducible build/flash instructions, versioned protocol, Jetson adapter, wiring and parameter records |
| Evidence | Communication logs, wheel response plots, invalid-input and disconnect stopping records |

Person 1 owns feedback transport. The integration lead owns differential-drive controller configuration, odometry integration, and assignment of the `odom → base_link` publisher.

### Acceptance criteria

- Wheel targets, direction, units, and feedback agree; loop error meets thresholds agreed before integration.
- Low-speed straight motion, turning in both directions, and stopping work; report command-to-feedback delay and actual feedback frequency.
- Test bad integrity checks, truncated frames, duplicate/out-of-order packets, excessive targets, disconnects, and restarts.
- The lower controller stops within the agreed timeout when commands cease; reconnection does not automatically resume motion.

## Person 2: ODIN1 integration, calibration, and data acquisition on Jetson

### Responsibilities and code ownership

Deliver sensor data that algorithms can directly consume, with explicit temporal and spatial meaning.

- Vendor driver workspace: `vendor_ws/`, with independent version records.
- Project adapter: `src/odin_racer/racer_odin/`.
- Sensor model and installation transforms: relevant configuration in `src/odin_racer/racer_description/`, coordinated with the integration lead.
- Calibration records: `hardware/calibration/`; raw data: `data/`.

### Prerequisites

Obtain the physical ODIN1, Jetson/carrier details, matching firmware and driver, working USB link, and correct power. Moving recordings require controlled motion, but static images, calibration inspection, and ground visibility checks can proceed independently.

### Task sequence

1. Record Jetson OS, ROS, device firmware, and driver versions; build and validate the connection on the target.
2. Inspect actual image, IMU, point-cloud, and pose topics, types, frames, timestamps, rates, and QoS. Prioritize the image chain required for tracking.
3. Distinguish raw and undistorted images and use the device model and calibration matching the chosen stream.
4. Provide matching `CameraInfo` in the adapter while preserving image acquisition time. Current perception requires identical timestamps and the FishPoly model.
5. Measure camera-to-body extrinsics and ground geometry; integrate TF with the lead.
6. Record straight lines, arcs, tight turns, and crossings under expected lighting; document near/far usable ground visibility.
7. Deliver replayable bags. Coordinate synchronized odometry, TF, command, and status recording during moving trials.
8. Validate sustained operation, reconnection, driver restart, and data stability under chassis load.

### Interfaces and deliverables

| Item | Requirement |
| --- | --- |
| Images | `sensor_msgs/Image` with documented encoding, resolution, optical frame, and acquisition time |
| Calibration | `sensor_msgs/CameraInfo` matching the image model and exact timestamp under the current interface |
| Installation | Versioned body-to-camera extrinsics and measurement evidence; TF ownership coordinated by the lead |
| Other data | Document IMU, point-cloud, and pose units, reference frames, clocks, and reset behavior; integrate as needed |
| Files | Driver version record, adapter/configuration, startup instructions, calibration, bag index, and validation report |

Planned `/sensors/odin/*` names are not guarantees about vendor topics. Person 2 and the lead record final remappings. Person 2 owns data and calibration correctness; Person 3 owns line extraction and matching algorithms.

### Acceptance criteria

- Jetson receives valid sustained data; report rate, delay, frame loss, and resource usage.
- Images, CameraInfo, and TF meet current perception requirements; quantify ground projection error.
- The installed camera sees the required lookahead region; provide reproducible straight, curved, and crossing samples to Person 3.
- Detect stale data, disconnects, and restarts without disguising old samples with new timestamps.
- Bags and configuration replay in the agreed environment and include version, scene, and acquisition conditions.

## Person 3: Perception, tracking, and real-robot algorithm adaptation

### Responsibilities and code ownership

Convert valid sensor and motion-state inputs into route-following commands. Own real-data adaptation, low-speed tracking, and subsequent precision and speed improvements.

- Perception: `src/odin_racer/racer_perception/`.
- Tracking: `src/odin_racer/racer_control/`, including `line_controller.cpp` and `lap_controller.cpp`.
- Routes: `src/odin_racer/racer_trajectory/`, `tracks/`, and `tools/generate_competition_lap.py`.
- Regression and analysis: relevant `tools/` and `tests/`; agree independent acceptance thresholds with the lead.

### Prerequisites and current status

| Stage | Prerequisites | Current status |
| --- | --- | --- |
| Simulation development | Images, calibration, TF, wheel odometry, actuation model, route, and evaluator | Available; core lap control exists; repetition and disturbance tests can start now |
| Offline real-image validation | Real images, correct intrinsics, installation extrinsics, and scene records | Real-data integration acceptance pending; Person 2 supplies these without waiting for F4 completion |
| Moving-data replay | Above inputs plus synchronized acquisition-time TF and motion state | Prepared jointly by Persons 1, 2, and the lead |
| Real straight/arc tracking | Valid perception, reliable wheel actuation/feedback, continuous odometry, consistent timing, and stopping | Complete physical chain not yet integrated |
| Correct complete laps | Basic tracking, measured ordered route, official start/direction/crossing order, tight-turn feasibility | Not fully confirmed |
| Real performance optimization | Repeatable low-speed route baseline and independent error measurement | Starts after preceding gates pass |

Simulation completion does not establish real-robot acceptance. Basic physical tracking is a shared four-person deliverable; Person 3 does not independently implement the entire hardware and system chain.

### Task sequence

1. Understand and preserve the existing baseline, keeping single-branch and complete-lap use cases distinct; record versions and configuration.
2. While hardware is prepared, test repetition, start offsets, image faults, and odometry disturbances in simulation, retaining failures.
3. Agree acquisition needs with Person 2; inspect line extraction, ground projection, confidence, and visual matching offline.
4. Adapt algorithms and parameters to real data, distinguishing calibration, detection, and association failures.
5. Integrate low-speed straight and arc tracking with the lead; validate error, actuation delay, and stopping on image/odometry faults.
6. Validate crossings, tight turns, start/finish, and continuous laps using the measured route; preserve ordered progress constraints.
7. Establish repeatable precision before optimizing lookahead, curvature limits, anticipatory braking, and speed profiles; do not relax thresholds to claim improvement.

### Interfaces and deliverables

| Item | Requirement |
| --- | --- |
| Inputs | Images and matching CameraInfo, TF, continuous odometry, ordered reference route, and runtime configuration |
| Internal perception interface | Retain `racer_interfaces/LineObservation`; complete-lap control also consumes the ground black-line mask |
| Outputs | Autonomous `geometry_msgs/TwistStamped` targets with status and diagnostic evidence |
| Control boundary | Person 3 owns autonomous commands; the lead owns mode selection and the final command outlet; Person 1 owns execution and lower-level timeout stopping |
| Files | Algorithms, configuration versions, route provenance, replay instructions, regression reports, and failure analysis |

### Acceptance criteria

- Real-sample detections and projections are visually inspectable, with explicit failure records.
- Simple physical routes are repeatable; invalid inputs stop motion without automatic resumption.
- Complete routes follow required crossing/checkpoint order and stop at the finish without branch jumps or shortcuts.
- Report success rate, time-weighted RMS, maximum error, valid-data coverage, lap time, and all failures. The lead organizes independent measurement; controller estimates alone are not ground truth.
- Compare changes under equivalent conditions and fixed thresholds. Set physical numeric criteria before trials using draft requirements, measured capabilities, and official rules.

## Shared interfaces and handoffs

### Agree before implementation

- Person 1 and lead: transport, protocol version, wheel order/direction, target/feedback rates, clocks, limits, enable, and timeout.
- Persons 2, 3, and lead: image model, topics, timestamps, QoS, extrinsics, and unique TF publishers.
- Person 3 and lead: odometry input, autonomous command outlet, mode switching, fault recovery, and route configuration format.
- Everyone: recording/replay, version archives, acceptance thresholds, and failure reporting. Explicitly mark unresolved parameters rather than treating them as frozen interfaces.

### Staged handoffs

| Stage | Person 1 | Person 2 | Person 3 | Delivery to integration lead |
| --- | --- | --- | --- | --- |
| A Device preparation | Motor bench, communication, feedback | Jetson driver, real images, initial calibration | Simulation regression, acquisition requirements | Independently testable chassis and camera |
| B Simple tracking | Actuation calibration and error | Ground projection checks, synchronized recordings | Straight/arc control and fault stopping | Physical low-speed loop and independent error report |
| C Complete route | Execution errors and slip | Visibility, timing, and image failures | Tight turns, crossings, ordered lap | Complete-route results and all failures |
| D Performance | Execution at higher targets | Moving image quality and delay | Precision, lookahead, speed profiles | Repeated comparisons with fixed versions |

Integrate before all three roles finish. Preserve a runnable version at each stage. Every delivery records owner, commit, configuration, reproduction steps, evidence location, and limitations. Keep large raw datasets in `data/` under repository policy and commit reviewable summaries.

## References

- [Remaining work and priorities](README.md)
- [Requirements and proposed acceptance gates](../01_requirements.md)
- [Interface conventions](../06_interfaces.md)
- [F4 firmware and communication](../../firmware/README.md)
- [ODIN1 vendor integration records](../../vendor_ws/README.md)
- [Real-robot bringup](../09_bringup.md)
