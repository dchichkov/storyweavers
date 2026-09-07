# Dialogue Requirement: Matched Paid Trial

Completed 2026-09-07. Trial `dialogue_required_v11_20260907` compares the new
dialogue requirement with [the v10 baseline](dialogue_v2_baseline_20260907.report.md).
**Dialogue increased and mean story quality improved; semantic diversity did
not improve, and the composite dataset score fell slightly.**

## Matched Setup

- Same seven `dialogue_v2` references: Puddles, Pirates, Garnet, Library, Cart,
  Bridge, Nell v2. All seven source hashes match the baseline exactly.
- Same three tasks per reference, seed `2026090605`: dining-room quest with
  `decide`/`darling`, gingham/magic nursery rhyme, nose/sharing/foreshadowing
  bedtime story. Same local sample seeds 777/778/779.
- Luna (`gpt-5.6-luna`), reasoning `none`, Flex, concurrency 5, source emission,
  32k output cap, 900-second API timeout; no addendum.
- Same Terra (`gpt-5.6-terra`) judge, calibration, ten random story positions
  per world, reasoning `none`, Flex; unchanged quality/diversity formula.
- Preflight compared all task metadata and source fingerprints. Only `STORY.md`
  and the shared prompt builder differ from v10. Protocol v11 adds a brief
  consequential spoken exchange in every sample, excludes inner monologue and
  quoted notes, and explicitly gives the current contract precedence over older
  examples. Seed-feature sampling was not changed.
- All 21 generation calls and 21 judge calls completed successfully. All actual
  returned tiers are Flex. No extra generation or paid exploratory requests.

These are matched tasks, not identical model draws or a replicated experiment.
There is one newly generated program per arm/task. The 210 story ratings are
clustered within 21 programs, not 210 independent generation experiments.

## Main Comparison

Both columns below use the final, separately documented manually assisted
corpora. Automatic-only outcomes are shown separately afterward.

| Metric | V10 baseline | V11 dialogue required |
| --- | ---: | ---: |
| Mean story quality /9 | 6.41 | **6.92** |
| Mean semantic diversity /9 | 1.19 | **1.19** |
| Geometric dataset score /100 | 6.26 | **5.91** |
| Worlds meeting mean quality >= 6 | 13/21 | 15/21 |
| Individual judged stories below 6 | 66/210 | 36/210 |
| Quoted-word fraction | 17.7% | **34.0%** |
| Mean story words | 191.1 | **252.4** |
| Mean story + story-QA words | 304.3 | **365.4** |
| Returned / requested local stories | 20,915 / 21,000 | 20,504 / 21,000 |
| Exact unique story strings | 11,637 | **9,720** |
| Quality-qualified exact uniques | 7,135 | 6,700 |
| Full shuffled story corpus XZ/input | 1.94% | **1.66%** |
| Exact-deduplicated corpus XZ/input | 2.24% | 2.21% |
| Qualified compression retention | 4.14% | 4.09% |
| Estimated generation + judge cost | $0.2925 | **$0.3195** |

Quoted words use the same heuristic in both runs: straight/curly double-quoted
text and standalone single-quoted spans. This includes thoughts, chants, and
notes; it is not a semantic dialogue score. Separately, **all 21 manually read
v11 samples contain spoken back-and-forth**, often used to agree on a plan,
ask for a clue, or coordinate an action. That observation applies to the reviewed
sample from each world, not a manual certification of all 20,504 stories.

Paired by reference/task, mean quality increases in 11 worlds, is unchanged in
one, and decreases in nine. The overall increase is 0.50 points. The high score
of the easiest-to-run subset is not used as the main headline.

## Per Reference

Each row represents three generated programs, 3,000 requested local stories,
and 30 judged stories. Final quality/diversity are conditional on the assisted
repairs listed below. Composite scores recompress each arm's own qualified pool;
the whole-trial score is not an average of these scores.

| Reference | V10 quality | V11 quality | V11 semantic diversity | V11 exact uniques | V11 composite /100 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Puddles | 5.80 | 6.47 | 1.67 | 1,652 | 3.54 |
| Pirates | 5.67 | 7.67 | 0.33 | 2,544 | 14.88 |
| Garnet | 6.43 | 6.80 | 3.00 | 3,000 | 11.26 |
| Library | 6.07 | 7.23 | 0.67 | 793 | 4.96 |
| Cart | 6.80 | 6.83 | 0.67 | 983 | 2.87 |
| Bridge | 6.37 | 5.63 | 1.00 | 628 | 1.08 |
| Nell v2 | 7.77 | 7.80 | 1.00 | **120** | **0.82** |

Nell is still the highest-quality reference arm on this tiny task set, but its
three programs produce only **6, 6, and 108** exact strings in 1,000 draws each.
The dining and rhyme scripts fix voice/mood or protagonist defaults and offer
very few effective text variants; advancing prose seeds does not create new
authored alternatives. The bedtime story also follows one fixed causal path.
This is a measured collapse, not evidence that the original Nell v2 reference
itself has only 120 stories. That reference remains unchanged.

Pirates gains the most quality, while its semantic diversity drops. Garnet
retains the most substantial within-world causal variation, although its
bedtime outputs still have bad phrase assembly and speaker-name errors.

## Reliability And Repairs

| Stage | V10 baseline | V11 |
| --- | ---: | ---: |
| Raw sampleable programs | 11/21 | 12/21 |
| Accepted automatic repairs | 3 | 2 |
| Sampleable after automatic repair | 14/21 | 14/21 |
| Own verification passes after automatic repair | 14/21 | **11/21** |
| Standalone CLI passes after automatic repair | 0/21 | 0/21 |
| Manually recovered worlds needing non-import changes | 7 | **10** |
| Final sampling / verification / standalone / replay | 21/21 | 21/21 |

Six v11 raw programs have syntax errors. Most are mismatched quote boundaries;
one also has an unclosed import-path expression, and one closes a string tuple
with a brace. More dialogue did not remove code-generation fragility. This
single pilot cannot establish a causal increase in syntax-error rates.

The unchanged automatic repair policy accepts a fix after a sampling probe,
not the full own-verification gate. Both accepted automatic repairs were in the
Puddles arm and still failed `--verify`. The saved automatic `eval_001` judged
11 worlds/110 stories: quality **7.45/9**, semantic diversity **1.00/9**, composite
**4.32/100**. That is a selected subset, not the full-corpus quality of 6.92/9.

The existing nested-path defect remains: automatic sampling injects
`PYTHONPATH`, while direct execution cannot locate the helpers. All 21 final
materialized copies locate the ancestor containing `results.py` and `asp.py`.
This is recorded as manual assistance, not silently counted as automated success.

| Generated program | Additional recovery |
| --- | --- |
| Puddles/dining | Restore raw source, repair quote boundary; replace a false exact-substring assertion on QA paraphrases with exact trace-derived QA/render consistency. Keep physical outcome checks. |
| Puddles/bedtime | Restore raw source and repair quote boundary, avoiding the broad fallback edits retained in the automatic snapshot. |
| Pirates/dining | Repair the adjacent f-string quote boundaries. |
| Pirates/bedtime | Repair the missing import-path parenthesis and a quote boundary, using the original source rather than a broad fallback rewrite from the first manual check attempt. |
| Garnet/bedtime | Repair one f-string delimiter. |
| Cart/dining | Represent the selected `plan` as a real dataclass field, validate compatible worry/plan pairs, and return the found cup to the table with a recorded action. |
| Bridge/dining | Correct the closing delimiter of `PROMPT`. |
| Bridge/gingham | Remove the erroneous ASP condition requiring a problem ID also to be a repair ID; keep the problem-to-repair relation and registered repair requirement. |
| Bridge/bedtime | Narrow the debug-leak guard so ordinary `friend`/`friends` is allowed while template braces, entity reprs, and meter/meme assignments are still rejected. |
| Nell/dining | Close the story once `quest_complete` is established; previously the policy repeated the final action without ever recording an ending. |

Raw responses and `eval_001` are untouched. `manual_001/before/` snapshots the
post-automatic sources. Both manual check attempts, exact diffs, regression
tests, and final source copies are retained. No global repair or prompt change
was made during the run. Seven focused recovery tests pass, including invalid
plan rejection, unresolved-world rejection, changed-QA rejection, and ASP
behavior without a mapped repair. The existing 94-test suite also passes.

The 11 already judged full pools, including parameters and QA, are exactly
unchanged after their import-only fixes. Their ratings are reused with origin
metadata. Only the ten recovered worlds incurred another 100-story judge pass:
**210 submitted sample positions total, not 320**.

## Manual Review

Read the first selected judge sample from every world with all its story QA and
world QA before examining ratings. Exact records are retained in
`manual_001/manual_review_samples.json`. Dining IDs are `s000234`, except
Puddles/dining `s000117` because its returned pool is shorter; rhyme IDs are
`s000043`, bedtime IDs `s000576`.

The dialogue requirement visibly works. Library's quest exchanges clues before
searching, Bridge's rhyme explains and tests a knot, Pirates' toy rescue weighs
a risk before asking for help, and Nell's new stories now have actual spoken
exchanges. But a number of exchanges repeat the moral or narrate a decision
already made, rather than exposing a distinct viewpoint or changing the plan.

Important remaining defects, deliberately not rewritten after evaluation:

- Bridge/dining leaks `{d}`; the spoon sound is left unrelated to the chair
  repair. Terra flags the placeholder and weak causal link (world quality 4.5).
- Cart/dining switches between sampled Nia/Nora and hardcoded Leo/Mina in both
  prose and QA. Terra catches the story name confusion (5.1).
- Bridge/bedtime repeats dialogue and produces `their the warm blanket` and
  `the the warm blanket`. Terra flags both repetition and grammar (4.4).
- Garnet/bedtime has a character addressing their own name and `The a faint
  squeak`; QA repeats malformed clauses. Terra flags prose defects (5.6).
- Library/bedtime splits a `starstone` into portions, feeds it to a rabbit,
  and has the children eat it, without establishing it as edible. The related
  tea scent does not resolve the object/action mismatch. Terra nevertheless
  calls the reviewed sample coherent (world quality 7.0).
- Library/dining follows a clue to a pantry shelf, then receives an instruction
  to open a drawer. The scene ends coherently enough to be rated 7.0, but the
  location/action match remains weak.
- Cart/bedtime moves between gate and window without clean spatial staging;
  it earns 8.0 despite that ambiguity.
- Puddles/dining combines a berry stain with a thought about something being
  trapped. It is a branch-compatibility problem, not a missing quote.
- Puddles/bedtime uses the noun `blanket` even when the selected missing object
  changes elsewhere in the sampled set. Careful lexical substitution still
  matters after successful code repair.

The judge sees story prose, not QA or executable traces. These scores do not
certify QA grounding, physical consistency, or training readiness. No attempt
was made to massage low ratings by editing stories and buying new judgments.

## Sampling And Compression

Puddles/dining internally deduplicates 1,000 attempted draws to **504 returned
stories**, without replacement draws. No output is padded. The other 20 scripts
return 1,000 each. The scorer retains the full 21,000 requested denominator.
The short pool also changes its judge selection population; this is documented
rather than presented as an unbiased sample of its original draws.

The final pooled archive compresses **all 20,504 returned story strings together**,
with no prompts, QA, parameters, filenames, or trace metadata. UTF-8 JSONL, XZ,
LZMA2 preset 6, 64 MiB dictionary, deterministic shuffle seed 0.

| Corpus | Stories | Input bytes | XZ bytes | XZ/input |
| --- | ---: | ---: | ---: | ---: |
| All, shuffled | 20,504 | 30,013,487 | 498,368 | **1.66%** |
| All, grouped | 20,504 | 30,013,487 | 396,176 | 1.32% |
| Exact deduplicated, shuffled | 9,720 | 12,748,709 | 281,288 | **2.21%** |
| Unique slot-normalized skeletons | 346 | 414,059 | 19,664 | 4.75% |
| Word-order-destroyed control | 20,504 | 29,291,469 | 7,692,556 | 26.26% |

The full shuffled pool is **28.62 MiB -> 486.7 KiB**, 24.31 compressed
bytes/story. This is more compressed bytes/story than v10's 21.43, but also
substantially more words/story. Lower compressed/input ratio does not alone
measure improvement or decline. Qualified cross-story compression retention
is almost unchanged; reduced usable unique yield drives the lower composite.
Skeleton counts are not counts of independent plots.

At 10/50/100/250/500/1,000 samples per world, shuffled bytes/story are
121.85/52.21/39.78/30.36/26.49/24.31. These prefixes are separate from the random
judge sample. The word-order-destroyed control again shows why compression
cannot be optimized without a prose-quality gate.

## Spend And Artifacts

Returned-usage estimates at the repository's recorded Flex rates, not account
invoice reconciliation. No unknown/unpriced responses in these 42 calls.

| Work | Calls | Input tokens | Output tokens | Estimated USD |
| --- | ---: | ---: | ---: | ---: |
| Luna generation | 21 | 258,576 | 85,913 | $0.083868 |
| Initial Terra judging | 11 | 51,379 | 9,634 | $0.122020 |
| Recovered-world Terra judging | 10 | 46,788 | 9,191 | $0.113624 |
| Total | **42** | **356,743** | **104,738** | **$0.319511** |

Judging totals **$0.235643**, versus $0.210983 in v10, partly because the
stories are longer. Agent repair/local compute is excluded. Returned usage does
not prove that no unobserved transport/provider retry was billed.

Trial directory: `storyworlds/batches/prompt_trials/dialogue_required_v11_20260907/`.
Materialized sources: `storyworlds/worlds/prompt_trials/dialogue_required_v11_20260907/`.
The archive includes frozen requests/source snapshots, original responses/raw
scripts, automatic and manual check attempts, before/after patches, final JSONL
pools, judge requests/responses, reused-rating provenance, manual-review records,
local analysis/repair helpers and tests, and all pooled compression controls.
There are no per-story Markdown files. Historical v10 artifacts remain unchanged.

Retained snapshot: [trial archive](../batch_archives/prompt_trial_dialogue_required_v11_20260907_20260907T082127Z.tar.gz)
and [SHA-256 checksum](../batch_archives/prompt_trial_dialogue_required_v11_20260907_20260907T082127Z.tar.gz.sha256).
The embedded report predates these archive links; its measurements are identical.

```bash
# Read the original automatic-only evaluations without spending.
./.venv/bin/python storyworlds/prompt_trials.py report dialogue_v2_baseline_20260907 dialogue_required_v11_20260907

# Local-only reproduction after restoring this trial's archive.
./.venv/bin/python storyworlds/batches/prompt_trials/dialogue_required_v11_20260907/manual_001/test_repairs.py
./.venv/bin/python storyworlds/batches/prompt_trials/dialogue_required_v11_20260907/manual_001/analyze.py
```

The standard report command intentionally shows `eval_001`, not the separately
assisted corpus described here. Do not call `evaluate` just to inspect results;
it creates another paid judge pass. Keep the dialogue requirement for the
dialogue objective, but target state-dependent branch compatibility and real
causal variation next. The present run does not establish a better training
dataset despite better average story quality.
