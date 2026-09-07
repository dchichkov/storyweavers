# Dialogue V2: First Generated Baseline

**Later prompt change:** after this run, the user requested dialogue as a general
requirement. Prompt protocol `custom_tool_python_v11` now requires a brief
consequential spoken exchange in every sample, through `STORY.md`, independently
of seed features. This report and its archive measure the earlier v10 prompt;
no new API calls or retroactive score changes were made for v11.

Completed 2026-09-07 after explicit approval for Luna generation, Terra judging,
and publishing the code, reports, and retained batch archives to GitHub.
These are **21 new generated worlds**, not ratings of the seven reference scripts.

## Setup

- Reference set: `dialogue_v2`; Puddles, Pirates, Garnet, Library, Cart, Bridge,
  Nell v2. One example per request, three matched tasks per example.
- Latest canonical Puddles was not edited. Its SHA-256 remains
  `c64ae1bd909e6c8414ae399d58c7f7d932325aeeaf09331297504a86f0cf3a58`.
- Generation: `gpt-5.6-luna`, reasoning `none`, Flex, concurrency 5,
  32,000 output-token cap, 900-second API timeout. No prompt addendum.
- Matched task seed: `2026090605`; tasks are dining-room quest/inner monologue
  (`decide`, `darling`), gingham/magic nursery rhyme, and nose/sharing/
  foreshadowing bedtime story. Same tasks in every arm.
- Local sampling: 1,000 requested per world, seeds 777/778/779 by task position;
  own verification, standalone CLI check, and hash-seed replay.
- Judge: `gpt-5.6-terra`, reasoning `none`, Flex, ten random sample positions
  together per world. Original calibration retained. Protocol
  `story_set_quality_v1`; geometric score `quality_diversity_geometric_v1`.
- All 21 generation responses and 21 judge responses completed successfully.
  The initial authorization check stopped before API execution; no extra pilot
  or repeat generation was submitted. Frozen prompts/formula were not optimized.

## Automatic Versus Assisted

| Stage | Sampling passes | Own verify passes | Standalone CLI passes | Rated worlds / stories | Mean quality /9 | Dataset score /100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Raw generation | 11/21 | Not a separate full raw pass | Not a separate full raw pass | 0 / 0 | - | - |
| Automatic repair, `eval_001` | 14/21 | 14/21 | 0/21 | 14 / 140 | 6.26 | 5.56 |
| Manual recovery, `manual_001` | 21/21 | 21/21 | 21/21 | 21 / 210 | 6.41 | 6.26 |

The three accepted automatic repairs recovered the Pirates, Garnet, and Bridge
gingham tasks. Seven worlds still needed narrow manual patches. All 21 also
needed a helper-import path fix for nested materialization. The automatic
sampler injected `PYTHONPATH`, hiding that standalone failure. The existing
score gate uses runtime/verify, not standalone execution: **5.56 is the saved
automatic score, not evidence of 14 independently runnable scripts**.

All original responses, raw sources, failed repair attempts, and `eval_001`
remain intact. `manual_001/before/` captures the post-automatic sources; patches
and both local check attempts are retained. The final check sampled and replayed
every world successfully. The 14 previously judged full sample pools, including
QA and parameters, were exactly unchanged after import-only fixes. Their ratings
were reused; only the seven recovered worlds incurred another 70-story judge
pass. There were **210 distinct submitted sample positions, not 350**.

This is a manually assisted baseline, not a claim of 100% automatic repair or
100% QA correctness. The source-level repair rules and canonical examples were
not changed during the measured run.

## Results By Example

Each row is three generated worlds and 30 judged stories. Quality and semantic
diversity are means on 0-9 scales. The qualified-world threshold is mean story
quality >= 6; QA correctness is not part of this judge.

| Example | Raw / auto runnable | Quality /9 | Semantic diversity /9 | Qualified worlds | Exact unique texts | Geometric /100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Puddles | 1 / 1 | 5.80 | 0.00 | 1/3 | 1,491 | 0.47 |
| Pirates | 2 / 3 | 5.67 | 1.00 | 1/3 | 1,633 | 5.73 |
| Garnet | 2 / 3 | 6.43 | 2.67 | 2/3 | 3,000 | 10.74 |
| Library | 2 / 2 | 6.07 | 1.00 | 2/3 | 985 | 5.24 |
| Cart | 1 / 1 | 6.80 | 1.00 | 2/3 | 1,351 | 4.05 |
| Bridge | 1 / 2 | 6.37 | 1.33 | 2/3 | 1,202 | 2.63 |
| Nell v2 | 2 / 2 | **7.77** | 1.33 | 3/3 | 1,975 | **12.83** |
| All | 11 / 14 | **6.41** | **1.19** | **13/21** | **11,637** | **6.26** |

The whole-trial score recompresses its own pooled corpus; it is not the mean
of arm scores. Its qualified exact-unique yield is 7,135/21,000 = **33.98%**;
quality weighted over those unique texts is 7.38/9; cross-story compression
retention is **4.14%**. Eight worlds fail the mean-quality gate. Of the 210
individual judged stories, 66 score below six. Passing the world mean does not
certify every story, and none of these counts certifies training QA.

Garnet's two stronger tasks have four and five judged causal groups. By contrast,
Nell's dining task produces only eight exact strings in 1,000 draws. Nell's
bedtime task produces 1,000 exact strings but the judge identifies one causal
plot. The composite therefore still rewards some lexical variation more than
semantic diversity; do not optimize it alone.

### Length And Dialogue

| Example | Returned / requested | Mean story words | Mean story + story-QA words | Quoted words |
| --- | ---: | ---: | ---: | ---: |
| Puddles | 2,915 / 3,000 | 186.2 | 302.7 | 14.0% |
| Pirates | 3,000 / 3,000 | 179.7 | 293.1 | 13.8% |
| Garnet | 3,000 / 3,000 | 197.6 | 291.8 | 17.5% |
| Library | 3,000 / 3,000 | 159.6 | 296.0 | 14.1% |
| Cart | 3,000 / 3,000 | 240.0 | 349.0 | 34.5% |
| Bridge | 3,000 / 3,000 | 230.2 | 364.3 | 15.9% |
| Nell v2 | 3,000 / 3,000 | 143.9 | 233.3 | 6.3% |
| All | **20,915 / 21,000** | **191.1** | **304.3** | **17.7%** |

The quoted-word heuristic recognizes straight/curly double quotes and standalone
single-quoted spans. It includes inner thoughts, chants, and written notes; it
is not a dialogue-quality score. World-facts QA is excluded from the length
column. These are sample-weighted means, including duplicates.

Cart transfers sustained conversational exchanges, especially in the bedtime
task. Nell's best-quality ranking does **not** mean it transfers Nell's dialogue:
the reviewed bedtime story contains none, and the dining story mostly narrates
an inner thought. Dialogue-heavy reference code alone did not reliably induce
dialogue-heavy generated worlds in this small trial.

Puddles/nose deduplicates internally while attempting 1,000 draws, returning
915 without replenishing skipped duplicates. We retained that behavior rather
than padding the pool. The judge samples its returned pool, so this arm's
selection is not an unbiased sample of its pre-dedup draws. All other worlds
returned 1,000; the score denominator remains 21,000.

## Pooled Compression

One story-only archive contains the entire returned corpus, not 21 separate
compression runs. UTF-8 JSONL of story strings, XZ, LZMA2 preset 6, explicit
64 MiB dictionary, deterministic shuffle seed 0. No prompts, filenames, params,
QA, or traces are included in these bytes.

| Corpus | Stories | Input bytes | XZ bytes | XZ/input |
| --- | ---: | ---: | ---: | ---: |
| All, shuffled | 20,915 | 23,066,069 | 448,204 | **1.94%** |
| All, grouped | 20,915 | 23,066,069 | 355,416 | 1.54% |
| Exact deduplicated, shuffled | 11,637 | 12,921,510 | 289,852 | **2.24%** |
| Unique slot-normalized skeletons | 1,867 | 1,935,474 | 44,388 | 2.29% |
| Word-order-destroyed control | 20,915 | 22,671,323 | 5,874,024 | 25.91% |

The full shuffled pool is **22.00 MiB -> 437.7 KiB**, or **21.43 compressed
bytes/story**. Exact dedup removes 9,278 returned repeats, but the remaining
texts are still highly predictable. Skeletons are not independent plot counts.
Destroyed word order compresses far worse, confirming why compression alone
would reward bad text. A matched natural-story control is still needed before
setting an absolute acceptance threshold.

| Max samples/world | Returned stories | Shuffled compressed bytes/story |
| --- | ---: | ---: |
| 10 | 210 | 98.21 |
| 50 | 1,050 | 41.21 |
| 100 | 2,100 | 31.91 |
| 250 | 5,250 | 25.29 |
| 500 | 10,500 | 22.81 |
| 1,000 | 20,915 | 21.43 |

The ten-story growth-curve subset is the first ten local samples per world,
not the separate random sample submitted to the judge.

## Manual Reading

Before examining ratings, read the first selected judge story from each of
the 21 worlds, together with its story QA and world QA. This is **21 manually
reviewed stories**, not all 210 judged stories. Exact records are retained in
`manual_001/manual_review_samples.json`. IDs are `s000234` for dining,
`s000043` for gingham, and `s000576` for bedtime.

| Example/task | Observations from that story and QA |
| --- | --- |
| Puddles/dining | Clear search and return, but repeated endearments and awkward location wording; moral explained at the end. |
| Puddles/gingham | Clean magical crossing, physical payoff, a little dialogue; only one plot and 72 exact texts. |
| Puddles/bedtime | Lowercased names; sharing a used tissue with a nose/adult is forced; first QA does not actually identify the requested place/person. |
| Pirates/dining | Helper becomes the unexplained lowercased `sweet captain`; the text calls itself suspenseful. |
| Pirates/gingham | Overloaded noun phrase and little conflict; one QA leaks an `Entity(...)` object representation. |
| Pirates/bedtime | Readable conversation and lost-bird rescue, but the shared wish and scarf do little causal work. |
| Garnet/dining | `discovered theo found` in prose and repeated finding in QA; claimed decision not to touch contradicts earlier handling. |
| Garnet/gingham | Real pocket problem and corrective action; duplicated solution beat, awkward `by turned` QA, unrelated moon claim in world QA. |
| Garnet/bedtime | Strong early leak clue, reporting, physical repair, and closing bowl image; some QA phrasing is clumsy. |
| Library/dining | A gesture answers a question and changes placement; small but coherent problem and resolution. |
| Library/gingham | `the the`, lowercase starts, journey apparently returns to its starting gate, confused day/dark progression. |
| Library/bedtime | Setup presents a smell but payoff and QA assert remembered tapping; the clue is not the same fact. |
| Cart/dining | Sustained speech and internal debate, but repetitive tags and no modeled distinction explaining which decoration suits the guest. |
| Cart/gingham | Literal `{helper}`, doubled articles, yellow cloth described as red at the end; broken language remains after runtime repair. |
| Cart/bedtime | Real back-and-forth coordination; treat changes from saved-for-later to gone without an eating beat. |
| Bridge/dining | Doubled articles; recipe book is found by the child, then arrives with Grandma without a transfer. |
| Bridge/gingham | Dialogue supports inspecting, tying, testing, and crossing; good concrete sequencing. |
| Bridge/bedtime | `blue` is used as an object with no noun; scent-to-moth moral is weakly motivated. |
| Nell/dining | Short complete rescue, but the initially unlit lantern produces light without an ignition beat; little spoken exchange. |
| Nell/gingham | Concise rhyme, mending, and usable-basket payoff; only one plot in the judged set. |
| Nell/bedtime | Warm ending but no dialogue; nose repetition is awkward and the cold-room window is opened without an evident need. |

Terra correctly flags the broken discovery clause, doubled articles, literal
placeholder, ambiguous `blue`, and forced tissue sharing. It agrees that most
sets collapse to one plot. It misses the Library/bedtime clue mismatch in
`s000576`: its note says the remembered tapping follows naturally, although the
actual setup is a carrot smell. It notices similar drift in other set members.
The Cart snack disappearance and unlit Nell lantern also survive favorable
ratings. Thus the score is useful for triage, not a complete continuity audit.

The judge receives stories, **not QA or executable world traces**. It cannot
detect the leaked `Entity(...)` answer, unrelated world QA, or evidence/answer
contradictions. Generated self-checks also missed these. Do not export this
entire pool as approved training data on the strength of runtime and story scores.

## Manual Repairs

| Scope | Narrow recovery |
| --- | --- |
| All 21 | Locate the ancestor containing `results.py` and `asp.py`; nested standalone execution no longer depends on injected `PYTHONPATH`. |
| Puddles/dining | Preserve required literal `darling` across sampled endearments; expose three existing ASP atoms expected by verification. |
| Puddles/gingham | Repair malformed quote boundaries; retain required seed word `magic`. |
| Library/dining | Record existing creak/shadow sentences as suspense events instead of incorrectly tagging them only as inner monologue. |
| Cart/dining | Supply missing `World.sample()` using the existing event text and event QA. No invented world-fact answers. |
| Cart/gingham | Correct problem-to-spell dictionary lookups; keep rejection of incompatible combinations. |
| Bridge/dining | Accept supported two-word names; validate the correct ending for share versus save paths. |
| Nell/dining | Retrieve the suspense event by kind instead of indexing an unrelated history entry. |

No prose cleanup or extra quality rewrite followed judging. Seven focused
repair regression tests pass, including invalid combos and event-index shifts.
The 92-test canonical/factory/prompt-trial/dialogue/scoring/judge suite also
passes. Canonical Puddles and original Nell are unchanged.

## Spend

Estimates from saved returned usage and the repository's recorded Flex rates,
not invoice reconciliation. All returned tiers are Flex. No unknown/unpriced
responses in these 42 calls.

| Work | Calls | Input tokens | Output tokens | Estimated USD |
| --- | ---: | ---: | ---: | ---: |
| Luna generation | 21 | 257,337 | 82,306 | $0.081549 |
| Terra automatic-pass judging | 14 | 50,840 | 12,741 | $0.139986 |
| Terra recovered-world judging | 7 | 26,965 | 6,216 | $0.070997 |
| Total | **42** | **335,142** | **101,263** | **$0.292532** |

Judging totals **$0.210983**, about 72% of this run's estimated API cost.
Human/agent repair and local compute are not priced here. Saved response usage
does not establish whether any unobserved provider/transport retry was billed.

## Next Experiment

Keep these prompts, scripts, and scores fixed as the baseline. Before spending
on another prompt comparison, make nested CLI execution and full sample counts
explicit gates, and pin placeholder/object-repr/continuity/QA failures above.
Then compare a narrow prompt change on the same three tasks. Ask the model to
demonstrate dialogue changing knowledge or action and distinct causal outcomes,
not merely to add quoted sentences or synonyms. Report automatic repair yield,
manual assistance, quality, semantic diversity, and compression separately.

Nell is the strongest quality arm here; Garnet is the strongest semantic-
diversity arm. Neither result establishes a winner beyond three matched tasks.
The older 7.89/9 reference-world calibration used different source worlds and
is not a like-for-like baseline for these newly generated scripts.

## Reproduction And Retention

Trial: `storyworlds/batches/prompt_trials/dialogue_v2_baseline_20260907/`.
Materialized scripts: `storyworlds/worlds/prompt_trials/dialogue_v2_baseline_20260907/`.
The trial archive retains frozen inputs and sources, request/response ledgers,
raw generations, automatic before/after snapshots, failed manual check attempt,
final checks, 20,915 final samples with QA, both sets of judge requests/responses,
reused-rating provenance, patches, repair tests, manual-review records, and all
pooled XZ controls. There are no per-story Markdown files.

```bash
# A new matched trial, not a resubmission of the completed baseline.
./.venv/bin/python storyworlds/prompt_trials.py prepare dialogue_next --seed 2026090605
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/prompt_trials.py run dialogue_next

# Read the preserved automatic baseline; no API call.
./.venv/bin/python storyworlds/prompt_trials.py report dialogue_v2_baseline_20260907

# Local-only checks and analysis after restoring the retained trial archive.
./.venv/bin/python storyworlds/batches/prompt_trials/dialogue_v2_baseline_20260907/manual_001/test_repairs.py
./.venv/bin/python storyworlds/batches/prompt_trials/dialogue_v2_baseline_20260907/manual_001/analyze.py

# Archive a completed trial and its materialized worlds.
./.venv/bin/python storyworlds/prompt_trials.py archive dialogue_v2_baseline_20260907
```

`prompt_trials.py report` intentionally still shows `eval_001`; this document
adds the separately labeled manual recovery. Do not rerun `evaluate` merely to
read results: it starts a new paid judge pass. The archived `recover.py judge`
was used once for the seven missing ratings, not as a general resume command.

Retained snapshot: [trial archive](../batch_archives/prompt_trial_dialogue_v2_baseline_20260907_20260907T075741Z.tar.gz)
and [SHA-256](../batch_archives/prompt_trial_dialogue_v2_baseline_20260907_20260907T075741Z.tar.gz.sha256).
It includes the report as written before packaging; the post-baseline v11 note
above is a later Git-tracked addition, not a modification of that archive.
