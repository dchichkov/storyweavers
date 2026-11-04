# The Place We Saved

An offline, story-first mini-adventure about cousins Mara and Kit borrowing Aunt Salma’s blue picnic blanket and trying to welcome their late cousin Rowan. The module path is the harness name; there is no kite story in this pack.

## Run it

From the repository root, with the supplied `storyscenes` package available:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py .
```

The CLI prints only the generated prose. The Python API returns the path, validated parameters, event traces, final state, and bounded-search attempt count. `replay(params, path)` reproduces the episodes without searching. All scene-local changes use the supplied `storyscenes.mini_adventures.local_play.LocalPlay`; failed local actions are atomic.

Every seven-scene route contains the six core encounters and one ending. An eight-scene route includes exactly one of the two optional vignettes. Optional encounters do not run when omitted. The seeded search is bounded, deterministic, and speculative states are discarded.

## Parameter recipes for the endings

The CLI accepts a JSON object of parameter overrides. Save one of the objects below to a file, then pass it with `--params`. Other parameter fields are filled from the selected seed and validated normally.

**Shared lunch, dry blanket (`ending_feast`):** the blanket is heavy enough for the mild gust and the basket is latched.

```bash
printf '%s\n' '{"blanket_weight":3,"gust_force":1,"basket_latched":true,"priority":"blanket","bread_rolls":3,"delay_minutes":14}' > /tmp/kite-feast.json
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7 --params /tmp/kite-feast.json
```

**Shared lunch, wet blanket (`ending_damp`):** the strong gust wets the light blanket; choosing to catch lunch saves the rolls.

```bash
printf '%s\n' '{"blanket_weight":1,"gust_force":3,"basket_latched":true,"priority":"lunch","bread_rolls":3,"delay_minutes":14}' > /tmp/kite-damp.json
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7 --params /tmp/kite-damp.json
```

**Fruit after lost rolls (`ending_apples`):** the strong gust threatens both; the cousins save the blanket and loose rolls scatter. They still welcome Rowan with the apples and an honest account of what happened.

```bash
printf '%s\n' '{"blanket_weight":3,"gust_force":3,"basket_latched":false,"priority":"blanket","bread_rolls":3,"delay_minutes":14}' > /tmp/kite-apples.json
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7 --params /tmp/kite-apples.json
```

`priority` is the cousins’ consequential response when the gust makes both blanket and lunch vulnerable. A latched basket, a mild gust, or a sufficiently heavy blanket can remove that trade-off; the endings follow the enacted state rather than a fixed story variant. Valid ranges are blanket weight and gust force 1–3, one to four rolls, and a delay of 5–30 minutes. `basket_latched` is boolean and `priority` is `blanket` or `lunch`.

## Limits and verification status

This is a small scenario-specific model, not a general physics simulation. It tracks the blanket’s owner, holder, place, and condition; lunch conservation; one gust response; the cousin’s arrival and welcome; and the two optional vignettes. It does not simulate weather beyond the authored gust, exact distances, or arbitrary character choices. Names, event order, and prose are authored rather than produced by an LLM. Seven-scene routes omit both vignettes; eight-scene routes include one, never both.

**Tests were not executed in this response because no execution tools were available.** `test_world.py` covers both lengths over 100 seeds, replay and event traces, parameter validation, atomic illegal actions, optional omission, object/location continuity, distinct ending recipes, and a paired gust counterfactual. The repository’s read-only `check_pack.py` should also be run by the harness; no successful run is claimed here.
