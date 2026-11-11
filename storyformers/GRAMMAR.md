# Grammar neurons, heads and layers

The new core is independent of grammarworlds and uses the Python standard
library. [grammar.py](grammar.py) defines the reusable neuron;
[transformer.py](transformer.py) supplies heads, layers, joint projection,
generation and output-rule training. The former frequency model is explicitly
available as `FrequencyStoryformer`.

```sh
.venv/bin/python -m storyformers.demo --trace
.venv/bin/python -m storyformers.demo --save /tmp/grammar-model.json
.venv/bin/python -m unittest storyformers.test_transformer
```

The demo consumes five complete latents for `Lily needed tools and took` and
runs two layers with sixteen slots each. Its output token probabilities are
approximately scissors 0.5922, needle 0.3010 and thread 0.1068. Each word has
complete bundle alternatives; the strongest scissors bundle is:

```json
{
  "token": "scissors",
  "pos": "n",
  "entity": "scissors",
  "role": "patient",
  "location": "Lily",
  "event": "obtain tool",
  "position": {"token": 5, "sentence": 0, "in_sentence": 5}
}
```

These are authored demonstration rules, not learned story knowledge. Two head
slots are populated in each demo layer; the other fourteen are neutral slots.
The first layer copies an actor. The second can use that attribute for its event
lookup. Output grammars then copy the derived values into candidate bundles.
No LLM or WordNet download is required for this demo.

## One neuron in both roles

A `GrammarNeuron` contains weighted `Rule(pattern, emit, weight)` productions
and optional key-value tables. `activate(context)` returns projected dictionary
values, unnormalized match mass, rule identity and captured source positions.

```python
from storyformers import GrammarNeuron, Rule, Seq, Token, Gap, Ref, Lookup

neuron = GrammarNeuron(
    'acquisition',
    rules=(Rule(
        Seq(Token(bind='actor', entity='girl'), Gap(), Token(bind='verb', token='took')),
        {'actor': Ref('actor.token'),
         'event': Lookup('verbs', Ref('verb.token'))},
        weight=2.0,
    ),),
    tables={'verbs': {'took': 'obtain tool'}},
)
```

The exact same class can emit an attribute patch for a head or the full semantic
bundle for a vocabulary root. There is no separate token projection matrix.
Any valid serializable attribute value can be projected; the five required
semantic keys are POS, entity, role, location and event. Extra attributes are
retained and can be matched, copied, supervised and serialized.

Patterns consume the complete supplied context:

| Construct | Meaning |
| --- | --- |
| `Token(bind=..., **tests)` | Match one record; optionally bind it by name |
| `Seq(...)` | Compose patterns in order; empty Seq matches empty context |
| `Alt(..., weights=(...))` | Weighted alternatives, normalized locally |
| `Repeat(pattern, minimum, maximum)` | Finite repetition |
| `Gap(maximum=256)` | Consume an explicit bounded sequence of arbitrary records |
| `Search(pattern)` | Gap, pattern, Gap; find evidence anywhere in context |
| `Ref('actor.entity')` | Read a captured record, including nested dictionary paths |
| `Ref('query.event')` | Read the current query (the last record of this prefix) |
| `OneOf((...))`, `Present()` | Membership and explicit non-null feature tests |
| `Lookup('table', key)` | Project the value for a literal or captured key |

A shared Python pattern can be used by several neurons. Captures bind terminal
records, so an NP pattern can capture its noun head. A repeated capture name
requires equal records. Feature comparisons can refer to earlier captures.
Missing fields, captures or KV keys cause that derivation to abstain. Whitespace
is an ordinary record if present; use Gap or explicit tests to handle it.

Rule weights are unnormalized positive masses; alternative branch weights are
normalized. Distinct compatible derivations contribute mass. An explicit
matching-state budget bounds work and raises `MatchBudgetExceeded` on exhaustion;
it never silently discards probability mass. Nullable repetitions are rejected
when encountered. This is a finite pattern engine, not a full GF/Codeco parser.

## Heads and residual evidence

```python
from storyformers import GrammarHead, StoryformerBlock

layer = StoryformerBlock((GrammarHead(neuron),))  # padded to 16 slots
residuals, trace = layer.forward(context_latents)
readable = [row.view() for row in residuals]
```

A head's `operation` is `add` or `suppress`. Its neuron emits the attribute/value
pairs; the head converts match mass into signed residual evidence:

```text
delta = sign * strength * match_mass / (null_mass + total_match_mass)
```

The null match keeps weak evidence weak. Each field stores scores for competing
values plus an unknown candidate; input non-null attributes start with score 1
and unknown with score 0. `Residual.probabilities(field)` exposes normalized
scores, while `view()` supplies the strongest value to grammar matching.
Suppression subtracts evidence and can return the visible field to null. It
preserves the original observation and its alternatives. Strong conflicting
updates require sufficient strength or suppression of the old candidate.

All heads read one immutable snapshot of the preceding layer. Each query sees
only its prefix and writes only its own slot. Updates are summed before applying
them, so head ordering cannot change the result. Token, surface, positions and
source spans are protected. New attributes become available to other heads in
the next layer. No token insertion/deletion changes sequence length.

The residual keeps competing per-field evidence, but matching currently uses
its strongest readable value. It is not a full probabilistic lattice of every
intermediate feature combination. Final output alternatives are complete joint
bundles, not independent samples of their fields.

## Joint vocabulary projection and model

```python
from storyformers import GrammarProjection, Storyformer

projection = GrammarProjection({'scissors': scissors_neuron, 'needle': needle_neuron})
model = Storyformer(projection, layers=(layer, layer), context_size=256, top_k=10)
distribution = model.predict(context_latents)
print(distribution.to_dict())
```

Each vocabulary entry fixes the emitted token. Its neuron reads the processed
context and constructs one or more complete attribute bundles. Identical bundles
accumulate their derivation mass. Normalization happens over all word/bundle
pairs, then word probabilities are obtained by marginalization. Different
semantic meanings for the same word remain distinct alternatives.

`probabilities` contains the top ten distinct words, normalized over retained
word mass. `candidates` retains every complete bundle for those words with its
joint probability, normalized over that same mass. `retained_mass` reports the
truncation; `joint` exposes the full unpruned distribution for learning/scoring.
An unmatched vocabulary returns an empty distribution. Supply explicit fallback
productions when needed; the core does not secretly use trigrams or invent words.

The context is a list of complete latent dictionaries. Missing required semantic
fields become explicit nulls. Positions are computed locally if absent, and
existing structured positions are preserved across context clipping. The window
counts supplied records; passing whitespace records counts them toward 256.
Raw text annotation remains a separate pipeline, and no runtime API is called.

`forward()` also returns all visible position predictions, residual evidence
and match/update traces. `predict()` runs the layers and only the final readout.
`generate(context, steps, seed=...)` samples complete joint candidates and appends
the entire chosen latent before predicting the next one. END stops generation.
The next step can directly match the preceding prediction's semantic attributes.

## Learning and persistence

`model.fit(documents, epochs=..., learning_rate=...)` consumes sequences of full
annotated latents. It teacher-forces complete prefixes, runs the actual layers,
and updates output-rule log weights using the gradient of full next-bundle
negative log likelihood. A correct word with wrong attributes receives no target
mass. All candidates participate before display truncation. `model.loss(documents)`
reports mean full-target loss, including infinity for unsupported targets.

The separate [induction baseline](INDUCTION.md) learns token/POS pattern
structures from data and compiles them into a one-layer model. Use `induce()`
for that experiment; `model.fit()` below optimizes an existing grammar bank.

This first trainer learns weights of fixed output grammar rules. Pattern
structure, internal Alt weights, KV contents and head strengths remain authored.
Output parameters may be tied across vocabulary roots, but fit rejects parameters
also shared with attention-head rules: optimizing those would require accounting
for their effects through the residual computation.
Every target needs output grammar support, including document starts. Unsupported
targets raise a clear error in fit; no grammar induction or silent fallback is
performed. Attributes and auxiliary keys present in targets are supervised too;
deterministic surface/position/span metadata is excluded from the loss.

The [offline neuron review loop](NEURON_REVIEW.md) adds evidence collection,
LLM grammar/projection/naming proposals, coordinated typed feature bindings,
and validation-gated adoption. Its optional registry metadata is saved with the
model; previous checkpoints remain loadable. Grammar and target comparisons
distinguish boolean values from numbers.

`model.save(path)` / `Storyformer.load(path)` persist the grammar AST, KV tables,
layer/head setup and learned weights as JSON. Shared neuron/rule identities are
preserved, including weight tying across vocabulary roots or layers. Checkpoints
contain declared data types rather than executable code or serialized functions.

The trace and feature changes describe model hypotheses. They do not commit
physical world events, ownership changes or embedded meme magnitudes. Connecting
this feature model to a legal StoryWorld executor remains separate work.
