# Offline token annotation

For causal training inputs, use the separate [prefix-only parallel mode](PREFIX_ANNOTATION.md):
one last-word JSON record per growing prefix, with local spaces/punctuation and
explicit cache boundaries. The mode described below sees the entire story.

Luna annotates every word using a shared instruction prompt and six authored
examples. The local pipeline inserts spaces and punctuation to produce a JSON
array of dictionaries that reconstructs the story exactly. It preserves spelling,
case, repeated spaces, tabs and line breaks. Each row also has its index, kind,
and start/end Unicode character offsets.

## Run

From the repository root, using the existing project environment:

```sh
.venv/bin/python -m pip install -r storyformers/requirements.txt
.venv/bin/python -m storyformers.annotate \
  --story 'Lily took scissors, needle and some thread' \
  --out storyformers/runs/my_annotation
```

Credentials come from `OPENAI_API_KEY`, the project's `.API_KEY`, or an explicit
`--api-key-file`. Keys are never included in saved artifacts. Model and service
tier are fixed to `gpt-6-luna` and `flex`; default reasoning is `low`. There is no
automatic switch to another model or tier.

Other input modes:

```sh
# One full story, retaining its exact whitespace.
.venv/bin/python -m storyformers.annotate \
  --story-file /tmp/story.txt --out storyformers/runs/one_story

# One story per JSONL row; use only the original story field.
.venv/bin/python -m storyformers.annotate \
  --input TinyStories_kernels/data00.kernels.jsonl --text-key story --limit 10 \
  --out storyformers/runs/ten_stories

# Inspect frozen prompts/requests without making API calls.
.venv/bin/python -m storyformers.annotate \
  --story 'Lily took thread.' --out /tmp/annotation_preview --prepare-only
```

For plain text `--input`, each nonempty line is a document; only the line-ending
delimiter is removed. JSONL preserves whitespace inside the selected string.
Use `--story-file` for a single story spanning multiple lines. Stories are not
truncated to the predictor's 256-token context: this is full-story annotation.
The default output cap is 32,000 tokens; `--max-output-tokens` can change it.
Incomplete outputs are rejected rather than accepted as partial annotation.

## Output and fields

Each story gets a numbered directory containing:

- `request.json`: exact API body, schema, shared examples, story and token spans.
- `response.json`: raw provider response and usage, including cache evidence.
- `annotations.json`: the requested list of per-token dictionaries.
- `metadata.json`: model/tier, hashes, counts, annotation mode and cache usage.
- `validation.json`: accepted/rejected status and any validation error.
- `attempts/`: dispatch IDs and completion/error records.

The parent directory contains the frozen shared `prompt.json`, `manifest.json`,
and a cumulative `summary.json`. For example, these are selected fields from
the word rows for the short Lily input; actual output includes all fields,
spaces and punctuation:

```json
[
  {"token": "Lily", "pos": "n", "entity": "person", "entity_id": "e1", "entity_name": "Lily"},
  {"token": "took", "pos": "v", "event": "obtain object", "actor": "Lily", "actor_id": "e1", "patients": ["e2", "e3", "e4"]},
  {"token": "scissors", "pos": "n", "entity": "scissors", "role": "patient", "location": "Lily", "event": "obtain object"}
]
```

A name alone does not establish that Lily is a girl, and the tools alone do not
establish a repair purpose. A story that explicitly identifies her as a girl and
describes mending a coat can support `entity="girl"` and
`event="obtain repair tool"`.

Each participating object carries its event directly. For the repair story,
selected fields from the scissors dictionary are:

```json
{
  "token": "scissors",
  "pos": "n",
  "entity": "scissors",
  "role": "patient",
  "location": "Lily",
  "event": "obtain repair tool"
}
```

`location` names the physical holder or place at that mention, after the action
in its clause. Thus a needle given to Ava has `location="Ava"` at that mention;
a later mention when it is returned to Ben has `location="Ben"`. Ownership alone
does not establish physical location. Unknown locations stay null, and a denied
or imagined transfer does not establish a new holder. Names match the story's
canonical spelling.

| Fields | Meaning |
| --- | --- |
| `token`, `index`, `start`, `end`, `kind` | Exact surface, span position, character offsets, word/space/punct |
| `position` | Locally computed token, sentence and within-sentence indices |
| `lemma`, `pos` | Contextual lemma and compact POS (`n`, `v`, `adj`, etc.) |
| `entity`, `entity_id`, `entity_name` | Entity type, stable local ID, canonical name |
| `event`, `event_id`, `event_type` | Reusable semantic phrase, local event ID, broad event category |
| `actor`, `actor_id` | Canonical actor name and entity ID |
| `patients`, `instruments`, `recipient_id` | Event arguments as entity references |
| `role` | A token's participation, such as actor, patient or location |
| `location` | Canonical physical holder or place at this entity mention, or null |
| `factuality` | Asserted, negated, desired, hypothetical or reported event |
| `attributes` | Extensible list of `{ "name": "...", "value": "..." }` pairs |

Entity IDs (`e1`, ...) and event IDs (`ev1`, ...) restart per story. Resolved
pronouns retain the same entity ID/name/type as their antecedent. Event arguments
must point to entities mentioned in the annotated text. Null means no grounded
label; lists are empty when absent. Nonword rows have `pos="space"` or `"punct"`,
null semantic fields and empty lists. Word-level event argument fields live on
event triggers, identified by `role="action"`. Other participants carry the same
`event` label and `event_id` plus their own role and location. The validator
requires matching labels and exactly one trigger per event, so repeated event
labels on objects cannot hide a missing trigger.

## Local positional encoding

After validation, each token gets a symbolic positional dictionary without a
model call:

```json
"position": {"token": 9, "sentence": 2, "in_sentence": 1}
```

All three indices are zero-based. `token` is the global index in the complete
list, including spaces and punctuation. `sentence` identifies the sentence;
`in_sentence` is the token's index within it, using the same token counting.
For `Lily ran. Ben sat.`, Ben has `{"token":5,"sentence":1,"in_sentence":0}`.
End punctuation, closing quotes and following whitespace belong to the preceding
sentence; the next content token starts the next sentence. Newlines alone do not
start a sentence. Sentence rules recognize `.`, `!`, `?` and their CJK equivalents,
preserve decimal tokens and handle common titles such as Dr. They are deterministic
heuristics; unusual abbreviations and ellipses can remain ambiguous.

This is a dictionary of numeric features rather than a learned embedding vector.
Positions are computed after the API response, so the annotation prompt, schema
and prefix cache are unaffected. `metadata.json` records the local encoding
convention. Existing annotation arrays can be enriched entirely offline:

```sh
.venv/bin/python -m storyformers.positions \
  --input /tmp/annotations.json --output /tmp/positioned.json
```

The output may equal the input path to add or recompute positions in place.

## Keep labels consistent while expanding them

Edit [prompts/annotate_v2.txt](prompts/annotate_v2.txt) and
[data/annotation_examples.json](data/annotation_examples.json). The six examples
cover tool acquisition and repair, giving and pronoun resolution, an animal's
location/emotion, a negated acquisition, and acquisition without a stated repair
purpose, plus a give/return sequence with changing holder locations. They are authored teaching examples,
not model-generated evidence or a held-out quality benchmark.

For additional features, add consistent name/value pairs to `attributes`, explain
them in the prompt, and demonstrate them in the examples. This needs no structural
schema change. New top-level fields require coordinated edits to the schema,
validator, examples and version in [annotation.py](annotation.py). Custom prompt
and example files can be selected with `--prompt-file` and `--examples-file`.
Use a new output directory when changing the annotation contract.
The current contract is `storyformers-annotation-v2`; historical v1 requests,
responses and reports remain frozen in their original run directories.

Every example is validated before any request is prepared. Live output uses a
strict JSON schema and local checks for complete ordered word coverage, exact
tokens, allowed labels, stable entity identities, grounded ID references and
matching actor names. Validation does not prove that a label is semantically
entailed by the story; inspect samples when extending the prompt.

## Prefix caching and Flex

The shared developer prefix consists of the instructions and all examples. An
explicit cache breakpoint falls immediately after it, before each changing story
and word list. Requests set `prompt_cache_options={"mode":"explicit","ttl":"30m"}`.
A stable `prompt_cache_key` hashes the shared prefix, model, reasoning settings
and output schema. Story text never enters the key or shared prefix. Changing
examples or schema produces a new key automatically.

This follows the [official OpenAI prompt-caching
documentation](https://developers.openai.com/api/docs/guides/prompt-caching).
The substantial few-shot prefix exceeds the minimum cacheable length. The first
request may write it; subsequent sequential stories can reuse it. Cache hits
depend on provider availability and are **measured**, not assumed:
`cached_tokens` and `cache_write_tokens` are copied from each response's usage.
The first story runs before the second to allow cache population. The SDK
transport preserves cache fields even with the repository's older SDK version.

Requests use [Flex](https://developers.openai.com/api/docs/guides/flex-processing)
with a 15-minute timeout and SDK automatic retries disabled. Only a definite
HTTP 429 `flex_unavailable` rejection retries, twice, on Flex. Timeouts and other
uncertain dispatches stop for inspection; rerunning does not silently submit
them again. Completed raw responses are reused and revalidated without another
API call. Existing frozen requests must match the current inputs exactly.

## Relationship to the residual stream

These full-story annotations are offline teacher labels. Later sentences can
resolve an earlier pronoun or tool purpose, so these labels may contain future
information. They are saved separately from the causal WordNet residual stream;
the count predictor and its runtime remain unchanged. Use them as supervision
or analysis data. Feeding them directly into a causal predictor would require
a prefix-only annotation mode or a model that predicts those attributes.

Tests and a small live cache check:

```sh
.venv/bin/python -m unittest storyformers.test_annotation storyformers.test_storyformers
.venv/bin/python -m storyformers.annotate \
  --input storyformers/data/annotation_location_smoke_stories.jsonl \
  --out storyformers/runs/annotation_location_v2_20261106
```

The saved smoke directory contains both requests and responses. Repeating this
exact command reuses the completed responses. Its [report](runs/annotation_location_v2_20261106/REPORT.md)
records the measured cache reuse and a manual read of the annotations.
