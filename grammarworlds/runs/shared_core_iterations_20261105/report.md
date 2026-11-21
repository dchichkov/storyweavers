# Shared story core: three iterations

The seven worlds now share event commitment, declarative physical effects,
transition prerequisites, transfer guards, lexical entries, and several scene
families. Their custom packs are smaller. Using the shared scene families to
expand dialogue increases next-token choice frequency while retaining grounded
events and QA. This remains seven authored worlds, not a general plot planner.

## Iterations

Development used seeds 20–24, seven worlds, past/present tense. Baseline and the
first two stages each generated 280 stories across original/expanded grammar and
heads off/manual. The third stage generated 350, adding a separate tuned profile.

1. **Physical operations.** One validated commit protocol replaces seven copies.
   There are 73 declarative effect entries across the packs: move an existing
   entity, add/remove its state. Candidate-frame validation, snapshot/history,
   flags and focus are shared. All effect bindings are checked before mutation;
   specialized callbacks are not a general transactional rollback system.
   All 280 compact records exactly matched baseline: text, QA, paths, metrics,
   and changed-probability traces.
2. **Scene families and lexicon.** Shared intention, ability, offer, transfer and
   fetch families replace repeated constructions; fetch also shares grounded QA.
   Identical lexical entries move into a common dictionary; conflicting senses
   keep local overrides. Shared transfer guards require a held item and two
   co-located people, with permission/safety checks remaining in world packs.
   Again all 280 records exactly matched baseline.
3. **Reusable variation and receiver experiment.** The expanded grammar adds
   explicit listeners (`Sam told Mum…`), offers (`Let me…`), future intentions
   (`I'll…`), explicit future promises (`I promise I'll…`) and lexical alternatives
   inside action intentions. Abilities stay distinct from offers. Development
   review excluded `discover` and `hand` inside intentions because they weakened
   lost-object/gift purposes. Quote-head resolution now handles explicit
   listeners and `Let me` without treating the listener as speaker. A separate
   softer tool/state profile is available as `--head-profile tuned`.

The unchanged original grammar and manual weights remain defaults. The added
realizations require `--continuations expanded`; tuning is separately opt-in.

## Source size

Measured over the same 13 custom world/plan files before and after:

| Measure | Before | After | Change |
|---|---:|---:|---:|
| Python lexical tokens | 26,371 | 24,744 | −6.2% |
| AST statements | 1,242 | 1,022 | −17.7% |
| Bytes | 112,490 | 107,414 | −4.5% |
| Lines | 1,637 | 1,588 | −3.0% |

Python lexical tokens exclude comments and whitespace tokens; they are **not**
LLM tokens or model parameters. AST statements include declarations and are not
a count of semantic rules. The seven packs still declare 119 event-kernel entries.

This is a reduction in custom authoring, not net compression: all top-level
storytelling `.py` and `.json` files together grow from **197,682 to 207,277
bytes (+4.9%)**, including the shared layer, common lexicon, additional grammar,
optional weights and evaluation code. Tests, pins, docs and run artifacts are
excluded from that total. Much of the new layer is an up-front reuse cost.
Entity inventories, specialized consequences and most full scene plans remain
custom. No claim that arbitrary worlds can be authored only as data is made.

## Fresh-seed comparison

Weights/grammar were fixed before seeds **3000–3019**. Each profile has 280
stories: 7 worlds × 2 tenses × 20 seeds. The archived pre-merge package supplies
the baseline on exactly the same seeds. In total, 1,120 baseline and 1,400 merged
generations passed validation, with 15,120 QA pairs.

| Version / expanded profile | Choice steps | ≥4-way steps | Distinct texts / 280 | Mean words | Head-changed distributions | Texts changed by heads |
|---|---:|---:|---:|---:|---:|---:|
| Before / off | 7.36% | 194 | 272 | 91.10 | 0 | 0 |
| Before / manual | 7.36% | 198 | 272 | 90.96 | 470 | 26 |
| Merged / off | 10.82% | 180 | 280 | 92.59 | 0 | 0 |
| Merged / manual | 10.82% | 182 | 280 | 92.74 | 425 | 23 |
| Merged / tuned | 10.82% | 182 | 280 | 92.75 | 413 | 18 |

For the main manual comparison, choice steps rise from 2,595/35,257 to
3,874/35,807: **+3.46 percentage points**, about 47% higher frequency. Token
steps include punctuation and end markers, as in the earlier experiment.
Most added forks are two-way. Four-or-more-way forks actually decline slightly;
this is not progress toward four choices at every word.

Distinct-text totals sum within world/tense groups. Distinct event paths remain
65 across those groups for all expanded profiles: increased wording variety
has not produced new plot families. Variable-length wording consumes different
random draws, so matched seeds can change later paths without demonstrating an
intentional plot preference from heads.

The original grammar's off/manual profiles retain **560 exactly identical
records** between archived baseline and final code. The two refactoring stages
therefore separate behavior preservation from the later deliberate expansion.

### An actual four-way token decision

Fresh greenhouse sample, manual heads, prefix `Nia told Mr Bell, “I`:

| Next word | Probability |
|---|---:|
| want | 31.46% |
| would | 28.72% |
| can | 19.91% |
| could | 19.91% |

These come from the currently legal forest. State changes occur only after the
chosen sentence resolves to a legal frame; the adapter does not peek at a future
chosen frame. See `final_merged/sample_traces.jsonl.gz` for full distributions.

## Story and QA review

[Seven unfiltered samples with QA](samples.md) use seed 3000, past tense,
expanded/manual, selected by the harness before generation. Also inspected
seed 3000's seven expanded/tuned present-tense stories and all seven development
worlds. Premises, causal turns, physical consequences and ending images remained
legible in those samples. Examples:

- Kite: attempted repair fails; the paper becomes a boat's sail. Dialogue gains
  `I would like to fix the kite` and `Let me cover the tear` without changing
  the repair/failure/reuse sequence or its explanation.
- Music: Mateo declines the audience; Nia says `I'll perform a solo`. The
  ending and QA respect his refusal.
- Greenhouse: the sunflower is watered first; the brown leaf persists through
  repair. `I promise I'll water the tomato seedlings first tomorrow` preserves
  an explicit promise and its consequence.
- Pottery: the dent becomes a thumb rest after the wall inspection; firing and
  cooling precede gifting and tea. Grandpa's capability statement does not get
  the new offer-only `Let me` form.

Known roughness remains: repetitive names, procedural stretches, occasional
formal `locate` wording, and some shallow single-sentence QA answers. Mechanical
checks and this limited manual review support preservation of the existing
quality level; they do not establish literary improvement. No independent Luna
judge was run in this pass, and no numeric literary score is claimed.

## What the heads contributed

No new heads were added. The same four activate; P023 and P059 remain the two
that affect distributions. The tuned profile covers more instrument affordances
and gives synonymous actions equal preference, but uses softer multipliers.
Its total variation summed across word decisions is 14.36 versus 22.85 for the
merged manual profile. It changes fewer distributions and sampled texts, with
no demonstrated quality advantage. Keep the original manual profile as the
comparison default; tuned is an experiment, not an upgrade claim.

## Verification and limits

- **95 tests pass** across shared-core, continuation, head, storytelling,
  branch, eval, symbolic-head, base grammarworld and portable suites.
- All fresh generations pass event replay, completion, normalized positive
  probabilities, dialogue, question diversity, answer shape and exact QA
  evidence-span checks. These checks do not prove every paraphrase equivalent.
- **383 physical guard interventions** on the seven preselected fresh tuned
  traces reject removed carriers/prerequisites and forged actors without
  mutating state. The new transfer test also uses unfamiliar people/object IDs.
- Nine frozen portable-source hashes remain unchanged.
- New regression coverage replays seven pre-merge physical histories and checks
  declarative validation, role binding, ability/offer separation, promise
  preservation, speaker resolution and consent at high head strength.

Shared physical effects remain attached to entities; legal moves still depend
on persistent state. Water conservation, relationship changes, consent, safe
firing and the final proof of change stay in specialized callbacks/plans. This
moves toward the memeplex north star without pretending all consequences are
interchangeable or introducing a runtime LLM.

The next useful merge is another complete scene family with role-bound QA and
a real cross-world transition test—such as borrow/use/return with permission and
an outstanding obligation. Sharing only more wording will not expand semantic
continuation space.

## Reproduction and artifacts

```sh
.venv/bin/python -m grammarworlds.storytelling --scenario all --seed 3000 \
  --continuations expanded --heads --qa
.venv/bin/python -m grammarworlds.storytelling.head_comparison --expanded --tuned \
  --start 3000 --count 20 --out /tmp/shared-core-comparison
.venv/bin/python -m grammarworlds.runs.shared_core_iterations_20261105.analyze
.venv/bin/python -m unittest grammarworlds.test_shared_story_core \
  grammarworlds.test_continuations grammarworlds.test_story_heads \
  grammarworlds.test_storytelling grammarworlds.test_storytelling_branches \
  grammarworlds.test_storytelling_eval grammarworlds.test_symbolic_heads \
  grammarworlds.test_grammarworlds grammarworlds.test_portable
```

- `baseline_source/grammarworlds/`: executable pre-merge package; run it from
  `baseline_source` with the repository's absolute Python executable.
- `iteration1_source/`, `iteration2_source/`, `iteration3_source/`: stage code.
- `baseline/`, `iteration1_operations/`, `iteration2_families/`,
  `iteration3_variation/`: development records and source manifests.
- `final_baseline/`, `final_merged/`: fresh summaries, source hashes, compressed
  texts/QA/changed distributions, full preselected traces and paired samples.
- `analysis.json`, `*_custom_size.json`: size/guard/equivalence measurements.
- Implementation: [operations](../../storytelling/operations.py),
  [scene families](../../storytelling/scene_families.py),
  [expanded grammar](../../storytelling/continuations.py).
