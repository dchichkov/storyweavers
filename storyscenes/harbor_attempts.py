"""Enacted attempts and physical repairs for the opt-in question-led policy.

Only the local trial record is new. Successful movement still uses the physical
writer; a failed trial does not grant custody, expose contents, or fulfill a job.
"""
from dataclasses import asdict, dataclass, replace

from .capabilities.core import Action, CapabilityError, Query, Record, execute, fingerprint, plain, replay
from .capabilities.epistemic import Result
from .capabilities.physical import _capacity, accessible, location
from .capabilities.reading import Reader


@dataclass(frozen=True, kw_only=True)
class Trial(Record):
    actor: str
    kind: str
    result: str
    event_id: str


def try_action(tx):
    job = tx.get("harbor_jobs", "ari")
    tx.require(job.attempt_first and tx.action.actor == "ari" and tx.maybe("harbor_trials", "first") is None,
               "One enacted first attempt by Ari")
    tx.require(location(tx, "ari") == "workshop" and accessible(tx, "ari", "crate"), "Attempt needs actual access")
    if job.kind == "load":
        tx.require(tx.get("parents", "crate").parent == "workshop", "Lift starts on the floor")
        # The existing read-only capacity preflight is not a movement receipt.
        try:
            _capacity(tx, "crate", "ari")
            result = "liftable"
        except CapabilityError:
            result = "too_heavy"
    elif job.kind == "tool":
        tx.require(not tx.get("containers", "crate").open, "Pull starts with a closed parcel")
        result = "resists" if tx.get("containers", "crate").latched else "gives_way"
    elif job.kind == "shortcut":
        tx.require(tx.get("parents", "crate").parent == "ari", "Ari must carry the parcel to attempt delivery")
        road = tx.get("routes", "bridge")
        tx.require(road.source == location(tx, "ari"), "Try the crossing from its actual entrance")
        result = "passable" if road.open else "blocked"
    else:
        tx.require(job.kind == "parcel" and tx.get("parents", "crate").parent == "boat", "Unexamined delivery needs actual placement")
        tx.depend("early_place:1")
        result = "delivered_unchecked"
    tx.put("harbor_trials", Trial(id="first", actor="ari", kind=job.kind, result=result, event_id=tx.event_id))
    tx.emit(kind=job.kind, result=result)


def finish_attempt(tx):
    from .harbor_questions_story import Resolution, settled_prior_promise, understood_value
    from .harbor_recovery import decision, require_divided_load
    job = tx.get("harbor_jobs", "ari")
    trial = tx.get("harbor_trials", "first")
    tx.require(job.attempt_first and tx.action.actor == "ari" and tx.maybe("harbor_resolutions", "end") is None,
               "Only one attempt-first resolution")
    tx.depend(trial.event_id)
    settled_prior_promise(tx, job)
    where = tx.get("parents", "crate").parent
    req = tx.maybe("requests", "help")
    if job.kind == "shortcut" and trial.result == "passable":
        tx.require(where == "jetty", "Successful crossing requires actual parcel delivery")
        tx.depend("early_place:1")
        outcome = "self_delivered"
    elif job.kind == "tool" and trial.result == "gives_way":
        tx.require(where == "bench" and tx.get("containers", "crate").open, "The loosened parcel must actually be opened and placed")
        tx.depend("early_open:1")
        tx.depend("early_place:1")
        outcome = "opened_without_asking"
    else:
        value = understood_value(tx)
        tx.depend(decision(tx).event_id)
        if job.kind == "shortcut":
            tx.require(where == "jetty" and req is not None and req.completion_receipt is not None,
                       "The failed crossing needs an actual alternative delivery")
            outcome = "rerouted_after_attempt"
        elif value is None:
            tx.require(where == "workshop" and req is None, "Unverified cargo must not remain at the claimed destination")
            if trial.result in {"liftable", "delivered_unchecked"}:
                tx.depend("unverified_place:1")
            outcome = "retracted_unverified" if trial.result in {"liftable", "delivered_unchecked"} else "stopped_after_attempt"
        elif job.kind == "parcel" and value:
            tx.require(where == "boat" and req is None, "Confirmed early delivery must remain aboard")
            tx.depend("early_place:1")
            outcome = "delivery_confirmed_afterward"
        elif job.kind == "load" and value is False:
            tx.require(where == "bench" and req is None, "An empty crate must actually be removed from the cart")
            tx.depend("undo_place:1")
            outcome = "empty_load_removed"
        elif req is not None and req.response == "declined":
            tx.depend(req.response_event)
            tx.require(job.prior_commitment and job.keep_promise_first, "Refusal must follow the embodied promise priority")
            if job.kind == "parcel":
                tx.require(where == "bench", "Ari must actually repair the wrong delivery")
                tx.depend("self_repair:1")
                outcome = "self_repaired_delivery"
            elif job.kind == "load" and job.recover:
                require_divided_load(tx)
                outcome = "divided_after_refusal"
            else:
                tx.require(job.kind == "load" and where == "workshop", "Heavy load must remain unperformed")
                outcome = "failed_lift_waits_for_help"
        else:
            tx.require(req is not None and req.completion_receipt is not None, "Asking is not completed assistance")
            tx.depend(tx.get("receipts", req.completion_receipt).event_id)
            target = "cart" if job.kind == "load" else "bench"
            tx.require(where == target, "The repair/help needs its physical result")
            if job.kind == "tool":
                tx.require(tx.get("containers", "crate").open, "Handing over scissors does not open the parcel")
                tx.depend("cut:1")
                tx.depend("place_opened:1")
            outcome = {"load": "help_after_failed_lift", "parcel": "wrong_delivery_repaired", "tool": "tool_after_failed_pull"}[job.kind]
    tx.put("harbor_resolutions", Resolution(id="end", kind=job.kind, outcome=outcome, event_id=tx.event_id))
    tx.emit(kind=job.kind, outcome=outcome)


def register(reg):
    reg.table("harbor_trials", Trial)
    def initial(state):
        if state.tables["harbor_trials"]:
            raise CapabilityError("Attempts must be enacted, not preloaded")
    reg.initial_validators.append(initial)
    reg.operation("try_harbor_action", try_action,
        reads={"harbor_jobs", "harbor_trials", "entities", "parents", "containers", "routes"}, writes={"harbor_trials"})
    reg.operation("resolve_harbor_attempt", finish_attempt,
        reads={"harbor_jobs", "harbor_trials", "harbor_resolutions", "parents", "containers", "requests", "dispositions",
               "belief_heads", "beliefs", "propositions", "promises", "receipts"}, writes={"harbor_resolutions"})


def extend(spec, c):
    def q(table, key, field, value, op="eq"):
        return Query(table=table, key=key, field=field, value=value, op=op)
    records = dict(spec.records)
    if c.kind == "tool":
        records["propositions"] = tuple(replace(p, result=Result(kind="exact", value=False))
                                         if p.id == "assumption" else p for p in records["propositions"])
    if c.kind == "parcel":
        records["action_specs"] = tuple(replace(s, destination="bench", terms="repair_misdelivery")
                                         if s.id == "help" else s for s in records["action_specs"])
    actions = []
    trial_exists = (q("harbor_trials", "first", "actor", "ari"),)
    for a in spec.actions:
        if a.id in {"inspect", "open_view"}:
            a = replace(a, requires=trial_exists)
        elif a.id == "finish":
            a = replace(a, operation="resolve_harbor_attempt", actor="ari")
        elif c.kind == "parcel" and a.id == "cy_take":
            a = replace(a, args=dict(a.args, source="boat"))
        elif c.kind == "parcel" and a.id in {"accept", "refuse", "self_take", "self_load"}:
            a = replace(a, requires=tuple(replace(g, value=Result(kind="exact", value=False))
                if (g.table, g.key, g.field) == ("propositions", "seen:proposition", "result") else g for g in a.requires))
            if a.id == "self_take":
                a = replace(a, args=dict(a.args, source="boat"))
        elif c.kind == "parcel" and a.id == "complete":
            a = replace(a, args=dict(a.args, receipt="repair_put:1"))
        actions.append(a)
    def add(id, op, actor="ari", *, requires=(), **args):
        actions.append(Action(id=id, operation=op, actor=actor, args=args, requires=requires))
    add("first_try", "try_harbor_action")
    if c.kind in {"parcel", "shortcut"}:
        add("early_take", "pickup", object="crate", source="workshop")
    else:
        add("early_take", "pickup", object="crate", source="workshop",
            requires=(q("harbor_trials", "first", "result", "liftable" if c.kind == "load" else "gives_way"),))
    destination = {"load": "cart", "parcel": "boat", "shortcut": "jetty", "tool": "bench"}[c.kind]
    add("early_place", "put", object="crate", destination=destination)
    if c.kind == "shortcut":
        add("early_cross", "travel", route="bridge", requires=(q("harbor_trials", "first", "result", "passable"),))
        add("put_back", "put", object="crate", destination="workshop", requires=(q("harbor_trials", "first", "result", "blocked"),))
    if c.kind == "tool":
        add("early_open", "set_container", container="crate", open=True,
            requires=(q("harbor_trials", "first", "result", "gives_way"), q("containers", "crate", "latched", False)))
    if c.kind in {"load", "parcel"}:
        add("undo_take", "pickup", object="crate", source=destination,
            requires=(q("dispositions", "decision", "mode", ("resolve", "defer"), "in"),))
        for id, where in (("undo_place", "bench"), ("unverified_place", "workshop")):
            add(id, "put", object="crate", destination=where)
        if c.kind == "parcel":
            accepted = (q("requests", "help", "response", "accepted"),)
            add("repair_put", "put", "cy", object="crate", destination="bench", requires=accepted)
            if c.prior_commitment:
                add("self_repair", "put", object="crate", destination="bench",
                    requires=(q("requests", "help", "response", "declined"),))
    return replace(spec, records=records, actions=tuple(actions), title="Trying before asking")


def generate_attempt(seed, c, spec, reg):
    from .harbor_attempts_prose import render
    from .harbor_questions_story import understood_value
    state = reg.initial(spec)
    actions = {a.id: a for a in spec.actions}
    def do(id):
        nonlocal state
        after = execute(reg, spec, state, actions[id])
        if after is None:
            raise CapabilityError(f"Illegal attempt-first continuation: {id}")
        state = after
        return state
    def time(tick):
        if c.prior_commitment and tick > state.tick:
            do(f"time_{tick}")
    if c.prior_commitment:
        for id in ("prior_promise", "bo_lane", "bo_round"):
            do(id)
    if c.kind in {"parcel", "shortcut"}:
        do("early_take")
    if c.kind == "parcel":
        do("early_place")
    do("first_try")
    trial = state.get("harbor_trials", "first")
    early_success = (c.kind, trial.result) in {("shortcut", "passable"), ("tool", "gives_way")}
    if c.kind == "shortcut":
        if early_success:
            do("early_cross")
            do("early_place")
        else:
            do("put_back")
    elif c.kind == "tool" and early_success:
        for id in ("early_open", "early_take", "early_place"):
            do(id)
    elif c.kind == "load" and trial.result == "liftable":
        do("early_take")
        do("early_place")
    time(1)
    if not early_success:
        if c.kind in {"load", "parcel"}:
            do("open_view")
        do("inspect")
        if c.reported:
            for id in ("explain", "hear", "understand"):
                do(id)
        evidence = state.get("evidence", "seen")
        result = state.get("propositions", evidence.proposition).result
        prior = state.get("propositions", "assumption").result.value
        do("defer" if result.kind != "exact" else "adopt" if result.value == prior else "resolve")
        from .harbor_recovery import second_look, divide
        state = second_look(c, state, do)
        value = understood_value(state)
        needs_help = c.kind == "shortcut" or (value is not None and (not value if c.kind == "parcel" else value))
        if needs_help:
            for id in ("ask", "request", "acknowledge", "say_uncertain" if value is None else "say_decision", "cy_hears", "cy_understands"):
                do(id)
            refuses = c.prior_commitment and c.keep_promise_first and c.kind in {"load", "parcel"}
            if refuses:
                do("refuse")
                if c.kind == "parcel":
                    do("self_take")
                    do("self_repair")
                elif c.recover:
                    divide(do)
            else:
                do("accept")
                if c.kind in {"load", "parcel"}:
                    time(3)
                if c.kind == "tool":
                    for id in ("ready", "give", "complete", "cut", "take_opened", "place_opened"):
                        do(id)
                else:
                    do("cy_take")
                    if c.kind == "shortcut":
                        for id in ("lane", "round"):
                            do(id)
                            time(state.tick + 1)
                    do({"load": "place_cart", "parcel": "repair_put", "shortcut": "place_jetty"}[c.kind])
                    do("complete")
        elif (value is None or c.kind == "load") and trial.result in {"liftable", "delivered_unchecked"}:
            do("undo_take")
            do("unverified_place" if value is None else "undo_place")
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
        raise CapabilityError("Attempt-first path failed exact replay")
    doc = render(spec, state)
    row = dict(ok=True, world="harbor_questions", sample_id=f"harbor_questions:{seed}", seed=seed,
        conditions=asdict(c), story=doc.story, words=len(doc.story.split()), path=path, trace_sha256=fingerprint(state),
        qa=[plain(q) for q in Reader(doc).questions()], plot=dict(purpose=c.kind,
            outcome=state.get("harbor_resolutions", "end").outcome, attempt=trial.result,
            reinspection=state.get("evidence", "reseen").outcome if state.get("evidence", "reseen") else "none",
            prior_promise=state.get("promises", "key_return").status if c.prior_commitment else "none"))
    return row, spec, state, doc
