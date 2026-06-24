- QA must be grounded in simulated state/history, with natural two-or-three
  sentence answers where the trace supports cause/effect.
- Avoid scaffold leaks, raw template fragments, and implementation jargon.
- Do not copy an existing world. Create a fresh tiny domain from the seed,
  and progress from a fresh story to a complete storyworld.
- Make complete stories: clear premise, state-driven turn, and ending image
  that proves what changed.
- Before `tell()` or `story_qa()` emits text, convert every selected
  `StoryParams` key into a concrete entity/object/config object with a stable
  child-readable display label.
- Prose and story QA may use names and labels only. Do not emit role keys or
  placeholders such as `child`, `adult`, `hero`, `helper`, `item`, `tool`,
  `problem`, raw ids, dataclass reprs, `None`, or blank slots.
- Every sentence template that interpolates a selected value must have a
  complete fallback phrase.
