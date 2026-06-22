# gpt-5.4-mini Direct-Service Reliability Addendum v2

This addendum supersedes v1 after a direct-service run still produced mostly
non-runnable scripts. Optimize for runnable, evaluable storyworlds before adding
domain richness.

Hard gate:
- The script must pass these commands from the repository root:
  - `./.venv/bin/python TARGET.py --json --seed 777`
  - `./.venv/bin/python TARGET.py -n 3 --seed 42 --json`
  - `./.venv/bin/python TARGET.py --qa --seed 777`
  - `./.venv/bin/python TARGET.py --verify`
- If a design choice makes any of those hard to satisfy, simplify the world.
  Prefer three valid knobs and a short reliable simulator over a rich registry
  that crashes.

Structure:
- Define `StoryParams` exactly once before any `CURATED`, constants, lookup
  entries, or module-level `StoryParams(...)` calls. Never instantiate
  `StoryParams` before the class exists.
- Give every `StoryParams` field a default or ensure `resolve_params()` supplies
  it every time.
- `resolve_params()` must never raise `StoryError` during ordinary random
  generation with no CLI filters. If filtered choices leave no combo, choose a
  valid fallback or raise only for explicit invalid user filters.
- Ensure `valid_combos()` returns at least 3 combinations and that `-n 3 --json`
  can produce 3 samples without crashing.

Type discipline:
- Keep registries consistently typed. If `MIXUPS` stores strings, do not call
  `.id`; if code calls `.id`, store dataclass objects. Do not mix strings and
  objects in the same registry.
- Before calling `world.get("x")`, make sure `tell()` has already added entity
  `"x"`. Prefer storing direct entity references in `world.facts` after creation.
- Every rule must tolerate the current world state. Initialize all facts,
  attrs, meters, memes, and helper fields before `propagate()`.
- Do not rely on optional attributes like `.help_line`, `.phrase`, `.region`,
  `.covers`, or `.protective` unless every relevant object defines them.

Syntax and prose:
- Avoid complicated quoted f-string dialogue. Use simple sentence assembly:
  `world.say(f'{speaker.name} said, "{line}"')` only when both quotes match.
- Never mix quote styles across one string literal. Mentally compile every
  f-string that contains dialogue.
- Avoid doubled text such as "The the", wrong pronouns, or role words as names
  ("boy came over and she..."). Use entity names for actors and role labels only
  in descriptions.

QA:
- `story_qa` must vary across the `-n 3 --json` samples. Build each question
  from `StoryParams` and `world.facts` values such as actor, place, object,
  conflict, helper, method, and ending.
- Do not repeat an identical story-specific QA pair across variants. If a QA
  item is generic world knowledge, put it in `world_qa`, not `story_qa`.
