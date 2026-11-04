# The Compass at Fernwater Fork

A standard-library-only, offline mini-adventure. The executable pack is new woodland-trail material; `kite` is only the isolated harness directory name.

## Run

From the repository root:

```sh
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py .
```

The CLI accepts an optional JSON object of parameter overrides with `--params`. For example:

```sh
python -m storyscenes.mini_adventures.kite.world --seed 3 --scenes 8 --params '{"rain": true, "puddle_depth": 3}'
```

`generate(seed, count=7|8, params=...)` returns the selected compatible path, episode prose, local action traces, state snapshots, final state, and bounded-search attempt count. `replay(params, path)` reproduces the episodes exactly. Each episode is 40–70 whitespace-separated words and contains at least one enacted, non-no-op local action.

## Parameters and ending recipes

`Parameters` is keyword-only and validates all fields:

- `compass_drift`: integer `0` or `1`. A drifting borrowed compass needs the observed brook bend to calibrate.
- `shortcut_open`: boolean. The stone-step shortcut can only be selected when open.
- `rain`: boolean. Rain makes the puddle crossing slower and the pool spur unsafe.
- `puddle_depth`: integer `1`–`3`. Only depth 1 without rain permits the stepping stones.
- `pace_gap`: integer `1`–`3`. It affects the time required to walk at Rowan’s pace.
- `pool_window`: integer `30`–`90` minutes. Arriving after the quiet-hour window sends the friends to the shelter instead.

A reproducible successful pool recipe, for either length:

```python
from storyscenes.mini_adventures.kite.world import Parameters, generate
p = Parameters(compass_drift=0, shortcut_open=True, rain=False,
               puddle_depth=1, pace_gap=1, pool_window=70)
row = generate(9, count=8, params=p)
assert row['final_state']['story.outcome'] == 'found_pool_together'
```

A reproducible rainy shelter ending:

```python
p = Parameters(compass_drift=0, shortcut_open=False, rain=True,
               puddle_depth=3, pace_gap=3, pool_window=80)
row = generate(9, count=7, params=p)
assert row['final_state']['story.outcome'] == 'missed_pool_found_frogs_together'
```

A separate clear-weather, late-arrival shelter recipe:

```python
p = Parameters(compass_drift=1, shortcut_open=False, rain=False,
               puddle_depth=3, pace_gap=3, pool_window=30)
row = generate(9, count=8, params=p)
assert row['final_state']['story.outcome'] == 'missed_pool_found_frogs_together'
```

The two optional vignettes are `fern_vignette` and `lace_vignette`. Six core encounters plus one optional vignette make a seven-scene story; both vignettes make an eight-scene story. Their effects are local and persistent: the brook bend can correct a drifting compass, and heel tape supports Rowan’s pace and may make the shortcut usable. No omitted vignette executes effects in the background. The route choice always keeps Rowan with Nia.

## Limits

The world is a small scenario model, not a general hiking or compass simulator. Rain, footing, timing, and pace are deliberately coarse. Generated prose is authored per scene and conditioned on enacted outcomes; there is no runtime language model, network access, or whole-story template selection. Characters do not separate, scenes do not repeat, and the reference story has details not represented in every short generated route. Mechanical coherence does not prove literary quality.

## Verification status

Tests were **not executed** in this single-response run because no execution tools were available. The commands above are provided for the parent environment; they are not claimed as successful results. The included tests cover both lengths over 100 seeds, replay, invalid parameters, failed actions without caller mutation, optional omission, object/location continuity, and paired counterfactuals.