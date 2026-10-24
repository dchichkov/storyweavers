"""Slice 1 physical continuity, explicit consent, and immediate loan settlement.

Grants and terms are authored finite rows, never inferred from claims. Grant
scope is a terms ID for lend/release and a loan ID for receive/settle/deposit.
Destinations are exact: borrower for lend, source parent for release, recipient
for receive/settle, and container for deposit. Only an owner toggles a grant.
An optional place restricts both grantee and object at offer/performance time.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

from .core import Record, Rejected


@dataclass(frozen=True, kw_only=True)
class Parent(Record):
    parent: str


@dataclass(frozen=True, kw_only=True)
class Ownership(Record):
    owner: str


@dataclass(frozen=True, kw_only=True)
class Container(Record):
    open: bool = True
    latchable: bool = False
    latched: bool = False


@dataclass(frozen=True, kw_only=True)
class Route(Record):
    source: str
    destination: str
    open: bool = True
    max_load: int = 10


@dataclass(frozen=True, kw_only=True)
class Grant(Record):
    issuer: str
    grantee: str
    object: str
    right: str
    scope: str
    destination: str
    active: bool = True
    place: str | None = None


@dataclass(frozen=True, kw_only=True)
class LoanTerms(Record):
    version: int
    object: str
    owner: str
    lender: str
    borrower: str
    source: str
    return_authority: str
    return_recipient: str
    return_destination: str
    collection_from: int = 0
    collection_before: int = 200
    require_latch: bool = False


@dataclass(frozen=True, kw_only=True)
class LoanOffer(Record):
    terms: str
    version: int
    loan_id: str
    event_id: str
    status: str = "pending"
    response_event_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class TermsComprehension(Record):
    offer: str
    terms: str
    version: int
    actor: str
    event_id: str


@dataclass(frozen=True, kw_only=True)
class OfferResponse(Record):
    offer: str
    kind: str
    version: int
    responder: str
    decision: str
    event_id: str
    tick: int


@dataclass(frozen=True, kw_only=True)
class Readiness(Record):
    giver: str
    recipient: str
    object: str
    operation: str
    event_id: str
    consumed: bool = False


@dataclass(frozen=True, kw_only=True)
class Loan(Record):
    terms: str
    version: int
    borrower: str
    status: str
    activation_receipt: str
    settlement_receipt: str | None = None


@dataclass(frozen=True, kw_only=True)
class ReturnOffer(Record):
    loan_id: str
    object: str
    recipient: str
    destination: str
    version: int
    event_id: str
    status: str = "pending"
    response_event_id: str | None = None


@dataclass(frozen=True, kw_only=True)
class PhysicalReceipt(Record):
    operation: str
    object: str
    source: str
    destination: str
    actor: str
    recipient: str | None
    event_id: str
    tick: int
    loan_id: str | None = None


TABLES = {
    "parents": Parent, "ownership": Ownership, "containers": Container,
    "routes": Route, "grants": Grant, "loan_terms": LoanTerms,
    "loan_offers": LoanOffer, "terms_comprehensions": TermsComprehension,
    "offer_responses": OfferResponse, "readiness": Readiness, "loans": Loan,
    "return_offers": ReturnOffer, "receipts": PhysicalReceipt,
}

HISTORY_TABLES = frozenset({
    "loan_offers", "terms_comprehensions", "offer_responses", "readiness",
    "loans", "return_offers", "receipts",
})


def validate_initial(state):
    """Initial-only hook: history is enacted, never authored as prior performance."""
    if any(state.tables[table] for table in HISTORY_TABLES):
        raise Rejected("Physical interaction/receipt history must start empty")


def path(tx, entity):
    """Return subject-to-place IDs, retaining every physical path read."""
    result = []
    while True:
        tx.require(entity not in result, "Cyclic physical path")
        result.append(entity)
        if tx.get("entities", entity).kind == "place":
            return tuple(result)
        entity = tx.get("parents", entity).parent


def location(tx, entity):
    return path(tx, entity)[-1]


def holder(tx, entity):
    """Nearest actor ancestor, not legal owner, keeper, or borrower."""
    for ancestor in path(tx, entity)[1:]:
        if tx.get("entities", ancestor).kind == "actor":
            return ancestor
    return None


physical_holder = holder


def accessible(tx, actor, entity):
    tx.entity(actor, "actor")
    subject_path = path(tx, entity)
    if location(tx, actor) != subject_path[-1]:
        return False
    for ancestor in subject_path[1:]:
        kind = tx.get("entities", ancestor).kind
        if kind == "actor" and ancestor != actor:
            return False
        if kind == "container":
            box = tx.get("containers", ancestor)
            if not box.open or box.latched:
                return False
    return True


def _new(tx, table, key):
    tx.require(bool(key) and tx.maybe(table, key) is None, "Identity already used")


def _portable(tx, object):
    tx.require(tx.get("entities", object).kind in {"object", "container"}, "Not portable")


def _owner(tx, object):
    return tx.get("ownership", object).owner


def _grant(tx, *, grantee, object, right, scope, destination, authority):
    owner = _owner(tx, object)
    matches = [g for g in tx.all("grants")
               if g.active and g.grantee == grantee and g.object == object
               and g.right == right and g.scope == scope and g.destination == destination
               and g.issuer in {owner, authority}
               and (g.place is None or (location(tx, g.grantee) == g.place and location(tx, object) == g.place))]
    tx.require(bool(matches), "No current exact scoped grant")
    # Reading the scan records activation/revocation dependencies, including absence.
    return sorted(matches, key=lambda g: g.id)[0]


def _terms(tx, terms, version):
    result = tx.get("loan_terms", terms)
    tx.require(result.version == version, "Stale terms version")
    tx.require(_owner(tx, result.object) == result.owner, "Terms owner mismatch")
    return result


def _lending_authority(tx, terms):
    grants = ()
    if terms.lender != terms.owner:
        lend = _grant(tx, grantee=terms.lender, object=terms.object, right="lend",
               scope=terms.id, destination=terms.borrower, authority=terms.owner)
        release = _grant(tx, grantee=terms.lender, object=terms.object, right="release",
               scope=terms.id, destination=terms.source, authority=terms.owner)
        grants = (lend.id, release.id)
    physical_holder = holder(tx, terms.object)
    tx.require(physical_holder in {None, terms.lender}, "Lender cannot release another holder's object")
    return grants


def _ready(tx, readiness_id, giver, recipient, object, operation):
    ready = tx.get("readiness", readiness_id)
    tx.require(not ready.consumed and
               (ready.giver, ready.recipient, ready.object, ready.operation) ==
               (giver, recipient, object, operation), "Readiness mismatch or already consumed")
    tx.depend(ready.event_id)
    tx.put("readiness", replace(ready, consumed=True))


def _move(tx, object, source, destination):
    _portable(tx, object)
    tx.require(tx.get("parents", object).parent == source, "Current source mismatch")
    tx.require(source != destination, "Duplicate movement")
    tx.require(object not in path(tx, destination), "Cyclic placement")
    _capacity(tx, object, destination)
    tx.put("parents", Parent(id=object, parent=destination))


def _capacity(tx, object, destination):
    # Occupancy scans retain freeing/consuming-capacity events through replay.
    physical_paths = {row.id: path(tx, row.id) for row in tx.all("parents")}
    masses = {key: tx.get("entities", key).mass for key in physical_paths}
    moved_mass = sum(masses[key] for key, chain in physical_paths.items() if object in chain)
    old_ancestors = physical_paths[object][1:]
    for ancestor in path(tx, destination):
        target = tx.get("entities", ancestor)
        if target.kind not in {"actor", "container"}:
            continue
        current = sum(masses[key] for key, chain in physical_paths.items() if ancestor in chain[1:])
        added = 0 if ancestor in old_ancestors else moved_mass
        tx.require(current + added <= target.capacity, "Current physical capacity exceeded")


def _receipt(tx, object, source, destination, recipient=None, loan_id=None):
    _new(tx, "receipts", tx.event_id)
    tx.put("receipts", PhysicalReceipt(
        id=tx.event_id, operation=tx.action.operation, object=object, source=source,
        destination=destination, actor=tx.action.actor, recipient=recipient,
        event_id=tx.event_id, tick=tx.tick, loan_id=loan_id))
    return tx.event_id


def pickup(tx, *, object, source):
    actor = tx.action.actor
    tx.require(holder(tx, object) is None, "Object already physically held")
    tx.require(accessible(tx, actor, object), "Object inaccessible")
    _move(tx, object, source, actor)
    receipt = _receipt(tx, object, source, actor, actor)
    tx.emit(object=object, source=source, destination=actor, receipt=receipt)


def _placement(tx, object, destination):
    actor = tx.action.actor
    tx.require(holder(tx, object) == actor and accessible(tx, actor, object), "No accessible custody")
    target = tx.get("entities", destination)
    tx.require(target.kind in {"place", "container"}, "Use handoff for actor recipients")
    tx.require(accessible(tx, actor, destination), "Destination inaccessible")
    if target.kind == "container":
        box = tx.get("containers", destination)
        tx.require(box.open and not box.latched, "Destination closed")
    return tx.get("parents", object).parent


def put(tx, *, object, destination):
    source = _placement(tx, object, destination)
    _move(tx, object, source, destination)
    receipt = _receipt(tx, object, source, destination)
    tx.emit(object=object, source=source, destination=destination, receipt=receipt)


def travel(tx, *, route):
    actor = tx.action.actor
    road = tx.get("routes", route)
    tx.require(road.open and location(tx, actor) == road.source, "Route unavailable")
    load = sum(tx.get("entities", e.id).mass for e in tx.all("parents")
               if actor in path(tx, e.id)[1:])
    tx.require(load <= road.max_load, "Route requires free carrying capacity")
    tx.put("parents", Parent(id=actor, parent=road.destination))
    receipt = _receipt(tx, actor, road.source, road.destination, actor)
    tx.emit(route=route, source=road.source, destination=road.destination, receipt=receipt)


def set_container(tx, *, container, open, latch=False):
    """A latch is not a lock: opening explicitly unlatches a reachable box."""
    tx.entity(container, "container")
    box = tx.get("containers", container)
    tx.require(type(open) is bool and type(latch) is bool, "Container settings must be booleans")
    tx.require(accessible(tx, tx.action.actor, container), "Outer container is not reachable")
    tx.require(not latch or (not open and box.latchable), "Unsupported latch request")
    updated = replace(box, open=open, latched=latch)
    tx.require(updated != box, "Container already in that state")
    tx.put("containers", updated)
    tx.emit(container=container, open=open, latched=latch)


def readiness(tx, *, id, giver, object, operation="handoff"):
    actor = tx.action.actor
    _new(tx, "readiness", id)
    tx.entity(giver, "actor")
    _portable(tx, object)
    tx.require(giver != actor and operation in {"handoff", "activate_loan", "complete_return"},
               "Invalid readiness participants/operation")
    tx.put("readiness", Readiness(id=id, giver=giver, recipient=actor, object=object,
                                 operation=operation, event_id=tx.event_id))
    tx.emit(readiness=id, giver=giver, recipient=actor, object=object, operation=operation)


def _handover(tx, object, recipient):
    actor = tx.action.actor
    tx.entity(recipient, "actor")
    tx.require(actor != recipient and location(tx, actor) == location(tx, recipient), "Recipient out of reach")
    tx.require(holder(tx, object) == actor and accessible(tx, actor, object), "No accessible custody")
    return tx.get("parents", object).parent


def handoff(tx, *, object, recipient, readiness_id, loan_id=None):
    source = _handover(tx, object, recipient)
    if loan_id is not None:
        loan, terms = _active(tx, loan_id)
        tx.require(terms.object == object, "Wrong loan object")
    _ready(tx, readiness_id, tx.action.actor, recipient, object, "handoff")
    _move(tx, object, source, recipient)
    receipt = _receipt(tx, object, source, recipient, recipient, loan_id)
    tx.emit(object=object, recipient=recipient, receipt=receipt, loan_id=loan_id)


def set_grant(tx, *, grant, active):
    row = tx.get("grants", grant)
    tx.require(type(active) is bool and tx.action.actor == _owner(tx, row.object), "Only owner toggles finite grants")
    tx.require(row.active != active, "Grant already in that state")
    tx.put("grants", replace(row, active=active))
    tx.emit(grant=grant, active=active)


def offer_loan(tx, *, id, terms, version, loan_id):
    terms = _terms(tx, terms, version)
    tx.require(tx.action.actor == terms.lender, "Not the named lender")
    tx.require(location(tx, terms.lender) == location(tx, terms.borrower), "Offer not directly delivered")
    grants = _lending_authority(tx, terms)
    _new(tx, "loan_offers", id)
    _new(tx, "loans", loan_id)
    tx.require(not any(o.loan_id == loan_id for o in tx.all("loan_offers")), "Loan ID already offered")
    tx.put("loan_offers", LoanOffer(id=id, terms=terms.id, version=version,
                                    loan_id=loan_id, event_id=tx.event_id))
    tx.emit(offer=id, terms=terms.id, version=version, loan_id=loan_id, delivered_to=terms.borrower,
            authority_grants=grants)


def comprehend_loan(tx, *, offer, version):
    offered = tx.get("loan_offers", offer)
    terms = _terms(tx, offered.terms, version)
    tx.require(offered.version == version and offered.status == "pending", "Offer no longer pending")
    tx.require(tx.action.actor == terms.borrower, "Wrong terms reader")
    _new(tx, "terms_comprehensions", offer)
    tx.depend(offered.event_id)
    tx.put("terms_comprehensions", TermsComprehension(
        id=offer, offer=offer, terms=terms.id, version=version,
        actor=tx.action.actor, event_id=tx.event_id))
    tx.emit(offer=offer, terms=terms.id, version=version, comprehended_by=tx.action.actor)


def _response(tx, offered, kind, version, decision, responder):
    tx.require(decision in {"accepted", "declined"}, "Unsupported response decision")
    tx.require(offered.status == "pending" and offered.version == version, "Response stale or duplicate")
    tx.require(tx.action.actor == responder, "Wrong responder")
    tx.depend(offered.event_id)
    _new(tx, "offer_responses", tx.event_id)
    tx.put("offer_responses", OfferResponse(id=tx.event_id, offer=offered.id, kind=kind,
           version=version, responder=responder, decision=decision, event_id=tx.event_id, tick=tx.tick))
    table = "loan_offers" if kind == "loan" else "return_offers"
    tx.put(table, replace(offered, status=decision, response_event_id=tx.event_id))
    # This is the single payload owner, also when called by the social refuse adapter.
    tx.emit(offer=offered.id, kind=kind, version=version, decision=decision, responder=responder)


def respond_loan(tx, *, offer, version, decision="accepted"):
    """Interaction-owned response helper; social refusal delegates here once."""
    offered = tx.get("loan_offers", offer)
    terms = _terms(tx, offered.terms, version)
    if decision == "accepted":
        understood = tx.get("terms_comprehensions", offer)
        tx.require((understood.terms, understood.version, understood.actor) ==
                   (terms.id, version, terms.borrower), "Terms not comprehended")
        tx.depend(understood.event_id)
    _response(tx, offered, "loan", version, decision, terms.borrower)


def activate_loan(tx, *, offer, version, readiness_id):
    offered = tx.get("loan_offers", offer)
    terms = _terms(tx, offered.terms, version)
    actor = tx.action.actor
    tx.require(offered.status == "accepted" and offered.version == version, "No exact loan consent")
    tx.require(actor == terms.borrower, "Only borrower collects")
    tx.require(terms.collection_from <= tx.tick < terms.collection_before, "Outside collection window")
    _lending_authority(tx, terms)
    _new(tx, "loans", offered.loan_id)
    tx.require(not any(l.status == "active" and tx.get("loan_terms", l.terms).object == terms.object
                       for l in tx.all("loans")), "Object already on loan")
    # Actor-held collection is a lender-to-borrower handover, not ordinary access.
    tx.require(location(tx, terms.object) == location(tx, actor), "Collection out of reach")
    for ancestor in path(tx, terms.object)[1:]:
        kind = tx.get("entities", ancestor).kind
        if kind == "actor":
            tx.require(ancestor == terms.lender, "Another actor controls collection")
        if kind == "container":
            box = tx.get("containers", ancestor)
            tx.require(box.open and not box.latched, "Collection container closed")
    _ready(tx, readiness_id, terms.lender, actor, terms.object, "activate_loan")
    tx.depend(offered.response_event_id)
    _move(tx, terms.object, terms.source, actor)
    receipt = _receipt(tx, terms.object, terms.source, actor, actor, offered.loan_id)
    tx.put("loan_offers", replace(offered, status="activated"))
    tx.put("loans", Loan(id=offered.loan_id, terms=terms.id, version=version,
           borrower=actor, status="active", activation_receipt=receipt))
    tx.emit(offer=offer, loan_id=offered.loan_id, object=terms.object, receipt=receipt)


def _active(tx, loan_id):
    loan = tx.get("loans", loan_id)
    tx.require(loan.status == "active", "Loan is not active")
    terms = _terms(tx, loan.terms, loan.version)
    tx.depend(tx.get("receipts", loan.activation_receipt).event_id)
    return loan, terms


def offer_return(tx, *, id, loan_id, object, recipient, destination, version):
    loan, terms = _active(tx, loan_id)
    tx.require(tx.action.actor == loan.borrower and object == terms.object, "Wrong borrower/object")
    tx.require(version == loan.version, "Stale return terms")
    tx.entity(recipient, "actor")
    tx.require(location(tx, tx.action.actor) == location(tx, recipient), "Return offer not delivered")
    _new(tx, "return_offers", id)
    sequence = 1 + sum(row.loan_id == loan_id for row in tx.all("return_offers"))
    tx.put("return_offers", ReturnOffer(id=id, loan_id=loan_id, object=object,
           recipient=recipient, destination=destination, version=version, event_id=tx.event_id))
    tx.emit(offer=id, loan_id=loan_id, object=object, recipient=recipient, destination=destination, sequence=sequence)


def respond_return(tx, *, offer, version, decision="accepted"):
    """Exact pending return response; acceptance is not receipt readiness."""
    offered = tx.get("return_offers", offer)
    loan, terms = _active(tx, offered.loan_id)
    tx.require(version == loan.version, "Stale return terms")
    _response(tx, offered, "return", version, decision, offered.recipient)


def _settlement(tx, loan_id, object):
    loan, terms = _active(tx, loan_id)
    tx.require(tx.action.actor == loan.borrower and object == terms.object, "Wrong loan/object/borrower")
    return loan, terms


def complete_return(tx, *, offer, version, readiness_id):
    offered = tx.get("return_offers", offer)
    loan, terms = _settlement(tx, offered.loan_id, offered.object)
    tx.require(offered.status == "accepted" and offered.version == version == loan.version,
               "No exact return consent")
    tx.require(offered.recipient == terms.return_recipient and offered.destination == offered.recipient
               and terms.return_destination == offered.destination, "Wrong designated return target")
    tx.require(not terms.require_latch, "Required latched return needs authorized deposit")
    grant = _grant(tx, grantee=offered.recipient, object=terms.object, right="settle", scope=loan.id,
           destination=offered.recipient, authority=terms.return_authority)
    source = _handover(tx, terms.object, offered.recipient)
    _ready(tx, readiness_id, tx.action.actor, offered.recipient, terms.object, "complete_return")
    tx.depend(offered.response_event_id)
    _move(tx, terms.object, source, offered.recipient)
    receipt = _receipt(tx, terms.object, source, offered.recipient, offered.recipient, loan.id)
    tx.put("return_offers", replace(offered, status="completed"))
    tx.put("loans", replace(loan, status="discharged", settlement_receipt=receipt))
    tx.emit(offer=offer, loan_id=loan.id, object=terms.object, receipt=receipt, authority_grant=grant.id)


def authorized_deposit(tx, *, loan_id, object, destination):
    loan, terms = _settlement(tx, loan_id, object)
    tx.entity(destination, "container")
    tx.require(destination == terms.return_destination, "Wrong designated deposit site")
    _grant(tx, grantee=tx.action.actor, object=object, right="deposit", scope=loan.id,
           destination=destination, authority=terms.return_authority)
    source = _placement(tx, object, destination)
    box = tx.get("containers", destination)
    if terms.require_latch:
        tx.require(box.latchable, "Required latch unsupported")
        tx.put("containers", replace(box, open=False, latched=True))
    _move(tx, object, source, destination)
    receipt = _receipt(tx, object, source, destination, loan_id=loan.id)
    tx.put("loans", replace(loan, status="discharged", settlement_receipt=receipt))
    tx.emit(loan_id=loan.id, object=object, destination=destination, receipt=receipt,
            latched=terms.require_latch)


def validate(state):
    """State-only invariants; operation guards additionally validate current authority."""
    def require(condition, message):
        if not condition:
            raise Rejected(message)

    def entity(key, kinds):
        row = state.get("entities", key)
        require(row is not None and row.kind in kinds, "Invalid physical reference")
        return row

    def rows(table):
        return state.tables[table].values()

    def response(offered, kind, responder):
        if offered.status == "pending":
            require(offered.response_event_id is None, "Pending offer cannot have a response")
            return
        decision = state.get("offer_responses", offered.response_event_id)
        expected = "declined" if offered.status == "declined" else "accepted"
        require(decision is not None and decision.offer == offered.id and decision.kind == kind
                and decision.version == offered.version and decision.responder == responder
                and decision.decision == expected, "Offer requires its exact owning response")

    entities = state.tables["entities"]
    require(set(state.tables["parents"]) == {e.id for e in entities.values() if e.kind != "place"},
            "Every non-place needs exactly one parent")
    require(set(state.tables["containers"]) == {e.id for e in entities.values() if e.kind == "container"},
            "Container capability must match physical entity")
    paths = {}
    for e in entities.values():
        current, chain = e.id, []
        while True:
            require(current not in chain, "Cyclic containment")
            chain.append(current)
            if entity(current, {"actor", "place", "object", "container"}).kind == "place":
                break
            parent = state.get("parents", current)
            require(parent is not None, "Missing physical parent")
            target = entity(parent.parent, {"actor", "place", "container"})
            if entities[current].kind == "actor":
                require(target.kind == "place", "Actor must directly inhabit a place")
            current = target.id
        paths[e.id] = chain
    for e in entities.values():
        if e.kind in {"actor", "container"}:
            load = sum(entities[key].mass for key, chain in paths.items() if e.id in chain[1:])
            require(load <= e.capacity, "Physical capacity exceeded")
    for box in rows("containers"):
        require(all(type(v) is bool for v in (box.open, box.latchable, box.latched)), "Invalid container flags")
        require(not box.latched or (box.latchable and not box.open), "Invalid latch state")
    for row in rows("ownership"):
        entity(row.id, {"object", "container"})
        entity(row.owner, {"actor"})
    for road in rows("routes"):
        entity(road.source, {"place"})
        entity(road.destination, {"place"})
        require(road.source != road.destination and type(road.open) is bool
                and type(road.max_load) is int and road.max_load >= 0, "Invalid finite route")
    for terms in rows("loan_terms"):
        entity(terms.object, {"object", "container"})
        for actor in (terms.owner, terms.lender, terms.borrower, terms.return_authority, terms.return_recipient):
            entity(actor, {"actor"})
        entity(terms.source, {"actor", "place", "container"})
        entity(terms.return_destination, {"actor", "container"})
        require(terms.lender != terms.borrower and type(terms.version) is int and terms.version > 0,
                "Invalid loan participants/version")
        require(type(terms.collection_from) is int and type(terms.collection_before) is int
                and 0 <= terms.collection_from < terms.collection_before
                and type(terms.require_latch) is bool, "Invalid collection/latch terms")
        require(state.get("ownership", terms.object) is not None
                and state.get("ownership", terms.object).owner == terms.owner, "Terms must preserve title")
    for grant in rows("grants"):
        entity(grant.grantee, {"actor"})
        entity(grant.issuer, {"actor"})
        entity(grant.object, {"object", "container"})
        entity(grant.destination, {"actor", "place", "container"})
        if grant.place is not None:
            entity(grant.place, {"place"})
        require(grant.right in {"lend", "release", "receive", "settle", "deposit"}
                and bool(grant.scope) and type(grant.active) is bool, "Invalid finite grant")
        owner = state.get("ownership", grant.object)
        require(owner is not None, "Grant needs legal owner")
        authorities = {owner.owner}
        if grant.right in {"receive", "settle", "deposit"}:
            authorities.update(t.return_authority for t in rows("loan_terms") if t.object == grant.object)
        require(grant.issuer in authorities, "Grant issuer lacks original authority")
    active_objects = set()
    for loan in rows("loans"):
        terms = state.get("loan_terms", loan.terms)
        require(terms is not None and terms.version == loan.version and terms.borrower == loan.borrower,
                "Invalid loan terms binding")
        require(loan.status in {"active", "discharged"}, "Invalid loan status")
        activation = state.get("receipts", loan.activation_receipt)
        require(activation is not None and activation.operation == "activate_loan"
                and activation.loan_id == loan.id and activation.object == terms.object
                and activation.destination == loan.borrower, "Loan needs its exact activation receipt")
        if loan.status == "active":
            require(terms.object not in active_objects and loan.settlement_receipt is None,
                    "Only one active loan per object")
            active_objects.add(terms.object)
        else:
            receipt = state.get("receipts", loan.settlement_receipt)
            require(receipt is not None and receipt.operation in {"complete_return", "authorized_deposit"}
                    and receipt.loan_id == loan.id and receipt.object == terms.object,
                    "Settlement needs exact immediate return receipt")
    for offered in rows("loan_offers"):
        terms = state.get("loan_terms", offered.terms)
        require(terms is not None and terms.version == offered.version, "Invalid offered terms")
        require(offered.status in {"pending", "accepted", "declined", "activated"}, "Invalid loan offer status")
        response(offered, "loan", terms.borrower)
        if offered.status in {"accepted", "activated"}:
            understood = state.get("terms_comprehensions", offered.id)
            require(understood is not None and understood.terms == terms.id
                    and understood.version == offered.version and understood.actor == terms.borrower,
                    "Acceptance needs exact comprehension")
        if offered.status == "activated":
            loan = state.get("loans", offered.loan_id)
            require(loan is not None and loan.terms == offered.terms and loan.version == offered.version,
                    "Activated offer needs its specific loan")
    for understood in rows("terms_comprehensions"):
        offered = state.get("loan_offers", understood.offer)
        require(offered is not None and understood.id == understood.offer
                and understood.terms == offered.terms and understood.version == offered.version
                and understood.actor == state.get("loan_terms", offered.terms).borrower,
                "Comprehension must identify delivered exact terms")
    for offered in rows("return_offers"):
        loan = state.get("loans", offered.loan_id)
        require(loan is not None and loan.version == offered.version
                and state.get("loan_terms", loan.terms).object == offered.object, "Return must bind exact loan")
        entity(offered.recipient, {"actor"})
        entity(offered.destination, {"actor", "container"})
        require(offered.status in {"pending", "accepted", "declined", "completed"}, "Invalid return offer status")
        response(offered, "return", offered.recipient)
        if offered.status == "completed":
            receipt = state.get("receipts", loan.settlement_receipt)
            require(loan.status == "discharged" and receipt is not None
                    and receipt.operation == "complete_return" and receipt.destination == offered.recipient,
                    "Completed return needs exact hand-back")
    responses = set()
    for decision in rows("offer_responses"):
        require(decision.kind in {"loan", "return"} and decision.decision in {"accepted", "declined"}
                and decision.id == decision.event_id and type(decision.tick) is int and decision.tick >= 0,
                "Invalid typed offer response")
        table = "loan_offers" if decision.kind == "loan" else "return_offers"
        offered = state.get(table, decision.offer)
        require(offered is not None and offered.response_event_id == decision.event_id,
                "Response cannot be detached from its owner")
        key = (decision.kind, decision.offer)
        require(key not in responses, "Offer can be answered only once")
        responses.add(key)
    for ready in rows("readiness"):
        entity(ready.giver, {"actor"})
        entity(ready.recipient, {"actor"})
        entity(ready.object, {"object", "container"})
        require(ready.giver != ready.recipient and type(ready.consumed) is bool
                and ready.operation in {"handoff", "activate_loan", "complete_return"}, "Invalid receipt readiness")
    by_event = {event.id: event for event in state.events}
    for receipt in rows("receipts"):
        entity(receipt.object, {"actor"} if receipt.operation == "travel" else {"object", "container"})
        entity(receipt.source, {"actor", "container", "place"})
        entity(receipt.destination, {"actor", "container", "place"})
        entity(receipt.actor, {"actor"})
        if receipt.recipient is not None:
            entity(receipt.recipient, {"actor"})
        require(receipt.source != receipt.destination and type(receipt.tick) is int and receipt.tick >= 0,
                "Invalid physical receipt")
        require(receipt.id == receipt.event_id and receipt.operation in {
            "pickup", "put", "travel", "handoff", "activate_loan", "complete_return", "authorized_deposit"},
            "Receipt must identify one physical performance")
        if receipt.loan_id is not None:
            loan = state.get("loans", receipt.loan_id)
            require(loan is not None and state.get("loan_terms", loan.terms).object == receipt.object,
                    "Receipt loan identity must match the physical object")
        if receipt.operation == "travel":
            entity(receipt.source, {"place"})
            entity(receipt.destination, {"place"})
            require(receipt.object == receipt.actor == receipt.recipient,
                    "Travel receipt must identify actor and actual places")
        event = by_event.get(receipt.event_id)
        if event is not None:
            original = [c for c in event.changes if c.table == "receipts" and c.key == receipt.id]
            require(len(original) == 1 and original[0].before is None and original[0].after == receipt
                    and event.tick == receipt.tick and event.action.operation == receipt.operation
                    and event.action.actor == receipt.actor, "Committed receipt is immutable")
            movement = [c for c in event.changes if c.table == "parents" and c.key == receipt.object]
            require(len(movement) == 1 and movement[0].before is not None
                    and movement[0].before.parent == receipt.source
                    and movement[0].after.parent == receipt.destination,
                    "Receipt must describe its actual physical movement")


def register(registry):
    for table, record in TABLES.items():
        registry.table(table, record)
    registry.validators.append(validate)
    registry.initial_validators.append(validate_initial)
    operations = {
        "pickup": pickup, "put": put, "travel": travel, "set_container": set_container, "readiness": readiness,
        "handoff": handoff, "set_grant": set_grant, "offer_loan": offer_loan,
        "comprehend_loan": comprehend_loan, "respond_loan": respond_loan,
        "activate_loan": activate_loan, "offer_return": offer_return,
        "respond_return": respond_return, "complete_return": complete_return,
        "authorized_deposit": authorized_deposit,
    }
    # Conservative family read contract permits shared helpers and delegated responses.
    reads = set(TABLES) | {"entities"}
    writes = {
        "pickup": {"parents", "receipts"}, "put": {"parents", "receipts"},
        "travel": {"parents", "receipts"}, "set_container": {"containers"}, "readiness": {"readiness"},
        "handoff": {"parents", "receipts", "readiness"}, "set_grant": {"grants"},
        "offer_loan": {"loan_offers"}, "comprehend_loan": {"terms_comprehensions"},
        "respond_loan": {"loan_offers", "offer_responses"},
        "activate_loan": {"parents", "receipts", "readiness", "loan_offers", "loans"},
        "offer_return": {"return_offers"}, "respond_return": {"return_offers", "offer_responses"},
        "complete_return": {"parents", "receipts", "readiness", "return_offers", "loans"},
        "authorized_deposit": {"parents", "receipts", "loans", "containers"},
    }
    for name, handler in operations.items():
        registry.operation(name, handler, reads=reads, writes=writes[name])
