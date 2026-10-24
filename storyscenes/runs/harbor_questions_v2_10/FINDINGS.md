# Questions before requests: readable scenes, small finite repertoire

## Result

The opt-in `harbor_questions` generator tests four practical requests: loading
stones, supplying picnic cups, delivering a parcel, and opening paper flags.
The recipient asks for an inspection. Actual evidence can confirm the request,
change the plan, or leave the question unresolved. Scene-sized dialogue and
closing images are authored around those transitions; no runtime LLM is used.

The fixed ten-story batch, seeds 10000-10009, received the unchanged paired
Terra/Luna Flex evaluation. Both judges saw all ten positions, including duplicates.
They saw prose and visible QA only, not hidden state or source code.

| Metric | Terra | Luna |
| --- | ---: | ---: |
| Storytelling / 9 | 7.50 | 8.00 |
| Overall / 9 | 8.00 | 8.00 |
| Diversity / 9 | 3 | 4 |
| QA overall / 9 | 8.967 | 8.817 |
| QA usable | 59/60 | 60/60 |

All six requests returned valid results, costing an estimated **$0.039282**.
The shared conservative commitment is now **$4.54227640 / $5**, including earlier
uncertain reservations. Remaining authorization is $0.45772360. No larger paid
batch was started after this weak diversity result; no additional budget was used.

## What the judges and manual reading agree on

The text reads as short stories, not event logs. Ari's assumptions create an
opening, Cy's questions supply friction, physical evidence changes what happens,
and a final object placement closes the scene. Dialogue can carry the causal
turn without narrating every bookkeeping event. These are hand-authored feasibility
results, not measured automatic authoring quality or cost.

The same improvement also exposes the template: every premise follows roughly
"Ari assumes; Cy asks; someone checks; they act." Both judges call this out.
Neither richer epistemic bookkeeping nor different props makes that structure
substantially different. Terra grouped the bow-opening story under confirmation
despite its note correctly describing a reversal; retain the grades, but do not
treat the judge's individual group labels as causal ground truth.

The paid ten contains no unresolved inspections. Its scores do not certify those
branches. Manual reading of the full prose families found another policy limit:
the fogged-bridge branch stops even though the setting offers a longer route.
It is legal under the authored policy, but poorly motivated. This is a
`premature_deferral` defect, not evidence that uncertainty requires abandoning a
goal. Future policies should separate an unknown shortcut from a known usable
alternative, with actual character knowledge guards.

## Scale and finite-space check

The local v2 ten/thirty/hundred use fresh seed ranges 10000, 11000 and 60000.
All batches retain source, worlds, traces, prose, QA and duplicate positions.

| Sample count | Exact texts | XZ / raw story bytes | Paid quality/diversity |
| --- | ---: | ---: | --- |
| 10 | 8 | 2,700 / 12,046 (22.41%) | Above |
| 30 | 18 | 3,564 / 35,062 (10.16%) | Not judged |
| 100 | 23 | 4,256 / 118,890 (3.58%) | Not judged |

The complete declared space has **32 configurations, 24 texts, 18 action paths**,
and zero JSON-replay failures. Both the scored v2 and locally corrected v4 have
this ceiling. Audits are in `../harbor_iteration_campaign/questions_space_v2.json`
and `questions_space_v4.json`. These are four authored premise families with
Boolean branches, not a general story planner. More samples cannot create more
than 24 exact texts without changing this generator.

The final local hundred has 653 paragraph positions but only 66 exact paragraphs;
90.83% of word positions are repeats beyond each paragraph's first occurrence.
XZ is a redundancy diagnostic, not a calibrated semantic diversity score.

## Corrections and version boundaries

- v1 is an unjudged preview. Its uncertainty sampler accidentally correlated
  with two problem types. v2 makes readability an independent seeded draw.
  Therefore v1/v2 are not a matched-trace prose-only comparison.
- Before grading v2, remove unsupported implications that an unknown box was a
  proven mistake or that the missing cups definitely existed elsewhere. Keep
  inspection distinct from the subsequent report and acknowledgement.
- v3 is an unjudged, matched local repair: remove premature conversation in the
  unknown-box inspection and replace "parcel or crate" with the actual noun in QA.
- Terra rejected one v2 answer because "Ari ... after finding a bow" implies
  Ari inspected it, while Cy did. v4 explicitly names the inspector. This fixes
  ambiguity without inventing a second inspection. Corrected QA is not regraded.
- Luna questioned whether agreement and subsequent performance justified saying
  Cy accepted the request. This is less decisive: acceptance is enacted and Cy
  visibly performs it. Preserve the disagreement instead of auto-editing from it.

The v4 batches preserve all 140 v2 conditions and traces. Story changes are zero
in ten, one in thirty, three in a hundred; QA-set changes are one, six and nineteen.
The intermediate v3 batches remain intact. The ten's story texts are identical
to the scored v2, but do not transfer its QA score to the corrected answer.
See `../harbor_questions_v4_100_local/matched_v2_checks.json`.
Frozen v4 runtime, imported outside the checkout, reproduced all 100 stories,
QA sets and trace hashes. Full condition tests include hidden-truth invariance,
real communication before belief revision, physical completion after acceptance,
blocked-bridge legality, inspector attribution and reader-mask abstention.
The final full StoryScenes suite passes **522 tests**. AST/whitespace checks
also pass for the touched Python files. The trade-off example CLI now accepts
the documented `--qa` flag; its default JSON output is unchanged.

## Next gate

Keep this as a small canonical prose example, not a dataset multiplier or a
replacement for the better-diversity harbor baseline. The next experiment must
compose reusable scene moves into held-out causal combinations. It must show
different conflicts and resolutions, not just more observations, reports or
synonyms. Preserve the readable scene layer while testing those combinations.
Run a finite-space and paragraph-reuse audit before buying another larger judge
batch. This diversity gate remains open.

```bash
./.venv/bin/python -m storyscenes.harbor_questions_story --seed 10003 --qa
./.venv/bin/python -m unittest discover -s storyscenes -p 'test_harbor_questions.py'
./.venv/bin/python storyscenes/replication_space_audit.py --scope harbor-questions --out /tmp/NEW_questions_audit.json
```
