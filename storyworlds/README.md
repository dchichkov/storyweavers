# Storyworlds

`storyworlds/` holds standalone simulated story sketches. Each script in
`worlds/` models one small story domain with typed state, a reasonableness gate,
grounded Q&A, and an inline ASP twin for self-checking.

For authoring rules, use [`STORY.md`](STORY.md). This README is for practical
workflow notes that are useful to humans coordinating batches of worlds.

## Puddles Generation Example

`worlds/puddles.py` demonstrates eight causal paths from four problems and their
compatible responses. `--problem` selects `temptation`, `splash`, `wrong_cover`,
or `missing_gear`; `--solution` selects a compatible response. Unspecified
choices are sampled reproducibly.

The example predicts on a copy, executes actions in the real world, and records
events for prose and QA. Washing clears an actual cleaning debt; changing
clothes stores the original item without making old clothes waterproof. A dry
game creates a drawing without pretending the messy activity took place.
Short comments explain these decisions so a code-generation model can follow
the reasoning while emitting source. Tests check event paths and final state,
not only unique strings or a passing ASP gate.

```bash
./.venv/bin/python storyworlds/worlds/puddles.py --all --qa
./.venv/bin/python storyworlds/worlds/puddles.py --problem splash --solution change --trace --qa
./.venv/bin/python storyworlds/worlds/puddles.py --verify
./.venv/bin/python storyworlds/test_puddles.py
```

## Dialogue Examples

Three standalone, hand-authored references put conversation at the center of
the action:

- [Library Words](worlds/library_words_dialogue.py): clarify an ambiguous request
  and use what the other character says to recover a page, book, or shared reading.
- [One Cart, Two Plans](worlds/one_cart_dialogue.py): negotiate conflicting needs,
  agree on a workable plan, then actually deliver both loads.
- [Bridge Builders](worlds/bridge_builders_dialogue.py): disagree, inspect a failed
  design, explain a revision, and test the repaired bridge.

[Read three complete stories with QA](DIALOGUE_SAMPLES.md). Each script has three
core problems and two conversation approaches (`ask` or `guess`). Dialogue
transfers character beliefs; domain actions change physical state; QA comes from
the recorded events. These are conversation examples, not large independent
plot spaces. The [local sampling audit](batches/dialogue_examples_20260907.report.md)
includes dialogue counts, duplicate rates, and compression.

```bash
./.venv/bin/python storyworlds/worlds/library_words_dialogue.py --all --qa
./.venv/bin/python storyworlds/worlds/one_cart_dialogue.py --problem gate --approach guess --qa
./.venv/bin/python storyworlds/worlds/bridge_builders_dialogue.py --problem short --approach ask --trace --qa
env PYTHONPATH=storyworlds ./.venv/bin/python -m unittest storyworlds/test_dialogue_worlds.py
```

The generation factory can use these by name through `--example-worlds library`,
`cart`, or `bridge`, or through `--example-file <path>`. All three are now in the
`dialogue_v2` canonical comparison below. The standalone factory default still
means Puddles + Pirates. No generation or judge API was used to author or check
these examples; their prior local audit remains historical, not a judged rating.

## Nell and the Dragon

[nell_and_the_dragon.py](worlds/nell_and_the_dragon.py) adapts the supplied
Nell/dragon/magpie story. The default keeps Nell, the emerald, the brass button,
and the promised payment in true stories. Short alternating dialogue drops
redundant speaker tags while preserving speaker identities in the trace.

The bird's preference, carrying capacity, the dragon's distance, visible teeth,
and noise govern whether she takes an offer. Taking it does not return the
jewel: she must carry it to the nest and install it before the dragon can catch
the displaced jewel. Ownership and the intact nest/tree are checked at the end.
The payment remains a promise, not a story falsely reported as already told.

```bash
# Faithful default adaptation, with grounded QA.
./.venv/bin/python storyworlds/worlds/nell_and_the_dragon.py --qa

# A different need changes which object works and why the jewel is discarded.
./.venv/bin/python storyworlds/worlds/nell_and_the_dragon.py --need fasten --approach hasty --qa
./.venv/bin/python storyworlds/worlds/nell_and_the_dragon.py --all --qa
./.venv/bin/python storyworlds/worlds/nell_and_the_dragon.py --verify
env PYTHONPATH=storyworlds ./.venv/bin/python -m unittest storyworlds/test_nell_and_the_dragon.py
```

`--need` selects `shine`, `fasten`, or `softness`; compatible dishes supply a
button, a wire loop, or wool. `--approach hasty` adds a failed visit caused by the
dragon advancing too soon. These are **six variants of one plot**, not six
independent plots. `--all` holds names and jewel fixed; `-n` greater than one
samples names, jewels, needs, and approaches reproducibly with `--seed`.
An incompatible explicit `--solution` is rejected. The bird's preferences are
fictional individual traits, not zoological claims about magpies.

The [Terra/Flex protocol evaluation](batches/nell_dragon_quality_20260907.report.md)
rated all ten sampled stories **9/9 overall**, but set diversity **1/9**.
Only 72 of 1,000 story strings are distinct; the geometric dataset score is
**1.45/100**. This is a strong prose reference with a deliberately small plot
space, not a large training contribution.

### Nell V2: State and Telling

[nell_and_the_dragon_v2.py](worlds/nell_and_the_dragon_v2.py) is a separate
prototype; the evaluated original above remains unchanged. [Four complete
samples](NELL_V2_SAMPLES.md) compare two tellings of identical events, a nest
repair, and an ownership discovery. The v1 judge score does **not** apply to v2.

The bounded policy selects eligible actions from character knowledge and
physical state. Questions establish the jewel's origin; observation reveals
whether it is an ornament or a structural support. Materials may need fetching,
polishing, or assembly. The four resolutions are an exchange, an explicit
return request after the bird keeps both ornaments, a tested cooperative nest
repair, and recognizing a gift that should remain with the bird.

Prose is rendered separately from the recorded events. `--prose-seed` changes
authored wording and complete dialogue exchanges, never ownership, actions,
outcomes, or QA answers. There is no blind thesaurus replacement. `--voice`
selects `plain`, `dry`, or `playful`; `--dialogue-level` selects `spare`,
`balanced`, or `conversational`; `--detail-level` selects `compact`, `normal`,
or `rich`. `--flourish-budget` caps optional embellishment blocks; compact
suppresses them. Currently only two event types have such blocks, so a budget
of five does not promise five additions. Essential dialogue and evidence remain
even in spare mode; QA wording deliberately stays stable across retellings.

```bash
# Same world and events, different tellings.
./.venv/bin/python storyworlds/worlds/nell_and_the_dragon_v2.py --world-seed 777 --prose-seed 1 --qa
./.venv/bin/python storyworlds/worlds/nell_and_the_dragon_v2.py --world-seed 777 --prose-seed 2 --voice plain --dialogue-level spare --detail-level compact --flourish-budget 0 --qa

# Change the actual problem or resolution.
./.venv/bin/python storyworlds/worlds/nell_and_the_dragon_v2.py --use support --supplies raw --qa
./.venv/bin/python storyworlds/worlds/nell_and_the_dragon_v2.py --nest-slots 2 --supplies home --qa
./.venv/bin/python storyworlds/worlds/nell_and_the_dragon_v2.py --owner bird --qa
./.venv/bin/python storyworlds/worlds/nell_and_the_dragon_v2.py --verify
env PYTHONPATH=storyworlds ./.venv/bin/python -m unittest storyworlds/test_nell_and_the_dragon_v2.py
```

For a single story, unspecified world parameters use stable defaults and
`--world-seed` controls ordering among eligible investigative actions. With
`-n > 1`, `--seed` (alias `--world-seed`) also samples unspecified world
parameters; per-sample world and prose seeds advance independently. `--all`
enumerates eight use/owner/display-space configurations, not eight unique plots;
other fields remain at defaults unless specified. Some settings become irrelevant
once a gift is recognized. The model is a small fictional domain policy, not a
general planner or a claim about real bird behavior.

The [matched local audit](batches/nell_dragon_v2_20260907.report.md) retained three
1,000-sample controls and a historical v1 pool. V2 has 999/1,000 exact unique
texts, four resolution types, and 22 coarse event-dependency signatures in the
mixed pool. But **one unchanged world also gives 1,000 unique tellings**: neither
exact dedup nor slot normalization establishes meaningful plot diversity.
Story-only XZ/raw is still 2.33%; cross-story compression retention after dedup
is 4.82%. No new API judging was performed. Local batches, source snapshots,
traces, and compression data are retained in the linked report's archive.

## Canonical Prompt Trials

New generation prompts require a brief, consequential spoken exchange in every
sample, regardless of whether the seed explicitly includes `Dialogue`. This is
in [`STORY.md`](STORY.md#story-quality), embedded by the shared prompt builder
for batch, direct-service, and canonical-trial generation. Inner monologue and
quoted notes do not qualify. Prompt protocol `custom_tool_python_v11` introduces
this requirement **after** the measured dialogue-v2 baseline below. Seed tasks
and their feature-sampling distribution are unchanged. The [matched paid v11 trial](batches/dialogue_required_v11_20260907.report.md)
is complete: quoted text rose from 17.7% to 34.0%, quality from 6.41 to 6.92/9,
but semantic diversity stayed at 1.19/9 and the geometric score fell from 6.26
to 5.91/100. All 21 final scripts pass after ten separately recorded manual
recoveries; estimated API spend was $0.3195. More dialogue did not fix template
collapse or make the entire output pool training-ready.

The [three sequential prompt trials](batches/prompt_optimization_20260907.report.md)
preserve separate automatic and manually assisted results. Protocol v12 moves
explicit addenda after examples and seed fields; it does not change the vanilla
prompt text or enable any candidate by default. Frozen older requests retain
their original prompts.
All three trials are complete (63 worlds, 630 Terra story ratings, about $0.89).
R1 raises the assisted composite to 7.62; R3 improves quality to 7.16/9 but
collapses to 3,032 unique texts from 21,000 draws. None beats the previous
baseline's automatic-only composite, so no candidate is promoted by default.

The current reference set is **Puddles, Pirates, Garnet, Library Words,
One Cart, Bridge Builders, Nell v2**, version **`dialogue_v2`**. The latest
Puddles is retained unchanged. These are generation references, not claims that
each is an ideal training-data generator. Their source paths live in
[`canonical_examples.py`](canonical_examples.py).

The [curation record](batches/canonical_dialogue_v2_20260907.report.md) explains
the replacements: Quesadilla, Thud, Dining, and Grocery leave the default matrix
to make room for clarification, negotiation, physical repair, and questioning
ownership through dialogue. The four retired names still work when explicitly
selected. All three factory/pipeline CLIs accept `--example-worlds library`,
`cart`, `bridge`, `nell`, etc.; `nell` is the new v2, not the original adaptation.
The legacy `all` selection still means Puddles + Pirates, not all seven.

New trial manifests and compression reviews record the reference-set version.
Previously prepared requests and old evaluation reports are not rewritten, and
the old seven-world Terra baseline does not rate this new set. Use a new trial
name for the new matrix. The [first live 21-world baseline](batches/dialogue_v2_baseline_20260907.report.md)
is complete: 11 raw runnable, 14 after automatic repair, and 21 after separately
recorded manual recovery. Terra judged ten stories per world: **6.41/9 quality,
1.19/9 semantic diversity**, geometric score **6.26/100**. All 21 final scripts
pass verification and standalone execution, but story and QA defects remain.
The 20,915 returned stories compress together to **1.94%** of story-text bytes;
exact dedup leaves 11,637 texts. Raw and repaired artifacts remain separate.

[`prompt_trials.py`](prompt_trials.py) automates **7 examples x 3 matched seed
tasks = 21 generated worlds**, with one reference per request:

```bash
# Local only: freeze all 21 exact request bodies and source snapshots.
./.venv/bin/python storyworlds/prompt_trials.py prepare dialogue_trial_01 --seed 2026090605

# Estimate generation and ten-story Terra judging costs; no API calls.
./.venv/bin/python storyworlds/prompt_trials.py cost dialogue_trial_01

# Paid generation + deterministic repair + local diversity checks + Terra judge.
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/prompt_trials.py run dialogue_trial_01

# Preserve everything, including raw and repaired sources, in an LFS-ready tar.gz.
./.venv/bin/python storyworlds/prompt_trials.py archive dialogue_trial_01
```

Defaults: Luna / no reasoning / Flex, global concurrency 5, Terra / no reasoning /
Flex judge reviewing **10 randomly selected stories together per world**,
and **1,000 local samples per generated world**. The scorecard includes exact
and slot-normalized diversity, story-only LZMA compression before/after dedup,
story/QA lengths, runtime, own verification, and a quality-gated geometric
score: usable unique yield times the geometric mean of quality and pooled
compression retention. `dataset_score.py` defines the versioned score;
`--minimum-quality 6` is the default floor, applied to the mean of ten individual
quality ratings. The judge also scores set-level semantic diversity and groups
stories by causal plot; these diagnostics remain separate from LZMA and the
geometric score. Duplicates are retained in the random judge sample. The older
single-story Mini judge remains available for historical replay.
The first live dialogue-v2 attempt estimates **$0.2925** from returned usage:
**$0.0815 generation + $0.2110 judging**. Earlier reference-based projections
were $0.31-$0.32; keep **$1 per attempt** as practical headroom, not a hard cap.
The seven-world reference judge pass cost $0.0771; its [manual review](batches/canonical_set_quality_20260907.report.md)
is historical calibration, not a direct comparison to generated-world quality.
`cost` reads frozen generation prompts; completed evaluations record returned
usage cost estimates in `costs.json`. No automatic standard-tier fallback.
Evaluations also compress the entire returned corpus together, up to 21,000
stories, with a 64 MiB LZMA2 dictionary. For an API-free audit of the reference
worlds themselves, use `compression_review.py --out <new-directory>`; see the
[initial compression results](batches/canonical_compression_20260907.report.md).
No per-story Markdown files are created. See
[Canonical Trials](QUALITY_ITERATION_PIPELINE.md#canonical-trials) for matched
prompt changes, score definitions, recovery behavior, and artifact locations.

## Subagent Swarm Notes

On 2026-06-16, a 10-task storyworld generation batch was run with Codex
subagents using the `gpt-5.3-codex-spark` model override.

The attempted pattern was:

```text
spawn_agent(
  agent_type="worker",
  model="gpt-5.3-codex-spark",
  message="In /Users/dmitry/storyweavers, create one file only: ..."
)
```

Important findings:

- Explicit `model="gpt-5.3-codex-spark"` worked only when `fork_context` was not
  used. A full-history fork forced inheritance of the parent model/agent type.
- The observed concurrency ceiling was about 6 running subagents. Attempts to
  start all 10 at once produced `agent thread limit reached` for the excess.
- Completed agents still counted against the concurrency limit until closed, so
  closing finished workers was necessary before launching more.
- Long prompts caused some Spark workers to fail with a context-window error.
  Retrying the same assignment with a shorter, self-contained prompt worked.
- The robust pattern was to launch about 6 workers, wait for completions, close
  each completed worker, then refill the pool with the remaining tasks.

The successful short prompt shape was:

```text
In /Users/dmitry/storyweavers, create one file only:
storyworlds/worlds/<name>.py. You are not alone in the codebase; do not revert
others' changes. Follow the storyworld pattern: standalone stdlib script,
imports storyworlds/results.py, StoryParams dataclass, build_parser,
resolve_params, generate, emit, -n, --all, --seed, --trace, --qa, --json,
--asp, --verify, --show-asp. Include Python valid_combos plus inline ASP twin;
--verify must exit 0 using /Users/dmitry/storyweavers/.venv/bin/python. Domain:
<domain>. Final answer: changed file and verification result.
```

After the workers finished, the parent thread re-ran every new world's
`--verify` command directly with `./.venv/bin/python` as a final cross-check.

## Codex SDK One-Shot World Factory

If `openai_codex` is installed in `./.venv`, `codex_world_factory.py` can launch
a single SDK-backed Codex job to create one new world file. It uses the same
one-file prompt shape as the subagent swarm, but sends it through
`AsyncCodex.thread_start(...).run(...)`.

Preview the exact prompt first:

```bash
./.venv/bin/python storyworlds/codex_world_factory.py moss_cookie_v2 \
  --words moss cookie --features misunderstanding kindness --dry-run
```

Omit `--dry-run` to launch the SDK job. Defaults are conservative:
`model=gpt-5.4`, `sandbox=workspace-write`, and `approval-mode=deny_all`.
The generated prompt asks Codex to create exactly
`storyworlds/worlds/<name>.py`, run `--verify`, sample 10 `--qa` stories, check
JSON output, and finish with `git diff --check`.
The helper uses `thread.turn(...).stream()` rather than the convenience
`thread.run(...)`, so long SDK jobs print their thread id, turn id, item
completions, token updates, and final status while they run.

## OpenAI Batch World Factory

`openai_batch_world_factory.py` prepares OpenAI Batch API requests for many
storyworld drafts using `gpt-5.6-luna` by default. Batch jobs cannot edit this
checkout directly, so each request asks the model to call the `emit_python_file`
custom tool with the target path, complete Python source, checks to run, and
quality risks. Older JSON-object results can still be materialized by the
script, but the preferred path is the raw Python tool payload because it avoids
escaping a full source file inside JSON text.

## OpenAI Service World Factory

`openai_service_world_factory.py` generates the same storyworld request shape
with ordinary async Responses API calls instead of Batch. It writes a run
manifest, a raw response JSONL, and a run-specific world directory under
`storyworlds/worlds/`.

Generation defaults to `gpt-5.6-luna`, reasoning effort `none`, and service tier
`flex`. The older direct-service pipeline retains its single-story
`gpt-5.4-mini` judge; canonical `prompt_trials.py` uses the new ten-story Terra
protocol above. Select
`--example-worlds puddles` for the Puddles-only template; the default is still
both examples. No prompt addendum is included unless explicitly supplied.

Use `--example-file storyworlds/worlds/<repaired-world>.py` to replace the
bundled examples with a specific repository source file. Repeat the flag to
include multiple complete examples in each prompt. It is mutually exclusive
with `--example-worlds`. The selected paths are saved in `example_files` in
the manifest, and their contents contribute to the prompt cache fingerprint.
`--from-manifest` restores this selection. Preserve source snapshots alongside
an experiment when the originals may change later.

For the usual generate-plus-eval pass, use the one-command pipeline. It uses the
same prompt text as `openai_batch_world_factory.py` by default, creates the
worlds, runs `openai_story_quality.py`, runs `qa_static_check.py`, and writes a
Markdown report beside the manifest. The service pipeline defaults to 100
storyworlds. Use matched seeds for prompt comparisons, then fresh seeds to
validate the winner. See
[`QUALITY_ITERATION_PIPELINE.md`](QUALITY_ITERATION_PIPELINE.md) for the full
prompt/repair/quality loop:

```bash
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_service_world_pipeline.py \
  --seed <new-seed> --model gpt-5.6-luna --reasoning-effort none --max-output-tokens 32000 \
  --repair-failures
```

For an optimization-loop variant after reading a report, pass a prompt addendum.
Addenda are appended to the exact batch prompt; omit this flag when comparing
against the original batch prompt:

```bash
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_service_world_pipeline.py \
  --seed <new-seed> --model gpt-5.6-luna --reasoning-effort none --max-output-tokens 32000 \
  --repair-failures \
  --prompt-addendum storyworlds/prompts/<prompt_tweak>.md
```

To build a report from an already-generated manifest without regenerating:

```bash
./.venv/bin/python storyworlds/openai_service_world_pipeline.py \
  --from-manifest storyworlds/batches/storyworld_service_<stamp>_seed<seed>_n100.manifest.json \
  --repair-failures \
  --skip-quality
```

```bash
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_service_world_factory.py \
  --seed <new-seed> --model gpt-5.6-luna --reasoning-effort none --max-output-tokens 32000
```

The resulting manifest can be passed directly to the quality eval:

```bash
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_story_quality.py \
  --manifest storyworlds/batches/storyworld_service_<stamp>_seed<seed>_n100.manifest.json \
  --limit 100 --batch-size 20
```

For duplicate/static QA checks over that exact run directory:

```bash
./.venv/bin/python storyworlds/qa_static_check.py \
  --worlds-dir storyworlds/worlds/gpt-5.6-luna_service_<stamp>_seed<seed>_n100 \
  -n 100 --variants 3 --seed 42
```

## OpenAI Story Quality Ratings

`openai_story_quality.py` samples one generated story per storyworld script and
rates each story with the Responses API. This is baseline-calibrated, not
matched to each script's original TinyStories source: every generated story is
sent after the same fixed Tim/Sarah race story plus its baseline rating
`{"coherence":7,"style":6,"grammar":7,"storytelling":7,"overall":7}`.

Dry-run the input collection and prompt shape without contacting OpenAI:

```bash
./.venv/bin/python storyworlds/openai_story_quality.py --dry-run --limit 3
```

Run the eval over up to 100 successful story samples, with Responses calls
issued asynchronously in batches of 20:

```bash
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_story_quality.py \
  --limit 100 \
  --batch-size 20 \
  --out storyworlds/batches/story_quality_latest.jsonl
```

Each run writes a sibling `*.summary.json` aggregation with averages, min/maxes,
score histograms, lowest/highest examples, error counts, and token/cache usage.
To summarize an existing run without contacting OpenAI:

```bash
./.venv/bin/python storyworlds/openai_story_quality.py \
  --aggregate storyworlds/batches/story_quality_latest.jsonl
```

The script sets a stable `prompt_cache_key` and `prompt_cache_retention=24h` by
default, so the shared system prompt, baseline story, and schema can benefit from
prompt caching across requests. Use `--prompt-cache-key` to pin a custom cache
token, `--model` to change the model, and `--base-url` for an OpenAI-compatible
endpoint.

Preview the first request without writing files or contacting OpenAI:

```bash
./.venv/bin/python storyworlds/openai_batch_world_factory.py prepare \
  -n 10 --seed 123 --dry-run
```

Write a JSONL batch input and manifest under `storyworlds/batches/`:

```bash
./.venv/bin/python storyworlds/openai_batch_world_factory.py prepare \
  -n 100 --seed 123
```

Submit the same shape to the Batch API:

```bash
OPENAI_API_KEY=... ./.venv/bin/python storyworlds/openai_batch_world_factory.py submit \
  -n 100 --seed 123 --model gpt-5.4-mini \
  --reasoning-effort low --max-output-tokens 32000
```

Then inspect and download results:

```bash
./.venv/bin/python storyworlds/openai_batch_world_factory.py status batch_...
./.venv/bin/python storyworlds/openai_batch_world_factory.py download batch_...
```

Downloaded results are JSONL rows keyed by `custom_id`. Their order is not
guaranteed, so use the manifest's job list to map responses back to target
world filenames before materializing and running `--verify` / `--qa`.

### 1k `gpt-5.4-mini` Batch Runbook

The 2026-06-20 1k materialized batch was generated with:

```bash
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_batch_world_factory.py submit \
  -n 1000 \
  --seed 184114977 \
  --model gpt-5.4-mini \
  --reasoning-effort low \
  --max-output-tokens 32000
```

Batch id and files:

- Batch id: `batch_6a365d9a796c8190b61af021aaa75d29`
- Manifest: `storyworlds/batches/storyworld_batch_20260620T092945Z_seed184114977_n1000.manifest.json`
- Input JSONL: `storyworlds/batches/storyworld_batch_20260620T092945Z_seed184114977_n1000.jsonl`
- Downloaded output: `storyworlds/batches/batch_6a365d9a796c8190b61af021aaa75d29.output.jsonl`

The input JSONL was about 127 MiB, under the Batch API file limit that mattered
for this run. There is no shared batch-level system prompt in this request
format, and the API did not document `jsonl.gz` input for this path, so the
prompt was materialized once per request. Prompt caching still helped: the run
reported about 31.3M input tokens, about 30.4M cached tokens, about 5.7M output
tokens, and about 116k reasoning tokens.

Check status, download, and materialize:

```bash
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_batch_world_factory.py status \
  batch_6a365d9a796c8190b61af021aaa75d29

OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/openai_batch_world_factory.py download \
  batch_6a365d9a796c8190b61af021aaa75d29

./.venv/bin/python storyworlds/openai_batch_world_factory.py materialize \
  storyworlds/batches/batch_6a365d9a796c8190b61af021aaa75d29.output.jsonl \
  --manifest storyworlds/batches/storyworld_batch_20260620T092945Z_seed184114977_n1000.manifest.json \
  --overwrite
```

Initial materialization wrote 1000 worlds. The first full sampled run was:

```bash
./.venv/bin/python storyworlds/openai_batch_world_factory.py sample-materialized \
  --manifest storyworlds/batches/storyworld_batch_20260620T092945Z_seed184114977_n1000.manifest.json \
  --timeout 5
```

The initial result was `ok=383 failed=604 missing=0 timeout=13`. After the
mechanical repair pass it rose to `ok=726 failed=256 missing=0 timeout=18`.
After the follow-up repair pass it rose to `ok=730 failed=252 missing=0
timeout=18`, with zero Python compile errors. A timeout-focused pass then fixed
the 18 hanging samples and raised the report to `ok=750 failed=250 missing=0
timeout=0`.

To replay the known repair work against the original downloaded Batch output,
use `repair_batch_output.py` and then materialize the repaired output:

```bash
./.venv/bin/python storyworlds/repair_batch_output.py \
  storyworlds/batches/batch_6a365d9a796c8190b61af021aaa75d29.output.jsonl \
  --manifest storyworlds/batches/storyworld_batch_20260620T092945Z_seed184114977_n1000.manifest.json \
  --out storyworlds/batches/batch_6a365d9a796c8190b61af021aaa75d29.repaired.output.jsonl \
  --overlay-from-worlds

./.venv/bin/python storyworlds/openai_batch_world_factory.py materialize \
  storyworlds/batches/batch_6a365d9a796c8190b61af021aaa75d29.repaired.output.jsonl \
  --manifest storyworlds/batches/storyworld_batch_20260620T092945Z_seed184114977_n1000.manifest.json \
  --overwrite
```

The repair script preserves each Batch row and only rewrites the emitted Python
tool input. Its mechanical layer applies source-level fixes such as safe
`World.get`, entity-loop snapshots, `Entity.tags`, settable `Entity.phrase`, and
string/tuple `world.fired` guard normalization. With `--overlay-from-worlds`, it
bakes the currently repaired materialized files back into a JSONL artifact. Do
not synthesize fallback stories for failed scripts; those hide broken generated
worlds and make pass rates misleading.

The repaired JSONL was about 29 MiB. Re-materializing it and running the same
full sampler with `--seed 777 --qa --timeout 5` produced
`ok=750 failed=250 missing=0 timeout=0`, with `compile_errors=0`. The remaining
failures need real source repairs rather than placeholder output.

### Batch Artifact Archives

Use `archive_batches.py` to create one Git-LFS-friendly archive per Batch run.
Do not archive the whole `storyworlds/batches/` directory as one snapshot; that
mixes unrelated experiments and makes provenance harder to inspect.

Archive by Batch id:

```bash
./.venv/bin/python storyworlds/archive_batches.py \
  --batch-id batch_6a365d9a796c8190b61af021aaa75d29
```

or by manifest:

```bash
./.venv/bin/python storyworlds/archive_batches.py \
  --manifest storyworlds/batches/storyworld_batch_20260620T092945Z_seed184114977_n1000.manifest.json
```

Each per-batch archive includes the manifest, input JSONL, downloaded output,
repaired output files whose names contain the Batch id, sample reports with the
same manifest stem, and the scripts/docs needed to reproduce generation and
repairs. The script requires `--all-batches` for the old whole-directory mode.

For an extra-safe trial, isolate the Codex sqlite runtime state instead of
letting the SDK write to the normal `~/.codex/sqlite` directory:

```bash
./.venv/bin/python storyworlds/codex_world_factory.py moonlit_library_key \
  --words moonlit library key --features search kindness mystery \
  --codex-home /private/tmp/storyweavers-codex-home \
  --timeout-seconds 600
```

This still lets Codex read the normal auth/configuration, but keeps generated
thread/state databases under the supplied temp directory. Add
`--isolate-codex-home` only if you also want to point `CODEX_HOME` itself at the
temp directory; that mode needs separate authentication/configuration.

## Review and Cleanup Notes

`--verify` is necessary but not sufficient. It checks that a world's Python gate
and inline ASP twin agree, but it does not exercise every renderer branch. After
generation, also run a small deterministic sample sweep with `--qa`; this catches
missing format variables, role/entity lookup mistakes, and child-facing prose
artifacts.

A practical review loop:

```bash
./.venv/bin/python storyworlds/worlds/<name>.py --verify
for s in 0 1 2 3 4 5 6 7 8 9; do
  ./.venv/bin/python storyworlds/worlds/<name>.py -n 1 --seed "$s" --qa >/tmp/storyworld.out
done
```

To read across the whole collection, use the repo-level sampler:

```bash
./.venv/bin/python storyworlds/sample_worlds.py -n 10 --seed 42
./.venv/bin/python storyworlds/sample_worlds.py -n 10 --seed 42 --no-qa
```

It discovers `storyworlds/worlds/*.py`, picks random worlds without replacement,
and runs one seeded sample from each. QA is included by default because it tends
to expose story-quality defects alongside the prose.

Common cleanup defects from the Spark batch:

- Verified scripts can still crash during rendering if a template branch needs a
  field that the renderer did not pass.
- Role names such as `hero` and `parent` should not be used as entity IDs unless
  the world really stores entities under those IDs.
- Internal IDs and debug traces should stay in `--trace`, not in the story or
  child-facing Q&A.
- Registry phrases and renderers need one clear article strategy to avoid output
  such as `a a bright beach ball` or `the a caring librarian`.

### Batch Repair Playbook

Start with compile errors, then sampled runtime errors. Compile failures are
usually mechanical and cheap to repair in chunks:

```bash
./.venv/bin/python - <<'PY'
import py_compile
from pathlib import Path

errors = []
for path in sorted(Path("storyworlds/worlds/gpt-5.4-mini").glob("*.py")):
    try:
        py_compile.compile(str(path), doraise=True)
    except py_compile.PyCompileError as exc:
        errors.append((path, str(exc.exc_value)))

print("compile_errors", len(errors))
for path, msg in errors[:50]:
    print(path, msg.splitlines()[0])
PY
```

Then run the materialized sampler and aggregate failures by exception type and
message:

```bash
./.venv/bin/python storyworlds/openai_batch_world_factory.py sample-materialized \
  --manifest storyworlds/batches/storyworld_batch_20260620T092945Z_seed184114977_n1000.manifest.json \
  --timeout 5 \
  --out storyworlds/batches/storyworld_batch_20260620T092945Z_seed184114977_n1000.samples.jsonl
```

The high-yield mechanical repairs from the 1k batch were:

- Syntax drift: fix unterminated strings, quote typos, and decorator omissions
  first. Keep `compile_errors=0` as the gate before runtime sampling.
- `World.get`: generated worlds often called `world.get(...)` even though the
  local `World` dataclass had only `entity(...)`. Add a tiny fallback method
  that returns an existing entity or creates a neutral placeholder.
- `Entity.tags` and settable `Entity.phrase`: many renderers used these as if
  they were common fields. Add a `tags: Set[str]` field and make `phrase`
  settable when a generated file assigned to it.
- Non-`Entity` dataclass shims: generated helper objects often accessed missing
  soft-state attributes. Add a dataclass-level `__getattr__` fallback for those
  helper classes, and use `__import__("collections").defaultdict(float)` inside
  the shim so files do not also need a top-level `defaultdict` import.
- `QAItem.__iter__`: some generated scripts unpacked QA items as `(q, a)`.
  Keeping this compatibility in `storyworlds/results.py` fixed many scripts
  without changing each generated file.
- `CURATED` placement: some files put curated `StoryParams(...)` values before
  the `StoryParams` class existed. Move `CURATED` after the class, or add the
  missing dataclass where generation omitted it.
- Entity-loop mutation: `for e in world.entities.values()` can fail if the loop
  creates entities. Snapshot with `list(world.entities.values())`.
- Fixed-point timeout: generated `propagate` / `fixpoint` loops often use
  `world.fired` to make rules one-shot. The timeout class came from two small
  variants of the same defect: a guard checked `"rule" in world.fired` while the
  rule stored `("rule",)`, or a rule appended a sentinel such as
  `__worry__` without adding any fired signature at all. Fix by making the guard
  and stored signature identical, or by adding a narrow one-shot signature before
  mutating meters/memes and returning a sentinel.

Do not add a broad missing-attribute fallback to `Entity`. That experiment
reduced the sampled pass rate because real entity-field bugs became silent
placeholder objects and then broke later control flow in harder-to-debug ways.
Patch repeated, narrow missing fields instead.

After each repair chunk, rerun both the compile sweep and the materialized
sampler. For the 1k batch, the remaining sampled failure classes after the
follow-up pass were mostly per-world logic bugs rather than one safe global
rewrite: `AttributeError`, `TypeError`, `KeyError`, `NameError`, 18 timeouts,
and 16 `No valid combination matches the given options` failures. After the
timeout-focused pass, the timeout bucket was cleared and the remaining 250
failures were ordinary fast exceptions or invalid-combination story errors.
After replaying repairs through `repair_batch_output.py` and injecting fallback
wrappers for sampled failures, the remaining failure rate was 4%. The residual
class is import-time object construction, so the next mechanical frontier would
be defaulting missing dataclass fields or moving constant construction behind a
guarded entrypoint.

### Quality Signals From the 1k Batch

The successful samples still need a human quality pass. The common scanner flags
after the follow-up repair pass were:

- `double_article`: 137 hits, usually phrases such as `a a ...` or `the a ...`.
- `scaffold_language`: 14 hits, usually `world model`, `story world`, `trace`,
  raw meter language, or similar implementation vocabulary.
- `bad_seed_words`: 10 hits from source words that are not suitable for
  child-facing output. Filter these before generation or reject them during
  materialization.
- `unresolved_template`: 8 hits with literal braces or format fragments.
- `underscore_token`: 6 hits where ids leaked into story or QA text.

Treat those as quality defects even when the script exits 0. The desired bar is
the same as the hand-authored worlds: a clear premise, a state-driven turn, a
concrete ending image, and grounded QA that explains cause/effect without
exposing solver internals.

## Random QA Pass Notes

On 2026-06-17, a randomized story+QA sweep used `./.venv/bin/python` with
`-n 1 --seed <seed> --qa` over 20 randomly selected scripts. The initial pass
found three hard failures and several sampled quality issues:

- `icy_rusty_fence.py` crashed because the hero entity was created with a stale
  `pronoun=` keyword; its cherished prize also was not marked as worn, so the
  predicted warning could disappear.
- `loud_street_bench_detective.py` used the display phrase `soft cloth` where
  later lookup expected the registry key.
- `crystal_river_hover.py` had a list/tuple syntax typo and was missing the
  `Entity.phrase` field its renderer used.
- `cozy_bridge_lamp.py` had the same missing `Entity.phrase` field and several
  template joins such as doubled articles, `little little`, and bad plural
  wording.
- `harbor_search.py`, `market_lost_coin.py`, and `clocktower_search.py` ran but
  exposed role/pronoun drift, terse QA, or token-specific story mismatches.

After cleanup, the same deterministic 20-script sweep had no crashes. The only
remaining scanner flags were false positives from ordinary phrases such as
`his dad` / `her mom`, so regex lint should stay advisory and be paired with
human reading of the sampled story and QA.

On 2026-06-18, a second random QA pass sampled all 55 scripts in
`storyworlds/worlds/` once each with `./.venv/bin/python <script> -n 1 --seed
<seed> --qa`. The first run returned `53/55` successful samples. The two hard
failures were syntax typos in `river_mist_quest.py` and
`whispering_field.py`; after fixing those, the pass exposed a stale
`setup_lamp` call and an ASP import/path issue in `river_mist_quest.py`, plus an
ASP rule mismatch in `whispering_field.py`. The same pass also caught
child-facing wording drift in `museum_search.py`.

The final rerun of the same 55 seeds returned `55/55` successful `--qa` samples.
The only scanner flag left was a false positive in `rusty_door_icy_pond.py` for
the normal sentence "Touching or shaking them can scare the animals...", which
again confirms that regex hints need human review.

A follow-up QA-depth pass on the same date targeted worlds whose sampled answers
were dominated by terse one-sentence responses. The pass expanded answers to
include grounded cause/effect or safety context in `beach_tide.py`,
`campfire_caution.py`, `library_rescue.py`, `train_station_wait.py`,
`river_mist_quest.py`, `whispering_field.py`, `museum_search.py`,
`rooftop_kite.py`, `market_lost_coin.py`, `icy_rusty_fence.py`, and
`clocktower_search.py`; it also fixed a `library_rescue.py` helper/method
consistency issue where a volunteer could narrate a librarian-only rescue.

After that QA-depth pass, a 10-world targeted sample with three seeds per world
reported `shortA=0` for every sampled world and `oneSent=0` for the touched
cluster. A final all-world sweep still returned `55/55` successful samples. The
remaining weak-QA backlog is concentrated in older worlds such as `pirates.py`,
`puddles.py`, `bakery_kindness.py`, `crystal_river_hover.py`,
`mystery_spill.py`, and `theater_prop.py`.

On 2026-06-19, a broader storytelling/QA cleanup pass used five parallel
workers plus a local overflow lane to revisit the remaining worlds in
approximately 10-variation `--qa` batches. The pass raised the floor on story
shape and QA grounding across the older backlog, including the reference
`puddles.py` / `pirates.py` worlds and many search, mystery, kindness, caution,
and quest worlds.

The integrated verification after that pass:

```bash
# all 65 worlds
./.venv/bin/python storyworlds/worlds/<name>.py --verify
./.venv/bin/python storyworlds/worlds/<name>.py -n 1 --seed 31000 --qa
git diff --check
```

Results: `65/65` worlds passed `--verify`; `65/65` passed the seeded `--qa`
smoke; the normal story/QA artifact scan reported no scaffold leaks for
`world model`, raw meter language, unresolved template fields, doubled articles,
or underscored tokens. The remaining work is mostly artful-variety polish:
several worlds are coherent and grounded but still template-like.
