"""Select and group event-backed prose without changing simulation order.

The diagnostic document remains the source of reading evidence. Omitted facts
are omitted from QA too; retained facts bring their visible dependencies.
"""
from dataclasses import replace

from .reading import Document, Reader, Statement


def compose(spec, state, document, *, complete):
    events = {event.id: event for event in state.events}
    by_id = {s.id: s for s in document.statements}
    reader = Reader(document)
    available = {s.id for s in document.statements if reader.support(s) is not None}
    parents = {p.id: p.parent for p in spec.records.get("parents", ())}
    unheld = set()
    for event in state.events:
        parents.update({c.key: c.after.parent for c in event.changes if c.table == "parents"})
        for statement in document.statements:
            if statement.kind != "borrower" or event.id not in statement.event_ids:
                continue
            current = parents.get(statement.focus)
            while current and state.get("entities", current).kind != "actor":
                current = parents.get(current)
            if current is None:
                unheld.add(statement.id)
    requests = {s.focus for s in document.statements if s.kind == "request" and s.id in available}
    quiet = {"readiness", "terms_understood", "request_status", "holder", "location", "borrower", "owner", "loan_status",
             "historical_truth", "later_change"}
    chosen, owners, responsibilities = set(), set(), set()
    for statement in document.statements:
        if statement.id not in available:
            continue
        event = events.get(statement.event_ids[0]) if statement.event_ids else None
        op = event.action.operation if event else None
        kind = statement.kind
        keep = kind not in quiet
        if kind == "intention" and statement.focus in requests:
            keep = False
        if kind == "location" and op == "travel" and statement.focus == event.action.actor:
            keep = True
        if kind == "owner" and statement.focus not in owners:
            keep = True
            owners.add(statement.focus)
        # Setting down a borrowed object does not remove responsibility. Say
        # this once at a meaningful pause, not after every parent-path change.
        if (kind == "borrower" and op == "put" and statement.id in unheld
                and statement.focus != event.action.args["object"] and statement.focus not in responsibilities):
            keep = True
            responsibilities.add(statement.focus)
        if kind == "loan_status" and op in {"authorized_deposit", "complete_return"}:
            keep = True
        if kind == "belief" and op == "update_belief":
            disposition = state.get("dispositions", event.data["disposition"])
            if disposition.mode == "init" and state.get("belief_policies", disposition.policy).kind == "percept":
                keep = False
        if kind == "why" and event and not event.action.reason:
            keep = False
        if keep:
            chosen.add(statement.id)

    closing = None
    if complete and not any(s.id == "ending" for s in document.statements):
        subjects = {t.object for t in state.tables.get("loan_terms", {}).values()}
        subjects.update(state.get("action_specs", p.action_spec).object
                        for p in state.tables.get("promises", {}).values())
        last_transfer = next((e for e in reversed(state.events)
                              if e.action.operation in {"pickup", "handoff", "authorized_deposit", "complete_return"}), None)
        if last_transfer:
            subjects.add(last_transfer.data["object"])
        for statement in reversed(document.statements):
            if statement.kind not in {"location", "holder"} or statement.focus not in subjects or statement.id not in available:
                continue
            # A snapshot can become an ending only if its whole parent path
            # remains unchanged afterward. Never turn an old location into a
            # claim about the present, or reveal hidden container contents.
            path, current = set(), statement.focus
            while current not in path:
                path.add(current)
                parent = state.get("parents", current)
                if parent is None:
                    break
                current = parent.parent
            if statement.kind == "holder" and not any(state.get("entities", key).kind == "actor" for key in path):
                continue
            index = next(i for i, e in enumerate(state.events) if e.id == statement.event_ids[0])
            if any(c.table == "parents" and c.key in path
                   for e in state.events[index + 1:] for c in e.changes):
                continue
            if any(statement.id in by_id[sid].needs for sid in chosen):
                continue
            closing = replace(statement, paragraph="scene_ending", reference_tick=state.tick,
                              question=statement.question.replace("at this point", "at the end of the story"))
            chosen.add(statement.id)
            break

    pending = list(chosen)
    while pending:
        sid = pending.pop()
        for need in by_id[sid].needs:
            if need not in chosen:
                chosen.add(need)
                pending.append(need)
    rows = [replace(s, paragraph=s.event_ids[0] if s.event_ids else s.id)
            for s in document.statements if s.id in chosen and (closing is None or s.id != closing.id)]
    # Adjacent physical beats can share a paragraph; dialogue and changes of
    # actor/time keep their own boundaries. Evidence spans stay sentence-exact.
    physical = {"pickup", "put", "travel", "set_container"}
    previous, group, beats = None, None, 0
    questions_by_event = {}
    for row in rows:
        if row.question and row.event_ids:
            questions_by_event.setdefault(row.event_ids[0], set()).add(row.question)
    group_questions = set()
    grouped = []
    for row in rows:
        event = events.get(row.event_ids[0]) if row.event_ids else None
        if event != previous:
            questions = questions_by_event.get(event.id, set()) if event else set()
            continuation = (event and previous and event.action.operation in physical
                            and previous.action.operation in physical and event.tick == previous.tick
                            and event.action.actor == previous.action.actor and beats < 3
                            and not questions.intersection(group_questions))
            group = group if continuation else row.paragraph
            beats = beats + 1 if continuation else 1
            group_questions = group_questions | questions if continuation else set(questions)
            previous = event
        grouped.append(replace(row, paragraph=group or row.paragraph))
    rows = grouped
    # One heard-and-believed sentence can retain two independently maskable
    # assertions. Merge only an immediately adjacent, single-report adoption.
    for index in range(1, len(rows)):
        previous, current = rows[index - 1:index + 1]
        if previous.kind != "receipt" or current.kind != "belief" or current.needs != (previous.id,):
            continue
        event = events[current.event_ids[0]]
        disposition = state.get("dispositions", event.data["disposition"])
        if (disposition.mode not in {"init", "adopt"} or disposition.evidence_ids
                or len(disposition.comprehension_ids) != 1
                or state.get("belief_policies", disposition.policy).kind != "testimony"):
            continue
        comprehension = state.get("comprehensions", disposition.comprehension_ids[0])
        receipt = state.get("claim_receipts", comprehension.receipt)
        if state.get("claims", receipt.claim).proposition != disposition.proposition:
            continue
        rows[index - 1] = replace(previous, text=previous.text.removesuffix("."))
        rows[index] = replace(current, text="and believed it.", paragraph=previous.paragraph)
    if complete and rows and not any(s.id == "opening" for s in rows):
        initial_entities = {r.id: r for r in spec.records.get("entities", ())}
        parents = {r.id: r.parent for r in spec.records.get("parents", ())}
        actor = state.events[0].action.actor
        place = parents.get(actor)
        if place in initial_entities and initial_entities[place].kind == "place":
            companions = [e for e in initial_entities.values() if e.kind == "actor" and parents.get(e.id) == place]
            names = [e.name for e in companions]
            subject = names[0] if len(names) == 1 else ", ".join(names[:-1]) + " and " + names[-1]
            text = f"{subject} {'was' if len(names) == 1 else 'were'} at {initial_entities[place].name}."
            rows.insert(0, Statement(id="scene_opening", text=text, kind="flourish", focus="", answer="",
                                    event_ids=(), entity_ids=tuple(e.id for e in companions) + (place,),
                                    paragraph=rows[0].paragraph))
    if closing:
        rows.append(closing)
    return Document(title=document.title, statements=tuple(rows))
