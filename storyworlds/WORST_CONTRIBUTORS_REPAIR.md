# Worst-Contributor Repair Campaign

This campaign repairs 126 production StoryWorld scripts in rolling waves of six.
The scope combines six independently identified low-quality, duplicate-heavy
worlds with a frozen ranking of 120 template-collapsed contributors. Selection
uses historical `gpt-5.4-mini` story-quality ratings, generation statistics
preserved in the production export manifests, and slot-normalized narrative
skeleton counts measured from the exported training corpus.

## Evidence And Scope

- Production worlds successfully exported: 6,855.
- Worlds with historical quality ratings: 685 (10.0%).
- Worlds with any exact generated-story duplicates: 476.
- Worlds with at least 50% exact duplicates: 224.
- Worlds with at least 90% exact duplicates: 114.
- Rated worlds with overall quality at most 5 and exact duplicates: 21.
- Exact duplicate stories were removed before the final JSONL was written.
  Repeated and near-template QA remains a separate corpus-level issue.

The first six targets combine low quality and exact duplication. The frozen
120-target ranking then prioritizes worlds whose exported stories collapse to
the fewest slot-normalized narrative skeletons, with exact duplication and
historical quality retained as supporting evidence. A single historical quality
rating is only a triage signal, not proof that every seed is poor.

## Repair Gate

Each repaired script must:

1. Preserve its public CLI and emit valid `StorySample` JSON.
2. Generate a valid batch with deterministic replay for a fixed seed.
3. Improve or preserve exact-story uniqueness over a 100-sample baseline.
4. Add meaningful variation in events, causal turns, language, or endings, not
   merely names and cosmetic substitutions.
5. Produce complete child-facing stories with a beginning, state-driven turn,
   and ending image that demonstrates what changed.
6. Keep story QA and world QA grounded in the emitted story and parameters.
7. Pass syntax/static checks and a post-repair 100-sample generation check.

## Progress

Legend: `queued`, `active`, `repaired`, `verified`, `blocked`.

| Wave | Status | Script | Triage evidence | Before | After | Notes |
| ---: | --- | --- | --- | --- | --- | --- |
| 1 | verified | `act_arithmetic_teak_bad_ending_transformation_tall.py` | quality 3; 70% exact duplicates | 30/100 unique | 100 unique; 100 skeletons | Independent 100-row schema/replay check passed. |
| 1 | verified | `dam_ophthalmology_barrette_flashback_folk_tale.py` | quality 4; 61% exact duplicates | 43/100 unique | 100 unique; 97 skeletons | Ending-state defect fixed; independent check passed. |
| 1 | verified | `spanish_shotgun_dark_bravery_rhyming_story.py` | quality 4; 29% exact duplicates | 71/100 unique | 100 unique; 99 skeletons | Independent check passed. |
| 1 | verified | `chug_digital_polio_teamwork_fable.py` | quality 4; 25% exact duplicates | 69/100 unique | 100 unique; 98 skeletons | Eight causal paths; independent check passed. |
| 1 | verified | `alec_proper_repetition_happy_ending_superhero_story.py` | quality 5; 99% exact duplicates | 1/100 unique | 100 unique; 100 skeletons | Import regression repaired; independent check passed. |
| 1 | verified | `quesadilla_mystery_to_solve_bedtime_story.py` | quality 5; 99% exact duplicates | 1/100 unique | 100 unique; 6 core skeletons | Eight causal arcs and 400/400 unique story-QA pairs. |
| 2 | verified | `thud_teamwork_rhyming_story.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 12 skeletons | Twelve substantive causal stories. |
| 2 | verified | `contagious_interchange_teamwork_ghost_story.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Ten causal arcs; setting/task collapse fixed. |
| 2 | verified | `employee_pylon_magic_pirate_tale.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 94 skeletons | Nine arcs and all three magic moves restored. |
| 2 | verified | `garnet_humor_curiosity_repetition_tall_tale.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 73 skeletons | Eight causal arcs; independent check passed. |
| 2 | verified | `hibachi_rhyme_suspense_comedy.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Eight incidents and rhyme/comedy forms. |
| 2 | verified | `loop_energy_ginger_conflict_pirate_tale.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Eight causal arcs; 333/400 unique story-QA pairs. |
| 3 | verified | `shishkebab_ice_fluid_friendship_kindness_myth.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 96 skeletons | Twelve causal arcs and six narrative structures. |
| 3 | verified | `snicker_railing_systematic_lesson_learned_teamwork_repetition.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve mystery arcs; independent check passed. |
| 3 | verified | `performance_flashback_moral_value_humor_rhyming_story.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | 400/400 unique story-QA pairs. |
| 3 | verified | `biology_nurse_oil_dialogue_superhero_story.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve incidents; 327/400 unique story-QA pairs. |
| 3 | verified | `bran_surprise_heartwarming.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Ten causal arcs; 315/400 unique story-QA pairs. |
| 3 | verified | `vehicle_lovin_zoom_children_s_museum_misunderstanding.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve causal arcs; 399/400 unique story-QA pairs. |
| 4 | verified | `chair_problem_solving_sound_effects_flashback_fable.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve arcs; 372/400 unique story-QA pairs. |
| 4 | verified | `cantina_shriek_referendum_suspense_slice_of_life.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve arcs; 424/500 unique story-QA pairs. |
| 4 | verified | `dogie_sophisticated_thank_friendship_sharing_animal_story.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve arcs; child-readable language improved. |
| 4 | verified | `coast_nostril_inner_monologue_comedy.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Ten incidents and functional thinking modes. |
| 4 | verified | `distinction_slot_nutrient_foreshadowing_dialogue_pirate_tale.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve pirate arcs; 400/400 unique story-QA pairs. |
| 5 | verified | `dress_sweetwilliam_curiosity_quest_bad_ending_fairy.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Independent replay check passed; 271/400 unique story-QA pairs. |
| 5 | verified | `emergency_clamp_starfish_friendship_quest_transformation_animal.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Independent replay check passed; 680/800 unique story-QA pairs. |
| 5 | verified | `fluid_illegal_medal_inner_monologue_fable.py` | 1 skeleton/100 exported stories | 88/100 exact unique; 1 skeleton | 100 unique; 100 skeletons | Twelve causal arcs; independent replay and QA checks passed. |
| 5 | verified | `folly_chimp_rhyme_cautionary_pirate_tale.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve pirate incidents; 574/600 unique story-QA pairs. |
| 5 | verified | `gypsy_teeny_playroom_lesson_learned_mystery_to.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve mysteries; source term handled as an old, potentially hurtful label. |
| 5 | verified | `hedge_mash_explore_magic_curiosity_problem_solving.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve magical problems; independent replay and QA checks passed. |
| 6 | verified | `huge_movement_silo_grocery_store_moral_value.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve incidents; 333/400 unique story-QA pairs. |
| 6 | verified | `mattress_fame_artichoke_petting_zoo_sound_effects.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 96 skeletons | Twelve scenarios; placeholder output eliminated. |
| 6 | verified | `narrative_specify_coupon_teamwork_foreshadowing_tall_tale.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 67 skeletons | Twelve arcs and eight telling modes; 229/600 unique story-QA pairs. |
| 6 | verified | `photography_twit_aster_transformation_kindness_comedy.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve scenarios; potentially insulting term recast as a fictional bird. |
| 6 | verified | `plunge_frigate_inner_monologue_twist_sharing_rhyming.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve incidents; 383/500 unique story-QA pairs. |
| 6 | verified | `pleasant_slide_bare_kindness_conflict_detective_story.py` | 1 skeleton; 79/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve safe detective cases; 214/500 unique story-QA pairs. |
| 7 | verified | `praise_repetition_cautionary_kindness_superhero_story.py` | 1 production skeleton; 2 in fresh baseline | 2 skeletons | 100 unique; 100 skeletons | Fifteen safety incidents; independent replay check passed. |
| 7 | verified | `prospector_kale_dialogue_cautionary_suspense_bedtime_story.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve cautionary mysteries; 221/500 unique story-QA pairs. |
| 7 | verified | `psychiatry_sticky_palm_sound_effects_transformation_cautionary.py` | 1 production skeleton; 2 in fresh baseline | 2 skeletons | 100 unique; 100 skeletons | Twelve non-stigmatizing incidents; 336/600 unique story-QA pairs. |
| 7 | verified | `pun_teamwork_heartwarming.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve scenarios with functional wordplay; 197/500 unique story-QA pairs. |
| 7 | verified | `pupa_appetizing_quail_campground_reconciliation_kindness_quest.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve reconciliation quests; missing required terms and QA grounding fixed. |
| 7 | verified | `quote_glutton_craft_workshop_inner_monologue_teamwork.py` | 1 production skeleton; 2 in fresh baseline | 2 skeletons | 100 unique; 100 skeletons | Twelve mysteries; source label explicitly reconsidered as hurtful. |
| 8 | verified | `rascal_bilge_ambidextrous_lesson_learned_suspense_space.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve emergencies; source term recast as a robot class. |
| 8 | verified | `seam_remote_rust_dialogue_animal_story.py` | 1 skeleton; 72/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve incidents; nondeterministic name selection fixed. |
| 8 | verified | `session_rotten_rhyme_twist_conflict_animal_story.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve incidents; 258/600 unique story-QA pairs. |
| 8 | verified | `sledge_classic_linguini_teamwork_foreshadowing_superhero_story.py` | 1 production skeleton; 3 in fresh baseline | 3 skeletons | 100 unique; 100 skeletons | Twelve rescues and eight telling modes; ASP verification fixed. |
| 8 | verified | `slob_fatten_helly_friendship_humor_dialogue_rhyming.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve incidents; awkward terms given non-insulting meanings. |
| 8 | verified | `stride_convenient_reading_nook_kindness_happy_ending.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve scenarios; repository-root import and ASP parity fixed. |
| 8 | verified | `switch_checker_conflict_detective_story.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve detective cases; 382/600 unique story-QA pairs. |
| 9 | verified | `system_vacancy_test_sharing_curiosity_folk_tale.py` | 1 skeleton; 70/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve folk-tale scenarios; 409/700 unique story-QA pairs. |
| 9 | verified | `tar_endanger_thin_flower_field_repetition_animal.py` | 1 skeleton; 68/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve child-safe hazard incidents; 237/600 unique story-QA pairs. |
| 9 | verified | `teller_remainder_margarita_quest_animal_story.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve quests; margarita kept in a flower/name context. |
| 9 | verified | `thorn_like_foil_surprise_reconciliation_magic_space.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve reconciliation scenarios and eight telling modes. |
| 9 | verified | `toe_pl_moisture_county_misunderstanding_teamwork_animal.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve incidents; awkward seed term made natural and child-safe. |
| 9 | verified | `toss_definitive_friendship_sharing_nursery_rhyme.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve nursery-rhyme scenarios; 255/500 unique story-QA pairs. |
| 9 | verified | `transcribe_children_s_museum_misunderstanding_friendship_repetition.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve museum incidents and ten telling modes. |
| 10 | verified | `transmission_mushroom_lesson_learned_sound_effects_misunderstanding.py` | 1 skeleton; 89/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve cases; ASP and curated-place defects fixed. |
| 10 | verified | `tube_cliff_lookout_quest_curiosity_sharing_nursery.py` | 1 skeleton; 65/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve child-safe cliff quests; disconnected world state fixed. |
| 10 | verified | `treat_kefir_hyacinth_teamwork_misunderstanding_fairy_tale.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve incidents; unsafe use of hyacinth petals removed. |
| 10 | verified | `yam_chuckle_laser_storm_drain_humor_flashback.py` | 1 skeleton; 67/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve child-safe drain incidents; 310/600 unique story-QA pairs. |
| 10 | verified | `yum_dim_crest_noon_curiosity_bravery_happy.py` | 1 skeleton; 72/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve scenarios; incorrect universal-key narration fixed. |
| 10 | verified | `yell_surprise_suspense_dialogue_animal_story.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve suspense incidents; 424/500 unique story-QA pairs. |
| 11 | verified | `blase_canned_sharing_inner_monologue_animal_story.py` | 1 skeleton; 98/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve scenarios; source label framed as a temporary pose. |
| 11 | verified | `deposit_pediatric_muddy_slope_mystery_to_solve.py` | 2 skeletons; 96/100 emitted in fresh baseline | 2 skeletons | 100 unique; 100 skeletons | Twelve child-safe medical mysteries; partial generation fixed. |
| 11 | verified | `webbed_joey_conflict_mystery.py` | 1 skeleton/100 exact-unique stories | 1 skeleton | 100 unique; 100 skeletons | Twelve mystery cases; 353/500 unique story-QA pairs. |
| 11 | verified | `destructor_sharing_surprise_cautionary_nursery_rhyme.py` | 1 skeleton; 91/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve incidents; destructor recast as a harmless craft toy. |
| 11 | verified | `equivalent_sherbet_kindergarten_kindness_dialogue_ghost_story.py` | 1 skeleton; 96/100 emitted in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve gentle kindergarten mysteries; partial generation fixed. |
| 11 | verified | `eyed_cautionary_sharing_humor_pirate_tale.py` | 1 skeleton; 97/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve pirate incidents; 330/600 unique story-QA pairs. |
| 12 | verified | `commit_riverbank_transformation_quest_slice_of_life.py` | 2 skeletons; 88/100 exact unique in fresh baseline | 2 skeletons | 100 unique; 100 skeletons | Twelve riverbank incidents and ten narrative routes. |
| 12 | verified | `head_scrawny_sneer_sound_effects_lesson_learned.py` | 1 skeleton; 96/100 emitted in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve incidents; body-shaming and sneering explicitly corrected. |
| 12 | verified | `subjunctive_aquarium_sharing_slice_of_life.py` | 1 skeleton; 95/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve aquarium incidents; duplicate parameter class removed. |
| 12 | verified | `engrave_ceiling_conflict_friendship_detective_story.py` | 1 skeleton; 90/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve child-safe ceiling mysteries; 389/500 unique story-QA pairs. |
| 12 | verified | `ghetto_chowder_repetition_happy_ending_ghost_story.py` | 1 skeleton; 80/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve incidents; loaded term restricted to accurate historical context. |
| 12 | verified | `progeny_cemetery_semi_sharing_magic_dialogue_comedy.py` | 1 skeleton; 86/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve respectful cemetery scenarios; vehicle actions made adult-controlled. |
| 13 | verified | `whatchamacallem_mansion_three_sharing_bad_ending_nursery.py` | 1 skeleton; 81/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve non-cruel bad-ending incidents and eight telling modes. |
| 13 | verified | `clarinet_tiara_rinse_lesson_learned_conflict_flashback.py` | 1 skeleton; 77/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve incidents; flashbacks now causally affect present choices. |
| 13 | verified | `croquet_animal_diabetic_rhyme_nursery_rhyme.py` | 1 skeleton; 79/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve medically careful scenarios with individualized care plans. |
| 13 | verified | `guppy_cashew_misunderstanding_bravery_slice_of_life.py` | 1 skeleton; 81/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve incidents with correct fish-feeding and allergy safeguards. |
| 13 | verified | `chief_urge_bows_teamwork_rhyme_superhero_story.py` | 1 skeleton; 81/100 emitted in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve missions; chief made a rotating job and bows made decorative. |
| 13 | verified | `mandolin_italian_navigate_repetition_bad_ending_happy.py` | 1 skeleton; 74/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve navigation incidents; non-cruel setbacks and no stereotypes. |
| 14 | verified | `sentence_trawler_reconciliation_bravery_tall_tale.py` | 1 skeleton; 80/100 emitted in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve scenarios; arbitrary-name pronouns and root CLI fixed. |
| 14 | verified | `banner_transformation_lesson_learned_space_adventure.py` | 1 skeleton; 75/100 emitted in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve cabin-safe space incidents and eight narrative routes. |
| 14 | verified | `instance_chowmein_lesson_learned_bad_ending_rhyme.py` | 1 skeleton; 54/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve food-safe, non-cruel incidents; pronouns fixed. |
| 14 | verified | `jambalaya_lasagne_duplicate_foreshadowing_twist_problem_solving.py` | 1 skeleton; 75/100 emitted in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve duplicate mysteries; duplication made causally meaningful. |
| 14 | verified | `putty_pupil_exclusion_playground_quest_conflict_pirate.py` | 1 skeleton; 71/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 99 skeletons | Twelve inclusive playground quests; 312/500 unique story-QA pairs. |
| 14 | verified | `coincide_linguine_icicle_warehouse_aisle_dialogue_slice.py` | 1 skeleton; 70/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve warehouse incidents with trained staff handling hazards. |
| 15 | verified | `infer_archer_colony_reconciliation_rhyming_story.py` | 1 skeleton; 72/100 emitted in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve supervised soft-archery incidents; colony means animal community. |
| 15 | verified | `somersault_sanitary_sound_effects_fable.py` | 1 skeleton; 72/100 emitted in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve sanitation incidents; acrobatics made supervised and safe. |
| 15 | verified | `alliance_shrivel_fifty_dining_room_surprise_detective.py` | 1 skeleton; 75/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 99 skeletons | Twelve dining-room mysteries and eight narration modes. |
| 15 | verified | `stern_demolish_cautionary_animal_story.py` | 1 skeleton; 54/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve adult-controlled demolition incidents; root CLI fixed. |
| 15 | verified | `veal_fast_twist_rhyming_story.py` | 1 skeleton; 63/100 emitted in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve food-safe incidents; veal retained as a non-graphic meal context. |
| 15 | verified | `bulls_lullabye_marina_transformation_friendship_mystery.py` | 1 skeleton; 48/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve marina mysteries; trained workers handle livestock. |
| 15 | verified | `fair_scrub_problem_solving_inner_monologue_bad.py` | 1 skeleton; 65/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve incidents with safe cleaning and non-cruel setbacks. |
| 16 | verified | `iguana_canal_path_misunderstanding_animal_story.py` | 1 skeleton; 64/100 emitted in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve canal incidents; animals remain behind barriers. |
| 16 | verified | `connect_yak_quest_lesson_learned_suspense_whodunit.py` | 2 skeletons; 60/100 emitted in fresh baseline | 2 skeletons | 100 unique; 100 skeletons | Twelve whodunits; inherited ASP contradiction fixed. |
| 16 | verified | `coward_chord_bonus_friendship_happy_ending_fable.py` | 1 skeleton; 55/100 exact unique in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve incidents; loaded label explicitly challenged. |
| 16 | verified | `equity_gamble_marmoset_mystery_to_solve_lesson.py` | 1 skeleton; 60/100 emitted in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve equity mysteries; gambling made non-monetary and reversible. |
| 16 | verified | `wine_grump_mystery_to_solve_fable.py` | 1 skeleton; 64/100 emitted in fresh baseline | 1 skeleton | 100 unique; 100 skeletons | Twelve mysteries; wine adult-managed and grump made a temporary mood. |

Additional waves follow the frozen 120-script template-collapse ranking.
