# The Pears We Could Reach

A standard-library-only, local-play adventure in a small orchard. Mira and Theo borrow a picking basket, gather only fruit they can take safely, share a snack, and return the useful basket clean. `world.py` uses the supplied `storyscenes.mini_adventures.local_play.LocalPlay`; it does not change shared engine files or call a model.

## Run it

From the repository root:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py .
```

The CLI prints the generated prose. The Python interface also returns the path, parameters, per-scene before/after states, atomic event traces, final outcome, and bounded scene-attempt count. `replay(params, path)` reproduces the recorded episodes.

## Validated parameters and ending recipes

`Parameters` is keyword-only. Its six validated fields are `reach_cm` (integer 100–190), `windy` (boolean), `low_ripe` (integer 1–4), `windfalls` (integer 1–3), `basket_handle` (`'sound'` or `'frayed'`), and `crate_level` (boolean). Reach and wind determine whether the low branch is safe; fruit availability and handle capacity determine the amount gathered; crate stability determines whether the optional crate scene can offer a table.

A full shared harvest is reproducibly available with:

```python
from storyscenes.mini_adventures.kite.world import Parameters, generate
p = Parameters(reach_cm=160, windy=False, low_ripe=3, windfalls=1,
               basket_handle='sound', crate_level=True)
row = generate(0, count=7, params=p)
assert row['path'][-1] == 'ending_full'
```

A complete small-snack ending is reproducibly available with:

```python
from storyscenes.mini_adventures.kite.world import Parameters, generate
p = Parameters(reach_cm=120, windy=True, low_ripe=3, windfalls=1,
               basket_handle='frayed', crate_level=False)
row = generate(0, count=8, params=p)
assert row['path'][-1] == 'ending_small'
```

The first recipe permits at least two safely reachable pears in a sound basket. The second permits one windfall in the limited-capacity basket; the friends share it and finish the day. Neither ending damages the tree or leaves the borrowed basket unreturned. The seed chooses which of the two optional vignettes appears in a seven-scene story and their order in an eight-scene story; the core scenes remain compatible.

## Scene and state design

There are nine executable scene IDs: borrowing, two optional vignettes, survey, harvest choice, picking, sharing, and two mutually exclusive endings. The twenty-entry inventory maps reference encounters to those executable IDs and identifies consolidations. A scene omitted from the path contributes no state effects. The crate is never used as a ladder. The basket travels with the friends, carries the pears to the snack, and is cleaned and returned.

The local simulation is deliberately small. It records validated integer/boolean/string state, guarded atomic actions, and equality preconditions. A safe low branch requires calm conditions and at least 145 cm of stated reach; otherwise the friends gather only configured windfalls. A frayed handle limits the basket to one pear. All stories share authored local scenes rather than selecting prewritten whole-story variants. Text aims for 40–70 whitespace-separated words per scene.

## Limitations and verification status

This is a scenario-specific abstraction, not a general model of trees, fruit quality, or child safety. The two endings differ in harvest outcome and payoff, but the friends' central goal remains a shared snack. Names and central motives are fixed; diversity comes from parameter-driven actions, amounts, outcomes, optional encounters, and callbacks. The reference story is an authored reading, not a guarantee that every generated route follows its exact details.

Reference prose length is approximately 1,000 words, excluding its heading; this is an estimate, not a tool-counted result. Tests were **not executed** in this single-response run because no execution tools were available. In particular, neither `test_world.py` nor the supplied `check_pack.py` has been run here; the commands above are instructions, not claimed results.
