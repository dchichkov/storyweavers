"""Finite requests, explicit undertakings, and attributed refusal decisions.

Nothing here grants physical authority or treats speech as performance. Physical
receipts are checked against their producing event; the small booking extension
does the same for nonphysical work. Deadline assessment requires a closed clock
interval, not merely an absence of selected narrative events.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from .core import CapabilityError, Record


PHYSICAL_OPERATIONS = frozenset({
    "pickup", "put", "travel", "handoff", "activate_loan",
    "complete_return", "authorized_deposit",
})
DEADLINES = frozenset({"strict_before", "inclusive_by"})
RECEIPT_TABLES = ("receipts", "domain_receipts", "evidence")


@dataclass(frozen=True, kw_only=True)
class ActionSpec(Record):
    operation: str
    actor: str
    terms: str
    version: int
    checkpoint: int
    deadline: str = "inclusive_by"
    object: str | None = None
    destination: str | None = None
    result: str | None = None
    source: str | None = None
    recipient: str | None = None
    loan_id: str | None = None
    loan_version: int | None = None
    inspection_fact: str | None = None
    result_value: str | bool | int | float | None = None
    reference_start: int | None = None
    reference_end: int | None = None
    coverage: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class Request(Record):
    requester: str
    responder: str
    action_spec: str
    version: int
    created_event: str
    created_tick: int
    delivery_event: str | None = None
    understood_event: str | None = None
    response: str = "pending"
    response_event: str | None = None
    withdrawal_event: str | None = None
    completion_receipt: str | None = None
    completion_table: str | None = None


@dataclass(frozen=True, kw_only=True)
class Promise(Record):
    promisor: str
    beneficiary: str
    action_spec: str
    version: int
    created_event: str
    created_tick: int
    request: str | None = None
    loan_id: str | None = None
    replaces: str | None = None
    status: str = "active"
    assessment_event: str | None = None
    performance_receipt: str | None = None
    performance_table: str | None = None
    release_event: str | None = None
    repair_receipt: str | None = None
    repair_table: str | None = None


@dataclass(frozen=True, kw_only=True)
class RefusalDecision(Record):
    interaction: str
    target: str
    version: int
    actor: str
    audience: str
    reason_kind: str
    attributed_reason: str
    support: tuple[str, ...]
    event_id: str
    tick: int


@dataclass(frozen=True, kw_only=True)
class BookingSlot(Record):
    place: str
    version: int = 1
    booked_by: str | None = None


@dataclass(frozen=True, kw_only=True)
class DomainReceipt(Record):
    """Executed booking or availability inspection, never an arbitrary claim."""
    operation: str
    actor: str
    object: str
    destination: str
    result: str
    terms: str
    version: int
    event_id: str
    tick: int
    recipient: str | None = None
    loan_id: str | None = None


def _fresh(tx, table, key):
    tx.require(tx.maybe(table, key) is None, "Identity already exists")


def _spec(tx, key, version):
    spec = tx.get("action_specs", key)
    tx.require(spec.version == version, "Stale action terms/version")
    return spec


def _within(spec, tick):
    return tick < spec.checkpoint if spec.deadline == "strict_before" else tick <= spec.checkpoint


def _direct_speech(tx, speaker, audience):
    """This slice defines finite terms spoken in person as understandable speech.

    It does not infer understanding of arbitrary text or support remote channels.
    """
    from .physical import location
    tx.entity(speaker, "actor")
    tx.entity(audience, "actor")
    tx.require(location(tx, speaker) == location(tx, audience), "Direct speech is out of reach")


def _local_slot(tx, row):
    from .physical import location
    tx.entity(row.place, "place")
    tx.require(location(tx, tx.action.actor) == row.place, "Booking ledger is not locally accessible")


def create_request(tx, *, request, responder, action_spec, version):
    _fresh(tx, "requests", request)
    tx.entity(responder, "actor")
    spec = _spec(tx, action_spec, version)
    tx.require(spec.actor == responder and _within(spec, tx.tick), "Invalid request performer/interval")
    tx.put("requests", Request(id=request, requester=tx.action.actor,
           responder=responder, action_spec=spec.id, version=version,
           created_event=tx.event_id, created_tick=tx.tick))
    tx.emit(kind="request_created", request=request, audience=responder, action_spec=spec.id)


def deliver_request(tx, *, request, version):
    req = tx.get("requests", request)
    spec = _spec(tx, req.action_spec, version)
    tx.require(tx.action.actor == req.requester and req.version == version,
               "Only requester may deliver exact request")
    tx.require(req.delivery_event is None and req.withdrawal_event is None and _within(spec, tx.tick),
               "Request cannot be delivered")
    _direct_speech(tx, req.requester, req.responder)
    tx.put("requests", replace(req, delivery_event=tx.event_id, understood_event=tx.event_id))
    tx.emit(kind="request_delivered", request=request, audience=req.responder, version=version,
            understood_by=req.responder, mode="direct_finite_terms")


def _pending_request(tx, request, version):
    req = tx.get("requests", request)
    spec = _spec(tx, req.action_spec, version)
    tx.require(req.version == version and req.responder == tx.action.actor,
               "Wrong request responder/version")
    tx.require(req.delivery_event is not None and req.understood_event is not None and req.response == "pending"
               and req.withdrawal_event is None and _within(spec, tx.tick),
               "Only delivered open pending requests may be answered")
    tx.depend(req.delivery_event)
    _direct_speech(tx, req.responder, req.requester)
    return req


def acknowledge_request(tx, *, request, version):
    req = _pending_request(tx, request, version)
    tx.emit(kind="request_acknowledged", request=request, audience=req.requester, version=version)


def respond_request(tx, *, request, version, decision, decision_id=None, reason_kind=None):
    """Requesting's sole response writer; also used by the refusal adapter."""
    req = _pending_request(tx, request, version)
    tx.require(decision in {"accepted", "declined"}, "Unknown response decision")
    if decision == "declined":
        _refusal(tx, interaction="request", target=request, version=version,
                 audience=req.requester, decision_id=decision_id, reason_kind=reason_kind)
    tx.put("requests", replace(req, response=decision, response_event=tx.event_id))
    tx.emit(kind="request_response", request=request, decision=decision,
            audience=req.requester, version=version,
            refusal=decision_id or tx.event_id if decision == "declined" else None)


def withdraw_request(tx, *, request, version):
    req = tx.get("requests", request)
    _spec(tx, req.action_spec, version)
    tx.require(req.requester == tx.action.actor and req.version == version,
               "Only requester may withdraw exact request")
    tx.require(req.withdrawal_event is None and req.completion_receipt is None and req.response != "declined",
               "Request is already ended")
    _direct_speech(tx, req.requester, req.responder)
    tx.put("requests", replace(req, withdrawal_event=tx.event_id))
    tx.emit(kind="request_withdrawn", request=request, audience=req.responder,
            preserved_response=req.response)


def _receipt_tick(table, receipt):
    return receipt.acquired_at if table == "evidence" else receipt.tick


def _receipt_matches(tx, spec, table, receipt, after):
    """Exact mechanical matching, with provenance and actual event ordering.

    Physical and epistemic receipts have no contractual terms field: their exact
    effect is interpreted by the immutable versioned ActionSpec. Booking receipts
    additionally bind authored terms/version. A request, promise or claim is not
    a performance receipt provider.
    """
    if table not in RECEIPT_TABLES:
        return False
    if spec.inspection_fact is not None and table != "evidence":
        return False
    by_id = {e.id: e for e in tx.before.events}
    if receipt.event_id not in by_id or after not in by_id:
        return False
    event, anchor = by_id[receipt.event_id], by_id[after]
    events = tuple(e.id for e in tx.before.events)
    if events.index(event.id) <= events.index(anchor.id):
        return False
    if _receipt_tick(table, receipt) != event.tick:
        return False
    if not any(c.table == table and c.key == receipt.id and c.before is None
               and c.after == receipt for c in event.changes):
        return False
    if table == "evidence":
        if (spec.operation != "inspection" or event.action.operation != "observe"
                or receipt.outcome != "exact" or receipt.observer != spec.actor
                or receipt.observer != event.action.actor or spec.inspection_fact != receipt.fact
                or spec.object != receipt.source or not receipt.actor_path
                or spec.destination != receipt.actor_path[-1]):
            return False
        proposition = tx.get("propositions", receipt.proposition)
        if proposition.result.kind != "exact":
            return False
        if spec.result is not None and proposition.id != spec.result:
            return False
        if spec.result_value is not None and (type(proposition.result.value) is not type(spec.result_value)
                                             or proposition.result.value != spec.result_value):
            return False
        if spec.reference_start is not None and (proposition.reference_start, proposition.reference_end) != (
                spec.reference_start, spec.reference_end):
            return False
        if spec.coverage and set(receipt.coverage) != set(spec.coverage):
            return False
        tx.depend(event.id)
        tx.depend(anchor.id)
        return spec.loan_id is None
    if receipt.actor != event.action.actor or receipt.operation != spec.operation or receipt.actor != spec.actor:
        return False
    for name in ("object", "destination", "result", "source", "recipient"):
        expected = getattr(spec, name)
        if expected is not None and getattr(receipt, name, None) != expected:
            return False
    if getattr(receipt, "loan_id", None) != spec.loan_id:
        return False
    if table == "receipts":
        valid = spec.operation in PHYSICAL_OPERATIONS and event.action.operation == spec.operation
        if spec.loan_id is not None:
            loan = tx.get("loans", spec.loan_id)
            expected_version = spec.loan_version if spec.loan_version is not None else spec.version
            valid = valid and loan.version == expected_version
    else:
        valid = (receipt.terms == spec.terms and receipt.version == spec.version
                 and event.action.operation == {"booking": "perform_booking", "inspection": "check_booking"}.get(spec.operation))
    if valid:
        tx.depend(event.id)
        tx.depend(anchor.id)
    return valid


def _receipt(tx, table, key):
    tx.require(table in RECEIPT_TABLES and table in tx.registry.tables,
               "Not a performance receipt provider")
    return tx.get(table, key)


def complete_request(tx, *, request, version, receipt, table="receipts"):
    req = tx.get("requests", request)
    spec = _spec(tx, req.action_spec, version)
    tx.require(req.version == version and req.responder == tx.action.actor
               and req.response == "accepted" and req.withdrawal_event is None
               and req.completion_receipt is None, "Request is not completion eligible")
    actual = _receipt(tx, table, receipt)
    tx.require(_receipt_matches(tx, spec, table, actual, req.response_event)
               and _within(spec, _receipt_tick(table, actual)), "Receipt does not complete this accepted request")
    tx.put("requests", replace(req, completion_receipt=receipt, completion_table=table))
    tx.emit(kind="request_completed", request=request, receipt=receipt, receipt_table=table)


def make_promise(tx, *, promise, beneficiary, action_spec, version,
                 request=None, loan_id=None, replaces=None):
    _fresh(tx, "promises", promise)
    spec = _spec(tx, action_spec, version)
    tx.entity(beneficiary, "actor")
    _direct_speech(tx, tx.action.actor, beneficiary)
    tx.require(spec.actor == tx.action.actor and _within(spec, tx.tick),
               "Promise must name its speaker and an open finite interval")
    # A related loan is not the promised performance itself. In particular a
    # promise to activate a future loan can name that exact future receipt ID
    # in ActionSpec without pretending the loan already exists.
    tx.require(loan_id is None or spec.loan_id in {None, loan_id}, "Unrelated promise loan link")
    if request is not None:
        req = tx.get("requests", request)
        tx.require(req.action_spec == spec.id and req.version == version
                   and req.requester == beneficiary and req.responder == tx.action.actor
                   and req.understood_event is not None, "Unrelated request")
    if loan_id is not None:
        loan = tx.get("loans", loan_id)
        tx.require(loan is not None, "Unknown linked loan")
    if replaces is not None:
        old = tx.get("promises", replaces)
        tx.require(old.release_event is not None and old.promisor == tx.action.actor
                   and old.beneficiary == beneficiary and old.action_spec != spec.id
                   and version > old.version, "Replacement needs released earlier terms")
        tx.require(not any(p.replaces == replaces for p in tx.all("promises")),
                   "Undertaking already replaced")
        tx.depend(old.release_event)
    tx.put("promises", Promise(id=promise, promisor=tx.action.actor,
           beneficiary=beneficiary, action_spec=spec.id, version=version,
           created_event=tx.event_id, created_tick=tx.tick, request=request,
           loan_id=loan_id, replaces=replaces))
    tx.emit(kind="explicit_promise", promise=promise, audience=beneficiary,
            action_spec=spec.id, version=version, replaces=replaces,
            understood_by=beneficiary, mode="direct_finite_terms")


def release_promise(tx, *, promise, version):
    p = tx.get("promises", promise)
    _spec(tx, p.action_spec, version)
    tx.require(p.version == version and tx.action.actor == p.beneficiary
               and p.release_event is None and p.status in {"active", "breached"},
               "Only beneficiary may release an unreleased undertaking")
    _direct_speech(tx, p.beneficiary, p.promisor)
    tx.put("promises", replace(p, release_event=tx.event_id,
           status="released" if p.status == "active" else "breached"))
    tx.emit(kind="promise_released", promise=promise, preserved_breach=p.status == "breached")


def assess_promise(tx, *, promise, version):
    p = tx.get("promises", promise)
    spec = _spec(tx, p.action_spec, version)
    tx.require(p.version == version and tx.action.actor in {p.promisor, p.beneficiary}
               and p.status == "active" and p.assessment_event is None,
               "Undertaking is not assessable")
    # Clock movement closes every event at the deadline tick, including inclusive
    # performance. No same-tick assessor can preempt a later same-tick receipt.
    tx.require(tx.tick > spec.checkpoint, "Performance interval has not closed")
    found = []
    for table in RECEIPT_TABLES:
        if table not in tx.registry.tables:
            continue
        for receipt in tx.all(table):
            if _receipt_matches(tx, spec, table, receipt, p.created_event) and _within(spec, _receipt_tick(table, receipt)):
                found.append((_receipt_tick(table, receipt), receipt.event_id, table, receipt.id))
    order = {event.id: index for index, event in enumerate(tx.before.events)}
    selected = min(found, key=lambda item: order[item[1]]) if found else None
    tx.put("promises", replace(p, status="fulfilled" if selected else "breached",
           assessment_event=tx.event_id,
           performance_table=selected[2] if selected else None,
           performance_receipt=selected[3] if selected else None))
    tx.emit(kind="promise_assessed", promise=promise,
            outcome="fulfilled" if selected else "breached", checkpoint=spec.checkpoint,
            deadline=spec.deadline, receipt=selected[3] if selected else None)


def record_late_repair(tx, *, promise, version, receipt, table="receipts"):
    p = tx.get("promises", promise)
    spec = _spec(tx, p.action_spec, version)
    tx.require(p.version == version and tx.action.actor == p.promisor
               and p.status == "breached" and p.repair_receipt is None,
               "Only an unrepaired breach can receive late repair")
    actual = _receipt(tx, table, receipt)
    tx.require(_receipt_matches(tx, spec, table, actual, p.created_event)
               and not _within(spec, _receipt_tick(table, actual)), "Not a late exact performance")
    tx.put("promises", replace(p, repair_receipt=receipt, repair_table=table))
    tx.emit(kind="late_repair", promise=promise, receipt=receipt, preserved_breach=True)


def _refusal(tx, *, interaction, target, version, audience, decision_id, reason_kind):
    tx.require(reason_kind in {"inability", "unwillingness", "no_authority", "unknown_authority"}
               and isinstance(tx.action.reason, str) and bool(tx.action.reason.strip()),
               "Refusal needs an attributed reason and kind")
    key = decision_id or tx.event_id
    _fresh(tx, "refusals", key)
    for support in tx.action.reason_support:
        tx.depend(support)
    tx.put("refusals", RefusalDecision(id=key, interaction=interaction, target=target,
           version=version, actor=tx.action.actor, audience=audience,
           reason_kind=reason_kind, attributed_reason=tx.action.reason,
           support=tx.action.reason_support, event_id=tx.event_id, tick=tx.tick))


def refuse(tx, *, interaction, target, version, reason_kind, decision_id=None):
    if interaction == "request":
        return respond_request(tx, request=target, version=version, decision="declined",
                               decision_id=decision_id, reason_kind=reason_kind)
    tx.require(interaction in {"loan_offer", "return_offer"}, "Unknown interaction type")
    # The physical domain owns offer responses and their event payload. Import
    # lazily so registry construction order does not couple the domain modules.
    from .physical import respond_loan, respond_return
    table = "loan_offers" if interaction == "loan_offer" else "return_offers"
    offer = tx.get(table, target)
    audience = (tx.get("loan_terms", offer.terms).lender if interaction == "loan_offer"
                else tx.get("loans", offer.loan_id).borrower)
    _direct_speech(tx, tx.action.actor, audience)
    _refusal(tx, interaction=interaction, target=target, version=version,
             audience=audience, decision_id=decision_id, reason_kind=reason_kind)
    helper = respond_loan if interaction == "loan_offer" else respond_return
    helper(tx, offer=target, version=version, decision="declined")


def acknowledge_refusal(tx, *, refusal):
    decision = tx.get("refusals", refusal)
    tx.require(tx.action.actor in {decision.actor, decision.audience}, "Not a refusal participant")
    _direct_speech(tx, decision.actor, decision.audience)
    tx.depend(decision.event_id)
    tx.emit(kind="refusal_acknowledged", refusal=refusal, target=decision.target,
            audience=decision.audience if tx.action.actor == decision.actor else decision.actor,
            attributed_reason=decision.attributed_reason)


def perform_booking(tx, *, slot, version, terms):
    row = tx.get("booking_slots", slot)
    tx.require(row.version == version and row.booked_by is None, "Booking slot unavailable/version changed")
    _local_slot(tx, row)
    tx.require(isinstance(terms, str) and bool(terms), "Explicit booking terms required")
    tx.put("booking_slots", replace(row, booked_by=tx.action.actor))
    _domain_receipt(tx, row, "booking", "booked", terms, recipient=tx.action.actor)


def check_booking(tx, *, slot, version, terms):
    """A selected bounded inspection can observe conflict; a rejected booking cannot."""
    row = tx.get("booking_slots", slot)
    _local_slot(tx, row)
    tx.require(row.version == version and isinstance(terms, str) and bool(terms), "Invalid slot inspection")
    _domain_receipt(tx, row, "inspection", "occupied" if row.booked_by else "available", terms)


def _domain_receipt(tx, row, operation, result, terms, recipient=None):
    _fresh(tx, "domain_receipts", tx.event_id)
    tx.put("domain_receipts", DomainReceipt(id=tx.event_id, operation=operation,
           actor=tx.action.actor, object=row.id, destination=row.place, result=result,
           terms=terms, version=row.version, event_id=tx.event_id, tick=tx.tick,
           recipient=recipient))
    tx.emit(kind="domain_performance", operation=operation, object=row.id,
            result=result, receipt=tx.event_id, booked_by=row.booked_by)


def validate_initial(state):
    """Static terms/booking occupancy are premises; interactions must be enacted."""
    if any(state.tables[table] for table in ("requests", "promises", "refusals", "domain_receipts")):
        raise CapabilityError("Social interaction/receipt history must start empty")


def validate(state):
    def check(condition, message):
        if not condition:
            raise CapabilityError(message)

    def actor(key):
        e = state.get("entities", key)
        return e is not None and e.kind == "actor"

    for spec in state.tables["action_specs"].values():
        check(actor(spec.actor) and spec.operation in PHYSICAL_OPERATIONS | {"booking", "inspection"},
              "ActionSpec requires a supported operation and embedded actor")
        check(type(spec.version) is int and spec.version > 0 and type(spec.checkpoint) is int
              and spec.checkpoint >= 0 and spec.deadline in DEADLINES
              and isinstance(spec.terms, str) and bool(spec.terms.strip()),
              "Invalid finite action terms/deadline")
        check(spec.object is not None or spec.result is not None, "Exact object or result required")
        check(spec.destination is not None or spec.result is not None, "Exact destination or result required")
        check((spec.reference_start is None and spec.reference_end is None) or
              (type(spec.reference_start) is int and type(spec.reference_end) is int
               and 0 <= spec.reference_start <= spec.reference_end), "Invalid inspection reference interval")
        check(not spec.inspection_fact or (spec.operation == "inspection"
              and state.get("facts", spec.inspection_fact) is not None), "Unknown inspection signal")
        check(spec.loan_version is None or (spec.loan_id is not None and type(spec.loan_version) is int
              and spec.loan_version > 0), "Invalid exact loan version")
        if spec.recipient is not None:
            check(actor(spec.recipient), "Unknown action recipient")
    for req in state.tables["requests"].values():
        spec = state.get("action_specs", req.action_spec)
        check(spec is not None and req.version == spec.version and req.responder == spec.actor
              and actor(req.requester), "Invalid request terms/participants")
        check(req.response in {"pending", "accepted", "declined"}
              and (req.response_event is None) == (req.response == "pending"), "Invalid request response")
        check((req.delivery_event is None) == (req.understood_event is None), "Direct finite terms must be heard and understood")
        check(req.response == "pending" or req.understood_event is not None, "Response requires understood request")
        check(req.completion_receipt is None or (req.response == "accepted" and req.withdrawal_event is None),
              "Only a live accepted request can complete")
    for p in state.tables["promises"].values():
        spec = state.get("action_specs", p.action_spec)
        check(spec is not None and p.version == spec.version and p.promisor == spec.actor
              and actor(p.beneficiary), "Invalid promise identity")
        if p.loan_id is not None:
            check(state.get("loans", p.loan_id) is not None and spec.loan_id in {None, p.loan_id}, "Unknown related loan")
        check(p.status in {"active", "released", "fulfilled", "breached"}, "Invalid promise status")
        check((p.status in {"fulfilled", "breached"}) == (p.assessment_event is not None),
              "Promise assessment must preserve disposition")
        check((p.status == "fulfilled") == (p.performance_receipt is not None), "Fulfillment requires a receipt")
        check(p.repair_receipt is None or p.status == "breached", "Repair cannot erase breach")
        check(p.status != "released" or p.release_event is not None, "Release requires an event")
    for row in state.tables["booking_slots"].values():
        place = state.get("entities", row.place)
        check(place is not None and place.kind == "place" and type(row.version) is int and row.version > 0,
              "Invalid booking slot")
        check(row.booked_by is None or actor(row.booked_by), "Invalid slot assignee")
    for event in state.events:
        for change in event.changes:
            if change.table in {"action_specs", "refusals", "domain_receipts"}:
                check(state.get(change.table, change.key) == change.after, "Immutable social record changed")
            if change.table == "requests":
                current = state.get("requests", change.key)
                if change.after.response != "pending":
                    check(current.response == change.after.response
                          and current.response_event == change.after.response_event,
                          "An initial request response cannot be rewritten")
                if change.after.withdrawal_event is not None:
                    check(current.withdrawal_event == change.after.withdrawal_event, "Withdrawal cannot be erased")
            if change.table == "promises":
                current = state.get("promises", change.key)
                check((current.action_spec, current.version, current.created_event, current.promisor,
                       current.beneficiary, current.request, current.loan_id, current.replaces) ==
                      (change.after.action_spec, change.after.version, change.after.created_event,
                       change.after.promisor, change.after.beneficiary, change.after.request,
                       change.after.loan_id, change.after.replaces), "Undertaking identity is immutable")
                if change.after.status == "breached":
                    check(current.status == "breached" and current.assessment_event == change.after.assessment_event,
                          "Breach cannot be erased")
                if change.after.status in {"fulfilled", "released"}:
                    check(current.status == change.after.status, "Terminal promise disposition cannot change")
                if change.after.release_event is not None:
                    check(current.release_event == change.after.release_event, "Release cannot be erased")


def register(registry):
    for table, cls in (("action_specs", ActionSpec), ("requests", Request), ("promises", Promise),
                       ("refusals", RefusalDecision), ("booking_slots", BookingSlot),
                       ("domain_receipts", DomainReceipt)):
        registry.table(table, cls)
    registry.validators.append(validate)
    registry.initial_validators.append(validate_initial)
    from .physical import TABLES as PHYSICAL_TABLES
    social = {"entities", "parents", "containers", "action_specs", "requests", "promises", "refusals"}
    receipts = set(RECEIPT_TABLES) | {"propositions", "loans"}
    contracts = (
        ("create_request", create_request, social, {"requests"}),
        ("deliver_request", deliver_request, social, {"requests"}),
        ("acknowledge_request", acknowledge_request, social, set()),
        ("respond_request", respond_request, social, {"requests", "refusals"}),
        ("withdraw_request", withdraw_request, social, {"requests"}),
        ("complete_request", complete_request, social | receipts, {"requests"}),
        ("make_promise", make_promise, social | {"loans"}, {"promises"}),
        ("release_promise", release_promise, social, {"promises"}),
        ("assess_promise", assess_promise, social | receipts, {"promises"}),
        ("record_late_repair", record_late_repair, social | receipts, {"promises"}),
        ("refuse", refuse, social | set(PHYSICAL_TABLES),
         {"requests", "refusals", "loan_offers", "return_offers", "offer_responses"}),
        ("acknowledge_refusal", acknowledge_refusal, social, set()),
        ("perform_booking", perform_booking, {"entities", "parents", "booking_slots", "domain_receipts"},
         {"booking_slots", "domain_receipts"}),
        ("check_booking", check_booking, {"entities", "parents", "booking_slots", "domain_receipts"}, {"domain_receipts"}),
    )
    for name, handler, reads, writes in contracts:
        registry.operation(name, handler, reads=reads, writes=writes)
