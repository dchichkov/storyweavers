# The Courtyard Cart

A self-contained, offline mini-adventure about Jo, Mina, a borrowed spanner, and a toy cart whose rattle has the wrong first diagnosis. The executable scenes use the shared `LocalPlay` helper and standard-library Python only. There is no runtime model, network access, or external dependency.

## Run it

From the repository root:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 23 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py .
```

The command prints just the story. `--scenes` accepts 7 or 8. `--params` may point to a JSON file with any subset of the validated `Parameters` fields, for example:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 4 --scenes 8 --params /tmp/cart.json
```

## Explicit ending recipes

These are complete parameter objects; save each as JSON and pass its filename with `--params`. The other values are chosen to make the physical route easy to inspect.

**Repaired, with Jo admitting the first mistake promptly:**

```json
{"washer_available": true, "spanner_fits": true, "cart_load": 2, "bench_level": true, "admission_style": "early"}
```

This reaches `ending_repaired`. With the same physical values and `"admission_style": "late"`, Jo postpones the admission and earns `ending_rebuilt` by owning the mistake before the story closes.

**Safe stop when no proper washer is available:**

```json
{"washer_available": false, "spanner_fits": true, "cart_load": 2, "bench_level": true, "admission_style": "early"}
```

This reaches `ending_stopped`. The cart is not falsely declared repaired: it is secured as a sign stand, and Mina completes the delivery by hand. A missing washer cannot be replaced by an unsafe cardboard shim.

For example, run any recipe with:

```bash
printf '%s\n' '{"washer_available":true,"spanner_fits":true,"cart_load":2,"bench_level":true,"admission_style":"early"}' > /tmp/cart.json
python -m storyscenes.mini_adventures.kite.world --seed 4 --scenes 7 --params /tmp/cart.json
```

## Parameters and their consequences

`Parameters` is a keyword-only frozen dataclass and rejects wrong types and out-of-range values.

- `washer_available` (boolean): determines whether the correct spacer can be installed or the safe-stop ending is required.
- `spanner_fits` (boolean): if false, the first local play checks the jaws and enacts an exchange for Len's adjustable spanner before turning the nut.
- `cart_load` (integer 1–3): the cart safely carries at most two pots. A third is set aside during repair and carried separately during a successful delivery.
- `bench_level` (boolean): a sloping bench requires a wedge to steady the cart; a level bench does not.
- `admission_style` (`"early"` or `"late"`): selects the enacted response to Jo's mistake and the matching repaired ending. The late route includes an apology before the story ends.

Two genuinely optional vignettes are `chalk_names` and `measure_story`. Seven-scene stories omit both; eight-scene stories include exactly one. Their effects appear only if the scene is enacted and may be recalled in the ending.

## State, actions, and routes

The adventure has seven required story beats: borrow, wrong first attempt, reinspect, respond to the mistake, repair or safely stop, test or mark out of service, and ending. The optional vignette accounts for the eighth scene. A bounded seeded search composes only compatible scenes; rejected branches are detached speculative runs and cannot affect the selected trace. `replay(params, path)` re-enacts a saved path and reproduces its states, atomic events, and prose.

The state tracks the spanner's owner and location, whether it fits and has been used, the washer's location, the wheel's play and rotation, the cart's load and location, the delivery, and the children's trust and admission. The ending returns the borrowed spanner and has Len use it on his vise. This is an enacted use, not custody alone. A missing washer leads to an emotionally complete failure: the children finish the delivery safely, identify the cart's status, and accept what happened without pretending the repair succeeded.

## Limitations and verification status

This is a small scenario-specific model, not a general mechanics simulator. It has a fixed cast, fixed scene pool, one cart, and exactly seven or eight scenes; it does not simulate arbitrary tool geometry, wear, or unlisted repairs. Seeded selection changes scene composition and local action paths, not a claim of unlimited literary diversity. Prose is authored per scene and conditioned on enacted state.

`reference_story.md` was written before implementation and is preserved as its own successful reference route. Its prose is intended to be about 1,000 words excluding the title; the word count and generated stories were not executed or inspected in this response. No execution tools were available here, so **the included tests and `check_pack.py` are unexecuted**. The test suite is provided for the parent harness to run; no test result is claimed.
