# Returning interface proposals

## returning-01
- Recipient: lending; coordinator.
- Issue: Existing `algebra.compose` Return matches `.loaned_by`, not a specific prior loan; future repeated loans and proxies require explicit identity.
- Proposed resolution: Opt-in v2 loans have immutable `loan_id`, object, borrower, return authority, and discharge terms. Return discharges exactly one active loan ID, never the latest lender/name match; authority grants distinguish receiving custody from discharging it. Align with lending-01: the designated return authority need not be owner or original lender.
- Affected stories/contracts: All three returning outlines; lending creation and returning settlement.
- Status: proposed.

## returning-02
- Recipient: carrying; lending; coordinator.
- Issue: Hand-back and put-back have different physical targets; neither should change title or silently discharge an obligation.
- Proposed resolution: Align with carrying-01: carrying owns the acyclic physical-parent relation and derived custody/location. Returning atomically couples validated handoff/placement effects to discharge only when the person or deposit site satisfies the loan terms. Ordinary placement remains placement; an unapproved shelf leaves the loan active. Coordinator must define the transaction boundary.
- Affected stories/contracts: Library authorized proxy; harbor refused handoff; observatory designated cabinet.
- Status: proposed.

## returning-03
- Recipient: refusing; requesting; informing; coordinator.
- Issue: Refused receipts and claims of proxy authority must not be interpreted as successful return or true authorization.
- Proposed resolution: A return offer is a pending interaction referencing loan ID, object, target, and terms version; refusal changes that interaction to declined without physical/loan effects. Informing owns claim delivery and belief acceptance; only a world-level scoped grant establishes authorization. Acceptance and performance remain separate. Per COMPATIBILITY.md, rejected candidates are not enacted failures; unchanged event-only outcomes need a bounded explicit extension, never meaningless flags. First slice uses consequential interaction transitions and defers unchanged repeated speech.
- Affected stories/contracts: Harbor refusal; library proxy verification; reader-grounded causal QA.
- Status: proposed.
