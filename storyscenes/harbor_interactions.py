"""Interacting harbor goals over the same physical and social capability laws."""
from dataclasses import replace

from .capabilities.api import registry
from .capabilities.core import Action, Entity, Query, execute, replay
from .capabilities.epistemic import Fact, Proposition, Result
from .capabilities.physical import Container, Grant, LoanTerms, Ownership, Parent
from .capabilities.social import ActionSpec


def simulate_shared_rope(c):
    from .harbor_story import build_errand
    # Reuse the capacity-constrained physical world, not its completed story.
    base = build_errand(replace(c, purpose="carry", correction=True))
    records = dict(base.records)
    records["entities"] += tuple(Entity(id=id, name=name, kind="container", capacity=20) for id, name in (
        ("pocket", "Ari's pocket"), ("clip", "Ari's spring clip"),
        ("board", "the jetty mounting board"), ("basin", "the workshop washbasin")))
    records["parents"] += tuple(Parent(id=id, parent=parent) for id, parent in (
        ("pocket", "ari"), ("clip", "pocket" if c.clip_available else "workshop"),
        ("board", "jetty"), ("basin", "workshop")))
    records["containers"] += (Container(id="pocket"), Container(id="clip"),
        Container(id="board", open=c.jetty_board), Container(id="basin", open=c.basin_available))
    records["ownership"] += (Ownership(id="clip", owner="ari"),)
    descriptions = {
        "goal": ("cy", "get the boat onto water, willing to use the workshop basin" if c.flexible_sailing else
                 "get the boat onto the launch water before the ferry bell"),
        "ari_goal": ("ari", "hang the harbor chart in the window for the planned display interval"),
        "bo_goal": ("bo", "use the rope and tools to lift the launch tub's cover"),
        "display_interval": ("chart", c.display_ticks),
        "return_priority": ("ari", c.return_priority),
        "clip_support": ("clip", "spring clip can hold the paper chart but cannot lift the tub cover"),
        "board_support": ("board", "mounting board at the jetty has clamps for a chart"),
        "basin_water": ("basin", "clean water for the toy boat; indoor use has no ferry launch cutoff"),
    }
    records["propositions"] = tuple(p for p in records["propositions"] if p.id != "goal") + tuple(
        Proposition(id=id, subject=carrier, predicate="plan", scope="authored_premise",
                    result=Result(kind="exact", value=value), reference_start=0, reference_end=0)
        for id, (carrier, value) in descriptions.items())
    records["facts"] = tuple(f for f in records["facts"] if f.id != "goal") + tuple(
        Fact(id=id, carrier=carrier, proposition=id) for id, (carrier, _) in descriptions.items())
    records["loan_terms"] = (LoanTerms(id="rope_terms", version=1, object="rope", owner="bo", lender="bo",
        borrower="ari", source="case", return_authority="bo", return_recipient="bo", return_destination="bo"),)
    records["grants"] = (Grant(id="rope_settlement", issuer="bo", grantee="bo", object="rope",
        right="settle", scope="rope_loan", destination="bo", place="jetty"),)
    records["action_specs"] = (ActionSpec(id="return_rope_by_bell", operation="complete_return", actor="ari",
        object="rope", destination="bo", recipient="bo", loan_id="rope_loan", loan_version=1,
        terms="rope_terms", version=1, checkpoint=c.last_launch),)
    on_time = Query(table="clock", key="clock", field="tick", op="in", value=tuple(range(c.last_launch + 1)))
    actions = [replace(a, requires=a.requires + (on_time,)) if a.id in {"open_tub", "sail_tub"} else a for a in base.actions]

    def add(action_id, op, actor="ari", *, requires=(), **args):
        actions.append(Action(id=action_id, operation=op, actor=actor, args=args, requires=requires))

    add("offer_rope", "offer_loan", "bo", id="rope_offer", terms="rope_terms", version=1, loan_id="rope_loan")
    add("read_rope_terms", "comprehend_loan", offer="rope_offer", version=1)
    add("accept_rope", "respond_loan", offer="rope_offer", version=1)
    add("decline_rope", "respond_loan", offer="rope_offer", version=1, decision="declined")
    add("ready_rope_loan", "readiness", id="rope_ready", giver="bo", object="rope", operation="activate_loan")
    add("borrow_rope", "activate_loan", offer="rope_offer", version=1, readiness_id="rope_ready")
    add("promise_rope", "make_promise", promise="rope_return", beneficiary="bo", action_spec="return_rope_by_bell",
        version=1, loan_id="rope_loan")
    add("take_chart", "pickup", object="chart", source="workshop")
    add("hang_rope", "put", object="rope", destination="display")
    add("hang_chart", "put", object="chart", destination="rope",
        requires=(Query(table="parents", key="rope", field="parent", value="display"),))
    add("unhang_chart", "pickup", object="chart", source="rope")
    add("lay_chart", "put", object="chart", destination="display")
    add("retrieve_rope", "pickup", object="rope", source="display")
    add("mount_clip", "put", object="clip", destination="display")
    add("clip_chart", "put", object="chart", destination="clip",
        requires=(Query(table="parents", key="clip", field="parent", value="display"),))
    add("board_chart", "put", object="chart", destination="board")
    add("release_deadline", "release_promise", "bo", promise="rope_return", version=1,
        requires=(on_time, Query(table="parents", key="cy", field="parent", value="quay")))
    add("sail_basin", "put", "cy", object="boat", destination="basin",
        requires=(Query(table="promises", key="rope_return", field="status", value="released"),))
    add("offer_rope_back", "offer_return", id="rope_back", loan_id="rope_loan", object="rope", recipient="bo",
        destination="bo", version=1)
    add("accept_rope_back", "respond_return", "bo", offer="rope_back", version=1)
    add("ready_rope_back", "readiness", "bo", id="rope_back_ready", giver="ari", object="rope", operation="complete_return")
    add("return_rope", "complete_return", offer="rope_back", version=1, readiness_id="rope_back_ready")
    add("assess_rope_promise", "assess_promise", "bo", promise="rope_return", version=1)
    add("record_rope_repair", "record_late_repair", promise="rope_return", version=1, receipt="return_rope:1")
    spec = replace(base, title="One rope, two plans", records=records, actions=tuple(actions), max_steps=150,
        goal=(Query(table="parents", key="boat", field="parent", op="in", value=("tub", "case", "basin")),
              Query(table="parents", key="chart", field="parent", op="in", value=("display", "clip", "board")),
              Query(table="parents", key="rope", field="parent", value="jetty")))
    eng, by_id = registry(), {a.id: a for a in spec.actions}
    state = eng.initial(spec)

    def do(id):
        nonlocal state
        after = execute(eng, spec, state, by_id[id])
        if after is None:
            raise ValueError(f"Shared-rope policy rejected {id} at tick {state.tick}")
        state = after

    def wait(tick):
        if tick > state.tick:
            do(f"time_{tick}")

    def walk_together(actors, destination):
        source = state.get("parents", actors[0]).parent
        if source == destination:
            return
        route = state.get("routes", f"{source}_{destination}")
        for stop in ((destination,) if route.open else ("quay", destination)):
            for actor in actors:
                do(f"{actor}_{state.get('parents', actor).parent}_{stop}")
            wait(state.tick + 1)

    do("offer_rope")
    do("read_rope_terms")
    conflict = c.display_ticks + 2 > c.last_launch
    clip = conflict and state.get("parents", "clip").parent == "pocket"
    move = conflict and not clip and c.return_priority == "promise" and state.get("containers", "board").open
    relax = (conflict and not clip and c.return_priority == "display" and c.flexible_sailing
             and state.get("containers", "basin").open)
    refused = c.cautious and conflict and not (clip or move or relax)
    if refused:
        do("decline_rope")
        do("take_chart")
        walk_together(("ari",), "quay")
        do("lay_chart")
        do("bo_rope")
    else:
        for id in ("accept_rope", "ready_rope_loan", "borrow_rope", "promise_rope", "take_chart"):
            do(id)
        walk_together(("ari",), "quay")
        do("hang_rope")
        do("hang_chart")
        display_end = state.tick + c.display_ticks
    # Removing the rope, whether for loan or transport, makes the case liftable.
    do("lift_case")
    walk_together(("bo", "cy"), "jetty")
    do("deliver_case")
    if not refused:
        if relax:
            walk_together(("bo", "cy"), "quay")
            do("release_deadline")
            walk_together(("cy",), "workshop")
            do("sail_basin")
            walk_together(("bo",), "jetty")
        departure = min(display_end, c.last_launch - 1) if c.return_priority == "promise" or clip else display_end
        wait(max(state.tick, departure))
        if clip:
            do("mount_clip")
        removed_at = state.tick
        do("unhang_chart")
        if clip:
            do("clip_chart")
        elif not move:
            do("lay_chart")
        do("retrieve_rope")
        walk_together(("ari",), "jetty")
        if move:
            do("board_chart")
            display_end += state.tick - removed_at
        for id in ("offer_rope_back", "accept_rope_back", "ready_rope_back", "return_rope"):
            do(id)
    do("bo_deliver_rope")
    if relax:
        pass  # The boat is already on basin water; the tub remains closed.
    elif state.tick <= c.last_launch:
        do("open_tub")
        do("sail_tub")
    else:
        do("dry_dock")
    if not refused:
        wait(max(state.tick, c.last_launch + 1, display_end if clip or move else 0))
    if not refused and not relax:
        do("assess_rope_promise")
        if state.get("promises", "rope_return").status == "breached":
            do("record_rope_repair")
    if replay(eng, spec, [e.action.id for e in state.events]) != state:
        raise ValueError("Shared-rope story failed exact replay")
    return spec, state
