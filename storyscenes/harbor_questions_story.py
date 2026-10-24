"""Four requests whose continuation depends on acquired, not hidden, evidence.

These are authored bounded stories over the shared capability laws. The policy
is not a general character planner. Initial assumptions may be wrong; only the
existing epistemic writer can revise them. No runtime language model is used.
"""
from dataclasses import asdict, dataclass, replace
import argparse
import json
import random

from .capabilities.api import registry as base_registry
from .capabilities.core import Action, CapabilityError, Entity, Query, Record, WorldSpec, execute, fingerprint, plain, replay
from .capabilities.epistemic import Attention, Belief, BeliefHead, BeliefPolicy, Channel, Exposure, Fact, Proposition, Result
from .capabilities.physical import Container, Ownership, Parent, Route
from .capabilities.reading import Reader
from .capabilities.social import ActionSpec

KINDS = ("load", "parcel", "shortcut", "tool")


@dataclass(frozen=True, kw_only=True)
class Job(Record):
    kind: str
    prior_commitment: bool = False
    keep_promise_first: bool = True
    attempt_first: bool = False
    recover: bool = False


@dataclass(frozen=True, kw_only=True)
class Resolution(Record):
    kind: str
    outcome: str
    event_id: str


def understood_value(state):
    from .harbor_recovery import decision
    disposition = decision(state)
    if disposition.mode == "defer":
        return None
    head = state.get("belief_heads", "ari_view")
    belief = state.get("beliefs", head.belief)
    return state.get("propositions", belief.proposition).result.value


def finish(tx):
    job, req = tx.get("harbor_jobs", "ari"), tx.get("requests", "help")
    tx.require(tx.action.actor == ("cy" if job.kind == "shortcut" else "ari")
               and tx.maybe("harbor_resolutions", "end") is None, "One resolution at the task's endpoint is allowed")
    from .harbor_recovery import decision, require_divided_load
    tx.depend(decision(tx).event_id)
    value = understood_value(tx)
    where = tx.get("parents", "crate").parent
    settled_prior_promise(tx, job)
    if req.response == "declined":
        tx.depend(req.response_event)
        tx.require(job.prior_commitment and job.keep_promise_first and value is True,
                   "This refusal must follow a confirmed need and the earlier commitment")
        if job.kind == "parcel":
            tx.require(where == "boat", "Ari must actually load the cups after the refusal")
            tx.depend("self_load:1")
            outcome = "self_loaded"
        elif job.kind == "load" and job.recover:
            require_divided_load(tx)
            outcome = "divided_after_refusal"
        else:
            tx.require(job.kind == "load" and where == "workshop", "No invented completion after refusal")
            outcome = "waiting_for_help"
    elif job.kind == "shortcut":
        tx.require(req.completion_receipt is not None and where == "jetty", "The parcel must actually arrive")
        outcome = "bridge" if value else "known_lane" if value is None else "long_way"
    elif value is None:
        tx.require(req.withdrawal_event is not None and where == "workshop", "Uncertainty must leave the task unperformed")
        outcome = "deferred"
    elif value:
        tx.require(req.completion_receipt is not None, "Acceptance is not performance")
        if job.kind == "tool":
            tx.require(tx.get("containers", "crate").open and where == "bench", "The parcel must be opened and placed")
        else:
            tx.require(where == ("cart" if job.kind == "load" else "boat"), "Wrong final destination")
        outcome = "help_completed"
    else:
        tx.require(req.withdrawal_event is not None and where == "bench", "A changed plan needs its actual alternative")
        if job.kind == "tool":
            tx.require(tx.get("containers", "crate").open, "The knot must actually be opened")
        outcome = {"load": "carried_alone", "parcel": "kept_for_sign", "tool": "untied"}[job.kind]
    if req.completion_receipt:
        tx.depend(tx.get("receipts", req.completion_receipt).event_id)
    elif req.withdrawal_event:
        tx.depend(req.withdrawal_event)
    tx.put("harbor_resolutions", Resolution(id="end", kind=job.kind, outcome=outcome, event_id=tx.event_id))
    tx.emit(kind=job.kind, outcome=outcome)


def settled_prior_promise(tx, job):
    if job.prior_commitment:
        promise = tx.get("promises", "key_return")
        tx.require(promise.status in {"fulfilled", "breached"} and tx.get("parents", "key").parent == "bo",
                   "The earlier promise needs assessed, actual performance")
        tx.depend(promise.assessment_event)
        if promise.status == "breached":
            tx.require(promise.repair_receipt is not None, "Record the actual late return separately from fulfillment")


def registry():
    reg = base_registry()
    reg.table("harbor_jobs", Job)
    reg.table("harbor_resolutions", Resolution)
    def validate(state):
        jobs = state.tables["harbor_jobs"]
        if set(jobs) != {"ari"} or jobs["ari"].kind not in KINDS:
            raise CapabilityError("One declared job embedded in Ari is required")
        if state.get("entities", "ari").kind != "actor":
            raise CapabilityError("The job needs a physical actor")
        for r in state.tables["harbor_resolutions"].values():
            if r.id != "end" or r.kind != jobs["ari"].kind or not r.event_id:
                raise CapabilityError("Invalid job resolution")
    def initial(state):
        if state.tables["harbor_resolutions"]:
            raise CapabilityError("Resolution must be enacted")
    reg.validators.append(validate)
    reg.initial_validators.append(initial)
    reg.operation("resolve_harbor_question", finish,
        reads={"harbor_jobs", "harbor_resolutions", "requests", "dispositions", "belief_heads",
               "beliefs", "propositions", "parents", "containers", "receipts", "promises"}, writes={"harbor_resolutions"})
    from .harbor_attempts import register
    register(reg)
    return reg


@dataclass(frozen=True, kw_only=True)
class Conditions:
    kind: str = "load"
    actual: bool = False
    readable: bool = True
    reported: bool = False
    prior_commitment: bool = False
    keep_promise_first: bool = True
    attempt_first: bool = False
    recover: bool = False

    def __post_init__(self):
        if self.kind not in KINDS or any(type(v) is not bool for v in
                (self.actual, self.readable, self.reported, self.prior_commitment, self.keep_promise_first, self.attempt_first, self.recover)):
            raise ValueError("Use a declared request kind and Boolean conditions")


def conditions(seed):
    rng = random.Random(seed)
    return Conditions(kind=KINDS[seed % len(KINDS)], actual=rng.random() < .5,
                      readable=rng.random() < .9, reported=rng.random() < .5,
                      prior_commitment=rng.random() < .65, keep_promise_first=rng.random() < .5,
                      attempt_first=rng.random() < .5, recover=True)


def build(c):
    def q(table, key, field, value, op="eq"):
        return Query(table=table, key=key, field=field, value=value, op=op)
    names = {"load": "the large crate", "parcel": "the picnic box", "shortcut": "the parcel", "tool": "the tied parcel"}
    entities = [Entity(id="ari", name="Ari", kind="actor", capacity=12),
                Entity(id="cy", name="Cy", kind="actor", capacity=40)]
    entities += [Entity(id=k, name=n, kind="place") for k, n in
                 (("workshop", "the harbor workshop"), ("jetty", "the jetty"), ("lane", "the lane past the sheds"))]
    entities += [Entity(id=k, name=n, kind="container", capacity=50, mass=2) for k, n in
                 (("crate", names[c.kind]), ("cart", "the handcart"), ("bench", "the workbench"), ("boat", "the picnic boat"))]
    entities += [Entity(id="scissors", name="the scissors", kind="object"),
                 Entity(id="clue", name={"load": "the stone slabs" if c.actual else "the wooden crate bottom",
                     "parcel": "the paper cups" if c.actual else "the paint tins",
                     "shortcut": "the footbridge barrier", "tool": "the parcel fastening"}[c.kind], kind="object",
                     mass=20 if c.kind == "load" and c.actual else 0)]
    if c.kind == "tool":
        entities.append(Entity(id="paper", name="the folded paper flags", kind="object"))
    if c.kind == "parcel":
        entities.append(Entity(id="sign", name="the unfinished harbor sign", kind="object"))
    if not c.readable:
        entities.append(Entity(id="cover", name="the fog" if c.kind == "shortcut" else "the inner wrapping", kind="object", mass=0))
    parents = [Parent(id=k, parent="workshop") for k in ("ari", "cy", "crate", "cart", "bench", "boat")]
    parents += [Parent(id="scissors", parent="cy"), Parent(id="clue", parent="crate" if c.kind in {"load", "parcel"} else "workshop")]
    if c.kind == "tool":
        parents.append(Parent(id="paper", parent="crate"))
    if c.kind == "parcel":
        parents.append(Parent(id="sign", parent="bench"))
    if not c.readable:
        parents.append(Parent(id="cover", parent="workshop"))
    containers = tuple(Container(id=k, open=k != "crate", latchable=k == "crate",
                                 latched=k == "crate" and c.kind == "tool" and c.actual)
                       for k in ("crate", "cart", "bench", "boat"))
    propositions = tuple(Proposition(id=k, subject="crate" if c.kind != "shortcut" else "clue",
        predicate={"load": "contains stone slabs", "parcel": "contains picnic cups", "shortcut": "footbridge is open",
                   "tool": "fastening needs scissors"}[c.kind], scope="initial_job_condition",
        result=Result(kind="exact", value=value), reference_start=0, reference_end=0)
        for k, value in (("assumption", True), ("actual", c.actual)))
    records = dict(entities=tuple(entities), parents=tuple(parents), containers=containers,
        harbor_jobs=(Job(id="ari", kind=c.kind, prior_commitment=c.prior_commitment,
                        keep_promise_first=c.keep_promise_first, attempt_first=c.attempt_first, recover=c.recover),), propositions=propositions,
        facts=(Fact(id="check", carrier="clue", proposition="actual"),),
        exposures=(Exposure(id="view", fact="check", exposed=c.readable),),
        channels=(Channel(id="eyes", kind="observation"), Channel(id="voice", kind="speech")),
        attention=tuple(Attention(id=a, actor=a, source="clue", channel="eyes", until=10) for a in ("ari", "cy")),
        belief_policies=(BeliefPolicy(id="premise", kind="authored", modes=("init",)),
                         BeliefPolicy(id="look", kind="percept"), BeliefPolicy(id="trust_cy", kind="testimony", source="cy"),
                         BeliefPolicy(id="wait", kind="defer", modes=("defer",))),
        beliefs=(Belief(id="prior", actor="ari", proposition="assumption", policy="premise", source_ids=("ari",)),),
        belief_heads=(BeliefHead(id="ari_view", actor="ari", belief="prior"),),
        routes=(Route(id="bridge", source="workshop", destination="jetty", open=c.actual),
                Route(id="lane", source="workshop", destination="lane"), Route(id="round", source="lane", destination="jetty")),
        action_specs=(ActionSpec(id="help", actor="cy", operation="handoff" if c.kind == "tool" else "put",
            object="scissors" if c.kind == "tool" else "crate", recipient="ari" if c.kind == "tool" else None,
            destination={"load": "cart", "parcel": "boat", "shortcut": "jetty", "tool": "ari"}[c.kind],
            terms=f"requested_{c.kind}", version=1, checkpoint=10),))
    actions = []
    def add(action_id, operation, actor, *, requires=(), **args):
        actions.append(Action(id=action_id, operation=operation, actor=actor, args=args, requires=requires))
    add("ask", "create_request", "ari", request="help", responder="cy", action_spec="help", version=1)
    add("request", "deliver_request", "ari", request="help", version=1)
    add("acknowledge", "acknowledge_request", "cy", request="help", version=1)
    if c.kind in {"load", "parcel"}:
        add("open_view", "set_container", "cy" if c.reported else "ari", container="crate", open=True,
            requires=(q("requests", "help", "delivery_event", None, "ne"),))
    observer = "cy" if c.reported else "ari"
    add("inspect", "observe", observer, fact="check", exposure="view", attention=observer, channel="eyes", evidence="seen", attempt=True,
        requires=(q("requests", "help", "delivery_event", None, "ne"),))
    add("explain", "speak", "cy", audience="ari", channel="voice", evidence="seen", claim="explanation")
    add("hear", "deliver", "ari", claim="explanation", receipt="heard")
    add("understand", "comprehend", "ari", receipt="heard", comprehension="understood")
    basis = dict(comprehension_ids=("understood",)) if c.reported else dict(evidence_ids=("seen",))
    for mode in ("adopt", "resolve", "defer"):
        add(mode, "update_belief", "ari", disposition="decision", head="ari_view", predecessor="prior", mode=mode,
            policy="wait" if mode == "defer" else "trust_cy" if c.reported else "look",
            **({} if mode == "defer" else dict(proposition="seen:proposition")), **basis)
    known = (q("dispositions", "decision", "mode", ("adopt", "resolve"), "in"),)
    add("say_decision", "speak", "ari", audience="cy", channel="voice", claim="decision_reply", belief="decision:belief", requires=known)
    add("say_uncertain", "speak", "ari", audience="cy", channel="voice", claim="decision_reply",
        **(dict(comprehension="understood") if c.reported else dict(evidence="seen")),
        requires=(q("dispositions", "decision", "mode", "defer"),))
    add("cy_hears", "deliver", "cy", claim="decision_reply", receipt="cy_heard")
    add("cy_understands", "comprehend", "cy", receipt="cy_heard", comprehension="cy_understood")
    reply = (q("comprehensions", "cy_understood", "actor", "cy"),)
    if c.kind == "shortcut" or c.prior_commitment:
        records["propositions"] += (Proposition(id="known_lane", subject="lane", predicate="passable route to jetty",
            scope="authored_route_knowledge", result=Result(kind="exact", value=True), reference_start=0, reference_end=0),)
        records["beliefs"] += (Belief(id="cy_lane", actor="cy", proposition="known_lane", policy="premise", source_ids=("cy",)),)
        records["belief_heads"] += (BeliefHead(id="cy_lane", actor="cy", belief="cy_lane"),)
    lane_known = (q("belief_heads", "cy_lane", "belief", "cy_lane"),
                  q("propositions", "known_lane", "result", Result(kind="exact", value=True))) if c.kind == "shortcut" or c.prior_commitment else ()
    confirmed = known + (q("propositions", "seen:proposition", "result", Result(kind="exact", value=True)),)
    priority = (q("harbor_jobs", "ari", "keep_promise_first", False),) if c.prior_commitment and c.kind in {"load", "parcel"} else ()
    add("accept", "respond_request", "cy", request="help", version=1, decision="accepted",
        requires=(lane_known if c.kind == "shortcut" else confirmed) + reply + priority)
    add("withdraw", "withdraw_request", "ari", request="help", version=1,
        requires=(q("dispositions", "decision", "mode", ("resolve", "defer"), "in"), *reply))
    accepted = (q("requests", "help", "response", "accepted"),)
    withdrawn = (q("requests", "help", "withdrawal_event", None, "ne"),)
    work_elapsed = (q("clock", "clock", "tick", tuple(range(3, 8)), "in"),) if c.prior_commitment and c.kind in {"load", "parcel"} else ()
    for actor in ("ari", "cy"):
        add(f"{actor}_take", "pickup", actor, object="crate", source="workshop", requires=accepted + work_elapsed if actor == "cy" else withdrawn)
    for destination in ("cart", "boat", "jetty"):
        add(f"place_{destination}", "put", "cy", object="crate", destination=destination, requires=accepted)
    add("alternative", "put", "ari", object="crate", destination="bench", requires=withdrawn)
    for route in ("bridge", "lane", "round"):
        knowledge = (q("propositions", "seen:proposition", "result", Result(kind="exact", value=True)),) if route == "bridge" else lane_known
        add(route, "travel", "cy", route=route, requires=accepted + knowledge)
    add("ready", "readiness", "ari", id="ready", giver="cy", object="scissors", requires=accepted)
    add("give", "handoff", "cy", object="scissors", recipient="ari", readiness_id="ready", requires=accepted)
    add("complete", "complete_request", "cy", request="help", version=1,
        receipt={"load": "place_cart:1", "parcel": "place_boat:1", "shortcut": "place_jetty:1", "tool": "give:1"}[c.kind])
    for id, latched, guard in (("cut", True, (q("parents", "scissors", "parent", "ari"),)), ("untie", False, withdrawn)):
        add(id, "set_container", "ari", container="crate", open=True,
            requires=(q("containers", "crate", "latched", latched), *guard, *known))
    add("take_opened", "pickup", "ari", object="crate", source="workshop", requires=(q("containers", "crate", "open", True), *known))
    add("place_opened", "put", "ari", object="crate", destination="bench", requires=known)
    if c.prior_commitment:
        records["entities"] += (Entity(id="bo", name="Bo", kind="actor", capacity=20),
                                Entity(id="key", name="Bo's brass key", kind="object"))
        records["parents"] += (Parent(id="bo", parent="workshop"), Parent(id="key", parent="cy"))
        records["ownership"] = (Ownership(id="key", owner="bo"),)
        records["action_specs"] += (ActionSpec(id="key_return", actor="cy", operation="handoff", object="key",
            recipient="bo", destination="bo", terms="return_key_by_bell", version=1, checkpoint=3),)
        add("prior_promise", "make_promise", "cy", promise="key_return", beneficiary="bo", action_spec="key_return", version=1)
        for route in ("lane", "round"):
            add(f"bo_{route}", "travel", "bo", route=route)
            add(f"key_{route}", "travel", "cy", route=route, requires=lane_known)
        for tick in range(1, 8):
            add(f"time_{tick}", "advance_time", "cy", to_tick=tick)
        add("key_ready", "readiness", "bo", id="key_ready", giver="cy", object="key")
        add("key_return", "handoff", "cy", object="key", recipient="bo", readiness_id="key_ready")
        add("key_assess", "assess_promise", "bo", promise="key_return", version=1)
        add("key_late", "record_late_repair", "cy", promise="key_return", version=1, receipt="key_return:1")
        declined = (q("requests", "help", "response", "declined"),)
        if c.kind in {"load", "parcel"}:
            add("refuse", "respond_request", "cy", request="help", version=1, decision="declined", reason_kind="unwillingness",
                requires=confirmed + reply + (q("promises", "key_return", "status", "active"),
                    q("harbor_jobs", "ari", "keep_promise_first", True)))
            actions[-1] = replace(actions[-1], reason="I promised Bo the key by the bell. I will keep that promise first.",
                                  reason_support=("prior_promise:1",))
        if c.kind == "parcel":
            add("self_take", "pickup", "ari", object="crate", source="workshop", requires=declined + confirmed)
            add("self_load", "put", "ari", object="crate", destination="boat", requires=declined + confirmed)
    add("finish", "resolve_harbor_question", "cy" if c.kind == "shortcut" else "ari")
    spec = WorldSpec(title="Before saying yes", records=records, actions=tuple(actions),
                     goal=(q("harbor_resolutions", "end", "kind", c.kind),))
    if c.attempt_first:
        from .harbor_attempts import extend
        spec = extend(spec, c)
    if c.recover:
        from .harbor_recovery import extend
        spec = extend(spec, c)
    return spec


def generate(seed=0, *, config=None, prose_seed=None):
    from .harbor_questions_prose import render
    c = conditions(seed) if config is None else config
    spec, reg = build(c), registry()
    if c.attempt_first:
        from .harbor_attempts import generate_attempt
        return generate_attempt(seed, c, spec, reg)
    state = reg.initial(spec)
    actions = {a.id: a for a in spec.actions}
    def do(id):
        nonlocal state
        after = execute(reg, spec, state, actions[id])
        if after is None:
            raise ValueError(f"Illegal authored continuation: {id}")
        state = after
        return state
    def time(tick):
        if tick > state.tick:
            do(f"time_{tick}")
    if c.prior_commitment:
        for id in ("prior_promise", "bo_lane", "bo_round"):
            do(id)
    do("ask")
    do("request")
    do("acknowledge")
    if c.kind in {"load", "parcel"}:
        do("open_view")
    do("inspect")
    if c.reported:
        for id in ("explain", "hear", "understand"):
            do(id)
    evidence = state.get("evidence", "seen")
    result = state.get("propositions", evidence.proposition).result
    do("defer" if result.kind != "exact" else "adopt" if result.value is True else "resolve")
    from .harbor_recovery import second_look, divide, decision
    state = second_look(c, state, do)
    value = understood_value(state)
    kind = state.get("harbor_jobs", "ari").kind
    for id in (("say_uncertain" if value is None else "say_decision"), "cy_hears", "cy_understands"):
        do(id)
    if c.prior_commitment:
        time(1)
    refuses = c.prior_commitment and c.keep_promise_first and value is True and kind in {"load", "parcel"}
    if refuses:
        do("refuse")
        if kind == "parcel":
            do("self_take")
            do("self_load")
        elif c.recover:
            divide(do)
    elif value is None and kind != "shortcut":
        do("withdraw")
    elif value or kind == "shortcut":
        do("accept")
        if c.prior_commitment and kind in {"load", "parcel"}:
            time(state.tick + 2)
        if kind == "tool":
            for id in ("ready", "give", "complete", "cut", "take_opened", "place_opened"):
                do(id)
        else:
            do("cy_take")
            if kind == "shortcut":
                for id in (("bridge",) if value else ("lane", "round")):
                    do(id)
                    if c.prior_commitment:
                        time(state.tick + 1)
            do({"load": "place_cart", "parcel": "place_boat", "shortcut": "place_jetty"}[kind])
            do("complete")
    else:
        do("withdraw")
        if kind == "tool":
            do("untie")
        do("ari_take")
        do("alternative")
    if c.prior_commitment:
        if state.get("parents", "cy").parent != "jetty":
            for route in ("lane", "round"):
                do(f"key_{route}")
                time(state.tick + 1)
        do("key_ready")
        do("key_return")
        time(max(4, state.tick))
        do("key_assess")
        if state.get("promises", "key_return").status == "breached":
            do("key_late")
    do("finish")
    path = [e.action.id for e in state.events]
    if replay(reg, spec, path) != state:
        raise ValueError("Question-led story did not replay")
    doc = render(spec, state)
    resolution = state.get("harbor_resolutions", "end")
    row = dict(ok=True, world="harbor_questions", sample_id=f"harbor_questions:{seed}", seed=seed,
        conditions=asdict(c), story=doc.story, words=len(doc.story.split()),
        plot=dict(purpose=kind, outcome=resolution.outcome, evidence=evidence.outcome,
                  disposition=decision(state).mode, source="reported" if c.reported else "direct",
                  reinspection=state.get("evidence", "reseen").outcome if state.get("evidence", "reseen") else "none",
                  prior_promise=state.get("promises", "key_return").status if c.prior_commitment else "none"),
        path=path, trace_sha256=fingerprint(state), qa=[plain(q) for q in Reader(doc).questions()])
    return row, spec, state, doc


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--qa", action="store_true")
    args = parser.parse_args()
    row = generate(args.seed)[0]
    print(row["story"])
    if args.qa:
        print(json.dumps(row["qa"], indent=2))


if __name__ == "__main__":
    main()
