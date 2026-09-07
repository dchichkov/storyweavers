# Three Sequential Prompt Trials

Authorized: three paid trials, 21 generated worlds each, using the existing
canonical evaluation protocol. This is an optimization set, not a held-out test.

## Result

Completed all three paid runs: **63 generated worlds, 63,000 local draws,
63 ten-story Terra sets, 630 individual ratings**. Estimated API cost is
**$0.893199** total, excluding the previous baseline and local/agent work.
All 63 final sources pass the four local checks after separately logged repairs.

| Variant | Quality /9 | Semantic diversity /9 | Assisted composite /100 | Automatic composite /100 |
| --- | ---: | ---: | ---: | ---: |
| Previous dialogue-required baseline | 6.919 | 1.190 | 5.905 | **4.316** |
| R1: causal paths | 6.719 | **3.048** | **7.625** | 2.999 |
| R2: executable-path checklist | 6.295 | 2.429 | 6.454 | 1.374 |
| R3: concise complete scenes, final placement | **7.162** | 2.905 | 2.748 | 1.548 |

| Variant | Automatic sample + verify | Non-import manual repairs | Exact uniques | Qualified uniques | Story / story+QA words | API USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 11/21 | 10 | 9,720 | 6,700 | 252.4 / 365.4 | 0.319511 |
| R1 | 7/21 | 14 | 12,115 | 8,427 | 170.8 / 257.5 | 0.312444 |
| R2 | 5/21 | 16 | 11,489 | 7,825 | 180.2 / 263.6 | 0.306981 |
| R3 | **13/21** | **8** | 3,032 | 2,942 | 153.2 / 230.2 | 0.273774 |

Automatic sample+verify is the existing score's gate, not the stricter final
four-check gate. Standalone-import fixes are counted separately. The baseline
returned 20,504 of 21,000 requested rows; all new trials returned all 21,000.
Quality and semantic-diversity means cover all 21 repaired worlds; the composite
uses quality-qualified unique texts, so these columns have different weighting.

**No unqualified production winner.** R1 raises the assisted composite by 29.1%
and qualified unique yield by 25.8%, but needs more repair and loses 0.20 quality
points. R2 is worse than R1 on both quality and diversity. R3 gives the strongest
story quality and best automatic pass count, but its small realized variation
space overwhelms those gains. None beats the baseline's automatic-only score.
No candidate has been enabled by default and no fourth paid run was made.

The next useful experiment would keep R3's complete scenes while requiring the
CLI to actually sample compatible prose/scene alternatives, borrowing R1's
variation guidance without its large cross-product. First fix deterministic
sampling/verification failures locally and add a sampling-diversity preflight;
then test on fresh tasks. R1's measured result belongs to its **frozen v11
placement**: supplying the same file to the current v12 builder changes that
placement and is not an already-validated reproduction.

## Frozen Controls

- Baseline: `dialogue_required_v11_20260907`, commit `0226c4a2`.
- Seven unchanged `dialogue_v2` references, three matched tasks each.
- Task seed `2026090605`; local sample seeds 777/778/779, 1,000 requested/world.
- Luna generation, reasoning none, Flex, concurrency 5, source emission.
- Terra/Flex ten-story set judging; same selection, rubric, quality floor, and
  geometric score formula. No changes to the judge or scoring implementation.
- Preserve raw generation, automatic-only checks, separately recorded manual
  recovery, sample pools, judge requests/responses, and compression artifacts.
- Reuse existing ratings only when their complete sampled pool is unchanged.
  At most 21 generation requests and 21 ten-story judge sets per candidate.
- Do not repair prose after seeing ratings. Manual recovery may fix execution,
  state transitions, or false verification guards; disclose all such assistance.

## Selection Policy

Compare automatic and assisted results separately. Use the existing composite
as the primary measure of usable unique yield and compressibility, with story
quality, semantic diversity, dialogue, manual review, and reliability as checks
against cosmetic or incoherent variation. Do not choose a candidate on a
conditional quality mean alone. No claim of statistical significance is planned.

Each next prompt is chosen after the previous trial's measurements and manual
review. Prompt text lives in separate addenda; no candidate is enabled by default.
Trial 3 also moves explicit addenda after the example and seed request, versioned
as prompt protocol v12. The no-addendum prompt text and canonical examples stay
unchanged. Trial 3 therefore tests content plus placement, not placement alone.

## Trial Log

| Trial | Hypothesis | Status |
| --- | --- | --- |
| `optimize_r1_causal_paths_20260907` | Explicit compatible causal paths plus genuinely sampled prose variants reduce fixed-plot collapse. | Completed; 21 worlds / 210 ratings |
| `optimize_r2_executable_paths_20260907` | Retain causal variety, but make a shared executable-path registry drive validation, state, text, and bounded sampling. | Completed; 21 worlds / 210 ratings |
| `optimize_r3_complete_scenes_20260907` | Shorter guidance after the example: three coherent paths, finished scenes, and path-specific endings/QA. | Completed; 21 worlds / 210 ratings |

Candidate 1: [`optimize_20260907_r1_causal_paths.md`](../prompts/optimize_20260907_r1_causal_paths.md).

Its preflight confirms identical task fields, seven reference-source hashes,
contract, prompt builder, sampler, repair code, judge, scorer, and API settings.
The only experimental input difference is the addendum (plus output paths).
The initial local factory/evaluation regression run passed 46 tests.

Implementation references consulted: official [prompt engineering guidance](https://developers.openai.com/api/docs/guides/prompt-engineering)
and [Luna model documentation](https://developers.openai.com/api/docs/models/gpt-5.6-luna).
Model, reasoning, and endpoint settings are intentionally unchanged.

## Trial 1 Findings

| Metric | Dialogue-required v11 baseline | Trial 1 |
| --- | ---: | ---: |
| Assisted quality /9 | 6.919 | 6.719 |
| Semantic diversity /9 | 1.190 | 3.048 |
| Assisted composite /100 | 5.905 | 7.625 |
| Automatic-only composite /100 | 4.316 | 2.999 |
| Exact unique stories | 9,720 | 12,115 |
| Quality-qualified unique stories | 6,700 | 8,427 |
| Mean story words | 252.4 | 170.8 |
| Mean story + story-QA words | 365.4 | 257.5 |
| Quoted-word share | 34.0% | 33.5% |
| Qualified compression retention | 4.093% | 4.551% |
| Full shuffled corpus XZ/input | 1.660% | 2.180% |
| Estimated API USD | 0.319511 | 0.312444 |

Trial 1 generation used 266,136 input / 106,067 output tokens ($0.096906).
Its 21 Terra sets used 73,808 input / 20,549 output tokens ($0.215538).
All returned models/tiers match Luna/Terra Flex; no unpriced responses.
Cost is estimated from returned usage, not invoice reconciliation, and excludes
local/agent recovery work. The 21,000-story shuffled corpus is 20,848,639 bytes
compressed to 454,492 bytes (21.64 compressed bytes/story). Exact-deduplicated
compression is 12,007,384 -> 303,308 bytes (2.526%).

Assisted result: quality **6.719/9**, semantic diversity **3.048/9**, geometric
score **7.6247/100**, 12,115 exact unique texts, 8,427 quality-qualified uniques,
15/21 quality-qualified worlds. All 21,000 requested samples were returned.
Compared with v11, variety improves materially on this matched optimization
set, but quality declines slightly and engineering reliability regresses.

Raw ten-sample probes pass 9/21; one automatic repair is accepted, but the full
1,000-sample pass still passes only 9/21 because Puddles/dining stalls while
deduplicating internally. Own verification passes 7/21. Final sampling, own
verification, standalone CLI, and cross-hash-seed replay pass 21/21 after
14 non-import manual recoveries. Seven complete already-judged pools are
identical and their ratings are reused; only 14 new sets/140 stories are judged.
Eight focused recovery regression tests pass. All check attempts are retained.

Manual recovery is not prompt success. Changes are preserved as source diffs:

- All 21: ancestor helper imports for nested targets.
- Puddles/dining and Garnet/bedtime: bounded raw sampling, with downstream dedup;
  no replacement draws to force uniqueness. Puddles' verifier now uses the
  existing entity dictionary rather than a nonexistent `World.get` method.
- Pirates/bedtime and Garnet/bedtime: narrow quote-delimiter repairs. Pirates
  initializes missing emotion meters and checks derived ASP atoms instead of
  searching for a literal fact string; its verifier also generates all nine
  problem/solution combinations. Garnet adds the missing cold/blanket ASP rule;
  its existing verifier is still a narrow default-case check, not certification
  of a complete ASP twin.
- Library's three worlds: remove copied arbitrary speech-count thresholds while
  retaining both-speaker and grounding checks. Dining records speaker IDs and
  sorts its set before seeded selection. Bedtime records the trust change from
  sharing information/light. Cart/dining and Bridge/bedtime accept two existing
  grounded QA pairs instead of requiring three.
- Cart/rhyme: align the ASP tuple order with Python. Cart/bedtime: store the
  trust change in memes, not physical meters.
- Bridge/rhyme: restore the missing approach field and sampling; restrict
  compatibility to the four actually rendered problem/solution paths. Remove
  the arbitrary speech quota. Bridge/bedtime: one real sharing action is enough;
  preserve rejection of an unshared object and absent speakers.
- Nell/dining and Nell/rhyme: close on the actual completed-state fact. Dining
  fixes repeated clue acquisition and a mismatched locket prerequisite.
- Three small renderer repairs preserve required seed concepts across wording
  alternatives: `nose` in Nell/bedtime, `magic` in Cart/rhyme and Bridge/rhyme.
  These are disclosed pre-judge changes, not a prose-quality rewrite. Remaining
  awkward text, name errors, and placeholders are deliberately retained.

Manual review read one fixed selected story plus its story QA from all 21 worlds
before reading ratings. All selected IDs are 234/43/576 by task. Variety is real
in several Library and Garnet paths, but unsupported cross-products remain a
major weakness. Examples: Cart/dining switches candle/lantern mid-scene;
Bridge/bedtime asks for a lantern while holding a bell; Bridge/rhyme requests
a moon-mouse but the sampled helper is a frog. Nell/dining retains `{hero}` and
speaker confusion. Puddles/dining leaks `Inner Monologue:` and nested quotes.
Pirates/rhyme's accepted automatic fallback repair leaves entity reprs in QA.
Garnet/rhyme changes ribbon color at the end; Cart/rhyme doubles `the`.
These defects remain in the scored data, not quietly edited after ratings.

Decision for trial 2: replace candidate 1 with the
[`executable-paths` addendum](../prompts/optimize_20260907_r2_executable_paths.md).
The new prompt targets these causal/implementation mismatches and sampling bugs,
not judge-specific vocabulary, score thresholds, or the three concrete tasks.

## Trial 2 Findings

Quality **6.295/9**, semantic diversity **2.429/9**, assisted composite
**6.454/100**. All 21,000 draws returned: 11,489 exact unique texts and 7,825
quality-qualified uniques from 15/21 worlds. There are 47/210 story ratings
below six. Mean lengths: 180.2 story words; 263.6 story-plus-QA words.
Quoted-word share is 31.2%; qualified compression retention is 3.970%.
The shuffled full corpus compresses 22,177,055 -> 434,292 bytes (1.958%);
deduplicated: 11,728,854 -> 267,720 bytes (2.283%).

Raw probes pass 9/21; automatic full sampling passes 10/21 and own verification
5/21. Automatic composite is **1.374**. Final four local checks pass 21/21 after
16 non-import recoveries. Five already-judged pools were preserved exactly;
only 16 new sets were judged. Seven focused positive/negative tests pass.

Generation: 268,110 input / 97,976 output tokens, **$0.092298**. Judging:
77,425 input / 19,653 output tokens, **$0.214684**. Total **$0.306981**,
all returned Flex, no unpriced responses.

Recovery details, with all intermediate checks and source diffs retained:

- All 21: ancestor imports. Puddles/dining and Pirates/dining: close broken
  import expressions. Puddles/dining also fixes a malformed f-string, accepts
  existing nonempty short QA, and makes two opening variants mention the room.
- Puddles/rhyme: verify the actual two named speakers, not an exact pair of
  speech verbs within one event. Puddles/bedtime: restore raw source over the
  automatic fallback, fix a quote, register actual event targets, and check the
  participating parent or helper rather than demanding an absent helper.
- Pirates/dining: retain `darling` in its third inner-thought variant.
- Garnet/dining: verify names in speech attribution, not inside the quotation.
  Garnet/rhyme: use the defined `rhyme` variable. Garnet/bedtime: close a list.
- Library/dining: remove the ten-turn quota, retain both speakers, and include
  `darling` in the cake path. Library/rhyme and bedtime: fix ASP joins between
  problems and solution requirements instead of comparing mismatched domains.
- Cart/bedtime: record speaker IDs and require both, without an eight-turn quota.
- Bridge/dining: record the listener of the opening question. Bridge/rhyme:
  close the prompt string, require brightness rather than mending for a dim
  banner, and sort compatible pairs for hash-seed replay. Bridge/bedtime: read
  hope from memes, where the simulation writes it.
- Nell/dining: advance by executed event kinds, not consequence-fact names;
  verify the actual chosen outcome (clean/light/welcome). A repair fallback
  accepted during the first recovery check disabled guards; it was rejected,
  the original restored, and narrow fixes retested before judging. Nell/bedtime:
  supply the missing entity kind. Final tests still reject premature endings.

Manual review read the first selected story and story QA for all 21 worlds,
plus nine neighboring samples, before inspecting scores. Recurring defects:
Pirates splices complete clauses into noun slots and leaks fixed names into QA;
Library/rhyme skips the actual problem/action while its QA asserts them;
Library/dining changes pancakes to stew. Cart/dining changes Milo to Nora and
talks about a plate while carrying a crown. Cart/bedtime varies the final object
without varying its affordances. Bridge/rhyme mixes red/white with missing blue;
Bridge/dining lights a lantern only in the ending. Nell/dining switches Jo to
Darling and lists possible ending objects; Nell/bedtime doubles quotation marks.
Garnet retains summary fragments and awkward clause grammar. These defects were
not repaired after rating.

Decision: reject trial 2 in favor of trial 1 so far. Trial 3 reduces the requested
cross-product to three complete causal paths, prioritizes finished scenes, and
places the concise guidance after the long example. This is a bundled prompt
experiment, not evidence that recency alone helps. No fourth paid run is planned.

Trial 3 preflight confirms all 21 task descriptions and all shared inputs except
the prompt builder are identical to baseline. Both emission modes' no-addendum
prompt text are byte-identical to HEAD; the addendum appears once, after seed
fields. The updated regression suite passes 47 tests. Candidate text:
[`complete scenes`](../prompts/optimize_20260907_r3_complete_scenes.md).

## Trial 3 Findings

Quality **7.162/9**, semantic diversity **2.905/9**, assisted composite
**2.748/100**. Twenty of 21 worlds qualify by mean quality, with only 9/210
stories rated below six, but 21,000 raw draws collapse to **3,032 exact unique
texts** and **2,942 qualified uniques**. Mean story length is 153.2 words;
story-plus-QA 230.2 words. Quoted-word share is 26.3%.

The shuffled corpus compresses 18,490,413 -> 260,244 bytes (**1.407%**, 12.39
bytes/draw); exact deduplication gives 2,606,729 -> 73,384 bytes (2.815%).
Quality-qualified unique compression retention is 4.781%. That last ratio is
not contradictory: the distinct texts can be less compressible while the full
draw pool contains many more exact repeats. The score correctly penalizes the
14.0% qualified-unique yield. Skeleton count is 139, a diagnostic heuristic,
not a count of proven distinct plots.

The collapse is visible in code, not only compression: all three Pirates worlds
produce just 12 exact texts each. Each Library and Cart world produces 90,
typically three paths times two distinct names from six choices. Library/rhyme
has opening variants but the ordinary resolver passes the same prose seed to
every draw, fixing the wording. Nell/dining varies its prose seed but offers
only a tiny set of opening/endings. Garnet retains the largest realized pools:
317, 694, and 626 unique texts. Cart's three worlds average 8/9 story quality,
yet only yield 270 unique texts out of 3,000 draws. This is why a ten-story
quality/diversity judgment cannot replace the 1,000-draw duplication audit.

Generation: 263,532 input / 68,655 output tokens, **$0.074133**. Judging:
67,964 input / 19,117 output tokens, **$0.199641**. Total **$0.273774**,
all returned Flex, no unpriced responses. Generation output shrank from roughly
5,051 tokens/world in R1 and 4,666 in R2 to 3,269 in R3.

### Recovery

Generation returned all 21 scripts. Raw probes and automatic full sampling pass
14/21; own verification passes 13/21. There are no accepted automatic repairs.
Eight non-import manual recoveries bring all 21 scripts through sampling, own
verification, standalone CLI, and cross-hash replay. Thirteen already-judged
pools are identical and retain their ratings; only eight new sets are submitted.
Six focused positive/negative recovery tests pass.

- All 21: add robust ancestor imports; four otherwise qualified worlds needed
  this for standalone execution. Existing complete pools remain identical.
- Puddles/bedtime: compare ASP path sets without tuple-order sensitivity;
  accept `share` as well as `shared`/`sharing`, while requiring the actual
  blanket sharing meter. Unshared state still fails.
- Pirates/rhyme: check the chosen branch and resolution instead of demanding
  the registry's exact initial-problem wording in the rendered story.
- Garnet/rhyme: repair three quotation delimiters.
- Library/bedtime and Cart/bedtime: allow more than the minimum QA count;
  do not reject three answers because the check expects exactly two, or two
  because it expects exactly one. Empty QA still fails.
- Cart/dining: write beliefs to the world entities, not their string labels;
  preserve checks for agreement and each path's physical outcome.
- Bridge/dining: include `darling` and `decide` in its opening exchange so every
  branch satisfies the seed, and accept `decide` rather than only `decided`.
- Nell/dining: use `self.p` for the prose seed; include `decide` in both opening
  alternatives. Unfinished world state still fails verification.

Manual review read the first selected story and its QA from all 21 worlds before
viewing scores. Scenes generally show their actions more clearly than in trial 2.
Library/rhyme explains a moon-restoring song; Cart/rhyme nests a leaking cloud;
Nell/dining resolves a specific letter or cake question. Problems remain:
Puddles/rhyme has an unclosed quotation; Puddles/dining changes the clue's speaker
to `the darling` and its QA does not directly explain finding the card.
Pirates/dining prints `Then They`; Pirates/bedtime shares a used handkerchief.
Garnet/dining relocates the same cake between room and pantry; Garnet/bedtime
duplicates its ending clause. Library/dining lists three possible final objects
instead of the selected one. Cart/dining retains `{hero}` in a question.
Bridge/dining has the instruction to place the candle but does not show that
last action; Bridge/bedtime joins clauses without punctuation. Nell/rhyme has
just one QA; Nell/bedtime's hunger question and prop are weakly motivated.
No scored prose was improved after inspecting ratings. Final regression tests:
47 shared factory/evaluation tests and 8/7/6 trial-local recovery tests pass.

## Preserved Artifacts

Each trial's ignored working directory is under `batches/prompt_trials/`; the
21 repaired scripts remain under `worlds/prompt_trials/<trial>/<example>/`.
Archives include frozen requests, original responses, original/materialized
scripts, automatic checks, manual snapshots/diffs, all repeated checks, selected
stories, raw judge responses, exact deduplication and pooled compression data.

- [Trial 1 archive](../batch_archives/prompt_trial_optimize_r1_causal_paths_20260907_20260907T091303Z.tar.gz):
  SHA-256 `69683a9efb7c2e8886da1dd1b783149a10893e1131018a4d59222ab681cb1384`;
  33.08 MiB, 648 files, 83,147 JSONL records, 21 final source scripts.
- [Trial 2 archive](../batch_archives/prompt_trial_optimize_r2_executable_paths_20260907_20260907T092918Z.tar.gz):
  SHA-256 `971c9363d77f3fa056361c4ecd62894ec899472f8a2ed483b7955eae31103ee2`;
  30.60 MiB, 654 files, 89,147 JSONL records, 21 final source scripts.
- [Trial 3 archive](../batch_archives/prompt_trial_optimize_r3_complete_scenes_20260907_20260907T094149Z.tar.gz):
  SHA-256 `9a59b4ff59a2e576f527278f2df6ca73afb83852fbedba9d978d3f3a2f82986a`;
  17.57 MiB, 492 files, 55,147 JSONL records, 21 final source scripts.

All three archives were checked against their SHA-256 sidecars and every file on
disk. JSON/JSONL parses, member paths are safe regular files, and an exact-byte
credential scan is clean. Local quality judges only story text; QA quality is
covered here by manual reading, not by the Terra numerical score.

Archive copies of this report are point-in-time snapshots. The tracked document
here is the complete evolving comparison. API cost excludes local and agent
time; manual recovery is significant and must not be treated as free at scale.
