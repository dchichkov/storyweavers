# A Line Before Rain

A standard-library-only, offline mini-adventure about Nia borrowing Mae’s peg bag to finish the shared-garden washing before a shower. The executable scenes are small local plays; the generator searches compatible compositions rather than selecting a complete prewritten story.

## Run

From the repository root:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py .
```

The module prints prose. Its optional `--params` value is a JSON object of `Parameters` overrides, for example:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8 --params '{"peg_count":8,"shower_after":6,"windy":false,"line_strength":true,"shelter_open":true,"sheet_heavy":false,"priority":"sheet"}'
```

The Python API returns the JSON-native trace as well as prose:

```python
from storyscenes.mini_adventures.kite.world import Parameters, generate
row = generate(0, count=8, params=Parameters())
print(row['path'])
print(row['final_state']['story.outcome'])
```

## Explicit ending recipes

These are complete parameter values, not seed guesses. Each recipe works at either supported scene count; an eight-scene route includes one optional vignette, while a seven-scene route includes neither.

```python
from storyscenes.mini_adventures.kite.world import Parameters, generate

recipes = {
    'line': Parameters(peg_count=8, shower_after=6, windy=False,
        line_strength=True, shelter_open=True, sheet_heavy=False, priority='sheet'),
    'shelter': Parameters(peg_count=8, shower_after=3, windy=False,
        line_strength=True, shelter_open=True, sheet_heavy=False, priority='sheet'),
    'rain_recovery': Parameters(peg_count=5, shower_after=3, windy=True,
        line_strength=False, shelter_open=False, sheet_heavy=True, priority='small'),
}
for label, params in recipes.items():
    row = generate(0, count=7, params=params)
    print(label, row['path'][-1], row['final_state']['story.outcome'])
```

- `line`: the full load is on a strong, secure line before rain (`ending_line`, outcome `hung_before_shower`).
- `shelter`: the shower arrives during the work window and the available covered rack protects every garment (`ending_shelter`, outcome `covered_in_shed`).
- `rain_recovery`: with no shelter, the laundry is gathered as rain arrives, then Mae and Nia rehang it indoors and return the useful peg bag (`ending_rain`, outcome `caught_then_rehung`).

## Parameters and stateful choices

`Parameters` is keyword-only and validates all fields. The consequential dimensions are peg count (4–12), shower timing (3–6 time units), wind, line strength, shelter availability, sheet weight, and Nia’s scarce-peg priority (`sheet` or `small`). Weather advances through guarded local actions. Pegs are conserved between the borrowed bag and garments. Garment locations, the bag’s owner, the child’s learned rhyme, and the rescued snail persist across scene boundaries.

The two optional scenes are `save_snail` and `peg_rhyme_vignette`. Neither is executed if omitted. The generator returns exactly seven or eight distinct compatible scenes. Its seeded depth-first search has explicit node and attempt limits; discarded speculative plays are not included in the returned trace. `replay(params, path)` reproduces the states, event requirements, changes, and prose.

## Reference and mapping

`reference_story.md` is the authored reference and is not regenerated or patched to match an implementation result. `scene_inventory.json` inventories about twenty reference encounters and explicitly maps consolidated beats to executable scenes; some reference-only beats have an empty `implemented_ids` list and never execute secretly. `world.py` uses the supplied `storyscenes.mini_adventures.local_play.LocalPlay` for atomic actions and detached event traces.

## Limitations

The simulation is deliberately small: time is an integer, rain begins at a parameterized threshold, and line strength is a scenario rule rather than a general physics model. The limited-peg choice changes which garments are hung, but prose is authored per encounter and does not offer unlimited semantic variety. The cast and setting are fixed. A sheltered rack can protect partially hung washing; it does not count as beating the original sunny-line deadline. The rain ending completes an indoor rehang rather than pretending the missed deadline was met. The renderer is deterministic and makes no API or network calls.

## Tests actually run

No execution tools were available in this single-response run, so **no tests, CLI runs, generated-story inspections, or integration checks were executed here**. Do not treat the listed commands as reported results. The supplied tests are intended to cover both lengths over 100 seeds, replay, invalid parameters, rejected actions without mutation, optional omissions, custody and location continuity, paired counterfactuals, ending recipes, and the command-line entry point. The parent integration check should be run independently.