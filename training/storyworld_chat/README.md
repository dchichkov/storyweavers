# StoryWorld Chat Training Scaffold

This directory contains a small from-scratch training setup for StoryWorld
models.  The data format is OpenAI-compatible chat JSONL:

```json
{"messages":[{"role":"system","content":"..."},{"role":"user","content":"..."},{"role":"assistant","content":"..."}],"metadata":{"task":"story"}}
```

The scripts are intentionally light on assumptions.  The exporter is stdlib-only
and samples `storyworlds/worlds/*.py`; the tokenizer/trainer scripts are for the
target Ubuntu/DGX machines and import optional ML dependencies only when run.

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
