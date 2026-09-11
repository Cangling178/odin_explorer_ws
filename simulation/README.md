# Simulation plan

English | [Chinese](README_cn.md)

No physics simulator is configured yet. The URDF preview is visual only.
Select the simulator after the ROS/JetPack and drive-model decisions.
Run compute-heavy simulation on the workstation where practical.

Begin with deterministic planar tests: straight, constant-radius arc, S-curve,
crossing with repeated coordinates, sharp corner and controlled data dropout.
Then model measured wheel geometry, actuator delay, saturation, slip and camera
field of view. Test that the chassis can traverse the surveyed corridor.

Acceptance: correct ordered progress, bounded command output, explicit invalid
state on missing observations, no corner shortcuts, and reproducible error/time
reports. Simulation results do not substitute for independent physical trials.
