# Capability slices: acceptance ledger

Independent acceptance specification, frozen 2026-10-22. User approval covers
all three slices; the design documents' earlier approval warnings are historical.
This file specifies evidence still needed, not completion, code grades, or test
results. All boxes remain open. Coordinator owns implementation and core choices.

Closeout note (2026-10-22): the original unchecked specification below is retained
unchanged for audit. Current dispositions and executable evidence for every gate
are in [ACCEPTANCE.md](ACCEPTANCE.md); do not read these historical checkboxes as
the current implementation status.

Authority: [SYNTHESIS](../SYNTHESIS.md), [DECISIONS](../DECISIONS.md) (overrides
conflicting drafts), [INTEGRATION_GATES](../INTEGRATION_GATES.md), and the
[physical](../reviews/physical.md), [epistemic](../reviews/epistemic.md), and
[social](../reviews/social.md) reviews. Proposal examples are regression inputs,
not a requirement to implement 27 scripts or accept their unreconciled wording.

## Evidence contract

For each gate below, attach a local test ID/command and fixture/seed, expected
assertions, before/after semantic state and identified events, and replay output.
For an intervention, retain both runs and explain the changed dependency and
outcome; different prose alone is insufficient. For reader gates, attach selected
prose, QA/follow-ups, support spans with event/entity/time references, masked-support
results, and a semantic reading review. Internal annotations alone prove no English
entailment. No runtime or judge APIs, paid evaluation, or quality scores are required
by this ledger. Rejection diagnostics are allowed but are not enacted story events.

## Shared requirements (all slices)

- [ ] X1 / C00, D01: One explicit opt-in typed schema/compiler boundary and explicit
  prose/QA adapters; no opaque nested JSON strings, silent legacy reinterpretation,
  independent family runtimes, or setting-title dispatch. Pin old builders, exports,
  fixtures and replays, including Move/Transfer/Lend/Return and stale-belief Tell.
- [ ] X2 / C01-C05: Named bounded operations declare reads/effects/provenance;
  each effect has one writer. Compose against one common pre-state and commit
  all effects or none, including domain postconditions. Deterministic replay
  preserves invariants, stable identities and idempotency; no hidden mutation or
  arbitrary string predicates. Evidence remains embedded in identified carriers.
- [ ] X3 / D07: Intentional checks use accessible actor beliefs/goals; matched
  hidden-state variants offer identical intentional checks. Physical results use
  world truth. Guard dependencies are not motives; obligations are not physics.
- [ ] X4 / C06, D07: Failure, refusal, uncertainty, breach and unresolved endings
  remain admissible, not success-filtered. Illegal/unselected candidates emit no
  attempt, speech or motive. Actual bounded attempts/utterances/inspections may
  leave physics unchanged; no dummy flags or unbounded event loops.
- [ ] X5 / D07: Pruning retains dependencies of selected turns/QA (including
  unchanged parent paths, evidence, replies and authored motives), then replays
  legally. Unused checks remain prunable; neither retain everything nor mark
  every event pivotal. Compare full and retained traces, not endpoints alone.
- [ ] X6 / C01, R04: Truth, character belief and reader evidence are separately
  queryable. Prose and comprehension QA share selected support; simulator-only
  facts stay in diagnostics. Hide each necessary support span and omit/abstain
  on its answer, including causal second sentences. Reject future evidence,
  unsupported lies/motives and offstage alternatives; preserve follow-up ID/time
  focus or fail closed, never guess. Full natural answers must stay grounded.
- [ ] X7: Review rendered stories and QA together for causal/temporal agreement,
  premise, consequential turn and ending evidence, not merely valid schemas.
  Report semantic outcomes/intervention sensitivity separately from duplicate
  rate, compression and literary quality; no inherited numerical pass claim.

## Slice 1: physical continuity and loans

- [ ] P1 / D02: One acyclic parent graph; derive effective location and
  `physical_holder` through nested passive containers. Owner, borrower, keeper
  and release authority remain distinct. Bench placement can leave no holder
  while responsibility persists; authorized shelf/cabinet collection needs no
  invented actor custodian. Travel moves contents without revealing them.
- [ ] P2: Pickup, Put, Travel and Handoff enforce current source/path, reach,
  exposure/access, route, mass/hands and recipient readiness. Exercise remote or
  wrong-source pickup, closed containment, overload, occupied-hand crossing,
  cyclic placement and double holding. Permission cannot bypass physics;
  physically feasible unauthorized movement is distinct from authorized lending.
- [ ] P3 / D03-D04: Every performed pickup/handoff/deposit has one immutable
  receipt identifying operation, object, source/destination, participants and
  time. Receipt readiness binds actual giver/recipient/object/operation; loan
  consent binds terms/version; return acceptance binds offer/loan. None is
  belief adoption. Duplicate performance cannot fabricate a second handover.
- [ ] P4: Finite predeclared scoped grants/terms; one object per active loan.
  Offer, delivered/comprehended terms, both consents and collection are distinct.
  Accepted-but-uncollected equipment creates no receipt or return debt; collection
  expiry creates no debt. Activation requires current grant, revision, window,
  source/access/capacity and compatible loan status; exactly one receipt opens
  the identified obligation without changing ownership. Request/claim alone cannot.
- [ ] P5 / R01, D03-D04: Immediate authorized return or designated deposit
  atomically combines physical receipt and discharge of only the matching active
  loan/object. Wrong/old loan, wrong object/recipient, absent activation, revoked
  grant, blocked access or stale acceptance cannot settle. Ordinary placement,
  overdue status and receive-only handoff leave debt outstanding. Cabinet latch
  is an explicit domain postcondition, not a generic Put side effect.
- [ ] P6: Revalidate all joint reads at performance after readiness/grant/location
  changes; assert no partial physical/social writes. Reader QA distinguishes
  owner, holder, location, borrower and identified loan status with timed paths.

## Slice 2: evidence, communication and revision

- [ ] E1 / D05: Accessible observation requires event-time path, exposure,
  channel/instrument and attention witnesses. Exact false/zero is not unknown;
  partial/failed inspection cannot establish global absence. Complete declared
  coverage can establish exact absence. Co-location alone reveals nothing.
- [ ] E2 / R02, D05: Typed propositions retain subject/value/scope/reference
  interval; evidence/claims retain source, immutable parents, actual versus
  attributed provenance and acquisition/emission/delivery times. Direct speech
  and a bounded delayed channel separate assertion, receipt, comprehension and
  explicit adoption. A failed delivery makes no receipt; acknowledgment is not
  adoption. Reject inaccessible channels, unsupported sources and ambiguous times.
- [ ] E3: One validated belief writer commits explicit basis/policy-linked
  initialization, adoption or discrepancy resolution once, retaining predecessors.
  No latest-writer-wins, automatic conflict resolution, truth copying on receipt,
  or belief withdrawal on missing evidence. Unknown prior initializes without
  invented discovery; rejecting a claim does not establish its opposite.
- [ ] E4: Hidden movement and delayed old reports do not refresh beliefs or
  reveal contents. Distinguish false-at-reference-time, evidenced change/outdated,
  and unresolved present applicability. No timestamp laundering or historical
  lie label. Wrong honest beliefs and source-dependent uncertainty stay possible.
- [ ] E5: Repeated reports from one source are not independent corroboration;
  reinspection at a new time is a new sample, not a new independent source.
  Preserve bounded receipts through replay, without duplicate revision.
- [ ] E6 / D06: Pin all five corrections: Observatory observation retains valid
  six-o'clock belief and initializes current belief; Harbor no-fresh-report retains
  Pavel's dated belief while explicit freshness policy defers clearance; occluded
  Harbor diagnostic retains Ivo's prior diagnosis; Library ledger needs declared
  current booking authority; Observatory exposure IDs need declared source and
  identity rule, not merely matching strings. Reading inscription is not truth.
- [ ] E7: Compare correction/direct-percept orders using explicit resolution;
  revision remains possible with corrective action disabled, and does not repair
  physical problems. Reader QA cites actual evidence/time, not hidden truth.

## Slice 3: requests, promises and refusals

- [ ] S1 / D08: Single-addressee delivered requests have exact action/terms/version
  and one owning response lifecycle. Acknowledgment stays pending; one authorized
  acceptance/decline is atomic and duplicates emit nothing. Wrong addressee,
  undelivered interaction, stale version or unauthorized proxy cannot respond.
  Typed loan-offer and return-offer adapters retain their own response owners;
  Refusing validates decision/reason, not an independent response write.
- [ ] S2: Acceptance does not move anything, create authority, fulfill work or
  silently promise. Match request completion to exact actual performance after
  acceptance; rejected booking candidates are not attempted failures. An enacted
  bounded booking/fitting/diagnostic check supplies evidence for narrated failure.
- [ ] S3 / D08: Requester withdrawal preserves earlier acceptance and ends mandate/
  completion eligibility, not independent physical ability or linked promise.
  Initial decline after acceptance is invalid. Harbor's "Bring the caliper back
  here" is a separate accepted request with its own performance link if rendered.
- [ ] S4 / D09: Explicit understood undertakings (requested or unsolicited) have
  separate identities from requests and loan obligations. Optional loan-linked
  promise adds no duplicate debt/discharge. Match exact post-creation actor,
  operation, item/result, recipient, terms/version and time receipts; intention,
  consent, claims, pre-creation/wrong receipts and archived-for-live delivery fail.
- [ ] S5 / D10: Finite checkpoint ordering distinguishes `strict_before` from
  `inclusive_by`, closes each interval before assessment, and prevents backdating.
  Exact-boundary performance differs. Library wording is "by five"; Harbor is
  "before the eight-o'clock bell." Complete simulated interval coverage is
  required to prove nonperformance; missing rendered prose or trace gaps cannot.
- [ ] S6 / D09-D10: Test on-time fulfillment, breach, authorized release before
  assessment and late repair. Release is not fulfillment; inability/apology/new
  request/refusal does not release; late repair never erases breach. Change terms
  by explicit release plus linked new undertaking: O0 stays released, only O0-v2
  can match the chart. Preserve any earlier breach and original terms/history.
- [ ] S7: Competing promises can both be physically selectable before resource
  consumption; choice can break one. Separate inability, lack/unknown authority
  and unwillingness with supported reasons; ability plus authority cannot force
  assent. QA explains priority only from rendered motive, not guard provenance.

## Three transfer fixtures, not 27 bespoke programs

Bind the same operations/contracts to three integrated worlds. Keep G4/H below
out of implementation demos. Retain proposal interventions as regression inputs;
map their approved semantic classes to shared parameterized tests, marking any
deferred extension explicitly rather than quietly dropping it.

| Fixture | Required distinct structures and contrasts | Evidence needed |
| --- | --- | --- |
| Neighborhood library | Contained-book recovery/bench placement; delayed assent and booking conflict; authoritative dated ledger correction; timely handover versus preference-based refusal. | P1-P6, E1-E7, S1-S7 bindings; successful and blocked/unresolved branches; rendered ownership/location/booking QA. |
| Harbor workshop | Hand-capacity/route constraint; restricted dry-bench grant and refused return; delayed accurate report; occluded diagnostic; accepted-but-blocked work, strict deadline and separate return request. | Same contracts with capacity/grant/visibility/freshness/checkpoint interventions; no repair inferred from revised diagnosis. |
| Mountain observatory | Accepted-uncollected detector; resource/time sacrifice; authorized latched deposit; old recording/current observation; shared-source exposure uncertainty; live-only substitute and competing promises. | Same contracts with window/latch/source-identity/resource/terms interventions; inclusive/strict boundary comparison and O0/O0-v2 history. |

- [ ] T1: Bind all three without title checks or per-story mechanics; include
  role/prop renaming and reason changes holding props fixed. Demonstrate causal
  differences after stripping names, not paraphrases or independent reorderings.
- [ ] T2: Run [G1-G3](../INTEGRATION_GATES.md) as integrated gates: G1 consent,
  custody, declined return, authorized deposit plus missing grant/wrong loan/
  claim-only delivery; G2 nested hidden movement, delayed report and explicit
  later evidence plus closed container/no second observation/reference-time
  changes; G3 competing choice, breach and new-request refusal plus action-only,
  promise-only and post-breach request variants. Require replay and reader QA.

## Required named falsifiers and evidence map

P-F/E-F/S-F numbers correspond exactly to each review's numbered falsifying tests;
G1-G3 are T2 and G4 is H. Every row needs a concrete test/artifact link under the
evidence contract, not a citation to implementation code as proof.

| Falsifier | Required assertions/interventions and evidence |
| --- | --- |
| P-F1 Receive-only / delayed settlement | P3/P5: Sol receives A2 once; A2 remains active, A1 untouched. Without authority/policy no settlement. In these slices later settlement is explicitly unsupported, with no extra handover or placement change. Positive later-authorized settlement referencing that same receipt is deferred (D03), not passed. |
| P-F2 Bench / cabinet source | P1/P4: tote/book path ends at bench, holder absent, Ada remains borrower, debt active; authorized cabinet collection activates without fabricated actor source. Show paths, role state and receipt. |
| P-F3 Stale readiness / revoked grant | P2/P6: fill Jo's hand after readiness; separately revoke lender grant before activation. Each joint performance rejects with no partial writes, receipt, or fictional attempt prose. |
| P-F4 Claim is not performance/authority/access | P4-P5/E4: accept delivery claim without receipt, outdated authority claim, and move observed closed container. No activation/discharge/new grant/content revelation/belief refresh. Compare belief and world separately. |
| P-F5 Latched deposit / replay | P5/X1/X5: authorized deposit settles only with required latch capability; removing it prevents joint settlement. Retained replay includes access, grant and path dependencies; frozen legacy interpretation unchanged. |
| E-F1 Evidence order / unknown prior | E3/E7: correction then percept and reverse order yield one explicit resolution/update, predecessor retention and no overwrite race; unknown prior initializes, never claims discovery. Compare histories, not just final value. |
| E-F2 Wrong/dated inscription / old report | E2/E4/E6/X6: inscription acquired without truth absent policy; old accurate report after hidden move retains reference time, not current refresh or lie. Mask historical support and suppress historical-truth QA. |
| E-F3 Failed/partial versus negative inspection | E1/E3/E6: obscured shelf/indicator yields bounded failed/partial evidence, prior diagnosis retained, no opposite/global absence. Complete visible coverage supports exact absence; unknown cannot pass false/zero checks. |
| E-F4 Inspection promise is not inspection | P1/E1/S2/S4: move closed container, request and promise inspection, but perform none: no content belief or fulfilled commitment. Later actual accessible inspection has event-time path witness and separate matching receipt. |
| E-F5 Repeat / reinspection / masked support | E5/X5-X6/H: repeated warning retains one source; unchanged-signal reinspection retains distinct sample times. Replay preserves meaningful events without corroboration/duplicate revision. Remove reply/motive support: linked QA abstains. |
| S-F1 Accepted request / withdrawal | S1-S3: reject initial decline after acceptance; requester withdrawal preserves acceptance and linked promise, permits independent movement but no withdrawn-request completion. Duplicate response emits nothing. |
| S-F2 Deadline / release / false performance | S4-S6: exact eight qualifies only under inclusive-by, not strict-before. Valid pre-assessment release avoids breach, not fulfills. Completion claim/wrong receipt cannot fulfill; late repair preserves breach. Show interval coverage/order. |
| S-F3 Typed declined return / separate offer | P3/P5/S1/X4/X6: first pending offer declined with custody/debt unchanged; separately identified accepted/performed offer settles once using one receipt. Rejected candidates emit no refusal/attempt; mask support and abstain. |

## HOLDOUT H: G4, repeated warning and an unperformed certification

Frozen acceptance case, not an implementation demo or a blind/secret case.
Use common operations only; no dependency on Python classes, storage or matcher
names. Do not weaken expected outcomes to accommodate implementation behavior.

**Premise/sequence.** At a harbor bench a sealed instrument is physically
reachable. Inspector A can see its external indicator but not its internal seal.
A bounded, actually performed inspection returns partial evidence: the visible
indicator alone cannot certify internal safety. A sends B a warning describing
exactly that limitation; B receives and understands it. B asks A to certify the
internal seal safe now. A actually declines that exact request, explicitly because
the seal has not been inspected. A repeats the warning once to emphasize the
still-unresolved limit. Also consider an inaccessible inspection candidate that
is rejected during search. No internal inspection, opening, repair or physical
transfer occurs. End unresolved; do not force certification or a happy ending.

**Frozen assertions.** Physics/ownership/loan state is unchanged. The enacted
partial inspection, two bounded utterances/receipts from the same source, delivered
request and one linked decline are distinct stable events. Internal safety remains
unknown, not false or accepted as true; repeated speech adds no independent
corroboration. Rejected candidate produces no story event. Decline supplies no
promise, inspection performance or repair. Pruned replay retains the partial
evidence, request/reply and stated reason used by prose/QA, but need not keep unused
search candidates. No artificial state flag exists solely to permit repetition.

**Frozen interventions (paired with the baseline).**

1. Remove the enacted reply: request remains pending, with no inferred decline,
   reason or guessed reply target. Do not turn search rejection into the reply.
2. Suppress the second warning: remove exactly that utterance/receipt; neither
   source independence, safety belief nor request disposition changes. Repeating
   it beyond the declared finite budget cannot loop or add corroboration.
3. Keep trace fixed but mask all prose establishing the decline's reason; "Why
   did A decline?" must omit/abstain. Separately mask all reply-target support;
   "Which request did A decline?" must omit/abstain rather than use hidden IDs.
4. Provide a genuinely accessible internal inspection in a separate branch:
   safety evidence may now support a fresh decision, but does not rewrite the
   earlier partial result/decline, create automatic assent or invent performance.

**Required H evidence.** Full/retained replay; event counts and identities; partial
versus unknown assertions; source lineage; finite-budget termination; selected
prose and baseline QA (what was checked, what remained unknown, which request was
declined and why); focused follow-ups and both masking outputs. Independently
inspect wording against the rendered evidence. H checks X3-X6, E1/E3/E5,
S1-S2/S7, E-F5 and G4; it does not replace the other family falsifiers.

## Deliberately deferred (not acceptance claims)

- Delayed loan settlement policy and its positive later-authorized branch of
  P-F1; until implemented, receive-only receipt leaves debt active and later
  settlement is unsupported. Future policy must reference the original receipt,
  validate current authority, change only settlement, never backdate a grant.
- Recursive delegation, competing/title adjudication, onward/subloans, partial
  quantities, compensation/damage claims, recall and cross-loan debt aggregation;
  joint lifting, carts/vehicles, continuous travel and inferred physics.
- General contracts/temporal logic, negotiation trees, responder abandonment,
  general amendment/renegotiation, delegated/conditional vows, partial credit and
  sanctions. Release-plus-new-undertaking and requester withdrawal are NOT deferred.
- Probabilistic perception/trust/persuasion, group audiences, arbitrary propositions,
  confidence arithmetic, general diagnosis, deception inference, automatic
  reputation/forgetting and unbounded inference. Narrow authored authority/source
  rules, explicit dispositions and bounded delayed messages are NOT deferred.
- Unrestricted unchanged speech/repeated refusals, 27 bespoke simulators, wholesale
  legacy migration, and paid literary/QA evaluation without separate approval.
  Bounded meaningful event-only speech/attempts and masked-support QA are required.
