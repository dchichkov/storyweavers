# Mixed-seed trial: ten worlds, thirty stories

The richer seeds produced some better voices and images, but did not improve overall quality. The unchanged authoring contract strongly pulled worlds back toward invitations, gardens, quiet neighbors and object handoffs. This run measures the original frozen contract; the prompt correction requested during the run is saved separately and has not yet been evaluated.

## Results

| Measure | This trial | Earlier 100-world batch |
|---|---:|---:|
| Story overall, /9 | 6.70 | 7.18 |
| Within-world diversity, /9 | 1.70 | 2.45 |
| Conversation overall, /9 | 6.48 | 6.43 |
| Conversations judged usable | 100/180 (55.6%) | 53.7% |
| Mechanically accepted worlds / attempts | 10/15 (66.7%) | 100/131 (76.3%) |

This is a small, unpaired comparison using different seeds, not a causal estimate. The same Terra rubrics were used. The accepted-world bootstrap interval for story overall is 6.27–7.10; it does not account for judge bias. Manual reading found mistakes that the judge missed.

Thirty stories were evaluated, sampled as three per world from 100 locally generated stories each. There are 28 distinct selected texts; two pairs are exact duplicates. Two stories scored below 6/9. All 180 conversations were graded once, covering 518 turns (483 substantive answers and 35 abstentions). Dialogue conversations were particularly weak: 6/21 judged usable.

## Cost and execution

| Phase | Estimated USD |
|---|---:|
| Luna authoring, including failed attempts and repairs | $0.0900704 |
| Terra story judging | $0.0489900 |
| Terra conversation judging | $0.1300800 |
| Total | **$0.2691404** |

All 63 returned requests report Flex. Reported cache reads/writes are zero. There are no unresolved reservations for this run. Costs are returned-usage estimates using the existing rate table, not an invoice. The shared $15 campaign now has $5.39634632 committed upper spend/reservations. Authoring cost per accepted world was about $0.0090 in this small sample.

Five authoring attempts failed: three incomplete output-limited responses and two exhausted mechanics-repair attempts. The first ten seed slots tried deterministic replacements only after mechanical failure. Slot 7 exhausted indices 7/17/27; the separately recorded supplemental sequence then accepted index 37. No low-scoring world was replaced. All repairs used Luna; Terra only judged.

## Per-world scores

| World | Ingredients | Story /9 | QA usable /18 |
|---|---|---:|---:|
| mix_00000 | doctor_instruments, refrain, DoorsAndThresholds | 6.67 | 11 |
| mix_00001 | cloud_harbor, comic_cost, ContestOfWits | 7.00 | 18 |
| mix_00002 | fireside, both_right, inventor_magpie | 6.67 | 9 |
| mix_00005 | Alice’s Adventures in Wonderland, SmallAndGreat, deadpan | 7.67 | 4 |
| mix_00006 | reframed_prize, The Sorcerer’s Apprentice, mystery | 6.67 | 5 |
| mix_00008 | NamesAndPromises, generous_trick, Alice’s Adventures in Wonderland | 7.67 | 10 |
| mix_00009 | generous_trick, recognition, map | 7.00 | 16 |
| mix_00013 | earned_surprise, dialogue, belong | 6.00 | 7 |
| mix_00014 | keep_promise, The Ugly Duckling, DoorsAndThresholds | 6.33 | 8 |
| mix_00037 | The Fisherman and His Wife, FireAndLaughter, Escalation | 5.33 | 12 |

## What the text actually does

- **Prompt copying:** the old contract literally supplies Ada wanting to deliver invitations, garden weather and a quiet/join neighbor. It also required Observe/Tell/Transfer. These details recur across otherwise unrelated seeds.
- **Some real charm:** the expert magpie says “My diagnosis was nearly correct,” described as “his favorite distance from wrong.” The giant story has a pleasant deadpan voice. These gains mostly happen at sentence level.
- **Weak causal kernels:** the enchanted saddle does not help deliver the list, then stops merely when told to stop. A mystery resolves because a ribbon is announced to be a sun catcher. In the last world, laughter makes a brazier safe with no established mechanism.
- **Branch contradictions:** a bent needle becomes straight without an event; still weather acquires a breeze; a window-shaped pancake is called a tower. Physical ownership bookkeeping also leaks into prose.
- **QA/prose disagreement:** answers refer to absent props, retain ownership after a narrated handoff, or state prerequisites instead of explaining motives. Dialogue extraction combines different speakers and skips intervening speech. Green replay checks do not establish that an answer follows from the visible story. The judge also missed the eaten bun remaining in the ownership answer.

## Vocabulary and validation

Exact case-insensitive word coverage: 25/30 selected stories and 878/1000 pool stories contain every required word. Inflections count separately in this audit: e.g. acquiesced is not the exact requested acquiesce. Presence alone does not prove natural usage. `cdefg` became a tune; `alls` became the ungrammatical banner ‘alls welcome’; hygienist helped push the last world into an incoherent clinic premise.

All ten world artifact hashes match, each has 100 local samples, every selected story and conversation is graded once, and mechanical QA checks report no defects. The 138 existing tests passed before the trial. No runtime changes were made in this pass. These checks establish reproducibility and shape, not storytelling quality.

## Prompt correction and next direction

The live AUTHORING_COMPACT.md now distinguishes required schema keys from illustrative content, uses placeholders in the entity example, explicitly directs content selection from the seed, and removes mandatory delivery/Observe/Tell/Transfer phrasing. Its old/new diff is in review/prompt_correction.diff. All trial authoring, including the final replacement, used the hash-checked original contract. The correction is not yet quality-tested.

The agreed next direction is several composable built-in palettes contributed by selected ingredients: school situations and mystery patterns can both supply operations. Choose relevant pieces across the palettes; do not require every listed operation. Those palettes are a proposed next step, not implemented by this trial. This preserves the north star: patterns act through physical characters, props and persistent state, and generation remains local execution.

## Reading and reproducibility files

- [Two worlds: six stories plus all conversations](TWO_WORLDS.md)
- [All thirty selected stories and their seeds](STORIES.md)
- [Manual reading notes](review/manual_notes.md)
- [Full metrics](evaluation_summary.json)
- [Coverage and per-world analysis](analysis.json)
- [Vocabulary audit](seed_audit.json)
- Frozen sources: _authoring/, _runtime/, _evaluation/, _scheduling/. Request/response artifacts and grades are in each world folder. Settings, initial_briefs.json and supplemental_attempts.json preserve the sampling procedure.
