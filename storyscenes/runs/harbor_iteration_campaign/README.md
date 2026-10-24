# Harbor storytelling experiment

One hand-authored harbor generator, offline capability execution, scene-sized
English realization and paragraph-grounded QA. This is a feasibility experiment,
not an automated authoring-cost benchmark or a production training corpus.

## Progress

All scores are on the unchanged 0-9 story-set rubric. Terra is gpt-5.6-terra;
Luna is gpt-6-luna; both Flex, reasoning none, store=false. Each judge receives
stories only for story/diversity grading, and stories plus visible questions and
answers for QA. Hidden traces and source code are not sent.

| Batch | N | Change | Storytelling Terra / Luna | Diversity Terra / Luna | Returned-usage USD |
| --- | ---: | --- | ---: | ---: | ---: |
| v1 | 10 | First authored boat story | Not judged | Not judged | 0 |
| v2 | 10 | Correct actual detour narration | 7.1 / 7.1 | 3 / 3 | 0.040466 |
| v3 | 10 | Shallow water; less explanatory prose | Not judged: JSON replay defect | Not judged | 0 |
| v4 | 10 | Typed query decoding; saved-world replay gate | 7.8 / 7.8 | 3 / 3 | 0.041106 |
| v5 | 10 | Add carrying and display-loan purposes | 7.3 / 7.0 | 5 / 3 | 0.038886, two unknown QA calls |
| v6 | 10 | Parcel mistake; enacted play-harbor ending | Local preview only | Not judged | 0 |
| v7 | 10 | Same generator; hard request deadline | 7.6 / 7.9 | 4 / 5 | 0.039901 |
| v8 | 10 | Whole-scene wording variants, same ten traces | 7.3 / 7.7 | 5 / 5 | 0.040982 |
| v8_30 | 30 | Unchanged generator, fresh seeds 1000-1029 | Invalid Terra partition / 7.133 | Invalid Terra partition / 5 | 0.114721 |
| v8_30_judge_v2 | 30 | Same stories; per-story plot membership; no repeated QA | 6.800 / 6.867 | 5 / 4 | 0.026141 |
| v9_10 | 10 | Delivery opens real launch tub; chart alternative; visible lantern light | 7.6 / 8.1 | 5 / 6 | 0.040483 |
| v9_30 | 30 | Unchanged v9 generator; new seeds 2000-2029 | 7.933 / 8.000 | 5 / 3 | 0.116954 |
| greenhouse_v1_10 | 10 | New plant-care mechanics and scene writing | 7.8 / 7.8 | 4 / 4 | 0.038640 |
| greenhouse_v2_30 | 30 | Fresh seeds 1000-1029; two narrower QA phrases | 8.733 / 7.900 | 4 / 3 | 0.109655 |
| theater_v2_10 | 10 | New stage problems; source-backed scene writing | 7.8 / 8.0 | 4 / 4 | 0.038314 |
| theater_v2_30 | 30 | Same generator; fresh seeds 1000-1029 | 7.833 / 8.000 | 4 / 4 | 0.109057 |
| harbor_v9_100 | 100 | Fresh seeds 10000-10099; all story positions graded | 7.790 / 7.780 | 5 / 5 | 0.358857 returned, five unpriced QA requests |
| greenhouse_v2_100 | 100 | Fresh seeds 10000-10099; all story positions graded | 7.940 / 7.940 | 4 / 3 | 0.354977 returned, one unpriced QA request |
| theater_v2_100 | 100 | Fresh seeds 10000-10099; all calls validated | 7.730 / 7.890 | 3 / 4 | 0.351813 |
| pooled_v1 | 90 | Thirty positions from each hundred, cross-script scope | 7.900 / 7.956 | 4 / 6 | 0.067531 |
| v10_10 | 10 | Shared rope couples display, carrying and launch goals | 7.900 / 8.000 | 5 / 6 | 0.040699 |
| v10_30 | 30 | Fresh seeds 3000-3029; manual review before judging | Not judged: two prose details corrected | Not judged | 0 |
| v11_30 | 30 | Same thirty traces; one text corrected | 7.900 / 7.900 | 5 / 5 | 0.115954 |
| v11_100 | 100 | Fresh seeds 20000-20099; same five-purpose sampler | 7.820 / 7.960 | 5 / 4 | 0.379026; all 42 calls valid |
| v12_100_qa_local | 100 | Same hundred stories/traces; narrower reader-visible QA | No new paid assessment | No new paid assessment | 0 |
| v13_100_qa_local | 100 | Also distinguish a loan offer from an accepted loan in QA | No new paid assessment | No new paid assessment | 0 |
| v14_10 | 10 | Substitution, relocation, and an explicitly released deadline; seeds 4000-4009 | 7.500 / 7.500 | 5 / 5 | 0.041480 |
| v14_30 | 30 | Same generator; fresh seeds 5000-5029 | 7.867 / 7.900 | 5 / 4 | 0.118130 |
| v14_100_local | 100 | Fresh seeds 30000-30099; 92 exact texts | Not judged | Not judged | 0 |
| v15_100_local | 100 | Same hundred traces and QA; one ambiguous pronoun corrected | Not judged | Not judged | 0 |
| tradeoffs_v1_10 | 10 | Persistent rope/light conflicts and enacted deferrals; seeds 8000-8009 | 7.800 / 7.900 | 3 / 4 | 0.045749 |
| questions_v2_10 | 10 | Requests, inspection and belief revision; seeds 10000-10009 | 7.500 / 8.000 | 3 / 4 | 0.039282 |
| favors_v2_10 | 10 | Requests compose independent project/ownership/priority assignments; seeds 12000-12009 | 7.100 / 6.200 | 3 / 3 | 0.041384 |
| questions_v6_10 | 10 | Earlier promises, compatible work, late repair and known alternatives; seeds 14000-14009 | 7.400 / 7.700 | 4 / 5 | 0.041558 |
| questions_v8_10 | 10 | Actual attempts before inspection and physical repairs; seeds 16000-16009 | 7.200 / 7.000 | 5 / 5 | 0.042928 |
| questions_v11_10 | 10 | Second inspections after cover removal; divided loading after refusal; same seeds 16000-16009 | 7.600 / 7.100 | 4 / 5 | 0.042656 |
| questions_v11_30 | 30 | Same recovery generator; seeds 17000-17029 | 7.733 / 6.900 | 5 / 5 | 0.120484 |

Each numbered batch is `../harbor_iteration_vN/`. Keep failed and unjudged
batches. Every prepared batch freezes source, serialized worlds, full traces,
statements, exact spans, all stories and QA. Paid batches retain planned and
actual requests, raw responses and validation results. No filtered replacement
samples, exact-text deduplication, automatic paid retries or fallback tiers.

The v3 JSON defect is substantive: `Query.value` became an untyped dictionary
when decoding a structured measurement result. The codec now reconstructs typed
values from the queried record field; tests cover goals and action guards.
This preserves state-driven decisions across export, in line with the physical
carrier/world-state north star. No gen6, gen7 or legacy runtime changes.

## What Improved

Writing whole scenes around a goal, turn and final image made a much larger
difference than ordering an event log. A depth measurement now changes launch
legality; timing and tool access determine the next step. Capacity forces a load
to be divided. Consent and a physical return settle a display loan without
transferring ownership. Inspection can contradict a packing list and trigger a
different delivery and an actual exchange of packing slips.

The v9 baseline has four deliberately authored goal policies over shared laws, not a
general autonomous character planner. The interpreter has not learned prose.
Additional scenes and dialogue required author effort. Current parameter names
are experimental and reused across purposes; they are not a finished authoring
interface. Declared paragraph provenance does not prove every English assertion.

Both judges penalized a completed delivery whose initial sailing goal received
no payoff. The revised ending physically places the boat in a rope-coil pretend
harbor (or tool-case dock). This is an enacted choice, not an added claim that
the boat sailed. Lending stories also distinguish a timely return from an
actually performed launch.

## Ladder And Limitations

The updated requested ladder is 10, then 30, then replication in two additional
StoryScenes scripts, then 100 per script and a cross-script diversity check.
Maintain storytelling >=7 and test semantic diversity. Ten reached moderate
diversity, not consistently distinct narratives. The first 30-story regrade
fell below 7 storytelling for both judges; keep this failure rather than choosing
the more favorable first response. v9 tests a fresh 30 after the next revision.
All three scripts pass the ten-, thirty- and hundred-story storytelling gates.
Their within-script diversity is still low to moderate. See the complete
[three-script findings](../replication_pooled_v1/FINDINGS.md), including partial
QA coverage and exact budget accounting. No paid requests remain active at that
checkpoint. The next unsolved goal is structural diversity. New runs
send the ENTIRE set in one story request per judge, with a larger output budget
for the required per-story ratings. QA remains six uniformly sampled single-turn
questions per story in five-story batches. This is actually up to six: four
declined-loan stories in harbor's hundred have five, giving 596 conversations.
No multi-turn claim is made.

The ten seeds are 0-9. The first thirty are 1000-1029; after using their feedback,
the v9 thirty use 2000-2029. Later sets should use predeclared new ranges to test
generalization, not just append the already optimized samples. Mechanical plot
descriptors are diagnostics, not counts of unique narratives. Exact uniqueness
and a larger compressed archive do not establish semantic diversity.

v7 -> v8 is a matched prose-only comparison: all ten trace hashes are identical,
seven texts changed. LZMA/XZ preset 9 of the entire shuffled story-only corpus
grew from 2,816 to 3,352 bytes (281.6 to 335.2 bytes/story). Earlier interventions
changed initial conditions and purposes and are not prose-only ablations.

## Coupled-Goal Test

v10 adds a fifth purpose: Ari borrows the rope to hang a chart while Bo needs
the same rope to open Cy's launch tub. Removing it also makes the tool case
light enough to carry. Display duration, route time, the launch deadline and
Ari's priority determine whether to refuse, shorten the display, finish both
plans, or return the rope too late. A late physical return settles the loan
but does not erase the broken timing promise. Counterfactual tests change the
priority in the same physical setup and check different actual boat locations.

This advances state-driven composition over physical carriers without changing
the capability laws, but it remains an authored policy, not a general planner.
The old seed-to-purpose mapping changed from four to five purposes; the new
hundred uses a fresh seed range. Differences from v9 are not a matched causal
estimate of this intervention's effect.

[The new findings](../harbor_iteration_v11_100/FINDINGS.md) are deliberately
negative about scaling: storytelling remains comfortably above seven, while
diversity is still 5/4 on a hundred. Twenty shared-rope positions yield only
eight exact texts. Exhausting its five-axis grid gives 72 configurations, 21
action paths and just 16 exact texts, including every renderer-choice leaf.
That audit covers this branch with other conditions at defaults, not all harbor
stories. More parameter combinations cannot remove its authored prose ceiling.

v11 corrects an implied second promise and an undeclared red sail in the
early-return branch. All original ten texts remain unchanged; among the thirty,
only harbor:3019 changes and all thirty trace hashes remain identical. v12 is
a local QA-only correction: avoid naming a hidden workshop in one prose
variant, and distinguish starting a return from completing the handover.
All hundred stories and traces match v11 exactly; 39 QA sets change and have
not received a new paid assessment. Preserve the historical QA grades.
v13 additionally removes a loan presupposition from the shared-rope ownership
question, which also appears in declined-offer stories. It asks who owned the
offered rope, not whether an enacted loan changed ownership. The current local
hundred preserves all stories/traces and changes 59 QA sets relative to v11;
these answers are not newly judged either.

Reproduce the bounded branch audit:

```bash
./.venv/bin/python storyscenes/replication_space_audit.py --scope harbor-shared-rope --out storyscenes/runs/NEW_SPACE_AUDIT.json
```

## Cost And Reproduction

The separate [composed-goal prototype](../harbor_composition_v2_100_local/LOCAL_REVIEW.md)
is local-only. Reusable methods now restore goals displaced by later resource
use; the original harbor generator is unchanged. Ten/thirty/hundred return and
replay, with 10/19/39 exact texts. Its complete 576-configuration space contains
48 texts and always ends with all three goals satisfied. This is not a new
literary or diversity pass. It incurred no API spend and did not alter the cap.

The [v14 alternatives report](../harbor_iteration_v14_30/FINDINGS.md) preserves
the next negative scaling result: storytelling stays above seven, but diversity
is 5/4 in thirty. The shared-rope nine-axis audit finds 28 texts across 1,152
configurations. Local counterfactuals verify substitution, relocation and
explicit deadline release; these are still authored policies, not a general
planner. The local hundred and the matched v15 pronoun correction are unjudged.

The [persistent trade-off test](../harbor_tradeoffs_v1_10_local/FINDINGS.md)
keeps rope/light constraints active after an action succeeds. Ari's embodied
priorities decide which goals to defer, and the corresponding chart or boat
is placed in an explicit fallback state. Its scored ten still tells good
stories (7.8/7.9), but diversity is only 3/4. Local thirty/hundred have 22/70
exact texts; the hundred compresses to 2.16%. Those larger sets were not sent
for paid assessment after the weak ten-story diversity result.
Its full v1 condition-space audit replays all 2,304 configurations but finds
only 154 texts / 75 paths. Matched local v3 batches narrow unsupported QA and
fix first-visit/return wording: all 140 traces match; story changes are zero
in ten, one in thirty, five in a hundred. The corrected QA has no new grades.
Both intermediate v2 and scored v1 remain intact.

`settings.json` preserves the original shared $5 authorization, prior ledger hashes and
their $0.73362090 conservative commitment. `budget.json` is the single ledger
for ALL harbor versions and both replications. It retains reservations for unknown interrupted calls;
do not start simultaneous judge processes against it. Rates use returned usage
and are estimates, not invoices. Coding-agent usage is not API authoring cost.
The user's later **$10 total** authorization is recorded separately in
`authorization_increase.json`, linked to the historical settings hash. It does
not replace the original settings or discard earlier commitments. The dollar
amounts below each describe their historical checkpoint.

After v14_30, combined conservative commitment is $4.45724585 against $5,
leaving $0.54275415. Estimated returned usage across both earlier comparisons
and this campaign is $2.85610385; $1.601142 remains reserved for prior outcomes.
The v10 ten, v11 thirty and v11 hundred together cost $0.53567845. All their
paid requests returned. The v14 ten and thirty add $0.15961010, with all 20 calls
valid; no judge process is active at this checkpoint. The new hundred requires
a $0.639245 whole-set story reservation and cannot be dispatched under the
remaining cap. Keep it local-only rather than weakening the spending guard.

The subsequent trade-off ten adds $0.04574855, all six requests returned valid.
After that trade-off check, combined conservative commitment was **$4.50299440**, leaving
**$0.49700560**. Priced returned usage totals $2.90185240; the earlier
$1.601142 in unpriced reservations remains untouched. No budget extension
was applied. The ten's QA usable counts are 51/60 Terra and 48/60 Luna;
these grades expose real reader-visible grounding gaps as well as a few
judge mistakes. Preserve them when narrowing the answers locally.

The [question-led ten](../harbor_questions_v2_10/FINDINGS.md) adds **$0.039282**,
all six calls valid. At that checkpoint conservative commitment was **$4.54227640**,
leaving **$0.45772360**. Priced returned usage totals $2.94113440; the same
$1.601142 in prior reservations remains untouched. No budget extension was used.
Storytelling is 7.5/8.0, diversity 3/4; QA usable is 59/60 and 60/60. The full
32-config space produces only 24 texts, so larger paid grading is not justified
yet. Local thirty/hundred replay, with 18/23 exact texts. Matched v4 clarifies
an inspector role and uncertainty prose/QA; revised QA has no new scores.

The [favor-network ten](../harbor_favors_v2_10/FINDINGS.md) adds **$0.04138390**,
all six calls valid. At that checkpoint conservative commitment was **$4.58366030**,
leaving **$0.41633970**. Priced returned usage totals $2.98251830; the same
$1.601142 in prior reservations remains untouched. No budget extension was used.
Storytelling regresses to 7.1/6.2 and diversity is 3/3. Longer dependency chains
are not a diversity win. The local hundred has 56 exact texts and compresses to
2.48%; no larger paid assessment follows. The 972-config permutation subspace
replays with 135 texts, not a full-space ceiling. Local v3 records reply-time
listeners and corrects unsupported prose actions. Preserve all v1/v2/v3 batches
and do not apply v2 scores to the unjudged correction.

The [earlier-promise extension](../harbor_questions_v6_10/FINDINGS.md) adds
**$0.041558**, all six calls valid. At that checkpoint combined conservative commitment was
**$4.62521830**, leaving **$0.37478170**. Priced returned usage is $3.02407630;
the same $1.601142 in prior reservations remains untouched. No budget extension.
Ten-story storytelling is 7.4/7.7, diversity 4/5. The complete expanded space
has only 52 texts across 128 configurations. Local thirty/hundred are unjudged
at 27/43 exact texts; the hundred compresses to 3.57%. No larger paid run follows.
The paid ten has no refusals or unknown-bridge case, so its scores do not certify
those locally tested continuations. Local v7 corrects refusal-question focus
without changing any of the ten scored stories, QA sets or traces.

The [attempt-first extension](../harbor_questions_v8_10/FINDINGS.md) adds
**$0.04292835**, all six calls valid. Combined conservative commitment then
was **$4.66814665**, leaving **$0.33185335** under the original cap. Priced returned usage totaled
$3.06700465; the same $1.601142 in prior reservations remains untouched.
Storytelling is 7.2/7.0, diversity 5/5 and QA usable 58/60 versus 59/60.
The full 256-config space has 104 texts / 96 paths. Local thirty/hundred have
24/54 exact texts and remain unjudged. A matched hundred with attempt-first
disabled has 39 texts and 3.64% XZ ratio, versus 54 and 5.52% with mixed order.
That is a measured expansion, not sufficient semantic diversity. Local v9
clarifies one assumed load in prose, changing 1/2/15 texts at 10/30/100 while
preserving all traces and QA. These revised contexts are unjudged; keep v8.

The [recovery follow-up](../harbor_questions_v11_10/FINDINGS.md) adds
**$0.16314015** across ten and thirty, all 20 calls valid. Current combined
conservative commitment is **$4.83128680 / $10**, leaving **$5.16871320**.
Returned-usage estimates are $3.23014480; prior unknown reserves remain
$1.60114200. No paid process is active. The local hundred is not judged.
The enabled sampler has only 128 distinct texts across 256 configurations,
and the hundred repeats paragraphs over 83.23% of its word positions.

More importantly, the user rejected the randomly displayed prose as worse than
storyscripts despite the nominal seven-level averages. Manual review agrees
that audit-like narration, unearned repurposing endings and a loosely attached
key subplot are not evidence of good storytelling. The current judge's sole
race-story anchor is rated seven; its checklist and returned notes strongly
favor completed actions and concrete endpoints. Preserve all scores, but do
not promote the generator or buy another broad trial before a separate blind
literary calibration against stronger/weaker examples. This is an incomplete
goal, not a solved dataset-quality problem. Full local suite: 573 tests pass;
all hundred frozen-runtime samples reproduce, which does not certify prose.

The separate [literary diagnostic](../literary_calibration_v1/README.md) then
compares the two criticized texts with fixed-seed StoryScripts, saved Puddles
and Nell, the old race anchor, and two artificial controls. Both harbor samples
are consistently rejected; the Puddles/Nell preferences survive order reversal.
Six of fifteen complete two-order model-pair checks still flip, so this is not
a new calibrated acceptance gate. Human preferences remain unlabelled. All 32
calls returned; a quote-wrapper validation repair recovers 31 assessments
offline without retries, preserving the invalid original results as well.
New returned-usage cost is **$0.028596575**. Current conservative commitment is
**$4.859883375 / $10**, leaving **$5.140116625**; the $1.601142 prior reserves
remain unchanged. No paid process is active. The literary rubric experiment is
separate from the historical quality/diversity score table above.

Two v5 Luna QA calls were interrupted after remaining open beyond the intended
timeout; no response was obtained, and their $0.275583 reservations remain.
The shared evaluator now wraps each paid call in a hard 900-second async deadline
in addition to the HTTP timeout. Source-locked resume refuses to repeat uncertain
requests. Frozen runtime resume was used to record v5's missing QA outcomes
without another API request.

From the repository root:

```bash
./.venv/bin/python -m storyscenes.harbor_story --seed 7 --qa
./.venv/bin/python storyscenes/harbor_trial.py prepare --out storyscenes/runs/NEW_BATCH --count 10 --seed 0
./.venv/bin/python storyscenes/harbor_trial.py judge --out storyscenes/runs/NEW_BATCH --api-key-file .API_KEY --concurrency 4
./.venv/bin/python -m unittest discover -s storyscenes -p 'test*.py'
```

Use a new directory for every revision. `--count` accepts 10, 30 or 100. An old
batch can be resumed with its `_source/storyscenes/harbor_trial.py`; source and
sample hashes are checked. This does not authorize retrying unknown requests.
Near the remaining budget ceiling, use `--concurrency 1`: a hundred-story
request reserves approximately $0.63 even for Luna, because both arms use the
conservative Terra ceiling. Concurrent reservations can reject unsent jobs
before actual costs settle. In v11_100, all 36 such local rejection records and
the initial partial report were archived before sequential first dispatch.
No request/response artifact existed for those jobs; the six returned requests
were reused. Never apply this recovery to an uncertain paid request.
