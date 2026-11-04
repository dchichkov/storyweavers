# Two-Agent Story-First Authoring Trial

[Results and limitations](RESULTS.md), [verbatim release samples](SAMPLES.md),
and [latest reusable brief](AUTHORING_AGENT.v3.md.in).

Started October 24, 2026. Goal: test two low-reasoning workhorse agents through
the complete reference-story -> scene inventory -> executable scenario workflow,
then supervise 3-5 rounds. This is an authoring-process experiment, not a claim
of inexpensive corpus-scale diversity.

## Assignment

Both workers use `gpt-6.1-sol`, reasoning `low`, fresh context, and the saved
[brief](AUTHORING_AGENT.md.in). This is the available lightweight reasoning
setting, not a separately named "Sol light" model. Each has access to the repo
and existing engine, owns a distinct scenario pack, and can propose shared
library changes for parent integration. The parent owns review and cross-pack
tooling. No runtime LLM or external paid judging is authorized by this trial.

| Pack | Seed | Setting | Prop | Want |
| --- | ---: | --- | --- | --- |
| bakery | 757654805 | village bakery | a borrowed lantern | to keep a surprise secret |
| greenhouse | 822263077 | allotment greenhouse | a waxed paper parcel | to win back a friend's trust |

Draw method: `random.Random(20261024)`, per pack draw `randrange(2**31)` then
one choice from each list below, in order. These are first draws, not selected
for output quality.

- Settings: allotment greenhouse; village bakery; puppet theater; hilltop kite
  field; station waiting room; community pottery shed; canal towpath; school
  costume room.
- Props: a cracked bell; a waxed paper parcel; a bent key; a red ribbon; a
  borrowed lantern; a wobbly cart; a repaired umbrella; a tiny wooden boat.
- Wants: to keep a surprise secret; to finish before a visitor arrives; to win
  back a friend's trust; to show that a small contribution matters; to return
  something in better condition.

## Rounds And Evidence

1. Author reference and inventory; implement and test first complete product.
   Freeze outputs before parent intervention. Read seeds 0 and 1 at both lengths
   plus a separately labeled diagnostic branch. Check mechanics and replay.
2. Return concrete defects to the SAME workers. Repair the workflow and packs;
   preserve a second matched batch and compare the same seeds before/after.
3. Test held-out seeds and counterfactuals. Ask workers to resolve observed
   defects and contribute any demonstrably shared utility. Freeze final products,
   document effort/limitations and the revised reusable authoring brief.
4. Up to two further rounds if explicit requirements remain unfulfilled.

Per round, capture all failures rather than resampling: at least 100 generated
stories per pack (50 seeds at each length), exact replay, event-chain consistency,
scene coverage, outcome frequencies, exact text counts, LZMA ratio, and text/scene
lengths. These are diagnostics, not a combined literary score. Parent review must
read complete stories and references; no API judge is needed to spot basic defects.

The parent adds both packs to a shared discoverable scene inventory and runner.
This is inventory integration, not a claim that arbitrary cross-scenario scenes
are mutually compatible. Shared engine changes require concrete consumers/tests.

## State

Round 1 dispatched. Worker handles:

- Bakery: Hume, `01a16ef5-9be0-77e1-a582-81de9000b189`.
- Greenhouse: Hubble, `01a16ef5-9cb8-7cc0-95c3-f30fb277cfc6`.

Both received the v1 brief path and their assignment above with fresh context.
The follow-up integration note specified an inventory object containing a
`scenes` list with `id`, `role`, and `implemented_ids` fields. Per-agent progress
is in each pack; round artifacts/findings are added when verified.
Shared notices: [BOARD.md](BOARD.md).

## Round 1 Evidence

Both first submissions completed. Parent audits preserved 100 positions each
(seeds 0-49 at both lengths), all replaying with consistent event traces. All
200 positions also reproduced in separate interpreters from their frozen source
trees, not the subsequently edited working source.

| Pack | Reference words, excluding title | Executable scenes | Exact texts / 100 | Pooled XZ ratio | First-read defects |
| --- | ---: | ---: | ---: | ---: | --- |
| Bakery | 957 | 20 | 55 | 1.61% | Returning unusable light; urgency inconsistent between branches; unearned future baking |
| Greenhouse | 997 | 19 | 37 | 1.70% | Abrupt crop loss; ignored available repair; missing prose links for watering/container handoff |

See [reference reading](REFERENCE_REVIEW.md),
[bakery review](round_01/BAKERY_REVIEW.md), and
[greenhouse review](round_01/GREENHOUSE_REVIEW.md). These are parent-agent
observations, not independent human ratings. Low compression ratios are already
evidence against treating these sample counts as a large story multiplier.

Round 2 was sent to the same workers with the saved defect lists. The original
brief remains unchanged; [v2](AUTHORING_AGENT.v2.md.in) incorporates the lessons
for a future first-time author. Round 2 repeats seeds 0-49; final held-out
sampling will use seeds 1000-1049 at both lengths, with no prose-based replacement.

## Round 2 Evidence

Both matched batches pass 100/100, including independent frozen-source replay.
All 100 texts changed in each pack. Bakery changed 22 paths and outcomes;
greenhouse changed no path or outcome category. The latter is a useful example
of improving enactment and explanation without pretending to add plot diversity.

| Pack | Exact texts / 100 | Pooled XZ ratio | Outcome distribution |
| --- | ---: | ---: | --- |
| Bakery | 73 | 1.83% | 89 postponed, 8 surprise suppers, 3 shared suppers |
| Greenhouse | 45 | 1.80% | 42 supervised trials, 40 separations, 18 joint-care |

[Round 2 review and next tasks](round_02/REVIEW.md) records full-story reading
and the specific third-round requests. Scope is now four rounds total: a shared
atomic-action contribution in round 3, then both consumers and held-out testing
in round 4. Bakery owns the new helper; greenhouse cannot edit it concurrently.
This tests a real library contribution without growing another general planner.

## Rounds 3-5 Evidence

Round 3 kept all paths/outcome categories unchanged. Bakery revised eleven ending
texts and contributed the shared `LocalPlay` helper; greenhouse revised 73 texts,
recorded tea consumption, and fixed exit-before-door-closure ordering. Both
100-position snapshots reproduce from independent frozen interpreters.

Round 4 migrated greenhouse to the shared helper with byte-identical 100-row
JSONL output. Bakery's release pass also preserved all 100 rows. Parent captured
100 additional positions per pack from the predeclared unseen seeds and replayed
all 400 matched/new-seed positions from frozen source. Read the
[release review](round_04/RELEASE_REVIEW.md) for the full-suite test import failure.

Round 5 corrected that single bakery test import and independently checked both
packs under discovery. The saved bakery recheck reproduces all 100 new-seed
rows byte-for-byte; it is explicitly a recheck, not a new untouched holdout.
Both workers completed and were closed. The parent full-suite rerun passed
**660 tests in 265.182 seconds**; see [RESULTS.md](RESULTS.md) for the complete
evidence and limits.

There are eleven frozen 100-position audit batches: six across rounds 1-3, four
in round 4, and one round-5 recheck. Repeated seeds/revisions are intentional;
these are not 1,100 independent story ideas. Original failed unit-test evidence,
all earlier generated samples, and source snapshots remain preserved.
