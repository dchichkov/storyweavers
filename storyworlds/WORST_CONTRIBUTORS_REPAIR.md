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

Additional waves follow the frozen 120-script template-collapse ranking.
