# Documentation map

| Document | Purpose |
| --- | --- |
| [Requirements](01_requirements.md) | Confirmed scope, unknown rules and acceptance |
| [Architecture](02_architecture.md) | Responsibilities, compute boundaries and TF ownership |
| [Hardware](03_hardware.md) | Chassis identification, power and controller choices |
| [ODIN1 integration](04_odin1_integration.md) | Vendor isolation, timing and visibility evidence |
| [Course strategy](05_course_strategy.md) | Line perception, crossings and speed/accuracy tradeoffs |
| [Interfaces](06_interfaces.md) | Proposed topic contracts and state semantics |
| [Development](07_development.md) | Build, preview, validation and dependencies |
| [Evaluation](08_evaluation.md) | Independent measurement and repeatable comparisons |
| [Bringup](09_bringup.md) | Staged integration and troubleshooting |
| [Calibration](10_calibration.md) | Wheel, camera, timing and frame procedures |
| [Repository guide](11_repository_guide.md) | Ownership, configuration and artifact policy |
| [References](REFERENCES.md) | Primary sources checked on 2026-09-10 |
| [Architecture decisions](adr/README.md) | Reasons for durable design choices |

Project status lives in `management/`; measured hardware facts live in
`hardware/`; experiment evidence lives in `experiments/`. Use links instead of
maintaining conflicting copies of the same parameter.
