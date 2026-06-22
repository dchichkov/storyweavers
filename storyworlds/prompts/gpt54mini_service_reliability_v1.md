# gpt-5.4-mini Direct-Service Reliability Addendum v1

Use this addendum when optimizing the direct-service storyworld prompt after
seeing generated scripts fail downstream sampling, quality, or QA-static checks.

Reliability requirements:
- The target file may live inside a nested run directory under
  `storyworlds/worlds/`. Do not assume `dirname(dirname(__file__))` is
  `storyworlds/`. Use a robust import bootstrap that walks parent directories
  until it finds `results.py`, then insert that directory into `sys.path`.
- The script must run successfully in all of these modes:
  `--json --seed 777`, `-n 3 --seed 42 --json`, `--qa --seed 777`, and
  `--verify`.
- Avoid quote-sensitive f-string dialogue such as
  `f"Maybe it's lunch," {name} said...`. Put dialogue quotes entirely inside
  the f-string or build the speaker/action as separate sentence fragments.
- Before emitting, mentally compile every f-string, dictionary literal, and
  multiline string. Syntax errors are worse than weak prose.
- `resolve_params()` must generate varied valid params for `-n`; do not make
  only the default seed work.

Story and QA requirements:
- `story_qa` must be parameterized by `StoryParams` and `world.facts`, not a
  repeated literal list. Across `-n 3 --json`, story QA should vary with the
  selected place, actor, object, conflict, helper, and outcome.
- Do not duplicate the same question/answer pair across variants unless the
  story state is genuinely identical. Prefer cause/effect answers tied to the
  simulated turn.
- Avoid event-log phrasing and repeated summary sentences. The story should have
  a clear beginning, a state-driven turn, and a final physical image proving the
  change.
- Keep child-facing prose polished: no doubled punctuation, doubled articles,
  capitalized mid-sentence fragments, raw ids, or scaffold language.
