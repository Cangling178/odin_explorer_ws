# ADR-0003: Workspace and dependency boundaries

English | [Chinese](0003_workspace_boundaries_cn.md)

Status: accepted for foundation, 2026-09-10.

Context: hardware, perception, control and experiments evolve together, while
the vendor has its own build assumptions and release/firmware coupling.

Decision: keep first-party assets in one colcon/Git workspace. Isolate ODIN1
source in `vendor_ws/src/odin_ros_driver`, excluded from root package discovery.
Use responsibility-based package names and a single source for measured facts.

Consequences: explicit underlay sourcing and version records are required.
The initial packages can install documentation/templates without pretending to
contain working drivers. Large data is kept out of Git. No remote is required.

Validation: clean package discovery and build; no vendor artifacts tracked;
all documentation and small evaluation fixtures remain locally reviewable.
