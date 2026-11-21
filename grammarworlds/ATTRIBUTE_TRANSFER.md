# Attributes on imported event lines

Imported lines now use joint annotated-token generation by default. The adapter
transfers a reviewed operation and its role bindings, then regenerates attributes
from the receiving world and typed grammar before sampling each scene.

Source-graph correspondences now come from an [event mapping grammar bank](EVENT_MAPPING.md).
It can infer compatible local bindings and rank alternative target operations;
the field-transfer policy below still governs their attributes.

| Attribute | Transfer policy |
|---|---|
| Event meaning | Use the reviewed target operation: kite mending can become paper repair. |
| Actor, object, tool, recipient, other slots | Bind every operation slot to a target entity; preserve distinct roles. |
| Name, noun, pronoun, number | Use the target entity and regenerate grammatical agreement. |
| Location, state, emotions/memes, capabilities | Read current target state before each scene; do not overwrite existing carriers with source facts. |
| Expected changes | Recompute declared effects from the bound target operation; guards still decide whether it can execute. |
| Source positions | Discard and recompute target token/sentence/rotary coordinates. |
| Unknown fields, source guards and context | Keep as provenance or explicit untransferred context, not live target facts. |

For example, a source kite's `flyable` property and `fragile` state do not become
properties of Ada's book. The imported fetch puts the tape in Ada's possession;
the next scene's tool attributes read that updated location. Repair requires
the receiving book to be paper and the receiving actor to have the relevant
capability. The import cannot manufacture that permission.

When a **new** entity is instantiated from a catalog prototype, its reviewed
defaults and dependencies still supply source flavor. This policy preserves
existing entities; it does not prohibit inheritance when creating a carrier.

## Ambiguous bindings

A pool brief can explicitly supply weighted alternatives:

```json
{"roles": {"actor": {"candidates": [
  {"entity": "ada", "weight": 3},
  {"entity": "omar", "weight": 1}
]}}}
```

These are alternatives for one role, not a merged actor. Multiple uncertain
roles expand into complete joint bindings (at most 32 combinations). Retrieval
multiplies each recipe's score by the binding weight, rejects physically
infeasible candidates, and normalizes over the remaining recipe/binding pairs.
It does not renormalize binding mass separately within each recipe.

One complete attachment is selected **before** word generation. Its retrieval
trace retains the alternative distribution and rejection reasons; within that
attachment, the annotated sampler retains ambiguity between token meanings.
The separate event mapping bank can enumerate compatible local role alternatives.
Pool briefs still require these explicit weighted hints; carrying attachment
uncertainty through the whole story is not implemented.

A single source identity can supply provenance for several explicitly defined
target roles. Distinct target roles still cannot alias one entity. Inventing a
group actor, splitting an operation into multiple events, or deciding arbitrary
many-to-many correspondences requires a new reviewed adapter/recipe.

## Trace and limits

Each scene contains `attribute_transfer` audits for its available events,
including source/target field comparisons, discarded source-only properties,
missing profiles, unknown fields, and current target role features. Its
`attribute_table` supplies the live bundles referenced by joint word choices
and selected token posteriors. The event metadata includes all operation slots,
even when the older coarse frame representation omits some of them.

`expected_effects` describes declared target-operation effects and is marked
`effects_complete: false`: specialized commits can have additional bookkeeping
or effects. Proposed annotations do not assert that an event has happened.
The committed world history remains authoritative.

This is explicit symbolic adaptation, not learned semantic inference. The two
source-graph ports remain kite fetch/mend; catalog/pool operations use their
existing reviewed implementations. Arbitrary annotations are not executable
instructions. No story-quality improvement is claimed from this change alone.

Reproduce the [examples and comparisons](runs/attribute_transfer_20261106/report.md):

```sh
.venv/bin/python grammarworlds/runs/attribute_transfer_20261106/run.py
.venv/bin/python -m unittest grammarworlds.test_attribute_transfer -q
```

`event_line_replay.replay(..., predict_attributes=False)` retains the previous
surface-only sampler for comparison.
