# The Last Dough

A standard-library-only mini-adventure in a crowded family kitchen. Mara and Eli borrow their neighbor’s biscuit cutters to make a thank-you gift, then decide what to do with the last dough. The pack uses the supplied `LocalPlay` helper for guarded, atomic local actions and traces; it does not modify shared files or use a runtime language model.

## Run it

From the repository root:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 12 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py .
```

The program supports exactly seven or eight scenes. Seven-scene routes contain the six required encounters plus an ending. Eight-scene routes include exactly one optional vignette: `flour_memory` or `timer_song`. `generate` returns JSON-native parameters, the path, episode states and traces, complete prose, final state, and a bounded-search attempt count. `replay(params, path)` re-enacts the route.

You may override parameters from the command line with a JSON object:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7 --params '{"dough_grams":140,"dough_chilled":true,"flour_available":true,"cutters_tacky":true,"oven_preheated":false,"share_plan":"equal"}'
```

The Python API is also convenient for reproducible recipes:

```python
from storyscenes.mini_adventures.kite.world import Parameters, generate

success = Parameters(dough_grams=140, dough_chilled=True, flour_available=True,
                     cutters_tacky=True, oven_preheated=False, share_plan='gift_first')
row = generate(2026102421, count=7, params=success)
print(row['path'][-1])  # ending_gift

fallback = Parameters(dough_grams=80, dough_chilled=False, flour_available=False,
                      cutters_tacky=False, oven_preheated=True, share_plan='equal')
row = generate(2026102421, count=8, params=fallback)
print(row['path'][-1])  # ending_note
```

These recipes explicitly select the outcomes. `ending_gift` requires neat shapes and at least 60 grams assigned to the gift. Either sharing plan can earn it: `gift_first` assigns two thirds of the dough to the gift; `equal` assigns half, with equal contributions from both siblings. The second recipe makes rough shapes and assigns too little dough to the gift, so the siblings deliver an honest note instead. In both endings they return clean cutters and Mrs. Flores uses them on her own dough.

## Parameters and consequences

`Parameters` is keyword-only and validates every value. `dough_grams` is an integer from 70 to 180. `dough_chilled`, `flour_available`, `cutters_tacky`, and `oven_preheated` must be booleans. `share_plan` is either `equal` or `gift_first`.

The dough is cut neatly if it is chilled or the counter can be floured; otherwise the warm dough smudges. Tacky cutters are washed before use. An unheated oven is preheated during preparation; light is not a prerequisite for heating. The dough is conserved across gift and home portions. The sharing plan changes those portions, while dough condition and amount determine which ending is possible. The borrowed cutters change carrier and location, become dirty through use, are washed, returned, and used by their owner.

## Limitations

This is a deliberately small scenario model, not a general kitchen physics engine. Dough quality is a two-state abstraction, oven behavior is limited to preheating, and the gift threshold is authored for this story. The siblings and recipient are fixed characters. There are two optional vignettes, but a length-eight route can contain only one. The two endings cover a viable biscuit gift and a sincere fallback note; they do not model every possible family response. The reference story is a longer authored narrative, not a promise that every reference beat appears in every generated route. A compatible route and a valid trace do not prove literary quality or broad semantic diversity.

## Tests and execution status

The test file covers both lengths over 100 seeds, exact replay, strict parameter validation, illegal actions without caller mutation, omission of optional scenes, object/location continuity, dough conservation, paired outcome counterfactuals, and the command-line entry point. **Tests were not run for this response: no execution tools were available.** The provided `check_pack.py` was also not run. No test result is claimed.