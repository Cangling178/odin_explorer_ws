# Repository and configuration guide

English | [Chinese](11_repository_guide_cn.md)

## Ownership

First-party package source belongs in `src/odin_racer/`. Each package owns its
runtime configuration and launch assets when implemented. Hardware facts live
in `hardware/`; course facts live in `tracks/`; experiment-specific snapshots
live in `experiments/`. Generated maps and large captures live in ignored `data/`.

Vendor source belongs in the separate ignored `vendor_ws/src/` underlay. Use a
fixed commit and record any patches when integrating. Do not copy vendor SDK
binaries into first-party packages or lose upstream license notices.

## Template versus runtime configuration

`*.template.yaml` files are human-reviewed specification forms. They contain
`null` values and descriptive keys, and are never passed to a live ROS node.
When implementing a component, create a versioned validated runtime file with
the real node's parameter schema. Explicitly document the conversion from the
hardware/course records and validate required fields before launch.

Avoid duplicated tuning constants. A robot variant selects geometry and device
bindings; a course revision selects route geometry; an experiment selects a
controller profile. Record all three in the run manifest.

## Data policy

Keep small summaries, text configuration and synthetic fixtures in Git.
Do not commit bags, raw video, point clouds, device SDK binaries or credentials.
For external captures, record a relative storage reference, content hash, size,
capture context and retention note. The user-supplied course JPEG is the one
small reference image included in this initial local repository; its ownership
is not changed by inclusion.

## Documentation languages

Keep the English originals and provide `<original_stem>_cn.md` translations in the
same directory. Link each language pair in both directions; Chinese pages link to
Chinese counterparts where available. Preserve commands, identifiers and configuration
keys. Update both versions when technical meaning changes to avoid diverging
requirements or implementation status.

## Change completion

A change is complete when behavior and interfaces are documented, relevant
checks pass, requirements have evidence, and status is accurate. A package
building successfully does not mean its future subsystem has been implemented.
Record known limitations with a backlog ID rather than hidden TODO values.
