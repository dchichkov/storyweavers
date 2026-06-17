# Storyworlds TODO

## Cleanup findings from Spark batch review

- Add a normal-generation smoke pass after `--verify`: `--verify` proves the
  ASP gate matches Python, but it does not prove sampled prose runs for every
  template branch. The Spark batch had worlds that verified but failed under
  `-n 1 --seed <seed> --qa`.
- Include at least a small deterministic seed sweep for each new world, for
  example seeds `0..9` with `--qa`, before calling a script done.
- Treat internal identifier leakage as a quality defect: prose and child-facing
  QA should not expose tokens such as `edge_patio`, `platform_three`,
  `move_to_wait_area`, or `Risk per hazard`.
- Watch for article composition bugs when registry phrases already include an
  article. Prefer registry phrases like `bright beach ball`, or render with the
  stored phrase directly instead of prefixing `a`.
- Humanize identifiers before they reach prose or Q&A. Entity keys such as
  `tiny_drummer` and action keys such as `ask_adult` are useful in traces and
  ASP facts, but child-facing text should render them as phrases.
- Avoid entity lookup by role-string unless the world actually stores role IDs.
  If entities are keyed by names, keep role references in `world.facts` or use a
  small helper such as `hero(world)` / `parent(world)`.
- Add a surface-quality lint later: underscore tokens in prose, doubled
  articles, unresolved template fields, and debug-rule strings are cheap to
  detect and caught several Spark artifacts.

## Current cleanup queue

- Re-run a human sample review on the Spark worlds after each cleanup batch.
  The cleanup pass raised normal sampled robustness from `88/100` to `100/100`
  over seeds `0..9`; the final lightweight artifact scan reported
  `flagged_files=0` for the 10 Spark worlds.
- `bakery_kindness.py`, `campfire_caution.py`, `forest_bridge.py`, and
  `snow_day_help.py` have had their first cleanup pass for underscore leakage
  and article composition. Keep them in the next human sample review, but they
  are no longer the highest-risk crash/artifact items.
- Next quality layer: move beyond regex artifacts and do a human readability
  pass for scene vividness, emotional causality, and whether QA answers use full
  natural-language explanations rather than terse template statements.

## Readability pass findings

- Fixed a cluster where role/name references broke emotional causality, especially
  parent/helper wording such as `his Milo`, object-pronoun hugs, and parent-role
  endings in market and snow-day stories.
- Fixed a cluster where action fragments were dropped into prose without grammar
  repair, such as `chooses to watched`, `if I used`, `At beneath`, and method
  answers like `used wading in carefully`.
- Improved several QA answers from terse rule labels into short explanations
  that connect scene facts to causality: why the coin could slip, why the station
  action fits the hazard, why the beach method fits tide/place/object risk, and
  why rooftop grounding avoids unsafe launch conditions.
- Remaining frontier: several stories are now coherent but still plain. A future
  pass should add more sensory detail and emotional beats without weakening the
  constraint gates; good targets are `beach_tide.py`, `campfire_caution.py`,
  `library_rescue.py`, and `train_station_wait.py`.
- Treat regex-reported pronoun issues as review hints, not automatic failures:
  some matches are normal phrases such as `she said`, while others are real
  errors such as object pronouns used as subjects.
