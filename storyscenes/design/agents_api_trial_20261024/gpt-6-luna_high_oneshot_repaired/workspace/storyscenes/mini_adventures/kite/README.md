# The Reel That Came Back

An offline, seeded kite-flying mini-adventure. It uses the supplied `LocalPlay` helper and standard-library Python only; it makes no network or model calls. The reference story was written before the simulation and is preserved as an independent target, not a repair note for generated prose.

## Run

From the repository root:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 2026102401 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
```

`generate(seed, count=7|8, params=None)` returns a JSON-native result with the selected path, per-scene event traces, prose and final state. `replay(params, path)` reproduces the episodes. Every generated story contains exactly seven or eight scenes; the two optional scenes are `ribbon` and `practice`. Seven-scene routes include one of them, while eight-scene routes include both. Scene search is seeded and bounded; rejected speculative branches never enter the returned trace.

## Parameters and ending recipes

All four keyword-only parameters are validated integers:

- `wind`: 1–3. Stronger wind needs a stronger frame and line handling.
- `reel_wear`: 0–2. A more worn borrowed line has less margin.
- `frame_strength`: 1–3. Workshop willow quality affects the build.
- `shyness`: 1–3. The invitation offers Pavel a quieter entry at the highest level; handing him the reel requires sufficient comfort. The practice vignette can earn that comfort.

`parameters(seed)` deterministically selects values. For exact paths, use `replay` with the following parameter recipes; these are scene-by-scene routes, not prewritten whole-story variants:

```python
from storyscenes.mini_adventures.kite.world import Parameters, replay

# Shared flight: Pavel holds the borrowed reel and leads the line.
shared = Parameters(wind=1, reel_wear=0, frame_strength=3, shyness=1)
shared_path = ("workshop", "build", "invite", "practice", "hand_reel",
               "launch", "ending_airborne_shared")

# Guided flight: Nia keeps the reel; Pavel chooses to guide the kite's tail.
guided = Parameters(wind=1, reel_wear=0, frame_strength=3, shyness=1)
guided_path = ("workshop", "build", "invite", "ribbon", "keep_reel",
               "launch", "ending_airborne_guided")

# Safe landing: poor frame, worn line and strong wind defeat even both vignettes.
grounded = Parameters(wind=3, reel_wear=2, frame_strength=1, shyness=3)
grounded_path = ("workshop", "build", "invite", "ribbon", "practice",
                 "keep_reel", "launch", "ending_grounded")

for params, path in ((shared, shared_path), (guided, guided_path), (grounded, grounded_path)):
    episodes = replay(params, path)
    print(episodes[-1].after["story.outcome"])
```

The endings are `shared_flight`, `guided_flight`, and `safe_landing`. The grounded ending is a completed afternoon: the kite is safely recovered, Pavel has participated, and the still-useful borrowed reel is returned. The two airborne endings differ in who held the spool and how Pavel contributed.

## State and limits

The reel's owner remains Tamsin throughout. Its custody changes during the outing, the flight consumes some string, and each ending returns it to the workshop ready for another flight. The launch result depends on the actual frame, wind, ribbon, practice and reel-wear state. Pavel's comfort affects whether he can choose the spool-holder role. Omitting a vignette omits its state effects.

This is a small scenario-specific model, not a general kite or weather simulator. It has four parameters, three endings and two optional scenes; characters do not split up, and scenes do not repeat. Generated prose is authored locally from enacted outcomes, but literary variety is limited by the scene pool. A legal route does not guarantee that every reader will find it compelling.

## Tests actually run

No execution tools were available in this single-response run. The test suite is supplied but **was not run**, and no test success is claimed. In particular, the requested 100-seed checks and the read-only `check_pack.py` integration check remain unexecuted here. The parent should run its independent checks against these untouched files.
