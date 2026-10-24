"""A local story-writing experiment over the existing capability engine.

The policy is an authored, bounded search for a physical instrument. Initial
conditions vary; no plot number or finished paragraph selects an outcome.
Run with ``python -m storyscenes.harbor_story --seed 42 --qa``.
"""
from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass, replace
import json
import random

from .capabilities.api import registry
from .capabilities.core import Action, Entity, Query, WorldSpec, execute, fingerprint, plain, replay
from .capabilities.epistemic import Attention, BeliefPolicy, Channel, Exposure, Fact, Proposition, Result
from .capabilities.physical import Container, Grant, LoanTerms, Ownership, Parent, Route
from .capabilities.reading import Reader
from .capabilities.social import ActionSpec


@dataclass(frozen=True, kw_only=True)
class Conditions:
    message_delay: int = 2
    moved: bool = True
    correction: bool = True
    cautious: bool = False
    direct_path: bool = True
    case_shut: bool = False
    last_launch: int = 6
    basin_available: bool = True
    pool_deep: bool = True
    purpose: str = "trial"
    display_ticks: int = 3
    return_priority: str = "promise"
    clip_available: bool = False
    jetty_board: bool = False
    flexible_sailing: bool = False

    def __post_init__(self):
        if self.message_delay not in (0, 2, 4) or self.last_launch not in (4, 6, 8):
            raise ValueError("Unsupported harbor timing")
        if self.purpose not in ("trial", "carry", "lend", "parcel", "shared_rope"):
            raise ValueError("Unsupported harbor purpose")
        if type(self.display_ticks) is not int or self.display_ticks not in (1, 3, 5):
            raise ValueError("Unsupported display interval")
        if self.return_priority not in ("promise", "display"):
            raise ValueError("Unsupported return priority")
        for key, value in asdict(self).items():
            if key not in {"message_delay", "last_launch", "purpose", "display_ticks", "return_priority"} and type(value) is not bool:
                raise ValueError(f"Boolean condition required: {key}")


def conditions(seed):
    rng = random.Random(seed)
    # Stratify the communication condition, not successful outcomes or grades.
    delays = [0, 2, 4]
    random.Random(seed // 3).shuffle(delays)
    c = Conditions(message_delay=delays[seed % 3], moved=rng.random() < .8,
        correction=rng.random() < .7, cautious=rng.random() < .5,
        direct_path=rng.random() < .65, case_shut=rng.random() < .5,
        last_launch=rng.choice((4, 6, 8)), basin_available=rng.random() < .65,
        pool_deep=rng.random() < .6, purpose=("trial", "carry", "lend", "parcel", "shared_rope")[seed % 5],
        display_ticks=rng.choice((1, 3, 5)), return_priority=rng.choice(("promise", "display")),
        clip_available=rng.random() < .4, jetty_board=rng.random() < .5, flexible_sailing=rng.random() < .6)
    # Sample tighter competing plans before execution; never select by outcome.
    return replace(c, display_ticks=rng.choice((3, 5)), last_launch=rng.choice((4, 6))) if c.purpose == "shared_rope" else c


def build(c):
    def q(table, key, field, value, op="eq"):
        return Query(table=table, key=key, field=field, value=value, op=op)

    entities = tuple(Entity(id=i, name=n, kind=k, capacity=20) for i, n, k in (
        ("ari", "Ari", "actor"), ("bo", "Bo", "actor"), ("cy", "Cy", "actor"),
        ("workshop", "the workshop", "place"), ("quay", "the quay", "place"),
        ("jetty", "the jetty", "place"), ("pool", "the sheltered harbor pool", "container"),
        ("basin", "the washbasin", "container"), ("rack", "the dry shelf", "container"),
        ("case", "the tool case", "container"), ("gauge", "the measuring stick", "object"),
        ("boat", "the little wooden boat", "object"), ("notice", "the harbor timetable", "object")))
    routes = tuple(Route(id=f"{a}_{b}", source=a, destination=b,
                         open=c.direct_path if {a, b} == {"workshop", "jetty"} else True)
                   for a, b in (("workshop", "jetty"), ("jetty", "workshop"),
                                ("workshop", "quay"), ("quay", "workshop"),
                                ("quay", "jetty"), ("jetty", "quay")))
    records = dict(entities=entities,
        parents=tuple(Parent(id=i, parent=p) for i, p in (
            ("ari", "workshop"), ("bo", "workshop"), ("cy", "quay"),
            ("case", "workshop"), ("gauge", "case"), ("boat", "cy"),
            ("pool", "jetty"), ("basin", "workshop"), ("rack", "workshop"), ("notice", "quay"))),
        containers=(Container(id="case"), Container(id="pool"),
                    Container(id="basin", open=c.basin_available), Container(id="rack")),
        ownership=(Ownership(id="gauge", owner="cy"), Ownership(id="boat", owner="cy"),
                   Ownership(id="case", owner="bo")), routes=routes,
        propositions=(
            Proposition(id="where", subject="gauge", predicate="location", scope="physical",
                result=Result(kind="exact", value="workshop"), reference_start=0, reference_end=0),
            Proposition(id="depth", subject="pool", predicate="depth", scope="measurement",
                result=Result(kind="exact", value="deep enough" if c.pool_deep else "too shallow"), reference_start=None, reference_end=None),
            Proposition(id="goal", subject="cy", predicate="desire", scope="authored_premise",
                result=Result(kind="exact", value="test the boat in the harbor pool before the ferry bell"),
                reference_start=0, reference_end=0),
            Proposition(id="schedule", subject="notice", predicate="last launch", scope="harbor_rule",
                result=Result(kind="exact", value=c.last_launch), reference_start=0, reference_end=0),
            Proposition(id="basin_water", subject="basin", predicate="contents", scope="physical",
                result=Result(kind="exact", value="clean water"), reference_start=0, reference_end=0),
            Proposition(id="boat_design", subject="boat", predicate="appearance", scope="physical",
                result=Result(kind="exact", value="a red cloth sail"), reference_start=0, reference_end=0)),
        facts=(Fact(id="where", carrier="gauge", proposition="where", live=True, projection="location"),
               Fact(id="depth", carrier="pool", proposition="depth", live=True),
               Fact(id="goal", carrier="cy", proposition="goal"),
               Fact(id="schedule", carrier="notice", proposition="schedule"),
               Fact(id="basin_water", carrier="basin", proposition="basin_water"),
               Fact(id="boat_design", carrier="boat", proposition="boat_design")),
        exposures=(Exposure(id="gauge_view", fact="where"), Exposure(id="pool_view", fact="depth")),
        channels=(Channel(id="eyes", kind="observation"), Channel(id="measure", kind="observation", instrument="gauge"),
                  Channel(id="old_post", kind="delayed", delay=c.message_delay),
                  Channel(id="new_post", kind="delayed", delay=1, enabled=c.correction)),
        attention=(Attention(id="ari_focus", actor="ari", source="gauge", channel="eyes", until=50),
                   Attention(id="cy_focus", actor="cy", source="gauge", channel="eyes", until=50),
                   Attention(id="pool_focus", actor="cy", source="pool", channel="measure", until=50)),
        belief_policies=(BeliefPolicy(id="trust_ari", kind="testimony", source="ari"),),
        action_specs=(ActionSpec(id="give_stick", operation="handoff", actor="bo", object="gauge",
            recipient="cy", destination="cy", terms="return_cys_stick", version=1, checkpoint=39),))
    actions = []

    def add(action_id, operation, actor, *, requires=(), reason=None, **args):
        actions.append(Action(id=action_id, operation=operation, actor=actor, args=args, requires=requires,
                              reason=reason, max_uses=3 if operation == "travel" else 1))

    for actor in ("ari", "bo", "cy"):
        for route in routes:
            add(f"{actor}_{route.id}", "travel", actor, route=route.id)
    for tick in range(1, 40):
        add(f"time_{tick}", "advance_time", "cy", to_tick=tick)
    for tag, actor in (("old", "ari"), ("fresh", "ari"), ("search", "cy"), ("find", "cy")):
        add(f"{tag}_look", "observe", actor, evidence=tag, fact="where", exposure="gauge_view",
            channel="eyes", attention=f"{actor}_focus", attempt=actor == "cy")
    for tag, basis, channel in (("old", "old", "old_post"), ("fresh", "fresh", "new_post")):
        add(f"{tag}_send", "speak", "ari", claim=tag, audience="cy", channel=channel, evidence=basis)
        add(f"{tag}_receive", "deliver", "cy", claim=tag, receipt=f"{tag}_receipt")
        add(f"{tag}_understand", "comprehend", "cy", receipt=f"{tag}_receipt", comprehension=f"{tag}_understood")
        add(f"{tag}_adopt", "update_belief", "cy", disposition=f"{tag}_adopt", mode="init", head=f"cy_{tag}",
            policy="trust_ari", proposition=f"{basis}:proposition", comprehension_ids=(f"{tag}_understood",))
    add("bo_close", "set_container", "bo", container="case", open=False)
    add("bo_lift", "pickup", "bo", object="case", source="workshop", reason="I need the case at the jetty.")
    add("bo_deposit", "put", "bo", object="case", destination="jetty")
    for actor in ("ari", "bo", "cy"):
        add(f"{actor}_open", "set_container", actor, container="case", open=True)
    add("take_stick", "pickup", "cy", object="gauge", source="case", reason="There you are.")
    add("ask_stick", "create_request", "cy", request="stick", responder="bo", action_spec="give_stick", version=1)
    add("deliver_stick_request", "deliver_request", "cy", request="stick", version=1)
    add("accept_stick_request", "respond_request", "bo", request="stick", version=1, decision="accepted")
    add("ready_stick", "readiness", "cy", id="ready_stick", giver="bo", object="gauge")
    add("give_stick", "handoff", "bo", object="gauge", recipient="cy", readiness_id="ready_stick")
    add("complete_stick_request", "complete_request", "bo", request="stick", version=1, receipt="give_stick:1")
    add("measure", "observe", "cy", evidence="depth", fact="depth", exposure="pool_view",
        channel="measure", attention="pool_focus", reason="A boat is small. A harbor is not.")
    add("launch", "put", "cy", object="boat", destination="pool", requires=(
        q("evidence", "depth", "outcome", "exact"),
        q("propositions", "depth:proposition", "result", Result(kind="exact", value="deep enough")),
        q("clock", "clock", "tick", tuple(range(c.last_launch + 1)), "in")),
        reason="A small boat deserves a proper voyage.")
    for ending, destination in (("basin", "basin"), ("postpone", "rack")):
        add(ending, "put", "cy", object="boat", destination=destination,
            requires=(q("clock", "clock", "tick", tuple(range(c.last_launch + 1, 40)), "in"),),
            reason="It is still water. It still counts." if ending == "basin" else "I'll keep it dry. We can try again.")
        add(ending + "_shallow", "put", "cy", object="boat", destination=destination,
            requires=(q("evidence", "depth", "outcome", "exact"),
                q("propositions", "depth:proposition", "result", Result(kind="exact", value="too shallow"))),
            reason="A small sea, then." if ending == "basin" else "Not today. You would scrape your bottom.")
    return WorldSpec(title="The little harbor boat", records=records, actions=tuple(actions), max_steps=120,
        goal=(q("parents", "boat", "parent", ("pool", "basin", "rack"), "in"),))


def simulate(c):
    """An explicit author policy, not an omniscient character or a route index."""
    if c.purpose == "shared_rope":
        from .harbor_interactions import simulate_shared_rope
        return simulate_shared_rope(c)
    if c.purpose != "trial":
        return simulate_errand(c)
    engine, spec = registry(), build(c)
    state = engine.initial(spec)
    actions = {a.id: a for a in spec.actions}

    def do(id):
        nonlocal state
        result = execute(engine, spec, state, actions[id])
        if result is None:
            raise ValueError(f"Harbor policy attempted illegal action {id} at {state.tick}")
        state = result

    def time(tick):
        if tick > state.tick:
            do(f"time_{tick}")

    def travel(actor, destination):
        source = state.get("parents", actor).parent
        if source == destination:
            return
        route = state.get("routes", f"{source}_{destination}")
        steps = (destination,) if route.open else ("quay", destination)
        for stop in steps:
            current = state.get("parents", actor).parent
            do(f"{actor}_{current}_{stop}")
            time(state.tick + 1)

    def receive(tag):
        time(state.get("claims", tag).available_at)
        for op in ("receive", "understand", "adopt"):
            do(f"{tag}_{op}")

    def inspect(tag):
        # Co-located case contents are visible only after actually opening it.
        if (state.get("parents", "case").parent == state.get("parents", "cy").parent
                and not state.get("containers", "case").open):
            do("cy_open")
        do(f"{tag}_look")
        if state.get("evidence", tag).outcome == "exact":
            do("take_stick")
            return True
        return False

    do("old_look")
    do("old_send")
    if c.message_delay == 0:
        receive("old")
        if c.moved:
            if c.case_shut:
                do("bo_close")
            do("bo_lift")
        travel("cy", "workshop")
        if c.moved:
            for step in ("ask_stick", "deliver_stick_request", "accept_stick_request", "ready_stick"):
                do(step)
            if c.case_shut:
                do("bo_open")
            do("give_stick")
            do("complete_stick_request")
        else:
            inspect("search")
    else:
        if c.moved:
            if c.case_shut:
                do("bo_close")
            do("bo_lift")
            travel("bo", "jetty")
            do("bo_deposit")
        time(c.message_delay)
        receive("old")
        if not c.cautious:
            travel("cy", "workshop")
            found = inspect("search")
        else:
            found = False
        if not found:
            if c.correction:
                # Ari checks rather than transmitting a predicted present location.
                travel("ari", "jetty" if c.moved else "workshop")
                if not state.get("containers", "case").open:
                    do("ari_open")
                do("fresh_look")
                do("fresh_send")
                receive("fresh")
                believed = state.get("beliefs", state.get("belief_heads", "cy_fresh").belief)
                destination = state.get("propositions", believed.proposition).result.value
                travel("cy", destination)
                inspect("find")
            else:
                if c.cautious:
                    time(state.tick + 1)
                    travel("cy", "workshop")
                    found = inspect("search")
                if not found:
                    # A declared two-place search, not knowledge of a hidden location.
                    travel("cy", "jetty")
                    inspect("find")
    travel("cy", "jetty")
    do("measure")
    deep = state.get("propositions", state.get("evidence", "depth").proposition).result.value == "deep enough"
    if deep and state.tick <= c.last_launch:
        do("launch")
    else:
        travel("cy", "workshop")
        do(("basin" if c.basin_available else "postpone") + ("" if deep else "_shallow"))
    path = [e.action.id for e in state.events]
    if replay(engine, spec, path) != state:
        raise ValueError("Harbor path failed exact replay")
    return spec, state


def build_errand(c):
    """Construct the physical setting without running any character's policy."""
    entities = [Entity(id=i, name=n, kind=k, capacity=20, mass=m) for i, n, k, m in (
        ("cy", "Cy", "actor", 1), ("bo", "Bo", "actor", 1), ("ari", "Ari", "actor", 1),
        ("workshop", "the workshop", "place", 1), ("quay", "the quay", "place", 1),
        ("jetty", "the jetty", "place", 1), ("case", "the tool case", "container", 1),
        ("rope", "the coil of rope", "container", 12), ("tools", "the bundle of tools", "object", 12),
        ("boat", "the little wooden boat", "object", 1), ("display", "the window shelf", "container", 1),
        ("notice", "the timetable", "object", 1), ("tub", "the covered launch tub", "container", 1),
        ("chart", "Ari's harbor chart", "object", 1))]
    # The case can contain the load but neither child can carry the full case.
    entities = [Entity(id=e.id, name=e.name, kind=e.kind, capacity=30 if e.id == "case" else e.capacity,
                       mass=e.mass) for e in entities]
    parents = dict(cy="workshop", bo="workshop" if c.correction else "jetty", ari="workshop",
        workshop=None, quay=None, jetty=None, case="workshop", rope="case", tools="case",
        boat="cy", display="quay", notice="workshop", tub="jetty", chart="workshop")
    routes = tuple(Route(id=f"{a}_{b}", source=a, destination=b, max_load=20,
                        open=c.direct_path if {a, b} == {"workshop", "jetty"} else True)
                   for a, b in (("workshop", "jetty"), ("jetty", "workshop"), ("workshop", "quay"),
                                ("quay", "workshop"), ("quay", "jetty"), ("jetty", "quay")))
    premise = ("bring Bo's rope and tools to the jetty before the ferry bell" if c.purpose == "carry" else
               "lend Ari the boat for a window display if it can come back before launch time")
    records = dict(entities=tuple(entities), parents=tuple(Parent(id=i, parent=p) for i, p in parents.items() if p),
        containers=(Container(id="case"), Container(id="display"), Container(id="rope"), Container(id="tub", open=False)), routes=routes,
        ownership=(Ownership(id="case", owner="bo"), Ownership(id="rope", owner="bo"),
                   Ownership(id="tools", owner="bo"), Ownership(id="boat", owner="cy"), Ownership(id="chart", owner="ari")),
        propositions=(Proposition(id="goal", subject="cy", predicate="desire", scope="authored_premise",
            result=Result(kind="exact", value=premise), reference_start=0, reference_end=0),
            Proposition(id="load", subject="case", predicate="total weight", scope="physical",
                result=Result(kind="exact", value=25), reference_start=0, reference_end=0),
            Proposition(id="schedule", subject="notice", predicate="last launch", scope="harbor_rule",
                result=Result(kind="exact", value=c.last_launch), reference_start=0, reference_end=0),
            Proposition(id="crew", subject="bo", predicate="starting place", scope="physical",
                result=Result(kind="exact", value=parents["bo"]), reference_start=0, reference_end=0),
            Proposition(id="tub", subject="tub", predicate="preparation", scope="physical",
                result=Result(kind="exact", value="filled and checked for toy boats; heavy cover needs rope and tools to lift"), reference_start=0, reference_end=0),
            Proposition(id="chart", subject="chart", predicate="depicts", scope="physical",
                result=Result(kind="exact", value="the whole harbor"), reference_start=0, reference_end=0)),
        facts=(Fact(id="goal", carrier="cy", proposition="goal"), Fact(id="load", carrier="case", proposition="load"),
               Fact(id="schedule", carrier="notice", proposition="schedule"), Fact(id="crew", carrier="bo", proposition="crew"),
               Fact(id="tub", carrier="tub", proposition="tub"), Fact(id="chart", carrier="chart", proposition="chart")))
    actions = []

    def add(action_id, op, actor="cy", *, requires=(), **args):
        actions.append(Action(id=action_id, operation=op, actor=actor, args=args, requires=requires,
                              max_uses=4 if op == "travel" else 1))

    def q(table, key, field, value, op="eq"):
        return Query(table=table, key=key, field=field, value=value, op=op)

    for actor in ("cy", "bo", "ari"):
        for route in routes:
            add(f"{actor}_{route.id}", "travel", actor, route=route.id)
    for tick in range(1, 40):
        add(f"time_{tick}", "advance_time", to_tick=tick)
    if c.purpose == "carry":
        add("try_full_case", "pickup", object="case", source="workshop")
        add("bo_rope", "pickup", "bo", object="rope", source="case")
        add("cy_rope", "pickup", object="rope", source="case")
        add("leave_rope", "put", object="rope", destination="workshop")
        add("lift_case", "pickup", object="case", source="workshop")
        add("deliver_case", "put", object="case", destination="jetty")
        add("collect_rope", "pickup", object="rope", source="workshop")
        for actor in ("cy", "bo"):
            add(f"{actor}_deliver_rope", "put", actor, object="rope", destination="jetty")
        add("open_tub", "set_container", "bo", container="tub", open=True, requires=(
            q("parents", "rope", "parent", "jetty"), q("parents", "case", "parent", "jetty"),
            q("parents", "tools", "parent", "case")))
        add("sail_tub", "put", object="boat", destination="tub")
        add("dry_dock", "put", object="boat", destination="case")
        goal = (q("parents", "case", "parent", "jetty"), q("parents", "boat", "parent", ("tub", "case"), "in"))
    elif c.purpose == "lend":
        records["grants"] = (Grant(id="owner_return", issuer="cy", grantee="cy", object="boat",
            right="settle", scope="boat_loan", destination="cy"),)
        records["loan_terms"] = (LoanTerms(id="display_loan", version=1, object="boat", owner="cy",
            lender="cy", borrower="ari", source="cy", return_authority="cy", return_recipient="cy",
            return_destination="cy"),)
        add("offer", "offer_loan", id="display_offer", terms="display_loan", version=1, loan_id="boat_loan")
        add("read_terms", "comprehend_loan", "ari", offer="display_offer", version=1)
        add("accept", "respond_loan", "ari", offer="display_offer", version=1)
        add("decline", "respond_loan", "ari", offer="display_offer", version=1, decision="declined")
        add("ready_loan", "readiness", "ari", id="loan_ready", giver="cy", object="boat", operation="activate_loan")
        add("collect", "activate_loan", "ari", offer="display_offer", version=1, readiness_id="loan_ready")
        add("exhibit", "put", "ari", object="boat", destination="display")
        add("retrieve", "pickup", "ari", object="boat", source="display")
        add("offer_back", "offer_return", "ari", id="boat_back", loan_id="boat_loan", object="boat",
            recipient="cy", destination="cy", version=1)
        add("accept_back", "respond_return", offer="boat_back", version=1)
        add("ready_back", "readiness", id="back_ready", giver="ari", object="boat", operation="complete_return")
        add("return", "complete_return", "ari", offer="boat_back", version=1, readiness_id="back_ready")
        add("pick_chart", "pickup", "ari", object="chart", source="workshop")
        add("display_chart", "put", "ari", object="chart", destination="display")
        goal = (q("parents", "boat", "parent", "cy"), q("loan_offers", "display_offer", "status", ("declined", "activated"), "in"))
    else:
        lantern_box = "red_box" if c.moved else "blue_box"
        cloth_box = "blue_box" if c.moved else "red_box"
        records["entities"] += tuple(Entity(id=i, name=n, kind=k, capacity=10) for i, n, k in (
            ("red_box", "the red parcel box", "container"), ("blue_box", "the blue parcel box", "container"),
            ("lantern", "the shuttered lantern", "container"), ("cloth", "the folded cleaning cloth", "object"),
            ("bulb", "the glowing battery bulb", "object"),
            ("lamp_tag", "the lantern tag", "object"), ("cloth_tag", "the cloth tag", "object")))
        records["parents"] = tuple(p for p in records["parents"] if p.id != "bo") + (
            Parent(id="bo", parent="jetty"), Parent(id="red_box", parent="workshop"), Parent(id="blue_box", parent="workshop"),
            Parent(id="lantern", parent=lantern_box), Parent(id="cloth", parent=cloth_box), Parent(id="bulb", parent="lantern"),
            Parent(id="lamp_tag", parent="blue_box"), Parent(id="cloth_tag", parent="red_box"))
        records["containers"] += (Container(id="red_box", open=False), Container(id="blue_box", open=False), Container(id="lantern", open=False))
        records["propositions"] = tuple(p for p in records["propositions"] if p.id not in ("goal", "crew")) + (
            Proposition(id="goal", subject="cy", predicate="desire", scope="authored_premise",
                result=Result(kind="exact", value="bring Bo the lantern, not merely a box labeled lantern"), reference_start=0, reference_end=0),
            Proposition(id="crew", subject="bo", predicate="starting place", scope="physical",
                result=Result(kind="exact", value="jetty"), reference_start=0, reference_end=0),
            Proposition(id="packing_list", subject="notice", predicate="inscription", scope="authored_claim",
                result=Result(kind="exact", value="lantern in blue box; cloth in red box"), reference_start=0, reference_end=0),
            Proposition(id="light", subject="bulb", predicate="lit", scope="physical",
                result=Result(kind="exact", value=True), reference_start=None, reference_end=None))
        records["facts"] += (Fact(id="packing_list", carrier="notice", proposition="packing_list"),
                             Fact(id="light", carrier="bulb", proposition="light", live=True))
        for color in ("blue", "red"):
            box = color + "_box"
            content = "lantern" if box == lantern_box else "cloth"
            records["propositions"] += (Proposition(id=color, subject=box, predicate="contents", scope="physical",
                result=Result(kind="exact", value=content), reference_start=None, reference_end=None),)
            records["facts"] += (Fact(id=color, carrier=content, proposition=color, live=True),)
            add("open_" + color, "set_container", container=box, open=True)
            add("inspect_" + color, "observe", evidence=color, fact=color, exposure=color, channel="eyes", attention=color)
            add("pick_" + color, "pickup", object=box, source="workshop")
        records["exposures"] = tuple(Exposure(id=color, fact=color) for color in ("blue", "red", "light"))
        records["channels"] = (Channel(id="eyes", kind="observation"),)
        records["attention"] = tuple(Attention(id=color, actor="cy", source="lantern" if color + "_box" == lantern_box else "cloth", channel="eyes", until=50) for color in ("blue", "red")) + (
            Attention(id="bo_light", actor="bo", source="bulb", channel="eyes", until=50),)
        add("put_back_blue", "put", object="blue_box", destination="workshop")
        for tag, source, dest in (("lamp_tag", "blue_box", "red_box"), ("cloth_tag", "red_box", "blue_box")):
            add("take_" + tag, "pickup", object=tag, source=source)
            add("fix_" + tag, "put", object=tag, destination=dest)
        add("ready_parcel", "readiness", "bo", id="parcel_ready", giver="cy", object=lantern_box)
        add("give_parcel", "handoff", object=lantern_box, recipient="bo", readiness_id="parcel_ready",
            requires=(q("evidence", "red" if c.moved else "blue", "outcome", "exact"),))
        add("open_shutter", "set_container", "bo", container="lantern", open=True)
        add("see_light", "observe", "bo", evidence="light", fact="light", exposure="light", channel="eyes", attention="bo_light")
        goal = (q("parents", lantern_box, "parent", "bo"), q("evidence", "light", "outcome", "exact"))
    return WorldSpec(title="Harbor errands", records=records, actions=tuple(actions), goal=goal, max_steps=100)


def simulate_errand(c):
    """Authored goal policies over shared capacity, custody and timing laws."""
    spec = build_errand(c)
    engine = registry()
    state = engine.initial(spec)
    available = {a.id: a for a in spec.actions}

    def do(id):
        nonlocal state
        result = execute(engine, spec, state, available[id])
        if result is None:
            raise ValueError(f"Errand policy rejected {id}")
        state = result

    def wait(tick):
        if tick > state.tick:
            do(f"time_{tick}")

    def go(actor, dest):
        source = state.get("parents", actor).parent
        if source == dest:
            return
        steps = (dest,) if state.get("routes", f"{source}_{dest}").open else ("quay", dest)
        for stop in steps:
            do(f"{actor}_{state.get('parents', actor).parent}_{stop}")
            wait(state.tick + 1)

    if c.purpose == "carry":
        # Failed capacity is a deterministic precondition, not a silently lost load.
        if execute(engine, spec, state, available["try_full_case"]) is not None:
            raise ValueError("The overfull case should require splitting the load")
        if state.get("parents", "bo").parent == "workshop":
            do("bo_rope")
            do("lift_case")
            go("bo", "jetty")
            do("bo_deliver_rope")
            go("cy", "jetty")
            do("deliver_case")
        else:
            do("cy_rope")
            do("leave_rope")
            do("lift_case")
            go("cy", "jetty")
            do("deliver_case")
            # A time estimate is computed from declared routes, not an ending ID.
            leg = 1 if c.direct_path else 2
            if state.tick + 2 * leg <= c.last_launch:
                go("cy", "workshop")
                do("collect_rope")
                go("cy", "jetty")
                do("cy_deliver_rope")
        if state.get("parents", "rope").parent == "jetty":
            do("open_tub")
            do("sail_tub")
        else:
            do("dry_dock")
    elif c.purpose == "lend":
        do("offer")
        do("read_terms")
        # Ari knows how long the display is meant to stay up. Refusal can protect
        # Cy's competing plan; acceptance does not magically make a return timely.
        expected_return = c.message_delay + 2
        if c.cautious and expected_return > c.last_launch:
            do("decline")
            do("pick_chart")
            go("ari", "quay")
            do("display_chart")
        else:
            do("accept")
            do("ready_loan")
            do("collect")
            go("ari", "quay")
            do("exhibit")
            wait(state.tick + c.message_delay)
            do("retrieve")
            if c.moved:
                go("cy", "jetty")
            go("ari", "workshop")
            if c.moved:
                go("ari", "jetty")
            for step in ("offer_back", "accept_back", "ready_back", "return"):
                do(step)
    else:
        if not c.cautious:
            do("pick_blue")
            go("cy", "jetty")
        do("open_blue")
        do("inspect_blue")
        content = state.get("propositions", state.get("evidence", "blue").proposition).result.value
        if content != "lantern":
            if not c.cautious:
                go("cy", "workshop")
                do("put_back_blue")
            do("open_red")
            do("inspect_red")
            for step in ("take_lamp_tag", "fix_lamp_tag", "take_cloth_tag", "fix_cloth_tag"):
                do(step)
            do("pick_red")
        elif c.cautious:
            do("pick_blue")
        go("cy", "jetty")
        do("ready_parcel")
        do("give_parcel")
        do("open_shutter")
        do("see_light")
    path = [e.action.id for e in state.events]
    if replay(engine, spec, path) != state:
        raise ValueError("Errand failed exact replay")
    return spec, state


def generate(seed=0, *, prose_seed=None, config=None):
    from .harbor_prose import render
    c = config or conditions(seed)
    spec, state = simulate(c)
    document = render(spec, state, c, seed if prose_seed is None else prose_seed)
    path = [e.action.id for e in state.events]
    evidence = state.get("evidence", "search")
    outcome = state.get("parents", "boat").parent
    signature = dict(purpose=c.purpose, outcome=outcome, shallow=not c.pool_deep, wrong_place=bool(evidence and evidence.outcome != "exact"),
        corrected="fresh_receive" in path, early=c.message_delay == 0,
        detour=not c.direct_path and any(a in path for a in ("cy_workshop_quay", "cy_jetty_quay")),
        opened=any(a in path for a in ("cy_open", "ari_open", "bo_open")))
    if c.purpose == "carry":
        signature = dict(purpose=c.purpose, outcome="helped_delivery" if "bo_rope" in path else
                         "two_trips" if "collect_rope" in path else "partial_delivery", detour=not c.direct_path)
    elif c.purpose == "lend":
        signature = dict(purpose=c.purpose, outcome="declined" if "decline" in path else
                         "late_return" if state.tick > c.last_launch else "timely_return",
                         missed_meeting="cy_workshop_jetty" in path or "cy_quay_jetty" in path)
    elif c.purpose == "parcel":
        signature = dict(purpose=c.purpose, outcome="labels_fixed" if "fix_lamp_tag" in path else "correct_delivery",
                         wrong_trip="put_back_blue" in path)
    elif c.purpose == "shared_rope":
        promise = state.get("promises", "rope_return")
        hung = next((e.tick for e in state.events if e.action.id == "hang_chart"), None)
        removed = next((e.tick for e in state.events if e.action.id == "unhang_chart"), None)
        interrupted = hung is not None and removed < hung + c.display_ticks
        signature = dict(purpose=c.purpose, outcome="clip_preserves_both" if "clip_chart" in path else
            "display_moves_to_jetty" if "board_chart" in path else
            "released_deadline_and_basin" if "sail_basin" in path else
            "flat_chart_and_sailing" if promise is None else
            "shortened_display_and_sailing" if interrupted else "both_plans" if outcome == "tub" else "display_costs_sailing",
            promise=promise.status if promise else "not_made", late_repair=bool(promise and promise.repair_receipt),
            detour=not c.direct_path)
    return dict(sample_id=f"harbor:{seed}", world="harbor", seed=seed, ok=True,
        conditions=asdict(c), story=document.story, qa=plain(Reader(document).questions()),
        story_sha256=fingerprint(document.story), trace_sha256=fingerprint(state), path=path,
        plot=signature, words=len(document.story.split())), spec, state, document


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--seed", type=int, default=0)
    p.add_argument("--prose-seed", type=int)
    p.add_argument("--qa", action="store_true")
    p.add_argument("--json", action="store_true")
    args = p.parse_args()
    row, _, _, _ = generate(args.seed, prose_seed=args.prose_seed)
    if args.json:
        print(json.dumps(row, ensure_ascii=False, indent=2))
    else:
        print(row["story"])
        if args.qa:
            for qa in row["qa"]:
                print(f"\nQ: {qa['question']}\nA: {qa['answer']}")


if __name__ == "__main__":
    main()
