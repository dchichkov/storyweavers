"""Controlled event realization and reading support for capability worlds.

Each supported statement is produced from the event-time record, not final state.
Optional authored opening/closing flourishes provide no automatic QA evidence.
"""
from .core import CapabilityError
from .reading import Document, Statement


def render(spec, state, *, visible=None, premise=None, ending=None, narrative=False):
    selected = {e.id for e in state.events} if visible is None else set(visible)
    if selected - {e.id for e in state.events}:
        raise CapabilityError("Unknown visible event")
    records = {table: {r.id: r for r in rows} for table, rows in spec.records.items()}
    rows = []
    known_placement = {}
    observations, reports = {}, {}
    events = {event.id: event for event in state.events}
    primary_by_event = {}

    def get(table, key):
        return records.get(table, {}).get(key)

    def name(key):
        entity = get("entities", key)
        return entity.name if entity else str(key)

    def add(event, kind, focus, text, *, answer=None, needs=(), question="", refs=(), tick=None):
        sid = f"{event.id}/{kind}/{focus}"
        entities = tuple(dict.fromkeys(k for k in (event.action.actor, focus, *refs) if get("entities", k)))
        rows.append(Statement(id=sid, text=text, kind=kind, focus=focus, answer=answer or text,
                    event_ids=(event.id,), entity_ids=entities,
                    reference_tick=event.tick if tick is None else tick, acquired_tick=event.tick,
                    needs=tuple(needs), question=question))
        return sid

    def event_statement(event_id, kind, focus):
        return f"{event_id}/{kind}/{focus}"

    def reason_support(event):
        support = []
        for eid in event.action.reason_support:
            source = events[eid]
            if eid in selected and eid in primary_by_event:
                support.append(primary_by_event[eid])
            elif eid in selected and source.action.operation == "comprehend":
                receipt = get("claim_receipts", source.data["receipt"])
                support.append(event_statement(receipt.event_id, "receipt", receipt.claim))
            else:
                support.append(f"{eid}/unshown_reason_support")
        return tuple(support)

    def ordinal(number):
        words = ("first", "second", "third", "fourth", "fifth", "sixth", "seventh", "eighth", "ninth", "tenth")
        if number <= len(words):
            return words[number - 1]
        suffix = "th" if 10 <= number % 100 <= 20 else {1: "st", 2: "nd", 3: "rd"}.get(number % 10, "th")
        return f"{number}{suffix}"

    def return_label(offer):
        return f"the {ordinal(events[offer.event_id].data['sequence'])} return offer"

    def loan_label(loan):
        item = get("loan_terms", loan.terms).object
        loans = [row.id for row in records.get("loans", {}).values()
                 if get("loan_terms", row.terms).object == item]
        return f"{ordinal(loans.index(loan.id) + 1)} loan"

    def report_comparisons(event):
        # Only visible direct physical readings can certify a report. An
        # inscription, testimony or a belief by itself is not an oracle.
        for claim_id, (claim_prop, claim_sid) in reports.items():
            candidates = []
            for evidence_id, (prop, sid) in observations.items():
                if (prop.subject, prop.predicate, prop.scope) != (claim_prop.subject, claim_prop.predicate, claim_prop.scope):
                    continue
                if event.action.operation == "speak" and event.data["claim"] != claim_id:
                    continue
                if event.action.operation == "observe" and event.data["evidence"] != evidence_id:
                    continue
                candidates.append((prop, sid))
            exact = [(prop, sid) for prop, sid in candidates
                     if (prop.reference_start, prop.reference_end) == (claim_prop.reference_start, claim_prop.reference_end)]
            if exact and claim_prop.result.kind == "exact":
                prop, sid = exact[-1]
                agrees = prop.result == claim_prop.result
                text = ("The report matched the inspection for that time. " if agrees else
                        "The report did not match the inspection for that time. ") + sentence(proposition_text(prop)) + "."
                add(event, "historical_truth", claim_id, text, needs=(claim_sid, sid),
                    refs=(prop.subject,), tick=prop.reference_start,
                    question=f"Did this report agree with what was observed for time {prop.reference_start}?")
            # A later contradictory view is a change, not a historical lie.
            elif event.action.operation == "observe" and claim_prop.result.kind == "exact":
                old = [(p, s) for p, s in observations.values()
                       if (p.subject, p.predicate, p.scope, p.reference_start, p.reference_end, p.result) ==
                          (claim_prop.subject, claim_prop.predicate, claim_prop.scope,
                           claim_prop.reference_start, claim_prop.reference_end, claim_prop.result)]
                later = [(p, s) for p, s in candidates if claim_prop.reference_end is not None
                         and p.reference_start is not None and claim_prop.reference_end < p.reference_start
                         and p.result != claim_prop.result]
                if old and later:
                    prop, sid = later[-1]
                    add(event, "later_change", claim_id,
                        f"The earlier and later inspections showed a change. {sentence(proposition_text(prop))}; the report still described time {claim_prop.reference_start}.",
                        needs=(claim_sid, old[-1][1], sid), refs=(prop.subject,), tick=prop.reference_start,
                        question="Did the later inspection make the earlier report false at its own time?")

    def physical_snapshot(event, item, primary, *, prior=None):
        path, current = [item], item
        while (parent := get("parents", current)) is not None:
            current = parent.parent
            path.append(current)
        place = next((key for key in path if get("entities", key).kind == "place"), None)
        carrier = next((key for key in path[1:] if get("entities", key).kind == "actor"), None)
        needs = (primary,) if prior is None else (prior, primary)
        if place is not None:
            containers = [key for key in path[1:-1] if get("entities", key).kind == "container"]
            containment = " inside " + " inside ".join(name(key) for key in containers) if containers else ""
            add(event, "location", item, f"{sentence(name(item))} was{containment} at {name(place)}.",
                needs=needs, refs=tuple(path[1:]), question=f"Where was {name(item)} at this point?")
        add(event, "holder", item,
            (f"{name(carrier)} held {name(item)}." if narrative else f"{name(carrier)} physically carried {name(item)}.")
            if carrier else f"No one was physically holding {name(item)}.",
            needs=needs, refs=(carrier,) if carrier else (), question=f"Who physically held {name(item)} at this point?")
        loans = [loan for loan in records.get("loans", {}).values()
                 if get("loan_terms", loan.terms).object == item and loan.status == "active"]
        if loans and (carrier is None or event.action.operation == "activate_loan" or event.data.get("loan_id")):
            loan = loans[0]
            terms = get("loan_terms", loan.terms)
            add(event, "owner", item, f"{name(terms.owner)} still owned {name(item)}.",
                needs=needs, refs=(terms.owner,), question=f"Who owned {name(item)} at this point?")
            add(event, "borrower", item, f"{name(loan.borrower)} remained responsible for returning {name(item)}.",
                needs=needs, refs=(loan.borrower,), question=f"Who was responsible for returning {name(item)}?")
            add(event, "loan_status", loan.id, f"The {loan_label(loan)} of {name(item)} was still outstanding.",
                needs=needs, refs=(item, loan.borrower), question=f"Was the {loan_label(loan)} of {name(item)} settled at this point?")

    def visible_contents(event, moved, primary):
        # A moved closed container is not an observation of its contents. Even
        # open contents need their own earlier visible placement support.
        for item, support in tuple(known_placement.items()):
            if item == moved:
                continue
            current = item
            while (parent := get("parents", current)) is not None:
                current = parent.parent
                container = get("containers", current)
                if container is not None and not container.open:
                    break
                if current == moved:
                    physical_snapshot(event, item, primary, prior=support)
                    break

    def action_phrase(action_spec, *, speaker=None, listener=None):
        target = name(action_spec.object) if action_spec.object else "the requested result"
        destination = name(action_spec.destination) if action_spec.destination else ""
        if action_spec.destination and speaker == action_spec.destination:
            destination = "me"
        elif action_spec.destination and listener == action_spec.destination:
            destination = "you"
        if action_spec.operation == "inspection" and action_spec.inspection_fact and action_spec.result_value is not None:
            fact = get("facts", action_spec.inspection_fact)
            proposition = get("propositions", fact.proposition)
            return f"inspect {target} and certify its {proposition.predicate} as {action_spec.result_value}"
        phrases = {
            "authorized_deposit": f"return {target} to {destination}",
            "complete_return": f"hand {target} back to {destination}",
            "handoff": f"hand {target} to {destination}",
            "pickup": f"collect {target}", "put": f"put {target} in {destination}",
            "travel": f"go to {destination}", "booking": f"book {target}",
            "inspection": f"inspect {target}", "observe": f"inspect {target}",
            "activate_loan": f"collect {target} on loan",
        }
        return phrases.get(action_spec.operation, f"perform {action_spec.operation} with {target}")

    def show_reference(prop):
        return prop.reference_start is not None and not (
            narrative and prop.reference_start == prop.reference_end == 0
            and not any(c.kind == "delayed" for c in records.get("channels", {}).values()))

    def proposition_text(prop):
        result = prop.result
        if result.kind == "unknown":
            text = f"the check did not establish {name(prop.subject)}'s {prop.predicate}"
        elif result.kind == "partial":
            text = f"the check left {name(prop.subject)}'s {prop.predicate} unresolved"
        else:
            value = name(result.value) if isinstance(result.value, str) else str(result.value).lower()
            if prop.predicate == "location":
                text = f"{name(prop.subject)} was at {value}"
            elif narrative and prop.predicate == "destination":
                text = f"{name(prop.subject)} named {value} as its destination"
            else:
                text = f"{name(prop.subject)}'s {prop.predicate} was {value}"
        if show_reference(prop):
            text += f" at time {prop.reference_start}"
            if prop.reference_end != prop.reference_start:
                text += f" through {prop.reference_end}"
        return text

    def sentence(text):
        return text[:1].upper() + text[1:]

    if premise:
        rows.append(Statement(id="opening", text=premise, kind="flourish", focus="", answer="", event_ids=()))
    for event in state.events:
        for change in event.changes:
            records.setdefault(change.table, {})[change.key] = change.after
            if change.table == "parents":
                known_placement.pop(change.key, None)
        if event.id not in selected:
            continue
        op, data, actor = event.action.operation, event.data, name(event.action.actor)
        focus, primary = event.action.actor, None
        if op in {"pickup", "put", "handoff", "activate_loan", "complete_return", "authorized_deposit"}:
            receipt = get("receipts", data["receipt"])
            focus = receipt.object
            if op == "pickup":
                text = f"{actor} picked up {name(focus)} from {name(receipt.source)}."
            elif op == "activate_loan":
                text = f"{actor} collected {name(focus)}. The loan had now begun."
                if narrative:
                    text = f"{actor} collected {name(focus)} on loan."
            elif op == "authorized_deposit":
                text = f"{actor} returned {name(focus)} to {name(receipt.destination)}."
                if data.get("latched"):
                    text += " The latch clicked shut."
            elif op == "put":
                preposition = "in" if get("entities", receipt.destination).kind == "container" else "at"
                text = f"{actor} put {name(focus)} {preposition} {name(receipt.destination)}."
                if narrative and preposition == "at":
                    text = f"{actor} set {name(focus)} down at {name(receipt.destination)}."
            else:
                text = f"{actor} handed {name(focus)} to {name(receipt.destination)}."
            if receipt.tick:
                text = f"At time {receipt.tick}, " + text
            primary = add(event, "placement", focus, text, refs=(receipt.destination,),
                          question=f"What did {actor} do with {name(focus)} at this point?")
            physical_snapshot(event, focus, primary)
            visible_contents(event, focus, primary)
            known_placement[focus] = primary
            if receipt.loan_id:
                loan = get("loans", receipt.loan_id)
                if op in {"complete_return", "authorized_deposit"}:
                    terms = get("loan_terms", loan.terms)
                    add(event, "owner", focus, f"{name(terms.owner)} still owned {name(focus)}.",
                        needs=(primary,), refs=(terms.owner,), question=f"Who owned {name(focus)} after the return?")
                    settlement_needs = [primary]
                    offer_text = ""
                    if op == "complete_return":
                        offer = get("return_offers", data["offer"])
                        settlement_needs += [event_statement(offer.event_id, "return_offer", offer.id),
                                             event_statement(offer.response_event_id, "response", offer.id)]
                        offer_text = f" through {return_label(offer)}"
                    add(event, "loan_status", receipt.loan_id,
                        f"That authorized return settled {name(loan.borrower)}'s {loan_label(loan)} of {name(focus)}{offer_text}.",
                        needs=settlement_needs, refs=(loan.borrower, focus), question=f"Was the {loan_label(loan)} of {name(focus)} settled?")
                    if op == "complete_return":
                        grant = get("grants", data["authority_grant"])
                        scope = (f"only at {name(grant.place)}" if grant.place is not None
                                 else "without restricting the place")
                        add(event, "authority", grant.id,
                            f"{name(grant.issuer)} had authorized {name(grant.grantee)} to settle this loan {scope}.",
                            needs=settlement_needs, refs=(grant.issuer, grant.grantee),
                            question=f"Where could {name(grant.grantee)} settle this loan under the grant?")
        elif op == "travel":
            focus = event.action.actor
            text = f"{actor} went from {name(data['source'])} to {name(data['destination'])}."
            supports, carried_ids = (), ()
            if narrative:
                carried_ids = tuple(p.id for p in records.get("parents", {}).values()
                                    if p.parent == focus and p.id in known_placement)
                supports = tuple(known_placement[key] for key in carried_ids)
                if carried_ids:
                    text = f"{actor} carried {' and '.join(name(key) for key in carried_ids)} from {name(data['source'])} to {name(data['destination'])}."
            primary = add(event, "location", focus, text,
                          needs=supports, refs=(data["destination"], *carried_ids), question=f"Where did {actor} go?")
            visible_contents(event, focus, primary)
        elif op == "readiness":
            focus = data["object"]
            ready = "I'm ready for" if narrative else "I am ready to receive"
            primary = add(event, "readiness", focus, f'"{ready} {name(focus)}," {actor} told {name(data["giver"])}.',
                          question=f"Was {actor} ready to receive {name(focus)}?")
        elif op == "offer_loan":
            terms = get("loan_terms", data["terms"])
            focus = data["offer"]
            primary = add(event, "loan_offer", focus,
                f'{actor} offered {name(terms.borrower)} a loan of {name(terms.object)}. "It must come back to {name(terms.return_destination)}," {actor} said.',
                refs=(terms.borrower, terms.object), question=f"What return condition did {actor} give?")
            grants = [get("grants", key) for key in data.get("authority_grants", ())]
            if grants:
                places = tuple(dict.fromkeys(g.place for g in grants if g.place is not None))
                text = (f"{name(terms.owner)}'s grant limited this lending and release to {' and '.join(name(p) for p in places)}."
                        if places else f"{name(terms.owner)}'s grant did not restrict the place of this lending and release.")
                add(event, "authority", focus, text, needs=(primary,), refs=(terms.owner, *places),
                    question=f"Where did {name(terms.owner)} authorize this loan to be made?")
        elif op == "comprehend_loan":
            focus = data["offer"]
            primary = add(event, "terms_understood", focus, f"{actor} understood the loan's return conditions.")
        elif op in {"respond_loan", "respond_return"} or (op == "refuse" and "offer" in data):
            focus = data["offer"]
            offer = get("loan_offers" if data["kind"] == "loan" else "return_offers", focus)
            kind = "loan_offer" if data["kind"] == "loan" else "return_offer"
            needs = (event_statement(offer.event_id, kind, focus),)
            label = "the loan offer" if data["kind"] == "loan" else return_label(offer)
            text = f'"{"Yes" if data["decision"] == "accepted" else "No"}," {actor} answered {label}.'
            if narrative and data["kind"] == "loan" and data["decision"] == "accepted":
                terms = get("loan_terms", offer.terms)
                text = f'"I\'ll bring {name(terms.object)} back to {name(terms.return_destination)}," {actor} agreed.'
            primary = add(event, "response", focus, text,
                          needs=needs, question=f"How did {actor} answer {label}?")
        elif op == "offer_return":
            focus = data["offer"]
            offer = get("return_offers", focus)
            primary = add(event, "return_offer", focus,
                f'"Can you accept {name(data["object"])} as my return?" {actor} asked {name(data["recipient"])}. This was {return_label(offer)} for this loan.',
                refs=(data["object"], data["recipient"]), question=f"Whom did {actor} address with {return_label(offer)}?")
        elif op == "set_grant":
            grant = get("grants", data["grant"])
            focus = grant.id
            purpose = {
                "settle": f"settle the specified loan of {name(grant.object)} when receiving it",
                "deposit": f"return {name(grant.object)} to {name(grant.destination)}",
                "receive": f"receive {name(grant.object)}",
                "lend": f"lend {name(grant.object)}",
                "release": f"release {name(grant.object)} for collection",
            }[grant.right]
            if grant.place is not None:
                purpose += f", only at {name(grant.place)}"
            primary = add(event, "authority", focus,
                f'{actor} {"authorized" if grant.active else "withdrew authorization from"} {name(grant.grantee)} to {purpose}.',
                refs=(grant.grantee, grant.object, grant.destination))
        elif op == "set_container":
            focus = event.action.args["container"]
            box = get("containers", focus)
            primary = add(event, "container", focus, f'{actor} {"opened" if box.open else "closed"} {name(focus)}.')
        elif op in {"create_request", "deliver_request"}:
            req = get("requests", data["request"])
            terms = get("action_specs", req.action_spec)
            focus = req.id
            if op == "create_request":
                primary = add(event, "intention", focus,
                    f"{actor} wanted to ask {name(req.responder)} to {action_phrase(terms)}.")
            else:
                primary = add(event, "request", focus,
                    f'"Will you {action_phrase(terms, speaker=req.requester if narrative else None)}?" {actor} asked {name(req.responder)}.',
                    refs=(req.responder,), question=f"What did {actor} ask {name(req.responder)} to do?")
        elif op in {"respond_request", "refuse"} and "request" in data:
            req = get("requests", data["request"])
            terms = get("action_specs", req.action_spec)
            focus = req.id
            text = f'"{"Yes, I accept" if req.response == "accepted" else "No, I decline"}," {actor} answered {name(req.requester)}\'s request to {action_phrase(terms)}.'
            if narrative:
                reply = "I will" if req.response == "accepted" else "No, I won't"
                text = f'"{reply} {action_phrase(terms, speaker=event.action.actor, listener=req.requester)}," {actor} told {name(req.requester)}.'
            primary = add(event, "response", focus, text,
                answer=f"{actor} {req.response} {name(req.requester)}'s request to {action_phrase(terms)}.",
                needs=(event_statement(req.delivery_event, "request", focus),),
                refs=(req.requester,), question=f"How did {actor} answer this request?")
        elif op == "withdraw_request":
            req = get("requests", data["request"])
            terms = get("action_specs", req.action_spec)
            focus = req.id
            primary = add(event, "withdrawal", focus,
                f'{actor} withdrew the request to {action_phrase(terms)}. The earlier response was still {req.response}.',
                needs=(event_statement(req.delivery_event, "request", focus),),
                question=f"What happened to the request to {action_phrase(terms)}?")
        elif op == "complete_request":
            req = get("requests", data["request"])
            terms = get("action_specs", req.action_spec)
            focus = req.id
            primary = add(event, "request_status", focus,
                f'{actor} had completed the accepted request to {action_phrase(terms)}.',
                needs=(event_statement(req.delivery_event, "request", focus),
                       event_statement(req.response_event, "response", focus)),
                question=f"Was the request to {action_phrase(terms)} completed?")
        elif op == "make_promise":
            promise = get("promises", data["promise"])
            terms = get("action_specs", promise.action_spec)
            focus = promise.id
            preposition = "before" if terms.deadline == "strict_before" else "by"
            primary = add(event, "promise", focus,
                f'"I promise to {action_phrase(terms, speaker=promise.promisor if narrative else None, listener=promise.beneficiary if narrative else None)} {preposition} time {terms.checkpoint}," {actor} told {name(promise.beneficiary)}.',
                question=f"What did {actor} promise, and when was it due?")
        elif op in {"assess_promise", "release_promise", "record_late_repair"}:
            promise = get("promises", data["promise"])
            terms = get("action_specs", promise.action_spec)
            focus = promise.id
            task = action_phrase(terms)
            needs = [event_statement(promise.created_event, "promise", focus)]
            if op == "assess_promise":
                bound = "before" if terms.deadline == "strict_before" else "by"
                text = (f"{name(promise.promisor)} had kept the promise to {task} {bound} time {terms.checkpoint}." if promise.status == "fulfilled"
                        else f"{name(promise.promisor)} had not kept the promise to {task} {bound} time {terms.checkpoint}. That promise was breached; a later action could not make it timely.")
                if narrative and promise.status != "fulfilled":
                    text = f"{name(promise.promisor)} had missed the deadline: the promise was to {task} {bound} time {terms.checkpoint}."
            elif op == "release_promise":
                text = f'{actor} released {name(promise.promisor)} from the undertaking to {task}.'
                if promise.status == "breached":
                    text += " Its earlier breach remained."
            else:
                text = f"{actor} completed the undertaking to {task} late. That repair did not erase the earlier breach."
            primary = add(event, "promise_status", focus, text, needs=needs,
                          question=f"What became of {name(promise.promisor)}'s promise to {task}?")
        elif op == "observe":
            evidence = get("evidence", data["evidence"])
            prop = get("propositions", evidence.proposition)
            focus = evidence.id
            inspection = "tried to inspect" if evidence.outcome == "inaccessible" else "inspected"
            instrument = get("channels", evidence.channel).instrument
            introduction = f"{actor} {inspection} {name(evidence.source)}."
            if narrative and instrument:
                introduction = f"Using {name(instrument)}, {actor} {inspection} {name(evidence.source)}."
            primary = add(event, "observation", focus,
                f"{introduction} {sentence(proposition_text(prop))}.",
                refs=(evidence.source, prop.subject, instrument), tick=prop.reference_start,
                question=f"What did {actor}'s inspection establish?")
            fact = get("facts", evidence.fact)
            if evidence.outcome == "exact" and fact.assertion is None and (
                    fact.projection == "location" or fact.carrier == prop.subject):
                observations[focus] = (prop, primary)
        elif op == "speak":
            claim = get("claims", data["claim"])
            prop = get("propositions", claim.proposition)
            focus = claim.id
            text = f'{actor} sent {name(claim.audience)} this report: "{sentence(proposition_text(prop))}."'
            if narrative and get("channels", claim.channel).kind == "speech":
                text = f'"{sentence(proposition_text(prop))}," {actor} told {name(claim.audience)}.'
            primary = add(event, "claim", focus, text,
                refs=(claim.audience, prop.subject), tick=prop.reference_start,
                question=f"What did {actor} report, and what time did it describe?" if show_reference(prop)
                         else f"What did {actor} report?")
            reports[focus] = (prop, primary)
        elif op == "deliver":
            receipt = get("claim_receipts", data["receipt"])
            claim = get("claims", receipt.claim)
            prop = get("propositions", claim.proposition)
            focus = claim.id
            text = f"At time {receipt.received_at}, {actor} received {name(claim.speaker)}'s report."
            if narrative and get("channels", claim.channel).kind == "speech":
                text = f"{actor} heard {name(claim.speaker)}'s report."
            primary = add(event, "receipt", focus, text,
                needs=(event_statement(claim.event_id, "claim", claim.id),),
                tick=prop.reference_start,
                question=f"Did {actor} receive this report?")
            if prop.reference_end is not None and prop.reference_end < receipt.received_at:
                add(event, "present_applicability", focus,
                    f"The report described time {prop.reference_start}, not its arrival at time {receipt.received_at}. It did not establish the current {prop.predicate}.",
                    needs=(primary,), refs=(prop.subject,),
                    question="Did the dated report establish the situation when it arrived?")
        elif op == "update_belief":
            disposition = get("dispositions", data["disposition"])
            focus = disposition.head
            basis = []
            sources = []
            belief_answer = None
            for evidence_id in disposition.evidence_ids:
                evidence = get("evidence", evidence_id)
                basis.append(event_statement(evidence.event_id, "observation", evidence_id))
                sources.append(name(evidence.source))
            for comprehension_id in disposition.comprehension_ids:
                comprehension = get("comprehensions", comprehension_id)
                receipt = get("claim_receipts", comprehension.receipt)
                claim = get("claims", receipt.claim)
                basis.append(event_statement(receipt.event_id, "receipt", claim.id))
                sources.append(f"{name(claim.speaker)}'s report")
            if disposition.belief:
                prop = get("propositions", disposition.proposition)
                verb = "revised the earlier belief and accepted" if disposition.mode == "resolve" else "accepted"
                text = f"{actor} {verb} that {proposition_text(prop)}."
                if narrative and disposition.mode == "resolve":
                    belief = get("beliefs", disposition.belief)
                    earlier = get("beliefs", belief.predecessor)
                    if earlier:
                        old = get("propositions", earlier.proposition)
                        text = f"{actor} had believed that {proposition_text(old)}. Now {actor} accepted that {proposition_text(prop)}."
                if narrative and disposition.mode in {"init", "adopt"} and len(disposition.comprehension_ids) == 1:
                    comprehension = get("comprehensions", disposition.comprehension_ids[0])
                    receipt = get("claim_receipts", comprehension.receipt)
                    claim = get("claims", receipt.claim)
                    if get("belief_policies", disposition.policy).kind == "testimony" and claim.proposition == prop.id:
                        belief_answer, text = text, f"{actor} believed {name(claim.speaker)}'s report."
            else:
                text = f"{actor} {'deferred a decision' if disposition.mode == 'defer' else 'rejected the report'}. No opposite belief was established."
            primary = add(event, "belief", focus, text,
                          answer=belief_answer, needs=tuple(basis),
                          tick=prop.reference_start if disposition.belief else event.tick,
                          question=f"What did {actor} decide to believe?")
            if sources and not event.action.reason:
                policy = get("belief_policies", disposition.policy)
                source_text = " and ".join(dict.fromkeys(sources))
                if policy.kind == "authority":
                    authority = get("authority_policies", policy.authority)
                    rule = "current-ledger authority" if authority.kind == "ledger" else "verified exposure-identity"
                    explanation = f"{actor}'s decision used {source_text} under the declared {rule} rule. Reading an inscription alone did not authorize that inference."
                elif policy.kind == "freshness":
                    explanation = f"{actor}'s decision used {source_text} under the rule allowing reports at most {policy.max_age} time units old. This was a policy-supported belief, not a fresh observation."
                elif policy.kind == "defer":
                    explanation = f"{actor} deferred on the basis of {source_text}. That decision did not establish an opposite belief."
                else:
                    explanation = f"{actor}'s recorded basis for the belief was {source_text}."
                add(event, "why", focus, explanation, needs=(primary,),
                    tick=prop.reference_start if disposition.belief else event.tick,
                    question=f"What evidence supported {actor}'s belief decision?")
        elif op in {"perform_booking", "check_booking"}:
            focus = data["object"]
            text = (f"{actor} booked {focus}." if op == "perform_booking" else
                    f"{actor} checked {focus}; it was {data['result']}.")
            primary = add(event, "performance", focus, text)
        elif narrative and op == "advance_time" and event.action.reason:
            primary = add(event, "elapsed_time", focus, f"The clock reached {data['to_tick']}.",
                          tick=data["to_tick"], question="What time had the clock reached?")
        # Bookkeeping events remain in the trace; absence of a paragraph is not
        # evidence of nonperformance. Deadline statements come from assessment.
        if op in {"observe", "speak"}:
            report_comparisons(event)
        if event.action.reason and primary:
            reference = next(s.reference_tick for s in rows if s.id == primary)
            add(event, "why", focus, f'"{event.action.reason.rstrip(".")}," {actor} explained.',
                answer=f"{actor} gave this reason: {event.action.reason}",
                needs=(primary,) + (reason_support(event) if narrative else ()),
                tick=reference, question=f"Why did {actor} make this choice?")
        if primary:
            primary_by_event[event.id] = primary
    if ending:
        rows.append(Statement(id="ending", text=ending, kind="flourish", focus="", answer="", event_ids=()))
    document = Document(title=spec.title, statements=tuple(rows))
    if narrative:
        from .narrative import compose
        return compose(spec, state, document, complete=selected == set(events))
    return document


def render_story(spec, state, **kwargs):
    """Readable, evidence-preserving view; render() retains the diagnostic view."""
    return render(spec, state, narrative=True, **kwargs)
