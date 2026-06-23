- Write a complete, valid, stdlib-only Python script.
- Import and use storyworlds/results.py and storyworlds/asp.py as example worlds.
- Include StoryParams, build_parser, resolve_params, generate, emit, -n, --all,
  --seed, --trace, --qa, --json, --asp, --verify, and --show-asp.
- Include a Python valid_combos checker plus an inline ASP twin. --verify must
  exit 0 when run from the repo with ./.venv/bin/python.
- --verify must run at least one normal generate/emit smoke test with default or
  curated params and fail if ordinary story generation crashes.
- QA must be grounded in simulated state/history, with natural two-or-three
  sentence answers where the trace supports cause/effect.
- Avoid scaffold leaks, raw template fragments, and implementation jargon.
- Do not copy an existing world. Create a fresh tiny domain from the seed,
  and progress from a fresh story to a complete storyworld.
- Make complete stories: clear premise, state-driven turn, and ending image
  that proves what changed.
- Give optional dataclass fields defaults. When constructing dataclasses in
  CURATED, lookup tables, or constants, use keyword arguments for every field.
  Do not mix positional and keyword arguments in the same dataclass call.
- Define exactly one top-level @dataclass class StoryParams before CURATED,
  resolve_params, generate, verify, or any module-level StoryParams instances.
  Construct StoryParams with keyword arguments, not positional argument lists.
- Objects used as actors/helpers in prose or QA must either be Entity instances
  or implement the same fields/methods you call, especially pronoun(), attrs,
  tags, and meters. Do not call .pronoun(), .attrs, or .meters on arbitrary
  domain config objects unless those attributes are defined.
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
