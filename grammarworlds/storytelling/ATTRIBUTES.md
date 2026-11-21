# Joint annotated-token generation

`storytelling.generate()` now predicts a joint distribution over the next surface
unit and its typed semantic attributes. All seven storyworlds use it by default.
This replaces the word-only sampling path; the earlier post-commit
`token_annotations` exporter remains available as a separate diagnostic.

```sh
.venv/bin/python -m grammarworlds.storytelling --scenario all --seed 7 --json
.venv/bin/python -m grammarworlds.storytelling --scenario kite --heads --continuations expanded --json
# Comparison against the original word-only sampler:
.venv/bin/python -m grammarworlds.storytelling --scenario kite --surface-only --json
```

Python: `generate(..., predict_attributes=False)` selects the old sampler.
`build_forest(..., predict_attributes=True)` constructs the incremental annotated
forest explicitly; its default remains the stateless old forest for existing
inspection tools.

## What is authored

The existing seven scene plans already call typed constructions with bound
entities, predicates, complements, tense and polarity. `SemanticRules` preserves
those arguments as inert grammar-node metadata, before expansion or sampling.
Shared construction annotations therefore cover all seven plans without copying
119 event-specific templates. The portable GF/Codeco implementation is unchanged.

| Field | Meaning and scope |
|---|---|
| `pos`, `syntax_role` | Terminal category and constituent role; a multiword noun can occupy several word terminals. |
| `entity` | Explicit physical referent, including bound pronouns; a common noun is not automatically an entity. |
| `entity_features` | Current name, type, number, pronoun, location, properties, state and concept magnitudes for that referent. |
| `state_scope` | Always `before_scene`: no hypothetical post-event state is supplied as an observed fact. |
| `nominal` | Typed noun description, modifiers, number, determiner or possessor when available. |
| `clause` | Subject binding/description, predicate slots, tense and polarity. |
| `action` | Current finite or embedded predicate, lemma, arguments, modifiers and modality. |
| `action_scope` | Finite clause, embedded action, or scene context. |
| `assertion` | Narrated candidate, reported speech, hypothetical action or negated clause. None authorizes a physical commit. |
| `quoted`, `speaker`, `listener` | Dialogue scope and explicit attribution. |
| `modifier` | Preposition and its typed object, when supplied by the construction. |
| `event` | Proposed scene name, coarse frame roles, declared causes and attention tags. These are not every clause's roles. |
| `unresolved` | Missing or inapplicable token-local categories, retained explicitly rather than fabricated. |

Positions and symbolic rotary coordinates accompany emitted units in
`attribute_generation.tokens`. Namespace creation uses generation configuration,
not future generated text. Unit boundaries preserve the word sampler, including
punctuation; this does not turn sentences into multiword tokens. A custom Node can
still contain a multiword terminal.

## Sampling and conditioning

A derivation carries both surface terminals and corresponding attribute bundles.
The sampler maintains its posterior mass. At a step it groups this mass by
`(next word, complete attribute bundle)`; summing over bundles gives the word
probabilities used by the existing sampler.

After selecting only a visible word, `observe()` conditions the derivation
posterior. Different interpretations of that word survive with their relative
weights. Later predictions use those retained weights, preserving correlations
between participants, events and future words. They are not independent attribute
marginals.

For example, `took/scissors = .40` and `took/tape = .25` give `P(took) = .65`.
After selecting `took`, the patient distribution is `.61538/.38462`. Explicitly
binding the tape alternative changes the next-token distribution; it does not
merely change an exported label. The regression test also applies a tape-bundle
multiplier of two: the conditional patient distribution becomes
`scissors = .44444, tape = .55556`.

`AttributeForest.rerank_attributes(prediction, factors)` accepts positive authored
multipliers keyed by complete bundle ID, normalizes the joint, and updates its word
marginals. This is the receiving interface for heads scoring semantic bundles.
`observe(word, prediction, attribute_id=...)` optionally makes a specific semantic
commitment; ordinary story generation retains uncertainty instead.

At `<END>`, the final event is selected from the conditioned posterior. Only then
does the existing guarded world operation commit. Unnarrated operations predict
an annotated `<END>`; they do not invent visible words.

## Head integration

Existing word-head scores lift into the joint as a factor shared by all bundles
with the same word, preserving `P(attributes | word)`. Subject-dependent agreement,
concept and instrument adapters now consume the previous token's weighted entity
bindings when an annotated forest is present. These bindings distinguish explicit
subjects and quoted speakers without requiring name/pronoun guessing. Current
physical carriers supply their actual feature values.

The old prefix recognizers remain for the surface-only ablation. Other heads still
use their existing inputs. Not every new attribute has a receiving head, and no
new weights were learned. General bundle reranking is exposed and tested, but the
shipped story heads currently rerank words rather than assign different scores to
two bundles with the same word. Long-range attention over the whole annotated
history and rotary-distance scoring are follow-on work; the live adapter currently
uses the previous token's posterior and persistent world state.

## Trace format and inspection

Each event trace has an `attribute_table`. Its compact IDs (`a0`, `a1`, …) are
interning references local to that scene, not semantic event names. Each word step
has:

- `choices`: the marginal word distribution;
- `annotated_choices`: the joint distribution, with references into that table;
- `selected_attributes`: the conditional bundle distribution immediately after
  the visible word was selected.

`attribute_generation.tokens` retains the same online posterior and its positions.
Later evidence can refine earlier interpretations internally; exported emission
records are not rewritten with hindsight. `scene_index` identifies the table and
occurrence, so semantic names may repeat. Complete traces include losing
candidates, while the readable token files inline each selected word's alternatives.

See [seven annotated stories and comparison report](../runs/attribute_generation_20261106/report.md).
Reproduce it with:

```sh
.venv/bin/python -m grammarworlds.storytelling.attribute_experiment --seeds 10
.venv/bin/python -m unittest grammarworlds.test_attribute_generation -q
```

The comparison covers 140 matched runs with heads off and 140 head-enabled runs,
across original and expanded grammar. All 119 registered scene kernels appear
among the offered candidates, including silent ones. Preservation of prose, state,
QA and probability distributions is a correctness gate, not an independent
story-quality improvement claim.

## Bounds

This remains a finite authored grammar with exact bounded enumeration, not a
learned transformer or an arbitrary-English annotator. Candidate structure can
specify intended future participants; these remain hypotheses until the prefix
and commit resolve them. Complex nested reporting/negation and flattened noun
constructions need richer scope/category annotations before generalizing beyond
these controlled grammars. Unknown fields are retained rather than inferred from
noun spelling. Noun-phrase referent tags can include determiners and modifiers.

The design keeps semantic features attached to physical carriers, reads accumulated
state, and commits only compatible moves. This follows the memeplex north star;
metadata itself never creates a carrier or executes an imagined action.
