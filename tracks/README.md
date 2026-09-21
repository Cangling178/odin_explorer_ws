# Course sources and route data

English | [Chinese](README_cn.md)

[course_reference.jpg](reference/course_reference.jpg) is the owner's original attachment dated 2026-09-10; ownership is unchanged. It labels an outer field of 200×150 cm and a red reference span of 161×120 cm. It does not establish official start/direction, crossing order, line width or scoring tolerances.

| Data | Meaning |
| --- | --- |
| [reference_reconstruction.yaml](competition/reference_reconstruction.yaml) | Image crop/extraction and original resource scale |
| [course.template.yaml](competition/course.template.yaml), [centerline.template.csv](competition/centerline.template.csv) | Unfilled physical survey and ordered-route records |
| [Generated simulation route](../src/odin_racer/racer_control/config/competition_lap.csv), [metadata](../src/odin_racer/racer_control/config/competition_lap.json) | Image-derived ordered lap for the selected 4×3 m simulation |

Original extracted PNG/DAE resources represent 2×1.5 m; the runtime course defaults to scale 2 (4×3 m) and approximately 21.2 mm line width, independently controlled. The lap generator uses explicit image anchors and a fixed 4×3 m conversion. Changing generic course scale does not automatically regenerate the lap route.

[Course generation and verification](../simulation/COMPETITION_COURSE.md) explains texture coordinates and resource provenance; [lap operation](../simulation/COMPETITION_LAP.md) explains selected traversal order. These are simulation inputs, not surveyed truth or the official competition route. Store measured samples in meters with ordered segment IDs/progress and retain distinct visits at crossings. Record route version/hash in every experiment.
