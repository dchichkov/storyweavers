# Cross-review of native world candidates

Reviewed 2026-11-07 against `sources/world.py`, `annotation.story_tokens`,
`neuron_spec.parse_neuron`, and `GrammarNeuron.activate`. No world source edits
were made by this reviewer. Findings were sent to the owner and coordinator.

## Coverage and execution

Read all 64 native rules and their full lookup alternatives: 32 physical-state
copulas, 16 material-property copulas, eight movement constructions, and eight
event cues. The initial 128 positive/contrastive fixtures all passed, despite
the semantic issues below. The owner expanded the final set to **218 fixtures**,
all independently rechecked successfully. The review also tested out-of-family
senses and real punctuation tokenization.

Each native projection emits one atomic object-valued field containing entity,
scope, candidate status, and value. This avoids the independently merged
holder/content/event fields demonstrated in the mind shard. These are candidate
interpretations, not physical state commits. The distinction is useful, but does
not by itself establish subject binding or resolve a lexical sense.

## Concrete findings sent to the owner

| Area | Reproduced mismatch | Suggested correction |
| --- | --- | --- |
| Hyphenated adjective alternatives | `half-full` and `rust-free` are single lemma keys. The actual tokenizer returns `half`, `-`, `full` and `rust`, `-`, `free`, so these alternatives cannot match the declared input convention. | Use a multi-record construction, a declared normalization adapter, or remove the unreachable alternatives. |
| `material_composition` | `metallic` maps directly to `metal`, although the adjective can describe a metal-like appearance. | Remove that ambiguous alternative or require an already disambiguated composition sense. A candidate label should not conceal the difference between composition and appearance. |
| `material_absorbency` | `waterproof` maps to `water_repellent`, putting permeability/repellency terminology in an absorbency dimension. | Use a direct absorbency contrast such as `nonabsorbent`, or represent the distinct property under its own definition. |
| Movement role bindings | With only the final entity token changed, `Lily followed the instructions` emits a physical route; `Lily entered the competition` emits a reached destination; `Lily left the job` emits a departure landmark. | Gate the verb with the existing `event_type=move` and POS, and obtain explicit participant/landmark bindings, or mark the missing interpretation as an adapter requirement. |
| `motion_medium` | `flew` maps to `air` and `burrowed` to `ground`; the description calls these lexically entailed. The same finite rule accepts `spacecraft flew`; burrowing can be through blankets or another material. | Describe these as lexical defaults or require explicit medium evidence. Do not call them entailments. |
| Shared subject/actor capture | A gap followed by any entity and a verb selects the last entity before the predicate. In `the friend of Lily was tired`, that is Lily, although the fatigue is predicated of the friend. The same issue affects movement and event cues. | Use resolved `grammatical_subject_id`/`actor_id` equality where appropriate, or require construction-role binding. Adjacency is insufficient to identify a subject. |

The previously noticed `growing`/`pos=adj` mismatch had already been removed by
the owner at review time; `object_growth_state` now uses adjectival `dormant`.
Other participial forms can have genuine adjectival uses, so this review does
not treat every participle as an erroneous POS label. The broad literal versus
figurative ambiguity of `cold`, `sharp`, `stable`, and similar adjectives is a
known limitation of a small candidate lexicon rather than evidence that the
dimensions themselves are invalid.

The eight event cues deliberately leave the affected event unresolved and do
not assert execution of a cancelled or completed task. This is appropriately
weaker than full event-state interpretation. The final source now also requires
a selected sense for `succeeded`, `finished`, and the other cue verbs.

## Verified resolutions

The owning author fixed all six classes above:

- Every copula tests `grammatical_subject_id == subject.entity_id`. Every
  movement/event predicate tests `actor_id == actor.entity_id`. Each native
  includes a mismatched-role contrast. Independently removing the supplied role
  from each of the 64 positive fixtures makes all 64 rules abstain.
- Movement predicates require `pos=v`, `event_type=move`, and a selected
  `lexical_sense_id`. The four path-role rules also require the landmark's
  `event_id` to match the action and its input role to be `location`.
- Movement and event lookup tables use explicit authored sense labels, with
  unresolved/incompatible-sense contrasts. These are documented as local sense
  conventions, not WordNet IDs. `fly:move_through_space`,
  `burrow:move_through_blankets`, and `succeed:inherit_position` abstain.
- `half-full` was removed from the finite seed; `rust-free` became the
  single-token adjective `uncorroded`. Every remaining alternative in these
  two tables agrees with the actual tokenizer's single-token behavior.
- `metallic` no longer produces a composition candidate. `waterproof` no longer
  produces an absorbency candidate; the table now uses `nonabsorbent`.
- All 64 native projections retain a single atomic object-valued field with
  candidate status inside the payload. The corrections do not claim to execute
  physical effects or revise prior records.

Final independently verified counts: **256 linked triples; 64 native and 192
adapter-required grammars; 218 passing native fixtures**, plus the 64 missing-role
abstention probes and targeted removed-material/tokenization checks.

## Limits of this review

Fixture success verifies finite matching and projection, not broad semantic
precision. Native status is conditional on the supplied role, event, scope and
sense inputs; it does not claim those inputs have already been learned or
produced from raw text. In particular, a preceding token's sense cannot be filled
from a later object by an offline whole-story annotator and then called causal.
An unresolved earlier sense must cause abstention, retain a scoped alternative,
or be handled by a causal interpretation at the current query. These synthetic
fixtures test the downstream conditional projection rather than the correctness
of the upstream annotation process.

The adjective tables remain finite candidate lexicons, with residual polysemy
and physical-type ambiguity. Their metadata and candidate status expose this
limit. The findings above concern native seeds only; the 192 world adapter
contracts have not all received a second independent semantic review here.
