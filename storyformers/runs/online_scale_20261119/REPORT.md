# Ten larger continuation runs

Ten independent runs completed ten training iterations each, starting from the best previous four-story checkpoint. Five seeds use eight stories per iteration; five use sixteen. All positions contribute to one output-weight gradient per iteration, followed by one live Luna grammar proposal and a full-batch/replay gate.

The runs share the 192-story synthetic token/POS training pool. Their 1,200 story exposures overlap across runs; these are not 1,200 unique new stories. Within a run, stories are sampled without replacement. Paired batch sizes share a shuffled order. Model capacity stays context 32, one layer and sixteen head slots.

The teacher now receives the previous candidate scores and a short pre-update generated sample. Generated tokens are diagnostic, never gold targets. The gate remains next-token likelihood plus replay protection; it does not directly optimize story quality. This combined protocol change is not an isolated ablation of batch size or feedback.

All training was frozen before evaluating validation/test rows 24–47 (24 stories each), outside the earlier online pilot subsets. Controls start from the identical checkpoint and receive the same ten weight updates and replay gate, without new teacher edits. Runtime generation makes no LLM calls.

## Held-out results

Starting checkpoint on this test slice: NLL **1.900**, accuracy **46.7%**.

| Run | Stories/step | Targets | Teacher edits | Test NLL | Accuracy | Control NLL | Complete framing |
|---|---:|---:|---:|---:|---:|---:|---:|
| [run_01_b08](run_01_b08/training_report.json) | 8 | 1717 | 9/10 | 1.327 | 53.7% | 1.893 | 0/5 |
| [run_02_b16](run_02_b16/training_report.json) | 16 | 3513 | 4/10 | 1.452 | 54.0% | 1.893 | 0/5 |
| [run_03_b08](run_03_b08/training_report.json) | 8 | 1757 | 5/10 | 1.460 | 54.0% | 1.893 | 0/5 |
| [run_04_b16](run_04_b16/training_report.json) | 16 | 3507 | 8/10 | 1.260 | 53.7% | 1.893 | 0/5 |
| [run_05_b08](run_05_b08/training_report.json) | 8 | 1736 | 7/10 | 1.327 | 51.9% | 1.893 | 0/5 |
| [run_06_b16](run_06_b16/training_report.json) | 16 | 3513 | 6/10 | 1.393 | 49.2% | 1.893 | 0/5 |
| [run_07_b08](run_07_b08/training_report.json) | 8 | 1767 | 6/10 | 1.303 | 51.7% | 1.893 | 0/5 |
| [run_08_b16](run_08_b16/training_report.json) | 16 | 3499 | 6/10 | 1.306 | 56.0% | 1.893 | 0/5 |
| [run_09_b08](run_09_b08/training_report.json) | 8 | 1746 | 8/10 | 1.317 | 54.4% | 1.893 | 0/5 |
| [run_10_b16](run_10_b16/training_report.json) | 16 | 3514 | 8/10 | 1.293 | 52.3% | 1.893 | 0/5 |

Five-run averages (with observed range; not a confidence interval):

- Batch 8: accuracy 53.2% (51.7%–54.4%); NLL 1.347 (1.303–1.460), 5/5 evaluable runs.
- Batch 16: accuracy 53.0% (49.2%–56.0%); NLL 1.341 (1.260–1.452), 5/5 evaluable runs.

All five samples from every teacher model, including failures, are included below. The exact-template framing check is not a general narrative-quality judge.

## Learned structure

| Run | Added output rules | Occupied heads | New fields |
|---|---:|---:|---|
| run_01_b08 | 35 | 2 | none |
| run_02_b16 | 18 | 2 | none |
| run_03_b08 | 21 | 2 | none |
| run_04_b16 | 32 | 2 | none |
| run_05_b08 | 30 | 2 | none |
| run_06_b16 | 22 | 2 | none |
| run_07_b08 | 27 | 2 | none |
| run_08_b16 | 26 | 2 | none |
| run_09_b08 | 26 | 2 | none |
| run_10_b16 | 24 | 2 | none |

## Unfiltered generations

### initial

Seed 0:

```text
Tom's scissors

One day.
```

Seed 1:

```text
A time

And Lily slowly took apples, Lily found the story, Lily's the time.. Lily slowly used the day.

And scissors.
```

Seed 2:

```text
Tom took red apples.

The End.
```

Seed 3:

```text
The day

The scissors, the time!
```

Seed 4:

```text
The small the small red the time.
```

### run_01_b08_teacher

Seed 0:

```text
Tom's needles

One morning..
```

Seed 1:

```text
A time

And needles.
```

Seed 2:

```text
Tom took red apples.

The End.
```

Seed 3:

```text
The needles

The scissors, Ben found small day found the story ended the small needles.

Until a little village.. red story.
```

Seed 4:

```text
The small day. small day.
```

### run_02_b16_teacher

Seed 0:

```text
Tom's scissors

One morning.
```

Seed 1:

```text
A time

And so found the story.

That is all small Lily's the time.. Lily slowly used the day.

And so found small apples, Lily slowly ate apples.

And that was red slowly took the time!
```

Seed 2:

```text
Tom took red apples.

The End.
```

Seed 3:

```text
The day

The scissors, Ben found small needles found the story ended the small day.

Until a little village.
```

Seed 4:

```text
The small day.
```

### run_03_b08_teacher

Seed 0:

```text
Tom's needles

One morning.
```

Seed 1:

```text
A time

And the end.
```

Seed 2:

```text
Tom took red apples.

The End.
```

Seed 3:

```text
The needles

The scissors, Ben found small needles
```

Seed 4:

```text
The small needles.
```

### run_04_b16_teacher

Seed 0:

```text
Tom's small day

One story.
```

Seed 1:

```text
A time

And the end.
```

Seed 2:

```text
Tom took red apples.

The End.
```

Seed 3:

```text
The pears

The scissors, Ben found small day
```

Seed 4:

```text
The small needles. small needles.
```

### run_05_b08_teacher

Seed 0:

```text
Tom's scissors

One needles.
```

Seed 1:

```text
A story

And so found the story.

That is all small needles.
```

Seed 2:

```text
Tom took red apples.

The End.
```

Seed 3:

```text
The needles

The scissors, Ben found small day found the story ended the small pears.

Until a little village.
```

Seed 4:

```text
The small needles.
```

### run_06_b16_teacher

Seed 0:

```text
Tom's scissors

One morning.
```

Seed 1:

```text
A story

And that is the scissors, Ben found the scissors small Lily's the time.. Lily slowly used the apples.

And needles.
```

Seed 2:

```text
Tom took red apples.

The apples.
```

Seed 3:

```text
The pears

The scissors, Ben found small needles
```

Seed 4:

```text
The small day.
```

### run_07_b08_teacher

Seed 0:

```text
Tom's scissors

One morning.
```

Seed 1:

```text
A time

And the end.
```

Seed 2:

```text
Tom took red apples.

The End.
```

Seed 3:

```text
The needles

The scissors, Ben found small apples found the story ended the small pears.

Until a little village.
```

Seed 4:

```text
The small needles.
```

### run_08_b16_teacher

Seed 0:

```text
Tom's scissors

One day.
```

Seed 1:

```text
A story ended small Lily slowly took apples, Ben found the scissors small Lily's the time.. Lily slowly used the apples.

And so found small apples, Lily slowly ate apples.

And that was red slowly took the time!
```

Seed 2:

```text
Tom took red apples.

The apples.
```

Seed 3:

```text
The pears

The pears, Ben found small needles
```

Seed 4:

```text
The small the small red the time.
```

### run_09_b08_teacher

Seed 0:

```text
Tom's scissors

One morning.
```

Seed 1:

```text
A time

And so found the story.

That is all small needles.
```

Seed 2:

```text
Tom took red apples.

The End.
```

Seed 3:

```text
The needles

The scissors, Ben found small day
```

Seed 4:

```text
The small day

Long ate.
```

### run_10_b16_teacher

Seed 0:

```text
Tom's small needles

One story.
```

Seed 1:

```text
A story

And so found the scissors, Ben found the scissors small needles.
```

Seed 2:

```text
Tom took red apples.

The apples.
```

Seed 3:

```text
The pears

The pears, Ben found small apples
```

Seed 4:

```text
The small needles.
```

## Accounting and verification

All 100 logical teacher steps have settled Luna/Flex responses. Prefix-cache hits: 96/100; cached input 297,792 tokens; cache writes 12,408. Total input 1,967,621, output including reasoning 262,854 tokens.

New estimated cost: **$0.150849**. Conservative new accounting: $1.295171; including earlier experiments: **$1.355084**, below $10. Known-response usage estimates exclude any unknown charges; unresolved attempts retain their entire conservative reservation in the total. Usage estimates are not a billing invoice. [Official Luna pricing](https://developers.openai.com/api/docs/models/gpt-6-luna) was checked before dispatch.

Unresolved earlier attempts: 9, with $1.123604 reserved conservatively. These attempts were preserved and any retry was separately reserved. Proposal/validation errors recorded: 3. Transport failures/rejections: 33; the journal distinguishes definite free retryable failures from unknown outcomes. Original attempts are preserved. [Audit](audit.json), [budget](budget.json), [evaluation](evaluation.json), [summary](summary.json).

The audit checks all 100 model/control transitions, source hashes, served model/tier, request fingerprints, cache-prefix identity, every evaluation checkpoint, and all 55 generations. Per-step folders preserve evidence, replay examples, proposal, receipt, decision and both checkpoints. The test suite passed 157 tests before live execution and 159 tests after adding unknown-outcome recovery checks.

```sh
.venv/bin/python -m storyformers.online_scale \
  --out storyformers/runs/online_scale_20261119 --concurrency 3
.venv/bin/python -m storyformers.scale_report storyformers/runs/online_scale_20261119
```

The first command resumes this suite without repeating committed steps. A different directory creates new paid requests and its own ledger; the spending limit is per suite, not an account-wide limit.
