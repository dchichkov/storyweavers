# The Borrowed Blue Can

An offline mini-adventure set in a community greenhouse. Mina borrows Ivo’s watering can to help Rosa’s thirsty seedlings. Water supply, heat, soil dryness, a leaking seam, and available shade determine what the local actions can accomplish. The stable ending protects the seedlings for the afternoon; the cuttings ending acknowledges that the tray could not be saved and roots viable tips instead.

## Run

From the repository root:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 12 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
```

Optional parameter overrides are a JSON file. For example:

```bash
printf '{"heat":"mild","can_leak":false,"water_units":2,"soil_dryness":1,"shade_cloth":true}\n' > /tmp/kite-stable.json
python -m storyscenes.mini_adventures.kite.world --seed 4 --scenes 7 --params /tmp/kite-stable.json
```

The CLI prints prose only. In Python, use `generate(seed, count=7, params=Parameters(...))` for a JSON-native result. `replay(params, path)` replays an explicit scene path and returns its episodes.

## Explicit ending recipes

The selector prefers Rosa’s shade-advice vignette for a seven-scene route when unsealed water is sufficient and a screen exists. Otherwise it prefers the label vignette. These recipes therefore select distinct endings at either supported length:

- **Stable seedlings:** `Parameters(heat='mild', can_leak=False, water_units=2, soil_dryness=1, shade_cloth=True)`. A seven-scene generated route can use Rosa’s advice, hang the screen, and finish `seedlings_stable`. For an explicit replay path, use `('notice', 'borrow_can', 'talk_to_rosa', 'fill_and_water', 'make_shade', 'return_can', 'ending_stable')`.
- **Rooted cuttings:** `Parameters(heat='hot', can_leak=True, water_units=1, soil_dryness=2, shade_cloth=False)`. Even with the label band, the supply cannot meet the seedlings’ need; the tray is sheltered and viable tips are rooted. An explicit seven-scene path is `('notice', 'borrow_can', 'read_labels', 'fill_and_water', 'make_shade', 'return_can', 'ending_cuttings')`.

At eight scenes both optional vignettes are enacted. The parameters still determine whether the final scene confirms stable seedlings or roots cuttings.

## Scenes and state

The executable pool has seven shared scenes and two mutually exclusive endings. The label-reading and Rosa-conversation vignettes are optional at seven scenes and both appear at eight. `scene_inventory.json` maps about twenty reference encounters onto those nine executable IDs, and explains where multiple reference beats were consolidated.

`LocalPlay` owns a detached state and records each atomic action’s equality preconditions and changed keys. `play_scene` rejects incompatible scenes before committing anything. The bounded search commits only the chosen route; failed speculative branches do not enter its state or prose. The borrowed can remains Ivo’s, is actually used to deliver water, and is rinsed and returned. A label band used to seal a leak is returned to its clip.

## Limitations and verification status

The physical model is intentionally small: one tray, one shared water supply, a one-unit leak loss, and two shade options. It is not a general plant-growth simulator. The cuttings ending treats two viable tips as salvageable in this scenario. Prose is authored per scene and conditioned on enacted outcomes; it is not a general-purpose language generator. Parameter values are validated, but arbitrary edits to state are not a supported authoring interface.

**Tests were not executed in this response because no execution tools were available.** The test file covers both lengths over 100 seeds, replay and trace reconstruction, invalid parameters, illegal actions without mutation, optional-scene omission, object continuity, and paired counterfactuals. The supplied `check_pack.py` was not run. No success or word-count verification is claimed here.
