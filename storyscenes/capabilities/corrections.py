"""D06's five finite correction stories, executed only by shared operations.

Premises and endings are reading aids, not extra world effects or QA support.
The fixtures bind beliefs to people and evidence to physical carriers, following
story.py; none infers truth, identity, or a repair from rendered English.
"""
from dataclasses import replace

from .core import Entity, WorldSpec
from .epistemic import (Attention, AuthorityPolicy, Belief, BeliefHead,
                        BeliefPolicy, Channel, Exposure, Fact, Proposition, Result)
from .examples import Scenario, action, query
from .physical import Container, Parent
from .social import ActionSpec, BookingSlot


def _room(*entities, place="the observing room"):
    return {
        "entities": (Entity(id="room", name=place, kind="place"),) + tuple(
            Entity(id=i, name=n, kind=k) for i, n, k in entities),
        "parents": tuple(Parent(id=i, parent="room") for i, _, _ in entities),
        "channels": (Channel(id="eyes", kind="observation"), Channel(id="voice", kind="speech")),
        "belief_policies": (BeliefPolicy(id="assumption", kind="authored", modes=("init",)),
                            BeliefPolicy(id="percept", kind="percept"),
                            BeliefPolicy(id="wait", kind="defer", modes=("defer",))),
    }


def _p(key, subject, predicate, value, tick, scope):
    return Proposition(id=key, subject=subject, predicate=predicate,
                       result=Result(kind="exact", value=value), scope=scope,
                       reference_start=tick, reference_end=tick)


def _views(records, actor):
    records["exposures"] = tuple(Exposure(id=f.id, fact=f.id) for f in records["facts"])
    records["attention"] = tuple(Attention(id=f.id, actor=actor, source=f.carrier,
                                         channel="eyes", until=30) for f in records["facts"])


def _look(key, actor, fact, **kw):
    return action(key, "observe", actor, fact=fact, evidence=key, exposure=fact,
                  attention=fact, channel="eyes", **kw)


def _story(title, records, actions, path, premise, ending):
    last = next(a for a in actions if a.id == path[-1])
    return Scenario(spec=WorldSpec(title=title, records=records, actions=tuple(actions),
                    goal=(query("dispositions", last.args["disposition"], "mode", last.args["mode"]),)),
                    path=tuple(path), premise=premise, ending=ending)


def observatory_reading_story(*, current="cloud", open_slit=True):
    """Six was valid. Eight initializes a new interval, with no invented prior."""
    records = _room(("sal", "Sal", "actor"), ("noor", "Noor", "actor"),
                    ("sector", "the target sector", "object"),
                    ("slit", "the viewing slit", "container"),
                    ("strip", "the six-o'clock recorder strip", "object"))
    records["parents"] = tuple(Parent(id=p.id, parent="slit") if p.id == "sector" else p
                               for p in records["parents"])
    records["containers"] = (Container(id="slit", open=True),)
    records["propositions"] = (
        _p("six", "sector", "sky", "clear", 6, "target-sector"),
        _p("eight", "sector", "sky", current, 8, "target-sector"),
        _p("ink", "strip", "inscription", "clear sky; observed at six", 6, "recorder-ink"))
    records["facts"] = (Fact(id="six_view", carrier="sector", proposition="six"),
                        Fact(id="eight_view", carrier="sector", proposition="eight"),
                        Fact(id="strip_ink", carrier="strip", proposition="ink", assertion="six"))
    _views(records, "sal")
    actions = [
        action("six_oclock", "advance_time", "sal", to_tick=6),
        _look("look_six", "sal", "six_view"),
        action("remember_six", "update_belief", "sal", disposition="six", mode="init", head="six",
               policy="percept", proposition="look_six:proposition", evidence_ids=("look_six",)),
        action("close_slit", "set_container", "noor", container="slit", open=False),
        action("eight_oclock", "advance_time", "sal", to_tick=8),
        _look("read_strip", "sal", "strip_ink"),
        action("open_slit", "set_container", "noor", container="slit", open=True),
        _look("look_eight", "sal", "eight_view", attempt=True),
        action("learn_eight", "update_belief", "sal", disposition="eight", mode="init", head="current",
               policy="percept", proposition="look_eight:proposition", evidence_ids=("look_eight",)),
        action("defer_eight", "update_belief", "sal", disposition="eight", mode="defer", head="current",
               policy="wait", evidence_ids=("look_eight",)),
    ]
    path = [a.id for a in actions[:6]]
    if open_slit:
        path.append("open_slit")
    path += ["look_eight", "learn_eight" if open_slit else "defer_eight"]
    return _story("Observatory: the reading from six o'clock", records, actions, path,
                  "Sal wanted a clear-sky exposure, but Noor needed power for the weather recorder.",
                  "The old strip lay beside the slit. Sal had a current sector reading."
                  if open_slit else "The slit stayed shut; the old strip still supplied no current view.")


def harbor_clearance_story(*, report_age=15, fresh_report=False, gate_now="closed"):
    """Minutes after eight: dated open belief survives explicit current-use policy."""
    records = _room(("sal", "Sal", "actor"), ("pavel", "Pavel", "actor"),
                    ("gate", "the harbor gate", "object"), place="the harbor keeper's room")
    records["channels"] += (Channel(id="post", kind="delayed", delay=report_age),)
    records["propositions"] = (
        _p("dated_open", "gate", "position", "open", 0, "harbor-gate"),
        _p("now_open", "gate", "position", "open", report_age, "harbor-gate"),
        _p("actual_now", "gate", "position", gate_now, report_age, "harbor-gate"))
    records["facts"] = (Fact(id="old_gate", carrier="gate", proposition="dated_open"),
                        Fact(id="current_gate", carrier="gate", proposition="actual_now"))
    _views(records, "sal")
    records["belief_policies"] += (BeliefPolicy(id="clearance", kind="freshness", source="sal",
                                               max_age=2, modes=("init", "defer")),)
    records["beliefs"] = (Belief(id="dated_prior", actor="pavel", proposition="dated_open",
                                policy="assumption", source_ids=("pavel",)),)
    records["belief_heads"] = (BeliefHead(id="dated", actor="pavel", belief="dated_prior"),)
    actions = [
        _look("look_old_gate", "sal", "old_gate"),
        action("send_old", "speak", "sal", claim="old_report", audience="pavel", channel="post",
               evidence="look_old_gate"),
        action("arrival", "advance_time", "sal", to_tick=report_age),
        action("receive_old", "deliver", "pavel", claim="old_report", receipt="old_receipt"),
        action("understand_old", "comprehend", "pavel", receipt="old_receipt", comprehension="old_understood"),
        _look("look_current_gate", "sal", "current_gate"),
        action("send_current", "speak", "sal", claim="fresh_report", audience="pavel", channel="voice",
               evidence="look_current_gate"),
        action("receive_current", "deliver", "pavel", claim="fresh_report", receipt="fresh_receipt"),
        action("understand_current", "comprehend", "pavel", receipt="fresh_receipt", comprehension="fresh_understood"),
        action("use_old_now", "update_belief", "pavel", disposition="current", mode="init", head="current",
               policy="clearance", proposition="now_open", comprehension_ids=("old_understood",)),
        action("use_fresh_now", "update_belief", "pavel", disposition="current", mode="init", head="current",
               policy="clearance", proposition="look_current_gate:proposition", comprehension_ids=("fresh_understood",)),
        action("defer_clearance", "update_belief", "pavel", disposition="current", mode="defer", head="current",
               policy="clearance", comprehension_ids=("old_understood",),
               reason="The report describes eight o'clock; our clearance rule requires a report at most two minutes old.",
               reason_support=("send_old:1", "receive_old:1")),
    ]
    path = [a.id for a in actions[:5]]
    if fresh_report:
        path += [a.id for a in actions[5:9]] + ["use_fresh_now"]
    else:
        path += ["use_old_now" if report_age <= 2 else "defer_clearance"]
    return _story("Harbor: Pavel's dated clearance", records, actions, path,
                  "At eight Pavel believed the gate was open. He waited for keeper Sal's message before deciding about current clearance.",
                  "The dated report lay on Pavel's desk beside the current decision. No departure had been performed.")


def harbor_diagnostic_story(*, indicator_visible=False):
    """A finite isolated-test signal encodes exclusion, not a general diagnosis AI."""
    records = _room(("ivo", "Ivo", "actor"), ("ren", "Ren", "actor"),
                    ("motor", "the pump motor", "object"),
                    ("indicator", "the isolated-test indicator (turning excludes motor failure)", "object"),
                    place="the harbor workshop")
    records["propositions"] = (
        _p("diagnosis", "motor", "failure in the isolated test", True, 0, "isolated-motor-test"),
        _p("test_result", "motor", "failure in the isolated test", False, 0, "isolated-motor-test"))
    records["facts"] = (Fact(id="motor_test", carrier="indicator", proposition="test_result"),)
    _views(records, "ivo")
    records["exposures"] = (Exposure(id="motor_test", fact="motor_test", exposed=indicator_visible),)
    records["beliefs"] = (Belief(id="diagnosis", actor="ivo", proposition="diagnosis",
                                policy="assumption", source_ids=("ivo",)),)
    records["belief_heads"] = (BeliefHead(id="diagnosis", actor="ivo", belief="diagnosis"),)
    actions = [
        action("state_diagnosis", "speak", "ivo", claim="diagnosis", audience="ren", channel="voice", belief="diagnosis"),
        _look("inspect_indicator", "ivo", "motor_test"),
        action("clear_motor", "update_belief", "ivo", disposition="diagnostic", mode="resolve", head="diagnosis",
               policy="percept", predecessor="diagnosis", proposition="inspect_indicator:proposition",
               evidence_ids=("inspect_indicator",)),
        action("defer_diagnosis", "update_belief", "ivo", disposition="diagnostic", mode="defer", head="diagnosis",
               policy="wait", predecessor="diagnosis", evidence_ids=("inspect_indicator",),
               reason="The indicator was occluded; I will wait for evidence without withdrawing my prior diagnosis.",
               reason_support=("inspect_indicator:1",)),
    ]
    return _story("Harbor: Ivo's occluded indicator", records, actions,
                  ("state_diagnosis", "inspect_indicator", "clear_motor" if indicator_visible else "defer_diagnosis"),
                  "Ivo suspected motor failure. The isolated test's turning indicator excludes motor failure but cannot diagnose the rest of the pump.",
                  "The pump remained on the bench. No repair or dispatch had been performed.")


def library_ledger_story(*, authoritative=True, current_ledger=True, booking_date=21):
    """Ink is acquired first; only the declared current-ledger policy projects it."""
    records = _room(("nia", "Nia", "actor"), ("omar", "Omar", "actor"),
                    ("ledger", "the booking ledger", "object"),
                    ("seal", "the current-ledger seal", "object"),
                    ("projector", "the shared projector", "object"), place="the library booking desk")
    records["propositions"] = (
        _p("tonight", "nia", "booking date", 14, 0, "projector-booking"),
        _p("assignment", "nia", "booking date", booking_date, 0, "projector-booking"),
        _p("rows", "ledger", "inscription", f"Nia: Wednesday {booking_date}; Omar: Wednesday {21 if booking_date == 14 else 14}", 0, "ledger-ink"),
        _p("current", "ledger", "current booking authority", current_ledger, 0, "ledger-validity"))
    records["facts"] = (Fact(id="rows", carrier="ledger", proposition="rows", assertion="assignment"),
                        Fact(id="current", carrier="seal", proposition="current"))
    _views(records, "nia")
    if authoritative:
        records["authority_policies"] = (AuthorityPolicy(id="ledger_rule", kind="ledger", fact="rows",
            assertion="assignment", validity_fact="current", valid_from=0, valid_until=0),)
    records["belief_policies"] += (BeliefPolicy(id="project", kind="authority", authority="ledger_rule")
                                    if authoritative else BeliefPolicy(id="project", kind="percept"),)
    records["beliefs"] = (Belief(id="tonight", actor="nia", proposition="tonight",
                                policy="assumption", source_ids=("nia",)),)
    records["belief_heads"] = (BeliefHead(id="booking", actor="nia", belief="tonight"),)
    actions = [
        action("state_booking", "speak", "nia", claim="booking", audience="omar", channel="voice", belief="tonight"),
        _look("read_rows", "nia", "rows"),
        _look("check_current", "nia", "current"),
        action("apply_ledger", "update_belief", "nia", disposition="booking", head="booking",
               mode="adopt" if booking_date == 14 else "resolve", policy="project", predecessor="tonight",
               proposition="assignment", evidence_ids=("read_rows", "check_current")),
        action("defer_booking", "update_belief", "nia", disposition="booking", mode="defer", head="booking",
               policy="wait", predecessor="tonight", evidence_ids=("read_rows", "check_current")),
    ]
    return _story("Library: the wrong Wednesday", records, actions,
                  ("state_booking", "read_rows", "check_current",
                   "apply_ledger" if authoritative and current_ledger else "defer_booking"),
                  "Nia had prepared maps for tonight. The library designates its sealed current ledger as authoritative for projector bookings; an unsealed or superseded copy is only writing.",
                  "The ledger stayed open beside Nia's maps. Reading and belief revision had not moved the projector or reassigned a booking.")


def observatory_identity_story(*, identity_policy=True, verified_source=True, same_exposure=True):
    """Declared registry identity, not equal label strings, can defeat independence."""
    records = _room(("sera", "Sera", "actor"), ("tavi", "Tavi", "actor"),
                    ("file_a", "yesterday's file", "object"), ("file_b", "tonight's working file", "object"),
                    ("log", "the exposure registry", "object"), ("seal", "the registry-source seal", "object"),
                    ("old_plate", "yesterday's exposure plate", "object"),
                    ("new_plate", "tonight's exposure plate", "object"))
    second_id = "E17" if same_exposure else "E18"
    sources = ("old_plate",) if same_exposure else ("old_plate", "new_plate")
    records["propositions"] = (
        _p("independent", "file_b", "independent exposure", True, 0, "exposure-origin"),
        _p("identity", "file_b", "independent exposure", not same_exposure, 0, "exposure-origin"),
        _p("a_label", "file_a", "printed exposure ID", "E17", 0, "file-label"),
        _p("b_label", "file_b", "printed exposure ID", second_id, 0, "file-label"),
        _p("log_row", "log", "inscription", f"file A: E17 yesterday; file B: {second_id}", 0, "registry-ink"),
        _p("source_valid", "log", "verified exposure-ID source", verified_source, 0, "source-validity"))
    records["facts"] = (
        Fact(id="a_label", carrier="file_a", proposition="a_label"),
        Fact(id="b_label", carrier="file_b", proposition="b_label"),
        Fact(id="log", carrier="log", proposition="log_row", assertion="identity", source_ids=sources),
        Fact(id="source_valid", carrier="seal", proposition="source_valid"))
    _views(records, "sera")
    if identity_policy:
        records["authority_policies"] = (AuthorityPolicy(id="identity_rule", kind="exposure_identity", fact="log",
            assertion="identity", validity_fact="source_valid", valid_from=0, valid_until=0),)
    records["belief_policies"] += (BeliefPolicy(id="project", kind="authority", authority="identity_rule")
                                    if identity_policy else BeliefPolicy(id="project", kind="percept"),)
    records["beliefs"] = (Belief(id="independent", actor="sera", proposition="independent",
                                policy="assumption", source_ids=("sera",)),)
    records["belief_heads"] = (BeliefHead(id="independence", actor="sera", belief="independent"),)
    actions = [
        action("state_independence", "speak", "sera", claim="independence", audience="tavi", channel="voice", belief="independent"),
        _look("read_a", "sera", "a_label"), _look("read_b", "sera", "b_label"),
        _look("read_log", "sera", "log"), _look("verify_source", "sera", "source_valid"),
        action("apply_identity", "update_belief", "sera", disposition="identity", head="independence",
               mode="resolve" if same_exposure else "adopt", policy="project", predecessor="independent",
               proposition="identity", evidence_ids=("read_a", "read_b", "read_log", "verify_source")),
        action("defer_identity", "update_belief", "sera", disposition="identity", mode="defer", head="independence",
               policy="wait", predecessor="independent", evidence_ids=("read_a", "read_b", "read_log", "verify_source")),
    ]
    return _story("Observatory: yesterday's bright point", records, actions,
                  ("state_independence", "read_a", "read_b", "read_log", "verify_source",
                   "apply_identity" if identity_policy and verified_source else "defer_identity"),
                  "Sera wanted an independent detection. The observatory's identity rule maps files through its verified exposure registry to physical plates; equal printed labels alone prove no identity.",
                  "The two files remained beside the registry. Their origin could not establish whether the bright point existed in tonight's sky.")


def library_booking_story(*, occupied=False):
    """After correcting the projector date, separately arrange the room session."""
    base = library_ledger_story()
    records = dict(base.spec.records)
    slot = "the reading room on Wednesday 21"
    records["entities"] += (Entity(id="edda", name="Edda", kind="actor"),)
    records["parents"] += (Parent(id="edda", parent="room"),)
    records["booking_slots"] = (BookingSlot(id=slot, place="room", booked_by="edda" if occupied else None),)
    records["action_specs"] = (ActionSpec(id="room_session", operation="booking", actor="nia",
        object=slot, destination="room", recipient="nia", result="booked",
        terms="room_on_21", version=1, checkpoint=5),)
    actions = (
        action("ask_room", "create_request", "omar", request="room", responder="nia", action_spec="room_session", version=1),
        action("deliver_room", "deliver_request", "omar", request="room", version=1),
        action("ack_room", "acknowledge_request", "nia", request="room", version=1),
        action("accept_room", "respond_request", "nia", request="room", version=1, decision="accepted"),
        action("check_room", "check_booking", "nia", slot=slot, version=1, terms="room_on_21"),
        action("book_room", "perform_booking", "nia", slot=slot, version=1, terms="room_on_21"),
        action("complete_room", "complete_request", "nia", request="room", version=1,
               table="domain_receipts", receipt="book_room:1"),
    )
    goal = ((query("domain_receipts", "check_room:1", "result", "occupied"),
             query("requests", "room", "response", "accepted")) if occupied else
            (query("requests", "room", "completion_receipt", "book_room:1"),))
    return Scenario(spec=replace(base.spec, title="Library: a date is not a room booking", records=records,
        actions=base.spec.actions + actions, goal=goal),
        path=base.path + tuple(a.id for a in (actions[:5] if occupied else actions)),
        premise="Nia needed both a projector reservation and a reading-room session for the map club. Confirming one would not reserve the other.",
        ending=("The projector date was corrected, but the room session remained occupied. Nia's accepted request was still unfinished."
                if occupied else "Nia had the corrected projector date and a separate room reservation. Neither decision had moved the projector."))
