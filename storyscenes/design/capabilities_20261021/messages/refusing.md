# Refusing interface proposals

First-pass design only. These dependencies are proposed, not frozen agreements;
the coordinator owns reconciliation. No implementation is authorized.

## refusing-01
- Recipient: requesting, promising, coordinator.
- Issue: Declining a new request must not erase an earlier acceptance or commitment, and agreement acceptance is neither performance nor necessarily a promise.
- Proposed resolution: Refusing validates a decline against an exact pending request ID/terms version and supplies one refusal record; requesting owns the pending-to-declined write in the same checked transaction. An accepted request needs requesting-owned withdrawal/reconsideration, not relabeling as an initial decline. A refusal to do something already promised references the commitment but never discharges it; promising alone classifies fulfillment, breach, release, or renegotiation under its terms.
- Affected stories/contracts: Library unwillingness, harbor lack of authority, observatory existing-promise conflict; request response and commitment interfaces.
- Status: proposed.

Coordinator relay received: explicitly agree with requesting-01's sole
response-state owner and promising-01's separate commitment ledger. Refusing
will not maintain a parallel request response status. Exact finite action terms,
single addressee and explicit checkpoints are the first slice. Executable speech
annotations must distinguish intention from undertaking a commitment; neither
"I'll" nor agreement acceptance is a promise detector. This is Refusing's
position, not a claim that shared interfaces are frozen.

## refusing-02
- Recipient: carrying, lending, observing, informing, discovering_mistake, coordinator.
- Issue: Physical inability, lack of authority, and unwillingness differ; an asserted reason is not omniscient truth or a motive inferred from a guard.
- Proposed resolution: A bounded reason references a scoped action predicate, actor-accessible timed evidence/belief, and an explicit actor goal/preference when motivating choice. Preserve stated reason separately from world validation (supported, contradicted, unknown); physical and authority owners supply predicates without refusal writing their state. A replacement is a separate proposed request, not consent or performance. Observation/communication/revision owners retain their own belief writes.
- Affected stories/contracts: All three outlines and reader-grounded reason QA.
- Status: proposed.

## refusing-03
- Recipient: requesting, promising, returning, coordinator.
- Issue: runtime.transition drops unchanged state, while refused offers, repeated speech, and actual failed attempts require evidence; search rejection is not an attempted action.
- Proposed resolution: First slice uses real pending-to-declined social changes, retaining refusal utterance, reason evidence, and response IDs through pruning/replay. Return-offer declines need an adapter to the offer owner's lifecycle, not a second refusal-owned status. Event-only speech/explicit attempts require a bounded opt-in evidence log with participant, target, time, outcome and usage limits; defer repeated unchanged refusals until agreed. Never add dummy flags or infer attempts from rejected candidates.
- Affected stories/contracts: Harbor authority refusal; observatory promise consequence; cross-capability receipt refusal.
- Status: unresolved.
