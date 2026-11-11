# Storyformers

A separate experiment in a learnable symbolic analogue of a decoder-only
transformer. It starts with dictionaries instead of embedding vectors. The grammar
neurons, layers, joint readout and weight trainer run locally. The optional [offline annotation
pipeline](ANNOTATION.md) calls Luna on Flex to create richer per-token labels.
The separate [prefix annotation mode](PREFIX_ANNOTATION.md) annotates one last
word per causal prefix in parallel, with locally generated spaces and positions.
Its default catalog prompt now adapts the reviewed 20-story v4 conventions,
with all 1,024 field definitions, sparse typed output and prefix-local references.
The [Luna reconciliation review](runs/prefix_reconciliation_20261109/REPORT.md)
adds v3 goal/scope examples and typed `plot`/`depiction` extensions, with a live
17-prefix comparison and separate agent-corrected records. Archived catalog runs
remain available with `--contract catalog-v2`.

The implemented core is documented in [GRAMMAR.md](GRAMMAR.md): one weighted
grammar neuron supports both residual-update heads and vocabulary projection.
`Storyformer` defaults to two layers with sixteen head slots each. The original
trigram model remains available as `FrequencyStoryformer` and the old text CLI.
The [block proposal](BLOCK_PROPOSAL.md) records the wider design and future work.

The [neuron review workflow](NEURON_REVIEW.md) collects training statistics and
examples for a head or output neuron, asks Luna/Flex for a training-time revision,
and evaluates a staged copy before saving an accepted checkpoint. Revisions can
adjust grammar, projections, typed feature names/bindings and neuron names.
This is a training-time tool; the proposed interleaved batch loop is described in
the [catalog learning notes](catalog/README.md#use-in-the-batch-learning-loop).

The [grammar-induction baseline](INDUCTION.md) learns head conditions and output
weights from synthetic token/POS sequences, using one layer and a 19-token
vocabulary. Run it locally with `.venv/bin/python -m storyformers.synthetic`.
Its saved corpus, checkpoint, learned rules, and held-out comparisons are in
[`runs/induction_baseline/`](runs/induction_baseline/).

The [learning emulation](runs/learning_emulation_20261109/REPORT.md) continues
that checkpoint through evidence collection, agent-proposed grammar revisions,
output-weight fitting, and validation gates. It removes redundant POS heads,
tests three verb-memory/readout revisions, and freezes the result before test
evaluation. This is an agent-guided experiment; it does not call Luna or provide
an autonomous proposal scheduler. Reproduce the reviewed revisions in a fresh
directory with `.venv/bin/python -m storyformers.learning_emulation --out /tmp/storyformer-learning`.
`LearningBatch` caches fixed-structure derivations for batch weight gradients;
it rejects stale evidence after external model changes.

The [generation sample sheet](runs/generation_samples_20261110/README.md)
records 12 unprompted generations and six prompted continuations from that
checkpoint, including awkward outputs. Seeds, raw tokens, full latent records,
decoding settings and the checkpoint fingerprint are retained. Reproduce with
`.venv/bin/python -m storyformers.sample_generations --out /tmp/storyformer-samples.json`.
Shared annotation prompts, parsed corpora and training/evaluation artifacts are
versioned; repeated provider requests/responses and per-prefix dispatch caches
remain local and are excluded from Git.

The [candidate catalog](catalog/README.md) provides 1,024 typed attributes,
1,024 proposed head functions and 1,024 linked grammar records, with examples,
research provenance and explicit runtime requirements. Selected executable seeds
can be loaded into existing blocks; the remaining records are implementation
contracts for future learning and adapters.

```text
complete latents -> causal residual stream (last 256 positions)
                -> grammar block 0 (16 head slots)
                -> grammar block 1 (16 head slots)
                -> vocabulary grammars -> joint next-latent distribution
```

## Run

From the repository root:

```sh
.venv/bin/python -m storyformers.demo --trace
.venv/bin/python -m unittest storyformers.test_transformer
```

The demo uses five authored latents for `Lily needed tools and took`, two layers
with sixteen slots each, and output grammars for scissors, needle, thread and
END. Its copy and lookup heads make the output bundles reflect Lily and tool
acquisition. The small grammar set is an architecture example, not a trained
story generator. No external package, WordNet download or API is needed for it.

### Try reviewed story annotations

```sh
.venv/bin/python -m storyformers.annotated_demo \
  --out storyformers/runs/annotated_forward_20261107/report.json
```

This passes the five actual annotated words `Then he took the lantern` through
three existing catalog seed heads, then the seven heads in the saved synthetic
learner: two layers with sixteen slots each. The rich input dictionaries and
source positions are retained; whitespace is omitted from the model stream.
The report saves inputs, residual changes, every firing, per-position joint
predictions and the top-ten word distribution. `--annotations`, `--start-word`
and `--words` select a different reviewed span within the checkpoint's context
limit; `--checkpoint` selects another saved grammar model.

A separate copy has determiner/count labels removed to show whether the seed
heads can reconstruct them. In the default span both missing labels on `the`
are restored. The learned layer adds its existing noun, verb, determiner and
adverb detectors. No new grammar is trained or authored by this probe.

This verifies that rich annotations run through the architecture. The projection
still has the synthetic learner's 19-token vocabulary and token/POS supervision;
its candidates do not reconstruct the rich semantic targets. Story-local ID
references are preserved, but companion entity/event tables are not automatically
queried. Whole-story retrospective inputs also make this unsuitable as a causal
next-token quality evaluation. The report checks block prefix invariance, which
does not remove future information already present in those input labels.

### Run and time the causal story

```sh
.venv/bin/python -m storyformers.benchmark_annotated \
  --out storyformers/runs/my_causal_forward
```

The [causal forward benchmark](runs/causal_forward_20261109/REPORT.md) uses the
753-word Luna story with the 17 reviewed corrections restored at their original
positions. It preserves sparse semantic bundles, removes only space records,
and saves residuals, head traces and top-ten predictions for every word and
punctuation mark. The model has three catalog seeds and seven learned heads in
two 16-slot layers, with the existing 19-token readout.

The benchmark separately measures next-token prediction, an all-position pass
over independent 256-record segments, and rolling prediction with the unchanged
16-record checkpoint. Its 256-context copy widens only wildcard grammar bounds;
it does not train a long-context model or modify the checkpoint. Source IDs and
positions remain intact, and companion reference tables stay outside the stream.
The timing includes traces and residual creation but excludes annotation API
calls, loading and output-file writes. The saved profile identifies current
Python implementation overhead; these measurements do not represent the proposed
24-layer, 32k-vocabulary architecture.

## Frequency baseline

```sh
.venv/bin/python -m pip install -r storyformers/requirements.txt
.venv/bin/python -m nltk.downloader -d storyformers/data/nltk_data wordnet
.venv/bin/python -m storyformers --prompt 'the rabbit' --trace
.venv/bin/python -m unittest storyformers.test_storyformers
```

The default training source is [data/demo.txt](data/demo.txt), twelve small,
authored illustrative documents, not corpus statistics or a pretrained model.
The prompt above returns:

```python
{'found': 0.5, 'carried': 0.2, 'shared': 0.2, 'rested': 0.1}
```

Train on the original story field of local TinyStories rows, then reuse counts:

```sh
.venv/bin/python -m storyformers \
  --train TinyStories_kernels/data00.kernels.jsonl --text-key story --limit 1000 \
  --save /tmp/storyformer.json --prompt 'once upon a'
.venv/bin/python -m storyformers --load /tmp/storyformer.json --prompt 'the rabbit'
```

`--train` can be repeated; training adds counts. Plain text has one document per
nonempty line, while JSONL has one document per selected string field, including
any embedded newlines. Documents never share n-grams. Loading alone adds no demo
data; loading together with `--train` continues training. `--top-k`,
`--context-size` and `--blocks` configure a new model. Loaded models retain their
context/block settings, with an optional `--top-k` override. Downloaded WordNet
data and models under `storyformers/models/` are ignored by git.

## Latents and the residual stream

The remaining model details below describe the original `FrequencyStoryformer`
baseline. See [GRAMMAR.md](GRAMMAR.md) for the residual-writing grammar model.

A token occurrence becomes an independent, JSON-serializable dictionary:

```python
{
    'token': 'rabbit', 'surface': 'Rabbit', 'position': 1,
    'pos': 'n', 'pos_candidates': ['n', 'v'], 'lemma': 'rabbit',
    'synsets': ['rabbit.n.01', 'lapin.n.01', 'rabbit.n.03', 'rabbit.v.01'],
    'lexname': 'noun.animal', 'hypernyms': ['leporid.n.01'],
    'lexicon': 'wordnet',
}
```

Token keys are case-folded; original surface form and absolute position survive.
Punctuation is a token. WordNet's first sense supplies the default POS, lemma,
lexical category and immediate hypernyms. All matching synset names and POS
candidates remain available. This is lexical lookup, **not contextual sense or
POS disambiguation**. Function words, punctuation, numbers, and out-of-vocabulary
tokens without WordNet senses have `pos=None`, empty sense lists and
`lexicon='unknown'`. Missing WordNet installation/data fails with setup
instructions, rather than silently substituting a hand-authored lexicon.

The residual stream is a list of these dictionaries, capped at 256 by default.
Every block returns its current dictionary unchanged. A block receives
`CausalAttention.visible`, containing only that position and earlier residuals
from the preceding layer. `causal_mask(n)` exposes the equivalent lower
triangular visibility matrix; `True` means visible. There are no query/key
vectors, attention scores, residual additions, feed-forward updates, or learned
block parameters yet. The interface leaves room for symbolic heads to read
features and contribute updates later.

## Readout and learning

At position `i`, the readout predicts `token[i+1]`. It reads the last **three**
visible latents and uses their final **two** token keys to look up a trigram:

```text
visible tail: [older, previous, current]
lookup:      C(previous, current, candidate)
probability: C(previous, current, candidate) / sum_candidate C(...)
```

This resolves the terminology explicitly: a trigram is two context tokens plus
the next token. Conditioning on all three would require four-gram counts, which
are not implemented. The oldest of the three latents is exposed in the trace
for future heads. WordNet attributes currently pass through; counts use only
the `token` channel, so semantic generalization has not been added yet.

The head backs off from an unseen final bigram to the final token's continuations,
then to unigram counts. It selects at most ten candidates and normalizes the
retained counts into the returned dictionary. `retained_mass` reports how much
of the original conditional mass survived this truncation; `order`,
`matched_context`, and `observations` explain the lookup. Empty models return an
empty dictionary. No unseen words receive invented mass. Stable alphabetical
ties make repeated predictions deterministic. Stored counts are sparse observed
continuations, and prediction never builds a full vocabulary probability table.

Training is maximum-likelihood **count estimation**, with no gradients.
`training_examples(document)` exposes teacher-forced `(context, target)` pairs:
only tokens strictly before the target enter its bounded sliding context. The
first token has empty context and contributes to the unigram fallback. Every
target contributes once, including beyond the 256-token window. `fit()` uses
the equivalent direct count update, avoiding redundant WordNet lookup/window
construction while blocks are identities. It rejects non-pass-through blocks;
future feature-transforming blocks will need their own learning procedure.

`forward(text)` returns the residual stream, a sparse prediction at each visible
position, and the final next-token readout. `predict(text)` returns just the final
dictionary. A prefix readout is independent of future input tokens; neither
forward method trains on the supplied prompt.

```python
from storyformers import FrequencyStoryformer as Storyformer

model = Storyformer(context_size=256, num_blocks=2, top_k=10)
model.fit(['the rabbit runs', 'the rabbit rests'])
model.predict('the rabbit')  # {'rests': 0.5, 'runs': 0.5}
model.forward('the rabbit').residual_stream[-1]['pos']  # 'n'
```

## Relationship to grammarworlds and Storyweavers

This borrows grammarworlds' explicit weighted alternatives and inspectable
symbolic heads, while leaving its worlds, grammar, and head tables untouched.
An optional bridge can learn fractional counts from a small weighted grammar:

```python
from grammarworlds.grammar import choice
from storyformers import FrequencyStoryformer as Storyformer

model = Storyformer()
model.head.fit_grammar(choice('move', 'rabbit runs', 'rabbit rests', weights=(3, 1)))
model.predict('rabbit')  # {'runs': 0.75, 'rests': 0.25}
```

This enumerates the finite grammar's derivations and uses their normalized
weights as observations. It does not enforce grammar constraints during decoding
or import the existing authored head tables. Ordinary text training does not
import grammarworlds at all.

In relation to [story.py](../story.py), these latents are lexical records, not
physical carriers or asserted world facts. This experiment does not yet resolve
entities, embed memeplexes, track concept magnitudes, or check legal world moves.
Future semantic heads should bind concepts to carriers before using them to
change a simulated story world. This first experiment establishes the causal
dictionary-stream interface and a measurable token-frequency baseline.

Next experiments: held-out next-token coverage/loss, explicit unknown/end-token
policy, symbolic feature updates within blocks, learned weighting of competing
heads, and a grammar-constrained readout. The toy demo is an architecture check,
not evidence of story quality or transformer-level learning.
