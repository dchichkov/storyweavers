# Refusing: Grounded Boundaries Without Erasing Obligations

## Scope and existing behavior

Design only; not implemented or tested. Refusing declines a directed request with
an inspectable basis and consequential social response, not automatic physical
failure or cancellation of related obligations.

Reuse guarded atomic transitions in `storyscenes/runtime.py::transition`, role
binding and candidate composition in `algebra.py::Kernel.bind` and `Pattern`.
`runtime.solve` distinguishes backtracking from fictional events.
Existing `observe` copies truth and `tell` copies stored belief;
neither implements a request/refusal protocol. `dialogue.collect_dialogue`
indexes speech but does not execute its social meaning. `Conversation.causal_answer`
explains prerequisites, not automatically motives. `prose.render_book` checks
card conditions, not all English claims. The 100-world REPORT and TODO document
offstage QA and weak causal explanations despite deterministic evidence checks.

Following `story.py`, preferences and concerns reside in physical characters and
influence choices. No free-floating Refusal or compulsory kindness outcome is
introduced. Proposed `refusing_v2` is opt-in alongside legacy builders, worlds,
traces and exports; no reinterpretation of old ownership or knowledge slots.

## Reusable contract

**Ownership agreement.** Explicitly agree with requesting-01: Requesting alone
writes request response state. Refusing supplies a validated decline decision
and reason record to that operation, never a parallel response-status ledger.
Explicitly agree with promising-01: Promising owns separate commitments;
agreement acceptance is neither physical performance nor necessarily a promise.
Interfaces remain provisional.

**Bounded participants and terms.** One requester, one addressed responder, one
immutable request ID/terms version. Finite action terms name an operation,
participants, target, desired result and time checkpoint. First slice supports
declining a delivered, comprehended, pending request. Already accepted requests
need Requesting's withdrawal/reconsideration operation, not retrospective decline.
Expired, withdrawn, duplicate or mismatched-version responses reject atomically.

**Reads and reasons.** Read the pending request, delivery evidence, responder's
accessible beliefs/evidence and declared goal/preference. Classify the basis as
`inability`, `unwillingness`, or `no_authority`, retaining specific predicates:
physical feasibility, actor choice, and scoped permission are separate dimensions.
An able person may decline; a willing custodian may lack lending authority.
Unknown permission is not proven absence of authority. Author-side validation
can compare a stated reason with world truth, but cannot secretly inform the actor.

Reasons include a proposition, reference time, belief/evidence IDs and an
explicit motive reference when claiming motivation. Record world assessment as
supported, contradicted or unknown, independently of the stated reason. An
honestly mistaken explanation can ground a decline without becoming true;
contradiction alone does not prove a lie. First stories use supported reasons;
deception detection is deferred. Guards establish legality, not why someone chose.

**Atomic effects and evidence.** Validate exact terms and commit the
Requesting-owned pending-to-declined response with the Refusing-owned immutable
reason/decision record, or neither. Record decision ID, request/version,
participants, decision/delivery time, reason kind, referenced predicate and scope,
belief/evidence/motive IDs, optional related commitment ID, response-event ID and
utterance spans. Reference the shared response result rather than copying it.
The decline does not write custody, authority, belief, commitment or reputation.
Requester disappointment or rescheduling requires its own evidenced reaction;
no universal trust penalty follows a refusal.

An alternative references a separate finite proposed request. It is not accepted,
promised or performed merely because suggested. Speech annotations distinguish
request, decline, proposal, acceptance, intention and explicit promise, with exact
IDs and readable wording. Do not infer a promise from every "I'll" phrase.

**Commitment boundary.** Declining a new request leaves an earlier promise intact.
An expressed refusal to perform an existing undertaking also does not discharge
it. Promising alone checks terms, fulfillment, breach, release or renegotiation
at explicit checkpoints; inability may explain nonperformance without excusing it.
A replacement outcome satisfies the old commitment only if its terms permit it
or a separate authorized amendment occurs.

**Event boundary.** Pending-to-declined is meaningful social state, not a dummy
flag. `runtime.transition` currently drops unchanged state: a future structured
record/compiler adapter is required, not JSON hidden inside scalar strings.
Repeated unchanged refusals are deferred. Any later event-only extension needs
finite usage/step bounds, actor/target/time/result and evidence retention through
`planning.prune_path`, followed by replay. Rejected planner candidates are never
failed attempts. An actual unsuccessful attempt requires its own executed event
and observed outcome; none is inferred in these outlines.

Non-goals: universal law, unrestricted action descriptions, multi-addressee
negotiation, automatic persuasion, personality diagnosis or runtime LLMs.
Outlines are possible executions, not mandated routes.

## Story 1: Library - A Place Away from the Microphone

**Premise and initial evidence.** At 16:45, volunteer Elin wants to finish a
picture-book display before the neighborhood library's 17:00 reading. Organizer
Ravi wants a reader. Elin can read aloud and is permitted to use the working
microphone; she prefers quiet preparation, with stage discomfort embedded in her
state rather than treated as physical incapacity. The opening establishes that
she volunteered for displays, not a speaking role. Both know the programme and
17:15 closing time. No speaking promise exists. Her refusal changes the programme,
not her ability; Ravi must choose another reader.

**Six candidate beats.**
1. At 16:46 Ravi delivers request L1: Elin reads one book at 17:00. Pending terms
   establish a real opportunity to answer, not an obligation.
2. At 16:47 Elin declines L1, citing her preference and display goal. The response
   changes to declined; microphone and permission remain unchanged.
3. Ravi, disappointed and short of preparation time, removes her tentative reader
   assignment. His schedule reaction cites the received decline, not assumed shame.
4. Elin proposes preparing the selected book. Ravi issues distinct request L2
   for arranging its pages by 16:55; she accepts without a promise annotation.
5. Elin completes that preparation through a separate domain action. Ravi chooses
   to read; no transfer of Elin's earlier response occurs.
6. At 17:00 Ravi reads beside her display. End on the microphone in his hand and
   the illustrated pages Elin arranged, preserving both contribution and boundary.

**Exchange; executable annotations match these lines.**
Ravi: "Please read the book at five." [request L1]
Elin: "No, I prefer preparing the display. Could I arrange the pages instead?" [decline L1; proposal]
Ravi: "Please have the pages ready by five to five." [new request L2]
Elin: "Yes, I accept that job." [accept L2, not promise]

**Two interventions.** Change Elin's preference to wanting the speaking role:
acceptance and later reading become available, with no forced refusal. Remove
Ravi's ability to read: L1 can still be declined, but page preparation cannot
produce the original reading; a cancelled session is a legitimate outcome.

**Timed reader-supported QA.**
- Why did Elin decline? "She preferred quiet display work to speaking into the
  microphone. She chose that work even though she could read aloud." Requires
  visible opening ability/preference and 16:47 speech, not hidden discomfort.
- Linked follow-up, What did she agree to instead? "She accepted Ravi's new
  request to arrange the pages. She finished that preparation before the reading."
  Retain L1-to-L2 link, then use 16:55 performance, not acceptance as completion.
- Had she broken a promise to read? "No speaking promise had been made. She
  declined the new request and Ravi took the reading role." Render the initial
  limited volunteering terms and replacement assignment; ledger silence is insufficient.

## Story 2: Harbor - The Gauge That Stayed Ashore

**Premise and initial evidence.** At 10:40 Jun needs a pressure measurement before
his boat's 11:00 departure cutoff. Mara holds the workshop's gauge and wants to
help. She is physically able to hand it over, but the workshop's explicit grant
allows only foreman Sal to authorize overnight offsite loans. Sal is unavailable.
The opening shows the verified authority notice, Mara reading it, the gauge on
her bench, and Jun learning the rule. Custody is not lending authority. A local
bench measurement is permitted but takes twenty minutes from readiness.

**Six candidate beats.**
1. At 10:42 Jun requests H1: Mara lends him the gauge overnight on the boat.
   Requesting records delivery; no consent, loan or movement follows automatically.
2. At 10:43 Mara declines with the scoped authority evidence. Her willingness
   remains; this is neither inability nor an arbitrary preference against Jun.
3. She proposes a bench measurement. Jun receives the twenty-minute duration and
   chooses accuracy over this departure slot, making the tradeoff explicit.
4. At 10:44 Jun issues H2 for that service; Mara accepts. This different action
   needs no offsite-loan authority and is not acceptance of H1.
5. The permitted service completes at 11:04, producing a reading. Domain effects
   consume time; custody and workshop ownership stay unchanged.
6. Jun books the next departure rather than pretending the cutoff was met. End
   with the gauge in its workshop cradle and his new sailing time beside the reading.

**Exchange.**
Jun: "Lend me the gauge overnight on the boat." [request H1]
Mara: "No. Sal alone can approve that loan. I can measure it here in twenty minutes." [decline H1; proposal]
Jun: "Please measure it here; I choose the later departure." [request H2; stated choice]
Mara: "Yes, I accept the bench job." [accept H2]

**Two interventions.** Give Mara a valid scoped offsite-loan grant and accessible
evidence: authority refusal loses its support; an authorized lending branch can
allow earlier departure, but still requires consent and handover. Move the cutoff
to 11:10: the same decline and bench service can succeed without missing departure.

**Timed reader-supported QA.**
- Why would Mara not lend the gauge? "She was not authorized to approve an
  overnight offsite loan. The workshop reserved that decision for Sal." Requires
  rendered grant scope and 10:43 refusal, not possession alone.
- Linked follow-up, What could she do instead? "She could measure it at the
  workshop without lending the gauge. Jun accepted the delay and requested that
  service." Preserve H1 focus through the proposed H2 link and visible choice.
- Where was the gauge after the measurement? "It remained in the workshop and
  was placed in its cradle. Jun left with a reading, not the gauge." Requires
  11:04 placement evidence and ending image; do not answer from a stale owner slot.

## Story 3: Observatory - The Frame That Never Arrived

**Premise and initial evidence.** At 21:50, Nila explicitly promises Oren a live
observatory image by 22:10, commitment O0 with no substitution or inability-release
clause. Oren wants a live comparison; Nila wants to supply honest usable data.
The dome motor later seizes. A visible diagnostic at 22:00 establishes that it
cannot open within the remaining window; Nila acquires that evidence. She has
permission and willingness, but lacks physical ability to make the live capture.
An archived chart exists and is clearly dated, not equivalent to a live image.

**Six candidate beats.**
1. O0 is created by the explicit promise at 21:50, separately from any request
   acceptance. Its live-image terms and checkpoint are shown to the reader.
2. At 22:00 an equipment diagnostic produces seized-motor evidence. This is an
   executed inspection, not an inferred failed opening from planner rejection.
3. At 22:02 Oren requests O1: start live capture at 22:05. Nila declines with
   the diagnostic and explains that O0 remains outstanding.
4. She proposes the archived chart. Oren requests that distinct item as O2 and
   Nila accepts; neither speech amends or releases O0.
5. A separate information-delivery action supplies the dated chart at 22:07.
   Oren uses it for planning, but postpones the live comparison.
6. At 22:10 Promising's checkpoint finds no qualifying live-image performance
   and records O0's missed-due breach under its unconditional terms. End with
   the dark dome window above the dated chart: useful help, an unmet promise.

**Exchange.**
Nila: "I promise to send a live image by ten past ten." [promise O0, beat 1]
Oren: "Please start the live capture at five past." [request O1, beat 3]
Nila: "No. The motor is seized. My promise is still outstanding; would the dated chart help?" [decline O1; proposal]
Oren: "Please send the chart, but that does not replace the live image." [request O2; no release]

**Two interventions.** Restore the motor at 22:01 and give Nila evidence:
inability no longer supports declining O1; timely live performance can fulfill O0.
Authorize and execute an explicit O0 amendment allowing the dated chart before
22:07: the same delivery may fulfill amended terms, without rewriting O0's history.

**Timed reader-supported QA.**
- Why did Nila decline the live-capture request? "The seized motor prevented
  opening the dome in time. Nila had the diagnostic result before she answered."
  Requires visible 22:00 evidence and 22:02 reply; no hidden machinery explanation.
- Linked follow-up, Did that cancel her promise? "No, the original live-image
  promise remained outstanding. At its deadline she had sent only the dated
  chart, which did not satisfy those terms." Retain O1-to-O0 focus and render
  initial terms, no-release speech, delivery and 22:10 checkpoint.
- What did Oren receive? "He received the archived chart at 22:07. It helped
  planning, but his live comparison was postponed." Requires dated delivery and
  explicit subsequent planning consequence; do not invent an observation.

## Cross-capability composition

Outside the social peer group, observing owns diagnostic/notice acquisition;
informing owns claims, receipts and belief acceptance; discovering_mistake owns
conflicting-belief revision. Refusing only references their timed records.
Carrying owns gauge placement/custody; lending validates grants and activates
loans; returning owns identified discharge. A refused return offer needs its
owner's lifecycle adapter, not a duplicate Refusing status. Shared transactions
must reject conflicting writers. Pruning must retain response, motive, deadline
and reader-support dependencies even if an endpoint is reachable without them.

## Acceptance tests

Proposed tests, not execution claims:
- Positive: one delivered pending request produces exactly one declined response
  and linked reason; physical, belief and commitment state remain unchanged.
- Negative: wrong addressee/version, undelivered request and duplicate decline
  produce no narrated event. Accepted requests cannot become initial declines.
- Reason separation: ability plus authority does not compel acceptance; custody
  does not prove permission; unknown permission cannot justify asserted absence.
- Commitment: accepted L2 creates no promise; O1 refusal cannot discharge O0;
  archived delivery cannot fulfill live-only terms. A valid amendment can change
  the latter result while preserving prior versions and evidence.
- Intervention: replay both interventions per setting, checking changed legality,
  deadlines, performance and endings, not just alternate prose.
- Transfer: rebind the same decline contract across all settings; swap reason
  predicates while holding props fixed. Preference, delegation and equipment
  changes must yield distinct dependencies, not noun-swapped stories.
- Evidence: all nine QA answers require timed rendered support and correct linked
  focus; removing support forces abstention. Future diagnostics cannot explain
  earlier choices. No candidate rejection becomes an attempt or quotation.
- Compatibility: future implementation must replay frozen legacy fixtures
  unchanged and preserve meaningful social evidence under bounded pruning/replay.

## Open decisions

Smallest slice: single-addressee pending declines, finite terms, three reason
kinds, separately requested alternatives and explicit commitment checkpoints.
Unresolved interfaces: checked Requesting/Refusing transaction and record schema;
Promising's exact breach/amendment/checkpoint API; authority predicate provenance;
reader-span/motive adapters; and bounded event-only retention for unchanged speech
or actual attempts. Defer multi-party negotiation, repeated refusals, deception
inference and automatic reputation. Coordinator reconciliation and cross-review
remain separate from this completed first pass.
