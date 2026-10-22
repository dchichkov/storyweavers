# Social Cross-Review

Design review only; no tests executed. D01-D07 already settle the shared version
boundary, joint validation, receipt identity, belief writer and enacted-event
principles. Keep those decisions; the issues below concern their social adapters.

## Findings and Minimal Fixes

**1. Single response ownership agrees; post-acceptance authority is incomplete.**
All three contracts correctly give Requesting sole ownership of
`pending -> accepted | declined`; Refusing contributes a validated decision and
reason atomically. However, Refusing's contract mentions a
"withdrawal/reconsideration" operation for accepted requests without defining
who can invoke it. Requesting/Harbor beat 6 demonstrates requester withdrawal,
not responder reconsideration. Define requester withdrawal explicitly; defer
responder abandonment or give it a separate bounded disposition preserving
acceptance. Neither may retroactively decline the request or release a promise.
Requesting's "Withdrawals stop further requested work" must mean ending the
request's mandate/completion eligibility, not physically prohibiting independent
work. Its Harbor exchange also adds "Bring the caliper back here": annotate that
as a separate request if operative, or clearly retain the independently authorized
movement in beat 7 without implying automatic acceptance.

**2. Actual refusal is sound; one intervention risks narrating search failure.**
Refusing/Observatory beat 2 correctly uses an executed diagnostic, and
Promising/Harbor beat 2 requires an actual fitting-test receipt. Preserve these
under D07. Requesting/Library's occupied-slot intervention says the booking
"fails." A rejected booking candidate supports only unresolved completion,
not an attempted booking, refusal or spoken explanation. Minimal fix: retain
the unresolved ending, or require an enacted bounded booking attempt/check with
an observed conflict before narrating failure. No dummy failure flags.

**3. Promise identity is consistent; amendment identity is not.**
Requesting/Library beats 5-6 separate acceptance from booking; Promising/Library
beat 2 explicitly composes acceptance and promise. Preserve executable act IDs
and matching speech; Pavel's "I'll use another chest" remains intention.
Refusing/Observatory's amendment intervention says a chart may fulfill amended
O0. Promising instead requires release plus a new versioned undertaking. Choose
that smaller existing rule: release O0, create linked O0-v2 permitting the chart,
then match its receipt. Original O0 is released, not fulfilled. Refusing O1,
reporting inability, or accepting O2 releases neither promise. Match performance
by actor, operation, exact item/result, version and time; archived information
cannot satisfy live-only terms. D03 also prevents replaying physical performance
for settlement.

**4. Deadline wording contradicts universal inclusive assessment.**
Promising/Harbor promises "before the eight-o'clock bell," but its acceptance
test allows a receipt at the deadline. Library mixes a "before five" premise
with "by five" undertaking; its 16:59 example conceals the boundary difference.
Use explicit finite terms `strict_before(checkpoint)` versus
`inclusive_by(checkpoint)`, with aligned prose and QA. Define same-time ordering
once; do not silently normalize "before" into "by." Release before assessment
avoids breach; later performance preserves a recorded breach. Inability affects
explanation, not deadline semantics or automatic excuse.

**5. Loan/return adapters need one response owner per interaction type.**
Refusing's composition section acknowledges return offers but supplies no adapter.
Requesting/Harbor acceptance authorizes neither loan activation nor settlement;
Refusing/Harbor's H1 decline must create no accepted loan agreement. Under
D03-D04, bind decline decisions to typed request, loan-offer or return-offer IDs;
their lifecycle owner commits the disposition. Requesting owns request responses,
not every offer ledger. Consent/readiness, physical receipt and settlement stay
distinct; accepting a request to receive cannot discharge a loan.

## Three Falsifying Tests

1. Accept a request, then submit initial decline, withdraw it, and perform
   independently. Preserve acceptance; reject decline; record withdrawal without
   blocking physics or erasing a linked promise. Duplicate responses emit nothing.
2. Perform exactly at eight under strict-before and inclusive-by terms: require
   different settlement. Release before assessment prevents breach; a completion
   claim, wrong receipt or later repair cannot counterfeit timely fulfillment.
3. Decline a pending return offer using the adapter, then accept and perform a
   separate correctly identified offer. First decline changes no custody/loan;
   second settlement uses one receipt once. Rejected candidates produce no
   refusal/attempt; masked reader support forces QA abstention.

## Outstanding Decisions

Withdrawal authority and deferred responder abandonment; typed offer-response
adapters; release/new-version amendment naming; strict/inclusive checkpoint
ordering; action-receipt matching and interval-coverage certification. Implement
these only within D01's shared boundary, not separate capability runtimes.
