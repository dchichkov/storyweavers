# Storypatches

An isolated authoring experiment:

1. a deterministic seed selects three required CHILDES words, 3–5 compatible
   kernels, a beginning, ending, basic plot, ATU type, genre, situation, and
   location;
2. Luna/Flex writes an outline, six-section story, and grounded conversational
   Q&A;
3. Luna produces 100 independent edits through one synthetic OpenAI custom text
   tool named `apply_patch`;
4. local code applies compatible sets of 3–5 patches to make 100 unique variants;
5. deterministic QA checks and the existing Terra story-set judge evaluate them.

Patch calls have no read, write, shell, or search tools. Each call receives the
complete base bundle in a stable cached prefix and must finish with one
`apply_patch` tool call. The tool only returns text; `storypatches` parses,
validates, and applies it locally. OpenCode is neither imported nor invoked.

## Setup and tests

From the repository root:

```bash
./.venv/bin/pip install -r storyscenes/requirements-authoring.txt
./.venv/bin/python -m unittest storypatches.test_storypatches
```

## Inspect requests without an API call

```bash
./.venv/bin/python -m storypatches.pipeline \
  --out storypatches/runs/dry_run --seed 42 --count 2 --dry-run
```

## Author and evaluate

This makes at least 103 paid Luna calls per base story: outline, prose,
conversations, and 100 patches. Known-invalid returned patches may use a bounded
replacement call. The first patch request warms the explicit 30-minute cache;
the rest share exactly the same prefix and cache key.

```bash
OPENAI_API_KEY=... ./.venv/bin/python -m storypatches.pipeline \
  --out storypatches/runs/trial_01 \
  --campaign storypatches/campaigns/trial_01 \
  --seed 42 --count 1 --variants 100 --evaluate
```

Use `--api-key-file PATH` instead of the environment variable if needed.
`--cache-mode legacy` is available for clients/models without explicit cache
breakpoints. There is no automatic fallback after a dispatched request.

For a local OpenAI-compatible Responses endpoint, the pipeline appends `/v1`
when it is absent, does not require an API key, and omits OpenAI-only Flex,
reasoning, and prompt-cache fields:

```bash
./.venv/bin/python -m storypatches.pipeline \
  --base-url http://127.0.0.1:8001/ \
  --model Qwen/Qwen3.8-27B-FP8 \
  --out storypatches/runs/qwen_debug --count 1 --variants 100
```

Custom endpoints default to `--cache-mode off`; override it only if the server
implements the corresponding cache fields. The server must implement the
Responses API, strict JSON-schema output, and custom text tools. A
Chat-Completions-only endpoint is not sufficient for this pipeline.

An interrupted request leaves its request file without a response and is not
silently retried. Put an empty `STOP` file in the run directory to block new
dispatches. Outputs include every frozen request/response, base bundle, patch
attempt, accepted patch, conflict graph, variants, QA metrics, token cost, and
evaluation artifacts.
