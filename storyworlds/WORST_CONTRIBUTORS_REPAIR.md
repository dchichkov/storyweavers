# Worst-Contributor Repair Campaign

This campaign repairs 120 production StoryWorld scripts in waves of six. The
selection combines historical `gpt-5.4-mini` story-quality ratings with
per-world generation statistics preserved in the production export manifests.

## Evidence And Scope

- Production worlds successfully exported: 6,855.
- Worlds with historical quality ratings: 685 (10.0%).
- Worlds with any exact generated-story duplicates: 476.
- Worlds with at least 50% exact duplicates: 224.
- Worlds with at least 90% exact duplicates: 114.
- Rated worlds with overall quality at most 5 and exact duplicates: 21.
- Exact duplicate stories were removed before the final JSONL was written.
  Repeated and near-template QA remains a separate corpus-level issue.

The target list prioritizes worlds with both low quality and high duplication,
then the remaining lowest-quality rated contributors and highest-duplication
contributors. A single historical quality rating is only a triage signal, not
proof that every seed is poor.

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
| 2 | active | `garnet_humor_curiosity_repetition_tall_tale.py` | 1 skeleton/100 exact-unique stories | pending | pending | |
| 2 | active | `hibachi_rhyme_suspense_comedy.py` | 1 skeleton/100 exact-unique stories | pending | pending | |
| 2 | active | `loop_energy_ginger_conflict_pirate_tale.py` | 1 skeleton/100 exact-unique stories | pending | pending | |

Additional waves are appended after the full 120-script ranking is frozen.
