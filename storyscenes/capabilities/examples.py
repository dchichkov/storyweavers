"""Small integrated conformance worlds, not independent story-specific mechanics."""
from dataclasses import dataclass, replace

from .core import Action, Entity, Query, WorldSpec
from .physical import Container, Grant, LoanTerms, Ownership, Parent, Route
from .social import ActionSpec
from .epistemic import (Attention, Belief, BeliefHead, BeliefPolicy, Channel,
                       Exposure, Fact, Proposition, Result)


@dataclass(frozen=True, kw_only=True)
class Scenario:
    spec: WorldSpec
    path: tuple[str, ...]
    premise: str
    ending: str


def action(action_id, operation_name, actor_id, *, requires=(), reason=None, reason_support=(), **args):
    return Action(id=action_id, operation=operation_name, actor=actor_id, args=args, requires=requires,
                  reason=reason, reason_support=reason_support)


def query(table, key, field, value):
    return Query(table=table, key=key, field=field, value=value)


def loan_story(*, setting="library", grant_available=True, latchable=True, collect=True):
    """G1 loan/return core binds in three settings without changing any operation."""
    names = {
        "library": ("Neighborhood library", "Inez", "Nia", "Sol", "the atlas", "the reading room", "the courtyard"),
        "harbor": ("Harbor workshop", "Tessa", "Rui", "Jo", "the caliper", "the workshop", "the dry bench"),
        "observatory": ("Mountain observatory", "Kit", "Noor", "Vale", "the detector", "the instrument room", "the terrace"),
    }
    title, owner, borrower, helper, item, room, yard = names[setting]
    records = {
        "entities": (
            Entity(id="owner", name=owner, kind="actor"),
            Entity(id="borrower", name=borrower, kind="actor", capacity=5),
            Entity(id="helper", name=helper, kind="actor"),
            Entity(id="room", name=room, kind="place"),
            Entity(id="yard", name=yard, kind="place"),
            Entity(id="item", name=item, kind="object", mass=1),
            Entity(id="bag", name="the carrying bag", kind="container", capacity=3, mass=1),
            Entity(id="cabinet", name="the return cabinet", kind="container", capacity=5, mass=0)),
        "parents": tuple(Parent(id=k, parent=v) for k, v in (
            ("owner", "room"), ("borrower", "room"), ("helper", "room"),
            ("item", "cabinet"), ("bag", "room"), ("cabinet", "room"))),
        "ownership": tuple(Ownership(id=k, owner="owner") for k in ("item", "bag", "cabinet")),
        "containers": (Container(id="bag"), Container(id="cabinet", latchable=latchable)),
        "routes": (Route(id="out", source="room", destination="yard", max_load=3),
                   Route(id="home", source="yard", destination="room", max_load=3)),
        "loan_terms": (LoanTerms(id="terms", version=1, object="item", owner="owner", lender="owner",
                        borrower="borrower", source="cabinet", return_authority="owner",
                        return_recipient="owner", return_destination="cabinet", require_latch=True),),
        "grants": (Grant(id="deposit_grant", issuer="owner", grantee="borrower", object="item",
                         right="deposit", scope="L", destination="cabinet", active=False),),
        "action_specs": (ActionSpec(id="return_task", operation="authorized_deposit", actor="borrower",
                           terms="terms", version=1, checkpoint=5, object="item", destination="cabinet",
                           loan_id="L"),),
    }
    actions = [
        action("ask", "create_request", "owner", request="R", responder="borrower", action_spec="return_task", version=1),
        action("deliver_request", "deliver_request", "owner", request="R", version=1),
        action("accept_request", "respond_request", "borrower", request="R", version=1, decision="accepted"),
        action("offer", "offer_loan", "owner", id="O", terms="terms", version=1, loan_id="L"),
        action("understand", "comprehend_loan", "borrower", offer="O", version=1),
        action("consent", "respond_loan", "borrower", offer="O", version=1),
        action("ready", "readiness", "borrower", id="ready", giver="owner", object="item", operation="activate_loan"),
        action("collect", "activate_loan", "borrower", offer="O", version=1, readiness_id="ready"),
        action("promise", "make_promise", "borrower", promise="P", beneficiary="owner", action_spec="return_task",
               version=1, request="R", loan_id="L", requires=(query("requests", "R", "response", "accepted"),)),
        action("pack", "put", "borrower", object="item", destination="bag"),
        action("lift", "pickup", "borrower", object="bag", source="room",
               requires=(query("parents", "item", "parent", "bag"),)),
        action("outward", "travel", "borrower", route="out",
               requires=(query("parents", "bag", "parent", "borrower"),)),
        action("rest", "put", "borrower", object="bag", destination="yard"),
        action("relift", "pickup", "borrower", object="bag", source="yard"),
        action("homeward", "travel", "borrower", route="home"),
        action("return_offer", "offer_return", "borrower", id="RO", loan_id="L", object="item",
               recipient="helper", destination="helper", version=1),
        action("decline", "refuse", "helper", interaction="return_offer", target="RO", version=1,
               reason_kind="no_authority", reason="I am not authorized to settle this loan."),
    ]
    if grant_available:
        actions.append(action("authorize", "set_grant", "owner", grant="deposit_grant", active=True,
                       requires=(query("return_offers", "RO", "status", "declined"),)))
    actions += [
        action("deposit", "authorized_deposit", "borrower", loan_id="L", object="item", destination="cabinet"),
        action("complete", "complete_request", "borrower", request="R", version=1, receipt="deposit:1"),
        action("close_interval", "advance_time", "owner", to_tick=6,
               requires=(query("loans", "L", "status", "discharged"),)),
        action("assess", "assess_promise", "owner", promise="P", version=1),
    ]
    path = tuple(a.id for a in actions)
    if not collect:
        path = path[:path.index("ready")]
    spec = WorldSpec(title=title, records=records, actions=tuple(actions),
        goal=(query("promises", "P", "status", "fulfilled"), query("loans", "L", "status", "discharged")))
    return Scenario(spec=spec, path=path,
        premise=f"{borrower} needed {item} outside, but {owner} needed it returned to the cabinet by five.",
        ending=f"The cabinet latch was closed. {borrower} could set the empty bag down.")


def delayed_report_story(*, open_after=True, extrapolate=True, second_observation=True, report_reference=0):
    """G2: historical truth survives hidden movement and a late report."""
    if report_reference not in (0, 2) or report_reference == 2 and not extrapolate:
        raise ValueError("A changed reference needs the explicit present extrapolation")
    records = {
        "entities": tuple(Entity(id=i, name=n, kind=k) for i, n, k in (
            ("ari", "Ari", "actor"), ("bo", "Bo", "actor"), ("cy", "Cy", "actor"),
            ("workshop", "the workshop", "place"), ("jetty", "the jetty", "place"),
            ("case", "the instrument case", "container"), ("gauge", "the tide gauge", "object"))),
        "parents": tuple(Parent(id=i, parent=p) for i, p in (
            ("ari", "workshop"), ("bo", "workshop"), ("cy", "workshop"),
            ("case", "workshop"), ("gauge", "case"))),
        "containers": (Container(id="case"),),
        "ownership": (Ownership(id="case", owner="ari"), Ownership(id="gauge", owner="ari")),
        "routes": (Route(id="to_jetty", source="workshop", destination="jetty"),),
        "propositions": (
            Proposition(id="location", subject="gauge", predicate="location", scope="physical",
                        reference_start=0, reference_end=0, result=Result(kind="exact", value="workshop")),
            Proposition(id="prediction", subject="gauge", predicate="location", scope="physical",
                        reference_start=2, reference_end=2, result=Result(kind="exact", value="workshop"))),
        "facts": (Fact(id="where", carrier="gauge", proposition="location", live=True, projection="location"),),
        "exposures": (Exposure(id="view", fact="where"),),
        "channels": (Channel(id="eyes", kind="observation"), Channel(id="post", kind="delayed", delay=2)),
        "attention": (Attention(id="focus", actor="ari", source="gauge", channel="eyes", until=10),),
        "belief_policies": (BeliefPolicy(id="percept", kind="percept"),
                            BeliefPolicy(id="trust_ari", kind="testimony", source="ari"),
                            BeliefPolicy(id="assumption", kind="authored", modes=("init",))),
    }
    if extrapolate:
        records["beliefs"] = (Belief(id="prediction", actor="ari", proposition="prediction",
                                      policy="assumption", source_ids=("ari",)),)
        records["belief_heads"] = (BeliefHead(id="current", actor="ari", belief="prediction"),)
    actions = [
        action("look_old", "observe", "ari", evidence="old", fact="where", exposure="view", channel="eyes", attention="focus",
               requires=(query("clock", "clock", "tick", 0), query("parents", "case", "parent", "workshop"))),
        action("remember", "update_belief", "ari", disposition="remember", mode="init", head="historical",
               policy="percept", proposition="old:proposition", evidence_ids=("old",)),
        action("report", "speak", "ari", claim="report", audience="cy", channel="post",
               **({"evidence": "old"} if report_reference == 0 else {"belief": "prediction"}),
               requires=(query("clock", "clock", "tick", 0),)),
        action("close", "set_container", "bo", container="case", open=False,
               requires=(query("claims", "report", "id", "report"),)),
        action("lift", "pickup", "bo", object="case", source="workshop",
               requires=(query("containers", "case", "open", False),)),
        action("move", "travel", "bo", route="to_jetty",
               requires=(query("parents", "case", "parent", "bo"), query("parents", "ari", "parent", "workshop"))),
        action("put_down", "put", "bo", object="case", destination="jetty"),
        action("later", "advance_time", "ari", to_tick=2,
               requires=(query("parents", "case", "parent", "jetty"), query("claims", "report", "id", "report"))),
        action("receive", "deliver", "cy", claim="report", receipt="mail"),
        action("understand", "comprehend", "cy", receipt="mail", comprehension="understood"),
        action("accept_old", "update_belief", "cy", disposition="accept_old", mode="init", head="cy_old",
               policy="trust_ari", proposition="old:proposition" if report_reference == 0 else "prediction",
               comprehension_ids=("understood",)),
        action("follow", "travel", "ari", route="to_jetty",
               requires=(query("parents", "case", "parent", "jetty"), query("clock", "clock", "tick", 2))),
    ]
    if open_after:
        actions.append(action("open", "set_container", "ari", container="case", open=True))
    if second_observation:
        actions.append(action("look_new", "observe", "ari", evidence="fresh", fact="where", exposure="view",
                              channel="eyes", attention="focus", attempt=True))
    if open_after and second_observation:
        actions.append(action("revise", "update_belief", "ari", disposition="revision",
            mode="resolve" if extrapolate else "init", head="current", policy="percept",
            proposition="fresh:proposition", predecessor="prediction" if extrapolate else None,
            evidence_ids=("fresh",)))
    goal = (query("dispositions", "revision", "id", "revision"),
            query("belief_heads", "cy_old", "id", "cy_old")) if open_after and second_observation else (
        (query("evidence", "fresh", "outcome", "inaccessible"),) if second_observation else
        (query("belief_heads", "cy_old", "id", "cy_old"),))
    return Scenario(spec=WorldSpec(title="The report that arrived late", records=records,
                    actions=tuple(actions), goal=goal), path=tuple(a.id for a in actions),
        premise=("Ari had seen the tide gauge in the workshop" +
                 (" and expected it to remain there." if extrapolate else ".") +
                 " Cy was waiting for Ari's report."),
        ending=("Ari reached the jetty but made no fresh inspection. The report alone established no current location."
                if not second_observation else
                "At the jetty, Ari could finally point to the gauge. The old report still described the earlier visit, not the present one."
                if open_after and report_reference == 0 else
                "The fresh inspection disagreed with Ari's time-two prediction. The earlier workshop visit had not established that prediction."
                if open_after else "The case stayed shut. Ari still lacked a fresh view of the gauge."))


def claimed_return_story():
    """G1 negative: a heard, explicitly adopted claim is still not a return."""
    base = loan_story(grant_available=False)
    records = dict(base.spec.records)
    records.update({
        "propositions": (Proposition(id="settled_claim", subject="item", predicate="return status",
                            result=Result(kind="exact", value="settled"), scope="loan:L",
                            reference_start=0, reference_end=0),),
        "belief_policies": (BeliefPolicy(id="assumption", kind="authored", modes=("init",)),
                            BeliefPolicy(id="trust_borrower", kind="testimony", source="borrower")),
        "beliefs": (Belief(id="assumed_return", actor="borrower", proposition="settled_claim",
                          policy="assumption", source_ids=("borrower",)),),
        "belief_heads": (BeliefHead(id="borrower_return", actor="borrower", belief="assumed_return"),),
        "channels": (Channel(id="voice", kind="speech"),),
    })
    statements = (
        action("claim_return", "speak", "borrower", claim="claimed_return", audience="owner",
               channel="voice", belief="assumed_return"),
        action("hear_return", "deliver", "owner", claim="claimed_return", receipt="return_report"),
        action("understand_return", "comprehend", "owner", receipt="return_report", comprehension="return_understood"),
        action("accept_claim", "update_belief", "owner", disposition="accept_return_claim", mode="init",
               head="owner_return", policy="trust_borrower", proposition="settled_claim",
               comprehension_ids=("return_understood",)),
    )
    prefix = base.path[:base.path.index("deposit")]
    return Scenario(spec=replace(base.spec, title="A report is not a return", records=records,
        actions=base.spec.actions + statements,
        goal=(query("belief_heads", "owner_return", "id", "owner_return"),
              query("loans", "L", "status", "active"))),
        path=prefix + tuple(a.id for a in statements), premise=base.premise,
        ending="The atlas remained in Nia's bag. The return cabinet had received nothing.")


def harbor_site_return_story():
    """The authorized passive return site differs from the collection site."""
    base = loan_story(setting="harbor")
    records = dict(base.spec.records)
    records["entities"] = tuple(replace(e, name="the dry-bench return box") if e.id == "cabinet" else e
                                for e in records["entities"]) + (
        Entity(id="shelf", name="the workshop storage shelf", kind="container", capacity=5, mass=0),)
    records["parents"] = tuple(replace(p, parent="shelf" if p.id == "item" else "yard")
                               if p.id in {"item", "cabinet"} else p for p in records["parents"]) + (
        Parent(id="shelf", parent="room"),)
    records["containers"] += (Container(id="shelf"),)
    records["ownership"] += (Ownership(id="shelf", owner="owner"),)
    records["loan_terms"] = tuple(replace(t, source="shelf") for t in records["loan_terms"])
    travel = action("to_return_site", "travel", "borrower", route="out",
                    requires=(query("grants", "deposit_grant", "active", True),))
    wrong = action("wrong_site", "authorized_deposit", "borrower", loan_id="L", object="item", destination="shelf")
    index = base.path.index("deposit")
    return Scenario(spec=replace(base.spec, title="Harbor: the designated dry-bench return",
        records=records, actions=base.spec.actions + (travel, wrong)),
        path=base.path[:index] + (travel.id,) + base.path[index:],
        premise="Rui needed Tessa's caliper from the workshop shelf. Its designated return box was outside at the dry bench.",
        ending="The caliper lay in the latched dry-bench box. The workshop shelf was not its authorized return site.")


def promise_story(*, deadline="strict_before", perform_at=8, release=False, late_repair=False):
    """G3: the same boundary-time delivery either fulfills or breaches explicit terms."""
    records = {
        "entities": tuple(Entity(id=i, name=n, kind=k) for i, n, k in (
            ("noor", "Noor", "actor"), ("vale", "Vale", "actor"),
            ("dome", "the observatory dome", "place"), ("chart", "the star chart", "object"),
            ("card", "the calibration card", "object"))),
        "parents": (Parent(id="noor", parent="dome"), Parent(id="vale", parent="dome"),
                    Parent(id="chart", parent="noor"), Parent(id="card", parent="noor")),
        "ownership": (Ownership(id="chart", owner="vale"), Ownership(id="card", owner="noor")),
        "action_specs": (ActionSpec(id="delivery", operation="handoff", actor="noor", terms="deliver_chart",
                        version=1, checkpoint=8, deadline=deadline, object="chart", destination="vale", recipient="vale"),
                        ActionSpec(id="another", operation="handoff", actor="noor", terms="another_delivery",
                        version=1, checkpoint=20, object="card", destination="vale", recipient="vale")),
    }
    actions = [
        action("ask", "create_request", "vale", request="R", responder="noor", action_spec="delivery", version=1),
        action("deliver", "deliver_request", "vale", request="R", version=1),
        action("accept", "respond_request", "noor", request="R", version=1, decision="accepted"),
        action("promise", "make_promise", "noor", promise="P", beneficiary="vale", action_spec="delivery", version=1, request="R"),
    ]
    if release:
        actions.append(action("release", "release_promise", "vale", promise="P", version=1))
    actions.append(action("boundary", "advance_time", "vale", to_tick=perform_at))
    if not late_repair:
        actions += [
            action("ready", "readiness", "vale", id="ready", giver="noor", object="chart"),
            action("handoff", "handoff", "noor", object="chart", recipient="vale", readiness_id="ready"),
        ]
    actions.append(action("close", "advance_time", "vale", to_tick=max(9, perform_at + 1)))
    if not release:
        actions.append(action("assess", "assess_promise", "vale", promise="P", version=1))
    if late_repair:
        actions += [
            action("ready", "readiness", "vale", id="ready", giver="noor", object="chart"),
            action("handoff", "handoff", "noor", object="chart", recipient="vale", readiness_id="ready"),
            action("repair", "record_late_repair", "noor", promise="P", version=1, receipt="handoff:1"),
        ]
    actions += [
        action("new_request", "create_request", "vale", request="R2", responder="noor", action_spec="another", version=1),
        action("new_delivery", "deliver_request", "vale", request="R2", version=1),
        action("decline", "refuse", "noor", interaction="request", target="R2", version=1, reason_kind="unwillingness",
               reason="I want to finish my own observation before taking another job."),
    ]
    status = "released" if release else "fulfilled" if not late_repair and (
        perform_at < 8 or (perform_at == 8 and deadline == "inclusive_by")) else "breached"
    return Scenario(spec=WorldSpec(title="A promise at the bell", records=records, actions=tuple(actions),
                    goal=(query("promises", "P", "status", status), query("requests", "R2", "response", "declined"))),
        path=tuple(a.id for a in actions), premise="Vale needed the star chart for the next observing session. Noor had plans of her own.",
        ending="Vale held the star chart. Noor kept her calibration card for her own work.")


def separate_return_request_story():
    """D08: withdrawing outbound work never silently requests the return trip."""
    records = {
        "entities": tuple(Entity(id=i, name=n, kind=k) for i, n, k in (
            ("neri", "Neri", "actor"), ("jules", "Jules", "actor"), ("ivo", "Ivo", "actor"),
            ("workshop", "the workshop", "place"), ("slip", "slip two", "place"),
            ("caliper", "the caliper", "object"))),
        "parents": tuple(Parent(id=i, parent=p) for i, p in (
            ("neri", "workshop"), ("jules", "workshop"), ("ivo", "slip"), ("caliper", "jules"))),
        "ownership": (Ownership(id="caliper", owner="neri"),),
        "routes": (Route(id="walkway", source="workshop", destination="slip", open=False),
                   Route(id="arrive", source="slip", destination="workshop")),
        "action_specs": (
            ActionSpec(id="outbound", operation="handoff", actor="jules", object="caliper",
                       destination="ivo", recipient="ivo", terms="outbound_delivery", version=1, checkpoint=5),
            ActionSpec(id="bring_back", operation="handoff", actor="jules", object="caliper",
                       destination="neri", recipient="neri", terms="return_to_neri", version=1, checkpoint=5)),
    }
    actions = (
        action("ask_out", "create_request", "neri", request="out", responder="jules", action_spec="outbound", version=1),
        action("deliver_out", "deliver_request", "neri", request="out", version=1),
        action("accept_out", "respond_request", "jules", request="out", version=1, decision="accepted"),
        action("promise_out", "make_promise", "jules", promise="P", beneficiary="neri", action_spec="outbound", version=1, request="out"),
        action("withdraw_out", "withdraw_request", "neri", request="out", version=1),
        action("ask_back", "create_request", "neri", request="back", responder="jules", action_spec="bring_back", version=1),
        action("deliver_back", "deliver_request", "neri", request="back", version=1),
        action("accept_back", "respond_request", "jules", request="back", version=1, decision="accepted"),
        action("ready_back", "readiness", "neri", id="ready_back", giver="jules", object="caliper"),
        action("bring_back", "handoff", "jules", object="caliper", recipient="neri", readiness_id="ready_back"),
        action("complete_back", "complete_request", "jules", request="back", version=1, receipt="bring_back:1"),
        action("close", "advance_time", "neri", to_tick=6),
        action("assess", "assess_promise", "neri", promise="P", version=1),
        action("walk", "travel", "jules", route="walkway"),
        action("ivo_arrives", "travel", "ivo", route="arrive"),
        action("ready_out", "readiness", "ivo", id="ready_out", giver="jules", object="caliper"),
        action("deliver_caliper", "handoff", "jules", object="caliper", recipient="ivo", readiness_id="ready_out"),
        action("complete_out", "complete_request", "jules", request="out", version=1, receipt="deliver_caliper:1"),
    )
    return Scenario(spec=WorldSpec(title="A separate request at the workshop", records=records, actions=actions,
        goal=(query("requests", "back", "completion_receipt", "bring_back:1"), query("promises", "P", "status", "breached"))),
        path=tuple(a.id for a in actions[:13]),
        premise="Jules held Neri's caliper at the workshop. Ivo waited at slip two, beyond a closed walkway.",
        ending="Neri held the caliper again. Ivo had received nothing; withdrawing the request had not released Jules from the separate promise.")
