"""Integrated transfer and interventions, including narrative support masking."""
from dataclasses import replace
import json
from pathlib import Path
import subprocess
import sys
import unittest

from storyscenes.capabilities.api import registry
from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import CapabilityError, Transaction, execute, replay, replay_selection, solve
from storyscenes.capabilities.examples import delayed_report_story, loan_story, promise_story
from storyscenes.capabilities.physical import holder, location
from storyscenes.capabilities.reading import Reader
from storyscenes.capabilities.realize import render


class CapabilityIntegrationTests(unittest.TestCase):
    def setUp(self):
        self.engine = registry()

    def test_g1_same_operations_transfer_and_preserve_roles_in_three_settings(self):
        for setting in ("library", "harbor", "observatory"):
            with self.subTest(setting=setting):
                x = loan_story(setting=setting)
                self.assertEqual(loads(self.engine, dumps(x.spec)), x.spec)
                state = replay(self.engine, x.spec, x.path)
                self.assertEqual(state.get("loans", "L").status, "discharged")
                self.assertEqual(state.get("ownership", "item").owner, "owner")
                self.assertEqual(state.get("parents", "item").parent, "cabinet")
                self.assertTrue(state.get("containers", "cabinet").latched)
                self.assertEqual(state.get("promises", "P").status, "fulfilled")
                rested = replay(self.engine, x.spec, x.path[:x.path.index("relift")])
                tx = Transaction(self.engine, rested, x.spec.actions[0])
                self.assertEqual(location(tx, "item"), "yard")
                self.assertIsNone(holder(tx, "item"))
                self.assertEqual(rested.get("loans", "L").borrower, "borrower")
                self.assertEqual(rested.get("loans", "L").status, "active")
                retained = replay_selection(self.engine, x.spec, state, ["deposit:1", "assess:1"])
                self.assertEqual(retained.get("loans", "L"), state.get("loans", "L"))
                self.assertIn("decline:1", [e.id for e in retained.events])

    def test_g1_removed_grant_or_latch_leaves_debt_without_partial_deposit(self):
        for x in (loan_story(grant_available=False), loan_story(latchable=False)):
            prefix = x.path[:x.path.index("deposit")]
            state = replay(self.engine, x.spec, prefix)
            action = next(a for a in x.spec.actions if a.id == "deposit")
            self.assertIsNone(execute(self.engine, x.spec, state, action))
            self.assertEqual(state.get("parents", "item").parent, "bag")
            self.assertEqual(state.get("loans", "L").status, "active")
            self.assertIsNone(state.get("receipts", "deposit:1"))

    def test_accepted_uncollected_has_no_return_debt(self):
        x = loan_story(setting="observatory", collect=False)
        state = replay(self.engine, x.spec, x.path)
        self.assertEqual(state.get("loan_offers", "O").status, "accepted")
        self.assertFalse(state.tables["loans"])
        self.assertFalse(state.tables["receipts"])

    def test_g2_old_report_remains_historical_after_movement_and_revision(self):
        x = delayed_report_story()
        state = replay(self.engine, x.spec, x.path)
        old = state.get("propositions", "old:proposition")
        fresh = state.get("propositions", "fresh:proposition")
        self.assertEqual((old.reference_start, old.result.value), (0, "workshop"))
        self.assertEqual((fresh.reference_start, fresh.result.value), (2, "jetty"))
        self.assertEqual(state.get("claims", "report").proposition, old.id)
        self.assertEqual(state.get("beliefs", state.get("belief_heads", "cy_old").belief).proposition, old.id)
        self.assertEqual(state.get("beliefs", state.get("belief_heads", "current").belief).predecessor, "prediction")
        document = render(x.spec, state)
        report = Reader(document).ask("claim", "report")
        self.assertTrue(report.supported)
        self.assertTrue(Reader(document).ask("historical_truth", "report").supported)
        self.assertIn("time 0", report.answer)
        self.assertNotRegex(document.story.lower(), r"\b(?:lie|lied|liar)\b")
        reader = Reader(document.mask(["report:1/claim/report"]))
        self.assertFalse(reader.ask("receipt", "report").supported)
        self.assertFalse(reader.ask("historical_truth", "report").supported)

    def test_g2_inaccessible_check_retains_prior_unknown_initializes_without_discovery(self):
        x = delayed_report_story(open_after=False)
        state = replay(self.engine, x.spec, x.path)
        self.assertEqual(state.get("belief_heads", "current").belief, "prediction")
        self.assertEqual(state.get("evidence", "fresh").outcome, "inaccessible")
        self.assertIsNone(state.get("dispositions", "revision"))
        x = delayed_report_story(extrapolate=False)
        state = replay(self.engine, x.spec, x.path)
        self.assertEqual(state.get("dispositions", "revision").mode, "init")
        self.assertIsNone(state.get("beliefs", "revision:belief").predecessor)

    def test_g2_search_keeps_original_observation_before_absent_hidden_move(self):
        x = delayed_report_story()
        for seed in (0, 1, 42):
            with self.subTest(seed=seed):
                state = solve(self.engine, x.spec, seed, max_nodes=600)
                old = state.get("propositions", "old:proposition")
                fresh = state.get("propositions", "fresh:proposition")
                self.assertEqual((old.reference_start, old.result.value), (0, "workshop"))
                self.assertEqual((fresh.reference_start, fresh.result.value), (2, "jetty"))
                order = [e.action.id for e in state.events]
                self.assertLess(order.index("report"), order.index("move"))
                self.assertLess(order.index("move"), order.index("follow"))
                self.assertEqual(state, replay(self.engine, x.spec, order))

    def test_g3_boundary_release_and_late_repair_preserve_distinctions(self):
        for kwargs, expected in (({}, "breached"), ({"deadline": "inclusive_by"}, "fulfilled"),
                                  ({"release": True}, "released"), ({"late_repair": True}, "breached")):
            with self.subTest(kwargs=kwargs):
                x = promise_story(**kwargs)
                state = replay(self.engine, x.spec, x.path)
                self.assertEqual(state.get("promises", "P").status, expected)
                self.assertEqual(state.get("requests", "R2").response, "declined")
                self.assertEqual(state.get("parents", "chart").parent, "vale")
                if kwargs.get("late_repair"):
                    self.assertEqual(state.get("promises", "P").repair_receipt, "handoff:1")
                document = render(x.spec, state)
                promise = Reader(document).ask("promise", "P")
                self.assertIn("by time 8" if kwargs.get("deadline") == "inclusive_by" else "before time 8", promise.answer)

    def test_real_renderer_masking_removes_refusal_reason_and_reply_target(self):
        x = loan_story()
        state = replay(self.engine, x.spec, x.path)
        doc = render(x.spec, state)
        reader = Reader(doc)
        self.assertTrue(reader.ask("response", "RO").supported)
        self.assertTrue(reader.follow_up("why").supported)
        for hidden in ("decline:1/why/RO", "decline:1/response/RO", "return_offer:1/return_offer/RO"):
            self.assertFalse(Reader(doc.mask([hidden])).ask("why", "RO").supported)
        for span, statement in zip(doc.spans(), doc.statements):
            self.assertEqual(doc.story[span["start"]:span["end"]], statement.text)

    def test_offline_public_cli_json_contains_trace_and_reader_evidence(self):
        root = Path(__file__).resolve().parents[1]
        result = subprocess.run([sys.executable, "-m", "storyscenes.capabilities", "--example", "library",
                                 "--demo-path", "--json", "--qa"], cwd=root,
                                capture_output=True, text=True, check=True, timeout=30)
        row = json.loads(result.stdout)
        self.assertEqual(row["schema"], "storyscenes.capabilities.v1")
        from storyscenes.capabilities.story_examples import loan_story as narrative_loan
        self.assertEqual([e["action"]["id"] for e in row["trace"]["events"]], list(narrative_loan().path))
        self.assertTrue(row["qa"])
        self.assertTrue(all(a["statement_ids"] and a["event_ids"] for a in row["qa"]))


if __name__ == "__main__":
    unittest.main()
