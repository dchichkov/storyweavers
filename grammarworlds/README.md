# Grammarworlds

A local, classical prototype of **grammar + next-word distributions + executable
semantics + storytelling**. No LLM, pretrained neural model, external service,
or third-party package runs during generation.

This takes the first proposed route: integrate a weighted grammar with symbolic
kernels and attention. The separate `grammar_completion_experiment/` demonstrates
GF reuse; Grammarworlds itself does not use GF or claim to extend its grammar.

## Run it

From the repository root:

```sh
.venv/bin/python -m grammarworlds --scenario all --seed 7
.venv/bin/python -m grammarworlds --scenario rescue --samples 20
.venv/bin/python -m grammarworlds --scenario key --trace
.venv/bin/python -m grammarworlds --scenario kite --tense present
```

The three situations are an animal stranded on a ledge, a torn kite, and a missing
key beside a locked door. Each story progresses from a visible problem through
an attempt or plan, resource acquisition, a physical solution, and an ending
image showing the changed state. Asking someone for help, planning independently,
making an unsuccessful attempt, stating a goal, and thanking a helper are not
all mandatory steps. Decisions depend on the current world and character state.

Inspect the next-word distribution after a generated opening:

```sh
.venv/bin/python -m grammarworlds --seed 2 --after 1 --complete 'she' --top 10
.venv/bin/python -m grammarworlds --seed 2 --after 1 --complete 'she wanted'
.venv/bin/python -m grammarworlds --seed 2 --after 1 --complete 'she realized'
```

For this seed the hero is Lily. `she` can continue as `asked`, `reached`,
`realized`, `wanted`, or `hoped`. `she wanted` continues with `to`, while
`she realized` continues with `that`. There is no fixed word-position template.
Prefixes must be supported by this world's controlled grammar; this is not a
general English checker. Completion queries have no physical side effects.

Intervene on the same hero and compare distributions:

```sh
.venv/bin/python -m grammarworlds --seed 2 --after 1 --complete 'she' --fear 0
.venv/bin/python -m grammarworlds --seed 2 --after 1 --complete 'she' --fear 1
.venv/bin/python -m grammarworlds --seed 2 --after 1 --complete 'she' --fear 1 --attention off
```

`--json` returns all alternatives, their probabilities, event interpretations,
supporting grammar rule labels, attention evidence, and before/after world states.
`--top 4` limits the text display only. Sampling uses the **full distribution**;
omitted probability mass is reported. Some contexts have fewer than four legal
choices. Punctuation and `<END>` are explicit predicted symbols. The old fixed
eight-word limit has been replaced by grammatical sentence completion.

`--temperature` changes the **event-prior** temperature. It does not independently
temper lexical/grammar choices; their weights remain authored.

## How it works

1. **Semantic support.** Kernels propose frames only when their prerequisites hold.
   A frame identifies actors, patients, instruments, destinations, and causal fact
   IDs. Actors must have required abilities; a useful instrument must be held
   before it can solve the problem. An ending cannot claim a cold animal is warm.
2. **Evidence and attention.** Each kernel has a symbolic query. It attends to
   tagged physical facts, carrier-bound traits such as Fear/Care/Trust, and recent
   structured events. Matching facts receive normalized weights; their authored
   contributions adjust event logits. Availability and locations are refreshed
   from current entities. Attention weights are distinct from event probabilities.
3. **Compositional grammar.** Reusable subject references, noun phrases, verb
   forms, complements, coordination, contrast, and discourse rules build a finite
   weighted forest for all currently legal frames. It supports past/present
   inflection and number-aware verb forms. Each scenario also supplies authored
   clause schemas for its physical events.
4. **Word generation.** No event or complete sentence is sampled in advance.
   Each candidate next word receives the total probability of compatible
   derivations. Sampling a word conditions the forest. Multiple event meanings
   can remain possible until later words disambiguate them.
5. **Execution.** At sentence completion, the system selects an interpretation
   from the remaining semantic posterior and validates its preconditions again.
   Its effects update the world once. The next sentence starts from that state.

For derivation `d` and associated frame `f`, initial mass is

```text
P(d, f | world) = P(f | world) × P(d | f, grammar)

P(next word | prefix, world)
  = mass of compatible derivations continuing with that word
    / mass of all derivations compatible with the prefix
```

Grammar alternatives are normalized within each frame, so adding more paraphrases
does not silently make the corresponding physical action more probable. Shared
prefixes and ambiguous derivations are summed. Surface sentence probability is
the product of its conditional symbol probabilities, including stopping.

This is an authored probability model, **not calibrated uncertainty**, and does
not claim distributional equivalence to a trained language model. Prefix
conditioning uses grammatical/semantic hypotheses; there is no neural token
self-attention. Rule labels in a trace identify supporting derivations, not a
minimal causal explanation for each word.

## Files and extension points

| File | Responsibility |
|---|---|
| `world.py` | Entities, grounded facts, kernel preconditions/effects, three situations |
| `grammar.py` | Weighted phrase combinators, inflection, clause schemas, prefix forest |
| `engine.py` | Evidence scoring, attention, exact next-word marginalization, sampling |
| `__main__.py` | Story, trace, JSON, intervention, and completion commands |
| `audit.py` | Exhaustive reachable-state and grammar-support audit |
| `test_grammarworlds.py` | Behavioral regression tests |
| `samples.txt` | Twenty unfiltered reproducible generated stories |
| `evaluation.json` | Saved audit counts and fear/attention interventions |

To add a situation, give physical entities their states and affordances, add its
problem/solution effects and clause realizations, then extend the semantic and
generation tests. To add an event family, add a kernel, its effect, and its grammar
realization. The current implementation requires Python edits; it has no external
rule-pack format yet.

## Verification

```sh
.venv/bin/python -m grammarworlds --verify
.venv/bin/python -m grammarworlds.audit
```

Tests include 180 sampled stories (three situations, two tenses, 30 seeds), plus
exhaustive default-world support audits. They check normalization, exact prefix
marginalization, sentence likelihood, reproducibility, agreement, physical
preconditions, no mutation while predicting, changing attention under interventions,
grounded completion, and endings. These are mechanical checks, not literary grades.

The support audit counts 49 reachable states for rescue and 57 each for kite/key
at seed 2. It checks every available semantic transition and every grammatical
realization at those states. Histories with identical physical/discourse state
are merged for **support counting**, not probability estimation. Physical state
transitions make monotonic progress, so no default-world path ends in a loop or
unresolved dead end. Different lexical descriptions do not secretly alter effects.

## Scope, quality, and next experiment

- There are **11 authored event kernels**, not thousands. Shared grammar rules
  compose into many full-story derivation paths; those counts are neither
  independent plots nor evidence of human-level grammatical coverage.
- This is controlled English and three authored recovery situations. The plots
  share a recovery arc and successful endings. New situations need new semantic
  rules; broad domain-independent storytelling remains future work.
- The finite forest is explicitly enumerated. That is small and exact here, but
  a large recursive grammar needs a packed incremental chart rather than materialized
  derivations. No claim of scaling to thousands of rules has been tested yet.
- Ordinary random samples have an introduction, physical change, and final image.
  Known roughness: repetitive names/verbs, repeated `then`, sparse motivations,
  formulaic helpful parents, and little dialogue. No post-generation prose repair
  or selection of only successful samples is used.
- The next meaningful scale test is more **semantic and syntactic coverage**, not
  duplicating equivalent rules: add an event family with different argument
  structure, multiple competing goals, and a larger grounded lexicon; then track
  valid completion, semantic contradictions, structural diversity, and latency.
  With a teacher/reference corpus, also measure held-out next-word log loss or KL.

The north star is partially realized: concepts are attached to physical carriers,
accumulated state affects behavior, and effects precede subsequent narration.
The full `Story`/memeplex compositional algebra is not implemented. This package
is isolated from gen6/gen7; their engines, packs, and dataset tooling are unchanged.
