# Round 4 Release Check: One Test-Integration Failure

All 400 final generation positions pass: 100 matched and 100 predeclared new-seed
positions per pack. Both matched JSONL files are byte-identical to round 3.
All 400 reproduce from frozen source in fresh isolated interpreters. The parent
read seeds 1000/1001 at both lengths in both packs; verbatim copies are in
`../SAMPLES.md`. The predeclared range was not sampled by workers before release.

The new seeds still expose narrow families: bakery has 94 postponed evenings
and 6 shared suppers (no surprise supper in these 100 positions); greenhouse
has 62 supervised trials, 24 separations and 14 joint-care endings. They have
69/49 exact texts and pooled XZ ratios 1.81%/1.78%. These are not 200 independent
plots. The originals remain stronger/less repetitive than repeated short draws.

## Full-Suite Result

Command: `.venv/bin/python -m unittest discover -s storyscenes -p 'test_*.py'`.
Result: **660 tests in 266.657 seconds, one failure**.

`mini_adventures.bakery.test_world.BakeryTests.test_successful_endings_keep_checks_without_audit_label_dialogue`
imports the helper through the absolute `storyscenes.*` name, while bakery's
world imports it relatively. Under discovery those are different module/class
identities. The `issubclass` assertion fails despite the adapter using the shared
implementation. Direct package tests do not reveal the mismatch.

## Round 5 Tasks

Bakery worker: fix only the inconsistent test import (or equally small correct
integration fix), keeping the meaningful delegation assertion. Run direct tests
and `unittest discover -s storyscenes -p 'test_world.py'`; do not weaken checks or
change generation. Preserve every prior artifact. Record the failure and fix.

Greenhouse worker: independently run those discovery-mode pack tests after the
fix is present, confirm your own import/delegation tests remain meaningful, and
report. No source edits needed unless you find an actual integration defect.

Parent: rerun the full suite, save a final bakery snapshot/recheck with the fixed
test source, and verify story bytes remain identical. This is a fifth integration
round, not another prompt/prose optimization or a resampled holdout.
