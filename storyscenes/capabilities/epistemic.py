"""Opt-in finite evidence, communication and explicit belief dispositions.

Signals are authored facts embedded in physical carriers, not English to parse.
Only ``update_belief`` writes belief versions/heads. Observing and transmitting
never call it. Reference intervals are inclusive and distinct from event time.
"""
from __future__ import annotations

from dataclasses import dataclass, replace
import math

from .core import CapabilityError, Record


@dataclass(frozen=True, kw_only=True, eq=False)
class Result:
    kind: str  # exact / partial / unknown
    value: str | bool | int | float | None = None
    alternatives: tuple[str | bool | int | float, ...] = ()
    reason: str | None = None

    def _identity(self):
        # Physical false/zero and integer/float measurements are distinct values.
        return (self.kind, (type(self.value), self.value),
                tuple((type(v), v) for v in self.alternatives), self.reason)

    def __eq__(self, other):
        if type(other) is not Result:
            return NotImplemented
        return self._identity() == other._identity()

    def __hash__(self):
        return hash(self._identity())


@dataclass(frozen=True, kw_only=True)
class Proposition(Record):
    subject: str
    predicate: str
    result: Result
    scope: str
    reference_start: int | None
    reference_end: int | None


@dataclass(frozen=True, kw_only=True)
class Fact(Record):
    carrier: str
    proposition: str
    live: bool = False
    projection: str = "signal"  # signal / location (physical.location)
    domain: tuple[str, ...] = ()
    assertion: str | None = None  # inscription's assertion, NOT its truth
    source_ids: tuple[str, ...] = ()  # authored underlying sources; default carrier


@dataclass(frozen=True, kw_only=True)
class Exposure(Record):
    fact: str
    exposed: bool = True
    readable: bool = True
    coverage: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class Channel(Record):
    kind: str  # observation / speech / delayed
    enabled: bool = True
    carrier: str | None = None
    instrument: str | None = None
    delay: int = 0


@dataclass(frozen=True, kw_only=True)
class Attention(Record):
    actor: str
    source: str
    channel: str
    until: int


@dataclass(frozen=True, kw_only=True)
class Evidence(Record):
    event_id: str
    observer: str
    fact: str
    source: str
    proposition: str
    acquired_at: int
    channel: str
    attention: str
    exposure: str
    outcome: str  # exact / partial / unknown / inaccessible
    coverage: tuple[str, ...]
    actor_path: tuple[str, ...]
    source_path: tuple[str, ...]
    instrument_path: tuple[str, ...] = ()
    channel_path: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    parents: tuple[str, ...] = ()


@dataclass(frozen=True, kw_only=True)
class Claim(Record):
    event_id: str
    speaker: str
    audience: str
    proposition: str
    emitted_at: int
    available_at: int
    channel: str
    source_ids: tuple[str, ...]
    evidence_ids: tuple[str, ...] = ()
    parents: tuple[str, ...] = ()
    belief: str | None = None
    comprehension: str | None = None
    attributed_source: str | None = None
    attributed_reference_start: int | None = None
    attributed_reference_end: int | None = None


@dataclass(frozen=True, kw_only=True)
class Receipt(Record):
    event_id: str
    claim: str
    recipient: str
    received_at: int
    recipient_path: tuple[str, ...]


@dataclass(frozen=True, kw_only=True)
class Comprehension(Record):
    event_id: str
    receipt: str
    actor: str
    understood_at: int


@dataclass(frozen=True, kw_only=True)
class AuthorityPolicy(Record):
    kind: str  # ledger / exposure_identity; exact authored projection only
    fact: str
    assertion: str
    validity_fact: str
    valid_from: int
    valid_until: int


@dataclass(frozen=True, kw_only=True)
class BeliefPolicy(Record):
    kind: str  # percept / testimony / authority / authored / defer / freshness
    modes: tuple[str, ...] = ("init", "adopt", "resolve")
    source: str | None = None  # named speaker for testimony
    authority: str | None = None
    max_age: int | None = None  # freshness: named testimony projected to decision time


@dataclass(frozen=True, kw_only=True)
class Belief(Record):
    actor: str
    proposition: str
    policy: str
    evidence_ids: tuple[str, ...] = ()
    comprehension_ids: tuple[str, ...] = ()
    source_ids: tuple[str, ...] = ()
    predecessor: str | None = None
    disposition: str | None = None
    event_id: str | None = None  # None permits an authored initial wrong belief


@dataclass(frozen=True, kw_only=True)
class BeliefHead(Record):
    actor: str
    belief: str


@dataclass(frozen=True, kw_only=True)
class Disposition(Record):
    event_id: str
    actor: str
    mode: str
    head: str
    policy: str
    proposition: str | None
    predecessor: str | None
    belief: str | None
    evidence_ids: tuple[str, ...]
    comprehension_ids: tuple[str, ...]
    decided_at: int


TABLES = {
    "propositions": Proposition, "facts": Fact, "exposures": Exposure,
    "channels": Channel, "attention": Attention, "evidence": Evidence,
    "claims": Claim, "claim_receipts": Receipt, "comprehensions": Comprehension,
    "authority_policies": AuthorityPolicy, "belief_policies": BeliefPolicy,
    "beliefs": Belief, "belief_heads": BeliefHead, "dispositions": Disposition,
}


def validate_initial(state):
    """Initial premises may include assumptions, never enacted epistemic history."""
    if any(state.tables[table] for table in (
            "evidence", "claims", "claim_receipts", "comprehensions", "dispositions")):
        raise CapabilityError("Epistemic event history must start empty")
    if any(b.event_id is not None for b in state.tables["beliefs"].values()):
        raise CapabilityError("Epistemic belief history must start empty")


def _key(proposition):
    return (proposition.subject, proposition.predicate, proposition.scope,
            proposition.reference_start, proposition.reference_end)


def _new(tx, table, record):
    tx.require(tx.maybe(table, record.id) is None, f"Immutable {table}/{record.id}")
    tx.put(table, record)


def _dependency(tx, record):
    if record.event_id is not None:
        tx.depend(record.event_id)


def attend(tx, *, source, channel, until, attention=None):
    attention = tx.event_id if attention is None else attention
    tx.entity(tx.action.actor, "actor")
    tx.entity(source)
    ch = tx.get("channels", channel)
    tx.require(ch.kind == "observation" and ch.enabled, "Unavailable observation channel")
    tx.require(type(until) is int and tx.tick <= until <= tx.tick + 200,
               "Attention requires a finite current interval")
    _new(tx, "attention", Attention(id=attention, actor=tx.action.actor,
                                   source=source, channel=channel, until=until))
    tx.emit(kind="attention", attention=attention, source=source)


def observe(tx, *, fact, exposure, channel, attention, evidence=None, attempt=False):
    from . import physical

    actor = tx.action.actor
    evidence = tx.event_id if evidence is None else evidence
    tx.require(type(attempt) is bool, "Inspection attempt must be explicit")
    signal = tx.get("facts", fact)
    tx.entity(actor, "actor")
    tx.entity(signal.carrier)
    ch = tx.get("channels", channel)
    focus = tx.get("attention", attention)
    view = tx.get("exposures", exposure)
    tx.require(ch.kind == "observation" and ch.enabled, "Unavailable channel")
    tx.require(focus.actor == actor and focus.source == signal.carrier
               and focus.channel == channel and focus.until >= tx.tick,
               "Inspection needs current attention")
    tx.require(view.fact == fact, "Exposure belongs to another signal")
    actor_path = physical.path(tx, actor)
    source_path = physical.path(tx, signal.carrier)
    accessible = physical.accessible(tx, actor, signal.carrier)
    instrument_path, channel_path = (), ()
    if ch.carrier is not None:
        channel_path = physical.path(tx, ch.carrier)
        tx.require(physical.accessible(tx, actor, ch.carrier), "Channel is inaccessible")
    if ch.instrument is not None:
        instrument_path = physical.path(tx, ch.instrument)
        tx.require(physical.accessible(tx, actor, ch.instrument), "Instrument is inaccessible")
    tx.require(accessible or attempt is True, "Illegal inaccessible inspection")
    template = tx.get("propositions", signal.proposition)
    # Do not read hidden result fields to manufacture partial alternatives.
    if not accessible:
        result = Result(kind="unknown", reason="inaccessible")
        outcome, coverage = "inaccessible", ()
    elif not view.exposed or not view.readable:
        result = Result(kind="unknown", reason="occluded" if not view.exposed else "unreadable")
        outcome, coverage = "unknown", ()
    elif signal.domain and set(view.coverage) != set(signal.domain):
        result = Result(kind="unknown", reason="incomplete_domain")
        outcome, coverage = "unknown", view.coverage
    else:
        result, coverage = template.result, view.coverage
        tx.require(signal.live or template.reference_end is None or template.reference_end <= tx.tick,
                   "A recorded observation cannot come from the future")
        if signal.projection == "location":
            tx.require(physical.accessible(tx, actor, template.subject), "Subject is inaccessible")
            result = Result(kind="exact", value=physical.location(tx, template.subject))
        outcome = result.kind
    proposition = replace(template, id=f"{evidence}:proposition", result=result,
                          reference_start=tx.tick if signal.live else template.reference_start,
                          reference_end=tx.tick if signal.live else template.reference_end)
    _new(tx, "propositions", proposition)
    record = Evidence(id=evidence, event_id=tx.event_id, observer=actor, fact=fact,
                      source=signal.carrier, proposition=proposition.id, acquired_at=tx.tick,
                      channel=channel, attention=attention, exposure=exposure, outcome=outcome,
                      coverage=coverage, actor_path=actor_path, source_path=source_path,
                      instrument_path=instrument_path, channel_path=channel_path,
                      source_ids=signal.source_ids or (signal.carrier,))
    _new(tx, "evidence", record)
    tx.emit(kind="inspection", evidence=evidence, observer=actor, source=signal.carrier,
            proposition=proposition.id, outcome=outcome)


def _channel_access(tx, channel, speaker, recipient, *, delivering=False):
    from . import physical

    ch = tx.get("channels", channel)
    tx.entity(speaker, "actor")
    tx.entity(recipient, "actor")
    tx.require(ch.kind in {"speech", "delayed"} and ch.enabled, "Unavailable communication channel")
    actor = recipient if delivering else speaker
    if ch.carrier is not None:
        tx.require(physical.accessible(tx, actor, ch.carrier), "Channel is inaccessible")
    if ch.kind == "speech":
        tx.require(physical.location(tx, speaker) == physical.location(tx, recipient)
                   and physical.accessible(tx, speaker, recipient), "Speech cannot reach recipient")
    return ch


def _understood(tx, comprehension, actor):
    understood = tx.get("comprehensions", comprehension)
    receipt = tx.get("claim_receipts", understood.receipt)
    claim = tx.get("claims", receipt.claim)
    tx.require(understood.actor == actor and receipt.recipient == actor,
               "Only the recipient can use understood content")
    _dependency(tx, understood)
    _dependency(tx, receipt)
    _dependency(tx, claim)
    return claim


def speak(tx, *, audience, channel, claim=None, evidence=None, belief=None, comprehension=None,
          attributed_source=None, attributed_reference_start=None, attributed_reference_end=None):
    actor = tx.action.actor
    claim = tx.event_id if claim is None else claim
    ch = _channel_access(tx, channel, actor, audience)
    tx.require(sum(v is not None for v in (evidence, belief, comprehension)) == 1,
               "A claim needs exactly one accessible stored basis")
    parents, evidence_ids = (), ()
    if evidence is not None:
        basis = tx.get("evidence", evidence)
        tx.require(basis.observer == actor, "Evidence belongs to another observer")
        _dependency(tx, basis)
        evidence_ids = (basis.id,)
    elif belief is not None:
        basis = tx.get("beliefs", belief)
        tx.require(basis.actor == actor, "Belief belongs to another actor")
        _dependency(tx, basis)
        evidence_ids = basis.evidence_ids
    else:
        basis = _understood(tx, comprehension, actor)
        parents, evidence_ids = (basis.id,), basis.evidence_ids
    tx.get("propositions", basis.proposition)
    _new(tx, "claims", Claim(
        id=claim, event_id=tx.event_id, speaker=actor, audience=audience,
        proposition=basis.proposition, emitted_at=tx.tick, available_at=tx.tick + ch.delay,
        channel=channel, source_ids=basis.source_ids, evidence_ids=evidence_ids,
        parents=parents, belief=belief, comprehension=comprehension, attributed_source=attributed_source,
        attributed_reference_start=attributed_reference_start,
        attributed_reference_end=attributed_reference_end))
    tx.emit(kind="assertion", claim=claim, speaker=actor, audience=audience)


def deliver(tx, *, claim, receipt=None):
    from . import physical

    receipt = tx.event_id if receipt is None else receipt
    message = tx.get("claims", claim)
    tx.require(message.audience == tx.action.actor and tx.tick >= message.available_at,
               "Wrong recipient or message not yet available")
    _channel_access(tx, message.channel, message.speaker, message.audience, delivering=True)
    _dependency(tx, message)
    _new(tx, "claim_receipts", Receipt(id=receipt, event_id=tx.event_id, claim=claim,
                                recipient=message.audience, received_at=tx.tick,
                                recipient_path=physical.path(tx, message.audience)))
    tx.emit(kind="delivery", claim=claim, receipt=receipt, recipient=message.audience)


def comprehend(tx, *, receipt, comprehension=None):
    comprehension = tx.event_id if comprehension is None else comprehension
    delivered = tx.get("claim_receipts", receipt)
    tx.require(delivered.recipient == tx.action.actor, "Only recipient can comprehend")
    _dependency(tx, delivered)
    _new(tx, "comprehensions", Comprehension(id=comprehension, event_id=tx.event_id,
                                            receipt=receipt, actor=tx.action.actor,
                                            understood_at=tx.tick))
    tx.emit(kind="comprehension", comprehension=comprehension, receipt=receipt)


def _basis(tx, evidence_ids, comprehension_ids):
    percepts, reports = [], []
    for key in evidence_ids:
        percept = tx.get("evidence", key)
        tx.require(percept.observer == tx.action.actor, "Cannot borrow another observer's evidence")
        _dependency(tx, percept)
        percepts.append(percept)
    for key in comprehension_ids:
        reports.append(_understood(tx, key, tx.action.actor))
    return percepts, reports


def _fresh_reports(get, policy, reports, decided_at):
    return tuple(r for r in reports if r.speaker == policy.source
                 and (p := get("propositions", r.proposition)).result.kind == "exact"
                 and p.reference_start is not None
                 and p.reference_end <= decided_at
                 and 0 <= decided_at - p.reference_start <= policy.max_age)


def _freshness_decision(get, policy, mode, percepts, reports, decided_at):
    """A single-topic, named report can authorize current use, never hidden truth."""
    if policy.kind != "freshness":
        return True
    if percepts or not reports or any(r.speaker != policy.source for r in reports):
        return False
    topics = {_key(get("propositions", r.proposition))[:3] for r in reports}
    if len(topics) != 1:
        return False
    return mode != "defer" or not _fresh_reports(get, policy, reports, decided_at)


def _support_sources(get, policy, target, percepts, reports, decided_at):
    def matches(key):
        proposition = get("propositions", key)
        return _key(proposition) == _key(target) and proposition.result == target.result

    if policy.kind == "percept":
        return tuple(sorted({s for p in percepts if p.outcome == "exact" and matches(p.proposition)
                             for s in p.source_ids}))
    if policy.kind == "testimony":
        return tuple(sorted({s for r in reports if r.speaker == policy.source and matches(r.proposition)
                             for s in r.source_ids}))
    if policy.kind == "freshness":
        if target.reference_start != decided_at or target.reference_end != decided_at:
            return ()
        return tuple(sorted({s for r in _fresh_reports(get, policy, reports, decided_at)
                             if _key(get("propositions", r.proposition))[:3] == _key(target)[:3]
                             and get("propositions", r.proposition).result == target.result
                             for s in r.source_ids}))
    if policy.kind == "authority":
        authority = get("authority_policies", policy.authority)
        signal = get("facts", authority.fact)
        if signal.assertion != authority.assertion:
            return ()
        if not matches(authority.assertion):
            return ()
        for reading in percepts:
            if reading.fact != authority.fact or reading.outcome != "exact":
                continue
            if not authority.valid_from <= reading.acquired_at <= authority.valid_until:
                continue
            for valid in percepts:
                if valid.fact != authority.validity_fact or valid.outcome != "exact":
                    continue
                vp = get("propositions", valid.proposition)
                if (vp.result.kind == "exact" and vp.result.value is True
                        and vp.reference_start is not None
                        and vp.reference_start <= reading.acquired_at <= vp.reference_end
                        and valid.acquired_at == reading.acquired_at):
                    return tuple(sorted(set(reading.source_ids)))
    return ()


def update_belief(tx, *, disposition, mode, head, policy, proposition=None,
                  predecessor=None, evidence_ids=(), comprehension_ids=()):
    """Single owner of belief versions and heads; duplicate decisions are no-ops."""
    tx.entity(tx.action.actor, "actor")
    tx.require(tx.maybe("dispositions", disposition) is None, "Disposition already committed")
    rule = tx.get("belief_policies", policy)
    tx.require(mode in rule.modes, "Policy does not authorize disposition")
    current = tx.maybe("belief_heads", head)
    prior = None
    if current is not None:
        tx.require(current.actor == tx.action.actor, "Belief head belongs to another actor")
        prior = tx.get("beliefs", current.belief)
        _dependency(tx, prior)
    tx.require(predecessor == (prior.id if prior else None), "Stale or missing predecessor")
    percepts, reports = _basis(tx, evidence_ids, comprehension_ids)
    tx.require(len(set(evidence_ids)) == len(evidence_ids)
               and len(set(comprehension_ids)) == len(comprehension_ids), "Duplicate basis")
    tx.require(_freshness_decision(tx.get, rule, mode, percepts, reports, tx.tick),
               "Freshness decision needs one named report topic; fresh support cannot be deferred")
    belief_id = None
    if mode in {"init", "adopt", "resolve"}:
        target = tx.get("propositions", proposition)
        tx.require(target.result.kind == "exact" and target.reference_start is not None,
                   "Unknown result/time cannot become an exact belief")
        if mode == "init":
            if prior is not None:
                old = tx.get("propositions", prior.proposition)
                tx.require(old.result.kind == "unknown" and _key(old)[:3] == _key(target)[:3]
                           and (old.reference_start is None or _key(old) == _key(target)),
                           "Initialization cannot replace an asserted belief")
            for other in tx.all("belief_heads"):
                if other.actor == tx.action.actor and other.id != head:
                    other_belief = tx.get("beliefs", other.belief)
                    tx.require(_key(tx.get("propositions", other_belief.proposition)) != _key(target),
                               "This actor already has a head for that proposition interval")
        else:
            tx.require(prior is not None, "A prior is required for adoption/resolution")
            old = tx.get("propositions", prior.proposition)
            tx.require(_key(old) == _key(target), "Different reference interval needs a distinct head")
            if mode == "adopt":
                tx.require(old.result == target.result, "Conflict needs explicit resolution")
            else:
                tx.require(old.result.kind == "exact" and old.result != target.result,
                           "Only an asserted prior can have a discrepancy")
        authored = rule.kind == "authored" and mode == "init" and not (percepts or reports)
        sources = _support_sources(tx.get, rule, target, percepts, reports, tx.tick)
        tx.require(authored or bool(sources),
                   "No policy-supported evidence for this proposition")
        if authored:
            sources = (tx.action.actor,)
        if prior is not None and mode == "adopt":
            sources = tuple(sorted(set(sources + prior.source_ids)))
            tx.require(bool(set(evidence_ids) - set(prior.evidence_ids)
                            or set(comprehension_ids) - set(prior.comprehension_ids)),
                       "Matching support already recorded")
        retained = prior if mode == "adopt" else None
        belief_id = f"{disposition}:belief"
        _new(tx, "beliefs", Belief(
            id=belief_id, actor=tx.action.actor, proposition=proposition, policy=policy,
            evidence_ids=tuple(dict.fromkeys((retained.evidence_ids if retained else ()) + tuple(evidence_ids))),
            comprehension_ids=tuple(dict.fromkeys((retained.comprehension_ids if retained else ())
                                                + tuple(comprehension_ids))),
            source_ids=sources, predecessor=predecessor, disposition=disposition, event_id=tx.event_id))
        tx.put("belief_heads", BeliefHead(id=head, actor=tx.action.actor, belief=belief_id))
    else:
        tx.require(mode in {"defer", "reject"} and bool(percepts or reports),
                   "Deferral/rejection needs an explicit basis and never asserts an opposite")
        tx.require(proposition is None, "Deferral/rejection does not assert a proposition")
    _new(tx, "dispositions", Disposition(
        id=disposition, event_id=tx.event_id, actor=tx.action.actor, mode=mode,
        head=head, policy=policy, proposition=proposition, predecessor=predecessor,
        belief=belief_id, evidence_ids=tuple(evidence_ids),
        comprehension_ids=tuple(comprehension_ids), decided_at=tx.tick))
    tx.emit(kind="belief_disposition", disposition=disposition, mode=mode, head=head,
            belief=belief_id, predecessor=predecessor)


def _validate(state):
    def require(condition, message):
        if not condition:
            raise CapabilityError(message)

    def get(table, key):
        result = state.get(table, key)
        require(result is not None, f"Unknown {table}/{key}")
        return result

    def entity(key, kind=None):
        ent = get("entities", key)
        require(kind is None or ent.kind == kind, "Epistemic entity role mismatch")

    def time(value):
        return type(value) is int and value >= 0

    def interval(start, end):
        require((start is None and end is None) or
                (time(start) and time(end) and start <= end), "Ambiguous reference interval")

    def path(path_ids, first):
        require(isinstance(path_ids, tuple) and path_ids and path_ids[0] == first
                and len(set(path_ids)) == len(path_ids), "Invalid historical access path")
        for key in path_ids:
            entity(key)
        entity(path_ids[-1], "place")

    def acyclic(table, parents):
        done = set()
        for row in state.tables[table].values():
            pending, visiting = [(row.id, False)], set()
            while pending:
                key, leaving = pending.pop()
                if leaving:
                    visiting.remove(key)
                    done.add(key)
                elif key not in done:
                    require(key not in visiting, f"Cyclic {table} provenance")
                    visiting.add(key)
                    pending.append((key, True))
                    pending.extend((p, False) for p in parents(get(table, key)))

    for p in state.tables["propositions"].values():
        entity(p.subject)
        require(isinstance(p.predicate, str) and isinstance(p.scope, str)
                and bool(p.predicate and p.scope), "Proposition needs predicate and scope")
        interval(p.reference_start, p.reference_end)
        r = p.result
        require(type(r) is Result and r.kind in {"exact", "partial", "unknown"}
                and isinstance(r.alternatives, tuple)
                and (r.reason is None or isinstance(r.reason, str)), "Invalid result")
        scalar = lambda v: type(v) in {str, bool, int, float} and (type(v) is not float or math.isfinite(v))
        if r.kind == "exact":
            require(scalar(r.value) and not r.alternatives and r.reason is None, "Invalid exact result")
        elif r.kind == "partial":
            require(r.value is None and len(r.alternatives) >= 2 and all(map(scalar, r.alternatives)),
                    "Partial evidence needs finite visible alternatives")
            require(len({(type(v), v) for v in r.alternatives}) == len(r.alternatives),
                    "Partial alternatives must be distinct")
        else:
            require(r.value is None and not r.alternatives and bool(r.reason), "Unknown is not false/zero")
    for f in state.tables["facts"].values():
        entity(f.carrier)
        p = get("propositions", f.proposition)
        require(f.projection in {"signal", "location"} and type(f.live) is bool, "Unknown signal projection")
        require(f.projection != "location" or (f.live and not f.assertion), "Location is a live physical projection")
        require(len(set(f.domain)) == len(f.domain) and all(isinstance(v, str) and v for v in f.domain),
                "Signal needs a finite unique domain")
        if f.assertion is not None:
            assertion = get("propositions", f.assertion)
            require(_key(assertion) != _key(p), "Inscription and assertion must be distinct propositions")
        require(len(set(f.source_ids)) == len(f.source_ids), "Duplicate underlying sources")
        for source in f.source_ids:
            entity(source)
        require(f.live or p.reference_start is not None or p.result.kind != "exact",
                "A recorded exact signal needs explicit reference time")
    for e in state.tables["exposures"].values():
        f = get("facts", e.fact)
        require(type(e.exposed) is bool and type(e.readable) is bool
                and len(set(e.coverage)) == len(e.coverage) and set(e.coverage) <= set(f.domain),
                "Invalid exposure coverage")
    for c in state.tables["channels"].values():
        require(c.kind in {"observation", "speech", "delayed"} and type(c.enabled) is bool
                and time(c.delay) and c.delay <= 200 and (c.kind == "delayed" or c.delay == 0),
                "Invalid bounded channel")
        for carrier in (c.carrier, c.instrument):
            if carrier is not None:
                entity(carrier)
    for a in state.tables["attention"].values():
        entity(a.actor, "actor")
        entity(a.source)
        require(get("channels", a.channel).kind == "observation" and time(a.until), "Invalid attention")
    for a in state.tables["authority_policies"].values():
        signal = get("facts", a.fact)
        get("facts", a.validity_fact)
        get("propositions", a.assertion)
        interval(a.valid_from, a.valid_until)
        require(a.kind in {"ledger", "exposure_identity"} and a.valid_from is not None
                and a.fact != a.validity_fact and signal.assertion == a.assertion,
                "Authority must be an exact authored assertion and independent validity signal")
    for p in state.tables["belief_policies"].values():
        require(p.kind in {"percept", "testimony", "authority", "authored", "defer", "freshness"}
                and p.modes and set(p.modes) <= {"init", "adopt", "resolve", "defer", "reject"},
                "Invalid disposition policy")
        if p.kind == "authored":
            require(set(p.modes) <= {"init"}, "Authored assumptions cannot authorize revision")
        if p.kind in {"testimony", "freshness"}:
            entity(p.source, "actor")
        if p.kind == "freshness":
            require(type(p.max_age) is int and 0 <= p.max_age <= 200
                    and set(p.modes) <= {"init", "adopt", "resolve", "defer"},
                    "Freshness policy needs a bounded maximum age and supported modes")
        else:
            require(p.max_age is None, "Only freshness policies have a maximum age")
        if p.kind == "authority":
            get("authority_policies", p.authority)
    for e in state.tables["evidence"].values():
        entity(e.observer, "actor")
        f = get("facts", e.fact)
        p = get("propositions", e.proposition)
        focus = get("attention", e.attention)
        view = get("exposures", e.exposure)
        require(e.source == f.carrier and bool(e.source_ids) and not e.parents
                and focus.actor == e.observer and focus.source == e.source and focus.channel == e.channel
                and view.fact == e.fact and get("channels", e.channel).kind == "observation",
                "Invalid inspection lineage")
        require(time(e.acquired_at) and e.acquired_at <= state.tick
                and e.outcome in {"exact", "partial", "unknown", "inaccessible"}
                and p.result.kind == ("unknown" if e.outcome == "inaccessible" else e.outcome)
                and set(e.coverage) <= set(f.domain), "Invalid inspection result/time")
        require(bool(e.event_id) and focus.until >= e.acquired_at, "Inspection needs event-time attention")
        path(e.actor_path, e.observer)
        path(e.source_path, e.source)
        ch = get("channels", e.channel)
        for witness, first in ((e.instrument_path, ch.instrument), (e.channel_path, ch.carrier)):
            if first is not None:
                path(witness, first)
            else:
                require(not witness, "Unexpected channel/instrument witness")
        for source in e.source_ids:
            entity(source)
    for c in state.tables["claims"].values():
        entity(c.speaker, "actor")
        entity(c.audience, "actor")
        get("propositions", c.proposition)
        ch = get("channels", c.channel)
        require(time(c.emitted_at) and time(c.available_at) and c.emitted_at <= c.available_at
                and c.emitted_at <= state.tick and c.available_at == c.emitted_at + ch.delay
                and ch.kind in {"speech", "delayed"} and bool(c.event_id) and bool(c.source_ids),
                "Invalid claim time/lineage")
        interval(c.attributed_reference_start, c.attributed_reference_end)
        for source in c.source_ids:
            entity(source)
        for key in c.evidence_ids:
            get("evidence", key)
        for key in c.parents:
            parent = get("claims", key)
            require(parent.emitted_at <= c.emitted_at and parent.id != c.id
                    and parent.proposition == c.proposition and parent.source_ids == c.source_ids,
                    "Claim cannot launder provenance or reference time")
        if c.belief is not None:
            b = get("beliefs", c.belief)
            require(b.actor == c.speaker and b.proposition == c.proposition
                    and b.source_ids == c.source_ids and b.evidence_ids == c.evidence_ids
                    and not c.parents and c.comprehension is None,
                    "Invalid belief claim")
        elif c.parents:
            require(len(c.parents) == 1 and get("claims", c.parents[0]).evidence_ids == c.evidence_ids,
                    "Forwarded claim changes evidence lineage")
            understood = get("comprehensions", c.comprehension)
            receipt = get("claim_receipts", understood.receipt)
            require(understood.actor == c.speaker and receipt.recipient == c.speaker
                    and receipt.claim == c.parents[0] and understood.understood_at <= c.emitted_at,
                    "Forwarding needs the speaker's actual comprehension")
        else:
            require(len(c.evidence_ids) == 1 and c.comprehension is None,
                    "Claim has no accessible stored basis")
            e = get("evidence", c.evidence_ids[0])
            require(e.observer == c.speaker and e.proposition == c.proposition
                    and e.source_ids == c.source_ids and e.acquired_at <= c.emitted_at,
                    "Claim cannot launder percept provenance or time")
    for r in state.tables["claim_receipts"].values():
        c = get("claims", r.claim)
        require(r.recipient == c.audience and time(r.received_at)
                and c.available_at <= r.received_at <= state.tick
                and bool(r.event_id) and r.recipient_path and r.recipient_path[0] == r.recipient,
                "Invalid delivery receipt")
        path(r.recipient_path, r.recipient)
    for c in state.tables["comprehensions"].values():
        r = get("claim_receipts", c.receipt)
        require(c.actor == r.recipient and time(c.understood_at)
                and r.received_at <= c.understood_at <= state.tick
                and bool(c.event_id), "Invalid comprehension")
    for b in state.tables["beliefs"].values():
        entity(b.actor, "actor")
        p = get("propositions", b.proposition)
        policy = get("belief_policies", b.policy)
        for key in b.evidence_ids:
            require(get("evidence", key).observer == b.actor, "Belief borrows inaccessible evidence")
        for key in b.comprehension_ids:
            require(get("comprehensions", key).actor == b.actor, "Belief borrows comprehension")
        if b.predecessor is not None:
            prior = get("beliefs", b.predecessor)
            old = get("propositions", prior.proposition)
            require(prior.actor == b.actor and prior.id != b.id
                    and (_key(old) == _key(p) or (old.result.kind == "unknown"
                         and old.reference_start is None and _key(old)[:3] == _key(p)[:3])),
                    "Invalid belief predecessor")
        if b.disposition is not None:
            require(get("dispositions", b.disposition).belief == b.id, "Unowned belief write")
        require((b.event_id is None) == (b.disposition is None), "Belief event/disposition mismatch")
        if b.event_id is None:
            require(policy.kind == "authored" and not b.evidence_ids and not b.comprehension_ids
                    and b.predecessor is None and b.source_ids == (b.actor,),
                    "Initial assumptions need an explicit authored policy, not invented percepts")
        require(bool(b.source_ids) and len(set(b.source_ids)) == len(b.source_ids), "Belief needs finite source provenance")
        for source in b.source_ids:
            entity(source)
    active_slots = set()
    for h in state.tables["belief_heads"].values():
        b = get("beliefs", h.belief)
        require(b.actor == h.actor, "Belief head actor mismatch")
        slot = (h.actor, _key(get("propositions", b.proposition)))
        require(slot not in active_slots, "Duplicate active belief head for one proposition interval")
        active_slots.add(slot)
    for d in state.tables["dispositions"].values():
        entity(d.actor, "actor")
        p = get("belief_policies", d.policy)
        require(d.mode in p.modes and time(d.decided_at) and d.decided_at <= state.tick
                and bool(d.event_id), "Invalid disposition")
        for key in d.evidence_ids:
            e = get("evidence", key)
            require(e.observer == d.actor and e.acquired_at <= d.decided_at,
                    "Disposition borrows inaccessible/future evidence")
        for key in d.comprehension_ids:
            c = get("comprehensions", key)
            require(c.actor == d.actor and c.understood_at <= d.decided_at,
                    "Disposition borrows inaccessible/future comprehension")
        percepts = [get("evidence", key) for key in d.evidence_ids]
        reports = [get("claims", get("claim_receipts", get("comprehensions", key).receipt).claim)
                   for key in d.comprehension_ids]
        require(_freshness_decision(get, p, d.mode, percepts, reports, d.decided_at),
                "Invalid freshness disposition")
        if d.belief is not None:
            b = get("beliefs", d.belief)
            require(b.actor == d.actor and b.predecessor == d.predecessor
                    and b.proposition == d.proposition and b.event_id == d.event_id
                    and b.policy == d.policy and d.mode in {"init", "adopt", "resolve"},
                    "Invalid disposition result")
            require(bool(d.evidence_ids or d.comprehension_ids) or
                    (p.kind == "authored" and d.mode == "init"), "Unsupported belief write")
            target = get("propositions", d.proposition)
            authored = p.kind == "authored" and d.mode == "init" and not (percepts or reports)
            sources = _support_sources(get, p, target, percepts, reports, d.decided_at)
            require(target.result.kind == "exact" and target.reference_start is not None
                    and (authored or bool(sources)),
                    "Belief disposition lacks policy-supported evidence")
            if authored:
                sources = (d.actor,)
            if d.mode != "init":
                prior = get("beliefs", d.predecessor)
                old = get("propositions", prior.proposition)
                require(_key(old) == _key(target), "Reference interval changed during revision")
                require((old.result == target.result if d.mode == "adopt" else
                         old.result.kind == "exact" and old.result != target.result),
                        "Adoption is not conflict resolution; unknown prior is not a mistake")
                if d.mode == "adopt":
                    sources = tuple(sorted(set(sources + prior.source_ids)))
            require(b.source_ids == sources, "Context is not independent supporting provenance")
        else:
            require(d.mode in {"defer", "reject"} and d.proposition is None
                    and bool(d.evidence_ids or d.comprehension_ids),
                    "Only deferral/rejection can leave belief unchanged")
    acyclic("beliefs", lambda b: (b.predecessor,) if b.predecessor else ())
    acyclic("claims", lambda c: c.parents)
    # Evidence/versions remain immutable even when another domain writes a table.
    immutable = {"propositions", "evidence", "claims", "claim_receipts", "comprehensions",
                 "beliefs", "dispositions"}
    for event in state.events:
        for change in event.changes:
            if change.table in immutable:
                require(state.get(change.table, change.key) == change.after,
                        "Epistemic history is immutable")


def _intent(state, actor, query):
    if query.table not in {"beliefs", "belief_heads"}:
        return False
    record = state.get(query.table, query.key)
    return record is not None and record.actor == actor


OPERATIONS = {
    "attend": attend, "observe": observe, "speak": speak, "deliver": deliver,
    "comprehend": comprehend, "update_belief": update_belief,
}


def register(registry):
    for table, record in TABLES.items():
        registry.table(table, record)
    # Conservative contracts include insert checks and read-tracked physical helpers.
    physical_reads = {"entities", "parents", "containers"}
    contracts = {
        "attend": ({"entities", "channels", "attention"}, {"attention"}),
        "observe": (physical_reads | {"facts", "exposures", "channels", "attention", "propositions", "evidence"},
                    {"propositions", "evidence"}),
        "speak": (physical_reads | {"channels", "evidence", "beliefs", "comprehensions", "claim_receipts", "claims", "propositions"},
                  {"claims"}),
        "deliver": (physical_reads | {"channels", "claims", "claim_receipts"}, {"claim_receipts"}),
        "comprehend": ({"claim_receipts", "comprehensions"}, {"comprehensions"}),
        "update_belief": ({"entities", "dispositions", "belief_policies", "belief_heads", "beliefs", "evidence",
                           "comprehensions", "claim_receipts", "claims", "propositions", "authority_policies", "facts"},
                          {"beliefs", "belief_heads", "dispositions"}),
    }
    for name, handler in OPERATIONS.items():
        reads, writes = contracts[name]
        registry.operation(name, handler, reads=reads, writes=writes)
    registry.validators.append(_validate)
    registry.initial_validators.append(validate_initial)
    registry.intent_validators.append(_intent)
