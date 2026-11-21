# Grammarworlds

A local, classical prototype of **grammar + next-word distributions + executable
semantics + storytelling**. No LLM, pretrained neural model, external service,
or third-party package runs during generation.

The [twenty-seed collection](storytelling/seed_worlds/README.md) is now fully
implemented: 16 new grammarworlds join music, greenhouse, library and pottery.
The three earlier prototypes remain, bringing the runtime to 23 worlds.
[Samples, annotations and checks](runs/seed_worlds_20261107_v4/report.md) cover
the full seed collection, dialogue, QA, physical branches and memory reuse.

Imported event lines now produce [adapted semantic attributes](ATTRIBUTE_TRANSFER.md)
using current target entities, with explicit transfer audits and weighted
alternatives for uncertain role bindings.

The [event mapping bank](EVENT_MAPPING.md) now expresses source-to-target
correspondences as weighted data rules, infers compatible local role bindings,
and checks complete candidate programs before generation.

[Intact story memory](STORY_MEMORY.md) now exposes all seven worlds as complete
annotated token streams. Retrieval returns references into the original stories;
17 mapping rules support 19 of their 119 event kinds. [Examples and checks](runs/story_memory_20261107_v2/report.md)
cover 140 generated samples, source preservation and repeated target-state queries.

A [sampled continuation loop](STORY_MEMORY.md#sampled-continuation-loop) now accepts
an optional event prefix, retrieves again after each state change, and samples
events plus a stop option. [Comparison and samples](runs/memory_continuation_20261107_v2/report.md)
show plain sampling versus explicit state/goal/history weights; suffix event
sequences are not supplied.

This integrates a weighted grammar with symbolic kernels and attention. The
baseline below uses our original authored grammar. The optional
[portable rule experiment](portable/README.md) now adapts selected GF RGL
constructions and Codeco-style reference mechanisms into the same Python
`Node`/`Forest` system. It does not use GF at runtime. The earlier, separate
`grammar_completion_experiment/` remains a probe of the live GF Phrasebook service.

Try short stories with dialogue and reading QA across all 23 current worlds:

```sh
.venv/bin/python -m grammarworlds.portable --scenario all --seed 7 --qa
.venv/bin/python -m grammarworlds.portable --scenario heldout --seed 7
.venv/bin/python -m grammarworlds.portable --scenario pottery --qa --evidence
```

Its [transfer report](runs/portable_transfer_20261103/REPORT.md) records 1,000
completed/replayed stories and one greenhouse adaptation requiring no shared
grammar changes. The 29 catalog entries are selected construction/mechanism
contracts, not a full GF/ACE import and not additive with the baseline rule count.

The original seven-world short style covers rescue, kite, key, music, greenhouse, library and
pottery; the twenty-seed expansion adds the other 16 worlds. [Read fresh samples with QA](runs/ten_rounds_20261103/final_heldout_audit/samples.md).
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

The subsequent [shared-core merge](runs/shared_core_iterations_20261105/report.md)
replaces repeated commit/effect/transfer logic, lexical entries and scene
constructions across all seven worlds. Custom world/plan Python tokens fall
6.2%; total storytelling source/data bytes grow 4.9% to support the shared layer
and extra alternatives. In fresh matched comparisons, expanded/manual choice
steps rise from 7.36% to 10.82%, distinct texts from 272 to 280/280, and mean
length from 91 to 93 words. Most added forks are two-way; plot families remain
unchanged. Original-mode records are preserved exactly. See the report for
unfiltered stories/QA, stage snapshots, 95-test verification and the optional
`--head-profile tuned` experiment, which has no demonstrated quality advantage.

Defined stories can now be projected into [entity-specific event lines](storytelling/EVENT_LINES.md).
Each line records roles, physical/concept changes and shared event IDs; local
slices expose dependencies and counterpart joins for future substitution work.
The [first annotation audit](runs/entity_event_lines_20261106/report.md) covers
all 119 pack-qualified event kinds over 140 stories. This is an annotation and
boundary-extraction layer; independent local planning/swapping is not yet implemented.

The underdefined adapter now has an opt-in [local-line replay path](ATTACHED_LINES.md).
Entities bind to typed roles; independently ready local steps share the word
sampler, while joint handoffs commit once across all participating lines.
Five portable operations execute with physical guards, and two reviewed kite
events supply a fetch/patch segment. The [experiment](runs/event_line_replay_20261106/report.md)
repairs a book with solo or cooperative bindings and rejects missing handoffs or
undeclared capabilities. This is supplied-line replay with explicit operation
ports, not automatic line inference or unrestricted replay of annotated effects.

### Catalog-driven attachment to a bare world

`catalog_attachment.py` resolves a structured line against entity prototypes
from library, kite and music, imports required objects and carrier-bound
capabilities, then reuses attached-line replay. It records every inferred
binding and assembly assumption. See [CATALOG_ATTACHMENT.md](CATALOG_ATTACHMENT.md)
and the [three-source experiment](runs/catalog_attachment_20261106/report.md)
(40/40 completed; 100/100 invalid-condition runs blocked; 140 tests pass).

### Event fragments that travel with entities

`event_pool.py` retrieves authored programs from a short goal plus entity anchors.
The rabbit/hat example expands to setup, obstacle/recovery, reveal and a care
ending; an ordinary hat selects a stage mechanism instead. Six reusable
subfragments support five recipes, including existing kite and drawing ports.
Source flavor and supporting props may travel with the selected program.
See [EVENT_POOL.md](EVENT_POOL.md) and the
[280-sample comparison](runs/event_pool_20261106/report.md).

### Symbolic rotary token positions

`symbolic_heads/positions.py` adds an opt-in discrete rotary position prototype
for annotated, possibly multiword token units. It supports repeated event names,
relative token/sentence coordinates, causal masking, and a demo using the
existing table-head/grammar reranker. See
[symbolic_heads/POSITIONS.md](symbolic_heads/POSITIONS.md). Main generation is unchanged.

Generated `storytelling` traces now support `--token-annotations --json` (or
`generate(..., token_annotations=True)`). This exports actual sampled units,
conservative token-local grammar/entity provenance, repeated scene names with
position anchors, explicit scene-boundary entity state, and rotary coordinates.
See the [generated-story integration](symbolic_heads/POSITIONS.md#generated-story-integration).

### Predicting annotated tokens

The seven `storytelling` worlds now generate a joint distribution over words and
attributes by default. Typed constructions supply entity bindings, clause roles,
predicates, tense, polarity, dialogue scope and current physical features before
sampling. Selecting a word retains its conditional semantic alternatives for the
next step. Subject-dependent heads can read these weighted bindings.

See [the implementation contract](storytelling/ATTRIBUTES.md) and
[all seven annotated examples and matched comparisons](runs/attribute_generation_20261106/report.md).
Use `--surface-only` / `predict_attributes=False` for the original sampler.

### Transfer across the joined twenty-world pool

[Native mechanics transfer](NATIVE_TRANSFER.md) allows compound events to bring
supporting entities and guarded physics into an underdefined receiver. It supports
existing-object analogies, explicit leakage records, source-branch distributions,
rebound annotated tokens and native replay. See the
[twenty-world transfer audit](runs/joined_transfer_20261107_v3/report.md).

### Multiple event scales and world time

[Event scales](EVENT_SCALES.md) add opt-in story/episode/participant-chain
attributes to token candidates, a sampled world clock, and physically grounded
commitments across all 20 seed worlds. A coarse continuation sampler can rank
native source episodes against one persistent receiving goal, including time
budgets and resuming compatible prefixes on existing carriers. See the
[matched sampling experiment](runs/event_scales_20261108/report.md).

### Plot roles and attribute inventory

The [attribute inventory](ATTRIBUTE_INVENTORY.md) separates implemented candidate
attributes, retrospective source observations, and proposed storytelling fields.
All 20 seed worlds now have authored plot-role readings, bound narrative roles,
and links between actual setup/discovery/payoff events. Runtime token candidates
can include this context with `--plot-annotations`; source memory retains it on
intact tokens. These annotations do not yet drive a plot planner. See the
[full-pool annotation export](runs/plot_annotations_20261108/report.md).

### Executable receiving plots

[Plot execution](PLOT_EXECUTION.md) now uses the annotations to enforce shared
object/recipient bindings, stage transitions, setup/payoff obligations and
minimum narration coverage. Two contracts—adapt/give/use and failed-attempt/
discovery/changed-approach—rank and sample native continuations from the full
pool. [Generated examples and comparison](runs/plot_execution_20261109_v2/report.md)
show coherent source reuse; novel cross-source plot planning remains limited.

Source and plot generation now include weighted titles, openings and closings by default:
traditional/everyday introductions, direct starts, explicit end markers and
native final-image endings. [Eight examples](runs/story_presentation_20261110/report.md)
show the variation. `raw_story` and native rows preserve the body and replay;
Standalone source rows expose framed text as `presented_story` and keep `story`
raw; the CLI displays framing by default (`--raw` omits it). Joined plot `story`
is the framed assembled result. `presentation.body_offset` maps raw evidence to
display offsets. `presentation` records the framing's annotated-word distributions. See
[usage and controls](PLOT_EXECUTION.md#titles-openings-and-closings).

### Optional story beats

[Beat annotations and generation](BEATS.md) add expectation, interruption,
reaction, discovery, choice and payoff readings to intact story text. Optional
`beat_budget=2` or `6` enables shared reactions, functional dialogue, inspections
and state-grounded reminders; the joined plot generator preserves one budget
across stages. [Ten refinement rounds and samples](runs/beats_20261113/REPORT.md)
include baseline comparisons, QA and code snapshots. A
[second ten-round campaign](runs/beats_20261115/REPORT.md) integrates framing in
source reports, separates physical actors from experiencers, preserves candidate
semantics, adds ten motifs, and types optional dialogue/action attributes.
Reminders now cover 16 motifs across13 worlds, with one per source arc. This is
an inspectable classical grammar extension; literary improvement is not yet a
calibrated result.

### Rewritten storytelling prototypes

An opt-in `--edition crafted` now offers richer pottery, music and greenhouse
stories with three consequential branches each. See [STORYCRAFT.md](STORYCRAFT.md)
for execution, annotations, QA, examples and limitations. These are authored
content experiments over the existing sampler; the default twenty worlds stay
unchanged. The revisions trade extra words and authoring for stronger motive,
conflict and payoff, and have not yet demonstrated general event transfer.

Add `--decision-beats` to a crafted run to sample character appraisals that change
branch probabilities, require actual dialogue commitments, gate payoffs on
visible setups, and downweight known reminders. `--appraisal` supports controlled
comparisons; `--no-compression` disables the repetition penalty. See the
[decision-beat experiment](runs/decision_beats_20261119/REPORT.md).
