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

- 2026-06-17 random QA pass: fixed sampled crashers in
  `icy_rusty_fence.py`, `loud_street_bench_detective.py`,
  `crystal_river_hover.py`, and `cozy_bridge_lamp.py`; fixed sampled QA/prose
  quality defects in `harbor_search.py`, `market_lost_coin.py`, and
  `clocktower_search.py`. The rerun of the same deterministic 20-script random
  sweep completed with `20/20` scripts returning exit 0 under `--qa`.
- 2026-06-18 all-world random QA pass: sampled all 55
  `storyworlds/worlds/*.py` scripts once with `./.venv/bin/python <script> -n 1
  --seed <seed> --qa`. Initial result was `53/55`; final rerun was `55/55`.
  Fixed `crash` / `syntax_error` in `river_mist_quest.py` and
  `whispering_field.py`, `bad_call_signature` and `bad_import_path` in
  `river_mist_quest.py`, `asp_mismatch` in `whispering_field.py`, and
  `bad_pronoun` / `wrong_focus` / `too_shallow` wording in `museum_search.py`,
  `river_mist_quest.py`, and `whispering_field.py`.
- 2026-06-18 QA-depth follow-up: expanded terse one-sentence answers into
  grounded two-sentence responses in `beach_tide.py`, `campfire_caution.py`,
  `library_rescue.py`, `train_station_wait.py`, `river_mist_quest.py`,
  `whispering_field.py`, `museum_search.py`, `rooftop_kite.py`,
  `market_lost_coin.py`, `icy_rusty_fence.py`, and `clocktower_search.py`.
  Also fixed `library_rescue.py` helper/method drift where `ask_librarian`
  could be narrated by a non-librarian helper.
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
- Add a repo-level `storyworlds` smoke launcher that discovers
  `storyworlds/worlds/*.py`, runs `--verify` where supported, runs a seeded
  `--qa` sample, and reports crash/artifact hints. Keep pronoun regexes as hints:
  the 2026-06-17 sweep flagged normal `his dad` / `her mom` phrases as false
  positives.
- Promote the 2026-06-18 all-world sweep into that launcher or a saved command
  so future passes can rerun the same seed stream and compare failure/artifact
  counts. The only remaining scanner flag in the final sweep was a false
  positive in `rusty_door_icy_pond.py` for "Touching or shaking them can...".
- 2026-06-19 seed-world storytelling pass: polished `puddles.py` and
  `pirates.py` after 10-variant random samples with `--qa`. `puddles.py` now
  has a clearer beginning, sensory setup, softer conflict, concrete final image,
  and fuller cause/effect QA. `pirates.py` now has a stronger opening, grounded
  darkness/flame warning, branch-aware safe-light ending, and fuller QA answers.
  Both scripts pass `--verify`; keep them in future human samples for tone, but
  remove them from the highest-priority QA-depth queue.
- 2026-06-19 all-world storytelling/QA pass: used five parallel workers plus a
  local overflow lane to sample the remaining storyworlds in 10-variant batches
  with `--qa`, then polish prose and grounded answers. The pass fixed a sampled
  crash in `quiet_sign_fuzzy_flower_mystery.py`, a `harbor_search.py` QA
  crasher, stale scaffold phrases such as `world model` / `ending state is`,
  repeated/raw wording (`new new dress`, `the sign, the sign`, raw risk
  numbers), and many terse one-sentence QA answers.
- Integrated verification for the 2026-06-19 pass: all 65
  `storyworlds/worlds/*.py` scripts pass `--verify`; all 65 pass
  `-n 1 --seed 31000 --qa`; a normal story/QA artifact scan reported
  `flagged=0` for scaffold phrases, unresolved templates, doubled articles, and
  underscored tokens. `git diff --check` is clean.
- Remaining quality frontier: the all-world pass raised the floor, but some
  worlds are still intentionally template-like. Future passes should focus on
  prose variety, richer protagonist desire, and less safety-explainer cadence in
  otherwise-correct worlds such as `market_lost_coin.py`, `whispering_field.py`,
  `rooftop_kite.py`, `cozy_bridge_lamp.py`, `forest_bridge.py`, and
  `snow_day_help.py`.
- Keep using the storytelling-shape rubric when sampling: a beginning that
  explains why the story is happening, a middle turn driven by simulated state,
  and an ending that pays off the premise with a changed
  world/object/relationship. Track defects as `missing_beginning`,
  `missing_ending`, `event_log_prose`, `raw_fact_fragment`, `no_final_image`,
  and `weak_turn`.

## Readability pass findings

- 2026-06-17 pass: recurring defects were `crash`, `missing_entity_field`,
  `bad_registry_key`, `article_composition`, `wrong_focus`, `bad_pronoun`, and
  `too_shallow`. The most useful fixes were state-level first: marking prizes as
  worn before prediction in `icy_rusty_fence.py`, using registry keys rather than
  display phrases in `loud_street_bench_detective.py`, and adding the shared
  `phrase` field where renderers already depended on it.
- 2026-06-18 pass: broad `--qa` sampling found that syntax/parity checks are
  still worthwhile even after sampled robustness looks good. The highest-value
  next quality layer is not more regexes but reading bland-yet-valid worlds for
  emotional causality, especially worlds whose parent/child roles are rendered
  as generic `mom` / `dad` labels and whose QA explains the fix without naming
  the world-state cause.
- 2026-06-18 QA-depth follow-up: a targeted 10-world, 3-seed sample improved
  the touched cluster to `shortA=0` and `oneSent=0` for the sampled QA answers.
  The useful pattern was to add a causal second sentence tied to the world trace
  (`risk`, `method`, `gear`, `helper`, `location`, or `material`) rather than a
  generic audit sentence.
- 2026-06-18 storytelling follow-up from `haunted_feast_mystery.py`: validity
  and atmosphere were not enough. A sampled story still felt incomplete until
  the renderer stated the premise, gave Iris an investigative purpose, converted
  raw secret/clue facts into authored beats, and ended with a concrete image of
  the haunting resolved. Apply this same bar to future readability passes.
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
- Storytelling bar for that frontier: avoid prose that merely reports
  `event -> clue -> method -> solved`. Prefer a reader-facing premise, textured
  transitions, protagonist choice, and an ending image that proves what changed.
- Treat regex-reported pronoun issues as review hints, not automatic failures:
  some matches are normal phrases such as `she said`, while others are real
  errors such as object pronouns used as subjects.

## New storyworld batch notes

- Added `moss_cookie_misunderstanding.py`, seeded from `storyworlds/seed.py`
  (`cookie`, `golden moss`, `Misunderstanding`, `Humor`, `Fairy Tale`). The
  world models a child mistaking living fairy-glade growth for a treat, treasure,
  or stepping place; the gate requires the mistake to create an honest risk and
  the remedy to address that risk.
- Added `aquarium_calm.py`, a calm-animal-care world where the child wants a
  small water animal to respond; the parent predicts stress from tapping,
  shaking, overfeeding, or net-chasing and offers a compatible quiet plan.
- Verification evidence for this batch: both new worlds pass `--verify`;
  `moss_cookie_misunderstanding.py` reports 22 ASP/Python-valid combos and
  `aquarium_calm.py` reports 68. Both pass a deterministic seeds `0..9` `--qa`
  sweep, curated `--all --qa`, `--json`, representative `--trace`, and explicit
  invalid-combo rejection probes.
- Remaining frontier for the next batch: add a small launcher or meta-smoke that
  discovers new `storyworlds/worlds/*.py` scripts and runs `--verify`, a seeded
  `--qa` sweep, `--json`, and one registered invalid-combo probe where available.
