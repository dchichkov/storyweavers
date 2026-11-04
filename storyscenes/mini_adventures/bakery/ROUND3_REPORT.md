# Bakery: Round 3

## Shared Contribution

Stable proposed contract, ready for parent confirmation and Round 4 adoption:

```python
from storyscenes.mini_adventures.local_play import LocalPlay

play = LocalPlay(state, actors=("actor",), validate=validate)
play.act("action", requires={"key": "old"}, **{"key": "new"})
play.state
play.events
```

The helper constructs runtime Scene/Condition/Effect dataclasses using keywords
and calls `runtime.transition`. It validates detached initial/candidate states,
prepares detached event data, and commits only after success. Failed conditions,
invariant exceptions, undeclared keys, and no-ops leave state and existing events
unchanged. Nested input/requirements/change/state/event data are isolated; even
retained validator snapshots cannot mutate the committed world. Validation uses
raise-on-failure semantics. `act` returns None; state and events remain mutable
owner-facing attributes. No planner, narrative rules, or actor-specific behavior
was added to this utility.

Bakery's existing `world.LocalPlay(state)` subclasses it with the same cast and
validator. Its movement, handoff, usable-return settlement, and scenario actions
are unchanged. Greenhouse is deliberately not adapted or edited this round.
Parent source snapshots must include the new shared helper dependency.

## Prose And Recipes

Successful endings retain the same oil/wick checks, loan settlement, and final
prop actions. "Now it's returned" becomes Nell's "Enough for your steps?" and
Vale's "Enough." The surprise ending simply rests the lantern and lets Vale ask
for the crust; it no longer calls the prop a "usable lantern." Dialogue requests
and descriptions introduce no new simulated outcomes or offstage success.

The new pack `README.md` documents executable, explicit parameter recipes for
all three outcome IDs, labeled diagnostic counterfactuals rather than first-draw
samples. Tests execute these recipes. Sampling probabilities and the existing
failure skew were not changed.

## Verification

```sh
.venv/bin/python -m unittest storyscenes.mini_adventures.test_local_play storyscenes.mini_adventures.bakery.test_world
```

Result: **27 tests passed** in 8.082 seconds: nine shared helper tests and
eighteen bakery tests, including the existing 200 seeded/length routes and
288 parameter-grid routes. Shared tests cover invalid initial states, rejected
conditions, rejected candidate invariants, no-ops, unknown keys, valid traces,
runtime delegation, actor-list isolation, nested payload isolation in both
directions, later-event independence, and retained/mutating validator snapshots.
Bakery adds assertions for helper adoption, documented recipes, and preservation
of the successful endings' actual checks despite their less audit-like wording.

Compared every one of the parent's 100 frozen Round 2 rows against current
generation with its saved parameters and count. All parameters, paths, search
attempts, final states, episode states, and events are exactly equal. Non-ending
prose is identical. Only the eleven successful stories differ, in the two
intentionally revised ending renderers. The same 89 postponed, eight surprise,
and three shared outcomes remain. No rows were filtered or resampled.

`round_03_samples.md` and `.jsonl` save seeds 0, 1, 6, 42, and 757654805 at both
lengths, with no outcome filtering. Read all ten full stories locally, including
the two successful branches at both lengths. The reference remains byte-equal
to its frozen Round 2 copy. Prior samples and reports were not overwritten.

## Changed Paths

- `storyscenes/mini_adventures/local_play.py`
- `storyscenes/mini_adventures/test_local_play.py`
- `storyscenes/mini_adventures/bakery/world.py`
- `storyscenes/mini_adventures/bakery/prose.py`
- `storyscenes/mini_adventures/bakery/test_world.py`
- `storyscenes/mini_adventures/bakery/README.md`
- `storyscenes/mini_adventures/bakery/PROGRESS.md`
- `storyscenes/mini_adventures/bakery/LIBRARY_PROPOSALS.md`
- `storyscenes/mini_adventures/bakery/ROUND3_REPORT.md`
- `storyscenes/mini_adventures/bakery/round_03_samples.md` and `.jsonl`

No other source files, previous artifacts, or greenhouse files edited. No API
calls, commits, additional agents, or changes to engines/planning. The shared
helper supports the embedded-state model without inventing new abstractions
for stories: physical/world invariants still belong to each consumer.

## Remaining Limits

The helper has one live consumer until Round 4. It deep-copies for correctness,
not throughput, and deliberately provides no immutable public views. Focused
tests and frozen-row comparisons passed; the complete StoryScenes suite and
held-out release batch remain the parent's scheduled Round 4 gate, not a result
claimed here. Bakery still repeats a narrow backbone, favors postponement, and
uses symbolic fuel/time rules. No human literary score, diversity multiplier,
or unattended-generation claim follows from this contribution.
