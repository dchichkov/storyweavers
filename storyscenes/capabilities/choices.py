"""Bounded G3 fixtures using only the shared physical/epistemic/social ops.

The scarce resource is available custody of one prop, not a new fuel/time model.
Giving it to one beneficiary consumes that availability for the other handoff.
No return is authored within this interval; this is not irreversible destruction
or a claim that two sequential deliveries are impossible in an extended world.
"""
from dataclasses import dataclass

from .core import Entity, WorldSpec
from .epistemic import BeliefPolicy, Channel, Exposure, Fact, Proposition, Result
from .examples import Scenario, action, query
from .physical import Ownership, Parent
from .social import ActionSpec


@dataclass(frozen=True, kw_only=True)
class ChoiceBinding:
    title: str
    worker: str
    first: str
    second: str
    place: str
    resource: str
    substitute: str
    signal: str


CHOICE_BINDINGS = (
    ChoiceBinding(title="Neighborhood library", worker="Ada", first="Bea", second="Cleo",
                  place="the reading room", resource="the only projector",
                  substitute="the printed reading chart", signal="the session indicator"),
    ChoiceBinding(title="Harbor workshop", worker="Jules", first="Mara", second="Pavel",
                  place="the workshop", resource="the only inspection lamp",
                  substitute="the printed repair chart", signal="the departure indicator"),
    ChoiceBinding(title="Mountain observatory", worker="Noor", first="Vale", second="Kit",
                  place="the instrument room", resource="the only live detector",
                  substitute="the printed star chart", signal="the observing-window indicator"),
)


def competing_promise_story(*, binding=CHOICE_BINDINGS[0], priority="first",
                            intervention="compete", priority_reason=None):
    """Build G3/S7/T2; bindings change names, never operation dispatch.

    ``action_only`` omits undertakings, not accepted requests. ``promise_only``
    omits physical performance. ``release_new`` releases the losing undertaking
    before assessment and explicitly promises a different object under v2 terms.
    The baseline's new, physically feasible request is declined after the breach.
    All dynamic tables start empty, including attention and beliefs.
    """
    if priority not in {"first", "second"}:
        raise ValueError("Priority must identify one of the two beneficiaries")
    if intervention not in {"compete", "action_only", "promise_only", "release_new"}:
        raise ValueError("Unknown bounded choice intervention")
    other = "second" if priority == "first" else "first"
    names = {"worker": binding.worker, "first": binding.first, "second": binding.second,
             "room": binding.place, "resource": binding.resource,
             "substitute": binding.substitute, "signal": binding.signal}
    records = {
        "entities": tuple(Entity(id=key, name=name,
                                 kind="actor" if key in {"worker", "first", "second"}
                                 else "place" if key == "room" else "object")
                          for key, name in names.items()),
        "parents": tuple(Parent(id=key, parent="worker" if key in {"resource", "substitute"} else "room")
                         for key in names if key != "room"),
        "ownership": tuple(Ownership(id=key, owner="worker")
                           for key in ("resource", "substitute", "signal")),
        "action_specs": tuple(
            ActionSpec(id=f"task_{role}", operation="handoff", actor="worker",
                       terms=f"deliver_resource_to_{role}", version=1, checkpoint=5,
                       object="resource", source="worker", destination=role, recipient=role)
            for role in ("first", "second")) + (
            ActionSpec(id="new_task", operation="handoff", actor="worker", terms="new_chart_request",
                       version=1, checkpoint=12, object="substitute", source="worker",
                       destination=other, recipient=other),
            ActionSpec(id="replacement_task", operation="handoff", actor="worker",
                       terms="chart_instead_of_resource", version=2, checkpoint=8,
                       object="substitute", source="worker", destination=other, recipient=other)),
        "propositions": (Proposition(id="need", subject="signal", predicate="next user",
                                     result=Result(kind="exact", value=priority), scope="current_session",
                                     reference_start=1, reference_end=1),),
        "facts": (Fact(id="need_signal", carrier="signal", proposition="need"),),
        "exposures": (Exposure(id="need_view", fact="need_signal"),),
        "channels": (Channel(id="eyes", kind="observation"), Channel(id="voice", kind="speech")),
        "belief_policies": (BeliefPolicy(id="trust_reporter", kind="testimony", source=priority),),
    }
    actions, path = [], []

    def add(action_id, operation, actor, *, selected=True, **kwargs):
        actions.append(action(action_id, operation, actor, **kwargs))
        if selected:
            path.append(action_id)

    promised = intervention != "action_only"
    performed = intervention != "promise_only"
    for role in ("first", "second"):
        add(f"ask_{role}", "create_request", role, request=f"R_{role}", responder="worker",
            action_spec=f"task_{role}", version=1)
        add(f"deliver_{role}", "deliver_request", role, request=f"R_{role}", version=1)
        # An enacted but unused acknowledgment provides a real pruning contrast.
        add(f"ack_{role}", "acknowledge_request", "worker", request=f"R_{role}", version=1)
        add(f"accept_{role}", "respond_request", "worker", request=f"R_{role}", version=1,
            decision="accepted")
        add(f"promise_{role}", "make_promise", "worker", selected=promised,
            promise=f"P_{role}", beneficiary=role, action_spec=f"task_{role}", version=1,
            request=f"R_{role}", requires=(query("requests", f"R_{role}", "response", "accepted"),))
        add(f"ready_{role}", "readiness", role, id=f"ready_{role}", giver="worker", object="resource")

    add("need_arrives", "advance_time", priority, to_tick=1)
    add("attend_need", "attend", priority, source="signal", channel="eyes", until=5, attention="focus")
    add("see_need", "observe", priority, fact="need_signal", exposure="need_view", channel="eyes",
        attention="focus", evidence="need_evidence")
    add("report_need", "speak", priority, audience="worker", channel="voice", claim="need_report",
        evidence="need_evidence")
    add("receive_need", "deliver", "worker", claim="need_report", receipt="need_receipt")
    add("understand_need", "comprehend", "worker", receipt="need_receipt", comprehension="need_understood")
    add("adopt_need", "update_belief", "worker", disposition="priority_decision", mode="init",
        head="priority_belief", policy="trust_reporter", proposition="need_evidence:proposition",
        comprehension_ids=["need_understood"])
    for role in ("first", "second"):
        reason = (priority_reason if role == priority and priority_reason is not None else
                  f"I give {names[role]}'s session priority" +
                  (" because the indicator names them as the next user." if role == priority else
                   " even though the indicator names someone else as the next user."))
        add(f"choose_{role}", "handoff", "worker", selected=performed and role == priority,
            object="resource", recipient=role, readiness_id=f"ready_{role}", reason=reason,
            reason_support=("understand_need:1", "adopt_need:1"),
            requires=(query("belief_heads", "priority_belief", "belief", "priority_decision:belief"),))
        add(f"complete_{role}", "complete_request", "worker", selected=performed and role == priority,
            request=f"R_{role}", version=1, receipt=f"choose_{role}:1")

    replace_old = intervention == "release_new"
    add("release_old", "release_promise", other, selected=replace_old, promise=f"P_{other}", version=1)
    add("promise_replacement", "make_promise", "worker", selected=replace_old,
        promise="P_replacement", beneficiary=other, action_spec="replacement_task", version=2,
        replaces=f"P_{other}")
    add("ready_substitute", "readiness", other, id="ready_substitute", giver="worker", object="substitute")
    add("deliver_substitute", "handoff", "worker", selected=replace_old, object="substitute",
        recipient=other, readiness_id="ready_substitute")
    add("close_interval", "advance_time", "worker", to_tick=9)
    for role in ("first", "second"):
        add(f"assess_{role}", "assess_promise", role, selected=promised and not (replace_old and role == other),
            promise=f"P_{role}", version=1)
    add("assess_replacement", "assess_promise", other, selected=replace_old, promise="P_replacement", version=2)
    add("new_request", "create_request", other, selected=not replace_old, request="R_new",
        responder="worker", action_spec="new_task", version=1)
    add("deliver_new_request", "deliver_request", other, selected=not replace_old, request="R_new", version=1)
    add("decline_new", "refuse", "worker", selected=not replace_old, interaction="request",
        target="R_new", version=1, reason_kind="unwillingness",
        reason="I choose not to take another task; I want to finish my own work.")
    # Recovery is available only after the closed session, never as an implicit
    # same-tick way to satisfy both original undertakings.
    add("ready_recovery", "readiness", "worker", selected=False, id="ready_recovery",
        giver=priority, object="resource", requires=(query("clock", "clock", "tick", 9),))
    add("recover_resource", "handoff", priority, selected=False, object="resource",
        recipient="worker", readiness_id="ready_recovery",
        requires=(query("clock", "clock", "tick", 9),))
    add("repair_other", "record_late_repair", "worker", selected=False,
        promise=f"P_{other}", version=1, receipt=f"choose_{other}:1")

    goal = [query("parents", "resource", "parent", priority if performed else "worker")]
    if promised:
        for role in ("first", "second"):
            status = "fulfilled" if performed and role == priority else "released" if replace_old else "breached"
            goal.append(query("promises", f"P_{role}", "status", status))
    if replace_old:
        goal.append(query("promises", "P_replacement", "status", "fulfilled"))
    else:
        goal.append(query("requests", "R_new", "response", "declined"))
    if not performed:
        ending = f"{binding.resource.capitalize()} still rested with {binding.worker}; both waiting hands were empty."
    elif replace_old:
        ending = f"{names[priority]} held {binding.resource}; {names[other]} held {binding.substitute} instead."
    else:
        ending = f"{names[priority]} held {binding.resource}. {names[other]}'s hands were still empty."
    return Scenario(spec=WorldSpec(title=binding.title, records=records, actions=tuple(actions),
                                  goal=tuple(goal), max_steps=45), path=tuple(path),
                    premise=(f"{binding.first} and {binding.second} each needed {binding.resource} by time five. "
                             f"{binding.worker} held the only one; either could receive it, but no return was arranged "
                             "during this session."), ending=ending)
