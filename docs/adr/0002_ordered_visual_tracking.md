# ADR-0002: Ordered course with local visual feedback

English | [Chinese](0002_ordered_visual_tracking_cn.md)

Status: selected design direction, 2026-09-10; camera visibility and calibration
remain validation gates. The owner allows mapping, preloaded routes and camera use.

Context: speed and accuracy on a small self-intersecting marked course differ
from general point-to-point navigation. Pose-only tracking can drift relative
to the painted line, and shortest paths can skip required course segments.

Decision: prefer local line-relative camera feedback with wheel/ODIN1 motion
context and ordered segment progress. Keep the crossing topology explicit.

Consequences: local vision, calibration and route association are core components.
Prior route storage is allowed by the owner. Confirm the required crossing
sequence before authoring the course. Treat Nav2 as optional or a carefully
adapted controller backend; do not use a goal planner to redefine the race route.

Validation: independently measured line error and correct crossing order on
repeated low-speed runs before speed optimization.
