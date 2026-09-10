# Experiments

Copy `run.template.yaml` for each real run and fill all provenance fields. Keep
compact results in `results.csv`; store large evidence under ignored `data/` or
external storage with a hash and path reference. Log incomplete attempts too.

The `examples/` directory is synthetic and exists to exercise the offline tool.
It must not be included in measured robot results. A future bag-to-CSV adapter
must preserve invalid samples and associate the correct course segment.
