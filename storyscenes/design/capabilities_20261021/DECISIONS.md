# Shared design decisions

Status: nine drafts and three cross-reviews reconciled. Decisions here are design recommendations,
not approval to implement or claims of validated behavior.

## Baseline constraints

- C00: Existing worlds and their ownership/knowledge semantics remain unchanged.
- C01: New semantics must separate truth, beliefs, and reader-visible evidence.
- C02: Ownership, custody, and location must not be conflated.
- C03: Requests, promises, and outcomes must not be conflated.
- C04: Each state change has one responsible operation, even in a composed scene.
- C05: New behavior executes offline, with inspectable effects and provenance.
- C06: Meaningful failure, refusal, and breached obligations are valid narrative
  outcomes; they must not be excluded merely to reach a happy-ending goal.

## Reconciliation log

### R01: Physical handover and loan lifecycle

Sources: `carrying-01`, `lending-01`, `returning-01`, `returning-02` in messages/.
Proposed common boundary: carrying owns physical receipt/placement; lending owns
loan activation; returning owns discharge of one identified loan. Compose these
as a checked atomic operation when both effects are intended. Ownership remains
separate. Authority to receive an object is not automatically authority to settle
its loan. Cross-review must check refusal, wrong recipient, and deposit-site cases.

### R02: Evidence, claims, and revision

Sources: `observing-01`, `observing-03`, `informing-01`, `informing-02`,
`discovering_mistake-01`, `discovering_mistake-03` in messages/.
Proposed common boundary: acquisition, communication, receipt, acceptance and
revision are explicit distinguishable steps. Preserve old evidence/beliefs and
reference time. A changed world does not make a previously accurate observation
false at its original time. Cross-review must assign one owner to belief writes
and avoid double-updating the same belief during observation and discovery.

### R03: Actions, acceptance, and explanations

Sources: `lending-02`, `carrying-03`, `informing-03`, `returning-03`,
`discovering_mistake-02` in messages/.
Proposed common boundary: accepting a request/offer does not move an object,
create an unspoken promise, repair an error, or establish a claim's truth.
Physical inability, lack of authority, and unwillingness are distinct. Guard
dependencies are not motives. Waiting for the social-capability proposals.

### R04: Narrative visibility

Sources: `observing-03`, `discovering_mistake-03`, `lending-03` in messages/.
Proposed common boundary: timed evidence and explicit response/loan IDs persist
through rendering and follow-up QA. Hidden facts remain available for simulator
diagnostics, not for story-only comprehension answers. English entailment still
requires review; annotations alone are not a proof.

All four entries are coordinator proposals for review, not claims of unanimous
agreement. Native messages relayed this summary to the six active workers; the
remaining workers will receive it in their launch briefing.

## Coordinator dispositions

These refine the initial proposals. They are recommendations for the user's next
approval, not implemented behavior. Original proposals remain intact so conflicts
and their resolution stay auditable.

### D01: One version boundary, not nine runtimes

Adopt one opt-in capability-world schema/compiler boundary with named operation
contracts. Worker names such as `physical_v1`, `lending_v2`, and `communication_v2`
are conceptual draft labels, not a plan for independent state models. Legacy
builders and frozen fixtures retain their exact meaning. Use typed records;
do not encode nested records as opaque JSON in scalar strings.

### D02: Physical holder is not borrower, keeper, or owner

Accept the physical review's findings 2 and 3. Carrying owns an acyclic physical
parent relation and derived effective place/physical-holder queries. The source
of a pickup can be a shelf or container, not an invented actor custodian.
Borrower responsibility, permission to release an object, and legal ownership
are separate domain records. Kit can manage the observatory cabinet without
physically holding its detector. A book left on a bench still has a borrower.
Call the derived actor relation `physical_holder` in the common contract to
avoid implying institution-level custody or responsibility.

### D03: One receipt, explicit settlement

Accept physical review finding 1. Physical performance emits one immutable
receipt with operation, object, source/destination, participants and time. An
authorized immediate return may atomically combine that receipt with loan
discharge. A later settlement must reference the existing receipt, validate
current settlement authority and an explicit policy, and write only the loan's
settlement record. It cannot replay a handover or backdate authorization.

Keep delayed settlement as an explicit conformance case, but defer its policy
implementation until the immediate-return slice is working. Until then a
receive-only handoff leaves the loan active; later settlement is unsupported,
not silently successful. The returning Library intervention describes the later
extension. Inspect the receipt's object and loan identity, not just its recipient.

### D04: Joint validation, distinct kinds of acceptance

Accept physical review findings 3-5. Validate the combined physical and social
reads against one pre-state, then commit all effects or none. Receipt readiness
is bound to the actual giver/recipient/object operation; agreement consent is
bound to terms/version; return-offer acceptance is bound to offer/loan. Neither
is belief acceptance. Recheck current location, capacity, authority and terms
at performance. Cabinet latching is an explicit domain effect/postcondition, not
an invented side effect of generic Put.

Do not implement unrestricted delegation or legal adjudication. Initially use
predeclared scoped grants and terms, one object/active loan, single-person
transport and bounded locations/containers. The physical review's five tests
are proposed falsifiers, not a declaration that all five are supported in slice 1.

### D05: One belief writer; explicit decisions

Accept epistemic review findings 1, 3 and 4. Observation and communication own
evidence/receipts. Acquisition, adoption and discrepancy resolution propose
belief dispositions with basis and policy IDs. One shared validated update
operation commits the belief head and retains its predecessor exactly once.
Receiving a claim or failing to obtain evidence does not silently change a belief.
No latest-writer-wins or implicit trust-score rule. Wrong beliefs remain possible.

Propositions carry reference time/scope; records also carry acquisition/delivery
time and distinguish attributed from verified provenance. An old report is not
automatically false. Unsupported present applicability is not proof that the
world changed. Reading an inscription first establishes what the inscription
says; accepting its factual assertion needs a narrow authored authority policy.

### D06: Explicit corrections to the first-pass epistemic stories

These design corrections supersede the indicated draft beats/interventions;
original proposals are retained for audit, not silently treated as error-free.

- Observing / Observatory, beat 5: keep the valid six-o'clock belief. The fresh
  view initializes a distinct current belief; do not invent a prior present-use
  belief solely to produce a mistake-discovery event.
- Informing / Harbor, no-fresh-report intervention: retain Pavel's dated prior
  belief while deferring current clearance under an explicit freshness policy.
  Do not claim he became uncertain without a recorded belief disposition.
- Discovering mistake / Harbor, occluded-indicator intervention: preserve Ivo's
  prior diagnosis; the failed check supplies no decisive revision. He can defer
  action pending evidence without automatically withdrawing that diagnosis.
- Discovering mistake / Library: declare the shown current ledger authoritative
  for booking assignments. Reading its rows alone does not prove their truth.
- Discovering mistake / Observatory: declare the exposure-ID source and its
  identity rule. Matching readable strings alone is insufficient evidence that
  two files actually derive from the same exposure.

The epistemic review's five falsifiers are required design cases. They include
evidence-order variation, failed inspection, dated/false source documents, and
masked reader support. None is reported as an executed test.

### D07: Events, choices, and narrative retention

An illegal search candidate is not an enacted attempt. A meaningful attempt,
utterance, receipt or inspection may leave physical state unchanged; represent
its actual event/evidence or social disposition with finite usage bounds, not a
dummy flag. Reinspection at a new time is a new sample, not an independent source.
Repeated delivery is not repeated corroboration. Duplicate settlement/revision
must remain idempotent.

Intentional action proposals depend on the actor's accessible beliefs and goals;
physical effects/results are checked against world state. Observationally
equivalent hidden states must offer the same intentional checks. This does not
claim the current omniscient author-side search already implements an agent policy.

Pruning/replay must retain the actual evidence, response and motive dependencies
used by selected narrative turns and QA. Do not mark every event pivotal or retain
all unused events to inflate the number of questions. QA additionally needs
reader-visible support; annotations alone do not prove English entailment.

### D08: Responses belong to the interaction owner

Accept social review findings 1 and 5 and messages requesting-01, promising-01,
refusing-01. Requesting owns a request's response state. Refusing validates the
decline/reason and delegates the actual response transition to the interaction
owner. A loan offer or return offer has its own typed lifecycle adapter; not all
offers are silently converted into requests. Every response binds an exact ID
and terms version, with one responsible writer and one atomic decision record.

Initially support requester-initiated withdrawal. Preserve earlier acceptance;
do not rewrite it as decline. Withdrawal ends the request mandate/completion
eligibility, not physical ability to act independently. It does not cancel a
promise. Responder abandonment/reconsideration is a deferred extension.

Story correction: Requesting / Harbor's "Bring the caliper back here" is a new
request, not part of withdrawing the outbound request. Give that request an
explicit acceptance and performance link, or omit the imperative and describe
Jules' independently chosen authorized transport. Use the first option when
implementing the outlined dialogue, which keeps the quoted exchange intact.

### D09: Commitment replacement preserves history

Accept social review finding 3 and promising-02. Requests, loan obligations and
explicit promises have distinct identities/lifecycles. An optional promise may
reference a loan but cannot duplicate its debt or discharge. Exact post-creation
domain receipts establish promise performance; intention/claims do not.

For the initial slice, change commitment terms by releasing the active old
undertaking and explicitly creating a linked new undertaking, not by mutating
the old terms. Refusing / Observatory's amendment intervention therefore releases
O0 and creates O0-v2 permitting the chart. Only O0-v2 may be fulfilled by that
delivery; O0 remains released. Earlier breaches are never erased. General
amendment/renegotiation policy is deferred.

### D10: Deadline terms are explicit

Accept social review finding 4. Finite terms distinguish
`strict_before(checkpoint)` from `inclusive_by(checkpoint)`. Narrative wording,
QA, and matching performance must use the same interpretation. Deterministic
event/checkpoint ordering closes the permitted performance interval before its
assessment; later events cannot be backdated into it. Absence checks require
complete simulated interval coverage, not absence of a rendered paragraph.

Story corrections: Promising / Library uses inclusive "by five" consistently;
Promising / Harbor retains strict "before the eight-o'clock bell." A performance
exactly at the checkpoint must produce different results for these two terms.
Replace the draft's universal inclusive-boundary test with both cases. A valid
release before assessment is not fulfillment; later repair does not erase breach.

### D11: A rejected booking is not a performed failure

Accept social review finding 2. Requesting / Library's occupied-slot intervention
may end with acceptance but no completed booking. To narrate an attempted booking
and observed conflict, add a real bounded check/attempt event. An unselected or
guard-rejected candidate alone supplies no speech, motive, or failure evidence.

## Remaining implementation choices

The semantic distinctions above are reconciled recommendations. Exact Python
record layouts, serialization/compiler integration, event-aware pruning, matcher
registry signatures, and reader-support realization remain implementation work.
They are not settled merely because the proposed fields have names. Approve and
build a small vertical slice before expanding to all 27 outlines.

Deferred deliberately: delayed settlement policy, recursive authority chains,
generalized contracts/temporal logic, probabilistic trust/perception, joint
lifting/vehicles, responder abandonment, and unrestricted repeated no-change
speech. Retain their boundary cases in the design corpus without claiming support.
