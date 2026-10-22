# Carrying interface proposals

## carrying-01
- Recipient: lending, returning, coordinator.
- Issue: Existing `runtime.transfer` changes ownership; a physical handoff must not silently inherit that interpretation.
- Proposed resolution: In an opt-in future schema, carrying owns one acyclic immediate physical-parent relation plus derived effective location/custodian. Pickup, placement, travel, and accepted handoff never write legal ownership or loan discharge. Lending/returning compose their effects with a validated physical receipt under one transaction when needed.
- Affected stories/contracts: All three carrying stories; reusable pickup/handoff/return composition.
- Status: proposed.

## carrying-02
- Recipient: observing, informing, discovering_mistake.
- Issue: Moving a container relocates its contents without revealing them or refreshing everyone's beliefs.
- Proposed resolution: Export event-time physical-parent paths and derived-location evidence, not automatic belief writes. A closed bag can move while its contents remain unobserved. Observation owns access and belief acquisition; informing owns transmitted claims and acceptance.
- Affected stories/contracts: Library book inside a tote; harbor tool inside a case; observatory supply nested in a backpack.
- Status: proposed.

## carrying-03
- Recipient: requesting, promising, refusing, coordinator.
- Issue: Physically executable transport differs from authorized conduct, accepted requests, and successful delivery.
- Proposed resolution: Keep physical feasibility, social authorization, and motive evidence separate. Requests/promises reference physical predicates but cannot move objects. Narrate failure only from explicit attempt events, never planner rejection. Compatibility note: unchanged attempts/speech need bounded event support and evidence-aware pruning, not dummy flags; this remains unresolved. Minimal slice excludes joint lifting/carts.
- Affected stories/contracts: Harbor free-hand relay; observatory last-supply choice; all action failure evidence.
- Status: proposed.
