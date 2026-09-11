# Hardware integration plan

English | [Chinese](03_hardware_cn.md)

## Confirmed chassis and remaining measurements

Record wheel layout, steering linkage, wheel diameter under load, wheelbase,
track width, footprint including overhang, mass and approximate center of mass.
Photograph the underside and wiring; add measurements to the inventory. The drive layout is confirmed; its dimensions are still unmeasured.

The owner confirmed two rear drive motors, two passive front casters and an F4
lower-level controller. Use a two-wheel differential-drive model with one driven
wheel per side. The caster swivel and rolling behavior still affect transient
turning, rolling resistance and the swept footprint; do not model the front
wheels as powered skid-steer wheels.

Proposed body origin: rear drive axle midpoint. For wheel radius `r`, effective
rear wheel separation `b`, body forward speed `v` and yaw rate `omega`:

```text
left_wheel_radps  = (v - omega * b / 2) / r
right_wheel_radps = (v + omega * b / 2) / r
```

Start with measured radius/separation and validate wheel-specific scale factors.
A standard ros2_control diff_drive_controller with one wheel joint per side is
the initial candidate. The Jetson computes body-to-wheel targets and the F4
closes wheel velocity loops when feedback is available. Keep that conversion in
one place so the F4 does not apply differential kinematics a second time.

F4 is recorded exactly as provided. STM32F4 is a working family interpretation,
not a confirmed chip or board model. Obtain the board marking, schematic, timer
pin allocation, programmer/debugger and existing firmware before selecting a
build toolchain or peripherals.

## Motor and feedback inventory

For each motor record nominal voltage, stall/current rating from its datasheet,
gear ratio, speed under load and encoder presence. Distinguish pulses per motor
revolution, quadrature counts and counts per wheel revolution. Verify the left and right motor channels and their wiring to the F4/driver.

If no encoder feedback exists, document the limitation and choose a feedback
solution before claiming precise wheel-speed control. The host should send physical wheel velocity targets to the F4, not treat
uncalibrated PWM as speed.

## Power and wiring deliverables

Complete an electrical block diagram showing battery, fuse, accessible motor
stop, motor supply, regulated Jetson supply, ODIN1 supply and communications.
Verify ratings against the **actual carrier board and module**. Do not reuse a
developer-kit connector voltage for a different carrier. Separate motor noise
from compute power and document grounding and cable strain relief.

Measure rail sag while turning under load, driver temperature, Jetson thermal
throttling and ODIN1 disconnects. Add expected and measured values to a power
budget. Select DC/DC current headroom from measured peaks and datasheets.

## Mounting

Use a rigid, repeatable sensor mount with an observable ground region before the
front wheels reach the line. Check near-field blind spots, chassis occlusion,
exposure blur, vibration and whether the ground tilt sacrifices localization
features. The sensor mount is a calibration parameter, not an arbitrary URDF offset.
If the ODIN1 RGB view cannot support this task, evaluate a separate ordinary
camera only after confirming the rules; a dedicated line sensor is not assumed.

## Completion evidence

- Filled BOM and robot specification; unresolved fields explained.
- Measured low-speed straight motion and both turn directions.
- Encoder sign/scaling table and timeout/stop observations.
- Thermal and power trial with the sensor and compute operating together.
