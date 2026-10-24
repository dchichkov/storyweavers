"""Preserve local conformance stories, reader QA and intervention evidence."""
import argparse
from dataclasses import replace
from datetime import datetime, timezone
import hashlib
import json
import lzma
from pathlib import Path

from .api import registry
from .codec import dumps, loads
from .choices import CHOICE_BINDINGS, competing_promise_story
from .corrections import (harbor_clearance_story, harbor_diagnostic_story,
                          library_booking_story, library_ledger_story, observatory_identity_story,
                          observatory_reading_story)
from .core import execute, fingerprint, matches, plain, replay, replay_selection
from .examples import (claimed_return_story, delayed_report_story, harbor_site_return_story, loan_story,
                       promise_story, separate_return_request_story)
from .reading import Reader
from .realize import render
from .returns import (harbor_scoped_lending_story, harbor_scoped_return_story,
                      receive_only_story, stale_authority_story, two_offer_story)


def cases():
    return {
        "library_return": loan_story(),
        "harbor_return_transfer": loan_story(setting="harbor"),
        "harbor_designated_return_site": harbor_site_return_story(),
        "observatory_return_transfer": loan_story(setting="observatory"),
        "observatory_accepted_uncollected": loan_story(setting="observatory", collect=False),
        "harbor_dated_report": delayed_report_story(),
        "harbor_closed_case": delayed_report_story(open_after=False),
        "harbor_no_prior_prediction": delayed_report_story(extrapolate=False),
        "harbor_no_second_observation": delayed_report_story(second_observation=False),
        "harbor_changed_reference": delayed_report_story(report_reference=2),
        "harbor_unverified_changed_reference": delayed_report_story(report_reference=2, second_observation=False),
        "observatory_strict_boundary": promise_story(),
        "observatory_inclusive_boundary": promise_story(deadline="inclusive_by"),
        "observatory_released": promise_story(release=True),
        "observatory_late_repair": promise_story(late_repair=True),
        "library_claim_only_return": claimed_return_story(),
        "library_competing_promises": competing_promise_story(binding=CHOICE_BINDINGS[0]),
        "harbor_competing_promises": competing_promise_story(binding=CHOICE_BINDINGS[1]),
        "observatory_competing_promises": competing_promise_story(binding=CHOICE_BINDINGS[2]),
        "library_reversed_priority": competing_promise_story(priority="second"),
        "library_action_without_promise": competing_promise_story(intervention="action_only"),
        "library_promise_without_action": competing_promise_story(intervention="promise_only"),
        "observatory_released_replaced": competing_promise_story(binding=CHOICE_BINDINGS[2], intervention="release_new"),
        "harbor_separate_return_request": separate_return_request_story(),
        "observatory_old_and_current": observatory_reading_story(),
        "observatory_closed_slit": observatory_reading_story(open_slit=False),
        "harbor_stale_clearance": harbor_clearance_story(),
        "harbor_fresh_clearance": harbor_clearance_story(fresh_report=True),
        "harbor_recent_report_policy": harbor_clearance_story(report_age=1),
        "harbor_occluded_diagnosis": harbor_diagnostic_story(),
        "harbor_visible_diagnosis": harbor_diagnostic_story(indicator_visible=True),
        "library_authoritative_ledger": library_ledger_story(),
        "library_unauthorized_ledger": library_ledger_story(authoritative=False),
        "library_old_ledger": library_ledger_story(current_ledger=False),
        "library_confirmed_prior": library_ledger_story(booking_date=14),
        "library_separate_room_booking": library_booking_story(),
        "library_room_booking_conflict": library_booking_story(occupied=True),
        "observatory_shared_exposure": observatory_identity_story(),
        "observatory_no_identity_policy": observatory_identity_story(identity_policy=False),
        "observatory_unverified_identity": observatory_identity_story(verified_source=False),
        "observatory_independent_exposure": observatory_identity_story(same_exposure=False),
        "library_receive_only_new_loan": receive_only_story(),
        "library_stale_return_authority": stale_authority_story(),
        "library_stale_lending_authority": stale_authority_story(operation="lend"),
        "library_two_return_offers": two_offer_story(),
        "harbor_two_return_offers": two_offer_story(harbor=True),
        "harbor_bench_only_lending": harbor_scoped_lending_story(),
        "harbor_unrestricted_lending": harbor_scoped_lending_story(unrestricted=True),
        "harbor_bench_only_return": harbor_scoped_return_story(),
        "harbor_unrestricted_return": harbor_scoped_return_story(unrestricted=True),
    }


def blocked_cases():
    wrong_loan = loan_story()
    wrong_loan = replace(wrong_loan, spec=replace(wrong_loan.spec, actions=tuple(
        replace(a, args={**a.args, "loan_id": "another_loan"}) if a.id == "deposit" else a
        for a in wrong_loan.spec.actions)))
    result = {}
    for key, scenario in (("library_missing_return_grant", loan_story(grant_available=False)),
                          ("library_wrong_loan", wrong_loan),
                          ("observatory_missing_latch", loan_story(setting="observatory", latchable=False))):
        result[key] = (replace(scenario, path=scenario.path[:scenario.path.index("deposit")]), "deposit")
    result["library_revoked_return_grant"] = (stale_authority_story(), "finish1")
    result["library_revoked_lending_grant"] = (stale_authority_story(operation="lend"), "collect2")
    harbor = two_offer_story(harbor=True)
    result["harbor_full_hands"] = (replace(harbor, path=harbor.path[:-1] + ("fill_hands",)), "finish2")
    result["harbor_wrong_scoped_grant"] = (replace(harbor, path=harbor.path[:-1] + ("revoke",)), "finish2")
    result["library_occupied_booking"] = (library_booking_story(occupied=True), "book_room")
    lending = harbor_scoped_lending_story()
    result["harbor_lending_outside_grant_place"] = (replace(lending, path=()), "offer2")
    returning = harbor_scoped_return_story()
    result["harbor_return_outside_grant_place"] = (
        replace(returning, path=returning.path[:returning.path.index("receiver_aboard") + 1]), "finish2")
    return result


def verify(destination):
    destination.mkdir(parents=True, exist_ok=False)
    engine = registry()
    summaries, stories, files = [], [], []

    def write(name, value):
        path = destination / name
        path.parent.mkdir(parents=True, exist_ok=True)
        text = value if isinstance(value, str) else json.dumps(plain(value), indent=2, sort_keys=True) + "\n"
        path.write_text(text, encoding="utf-8")
        files.append(dict(path=name, bytes=len(text.encode()), sha256=hashlib.sha256(text.encode()).hexdigest()))

    # Preserve the exact executable source with new evidence batches. Earlier
    # development snapshots retain their raw records, not a claimed frozen API.
    source_files = {f"runtime/storyscenes/capabilities/{path.name}": path
                    for path in sorted(Path(__file__).parent.glob("*.py"))}
    source_files["runtime/storyscenes/__init__.py"] = Path(__file__).parent.parent / "__init__.py"
    source_text = {name: path.read_text(encoding="utf-8") for name, path in source_files.items()}
    for name, source in source_text.items():
        write(name, source)

    for key, scenario in cases().items():
        spec = loads(engine, dumps(scenario.spec))
        state = replay(engine, spec, scenario.path)
        again = replay(engine, spec, scenario.path)
        if state != again:
            raise ValueError(f"Nondeterministic replay: {key}")
        goal_met = all(matches(state, goal) for goal in spec.goal)
        if not goal_met and key != "observatory_accepted_uncollected":
            raise ValueError(f"Conformance path missed its declared outcome: {key}")
        # Uncollected intervention is a prefix, not the complete return ending.
        ending = scenario.ending if key != "observatory_accepted_uncollected" else None
        document = render(spec, state, premise=scenario.premise, ending=ending)
        reader = Reader(document)
        qa = reader.questions()
        masks = []
        for statement in (s for s in document.statements if s.question):
            answer = reader.ask(statement.kind, statement.focus,
                                event_id=statement.event_ids[0], reference_tick=statement.reference_tick)
            for support_id in answer.statement_ids:
                masked = Reader(document.mask([support_id]))
                result = masked.ask(statement.kind, statement.focus,
                                    event_id=statement.event_ids[0], reference_tick=statement.reference_tick)
                if result.supported:
                    raise ValueError(f"Hidden support still answerable: {key}/{support_id}")
                masks.append(dict(hidden=support_id, target=statement.id, answer=result))
        salient = {"assess_promise", "record_late_repair", "release_promise", "refuse",
                   "update_belief", "authorized_deposit"}
        roots = tuple(e.id for e in state.events if e.action.operation in salient or
                      e.id == state.events[-1].id or e.action.id == "rest")
        retained = replay_selection(engine, spec, state, roots)
        selected = render(spec, state, visible={e.id for e in retained.events})
        if selected != render(spec, retained):
            raise ValueError(f"Selected replay changed narrative support: {key}")
        row = dict(schema=spec.schema, title=spec.title, path=scenario.path,
                   goal_met=goal_met, trace=state, trace_sha256=fingerprint(state), story=document.story,
                   statements=document.statements, spans=document.spans(), qa=qa, masked_answers=masks,
                   retained=dict(roots=roots, trace=retained, story=selected.story,
                                 spans=selected.spans(), qa=Reader(selected).questions()))
        write(f"{key}.world.json", dumps(spec))
        write(f"{key}.json", row)
        summaries.append(dict(case=key, events=len(state.events), questions=len(qa),
            goal_met=goal_met, retained_events=len(retained.events), masks=len(masks), story_words=len(document.story.split()),
            loan_outcomes={k: v.status for k, v in state.tables["loans"].items()},
            promise_outcomes={k: v.status for k, v in state.tables["promises"].items()},
            belief_dispositions={k: v.mode for k, v in state.tables["dispositions"].items()}))
        stories.append(document.story)
    blocked = []
    for key, (scenario, rejected) in blocked_cases().items():
        prefix = scenario.path
        state = replay(engine, scenario.spec, prefix)
        before = fingerprint(state)
        action = next(a for a in scenario.spec.actions if a.id == rejected)
        after = execute(engine, scenario.spec, state, action)
        if after is not None or fingerprint(state) != before:
            raise ValueError(f"Rejected operation was not atomic: {key}")
        doc = render(scenario.spec, state)
        write(f"{key}.world.json", dumps(scenario.spec))
        write(f"{key}.json", dict(path=prefix, rejected_action=action, trace=state,
              before_sha256=before, after_sha256=fingerprint(state), story=doc.story,
              statements=doc.statements, spans=doc.spans(), qa=Reader(doc).questions()))
        blocked.append(dict(case=key, rejected=action.id, unchanged=True,
                            loan_status={k: row.status for k, row in state.tables["loans"].items()}))
    payload = "\n\n---\n\n".join(stories).encode()
    metrics = dict(stories=len(stories), exact_unique=len(set(stories)), utf8_bytes=len(payload),
                   lzma_bytes=len(lzma.compress(payload)),
                   caveat="Small conformance corpus only; not a 1000-sample diversity or literary evaluation.")
    write("summary.json", dict(cases=summaries, blocked=blocked, corpus=metrics, paid_calls=0, runtime_calls=0))
    write("samples.md", "# Local capability samples\n\n" + "\n\n---\n\n".join(
        f"## {row['case']}\n\n{story}" for row, story in zip(summaries, stories)) + "\n")
    if any(path.read_text(encoding="utf-8") != source_text[name] for name, path in source_files.items()):
        raise ValueError("Runtime source changed while the evidence batch was running")
    write("manifest.json", dict(created_at=datetime.now(timezone.utc).isoformat(),
        protocol="capability_conformance_v3", files=files.copy(), tests="Run unittest separately; this does not grade test coverage."))
    return dict(cases=len(summaries), blocked=len(blocked), files=len(files), corpus=metrics)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(verify(args.out), indent=2))


if __name__ == "__main__":
    main()
