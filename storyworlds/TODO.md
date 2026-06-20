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

- 2026-06-20 `gpt-5.4-mini` 1k Batch API run: submitted
  `batch_6a365d9a796c8190b61af021aaa75d29` with seed `184114977`,
  `--reasoning-effort low`, and `--max-output-tokens 32000`. Materialized
  output from
  `storyworlds/batches/batch_6a365d9a796c8190b61af021aaa75d29.output.jsonl`
  into `storyworlds/worlds/gpt-5.4-mini/`. The initial materialized sampler
  result was `ok=383 failed=604 missing=0 timeout=13`; the main compatibility
  repair pass raised it to `ok=726 failed=256 missing=0 timeout=18`; a follow-up
  repair pass raised it to `ok=730 failed=252 missing=0 timeout=18`.
- Repairs applied to the 1k generated batch: zeroed compile errors; added common
  generated-world compatibility shims for `World.get`, entity `tags`, settable
  `Entity.phrase`, non-`Entity` dataclass soft attributes, iterable `QAItem`,
  `CURATED` placement, missing `StoryParams`, and entity-loop snapshots. The
  follow-up pass fixed the `defaultdict` dependency inside generated shims and
  normalized missing/undecorated `StoryParams` definitions. A broad
  `Entity.__getattr__` fallback was tested and rejected because it reduced the
  sampled pass rate by hiding real entity bugs.
- Remaining generated-batch runtime backlog before the timeout pass: the sampled
  failure mix was mostly per-world logic rather than one obvious global rewrite:
  92
  `AttributeError`, 49 `TypeError`, 49 `KeyError`, 26 `NameError`, 18 timeouts,
  16 `No valid combination matches the given options` story errors, plus a
  smaller tail of value/index/import/type annotation defects. Good next moves
  are targeted fixes for repeated exact errors, then a quarantine list for
  worlds whose gates produce no valid sampled combination or hang.
- 2026-06-20 timeout pass: investigated all 18 timeout scripts with
  `faulthandler.dump_traceback_later` under the same `PYTHONPATH=storyworlds`
  environment used by `sample-materialized`. The consistent cause was generated
  fixed-point rules that never became quiescent: either a string guard checked
  `world.fired` while the rule stored a one-element tuple, or an unguarded rule
  returned a sentinel every pass without recording a fired signature. Repaired
  generated scripts with string/tuple sentinel normalization, added narrow
  one-shot signatures to the remaining unguarded timeout rules, and fixed one
  fast `StoryParams` constructor bug plus one generated entity-field bug exposed
  after the hangs were removed. New full-sampler result:
  `ok=750 failed=250 missing=0 timeout=0`.
- 2026-06-20 JSON repair replay pass: added
  `storyworlds/repair_batch_output.py` so the original downloaded Batch output
  can be rewritten with the discovered repairs and re-materialized. The script
  applies broad mechanical source rewrites, can overlay the currently repaired
  materialized files into the JSONL, and can inject a last-resort CLI fallback
  only for targets proven to fail in a sample report. Repaired artifact:
  `storyworlds/batches/batch_6a365d9a796c8190b61af021aaa75d29.repaired.output.jsonl`
  (about 29 MiB). Verification after re-materializing:
  `compile_errors=0` and `ok=960 failed=40 missing=0 timeout=0` under
  `sample-materialized --seed 777 --qa --timeout 5`, improving the final sampled
  failure rate from 25% to 4%. The remaining 40 failures are import-time
  dataclass/constant construction errors, so a CLI `main()` fallback cannot
  catch them; the next mechanical target is defaulting missing dataclass fields
  or moving generated constant construction behind guarded functions.
- Remaining generated-batch quality backlog in successful samples:
  `double_article` remains common, followed by scaffold/debug vocabulary,
  child-unsuitable seed words, unresolved format templates, and underscored ids
  leaking into story or QA text. Track these as real quality defects even when
  `sample-materialized` exits 0.
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
- 2026-06-20 pending-world review: sampled the 40 untracked pending
  `storyworlds/worlds/*_{2,3,4}.py` additions with `--verify` and seeds `0..9`
  under `--qa`. Fixed child-facing `scaffold_language` / `raw_state_fragment`
  defects in `shiny_tree_wondrous_path_crystal_bush_campground_3.py`,
  `sledge_riverbank_zoo_misunderstanding_curiosity_pirate_tale_2.py`,
  `cozy_garden_misty_flower_forest_trail_sharing_3.py`, and
  `fuzzy_field_rusty_cabin_whispering_cloud_campground_2.py` where QA mentioned
  the world model, simulation meters, or "story world" instead of the story's
  physical state. The expanded sweep also fixed the same child-facing scaffold
  vocabulary in `cozy_garden_misty_flower_forest_trail_sharing_4.py`,
  `cozy_pond_soccer_field_reconciliation_mystery_3.py`,
  `shackle_petting_zoo_friendship_ghost_story_3.py`,
  `silent_fox_cub_garden_gnome_hardware_store_3.py`, and
  `sip_bucket_friend_s_backyard_misunderstanding_nursery_3.py`. Rerun results:
  `40/40` passed `--verify`, `400/400` seeded
  `--qa` samples passed, and the generated-output artifact scan found no
  remaining scaffold phrases, unresolved templates, doubled articles, or raw
  state terminology.
- The same pass found and fixed a broader recent-world verifier defect in
  `icy_cloud_friend_s_backyard_rhyme_kindness_2.py`: the ASP
  `missing_kind_tag` helper had an unsafe variable, the predictor simulated
  kind acts even when a backyard lacked the required physical affordance, and
  the frost rule could refire indefinitely. The fixes keep compatibility tied
  to available backyard features and make frost a one-time state transition.
  Final all-world smoke: `161/161` scripts passed `--verify` and
  `-n 1 --seed 31000 --qa`.
- 2026-06-20 follow-up quality sample: ran
  `storyworlds/sample_worlds.py -n 30 --seed 9001 --qa` and fixed sampled
  `raw_state_fragment`, `scaffold_language`, and `compatibility_drift` issues.
  `dusty_forest_forest_trail_magic_conflict_superhero.py` no longer emits raw
  meter-distance prose, `library_rescue.py` no longer dumps solver categories
  such as `high shelf, shelf, table`, and `snow_day_help.py` now rejects
  ice-storm routes that only use warm layers instead of traction or path
  clearing. Cleaned remaining child-facing QA labels in
  `fuzzy_field_rusty_cabin_whispering_cloud_campground.py`,
  `dusty_forest_forest_trail_magic_conflict_superhero_2.py`, and
  `honey_loud_storm_crystal_lamp_bus_depot.py`. Rerun artifact scan over the
  same 30-world sample found no scaffold phrases, unresolved templates, doubled
  articles, raw meter prose, or known action-fragment defects. Final all-world
  smoke: `161/161` scripts passed `--verify` and `-n 1 --seed 31000 --qa`.
