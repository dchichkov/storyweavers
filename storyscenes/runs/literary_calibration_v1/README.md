# Literary Calibration Diagnostic

The user rejected two randomly displayed harbor stories despite seven-level
historical judge averages. This separate diagnostic asks whether the existing
judges distinguish those texts from specific older examples. It does not alter
the historical rubric or establish a new numeric acceptance threshold.

## Selection And Protocol

- Two exact criticized outputs: v9 `harbor_questions:63024` and v11
  `harbor_questions:63041`. Neither inherits a ten-story average as its own grade.
- One first draw each from `storyscripts/discovery.py`, `gift.py`, and
  `apology.py`, resetting seed 20261023 before each draw. No quality filtering.
- One position each from the saved Puddles and Nell judge-input sets, selected
  uniformly with seed 20261023. Both happen to have source index 276. These are
  saved September versions, not a claim about every current canonical output.
- The original race-story calibration anchor, now presented without its rating.
- Two explicitly artificial diagnostics: a compressed event-log version of the
  discovery story, and Puddles with a contradictory ending appended. Neither is
  an estimate of how often a generator fails.

Ten texts, eight fixed pairs, two orders and two models: 32 requests, all on
Flex, reasoning none, store false. The model receives only story A and story B,
not source paths, author labels, traces, QA, grades or presumed winners. It
chooses A/B/tie, separately accepts or rejects each story as reading material,
and provides short evidence. Both may be unacceptable. No numerical score is
requested. The texts have different lengths and genres; those are confounds,
not controlled away merely by instructing the judge to ignore length alone.

The [blind worksheet](BLIND_REVIEW.md) hides source labels. A reader who has
already seen a story may recognize it, so this is not full human blinding.
`provenance.json` records the exact origins and hashes. `human_labels.json`
remains entirely null: **no human pairwise rankings have been invented**.

This follows the general guidance to compare outputs, check order effects and
validate automated judgments against human labels in the
[official OpenAI evaluation guidance](https://developers.openai.com/api/docs/guides/evaluation-best-practices).
That guidance does not validate this particular rubric or these judgments.

## Results

Use `revalidated_quotes_v2/comparison.json`, together with the original raw
responses and the validation explanation below.

| Pair | Left | Right | Terra, both orders | Luna, both orders |
| --- | --- | --- | --- | --- |
| p00 | Empty crate | Discovery | Discovery | Changes with order |
| p01 | Paint box | Gift | Changes with order | Changes with order |
| p02 | Empty crate | Apology | Changes with order | Empty crate |
| p03 | Paint box | Puddles | Puddles | Puddles |
| p04 | Empty crate | Nell | Nell | Nell |
| p05 | Paint box | Historical race anchor | Race | Changes with order |
| p06 | Discovery | Event-log control | Changes with order | Event-log control |
| p07 | Puddles | Contradictory Puddles | Puddles in one valid order; other invalid | Puddles |

Puddles beats the paint-box story in all four presentations; Nell beats the
empty-crate story in all four. In those comparisons the references are accepted
and the harbor examples rejected. Across all comparisons, each criticized
harbor story is rejected in **12/12** valid judgments. This is useful evidence
that the old averages were too reassuring for these particular texts.

However, Terra is order-consistent on only **4/7 complete pairs**, and Luna on
**5/8**. In all six inconsistent model-pair cases, the model chooses **A in both
orders**, changing the identity of the winner. This is evidence of order
sensitivity, not a reason to choose whichever orientation supports our view.
Acceptance itself also changes in some contexts. There are no human pair
labels, so the harness correctly reports **uncalibrated**.

The event-log control is deliberately not assigned a presumed gold preference.
The original discovery includes an awkward adjective pair and an ill-fitting
sharing moral; a concise factual account can reasonably beat poor ornament.
The reference StoryScripts also contain repeated sentences, generic repair
actions and awkward motivations. Do not use this set to claim either entire
system is superior. Do not equate making the rubric harsher with calibrating it.

Both the comparison context and instructions changed from the historical judge.
This experiment does not isolate the race anchor as the cause of high scores.
The useful next writing test is an earned resolution of a meaningful initial
want, not another average over physically complete actions. In the paint story,
integrate Bo's key with obtaining the missing cups through enacted state changes,
then inspect the resulting story and QA before any larger paid run. This is a
next intervention, not an implemented fix or a promised quality gain.

## Validation Repair

All 32 API responses returned with known usage. The initial validator rejected
all because it treated presentation quotation marks as part of the excerpt.
Of the 64 evidence fields, two were exact substrings and 61 were exact
substrings enclosed in one matching pair of quotation marks. One Terra field
instead combined two quotations with commentary.

The corrected validator permits removing one enclosing quote pair, then still
requires an exact substring of the specified story. It does not normalize
paraphrases, remove internal words or accept fabricated evidence. Offline
revalidation recovers **31/32** assessments. The remaining Terra `p07_reverse`
response stays invalid; its preference is not counted in a complete pair.
Original results, requests, raw responses and frozen sources are unchanged.
The revalidation directory includes its own code snapshot and records original
result and raw-response hashes plus verified excerpts. No paid retry occurred.

Nine focused tests cover blinding, order mapping, order-dependent preferences,
missing results, human-label handling, exact evidence, quote wrappers, frozen
input/request tampering, deterministic sampling and no-API revalidation.
The full 580-test suite passed before the final quote-wrapper correction; all
nine focused tests pass after it. No generator or shared capability law changed.

## Cost And Reproduction

Actual returned-usage estimate: **$0.028596575** for 29,636 input and 3,889 output
tokens, not an invoice. Revalidation costs $0. The existing shared campaign now
has **$4.859883375 / $10** conservatively committed, including $1.601142 in
unchanged unknown-request reserves. Remaining headroom is $5.140116625.
No paid request is still running at this checkpoint.

```bash
./.venv/bin/python -m unittest discover -s storyscenes -p 'test_literary_calibration.py'
# Offline preparation for a NEW diagnostic, not permission to dispatch it:
./.venv/bin/python storyscenes/literary_calibration.py prepare --out storyscenes/runs/NEW_CALIBRATION
```

The original batch loads successfully from its frozen source outside the repo.
The working source now intentionally differs because validation was repaired.
Do not rerun paid judging to repair validation. The completed offline command
was `literary_calibration.py revalidate --out storyscenes/runs/literary_calibration_v1`;
it refuses to overwrite its existing output. Future requests still check the
shared campaign authorization, hash-locked inputs and the source manifest.
