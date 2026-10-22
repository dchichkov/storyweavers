# Returning: receipt is not settlement

## Scope and existing behavior

Design only: opt-in/versioned semantics; outlines illustrate outcomes, not scripts.
`algebra.py:compose` implements Lend and Return through `runtime.py:transfer`:
the giver must match `.owner`, Return's recipient must match `.loaned_by`, and
completion changes `.owner` and clears `.loaned_by`. Thus wrong-lender rejection
already exists (`test_algebra.py:test_return_cannot_repay_the_wrong_lender`).
It does not identify a particular loan, preserve title during borrowing, support
authorized proxies, or distinguish shelving from settlement. `Move` changes only
object location. Preserve those historical interpretations and frozen worlds.

Reuse role binding from `Kernel.bind`, composition from `algebra.Pattern`, atomic
validation from `runtime.transition`, and timed evidence from `runtime.solve`.
`Conversation.event_description` currently recognizes returns through
Transfer/owner/loaned_by changes; new records need an explicit QA adapter.
`prose.render_book` and `dialogue.collect_dialogue` provide conditional text and
attributed speech, not proof that English states every annotated fact.

`runs/worlds_100_v1/REPORT.md` reports premature returns, duplicate handovers,
stale custody, and offstage questions despite zero deterministic evidence-check
defects. Following `story.py`, concern or responsibility resides in a
character and influences choices; no floating moral event or compulsory happy
settlement is required.

## Reusable contract

**Participants and identity.** Proposed `OfferReturn(actor, loan_id, target,
mode)` references one lending-activated loan and its exact physical object.
`mode` is `hand_back` or `put_back`. The loan records borrower, return authority,
terms version, status, activation evidence, and permitted return targets. Title,
lender, return authority, recipient, and current carrier are distinct roles.
Initially permit one active loan per object; successive loans have different IDs.
Old receipts never settle newer loans.

**State boundary.** Lending owns terms, activation, amendments, and delegated
authority. Returning validates and records discharge of that loan's return
obligation. Carrying owns the single acyclic physical-parent relation and derived
custody/location; returning composes a validated receipt, not a second custody
model. Legal title is read for explanation if needed, never written. Agreements
and interaction records are typed metadata tied to named characters and objects,
not fictitious physical "loan entities" or JSON hidden inside scalar fields.
These need a new schema beyond today's scalar state.

**Prerequisites.** Completion requires an active exact loan, matching object,
current terms, physical control/access, feasible transfer or placement, and a
loan-scoped authority grant valid at performance time. A grant distinguishes
permission to receive custody from permission to discharge. A hand-back also
requires the target's acceptance of this offer. Put-back requires an explicitly
authorized site and satisfied deposit terms, not an absent person's imaginary
acceptance. A third-party courier requires explicit return-on-behalf permission;
otherwise initial scope permits the borrower alone. Selection uses character
evidence and motives; authority validation never refreshes beliefs automatically.

**Atomic performance.** `CompleteReturn` rechecks these prerequisites, applies
carrying's parent change, resolves the offer, and changes exactly the referenced
loan from active to discharged atomically. Stale acceptance cannot bypass revoked
authority or changed custody. Acceptance
does nothing physical. Ordinary pickup, handoff, or placement can occur without
settlement; an unauthorized recipient can physically receive an object without
becoming its owner or clearing the debt. Returning must not prohibit such social
mistakes as physical impossibilities. A designated cabinet deposit can settle
without a human receiver. No reservation, repair, trust, or promise effects
follow automatically.

**Attempts and refusal.** Failed guards during planning are not fictional
attempts. An enacted offer, refusal, or discovered mismatch needs an actual event
and consequence: a pending offer becomes declined, an actor learns the target
lacks authority, or an attempt consumes a meaningful available time window.
Reasons distinguish no active loan, wrong object, unauthorized target, blocked
access, unmet receipt terms, and discretionary refusal. Unknown authority is not
known denial. Failure leaves physical state and loan status unchanged unless a
separate physical act occurred. `transition` rejects unchanged state; event-only
failures need a bounded extension, not dummy flags.
Repeated speech without new consequences is deferred. Pruning must retain
replayed causal interactions and declared pivotal choices, not every rejected
candidate.

**Evidence and non-goals.** Events carry event/offer/loan/object IDs, actor,
target, mode, terms version, outcome, timed reads and changes, authority-source
and activation links, acceptance/refusal IDs, and separately authored motive
evidence. Prose realization has one primary handover event; bridges and endings
must not perform it again. QA additionally requires rendered support spans and
keeps loan/event/time focus through follow-ups. Non-goals: compensation,
automatic forgiveness, legal adjudication,
partial fungible returns, subloans, and inference of authorization from politeness.

## Story 1: Library - The Right Pair of Hands

**Premise and initial evidence.** Nia wants to return a reserved atlas before
closing, then reach her rehearsal. The library owns it; Nia carries it under
active loan `A2`. Earlier loan `A1` for the same atlas is already discharged.
The opening establishes the new checkout and reservation. Inez is upstairs;
volunteer Sol staffs the desk. Nia believes
only Inez can receive it. A loan-scoped delegation actually authorizes Sol to
receive and discharge `A2`; Nia has not learned that yet.

**Six possible beats.**
1. Nia arrives carrying the atlas; co-location permits an offer. Her rehearsal
   goal and concern for the waiting reader motivate a quick hand-back.
2. She offers it to Sol. The pending offer references the current loan, not last
   week's completed checkout; no transfer has occurred.
3. Nia asks whether Sol can check it in. Sol shows Inez's scoped desk delegation;
   observation and informing establish accessible evidence and Nia's acceptance.
4. Sol accepts this offer after checking the atlas identity. Acceptance creates
   readiness, not custody, discharge, or ownership.
5. Nia chooses to trust the verified delegation instead of waiting upstairs.
   The atomic hand-back moves the atlas to Sol and discharges `A2` only.
6. A separate library workflow places it on the reservation shelf. Ending image:
   the waiting reader's name faces outward while Nia leaves with an empty tote.

**Consequential speech** (offer, authority inquiry, evidence delivery, acceptance):

Nia: "Can I return this atlas to you?"
Sol: "Inez authorized me to check in this loan; here is her note."
Nia: "Then please take it."
Sol: "I can receive it now."

**Interventions.** Remove Sol's discharge grant but retain receive-only permission:
a physical handoff may occur, yet `A2` stays active and Inez must settle it later.
Change the offered object to Nia's similar-looking personal atlas: identity
mismatch prevents settlement; the reservation remains unfilled.

**QA with required rendered evidence.**
- Q: Why could Sol finish the return although Inez was upstairs? A: Inez had
  authorized Sol to check in this loan. Sol accepted it and received the atlas.
  Require the shown delegation, acceptance, and actual hand-back, not desk presence.
- Follow-up, Q: Did that make Sol the owner? A: No, the atlas still belonged to
  the library. Sol received it on the library's behalf, settling Nia's loan.
  Require explicit title and receipt/discharge; preserve atlas/`A2` focus.
- Q: Did last week's return settle this checkout? A: No, Nia borrowed the atlas
  again afterward. Today's hand-back settled that newer loan. Require both the
  prior return and subsequent checkout stated in the opening, plus today's receipt.

## Story 2: Harbor - The Gauge That Stayed Aboard

**Premise and initial evidence.** Boat mechanic Ren borrowed Mara's pressure gauge
to finish a repair before the tide turns. Mara owns it; Ren carries it aboard
under `G1`, whose shown terms require a dry gauge for receipt. Mara is an authorized
recipient at the adjacent workshop. Spray has wetted the gauge's casing. Ren
believes the wetness harmless; Mara wants to protect its sensitive seal. The
opening gives both the departure window and the dry-return agreement; discovering
moisture must occur onstage rather than becoming retrospective omniscience.

**Six possible beats.**
1. Ren finishes testing the repair, then carries the gauge to Mara within the
   departure window. Finishing a repair is not itself a return.
2. Ren offers it back; Mara can see the casing. An observation supplies her
   moisture evidence while the offer remains pending.
3. Mara refuses receipt under the agreed dry condition. The offer becomes
   declined; custody, title, and `G1` remain unchanged.
4. Mara explains the seal risk. Informing records delivery and Ren's acceptance
   of her explanation, not an automatic truth/authority change.
5. Ren chooses the departing boat over drying it at the workshop. Ren puts the
   gauge into the boat's padded case, preserving the active return obligation.
6. Departure closes this receipt opportunity. Ending image: the case rests under
   Ren's bunk while Mara's empty gauge hook remains ashore. The loan is unresolved,
   not forgiven, and the repair's success does not erase it.

**Consequential speech** (offer, linked refusal, new information):

Ren: "Here is your gauge, before I sail."
Mara: "I won't take it wet; moisture can reach the seal."
Ren: "Then it stays with me tonight. I am taking this tide."

The last line states a choice, not a promise.

**Interventions.** Start with a dry casing: Mara accepts, Ren hands it back, and
`G1` discharges before departure. Extend the departure window and make Ren's
instrument-care motive outweigh haste: drying becomes feasible and selected,
allowing a later fresh offer and completed return. Neither intervention changes title.

**QA with required rendered evidence.**
- Q: Why did Mara refuse the return? A: The casing was wet, and their agreement
  required a dry gauge. Mara explained that moisture could reach its seal.
  Require the terms, visible moisture, and attributed refusal/explanation.
- Follow-up, Q: Who had it after that? A: Ren still held the gauge. Mara had
  declined to receive it, so no hand-back had occurred. Require explicit retained
  custody; focus stays immediately after refusal, not at later case placement.
- Q: Was Ren's loan finished when the boat left? A: No, Mara had not received
  the gauge, and the return remained outstanding. The gauge sailed with Ren.
  Require an explicit outstanding-loan statement and departure with the case.

## Story 3: Observatory - A Place for the Star Plate

**Premise and initial evidence.** Observer Elin borrowed a calibration plate from
keeper Pavel for a short exposure. The observatory owns it; Elin holds it under
`P1`. Pavel is sleeping ahead of dawn duty. Written terms authorize put-back into
the latched calibration cabinet; the nearby open rack is storage but not a return
site. Elin mistakenly believes the rack suffices. Her goal is another exposure
before clouds arrive, competing with concern for the shared instrument.

**Six possible beats.**
1. Elin places the plate on the rack to free her hands. Carrying changes parent;
   `P1` stays active. Prose explicitly says it has not been checked back in.
2. Technician Noor sees the placement and asks whether the loan is finished.
   The question opens a clarification, not a new loan or return.
3. Together they read Pavel's instructions. Accessible written evidence contradicts
   Elin's rack belief; discovering_mistake preserves and revises that belief.
4. Elin chooses to miss the brief exposure rather than leave the return unresolved.
   She retrieves the plate; the approaching cloud window explains the cost.
5. Elin puts it in the authorized cabinet and latches it. This authored atomic
   deposit validates access, object identity, and latch condition; `P1` discharges
   without any person accepting custody.
6. Clouds hide the target. Ending image: the plate sits secured behind glass;
   Elin closes an observation page with one exposure space blank.

**Consequential speech** (question, mistaken claim, corrective evidence):

Noor: "Does leaving it there finish Pavel's loan?"
Elin: "I thought the rack counted."
Noor: "His instructions say the latched cabinet. Let's read them."

**Interventions.** Change `P1` terms to authorize the rack: the initial placement
can be composed as a valid deposit; no retrieval/cabinet detour is needed. Lock
the cabinet with its key unavailable: retrieval is possible but deposit fails;
Elin retains the plate and the loan stays active, without waking Pavel by fiat.

**QA with required rendered evidence.**
- Q: Why did Elin move the plate again? A: Pavel's instructions required the
  latched cabinet, not the rack. Elin chose to finish the return even though it
  cost the next exposure. Require read instructions and stated costly choice.
- Follow-up, Q: Did Pavel have to take it himself? A: No, his instructions
  allowed a cabinet deposit. Elin secured the plate there while Pavel slept.
  Require authorized deposit terms, completed latch, and established sleeping state.
- Q: Was the plate returned when it first reached the rack? A: No, that was
  only a placement. The loan ended after Elin secured it in the designated cabinet.
  Require both placements and explicit loan-status contrast, not hidden status alone.

## Cross-capability composition

Carrying supplies physical feasibility and parent effects; lending supplies active
loan identity, terms, and authority. Returning owns settlement validation and
discharge, with one transaction boundary agreed by the coordinator. Receive-only
proxies and discharge-capable proxies must remain distinct.

Outside that peer group, observing owns access to the wet casing and written
instructions; informing owns delivered claims and acceptance; discovering_mistake
owns Elin's retained/revised belief evidence. Requesting owns pending interaction
identity and acceptance; refusing owns Mara's linked decline and grounded reason.
These remain proposed dependencies, not available APIs.
Promising may separately monitor a commitment whose performance references `G1`;
returning emits a performance event, never marks every related promise fulfilled.

## Acceptance tests

Proposed tests, not implemented or executed:

- Positive: authorized Sol hand-back discharges only `A2`; `A1` is unchanged.
  Cabinet deposit discharges `P1` with no human receiver; title never changes.
- Negative: no prior activation, old loan ID, wrong object, receive-only proxy,
  revoked grant, blocked cabinet, or stale acceptance cannot discharge a loan.
  Physically feasible unauthorized handoffs remain representable without settlement.
- Refusal: an enacted offer becomes declined with linked evidence; `G1` and
  custody remain unchanged. Rejected planner candidates produce no prose. No-op
  flags are forbidden; meaningful social transitions survive replay/pruning.
- Intervention: assert each of the six changed outcomes above, including the
  observatory failure branch; do not force success by weakening constraints.
- Transfer: bind the same return contract to all settings without title-specific
  branches. Distinct semantics are proxy receipt, refusal with outstanding debt,
  and impersonal deposit, not renamed props or wording permutations.
- Reader QA: each nine-pair example needs timed trace and rendered-span support;
  removing the delegation, terms, or costly-choice sentence must suppress the
  corresponding answer or trigger abstention. Preserve follow-up focus and reject
  future evidence, invented motives, duplicate handovers, and offstage alternatives.
- Compatibility: old owner/Tell semantics and frozen replays remain unchanged;
  new typed events require explicit schema selection and QA realization.

## Open decisions

Smallest slice: one object, sequential loan IDs, borrower return,
one scoped proxy or deposit site, explicit acceptance/refusal, and atomic physical
receipt/discharge. Include failure endings rather than success-only goals. The
coordinator must settle metadata representation, transaction boundary,
and bounded event-only outcomes compatible with pruning. For refusal-only
moments, meaningful interaction-state changes suffice; unchanged repeated speech
is deferred. Defer subloans, partial quantities, damage claims,
conditional forgiveness, competing authorities, and cross-loan debt aggregation.
