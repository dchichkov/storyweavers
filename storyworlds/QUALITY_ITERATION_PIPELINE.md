# Storyworld Quality Iteration Pipeline

This loop is for improving the `gpt-5.4-mini` storyworld prompt and the cheap
scripted repair layer without using an LLM repair pass.

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
2. Narrow scripted repairs for repeated `gpt-5.4-mini` code mistakes.
3. No LLM repair pass unless explicitly requested; it is too expensive for the
   default loop and can hide prompt/codegen defects.

## Default Run

The direct-service pipeline defaults to 100 storyworlds. Use a new seed for each
iteration so the score is not tuned to one lucky or unlucky sample:

```bash
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_service_world_pipeline.py \
  --seed <new-seed> \
  --model gpt-5.4-mini \
  --reasoning-effort low \
  --max-output-tokens 32000 \
  --repair-failures
```

Omitting `-n` intentionally means `-n 100`. Use a different `--seed` every time
you compare a prompt change. Reuse an old seed only for an A/B check where the
prompt is the only thing you want to vary.

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
