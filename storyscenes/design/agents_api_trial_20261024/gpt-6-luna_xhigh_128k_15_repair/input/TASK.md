# Story-first pack authoring experiment

Create a complete runnable mini-adventure pack from these ingredients:
Task seed: 2026102416
Seed words: wheel, spanner, rattle
Setting: a courtyard repair bench
Premise: a child borrows a spanner to fix a shared toy cart and discovers that the first diagnosis was wrong.
The required kite/ module path is only the isolated harness name; write this new scenario, not a kite story.

Use the supplied engine files. This is a new scenario, not a rewrite of the
reference example. Produce files only under `storyscenes/mini_adventures/kite/`.
Do not modify shared files. Put any concrete library proposal in your pack's
`LIBRARY_PROPOSALS.md`. No dependencies beyond the Python standard library.
No API calls, network, agents, commits, or credentials. No LLM at runtime.

## Deliverables

1. `reference_story.md`: write a coherent 900-1100 word story FIRST. Ordinary
   wants, dialogue, complication, consequential choice, and an earned ending.
   Preserve this reference after implementation; do not rewrite it to excuse
   broken generated stories. Count prose words separately from its heading.
2. `scene_inventory.json`: an object with `scenes`, about 20 reference encounters.
   Each has `id`, `role`, `location`, `prerequisites`, `actions`, `consequences`,
   `prose_obligations`, and `implemented_ids` (a list of executable IDs).
   Explain consolidated encounters instead of pretending all are executable.
3. `__init__.py`, `world.py`, optional `prose.py`, and `test_world.py`.
4. `README.md`: commands, explicit parameter recipes for each ending, limitations,
   and actual tests run (or clearly state that you had no execution tools).

## Story and simulation

Generate complete stories of exactly 7 or 8 compatible scenes, about 40-70 words
per scene. Each scene has a short local play whose guarded actions change state.
Use 4-8 consequential validated parameters, two optional vignettes, at least two
meaningfully different endings, and at least two persistent cross-scene effects.
Do not use prewritten whole-story variants, name swaps or synonyms as diversity.

Use `storyscenes.mini_adventures.local_play.LocalPlay` for atomic actions/traces.
Scene guards and parameters must affect which actions and endings are possible.
No omitted scene may secretly execute effects. Failed actions must not mutate
the caller. Exploration must be bounded and speculative effects must not leak.
Keep physical state and embedded character motives consistent with `story.py`.

Track necessary state without narrating every bookkeeping step. A reader does
not need every door opening, container handoff or ownership check. Include such
actions when they matter to understanding, tension or payoff. Avoid legalistic
dialogue and instructional recitals of rules. Give characters distinct voices.
Reject arbitrary physical dependencies: a functioning oven does not need light
to keep heating. A constraint should have an ordinary understandable reason.
Return a borrowed object's usefulness, not only custody. Future plans are not
completed outcomes, but do not make every ending an unanswered conditional plan.
Let failures have an emotionally complete ending too.

## Exact interface

`world.py` exports:
- `Parameters`: keyword-only dataclass; validate types and ranges.
- `parameters(seed)`, `initial(params)`, `validate(state)`, `SCENES` (unique IDs).
- `guard(scene_id, state)` and `play_scene(params, state, scene_id)`.
- `generate(seed=0, *, count=8, params=None)` returns a JSON-native dict with
  `seed`, `parameters`, `scene_count`, `path`, `story`, `episodes`, `final_state`,
  and `search_attempts`.
- Episodes have `id`, `before`, `after`, `events`, `text`. Events have `action`,
  `requires` (equality mapping), `changes` (keys mapped to `{before, after}`).
- `story` equals episode text joined with two newlines. Every episode has an
  enacted non-no-op event. Use existing state keys, JSON-native values.
- `replay(params, path)` reproduces identical states, events and prose.
- Final state has `story.ended=True` and a nonempty `story.outcome`.
- `python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8` prints prose.

Test both lengths over 100 seeds, exact replay, invalid parameters, illegal
actions without mutation, optional omission, object/location continuity and
paired counterfactuals. The provided `check_pack.py` is a read-only integration
check. Do not change it, suppress failures or claim successful execution without
actually running it. The parent will independently test untouched code and read
unselected stories. No human repair will be counted as one-shot success.

## Output contract

Return one JSON object with `files`: a list of objects containing exactly `path`
and `content`, with complete UTF-8 text for every deliverable. Paths start with
`storyscenes/mini_adventures/kite/`. No omissions, placeholders or code fences.

For a coding harness, create these files, run tests, inspect several first-draw
stories and fix defects yourself within this single user task. Also write the
same JSON bundle to `/workspace/outputs/bundle.json` for artifact download.
For a single-response run without tools, output the bundle directly and label
tests unexecuted. Do not fabricate their results.
