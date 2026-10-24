# Favor networks: compositional dependencies, repetitive stories

## Decision

Do not promote this generator or buy a thirty/hundred-story assessment yet.
The fixed ten fails the storytelling >=7 gate for Luna and scores diversity
3/9 from both judges. More dependency combinations did not make better stories.
The earlier harbor baseline remains the default; this is an opt-in experiment.

`harbor_favors` gives three physical characters independent projects, tool
ownership and lending priorities. A bounded controller follows actual requests
and wait replies into the owner's project. A reciprocal character can relax a
first-work demand after an enacted waiting cycle. Shared loan/return operations
move the tools; actual opening, placement or observation completes the work.
No whole-plot ID is selected, but these are still small authored policies and
authored scene paragraphs, not general planning or learned prose. No runtime LLM.

## Paid ten

Seeds 12000-12009 were fixed before grading, with no replacement, filtering or
deduplication. The unchanged judges/rubrics saw all ten stories and up to six
uniformly sampled single-turn QA conversations each, 58 conversations total.
Only visible stories/QA were sent, not source code or hidden world state.

| Metric / 9 unless noted | Terra | Luna |
| --- | ---: | ---: |
| Storytelling | 7.1 | 6.2 |
| Overall | 7.0 | 7.0 |
| Style | 6.2 | 7.0 |
| Diversity | 3 | 3 |
| Causal-path diversity | 4 | 4 |
| QA overall | 9.0 | 8.259 |
| QA usable | 58/58 | 55/58 |

Six valid Flex responses cost an estimated **$0.04138390**, with 28,146 input
and 8,840 output tokens. Across the original shared $5 authorization, conservative
commitment is **$4.58366030**, leaving **$0.41633970**. Priced returned usage is
$2.98251830; $1.601142 remains reserved for earlier uncertain outcomes. No budget
extension, automatic retry or fallback tier was used. No larger paid run follows
this result.

## Manual reading and judge agreement

Both judges identify the same request, wait/lend, work, return pattern. The
three-person chain is mechanically consequential, but it reads as more repeated
exchanges, not a richer conflict. Direct generosity often resolves the opening
too easily. Waiting for another character to finish an unrelated task gives
delay without much narrative consequence. Flags, boats and charts change the
props, but most endings have the same shape and cooperative moral framing.

The two reciprocal-cycle stories are the strongest local signal: both judges
score them above their other eight stories. A character changing a demand is a
more meaningful turn than a longer sequence of completed jobs. That is a small,
post-hoc observation from ten, not an independently confirmed improvement.

The prose does have beginnings, dialogue and concrete closing images. It is
not the original raw event log. However, repeated explanatory flourishes and
identical return conversations make the underlying template conspicuous.
Correct simulation does not select interesting events or decide how much prose
each event deserves. This experiment does not solve those separate problems.

### QA disagreements, not automatic repairs

Inspect the actual saved request and story before treating a grade as truth.
The three Luna rejections appear to be false positives; retain their scores:

- `harbor_favors:12005/c005`: Cy explicitly raises Cy's tub cover and floats a
  boat before Ari does. The answer correctly attributes that work to Cy.
- `harbor_favors:12009/c000`: the question and answer both name Bo. The story
  explicitly gives Bo the rope and boat task; the judge says the answer names Cy.
- `harbor_favors:12009/c001`: Bo explicitly makes Ari wait for the scissors
  until Bo floats a boat. Bo subsequently asks Cy for a rope. The judge confuses
  those two relationships.

These are visible-text checks, not appeals to hidden simulation. Terra accepted
all three. The raw results, requests and original conversation IDs remain intact;
the reported 55/58 is not silently adjusted.

## Local scale check

Fresh thirty and hundred ranges are 13000-13029 and 61000-61099. These larger
sets are unjudged. Every position, including duplicate texts, is preserved.

| Scored revision v2 | Exact texts | Mechanical signatures | Completed / waiting | XZ / raw story bytes |
| --- | ---: | ---: | ---: | ---: |
| 10 | 10 | 8 | 10 / 0 | 2,004 / 16,287 (12.30%) |
| 30 | 28 | 19 | 29 / 1 | 2,700 / 49,381 (5.47%) |
| 100 | 56 | 30 | 96 / 4 | 3,812 / 153,439 (2.48%) |

The paid ten contains no unresolved cycle, so its grades do not certify the
waiting endings. A local permutation audit covers **972 configurations**, all
replayed, with **135 exact texts, 46 action paths, 54 mechanical signatures**,
924 completed sessions and 48 waiting cycles. This is NOT the complete space:
each project type and tool owner appears once. The full declared 19,683-config
space also permits repeated projects and owners. Neither 135 nor 56 is claimed
as a global text ceiling. See `../harbor_iteration_campaign/favors_permutation_space_v2.json`.

Mechanical signatures, exact uniqueness and compression are diagnostics, not
semantic diversity scores. Extending the dependency graph did increase local
combinations, but the paired judges still found the narratives very similar.

## Preserved revisions and grounding fixes

The unjudged v1 preview had ambiguous references between different characters'
parcels/boats and repeated whole work paragraphs. v2 names the separate physical
artifacts, shortens repeated same-kind work and fixes plural scissors agreement.
Only v2 received paid grades. All earlier samples and sources remain preserved.

Local v3 adds reply-time listeners to the finite in-person inquiry record.
Recognizing the shared waiting cycle requires that every participant heard each
reply. Meeting afterward no longer grants retroactive knowledge. A negative
test moves characters between replies, then reunites them; recognition is blocked
until the missing replies are actually repeated. This follows the project's
physical-carrier/embedded-state principle without changing shared capability laws.
It is a finite hearing rule, not unrestricted language comprehension.

v3 also removes an undeclared workshop-table action and parcel movement, and
replaces a promise to go "second" with a willingness not to be first. In a
three-person cycle the yielding character can finish third. These are grounding
corrections, not claimed literary improvements.

Matched v3 batches preserve all **140 conditions, action paths, outcomes and QA
sets**. Story texts change in 6/10, 11/30 and 42/100 positions. All trace hashes
change because listener provenance is now recorded; do not call these identical
traces or transfer the paid story scores to v3. The corrected hundred still has
56 texts and compresses to **3,784 / 152,636 bytes (2.479%)**. Its 716 paragraph
positions contain only 127 exact paragraphs; **81.26%** of word positions repeat
an already-seen exact paragraph. See the preserved matched comparison in
`../harbor_favors_v3_100_local/matched_v2_checks.json`.

The frozen v3 runtime, imported outside the checkout, reproduced all hundred
stories, QA sets, paths, plot descriptors and trace hashes. The full StoryScenes
suite passes **537 tests**. AST/whitespace checks pass for the six touched Python
files. No StoryWorld, gen6, gen7 or legacy engine behavior was changed.
The corrected v3 permutation audit also replays all 972 configurations with
zero failures and the same 135 texts, 46 paths and 924/48 outcome counts.
Its separately saved `favors_permutation_space_v3.json` retains new source and
trace hashes; the v2 audit is unchanged.

## Next experiment

Keep the earlier strong scene-writing baseline. Test composition of *different*
causal relations: a mistaken belief changes a request, a promise conflicts with
a discovered need, or an accepted compromise leaves a lasting physical cost.
The actors must know the relevant facts through enacted observation or speech.
Avoid another menu of whole plots, cosmetic synonym sampling, and a longer
chain of identical borrow/work/return scenes.

Before another paid run: read a fixed ten with QA, audit legal continuations,
and check repeated paragraphs and local hundred-sample collapse. Then use the
same storytelling/diversity criteria, not a new metric chosen to reward the
mechanics. The requested diversity goal remains open.

```bash
./.venv/bin/python -m storyscenes.harbor_favors_story --seed 12000 --qa
./.venv/bin/python -m unittest discover -s storyscenes -p 'test_harbor_favors.py'
./.venv/bin/python storyscenes/harbor_trial.py prepare --world harbor_favors --out storyscenes/runs/NEW_BATCH --count 10 --seed 12000
./.venv/bin/python storyscenes/replication_space_audit.py --scope harbor-favors --out /tmp/NEW_favors_audit.json
```
