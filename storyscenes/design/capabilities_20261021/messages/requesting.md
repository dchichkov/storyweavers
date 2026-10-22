# Requesting interface proposals

First-pass design only. Coordinator relay and cross-review remain pending; no
implementation or peer agreement is implied.

## requesting-01
- Recipient: promising, refusing, coordinator.
- Issue: A directed request, its acceptance, a future commitment, and performance need independently inspectable meanings.
- Proposed resolution: A versioned request has immutable requester/addressee/action terms and a response state pending/accepted/declined (plus explicit expiry/withdrawal). Acceptance records agreement to undertake that request, not a promise or completion. Promising alone creates commitments. Refusing supplies a decline proposal referencing request ID/version and grounded reason evidence; requesting owns the single response-state write. Performance is a separate linked domain event, checked against exact action terms.
- Affected stories/contracts: All three requesting outlines; response and commitment interfaces.
- First-pass response: Explicitly agree with refusing-01 and promising-01 after coordinator relay and reading their messages. Refusing supplies the decision/reason; Requesting alone changes response state. Promising alone creates and settles commitments. Speech-act annotations must agree with rendered wording; an ambiguous "I'll..." is not automatic commitment evidence.
- Status: proposed.

## requesting-02
- Recipient: lending, returning, carrying, informing, coordinator.
- Issue: Asking an actor to do something neither grants authority nor proves a communicated authority claim.
- Proposed resolution: Requests reference a bounded action specification and optional scoped authority evidence; domain operations validate authority at performance time. Carrying owns physical movement, lending owns agreement/activation, returning owns discharge, and informing owns claims/receipt/belief acceptance. A request to receive a return is not authorization to discharge its loan. Hearing a request is not accepting it.
- Affected stories/contracts: Library reservation workflow; harbor tool delivery; observatory observation request. Aligns provisionally with lending-02, returning-03, carrying-03, informing-03, and discovering_mistake-02.
- Status: proposed.

## requesting-03
- Recipient: refusing, promising, observing, coordinator.
- Issue: Existing runtime.transition rejects unchanged state; actual refusals/attempts must remain distinct from rejected search candidates and survive evidence pruning.
- Proposed resolution: Pending-to-declined is meaningful state, not a bypass flag. Successful actions emit their own effects. A deliberate failed attempt requires a bounded opt-in event record with actor, exact target, observed outcome, and evidence; a failed guard alone emits nothing. Request/response utterances, reason references, and performance links must be retained together for reader-grounded QA. Defer repeated no-change speech until a shared event-only contract exists.
- Affected stories/contracts: Harbor accepted-but-blocked request; observatory declined original and accepted replacement; all causal follow-ups.
- Status: unresolved.
