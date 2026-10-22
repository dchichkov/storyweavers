# Lending capability proposal

Design only, 2026-10-21; not implemented or tested.

## Scope and existing behavior

Reuse role binding/composition (`algebra.py`: `Kernel.bind`, `Pattern.__add__`), atomic validation (`runtime.py`: `transition`), and timed traces (`solve`). Existing `algebra.compose` implements Lend through `runtime.transfer`: `.owner` becomes the borrower and `.loaned_by` records the giver. Return reverses those slots. `test_algebra.py` rejects the wrong lender; it does not establish delegated authority, consent, custody, or deadlines. Historical interpretation stays unchanged.

Proposed opt-in `lending_v2` separates title, lending authority, agreement, custody, and obligation. `conversation.py` recognizes legacy loans through Transfer/owner changes; new records need a QA adapter. `dialogue.collect_dialogue` supplies speech evidence, not executable consent. `prose.render_book` cannot certify its English. The 100-world `REPORT.md` and `TODO.md` identify duplicate handovers, premature returns, stale custody, and offstage questions despite green evidence checks.

Following `story.py`, generosity or caution lives in a character's embedded state and affects choices; permission lives in a concrete relationship concerning an object. Neither becomes a floating moral event.

## Reusable contract

**Participants and representation.** Bind owner O, authorized lender L, borrower B, object P, current custodian C, and designated return recipient/site R. O, L, C, and R may differ. Proposed typed records, outside today's scalar-only schema, are indexed by P and participating physical carriers, not fictitious physical "loan" entities. No JSON-in-string workaround. Carrying provisionally owns an acyclic physical-parent relation and derived custody/location; lending never duplicates these fields.

Immutable terms contain `agreement_id`, `revision`, P/O/L/B, authority-grant ID, permitted use/area, collection window, due trigger, R, receipt/discharge policy, and no onward lending. Grants identify issuer, delegate, object, scope, validity, and delegation rights. Finite records may be predeclared initially. A loan has a distinct `loan_id`, agreement revision, activation event, return debtor B, status, due status, and discharge evidence.

**Read/write protocol.** Requesting owns the request; its absence does not prevent an unsolicited offer. `OfferLoan` reads an effective scoped grant and records lender consent to exact terms. Borrower acceptance reads delivered, comprehended terms and records explicit consent to that revision. It changes neither possession nor title and is not a promise or proof of delivery. A purported unauthorized offer remains a claim, never valid permission. Unknown authority does not pass validation, but is not classified as false.

`ActivateLoan` reads both consents, current grant validity, unexpired collection window, unmodified terms, no incompatible active loan, and carrying's feasible receipt from C to B. L also needs authority to release custody through C; title alone cannot teleport an object. One atomic transaction applies carrying's physical effects, opens the loan, and activates B's obligation to return P to R under the recorded terms. Ownership is unchanged. A request acceptance is not borrower consent unless explicitly bound to this agreement revision. Optional promises reference the agreement but remain separately owned commitments.

Before activation, rejection, withdrawal, revocation, or expiry closes eligibility without a return debt. After activation, passing the due trigger marks the loan overdue; it does not move P, discharge the debt, or forbid physical actions. Scope breaches record noncompliance, not impossible motion. Returning owns validated settlement of the identified loan, atomically coupled to carrying's receipt; receiving custody and possessing discharge authority are distinct. No unilateral deadline extension. Revised terms require the relevant parties' consent. Post-activation recall is deferred.

**Evidence and failure.** Events include operation/version, participant/object/loan IDs, terms revision, grant source, timed reads/changes, related request and utterance IDs, physical receipt ID, and explicit motive references when supported. Reader support maps each asserted permission, acceptance, handover, and deadline to rendered spans. Hearing permission does not establish authority; observation/information acceptance never grants it.

Failed guards remain nonexecuted candidates. A narrated refusal must resolve a real pending interaction; a failed collection attempt must record actual access/result evidence. `runtime.transition` rejects unchanged state; repeated speech without meaningful state change needs a future bounded evidence-event facility, not dummy flags. `planning.prune_path` must retain consent dependencies and consequential evidence, then replay; relevance must include social outcomes, not only final custody.

Non-goals: title transfer, general legal adjudication, coercion models, insurance, fungible stock, automatic trust rewards, and universal moral success. Unauthorized taking remains physically possible through carrying, but cannot masquerade as an authorized loan.

## Story 1: Library - The Lamp Before Four

**Premise and evidence.** Bea wants to finish a fine-print map before leaving. Marta owns a lamp deposited at the neighborhood library; librarian Ivo holds it with Marta's displayed lending authorization. Noah's reservation begins at four. Bea assumes overnight borrowing is possible without reading the reservation slip. The opening shows the lamp, ownership/authorization note, Bea's goal, reservation, and window light sufficient for broad outlines.

**Event outline.** All three outlines are candidate paths, not prescribed routes.

1. Bea requests an overnight loan; requesting creates a pending request, not consent or custody.
2. Ivo reads the reservation and offers use until 3:45, return to him at the desk. His stated motive is keeping the lamp available for Noah; scoped authority permits this shorter interval.
3. Bea reads the slip and accepts that exact counteroffer. Her overnight request is resolved by the linked response; she chooses less copying time rather than abandoning the map.
4. At the desk, Ivo hands Bea the lamp. Physical receipt activates the loan and return duty; Marta retains title.
5. Bea copies the needed route, stopping with marginal notes unfinished because the due time approaches. Her expressed priority, not merely a clock guard, explains stopping.
6. Bea returns it to Ivo by 3:45; returning discharges this loan. The ending shows Noah's map lit beneath the same lamp while Bea folds her useful, unfinished copy.

**Consequential exchange.** Each line has its own speech-act link.

Bea asked Ivo, "May I take the lamp overnight?"
Ivo told Bea, "Until 3:45, back to me here. Noah has it at four."
Bea replied, "I accept 3:45. I only need the route."

**Interventions.** Remove Noah's reservation, leaving an authorized overnight option: Ivo can offer longer terms and Bea can finish the margins. Have Bea decline the short terms: the lamp stays at the desk, no loan opens, and she leaves with only the broad route copied in daylight.

**QA, with required rendered support.**

- Who owned the lamp while Bea used it? "Marta still owned it. Bea had temporary custody under Ivo's loan." Require the ownership note and actual handover, not only a hidden owner field.
- Why did Bea stop copying? "She wanted the lamp back before Noah's reservation. She chose the route over finishing her notes." Require beats 2, 3, and 5, including Bea's expressed priority.
- Linked follow-up, "Who received it then?" "Ivo received the lamp at the desk. That completed Bea's return under the agreed terms." Preserve the same loan/object focus; require beat 6's receipt and completion, not inference from arrival.

## Story 2: Harbor - The Dry-Bench Loan

**Premise and evidence.** Rui needs a wrench to repair a detached pump before the departure bell. Sal owns it; workshop keeper Tessa has custody. Sal's signed grant allows lending only at the dry bench, with return to Sal there by the bell. Tessa believes her older unrestricted permission applies. The reader sees both notes, rain outside, and Rui's pump on helper Jo's trolley. The complication is delegated scope.

**Event outline.**

1. Rui requests the wrench for work aboard the launch; Tessa voices her remembered permission. Informing records a claim, not a valid unrestricted offer.
2. Reading the current signed grant gives Tessa conflicting evidence. Discovering_mistake preserves the earlier belief and records correction: the old scope is now outdated, not necessarily originally false.
3. Tessa declines the aboard-use request and offers a dry-bench loan. Her stated concern is keeping Sal's wrench out of the rain; no wrench moves during this response.
4. Rui chooses to bring the detached pump inside and accepts the restricted terms. Transport changes the pump's physical parent/location, not wrench ownership or loan status.
5. At the bench Tessa hands him the wrench; valid authority and receipt activate the loan. Owner Sal, lender Tessa, borrower Rui, and return recipient Sal remain distinct.
6. Rui repairs the pump on the bench, then sets the wrench in its tray. Placement does not discharge his obligation: Sal has not received it and the tray is not an authorized deposit site.
7. Rui waits beside the tray for Sal while Jo carries the repaired pump toward the launch. The ending holds the departure bell rope motionless; the loan remains active, not overdue yet.

**Consequential exchange.**

Tessa told Rui, "I remembered the old permission. Sal's new note says the dry bench only."
Tessa asked Rui, "Will you use it here and return it to Sal by the bell?"
Rui replied, "Use here, return to Sal by the bell. I accept."

**Interventions.** Give Tessa an explicit unrestricted current grant: an aboard-use agreement becomes available and the pump need not travel inside. Make the pump fixed aboard: restricted lending cannot achieve the repair; Rui must seek another tool or miss departure, not receive an invented exception.

**QA, with required rendered support.**

- Why did the pump come inside? "Rui accepted a loan limited to the dry bench. Bringing the pump there let him repair it within those terms." Require the grant, counteroffer, acceptance, and transport.
- Linked follow-up, "Who allowed that?" "Tessa offered the loan under Sal's dry-bench authorization. Sal remained the wrench's owner." Retain the restricted-loan focus; require both signed scope and Tessa's offer.
- Had Rui returned the wrench when he put it down? "No. It was in the tray, but Rui still owed its return to Sal." Require explicit pending-return narration and the agreed recipient; do not equate empty hands with discharge.

## Story 3: Observatory - The Detector That Stayed Upstairs

**Premise and evidence.** Sana wants a precise comet exposure from the mountain observatory's lower annex. Leena owns a portable detector kept by Kit in the summit equipment room. Kit can lend it for collection before ten and return by dawn. Sana has a basic camera that cannot produce the desired exposure. Both initially believe the connecting walkway will remain open; the reader receives these facts through the equipment label, posted terms, forecast, and Sana's stated aim.

**Event outline.**

1. Sana requests use of the detector, motivated by its sensitivity rather than a general wish to borrow.
2. Kit offers the authorized terms; informing delivers them to Sana. No delivery commitment is included: collection is her option.
3. Sana explicitly accepts. The agreement is eligible for collection, but the detector remains in Kit's cabinet and no return debt exists.
4. A gust closes the walkway before Sana travels. Observing records the closure; informing delivers that report to Sana without moving anyone or the detector.
5. Sana chooses a basic sky record instead of an attempted crossing. Her stated concern about the closed walkway and available camera grounds the choice; no failed handover is invented.
6. Ten passes. The uncollected agreement expires, not an active loan; Sana records a coarse sky image, losing the precise exposure she wanted.
7. Kit closes the cabinet on the detector still in its fitted recess while Sana dates the modest image downstairs. This ending proves the missed opportunity and continued custody.

**Consequential exchange.**

Kit told Sana, "Collect it before ten; return it by dawn."
Sana replied, "I accept those terms."
After receiving the closure report, Sana told Kit, "Then it stays with you. I'll record what I can down here."

**Interventions.** Keep the walkway open: Sana can travel, receive the detector, activate a loan, and make the precise exposure. Have Sana decline the dawn deadline: no accepted agreement exists even before the closure; her coarse observation follows a scheduling choice rather than an expired collection opportunity.

**QA, with required rendered support.**

- Why did Sana not get the detector? "The walkway closed before she could collect it. The collection window then ended without a handover." Require the closure report, cabinet continuity, and expiry narration.
- Linked follow-up, "Did she owe it back?" "No return duty began because she never received it. Accepting the terms had not moved the detector." Keep the agreement/object focus; require explicit noncollection and no-duty explanation in the story.
- Where was it at the end? "The detector remained in Kit's summit cabinet. Sana used the basic camera downstairs instead." Require both final images and locations; hidden initial location alone is insufficient.

## Cross-capability composition

Carrying owns physical feasibility, parent changes, and derived locations; lending couples activation to its receipt without requiring a duplicate handover scene. Returning owns loan-ID settlement and scoped recipient/site checks. Their visible message proposals are compatible provisionally; exact transaction and grant shapes remain unresolved.

Outside that peer group, requesting owns pending requests and linked counteroffer resolution; refusing owns declines; promising owns optional independent commitments. Those agents are queued, so no agreement is claimed. Observing supplies accessible, timed grant evidence. Informing supplies claim delivery/comprehension/acceptance, never authority; discovering_mistake owns Tessa's preserved old belief and revision. Loan acceptance is a domain act referring to terms, not generic belief acceptance. Prose/QA need explicit new adapters and reader-support links, not inference from legacy labels.

## Acceptance tests

- Positive: delegate L hands P to B under accepted terms; assert owner O unchanged, exactly one receipt, active loan ID, and correct debtor/R. Run the same contract in all settings.
- Negative: request only, offer only, mismatched revision, unknown/revoked grant, closed access, or acceptance without receipt never activates a loan. Unauthorized taking can change custody without producing authorized-loan evidence.
- Temporal: overdue status preserves debt and physical location; uncollected expiry produces no debt. Wrong recipient or ordinary placement cannot discharge. Repeated loans require distinct IDs; returning one cannot close another.
- Intervention: reservation removal, restricted-grant replacement, and walkway reopening must change legal opportunities/outcomes. Altering dialogue phrasing or names alone must not.
- Evidence: each outlined QA answer needs timed trace support plus visible supporting spans; suppress unsupported starters and abstain on unrecorded motives. Follow-ups retain loan/event focus. Check all nine pairs manually against selected prose.
- Replay/transfer: preserve social turns through pruning and replay; never narrate rejected candidates. Rebind roles/props without setting-name checks. Hold out a setting and verify authority, custody, and obligation semantics transfer. Three causal structures, not renamed equipment, constitute variety.

## Open decisions

Smallest slice: finite typed grants/agreements/loans, one nonfungible object per loan, explicit acceptance, receipt activation, fixed deadline, no onward lending, and returning's designated recipient. Coordinator must settle atomic receipt composition, physical-parent custody derivation, authority evidence versus actual grants, expiry clock, social-event retention, and new QA support indexing. Defer recall, renegotiation during active loans, contested title, and replacement/compensation. These examples authorize no implementation and claim no passing tests.
