# Experiments

English | [Chinese](README_cn.md)

Copy `run.template.yaml` for each real run and fill all provenance fields. Keep
compact results in `results.csv`; store large evidence under ignored `data/` or
external storage with a hash and path reference. Log incomplete attempts too.

The `examples/` directory is synthetic and exists to exercise the offline tool.
It must not be included in measured robot results. A future bag-to-CSV adapter
must preserve invalid samples and associate the correct course segment.

`run.template.yaml` is the full experiment record form. The evaluator accepts JSON for `--metadata`; do not pass this YAML file directly. Use [synthetic_run.json](examples/synthetic_run.json) as the shape for the run JSON metadata. Required fields and metric definitions are in [Evaluation](../docs/08_evaluation.md).
