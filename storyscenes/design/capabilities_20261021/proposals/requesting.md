# Requesting: directed action without implied completion

First-pass design recommendation, not implemented or tested. This proposal
supports R01-R04 in DECISIONS.md provisionally; cross-review remains separate.

## Scope and existing behavior

A request directs one actor toward a bounded action. Silence, acceptance,
refusal, and performance must support different endings.

Existing `algebra.Kernel.bind` and `Pattern` offer role-bound, namespaced
opportunities, not scripts. `runtime.transition` checks guards and applies effects
atomically, but rejects unchanged state. `runtime.solve` produces events only
for the selected path: rejected candidates are not attempted actions.
`runtime.validate_spec` permits only scalar state on named carriers. Consequently
the records below require an explicit future schema/compiler, not JSON hidden in
strings or fabricated physical request entities.

Preserve legacy `runtime.tell`, which copies stored belief, and
`algebra.compose`'s Lend/Return ownership-plus-lender behavior and object-only
Move. New requests never reinterpret those operations. An opt-in capability
version and explicit rendering/QA adapter are mandatory.

This follows `story.py` through physical speakers, listeners, and written
messages, with character goals and meme magnitudes influencing choices.

## Reusable contract

**Participants and finite terms.** One requester and one addressee; any beneficiary
is explicit. An immutable request identifies
its ID, version, physical participants, delivery evidence, action kind, performer,
exact object/target, recipient or result, and named completion checkpoint. Terms
use a small domain registry: reserve a slot, deliver an object, open a gate,
make an observation, or read an archive. Each domain supplies validation and a
performance matcher. No arbitrary Python predicates or natural-language goals.
Changed terms require a new request linked to its predecessor.

**State and ownership.** Requesting alone writes response
`pending -> accepted | declined`. Delivery/comprehension is separately recorded;
acknowledgment leaves the response pending. Lifecycle is separately open,
withdrawn, or expired, preserving an earlier acceptance. Performance is a linked
domain receipt, not another response state. A pending request may remain pending
at the ending. Checkpoint assessment is explicit; elapsed prose or silence is
not decline. Withdrawals stop further requested work but do not undo actions.

I explicitly agree with requesting-01, refusing-01, and promising-01: Refusing
validates and supplies a decline decision and reason; the checked transaction
uses Requesting's sole pending-to-declined operation. There is no parallel
refusal-owned response status. Promising alone owns its separate commitment
ledger. Accepting expresses assent to undertake the specified task; it neither
guarantees success nor creates a promise. A promise can reference a request, or
exist without one. Withdrawal, inability, and expiry never settle commitments.

**Reads, prerequisites, effects.** Issue reads declared participants, finite
terms, communication access, and an actor-accessible goal/belief motivating the
ask. It creates one carried interaction. A response requires comprehended
delivery, the exact ID/version, an open pending interaction, and the addressee's
own decision or explicitly scoped response authority. It atomically writes one
response and its attributed evidence. A messenger cannot accept for someone
merely by delivering words. Repeated responses and stale versions fail closed.

Asking does not require that the action is physically possible or authorized;
people may ask mistakenly. Acceptance does not manufacture authority either.
Performance owners recheck actual feasibility, scoped authority, resources, and
time when acting. Physical impossibility, lack of authority, and unwillingness
are distinct predicates, not interchangeable reasons. Social preferences and
obligations influence choices, not universal physics guards. Explicit domains
may distinguish executable unauthorized conduct from authorized success.

**Performance and evidence.** A domain receipt names event, actor, operation,
object, target/result, time/checkpoint, and terms version. Requesting links it
only to an accepted open request matching those fields. A pre-existing desired
state or another actor's similar action is not requested performance. Independent
achievement can be reported separately. Physical handover never itself activates
or discharges a loan: lending and returning own those effects, composed atomically
with carrying where appropriate.

Events preserve request/response IDs, before/after status, exact speech spans,
speaker/addressee, reply link, reason-belief/goal references, authority source,
and domain receipt references. Assertions of authority or completion remain
claims until the relevant operation/evidence establishes them. Observing and
Informing retain ownership of evidence and belief changes; hearing words never
automatically establishes their truth or acceptance.

Executable speech-act annotations must agree with rendered words. An ambiguous
"I'll..." is not automatically a promise; intention, acceptance, and commitment
need distinguishable wording/context and explicit acts. A composed acceptance
and promise invokes both owners only when both acts are established.

A decline changes real social state, even without moving anything. An enacted
failed attempt requires a bounded future event receipt with actor, target,
observed result and evidence. Failed guards emit nothing. Do not add meaningless
flags to bypass unchanged-state rejection. Defer repeated unchanged speech.
`planning.prune_path` currently preserves pivotal/state dependencies and replays;
the future adapter must also preserve linked request, response and evidence
dependencies. The registry does not supply this today.

## Story 1: Library - The Card Before the Cart

**Premise and evidence.** Mira wants a projector booking for her shadow-story
club. Volunteer Pax wants to help but cannot make reservations. Clerk Edda has
booking authority. The reader sees the projector on its shelf, the three-to-four
reservation, and the unbooked four-to-five slot before closing. Mira does not yet
know whether the later slot is available. Edda must inspect the current register.
Mira's eagerness competes with her stated wish not to displace another club;
neither desire grants permission.

**Seven beats.**
1. Mira addresses a request to Edda: reserve the projector for four-to-five;
   the club needs certainty before making its invitation cards.
2. Pax delivers the written request. Edda receives it while finishing a checkout;
   comprehension is recorded, but its response remains pending.
3. Pax acknowledges delivery. Mira nearly fetches the equipment cart, then
   chooses to leave it because she still has no booking decision.
4. Edda inspects the register; Observing supplies current availability evidence,
   distinct from granting a booking.
5. Edda explicitly accepts the exact slot request. No reservation has yet changed.
6. The reservation operation rechecks availability and Edda's scope, then writes
   Mira's booking and emits the matching performance receipt.
7. Edda hands Mira the booking card. Mira writes the club's invitations beside
   the still-shelved projector: the uncertainty is resolved, not a loan performed.

**Exchange** (attributed and linked to the corresponding beats):
- Mira: "Edda, please reserve the projector from four until five."
- Pax: "She has your note. That isn't a booking yet."
- Edda: "I accept that slot request. Now I can enter it."
- Edda, after entry: "Here is your booking card."

**Interventions.** Remove delivery: Edda cannot respond; Mira has no booking,
and cannot print a confirmed time. Occupy four-to-five before entry: acceptance
remains recorded, but the atomic booking fails and no completion receipt exists;
the story must show the conflict or end with the booking unresolved.

**QA**, with reader-visible support required:
- Why did Mira leave the cart alone? "Pax had confirmed delivery, not a booking.
  Mira wanted to avoid displacing another club." Render her choice and stated goal.
- Linked follow-up, "What happened next?": "Edda checked the register and accepted
  the slot request. She then entered the booking." Keep focus on this request and
  show the distinct check, response, and entry.
- Had Mira borrowed the projector? "No loan occurred in this story. The projector
  remained on its shelf while Mira received a booking card." Render the final
  location and distinguish reservation from borrowing explicitly.

## Story 2: Harbor - Accepted at the Workshop Door

**Premise and evidence.** Repairer Neri wants an already-authorized courier,
Jules, to deliver a caliper to Captain Ivo at slip two before departure. Jules
believes the walkway is open; that belief was accurate earlier. The reader sees
the named recipient, deadline, and permitted custody handoff. A later storm
closure is a real change, not proof Jules was previously mistaken. Gatekeeper
Ola can operate the gate but cannot authorize a storm exception.

**Seven beats.**
1. Neri issues the exact delivery request. Jules receives and accepts it;
   acceptance creates neither a loan nor an unspoken promise.
2. Carrying performs the authorized workshop handoff and Jules travels with the
   caliper to the gate; title remains unchanged.
3. Storm conditions close the walkway. Jules sees the closure notice and locked
   gate; Observing supplies updated evidence rather than omniscient notification.
4. Jules requests that Ola open it for this delivery. This is a new pending
   request, not a change to the original recipient or destination.
5. Ola declines, citing the closure and her limited authority. Refusing supplies
   that reason; Requesting writes the single declined response.
6. Jules reports the obstruction. Neri receives the report and explicitly withdraws
   the delivery request; no receipt to Ivo and no promise release are invented.
7. Jules carries the caliper back to the workshop under separate movement
   authority. Ivo departs without it; the dry tool beside the unfinished repair
   gives the ending its cost. No loan discharge is implied.

**Exchange:**
- Neri: "Please take this caliper to Ivo at slip two before departure."
- Jules: "I accept the delivery task."
- Jules, at the gate: "Ola, please open it for me."
- Ola: "No. The storm closure is in force; I cannot grant an exception."
- Neri, after the report: "Withdraw that delivery. Bring the caliper back here."

**Interventions.** Keep the walkway open: the existing accepted request can lead
to an actual Ivo handoff before departure. Give Ola scoped exception authority
but retain a physical impassability condition: authority alone still cannot
produce delivery; refusal may cite physical inability rather than lack of scope.

**QA:**
- Why was the delivery unfinished? "The storm closed the walkway after Jules
  accepted. Ola declined the gate request, and Neri withdrew the delivery."
  Render the timing, refusal, and withdrawal, not just a locked-gate fact.
- Linked follow-up, "Had Jules promised?": "Jules accepted the task, but did not
  make a separate promise. The story records an acceptance, not a commitment."
  Render the acceptance unambiguously; if wording implies a promise, reject the
  realization rather than use hidden metadata to contradict it.
- Who had the caliper at the gate? "Jules was carrying it. Ivo had not received
  it." Show the handoff and continuous custody; do not infer it from acceptance.

## Story 3: Observatory - The Blank in the Transit Log

**Premise and evidence.** Suri wants a fresh transit observation before the
window closes. Toma is the qualified telescope operator. A frosted lens can be
exposed physically, but Toma's embedded Care and expressed preservation goal
favor keeping it sealed. Suri has no command authority. Both see the frost
warning; an accessible archive contains yesterday's observation, not today's.
The reader receives these distinctions before anyone proposes the substitute.

**Six beats.**
1. Suri asks Toma to open the telescope and record today's transit at the named
   checkpoint. The addressed, comprehended request becomes pending.
2. Toma reads the current temperature evidence. Physical opening remains
   possible; choosing not to expose the lens is not a simulator rejection.
3. Toma declines, stating the preservation goal and risk. The response changes
   to declined; the shutter and observation log remain unchanged.
4. Suri chooses to narrow the work instead of pretending the refusal was consent:
   she issues a new request to read yesterday's archived measurement.
5. Toma accepts that separate request. The archive operation checks read access
   and copies the dated entry to Suri's working sheet, with its source retained.
6. Suri labels the sheet "Yesterday" and leaves today's observation line blank.
   The closed shutter and dated sheet prove useful work happened without a
   fabricated new sighting or compulsory moral victory.

**Exchange:**
- Suri: "Please open the telescope and record this transit."
- Toma: "I decline. I want to preserve the lens while it is frosted."
- Suri: "Then please read yesterday's measurement with me."
- Toma: "I accept that request. We must keep yesterday's date on it."

**Interventions.** Remove frost and its risk: Toma's stated reason no longer
supports that refusal; acceptance and a fresh observation become available,
not mandatory. Remove archive access: the substitute cannot be performed;
acceptance cannot produce a record, and today's line still remains blank.

**QA:**
- Why did Toma decline? "Toma wanted to preserve the frosted lens. Opening was
  possible, but he chose not to expose it." Render the preference, frost evidence,
  and choice; do not describe an impossible action.
- Linked follow-up, "What did Suri ask instead?": "She asked to read yesterday's
  archived measurement. That was a new request, not acceptance of the first."
  Link both request IDs and show their different dates/actions.
- Was today's transit recorded? "No. Today's line stayed blank, and the sheet
  contained yesterday's measurement." Render both the blank and the date; hidden
  log state alone cannot answer story-comprehension QA.

## Cross-capability composition

Accept the peer boundaries in carrying-03, lending-02, returning-03,
informing-03, and discovering_mistake-02 provisionally. Carrying supplies physical
receipts, not delivery assent. Lending owns loan agreement/activation; Returning
owns identified discharge. A request to receive an object cannot authorize
settlement. Observing supplies timed accessible evidence; Informing distinguishes
receipt, claims and belief adoption; Discovering Mistake owns conflicting belief
revision, not material correction. Domain authority providers supply scoped
grants, not authority inferred from speech. This proposal needs these interfaces
but does not duplicate their records or effects.

The future QA adapter needs focus `(request_id, version, event/checkpoint)` and
rendered support spans. Follow-ups preserve that focus; ambiguous alternatives
ask for clarification. Current `Conversation.causal_answer` explains enabling
guards, not all motives. `prose.render_book`'s fact bindings and
`dialogue.collect_dialogue`'s annotations do not prove free-English entailment.
Missing rendered evidence requires abstention. The existing trial's grounding
and stale-custody defects motivate manual story/QA alignment, not extra hidden facts.

## Acceptance tests

Proposed gates only; none were executed in this design round.
- Positive: one delivered request supports exactly one accepted or declined
  response; exact domain performance links only after the appropriate acceptance.
- Negative: receipt-only acknowledgment stays pending; unauthorized proxy,
  stale version, wrong performer/recipient, and late receipt cannot satisfy terms.
- Separation: acceptance moves nothing and creates no commitment; withdrawal
  preserves acceptance history and leaves an independent promise unsettled.
- Failure: a selected refusal retains its reason and response; rejected search
  candidates create neither speech nor attempts. Replay/pruning retains evidence.
- Interventions: exercise all six changes above, checking material outcomes and
  rendered causal QA rather than only state-key differences.
- Transfer: rebind the same request/response/matcher contract across all settings.
  Delayed assent, accepted-but-blocked delivery, and declined work with a dated
  substitute must remain different causal structures after removing names/props.
- Language: reject commitment-sounding prose annotated only as intention; omit
  support for a QA answer and require abstention without losing request focus.

## Open decisions

Smallest slice: finite single-addressee requests, explicit delivery, one response,
withdrawal/checkpoint expiry, exact domain receipts, and indexed dialogue. Defer
delegated responses, negotiation trees, groups, inferred promises, and repeated
unchanged assurances. Coordinator decisions remain necessary for the structured
record/compiler boundary, bounded event-only receipts, checkpoint ordering, and
evidence-preserving pruning. Authority providers and performance matchers need
shared minimal signatures; receiving custody and settling a loan stay separate.
