# Production Training Data: New-Criteria Audit

## Status

**Complete: 97/97 eligible worlds and all 951 submitted stories were judged.**
The user explicitly authorized the transfer after the initial privacy block.
All responses returned `gpt-5.6-terra` and `flex`; none required retry or repair.
The original local pools, selected stories, and request bodies were revalidated
unchanged, and every plot-group partition passed the strict response validator.

Unchanged `story_set_quality_v1`
protocol, `gpt-5.6-terra`, Flex, reasoning none, concurrency 20, 900-second timeout,
no automatic retry or standard-tier fallback. Returned usage: 332,410 input
tokens and 85,484 output tokens; estimated cost **$0.92834375**, not invoice reconciliation.
Three selected worlds have only one retained story and cannot enter the current
set judge. Three more have 2, 4, and 5 stories; 94 have the full ten-story sample.
Ineligible worlds have no invented quality or diversity ratings.

## Quality And Diversity Results

The old sample scores **4.975/9 quality and 1.031/9 semantic diversity**,
averaging worlds equally. Story-weighted quality is 4.967/9.

| Dataset | Rated worlds | Rated stories | Quality /9 | Diversity /9 | Worlds Q >=6 | Worlds Q >=6 and D >=3 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Old production training sample | 97 | 951 | 4.975 | 1.031 | 27/97 (27.8%) | 2/97 (2.1%) |
| Recent broad Luna 1,000-world run | 631 | 6,302 | 5.903 | 2.222 | 339/631 (53.7%) | 172/631 (27.3%) |
| Recent top-20-reference Luna 100-world run | 64 | 633 | 6.459 | 2.984 | 48/64 (75.0%) | 41/64 (64.1%) |
| Recent top-20-reference Mini 100-world run | 72 | 715 | 5.817 | 2.389 | 35/72 (48.6%) | 20/72 (27.8%) |

All quality/diversity means in this table are equal-world, using the same judge
and rubric. Recent results are reused from their preserved response files;
no new generation or rejudging of recent runs was performed. Rates are
**conditional on valid judgments**, not all generation attempts and not the
stricter runtime/replay gate. For example, 41 recent Luna worlds meet Q/D here,
but only 33 of the 100 attempts also passed the strict local runtime gate.
They are not the same cohort as the 50-world compression panels below.

Old sample diagnostics:

- **634/951 stories (66.7%) score below 6.**
- **65/97 worlds (67.0%) collapse into a single judged plot group.**
- Overall diversity counts: 29 worlds score 0, 40 score 1, 24 score 2, and 4 score 3.
  None scores 4 or higher; only two of the four D=3 worlds also meet Q >=6.
- Mean story dimensions: coherence 5.390, style 4.573, grammar 5.351,
  storytelling 5.119, overall 4.967 (story-weighted).
- Mean diversity dimensions: premise 1.289, causal path 1.134, ending 0.959,
  language 1.371, overall 1.031 (world-weighted).

The two old Q >=6 / D >=3 contributors are
`tutu_conflict_flashback_pirate_tale` (Q 7.6, D 3) and
`mole_increment_conflict_problem_solving_rhyme_tall` (Q 6.9, D 3), both from the
older repaired full-GPT-5.4 batch. The first changes the disagreement, compromise,
and whether play resumes; the second branches among three distinct emergencies,
although the higher-level structure still repeats. Their full paths are retained
in `qualified_retained_worlds.json`; no current-script runtime claim is made.

The corpus is not uniformly weak: the nine sampled worlds from the full-GPT-5.4
batch average Q 6.967, D 1.778, while the 67 judged contributors from the old
5,000-world Mini batch average Q 4.752, D 0.985. These small, non-matched subsets
are descriptive, not a causal model comparison.

**Takeaway:** the curated recent Luna data looks like a meaningful quality and
diversity improvement over this old training sample, not just more tokens.
That supports selective addition or replacement, but not indiscriminate bulk
merging or an assumption that 100 variants are 100 independent plots. These
ratings do not prove a downstream training gain. Different task distributions,
old-pool deduplication, and the selection of the recent top-20 references remain
important confounds. Historical runnable/QA pass rates are not narrative-quality
or diversity pass rates under this newer protocol.

## Source And Selection

The source is the actual finalized production **train** file, streamed from
`training/storyworld_chat/data_archives/storyworld_chat_production_20260904_corpus.tar.gz`.
Its SHA-256 matches the recorded training checksum:
`3bf0324ba049e1db5a81e7238b70ee8b44028d164c82729f486e8a3e3ee72b76`.
No current generator scripts were executed, repaired, or substituted for old text.

| Measure | Count |
| --- | ---: |
| Final training rows scanned | 596,966 |
| World paths actually present in the final file | 6,505 |
| Exact-unique base-story/world pairs in the final file | 531,026 |
| Deterministically selected worlds | 100 |
| Distinct retained base stories from those worlds | 8,246 |
| Worlds eligible for ten-or-fewer-story judging | 97 |
| Prepared judge stories | 951 |

The older export report's 6,516 successful worlds and 531,850 samples are not
the measured final-file counts above. The finalizer excluded 724 conversations;
the export manifest and final retained-text census must not be conflated.

World selection uses the lowest SHA-256 hashes of `seed + world path`, seed
`20260908`: equal selection probability per world, independent of packed-row
counts. It is not proportional to training tokens. Only the first assistant
story in a row whose first packed task is `story` is extracted; QA answers are
not mistaken for additional stories. Exact base-story repeats caused by packing
are collapsed within each world. Original messages, params, and source line
numbers are retained in the local pools for inspection.

The production export already deduplicated stories. Therefore its judge sample
is drawn from retained unique stories, unlike recent generator evaluations that
sampled draw positions and retained duplicates. This favors the old data on
diversity; the story rubric is unchanged, but the pool construction differs.

## Local Compression

Only story strings are compressed, as UTF-8 JSONL. No prompts, QA, params, or
filenames. XZ/LZMA2 preset 6, 64 MiB dictionary, deterministic shuffle seed 0.

| Retained stories per world, up to | Actual stories | Text bytes | XZ bytes | XZ/text | XZ bytes/story |
| --- | ---: | ---: | ---: | ---: | ---: |
| 10 | 954 | 970,236 | 78,408 | 8.08% | 82.19 |
| 50 | 4,445 | 4,545,909 | 172,836 | 3.80% | 38.88 |
| 100 | 8,246 | 8,509,472 | 264,516 | 3.11% | 32.08 |

All 8,246 story strings are exact-unique across the selected corpus. Exact dedup
therefore does not remove this compressibility. Pooled raw-LZMA2 size divided by
the sum of individually compressed story sizes is **5.45%**. This is compression
retention, not an estimate that only 5.45% of tokens are useful for learning.
Median slot-normalized skeleton count is 19 per world; skeletons are not plots.
These are retained samples, **not 1,000 fresh draws per world**.

## Equal-Size Comparison

Each panel contains **50 worlds x 100 exact-unique stories = 5,000 stories**.
Worlds are sampled without looking at quality scores. Old candidates come from
the 100-world training sample; new candidates must pass sample+verify. All must
have at least 100 unique retained stories. New stories are uniformly subsampled
from the exact-unique pool, so duplicates are removed on both sides.

| Panel | Eligible worlds | Mean story words | XZ/text | Pooled compression retention | Median within-world retention |
| --- | ---: | ---: | ---: | ---: | ---: |
| Old production training data | 70 | 187.1 | 2.99% | 5.23% | 4.83% |
| Recent broad Luna 1,000-world run | 634 | 246.9 | 3.19% | 5.81% | 5.55% |
| Recent top-20-reference Luna 100-world run | 64 | 235.0 | 3.44% | 6.17% | 6.18% |
| Recent top-20-reference Mini 100-world run | 69 | 219.7 | 3.94% | 6.97% | 7.24% |

Higher retention means less reuse across stories under this compressor. Recent
Luna is modestly less repetitive than the old corpus in these panels, but all
remain highly compressible. Mini is least compressible here despite lower
quality than Luna in the existing judged runs. Compression alone cannot rank
training quality.

This comparison excludes small pools and conditions on successful export or
sampling. The panels have different tasks, lengths, reference distributions,
and selection history; this is not a controlled generation experiment or a
full-corpus census. It does not establish improvement in a trained model.

## Manual Spot-Check

Read the first two selected judge stories from each of the first eight
judge-eligible worlds in the seeded ordering: 16 stories, no score-based selection.
These observations are qualitative, not substitute Terra ratings.

| World stem | Observations in the two inspected stories |
| --- | --- |
| `kennel_calamine_sausage_bad_ending_fable` | Mostly adjective/location swaps; lowercase sentence starts and missing articles; sausage disappears through an abstract "wind of the bad choice" rather than a concrete cause. |
| `ginger_revolt_misunderstanding_sharing_tall_tale` | Appealing voice, but subjectless fragments such as "handed out slices"; fixed dialogue refers to a stolen star regardless of the actual misunderstanding. Tea variation still ends "After the first bite." |
| `peck_lullaby_repetition_humor_myth` | Coherent broad arc and dialogue; the same problem, song, and resolution recur after character/object swaps. |
| `finger_scissor_bravery_twist_bedtime_story` | Safety instructions are spliced directly into a narrative sentence without grammatical integration. Same successful craft arc. |
| `scratch_dim_mallet_blade_magic_problem_solving` | Stronger atmosphere and ending image; real local tool-sequencing variation, but the larger arc remains shared and dialogue has an unclosed quotation. |
| `priest_sharing_surprise_fairy_tale` | Some meaningful gift/need/reward variation and attractive imagery, undermined by literal `hero` placeholders and name/pronoun inconsistency. |
| `grant_hideous_wont_post_office_twist_happy` | Nearly identical plots; clue dismissed and missing letter found without consequential investigation. |
| `military_sharing_dialogue_animal_story` | Dialogue exists, but slot compatibility fails: "some crackers" are treated as a single reusable tool, and location/task details do not consistently carry into the ending. |

The sample supports the concern that runnable scripts and exact deduplication
did not guarantee grammatical, causally complete, or meaningfully varied prose.
It also contains some good storytelling; this is not evidence that every old
world should be discarded. QA grounding has not been scored by this audit.

The judge agrees with the central manual findings: `military_sharing` scores
Q 3.6 / D 0 and explicitly catches the reusable-crackers and location problems;
`peck_lullaby` scores Q 7 / D 0, distinguishing readable prose from plot diversity.
It is not a flawless copy editor: `scratch_dim` receives grammar 9 despite an
unclosed quotation, and `priest_sharing` receives Q 7.8 while treating the literal
`hero` placeholder as a small defect. Preserve manual review and deterministic
text checks alongside the judge, especially for training-data acceptance.

## Reproduce

Prepare locally; use a new output directory for every new selection:

```bash
./.venv/bin/python training/storyworld_chat/evaluate_export.py \
  --archive training/storyworld_chat/data_archives/storyworld_chat_production_20260904_corpus.tar.gz \
  --expected-sha256 3bf0324ba049e1db5a81e7238b70ee8b44028d164c82729f486e8a3e3ee72b76 \
  --worlds 100 --seed 20260908 \
  --out storyworlds/batches/production_train_newcriteria_20260908
```

Paid command used after explicit authorization, with `OPENAI_API_KEY` configured
locally (already complete; do not resubmit this run):

```bash
caffeinate -is ./.venv/bin/python training/storyworld_chat/evaluate_export.py \
  --out storyworlds/batches/production_train_newcriteria_20260908 \
  --judge --concurrency 20
```

The judge refuses an existing `judge/` directory. Do not overwrite, silently
retry failed paid calls, or impute invalid plot-group partitions.

Equal-size local comparison command, also refusing an existing comparison output:

```bash
./.venv/bin/python training/storyworld_chat/evaluate_export.py \
  --out storyworlds/batches/production_train_newcriteria_20260908 \
  --compare-trial storyworlds/batches/prompt_trials/repaired100_canonical_luna_20260907 \
  --compare-trial storyworlds/batches/prompt_trials/top20_luna100_20260907 \
  --compare-trial storyworlds/batches/prompt_trials/top20_mini100_20260907
```

Retained artifacts under `storyworlds/batches/production_train_newcriteria_20260908/`:
`source.json`, `catalog.json`, `pools/*.jsonl`, `judge_inputs.json`, source snapshots,
`compression/`, and `retained_comparison/` with compressed story archives,
per-world metrics, and selected-story hashes. `judge/` preserves all frozen
requests, attempts, responses, ratings, settings, and judge source snapshots.
`summary.json`, `comparison_quality.json`, `qualified_retained_worlds.json`,
`judge_verification.json`, and `run_status.json` preserve the final results.
The pre-authorization state remains in `run_status.prejudge.json`.

The completed audit is also bundled in
`storyworlds/batch_archives/production_train_newcriteria_20260908.tar.gz`, with
SHA-256 and per-member verification sidecars, using the existing LFS path rule.
The archive and report have not been committed or pushed by this evaluation.

Do not calculate the existing full geometric pipeline score from this export:
it cannot establish the current runtime, verify, standalone, replay, and
1,000-draw yield gates. Report component metrics and missing evidence explicitly.
