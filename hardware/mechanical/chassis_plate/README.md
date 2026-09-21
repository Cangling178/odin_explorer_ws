# Chassis dimensions and CAD provenance

English | [Chinese](README_cn.md)

This page records the final modeling inputs, replacing incremental descriptions that were superseded. Values supplied/approved by the owner are not independent measurements. Front is the passive-support side; `base_link` is the rear axle midpoint, x forward/y left/z up.

## CAD and conversion

Original SolidWorks and STEP files remain in this directory. STEP SHA-256: `3034a4fd0d791a35212bf166a0775f7630fcfa31570a78389df7a697e52937d8`.
Converted 2026-09-12 with Gmsh 4.15.2 / trimesh 5.1.0; mm to m, `(x,y,z)=(-CAD_z,CAD_x,CAD_y)`. Mesh origin is the horizontal bounding-box center and lowest z=0; bounds approximately 247.416×220×33.5 mm, 113696 triangles. Visual placement relative to the rear axle is `(0.103708,0,0.02875)` m.

The chassis STL is checked in and consumed directly by normal builds. One-time CAD conversion and standoff generation scripts have been removed from the current tree; restore the relevant tools from `tools/` at Git revision `508bf26` when changing CAD or regenerating base meshes. Conversion versions, units and coordinate conventions above remain the provenance record.

## Adopted geometry

| Item | Current input / provenance |
| --- | --- |
| Rear wheel diameter / width / spacing | 66.5 / 26 / 257 mm, owner supplied |
| Rear axle inward from plate rear edge | 20 mm, owner supplied |
| Horizontal plate bottom above ground | 62 mm, owner-selected modeling height |
| Front support ball diameter / assembly height | 15.875 / 20 mm, CY-15A product reference |
| Support housing | Diameter 27 mm, height 16 mm, simplified cylinder |
| Standoff hex width / length | 4.5 mm owner supplied / 42 mm derived as 62−20 |
| Same-side mounting-hole spacing | 38.3 mm from CAD; product reference is 40 mm |
| Front support centers in base_link | x=196.348442 mm, y=±103.111804 mm; centered between CAD holes |
| Front support center inward from front edge | 31.067560 mm, CAD-derived |

These replace early 18 mm ball diameter, 208 mm ball spacing, 23 mm front offset and 57 mm plate-height assumptions. Ground is at z=−33.25 mm relative to base_link; wheel centers are y=±128.5 mm. Four CAD hole axes: X=±103.111804 mm, Z=−135.498442/−97.198442 mm, along CAD Y, radius 2 mm. In base_link the mounting axes are x=215.498442/177.198442 mm, y=±103.111804 mm, plate underside z=28.75 mm.

The 40 vs 38.3 mm hole spacing differs by 1.7 mm (0.85 mm per side if centered); physical assembly is unverified. A 50 mm product flange length was supplied but flange width/thickness/hole diameter were not, so the flange remains omitted. The standoffs omit threads and nuts. Xacro scales the existing base mesh to the selected dimensions.

## Motors, brackets and mass

Reference: two MG513X GMR 500-line, 1:28 motors. Encoder counts per output revolution and electrical ratings remain unverified. Motor-cylinder axis is 35 mm ahead of the output axle at the same height. Owner-supplied reference dimensions: axial depth 45.5 mm, motor diameter 32.6 mm, encoder diameter 32.8 mm, gearbox envelope 64.5×38 mm, output shaft diameter/length 6/14.5 mm.

Approved appearance assumptions in `motor_assembly.xacro`: gearbox depth 10 mm, encoder cap 5 mm, cylinder 30.5 mm; gearbox-to-tire clearance 4 mm. L-bracket thickness 2 mm, length 64.3 mm, flange reach 20.7 mm, height 47.75 mm. Holes, fillets, shaft flats and hub details are omitted. Housings/brackets are fixed; the output shaft rotates with the wheel. These are not manufacturing drawings.

Reference masses: two motors 340 g, brackets 94 g, wheels/hubs 92 g, front support assemblies 71 g (35.5 g each, mean of 29/42 g product variants). With ODIN 280 g, the included subtotal is 877 g. Uniform boxes/cylinders estimate inertia; no separate output-shaft mass is added. Plate, standoffs and electronics remain uncounted. Only model geometry and inertia remain; contact worlds and simulated drive were removed. See [model scope](../../../src/odin_explorer/explorer_description/README.md). Hardware calibration is pending.
