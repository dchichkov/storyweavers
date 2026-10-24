# Purposeful capability stories: second repair pass

This pass changes executable plots as well as prose. It uses existing capability
operations and preserves the permissive conformance examples. No judge calls
were made, and no new quality score is claimed. The [full comparison](REPORT.md)
contains old-path and revised-plot stories side by side.

## Executed changes

**Library:** Inez requests an inspection of a courtyard marker. The atlas is an
actual required observation instrument, not an ornamental prop. Nia reads the
marker outside, brings its message back, and Inez receives and believes the
report. The original loan/return problem follows. Completing the requested task
requires its inspection receipt; returning the atlas cannot substitute for it.

**Observatory:** Noor says the calibration reading comes first. The reading has
an explicit availability time, and the handoff requires its evidence. The default
reading at time 8 makes a strict-before-8 promise late; binding the reading to
time 6 produces a fulfilled promise with the same operations. This is a bounded,
authored schedule, not a new general duration or workload simulation.

**Harbor:** Ari's new inspection leads to a corrected report. Cy must receive,
understand and adopt it before traveling to the jetty and picking up the gauge.
The old dated report is still historical evidence, not knowledge of the present.
Blocking the correction leaves Cy without the belief needed by this authored
retrieval policy. This is not a universal prohibition on searching independently.

The prose now names an inspection's actual instrument, distinguishes spoken from
delayed reports, omits unnecessary time-zero labels in immediate exchanges, and
can combine hearing/believing into one sentence while retaining separate evidence
spans. Final custody supplies a more specific closing image when supported.
Attributed causal reasons now require their visible supporting statements; hiding
the correction removes the corresponding explanation from reading QA.

## A caught planning regression

The preserved `capability_prose_review_v3` run returned only **25/30 matched** and
**46/60 independent** positions. Harbor accounted for the failures: **5/10** and
**6/20** respectively. Its fresh observation could be consumed during the first
visit, and its case could be reopened before transport. Both choices were legal
mechanically but defeated the intended later scene, causing expensive search.

V4 gates that opening/inspection on Ari reaching the jetty at time 2 with an open
case. The core operations remain permissive; the example's plot supplies the
extra prerequisites. All identical seed positions were rerun, without extending
the per-position limits or discarding failures from V3.

## Verification

| Profile | Matched positions | New seeds 44000-44019 | Distinct new stories | Mean new story words |
| --- | ---: | ---: | ---: | ---: |
| Library | 10/10 | 20/20 | 1 | 297 |
| Harbor | 10/10 | 20/20 | 1 | 241 |
| Observatory | 10/10 | 20/20 | 1 | 152 |

- Limits remain 6,000 search nodes, 2 CPU seconds and 6 wall seconds per position.
- All 30 historical trace hashes and diagnostic texts still reproduce exactly.
- All 90 revised outputs have verified statement spans and distinct visible QA
  anchors within each story. No historical batch was overwritten.
- **407 StoryScenes tests pass**, including 10 new purpose/causality tests.
- Negative tests cover an inaccessible atlas, an unreadable marker, blocked
  correction, hidden QA support, premature inspection and future-dated evidence.
- Time-6/time-8/time-10 calibration variants yield fulfilled/breached/breached
  promises, with the corresponding actual handoff receipts.
- StoryWorlds was unchanged and was not rerun. API spend: **$0**.

## Manual assessment and limits

The atlas trip now has work to do; the harbor discovery changes a later physical
action; and the chart's timing is connected to a stated priority and an available
reading. These are substantive improvements over adding connective prose to an
unchanged log. Exact consequence tests provide stronger evidence than a prettier
paragraph alone.

The language is still controlled and often administrative. The library has many
agreement/return steps, and harbor still explicitly explains report timestamps.
The observatory demonstrates overcommitment and refusal, but does not model a
learned lesson or emotional change. Do not assert those changes in narration.

Most importantly, **each fixed profile collapses to one visible story** in this
sample. Irrelevant permutations no longer masquerade as variety. These are useful
canonical examples and reliability tests, not a 90-story training dataset.
Further diversity must come from actual initial facts, conflicting goals, available
tools, delivery times and alternative consequences. The calibration intervention
is one tested example of such a parameter, but it is not yet sampled by default.

Before claiming literary quality, compare a deliberately varied set with the
unchanged story/QA judges. The historical 2.67/3.00 scores do not describe this
new prose, and passing mechanical tests is not a replacement for those judgments.
