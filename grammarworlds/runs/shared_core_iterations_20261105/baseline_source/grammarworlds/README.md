# Grammarworlds

A local, classical prototype of **grammar + next-word distributions + executable
semantics + storytelling**. No LLM, pretrained neural model, external service,
or third-party package runs during generation.

This integrates a weighted grammar with symbolic kernels and attention. The
baseline below uses our original authored grammar. The optional
[portable rule experiment](portable/README.md) now adapts selected GF RGL
constructions and Codeco-style reference mechanisms into the same Python
`Node`/`Forest` system. It does not use GF at runtime. The earlier, separate
`grammar_completion_experiment/` remains a probe of the live GF Phrasebook service.

Try short stories with dialogue and reading QA across all seven current worlds:

```sh
.venv/bin/python -m grammarworlds.portable --scenario all --seed 7 --qa
.venv/bin/python -m grammarworlds.portable --scenario heldout --seed 7
.venv/bin/python -m grammarworlds.portable --scenario pottery --qa --evidence
```

Its [transfer report](runs/portable_transfer_20261103/REPORT.md) records 1,000
completed/replayed stories and one greenhouse adaptation requiring no shared
grammar changes. The 29 catalog entries are selected construction/mechanism
contracts, not a full GF/ACE import and not additive with the baseline rule count.

The default short style covers rescue, kite, key, music, greenhouse, library and
pottery. [Read fresh samples with QA](runs/ten_rounds_20261103/final_heldout_audit/samples.md).
Speech is composed with typed grammar (including first/second-person agreement
and quote punctuation), and all words still come from the weighted Forest.
Routine physical operations may remain unnarrated, but their guards/effects are
executed and replayed. No action is skipped merely to shorten the text.

QA uses authored semantic facts aligned to the selected text, returning full
answers, exact evidence spans and event/entity IDs. Hidden facts do not supply
reading questions; changed text invalidates its alignment. This is a generator
for questions about our own stories, not a general parser for arbitrary prose.
`--style full` retains the earlier portable baseline. There are no runtime LLMs.

The [ten-round campaign](runs/ten_rounds_20261103/REPORT.md) extends all seven
worlds with physical alternatives: ladder/basket rescue; repaired kite/reused sail;
found/borrowed key; solo/written/private music; competing water priorities;
moon/whale drawings; and smooth/thumb-rest/bowl pottery designs. Choices use
carrier state and weighted attention; each selected event changes persistent
physical state. New dialogue and QA remain composed from typed constructions.

[Final Luna comparison](runs/ten_rounds_20261103/FINAL_COMPARISON.md) compares the
original and final versions on matched development positions and reserved fresh
seeds. On fresh matched samples, quality rises 5.56→6.60/9, diversity
1.00→1.86/9, QA 7.22→7.88/9, and grounded QA 90.1%→98.2%. Fifteen kite
answers still infer an unstated paper material. The [original evaluation](runs/luna_short_dialogue_qa_20261103/REPORT.md)
is preserved: 140 stories, quality 5.57/9, diversity 0.86/9, QA 7.30/9. These are
single-judge diagnostics; the seven worlds remain narrow authored plot families.

```sh
.venv/bin/python -m grammarworlds.storytelling --scenario all --seed 1007 --qa
.venv/bin/python -m grammarworlds --verify
.venv/bin/python -m grammarworlds.storytelling.audit --out NEW_DIRECTORY --start 1000
```

The audit checks both tenses, visible QA evidence, replay, invalid physical
interventions and attention ablation. `generate(..., attention=False)` disables
attention contributions while retaining the same physical rules; temperature
scales event priors. The frozen shared portable grammar is unchanged. Complete
sampling distributions and semantic posteriors remain inspectable in the trace.

The offline evaluator freezes code, lexicon, selected prose, QA and requests;
`storytelling.evaluate run` explicitly calls Luna. Historical calls and failed
attempts remain recorded. `storytelling.comparison` rebuilds the final comparison
from saved results. The new QA judge sees only text and evidence excerpts.

## Original three-world baseline

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

### Authoring prefix cache

The historical Terra authoring request used explicit-only caching without a
breakpoint: 22,362 input tokens, zero cache reads and zero writes. Its evidence
is unchanged. New `authoring_trial.prepare` requests use `author_request` to put
stable instructions and the sorted ruleset first, with an explicit breakpoint
and a 30-minute lifetime. The story, task contract and mismatches follow that
boundary. Recovery requests retain it. Model, reasoning, output schema and
ruleset content contribute to the cache key; different stories reuse it.
This follows the [OpenAI caching guide](https://developers.openai.com/api/docs/guides/prompt-caching).

The [live cache probe](runs/terra_cache_probe_20261103/summary.json) used two small
rule-authoring tasks on `gpt-6.1-terra`, Flex/high, through the same builder and
dispatcher. First request: 21,105 input tokens, 19,950 writes, zero reads. Second:
21,105 input tokens, **19,950 cached (94.53%)**, zero writes. Requests, responses,
dispatch records and source hashes are retained. This proves reuse for this
shared prefix, not a full-pack quality rerun or a guarantee for future requests.
Changing the prefix/settings or letting the entry expire can cause a miss.
Newly prepared Luna requests use the same policy; the live probe tested Terra.
The separate portable-rule catalog has no API authoring runner yet.

To repeat the paid, two-request diagnostic, choose a new output directory:

```sh
.venv/bin/python -m grammarworlds.authoring_cache_probe --out /tmp/terra-cache-probe-new
```

The probe caps each output at 2,048 tokens, never executes returned code, and
fails if the second response reports no cached tokens. The local regression
suite includes tests that varying story/task data preserves the prefix/key and
that the SDK receives the cache controls. All 36 tests pass.

## Two additional Terra-authored worlds

The [portable authoring report](runs/terra_portable_worlds_20261103/REPORT.md)
records two new experimental packs against the frozen shared Python grammar:
[library samples](runs/terra_portable_worlds_20261103/library/round2/samples.md)
and [pottery samples](runs/terra_portable_worlds_20261103/pottery/round2/samples.md).
Terra Flex/high authored 17 and 24 event kernels, respectively, using a shared
15,552-character context of interfaces, vocabulary and 20 retrieved contracts.
Each received one Terra revision; no authored code was manually edited.

Both final packs pass 120/120 unfiltered stories in past/present, replay and
9,666 combined physical guard checks. Pottery also passes 120 Care-attention
interventions. The first author call wrote 4,750 cache tokens; the next three
author calls reused all 4,750 with no new writes. The shared grammar is unchanged.

The existing Luna judge scored 20 random past-tense samples per world:
library quality 6.0/9, pottery 5.4/9, diversity 1/9 each. These executable worlds
still have `event_log_prose`, `repetition` and `too_shallow` defects. Both have
two distinct final-state branches, but narrow plot families and mostly surface
variation. The original authored packs remain isolated as experiment evidence;
the default short-style registry now uses semantic copies with revised narration
and QA in `storytelling/`. Reproduce the original packs' local checks using `portable_authoring check
--scenario library --round round2` or the equivalent pottery command.

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

## Symbolic attention head library

The opt-in [symbolic head library](symbolic_heads/README.md) now registers the
64 proposed behaviors separately from the research inventory. Fifteen execute
editable selection/value/receiving lookup tables over scoped symbolic memory;
49 require algorithms and deliberately raise `ProgramRequired` with a specific
implementation contract. The [catalog](symbolic_heads/CATALOG.md) includes ten
examples per head (640 total), with deferred examples clearly labeled.

The receiver reweights the existing `Forest` next-word distribution without
adding illegal candidates or mutating world state. Try an eight-word, four-choice
demonstration with `.venv/bin/python -m grammarworlds.symbolic_heads --demo`.
The seven-world storytelling generator now has an opt-in prefix/world adapter:

```sh
.venv/bin/python -m grammarworlds.storytelling --scenario pottery --seed 7 --heads --qa
.venv/bin/python -m grammarworlds.storytelling --scenario all --heads --head-strength 0.5
.venv/bin/python -m grammarworlds.storytelling --scenario all --continuations expanded --heads --qa
```

See [the live-head experiment](storytelling/HEADS.md) for manual weights, tracing,
ablations, and limitations. Default sampling remains unchanged. This is a
controlled-grammar adapter, not extraction of head inputs from arbitrary text.

The opt-in expanded continuation grammar composes more lexical, dialogue, tool,
recipient-order and clause-link alternatives over the same guarded events.
See [its evaluation](runs/expanded_continuations_20261105/report.md): choice
points increase from 2.8% to 7.4% and distinct texts from 144 to 267 per 280
samples, with mean length unchanged. This expands wording and syntax; new
semantic plot types remain separate work.
