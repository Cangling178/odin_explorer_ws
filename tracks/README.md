# Course assets

`reference/` holds the supplied image and annotation provenance. `competition/`
holds an unfilled survey/route specification and a CSV header for measured
samples. No line coordinates or branch order are inferred as ground truth.

Keep a course revision and hash with each run. Store ordered metric centerline
samples with segment ID and cumulative distance. A self-intersection can contain
identical x/y positions belonging to different route visits. Never sort samples
by x or by global nearest neighbor to construct the traversal sequence.
