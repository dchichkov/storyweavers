Build a family of complete stories, keeping consequential spoken dialogue.
Use a compact data-driven implementation so the story's alternatives really
execute, rather than existing only as parameter names.

- Author three or four distinct initial problems with two genuinely different
  compatible solutions each. Define the supported paths before the renderer:
  each path specifies the initial physical problem, needed clue or knowledge,
  action sequence, state changes, and final scene. Use the same registry for
  selection, Python validation, and emitted ASP compatibility facts.
- Every advertised path must execute its own appropriate actions and render
  those actions. Do not choose the prose by problem while changing state by an
  unrelated solution parameter. Facts required by an action must be established
  earlier; a solved state must lead to the ending, not repeat the last action.
- Compose the prose from authored event scenes, with several seeded alternatives
  for openings, useful spoken exchanges, reactions, and final images. Optional
  scenes must fit the current state. Vary the difficulty, information learned,
  decisions, and outcome as well as wording; keep each individual story concrete
  and fluent. Do not repeat a fixed moral or pad with irrelevant random detail.
- Names come from entity labels, not IDs or hardcoded sample names. Keep each
  object's properties, action, clue, location, and ending consistent within its
  path. Store noun phrases and complete sentences separately; QA is a full
  explanation of that executed path, not a list of alternative possible endings.
- Ordinary -n sampling returns exactly n seeded raw draws, retaining duplicates.
  Never loop until n unique stories exist. Sample omitted meaningful parameters
  and prose alternatives from stable ordered collections, without defaulting
  every draw to one path. Explicit incompatible choices still raise StoryError.
- Verification should check actual branch outcomes, grounded QA, and a spoken
  exchange involving both characters, not impose arbitrary eight- or twelve-turn
  quotas. Check every supported path and reject unresolved template fields.
  Define every accessed dataclass field and initialize meters before incrementing.
  Locate results.py and asp.py through the script's ancestor directories so the
  supplied nested Target file also works when executed directly.
