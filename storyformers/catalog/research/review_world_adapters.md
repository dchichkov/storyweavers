# Independent review of world adapter contracts

Reviewed on 2026-11-07 by the mental/SAE catalog author. Read all **192 adapter
definitions**, their positive and contrastive prefixes, and the generated
expected bundles from `sources/world.py`, including the `CONTRAST_VALUES`
overrides. This is a semantic review of authored contracts, not a claim that an
adapter executes them. The owning author made the source corrections below;
the reviewer did not edit the world source.

## Coverage

| Family | Adapter rows reviewed | Main checks |
| --- | ---: | --- |
| Spatial | 32 | Figure/landmark direction, relative frames, depiction/imagination, support, topology, distinct repeated objects, chronology. |
| Motion | 24 | Actor/carrier and path roles, intended versus actual motion, phases, support, control, return/detour, completed arrival. |
| Containment/access | 32 | Direct versus transitive containment, identity joins, boundary access versus actor reach, support loss, capacity, modality and clearance. |
| Possession/transfer | 32 | Ownership versus physical custody, requests/permissions versus accepted handoffs, source/recipient/courier roles, completion and loss. |
| Material/affordance | 16 | Actor/target binding, actual condition evidence, material suitability, explicit incompatibility rather than noun stereotypes. |
| Event structure | 24 | Initiator/causer/effector/theme distinctions, attempts and goals, simultaneous role conflicts, before/after state and creation/destruction. |
| Causality | 32 | Stated causation versus order, necessary/sufficient conditions, mediation, counterfactual effect identity, belief scope, delayed and prevented outcomes. |

The object-state family and the other native construction rows are outside this
adapter-only pass; the owner independently reviewed and strengthened their
native role/sense guards. This review also inspected the shared illustrative
fixture builder because incorrect supplied entity/POS annotations can invalidate
an otherwise sound semantic example.

## Concrete findings and requested repairs

| Record | Finding | Repair requested |
| --- | --- | --- |
| G0611 `possession_custodian` | Asking Ben to keep a book safe does not establish that he accepts responsibility or receives custody. | State acceptance and receipt explicitly, or label the custodian as proposed. |
| G0615 `possession_reservation` | `held_now=false` is unqualified even though the book stays with Lily. It could incorrectly deny all current holding. | Qualify the flag as `reserved_recipient_holds_now` and retain Lily as current holder. |
| G0633 `transfer_retained_ownership` | A contrast transferring legal ownership as a gift does not by itself establish physical holding by Ben. | Include an actual handoff and Ben's acceptance/holding, or leave physical holder unknown. |
| G0639 `transfer_delegated_custody` | Permission to leave a book with Nia is not completed custody delegation. | State the authorized handoff and Nia's accepted responsibility; also make the unauthorized contrast an actual completed handoff. |
| G0748 `causal_overdetermination` | A button pressed “to ring” a bell, causing rope movement, does not prove actual ringing or that the button alone is sufficient. | State a complete sufficient button→rope→ring mechanism and the observed activation, preserving mediation. |
| G0751 `causal_counterfactual_dependence` | `effect_would_occur` names no effect; the positive concerns unlocking while the contrast concerns opening. | Name the same unlocking effect in both, retain the counterfactual scope and explicit assumptions. |
| G0607 `access_bottleneck` | All routes passing a narrow tunnel does not establish it is the narrowest mandatory segment. | Supply the narrowest-segment condition explicitly or weaken the definition. |
| G0584 `containment_nested_access` | Open nested containers alone establish no obstructing container boundary, not that a particular actor can reach their contents. | Supply actor reach and no other obstruction; bind that actor in the result. |
| G0590 `containment_support_loss` | A bottom that tears may retain some support. `lost=true` overstates a partial tear. | State that the bottom tears away and leaves the stones unsupported. |
| G0523 / G0569 / G0715 / G0718 | Actual role fillers alternate between eN references and labels (`cord`, `different_path`, `hands`, `glue`). | Bind the mentioned objects consistently through `@cord`, `@path`, `@hands`, `@glue`; extend the fixture vocabulary where needed. Conceptual material/action labels remain labels. |
| Shared fixture builder | `light` in “box was light” and `support` in “strong enough to support Lily” receive `pos=n` and invented entity IDs solely from spelling. | Remove these unused ambiguous entries from automatic entity assignment, or explicitly disambiguate the fixtures. |
| G0529 `spatial_region` | An imagined corner location is a valid alternative scoped reading for this general resolver; an empty contrast hides it. | Return the imagined region, landmark and imaginer while withholding actual physical commitment. |
| G0753 `causal_scope` | `reported_belief` identifies a scope kind but loses the belief holder, although the visible sentence names Lily. | Retain the holder ID in the correlated causal-claim interpretation. |
| G0559 `motion_control` | Lily losing her grip does not rule out every other controller. | Explicitly describe the contrast as uncontrolled with nobody steering. |

These repairs preserve the original dimensions and counts. They do not add
arbitrary new attributes. In particular, the ownership/custody and
permission/action distinctions need stronger witnesses, not more semantic names.

## Positive findings and limits

Most contracts already make useful distinctions: a planned destination does not
entail arrival; a goal state does not entail achievement; a delayed effect stays
pending; a prevented break is not an actual break; ownership can persist through
a loan; a repeated noun with explicit “different” must not join an earlier
entity; and a temporal reversal does not imply a simultaneous spatial conflict.
The broad `CONTRAST_VALUES` table is useful: many contrasts correctly return
another grounded interpretation instead of being mislabeled universal
no-activation examples.

Every adapter emits a correlated entity/scope/value object with candidate status,
which avoids the mental shard's unsafe independent-field bundle construction.
Source spans and event provenance are declared in separate `trace_metadata`.
That trace association is part of the required adapter interface: consumers must
not discard it and then treat an eventless scalar as an established current
world fact. No graph parser, state replay, capability evaluator, physical
simulator or counterfactual solver is implemented by these contract records.

Fixtures supply their current focus/coreference and use schematic outer scope
`s1`. A real adapter must build nested claim/world/event scopes and distinguish
reported, remembered, depicted and imagined content. The helper's finite noun
inventory is fixture scaffolding, not a general entity recognizer or training
annotator. Even after the obvious nonnoun fixes, these examples should not be
ingested as a gold token annotation corpus without a separate annotation pass.

Structural and reference checks can verify record shape and that an eN output
refers to an entity in its prefix. They cannot verify the 192 semantic derivation
algorithms. Accuracy, paraphrase robustness, multi-event ambiguity, state
persistence assumptions, complete alternative enumeration and downstream causal
effects remain unmeasured.

## Final verification

All fourteen finding groups above were repaired by the owning author and
independently rechecked in the generated records. The sixteen affected contract
rows now show the strengthened witnesses or corrected bindings. The automatic
fixture scan finds no `light`/`support` occurrences incorrectly tagged as noun
entities. Counterfactual positive/contrastive values now name the same
`locked_to_unlocked` effect and counterfactual evaluation scope; belief-causal
and imagined-location interpretations retain their named holder.

The source still produces **256 linked world triples**, of which **192 are
adapter contracts** with **384 positive/contrastive fixtures**. Every adapter's
attribute example and emitted bundle passes its declared object-type check, and
every eN reference in all 384 expectations exists in that fixture's visible
prefix. Three targeted identity probes retain different IDs for the two boxes
in the spatial-chain contrast, two pouches in the nested-containment contrast,
and original versus replacement cup in compensation. This verifies identity
scaffolding and record consistency, not the unimplemented semantic algorithms.

No further concrete witness correction remained from this pass. The owner
separately reports all 218 native world fixtures passing; native execution was
outside this adapter review. No executable semantic-adapter accuracy is claimed.
