# LineObservation contract

English | [Chinese](README_cn.md)

Interface version 0.1.0. [LineObservation.msg](msg/LineObservation.msg) atomically carries the acquisition stamp/frame in `path.header`, image health, path validity/confidence, corner and exit evidence. Geometry uses that frame; `image_valid` certifies image/projection health, not visible line support.

Local `line_controller` requires usable path evidence for ordinary tracking, rejects multiple exits and permits only bounded reuse of observed geometry during corner/curve maneuvers. `lap_controller` uses image health plus a separately published ground `black_mask` to align its prerecorded route; local `path_valid=false` alone does not mean the lap must stop. Image/odometry freshness and visual-alignment travel bounds still apply.

The message contains no simulator truth, scene identity or finish region. [Current and proposed interfaces](../../../docs/06_interfaces.md) distinguish implemented topics from hardware plans.
