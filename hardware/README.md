# Hardware records

Start with `bom.csv` and `robot_spec.template.yaml`. The rear differential-drive layout and F4 lower-level controller are confirmed;
identify motor, encoder and exact board specifications before selecting a driver. `platform_lock.template.yaml` records
the future software/firmware baseline. Use `calibration/` for measured revisions,
`electrical/` for wiring and power records, and `mechanical/` for dimensions/mounts.
All unknown fields are intentional; none is a default suitable for actuation.
