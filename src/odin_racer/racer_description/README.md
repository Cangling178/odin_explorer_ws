# racer_description

English | [Chinese](README_cn.md)

Robot Xacro/CAD assets, frame geometry, simulation world generators and the FishPoly Gazebo camera plugin. Existing model mass is a 0.877 kg subtotal; 25 collision primitives are retained when fixed parts merge into three dynamic bodies.

| Location | Responsibility |
| --- | --- |
| `urdf/`, `meshes/` | Assembly, approximate inertia/collision and source-derived visuals |
| `racer_description/contact_world.py`, `drive_world.py` | Passive contact and ros2_control worlds |
| `racer_description/sensor_world.py`, `fishpoly.py` | Shared sensor generation and projection model |
| `racer_description/course_world.py`, `course_texture.py` | Image-derived competition map and isolated line fixtures |
| `plugins/odin_fishpoly_camera.cpp` | FishPoly rendering and ROS image/calibration output |
| `config/` | Contact, actuation, sensor and course settings |

[Simulation commands](../../../simulation/README.md) · [Model assumptions](../../../simulation/MODEL.md) · [Chassis provenance](../../../hardware/mechanical/chassis_plate/README.md) · [ODIN provenance](../../../hardware/mechanical/odin1/README.md).
Model preview is available through `racer_bringup preview.launch.py`; physical parameters and mounting remain uncalibrated against the vehicle.
