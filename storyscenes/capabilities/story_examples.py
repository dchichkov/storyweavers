"""Narrative ordering constraints on the permissive semantic test fixtures.

These are authored prerequisites, not universal laws: a handoff before a promise
remains legal in the engine, but is not this example's intended plot.
"""
from dataclasses import replace

from . import examples
from .core import Entity
from .epistemic import Attention, BeliefPolicy, Channel, Exposure, Fact, Proposition, Result
from .physical import Parent
from .social import ActionSpec


def with_requirements(scenario, requirements):
    actions = tuple(replace(a, requires=a.requires + tuple(requirements.get(a.id, ())))
                    for a in scenario.spec.actions)
    return replace(scenario, spec=replace(scenario.spec, actions=actions))


def loan_story(*, readable=True):
    q = examples.query
    base = with_requirements(examples.loan_story(), {
        "offer": (q("requests", "R", "response", "accepted"),),
        "pack": (q("promises", "P", "id", "P"),),
        "outward": (q("parents", "item", "parent", "bag"),),
        "relift": (q("evidence", "marker_reading", "outcome", "exact"),),
        "homeward": (q("receipts", "relift:1", "id", "relift:1"),),
        "return_offer": (q("receipts", "rest:1", "id", "rest:1"),
                         q("parents", "borrower", "parent", "room"),
                         q("parents", "bag", "parent", "borrower"),
                         q("belief_heads", "garden_name", "belief", "learn_marker:belief")),
    })
    records = dict(base.spec.records)
    records["entities"] += (Entity(id="marker", name="the stone marker", kind="object"),)
    records["parents"] += (Parent(id="marker", parent="yard"),)
    records.update({
        "propositions": (Proposition(id="marker_text", subject="marker", predicate="destination",
            result=Result(kind="exact", value="the walled garden"), scope="inscription",
            reference_start=None, reference_end=None),),
        "facts": (Fact(id="marker_text", carrier="marker", proposition="marker_text", live=True),),
        "exposures": (Exposure(id="marker_view", fact="marker_text", readable=readable),),
        "channels": (Channel(id="map_reading", kind="observation", instrument="item"),
                     Channel(id="voice", kind="speech")),
        "attention": (Attention(id="marker_focus", actor="borrower", source="marker",
                                channel="map_reading", until=5),),
        "belief_policies": (BeliefPolicy(id="trust_borrower", kind="testimony", source="borrower"),),
    })
    records["action_specs"] += (ActionSpec(id="marker_task", operation="inspection", actor="borrower",
        terms="read_the_courtyard_marker", version=1, checkpoint=5, object="marker",
        destination="yard", inspection_fact="marker_text"),)
    actions = []
    for action in base.spec.actions:
        if action.id == "ask":
            action = replace(action, args=dict(action.args, action_spec="marker_task"))
        elif action.id == "deliver_request":
            action = replace(action, reason="Use the atlas to read the marker in the courtyard.")
        elif action.id == "promise":
            action = replace(action, args=dict(action.args, request=None))
        elif action.id == "complete":
            action = replace(action, args=dict(action.args, receipt="marker_reading", table="evidence"))
        actions.append(action)
    read = examples.action("read_marker", "observe", "borrower", fact="marker_text", exposure="marker_view",
        channel="map_reading", attention="marker_focus", evidence="marker_reading",
        requires=(q("receipts", "rest:1", "id", "rest:1"),))
    report = (
        examples.action("report_marker", "speak", "borrower", audience="owner", channel="voice",
            claim="marker_report", evidence="marker_reading",
            requires=(q("receipts", "homeward:1", "id", "homeward:1"),)),
        examples.action("hear_marker", "deliver", "owner", claim="marker_report", receipt="marker_receipt"),
        examples.action("understand_marker", "comprehend", "owner", receipt="marker_receipt", comprehension="marker_understood"),
        examples.action("learn_marker", "update_belief", "owner", disposition="learn_marker", mode="init",
            head="garden_name", policy="trust_borrower", proposition="marker_reading:proposition",
            comprehension_ids=("marker_understood",)),
    )
    path = list(base.path)
    path.insert(path.index("relift"), read.id)
    index = path.index("return_offer")
    path[index:index] = [a.id for a in report]
    return replace(base, spec=replace(base.spec, records=records, actions=tuple(actions) + (read,) + report,
        goal=base.spec.goal + (q("requests", "R", "completion_receipt", "marker_reading"),)),
        path=tuple(path), premise="", ending="")


def promise_story(*, reading_at=8):
    if type(reading_at) is not int or not 1 <= reading_at <= 19:
        raise ValueError("The calibration reading must arrive within this bounded session")
    q = examples.query
    status = "fulfilled" if reading_at < 8 else "breached"
    base = with_requirements(examples.promise_story(perform_at=reading_at), {
        "promise": (q("requests", "R", "response", "accepted"),),
        "boundary": (q("promises", "P", "id", "P"),),
        "ready": (q("promises", "P", "id", "P"),),
        "handoff": (q("promises", "P", "id", "P"), q("clock", "clock", "tick", reading_at),
                    q("evidence", "calibration_reading", "outcome", "exact")),
        "close": (q("receipts", "handoff:1", "id", "handoff:1"),),
        "new_request": (q("promises", "P", "status", status),),
    })
    records = dict(base.spec.records)
    records.update({
        "propositions": (Proposition(id="calibration", subject="card", predicate="reading",
            result=Result(kind="exact", value="ready"), scope="scheduled_reading",
            reference_start=reading_at, reference_end=reading_at),),
        "facts": (Fact(id="calibration", carrier="card", proposition="calibration"),),
        "exposures": (Exposure(id="card_view", fact="calibration"),),
        "channels": (Channel(id="eyes", kind="observation"),),
        "attention": (Attention(id="card_focus", actor="noor", source="card", channel="eyes", until=20),),
    })
    actions = []
    for action in base.spec.actions:
        if action.id == "promise":
            action = replace(action, reason="I want to check my calibration reading first.")
        elif action.id == "boundary":
            action = replace(action, actor="noor", reason=f"The calibration reading is due at time {reading_at}.")
        actions.append(action)
    check = examples.action("check_card", "observe", "noor", fact="calibration", exposure="card_view",
        channel="eyes", attention="card_focus", evidence="calibration_reading",
        requires=(q("promises", "P", "id", "P"), q("clock", "clock", "tick", reading_at)))
    path = list(base.path)
    path.insert(path.index("handoff"), check.id)
    return replace(base, spec=replace(base.spec, records=records, actions=tuple(actions) + (check,)),
                   path=tuple(path), premise="", ending="")


def delayed_report_story(*, correction_enabled=True):
    q = examples.query
    base = with_requirements(examples.delayed_report_story(), {
        "follow": (q("belief_heads", "cy_old", "id", "cy_old"),),
        "open": (q("parents", "ari", "parent", "jetty"), q("clock", "clock", "tick", 2)),
        "look_new": (q("parents", "ari", "parent", "jetty"), q("clock", "clock", "tick", 2),
                     q("containers", "case", "open", True)),
    })
    records = dict(base.spec.records)
    records["channels"] += (Channel(id="correction_post", kind="delayed", delay=2, enabled=correction_enabled),)
    correction = (
        examples.action("send_correction", "speak", "ari", audience="cy", channel="correction_post",
            claim="correction", evidence="fresh", requires=(q("dispositions", "revision", "id", "revision"),)),
        examples.action("correction_arrives", "advance_time", "cy", to_tick=4,
            requires=(q("claims", "correction", "id", "correction"),)),
        examples.action("receive_correction", "deliver", "cy", claim="correction", receipt="new_mail"),
        examples.action("understand_correction", "comprehend", "cy", receipt="new_mail", comprehension="new_understood"),
        examples.action("adopt_correction", "update_belief", "cy", disposition="adopt_correction", mode="init",
            head="cy_latest", policy="trust_ari", proposition="fresh:proposition", comprehension_ids=("new_understood",)),
        examples.action("fetch_gauge", "travel", "cy", route="to_jetty",
            reason="I will try the jetty; Ari's newer report puts the gauge there.",
            reason_support=("adopt_correction:1",),
            requires=(q("belief_heads", "cy_latest", "belief", "adopt_correction:belief"),)),
        examples.action("take_gauge", "pickup", "cy", object="gauge", source="case",
            requires=(q("belief_heads", "cy_latest", "belief", "adopt_correction:belief"),)),
    )
    return replace(base, spec=replace(base.spec, records=records, actions=base.spec.actions + correction,
        goal=base.spec.goal + (q("parents", "gauge", "parent", "cy"),)),
        path=base.path + tuple(a.id for a in correction), premise="", ending="")
