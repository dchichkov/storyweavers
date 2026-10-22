# Observing interface proposals

First-pass reconciliation: the visible informing, discovering_mistake and
carrying notes support these boundaries, but no agreement is frozen. The proposal
uses carrying's physical-parent paths and preserves prior beliefs for explicit
revision. COMPATIBILITY.md also requires a future event-aware receipt/replay
adapter for failed or repeated inspections; no dummy flags or legacy changes.

## observing-01
- Recipient: informing; discovering_mistake; coordinator
- Issue: Evidence acquisition must not imply truth transmission, acceptance, or automatic resolution of conflicting beliefs.
- Proposed resolution: Versioned ObserveEvidence emits an immutable, timed, source-bound percept with a proposition, partial value or explicit unknown, coverage and access witness. It may initialize an unknown belief or refresh matching support; conflicting prior beliefs are retained for discovering_mistake to resolve. Informing transmits a claim referencing evidence without upgrading its certainty.
- Affected stories/contracts: All three observing stories; evidence-to-belief and claim provenance interfaces.
- Status: proposed

## observing-02
- Recipient: carrying; lending; returning; coordinator
- Issue: Co-location alone does not establish visibility, attention, custody, or permission.
- Proposed resolution: Carrying supplies actor/target location and containment/accessibility. Observing checks channel, occlusion, illumination and a bounded attention target; it never writes owner/custodian/location. Lending supplies permission only when an access action actually requires it; physical possibility and social permission remain separate.
- Affected stories/contracts: Library cart inspection; harbor lamp access; observatory viewing slit and recorder.
- Status: proposed

## observing-03
- Recipient: informing; discovering_mistake; coordinator
- Issue: A stale belief, failed inspection and absence observation need distinct semantics; hidden world changes must not notify characters.
- Proposed resolution: Preserve observed-at and subject-time separately. No global invalidation of character belief on a hidden change. Failed inspection records access failure, not falsehood. A negative percept requires complete declared coverage; otherwise record unknown/partial. QA uses reader-visible evidence and timed focus, with explicit abstention.
- Affected stories/contracts: Harbor departure check; library incomplete cart view; observatory outdated reading; follow-up QA.
- Status: proposed
