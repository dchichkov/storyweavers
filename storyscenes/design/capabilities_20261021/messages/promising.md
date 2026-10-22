# Promising interface proposals

First-pass design only. Shared interfaces remain proposed pending coordinator
reconciliation and cross-review; no implementation or peer agreement is implied.

Proposal saved in `../proposals/promising.md`. Explicitly agree with the
coordinator relay and requesting-01: Requesting alone writes request responses;
Refusing supplies a validated decline decision, and Promising owns no duplicate
response state. Promise creation requires an executable undertaking annotation
whose rendered speech supports that act; "I'll" alone is not classification.
First slice uses finite action terms, explicit checkpoints and one beneficiary.

## promising-01
- Recipient: requesting, refusing, lending, coordinator.
- Issue: Request acceptance or loan agreement acceptance is not automatically a promise, and an unsolicited promise needs no fabricated request.
- Proposed resolution: Promising alone owns a versioned commitment record, created by an explicit voluntary undertaking with immutable promisor, beneficiary, bounded action terms and optional request/agreement reference. Requesting alone writes its response state. A composed utterance may accept and promise atomically only when both acts are explicit; beneficiary acknowledgment is distinct from promise creation. Loan obligations remain lending-owned and may be referenced without duplicating their lifecycle.
- Affected stories/contracts: Requested library promise, unsolicited harbor promise, conflicting observatory promises; commitment creation and linked obligations.
- Status: proposed.

## promising-02
- Recipient: carrying, returning, observing, informing, coordinator.
- Issue: Intention, reported completion, actual matching performance, and reader-supported fulfillment are different evidence layers.
- Proposed resolution: Domain owners emit immutable event receipts with actor, exact object/action, recipient/result, time and terms version. Promising validates those receipts against one commitment and owns its settlement only; it does not move objects, discharge loans, or adopt beliefs. Deadline miss, inability, release and late repair remain distinguishable. Obligations influence choices but are not physical guards.
- Affected stories/contracts: All three outlines; event-to-fulfillment matching, temporal evidence, reader QA.
- Status: proposed.

## promising-03
- Recipient: requesting, refusing, informing, coordinator.
- Issue: Current transition drops unchanged state; actual failed attempts, inability reports and repeated assurances cannot be inferred from planner rejection.
- Proposed resolution: Creation, release, deadline assessment and settlement have real social effects. For physically unchanged enacted attempts, propose a bounded opt-in event receipt with actor, target, attempted operation, observed result, time and evidence, retained through replay/pruning; never add dummy flags. An inability claim alone neither excuses nor settles a promise. Coordinator must choose clock ordering and the event-only adapter; repeated assurances can wait.
- Affected stories/contracts: Harbor blocked repair, observatory allocation conflict, late performance and failed-attempt QA.
- Status: unresolved.
