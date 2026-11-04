# The Moon Behind the Curtain

An offline mini-adventure about Leni and Jo, two friends who borrow a sewing kit to help Ivo, a shy puppeteer, recover and repair a lost moon prop before rehearsal. The reference story is preserved in `reference_story.md`; its heading is excluded from the requested prose-word range. It was drafted to approximately 1,000 words. I did not run a word-count script in this single-response environment.

## Run

From the repository root:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py .
```

The CLI prints the story prose. It accepts an optional JSON object of parameter overrides:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8 --params '{"needle":"sharp","thread":"long","button_strength":"sound","curtain_weight":"heavy","minutes":4,"spare_button":false}'
```

Every generated route contains exactly seven or eight unique scenes. Seven-scene stories enact one of the two optional vignettes; eight-scene stories enact both. A scene is a local play built from guarded `LocalPlay` actions. The seed affects parameter selection and bounded scene search, not a stored whole-story variant. `replay(params, path)` reproduces episodes, event traces, state, and prose.

## Parameters and ending recipes

All fields are validated by the keyword-only `Parameters` dataclass.

| Parameter | Valid values | Consequence |
| --- | --- | --- |
| `needle` | `sharp`, `blunt` | A sharp needle can make a secure seam; a blunt one limits the repair to a temporary tie. |
| `thread` | `long`, `short` | A long thread permits a strong stitch or knot; a short one restricts the repair. |
| `button_strength` | `sound`, `cracked` | A sound old button is a usable anchor; a cracked one needs an enacted spare-button vignette or a cloth-loop alternative. |
| `curtain_weight` | `light`, `heavy` | The friends part a light curtain or gather and hold a heavy one to recover the moon. |
| `minutes` | integer 4–8 | At eight minutes, a sharp needle and long thread can make a new cloth loop even without a sound button. |
| `spare_button` | `true`, `false` | If true, the optional button vignette can discover a replacement anchor. It is not available unless that scene is played. |

**Rod-puppet ending (`ending_rod`):** generate eight scenes so the whisper vignette is enacted, and choose a repair that can hold:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8 --params '{"needle":"sharp","thread":"long","button_strength":"sound","curtain_weight":"heavy","minutes":4,"spare_button":false}'
```

This gives Ivo confidence to choose the rod and a secure button stitch to pass the test.

**Shadow-story ending (`ending_shadow`):** use parameters with neither a sound button nor a viable spare, needle, thread, or extra time:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8 --params '{"needle":"blunt","thread":"short","button_strength":"cracked","curtain_weight":"heavy","minutes":4,"spare_button":false}'
```

The repair cannot be secured, so the friends complete the rehearsal as a shadow scene. This is a finished performance, not a promise to repair the prop later. A shadow ending can also happen with a sound repair if Ivo has not enacted the whisper scene and chooses not to operate the rod.

Use JSON booleans (`true`/`false`) and integer minutes in CLI overrides. Unknown keys, invalid types, and out-of-range values are rejected.

## Tests and limitations

The included tests cover both lengths across 100 seeds, replay equality, event preconditions and changes, parameter validation, atomic rejection, optional-scene effects, object/location continuity, repair counterfactuals, and both endings. **Tests were not executed in this response: no execution tools were available.** The commands above are provided for a local run; this README does not claim that they passed.

This is a small authored scenario, not a general physical simulator. It has fixed characters, a narrow set of repair abstractions, and two authored ending forms. The seed changes local outcomes and scene composition but does not create unlimited literary diversity. Tests establish mechanical constraints only; they do not assess literary quality. No network, API, LLM, or non-standard-library dependency is used at runtime.
