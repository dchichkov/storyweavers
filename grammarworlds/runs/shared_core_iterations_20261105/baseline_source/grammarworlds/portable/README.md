# Porting grammar constructions into Grammarworlds

This is a **Python port/adaptation of selected grammar constructions**, not a GF
backend. It lowers typed phrases into our existing `Node`, `seq`, `choice`,
`expand`, and `Forest` implementation. Generation and tests use only the Python
standard library. There is no GF compiler, PGF, external service, or LLM at
runtime. The original generator remains available unchanged for comparison.

```sh
.venv/bin/python -m grammarworlds.portable --scenario all --seed 7 --qa
.venv/bin/python -m grammarworlds.portable --scenario heldout --seed 7
.venv/bin/python -m grammarworlds.portable --scenario music --tense present
.venv/bin/python -m grammarworlds.portable --style full --scenario rescue --after 1 --complete she
.venv/bin/python -m grammarworlds.portable --scenario key --trace
.venv/bin/python -m grammarworlds --verify
```

The default `--style short` covers the complete current set: rescue, kite, key,
music, greenhouse, library and pottery. `heldout` remains an alias for greenhouse.
All seven now have shorter narration, direct dialogue, and optional reading QA.
`--qa --evidence` displays the supporting passage for each answer; `--json`
includes offsets, event/entity IDs, word distributions and internal physical steps.
The QA is for these generated stories, not arbitrary external prose.

`--style full` retains the original development baseline (rescue, kite, key,
music, plus the separately selected greenhouse). The original transfer tests and
frozen construction modules remain unchanged. Short narration uses new typed
speech/scene rules in `storytelling/`, with active semantic copies of the two
Terra-authored worlds; immutable authoring evidence is not edited.

See the [short-story and QA audit](../runs/short_dialogue_qa_20261103_v2/REPORT.md)
and [all seven stories with questions, answers and evidence](../runs/short_dialogue_qa_20261103_v2/samples.md).

## What was ported

The catalog has **29 construction/mechanism contracts**. These are not 29
verbatim production rules and are not additive with the baseline's 34 trace
labels, since their responsibilities overlap.

| Origin | Contracts | Scope |
| --- | ---: | --- |
| GF RGL adaptations | 21 | Noun paradigms, features/case, determiners, adjectives, possession, verb valency, complements, copula/modal, tense/polarity, clauses |
| Codeco-style mechanisms | 3 | Introduce a referent, resolve accessible references by features, open/close scopes |
| Local composition/binding | 5 | Prepositional phrases, NP/sentence coordination, speaker binding, same-actor continuation |

The GF mapping is recorded per contract in `catalog.py` and its registrations,
with the source file and original operation name. Sources are pinned to RGL
`20260403`; original files, hashes, and upstream license are retained under
`sources/`. The morphology ports GF's regular heuristics with explicitly authored
lexical exceptions (for example `open/opened`). The article heuristic is an
adaptation with sound exceptions, not a complete phonological model.

Codeco contributes the **reference mechanism described in the paper**, independently
implemented here. We have **not** imported its full ACE grammar or implemented a
Codeco chart parser. References are physical entity IDs; committed typed mention
traces establish accessible antecedents. Negative-clause introductions do not
escape their scope. Ambiguous pronouns fall back to explicit references. Explicit
local bindings handle speakers inside reports and repeated actors in coordination.

This is a limited English subset: simple declaratives, present/past, positive or
uncontracted negative, and a few complement families. Questions, relatives,
quantifier scope, extraction, passive voice, aspect, broad lexical ambiguity,
and full GF/ACE equivalence are **not implemented**. Source construction names
describe ancestry, not support for every case handled by the original operation.

## Probabilities and physical meaning

All currently allowed event frames contribute to a weighted forest. No event or
whole sentence is sampled first. Each word receives the sum of compatible
derivation mass; a frame is committed only after sentence completion. Each
frame's grammar mass sums to one, so adding a paraphrase does not inflate its
event prior. Distinct frames sharing a kernel name retain separate priors.

The recovery worlds retain their existing guards/effects. The music world uses
the semantic functions extracted from Terra's saved pack, with fresh typed
realizations. The immutable original authoring evidence is untouched. The new
greenhouse world models a finite barrel supply, a broken tap, shade, physical
tools, cooperation, and returning a borrowed can. This keeps the port aligned
with the memeplex direction: grammar expresses allowed events; carrier state
and accumulated concepts determine availability/weight, and subsequent prose
sees the committed world.

The explicit forest remains bounded to 512 derivations per frame. Large rule
libraries do not require expanding every rule at every step, but large recursive
support still needs a packed/lazy implementation. This experiment does not
establish runtime scalability to 100,000 productions.

## Keeping author context small

See [AUTHORING.md](AUTHORING.md) for the fixed facade contract. Retrieve relevant
rule contracts without sending implementation or upstream grammar source:

```sh
.venv/bin/python -m grammarworlds.portable.catalog 'complement hope invitation' --budget 3000
.venv/bin/python -m grammarworlds.portable.catalog 'agreement noun possession' --budget 3000
.venv/bin/python -m grammarworlds.portable.catalog --list
```

The retriever includes declared dependencies and omits a contract if its complete
dependency closure will not fit. The budget is **characters**, not model tokens.
The complement query selects 8 contracts / 1,867 characters. A regression adds
100,000 unrelated metadata entries and checks that the prompt stays identical;
those entries are synthetic index records, not implemented linguistic rules.

An author needs the small facade contract, selected contracts, relevant lexicon
entries, target world/event shapes, and failing examples. Only the owner of a
construction needs its implementation. A vocabulary addition should normally
touch a lexicon module; a new story should normally add semantic mappings and
world rules. A genuinely new construction gets a focused port and regression
cases. No Terra authoring rerun or model-context benchmark is claimed here.

## Transfer result and validation

[Saved report](../runs/portable_transfer_20261103/REPORT.md) and
[20 unfiltered samples](../runs/portable_transfer_20261103/samples.md).

After developing the four worlds, we froze shared module/core-lexicon hashes,
then read `luna_high_direct_20/03_greenhouse/story.txt`. Its compact adaptation
added **32 lexical entries and 13 event kernels**, with **zero shared grammar
changes**. This is one manually authored transfer case, not a blind benchmark or
evidence that arbitrary stories require no new constructions.

The audit generated **1,000 stories**: 100 consecutive seeds × two tenses × five
worlds. All reached endings and replayed, and 2,340 physical/consent/resource
interventions passed. Tests include 51 saved GF reference cases, normalizing
only initial capitalization and standard negative contractions. The offline
reference grammar and raw expected outputs live under `sources/oracle/` and
`sources/gf_oracle.json`; these are test provenance, never a generation backend.

Reproduce a new audit (output directory must not already exist):

```sh
.venv/bin/python -m grammarworlds.portable.audit --out /tmp/portable-audit --count 100
.venv/bin/python -S -m grammarworlds.portable --scenario heldout
```

These are mechanical results. Prose is often plain and repetitive, and new
worlds still need authored semantic plans. The existing Luna/Terra literary
scores apply to the earlier generators, **not this port**. Next: judge this
version's prose, improve shared discourse/aggregation, and attempt several more
held-out stories before broadening the syntax inventory.
