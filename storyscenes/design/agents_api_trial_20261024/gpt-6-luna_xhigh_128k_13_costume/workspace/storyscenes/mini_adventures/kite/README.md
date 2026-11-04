# The Storm Costume

A standard-library-only, offline mini-adventure set in a school costume cupboard. Ada borrows a school cape and tries to help Jo keep the promised Storm role without forcing Jo into an ill-fitting Moon tunic. Scene actions use `storyscenes.mini_adventures.local_play.LocalPlay`; the shared engine and other packs are unchanged.

## Run it

From the repository root:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 12 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py /path/to/repository
```

The module accepts `--seed`, `--scenes 7|8`, and `--params` with a JSON object. For example:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 8 --scenes 8 --params '{"teacher_available":false,"minutes_left":1,"seam_allowance":0,"pins_available":false,"stage_lamp":false}'
```

The generated JSON-native result is available directly from `generate(seed, count=7|8, params=...)`. `replay(params, path)` re-enacts a compatible path and returns its episode records. Every episode records guarded local actions, equality preconditions, state changes, and prose.

## Explicit ending recipes

These recipes are independent of the random seed and work at either supported length:

```python
from storyscenes.mini_adventures.kite.world import Parameters, generate

fitted = Parameters(teacher_available=True, minutes_left=2)
row = generate(0, count=7, params=fitted)
assert row["path"][-1] == "ending_fit"

improvised = Parameters(teacher_available=False, minutes_left=1,
                        seam_allowance=0, pins_available=False)
row = generate(0, count=7, params=improvised)
assert row["path"][-1] == "ending_improvised"
```

With time and a present teacher, Jo can receive a fitting Storm coat. Otherwise, sufficient seam allowance and pins can safely alter the tunic. If neither repair is possible, Jo declines the painful costume and performs Storm through a cape-led shadow or sail. `stage_lamp` selects that local play; `mirror_clear` changes the optional mirror scene. `minutes_left`, `teacher_available`, `seam_allowance`, and `pins_available` affect the possible costume outcome. The two optional vignettes are `mirror_vignette` and `ribbon_vignette`.

## Scope and limitations

Generated stories contain exactly seven or eight compatible scenes. Seven-scene routes use the core encounters; eight-scene routes include one of the two optional vignettes. The bounded seeded search commits only selected scenes; rejected speculative routes do not alter state or appear in the trace. The cape remains school property, its wind/shadow use is recorded, and it is returned after the performance. A chosen ribbon is also returned. The scene prose is authored per encounter and conditioned on enacted outcomes, not assembled from whole-story variants.

The model deliberately abstracts a school play: it has only these two children and one teacher, no repeated scenes, and a small set of costume and lighting possibilities. Availability is represented by validated parameters rather than a general-purpose wardrobe or clock simulation. It does not attempt literary quality scoring, exhaustive physical modeling, or semantic diversity measurement.

## Tests run

No execution tools were available during this single-response authoring run. Tests were **not executed**, and no integration-check result is claimed. The included test module covers both lengths across 100 seeds, replay and trace reconstruction, invalid parameters and actions, optional-scene omission, object continuity, counterfactual outcomes, and the CLI. Run the commands above in an environment containing the supplied shared files to verify them.