# The Light Under the Cloth

A village-bakery mini-adventure: Nell borrows Vale's lantern to bake a secret
leaving-supper loaf. The lamp must still have oil for his dark cellar steps.
Six parameter dimensions and twenty authored encounters compose into seven or
eight scenes. Seven scenes use the backbone alone; eight add one vignette.

```sh
.venv/bin/python -m storyscenes.mini_adventures.bakery.world --seed 6 --scenes 7
.venv/bin/python -m unittest storyscenes.mini_adventures.test_local_play storyscenes.mini_adventures.bakery.test_world
```

## Diagnostic Outcome Recipes

These are explicit parameter counterfactuals for inspection, **not first-draw
samples**, a success-rate estimate, or additional plot diversity. All omitted
fields use `Parameters` defaults. `count=7` deliberately excludes optional oil
refilling, so the stated resource condition is reproducible.

| Outcome ID | Explicit Parameters | Why It Follows |
| --- | --- | --- |
| `surprise_supper` | `fuel=3, early_van=False, decision="request_extension"` | Two baking intervals consume two measures, one remains for the cellar; permission allows finishing without disclosing the supper until the reveal. |
| `shared_supper` | `fuel=3, early_van=False, decision="confess"` | The same fuel and permission support finishing; confession changes Vale's knowledge and lets him help hold the lamp, rather than changing the deadline. |
| `breakfast_instead` | `fuel=1, early_van=False, decision="return_now", spare_oil=False` | The only measure belongs to the cellar reserve. The loaf never enters the oven, the lamp returns usable, and the children deliver a tentative invitation instead of serving supper. Breakfast is not accomplished or agreed. |

Execute the recipes directly from the repository root:

```python
from storyscenes.mini_adventures.bakery.world import Parameters, generate

recipes = {
    "surprise_supper": Parameters(fuel=3, early_van=False, decision="request_extension"),
    "shared_supper": Parameters(fuel=3, early_van=False, decision="confess"),
    "breakfast_instead": Parameters(fuel=1, early_van=False, decision="return_now", spare_oil=False),
}
for expected, params in recipes.items():
    row = generate(0, count=7, params=params)
    assert row["final_state"]["story.outcome"] == expected
    print(row["story"])
```

Useful paired counterfactuals: changing `early_van` to `True` blocks either supper
recipe without changing its fuel. With `fuel=2` and no early van, finishing is
blocked after the first baking interval; explicitly replaying `refill` between
`borrow` and `bake` adds the real bottle's single measure and permits finishing.
Omitting that scene never grants its oil. `test_world.py` checks these pairs.

## Shared Action Boundary

The stable utility is `storyscenes.mini_adventures.local_play.LocalPlay`:

```python
LocalPlay(state, *, actors, validate)
play.act(name, requires=None, **changes)
play.state
play.events
```

`requires` maps state keys to equality values; changes set existing state keys.
The callback raises for invalid states. It receives detached initial/candidate
snapshots. Successful events contain `action`, `requires`, and changed keys with
`before`/`after` values. Nested input, state, and event payloads are detached.
Failed conditions, invariant failures, and no-ops do not change state or events.
Validation exceptions propagate; illegal/no-op transitions raise `StoryError`.
The helper calls the existing `runtime.transition`; it has no movement, actor
roles, fuel, story rules, or planner. Public state/events remain mutable to their
owner, so callers should not treat them as immutable read-only views.

Bakery's `world.LocalPlay(state)` subclasses that helper and supplies the cast
and invariant validator. Movement, custody, usable-return settlement, and fuel
remain bakery operations. Greenhouse adoption is reserved for Round 4.

## Evidence And Limits

The reference is unchanged: 957 prose words, 963 including its title. Earlier
`first_draws.*`, `round_02_*`, and round reports are preserved. `round_03_samples.*`
are unfiltered matched seeds 0, 1, 6, 42, and 757654805 at both lengths; these
reading examples do not replace the parent's frozen 100-position batches.

Round 3 changes only shared atomic mechanics and two ending renderers, not
sampling probabilities or outcomes. All 100 frozen Round 2 positions retain
their parameters, paths, search attempts, states, and events. The same 89
postponements, eight surprise suppers, and three shared suppers remain. Across
seeds 0-99 at both lengths, the existing 173/16/11 outcome counts also remain.
Tests prove bounded execution and invariants, not literary quality. Stories
still use a narrow backbone; optional crown changes have limited payoff. Fuel
intervals and availability are symbolic, not calibrated physics or a live clock.
