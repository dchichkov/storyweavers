- Keep dictionary keys aligned with StoryParams fields. resolve_params should
  choose from the actual keys of lookup dictionaries, and generate should fail
  closed with StoryError for invalid params instead of raising KeyError.
- Default generation must not silently substitute a curated story. `python file.py
  --seed N --qa` must generate from the params resolved for that seed. If those
  params are invalid, fix `resolve_params()` to choose only valid params
- `resolve_params()` must choose only from `valid_combos()` after applying CLI filters.
  Random generation should never select an invalid combination and rely on `generate()`
  to reject it.
- Before calling `propagate()`, initialize every `world.facts[...]`, entity `attrs`,
  `meters`, and `memes` value that any rule reads. No rule should depend on a fact
  assigned later in `tell()`.
- Before `tell()` or `story_qa()` emits text, convert every selected
  `StoryParams` key into a concrete entity/object/config object with a stable
  child-readable display label.
- Prose and story QA may use names and labels only. Do not emit role keys or
  placeholders such as `child`, `adult`, `hero`, `helper`, `item`, `tool`,
  `problem`, raw ids, dataclass reprs, `None`, or blank slots.
- Every sentence template that interpolates a selected value must have a
  complete fallback phrase.
