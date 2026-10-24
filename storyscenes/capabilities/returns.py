"""Bounded joint return falsifiers; all effects belong to shared operations.

These scenarios add evidence, not delayed settlement or a new authority model.
Speech has physical speakers/receipts and explicit adoption; it never moves the
prop or changes an owner's grant. Historical loans are executed, never seeded.
"""
from dataclasses import replace

from .core import Entity, WorldSpec
from .epistemic import BeliefPolicy, Channel, Exposure, Fact, Proposition, Result
from .examples import Scenario, action, query
from .physical import Container, Grant, LoanTerms, Ownership, Parent, Route


def _records(*, harbor=False, capacity=3):
    names = (("Tessa", "Rui", "Jo", "the caliper", "the dry bench") if harbor else
             ("Inez", "Nia", "Sol", "the atlas", "the reading room"))
    owner, borrower, receiver, prop, room = names
    return {
        "entities": (
            Entity(id="owner", name=owner, kind="actor"),
            Entity(id="borrower", name=borrower, kind="actor"),
            Entity(id="receiver", name=receiver, kind="actor", capacity=capacity),
            Entity(id="room", name=room, kind="place"),
            Entity(id="prop", name=prop, kind="object", mass=1),
            Entity(id="ballast", name="the bench weight", kind="object", mass=1),
            Entity(id="notice", name="the authorization notice", kind="object")),
        "parents": tuple(Parent(id=key, parent="owner" if key == "prop" else "room")
                         for key in ("owner", "borrower", "receiver", "prop", "ballast", "notice")),
        "ownership": (Ownership(id="prop", owner="owner"),),
        "loan_terms": tuple(
            LoanTerms(id=f"terms{n}", version=1, object="prop", owner="owner",
                      lender="owner" if n == 1 else "receiver", borrower="borrower",
                      source="owner" if n == 1 else "receiver", return_authority="owner",
                      return_recipient="receiver", return_destination="receiver")
            for n in (1, 2)),
        "grants": (
            Grant(id="settle1", issuer="owner", grantee="receiver", object="prop",
                  right="settle", scope="A1", destination="receiver", place="room" if harbor else None),
            Grant(id="settle2", issuer="owner", grantee="receiver", object="prop",
                  right="settle", scope="A2", destination="receiver", active=False),
            Grant(id="receive2", issuer="owner", grantee="receiver", object="prop",
                  right="receive", scope="A2", destination="receiver"),
            Grant(id="lend2", issuer="owner", grantee="receiver", object="prop",
                  right="lend", scope="terms2", destination="borrower", place="room" if harbor else None),
            Grant(id="release2", issuer="owner", grantee="receiver", object="prop",
                  right="release", scope="terms2", destination="receiver", place="room" if harbor else None)),
    }


def _checkout(n):
    lender = "owner" if n == 1 else "receiver"
    return (
        action(f"offer{n}", "offer_loan", lender, id=f"O{n}", terms=f"terms{n}", version=1, loan_id=f"A{n}"),
        action(f"understand{n}", "comprehend_loan", "borrower", offer=f"O{n}", version=1),
        action(f"accept{n}", "respond_loan", "borrower", offer=f"O{n}", version=1),
        action(f"ready{n}", "readiness", "borrower", id=f"ready{n}", giver=lender,
               object="prop", operation="activate_loan"),
        action(f"collect{n}", "activate_loan", "borrower", offer=f"O{n}", version=1, readiness_id=f"ready{n}"))


def _return(offer, loan):
    return action(offer, "offer_return", "borrower", id=offer, loan_id=loan,
                  object="prop", recipient="receiver", destination="receiver", version=1)


def _accept_and_perform(offer, suffix):
    return (
        action(f"yes{suffix}", "respond_return", "receiver", offer=offer, version=1),
        action(f"return_ready{suffix}", "readiness", "receiver", id=f"return_ready{suffix}",
               giver="borrower", object="prop", operation="complete_return"),
        action(f"finish{suffix}", "complete_return", "borrower", offer=offer, version=1,
               readiness_id=f"return_ready{suffix}"))


def _scenario(title, records, selected, *, extra=(), goal=(), premise, ending):
    # Flatten helper groups without inventing scenario-specific operations.
    actions = tuple(replace(a, max_uses=2) for group in selected
                    for a in (group if isinstance(group, tuple) else (group,)))
    return Scenario(spec=WorldSpec(title=title, records=records,
                                  actions=actions + tuple(replace(a, max_uses=2) for a in extra),
                                  goal=tuple(goal), max_steps=45),
                    path=tuple(a.id for a in actions), premise=premise, ending=ending)


def receive_only_story():
    """P-F1: A1 discharged, A2 handed over once, later authority is no receipt."""
    return _scenario("One object, two checkouts", _records(), (
        _checkout(1), _return("old_return", "A1"), _accept_and_perform("old_return", "1"),
        _checkout(2),
        action("receive_ready", "readiness", "receiver", id="receive_ready", giver="borrower", object="prop"),
        action("receive_only", "handoff", "borrower", object="prop", recipient="receiver",
               readiness_id="receive_ready", loan_id="A2"),
        action("later_authority", "set_grant", "owner", grant="settle2", active=True)),
        extra=(_return("stale_old_offer", "A1"),),
        goal=(query("loans", "A1", "status", "discharged"), query("loans", "A2", "status", "active")),
        premise="Nia wanted the atlas for two visits. Sol could receive returns, but his settlement authority differed between the two checkouts.",
        ending="Sol held the atlas again. The first checkout was closed; Nia still owed the second return.")


def stale_authority_story(*, operation="return"):
    """P-F4: an accurate old authority view is adopted after actual revocation.

    The lend branch prepares consent/readiness while authority is valid, then
    attempts activation after revocation. Both failures have positive controls.
    """
    if operation not in {"return", "lend"}:
        raise ValueError("Expected return or lend")
    records = _records()
    grant = "settle1" if operation == "return" else "lend2"
    records.update({
        "propositions": (Proposition(id="old_authority", subject="receiver",
            predicate=f"{operation} authority", scope=grant, reference_start=0, reference_end=0,
            result=Result(kind="exact", value="authorized")),),
        "facts": (Fact(id="notice_fact", carrier="notice", proposition="old_authority"),),
        "exposures": (Exposure(id="notice_view", fact="notice_fact"),),
        "channels": (Channel(id="eyes", kind="observation"), Channel(id="voice", kind="speech")),
        "belief_policies": (BeliefPolicy(id="percept", kind="percept"),
                            BeliefPolicy(id="trust_receiver", kind="testimony", source="receiver")),
    })
    if operation == "return":
        preparation = (_checkout(1), _return("return_offer", "A1"),
                       _accept_and_perform("return_offer", "1")[:2])
        attempt = _accept_and_perform("return_offer", "1")[2]
    else:
        # Move the prop to the designated lender before preparing this checkout.
        preparation = (
            action("owner_ready", "readiness", "receiver", id="owner_ready", giver="owner", object="prop"),
            action("owner_handoff", "handoff", "owner", object="prop", recipient="receiver", readiness_id="owner_ready"),
            _checkout(2)[:4])
        attempt = _checkout(2)[4]
    attempt = replace(attempt,
        requires=(query("belief_heads", "borrower_authority", "belief", "adopted:belief"),),
        reason="I am relying on Sol's earlier authorization report.",
        reason_support=("claim_authority:1", "adopt_authority:1"))
    return _scenario("An authorization report that was already old", records, preparation + (
        action("attend_notice", "attend", "receiver", source="notice", channel="eyes", until=5, attention="focus"),
        action("read_notice", "observe", "receiver", evidence="authority_seen", fact="notice_fact",
               exposure="notice_view", channel="eyes", attention="focus",
               requires=(query("grants", grant, "active", True), query("clock", "clock", "tick", 0))),
        action("remember_authority", "update_belief", "receiver", disposition="remembered", mode="init",
               head="receiver_authority", policy="percept", proposition="authority_seen:proposition",
               evidence_ids=("authority_seen",)),
        action("later", "advance_time", "owner", to_tick=1),
        action("revoke", "set_grant", "owner", grant=grant, active=False),
        action("claim_authority", "speak", "receiver", claim="authority_claim", audience="borrower",
               channel="voice", belief="remembered:belief"),
        action("hear_authority", "deliver", "borrower", claim="authority_claim", receipt="authority_receipt"),
        action("understand_authority", "comprehend", "borrower", receipt="authority_receipt", comprehension="understood"),
        action("adopt_authority", "update_belief", "borrower", disposition="adopted", mode="init",
               head="borrower_authority", policy="trust_receiver", proposition="authority_seen:proposition",
               comprehension_ids=("understood",))),
        extra=(attempt, action("restore", "set_grant", "owner", grant=grant, active=True)),
        goal=(query("grants", grant, "active", False), query("belief_heads", "borrower_authority", "belief", "adopted:belief")),
        premise="Inez had authorized Sol, and a notice recorded that grant. Nia would need the grant to remain valid when she acted.",
        ending="Nia accepted Sol's old report. That acceptance had not moved the atlas or restored Inez's revoked grant.")


def two_offer_story(*, harbor=False):
    """S-F3, with optional Harbor exact dry-bench grant/capacity interventions."""
    records = _records(harbor=harbor, capacity=1 if harbor else 3)
    # The other grant is real but deliberately cannot authorize A1 settlement.
    records["grants"] = tuple(replace(g, active=True) if harbor and g.id == "settle2" else g
                              for g in records["grants"])
    return _scenario("A second return offer at the dry bench" if harbor else "A second return offer", records, (
        _checkout(1), _return("first_return", "A1"),
        action("decline_first", "refuse", "receiver", interaction="return_offer", target="first_return",
               version=1, reason="Please wait while I clear a space.", reason_kind="unwillingness"),
        _return("second_return", "A1"), _accept_and_perform("second_return", "2")),
        extra=(
            action("finish_declined", "complete_return", "borrower", offer="first_return", version=1,
                   readiness_id="return_ready2"),
            action("late_yes_first", "respond_return", "receiver", offer="first_return", version=1),
            action("fill_hands", "pickup", "receiver", object="ballast", source="room"),
            action("free_hands", "put", "receiver", object="ballast", destination="room"),
            action("revoke", "set_grant", "owner", grant="settle1", active=False),
            action("restore", "set_grant", "owner", grant="settle1", active=True)),
        goal=(query("return_offers", "first_return", "status", "declined"),
              query("return_offers", "second_return", "status", "completed"),
              query("loans", "A1", "settlement_receipt", "finish2:1")),
        premise=("Rui planned to borrow Tessa's caliper. Jo was the designated return recipient at the dry bench, with room for only one object." if harbor else
                 "Nia planned to borrow Inez's atlas. Sol was the designated return recipient."),
        ending=("Jo held the caliper at the dry bench; only the separately accepted second offer had closed the loan." if harbor else
                "Sol held the atlas; only the separately accepted second offer had closed the loan."))


def harbor_scoped_lending_story(*, unrestricted=False):
    """The owner permits delegated lending at the dry bench, or everywhere."""
    records = _records(harbor=True)
    records["entities"] += (Entity(id="launch", name="the launch", kind="place"),
                             Entity(id="tray", name="the tool tray", kind="container", capacity=3))
    records["parents"] = tuple(replace(p, parent="receiver" if p.id == "prop" else "launch")
                               if p.id in {"prop", "borrower", "receiver"} else p
                               for p in records["parents"]) + (Parent(id="tray", parent="room"),)
    records["containers"] = (Container(id="tray"),)
    records["routes"] = (Route(id="inside", source="launch", destination="room"),
                          Route(id="aboard", source="room", destination="launch"))
    if unrestricted:
        records["grants"] = tuple(replace(g, place=None) for g in records["grants"])
    travel = (action("borrower_inside", "travel", "borrower", route="inside"),
              action("lender_inside", "travel", "receiver", route="inside"))
    checkout = _checkout(2)
    actions = (travel if not unrestricted else ()) + checkout
    return _scenario("Harbor: the place of lending", records, actions,
        extra=(travel if unrestricted else ()) + (
            action("put_in_tray", "put", "borrower", object="prop", destination="tray"),),
        goal=(query("loans", "A2", "status", "active"),),
        premise="Jo held Tessa's caliper aboard the launch. Rui wanted to borrow it, but Jo had to follow Tessa's current lending grant.",
        ending=("Rui held the caliper aboard the launch under an unrestricted lending grant." if unrestricted else
                "Rui held the caliper at the dry bench. Tessa still owned it; the return obligation had just begun."))


def harbor_scoped_return_story(*, unrestricted=False):
    """Acceptance/readiness travel with the actors; a site restriction does not."""
    scenario = two_offer_story(harbor=True)
    records = dict(scenario.spec.records)
    records["entities"] += (Entity(id="launch", name="the launch", kind="place"),)
    records["routes"] = (Route(id="aboard", source="room", destination="launch"),
                          Route(id="inside", source="launch", destination="room"))
    if unrestricted:
        records["grants"] = tuple(replace(g, place=None) for g in records["grants"])
    outward = tuple(action(f"{actor}_aboard", "travel", actor, route="aboard")
                    for actor in ("borrower", "receiver"))
    back = tuple(action(f"{actor}_inside", "travel", actor, route="inside")
                 for actor in ("borrower", "receiver"))
    path = scenario.path[:-1] + tuple(a.id for a in outward)
    if not unrestricted:
        path += tuple(a.id for a in back)
    path += ("finish2",)
    return replace(scenario, spec=replace(scenario.spec, records=records,
                   title="Harbor: the place of return", actions=scenario.spec.actions + outward + back),
                   path=path, ending=(
                       "Jo held the caliper aboard the launch. The unrestricted grant had allowed the return there."
                       if unrestricted else
                       "Back at the dry bench, Jo held the caliper. The site-restricted grant had allowed the return there."))
