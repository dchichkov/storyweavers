# Composed harbor: local feasibility, not a diversity pass

Checkpoint: 2026-10-23. **No paid judging and no transferred quality scores.**
The earlier scored harbor generator and every historical batch remain intact.

## Experiment

The previous shared-rope script selected a complete resolution before running
its actions. This opt-in experiment instead decomposes three physical goals:
hang the chart, launch the boat, and arrange the lantern. Authored methods use
the same retrieval, travel, placement and opening goals in different contexts.
Each candidate action goes through the existing capability executor. Later work
can undo an earlier result, and a final pass revisits displaced goals.

For example, showing the chart first can lead to taking it down to free the
rope, opening the launch tub, floating the boat, and hanging the chart again.
A dark launch can similarly borrow the light from an already-lit window, then
return it. An available clip removes the rope/display dependency; daylight
removes the light/launch dependency. These change enacted actions, not just
their ordering or wording. The two dependencies can occur in the same story.

The new `goal_planning.py` is bounded, author-side, depth-first decomposition.
It backtracks across locally completed goals when later work fails, checks all
root goals again at the end, rejects cyclic goal decomposition, and limits
actions, definition size and recursion depth. Methods and their order are
authored. This is not optimal planning, learned character reasoning, epistemic
planning, or a general replacement for the engine's solver. Rejected search
branches are never narrated as attempted actions or character thoughts.
Goal carriers are physical entities, and successful output is ordinary replayable
capability history. No gen6/gen7/legacy operations or physical laws were changed.

## Preserved local batches

| Batch | Seeds | Returned / planned | Exact texts | XZ bytes/story | Paid score |
| --- | --- | ---: | ---: | ---: | --- |
| composition_v1_10 | 6000-6009 | 10/10 | 10 | 176.40 | None |
| composition_v2_10 | Same ten, prose correction | 10/10 | 10 | 178.40 | None |
| composition_v2_30_local | 7000-7029 | 30/30 | 19 | 69.87 | None |
| composition_v2_100_local | 40000-40099 | 100/100 | 39 | 31.04 | None |

Directory names have the `harbor_` prefix. All returned samples pass serialized
world exact replay. Each batch freezes the planner, domain builder, renderer,
shared runtime, worlds, traces, statements, QA and judge request plans. The
request plans are **not dispatched requests**. Six single-turn QA conversations
per sample are selected uniformly, giving 60/180/600 at the three sizes.

The hundred has 29 stories that rehang the chart, 15 that move the lantern away
from the window, and seven that do both. These are mechanism counts, not counts
of semantically independent narratives. Its 26 mechanical plot signatures also
include order and condition distinctions that may not matter to a reader.

## Finite ceiling

`../harbor_iteration_campaign/composition_space_v2.json` exhausts the entire
declared sampler space: six goal priorities, six support preferences and four
Boolean conditions, for **576 configurations**. Prose has no random synonyms.

- **48 exact texts, 48 action paths, 27 mechanical signatures.**
- Every configuration ends with all three goals satisfied.
- At most 90 attempted actions per plan, below the 1,200 search bound.
- The local hundred compresses from 186,473 to 3,104 bytes: **1.665%**.
- Its 820 paragraph positions contain only **23 distinct exact paragraphs**.
  Counting each paragraph once removes **97.42%** of word positions.

This is not a successful diversity multiplier. Compared with the old shared-rope
branch's 28-text grid, the new experiment composes more sequences, but it also
adds a goal and different constraints. That is not a matched causal comparison.
Do not compare its single premise directly with the earlier five-purpose harbor
sampler and attribute the difference to the planning algorithm alone.

## Manual review and verification

Read all original ten stories and four additional distinct texts from the
thirty (7000, 7002, 7004, 7005), alongside their action sequences. They have
coherent physical turns and dialogue, but repeated openings, repeated success
endings and an obvious small paragraph inventory. Some round trips are
inefficient because method order prioritizes an authored goal, not shortest
execution. No literary acceptance score is claimed.

One temporal prose defect was fixed: when the lantern arrives after the boat
has launched, describe the boat already floating rather than where Cy "would
lower" it. v2 changes only story 6009 in the matched ten; all ten trace hashes
remain identical. The original text and its frozen source remain in v1.

**492 StoryScenes tests pass.** Fifteen new tests include rollback of failed
search branches, backtracking across goals, cyclic/over-budget definitions,
physical carriers, final-goal rechecking, resource-removal counterfactuals,
launch-light guards, a 16-configuration serialized replay/QA matrix, and the
temporal prose regression. The frozen runtime independently reproduced seeds
6000 and 6009 from outside the repository, matching text, QA, paths and traces.
Declared paragraph support still does not prove every English assertion.

## Next decision

Keep this optional; do not replace the scored baseline or export it as hundreds
of diverse training stories. The useful result is reusable causal work, not the
current corpus. The next experiment needs different goal conflicts and genuinely
different consequences, including alternatives to all-three-goals success, with
each new relation changing actual executable possibilities. Reordering these
three jobs or adding synonyms is not that experiment.

New API spend: **$0**. The shared $5 ledger remains at $4.45724585 committed,
including retained unknown reservations. A request to extend the total scoring
cap to $10 is awaiting a user answer; it has not changed authorization or files.
Existing story and QA rubrics are unchanged.

From the repository root:

```bash
./.venv/bin/python -m storyscenes.harbor_composition_story --seed 6001
./.venv/bin/python storyscenes/harbor_trial.py prepare --world harbor_composition --count 10 --seed 6000 --out storyscenes/runs/NEW_COMPOSITION
./.venv/bin/python storyscenes/replication_space_audit.py --scope harbor-composition --out storyscenes/runs/NEW_COMPOSITION_AUDIT.json
./.venv/bin/python -m unittest storyscenes.test_goal_planning storyscenes.test_harbor_composition
```

Use new output paths. Preparing, auditing and sampling are offline; `judge`
is a separate paid command and has not been run for this experiment.
