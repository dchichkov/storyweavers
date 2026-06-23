# Storyworld Quality Iteration Pipeline

This loop is for improving the `gpt-5.4-mini` storyworld prompt and the cheap
scripted repair layer without using an LLM repair pass.

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
