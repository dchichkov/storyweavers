# Qwen3.8 27B / Puddles Pilot

Run date: 2026-09-07 UTC. Five worlds using `qwen/qwen3.8-27b` through
OpenRouter, Puddles only, and the same seed tasks as the Luna pilot.

## Result

**Five completed API responses, five materialized Python files, one runnable
world.** Existing automatic repair rescued none of the four failures; failed
edits were rolled back. No generated Python was manually edited.

| Metric | Qwen3.8 27B | Luna / same Puddles |
|---|---:|---:|
| Requested / API-completed worlds | 5 / 5 | 5 / 5 |
| Raw runnable | 1/5 | 3/5 |
| Runnable after existing automatic repair | 1/5 | 4/5 |
| Own `--verify` passes | 1/5 | 2/5 |
| Quality-rated stories | 1 | 4 |
| Mini overall /9, runnable stories only | 5.00 | 6.25 |
| Mini overall on the shared nose/bedtime task | 5 | 5 |
| Generation output tokens | 46,625 | 18,950 |

The Qwen average is a **single observation**, not an estimate of its general
story quality. The clearest result is weaker code reliability in this small,
reasoning-disabled pilot. Five syntax parses succeeded, but four scripts failed
at import or execution time. This was not a truncation or proxy-error run.

## Settings

- Generation model: `qwen/qwen3.8-27b`, Responses API at `https://openrouter.ai/api/v1`.
- Generation count/concurrency: 5/5; source mode; 32,000 output-token cap; service tier `auto`.
- Reasoning: `{"effort":"none"}`. All five responses report **zero reasoning tokens**.
- Seed: `2026090605`, producing the same five requests as the Luna Puddles pilot.
- Example: `--example-worlds puddles`; no Pirates, custom example, or addendum.
- Puddles SHA256: `c64ae1bd909e6c8414ae399d58c7f7d932325aeeaf09331297504a86f0cf3a58`.
  Its source is identical to the source embedded in the earlier Luna prompts.
- Judge: direct OpenAI `gpt-5.4-mini`, actual model `gpt-5.4-mini-2026-03-17`,
  Flex, temperature 0, unchanged baseline-calibrated quality protocol.
- Quality seeds: 777-781 in manifest order. The surviving nose world was rated at 779.
- Static QA: ten variants, seed 42. Local diversity/replay check: `-n 100 --seed 2026090605 --qa --json`.

The current prompt wrapper says "Complete examples" rather than the earlier
"Two complete examples"; target paths and model differ. No other intentional
prompt change was made. Generation used OpenRouter credit; the one Mini rating
used the separate direct OpenAI key.

## Failures

| World | First normal-pipeline failure | Further observation |
|---|---|---|
| Decide / dining-room quest | `TypeError: non-default argument 'fragility' follows default argument` | `Prize.fragility` is required after `plural=False`. |
| Gingham / magic | `AttributeError: 'Entity' object has no attribute 'protective'` | `_r_tear` reads a field absent from the entity schema during prediction. |
| Nose / sharing / bedtime | Runnable; Mini 5/9 | Own verification passes, but prose and QA quality remain weak. |
| Bury / teamwork | `ModuleNotFoundError: No module named 'dataclassss'` | Literal misspelling in the standard-library import. |
| Naked / bravery / friendship | `NameError: name 'action_delight' is not defined` | Own verification also encounters unsafe variables in its ASP rules. |

All five fail a bare CLI call with `PYTHONPATH` unset. Four hit a wrong-depth
`results` import first; the fable hits `dataclassss`. The normal pipeline supplies
`PYTHONPATH=storyworlds`, which resolves the shared-helper import but does not
resolve the four failures above.

The import typo and dataclass field order are narrow mechanical defects. The
missing attribute/function and ASP errors need a closer consistency review;
fixing the first exception would not establish that those worlds work correctly.
Those repairs were not mixed into this baseline comparison.

## Surviving Story

Mini scores: coherence 6, style 5, grammar 4, storytelling 4, overall 5.

> The room was soft and dim. Zoe sat beside Parent, holding crinkly blue flannel blanket. A faint itch prickled near her nose, a secret tingling that wanted attention.
>
> A tickle in the nose made Zoe snuffle a little. The corner of the flannel blanket drifted over Parent's knee, waiting to be pulled closer.
>
> Zoe pushed flannel blanket slightly away and leaned she head closer to Parent A tiny glow seemed to come from the space between their noses.
>
> A quiet understanding passed between them, and Zoe smiled softly, no longer alone.

Manual findings:

- Missing articles, a subject pronoun in a possessive slot, and missing sentence punctuation.
- Generic `Parent` naming; the selected setting is recorded but not rendered.
- The sharing lesson is weakly enacted: the child pushes the comfort object away
  and leans closer rather than clearly sharing it. Another branch exhales toward
  the parent and marks the sharing state as satisfied.
- QA largely repeats complete narrative beats from history. Being trace-backed
  does not ensure that each answer directly addresses its question.
- The same defects recur in additional sampled variants, not just the judged story.

The CLI stops after 100 attempts even when asked for 100 distinct outputs. It
returned **71 distinct stories**, with **32 parameter-normalized patterns**.
These are not independent plot counts. Mean length: **94.18 story words**,
**196.42 story-plus-story-QA words**. There were 284 story-QA pairs, 108 distinct
normalized pairs. Replay under another `PYTHONHASHSEED` matched exactly.

The static QA pass sampled ten stories from this world, reported four failed
worlds, and found six repeated story-QA groups. Its own `--verify` reports 256
ASP combinations and five story checks, illustrating that passing these checks
does not establish good prose.

## Cost And Timing

The five saved response `usage.cost` values sum to **$0.146711936**:

| World | Input tokens | Output tokens | Elapsed seconds | Reported USD |
|---|---:|---:|---:|---:|
| Nose | 17,183 | 5,196 | 93.579 | 0.022804860 |
| Gingham | 17,173 | 13,613 | 142.315 | 0.034070120 |
| Dining | 17,200 | 9,734 | 163.205 | 0.029839000 |
| Bury | 17,167 | 7,435 | 186.232 | 0.029171800 |
| Friendship | 17,179 | 10,647 | 191.327 | 0.030826156 |
| Total | 85,902 | 46,625 | concurrent | **0.146711936** |

Starting balance was $6.067749257, implying approximately **$5.921037321** left
after these charges settle. Immediate credit snapshots reflected only the first
three charges ($0.08671398); the report uses all five response costs rather than
understating spend from that lagging account snapshot. Mini judging is separate:
556 input tokens and 32 output tokens, not charged to OpenRouter.

Preflight used the live [OpenRouter model API](https://openrouter.ai/api/v1/models),
which quoted $0.42/M input and $3/M output for the catalog entry. Actual routing
used different effective rates on some requests; the response costs above are
the relevant run measurements. The model and credit responses are saved locally.
OpenRouter documents `reasoning.effort=none` as disabling reasoning in its
[reasoning guide](https://openrouter.ai/docs/guides/best-practices/reasoning-tokens).

## Artifacts

- [Full batch bundle](qwen38_puddles_20260907/): raw responses, manifest, prompt snapshots, original source snapshot, logs, commands, cost metadata, and audit code.
- [Generated scripts](../worlds/qwen38_puddles_20260907/): all five materialized files, unchanged by the unsuccessful repair pass.
- [Pipeline report](qwen38_puddles_20260907/storyworld_service_20260907T030246Z_seed2026090605_n5.report.md).
- [Quality rows](qwen38_puddles_20260907/storyworld_service_20260907T030246Z_seed2026090605_n5.quality.jsonl).
- [Local checks](qwen38_puddles_20260907/checks.json) and [71 sampled stories with QA](qwen38_puddles_20260907/local_samples.jsonl).
- [Portable snapshot](qwen38_puddles_20260907.tgz): this report, full batch bundle, and generated scripts.
- [Luna Puddles comparison](storyworld_service_20260907T022844Z_seed2026090605_n5.manual_review.md).

Everything is preserved locally. No generation was repeated, no manual world
repairs were applied, and no commit or push was made. Factory/repair production
code was not changed for this test.

## Commands

Generation:

```bash
OPENROUTER_API_KEY="$(cat .OPEN_ROUTER.key)" ./.venv/bin/python storyworlds/openai_service_world_factory.py \
  -n 5 --seed 2026090605 --model qwen/qwen3.8-27b \
  --base-url https://openrouter.ai/api/v1 --api-key-env OPENROUTER_API_KEY \
  --reasoning-effort none --service-tier auto --emit-mode source \
  --max-output-tokens 32000 --concurrency 5 --example-worlds puddles \
  --output-dir storyworlds/batches/<new-run> \
  --target-dir storyworlds/worlds/<new-run>
```

Repair and quality, without generation:

```bash
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_service_world_pipeline.py \
  --from-manifest <manifest.json> -n 5 --model qwen/qwen3.8-27b \
  --reasoning-effort none --service-tier flex --example-worlds puddles \
  --quality-model gpt-5.4-mini --quality-base-url https://api.openai.com/v1 \
  --repair-failures --qa-variants 10
```
