# Observing: Accessible Evidence, Not Omniscient Knowledge

## Scope and existing behavior

Design only; implementation requires new approval.
`storyscenes/runtime.py::observe` copies a physical fact into
`actor.knows.fact`; access is whatever guards the author supplies. `tell` copies
stored belief, including stale belief. `algebra.py::compose` declares missing
knowledge slots as `None`; `test_algebra.py` pins stale transmission and
independent observation orders. Reuse immutable role binding, candidate
composition, atomicity and timed traces.

`runtime.holds` blocks numeric comparisons against `None`, but generic `ne`
is not epistemic reasoning. `Conversation.event_description`, `source_answer`
and `truth_answer` need adapters beyond their fact-copy vocabulary.
`prose.render_book` records bindings; `dialogue.collect_dialogue` validates speech.
Neither certifies English entailment. The 100-world REPORT and TODO's
`offstage_entity_question`, `wrong_speech_event` and `weak_causal_focus` defects
make reader support a separate obligation.

This proposal approaches `story.py`'s north star by attaching attention, evidence
and beliefs to people and physical sources. Embedded Curiosity or Care motivates
checking without exposing invisible facts. It does not reinterpret
legacy Observe, Tell, ownership, Move, saved runs or exports.

## Reusable contract

Propose opt-in `observing_v2`, composed as opportunities, not a mandatory route.
Outlines illustrate possible executions, not scripts.
`Attend(observer, target, purpose_ref)` directs bounded attention.
`ObserveEvidence(observer, target, channel, question, scope)` acquires a percept.
Participants: observer, physical target/source, optional instrument, proposition
subject. Purpose references a goal or embedded meme; access explains possibility,
not motive.

**Reads and legality.** Read event-time physical-parent paths and effective
locations from carrying; target exposure, channel reach, illumination, instrument
capability, observer attention and available time. Same-room presence is
insufficient. A lamp can reveal a surface without revealing its contents, owner
or another person's intention. Reading a label establishes its inscription, not
that its assertion is true. Device readings require a declared deterministic
measurement projection, never direct access to an arbitrary hidden property.

Attention has a target and finite duration/cost; pattern division remains search
weighting. Choices depend on accessible beliefs/purposes, sensor results on
truth. Indistinguishable states must offer identical intentional checks.

**Writes and atomic effects.** Commit an observer-bound receipt and declared
time/battery cost together; append its immutable trace record. Record
`id`, `event_id`, `observer`, `source`, `subject`, `predicate`, `scope`, `channel`,
`observed_at`, `subject_time`, `result`, `coverage`, `access_witness`,
`purpose_ref`, and source/evidence links. `subject_time` may be explicitly
unknown; it must not default to receipt time for an old recording.

`result` is tagged `exact(value)`, `partial(alternatives)`, or `unknown(reason)`.
False and zero are exact values. Unknown is neither false nor a usable value
for inequality guards. Partial alternatives must come from observable features,
not the simulator secretly eliminating possibilities. An exact, interpreted
percept may initialize an unknown belief or refresh matching support through a
named acquisition policy. A conflict preserves both evidence and prior belief;
discovering_mistake owns discrepancy classification and supersession. Ambiguity
does not erase an earlier belief. Beliefs retain source and reference time;
unseen changes never update them or notify their holders that they are stale.

**Failures and boundaries.** An illegal observation candidate never happened.
A legal inspection attempt may return unreadable, occluded or insufficient
coverage evidence without answering its question. "Not found on the visible
shelf" is not "absent from the library." Negative evidence requires a declared
complete search domain and adequate channel. Rechecking can yield new temporal
support even with identical values; repeating identical wording alone is not
new evidence.

`runtime.transition` rejects unchanged state; `planning.prune_path` slices state
dependencies. A future adapter must admit bounded receipts/attempts without
physical change, retain decision/revision/QA dependencies, and replay them.
No dummy flags, JSON-in-strings or invented physical "event" entities: structured
records need a versioned schema beyond scalar state. Non-goals: claim acceptance,
belief revision, legal permission, transport, repair, mind reading and runtime
LLMs.

## Story 1: Library - The Book Behind the Apron

**Premise and state.** Before opening, Inez wants to prepare Ravi's reserved
atlas; Ravi wants time with its foldout maps. The atlas is on a lower return-cart
shelf behind a canvas apron. Inez is at the desk, attending to reservation
cards; her atlas-location belief is unknown. The opening shows her limited viewpoint, without
revealing the atlas. Her complication is incomplete search, not a missing book.
She chooses to inspect before cancelling the reservation. The ending image is
Ravi's finger tracing the foldout beside the folded-back apron.

**Six candidate beats:**
1. Ravi requests the atlas for opening time; requesting owns the pending request.
   Inez's Care and goal motivate checking.
2. Inez attends to the cart from the desk. Only its upper shelf is visible;
   acquisition records no atlas there, with lower-shelf coverage unknown.
3. Rather than mark the whole reservation unavailable, Inez asks Ravi to wait
   beside the desk. The request does not change book truth.
4. Inez walks to the cart and lifts its apron through separate physical actions.
   The lower shelf becomes exposed; observing never moves the cart or atlas.
5. A focused shelf inspection supplies exact atlas-presence evidence. Inez's
   unknown location belief acquires scoped support.
6. Carrying places the atlas on the reading table after the separate permission
   decision. Ravi's reading fulfills the request; seeing it alone did not.

**Exchange, indexed at beats 3 and 5:**
- Inez: "Wait here while I check under the apron." A waiting request, not a loan.
- Ravi: "All right; keep my reservation." Acceptance preserves his request.
- Inez: "Here it is, on the bottom shelf." A sourced claim after inspection.

**Interventions.** Keep the apron closed and remove alternate access: location
stays unknown and the request remains pending, rather than becoming a confirmed
absence. Start with the apron open: direct inspection can find the atlas sooner,
without the uncovering/waiting dependency; prose must omit those unexecuted acts.

**QA, tied to events and rendered support:**
- Q: Why did Inez look under the apron? A: "She wanted to fill Ravi's
  reservation, and her first look covered only the upper shelf. She checked the
  hidden shelf before declaring the atlas unavailable." Require the request,
  stated purpose and visible coverage limitation.
- Linked Q: Did that first look prove the atlas was missing? A: "No. Inez could
  not see the lower shelf, so the atlas's whereabouts were still unknown to
  her." Keep focus on the first inspection, not the later discovery.
- Q: How did she learn where it was? A: "She lifted the apron and inspected the
  exposed shelf. She saw the atlas there before taking it to the table."
  Require uncovering, observation and placement.

## Story 2: Harbor - A Glint Before the Tide

**Premise and state.** Jun wants to finish a pump repair before the boat's
departure; Mae wants an intact borrowed inspection lamp returned. The pump is
clamped on a workshop bench. Its underside has a real crack; from Jun's present
angle, a wet seam and a crack produce the same glint. Jun believes neither
diagnosis yet. The reader first sees only the glint and approaching departure
time. Jun chooses a slower inspection over an unsupported clearance. The ending
image is the tagged pump beside Mae's returned lamp while the boat waits dark.

**Six candidate beats:**
1. Jun attends to the pump and sees the glint. The declared channel returns
   partial moisture-or-damage evidence, not `crack=True`.
2. He requests Mae's lamp, explaining the unresolved seam. The request does not
   grant custody; lending separately records consent and a physical receipt.
3. Mae agrees; carrying hands over the lamp. Jun can now illuminate the
   underside, but possession alone has not produced an observation.
4. With the pump still safely clamped, Jun directs the beam under it. He sees
   a gap through the metal; the specified projection supports a crack diagnosis.
5. Jun reports this evidence and chooses not to clear departure. Informing owns
   delivery/acceptance; refusing owns a scoped refusal to certify this pump.
6. Jun returns the lamp using its loan ID and receipt conditions. The pump
   remains tagged, not magically repaired or made safe by truthful speech.

**Exchange, indexed at beats 2 and 5:**
- Jun: "May I use your lamp? I cannot tell what that line is." A borrowing request.
- Mae: "Yes; bring it back before you leave." Consent with return terms.
- Jun: "The light shows a gap through the metal. I cannot clear this pump."
  A sourced report plus refusal, each with its own effect owner.

**Interventions.** Remove lamp access and all equivalent channels: the crack
remains unconfirmed; Jun may defer clearance because evidence is insufficient,
but must not report a diagnosed crack. Replace the crack with moisture while
keeping the initial glint identical: the same inspection choice remains
available; exact moisture evidence supports drying/retesting and potentially
clearance through the repair domain, not automatic success.

**QA, tied to events and rendered support:**
- Q: Why did Jun borrow the lamp? A: "The glint did not distinguish water from
  damage. He needed light under the pump before deciding whether to clear it."
  Require explicit alternatives and his stated inspection purpose.
- Linked Q: What did it reveal? A: "Jun saw a gap through the metal. That was
  new evidence for a crack, unlike the earlier glint." Require the lit view;
  retain the pump and inspection focus across the follow-up.
- Q: Did returning the lamp fix the pump? A: "No. The lamp went back to Mae,
  while the pump remained tagged and uncleared." Require both ending states;
  no inference from return completion to repair completion.

## Story 3: Observatory - The Reading from Six O'Clock

**Premise and state.** Sal wants one clear-sky exposure before midnight; Noor
wants enough battery reserved for the weather recorder. At six, Sal observed
clear sky. At eight the dome is shut and cloud now covers the viewing sector,
unseen by Sal. A paper recorder strip still bears the six-o'clock reading;
its timestamp is readable. The opening establishes Sal's earlier belief and
the old strip, not present sky truth. Sal chooses a small inspection cost rather
than spending the remaining exposure power. The ending image is an unused plate
beside a still-ticking weather recorder.

**Six candidate beats:**
1. Sal reads "clear" on the strip. Evidence concerns the strip's inscription;
   it does not refresh his sky belief to eight o'clock.
2. Attention shifts to its timestamp. Sal observes six o'clock and recognizes
   that the record supplies no current sky measurement.
3. Sal asks Noor to help open the viewing slit. Request acceptance and opening
   remain distinct; no reply creates visibility by itself.
4. With the slit open, Sal inspects the target sector. Direct evidence records
   cloud there now, without claiming the whole mountain sky is clouded.
5. discovering_mistake revises the current-use belief while preserving the
   valid six-o'clock observation: outdated evidence, not a proven earlier error.
6. Sal shelves the unused plate and reserves power for the recorder. These
   physical/operational actions, motivated by conserving scarce power, create
   the ending; observation does not guarantee an exposure or a moral victory.

**Exchange, indexed at beats 3 and 6:**
- Sal: "That strip is two hours old. Help me open the slit before I spend the battery."
  A help request with a recorded reason.
- Noor: "I'll open it now." A commitment, not yet completed performance.
- Sal: "Cloud in our sector. Keep the recorder running; I'll leave the plate."
  A sourced report and a request, followed by separately recorded choices.

**Interventions.** Prevent slit opening with no alternate channel: current sky
remains unknown to Sal; any postponed exposure is explained by uncertainty,
not knowledge of cloud. Make the current sector clear: the old record stays old,
but the fresh view supports an exposure if power and instrument guards permit.
The initial timestamp observation must not predict which branch occurs.

**QA, tied to events and rendered support:**
- Q: Why did Sal check outside instead of relying on the strip? A: "Its
  timestamp showed that it described six o'clock. Sal needed current evidence
  before using the remaining exposure power." Require timestamp and spoken aim.
- Linked Q: Was that earlier reading wrong? A: "The story says the sky was
  clear at six. Seeing cloud at eight shows a later change, not an error in the
  six-o'clock reading." Require both timed observations in the narrative.
- Q: What did Sal preserve by leaving the plate unused? A: "He reserved power
  for the weather recorder. The unused plate and running recorder show his
  choice at the end." Require explicit allocation and ending image, not a
  hidden numeric battery field alone.

## Cross-capability composition

Informing owns claims, receipts and adoption; evidence IDs supply provenance,
not truth or acceptance. discovering_mistake owns conflict
comparison, temporal classification and revision. Carrying's proposed physical
parent paths supply access evidence without revealing closed contents or
changing beliefs. Lending owns authority/consent and loan activation; returning
owns scoped receipt and discharge. Observing cannot infer permission or debt
from seeing a handoff.

Outside the primary peer group, requesting owns waiting/help/borrowing requests;
promising owns Noor's commitment and its later fulfillment; refusing owns Jun's
clearance refusal. Each references a typed action specification and event ID.
Opening, repair and battery allocation remain separate domain actions.
All interfaces remain proposals.

## Acceptance tests

- Positive: exposed target plus appropriate attention/channel produces scoped,
  timed evidence; exact false/zero values acquire valid support. Two independent
  checks can execute in either order without shared mutable definitions.
- Negative: co-location without attention, closed containment, darkness,
  unreadable timestamps and inadequate instruments never reveal hidden facts.
  Unknown fails both positive and negative value assertions; incomplete search
  cannot prove absence. Rejected candidates produce no narrated attempts.
- Temporal: hidden world changes preserve old beliefs. Reading an old strip
  preserves subject time; contradictory later evidence retains the earlier
  record until explicit revision. Reinspection can refresh evidence without
  changing the measured value.
- Intervention: execute all six interventions above; compare acquired evidence,
  feasible decisions and material endpoints, not just changed wording. Preserve
  identical intentional checks across observationally identical hidden states.
- Transfer: bind the same access/projection/receipt contract across shelf search,
  illuminated diagnosis and timestamped recording. Require distinct coverage,
  ambiguity and staleness failures; changing prop names alone is not variety.
- QA/prose: every answer and causal second sentence needs rendered support
  spans plus event/evidence/entity/time references. Hide a support sentence and
  abstain; never answer from offstage truth. Follow-ups preserve scope/time.
  Review English entailment manually as well as checking records.
- Lifecycle: bounded failed inspections survive replay when later choices cite
  them; irrelevant checks remain prunable. Legacy fixtures keep their original
  interpretations. These are proposed tests, not claimed passing results.

## Open decisions

Smallest slice: finite channels, exact/unknown/partial results, one attention
target, timed receipts and explicit acquisition policy.
Coordinator must settle structured-record storage, event-only replay/pruning,
and the acquisition-versus-revision boundary with informing/discovering_mistake.
Also unresolved: carrying's access-witness format and cross-event speech-act
links. Defer probabilistic perception, continuous vision, deception detection,
automatic inference and forgetting; none is needed for these three turns.
