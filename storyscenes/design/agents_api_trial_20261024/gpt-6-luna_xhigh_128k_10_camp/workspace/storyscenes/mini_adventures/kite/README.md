# The Last Bright Bar

An offline, story-first mini-adventure set at a family campsite. Mira borrows Dad’s lantern to help her frightened little brother Kit find his missing stuffed fox, Pip, before supper. The generated route has exactly seven or eight compatible scenes. Each paragraph is an authored local play rendered from actions that changed the shared state.

## Run it

From the repository root:

```sh
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 41 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py .
```

The CLI prints prose. To override parameters, write a JSON object to a file and pass `--params /path/to/overrides.json`; omitted fields use the seeded defaults. For example:

```sh
printf '{"toy_site":"fern_hollow","kit_memory":"fern_hollow","daylight_minutes":0,"lantern_charge":1,"toy_covered":true,"ground_wet":true,"search_policy":"conserve"}' > /tmp/found.json
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8 --params /tmp/found.json
```

## Explicit ending recipes

A recovered-toy ending is guaranteed by aligned memory: `toy_site='fern_hollow'`, `kit_memory='fern_hollow'`, `daylight_minutes=0`, `lantern_charge=1`, `toy_covered=True`, `ground_wet=True`, `search_policy='conserve'`. The lantern illuminates the remembered site, Kit recovers Pip, and the siblings return by campfire glow if they have no charge left.

A complete comfort-without-the-toy ending is guaranteed by a mistaken memory and no resources for a second look: `toy_site='fern_hollow'`, `kit_memory='tent_edge'`, `daylight_minutes=0`, `lantern_charge=1`, `toy_covered=False`, `ground_wet=True`, `search_policy='sweep'`. The first search spends the only lantern charge; no daylight remains for the other site. The children return safely and Kit accepts a blanket rather than being left with an unresolved, conditional promise.

For a consequential second-sweep success, use `toy_site='fern_hollow'`, `kit_memory='tent_edge'`, `daylight_minutes=0`, `lantern_charge=2`, `search_policy='sweep'`. Changing only the policy to `conserve` produces the loss ending: the battery and dark do not permit another look after the first sweep.

These recipes can be passed directly in Python as `Parameters(...)`, or encoded as JSON overrides for the CLI. The parameter set is validated: actual toy site, Kit’s remembered site, remaining daylight, lantern charge, whether the toy is covered, wet ground, and Mira’s search policy all affect enacted actions or outcomes.

## World and limits

The state distinguishes Dad’s ownership of the lantern from the siblings’ temporary custody. It tracks its charge, whether it is lit, where it is held, toy location, the children’s shared location, fear and courage, search progress, and the route home. The shadow and reflector scenes are optional vignettes; omitting one does not apply its effects elsewhere. A seven-scene route selects one vignette; an eight-scene route selects both.

The bounded seeded search explores compatible scene orders before committing a route. Each local action uses `storyscenes.mini_adventures.local_play.LocalPlay`, validates a candidate state before commit, and records equality requirements and changed values. Failed actions do not mutate the caller’s state. Search branches are speculative only; rejected routes are not narrated. Replay rebuilds the same action trace and prose.

This is a deliberately small model, not a general campsite physics engine. The search policy is an authored choice, the two toy sites are abstractions, and the lantern’s battery is represented in discrete units. The scenes do not model every handoff, tent peg, or cooking action. The generated prose has not been human-rated, and route compatibility is not a guarantee of literary quality.

## Tests actually run

Tests were **not executed in this single-response run because no execution tools were available**. No result is claimed for `test_world.py`, the 100-seed checks, or `check_pack.py`. The commands above are provided for an environment with the supplied repository files and Python standard library. The tests cover both lengths over 100 seeds, replay and event traces, invalid parameters, failed actions, optional omission, object/location continuity, and paired counterfactuals.
