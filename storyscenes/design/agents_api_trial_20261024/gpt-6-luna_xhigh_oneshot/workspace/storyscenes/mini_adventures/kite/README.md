# The Blue Reel: runnable mini-adventure

This pack uses only the Python standard library and the supplied `LocalPlay` / runtime. It makes no network or API calls. Run commands from the repository root, where `storyscenes` is importable.

## Run and replay

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py .
```

The module prints the generated prose. `generate(seed, count=7 or 8, params=...)` returns the JSON-native path, event traces, state snapshots, and final state. `replay(params, path)` returns the same episodes for any compatible path. Seeded parameters are reproducible; scene search is bounded and speculative episodes are detached from committed state.

`Parameters` has six validated, consequential fields:

- `wind`: 1–5; the usable flying range is 2–4.
- `gust`: 0–4; stronger gusts can snag the first lift and prevent a safe second run.
- `reel_length`: 12–45 metres; short line can prevent a repair or a sustained flight.
- `frame_sound`: whether the bamboo spar starts sound. A repair consumes three metres of the borrowed reel when enough line is available.
- `tail_weight`: 1–4; only a balanced tail (2 or 3) is stable in this small model.
- `shyness`: 1–4; this changes the invitation and whether June first takes the reel or the tail.

## Explicit ending recipes

Use a JSON file to override the seeded values. The omitted CLI defaults are filled from the seed, but these examples set every parameter explicitly.

```bash
printf '%s\n' '{"wind":3,"gust":1,"reel_length":32,"frame_sound":true,"tail_weight":2,"shyness":2}' > /tmp/kite-flight.json
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7 --params /tmp/kite-flight.json
```

That recipe makes `ending_flight` possible: the frame, tail, line, and wind are suitable, and June is comfortable taking the reel. The optional ribbon vignette is not required.

```bash
printf '%s\n' '{"wind":5,"gust":1,"reel_length":32,"frame_sound":true,"tail_weight":2,"shyness":2}' > /tmp/kite-grounded.json
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8 --params /tmp/kite-grounded.json
```

That recipe ends at `ending_grounded`, because a wind strength of 5 is outside the safe flying range. The kite is folded, signed, displayed in the workshop window, and the borrowed reel is returned; the ending is complete rather than a promise to try later. Either recipe works at both supported lengths. An eight-scene route includes exactly one of the two optional vignettes; a seven-scene route includes neither.

## Design and limitations

The seven required encounters are borrowing, inviting, preparing, walking to the common, first lift, responding, and a compatible ending. `vignette_mark` and `vignette_ribbon` are separate, optional encounters. Neither is simulated when omitted. The inventory maps about twenty reference beats to executable scenes and explains consolidated actions.

The ending depends on the enacted frame, string, wind, tail, and local choice. The reel pays out line, may supply a repair, is rewound, and is returned to Tomas. June has agency in either ending: she may handle the reel or choose and hold the tail. The grounded outcome does not claim the kite flew.

This is a small scenario model, not a general kite or weather simulator. It has two terminal outcomes, fixed characters, no repeated scenes, and a deliberately narrow physical state. The reference story is an authored example, not a requirement that every generated route repeat its exact events. Prose is composed per scene from local state; it is not a prewritten whole-story variant system. Mechanical tests do not establish literary quality.

## Actual tests run for this response

**Not run.** This was a single-response run without execution tools. I did not run the unit tests, inspect generated first-draw stories, or run the read-only `check_pack.py`; no test results are claimed. From the repository root, run the commands above to verify the pack.