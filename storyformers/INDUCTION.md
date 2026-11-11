# Learning grammar proposals from token/POS data

This is a small, local, ILP-inspired baseline: learn conjunctions of observed
input facts, turn them into residual-writing grammar heads, and learn a joint
token/POS readout. English rules and head patterns are not supplied to the
learner. The synthetic teacher supplies annotated sequences, not its templates.
There are no LLM calls or additional dependencies.

After induction, the separate [neuron review workflow](NEURON_REVIEW.md) can
collect statistics/examples, propose LLM revisions, and validate changes to
grammar, feature bindings, and names. Induction itself stays entirely local.

```sh
.venv/bin/python -m storyformers.synthetic
.venv/bin/python -m unittest storyformers.test_induction
```

The run saves its corpus, a normal `Storyformer` checkpoint, and an inspectable
[report](runs/induction_baseline/report.json) under `runs/induction_baseline/`.
Use `--out /tmp/induction --seed 11` to keep a separate run. Search bounds include
`--lookback`, `--max-literals`, `--max-rules`, and `--weight-steps`.

## Data and split

Each JSONL line is a document containing only token and POS records:

```json
[{"token":"Lily","pos":"pn"},{"token":"took","pos":"v"},{"token":"scissors","pos":"n"},{"token":".","pos":"punct"},{"token":"<END>","pos":"special"}]
```

The teacher varies four names, four verbs, four plural nouns, optional adverbs,
determiners, and adjectives. Its vocabulary is 19 tokens including punctuation
and END. `used` takes tools; `ate` takes fruit. The learner receives neither those
groups nor a list of valid constructions. POS names are opaque category values.

The default seed is 7, with 192 training documents and 64 each for validation
and test. Name/verb pairs are disjoint across all three splits; all vocabulary
items are observed in training. Exact documents never cross splits. Optional
modifiers make the next token genuinely uncertain even in this small domain.

Training visits every next-token position, including the empty prefix. The
target and its POS never enter their own prefix. END is an observed target in
the data, not invented by the learner. Positions are added locally by the model.
Its compatibility schema also supplies nulls for unused semantic fields; the
training files contain exactly the two fields above.

## Proposal search and learning

[induction.py](induction.py) implements a bounded hypothesis language:

```text
[-1].pos = 'v'
[-2].token = 'used' AND [-1].pos = 'adj'
```

Negative offsets are relative to the current prefix end. Proposals enumerate
co-occurring token/POS equalities and their conjunctions, by default up to two
literals within the last three positions. Empty-context matching is another
candidate. Longer-distance tests compile into explicit wildcard positions;
all patterns retain the original grammar engine's full-context matching.

For every proposed condition, count the joint next-token/POS outcomes in
training. Other continuations are competing probability mass, not impossible
or invalid words. Smooth each conditional distribution toward the training
unigram distribution, and score adding it to the current model:

```text
gain = change in training joint log likelihood
       - complexity * description_cost

mass(token, pos | context) = prior_weight(token, pos)
                           + sum(active_rule_weight(token, pos))
```

Normalize over all joint outcomes. Candidate mixture strengths are searched over
0.5, 2, 8, and 32. Default minimum support is eight targets. Description costs
penalize additional literals, larger categorical domains, and farther offsets.
Identical training coverage retains the cheapest condition. An explicit proposal
budget raises an error instead of silently dropping candidates.

Greedily accept the highest positive penalized gain. When supplied, validation
also requires positive held-out likelihood gain. This uses validation for model
selection; validation does not supply literals, vocabulary entries, or gradient
updates. The test split is used only for final evaluation. This matters here:
training contains name/verb correlations that fail on held-out pairs. Without
the validation veto, the learner spends extra heads on those correlations.

After structure selection, fit the output production log weights with exact
batch conditional-likelihood gradients. Prefixes are grouped with outcome
counts for efficiency. The grammar heads' conditions are learned through
discrete search; this is not backpropagation through symbolic matches.

## One real residual layer

Each accepted nonempty condition becomes a `GrammarNeuron` in one of sixteen
head slots. It writes a private boolean feature, such as `__grammar_4=True`,
into the current residual position. Output grammar roots match those features
and emit their learned token/POS alternatives. All heads read the preceding
snapshot and see only causal prefixes. At most one derivation of each fixed
suffix pattern matches a given prefix.

The learned empty-context rule lives directly in the readout because an empty
stream has no position to write. The unigram fallback also lives in the readout.
The fallback and all output lexical/POS values are estimated from training data.
The readout uses full joint probabilities for learning and scoring, retaining
top-ten word marginals and their bundle alternatives for display/generation.

The resulting object is the existing `Storyformer`, not a separate classifier
used in place of the block. Removing its learned heads disables those readout
conditions, which provides an intervention check. Save/load uses the existing
JSON grammar AST checkpoint format.

```python
from storyformers import Storyformer, induce
from storyformers.synthetic import make_corpus

corpus = make_corpus()
result = induce(corpus['train'], validation_documents=corpus['validation'])
model = result.model                       # one layer, sixteen slots
prediction = model.predict([
    {'token': 'Lily', 'pos': 'pn'},
    {'token': 'took', 'pos': 'v'},
])
print(prediction.to_dict())
model.save('/tmp/induced-storyformer.json')
restored = Storyformer.load('/tmp/induced-storyformer.json')
```

## Recorded baseline

The default run has 1,311 training targets, 272 supported, distinct-coverage
proposals, and 433 test targets. It selects seven heads and an empty-context
production. Conditions include `last.pos=n`, `last.pos=adv`, `last.pos=adj`,
and `last.pos=det`. The report includes each rule's gains, residual feature,
final output weights, and next-POS distribution.

| Model | Test joint NLL, nats | Perplexity | Joint top-one accuracy |
| --- | ---: | ---: | ---: |
| Unigram | 2.797 | 16.389 | 14.8% |
| Lexical bigram | 1.314 | 3.720 | 51.5% |
| Induced one-layer model | 1.060 | 2.887 | 52.4% |
| Same readout, heads removed | 2.561 | 12.945 | 16.4% |

All four have 100% test target coverage. Loss uses the untruncated distribution;
top-ten renormalization does not inflate the scores. POS accuracy is 83.8% for
both the induced model and lexical bigram. Optional construction choices keep
some next-POS outcomes ambiguous. Validation is also reported but is not an
independent estimate, because it participates in rule selection.

The model can generate `Lily quickly took red pears . <END>` from its own
predicted token/POS records. It also generates `Ben used red pears . <END>`:
this first bank learns local syntax but does not recover the teacher's lexical
selection restrictions. This is a measurable grammar-induction baseline, not
evidence of complete English grammar or story quality.

This finite conjunctive search is inspired by inductive logic programming;
it is not a general Prolog/ILP solver. See the
[ILP survey](https://ijcai.org/proceedings/2020/673) for the broader approach.
Recursive grammar induction, variable/copy projection induction, learned KV
tables, multilayer predicate invention, and 64-expert head routing remain later
experiments. The residual flags are model features; they do not assert physical
world events, ownership, or embedded memeplex state.
