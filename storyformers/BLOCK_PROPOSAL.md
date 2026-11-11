# Proposal: reusable Storyformer blocks

Status: design proposal following inspection of grammarworlds and Storyformers.
The compact first implementation is now documented in [GRAMMAR.md](GRAMMAR.md):
reusable grammar neurons, causal heads/layers, joint projection, generation and
fixed output-rule weight training. This proposal also describes future extensions.

## Recommendation

Use a fixed-length causal residual stream of token records. Each layer has
16 configurable head slots. A head recognizes a weighted grammatical pattern,
binds its captures, selects evidence, retrieves a value by copying or table
lookup, and proposes a weighted attribute update at the current query token.
All heads read the same layer input. Their updates combine once to produce the
next layer. Heads can strengthen or suppress attributes while preserving the
original token and its position.

```text
previous-layer token records
          |
          +--> typed grammar matches + query/capture bindings
          |          |
          |       16 heads, each reading the same input
          |          |
          |       copy / key-value lookup / projection
          |          |
          +------> combine weighted attribute deltas
                     |
               next-layer token records
                     |
               structured next-latent readout
```

The weighted grammar determines which evidence a head can address. The value
projection determines what information it transmits. The residual operation
determines which attribute it changes. These are separately inspectable and
potentially separately trainable stages.

## What grammarworlds actually provides

### Latest update: grammar rules already carry projection

The newer [SemanticRules](../grammarworlds/storytelling/semantic_rules.py),
[attribute expansion](../grammarworlds/storytelling/attribute_grammar.py) and
[AttributeForest](../grammarworlds/storytelling/attribute_sampler.py) go beyond
the earlier word-only head receiver. Typed grammar constructions carry bound
attributes, and expansion projects them into complete correlated word/attribute
alternatives. Bundle weights can be adjusted and then marginalized into word
probabilities. Conditioning on a word retains its alternative attribute bundles,
and that posterior affects the next prediction. A separate neural-style linear
projection is therefore one optional parameterization, not a requirement of
Storyformers: a weighted grammar unit can include its own retrieval, binding and
typed output projection.

This is candidate attribute construction and probabilistic conditioning; it is
not yet a generic instruction engine for arbitrary residual edits. Keep the
explicit update/merge contract, while allowing grammar productions themselves
to emit the attribute payload and its weight. The joint sampler's preservation
of correlations is a stronger initial model than independent attribute sampling.

### Shapes and parameter sharing

With five input positions and a shared bank of G grammar units, the conceptual
evaluation grid is `5 x G`, with weighted projected payloads alongside activation
strengths. Reuse the same grammar definitions at each position. If G is chosen
to equal vocabulary size V, the grid is `5 x V`, but it still contains V shared
grammar definitions rather than 5V independent learned grammars.

The marginal word output is `5 x V` when predicting at all input positions, or
`1 x V` for only the next token after the five-token context. Internally the
output is a sparse joint distribution over `(word, complete attribute bundle)`;
multiple bundles may share one word. Display at most ten word marginals while
retaining their bundle alternatives. One grammar may emit several words and
one word may be supported by several grammars, so G need not equal V.

The preferred first readout can directly accumulate grammar-produced joint
candidate mass and normalize it. An additional learned feature-to-word matrix
is an alternative design to test, not mandatory infrastructure.

### Vocabulary-indexed attributed grammar readout

A concrete first output architecture can have one entry per vocabulary token:
`output_grammars[token]`. Each entry names a weighted attributed grammar root.
The root receives the complete visible latent context and can match patterns
anywhere in that context, bind/retrieve values and project complete candidate
attribute bundles. Its output token is fixed by the root entry, while its
attribute bindings can vary. Include an explicit END root.

```text
G_scissors(context) -> [(complete_scissors_bundle_A, mass_A), ...]
G_needle(context)   -> [(complete_needle_bundle_B, mass_B), ...]
G_thread(context)   -> [(complete_thread_bundle_C, mass_C), ...]

mass(word, bundle | context)
  = root_prior(word) * sum(weights of compatible projecting derivations)

P(word, bundle | context) = mass(word, bundle | context) / total_mass(context)
P(word | context)         = sum_bundle P(word, bundle | context)
```

These grammars include their projection: setting a candidate's entity, role,
location, modality and event is part of constructing the output bundle. A
separate linear unembedding matrix or independent attribute classifier is not
required. Final output normalization divides joint candidate mass by its total.
The token distribution is its marginal; top-ten selection follows that
marginalization and retains bundle alternatives for the displayed tokens.

Whole-context matching means the matcher can inspect every latent within the
causal window, including attributes, order, identity and scope. A pattern can
constrain only relevant spans and permit intervening context through explicit
bounded gap/skip productions. It does not require memorizing one literal rule
for every possible five-token context. Shared subgrammars and parameterized
lexical leaves allow V output roots to reference one reusable grammar graph.
Index active rules by features to avoid unnecessarily scanning every root;
approximate pruning must be recorded rather than confused with exact support.
An explicit backoff/unknown construction is needed when no specific root matches.

The current implementation supplies the output-bundle and posterior model:
SemanticRules tags constructions, candidate_attributes projects one complete
bundle per candidate terminal, and AttributeForest.predict groups joint mass
by word and bundle ID. It does not yet recognize arbitrary input latent records:
build_forest expands typed scene candidates, and live observations condition the
derivation lattice. The reusable latent-context recognizer is the extension.

Preserve the sampler's cross-step correlations. Observing a word can retain a
posterior over its complete bundles; later prediction must consume that posterior
and its history bindings. A word or attribute observation can condition the same
lattice. One slot can therefore hold one observed word with several complete
semantic alternatives. Taking separate per-field maxima would discard bindings
that this implementation already preserves. Vocabulary root weights and grammar
production weights can learn from complete annotated next-latent targets.

| Existing component | Observed behavior | Reuse for Storyformers |
| --- | --- | --- |
| [Node/seq/choice/expand/Forest](../grammarworlds/grammar.py) | Weighted phrase generation and next-word mass from compatible finite derivations | Compositional rule vocabulary and normalized alternative weights |
| [HeadLibrary](../grammarworlds/symbolic_heads/runtime.py) | Scoped source selection, feature projection, then receiving word-score adjustments | Separate selection, value projection, receiver, confidence and trace contracts |
| [AttributeForest](../grammarworlds/storytelling/attribute_sampler.py) | Joint word/bundle predictions and conditioning that feeds later predictions | Direct structured grammar projection, bundle receiving and correlated uncertainty |
| [StoryHeads](../grammarworlds/storytelling/head_adapter.py) | Supplies selected heads with conservative prefix/world inputs | Explicit adapters rather than pretending an arbitrary token stream already has parsed roles |
| [Typed phrase records](../grammarworlds/portable/features.py) and [verb constructions](../grammarworlds/portable/verbs.py) | Agreement, case forms, verb valency and typed complements | Typed grammatical features and reusable NP/VP/clause patterns |
| [Discourse](../grammarworlds/portable/discourse.py) | Introduces entity IDs, resolves feature-compatible accessible references, opens/closes scopes | Scoped referent lookup and ambiguity handling |
| [Symbolic positions](../grammarworlds/symbolic_heads/positions.py) | Exact relative offsets, optional discrete rotary representation, positional source filtering | Relative position features after aligning token units and namespaces |

Direct library inspection found **64 contracts: 15 executable table heads and
49 deferred program heads**. The storytelling adapter supplies inputs for six
head IDs. Contract IDs are not physical transformer head slots. The larger
research inventory is also not a trained model architecture.

The current table pipeline is:

```text
(query, source key) -> selection weight
(query?, source key) -> feature distribution
(query?, feature, next word) -> count or multiplier
```

Selection uses source confidence and scope. Projection preserves competing
feature values. Receivers combine log adjustments and preserve the existing
grammar's allowed word set. A missing selection/projection abstains; it does
not invent a value. Source IDs and explanations remain in the trace.

There are three limits to direct reuse. Its tables consume already structured
sources rather than parse arbitrary latent sequences; its receivers reweight
word or attribute-bundle hypotheses rather than provide arbitrary residual-edit
instructions; and its current grammar enumerates
finite surface derivations rather than providing a general feature-grammar
recognizer. Storyformers needs those new components. Deferred programs such as
entity joins or belief tracking do not become implemented by renaming them heads.

## What to borrow from GF and Codeco

GF separates abstract syntax from concrete realizations and represents grammatical
objects using records, tables and parameters. Its resource grammars expose typed
phrase construction. Borrow that separation: grammatical categories and bound
roles are distinct from literal surface spellings. This lets several forms share
one semantic rule. See the [GF reference manual](https://www.grammaticalframework.org/doc/gf-refman.html)
and [RGL tutorial](https://www.grammaticalframework.org/lib/doc/rgl-tutorial/index.html).

Codeco supplies declarative references and accessibility scopes, with an
incremental chart-parsing approach for predictive editing. Its lookahead concerns
possible grammatical continuations of an observed prefix. That does not require
reading the continuation that will actually occur. Borrow scoped antecedents,
partial parse states and expected categories; keep uncertainty for unrestricted
story text. See [Kuhn's paper](https://arxiv.org/abs/1211.3643).

These are inspirations for a bounded Python subset. The proposed weighting,
residual updates and training procedure are our design, not an existing GF or
Codeco transformer implementation. Neither a full GF runtime nor the complete
ACE grammar is required for the first block.

## Residual representation

Keep three distinct parts of each token record:

1. **Observed data:** exact token, normalized token key, occurrence ID, character
   span, story namespace and structured position. Heads cannot overwrite these.
2. **Feature state:** sparse competing values and signed evidence for POS,
   entity identity/type, grammatical role, event, holder/location, etc.
3. **Provenance:** source token IDs, grammar rules, head/layer IDs and causal
   dependency positions for each contribution.

Expose a readable dictionary view, such as `location: "Lily"`, when the candidate
has enough support. Internally keep the candidates and evidence rather than
destructively replacing a string. Store entity references by identity; resolve
canonical names for display. This avoids conflating two people with the same
name. Unknown remains a real option.

Use categorical candidate scores initially. Include an explicit unknown candidate
with a baseline score, so one tiny positive contribution does not normalize to
certainty merely because it is the only retrieved value. Normalize the candidate
scores when a head reads a feature or the renderer exposes a dictionary. Numeric
concept magnitudes require a separately typed operation when introduced; they
should not accidentally share categorical softmax semantics.

For field `a`, candidate `v`, query position `i`, and layer `l`:

```text
S[l+1, i, a, v] = S[l, i, a, v] + sum_h Delta[h, i, a, v]
```

Suppression is negative evidence for a candidate, with its source retained.
The displayed attribute can disappear into unknown as its support falls. It is
not necessary to erase the observation or delete the token to suppress a feature.
Removing an entire feature can initially be expressed as suppressing its known
candidates; a separate irreversible erase operation is unnecessary.

This representation makes contradictory heads inspectable. Adding their deltas
is order-independent; a final normalization happens after the merge. Repeated
evidence within one head is deduplicated by evidence identity. Contributions from
different heads remain explicit; learned gates and ablations must detect harmful
double counting rather than treating sixteen votes as sixteen independent facts.

## Head contract

| Stage | Required definition |
| --- | --- |
| Query | Which current latent/feature distribution is asking, and what fields can it read? |
| Key grammar | Which prefix patterns can supply evidence? Include captures and typed constraints. |
| Scope | Same clause/sentence, accessible discourse scope, or bounded earlier context |
| Match score | Grammar derivation weight, feature compatibility, relative position preference and learned coefficients |
| Activation | Competition with a null match, evidence confidence, and head strength |
| Key extraction | A typed tuple of captured values, such as `(verb_class, lemma)` |
| Value retrieval | Copy a captured feature distribution or read a declared key-value table |
| Projection/write | Map retrieved values to typed attribute deltas at the query token |
| Trace | Matched spans, captures, retrieval key, attention, gate, operation and resulting score change |

Queries and keys are separate: the current token chooses what it needs, while a
grammar identifies possible sources. An individual head is one attention/value
operation; the block contains the heads and merge, and the model stacks blocks.

Use a small declarative grammar: `TokenTest`, `Seq`, weighted `Alt`, bounded
`Repeat`, `Capture`, shared nonterminal references and typed feature equality.
Match fields such as lemma/POS/number/entity ID, not just literal words. Patterns
must expose their captures. Cross-scope or type-incompatible matches are rejected
before weighting. Missing features are unknown rather than wildcard facts.

Start with a memoized bounded recognizer for finite patterns. Retain an interface
for packed weighted chart items as shared NP/VP patterns grow; a full chart parser
is a later implementation step, not already provided by grammarworlds. Recursive
or zero-width cycles must be rejected in the first grammar subset. Bound repeat
length, span width and retained matches; report pruning in the trace.

Normalize alternative rule weights locally. Sum the mass of distinct derivations
for the same semantic binding instead of selecting whichever parse happens to
appear first. Exact duplicate derivations/evidence IDs should not be counted
twice. Normalize source attention over matches **and a null match**. A single
weak source must still be able to produce a weak update or abstention. Confidence
gating is distinct from relative attention, following the existing library's
useful separation. Bound total write magnitude per head/query.

## Operations

| Operation | Effect |
| --- | --- |
| `add(attribute, value, weight)` | Add support for a categorical value |
| `suppress(attribute, value, weight)` | Subtract support for a categorical value |
| `copy(capture, source_attribute, target_attribute)` | Retrieve a captured distribution, project it into additive target evidence |
| `lookup(table, captured_key, target_attribute)` | Retrieve a sparse value distribution, project it into additive target evidence |

Copy and lookup retrieve values; add/suppress determine how those values affect
the residual. Their strengths include the match attention, confidence and head
gate. No lookup hit means abstention, not an invented default result. Tables
declare key types, output types, provenance and whether numbers are counts,
probabilities or authored weights.

The first release keeps the token sequence length fixed. Inserting/deleting
tokens would also change positions, causal caches and teacher-forcing alignment;
that is a separate sequence-editing model. Additional memory slots can be explored
later with explicit addressing and masks.

## Example: obtaining scissors

Suppose an earlier layer has identified the actor and the current query is the
scissors token in the observed prefix `Lily took scissors`. A reusable rule binds:

```text
AcquirePhrase :=
    Capture(actor, NP[entity_id known])
    Capture(verb, V[lemma in acquisition_lexicon])
    Capture(patient, NP[head_position == query_position])
```

One head copies the captured actor identity into the patient's `location`
candidates. Another retrieves an event label from the verb-class table and adds
`role=patient` / `event=obtain object` evidence at the query. This rule can work
with another actor or object without enumerating every complete sentence.
Names and entity bindings are inputs from earlier prefix-safe processing; the
grammar does not magically provide general entity resolution.

Negation, intention and hypothetical scope are eligibility conditions for the
holder update. `Lily did not take scissors` must not create location Lily.
`Lily wanted to take scissors` must distinguish desire from acquisition. Ambiguous
actor/referent matches preserve alternatives or abstain.

If a later sentence says that she mended a coat, an offline annotator can label
the earlier acquisition `obtain repair tool`. The causal generator may predict
that label as part of its complete next latent, and subsequent generation can
condition on the predicted purpose. It cannot use the actual later sentence as
evidence at the earlier step or retroactively change a cached earlier state.
Full-context annotation and causal generation remain distinct operations.

## Layer execution and causal writes

```python
def block_forward(previous_layer, heads):  # proposed interface
    deltas = []
    for query in previous_layer.positions:
        visible = previous_layer.causal_view(query, context_size=256)
        for head in heads:  # 16 slots; disabled slots return no contribution
            deltas.extend(head.propose(query, visible))
    return previous_layer.apply_merged(deltas)
```

All sixteen heads read the same immutable `previous_layer`. Head 7 does not
consume head 2's new output in the same block; that dependency takes another
layer. This is parallel semantics even if the Python implementation runs the
head calls in a loop.

For query `i`, read only source positions `j <= i`, and initially write only the
output for `i`. An earlier token's next-layer features may read its own earlier
prefix, but must not acquire information from later queries. This restriction
preserves cached earlier states and prefix invariance. Attribute edits to other
positions can be a separate analysis mode with recomputation rules.

The block should also expose an optional positionwise feature-transform stage
after attention, initially identity. This is the place to add a symbolic analogue
of an FFN later. Sparse feature normalization and bounded update strengths are
explicit design choices; dense layer normalization is not required to manipulate
these dictionaries.

## Integration issues already present

**Token units:** annotation arrays include spaces; the predictor currently drops
them. Their position formats also differ: annotation has a structured dictionary,
while the current WordNet encoder uses an integer. Add an explicit residual
adapter before connecting the two. Recommended canonical stream: lossless token
occurrences, a 256-occurrence window, structured global positions, and a grammar
view that skips whitespace while mapping captures back to original token IDs.
The frequency readout can skip spaces for lexical n-grams. Version the changed
window convention; compare baselines using identical windows and token units.
Clipping must not renumber global positions or pretend an evicted antecedent is
still present.

**Position bias:** start with exact signed token/sentence offsets and declared
scope constraints. Optional symbolic rotary features can be adapted later, but
the existing grammarworlds positional adapter uses declared token units that can
even be multiword. Convert units explicitly. Relative position does not itself
enforce causality or resolve anaphora. Do not use percentage-through-story features
that require knowing the future text length.

**Readout:** the current [FrequencyHead](head.py) reads only `latent['token']`.
Changing `location`, `pos` or `role` therefore cannot change its predictions.
Add a structured next-latent readout with token and attribute prediction channels.
Use a feature receiver, following the grammarworlds count/multiplier idea,
to adjust the frequency prior from derived features. Keep a zero-strength mode
that exactly recovers that prior. Rerank the sparse internal candidate row before
selecting the top ten for display, otherwise useful candidates may have already
been discarded. Initially keep the base support fixed and report candidates
outside it; expanding support can be a separately tested policy. When an explicit
output grammar supplies a hard allowed set, heads cannot revive excluded words.

**Training:** the current optimized count trainer bypasses blocks and explicitly
rejects non-pass-through blocks. Its persistence format also stores no head
definitions or learned block state. Add a training path and a versioned checkpoint
that save grammar/table versions, weights, layer configuration and feature schema.

## Full next-latent supervision

The supervised target at each step is the entire annotated next token record:

```text
context: preceding latents, up to the context limit
target:  {token, pos, entity, role, location, event, ...} at the next position
```

The model predicts distributions over the token and its semantic attributes.
Attribute supervision is part of the primary training objective. The sixteen
attention heads are reusable computations feeding this structured readout;
there is no requirement to dedicate one attention head to each target field.

The public readout returns a **sparse next-token distribution**, initially the
top ten token candidates, together with each candidate's complete latent
description and conditional attribute distributions. It does not collapse its
prediction to one token. A candidate's token probability is its marginal
probability; uncertainty about its attributes belongs to the conditional
structured distribution described below. A displayed complete latent can be a
representative hypothesis, and must not be confused with all conditional mass.

```text
next-token probability   complete candidate latent / attribute hypotheses
0.60                    scissors + POS, entity, role, location, event, ...
0.25                    needle   + POS, entity, role, location, event, ...
0.15                    thread   + POS, entity, role, location, event, ...
```

Normalize the displayed token probabilities over retained candidates and expose
their retained mass, as in the current frequency baseline. Keep the internal
conditional attribute distributions for training and structured decoding.
The supervised complete next latent is scored against the token distribution
and that token's conditional attribute distribution. Top-ten truncation is a
prediction/display choice, not a reason to omit a gold target during training.

A practical factorization is:

```text
P(next latent | context)
  = P(next token | context)
    * P(next attributes | context, next token)
```

This is a probability identity, not a requirement to build separate projection
matrices or independently sample attribute fields. Following the latest
AttributeForest, prefer grammar-generated complete bundles with joint weights;
sum them to get word marginals and condition them to get attribute posteriors.
Keep correlations between fields and, when retaining uncertainty across steps,
between history hypotheses. Separate conditional field predictors remain an
optional approximation to compare, rather than the required architecture.

During training, score the target word and complete bundle against the joint
prediction. A conditional attribute decoder, if used, may condition on the
target token under this factorization; that token must not enter the context
blocks or next-token predictor. During generation, conditioning on the selected
word can retain its distribution of complete bundles, as AttributeForest does.
An explicit semantic commitment can select one bundle; neither path leaves
attributes to be filled by an external annotator. Positions are attached locally.

Completeness is a hard interface requirement: the next prediction consumes the
whole previous latent, including its predicted attributes. Attribute outputs are
part of the autoregressive state. Internal token/attribute factorization happens
within one generation step; generation does not advance after predicting only a
word. A generation policy selects a token from the sparse distribution and
decodes a compatible complete attribute assignment before appending. The readout
itself remains a distribution. Multiple continuation branches may instead be
maintained explicitly, each with its own complete latent history and branch
weight; alternatives are not concatenated as successive tokens in one history.

```text
training:
    complete gold latents through t -> complete gold latent at t+1 as target

generation:
    C_t -> blocks -> top-ten next-token distribution + candidate latent attributes
        -> generation policy selects token and complete attribute assignment z_(t+1)
        -> attach deterministic positions -> validate required fields/references
        -> C_(t+1) = append(C_t, z_(t+1)) -> predict the next complete latent
```

Every required field is present before append, including explicit null/unknown
values when appropriate. A missing field is a structural error. The generation
loop has no external annotation or later LLM enrichment step. A text prompt must
also be converted into complete seed latents locally, using lexical features,
deterministic metadata and model-predicted attributes or explicit unknowns.

Use a weighted structured loss:

```text
L = L_token + lambda_pos * L_pos + lambda_entity * L_entity
    + lambda_role * L_role + lambda_location * L_location
    + lambda_event * L_event + ...
```

For example, correctly predicting scissors still incurs error if its predicted
role, holder or event disagrees with the supervised next latent. This gives
copy/lookup/suppression computations a direct learning signal even when token
accuracy is unchanged. Loss weights balance fields rather than allowing frequent
POS labels or mostly-null fields to dominate the objective.

Entity/holder references should be supervised as pointers to accessible entity
identities, with explicit new-entity and unknown outcomes, rather than learning
story-local e1/e2 strings as universal vocabulary. Canonical names remain the
readable view. Distinguish a missing annotation, which is masked out, from an
explicit annotated null/unknown label. Positions, offsets and deterministic
whitespace/punctuation features need no learned prediction loss.

Teacher forcing uses the complete annotated prefix as input and its next complete
latent as the target. No part of that next latent enters the context blocks.
During rollout, complete generated latents replace gold prefixes. Measure this
rollout setting as well as teacher-forced structured loss. Full-story annotations
define an annotated-sequence modeling task; its scores should be distinguished
from ordinary text-only next-word scores. A label informed by later text can
remain uncertain from the current prefix, so retain calibrated distributions.

## What can learn

Start with authored grammar structure and operation types. Learn rule-alternative
weights, selection weights, key-value count distributions, head gates and receiver
strengths. This is parameter learning within a declared symbolic architecture;
automatic grammar/program induction is a separate milestone.

Initially use count estimation for conditional tables and bounded optimization
of a small set of gate/rule logits. The full next-latent objective above uses
the Luna annotations to supervise both token and attribute distributions and
tune feature receivers. An end-to-end gradient trainer requires additional choices about
discrete matches and candidate support and is not established by this proposal.

Luna supplies complete training sequences offline. Runtime consumes complete
seed/generated latents and produces the next complete latent itself. A text-only
input ablation can use WordNet candidates and deterministic positions, but the
primary training contract uses complete annotated prefixes and next-latent targets.
Split by story before collecting counts, tuning grammar weights or inducing
examples. Report next-token loss/coverage alongside attribute accuracy, head
activation, actual prediction changes, abstention and runtime.

The current next-token baseline can assign zero probability to an unseen target.
Report that coverage and infinite loss honestly; add an explicit unknown/backoff
policy before claiming a finite general held-out perplexity.

## First implementation slice

Create the reusable block with sixteen configurable slots and initially populate
three small heads: one copy head, one key-value head and one suppression head.
Disabled slots are neutral. Demonstrate each on several entity/object names and
on counterexamples, rather than filling sixteen slots with brittle bespoke rules.

Suggested modules: `residual.py` for candidate evidence and immutable views,
`matching.py` for typed weighted patterns and captures, `blocks.py` for
HeadSpec/HeadResult/StoryformerBlock, `tables.py` for retrieval, and a distinct
feature receiver alongside the existing token-frequency head. Validate declared
read/write types and protected fields at load time.

Required gates:

- Zero-strength/disabled heads preserve the baseline under the same token/window
  convention; inputs and observations remain unchanged.
- Appending or replacing future suffixes cannot change earlier output states.
  Full evaluation equals incremental cached evaluation.
- Reordering heads preserves merged outputs; type conflicts, missing keys and
  unmatched patterns have explicit behavior.
- Copy, lookup and suppression produce independently checked weighted results;
  low evidence retains unknown mass instead of false certainty.
- Scope tests cover ambiguity, negated acquisitions, desired actions, transfers
  and returning an object. Locations stay tied to the correct entity and time.
- Grammar matches preserve raw positions across spaces, quotes and a clipped
  context. Charts/caches are scoped by story, layer, input revision and grammar
  version; budget pruning is visible.
- Feature interventions measurably change the readout, and zero-strength
  receivers recover its prior. Top-ten display is applied last.
- Full next-latent scores penalize wrong attributes even when the token is right.
  Attribute decoding receives the gold token only in its declared conditional
  training branch; generation uses the selected token. Missing annotations and
  deterministic positional fields are masked appropriately.
- Generation appends a complete predicted latent before the next step, and the
  next step demonstrably consumes its attributes. Missing required fields fail
  validation; explicit unknowns are valid. No external annotator is invoked.
- Readout preserves up to ten token candidates and their probabilities, complete
  latent hypotheses, conditional attribute uncertainty and retained token mass.
  Selection is separate; training scores gold targets before display truncation.
- Teacher forcing reads only complete gold latents before the target position;
  free rollout uses complete generated latents. Save/load preserves definitions,
  learned weights, prediction behavior and traces.

For the memeplex north star, these residual features are hypotheses about
identified carriers, not permission to mutate physical world state. An eventual
world adapter must check legal moves and embedded concept magnitudes before
committing events. Feature suppression must not erase a carrier or conceal an
incompatible physical action. The first implementation establishes a causal,
inspectable feature-computation layer toward that integration.
