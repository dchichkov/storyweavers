# Storyworld Quality Iteration Pipeline

This loop is for improving the storyworld prompt and the cheap scripted repair
layer without using an LLM repair pass. Generation now defaults to
`gpt-5.6-luna` with reasoning effort `none`. Canonical prompt trials now use
`gpt-5.6-terra` to judge ten stories together per world. Both use Flex.
The older direct-service pipeline and single-story Mini judge below are
retained for reproducibility; their historical ratings are never overwritten.

The loop has two distinct phases:

1. Make the generated scripts runnable and sampleable.
2. Judge story quality only after the runnable set is clean.

Do not skip the first phase. Quality scores are misleading when a large fraction
of scripts fail before producing stories.

## Goal

Raise downstream storyworld quality while keeping the generated scripts runnable,
auditable, and close to the original prompt. The main scorecard is:

- `openai_story_quality.py`: story quality averages and low-scoring examples.
- `openai_world_set_quality.py`: ten-story Terra quality plus semantic diversity
  for canonical trials, keeping individual ratings and plot-group evidence.
- `qa_static_check.py`: runnable count, static QA duplication, and script errors.
- Manual reading: generated stories, prompts, scripts, and report excerpts.

Prefer changes in this order:

1. Small prompt changes that improve many worlds.
2. Narrow scripted repairs for repeated generated-code mistakes.
3. No LLM repair pass unless explicitly requested; it is too expensive for the
   default loop and can hide prompt/codegen defects.

## Default Run

The direct-service pipeline defaults to 100 storyworlds. For controlled prompt
optimization, prefer the 21-world canonical trial below. Keep seeds matched
within a comparison, then validate the selected prompt on fresh seeds:

```bash
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_service_world_pipeline.py \
  --seed <new-seed> \
  --model gpt-5.6-luna \
  --reasoning-effort none \
  --service-tier flex \
  --quality-model gpt-5.4-mini \
  --max-output-tokens 32000 \
  --repair-failures
```

Omitting `-n` intentionally means `-n 100`. Reuse the same `--seed` for an A/B
check where the prompt is the only thing you want to vary. Use fresh seeds for
the subsequent validation run.

For a five-world Puddles-only pilot, add `-n 5 --concurrency 5
--example-worlds puddles`. Without `--example-worlds`, both Puddles and Pirates
are included. No addendum is used unless `--prompt-addendum` is supplied.

To compare repaired examples, use `--example-file <repository-script.py>`
instead of `--example-worlds`. One flag supplies one example; repeated flags
include all selected examples in every request. For separate five-world arms,
run `-n 5 --concurrency 5` once per example, with the same `--seed`, model,
reasoning effort, repair settings, and Mini judge. Give each arm its own
`--output-dir` and `--target-dir`, and keep a snapshot of each example source.
Quality outputs default to the manifest's directory, so same-seed parallel
arms do not overwrite each other. `--quality-out` can explicitly override this.
The manifest records `example_files`; prompt snapshots show the exact embedded
source. Reusing `--from-manifest` restores the selected example paths.

Completed example comparison: [five repaired-example Luna batches](batches/luna_repaired_examples_20260907.report.md)
(25 worlds, same seed as the Puddles pilot, separate preserved batches).
Also completed: [Qwen3.8 27B / OpenRouter Puddles pilot](batches/qwen38_puddles_20260907.report.md)
(five matched-seed worlds, reasoning disabled, same direct OpenAI Mini judge).

The command writes:

- generated scripts under `storyworlds/worlds/`
- a manifest and raw response JSONL under `storyworlds/batches/`
- prompt snapshots and sampled stories
- `*.quality.jsonl` and `*.quality.summary.json`
- a Markdown report with links to prompts, scripts, stories, repair logs, quality
  results, and static QA output

Keep these artifacts. Do not delete raw responses, manifests, prompt snapshots,
or earlier reports when iterating. They are the audit trail that lets us compare
prompt, repair, and quality changes without regenerating the same batch.

## Explicit Generation Caching

The direct-service factory and `prompt_trials.py prepare` accept
`--prompt-cache-mode explicit` for GPT-5.6+ requests. This separates the fixed
contract/helpers/example from the variable seed fields, marks the fixed block
with `prompt_cache_breakpoint`, and sends
`prompt_cache_options={"mode": "explicit", "ttl": "30m"}` instead of legacy
`prompt_cache_retention`. Concatenating the two blocks reproduces the original
prompt exactly; addenda still follow the task. Existing commands default to
`legacy`, and frozen historical requests are never rewritten.

Use `--cache-warmup` when preparing a prompt trial to complete one real request
per cache key before releasing that key's remaining requests. Warm-ups count
toward the requested generation total. Independent keys can warm concurrently,
and all requests still share the trial's concurrency limit. Resume retains the
existing attempt/response ledgers and does not silently retry unknown outcomes.
The factory alone does not implement this scheduling option.

```bash
./.venv/bin/python storyworlds/prompt_trials.py prepare <new-name> \
  --seed 2026091800 \
  --example-manifest storyworlds/reference_sets/luna_top20_20260907.json \
  --per-example 5 --model gpt-5.6-luna --reasoning-effort none \
  --concurrency 50 --local-samples 1000 \
  --prompt-cache-mode explicit --cache-warmup
```

GPT-5.6's default implicit breakpoint includes the changing last message. A
shared prefix alone is insufficient: explicitly mark its end so later requests
can reuse it. See the [official caching guide](https://developers.openai.com/api/docs/guides/prompt-caching#gotchas).
The installed Python SDK can pass the new top-level option through `extra_body`;
the saved requests remain the exact wire JSON, and a mock-transport test checks
both that option and the nested breakpoint survive serialization.

Measure `usage.input_tokens_details.cached_tokens` and `cache_write_tokens`
separately. Writes are not cache hits and have a different price. Report input
cost separately from output cost, and compare input at matched token counts.
With five requests per reference and one cold write each, the within-reference
cache-read ceiling is about 80%, not the near-100% ceiling of a much larger run.
Quality can be omitted: run generation, local audit/repair, and import repairs
without invoking `judge`. Local sample/verification success is not a quality
rating. Preserve raw and repaired source, compressed samples, usage, and archives.

Caching experiment: [100 matched Luna worlds, repairs without judging](batches/top20_luna100_cached_20260907.notes.md).

## Large Reference-Seeded Runs

`large_world_batch.py` scales the canonical protocol without retaining a million
full StorySample objects in memory or writing uncompressed per-story Markdown.
It selects the first 100 **verified entries in repair-ledger order** from
`WORST_CONTRIBUTORS_REPAIR.md`, resolves their current tracked source files
(excluding historical `tmp` copies), and adds the current canonical set.
Garnet overlaps both sets, giving 106 distinct references. This is a reproducible
subset of the 117 verified ledger entries, not a claim that the campaign had
exactly 100 repairs.

Each reference must pass `--verify`, a 100-sample draw, and deterministic replay
before any paid call. The preparation step freezes reference sources, their
hashes, the preflight evidence, and every request body. Exactly 1,000 fresh tasks
are balanced across references, 9 or 10 each. Unlike a matched prompt trial,
these tasks use disjoint seeds, and each request contains only one example.

```bash
./.venv/bin/python storyworlds/large_world_batch.py prepare repaired100_canonical_luna_20260907 \
  --count 1000 --seed 2026090710 --concurrency 50 --local-workers 4

OPENAI_API_KEY="$(cat .API_KEY)" OPENAI_BASE_URL=https://api.openai.com/v1 \
  ./.venv/bin/python -u storyworlds/large_world_batch.py generate repaired100_canonical_luna_20260907

./.venv/bin/python -u storyworlds/large_world_batch.py audit repaired100_canonical_luna_20260907

./.venv/bin/python -u storyworlds/large_world_batch.py repair-imports repaired100_canonical_luna_20260907

OPENAI_API_KEY="$(cat .API_KEY)" OPENAI_BASE_URL=https://api.openai.com/v1 \
  ./.venv/bin/python -u storyworlds/large_world_batch.py judge repaired100_canonical_luna_20260907

./.venv/bin/python -u storyworlds/large_world_batch.py summarize repaired100_canonical_luna_20260907
./.venv/bin/python storyworlds/large_world_batch.py archive repaired100_canonical_luna_20260907
```

Generation uses Luna, no reasoning, Flex, the current base prompt, and no
addendum unless explicitly supplied at preparation. API concurrency and local
worker count are separate. Generation and judging require authorization to send
the reference code and sampled story text to OpenAI. An interrupted generation
attempt with unknown billing is never automatically resubmitted; the underlying
generation SDK retains its existing bounded transport retries.

On a Mac, wrap long-running commands with `caffeinate -is` to prevent idle/system
sleep while the command runs. Sleeping can interrupt in-flight requests and
delay timeout handling. Preserve any uncertain attempt in the ledger instead
of blindly submitting the same paid request again.

To overlap local work with a running generation process, use `audit-stream`
instead of `audit` in a second process. It consumes only complete, durable
response records after raw-source preservation; generation and QC use separate
phase locks. Partial JSONL tails are deferred until the writer finishes them.
No additional generation requests or judge calls are made by streaming audit.

`repair-imports` addresses only missing `results`, `asp`, or `storyworlds`
module errors in standalone execution. It adds ancestor-based helper discovery,
preserves the pre-import audit and source, and reruns sampling/verification/CLI/
replay with general repair rules disabled. An existing sample pool must remain
exactly unchanged before the path repair is accepted. Newly runnable worlds
retain their original failed audit alongside the new pool. Run this before
judging; it will refuse to modify an already-judged pass.

The local audit reuses `repair_batch_output.py`, preserving raw, before, and
after sources. It requests 1,000 samples per generated world, runs verification,
checks standalone CLI execution and hash-seed replay, and measures exact/textual
skeleton uniqueness and QA duplication. Samples are retained as one compressed
`samples.jsonl.gz` per world, not 1,000 files. Successful subprocess stdout is
stored once as samples; checks retain its byte count/hash instead of another
large embedded copy. Completed local audits are resumed without rerunning them.

Terra/Flex judges ten randomly selected samples from each eligible world,
without deduplicating away repetition. The existing geometric formula and
runtime/verify gates remain; scoring also enforces the judge's minimum of two
returned stories. Smaller sets are counted as `insufficient_sample_set_worlds`,
not assigned fabricated ratings or left pending indefinitely. Full sample count, standalone
CLI, and replay are also reported as a stricter tally; neither a successful
repair nor a high story score establishes full world-state/QA correctness.
In particular, review any repair that introduces fallbacks or weakens guards
before admitting its source to a curated training dataset.

Inspect the generated sampler itself when counts are short or sampling times
out. Some generated CLIs deduplicate internally, so 1,000 requested outputs do
not necessarily represent 1,000 independent raw draws. A loop that insists on
1,000 unique stories can stall when its finite variation space is smaller.
Retain these failures and underfilled pools; do not pad them with copied stories
or silently relax their denominator. The judge selects uniformly from the
returned pool, which cannot undo any selection bias inside that CLI.

Aggregate scoring streams one world's samples at a time and recompresses the
actual pooled, quality-qualified exact-unique stories. Separate shuffled full
and exact-deduplicated story-only XZ archives use the same 64 MiB LZMA2 dictionary.
The large-run report omits the full-corpus word-scrambling/skeleton/growth-curve
controls used in the small canonical diagnostic; per-world skeleton and
compression metrics remain. Corpus size and composition affect compression, so
do not interpret its aggregate score as a matched comparison with 21-world trials.

Artifacts live under `storyworlds/batches/prompt_trials/<name>/`, materialized
sources under `storyworlds/worlds/prompt_trials/<name>/`, and the final summary
at `storyworlds/batches/<name>.report.md`. Preparation is offline; do not mistake
a prepared manifest for a completed generation run. At the frozen input lengths,
the 1,000-world plan estimates $4.74-5.03 generation plus $14.60-15.85 judging if
all worlds qualify. These are estimates, not billing or a hard spend cap.

First large-run result: [1,000-world Luna reference-seeded batch](batches/repaired100_canonical_luna_20260907.report.md).
It materialized 998 worlds; 684 passed sample-plus-verify and 566 passed the
stricter full-count/standalone/replay gate. Terra rated 631 worlds at 5.900/9
quality and 2.222/9 diversity. Fifty timed-out calls and two invalid judge
responses remain unrated, so the full-batch composite is withheld. Returned
usage totals $11.0329, excluding uncertain timeout billing. Raw, repaired,
rejected, sampled, judged, and manually reviewed evidence is retained.

### Screening Reference Examples

Use `rank_reference_worlds.py` to analyze a retained large-run catalog offline:

```bash
./.venv/bin/python storyworlds/rank_reference_worlds.py repaired100_canonical_luna_20260907 \
  --out storyworlds/batches/new_reference_screen.md \
  --shortlist garnet repaired_013 repaired_069 repaired_037 repaired_011 repaired_098 repaired_007 repaired_012
```

It writes a Markdown table, all-reference JSON metrics, and an explicit
candidate reference manifest. Existing output paths are refused. No API calls,
generation, repairs, or canonical changes occur. The manifest can be supplied
to `prompt_trials.py prepare --example-manifest`; omit `--unique-tasks` for a
matched-seed comparison. Revalidate current reference sources before paid use.

Quality and semantic diversity are conditional, equal-weighted world means;
ten sibling stories do not become ten independent reference experiments. Keep
attempted, eligible, rated, missing, strict-pass, and quality-qualified counts
alongside them. Never assign zero quality to an unjudged world. The exploratory
strict joint-delivery screen requires quality >=6 and diversity >=3 on the same
strictly passing world, with sensitivity counts at Q>=6,D>=4 and Q>=7,D>=3.
These screening thresholds do not replace the existing dataset-score protocol.
Small unmatched arms and selecting winners among many examples require fresh,
matched confirmation, not confidence from a precise-looking ranking.

See the [106-reference screen and eight-candidate shortlist](batches/repaired100_canonical_luna_20260907.reference_rankings.md).

The expanded [20-reference working set](batches/repaired100_canonical_luna_20260907.top20.md)
is available as `storyworlds/reference_sets/luna_top20_20260907.json`: 18 core
candidates plus Thud and Loop/Ginger as quality probes. It preserves the
eight-candidate shortlist and leaves the canonical set, including the latest
Puddles, unchanged. Pass this manifest to `prompt_trials.py prepare
--example-manifest` for a future matched trial. No paid run accompanies selection.

The subsequent [100-world Mini trial](batches/top20_mini100_20260907.report.md)
used this exact 20-reference manifest with five matched tasks per reference,
numeric seeds 2026091800-2026091804, `gpt-5.4-mini`/Flex/none, and concurrency 50.
Terra and all scoring/repair rules remained unchanged. It produced 100 files;
72 passed sample-plus-verify, 65 passed the strict local gate, and all 72 eligible
worlds were judged (715 stories). Mean quality was 5.817/9 and semantic diversity
2.389/9; 32 worlds passed both strict local checks and mean quality >=6.
The existing geometric score was 5.554/100. Returned usage cost $1.9901.
See [plan, commands, limitations, and manual QA checks](batches/top20_mini100_20260907.notes.md).
Wrong-branch QA persists even in readable stories; story-only judging is not a
QA correctness certificate. This trial is not a matched Mini-versus-Luna test.

The subsequent [matched 100-world Luna run](batches/top20_luna100_20260907.notes.md)
reused all 100 Mini source/task pairs; normalized request bodies differed only
in model and output path. Luna passed sample-plus-verify on 66 worlds and strict
local checks on 54 (Mini: 72 and 65). Valid judged-world means were Q=6.459 and
D=2.984; on 50 common judged pairs, Luna scored Q=6.402/D=2.860 versus Mini's
5.938/2.420. Confirmed strict-plus-Q>=6 worlds were 39 versus 32. Two invalid
Terra plot partitions remain unrated, so the full Luna composite is withheld.
Returned Luna usage cost $0.4062 generation plus $0.7305 judging. All original,
repaired, sampled, judged, and matched-comparison evidence is retained separately.

## Canonical Trials

`prompt_trials.py` replaces the one-off experiment drivers for controlled
comparisons. The starting matrix is **seven source examples, each generating
the same three tasks: 21 worlds per prompt variant**. Each request includes
only its own arm's example, not all seven examples concatenated together. The
current reference set is **`dialogue_v2`**, selected on 2026-09-07 before prompt
optimization. This deliberately replaces the original seven-world matrix;
historical evaluations remain attached to their original source snapshots.

| Name | Reference | Purpose / Caveat |
| --- | --- | --- |
| `puddles` | Upgraded bundled Puddles | State-driven problems, compatible responses, trace-grounded QA |
| `pirates` | Bundled Pirates | Existing simulation / ASP reference |
| `garnet` | Repaired humorous tall tale | Stronger prose in the earlier five-world pilot |
| `library` | Library Words | Clarify an ambiguous request; transfer knowledge before acting |
| `cart` | One Cart, Two Plans | Negotiate different needs, agree, and complete both deliveries |
| `bridge` | Bridge Builders | Discuss a physical fault, revise the design, test the repair |
| `nell` | Nell and the Dragon v2 | Question ownership; state-driven resolution; independently seeded dialogue/prose |

Puddles stays at its latest source, unchanged. Quesadilla, Thud, Dining, and
Grocery are retired from the default matrix but remain explicit named choices
for historical/custom trials. No old score is transferred to a replacement.
The dialogue references have small plot spaces: their inclusion prioritizes
what they demonstrate to the generator, not their exact-string yield. See the
[curation and local verification record](batches/canonical_dialogue_v2_20260907.report.md).

`canonical_examples.py` is the single registry of tracked source paths. No
extra copies become competing editable canon. `prepare` snapshots the selected
sources, contract, helper modules, factory, repair, judge, and addendum. It
stores **every complete request body before any API call**, with SHA-256
fingerprints. Generation submits those bodies unchanged even if the working
prompt/example files are subsequently edited.
New manifests record `example_set=dialogue_v2` for the full current matrix and
`custom` for explicit subsets/mixes; old unversioned manifests remain readable.
`--example-worlds all` in the standalone factories still means Puddles + Pirates.

```bash
./.venv/bin/python storyworlds/prompt_trials.py prepare dialogue_trial_01 --seed 2026090605
./.venv/bin/python storyworlds/prompt_trials.py cost dialogue_trial_01
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/prompt_trials.py run dialogue_trial_01

# Change only the addendum; task seeds and reference sources stay matched.
./.venv/bin/python storyworlds/prompt_trials.py prepare dialogue_causal_01 --seed 2026090605 \
  --prompt-addendum storyworlds/prompts/causal_v1.md
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/prompt_trials.py run dialogue_causal_01
./.venv/bin/python storyworlds/prompt_trials.py report dialogue_trial_01 dialogue_causal_01
```

The addendum filename above is illustrative: create the proposed prompt change
before preparing that trial. Do not alter the example code, reasoning setting,
and addendum in the same experiment. `--examples puddles library nell` selects a
subset; `--per-example 3`, `--local-samples 1000`, and `--concurrency 5` are
defaults. Concurrency is global, not multiplied by seven arms. `--model` and
`--reasoning-effort` are explicit generation overrides. The canonical judge is
`gpt-5.6-terra`, reasoning `none`, direct OpenAI/Flex, protocol
`story_set_quality_v1`. Each arm's task index uses the same local/selection seed
(777 + index). It reads **ten randomly selected stories together per world**
from the retained local samples: 21 calls, 210 judged stories per full trial.
The 1,000 local samples measure large-pool diversity and deterministic checks.
This is a new judge protocol, not a directly interchangeable Mini score.

Prompt protocol `custom_tool_python_v12` puts an explicitly supplied addendum
after the complete example and seed request. The no-addendum prompt text is
unchanged from v11; no optimization candidate is enabled by default. Older
prepared requests retain their original placement. The [three-run optimization
record](batches/prompt_optimization_20260907.report.md) distinguishes the first
two content-only trials from the third content-plus-placement experiment.
Re-evaluating an older prepared trial explicitly uses the current Terra set
protocol and logs it in the new evaluation's settings; frozen generation
requests and old evaluation results stay untouched.

### Diversity And Geometric Score

For each generated world, request 1,000 stories with QA in one JSON run. Keep
returned counts even when a script caps its output or returns fewer stories.
Store one `samples.jsonl` per world, not one Markdown document per story.

- **Exact uniques:** distinct story strings; uniqueness fractions divide by the
  requested count, not just the successfully returned count.
- **Skeleton uniques:** remove sampled parameter values and normalize numbers
  with the existing training contributor analyzer. Compute this after exact
  deduplication. This is a template-collapse diagnostic, not proof of distinct
  plots: unrecorded substitutions can escape it, and structural parameter
  values can also be removed.
- **LZMA:** XZ format, preset 6, on a compact UTF-8 JSON array of story strings
  only. Sort, then shuffle with fixed seed 0 before compression. Measure all
  returned stories, exact-deduplicated stories, and unique skeletons separately.
  Preserve input bytes, compressed bytes, and compressed/input ratio. Lower
  ratio means greater compressibility; higher ratio is the weak diversity
  signal. Excluding params/trace/QA prevents metadata from inflating diversity.
- Also record own `--verify`, bare CLI execution without injected `PYTHONPATH`,
  replay under two `PYTHONHASHSEED` values, static QA duplication/source hits,
  and mean story / story+QA word counts.

`dataset_score.py` replaces the initial additive weighted score with protocol
`quality_diversity_geometric_v1`. It scores each arm and the complete trial from
their own pooled corpus, **not by averaging per-world scores**:

```text
score = 100 * Y * sqrt(Q * D)

Y = usable distinct stories / requested stories
Q = mean assigned world quality of usable distinct stories / 9
D = min(1, compressed(pooled usable distinct stories)
           / sum(compressed(each usable distinct story independently)))
```

**Usable** means the source world passes runtime and its own `--verify`, and
its mean judged overall rating is at least **6/9**. Set `prepare --minimum-quality 6` to change
that explicit policy; the actual policy and code hash are recorded per
evaluation. Failed or below-floor worlds contribute no text, but their
requested slots stay in the denominator. Missing ratings on otherwise usable
worlds leave the pool unscored, rather than silently dropping those worlds.

Exact duplicate strings count once across the whole scoring pool. If the same
string is assigned different qualifying source-world ratings, use the lowest.
Each unique story inherits its world's measured quality estimate: the mean of
the ten individual overall ratings, not a judgment of every variant. `Q`
averages those assigned estimates. Cap each world's contribution
at the requested sample count, so overproducing cannot inflate the score.

`D` measures **cross-story compression retention**, not compressed/raw ratio.
The denominator compresses each story independently, accounting for some
ordinary language redundancy within a story. The numerator allows reuse across
stories. Compress the same UTF-8 JSON story-string lines using raw LZMA2,
preset 6; subtract empty-stream bytes to avoid per-file container overhead.
The pooled dictionary is 64 MiB. An independent story fitting in 64 KiB uses
that smaller dictionary, which can still retain its entire input; larger
stories use 64 MiB. Sort and shuffle pooled text with seed 0. Independent
compression sizes are cached. Params, QA, traces, and filenames never enter
this calculation.

Exact duplicate loss is penalized by `Y`; repetition among surviving distinct
stories is penalized by `D`. Repeating a returned story cannot increase the
score. Quality and compression retention have equal geometric weight: doubling
either, with the other components held fixed, multiplies the score by sqrt(2).
Low quality or diversity cannot be offset by merely adding the other score.

Hypothetical examples, not measured quality results:

| Quality | Retention D | Usable Yield Y | Score |
| ---: | ---: | ---: | ---: |
| 8/9 | 25% | 100% | 47.14 |
| 8/9 | 4% | 100% | 18.86 |
| 8/9 | 25% | 80% | 37.71 |
| 5/9 | 90% | 0%: below floor | 0 |

Keep the raw quality average, exact/skeleton counts, all-text XZ ratios, and
runtime/repair counts visible. `dataset_scores.json` stores yield, quality,
retention, rejected/unrated counts, policy, and composite for each arm and ALL.
Old evaluations are not rescored or overwritten; old `weighted_score` fields
remain historical and are not relabeled as geometric scores.

This is an **optimization index**, not a calibrated probability of usefulness
or a count of independent plots. Keep planned corpus size, sampling, judge,
and compression settings matched across trials. Ordinary shared language also
affects retention; a TinyStories control is still useful. A green `--verify`
is only the generated script's own check, and even ten judged stories can miss
bad variants. Confirm promising changes on fresh tasks and broader judging.
The set-level semantic-diversity rating is reported separately for now: it is
not silently multiplied into this established compression-based formula.

### Pooled Compressibility Review

The original 5% per-world compression coefficient is superseded by the
geometric score above. The all-text corpus measurements below remain separate
diagnostics; they include rejected worlds and repeated stories, while the
score's compression component uses only qualifying, distinct text.

Every evaluation also writes **one pooled archive of all returned stories** in
`eval_NNN/pooled/all_shuffled.stories.jsonl.xz`: up to 21,000 stories for the
default matrix. These files contain one JSON story string per line, nothing
else. The pooled comparison uses LZMA2 preset 6 with an explicit **64 MiB
dictionary**, large enough to look across much of this small corpus. Keep this
recipe fixed when comparing trials; it differs from the older per-world
default-preset measurements.

`compression_review.py` can audit the seven canonical references without
generation APIs, judging, or repairs:

```bash
./.venv/bin/python storyworlds/compression_review.py \
  --out storyworlds/batches/canonical_compression_review --count 1000 --seed 777

# Or pool previously retained samples without executing any world scripts.
./.venv/bin/python storyworlds/compression_review.py \
  --out storyworlds/batches/review_saved_samples \
  --samples-jsonl storyworlds/batches/prompt_trials/baseline/eval_001/*/*/samples.jsonl
```

It retains grouped and shuffled full corpora, exact-deduplicated text, all and
unique skeletons, and a word-order-destroyed control. The growth curve pools up
to 10/50/100/250/500/1,000 stories per world. Inspect compressed bytes/story as
well as compressed/input ratio: padding a story with predictable text changes
the latter. Do not pad short batches or hide returned counts.

First result: [canonical compression review](batches/canonical_compression_20260907.report.md).
Seven worlds returned 6,600 stories (Thud stopped at 600), with 6,596 exact
uniques. Their 8.26 MiB story-only corpus compressed to 243.3 KiB, **2.88%** of
input. Exact dedup barely changed this (2.87%). Thus exact uniqueness greatly
overstates new text information in this sample. The word-order-destroyed
control compressed to 28.44%, showing why compression needs a prose-quality
gate. A same-size natural-story control is still needed before setting an
absolute accept/reject threshold. The later [paid dialogue-v2 generated baseline](batches/dialogue_v2_baseline_20260907.report.md)
returned 20,915/21,000 stories and compressed them together to 1.94% of input;
exact dedup left 11,637 texts, still compressing to 2.24% of input.

### Judge Cost And Coverage

The canonical judge selects **10 raw sample positions per world**, uniformly
without replacement with a saved seed. Do not dedup first or pick the most
different stories. Preserve identical stories at different positions. A short
pool contributes only the available positions; fewer than two leaves the world
unrated. Judge only runtime/verify-passing worlds. Failed slots remain in the
score denominator, but do not spend judge calls on them.

One Terra call returns five 0-9 scores per story (coherence, style, grammar,
storytelling, overall), a short note per story, and set-level 0-9 diversity
scores (premise, causal path, ending, language, overall). It partitions all
selected IDs into causal plot groups, ignoring cosmetic name/color/object
swaps, with a short summary per group. Missing ratings, duplicate/unknown IDs,
invalid scores, incomplete responses, and invalid partitions fail validation.
Individual quality and cross-story repetition are separate judgments.
The original calibration story and ratings remain in the prompt, but the
model/set context changed, so do not directly pool these scores with Mini.

The new helper is `openai_world_set_quality.py`. It preserves selected source
indices, pool hash, exact requests, source fingerprints, judge-module snapshots, raw responses,
parsed ratings, evidence, usage and actual model/tier. It uses a 900-second
timeout and **no automatic retries or standard-tier fallback**. A failed or
interrupted paid attempt is retained for inspection. Use a fresh output path
for any deliberate retry. `run` itself never silently pays for a second eval.

To judge the seven reference worlds' already saved samples, without generating
new scripts or resampling worlds:

```bash
# Add --dry-run and a different --out path to save requests without API calls.
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_world_set_quality.py \
  --compression-review storyworlds/batches/canonical_compression_20260907_v2 \
  --out storyworlds/batches/canonical_set_quality_<new-name>
```

Ten stories provide a finer semantic diagnostic, not certification of all
1,000 samples or diversity across different worlds. For example, independent
sampling has only about a 40% chance of hitting a failure that occurs 5% of the
time (1 - 0.95^10). Keep the local compression, duplicates, and runtime checks.

#### Cost Per 21-World Attempt

Pricing checked 2026-09-07, USD per million tokens, short context:

| Model / Tier | Input | Cached Input | Cache Write | Output |
| --- | ---: | ---: | ---: | ---: |
| Luna / Flex | $0.10 | $0.01 | $0.125 | $0.60 |
| Terra / Flex | $1.00 | $0.10 | $1.25 | $6.00 |

Source: [OpenAI pricing](https://developers.openai.com/api/docs/pricing).
[Flex](https://developers.openai.com/api/docs/guides/flex-processing) trades
latency and availability for the lower rate; it is not a lower-quality model.
Both generation and judging explicitly request Flex. No standard-tier fallback
is configured. Generation retains the factory's existing SDK transport retries;
the new judge disables retries so an uncertain paid call is not resubmitted.

The 25 recent Luna/repaired-example generations averaged **10,670 input and
4,123 output tokens** each. Scaling those observed responses to 21 worlds is
roughly **$0.08**, including reported cache-write tokens. Canonical prompts vary
in size, so the preflight command uses the actual frozen request text:

```bash
./.venv/bin/python storyworlds/prompt_trials.py cost canonical_baseline_20260907
# Override planning assumptions after measuring the new judge.
./.venv/bin/python storyworlds/prompt_trials.py cost canonical_baseline_20260907 \
  --generation-output-tokens 4200 --judge-input-tokens 3950 --judge-output-tokens 1014
```

The completed [original seven-world reference baseline](batches/canonical_set_quality_20260907.report.md)
used 27,652 input and 7,098 output tokens across seven Terra calls, costing
**$0.07714775** including cache writes. The calculator now defaults to the
rounded observed judge means: **3,950 input + 1,014 output tokens per call**.
All seven calls used Flex, with no reasoning tokens or retries.

For the original prepared 21-world trial, with 4,200 output tokens/generated script and
those measured judge-token assumptions:

| Stage | Calls | Estimated Cost |
| --- | ---: | ---: |
| Luna generation | 21 | $0.082-$0.090 |
| Terra judging, 210 stories | 21 | $0.211-$0.231 |
| Repair, 21,000 local samples, dedup, LZMA | local | $0 API |
| Total | 42 | **$0.293-$0.321** |

Scaling actual recent Luna and Terra responses gives **$0.3114**. Budget
roughly **$0.32 typical, $1 with headroom**, not a hard spending cap.
The range above covers unreported cache writes, not all uncertainty. Input
estimation is frozen input JSON characters / 4, not exact API tokenization;
judge counts are measured on reference worlds, whose story lengths may differ
from newly generated worlds. The earlier unmeasured planning estimate was
$0.435-$0.474 using 6,000 input and 1,800 output judge tokens per request.
At every request's current output cap (32k generation, 4k judge), the same
estimated inputs would cost about **$1.05**, before retries. Failed/truncated
responses can still cost money. A quality-only re-evaluation pays just the
judge portion, not another generation batch.

Those projections predate `dialogue_v2`. Its first live 21-world run now has
returned-usage estimates of **$0.081549 generation + $0.210983 judging =
$0.292532 total**. All 42 returned tiers were Flex. Ten stories from each world
were judged exactly once: 140 after automatic repair, then 70 newly recovered
stories; unchanged ratings were reused. See the [full report](batches/dialogue_v2_baseline_20260907.report.md)
for token counts, manual repair caveats, and the retained batch archive.

`trial_cost.py` prices actual returned model/tier/usage, separates ordinary
input from cache reads and writes, and includes billed reasoning in total
output tokens. Missing cache-write breakdown produces a lower/upper estimate;
missing usage or unknown model/tier is marked unpriced, never presumed free.
Completed trial `costs.json` separates one-time generation from this judge pass.
These are usage estimates, not invoice reconciliation or account-wide totals.

#### Baseline Calibration Findings

The original seven canonical references were judged on ten random stories each; all 70
were also read manually before examining Terra's ratings. Mean quality was
**7.89/9**, semantic diversity **3.29/9**, and the pooled geometric score
**19.88/100** on 6,596 distinct stories out of 7,000 requested. All source
fingerprints matched and all seven sources passed a fresh own `--verify`.
This reference calibration is distinct from the later 21-world Luna
generation trial.
These are historical results for Puddles/Pirates/Quesadilla/Thud/Dining/Garnet/
Grocery, not ratings for the later `dialogue_v2` reference set.

The broad semantic ranking made sense: Garnet scored quality/diversity
**8.9/5**, Quesadilla **8/1**. But quality scores missed concrete continuity
defects, and plot-group counts used inconsistent granularity. Quesadilla had
six minor reason-based groups despite its justified diversity score of one.
Treat plot groups as inspectable evidence, not a comparable numeric objective.

The compression-based composite placed Pirates/Puddles ahead of Garnet and
penalized Thud's 600/1000 yield. This measures retained text information and
output coverage, not just storytelling or causal diversity. Keep its components
and Terra's semantic scores visible; do not optimize only the composite yet.
The baseline prompt/formula is unchanged. Pin the manual failures and matched
corrected controls before trying a new judge prompt. Details and sample IDs
are in the linked reference-baseline report.

#### First Dialogue-V2 Generated Baseline

**Post-baseline prompt change:** `custom_tool_python_v11` makes a brief spoken
back-and-forth exchange mandatory in each sample via the shared `STORY.md`
contract, regardless of reference or sampled features. Speech should change
knowledge, decisions, or actions; inner thoughts and quoted notes do not count.
This is prompt guidance, not a newly implemented semantic validation gate.
The feature sampler and matched seeds are unchanged. The completed baseline
used `custom_tool_python_v10`; its frozen requests, ratings, and source snapshots
were not rebuilt. Each subsequent trial must use a fresh name.

That matched [paid v11 trial is now complete](batches/dialogue_required_v11_20260907.report.md):
same 21 tasks, source hashes, seeds, Luna/Flex, Terra/Flex, and score formula.
After separately retained manual recovery, quality rose 6.41 -> 6.92/9 and
quoted-word share 17.7% -> 34.0%. Semantic diversity stayed 1.19/9; exact unique
texts fell 11,637 -> 9,720 and composite score 6.26 -> 5.91/100. Nell-based
outputs collapsed to 120 exact strings across three 1,000-draw pools.
Automatic verification passed 11/21 versus 14/21 in v10; final verification,
standalone execution, and replay pass 21/21. Eleven unchanged judged pools were
reused, and ten recovered pools added 100 judgments, for 210 stories total.
Estimated API spend: $0.319511. Retain the dialogue change for its demonstrated
dialogue benefit, not as proof that quality/diversity or training readiness is solved.

The [completed 21-world trial](batches/dialogue_v2_baseline_20260907.report.md)
uses the same three tasks in each of seven arms, no addendum, and the unchanged
score formula. Raw sampling passed 11/21; automatic repairs recovered three;
seven needed separately retained manual patches. All 21 needed a nested import
path correction for standalone execution. The original automated `eval_001`
remains unchanged; `manual_001` holds assisted recovery and provenance.

Final means: **quality 6.41/9, semantic diversity 1.19/9**. Thirteen worlds meet
the mean-quality floor; their 7,135 exact unique texts yield a **6.26/100**
geometric score. Nell leads quality at 7.77/9, Garnet leads semantic diversity
at 2.67/9. With three tasks per arm, these are exploratory comparisons.
Dialogue did not transfer reliably: Cart has sustained exchanges, while Nell
outputs often have little or no direct dialogue. Quote counts include thoughts,
chants, and notes, so they are diagnostic rather than a conversation score.

Read one preselected story plus QA from each generated world before inspecting
ratings. The judge catches major prose defects and repeated plots, but misses
some clue/continuity errors. It does not receive QA: object-repr leakage and
answers contradicting prose remain training blockers despite green self-checks.

Known pipeline gaps exposed by this run, not changed mid-baseline:

- The sampler injects `PYTHONPATH`; all 21 automatic standalone CLI checks fail
  at the deeper trial directory. Standalone/hash replay are recorded but are
  not currently part of the score gate. Require them before accepting a future
  trial as independently runnable.
- Puddles/nose silently deduplicates its own 1,000 draws to 915. Do not pad or
  hide the shortfall; a uniform sample from this pool is not a uniform sample
  of original draws. Enforce raw sampling for the next trial.
- Pin placeholder, doubled-article, object-repr, clue/payoff, and grounded-QA
  cases before optimizing the prompt or treating the composite as sufficient.

For manual recovery, snapshot post-automatic sources first and retain each
failed check attempt. Reuse old ratings only after proving the full local
sample pools unchanged, retaining source hashes and the originating judge run.
Judge only newly recovered/changed worlds within the authorized sample budget.
This batch verified equality for all 14 old pools and judged seven new pools;
it did not pay to judge all 21 a second time. The batch-local recovery driver,
seven repair regression tests, and analysis helper are in the retained archive.

#### Historical Mini Cost

On 2026-09-07, the 20 final repaired-example ratings used 13,297 input tokens
and 640 output tokens, no cached tokens, served on Mini/Flex. At the documented
standard Mini rates of $0.75/$4.50 per million input/output tokens and Flex's
Batch-rate discount, this estimates **$0.00643 total**, or **$0.000321 per
world**. This is a token-based estimate, not an account billing reconciliation.
See [Mini pricing](https://developers.openai.com/api/docs/models/gpt-5.4-mini),
[Flex pricing policy](https://developers.openai.com/api/docs/guides/flex-processing),
and [Batch discount](https://developers.openai.com/api/docs/guides/batch).

### Artifacts And Recovery

Each trial lives in `storyworlds/batches/prompt_trials/<name>/`; materialized
scripts live in `storyworlds/worlds/prompt_trials/<name>/<example>/`.

- `trial.json`, `inputs/`, per-arm `requests.jsonl` and generation manifests:
  frozen configuration, source snapshots, exact request bodies, matched tasks.
- Per-arm `attempts.jsonl`, `received.jsonl`, `responses.jsonl`, `raw/`:
  attempt ledger, durable original responses, materialization outcomes, and
  original generated scripts. Records are appended, never truncated on resume.
- `eval_001/`, `eval_002/`, etc.: per-world before/after sources, local samples,
  checks, repair outcomes, exact judge inputs, quality JSONL, summary, report.
  Repairs use `repair_batch_output.repair_source`; a failed local repair is
  rolled back. No LLM repair is involved.
- `eval_NNN/set_judge/`: frozen ten-story requests and pool hashes, request
  ledger, raw responses, quality/diversity ratings and plot groups, report.
- `eval_NNN/costs.json`: one-time generation and this evaluation's judge costs
  estimated from returned usage, with missing-usage counts.

```bash
# Stage generation and evaluation separately.
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/prompt_trials.py run baseline --generation-only
./.venv/bin/python storyworlds/prompt_trials.py evaluate baseline --skip-quality
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/prompt_trials.py evaluate baseline

# Archive all raw/repaired data and materialized sources under the existing LFS rule.
./.venv/bin/python storyworlds/prompt_trials.py archive baseline
```

`prepare` refuses existing trial names. `run` skips recorded requests and uses
a per-trial process lock. Saved responses can be materialized on resume without
another API call. A started request whose response was not saved has an unknown
billing outcome and is **not automatically resubmitted**; inspect its ledger
before explicitly preparing any replacement. SDK transport retries remain the
service factory's existing behavior.

Repeated `run` does not launch a second judge pass. Use `evaluate` explicitly;
each invocation makes a new evaluation directory and can spend on Terra again.
Reports show the latest completed evaluation; incomplete evaluations remain
on disk. Exit status 1 can mean the trial finished with failed worlds or missing
ratings, not necessarily that the whole run crashed. Read the report before
retrying. `archive` writes a timestamped `.tar.gz` and SHA-256 sidecar in
`storyworlds/batch_archives/`, which is already covered by Git LFS.

For sequential optimization, decide the next prompt only after the previous
trial's metrics and manual reading. Keep automatic-only and manually assisted
scores separate. A verifier can contain a false speech quota, but it can also
correctly expose a missing state transition: inspect the actual trace before
changing it. Check that repairs have not replaced validation with `pass` or
fallback defaults, and add negative tests for each such recovery. Passing the
script's own verifier is not an independent proof of semantic correctness.

Read the same fixed selected story plus its QA from each world before looking
at ratings. Do not edit prose after seeing its score. For recovered worlds,
reuse an earlier judgment only when the entire sampled pool is identical; judge
only previously unjudged pools. Preserve every attempt and its source diff.
After selecting a provisional winner, use new task seeds for confirmation;
improvement on this repeatedly inspected 21-world set is not held-out evidence.

## Repair Policy

Use `--repair-failures` by default. It probes each generated script with
`py_compile` and `-n <variants> --seed <seed> --json`.

If a script already passes, the repair pass leaves it alone. If a failing script
matches a known repair rule, the pipeline writes the repaired source, probes it
again, and keeps the edit only if the probe passes. Failed repair attempts are
rolled back.

Good repair rules are mechanical and model-specific, for example:

- add a missing short `-n` alias when the script only defines `--n`
- make generated `meters` / `memes` maps behave like `defaultdict(float)`
- add simple dataclass aliases such as `.label`, `.phrase`, or `.award_phrase`
- fix stale local variable references such as `thing.label` when the generated
  entity is named `item`

Avoid bulky reliability instructions in the prompt when a tiny deterministic
repair rule fixes a common generated-code mistake.

## Repair-First Workflow

When a run has script failures, repair before spending more quality-judge calls.
The target is near 100% runnable scripts, then quality assessment.

1. Preserve the generated batch artifacts.

   Before materializing broad repairs, copy the current report and world scripts
   to a clearly named backup:

   ```bash
   cp storyworlds/batches/storyworld_service_<stamp>_seed<seed>_n100.report.md \
     storyworlds/batches/storyworld_service_<stamp>_seed<seed>_n100.report.before_repair_iter1.md

   cp -R storyworlds/worlds/gpt-5.4-mini_service_<stamp>_seed<seed>_n100 \
     storyworlds/batches/storyworld_service_<stamp>_seed<seed>_n100.stories.before_repair_iter1
   ```

2. Improve `repair_batch_output.py` for repeated mechanical failures.

   Add rules only for concrete generated-code patterns. Good examples include:

   - `rng.choice(sorted(combos))` on tuples containing dataclass objects
   - invalid generated syntax such as `def ASP_RULES = r"""`
   - missing dataclass fields/properties used later by the script
   - ordinary dicts used as `meters` / `memes`
   - generated lookup code that assumes a constant table has a key
   - bounded propagation loops when a generated fixed-point rule can fire forever

   Syntax-check the repair script after edits:

   ```bash
   ./.venv/bin/python -m py_compile storyworlds/repair_batch_output.py
   ```

3. Re-materialize the same batch without quality.

   Use the original manifest so the model outputs stay fixed and only repair
   behavior changes:

   ```bash
   ./.venv/bin/python storyworlds/openai_service_world_pipeline.py \
     --from-manifest storyworlds/batches/storyworld_service_<stamp>_seed<seed>_n100.manifest.json \
     -n 100 \
     --repair-failures \
     --skip-quality \
     --report-out storyworlds/batches/storyworld_service_<stamp>_seed<seed>_n100.repair_iter1.report.md
   ```

4. Run static QA over the repaired worlds directory.

   This is the repair gate:

   ```bash
   ./.venv/bin/python storyworlds/qa_static_check.py \
     --worlds-dir storyworlds/worlds/gpt-5.4-mini_service_<stamp>_seed<seed>_n100 \
     -n 100 \
     --variants 3 \
     --seed 42 \
     --timeout 30
   ```

   The checker may exit nonzero because duplicate QA groups are a lint failure.
   For the repair gate, first look at the header:

   - `Sampled 100 world script(s)` is the runnable target.
   - `Run failures:` must be absent.
   - Duplicate story-QA groups are a quality/QA follow-up, not a script-repair
     failure.

5. Repair remaining failures one by one.

   If only a few scripts remain, inspect each traceback and patch the generated
   script directly. Also fold general patterns back into `repair_batch_output.py`
   when they are replayable. Probe individual scripts with the same import path
   used by the static checker:

   ```bash
   PYTHONPATH=storyworlds ./.venv/bin/python \
     storyworlds/worlds/gpt-5.4-mini_service_<stamp>_seed<seed>_n100/<script>.py \
     -n 3 \
     --seed 42 \
     --json
   ```

   Typical last-mile fixes:

   - relax an over-strict generated `valid_combos()` predicate
   - store ids or handle entity objects consistently in `world.facts`
   - add missing CLI tail code when a script was truncated after helper
     definitions
   - add `default=str` to JSON dumps for dataclass-heavy payloads
   - fix generated facts such as `hero` / `helper` missing from `world.facts`

6. Re-run the full static gate.

   Do not run quality assessment until all scripts are sampleable. A clean repair
   pass should say `Sampled 100 world script(s)` and list no run failures.

## Quality Assessment After Repair

Once static sampling is clean, run the quality judge against the repaired worlds
directory. This assesses the actual one-by-one repaired files instead of
regenerating or re-repairing from the manifest:

```bash
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_story_quality.py \
  --worlds-dir storyworlds/worlds/gpt-5.4-mini_service_<stamp>_seed<seed>_n100 \
  --limit 100 \
  --batch-size 50 \
  --sample-concurrency 16 \
  --sample-timeout 30 \
  --seed 777 \
  --model gpt-5.4-mini \
  --out storyworlds/batches/story_quality_service_<stamp>_seed<seed>_n100.repaired_final.jsonl \
  --summary-out storyworlds/batches/story_quality_service_<stamp>_seed<seed>_n100.repaired_final.summary.json
```

Record:

- rated count and API failures
- quality averages and baseline deltas
- lowest-overall examples
- duplicate QA group count from the static checker
- which repair rules were generalized and which scripts needed one-off patches

## Reading A Run

Start with the report summary:

- Requested/generated worlds
- Quality-rated stories and overall average
- QA static run failures
- Duplicate story-QA groups
- Repair log lines

Then inspect the low-scoring stories in `*.quality.summary.json`. Read the
linked script and prompt snapshot beside each bad story. Classify the defect:

- prompt-order or example-transfer issue
- runnable-code issue suited to scripted repair
- bland-but-valid story quality issue
- duplicate or shallow QA issue
- script-specific bug that should not become a broad repair rule

Only change the prompt when the defect looks broad. Only add a repair rule when
the failing pattern is concrete and repeated, or when it is clearly harmless and
specific.

## Diagnosing Prompt vs Repair vs Examples

When a run fails, do not immediately add more instructions. First decide which
part of the system owns the defect.

Check the exact run inputs:

```bash
head -80 storyworlds/batches/storyworld_service_<stamp>_seed<seed>_n100.manifest.json
```

Confirm:

- `prompt_addendum`: whether the run used an addendum or the base prompt only
- `model`, `base_seed`, `count`, `concurrency`, `reasoning_effort`
- prompt snapshots under `*.prompts/`

Then inspect the prompt stack:

- `storyworlds/STORY.md`: canonical contract
- `storyworlds/openai_batch_world_factory.py`: generated base prompt and example
  world selection
- `storyworlds/prompts/gpt54mini_service_reliability_*.md`: optional addenda
- the per-job prompt snapshot for a failed or low-scoring script

Use this ownership guide:

| Symptom | Likely owner | Preferred fix |
|---|---|---|
| Syntax typo, bad quote, `def ASP_RULES =`, `rng.choice(sorted(combos))` on dataclass tuples | repair layer | Add or adjust `repair_batch_output.py` rule |
| Missing dataclass convenience fields such as `.phrase`, `.label_word`, `.meters`, `.memes`, `.tags` | repair layer, unless it changes semantics | Add safe dataclass fallback/default rule |
| Ordinary `-n 3 --json` has no valid combos | prompt/addendum or examples | Tell model to keep a compact valid story space; examples should show this |
| `resolve_params()` chooses params that `generate()` rejects | prompt/addendum | Emphasize simple keys and combo consistency |
| `world.get("hero")` before adding hero, or QA reads missing `world.facts` | prompt/addendum | Emphasize state initialization before rules/prose/QA |
| Infinite propagation loop | prompt/addendum plus repair safety net | Ask for idempotent rules; keep bounded-loop repair |
| Role placeholders leak into prose (`child`, `hero`, `helper`) | examples/addendum | Improve examples and add semantic prose guidance |
| Duplicate story-specific QA across variants | addendum or example QA pattern | Require `story_qa` from `StoryParams` / `world.facts`; generic definitions go to `world_qa` |
| Many failures copy a pattern from `puddles.py` / `pirates.py` | examples | Replace examples with smaller golden examples |
| A single generated script has a one-off domain mistake | one-by-one generated-file repair | Patch the script; only generalize if repeated |

When editing an addendum, remove instructions that duplicate the repair script or
the base prompt. Addenda should focus on decisions the repair pass cannot safely
infer:

- choose a small valid state space
- keep `StoryParams` as CLI-safe keys/names
- make random generation select only accepted combos
- initialize `world.facts` and entities before readers/rules use them
- make causal rules idempotent
- prevent semantic quality defects such as role placeholders and duplicate QA

If a defect looks like example parroting, inspect the embedded examples before
adding more negative instructions. The current base prompt includes complete
world examples from `EXAMPLE_WORLD_PATHS` in
`storyworlds/openai_batch_world_factory.py`. Those examples are powerful: the
model may copy both their good architecture and their brittle idioms. Prefer
cleaning or replacing examples over stacking contradictory addenda.

Before running a new addendum broadly, keep it testable:

```bash
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_service_world_pipeline.py \
  -n 100 \
  --seed <new-seed> \
  --model gpt-5.4-mini \
  --reasoning-effort low \
  --max-output-tokens 32000 \
  --concurrency 50 \
  --prompt-addendum storyworlds/prompts/gpt54mini_service_reliability_v3.md \
  --repair-failures
```

Compare that against a base-prompt run, not just against an older repaired
manifest. The question is whether the addendum improves fresh generation after
the same repair layer is applied.

## Rerunning Existing Manifests

After changing repair rules, rerun from the same manifest so the generated model
outputs stay fixed:

```bash
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_service_world_pipeline.py \
  --from-manifest storyworlds/batches/storyworld_service_<stamp>_seed<seed>_n100.manifest.json \
  --repair-failures
```

For local runnable/static QA checks without the quality judge:

```bash
./.venv/bin/python storyworlds/openai_service_world_pipeline.py \
  --from-manifest storyworlds/batches/storyworld_service_<stamp>_seed<seed>_n100.manifest.json \
  --repair-failures \
  --skip-quality
```

## Comparing Iterations

Use one report per iteration. Record at least:

- prompt change, if any
- seed
- runnable scripts out of 100
- quality overall average and lowest examples
- duplicate QA groups
- repair rules added or changed

The best prompt changes should hold up across fresh seeds, not just recover a
single known run.
