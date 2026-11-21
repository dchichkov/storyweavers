# Symbolic attention head library

An executable, classical lookup layer for the [64 proposed behaviors](../proposed_symbolic_attention_inventory.md). It consumes typed symbolic memory and adjusts the **existing weighted grammar's next-word distribution**. It neither calls a model nor parses arbitrary prose.

**Coverage: 64 registered contracts, 15 executable table heads, 49 explicitly unimplemented program heads, and 640 authored examples (ten per head).** These are illustrative seeds, not learned statistics or extracted transformer circuits. There is no claim that all 64 algorithms have been implemented.

Read the [descriptions and all 640 examples](CATALOG.md). Each section links to its editable JSON file under [data/](data/). The [research inventory](../attention_head_inventory.md) remains separate.

## Run it

From the repository root:

```sh
.venv/bin/python -m grammarworlds.symbolic_heads
.venv/bin/python -m grammarworlds.symbolic_heads --head P059
.venv/bin/python -m grammarworlds.symbolic_heads --head P036
.venv/bin/python -m grammarworlds.symbolic_heads --demo --seed 7
.venv/bin/python -m unittest grammarworlds.test_symbolic_heads grammarworlds.test_grammarworlds
```

The demo composes and samples an eight-word sentence through `Node`/`Forest`:

> The river flows beside the old stone bridge.

At its verb slot, the authored seed counts produce:

| Word | Weighted grammar | After P059 |
| --- | ---: | ---: |
| flows | 0.4000 | 0.8857 |
| sings | 0.1000 | 0.0786 |
| freezes | 0.3000 | 0.0214 |
| sparkles | 0.2000 | 0.0143 |

All four remain possible. The demo prints the full distribution and evidence at every step; it does not just choose the highest score. Its semantic frame is an illustration, not a committed story event. The eight-word constraint is supplied by that demo grammar, not a general guarantee of the head library.

## What runs, and what deliberately does not

| IDs | Executable lookup operation |
| --- | --- |
| P001–P007 | Number/person/tense/auxiliary/determiner/argument/coordination mappings over parsed grammatical records |
| P013 | Context-cue-to-lexical-sense mapping |
| P015 | Authored ordered-item successors |
| P016 | Local register-cue mapping |
| P023 | Suitability mapping among tools explicitly supplied as available |
| P032 | Inverse-action mapping for supplied reversible changes |
| P044 | Speech-act-to-response-family mapping |
| P047 | Communicative-goal-to-utterance mapping |
| P059 | Current-word/feature/next-word count lookup with smoothing |

The remaining **49** require programs rather than pretending a finite vocabulary table implements them. Examples include variable-length prefix matching, entity-ID joins, ownership chronology, graph traversal, resource arithmetic, observer-specific beliefs, and dependency-aware evidence discounting. Every deferred JSON specification names its required algorithm and includes ten input/desired-feature design fixtures.

Requesting one raises **`ProgramRequired`, a subclass of `NotImplementedError`**, with `head_id` and `algorithm` attributes. There is no automatic fallback and no option that silently ignores requested deferred heads. Inspecting their descriptions is allowed; activating them is not. For example:

```python
from grammarworlds.symbolic_heads import HeadContext, ProgramRequired, load_library

library = load_library()
try:
    library.activate(HeadContext("P036", "Mira", "scene:1"), [])
except ProgramRequired as error:
    print(error.head_id, error.algorithm)
```

This distinction follows the requested exception policy. A small safe runtime abstention on a missing lookup is implemented everywhere; the broader P064 behavior—deciding whether to *say* something is unknown, rather than diagnosing a table coverage gap—still requires a program.

## Input contract: explicit scope and provenance

`Source(id, channel, scope, key, confidence=1)` is one symbolic memory record. `HeadContext(head_id, query, scope, strength=1)` requests one activation.

The grammar or world adapter must supply the channel and scope. For example, the noun in `grammatical_subject` must actually be the subject of the current clause, not merely a nearby noun. Tool records must actually represent available tools. A `reversible_change` record is a real scoped change, not a hypothetical event. This library does not hide a parser or world-state resolver behind those inputs.

Queries are semantic lookup keys; they need not be the immediately preceding word. P059's query is the current word in its illustrated experiment. Symbols are **case-sensitive and exact**. There is no stemming, substring match, or wildcard inference. Source IDs must be unique; channels and scopes prevent cross-clause or cross-entity leakage.

Selection normalizes positive authored selection weights multiplied by source confidence over matching records. Each source's projected feature weights are normalized, then mixed by those attention weights. The resulting activation contains a feature distribution, supporting source IDs, source attention, and a confidence gate. Thus a single low-confidence source does not acquire full influence just because its attention normalizes to one.

Prediction reads memory only. It does not update ownership, emotions, goals, or events. Carrier binding and state-changing actions remain the world layer's responsibility. This keeps the prototype aligned with `story.py`: concepts must be grounded in physical carriers, and a word score must not itself change the world. In particular, carrier/concept resolution P024 is explicitly deferred rather than implemented with bare emotion strings.

## Three editable lookup stages

Each `table` specification contains `selection`, `projection`, and `receiver`. A row has exactly `tokens` and `weight`:

```json
{"tokens": ["river", "water", "flows"], "weight": 12}
```

| Stage | Bigram meaning | Trigram meaning | Weight meaning |
| --- | --- | --- | --- |
| selection | `[query, source_key]` | Not used | Positive relative attention weight |
| projection | `[source_key, feature]` | `[query, source_key, feature]` | Positive relative transmitted-feature weight |
| receiver | `[feature, next_word]` | `[query, feature, next_word]` | Positive multiplier, or nonnegative count in count mode |

Bigram rows provide defaults. An exact trigram overrides the matching output's bigram weight; other bigram outputs remain. Multiple projection outputs form a distribution. These are **relative weights**, so they need not sum to one in the JSON.

P006 demonstrates why the query sometimes belongs in the transmitted mapping:

```json
{"tokens": ["put", "patient_filled", "location_remaining"], "weight": 1}
{"tokens": ["lend", "patient_filled", "recipient_remaining"], "weight": 1}
```

These are two separate JSON row objects, shown together for comparison. Likewise, P059 contains both:

```json
{"tokens": ["river", "water", "flows"], "weight": 12}
{"tokens": ["river", "water", "sings"], "weight": 1}
```

Its other examples include bird/song/sings, fire/heat/burns, door/locked/resists, door/unlocked/opens, seed/moisture/sprouts, and iron/moisture/rusts. The same transmitted feature can have a different receiving effect depending on the query.

### Receiver mathematics

For grammar probability `p₀(w)`, a head with feature distribution `a(f)` uses:

`score(w) = log p₀(w) + Σ_heads strength × confidence × Σ_f a(f) × log factor(query, f, w)`

Normalize those scores over **all grammar-supported words**, including `<END>` when permitted. Heads do not add candidates or resurrect zero-probability words. No four-candidate pruning occurs in the library; the demo happens to have four verb choices. Numerical floors preserve finite positive support at extreme weight ranges.

In **multiplier** mode an unlisted receiving row has factor 1, so it is neutral. Selection or projection misses cause an abstention with no score adjustment. Missing entries are not evidence of grammatical impossibility.

In **counts** mode, for each feature and the current allowed set `C`:

`p_f(w) = (count(query, f, w) + alpha × p₀(w)) / (Σ_v∈C count(query, f, v) + alpha)`

`factor = p_f(w) / p₀(w)`

Here `alpha` is `smoothing`, positive and initially 1. If no allowed count is present, the head backs off to the grammar. Counts outside `C` are excluded and listed in `outside_grammar`; they do not expand the grammar. A zero count is allowed and smoothed. This is a small fixed grammar-prior smoother, **not** P063's deferred learned hierarchy of trigram/bigram/effective-support backoff.

Several heads add log factors. The runtime does not assume their evidence is independent as a factual claim; this is the model being tested. P062's correlated-evidence discount is deferred. Repeating the same head ID in one prediction is rejected to catch accidental duplicate activation.

## Use with an existing weighted grammar

```python
from grammarworlds.symbolic_heads import HeadContext, Source, load_library, predict, sample
import random

library = load_library()
memory = [Source("river:water", "active_context_feature", "clause:1", "water")]
requests = [HeadContext("P059", "river", "clause:1")]

# forest is an existing grammarworlds.grammar.Forest with these prefix tokens.
prediction = predict(forest, ("the", "river"), library, requests, memory)
next_word = sample(prediction, random.Random(7))
```

The adapter keeps rule/event metadata and each candidate's original `grammar_probability`. It labels the forest's old prefix mass as `grammar_prefix_probability` to avoid confusing it with the reranked sequence probability. Multiply the sampled conditional probabilities to obtain the latter, as the demo does.

The seven-world storytelling generator now supplies a conservative subset of these
inputs through an [opt-in live adapter](../storytelling/HEADS.md), enabled with
`python -m grammarworlds.storytelling --heads`. Its separate manual profile does
not change this library's seed fixtures. Other callers must still supply scoped
inputs explicitly. Use only the prefix, committed world, or an explicitly
available plan; do not use the future chosen word to select a feature.

## Populate and verify

Edit the JSON specifications directly or generate validated rows offline. Keep counts and multipliers distinct. Preserve descriptions, input contracts, provenance, and diverse examples. New model-authored examples should be labeled as authored; corpus counts should identify their training source and exclude evaluation text. No authoring model runs during inference.

`load_library(custom_directory)` allows a separate set of specifications. Duplicate n-grams, malformed token lists, unknown status/mode, nonfinite values, and invalid weights fail at load time. Deferred entries cannot contain executable tables. An unknown head ID fails rather than silently doing nothing.

Regenerate the readable catalog after editing data:

```sh
.venv/bin/python -m grammarworlds.symbolic_heads.catalog > grammarworlds/symbolic_heads/CATALOG.md
```

Tests check all 150 executable examples and all 49 exception contracts, plus independent probability calculations, source/feature mixing, scoping, defaults, confidence gates, grammar exclusions, normalization, sampling, and existing-world immutability. The 490 deferred examples are design fixtures, not passed algorithm tests. These checks establish implementation behavior; story-quality improvement still requires corpus population and held-out evaluation.
