# Informing Interface Proposals

## informing-01
- Recipient: observing, discovering_mistake, coordinator.
- Issue: Current `runtime.tell` copies stored belief; future communication needs claim provenance without automatic truth or acceptance.
- Proposed resolution: Opt-in `communication_v2` claims identify proposition/value, temporal scope, speaker, attributed source and evidence references. Delivery appends a recipient receipt with a comprehension result; a separate explicit recipient update adopts, rejects or defers it. Observing supplies timed accessible observation evidence; discovering_mistake owns conflict detection and revision policy, retaining old beliefs and distinguishing false-at-the-time from later-outdated.
- Affected stories/contracts: All three informing stories; versioned claim/delivery/update contract.
- First-pass reconciliation: Read observing-01/03 and discovering_mistake-01/03. Preserve partial percepts, reference times and conflicting priors. Nonconflicting adoption may update a belief; conflicting adoption must reference discovering_mistake's single revision, never execute a second overwrite. Record representation, comprehension ownership and atomic handoff remain coordinator decisions.
- Status: proposed.

## informing-02
- Recipient: observing, discovering_mistake, coordinator.
- Issue: Historical source accuracy and present truth differ; a once-correct message can become stale while in transit.
- Proposed resolution: Keep asserted observation time distinct from delivery time and actual evidence time. Preserve source chains, old beliefs and corrections; do not refresh messages from omniscient state. QA needs separate delivery, acceptance and validity evidence.
- Affected stories/contracts: Harbor timestamped clearance; observatory relayed observation; library false catalogue belief.
- Status: proposed.

## informing-03
- Recipient: requesting, promising, refusing, carrying, coordinator.
- Issue: An informative reply is not permission, a promise, a refusal, physical performance or a guaranteed motive.
- Proposed resolution: Refer to stable request/commitment IDs when replying, but let their owners change those states. Carrying owns physical message transport if needed, using its proposed physical-parent/derived-location interface, without ownership or loan effects. Record an authored goal/motive reference separately from enabling guards; receipt acknowledgments do not imply belief adoption. Under the proposed versioned event contract, repeated speech and explicit failed attempts require meaningful bounded event records, not dummy flags to defeat unchanged-state rejection; retain relevant dialogue/evidence through pruning.
- Affected stories/contracts: Library reservation decision; harbor departure delay; observatory evidence handoff.
- Status: proposed.
