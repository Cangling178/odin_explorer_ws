# ADR-0001: Platform baseline

English | [Chinese](0001_platform_cn.md)

Status: proposed, 2026-09-10.

Context: the target is Jetson Orin Nano with a version-sensitive ODIN1 driver.
The current vendor README favors Humble/Ubuntu 22.04. The development host has
a Humble installation, but this does not establish the target Jetson image.

Decision: use Humble as the foundation build target and evaluate a compatible
JetPack 6.x/Ubuntu 22.04 target. Do not flash the Jetson or claim a driver lock.

Consequences: verify vendor ARM64 artifacts, firmware and CUDA/OpenCV compatibility
together. Newer ROS/JetPack releases remain an option only after vendor testing.
Before a longer-term deployment, review distribution support lifetime and upgrade
effort. Freeze exact revisions after the hardware smoke test, not from search snippets.

Validation: target inventory, vendor underlay build and timestamped sensor capture.
