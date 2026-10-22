# Lending interface proposals

## lending-01
- Recipient: carrying, returning, coordinator.
- Issue: Existing `algebra.compose` implements Lend/Return through `.owner` and `.loaned_by`; that cannot distinguish legal owner, authorized lender, and temporary custodian.
- Proposed resolution: Opt-in capability version keeps title unchanged; a carrying-owned handover atomically activates a lending-owned loan and return obligation. Return identifies the loan's designated recipient, not necessarily its owner or original lender. Preserve historical worlds unchanged.
- Affected stories/contracts: All three lending outlines; handover activation and discharge interface.
- Status: proposed.

Read-once reconciliation: carrying-01's physical-parent/derived-custody proposal and returning-01/02's loan-ID/scoped-settlement proposal fit the draft. Carrying owns the physical receipt, lending owns activation, and returning owns discharge; the coordinator still needs to choose their atomic composition API. These are not frozen agreements.

## lending-02
- Recipient: requesting, promising, refusing, coordinator.
- Issue: A request, an offer, borrower acceptance, a promise, and delivery must not collapse into one successful loan event.
- Proposed resolution: A request references desired terms; authority-backed offer and explicit borrower acceptance bind a versioned agreement without moving the object. Activation requires actual handover. Optional promises are separate commitments; rejection/expiry leaves custody untouched.
- Affected stories/contracts: Library reservation deadline; harbor delegated authority; observatory unfulfilled accepted offer.
- Status: proposed.

Requesting/promising/refusing were queued at the coordinator's relay. The proposal leaves their records and speech-act classification to those owners; it requires explicit consent to the exact loan terms, not a request's generic acceptance.

## lending-03
- Recipient: observing, informing, returning, coordinator.
- Issue: Hearing permission is not proof of authority; expiry or overdue status is not a physical return, and hidden permissions cannot justify reader-facing causal QA.
- Proposed resolution: Record authority source, exact consent terms, timed speech/evidence IDs, and physical handover separately. QA uses rendered evidence and retains loan/event focus; overdue loans remain active until a valid discharge or explicit cancellation disposition.
- Affected stories/contracts: Harbor false belief about delegation; observatory missed collection window; loan-status questions.
- Status: proposed.

Compatibility follow-through: the proposal distinguishes rejected candidates from real refused requests/expired collection windows. It requests bounded evidence events and social-outcome retention with replay, not dummy flags to bypass unchanged-state rejection. Reader-support indexing and the expiry clock remain unresolved.
