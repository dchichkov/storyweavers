# Promising: Undertakings Without Guaranteed Success

## Scope and existing behavior

Design only; no runtime changes or tests are claimed. Reuse role-bound candidate
composition in `storyscenes/algebra.py::Kernel.bind` and `Pattern`, atomic
effects in `runtime.transition`, and timed snapshots in `runtime.solve`.
`algebra.BUILTINS` has no promise operation. Custom Act labels alone do not
establish a reusable commitment contract. `runtime.validate_spec` currently
requires scalar, entity-embedded state; structured records need an explicit
future compiler, not JSON smuggled into strings.

`runtime.transition` drops unchanged states and rejected guards. Neither is
evidence that a character tried and failed. `Conversation.causal_answer`
explains prerequisites, not motives. `dialogue.collect_dialogue` indexes speech
annotations but does not execute promises. `prose.render_book` fact bindings do
not prove English entailment. The 100-world report and `storyscenes/TODO.md`
show why story-only QA requires additional visible support.

Agree explicitly with requesting-01 and the coordinator relay: Requesting alone
writes request response state; Refusing supplies its validated decline decision.
Promising maintains no parallel accepted/declined request state. Agreement
acceptance is neither performance nor necessarily a promise. This follows
`story.py` by embedding commitments and choice-relevant Care in named people,
not treating Obligation as an unattached force or a universal success condition.

## Reusable contract

**Proposed `commitment_v1`, opt-in only.** Each run has bounded, predeclared
commitment slots attached to a physical promisor, addressed to one beneficiary.
Immutable terms contain ID/version, promisor, beneficiary, action-spec ID/version,
creation event, optional request/agreement ID, and optional deadline checkpoint.
The finite action specification binds actor, operation, object, recipient or
target, required result, and whether personal performance is required. First
slice supports one achievement, not arbitrary temporal logic or recurring vows.
Records are social state carried by participants, not invented physical entities.

**Create.** Read identified participants, available channel/understood receipt,
exact terms, and an explicit executable `promise` speech act. Voluntary means
the promisor performs an undertaking rather than merely being assigned a task;
it does not prove sincerity or future ability. Unsupported coercion contexts
are outside this slice. Create atomically fills an unused slot with active status
and links the undertaking receipt. A request is optional: unsolicited promises
are legal. Beneficiary acknowledgment is not required after understood delivery.
Undelivered words do not create this interpersonal commitment. Communication
owns receipt/comprehension, not the commitment write. Joint validation must
prevent a commitment referencing a receipt that never occurred.

"I'll look at it" can be an intention. Do not classify promises by that phrase.
Executable act annotations, exact rendered speech, speaker, addressee and terms
must agree; ambiguous wording fails authoring review. An explicit promise does
not require a feasibility guard: someone can overcommit. Impossible performance
does not become physically possible because it was promised.

**Assess.** Read immutable domain receipts and checkpoint order. Only matching
post-creation performance fulfills: correct actor, object, target, result and
time. Intention, a completion claim, mere placement nearby, or a matching state
that predated the undertaking is insufficient. Domain owners supply effects;
Promising alone writes settlement and its evidence links. A loan's discharge
remains Returning-owned; an optional promise to return references that event
without duplicating the loan lifecycle.

Statuses are active, fulfilled, released, or breached. At an explicitly authored
deadline, process all performance ordered through that checkpoint, then assess
once. A verified miss becomes breached, whether caused by inability or choice;
this is a terms violation, not a judgment of blame. Inability evidence records
its scope/time separately and does not release or fulfill anything. Unknown
feasibility is not inability. A later matching performance is linked as late
repair without erasing the breach. No deadline means active until performance,
release, or the bounded story horizon, not automatic breach at story ending.

The beneficiary may explicitly release an active commitment; release is not
fulfillment. Revised terms require release plus a new versioned undertaking,
preserving predecessors and any prior breach. No silent deadline extension.
Conflicts are derived from finite resource/time requirements, not duplicate
conflict flags. Character choice uses accessible evidence and embedded goals;
omniscient conflict diagnostics do not give characters knowledge. Social duties
may influence selection but never forbid otherwise feasible conflicting actions.

**Evidence and bounds.** Keep event/commitment/terms IDs, participants, operation
receipt, before/after status, checkpoint/time, motive references, and separately
timed inability claims and verified tests. Checkpoint absence checks require
complete coverage of the simulated interval, not missing narrative paragraphs.
Unknown coverage cannot justify breach. Each slot has one creation and bounded
settlement; event-only actual attempts additionally need an explicit finite
budget and replayable result receipts. No dummy flags. Planner rejection emits
diagnostics only. Retain undertaking, deadline, release and outcome dependencies
through pruning, replay and rendering. QA needs visible supporting spans as
well as trace evidence; hidden state is debugging evidence only.

Old worlds, exports, `.owner` semantics and traces remain intact. New records,
event-only support and QA realization require a versioned adapter. Non-goals:
legal enforcement, automatic trust penalties, mind reading, group promises,
unbounded renegotiation, and universal moral-success goals.

## Story 1: Library - One More Chapter

**Premise, goals and evidence.** Mira wants to finish the atlas's final chapter;
Ezra needs that reserved atlas at the desk before five for his walk. Initially
Mira holds it, both are in the reading room, and the desk is reachable before
closing. The opening states the reservation, clock and Mira's reading wish.
Both know the deadline. The complication is not physical impossibility but her
temptation to treat leaving it on a cart as enough. She chooses exact delivery.

**Six beats; candidate opportunities, not a prescribed script.**
1. Ezra requests personal handover of this atlas at the desk by five. Requesting
   creates the pending request; the reservation motivates him.
2. Mira accepts through Requesting, then explicitly promises those terms.
   Promising creates L1; neither speech moves the atlas.
3. Wanting another minute with the chapter, she puts it on the nearby cart.
   Carrying records placement; no matching handover or fulfillment exists.
4. Ezra points out that he is waiting at the desk. Mira recalls her undertaking
   and chooses to stop reading rather than leave him searching.
5. She retrieves it, travels to the desk, and hands it to ready Ezra at 16:59.
   Carrying owns the receipt; L1 settles from that exact performance.
6. Five arrives with L1 fulfilled. End with Ezra tracing his route across the
   open atlas and Mira's bookmark resting on the now-empty cart.

**Speech with effects.**
Ezra: "Please hand me this atlas at the desk by five."
Mira: "I accept your request. I promise to hand it to you there by five."
Ezra, later: "I'm at the desk; the cart isn't the handover we agreed on."
The first creates a request; the second explicitly composes acceptance and
undertaking. The third communicates a discrepancy, not a new promise.

**Two interventions.** Remove only the undertaking act and its promise wording:
acceptance and delivery remain possible, but there is no promise to fulfill.
Delay the handover until 17:02: the five-o'clock assessment records breach;
later receipt is late repair, not on-time fulfillment.

**Timed reader-supported QA.**
- Why did Mira leave her chapter unfinished? "She chose to honor her promise
  before five. Finishing the chapter would have delayed Ezra's atlas." Require
  visible goal, explicit choice, terms and clock, not a Care guard alone.
- Linked follow-up, "Was leaving it on the cart enough?" "No. She had promised
  to hand it to Ezra at the desk, and the cart placement did not do that. The
  later handover fulfilled it." Keep L1 and the 16:59 receipt as focus.
- When was her promise fulfilled? "At the 16:59 handover, before five. Saying
  the promise earlier had not delivered the atlas." Render both times and
  physical receipt; hidden settlement metadata is insufficient.

## Story 2: Harbor - The Latch After the Bell

**Premise, goals and evidence.** At the harbor workshop, Neri wants Pavel's
delivery chest ready for departure. Without being asked, she promises personally
to fit its replacement latch before the eight-o'clock bell. The reader sees the
exact chest, apparently suitable spare, deadline and her wish to help. Neither
knows that the spare's thread is wrong. Unlike the library choice, a real
material mismatch defeats competent effort; honest warning cannot fulfill it.

**Six beats.**
1. With Pavel listening, Neri voluntarily undertakes H1. No synthetic request or
   acceptance record is created.
2. Neri makes an actual fitting test. A bounded domain test receipt records the
   attempted fit, rejected thread and unchanged broken latch; this is not a
   search candidate's failed guard.
3. She observes the mismatch and revises her suitability belief. The test
   supports inability with the available spare, not permanent impossibility.
4. She tells Pavel before eight. He acknowledges receipt but does not release
   H1; he chooses a different chest for today's delivery.
5. At eight the original latch remains unfitted. Complete interval receipts
   support deadline breach, without blaming Neri or inventing negligent intent.
6. A compatible spare arrives later; she fits it at 08:20. End with the repaired
   chest catching the light beside an empty departure berth. Late repair does
   not rewrite the missed departure or H1's history.

**Speech with effects.**
Neri: "I promise to fit this chest's latch before the eight-o'clock bell."
Neri, after testing: "This spare won't fit. I cannot finish with this part."
Pavel: "I understand. I'll use another chest today."
The first creates H1; the report communicates bounded inability. Pavel's line
acknowledges and declares a plan, not another promise or release.

**Two interventions.** Supply the compatible spare initially: fitting can
finish before eight and H1 fulfills. Have Pavel explicitly release H1 at 07:50:
the deadline does not breach that released commitment; later repair remains
ordinary work, not fulfillment of an active promise.

**Timed reader-supported QA.**
- Why was the promise missed? "The available spare had the wrong thread, so
  Neri could not fit it. The original latch was still unfitted when eight
  arrived." Render actual test, available inventory and deadline result.
- Linked follow-up, "Did telling Pavel settle it?" "No. She warned him, but
  the promised repair still had not happened. Pavel acknowledged her warning
  without releasing her." Require report, reply and explicit unchanged terms.
- Did Neri eventually repair that chest? "Yes, at 08:20 with the later spare.
  That repaired the chest but did not make her eight-o'clock promise on time."
  Render arrival, fitting receipt and both times; retain H1/chest focus.

## Story 3: Observatory - Two Promises, One Cell

**Premise, goals and evidence.** At the mountain observatory, Sera has promised
Ivo personally to record a calibration exposure by 22:00, and promised Tamsin
personally to transmit her valley report by 22:00. Initial speech establishes O1
and O2 separately. She believes there are two charged cells; an inventory check
shows only one usable, single-use cell. Both tasks are individually feasible but
jointly infeasible before the deadline. The report supports Tamsin's departing
survey team; calibration matters to Sera's research. Neither goal is universal.

**Six beats.**
1. Both explicit undertakings create separate records with different action
   terms and beneficiaries; neither reserves or consumes a cell.
2. Sera opens the battery box and tests its contents. Observation and revision
   replace her two-cell belief with the evidenced single-cell inventory.
3. Knowing each task consumes one cell and no recharge finishes before ten,
   she recognizes the conflict and explains it to both beneficiaries.
4. Ivo declines her request for release. Requesting owns that declined response;
   O1 remains active, and no prohibition prevents Sera choosing transmission.
5. She explicitly chooses the time-sensitive valley report. The transmitter
   consumes the cell and records successful transmission at 21:58; O2 fulfills.
6. At ten the calibration exposure is absent under complete checkpoint coverage;
   O1 breaches. End with the transmitter receipt beside a dark calibration
   monitor. The choice accomplishes something and leaves a genuine cost.

**Speech with effects.**
Sera to Ivo: "Only one cell works. Will you release my calibration promise?"
Ivo: "No. I still need that exposure tonight."
Sera: "I understand. I'm choosing the valley transmission; their team leaves."
The exchange requests release, records refusal, and states a grounded decision.
It does not silently cancel O1 or turn unwillingness into physical inability.

**Two interventions.** Add a second usable cell: both performances can finish,
eliminating resource conflict. Have Ivo grant release before transmission: O1
ends released, not breached; the physical ending may remain identical while
the social consequence changes materially.

**Timed reader-supported QA.**
- Why did Sera transmit instead of calibrating? "She chose the report because
  Tamsin's team was leaving. With one single-use cell, she could not complete
  both tasks before ten." Render inventory, consumption rule, goals and choice.
- Linked follow-up, "Did that cancel her other promise?" "No. Ivo declined
  to release it. The calibration promise was missed at ten even though the
  transmission succeeded." Keep O1/O2 distinct with visible reply/checkpoint.
- Was calibration forbidden? "No. She could have used the cell to calibrate
  instead. Her choice spent it on transmission, leaving calibration undone."
  Render both executable alternatives before consumption, not an invented
  failed calibration attempt afterward.

## Cross-capability composition

Requesting exclusively owns request responses, including release requests;
Promising validates an affirmative release before writing commitment status.
Refusing owns grounded decline proposals, not a second response ledger.
Lending owns loan activation and Returning its discharge. Carrying supplies
handover receipts without changing promise status. Outside the social peer
group, Observing supplies the test percept; discovering_mistake owns revision;
Informing supplies inability delivery without changing truth or excusing breach.
Equipment actions own fitting, cell consumption and transmission. R01-R04 are
provisional dependencies, not frozen agreements. Shared transaction, receipt,
clock and rendering interfaces still require coordinator reconciliation.

## Acceptance tests

Proposed, not executed:
- Positive: requested L1 and unsolicited H1 create only from explicit understood
  undertaking; exact on-time receipts settle each once, without domain rewrites.
- Negative: acceptance, intention, loan consent, completion claims, wrong
  recipient/object, and pre-creation performance never fulfill a promise.
- Boundary: receipt ordered at the deadline qualifies; later receipt preserves
  breach. Unknown event coverage cannot prove a miss. Inability does not release.
- Conflict: both observatory alternatives remain physically selectable before
  consumption; duties influence choice without making violation illegal.
- Attempt: actual fitting test has result evidence; rejected fitting candidates
  produce no story event. Event budgets terminate repeated unchanged attempts.
- Interventions: execute all six stated changes and inspect physical and social
  outcomes separately, including identical physical endings with different status.
- Transfer: bind the same create/match/assess/release operations to handover,
  repair and transmission; no setting-name branches. These vary choice, material
  inability and competing obligations, not merely props or phrasing.
- QA/preservation: remove each required rendered support span and require
  abstention; keep timed commitment focus across follow-ups. Replay retained
  evidence and verify frozen legacy fixtures remain unchanged.

## Open decisions

Smallest slice: finite slots, one promisor/addressee per commitment, one bounded
achievement, explicit checkpoints, exact receipts and beneficiary release.
Unresolved interfaces: action-term vocabulary and receipt matching; typed record
compiler; communication/undertaking atomicity; event-only attempt replay and
retention; checkpoint ordering and coverage certification; executable speech-act
annotations with reader-support spans. Defer partial credit, delegated promises,
conditional vows, sanctions and autonomous renegotiation. No implementation is
authorized by this proposal.
