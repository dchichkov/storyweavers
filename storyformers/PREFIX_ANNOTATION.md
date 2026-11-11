# Parallel prefix-only annotation

The default `catalog` contract (prefix v3) adapts the reviewed whole-story v4 prompt
to causal prefixes, with all 1,024 feature definitions and nine extensions. Luna sees a
growing story prefix and returns **one JSON object for its last word**. Every
word gets its own request. Previous annotations are never supplied or revised,
so requests can run independently in parallel. Whitespace and punctuation get
local synthetic records; positions are also computed locally.

```sh
.venv/bin/python -m storyformers.annotate_prefixes \
  --story 'Lily took scissors, needle and some thread' \
  --out storyformers/runs/my_prefix_annotations --concurrency 8

# Preview all exact requests without using credentials or contacting the API.
.venv/bin/python -m storyformers.annotate_prefixes \
  --story 'Lily took scissors.' --out /tmp/prefix_preview --prepare-only

# One growing-prefix set per original story in a corpus.
.venv/bin/python -m storyformers.annotate_prefixes \
  --input TinyStories_kernels/data00.kernels.jsonl --text-key story --limit 10 \
  --out storyformers/runs/ten_prefix_stories --concurrency 8
```

`--story-file` retains an entire UTF-8 file, including exact line endings.
Plain text `--input` has one story per nonempty line. Credentials use
`OPENAI_API_KEY`, the repository's `.API_KEY`, or `--api-key-file`. The model is
fixed to `gpt-6-luna`, the tier to `flex`, and default reasoning to `low`.
`--max-output-tokens` defaults to 4,096 for each single-record response.
Use `--contract legacy` for the original fixed-field v1 schema and prompt.
Use `--contract catalog-v2` to reproduce or resume the original catalog runs;
v3 has its own prompt and cache key and requires a fresh output directory.

## What is sent at each position

For `Lily took scissors.` the three model inputs reconstruct exactly:

```text
Lily
Lily took
Lily took scissors
```

No following space, punctuation, word, full-story hash, or future annotation
is included in a word's request. Input blocks contain JSON lines of exact span
records, so the model receives stable word indices along with the text.
Concatenating their `token` values gives the literal prefix. Instructions and
all few-shot examples come first in a shared developer message. The final
instruction asking for the last word comes after the span blocks.

For spaces, including a whitespace run such as a tab plus two spaces, the local
record has `pos="space"`, null semantic fields, and empty lists. Punctuation is
similarly local with `pos="punct"`. Neither requires a model call. These spans
still count toward indices and positions:

```text
0 Lily | 1 space | 2 took | 3 space | 4 scissors | 5 .
```

Thus `took.position.token` is 2, and `scissors.position.token` is 4. No duplicate
request is sent for the position after a space. Every word is annotated from
the prefix ending immediately after that word. The original story reconstructs
exactly from the final record list.

## Cache layout and scheduling

Requests use `prompt_cache_options={"mode":"explicit","ttl":"30m"}` with:

1. A breakpoint after the fixed instructions, full catalog, allowed enums, extensions and 18 causal examples.
2. A breakpoint after each word-ended input block. Each longer request preserves
   earlier blocks and their boundaries exactly; intervening local spaces and
   punctuation join the next word's block.
3. An uncached constant last-word instruction at the end.

The cache key is stable across stories and positions, derived from the prompt,
model, reasoning configuration, and output schema. Variable indices/text live
after the shared instructions. Nothing from a previous model response is added
to subsequent prompts.

This matters because simply replacing a string with a longer string can make
its former endpoint ineligible for a cache hit. Explicit content-block boundaries
preserve the earlier endpoints. The provider supports many lookup boundaries
while limiting writes per request; cache usage is measured from each raw
response, not assumed. See the [official OpenAI caching guide](https://developers.openai.com/api/docs/guides/prompt-caching).

The scheduler sorts by prefix word count, then character length, warms the
shortest pending request to completion, and dispatches the remainder in bounded
parallel waves. Each wave finishes before the next begins, allowing shorter
prefixes to populate caches before longer ones. `--concurrency 1` runs the same
requests sequentially. Parallelism controls the number of in-flight requests;
provider latency and cache availability still determine realized throughput.

## Semantic contract

The [catalog prefix prompt](prompts/annotate_prefix_catalog_v3.txt) ports the
reviewed naming, typed values, scope, polarity, identity and source-gap lessons.
It deliberately replaces retrospective interpretation with evidence available
at each word. The [18 causal examples](data/prefix_catalog_examples_v3.json)
are authored prefix examples; no full-story labels are copied into them. The v3
review adds goals and promises when their complements become visible, stable
possessive-name anchors, nested quote/operator scope, belief content, and literal
depictions. Existing goal, belief, obligation and narrative names are reused.

Two [new typed bundles](data/prefix_extensions_v3.json) cover distinct meanings:

- `plot` records a prefix-supported narrative interpretation: role, stage,
  optional archetype/cast/stakes/links, and evidence. `plot.role` is separate from
  the participant `role` (actor, patient, etc.). Interpretations retain
  `status="candidate"`; links never claim mechanically verified causality.
- `depiction` binds a drawn/reflected image to its carrier and, when known, its
  physical referent. The depicted entity has its own identity and scope.

These extensions reconcile useful parts of Grammarworlds' attribute inventory
without inventing native engine effects, dependencies, or completed story arcs.
The 1,033 registered field names are an available vocabulary, not an emission
quota or a count of implemented heads. The canonical 1,024-entry candidate
catalog remains unchanged.

Return one sparse JSON object with required `index`, `token`, `pos`, `lemma` and
`scope_id`, plus supported catalog features directly on that object. Booleans,
numbers, arrays and bundles keep their JSON types. Omission does not mean false.
The API uses JSON mode, followed by local catalog type, enum, alignment and
reference validation. It does not require 1,024 null-filled fields per word.

- At `Lily`, no future event is known and age/gender remain unsupported.
- At `Lily took`, the obtain event has an actor but no known patient.
- At `Lily took scissors`, the current snapshot can name that patient and holder;
  the earlier `took` record and its empty patient list remain unchanged.
- At `Nia took a needle. She did not mend`, the mending patient and instrument
  remain unknown. An earlier available object is not automatically either one.
- Negated acquisition establishes no new holder. Negation, desired absence,
  prohibition and rejected causal reasons retain their own scopes and content.

Independent requests use deterministic anchors: `eN` uses the first entity-head
span index plus one; `evN` uses the predicate-trigger span index plus one. Thus
scissors at index 4 is e5, and took at index 2 is ev3. Existing resolved pronouns
reuse their antecedent's ID. `s0` is the implicit narrator scope; sN anchors an
operator scope and qN anchors an opening quotation. pN anchors proposition
content. Meaningful suffixes distinguish, for example, p14 and p14_negative.
IDs remain story-local and must anchor within the request's visible prefix.
Catalog tN anchors instead count nonspace tokens, including punctuation.

Reserved `_references` tables define the entities, events, scopes and
propositions referenced by this word. They are minimal **as-of snapshots**;
later snapshots may add newly visible arguments but never update earlier ones.
`_evidence` stores prefix-local span indices and explanatory notes. `_feedback`
and `_new_attributes` capture uncertainty and explicitly typed new meanings.
Shared names are reused before proposing any new field.

The assembled residual records omit these reserved metadata keys. Their original
per-prefix responses retain them, and `reference_snapshots.json` collects them
by target index. Do not merge that file into one retrospective global state.
A grammar matching these dictionaries still needs an explicit adapter to look
up companion tables. Positions and exact spaces/punctuation stay local.

Structural validation checks supplied types, known enums (also in reference
tables), reference closure, prefix bounds and token alignment. It does not prove
that a semantic interpretation is grounded. The original `--contract legacy`
mode retains its stricter fixed fields and trigger-only argument convention;
use a new output directory when switching contracts or prompts.

## Artifacts and resuming

The run root contains `prompt.json`, `manifest.json`, and a final `summary.json`.
Each story directory contains:

- `story.json`: local exact source, never sent as a complete story to the model.
- `prefixes/NNNNNN/request.json`: frozen request for that word's span index.
- `prefixes/NNNNNN/response.json`: raw provider response and cache usage.
- `prefixes/NNNNNN/annotation.json`, `metadata.json`, `validation.json`.
- `prefixes/NNNNNN/attempts/`: dispatch times and completion/error evidence.
- `prefixes/NNNNNN/repairs/NNN/`: separately journaled catalog correction
  requests/responses, using the same prefix and cached blocks (one by default).
- `annotations.json`: all word, whitespace, and punctuation records with positions.
- `metadata.json` and `validation.json`: aggregate provenance and validation.
- `reference_snapshots.json`: catalog-mode supporting tables/evidence per target.

Completed responses are reused and revalidated without API calls or credentials.
Changed prompts, settings, or input require a new output directory. The runner
uses the [existing Flex convention](https://developers.openai.com/api/docs/guides/flex-processing):
a 15-minute timeout, SDK automatic retries disabled, and retries only for definite
uncharged `429 flex_unavailable` responses (up to five retries, with exponential
backoff capped at 60 seconds). Ambiguous failed dispatches are
journaled and require inspection before resubmission. If one task fails, the
runner retains other responses already in flight before stopping later waves.

Catalog mode permits one additional model call by default when a completed
Luna/Flex JSON record fails local validation. `--validation-repairs N` sets an
explicit per-word cap; use zero to disable corrections. The uncached final instruction contains the
validation error, rejected draft and locally computed allowed span anchors.
It supplies no future story text or other positions' annotations. The original
response is retained, every call's usage is counted, and accepted corrections are
reused on resume. Each correction starts from the original request and only the
latest rejected draft, without accumulating earlier drafts. Exhausting the cap
stops that word; increasing the cap on resume retains all earlier responses. This does not
retry refusals, incomplete responses, wrong models/tiers or ambiguous dispatch
failures. Legacy mode retains its original stop-on-validation-error behavior.

The [catalog live smoke report](runs/prefix_catalog_luna_20261107_v2/REPORT.md)
records the new prompt attempt and correction. The earlier
[legacy smoke report](runs/prefix_annotation_live_20261107/REPORT.md) records
actual cache reads and overlapping generation. Offline tests cover prefix
isolation, exact span preservation, cache boundary reuse, bounded concurrency,
failure handling, validation, and response reuse:

```sh
.venv/bin/python -m unittest storyformers.test_prefix_annotation storyformers.test_catalog_prefix_annotation storyformers.test_catalog_prefix_v3
```

## Comparing annotation versions

The [reconciliation review](runs/prefix_reconciliation_20261109/REPORT.md) compares
the complete Luna story with the manually reviewed retrospective labels. Those
labels are not causal ground truth: evidence that appears later must be omitted
at earlier targets. Reference IDs also use different anchoring schemes.

The diagnostic replay supplies selected prefixes to the production runner and
checks agent-authored expectations afterward. Expectations are never sent to Luna.
Without `--live`, the command prepares requests and reports existing results only:

```sh
.venv/bin/python -m storyformers.prefix_review \
  --cases storyformers/runs/prefix_reconciliation_20261109/cases.json \
  --out storyformers/runs/my_reconciliation --live
```

This is a selected regression set, not a held-out accuracy estimate. It writes
`comparison.json`, `evaluation.json`, and the usual per-prefix journals. A full
corpus should be annotated consistently with one contract version; the replay
does not silently splice new records into the archived full-story run.
