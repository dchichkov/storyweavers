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

## Luna quality and diversity evaluation

The [baseline report](runs/luna_baseline_20261103/report.md) evaluates unchanged
generation using the repository's shared story-set rubric and calibration story
(`storyscenes/evaluation/openai_world_set_quality.py`), with the validated
`harbor_judge_protocol` output format. The judge is `gpt-6-luna`, Flex, reasoning
`none`. Scores are **0–9**, not the older gen6 1–5 rubric.

We generated 100 consecutive seeds (777–876) per scenario and selected 20
positions uniformly without replacement per scenario, using selection seed 777.
Duplicates were retained; no filtering, rewriting, or cherry-picking occurred.
Luna sees only prose and the shared calibration, not world state or trace data.

| Scenario | Mean quality / 9 | Set diversity / 9 | Judge plot groups |
| --- | ---: | ---: | ---: |
| Rescue | 6.00 | 1 | 2 |
| Kite | 6.15 | 2 | 3 |
| Key | 7.00 | 2 | 2 |

Across 60 judged stories: overall **6.38**, coherence **7.67**, grammar **8.33**,
style **6.05**, storytelling **6.05**. Mean within-scenario diversity: **1.67**.
All 300 sampled texts were distinct, but these are largely surface variations:
the judge identifies self-directed versus adult-assisted solutions, with an
occasional failed attempt. Problems and successful endings barely vary. Event
sequences had 11/16/15 distinct paths, which include optional goals/thanks and
must not be interpreted as distinct plots. These are diagnostic samples, with
one judge response per set; no cross-scenario diversity score is claimed.

Prepare a fresh reproducible run locally, then explicitly call the judge:

```sh
.venv/bin/python -m grammarworlds.judge prepare --out grammarworlds/runs/my_run
.venv/bin/python -m grammarworlds.judge run --out grammarworlds/runs/my_run
.venv/bin/python -m grammarworlds.judge report --out grammarworlds/runs/my_run
.venv/bin/python -m grammarworlds --verify
```

`prepare` accepts `--pool-size`, `--judge-count`, and `--seed`; it refuses to
overwrite an existing run. `run` uses the existing `openai` SDK and reads
`OPENAI_API_KEY`, repository `.API_KEY`, or `--api-key-file`. Credentials never
enter saved artifacts. Ordinary story generation has no SDK or API dependency.
Artifacts include all 300 stories and compact world traces, selected samples,
frozen requests, source snapshots/hashes, raw responses, ratings, and token
usage. Mechanical measures include exact duplicates, repeated sentences, event
paths, and mean pairwise trigram overlap.

Saved responses are reused. Uncertain calls are not automatically retried.
`run --retry-unavailable` explicitly retries only a definite `429
flex_unavailable` rejection and archives its evidence; the baseline needed one
such retry for the key scenario. It never switches model or service tier.

The next quality target is greater character development and more natural
transitions. The next diversity target is materially different solutions and
consequences, measured on the same seeds alongside fresh held-out samples.

## Luna versus Terra authoring trial

[Full comparison](runs/authoring_music_20261103/REPORT.md) and untouched packs:
[Terra](runs/authoring_music_20261103/terra/round1/pack.py),
[Luna recovery](runs/authoring_music_20261103/luna/round2/pack.py).
Both received the current ruleset, `story.py`, the music-room story from
`luna_high_direct_20/08_music`, and a list of missing capabilities. The task was
to author executable event/grammar rules for competing wishes, consent,
performing solo, a possible private duet, and borrowed-instrument returns.

The latest available models were `gpt-6-luna` and `gpt-6.1-terra`, both Flex/high.
Terra completed the matched first attempt in 10,080 output tokens. Luna exhausted
the 32,000-token limit; one recovery using its partial output and error, with a
64,000-token cap, completed in another 17,800 tokens. Output counts include
reasoning. All original requests/responses and the failed attempt are retained.

| Authored pack | Unfiltered stories | Original intervention cases | Quality: Luna judge | Quality: Terra judge |
| --- | ---: | ---: | ---: | ---: |
| Terra, first attempt | 60/60 | 20/20 | 8.40/9 | 7.65/9 |
| Luna, recovery | 60/60 | 20/20 | 7.05/9 | 6.60/9 |

Both judges saw the same 20 random positions per pack, without author identity.
Both packs received diversity 3/9 from Luna and 2/9 from Terra. The source and
contract intentionally restrict the premise, so this tests variation within a
story family, not open-ended plot invention.

Reading the prose exposed defects beyond the initial test contract. Additional
probes applied equally to both packs found that Luna allows joining without
Nia present or holding her drum, and 14/60 stories prematurely claim that both
instruments have been returned. Its grammar also produces “hoped a duet” and
“Mateo choice stayed his.” Terra passes these particular probes. Counts and
witnesses are saved in each pack's `probe.json`; these targeted diagnostics do
not prove absence of other defects. No author code was manually repaired.

The new `pack_runtime.py` adapter retains the existing grammar/Forest and
attention calculations, sampling every word before committing a semantic frame.
This extends carrier-grounded state/consent/ownership testing toward the memeplex
model, but the authored modules remain scenario-specific experimental packs.
The original three-scenario generator is unchanged. Reproduce the isolated local
checks without any model calls:

```sh
.venv/bin/python -m grammarworlds.authoring_trial check --arm terra
.venv/bin/python -m grammarworlds.authoring_trial check --arm luna --round round2
.venv/bin/python -m grammarworlds.authoring_trial probe --arm terra
.venv/bin/python -m grammarworlds.authoring_trial probe --arm luna --round round2
.venv/bin/python -m grammarworlds.authoring_trial report
```

This is one source story and one initial attempt per model, with an unequal
recovery budget. It supports prioritizing Terra for the next authoring experiment;
it does not establish broad authoring reliability or a general model ranking.

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
