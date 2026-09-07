# Storyworld Quality Iteration Pipeline

This loop is for improving the storyworld prompt and the cheap scripted repair
layer without using an LLM repair pass. Generation now defaults to
`gpt-5.6-luna` with reasoning effort `none`; the quality judge remains
`gpt-5.4-mini`. Older Mini batch examples below are retained for reproducibility.

The loop has two distinct phases:

1. Make the generated scripts runnable and sampleable.
2. Judge story quality only after the runnable set is clean.

Do not skip the first phase. Quality scores are misleading when a large fraction
of scripts fail before producing stories.

## Goal

Raise downstream storyworld quality while keeping the generated scripts runnable,
auditable, and close to the original prompt. The main scorecard is:

- `openai_story_quality.py`: story quality averages and low-scoring examples.
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

## Canonical Trials

`prompt_trials.py` replaces the one-off experiment drivers for controlled
comparisons. The starting matrix is **seven source examples, each generating
the same three tasks: 21 worlds per prompt variant**. Each request includes
only its own arm's example, not all seven examples concatenated together.

| Name | Reference | Purpose / Caveat |
| --- | --- | --- |
| `puddles` | Upgraded bundled Puddles | State-driven problems, compatible responses, trace-grounded QA |
| `pirates` | Bundled Pirates | Existing simulation / ASP reference |
| `quesadilla` | Repaired bedtime mystery | Low-diversity control; source has few normalized templates |
| `thud` | Repaired rhyming teamwork | Rhyming control; can encourage authored-story/template copying |
| `dining` | Repaired dining-room detective | Broader normalized variation in the earlier source audit |
| `garnet` | Repaired humorous tall tale | Stronger prose in the earlier five-world pilot |
| `grocery` | Repaired grocery-store moral | Broader variation, but still inspect causal endings and QA |

`canonical_examples.py` is the single registry of tracked source paths. No
extra copies become competing editable canon. `prepare` snapshots the selected
sources, contract, helper modules, factory, repair, judge, and addendum. It
stores **every complete request body before any API call**, with SHA-256
fingerprints. Generation submits those bodies unchanged even if the working
prompt/example files are subsequently edited.

```bash
./.venv/bin/python storyworlds/prompt_trials.py prepare baseline --seed 2026090605
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/prompt_trials.py run baseline

# Change only the addendum; task seeds and reference sources stay matched.
./.venv/bin/python storyworlds/prompt_trials.py prepare causal_v1 --seed 2026090605 \
  --prompt-addendum storyworlds/prompts/causal_v1.md
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/prompt_trials.py run causal_v1
./.venv/bin/python storyworlds/prompt_trials.py report baseline causal_v1
```

The addendum filename above is illustrative: create the proposed prompt change
before preparing that trial. Do not alter the example code, reasoning setting,
and addendum in the same experiment. `--examples puddles grocery` selects a
subset; `--per-example 3`, `--local-samples 1000`, and `--concurrency 5` are
defaults. Concurrency is global, not multiplied by seven arms. `--model` and
`--reasoning-effort` are explicit generation overrides; the judge remains
`gpt-5.4-mini`, using the existing calibrated story-quality protocol on direct
OpenAI/Flex. Each arm's task index uses the same local/quality seed (777 + index).
The judge rates one story per generated world; the 1,000 local samples are for
diversity and deterministic checks, not 1,000 paid judgments.

### Diversity And Weighted Score

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

Initial **weighted score**, on a 0-100 scale:

```text
100 * (0.60 * Mini_overall/9
     + 0.20 * exact_unique/requested
     + 0.15 * skeleton_unique/requested
     + 0.05 * min(1, lzma_all_compressed_bytes/lzma_all_input_bytes))
```

Runtime or own-verify failure makes the score zero. Runnable, verifying worlds
without a successful judge rating are unscored, not excluded from the trial
average. Arm and overall weighted means are shown only when every planned world
has a score. The Mini-only average remains conditional on successful ratings,
with the rated/planned denominator beside it. Raw runnable count, accepted
repairs, and final runnable count are separate columns.

Weights are **provisional**, not a validated training-utility metric. Quality
dominates; compression gets only 5% because nonsense, long prose, and arbitrary
tokens can resist compression. Inspect all components and representative
stories before promoting a prompt. A green `--verify` is only the generated
script's own check, not an independent proof of semantics. Confirm gains on
fresh seed tasks after optimizing the fixed matrix.

### Pooled Compressibility Review

The 5% per-world coefficient above is an initial placeholder, **not a settled
optimization objective**. Following the first canonical audit, pooled corpus
compression is a primary diversity diagnostic alongside quality. Review and
calibrate it before choosing final weights; a per-world average misses the
cross-world question.

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
absolute accept/reject threshold. The paid 21-world baseline has not run.

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
each invocation makes a new evaluation directory and can spend on Mini again.
Reports show the latest completed evaluation; incomplete evaluations remain
on disk. Exit status 1 can mean the trial finished with failed worlds or missing
ratings, not necessarily that the whole run crashed. Read the report before
retrying. `archive` writes a timestamped `.tar.gz` and SHA-256 sidecar in
`storyworlds/batch_archives/`, which is already covered by Git LFS.

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
