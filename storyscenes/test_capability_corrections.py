"""Integrated D06 evidence: named stories, paired interventions and reader replay."""
from copy import deepcopy
from dataclasses import replace
import json
import unittest

from storyscenes.capabilities.api import registry
from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import CapabilityError, execute, replay, replay_selection
from storyscenes.capabilities.corrections import (
    harbor_clearance_story, harbor_diagnostic_story, library_booking_story, library_ledger_story,
    observatory_identity_story, observatory_reading_story)
from storyscenes.capabilities.epistemic import Result
from storyscenes.capabilities.examples import action
from storyscenes.capabilities.reading import Reader
from storyscenes.capabilities.realize import render


class CapabilityCorrectionTests(unittest.TestCase):
    def setUp(self):
        self.engine = registry()

    def run_story(self, story):
        return replay(self.engine, story.spec, story.path)

    def before(self, story, step):
        return replay(self.engine, story.spec, story.path[:story.path.index(step)])

    def candidate(self, story, step):
        return next(a for a in story.spec.actions if a.id == step)

    def proposition(self, state, head):
        belief = state.get("beliefs", state.get("belief_heads", head).belief)
        return state.get("propositions", belief.proposition)

    def rejected(self, story, state, step):
        before = deepcopy(state)
        self.assertIsNone(execute(self.engine, story.spec, state, self.candidate(story, step)))
        self.assertEqual(state, before)

    def reader(self, story, state):
        return Reader(render(story.spec, state, premise=story.premise, ending=story.ending))

    def test_observatory_six_remains_valid_eight_initializes_without_a_prior(self):
        story = observatory_reading_story()
        self.assertFalse(self.engine.initial(story.spec).tables["beliefs"])
        before = self.before(story, "look_eight")
        old = before.get("beliefs", "six:belief")
        self.assertIsNone(before.get("belief_heads", "current"))
        state = self.run_story(story)
        self.assertEqual(state.get("beliefs", old.id), old)
        self.assertEqual(state.get("belief_heads", "six").belief, old.id)
        self.assertEqual((self.proposition(state, "six").reference_start,
                          self.proposition(state, "six").result.value), (6, "clear"))
        self.assertEqual((self.proposition(state, "current").reference_start,
                          self.proposition(state, "current").result.value), (8, "cloud"))
        self.assertIsNone(state.get("beliefs", "eight:belief").predecessor)
        self.assertEqual([d.mode for d in state.tables["dispositions"].values()], ["init", "init"])
        reader = self.reader(story, state)
        for head, tick, value in (("six", 6, "clear"), ("current", 8, "cloud")):
            answer = reader.ask("belief", head, reference_tick=tick)
            self.assertTrue(answer.supported)
            self.assertIn(value, answer.answer)
            self.assertNotIn("revised", answer.answer)

    def test_observatory_clear_cloud_and_closed_slit_are_distinct(self):
        for current in ("clear", "cloud"):
            with self.subTest(current=current):
                story = observatory_reading_story(current=current)
                state = self.run_story(story)
                self.assertEqual(self.proposition(state, "current").result.value, current)
                closed = observatory_reading_story(current=current, open_slit=False)
                unseen = self.run_story(closed)
                self.assertEqual(unseen.get("evidence", "look_eight").outcome, "inaccessible")
                self.assertIsNone(unseen.get("belief_heads", "current"))
                self.assertEqual(unseen.get("belief_heads", "six").belief, "six:belief")
                self.assertEqual(unseen.get("dispositions", "eight").mode, "defer")
                self.rejected(closed, self.before(closed, "defer_eight"), "learn_eight")
                reader = self.reader(closed, unseen)
                answer = reader.ask("observation", "look_eight")
                self.assertTrue(answer.supported)
                self.assertIn("did not establish", answer.answer)
                self.assertNotIn(current, answer.answer)
        # The old strip and failed check do not disclose which hidden sky obtains.
        cloudy = observatory_reading_story(open_slit=False)
        clear = observatory_reading_story(current="clear", open_slit=False)
        self.assertEqual(self.run_story(cloudy).events, self.run_story(clear).events)

    def test_pavel_keeps_dated_open_belief_and_records_freshness_deferral(self):
        story = harbor_clearance_story()
        state = self.run_story(story)
        initial = self.engine.initial(story.spec)
        self.assertEqual(state.tables["beliefs"], initial.tables["beliefs"])
        self.assertEqual(state.tables["belief_heads"], initial.tables["belief_heads"])
        decision = state.get("dispositions", "current")
        self.assertEqual((decision.mode, decision.policy, decision.belief), ("defer", "clearance", None))
        self.assertEqual(decision.comprehension_ids, ("old_understood",))
        report = state.get("claims", "old_report")
        self.assertEqual(state.get("propositions", report.proposition).reference_start, 0)
        self.assertEqual(state.get("claim_receipts", "old_receipt").received_at, 15)
        self.rejected(story, self.before(story, "defer_clearance"), "use_old_now")
        reader = self.reader(story, state)
        self.assertIn("deferred", reader.ask("belief", "current").answer)
        why = reader.follow_up("why")
        self.assertTrue(why.supported)
        self.assertIn("two minutes", why.answer)
        self.assertFalse(reader.ask("observation", "look_current_gate").supported)

    def test_pavel_current_vs_stale_age_boundary_is_inclusive(self):
        for age, mode in ((1, "init"), (2, "init"), (3, "defer"), (15, "defer")):
            with self.subTest(age=age):
                story = harbor_clearance_story(report_age=age)
                state = self.run_story(story)
                self.assertEqual(state.get("dispositions", "current").mode, mode)
                self.assertEqual(state.get("belief_heads", "dated").belief, "dated_prior")
                if mode == "init":
                    prop = self.proposition(state, "current")
                    self.assertEqual((prop.reference_start, prop.result.value), (age, "open"))
                    self.rejected(story, self.before(story, "use_old_now"), "defer_clearance")
                else:
                    self.assertIsNone(state.get("belief_heads", "current"))

    def test_pavel_fresh_closed_report_initializes_current_not_rewrites_the_past(self):
        story = harbor_clearance_story(fresh_report=True)
        state = self.run_story(story)
        self.assertEqual(self.proposition(state, "dated").result.value, "open")
        current = self.proposition(state, "current")
        self.assertEqual((current.reference_start, current.result.value), (15, "closed"))
        belief = state.get("beliefs", "current:belief")
        self.assertIsNone(belief.predecessor)
        self.assertEqual(belief.source_ids, ("gate",))
        reader = self.reader(story, state)
        self.assertIn("time 0", reader.ask("claim", "old_report").answer)
        self.assertIn("closed at time 15", reader.ask("belief", "current").answer)
        later = action("later", "advance_time", "pavel", to_tick=20)
        spec = replace(story.spec, actions=story.spec.actions + (later,))
        after = execute(self.engine, spec, state, later)
        self.assertIsNotNone(after)  # Validate age at disposition time, not final time.
        self.assertEqual(after.get("beliefs", belief.id), belief)

    def test_pavel_freshness_never_reads_hidden_gate_truth(self):
        for age in (1, 15):
            branches = [harbor_clearance_story(report_age=age, gate_now=v) for v in ("open", "closed")]
            states = [self.run_story(s) for s in branches]
            self.assertEqual(states[0].events, states[1].events)
            self.assertEqual(states[0].tables["beliefs"], states[1].tables["beliefs"])
            for state in states:
                decision = state.events[-1]
                self.assertFalse({t for t, _ in decision.reads} & {"facts", "exposures"})
                self.assertNotIn(("propositions", "actual_now"), decision.reads)

    def test_freshness_validates_named_source_and_bounded_age_without_changing_old_policies(self):
        story = harbor_clearance_story(report_age=1)
        for max_age in (None, True, -1, 201, 1.5):
            rows = dict(story.spec.records)
            rows["belief_policies"] = tuple(replace(p, max_age=max_age) if p.id == "clearance" else p
                                            for p in rows["belief_policies"])
            with self.subTest(max_age=max_age), self.assertRaises(CapabilityError):
                self.engine.initial(replace(story.spec, records=rows))
        rows = dict(story.spec.records)
        rows["belief_policies"] = tuple(replace(p, source="pavel") if p.id == "clearance" else p
                                        for p in rows["belief_policies"])
        wrong_source = replace(story, spec=replace(story.spec, records=rows))
        self.rejected(wrong_source, self.before(wrong_source, "use_old_now"), "use_old_now")
        # Older serialized policy rows have no max_age field at all.
        old = library_ledger_story().spec
        document = json.loads(dumps(old))
        for row in document["records"]["belief_policies"]:
            row.pop("max_age")
        self.assertEqual(dumps(loads(self.engine, json.dumps(document))), dumps(old))

    def test_ivo_occluded_indicator_retains_diagnosis_visible_test_can_resolve(self):
        story = harbor_diagnostic_story()
        state = self.run_story(story)
        self.assertEqual(state.get("evidence", "inspect_indicator").outcome, "unknown")
        self.assertEqual(state.get("propositions", "inspect_indicator:proposition").result,
                         Result(kind="unknown", reason="occluded"))
        self.assertEqual(state.get("belief_heads", "diagnosis").belief, "diagnosis")
        self.assertEqual(self.proposition(state, "diagnosis").result.value, True)
        self.assertEqual(state.get("dispositions", "diagnostic").predecessor, "diagnosis")
        self.rejected(story, self.before(story, "defer_diagnosis"), "clear_motor")
        visible = harbor_diagnostic_story(indicator_visible=True)
        cleared = self.run_story(visible)
        self.assertEqual(cleared.get("dispositions", "diagnostic").mode, "resolve")
        self.assertIs(self.proposition(cleared, "diagnosis").result.value, False)
        self.assertEqual(cleared.get("beliefs", "diagnostic:belief").predecessor, "diagnosis")
        for scenario, end in ((story, state), (visible, cleared)):
            self.assertEqual(end.tables["parents"], self.engine.initial(scenario.spec).tables["parents"])
            self.assertFalse(end.tables["receipts"])
        reader = self.reader(story, state)
        self.assertIn("true", reader.ask("claim", "diagnosis").answer)
        self.assertIn("deferred", reader.ask("belief", "diagnosis").answer)
        self.assertIn("without withdrawing", reader.follow_up("why").answer)

    def test_library_reading_ink_does_not_write_booking_belief(self):
        story = library_ledger_story()
        before = self.before(story, "apply_ledger")
        self.assertEqual(before.get("belief_heads", "booking").belief, "tonight")
        self.assertEqual(before.get("propositions", "read_rows:proposition").scope, "ledger-ink")
        self.assertEqual(len(before.tables["beliefs"]), 1)
        # Even with both readings in hand, perception alone cannot project ink.
        candidate = replace(self.candidate(story, "apply_ledger"),
                            args={**self.candidate(story, "apply_ledger").args, "policy": "percept"})
        spec = replace(story.spec, actions=story.spec.actions + (replace(candidate, id="ink_is_truth"),))
        self.assertIsNone(execute(self.engine, spec, before, spec.actions[-1]))
        state = self.run_story(story)
        self.assertEqual(self.proposition(state, "booking").result.value, 21)
        self.assertEqual(state.get("beliefs", "booking:belief").predecessor, "tonight")
        self.assertEqual(state.tables["parents"], before.tables["parents"])
        self.assertIn("Wednesday 21", self.reader(story, state).ask("observation", "read_rows").answer)
        self.assertIn("revised", self.reader(story, state).ask("belief", "booking").answer)

    def test_library_authority_and_current_seal_are_each_required(self):
        for kw in ({"authoritative": False}, {"current_ledger": False}):
            with self.subTest(kw=kw):
                story = library_ledger_story(**kw)
                state = self.run_story(story)
                self.assertEqual(state.get("evidence", "read_rows").outcome, "exact")
                self.assertEqual(state.get("belief_heads", "booking").belief, "tonight")
                self.assertEqual(state.get("dispositions", "booking").mode, "defer")
                self.rejected(story, self.before(story, "defer_booking"), "apply_ledger")
                self.assertNotIn("revised", self.reader(story, state).document.story)

    def test_library_correct_prior_gets_support_not_an_invented_mistake(self):
        story = library_ledger_story(booking_date=14)
        state = self.run_story(story)
        self.assertEqual(state.get("dispositions", "booking").mode, "adopt")
        self.assertEqual(self.proposition(state, "booking").result.value, 14)
        self.assertNotIn("revised", self.reader(story, state).ask("belief", "booking").answer)

    def test_observatory_identity_uses_registry_policy_and_declared_underlying_source(self):
        story = observatory_identity_story()
        before = self.before(story, "apply_identity")
        self.assertEqual(before.get("belief_heads", "independence").belief, "independent")
        labels = [before.get("propositions", f"read_{f}:proposition").result.value for f in ("a", "b")]
        self.assertEqual(labels, ["E17", "E17"])
        state = self.run_story(story)
        self.assertIs(self.proposition(state, "independence").result.value, False)
        belief = state.get("beliefs", "identity:belief")
        self.assertEqual((belief.policy, belief.source_ids, belief.predecessor),
                         ("project", ("old_plate",), "independent"))
        self.assertEqual(state.get("authority_policies", "identity_rule").kind, "exposure_identity")
        decision = state.events[-1]
        self.assertIn(("authority_policies", "identity_rule"), decision.reads)
        self.assertNotIn(("facts", "a_label"), decision.reads)
        self.assertNotIn(("facts", "b_label"), decision.reads)
        self.assertFalse(any(p.scope == "tonight-sky" for p in state.tables["propositions"].values()))
        self.assertFalse(self.reader(story, state).ask("sky", "bright_point").supported)

    def test_observatory_equal_strings_without_policy_or_verified_source_do_not_resolve(self):
        for kw in ({"identity_policy": False}, {"verified_source": False}):
            with self.subTest(kw=kw):
                story = observatory_identity_story(**kw)
                state = self.run_story(story)
                for label in ("read_a", "read_b"):
                    self.assertEqual(state.get("propositions", f"{label}:proposition").result.value, "E17")
                self.assertEqual(state.get("belief_heads", "independence").belief, "independent")
                self.assertEqual(state.get("dispositions", "identity").mode, "defer")
                self.rejected(story, self.before(story, "defer_identity"), "apply_identity")

    def test_observatory_distinct_verified_exposure_supports_independence_not_sky_detection(self):
        story = observatory_identity_story(same_exposure=False)
        state = self.run_story(story)
        self.assertEqual(state.get("dispositions", "identity").mode, "adopt")
        self.assertIs(self.proposition(state, "independence").result.value, True)
        self.assertNotIn("revised", self.reader(story, state).ask("belief", "independence").answer)
        self.assertFalse(self.reader(story, state).ask("detection", "bright_point").supported)

    def test_named_authority_reading_order_still_has_exactly_one_belief_writer(self):
        for story, reordered, disposition in (
            (library_ledger_story(), ("state_booking", "check_current", "read_rows", "apply_ledger"), "booking"),
            (observatory_identity_story(), ("state_independence", "verify_source", "read_log", "read_b", "read_a", "apply_identity"), "identity"),
        ):
            first = self.run_story(story)
            second = replay(self.engine, story.spec, reordered)
            self.assertEqual(first.tables["beliefs"], second.tables["beliefs"])
            self.assertEqual(len(second.tables["dispositions"]), 1)
            self.assertEqual(second.get("dispositions", disposition).mode, "resolve")

    def test_all_five_stories_codec_and_selected_replay_preserve_actual_reader_answers(self):
        cases = (
            (observatory_reading_story(), "current", ("remember_six:1",)),
            (observatory_reading_story(open_slit=False), "current", ("remember_six:1",)),
            (harbor_clearance_story(), "current", ("receive_old:1",)),
            (harbor_clearance_story(fresh_report=True), "current", ("receive_old:1",)),
            (harbor_diagnostic_story(), "diagnosis", ("state_diagnosis:1",)),
            (harbor_diagnostic_story(indicator_visible=True), "diagnosis", ("state_diagnosis:1",)),
            (library_ledger_story(), "booking", ("state_booking:1",)),
            (library_ledger_story(authoritative=False), "booking", ("state_booking:1",)),
            (observatory_identity_story(), "independence", ("state_independence:1",)),
            (observatory_identity_story(identity_policy=False), "independence", ("state_independence:1",)),
        )
        for story, focus, roots in cases:
            with self.subTest(title=story.spec.title, path=story.path):
                decoded = loads(self.engine, dumps(story.spec))
                self.assertEqual(dumps(decoded), dumps(story.spec))
                state = self.run_story(story)
                self.assertEqual(replay(self.engine, decoded, story.path), state)
                retained = replay_selection(self.engine, story.spec, state, roots + (state.events[-1].id,))
                self.assertEqual(retained.tables["beliefs"], state.tables["beliefs"])
                self.assertEqual(retained.tables["dispositions"], state.tables["dispositions"])
                answer = self.reader(story, state).ask("belief", focus)
                self.assertTrue(answer.supported)
                self.assertEqual(self.reader(story, retained).ask("belief", focus), answer)
                doc = self.reader(story, retained).document
                for span, statement in zip(doc.spans(), doc.statements):
                    self.assertEqual(doc.story[span["start"]:span["end"]], statement.text)
                masked = doc.mask(answer.statement_ids)
                self.assertFalse(Reader(masked).ask("belief", focus).supported)
                self.assertIsNone(execute(self.engine, story.spec, state, state.events[-1].action))

    def test_named_reasons_and_dated_report_abstain_when_their_visible_support_is_masked(self):
        for story, focus in ((harbor_clearance_story(), "current"), (harbor_diagnostic_story(), "diagnosis")):
            state = self.run_story(story)
            doc = self.reader(story, state).document
            reader = Reader(doc)
            self.assertTrue(reader.ask("belief", focus).supported)
            reason = reader.follow_up("why")
            self.assertTrue(reason.supported)
            for hidden in reason.statement_ids:
                self.assertFalse(Reader(doc.mask((hidden,))).ask("why", focus).supported)
        story = harbor_clearance_story()
        doc = self.reader(story, self.run_story(story)).document
        reader = Reader(doc)
        self.assertTrue(reader.ask("receipt", "old_report").supported)
        self.assertFalse(Reader(doc.mask(("send_old:1/claim/old_report",))).ask("receipt", "old_report").supported)

    def test_authority_decision_and_why_require_visible_readings_not_only_hidden_ids(self):
        for story, focus, readings, rule in (
            (library_ledger_story(), "booking", ("read_rows", "check_current"), "current-ledger authority"),
            (observatory_identity_story(), "independence", ("read_a", "read_b", "read_log", "verify_source"), "exposure-identity"),
        ):
            with self.subTest(focus=focus):
                doc = render(story.spec, self.run_story(story))
                reader = Reader(doc)
                self.assertTrue(reader.ask("belief", focus).supported)
                why = reader.follow_up("why")
                self.assertTrue(why.supported)
                self.assertIn(rule, why.answer)
                for reading in readings:
                    hidden = f"{reading}:1/observation/{reading}"
                    masked = Reader(doc.mask((hidden,)))
                    self.assertFalse(masked.ask("belief", focus).supported)
                    self.assertFalse(masked.ask("why", focus).supported)

    def test_library_delayed_assent_and_actual_booking_are_distinct(self):
        story = library_booking_story()
        pending = self.before(story, "accept_room")
        self.assertEqual(pending.get("requests", "room").response, "pending")
        self.assertFalse(pending.tables["domain_receipts"])
        accepted = self.before(story, "check_room")
        self.assertEqual(accepted.get("requests", "room").response, "accepted")
        self.assertFalse(accepted.tables["domain_receipts"])
        final = self.run_story(story)
        self.assertEqual(final.get("requests", "room").completion_receipt, "book_room:1")
        self.assertEqual(final.get("booking_slots", "the reading room on Wednesday 21").booked_by, "nia")
        self.assertEqual(self.proposition(final, "booking").result.value, 21)
        reader = self.reader(story, final)
        self.assertIn("completed", reader.ask("request_status", "room").answer)
        self.assertFalse(final.tables["loans"])
        self.assertEqual(final.get("parents", "projector").parent, "room")

    def test_library_occupied_room_is_an_enacted_check_not_a_fictional_booking_attempt(self):
        story = library_booking_story(occupied=True)
        state = self.run_story(story)
        self.rejected(story, state, "book_room")
        self.assertEqual(state.get("domain_receipts", "check_room:1").result, "occupied")
        self.assertIsNone(state.get("domain_receipts", "book_room:1"))
        self.assertIsNone(state.get("requests", "room").completion_receipt)
        reader = self.reader(story, state)
        self.assertIn("occupied", reader.ask("performance", "the reading room on Wednesday 21").answer)
        self.assertFalse(reader.ask("request_status", "room").supported)
        retained = replay_selection(self.engine, story.spec, state, ["check_room:1", "accept_room:1", "apply_ledger:1"])
        self.assertEqual(render(story.spec, retained), render(story.spec, state, visible={e.id for e in retained.events}))


if __name__ == "__main__":
    unittest.main()
