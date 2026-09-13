# Odin1 official CAD and mounting

English | [Chinese](README_cn.md)

- [Product overview](https://manifoldtechltd.github.io/wiki/odin_series/odin1/1.%20Product%20Overview_.html)
- [Installation and CAD download](https://manifoldtechltd.github.io/wiki/odin_series/odin1/3.%20Installation%20Guide_.html)
- [Specifications](https://manifoldtechltd.github.io/wiki/odin_series/odin1/14.%20Technical%20Specifications_.html)
- [Original STEP](https://manifoldtechltd.github.io/wiki/odin_series/odin1/assets/stp/Odin1.stp)
- STEP SHA-256: `92a28478dfcfd8896e287ceecfa283515399f2cff61f0d86ff662433d29ac11f`.

Original manufacturer STEP retained; mesh generated with tools/convert_odin_step.py
using Gmsh 4.15.2 and trimesh 5.1.0, converting mm to m. No new license is
asserted for manufacturer CAD; rights remain with the original owner.
Official main body: width 100, height 62, depth 43 mm; mass approx 280 g.
Drawing depth including connector: 45.8 mm. Downloaded CAD bounds: 100x62x46.4 mm;
preserved without forcing the model to match approximate published dimensions.

odin_link is the bottom mounting-hole group center, X forward/Y left/Z up.
Conversion in mm: (x,y,z)=(CAD_Z-20.4,-CAD_X,31-CAD_Y).
Not the driver's IMU/lidar/camera frame; internal TF and sensor simulation pending.
Front four holes interpreted as the central 84x30.3 mm group, not caster mounts:
CAD X=-41.742355/42.257645, Z=-140.688953/-110.388953 mm.
Adjacent plate top verified at CAD Y=3.5 mm. Direct flat mounting, facing forward,
center in base_link: (205.538953,0.257645,32.25) mm.
Official pattern 84.3x30.7 mm differs by 0.15 mm per lateral side and 0.20 mm
per longitudinal side when centered. Actual assembly fit is not established.
No unmeasured bracket is added; mounting height/pitch need hardware confirmation.

Official installation guidance requires unobstructed FOV and >=10 mm surrounding
cooling clearance, and strongly recommends the underside >0.2 m from objects.
This user-directed plate layout does not meet that raised-installation advice;
FOV, thermal and structural clearances remain unvalidated.
Mass 0.280 kg added; uniform main-body box estimates COM/inertia.
Assigned subtotal 0.877 kg, excluding plate, pillars and other electronics.
