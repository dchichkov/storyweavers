# The Cup with the Crooked Lip

A standard-library-only, offline mini-adventure in a pottery workshop. Mina borrows Mrs. Vale's wooden shaping rib, makes a cup for her grandfather, and chooses whether to keep or repair its uneven rim. The isolated `kite` package name is only the harness path; this is not a kite story.

## Run

From the repository root:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py .
```

The command prints only the generated prose. `generate(seed, count=7|8, params=...)` returns the selected path, local action traces, per-scene text, final state, and bounded search-attempt count. `replay(params, path)` reproduces episodes exactly. To supply parameters at the command line, pass `--params path/to/parameters.json`, containing all five fields, for example:

```json
{"clay_grams":240,"sponge_damp":true,"wheel_level":false,"kiln_even":true,"finish_choice":"keep"}
```

## Explicit ending recipes

Each recipe below uses a complete `Parameters` object. The repair and kept-rim routes can be generated with either length; their endings follow the enacted treatment. The cracked-cup example uses a fixed seven-scene path so the optional sheltered-drying vignette is deliberately omitted.

```python
from storyscenes.mini_adventures.kite.world import Parameters, generate, replay

# Keep the crooked lip; an even firing leaves a useful drinking cup.
kept = generate(12, count=7, params=Parameters(
    clay_grams=240, sponge_damp=True, wheel_level=False,
    kiln_even=True, finish_choice='keep'))

# Spend reserved clay to reinforce and smooth the rim.
repaired = generate(12, count=8, params=Parameters(
    clay_grams=250, sponge_damp=True, wheel_level=False,
    kiln_even=False, finish_choice='repair'))

# A thin cup cracks in an uneven firing when it is not slow-dried.
# The child tells the truth and Grandpa uses the finished vessel for pencils.
p = Parameters(clay_grams=190, sponge_damp=True, wheel_level=False,
               kiln_even=False, finish_choice='keep')
path = ('borrow_rib', 'old_handle_memory', 'wedge_clay', 'shape_cup',
        'decide_flaw', 'fire_cup', 'ending_cracked')
cracked = replay(p, path)
print(cracked[-1]['after']['story.outcome'])
```

For the cracked outcome, the same parameters with the `sheltered_shelf` scene included protect the thin wall during drying, so the crack ending is no longer compatible. The repaired ending requires enough reserved clay; a repair request with insufficient material is rejected rather than silently succeeding.

## State and authoring limits

- `clay_grams` is 180–280; a repair needs at least 30 grams reserved after shaping. Boolean parameters are strict booleans. `finish_choice` is `keep` or `repair`.
- The wheel changes rim shape and wall risk. Sponge preparation changes the local actions. Kiln steadiness, wall thickness, and enacted slow drying determine whether a kept thin cup cracks. These are deliberately small scenario rules, not a general pottery simulator.
- The two optional vignettes are `old_handle_memory` and `sheltered_shelf`. A seven-scene story includes exactly one; an eight-scene story includes both. Neither omitted vignette executes an effect.
- The three endings are a crooked but useful drinking cup, a repaired drinking cup, and an honestly repurposed cracked cup used as a pencil holder. Every ending returns the clean, usable rib and completes an actual use of the gift.
- Search is seeded and bounded. It explores copied states by calling guarded scene plays; rejected branches cannot mutate the caller or enter the output. It is not a set of whole-story templates, but the small authored scene pool necessarily limits narrative breadth.
- The reference story is a longer authored exemplar, not a guarantee that every generated route contains all its beats. Generated scenes are shorter, and parameters or omitted vignettes alter what can truthfully be said.
- No runtime LLM, API, network access, non-standard dependency, human repair, or shared-file change is used.

## Tests and execution status

The included `test_world.py` covers both lengths across 100 seeds, exact deterministic replay, event preconditions and changes, parameter validation, illegal actions without mutation, optional omission, tool/cup location continuity, and paired physical counterfactuals including all three endings.

**Tests were not executed for this response: no execution tools were available.** The commands above are supplied for local verification; no successful test run is claimed.