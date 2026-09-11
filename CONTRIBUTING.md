# Contributing locally

English | [Chinese](CONTRIBUTING_cn.md)

Keep English documentation and provide sibling `_cn.md` Chinese translations for Markdown documents.
Use English for identifiers, code comments and commit messages. Update both language
versions when technical requirements change.
Keep changes tied to a requirement/backlog item and explain behavior and evidence.
Keep `main` usable; make focused branches with descriptive names.

Before completing a change, run the structural checker, relevant offline tests
and the ROS build when package assets change. Add behavioral regression tests
for parsers, geometry, crossing association and stop conditions as implemented.
Do not add tests that merely assert a copied placeholder value.

Record measured values with units and provenance. Keep templates unfilled until
measured and separate them from runtime parameters. Never label a scaffold,
synthetic dataset or simulation result as physical robot performance.

Use the PR template as a local review checklist even without a remote. External
dependencies require a recorded revision, license and integration evidence.
