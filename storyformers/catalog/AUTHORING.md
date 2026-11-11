# Catalog authoring contract

Deliver exactly 1,024 linked records in each final JSONL, assembled from four
independently reviewed shards. These are proposed semantic dimensions/functions,
not 1,024 established biological units or empirically discovered model heads.
Use `schema.py` helpers; put a `build()` returning `Catalog.records()` in your
owned module. Root assembles, checks references and executes native examples.

| Module | IDs | Coverage |
|---|---|---|
| `sources/core.py` | 1–256 | identity/reference, temporal relations, quantity/measurement, provenance/evidence, memory/retrieval/control |
| `sources/linguistic.py` | 257–512 | constituents, grammatical roles, valency, inflection/agreement, nominal/verbal constructions, clause scope, questions/relatives/coordination |
| `sources/world.py` | 513–768 | physical properties, spatial relations, motion, possession/transfer, action/event states, affordances, physical causality |
| `sources/mind.py` | 769–1024 | epistemic attitude, goals, affect/appraisal, social relations, communication, discourse, reasoning/memory, narrative perspective |

Each shard has eight coherent families of 32, with *individually meaningful*
members. Exact allocation is an organizing choice, not a reason to add synonyms
or arbitrary Cartesian products. Prefer typed dimensions to one boolean for
every value of a categorical dimension. Booleans are useful for independent
properties, obligations, relation tests or explicit construction evidence.
Missing/null is unknown, not false. Add/suppress affects evidence, not truth.

Use existing names when meanings agree. Root reserves `lemma`, `pos`, `entity`,
`entity_id`, `entity_name`, `event`, `event_id`, `event_type`, `actor`, `actor_id`,
`recipient_id`, `role`, `factuality`, `location`, `patients`, `instruments`,
`attributes`, `scope_id`, `assertion_status`, `evidence_source_id`.
Linguistic owns `clause_id`, `grammatical_subject_id`, `grammatical_number`,
`grammatical_person`, `clause_finiteness`, `voice`, `tense`, `aspect`, `mood`.
Other fields may be referenced across shards but coordinate names with root.
`token`, `surface`, `kind`, `index`, `start`, `end`, `position` are external,
protected structural inputs. Keys must be snake_case; do not use dots.

`type` uses the existing registry: boolean/string/number/array/object/entity_ref/
json. IDs other than eN entity IDs are strings. Explicit structured bundles are
valuable for correlated holder/event/scope/value hypotheses; explain their
shape. Samples are invented illustrations, never quoted research experiments.

Native grammar: `native=neuron(seq(gap(), tok(...), ...), {key: ...})` uses the
existing readable neuron DSL. Input examples omit whitespace; this is a declared
adapter convention, not the current lossless annotation tokenization. Use `Ref`
to copy data and `Lookup` for finite transformations. Native matcher lacks
inequality, absence, latest/argmax, arithmetic, scope stack, recursive grammar,
span captures, fresh IDs and graph search. Never hide these requirements in a
sentence beside a supposedly native grammar. For these use `contract` with
structured `match`, `guards`, `emit`, `requires`. Contract format is declarative
design material, not accepted by `parse_neuron`; give enough detail for an
implementer to implement the selection/projection, with explicit binders and
conditions. Prefix examples still required. Runtime support will be reported
honestly by counts.

Every triple must contain a causal positive and a meaningful contrastive
example, conditions, actual projection target/value, and a specific function.
Native negative `{expect:{}}` must have no activation. Do not encode an output
value into the same query's input merely to copy it back. It is fine to retrieve
an earlier attribute for a new mention, or consume an attribute to make a
different decision. More than one head can use the same mechanism; distinguish
its role/scope/preconditions. No universal stereotype or keyword-to-fact rules.

World/mental facts need entity/event/holder/scope provenance and assertion
status. A lexical cue can support a *candidate interpretation* before these are
resolved, but must not commit world state. Use complete structured candidate
bundles when scalar fields would mix incompatible hypotheses. Output grammars
are construction templates, not a 1,024-word fixed vocabulary. No inference-time
LLM call is added by the catalog.

Source IDs currently available: `local.storyformer`, `local.attribute_grammar`,
`local.head_catalog`, `local.head_inventory`, `local.memeplex`, `gf.reference`,
`gf.rgl`, `codeco`, `ace`, `sae.monosemanticity`, `sae.scaling`,
`sae.openai_scaling`, `sae.absorption`, `circuits.framework`,
`circuits.induction`, `circuits.ioi`, `circuits.copy_suppression`.
Root will maintain `sources.json` with URLs/files and evidence labels. Ask root
to add source IDs for additional directly consulted primary works. A citation
motivates a family; it does not validate the proposed field/head or example.

Use `Catalog.add(...)` as defined in `schema.py`. All source functions are
deterministic and do not perform API calls. Aim for varied mechanisms and
at least 64 genuinely executable native grammars per shard where suitable;
do not fake native support to hit a quota. Finish at 256 triples, inspect
sample records, and report unresolved concerns.
