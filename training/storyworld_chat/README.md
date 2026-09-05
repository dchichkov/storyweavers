# StoryWorld Chat Training Scaffold

This directory contains a small from-scratch training setup for StoryWorld
models.  The data format is OpenAI-compatible chat JSONL:

```json
{"messages":[{"role":"system","content":"..."},{"role":"user","content":"..."},{"role":"assistant","content":"..."}],"metadata":{"task":"story"}}
```

The scripts are intentionally light on assumptions.  The exporter is stdlib-only
and samples `storyworlds/worlds/*.py`; the tokenizer/trainer scripts are for the
target Ubuntu/DGX machines and import optional ML dependencies only when run.

## Current Linux Setup And Progress

Last verified on the `pi` host on 2026-09-04:

- Repository: `/home/dmitry/storyweavers`, on `main` and synchronized with the
  Mac clone before the production run.
- GPU: NVIDIA GeForce RTX 4090 with 24 GB VRAM.
- Python environment: `training/storyworld_chat/.venv` using Python 3.10.12.
- Training stack: PyTorch 2.14.0 with CUDA 13.0, Transformers 4.57.6,
  Accelerate 1.14.0, Tokenizers 0.22.2, and TensorBoard 2.21.0.
- CUDA import, allocation, matrix multiplication, model training, checkpoint
  save, checkpoint reload, and chat-template inference have all been verified.

Create the environment from a fresh clone with:

```bash
cd ~/storyweavers
python3 -m venv training/storyworld_chat/.venv
training/storyworld_chat/.venv/bin/python -m pip install --upgrade pip setuptools wheel
training/storyworld_chat/.venv/bin/python -m pip --isolated install \
  --index-url https://pypi.org/simple \
  -r training/storyworld_chat/requirements.txt
```

The explicit PyPI index and isolated mode avoid an unreachable NVIDIA extra
index configured on the current host. Transformers must remain below version 5
unless `train_chat.py` is updated for the newer `TrainingArguments` API.

### Verified Training Runs

Generated data, tokenizers, and model outputs below are intentionally ignored by
Git and currently live only on `pi`.

| Run | Train/eval rows | Steps | Time | Result |
| --- | ---: | ---: | ---: | --- |
| `outputs/smoke-20m-v4` | 39 / none | 10 | 3.8s | End-to-end 14.6M wiring smoke passed. |
| `outputs/chat60m-100w` | 1,572 / 308 | 50 | 13.8s | Best bounded generalization check; final eval loss 6.223. |
| `outputs/chat60m-100w-10ep` | 1,572 / 308 | 500 | 102s | Deliberate overfit check; train loss 0.06, eval loss 6.745. |

The bounded chat run used 100 shuffled training worlds and 20 disjoint eval
worlds from the repaired 5k batch. The small-corpus tokenizer reached 7,263
tokens, so the nominal 60M config instantiated 55,452,160 parameters. The
10-epoch model nearly reproduced seen stories but still drifted on names; on
unseen worlds it produced story-shaped but grammatically weak text. This proves
the training path works, while also showing that repeating a narrow slice is not
a substitute for the broad corpus.

The current one-sample execution audit found:

| Scope | Materialized scripts | Runnable | Emitted a story row |
| --- | ---: | ---: | ---: |
| All folders, including temporary and copied versions | 14,894 | 11,524 | 11,522 |
| Six high-value batches listed in `storyworlds/BATCH_CATALOG.md` | 8,200 | 6,993 | 6,992 |

The 6,992 emitting high-value scripts have no exact source duplicates. One
sample from each totals about 2.85M estimated tokens. The full export should
still oversample each script, deduplicate rendered stories, shuffle, and cap at
250 as described below; do not extrapolate the one-sample audit as the final
training row count.

### Production Corpus And Run (2026-09-04)

The first full corpus is materialized on `pi` under
`training/storyworld_chat/data/production_20260904/`. Generated data is ignored
by Git, while the commands and finalizer are tracked here.

| Split | Selected worlds | Successful worlds | Rows | Exact tokens | Mean tokens | Disk |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| train | 6,642 | 6,516 | 596,966 | 410,187,389 | 687.12 | 2.2 GB |
| dev | 350 | 339 | 31,435 | 21,694,272 | 690.13 | 117 MB |

The split seed is `20260904`; train and dev have zero world overlap and zero
exact-conversation overlap. Each world was asked for 100 samples, then rendered
stories were deduplicated and shuffled within that world. This yielded 531,850
distinct train samples from 553,982 raw samples; multiturn packing produced the
larger row count. All rows use the production 16k tokenizer, fit within 1,024
tokens, alternate valid chat roles, end with an assistant turn, and have unique
IDs. Finalization found no exact duplicate conversations. It rewrote 4,996
colliding train IDs and 269 colliding dev IDs without changing their messages.

A Unicode audit found 724 train rows (456,411 tokens) containing accidental
Cyrillic substitutions from 12 source worlds. Those rows were excluded during
finalization; the final train/dev files contain no Cyrillic, runtime traceback,
or code-fence rows. The original shards and pre-finalization files remain in
the production directory for audit and recovery.

Final artifact checksums:

- train SHA-256: `3bf0324ba049e1db5a81e7238b70ee8b44028d164c82729f486e8a3e3ee72b76`.
- dev SHA-256: `16c086d208fe546f862d5c3553ce175162e7ea9deb41ec8772dface4063a1e02`.

The clean train artifact was assembled with:

```bash
python training/storyworld_chat/finalize_chat_jsonl.py \
  training/storyworld_chat/data/production_20260904/train.part??.jsonl \
  --exclude-message-regex '[\u0400-\u04ff]' \
  --max-context-tokens 1024 \
  --out training/storyworld_chat/data/production_20260904/train.jsonl \
  --manifest training/storyworld_chat/data/production_20260904/train.final.manifest.json
```

Git LFS snapshots are stored in `training/storyworld_chat/data_archives/`:

- `storyworld_chat_production_20260904_corpus.tar.gz` contains the clean
  train/dev JSONL plus split, export, failure, and finalization metadata.
- `storyworld_chat_production_20260904_tokenizer.tar.gz` contains the tokenizer
  source export, its report/manifest, and the finalized 16k tokenizer.
- `SHA256SUMS` records archive checksums. Run `git lfs pull` before extraction,
  then `sha256sum -c training/storyworld_chat/data_archives/SHA256SUMS` from the
  repository root.

The production tokenizer is
`training/storyworld_chat/tokenizers/storyworld-16k-production` and contains
exactly 16,000 tokens. The two-epoch 60M run writes to
`training/storyworld_chat/outputs/storyworld-60m-production-20260904-2ep`.
At launch it scheduled 4,664 optimizer steps, with loss falling from 9.3234 at
step 10 to 7.8997 at step 30. It used about 10.7 GB of GPU memory and sustained
about 2.2 seconds per step.

Launch command:

```bash
training/storyworld_chat/.venv/bin/python \
  training/storyworld_chat/train_chat.py \
  --train-jsonl training/storyworld_chat/data/production_20260904/train.jsonl \
  --eval-jsonl training/storyworld_chat/data/production_20260904/dev.jsonl \
  --tokenizer training/storyworld_chat/tokenizers/storyworld-16k-production \
  --output-dir training/storyworld_chat/outputs/storyworld-60m-production-20260904-2ep \
  --config training/storyworld_chat/configs/storyworld_60m_1024.json \
  --num-train-epochs 2 \
  --per-device-train-batch-size 8 \
  --per-device-eval-batch-size 8 \
  --gradient-accumulation-steps 32 \
  --learning-rate 3e-4 \
  --logging-steps 10 \
  --eval-steps 1000 \
  --save-steps 1000 \
  --save-total-limit 3 \
  --bf16 \
  --report-to tensorboard
```

## 1. Export StoryWorld Chat JSONL

Small smoke export with separate one-turn rows:

```bash
./.venv/bin/python training/storyworld_chat/export_openai_chat_jsonl.py \
  --worlds-dir storyworlds/worlds \
  --samples-per-world 2 \
  --max-worlds 3 \
  --tasks story story_qa \
  --out training/storyworld_chat/data/storyworld_smoke.jsonl \
  --manifest training/storyworld_chat/data/storyworld_smoke.manifest.json
```

Packed multiturn smoke export:

```bash
./.venv/bin/python training/storyworld_chat/export_openai_chat_jsonl.py \
  --worlds-dir storyworlds/worlds \
  --samples-per-world 2 \
  --max-worlds 3 \
  --tasks story story_qa \
  --row-mode multiturn \
  --max-context-tokens 1024 \
  --out training/storyworld_chat/data/storyworld_smoke_multiturn.jsonl \
  --manifest training/storyworld_chat/data/storyworld_smoke_multiturn.manifest.json \
  --report training/storyworld_chat/data/storyworld_smoke_multiturn.report.md
```

Larger training export, packing each story plus as many follow-up QA turns as
fit in the context.  Use the real tokenizer after it exists so the manifest
reports exact token counts and context utilization:

```bash
./.venv/bin/python training/storyworld_chat/export_openai_chat_jsonl.py \
  --worlds-dir storyworlds/worlds \
  --recursive \
  --samples-per-world 1000 \
  --tasks story story_qa \
  --row-mode multiturn \
  --max-context-tokens 1024 \
  --world-qa-mode global \
  --world-qa-pool-samples-per-world 1 \
  --world-qa-max-per-sample 3 \
  --tokenizer /data/storyworld_chat/tokenizer-16k \
  --jobs 16 \
  --timeout 180 \
  --seed 20260621 \
  --out /data/storyworld_chat/train.jsonl \
  --manifest /data/storyworld_chat/train.manifest.json \
  --report /data/storyworld_chat/train.report.md
```

Notes:

- `--recursive` includes generated batch subdirectories under
  `storyworlds/worlds/`; omit it to use only the curated top-level worlds.
- For a specific generated run, point `--worlds-dir` at that materialized folder
  instead of using `--recursive`. For example, the current repaired 5k puddles
  run lives at
  `storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000`.
- Use `--start-world` plus `--max-worlds` to export repeatable chunks from the
  sorted world list. Example chunk 0:

  ```bash
  ./.venv/bin/python training/storyworld_chat/export_openai_chat_jsonl.py \
    --worlds-dir storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000 \
    --shuffle-worlds \
    --start-world 0 \
    --max-worlds 500 \
    --samples-per-world 1000 \
    --dedupe-story-samples \
    --shuffle-samples \
    --sample-cap-per-world 250 \
    --tasks story story_qa \
    --row-mode multiturn \
    --max-context-tokens 2048 \
    --jobs 50 \
    --timeout 90 \
    --seed 20260626 \
    --out training/storyworld_chat/data/gpt54mini_5k_chunk000_500w_x1000_cap250.jsonl \
    --manifest training/storyworld_chat/data/gpt54mini_5k_chunk000_500w_x1000_cap250.manifest.json \
    --report training/storyworld_chat/data/gpt54mini_5k_chunk000_500w_x1000_cap250.report.md
  ```

  For chunk 1, keep the same `--seed`, change `--start-world 500`, and update
  the output names; for chunk 2, use `--start-world 1000`, and so on. The
  shuffle avoids alphabetic chunks that overrepresent broken filename clusters.
  `--samples-per-world 1000 --dedupe-story-samples --shuffle-samples
  --sample-cap-per-world 250` treats `1000` as an oversampling budget: the
  exporter removes duplicate rendered stories per script, shuffles the surviving
  samples deterministically, then keeps at most 250 samples from that world.
  This caps prolific scripts without penalizing worlds whose valid parameter
  space is smaller.  It does not dedupe repeated QA turns inside otherwise
  unique story conversations; use the duplicate tables in the report to decide
  whether to downweight, omit, or post-filter QA-heavy rows.
- The story prompt comes from the StoryWorld sample's `prompts` field by
  default, plus serialized params when `--user-format prompt+params` is used.
  This is not reading an external TinyStories prompt JSON.
- `--row-mode single`: `story` emits one chat row asking for the story, and
  `story_qa` emits one chat row per story-grounded QA item.
- `--row-mode multiturn`: emits one chat row containing a story request, the
  generated story, and as many follow-up QA turns as fit under
  `--max-context-tokens`.
- `--world-qa-mode own|global|mixed` controls where world-knowledge turns come
  from in multiturn packing.  `global` does a small prepass, dedupes world QA
  pairs across worlds, then shuffles a few generic questions into each
  conversation.  `mixed` keeps the sample's own world QA and adds a few global
  ones.  Generic world questions are sometimes bare and sometimes get a short
  preamble such as `Quick question:` or `Different question:`.
- Pass `--tokenizer /path/to/tokenizer` after tokenizer training to pack with
  exact token counts. Without it, the exporter uses a conservative character
  heuristic so the script remains stdlib-only.
- The manifest and optional markdown report include `token_stats` with total
  estimated tokens, mean utilization, percentiles, rows above target, rows above
  90% target, and rows below 50% target.  They also summarize row/task mix,
  turns per row, assistant turns by task (`story`, `story_qa`, `world_qa`),
  stories that failed to fit, questions that were available/used/skipped, world
  QA pool size/deduplication, random row samples, longest/shortest row samples,
  world failures by kind including timeouts, and duplicate source-content
  counts.  World-knowledge duplicates are reported under
  `world_qa_*_expected` because those are expected to repeat; story and
  story-grounded QA duplicate groups should stay low.
- `world_qa` is available, but keep it separate or downweighted if you want the
  core model to focus on narrative causality.
- Held-out/eval corpora should stay separate, as planned: TinyStories protocol
  data and external QA such as BoolQ should not be mixed into this exporter.

## 2. Train Tokenizer

```bash
python training/storyworld_chat/train_tokenizer.py \
  --input /data/storyworld_chat/train.jsonl \
  --out /data/storyworld_chat/tokenizer-16k \
  --vocab-size 16000
```

The tokenizer script writes a tokenizer with a ChatML-style template:
`<|im_start|>role\ncontent<|im_end|>`.

## 3. Sizing Notes For The First Linux Run

Current working assumptions, based on the repaired generated worlds and the
`gpt54mini_5k_dedup_probe_5w_x1000_cap250` probe:

- Export plan: ask each script for `--samples-per-world 1000`, dedupe rendered
  stories, deterministically shuffle, then keep `--sample-cap-per-world 250`.
- Expected yield: roughly 100 unique story rows per script on average. Some
  worlds have more and get capped; some have much smaller parameter spaces or
  repair defects and contribute less.
- Corpus scale: around `8,000 * 100 = 800,000` story conversations.
- Token estimate with story plus ordinary story/world QA, no extra QA
  oversampling: about `0.5B` tokens. The probe averaged about 700 estimated
  tokens per packed row.
- JSONL disk estimate: about 5.1 bytes per estimated token, so `0.5B` tokens is
  roughly 2.5-3 GB of training JSONL. Budget 10 GB for JSONL, tokenizer, reports,
  and a few 60M checkpoints; budget 20 GB if keeping many exports/checkpoints.
- Do not oversample world-facts QA for the first run. It roughly doubles the
  token budget and the repeated QA turns are more repetitive than the stories.

Useful first-pass export shape on the Linux box:

```bash
python training/storyworld_chat/export_openai_chat_jsonl.py \
  --worlds-dir storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000 \
  --shuffle-worlds \
  --start-world 0 \
  --max-worlds 8000 \
  --samples-per-world 1000 \
  --dedupe-story-samples \
  --shuffle-samples \
  --sample-cap-per-world 250 \
  --tasks story story_qa world_qa \
  --row-mode multiturn \
  --max-context-tokens 1024 \
  --jobs 50 \
  --timeout 180 \
  --seed 20260626 \
  --out /data/storyworld_chat/train.jsonl \
  --manifest /data/storyworld_chat/train.manifest.json \
  --report /data/storyworld_chat/train.report.md
```

After tokenizer training, rerun the same export with
`--tokenizer /data/storyworld_chat/tokenizer-16k` if exact token packing/stats
matter. The first export without a tokenizer is usually good enough to train the
tokenizer itself.

## 4. Train Model

Tiny smoke ladder configs are also included:

- `configs/storyworld_20m_1024.json`: quick wiring and overfit checks.
- `configs/storyworld_60m_1024.json`: recommended first real 4090 run.
- `configs/storyworld_125m_1024.json`: next step if 60M clearly underfits.

All three use the same 16k tokenizer by default.  Smaller model size does not
require a smaller tokenizer; if you do try an 8k tokenizer for the 20M smoke
model, expect slightly more tokens for the same text and regenerate the packed
JSONL with that tokenizer before comparing runs.

Single RTX 4090, recommended 60M / 2 epoch run:

```bash
python training/storyworld_chat/train_chat.py \
  --train-jsonl /data/storyworld_chat/train.jsonl \
  --eval-jsonl /data/storyworld_chat/dev.jsonl \
  --tokenizer /data/storyworld_chat/tokenizer-16k \
  --output-dir /data/storyworld_chat/outputs/storyworld-60m \
  --config training/storyworld_chat/configs/storyworld_60m_1024.json \
  --num-train-epochs 2 \
  --per-device-train-batch-size 8 \
  --gradient-accumulation-steps 32 \
  --bf16
```

For 60M on a 24 GB 4090, try without `--gradient-checkpointing` first; it should
usually fit and train faster. If memory is tight, add `--gradient-checkpointing`.
At `0.5B` tokens, 2 epochs is about `1.0B` token exposures. With the command
above, that is roughly 4k-6k optimizer steps depending on padding. Practical
wall-clock estimate on a 4090 is about 4-8 hours, so budget an overnight run.

DGX 8xH100:

```bash
torchrun --nproc_per_node=8 training/storyworld_chat/train_chat.py \
  --train-jsonl /data/storyworld_chat/train.jsonl \
  --eval-jsonl /data/storyworld_chat/dev.jsonl \
  --tokenizer /data/storyworld_chat/tokenizer-16k \
  --output-dir /data/storyworld_chat/outputs/storyworld-125m \
  --config training/storyworld_chat/configs/storyworld_125m_1024.json \
  --per-device-train-batch-size 32 \
  --gradient-accumulation-steps 1 \
  --bf16
```

Both commands target roughly 262k tokens per optimizer step:

- 4090: `8 * 1024 * 32`
- DGX: `32 * 1024 * 8`

Use TinyStories and BoolQ as separate eval suites.  This scaffold only builds
the StoryWorld training feed and intrinsic chat-loss validation.

## 5. Held-Out Vibe Test

`vibe_test.py` runs a human-readable checkpoint comparison against frozen dev
prompts. It scores both generated stories and held-out reference stories with
the same fixed-baseline rubric as `storyworlds/openai_story_quality.py`:
coherence, style, grammar, storytelling, and overall, each from 0 to 9. The
default judge is always `gpt-5.4-mini` on the `flex` service tier.

Freeze the prompt set once. Reservoir sampling is uniform over eligible dev
rows and records the original dev line and prompt hash:

```bash
training/storyworld_chat/.venv/bin/python \
  training/storyworld_chat/vibe_test.py sample \
  --dev-jsonl training/storyworld_chat/data/production_20260904/dev.jsonl \
  --count 16 \
  --seed 20260905 \
  --out training/storyworld_chat/vibe_runs/dev16_seed20260905.prompts.jsonl
```

Generate against one or more checkpoints. Greedy decoding is the default so a
checkpoint gives repeatable output; pass `--temperature 0.7` for an explicitly
sampled companion run.

```bash
training/storyworld_chat/.venv/bin/python \
  training/storyworld_chat/vibe_test.py generate \
  --prompts-jsonl training/storyworld_chat/vibe_runs/dev16_seed20260905.prompts.jsonl \
  --model step3000=training/storyworld_chat/outputs/storyworld-60m-production-20260904-2ep/checkpoint-3000 \
  --model final=training/storyworld_chat/outputs/storyworld-60m-production-20260904-2ep \
  --batch-size 8 \
  --max-new-tokens 768 \
  --bf16 \
  --out training/storyworld_chat/vibe_runs/dev16_seed20260905.generations.jsonl
```

Judge on the Linux box, then produce the compact summary and the full prompt,
reference, generation, and score report:

```bash
OPENAI_API_KEY="$(cat .API_KEY)" \
training/storyworld_chat/.venv/bin/python \
  training/storyworld_chat/vibe_test.py judge \
  --generations-jsonl training/storyworld_chat/vibe_runs/dev16_seed20260905.generations.jsonl \
  --judge-model gpt-5.4-mini \
  --service-tier flex \
  --concurrency 16 \
  --out training/storyworld_chat/vibe_runs/dev16_seed20260905.ratings.jsonl

training/storyworld_chat/.venv/bin/python \
  training/storyworld_chat/vibe_test.py report \
  --ratings-jsonl training/storyworld_chat/vibe_runs/dev16_seed20260905.ratings.jsonl \
  --out training/storyworld_chat/vibe_runs/dev16_seed20260905.report.md
```

To test another epoch or optimizer step, reuse the same `*.prompts.jsonl` and
give its model path a new label. Use a separate generation file, or `--append`
only when the label is new. Reusing the frozen prompts is what makes checkpoint
deltas meaningful; changing the seed creates a new suite rather than extending
the old one.

## 6. Matched TinyStories Control Corpus

`export_tinystories_chat_jsonl.py` builds a data-quality control run using the
official TinyStories metadata archive. Unlike the text-only Parquet release,
`TinyStories_all_data.tar.gz` preserves each story's original instruction,
three required words, optional features, summary, and source model. The exporter
defaults to GPT-4 stories and places the original request inside StoryWorld's
exact `Task: write_story`, `Prompt:`, and `Params:` envelope.

It deliberately uses the existing production 16k tokenizer and defaults to the
exact production train/dev token budgets. This keeps tokenizer IDs, model
architecture, chat format, optimizer setup, token exposure, and `vibe_test.py`
checkpoint loading compatible. Splits are assigned by a seeded story-content
hash, and exact story duplicates cannot cross splits.

```bash
wget -c -O training/storyworld_chat/source_data/tinystories/TinyStories_all_data.tar.gz \
  'https://huggingface.co/datasets/roneneldan/TinyStories/resolve/main/TinyStories_all_data.tar.gz?download=true'

training/storyworld_chat/.venv/bin/python \
  training/storyworld_chat/export_tinystories_chat_jsonl.py \
  --archive training/storyworld_chat/source_data/tinystories/TinyStories_all_data.tar.gz \
  --tokenizer training/storyworld_chat/tokenizers/storyworld-16k-production \
  --train-target-tokens 410187389 \
  --dev-target-tokens 21694272 \
  --source gpt4 \
  --seed 20260905 \
  --train-out training/storyworld_chat/data/tinystories_gpt4_matched/train.jsonl \
  --dev-out training/storyworld_chat/data/tinystories_gpt4_matched/dev.jsonl \
  --manifest training/storyworld_chat/data/tinystories_gpt4_matched/export.manifest.json
```

Train from scratch with the same production command, changing only the input
and output paths. TinyStories rows are about half as long, so accumulation is
doubled to 64 to preserve approximately the same non-padding tokens per optimizer
update and nearly the same update count over two epochs:

```bash
training/storyworld_chat/.venv/bin/python \
  training/storyworld_chat/train_chat.py \
  --train-jsonl training/storyworld_chat/data/tinystories_gpt4_matched/train.jsonl \
  --eval-jsonl training/storyworld_chat/data/tinystories_gpt4_matched/dev.jsonl \
  --tokenizer training/storyworld_chat/tokenizers/storyworld-16k-production \
  --output-dir training/storyworld_chat/outputs/tinystories-gpt4-60m-matched-ga64-2ep \
  --config training/storyworld_chat/configs/storyworld_60m_1024.json \
  --num-train-epochs 2 \
  --per-device-train-batch-size 8 \
  --per-device-eval-batch-size 8 \
  --gradient-accumulation-steps 64 \
  --learning-rate 3e-4 \
  --logging-steps 10 \
  --eval-steps 500 \
  --save-steps 500 \
  --save-total-limit 20 \
  --bf16 \
  --report-to tensorboard
```

The resulting checkpoints can be passed directly to `vibe_test.py generate`
against the frozen StoryWorld dev prompts. Because plain TinyStories has no QA
turns, this control isolates story generation quality; it does not test whether
the model learned StoryWorld's follow-up QA behavior.

### Materialized Control And Distribution Difference

The GPT-4-only control was materialized on `pi` on 2026-09-05. Both files are
within one context window of their StoryWorld token targets, their checksums
match the export manifest, and a full audit found no repeated ID, repeated
story, cross-split story, or invalid role sequence.

| Measure | StoryWorld production | TinyStories GPT-4 control |
| --- | ---: | ---: |
| Train tokens | 410,187,389 | 410,186,394 |
| Dev tokens | 21,694,272 | 21,693,263 |
| Train rows | 596,966 | 1,132,573 |
| Dev rows | 31,435 | 59,945 |
| Mean train row tokens | 687.12 | 362.17 |
| Mean base story conversation tokens | 373.48 | 362.17 |
| Mean assistant turns per packed train row | 8.14 | 1.00 |
| Distinct train story samples | about 531,850 | 1,132,573 |
| Story source | executable StoryWorld scripts | GPT-4 |
| Follow-up QA | story QA plus world QA | none |

The close base-story lengths make this a useful end-to-end data-distribution
control. It is not a pure prose-quality ablation: at the same total token count,
TinyStories supplies about twice as many distinct stories, while StoryWorld
spends roughly half its corpus on millions of short QA turns. A later ablation
can equalize story count or add matched QA if this run shows a large advantage.

The matched run uses 64-way accumulation, schedules 4,426 optimizer steps over
two epochs, and evaluates/saves every 500 steps. The corresponding StoryWorld
run scheduled 4,664 steps. Using accumulation 32 would schedule 8,850 updates
for the shorter TinyStories rows and would confound data quality with twice as
many parameter updates.
