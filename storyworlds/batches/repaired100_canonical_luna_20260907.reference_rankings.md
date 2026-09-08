# Reference Screening: repaired100_canonical_luna_20260907

Offline analysis only. No API calls or canonical changes.

## Shortlist Interpretation

**Garnet and Shishkebab/Ice are the first two candidates I would retest.**
Garnet leads reliable joint delivery and the existing dataset index;
Shishkebab/Ice leads semantic diversity among the sufficiently observed groups.
The eight-entry candidate manifest deliberately includes both dependable
references and higher-quality, lower-yield probes; it is not the first eight
rows from any one ranking.

| Candidate | Why Keep It In The Next Test | Main Reservation |
| --- | --- | --- |
| Garnet | Q 7.24, D 2.75; 7/10 strict Q+D deliveries; highest existing index 13.04 | Still modest diversity, with recognizable plot copying |
| Shishkebab/Ice (013) | Q 6.35, D 3.62; 6/10 strict Q+D deliveries | Two underfilled pools; prose is less polished than Garnet/Thud |
| Head/Sneer (069) | Q 6.20, D 2.88; 8/9 strict passes and 5/9 strict Q+D deliveries | Quality is near the permissive floor; one general repair |
| Prospector/Kale (037) | Q 6.43, D 2.56; 8/10 strict passes; second-highest existing index 10.58 | Repeated investigate/explain/repair structure |
| Hibachi (011) | Q 6.36, D 3.00; 7/10 strict passes | Some literal word-slot artifacts remain |
| Coop/Architect (098) | Q 6.11, D 3.14; 7/9 strict passes | Stronger branching than prose; only four quality-qualified worlds |
| Thud (007) | Q 7.53, D 3.29 across seven rated children | Only 4/10 strict passes and 927 quality-qualified unique texts |
| Loop/Ginger (012) | Highest conditional Q, 7.62; D 3.00 across five rated children | Only 2/10 strict passes; four underfilled pools |

Thud illustrates why not to select on quality alone: its seven quality-qualified
children yield 927 distinct texts, while Garnet's eight yield 8,000. The existing
dataset indices are 1.98 and 13.04 respectively. Those indices include exact
uniqueness and pooled compression, but not the judge's semantic-diversity score.

The shortlist is sensitive to the goal. With strict **Q>=6,D>=4**, Shishkebab/Ice
has 4/10 deliveries, versus Garnet's 1/10. With strict **Q>=7,D>=3**, Garnet has
5/10, versus Shishkebab/Ice's 2/10. Neither is a universal winner. At the main
Q>=6,D>=3 floor, their descriptive 95% Wilson intervals are approximately
40-89% and 31-83%; the overlap and winner-selection bias preclude a strong
claim about which reference will generalize better.

## Coverage And Controls

Of 106 references, 80 meet the descriptive screening rule: at least five rated
child worlds and no missing eligible judge results. Thirteen have incomplete
judge coverage, and thirteen have fewer than five rated children despite
complete judge coverage. The 52 missing ratings are concentrated in 13 arms,
mostly repaired_017 through repaired_027, not evenly distributed. Incomplete
does not mean low quality; these arms cannot fairly be dismissed.

The current dialogue-heavy canonical references mostly show poor *within-world*
semantic diversity here: Nell 0.20, Cart 0.80, Bridge 0.57, Library 1.00, and
Puddles 0.33. Nell's quality is still 6.72. These are observations from different
tasks, not proof that adding dialogue caused collapse. Keep the latest Puddles
as a control; this analysis does not alter the canonical registry.

## Source And Output Review

Inspection of the frozen references suggests a useful mechanism to test:
several complete, internally matched causal sequences instead of a single plot
with independent noun swaps. Garnet has eight separate arc builders;
Shishkebab/Ice stores premise, problem, choice, action, result, ending and matching
QA in `MythArc` records. Thud similarly keeps each physical problem and its
complementary actions together. Loop/Ginger varies beats inside a chosen arc.
This is a hypothesis about transfer, not a controlled causal result, and does
not establish that their world-state simulations are complete.

The [retained reviewed samples](repaired100_canonical_luna_20260907.reference_review_samples.json) record one judged story from the
upper-median-quality child of six shortlisted references, selected with seed
777 within the judged set. These diagnostic readings broadly support the judge:

- Garnet's child tests a shadow by moving a lantern, gemstone, and screen; that
  is a concrete causal discovery, but the gemstone/lantern plot closely resembles
  the source's `_lantern_arc`. Quality can come from recycling the reference.
- Shishkebab/Ice's child has a real lost-oar/ferry-chain rescue, but mixes
  Luna/Pip/Faye in the introduction. The judge's positive note misses that drift.
- Head/Sneer's child resolves a forgotten lunch but still contains "Milo a friend"
  and an overt happy-ending label.
- Prospector/Kale's child investigates a lit shed but calls a caretaker after
  the caretaker has already arrived.
- Hibachi's child uses a sensible airflow intervention, but repeatedly calls the
  feather "the content", exposing the seed-word/template mechanism.
- Coop/Architect's child links a failed solo crossing to a shared bridge, but
  uses "chose to unrolled" and repeats its moral.

No reference or generated world was edited. Story quality remains conditional;
QA grounding and similarity to the reference are not certified by these scores.

## Confirmation Step

Retest the shortlisted references on the **same fresh task seeds**, with the
same Luna/Flex generation, repair policy, ten-story Terra judge, and 1,000-sample
local checks. Add the unchanged latest Puddles as a control. Use enough tasks
to reduce the influence of a single seed (for example, 20/reference); retain the
raw failures and complete judge coverage before deciding replacements. That
paid experiment has not been prepared or launched here.

## Method

Quality/diversity are conditional on valid judgements of worlds that passed sampling and verification.
Means weight generated worlds equally, not sibling stories as independent experiments.
Strict means full requested count, standalone CLI, verification, and deterministic replay.
Strict Q+D means strict AND world-average quality >=6 AND semantic diversity >=3.
Diversity 3 is only a modest floor (minor branch variation), not strong narrative diversity.
The JSON also gives Q>=6,D>=4 and Q>=7,D>=3 sensitivity counts.

Primary screens require >=5 rated worlds and no missing eligible judgements.
Strict-delivery sorting uses the lower endpoint of a descriptive 95% Wilson interval;
these intervals do not correct for selecting winners from 106 references or unmatched task difficulty.
Missing judge scores are not replaced by zero. Incomplete references appear separately.
The existing quality-gated exact-unique/compression index is unchanged and does NOT include semantic diversity.
Nine or ten tasks/reference give a shortlist to retest, not a demonstrated causal ranking.

## Candidate Manifest

Explicit exploratory shortlist, not a canonical replacement.

| Reference | Rated / tried | Unrated | Strict | Quality /9 | Diversity /9 | Strict Q+D | Index /100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [garnet: garnet_humor_curiosity_repetition_tall_tale](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/garnet_humor_curiosity_repetition_tall_tale.py) | 8/10 | 0 | 8/10 | 7.24 | 2.75 | 7/10 | 13.04 |
| [repaired_013: shishkebab_ice_fluid_friendship_kindness_myth](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/shishkebab_ice_fluid_friendship_kindness_myth.py) | 8/10 | 0 | 6/10 | 6.35 | 3.62 | 6/10 | 8.11 |
| [repaired_069: head_scrawny_sneer_sound_effects_lesson_learned](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/head_scrawny_sneer_sound_effects_lesson_learned.py) | 8/9 | 0 | 8/9 | 6.20 | 2.88 | 5/9 | 9.62 |
| [repaired_037: prospector_kale_dialogue_cautionary_suspense_bedtime_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/prospector_kale_dialogue_cautionary_suspense_bedtime_story.py) | 9/10 | 0 | 8/10 | 6.43 | 2.56 | 4/10 | 10.58 |
| [repaired_011: hibachi_rhyme_suspense_comedy](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/hibachi_rhyme_suspense_comedy.py) | 7/10 | 0 | 7/10 | 6.36 | 3.00 | 4/10 | 7.61 |
| [repaired_098: coop_architect_pappy_bravery_mystery_to_solve](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/coop_architect_pappy_bravery_mystery_to_solve.py) | 7/9 | 0 | 7/9 | 6.11 | 3.14 | 4/9 | 6.39 |
| [repaired_007: thud_teamwork_rhyming_story](../worlds/gpt-5.4-mini_batch_6a3744730bd48190b368f32c2819a0ed_seed953274611_n1000_repaired/thud_teamwork_rhyming_story.py) | 7/10 | 0 | 4/10 | 7.53 | 3.29 | 4/10 | 1.98 |
| [repaired_012: loop_energy_ginger_conflict_pirate_tale](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/loop_energy_ginger_conflict_pirate_tale.py) | 5/10 | 0 | 2/10 | 7.62 | 3.00 | 2/10 | 6.18 |

## Strict Joint Delivery

| Reference | Rated / tried | Unrated | Strict | Quality /9 | Diversity /9 | Strict Q+D | Index /100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [garnet: garnet_humor_curiosity_repetition_tall_tale](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/garnet_humor_curiosity_repetition_tall_tale.py) | 8/10 | 0 | 8/10 | 7.24 | 2.75 | 7/10 | 13.04 |
| [repaired_013: shishkebab_ice_fluid_friendship_kindness_myth](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/shishkebab_ice_fluid_friendship_kindness_myth.py) | 8/10 | 0 | 6/10 | 6.35 | 3.62 | 6/10 | 8.11 |
| [repaired_069: head_scrawny_sneer_sound_effects_lesson_learned](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/head_scrawny_sneer_sound_effects_lesson_learned.py) | 8/9 | 0 | 8/9 | 6.20 | 2.88 | 5/9 | 9.62 |
| [repaired_081: banner_transformation_lesson_learned_space_adventure](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/banner_transformation_lesson_learned_space_adventure.py) | 7/9 | 0 | 6/9 | 6.79 | 2.14 | 4/9 | 9.27 |
| [repaired_064: webbed_joey_conflict_mystery](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/webbed_joey_conflict_mystery.py) | 9/9 | 0 | 8/9 | 6.32 | 2.78 | 4/9 | 9.98 |
| [repaired_051: teller_remainder_margarita_quest_animal_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/teller_remainder_margarita_quest_animal_story.py) | 8/9 | 0 | 8/9 | 6.21 | 2.88 | 4/9 | 8.47 |
| [repaired_098: coop_architect_pappy_bravery_mystery_to_solve](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/coop_architect_pappy_bravery_mystery_to_solve.py) | 7/9 | 0 | 7/9 | 6.11 | 3.14 | 4/9 | 6.39 |
| [repaired_060: yum_dim_crest_noon_curiosity_bravery_happy](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/yum_dim_crest_noon_curiosity_bravery_happy.py) | 7/9 | 0 | 5/9 | 6.09 | 3.00 | 4/9 | 7.16 |
| [repaired_052: thorn_like_foil_surprise_reconciliation_magic_space](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/thorn_like_foil_surprise_reconciliation_magic_space.py) | 7/9 | 0 | 7/9 | 6.09 | 2.71 | 4/9 | 7.23 |
| [repaired_007: thud_teamwork_rhyming_story](../worlds/gpt-5.4-mini_batch_6a3744730bd48190b368f32c2819a0ed_seed953274611_n1000_repaired/thud_teamwork_rhyming_story.py) | 7/10 | 0 | 4/10 | 7.53 | 3.29 | 4/10 | 1.98 |
| [repaired_037: prospector_kale_dialogue_cautionary_suspense_bedtime_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/prospector_kale_dialogue_cautionary_suspense_bedtime_story.py) | 9/10 | 0 | 8/10 | 6.43 | 2.56 | 4/10 | 10.58 |
| [repaired_011: hibachi_rhyme_suspense_comedy](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/hibachi_rhyme_suspense_comedy.py) | 7/10 | 0 | 7/10 | 6.36 | 3.00 | 4/10 | 7.61 |

## Conditional Quality

| Reference | Rated / tried | Unrated | Strict | Quality /9 | Diversity /9 | Strict Q+D | Index /100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [repaired_012: loop_energy_ginger_conflict_pirate_tale](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/loop_energy_ginger_conflict_pirate_tale.py) | 5/10 | 0 | 2/10 | 7.62 | 3.00 | 2/10 | 6.18 |
| [repaired_007: thud_teamwork_rhyming_story](../worlds/gpt-5.4-mini_batch_6a3744730bd48190b368f32c2819a0ed_seed953274611_n1000_repaired/thud_teamwork_rhyming_story.py) | 7/10 | 0 | 4/10 | 7.53 | 3.29 | 4/10 | 1.98 |
| [repaired_082: instance_chowmein_lesson_learned_bad_ending_rhyme](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/instance_chowmein_lesson_learned_bad_ending_rhyme.py) | 8/9 | 0 | 0/9 | 7.25 | 1.00 | 0/9 | 0.66 |
| [garnet: garnet_humor_curiosity_repetition_tall_tale](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/garnet_humor_curiosity_repetition_tall_tale.py) | 8/10 | 0 | 8/10 | 7.24 | 2.75 | 7/10 | 13.04 |
| [repaired_090: veal_fast_twist_rhyming_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/veal_fast_twist_rhyming_story.py) | 7/9 | 0 | 2/9 | 6.90 | 3.29 | 1/9 | 6.14 |
| [repaired_081: banner_transformation_lesson_learned_space_adventure](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/banner_transformation_lesson_learned_space_adventure.py) | 7/9 | 0 | 6/9 | 6.79 | 2.14 | 4/9 | 9.27 |
| [nell: nell_and_the_dragon_v2](../worlds/nell_and_the_dragon_v2.py) | 5/10 | 0 | 5/10 | 6.72 | 0.20 | 0/10 | 0.21 |
| [cart: one_cart_dialogue](../worlds/one_cart_dialogue.py) | 5/10 | 0 | 5/10 | 6.62 | 0.80 | 0/10 | 0.89 |
| [repaired_003: spanish_shotgun_dark_bravery_rhyming_story](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/spanish_shotgun_dark_bravery_rhyming_story.py) | 9/10 | 0 | 8/10 | 6.50 | 1.33 | 0/10 | 8.55 |
| [repaired_049: system_vacancy_test_sharing_curiosity_folk_tale](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/system_vacancy_test_sharing_curiosity_folk_tale.py) | 6/9 | 0 | 5/9 | 6.45 | 2.50 | 2/9 | 7.09 |
| [repaired_037: prospector_kale_dialogue_cautionary_suspense_bedtime_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/prospector_kale_dialogue_cautionary_suspense_bedtime_story.py) | 9/10 | 0 | 8/10 | 6.43 | 2.56 | 4/10 | 10.58 |
| [repaired_079: mandolin_italian_navigate_repetition_bad_ending_happy](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mandolin_italian_navigate_repetition_bad_ending_happy.py) | 8/9 | 0 | 8/9 | 6.41 | 2.38 | 3/9 | 6.04 |

## Conditional Semantic Diversity

| Reference | Rated / tried | Unrated | Strict | Quality /9 | Diversity /9 | Strict Q+D | Index /100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [repaired_013: shishkebab_ice_fluid_friendship_kindness_myth](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/shishkebab_ice_fluid_friendship_kindness_myth.py) | 8/10 | 0 | 6/10 | 6.35 | 3.62 | 6/10 | 8.11 |
| [repaired_007: thud_teamwork_rhyming_story](../worlds/gpt-5.4-mini_batch_6a3744730bd48190b368f32c2819a0ed_seed953274611_n1000_repaired/thud_teamwork_rhyming_story.py) | 7/10 | 0 | 4/10 | 7.53 | 3.29 | 4/10 | 1.98 |
| [repaired_090: veal_fast_twist_rhyming_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/veal_fast_twist_rhyming_story.py) | 7/9 | 0 | 2/9 | 6.90 | 3.29 | 1/9 | 6.14 |
| [repaired_073: progeny_cemetery_semi_sharing_magic_dialogue_comedy](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/progeny_cemetery_semi_sharing_magic_dialogue_comedy.py) | 5/9 | 0 | 5/9 | 5.76 | 3.20 | 2/9 | 3.59 |
| [repaired_057: tube_cliff_lookout_quest_curiosity_sharing_nursery](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tube_cliff_lookout_quest_curiosity_sharing_nursery.py) | 6/9 | 0 | 3/9 | 6.13 | 3.17 | 2/9 | 4.66 |
| [repaired_098: coop_architect_pappy_bravery_mystery_to_solve](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/coop_architect_pappy_bravery_mystery_to_solve.py) | 7/9 | 0 | 7/9 | 6.11 | 3.14 | 4/9 | 6.39 |
| [repaired_034: plunge_frigate_inner_monologue_twist_sharing_rhyming](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/plunge_frigate_inner_monologue_twist_sharing_rhyming.py) | 9/10 | 0 | 6/10 | 6.13 | 3.11 | 3/10 | 7.72 |
| [repaired_012: loop_energy_ginger_conflict_pirate_tale](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/loop_energy_ginger_conflict_pirate_tale.py) | 5/10 | 0 | 2/10 | 7.62 | 3.00 | 2/10 | 6.18 |
| [repaired_011: hibachi_rhyme_suspense_comedy](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/hibachi_rhyme_suspense_comedy.py) | 7/10 | 0 | 7/10 | 6.36 | 3.00 | 4/10 | 7.61 |
| [repaired_056: transmission_mushroom_lesson_learned_sound_effects_misunderstanding](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/transmission_mushroom_lesson_learned_sound_effects_misunderstanding.py) | 5/9 | 0 | 4/9 | 6.32 | 3.00 | 3/9 | 7.02 |
| [repaired_047: stride_convenient_reading_nook_kindness_happy_ending](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/stride_convenient_reading_nook_kindness_happy_ending.py) | 5/9 | 0 | 5/9 | 6.30 | 3.00 | 3/9 | 7.16 |
| [repaired_060: yum_dim_crest_noon_curiosity_bravery_happy](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/yum_dim_crest_noon_curiosity_bravery_happy.py) | 7/9 | 0 | 5/9 | 6.09 | 3.00 | 4/9 | 7.16 |

## Existing Dataset Index

| Reference | Rated / tried | Unrated | Strict | Quality /9 | Diversity /9 | Strict Q+D | Index /100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [garnet: garnet_humor_curiosity_repetition_tall_tale](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/garnet_humor_curiosity_repetition_tall_tale.py) | 8/10 | 0 | 8/10 | 7.24 | 2.75 | 7/10 | 13.04 |
| [repaired_037: prospector_kale_dialogue_cautionary_suspense_bedtime_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/prospector_kale_dialogue_cautionary_suspense_bedtime_story.py) | 9/10 | 0 | 8/10 | 6.43 | 2.56 | 4/10 | 10.58 |
| [repaired_064: webbed_joey_conflict_mystery](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/webbed_joey_conflict_mystery.py) | 9/9 | 0 | 8/9 | 6.32 | 2.78 | 4/9 | 9.98 |
| [repaired_069: head_scrawny_sneer_sound_effects_lesson_learned](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/head_scrawny_sneer_sound_effects_lesson_learned.py) | 8/9 | 0 | 8/9 | 6.20 | 2.88 | 5/9 | 9.62 |
| [repaired_081: banner_transformation_lesson_learned_space_adventure](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/banner_transformation_lesson_learned_space_adventure.py) | 7/9 | 0 | 6/9 | 6.79 | 2.14 | 4/9 | 9.27 |
| [repaired_003: spanish_shotgun_dark_bravery_rhyming_story](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/spanish_shotgun_dark_bravery_rhyming_story.py) | 9/10 | 0 | 8/10 | 6.50 | 1.33 | 0/10 | 8.55 |
| [repaired_051: teller_remainder_margarita_quest_animal_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/teller_remainder_margarita_quest_animal_story.py) | 8/9 | 0 | 8/9 | 6.21 | 2.88 | 4/9 | 8.47 |
| [repaired_013: shishkebab_ice_fluid_friendship_kindness_myth](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/shishkebab_ice_fluid_friendship_kindness_myth.py) | 8/10 | 0 | 6/10 | 6.35 | 3.62 | 6/10 | 8.11 |
| [repaired_066: equivalent_sherbet_kindergarten_kindness_dialogue_ghost_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/equivalent_sherbet_kindergarten_kindness_dialogue_ghost_story.py) | 7/9 | 0 | 7/9 | 5.74 | 2.57 | 2/9 | 7.87 |
| [repaired_034: plunge_frigate_inner_monologue_twist_sharing_rhyming](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/plunge_frigate_inner_monologue_twist_sharing_rhyming.py) | 9/10 | 0 | 6/10 | 6.13 | 3.11 | 3/10 | 7.72 |
| [repaired_011: hibachi_rhyme_suspense_comedy](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/hibachi_rhyme_suspense_comedy.py) | 7/10 | 0 | 7/10 | 6.36 | 3.00 | 4/10 | 7.61 |
| [repaired_052: thorn_like_foil_surprise_reconciliation_magic_space](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/thorn_like_foil_surprise_reconciliation_magic_space.py) | 7/9 | 0 | 7/9 | 6.09 | 2.71 | 4/9 | 7.23 |

## Incomplete Judge Coverage

| Reference | Rated / tried | Unrated | Strict | Quality /9 | Diversity /9 | Strict Q+D | Index /100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [repaired_017: bran_surprise_heartwarming](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bran_surprise_heartwarming.py) | 5/10 | 1 | 5/10 | 6.44 | 2.80 | 4/10 (+1 unknown) | - |
| [repaired_018: vehicle_lovin_zoom_children_s_museum_misunderstanding](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/vehicle_lovin_zoom_children_s_museum_misunderstanding.py) | 4/10 | 5 | 8/10 | 6.47 | 2.00 | 1/10 (+5 unknown) | - |
| [repaired_019: chair_problem_solving_sound_effects_flashback_fable](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chair_problem_solving_sound_effects_flashback_fable.py) | 4/10 | 4 | 8/10 | 5.53 | 1.75 | 0/10 (+4 unknown) | - |
| [repaired_020: cantina_shriek_referendum_suspense_slice_of_life](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cantina_shriek_referendum_suspense_slice_of_life.py) | 1/10 | 2 | 0/10 | 7.90 | 2.00 | 0/10 | - |
| [repaired_021: dogie_sophisticated_thank_friendship_sharing_animal_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/dogie_sophisticated_thank_friendship_sharing_animal_story.py) | 1/10 | 6 | 5/10 | 7.00 | 2.00 | 0/10 (+5 unknown) | - |
| [repaired_022: coast_nostril_inner_monologue_comedy](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/coast_nostril_inner_monologue_comedy.py) | 1/10 | 5 | 5/10 | 5.90 | 2.00 | 0/10 (+4 unknown) | - |
| [repaired_023: distinction_slot_nutrient_foreshadowing_dialogue_pirate_tale](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/distinction_slot_nutrient_foreshadowing_dialogue_pirate_tale.py) | 0/10 | 4 | 4/10 | - | - | 0/10 (+4 unknown) | - |
| [repaired_024: dress_sweetwilliam_curiosity_quest_bad_ending_fairy](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/dress_sweetwilliam_curiosity_quest_bad_ending_fairy.py) | 0/10 | 7 | 7/10 | - | - | 0/10 (+7 unknown) | - |
| [repaired_025: emergency_clamp_starfish_friendship_quest_transformation_animal](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/emergency_clamp_starfish_friendship_quest_transformation_animal.py) | 0/10 | 7 | 4/10 | - | - | 0/10 (+4 unknown) | - |
| [repaired_026: fluid_illegal_medal_inner_monologue_fable](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/fluid_illegal_medal_inner_monologue_fable.py) | 0/10 | 3 | 3/10 | - | - | 0/10 (+3 unknown) | - |
| [repaired_027: folly_chimp_rhyme_cautionary_pirate_tale](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/folly_chimp_rhyme_cautionary_pirate_tale.py) | 1/10 | 6 | 5/10 | 6.00 | 3.00 | 1/10 (+4 unknown) | - |
| [repaired_031: mattress_fame_artichoke_petting_zoo_sound_effects](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mattress_fame_artichoke_petting_zoo_sound_effects.py) | 6/10 | 1 | 7/10 | 5.93 | 1.83 | 1/10 (+1 unknown) | - |
| [repaired_083: jambalaya_lasagne_duplicate_foreshadowing_twist_problem_solving](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/jambalaya_lasagne_duplicate_foreshadowing_twist_problem_solving.py) | 6/9 | 1 | 4/9 | 6.25 | 2.67 | 2/9 (+1 unknown) | - |

## All References

Original reference order; incomplete is not synonymous with poor.

| Reference | Rated / tried | Unrated | Strict | Quality /9 | Diversity /9 | Strict Q+D | Index /100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| [puddles: puddles](../worlds/puddles.py) | 6/10 | 0 | 6/10 | 5.88 | 0.33 | 0/10 | 0.79 |
| [pirates: pirates](../worlds/pirates.py) | 3/10 | 0 | 3/10 | 5.33 | 0.33 | 0/10 | 0.78 |
| [library: library_words_dialogue](../worlds/library_words_dialogue.py) | 6/10 | 0 | 6/10 | 5.05 | 1.00 | 0/10 | 0.18 |
| [cart: one_cart_dialogue](../worlds/one_cart_dialogue.py) | 5/10 | 0 | 5/10 | 6.62 | 0.80 | 0/10 | 0.89 |
| [bridge: bridge_builders_dialogue](../worlds/bridge_builders_dialogue.py) | 7/10 | 0 | 7/10 | 6.36 | 0.57 | 0/10 | 2.85 |
| [nell: nell_and_the_dragon_v2](../worlds/nell_and_the_dragon_v2.py) | 5/10 | 0 | 5/10 | 6.72 | 0.20 | 0/10 | 0.21 |
| [repaired_001: act_arithmetic_teak_bad_ending_transformation_tall](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/act_arithmetic_teak_bad_ending_transformation_tall.py) | 9/10 | 0 | 9/10 | 5.86 | 0.78 | 0/10 | 2.48 |
| [repaired_002: dam_ophthalmology_barrette_flashback_folk_tale](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/dam_ophthalmology_barrette_flashback_folk_tale.py) | 6/10 | 0 | 6/10 | 5.55 | 1.67 | 0/10 | 2.31 |
| [repaired_003: spanish_shotgun_dark_bravery_rhyming_story](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/spanish_shotgun_dark_bravery_rhyming_story.py) | 9/10 | 0 | 8/10 | 6.50 | 1.33 | 0/10 | 8.55 |
| [repaired_004: chug_digital_polio_teamwork_fable](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/chug_digital_polio_teamwork_fable.py) | 9/10 | 0 | 9/10 | 5.90 | 1.89 | 3/10 | 3.15 |
| [repaired_005: alec_proper_repetition_happy_ending_superhero_story](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/alec_proper_repetition_happy_ending_superhero_story.py) | 10/10 | 0 | 10/10 | 6.10 | 1.90 | 1/10 | 2.77 |
| [repaired_006: quesadilla_mystery_to_solve_bedtime_story](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/quesadilla_mystery_to_solve_bedtime_story.py) | 6/10 | 0 | 6/10 | 5.38 | 1.50 | 0/10 | 3.52 |
| [repaired_007: thud_teamwork_rhyming_story](../worlds/gpt-5.4-mini_batch_6a3744730bd48190b368f32c2819a0ed_seed953274611_n1000_repaired/thud_teamwork_rhyming_story.py) | 7/10 | 0 | 4/10 | 7.53 | 3.29 | 4/10 | 1.98 |
| [repaired_008: contagious_interchange_teamwork_ghost_story](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/contagious_interchange_teamwork_ghost_story.py) | 9/10 | 0 | 4/10 | 5.64 | 2.33 | 2/10 | 3.92 |
| [repaired_009: employee_pylon_magic_pirate_tale](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/employee_pylon_magic_pirate_tale.py) | 9/10 | 0 | 8/10 | 5.99 | 2.22 | 1/10 | 6.61 |
| [garnet: garnet_humor_curiosity_repetition_tall_tale](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/garnet_humor_curiosity_repetition_tall_tale.py) | 8/10 | 0 | 8/10 | 7.24 | 2.75 | 7/10 | 13.04 |
| [repaired_011: hibachi_rhyme_suspense_comedy](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/hibachi_rhyme_suspense_comedy.py) | 7/10 | 0 | 7/10 | 6.36 | 3.00 | 4/10 | 7.61 |
| [repaired_012: loop_energy_ginger_conflict_pirate_tale](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/loop_energy_ginger_conflict_pirate_tale.py) | 5/10 | 0 | 2/10 | 7.62 | 3.00 | 2/10 | 6.18 |
| [repaired_013: shishkebab_ice_fluid_friendship_kindness_myth](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/shishkebab_ice_fluid_friendship_kindness_myth.py) | 8/10 | 0 | 6/10 | 6.35 | 3.62 | 6/10 | 8.11 |
| [repaired_014: snicker_railing_systematic_lesson_learned_teamwork_repetition](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/snicker_railing_systematic_lesson_learned_teamwork_repetition.py) | 7/10 | 0 | 4/10 | 4.90 | 1.57 | 0/10 | 0.09 |
| [repaired_015: performance_flashback_moral_value_humor_rhyming_story](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/performance_flashback_moral_value_humor_rhyming_story.py) | 10/10 | 0 | 8/10 | 5.70 | 1.70 | 1/10 | 5.05 |
| [repaired_016: biology_nurse_oil_dialogue_superhero_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/biology_nurse_oil_dialogue_superhero_story.py) | 8/10 | 0 | 7/10 | 5.86 | 2.62 | 2/10 | 6.28 |
| [repaired_017: bran_surprise_heartwarming](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bran_surprise_heartwarming.py) | 5/10 | 1 | 5/10 | 6.44 | 2.80 | 4/10 (+1 unknown) | - |
| [repaired_018: vehicle_lovin_zoom_children_s_museum_misunderstanding](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/vehicle_lovin_zoom_children_s_museum_misunderstanding.py) | 4/10 | 5 | 8/10 | 6.47 | 2.00 | 1/10 (+5 unknown) | - |
| [repaired_019: chair_problem_solving_sound_effects_flashback_fable](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chair_problem_solving_sound_effects_flashback_fable.py) | 4/10 | 4 | 8/10 | 5.53 | 1.75 | 0/10 (+4 unknown) | - |
| [repaired_020: cantina_shriek_referendum_suspense_slice_of_life](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/cantina_shriek_referendum_suspense_slice_of_life.py) | 1/10 | 2 | 0/10 | 7.90 | 2.00 | 0/10 | - |
| [repaired_021: dogie_sophisticated_thank_friendship_sharing_animal_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/dogie_sophisticated_thank_friendship_sharing_animal_story.py) | 1/10 | 6 | 5/10 | 7.00 | 2.00 | 0/10 (+5 unknown) | - |
| [repaired_022: coast_nostril_inner_monologue_comedy](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/coast_nostril_inner_monologue_comedy.py) | 1/10 | 5 | 5/10 | 5.90 | 2.00 | 0/10 (+4 unknown) | - |
| [repaired_023: distinction_slot_nutrient_foreshadowing_dialogue_pirate_tale](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/distinction_slot_nutrient_foreshadowing_dialogue_pirate_tale.py) | 0/10 | 4 | 4/10 | - | - | 0/10 (+4 unknown) | - |
| [repaired_024: dress_sweetwilliam_curiosity_quest_bad_ending_fairy](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/dress_sweetwilliam_curiosity_quest_bad_ending_fairy.py) | 0/10 | 7 | 7/10 | - | - | 0/10 (+7 unknown) | - |
| [repaired_025: emergency_clamp_starfish_friendship_quest_transformation_animal](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/emergency_clamp_starfish_friendship_quest_transformation_animal.py) | 0/10 | 7 | 4/10 | - | - | 0/10 (+4 unknown) | - |
| [repaired_026: fluid_illegal_medal_inner_monologue_fable](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/fluid_illegal_medal_inner_monologue_fable.py) | 0/10 | 3 | 3/10 | - | - | 0/10 (+3 unknown) | - |
| [repaired_027: folly_chimp_rhyme_cautionary_pirate_tale](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/folly_chimp_rhyme_cautionary_pirate_tale.py) | 1/10 | 6 | 5/10 | 6.00 | 3.00 | 1/10 (+4 unknown) | - |
| [repaired_028: gypsy_teeny_playroom_lesson_learned_mystery_to](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gypsy_teeny_playroom_lesson_learned_mystery_to.py) | 7/10 | 0 | 7/10 | 5.40 | 2.86 | 2/10 | 3.22 |
| [repaired_029: hedge_mash_explore_magic_curiosity_problem_solving](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/hedge_mash_explore_magic_curiosity_problem_solving.py) | 9/10 | 0 | 6/10 | 6.16 | 1.56 | 0/10 | 3.60 |
| [repaired_030: huge_movement_silo_grocery_store_moral_value](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/huge_movement_silo_grocery_store_moral_value.py) | 8/10 | 0 | 7/10 | 5.25 | 2.12 | 1/10 | 2.95 |
| [repaired_031: mattress_fame_artichoke_petting_zoo_sound_effects](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mattress_fame_artichoke_petting_zoo_sound_effects.py) | 6/10 | 1 | 7/10 | 5.93 | 1.83 | 1/10 (+1 unknown) | - |
| [repaired_032: narrative_specify_coupon_teamwork_foreshadowing_tall_tale](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/narrative_specify_coupon_teamwork_foreshadowing_tall_tale.py) | 7/10 | 0 | 3/10 | 5.56 | 1.43 | 0/10 | 0.84 |
| [repaired_033: photography_twit_aster_transformation_kindness_comedy](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/photography_twit_aster_transformation_kindness_comedy.py) | 3/10 | 0 | 3/10 | 4.43 | 2.00 | 0/10 | 0.00 |
| [repaired_034: plunge_frigate_inner_monologue_twist_sharing_rhyming](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/plunge_frigate_inner_monologue_twist_sharing_rhyming.py) | 9/10 | 0 | 6/10 | 6.13 | 3.11 | 3/10 | 7.72 |
| [repaired_035: pleasant_slide_bare_kindness_conflict_detective_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pleasant_slide_bare_kindness_conflict_detective_story.py) | 5/10 | 0 | 3/10 | 6.20 | 2.00 | 1/10 | 3.56 |
| [repaired_036: praise_repetition_cautionary_kindness_superhero_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/praise_repetition_cautionary_kindness_superhero_story.py) | 8/10 | 0 | 5/10 | 4.96 | 1.88 | 0/10 | 2.18 |
| [repaired_037: prospector_kale_dialogue_cautionary_suspense_bedtime_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/prospector_kale_dialogue_cautionary_suspense_bedtime_story.py) | 9/10 | 0 | 8/10 | 6.43 | 2.56 | 4/10 | 10.58 |
| [repaired_038: psychiatry_sticky_palm_sound_effects_transformation_cautionary](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/psychiatry_sticky_palm_sound_effects_transformation_cautionary.py) | 5/10 | 0 | 5/10 | 4.88 | 2.00 | 0/10 | 2.64 |
| [repaired_039: pun_teamwork_heartwarming](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pun_teamwork_heartwarming.py) | 6/10 | 0 | 6/10 | 5.47 | 2.50 | 2/10 | 3.21 |
| [repaired_040: pupa_appetizing_quail_campground_reconciliation_kindness_quest](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pupa_appetizing_quail_campground_reconciliation_kindness_quest.py) | 4/10 | 0 | 2/10 | 5.70 | 2.50 | 0/10 | 3.29 |
| [repaired_041: quote_glutton_craft_workshop_inner_monologue_teamwork](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/quote_glutton_craft_workshop_inner_monologue_teamwork.py) | 7/9 | 0 | 6/9 | 6.19 | 2.71 | 3/9 | 5.71 |
| [repaired_042: rascal_bilge_ambidextrous_lesson_learned_suspense_space](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/rascal_bilge_ambidextrous_lesson_learned_suspense_space.py) | 6/9 | 0 | 6/9 | 5.02 | 2.83 | 0/9 | 0.00 |
| [repaired_043: seam_remote_rust_dialogue_animal_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/seam_remote_rust_dialogue_animal_story.py) | 7/9 | 0 | 6/9 | 5.66 | 2.43 | 1/9 | 6.60 |
| [repaired_044: session_rotten_rhyme_twist_conflict_animal_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/session_rotten_rhyme_twist_conflict_animal_story.py) | 4/9 | 0 | 1/9 | 5.95 | 2.25 | 0/9 | 0.64 |
| [repaired_045: sledge_classic_linguini_teamwork_foreshadowing_superhero_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sledge_classic_linguini_teamwork_foreshadowing_superhero_story.py) | 7/9 | 0 | 7/9 | 5.24 | 1.71 | 1/9 | 5.52 |
| [repaired_046: slob_fatten_helly_friendship_humor_dialogue_rhyming](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/slob_fatten_helly_friendship_humor_dialogue_rhyming.py) | 5/9 | 0 | 4/9 | 5.64 | 2.00 | 0/9 | 3.10 |
| [repaired_047: stride_convenient_reading_nook_kindness_happy_ending](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/stride_convenient_reading_nook_kindness_happy_ending.py) | 5/9 | 0 | 5/9 | 6.30 | 3.00 | 3/9 | 7.16 |
| [repaired_048: switch_checker_conflict_detective_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/switch_checker_conflict_detective_story.py) | 6/9 | 0 | 4/9 | 5.90 | 2.33 | 1/9 | 6.29 |
| [repaired_049: system_vacancy_test_sharing_curiosity_folk_tale](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/system_vacancy_test_sharing_curiosity_folk_tale.py) | 6/9 | 0 | 5/9 | 6.45 | 2.50 | 2/9 | 7.09 |
| [repaired_050: tar_endanger_thin_flower_field_repetition_animal](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tar_endanger_thin_flower_field_repetition_animal.py) | 3/9 | 0 | 2/9 | 5.67 | 3.00 | 0/9 | 0.96 |
| [repaired_051: teller_remainder_margarita_quest_animal_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/teller_remainder_margarita_quest_animal_story.py) | 8/9 | 0 | 8/9 | 6.21 | 2.88 | 4/9 | 8.47 |
| [repaired_052: thorn_like_foil_surprise_reconciliation_magic_space](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/thorn_like_foil_surprise_reconciliation_magic_space.py) | 7/9 | 0 | 7/9 | 6.09 | 2.71 | 4/9 | 7.23 |
| [repaired_053: toe_pl_moisture_county_misunderstanding_teamwork_animal](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/toe_pl_moisture_county_misunderstanding_teamwork_animal.py) | 4/9 | 0 | 3/9 | 5.60 | 2.00 | 1/9 | 3.01 |
| [repaired_054: toss_definitive_friendship_sharing_nursery_rhyme](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/toss_definitive_friendship_sharing_nursery_rhyme.py) | 5/9 | 0 | 5/9 | 5.62 | 3.00 | 1/9 | 1.93 |
| [repaired_055: transcribe_children_s_museum_misunderstanding_friendship_repetition](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/transcribe_children_s_museum_misunderstanding_friendship_repetition.py) | 7/9 | 0 | 4/9 | 5.99 | 2.29 | 1/9 | 4.86 |
| [repaired_056: transmission_mushroom_lesson_learned_sound_effects_misunderstanding](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/transmission_mushroom_lesson_learned_sound_effects_misunderstanding.py) | 5/9 | 0 | 4/9 | 6.32 | 3.00 | 3/9 | 7.02 |
| [repaired_057: tube_cliff_lookout_quest_curiosity_sharing_nursery](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tube_cliff_lookout_quest_curiosity_sharing_nursery.py) | 6/9 | 0 | 3/9 | 6.13 | 3.17 | 2/9 | 4.66 |
| [repaired_058: treat_kefir_hyacinth_teamwork_misunderstanding_fairy_tale](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/treat_kefir_hyacinth_teamwork_misunderstanding_fairy_tale.py) | 6/9 | 0 | 6/9 | 5.23 | 2.50 | 1/9 | 3.53 |
| [repaired_059: yam_chuckle_laser_storm_drain_humor_flashback](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/yam_chuckle_laser_storm_drain_humor_flashback.py) | 5/9 | 0 | 4/9 | 5.14 | 2.80 | 0/9 | 0.68 |
| [repaired_060: yum_dim_crest_noon_curiosity_bravery_happy](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/yum_dim_crest_noon_curiosity_bravery_happy.py) | 7/9 | 0 | 5/9 | 6.09 | 3.00 | 4/9 | 7.16 |
| [repaired_061: yell_surprise_suspense_dialogue_animal_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/yell_surprise_suspense_dialogue_animal_story.py) | 5/9 | 0 | 3/9 | 6.22 | 1.80 | 1/9 | 2.38 |
| [repaired_062: blase_canned_sharing_inner_monologue_animal_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/blase_canned_sharing_inner_monologue_animal_story.py) | 4/9 | 0 | 4/9 | 6.53 | 2.75 | 3/9 | 6.94 |
| [repaired_063: deposit_pediatric_muddy_slope_mystery_to_solve](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/deposit_pediatric_muddy_slope_mystery_to_solve.py) | 4/9 | 0 | 4/9 | 6.33 | 2.25 | 2/9 | 3.86 |
| [repaired_064: webbed_joey_conflict_mystery](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/webbed_joey_conflict_mystery.py) | 9/9 | 0 | 8/9 | 6.32 | 2.78 | 4/9 | 9.98 |
| [repaired_065: destructor_sharing_surprise_cautionary_nursery_rhyme](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/destructor_sharing_surprise_cautionary_nursery_rhyme.py) | 3/9 | 0 | 3/9 | 4.77 | 2.67 | 0/9 | 0.00 |
| [repaired_066: equivalent_sherbet_kindergarten_kindness_dialogue_ghost_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/equivalent_sherbet_kindergarten_kindness_dialogue_ghost_story.py) | 7/9 | 0 | 7/9 | 5.74 | 2.57 | 2/9 | 7.87 |
| [repaired_067: eyed_cautionary_sharing_humor_pirate_tale](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/eyed_cautionary_sharing_humor_pirate_tale.py) | 6/9 | 0 | 6/9 | 5.42 | 3.00 | 2/9 | 2.84 |
| [repaired_068: commit_riverbank_transformation_quest_slice_of_life](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/commit_riverbank_transformation_quest_slice_of_life.py) | 9/9 | 0 | 9/9 | 5.42 | 2.56 | 2/9 | 2.44 |
| [repaired_069: head_scrawny_sneer_sound_effects_lesson_learned](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/head_scrawny_sneer_sound_effects_lesson_learned.py) | 8/9 | 0 | 8/9 | 6.20 | 2.88 | 5/9 | 9.62 |
| [repaired_070: subjunctive_aquarium_sharing_slice_of_life](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/subjunctive_aquarium_sharing_slice_of_life.py) | 5/9 | 0 | 5/9 | 4.96 | 2.00 | 1/9 | 0.70 |
| [repaired_071: engrave_ceiling_conflict_friendship_detective_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/engrave_ceiling_conflict_friendship_detective_story.py) | 7/9 | 0 | 7/9 | 5.70 | 2.00 | 2/9 | 4.12 |
| [repaired_072: ghetto_chowder_repetition_happy_ending_ghost_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/ghetto_chowder_repetition_happy_ending_ghost_story.py) | 7/9 | 0 | 7/9 | 5.24 | 2.57 | 2/9 | 1.59 |
| [repaired_073: progeny_cemetery_semi_sharing_magic_dialogue_comedy](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/progeny_cemetery_semi_sharing_magic_dialogue_comedy.py) | 5/9 | 0 | 5/9 | 5.76 | 3.20 | 2/9 | 3.59 |
| [repaired_074: whatchamacallem_mansion_three_sharing_bad_ending_nursery](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/whatchamacallem_mansion_three_sharing_bad_ending_nursery.py) | 4/9 | 0 | 4/9 | 6.30 | 1.00 | 0/9 | 3.03 |
| [repaired_075: clarinet_tiara_rinse_lesson_learned_conflict_flashback](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/clarinet_tiara_rinse_lesson_learned_conflict_flashback.py) | 6/9 | 0 | 6/9 | 5.87 | 2.17 | 1/9 | 3.10 |
| [repaired_076: croquet_animal_diabetic_rhyme_nursery_rhyme](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/croquet_animal_diabetic_rhyme_nursery_rhyme.py) | 6/9 | 0 | 6/9 | 5.47 | 2.33 | 2/9 | 3.49 |
| [repaired_077: guppy_cashew_misunderstanding_bravery_slice_of_life](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/guppy_cashew_misunderstanding_bravery_slice_of_life.py) | 6/9 | 0 | 6/9 | 6.40 | 2.33 | 2/9 | 3.20 |
| [repaired_078: chief_urge_bows_teamwork_rhyme_superhero_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chief_urge_bows_teamwork_rhyme_superhero_story.py) | 7/9 | 0 | 3/9 | 5.26 | 2.43 | 1/9 | 3.14 |
| [repaired_079: mandolin_italian_navigate_repetition_bad_ending_happy](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/mandolin_italian_navigate_repetition_bad_ending_happy.py) | 8/9 | 0 | 8/9 | 6.41 | 2.38 | 3/9 | 6.04 |
| [repaired_080: sentence_trawler_reconciliation_bravery_tall_tale](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/sentence_trawler_reconciliation_bravery_tall_tale.py) | 4/9 | 0 | 3/9 | 5.53 | 3.00 | 1/9 | 3.13 |
| [repaired_081: banner_transformation_lesson_learned_space_adventure](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/banner_transformation_lesson_learned_space_adventure.py) | 7/9 | 0 | 6/9 | 6.79 | 2.14 | 4/9 | 9.27 |
| [repaired_082: instance_chowmein_lesson_learned_bad_ending_rhyme](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/instance_chowmein_lesson_learned_bad_ending_rhyme.py) | 8/9 | 0 | 0/9 | 7.25 | 1.00 | 0/9 | 0.66 |
| [repaired_083: jambalaya_lasagne_duplicate_foreshadowing_twist_problem_solving](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/jambalaya_lasagne_duplicate_foreshadowing_twist_problem_solving.py) | 6/9 | 1 | 4/9 | 6.25 | 2.67 | 2/9 (+1 unknown) | - |
| [repaired_084: putty_pupil_exclusion_playground_quest_conflict_pirate](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/putty_pupil_exclusion_playground_quest_conflict_pirate.py) | 8/9 | 0 | 8/9 | 5.39 | 2.62 | 1/9 | 2.52 |
| [repaired_085: coincide_linguine_icicle_warehouse_aisle_dialogue_slice](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/coincide_linguine_icicle_warehouse_aisle_dialogue_slice.py) | 5/9 | 0 | 5/9 | 5.60 | 2.20 | 1/9 | 4.64 |
| [repaired_086: infer_archer_colony_reconciliation_rhyming_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/infer_archer_colony_reconciliation_rhyming_story.py) | 8/9 | 0 | 7/9 | 5.44 | 1.75 | 1/9 | 3.34 |
| [repaired_087: somersault_sanitary_sound_effects_fable](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/somersault_sanitary_sound_effects_fable.py) | 9/9 | 0 | 6/9 | 5.63 | 1.56 | 0/9 | 2.30 |
| [repaired_088: alliance_shrivel_fifty_dining_room_surprise_detective](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/alliance_shrivel_fifty_dining_room_surprise_detective.py) | 4/9 | 0 | 4/9 | 4.95 | 3.00 | 0/9 | 0.00 |
| [repaired_089: stern_demolish_cautionary_animal_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/stern_demolish_cautionary_animal_story.py) | 7/9 | 0 | 7/9 | 5.60 | 1.86 | 1/9 | 5.61 |
| [repaired_090: veal_fast_twist_rhyming_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/veal_fast_twist_rhyming_story.py) | 7/9 | 0 | 2/9 | 6.90 | 3.29 | 1/9 | 6.14 |
| [repaired_091: bulls_lullabye_marina_transformation_friendship_mystery](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/bulls_lullabye_marina_transformation_friendship_mystery.py) | 6/9 | 0 | 0/9 | 6.32 | 2.50 | 0/9 | 1.10 |
| [repaired_092: fair_scrub_problem_solving_inner_monologue_bad](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/fair_scrub_problem_solving_inner_monologue_bad.py) | 8/9 | 0 | 8/9 | 5.49 | 2.50 | 1/9 | 4.78 |
| [repaired_093: iguana_canal_path_misunderstanding_animal_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/iguana_canal_path_misunderstanding_animal_story.py) | 3/9 | 0 | 2/9 | 7.07 | 2.00 | 0/9 | 4.36 |
| [repaired_094: connect_yak_quest_lesson_learned_suspense_whodunit](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/connect_yak_quest_lesson_learned_suspense_whodunit.py) | 8/9 | 0 | 6/9 | 5.79 | 1.50 | 0/9 | 3.31 |
| [repaired_095: coward_chord_bonus_friendship_happy_ending_fable](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/coward_chord_bonus_friendship_happy_ending_fable.py) | 7/9 | 0 | 7/9 | 5.24 | 2.43 | 1/9 | 4.36 |
| [repaired_096: equity_gamble_marmoset_mystery_to_solve_lesson](../worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/equity_gamble_marmoset_mystery_to_solve_lesson.py) | 7/9 | 0 | 5/9 | 5.13 | 1.71 | 1/9 | 2.09 |
| [repaired_097: wine_grump_mystery_to_solve_fable](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/wine_grump_mystery_to_solve_fable.py) | 6/9 | 0 | 4/9 | 6.13 | 2.50 | 2/9 | 3.73 |
| [repaired_098: coop_architect_pappy_bravery_mystery_to_solve](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/coop_architect_pappy_bravery_mystery_to_solve.py) | 7/9 | 0 | 7/9 | 6.11 | 3.14 | 4/9 | 6.39 |
| [repaired_099: evolution_pregnant_ewok_humor_animal_story](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/evolution_pregnant_ewok_humor_animal_story.py) | 6/9 | 0 | 6/9 | 5.88 | 1.00 | 1/9 | 1.33 |
| [repaired_100: salon_bushed_stylish_dialogue_reconciliation_fable](../worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/salon_bushed_stylish_dialogue_reconciliation_fable.py) | 6/9 | 0 | 5/9 | 5.63 | 2.33 | 1/9 | 6.27 |
