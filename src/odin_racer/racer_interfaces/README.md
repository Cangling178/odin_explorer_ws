# Visual line observation interface

[English](README.md) | [Chinese](README_cn.md)
`LineObservation` atomically carries the acquisition-stamped local path, image
health, path validity/confidence, corner position, observed exit direction and
exit count. All geometry uses `path.header.frame_id`; the stamp is the original
camera acquisition time. `image_valid` does not imply a visible line.

Empty/invalid paths authorize no normal translation. Only the bounded corner
state machine can temporarily use a previously observed corner in wheel odometry,
while new healthy images, TF and odometry remain mandatory. Multiple exits are
rejected. No scenario name, reference route, ground truth or end region is carried.

Interface version: 0.1.0 (isolated-scene prototype).
