# Iterating on a grammar neuron during training

The training workflow now has explicit steps:

```text
checkpoint + training documents
    -> evidence packet for one head/output neuron
    -> LLM revision proposal
    -> staged copy + validation evaluation
    -> accepted checkpoint or rejection report
```

The LLM can revise matching grammar, projections, weights, KV tables, feature
names/definitions, and the neuron name. It never executes code or participates
in generation. [neuron_review.py](neuron_review.py) performs collection and
evaluation without an API dependency; [refine.py](refine.py) adds the optional
Luna/Flex proposal step. [neuron_spec.py](neuron_spec.py) defines the readable
grammar JSON and typed feature checks.

## Intended batch loop

These commands are components of training, not a requirement to finish training
before revising grammars. The intended loop runs all causal positions of a batch
with a fixed model version, updates weights, and then proposes and evaluates
structural revisions before the next batch. The LLM is a training-time learner;
generation still executes only the learned symbolic model.

Candidate support, outcome counts and counterexamples accumulate across batches.
The LLM's working examples can focus on the current batch, supplemented by a
bounded history of relevant counterexamples, rolling statistics and canonical
feature definitions. Restricting it to one batch would make both grammar changes
and semantic naming depend too heavily on that batch's accidental correlations.
Keep statistics tied to the grammar/model version that produced them: after a
structural edit, re-run retained examples before comparing the revised neuron.

Weight updates can happen every batch; candidate search and LLM revision can also
run every batch, with limits on the neurons reviewed and proposed changes. Test
revisions on replay cases and a separate validation split before adopting them at
a batch boundary. Keep validation examples out of the LLM's learning packet.
An asynchronous proposal must be rebased and evaluated against the current model
if weights or structure have changed since its evidence was collected.

The combined scheduler and rolling-statistics store are not implemented yet.
`collect` currently profiles the supplied documents, and `evaluate_proposal`
checks one staged revision. The existing weight trainer fits output-rule weights;
head-weight learning still needs its own update procedure. See the
[catalog learning notes](catalog/README.md#use-in-the-batch-learning-loop).

An [agent-guided emulation](runs/learning_emulation_20261109/REPORT.md) now
exercises this process: three batches supply cumulative proposal evidence,
the previously seen training set supplies replay for weights, and paired head /
readout revisions compete with both an unchanged checkpoint and an equally
trained weight-only control. A small grammar-complexity charge also applies.
The initial batch-only pilot exposed a regression that a control-only comparison
missed; both the emulation and single-neuron `evaluate_proposal` now retain the
unchanged checkpoint in that case. Evaluation reports include its metrics under
`unchanged`, alongside the equally fitted control under `before`.

`learning.py` computes exact batch gradients over fixed output derivations,
including full semantic targets and all candidates before top-k. It preserves
causal prefix execution and refuses to reuse a batch after external model edits.
The concrete revision programs in `learning_emulation.py` were written by the
agent after inspecting saved evidence. They replay that experiment, rather than
claiming to infer these programs automatically or call a live LLM.

## Run a round

Use the existing synthetic model as a starting point, or run
`.venv/bin/python -m storyformers.synthetic` to create a new baseline. Use a
fresh directory for each round. These examples address layer 0, head slot 3;
slot assignments can change when retraining, so inspect the induction report.

```sh
# 1. Training evidence only; no API call.
.venv/bin/python -m storyformers.refine profile \
  --model storyformers/runs/induction_baseline/model.json \
  --train storyformers/runs/induction_baseline/train.jsonl \
  --layer 0 --head 3 --out /tmp/neuron_round/profile

# 2. First inspect the request with --prepare-only; remove it to call Luna/Flex.
.venv/bin/python -m storyformers.refine propose \
  --profile /tmp/neuron_round/profile/profile.json \
  --goal 'Clarify the neuron and feature names while preserving predictions.' \
  --out /tmp/neuron_round/proposal --prepare-only

# 3. Evaluate the completed proposal locally.
.venv/bin/python -m storyformers.refine evaluate \
  --model storyformers/runs/induction_baseline/model.json \
  --proposal /tmp/neuron_round/proposal/proposal.json \
  --train storyformers/runs/induction_baseline/train.jsonl \
  --validation storyformers/runs/induction_baseline/validation.jsonl \
  --out /tmp/neuron_round/evaluation
```

For an output grammar, replace `--layer 0 --head 3` with `--token scissors`.
The next round can use `evaluation/accepted_model.json` as its checkpoint.
Nothing overwrites the original model. A valid rejected candidate is retained
as `candidate_model.json`; an accepted copy is additionally saved as
`accepted_model.json`. Invalid syntax/types are reported without an accepted
checkpoint. Existing artifacts must match exactly when resuming a step.

Annotated inputs can be JSON arrays or one document array per JSONL line. Rich
fields are retained; the workflow evaluates the entire next-latent target.
They must be causal as-of records, such as the output of the
[prefix annotator](PREFIX_ANNOTATION.md). Known `full_story_offline` annotation
files are rejected because their earlier words can contain later information.
Unmarked corpora still require the caller to establish that property.

## Evidence for the LLM

`profile.json` contains the neuron JSON, base checkpoint fingerprint, training
data fingerprint, shared feature registry, and:

- Matched target count, unique prefix count, derivations, rule support, projected
  bundles, and empirical next-latent outcomes.
- Representative matches, helpful matches, harmful matches, and unmatched
  high-loss cases. The helpful/harmful distinction uses the change in gold
  next-latent probability when this neuron is ablated.
- Exact projected values, matching rule IDs, captured source positions, and the
  residual input visible to the selected neuron.
- Shared neuron/rule uses and the other grammar readers/writers of its features.

Examples are bounded by `--max-examples` (default four per category). Context
tails default to sixteen records, with an explicit omitted-record count.
Statistics cover all supplied training documents. A match can help one possible
continuation and hurt another for the same prefix: these are probabilistic
outcomes, not evidence that one of those continuations is impossible. A missing
match is an opportunity for inspection, not a known semantic false negative.

The LLM receives the selected neuron, registry, training statistics and examples.
It does not receive the whole checkpoint, validation examples, or test examples.
Validation is reserved for model selection. Keep test data untouched until
assessing the selected model; repeated validation-driven rounds can overfit it.

## Typed features and coordinated renaming

Registry entries have `type`, `description`, and `origin`. Types include boolean,
string, number, array, object, entity_ref, and json. Null remains unknown.
Booleans are distinct from numbers in grammar matching and target scoring:
`true` does not match `1`, and `false` does not match `0`. Names from the
corpus/schema retain their meaning and type. New features require definitions.

A proposal can introduce a descriptive name for a learned detector:

```json
{
  "feature_definitions": {
    "ends_in_verb": {
      "type": "boolean",
      "description": "The current input token has POS v."
    }
  },
  "bindings": [
    {"source":"__grammar_4","target":"ends_in_verb","value":true}
  ]
}
```

When equivalence is justified, it can instead reuse an existing categorical
feature:

```json
{"bindings":[{"source":"__grammar_4","target":"pos","value":"v"}]}
```

Bindings update positive boolean writes and reads throughout the staged model,
including output grammar consumers. A new boolean name is therefore more than
a cosmetic label that leaves consumers broken. Corpus fields cannot be renamed
this way. Ambiguous value-copy transformations and conflicting merged tests are
rejected. The old registry entry records its binding for provenance.

Semantic equivalence needs evidence. A condition observed at one layer is not
automatically interchangeable with a feature changed by later layers. The
evaluator checks behavior on validation data and contradictions of non-null
observed attributes; neither that check nor an LLM's explanation proves universal
equivalence. The registry is checked during review/evaluation, not a complete
static type system for all possible future inputs.

Registry metadata is persisted inside checkpoints. New induction runs seed
their private feature definitions from their actual learned conditions. Older
checkpoints without registry metadata still load and can be reviewed.

## Grammar and acceptance contract

The [LLM prompt](prompts/refine_neuron_v1.txt) explains the ordinary JSON grammar
syntax. A neuron has name, rules, tables and max_states. Patterns use token,
seq, alt and bounded repeat. Captures, `$ref`, `$lookup`, `$present` and
`$one_of` represent the existing grammar primitives. Membership/presence are
tests; references and lookups can project values. Patterns consume the complete
context, using explicit gaps where appropriate. No Python or arbitrary parser
operations are accepted.

The decoder limits rules, syntax size/depth, repetitions and matching states.
Protected observed fields cannot be rewritten by heads. Feature reads/writes
must be declared, static values must have compatible types, and actual dynamic
emissions are checked on evaluation examples. Shared neuron and rule identities
are retained; conflicting revisions of tied rules are rejected. Base checkpoint
hashes reject stale proposals.

The gate scores full, untruncated next-latent likelihood on validation data.
Acceptance requires improved likelihood, or equal likelihood with no additional
grammar/KV complexity. It also requires no additional contradictions of known
input attributes. Unsupported targets or matching/type failures reject a
candidate. Pure renames can pass without improving likelihood; unchanged
proposals are explicitly identified. This first gate does not measure story
quality or replace a semantic correctness benchmark.

`--fit-epochs N` optionally refits output weights using only training examples.
Both the baseline and candidate receive the same fitting opportunity before
comparison. Head structure/projection changes remain discrete proposals; this
does not add backpropagation through heads or grammar matching.

## LLM transport and recorded round

The adapter uses the existing project credentials and fixed `gpt-6-luna` on
`flex`. Stable instructions are first, with an explicit 30-minute cache
breakpoint; the profile, goal and proposal template come afterward. The same
instruction cache can serve different neurons and objectives. Exact request,
response, usage, proposal and validation artifacts are retained. Completed
responses are reused; ambiguous failures are not silently resubmitted.

The adapter uses [Responses JSON mode](https://developers.openai.com/api/docs/guides/structured-outputs?api-mode=responses)
for the recursive grammar and open feature maps, with strict local parsing and
validation afterward. JSON mode alone does not enforce the revision contract.
The cache layout follows the [OpenAI caching guide](https://developers.openai.com/api/docs/guides/prompt-caching).

The [recorded synthetic round](runs/neuron_review_live_20261107/REPORT.md) includes
an initial unchanged proposal and a naming-focused proposal that renamed the
neuron to `suffix_verb_context`, preserving validation likelihood. It illustrates
proposal generation and measured adoption, not a discovery of new semantics.

```sh
.venv/bin/python -m unittest storyformers.test_neuron_review
```
