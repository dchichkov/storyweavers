# gpt-5.4-mini Direct-Service Reliability Addendum v3

Use this addendum after the scripted repair layer is enabled. Do not spend
tokens restating mechanical Python mistakes that the repair pass can fix. Focus
on choices the repair script cannot infer safely: valid story space, consistent
world state, and story/QA quality.

Generation target:
- Prefer a reliable world over a brittle one: 3-5 registries, at least 4 
  valid `valid_combos()` rows for ordinary unfiltered generation, and
  enough variation that `-n 1000 --seed 42 --json` yields distinct samples.
- Keep `StoryParams` fields as simple CLI-safe keys and names, not dataclass
  objects. Convert those keys to registry objects inside `generate()` or `tell()`.
- `resolve_params()` should only choose combinations that `generate()` accepts.
  If the user supplies filters that leave no valid combo, raise `StoryError`.
  
World-state discipline:
- Add every entity before any rule or prose path calls `world.get(...)`.
- Initialize all `world.facts` entries before `story_qa`, `generation_prompts`,
  or causal rules read them. Store direct entity references for actors/helpers
  and direct config objects for selected place/object/problem/method.
- Causal rules must be idempotent: set a fired marker or solved/seen fact before
  returning an event, so repeated propagation reaches a stable state.

Story and QA quality:
- Render actual names or labels in prose and QA. Never leak role placeholders
  such as `child`, `hero`, `helper`, `adult`, raw ids, or dataclass reprs into
  child-facing text.
- The story must have a premise, a state-driven turn, and a final physical image
  proving what changed. Do not end with a generic moral or an event-log summary.
- `story_qa` must be built from `StoryParams` and `world.facts` and vary with
  actor, place, object, problem, helper/method, and ending. Put generic
  definitions in `world_qa`, not in `story_qa`.
