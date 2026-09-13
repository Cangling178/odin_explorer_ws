# Chassis CAD and preview mesh

English | [Chinese](README_cn.md)

This directory retains the user-supplied SolidWorks and STEP originals.
The user identified the ball-transfer end as the front (left in the supplied top photo).

- STEP SHA-256: `3034a4fd0d791a35212bf166a0775f7630fcfa31570a78389df7a697e52937d8`.
- Conversion: 2026-09-12, Gmsh 4.15.2 and trimesh 5.1.0.
- STEP millimetres become STL metres; no additional URDF scaling.
- Preview axes: `(x, y, z) = (-CAD_z, CAD_x, CAD_y)`, right-handed.
- Origin: horizontal bounding-box center, lowest surface at Z=0.
- Bounds size: approximately 247.416 x 220 x 33.5 mm; 113696 triangles.
- Export checked for watertightness and consistent winding.
- Preview placement relative to the rear axle: `xyz=0.103708 0 0.02875 m`, derived from user dimensions below.

Output: `src/odin_racer/racer_description/meshes/chassis_plate.stl`.
Rebuild with `tools/convert_chassis_step.py INPUT.STEP OUTPUT.stl` using the
versions above in a separate Python environment. These tools are not required
for normal ROS builds; the exported mesh is included.

Mass, inertia, collision, motor and contact models are pending. Wheels are dimensioned cylinders; Odin placeholder is removed. This is a visual preview, not dynamics.

## Confirmed chassis dimensions

User-provided dimensions in mm: wheel diameter 66.5, width 26, track 257;
rear axle 20 inward from rear edge; ball diameter 18, track 208, front inset 23.
Both pairs are symmetric about the centerline.
A level plate bottom at 62 mm above ground is a user-selected modeling value,
replacing the earlier 57 mm ball assembly height, not a new measurement.
Edge offsets refer to longitudinal CAD bounding-box extremes.

The rear axle center is base_link: X forward, Y left, Z up.
Derived positions in metres: plate bottom Z=0.02875; wheel Y=+/-0.1285;
ball XYZ=(0.204416, +/-0.104, -0.02425); ground Z=-0.03325.
Balls and wheels have equal lowest points. Existing caster link names are
retained, but these are fixed visual balls, not swivel joints or contact models.
Pillars, housings and motors are omitted because dimensions are unknown.
Odin is omitted pending actual geometry and mounting.

## Standoff mounting holes and revised ball centers

STEP cylindrical axes: CAD X=+/-103.111804301857 mm,
CAD Z=-135.498442220721 / -97.198442220721 mm, along CAD Y;
hole radius 2 mm. The axial location is not the mounting-surface height.
Hole spacing per side is 38.3 mm; left/right spacing is 206.223608603714 mm.
Per user instruction, ball centers use the pair midpoints (assembly assumption,
not a ball geometry extracted from CAD). Front inset becomes 31.067559623974 mm
instead of the earlier hand-measured 23 mm; track replaces 208 mm.
Mount axes in base_link, mm: X=215.498442220721 / 177.198442220721,
Y=+/-103.111804301857, Z=28.75. Ball X becomes 196.348442220721 mm.
Four empty mount frames are added; ground contact height is unchanged.
Standoff solids await measured length and diameter or hex across-flats width.
The 4 mm holes do not establish standoff width or length.

## CY-15A product-based preview (supersedes earlier ball/standoff status)

User authorized the supplied product drawing: ball diameter 15.875 mm,
assembly height 20 mm, housing height 16 mm, upper diameter 27 mm,
hole spacing 40 mm, flange length 50 mm. User confirmed standoff hex
across-flats width 4.5 mm. Effective length is derived as 62-20=42 mm,
not independently measured.
Ball XY remains at the original CAD pair midpoint; ground contact is unchanged.
Per latest user instruction, use CAD spacing 38.3 mm so all four standoff
axes coincide with the plate holes. Product spacing 40 mm is retained only
as a discrepancy: 1.7 mm total, 0.85 mm per side when centered. The plate CAD
is unchanged; physical compatibility with a 40 mm flange is not claimed.
Hex bodies omit threads, nuts and seams. Housing is a simplified cylinder
(27 mm diameter, 16 mm height), not an exact pressed shell. Flange width,
thickness and hole diameter are unspecified, so the 50 mm flange is omitted;
visible gaps remain between pillars and the housing. No mass/material assumed.
Regenerate unit hex mesh with `python3 tools/generate_standoff_mesh.py`.

## MG513X GMR simplified assemblies

Confirmed: two GMR 500-line 1:28 motors; motor axes 35 mm forward of wheel
axes at the same height, symmetric installation. Wheel geometry is unchanged.
User-supplied reference dimensions (not independently verified): total depth
45.5 mm, can diameter 32.6 mm, encoder diameter 32.8 mm, gearbox envelope
64.5 x 38 mm, shaft diameter 6 mm and extension 14.5 mm.

User-authorized visual assumptions in motor_assembly.xacro: gearbox depth
10 mm, encoder cover 5 mm, remaining can depth 30.5 mm; wheel inner face to
gearbox outer face gap 4 mm. Rectangular gearbox centered between the axes.
Inferred L bracket: thickness 2 mm, length 64.3 mm, flange reach 20.7 mm;
height 47.75 mm derived to reach the plate, not a manufacturer measurement.
Bolt holes, fillets, D flat and wheel hub details omitted.
Housings/brackets are fixed to the body; shafts follow the wheel joints.
Mirrored inward-facing cans. Bracket flange tops meet the plate bottom.
Visual-only, not manufacturing/collision geometry; no inferred mass/inertia.

## Adopted partial mass and estimated inertia (current)

User adopted catalog references and requested ignoring extra fasteners:
2 motor assemblies at 170 g (340 g), 2 brackets at 47 g (94 g),
2 tire/hub assemblies at 46 g (92 g). Total assigned mass: 526 g, NOT vehicle mass.
These values are not scale measurements. They are now in the link inertials.
Motor assembly mass includes gearbox, encoder and shaft, lumped into the fixed
motor link; shaft mass is not counted twice. Internal rotating inertia omitted.
Motor/bracket COM and inertia use uniform bounding-box approximations;
wheels use uniform solid cylinders with their axes along Y. Not measured data.
This supersedes earlier statements that no inertials exist. Plate, pillars,
ball assemblies and electronics remain unassigned. Product ball masses 29/42 g
refer to different variants; actual variant unconfirmed, neither is adopted.
Complete vehicle inertials, collisions and control remain pending.

## Ball-transfer assembly mass estimate update

User selected the mean of product variants: (29+42)/2=35.5 g per assembly,
71 g for both. Includes ball, housing and flange; excludes standoffs.
This is not a measurement. Mass is assigned once to each caster link.
COM/inertia approximate a uniform cylinder of diameter 27 mm and height 20 mm,
not the actual rotating ball inertia. Assigned total changes from 526 g to
597 g, still not complete vehicle mass. Plate, standoffs and electronics
remain unassigned; additional fasteners are ignored by user instruction.
