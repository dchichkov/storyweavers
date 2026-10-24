# Persistent resource trade-offs: readable, still repetitive

This is a separate opt-in generator, not a replacement for the scored harbor
baseline. The same executor and bounded goal methods now face continuous
resource constraints: a rope may have to keep holding the tub cover up, and
the lantern may have to remain beside the floating boat. Ari's declared
priorities select compatible final goals. Giving up a goal has a physical
consequence: a flat chart, a dark window, or a boat resting in a dry cradle.
Clips and board clamps can remove the rope conflict when the requested
display location permits them.

## Paid Ten-Story Test

Seeds 8000-8009 were declared before generation. Neither exact duplicates nor
low-scoring stories were replaced. Both judges saw the same ten stories in
one request and the same 60 sampled single-turn QA conversations in two
five-story requests. Rubrics, output limits, reasoning=none, store=false and
Flex remained unchanged. Source, requests, responses and grades are preserved.

| Metric, out of 9 unless noted | Terra | Luna |
| --- | ---: | ---: |
| Storytelling | 7.8 | 7.9 |
| Story overall | 7.8 | 8.0 |
| Diversity overall | 3 | 4 |
| Premise diversity | 2 | 3 |
| Causal-path diversity | 4 | 4 |
| Ending diversity | 4 | 4 |
| Language diversity | 3 | 3 |
| QA overall | 8.40 | 8.25 |
| QA usable | 51/60 | 48/60 |

All six API requests returned valid results. Estimated returned-usage cost:
**$0.04574855**. Combined conservative commitment, including prior uncertain
reservations, is now **$4.50299440 / $5**, leaving **$0.49700560**. Estimated
priced returned usage is $2.90185240; $1.601142 remains reserved for earlier
outcomes. The budget extension was not approved or applied. No larger paid
run of this version was dispatched after its weak ten-story diversity result.

## Local Scale Check

| Preserved batch | Seeds | Returned | Exact texts | XZ bytes | XZ/raw | XZ bytes/story |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| This ten | 8000-8009 | 10 | 10 | 2,212 | 12.01% | 221.20 |
| `../harbor_tradeoffs_v1_30_local` | 9000-9029 | 30 | 22 | 2,844 | 5.02% | 94.80 |
| `../harbor_tradeoffs_v1_100_local` | 50000-50099 | 100 | 70 | 4,124 | 2.16% | 41.24 |

Every sampled world passed exact replay after JSON serialization. Thirty and
hundred have no paid scores. The hundred contains 59 all-success cases, 16 dry
boats, 13 flat charts with the requested lamp placement, 10 upright charts
without their requested window light, and 2 cases giving up both chart goals
for the boat. These are physical outcome categories, not five independent
premises or a semantic diversity estimate.

Across the hundred, 828 paragraph positions use just 46 exact paragraphs.
Counting each paragraph once removes 94.28% of word positions. The delivery
and launch exchanges each occur verbatim 84 times. More exact whole-story
strings mainly come from combining and reordering the same small inventory.

A matched local control uses the same hundred seeds and common condition
values in the all-success composition generator: 39 exact texts and 3,020 XZ
bytes from 187,349 raw bytes, versus 70 texts and 4,124 XZ bytes here. The
comparison and per-seed trace hashes are saved in
`../harbor_tradeoffs_v1_100_local/matched_composition_diagnostic.json`.
This establishes additional physical outcome variation, not higher judged
diversity; neither matched hundred has paid grades.

The complete declared v1 grid is saved in
`../harbor_iteration_campaign/tradeoff_space_v1.json`: **2,304 configurations,
2,304 exact serialized replays, 154 exact texts, 75 action paths, five physical
outcomes, no failures**. Maximum author-side action-search attempts: 91 of
the 1,600 bound. Its generator/planner/prose hashes match this batch's frozen
runtime. These are v1 counts, not a newly audited v3 upper bound. The audit
also has an explicit failure-retention test; failed configurations are not
silently discarded or counted as successfully replayed.

## Manual Review And QA

All ten scored stories were read, alongside fresh thirty/hundred cases showing
dry boats, flat charts, dark windows and a chart moved to the jetty board.
The visible ending images and dialogue are stronger than an interaction log.
Different priorities genuinely change what is done, not just an outcome label.
But characters announce a choice almost immediately and then execute it; the
premise and most exchanges stay fixed. There is little discovery, negotiation,
or change of mind. This matches the judges' low diversity verdict.

Reading all 46 distinct paragraphs of the hundred also exposed an inherited
temporal assumption: after returning the lantern, the prose waits for the
chart to "return" even when it had not previously hung there. This affects
four hundred-story positions: three permanently defer hanging the chart and
one hangs it for the first time later. A related first-visit error calls the
lantern's arrival at the window a return. These defects were not present in
the ten paid story texts. The larger sets were unjudged, so this is a manual
continuity finding, not evidence that those judges missed these exact cases.

The QA complaints are partly valid. Answers introduced an electric bulb that
the prose never names, and stated a weight limit that is in the simulation
but only implicit in the visible delivery paragraph. Reader-facing answers
must not rely on those hidden details. Preserve these original grades when
narrowing the answers in a new local snapshot.

The corrections are now preserved as matched `harbor_tradeoffs_v3_10_local`,
`harbor_tradeoffs_v3_30_local`, and `harbor_tradeoffs_v3_100_local` batches.
All 140 serialized traces match v1. Ten story texts match; the thirty changes
only seed 9011; the hundred changes 50017, 50037, 50057, 50066 and 50068.
All QA sets change, and the opening's persistent-light statement now explicitly
anchors its darkness premise. No new paid grading was performed. The
intermediate v2 snapshots are also retained, including their incomplete
first-visit wording fix. See the [local repair record](../harbor_tradeoffs_v3_100_local/LOCAL_REPAIR.md).

Keep false rejections separate: Luna denies that the window light was planned
in seed 8006 even though the opening explicitly states that intention. It also
rejects describing a clipped upright chart as hanging in seed 8003. Do not
rewrite correct events to satisfy these judgments or silently remove them
from the reported QA denominator.

## What This Establishes

Persistent resource costs can produce complete, readable stories without a
runtime LLM. They do not by themselves solve corpus diversity. The exclusions
and goal priorities are authored for this bounded setting, not general
impossibility reasoning, autonomous character knowledge, or a physics engine.
Planner backtracking is author-side search; rejected search branches are not
narrated as actions the characters performed.

The next substantive experiment should change motives, information and
character responses, with enacted observations or refusals changing later
choices. It should not just add another rope allocation or synonym bank.
Keep the same prose/QA separation, reader-visible grounding, saved-world
replay and small-set diversity gate before paying for a larger evaluation.

## Reproduce

```bash
./.venv/bin/python -m storyscenes.harbor_tradeoffs_story --seed 8009 --qa
./.venv/bin/python storyscenes/harbor_trial.py prepare --world harbor_tradeoffs --count 10 --seed 8000 --out storyscenes/runs/NEW_BATCH
./.venv/bin/python storyscenes/replication_space_audit.py --scope harbor-tradeoffs --out storyscenes/runs/NEW_SPACE_AUDIT.json
```

Use the batch's `_source` runtime to reproduce the graded version exactly
after later code changes. Never overwrite the original samples or re-use
unknown paid requests.
