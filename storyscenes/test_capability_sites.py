"""A named return-site restriction is not merely a renamed recipient."""
from dataclasses import replace
import json
import unittest

from storyscenes.capabilities.api import registry
from storyscenes.capabilities.codec import dumps, loads
from storyscenes.capabilities.core import CapabilityError, execute, fingerprint, replay, replay_selection
from storyscenes.capabilities.examples import action, harbor_site_return_story
from storyscenes.capabilities.reading import Reader
from storyscenes.capabilities.realize import render
from storyscenes.capabilities.returns import harbor_scoped_lending_story, harbor_scoped_return_story


class CapabilitySiteTests(unittest.TestCase):
    def setUp(self):
        self.engine = registry()

    def reject(self, scenario, state, action_id):
        before = fingerprint(state)
        candidate = next(a for a in scenario.spec.actions if a.id == action_id)
        self.assertLess(state.counts.get(action_id, 0), candidate.max_uses)
        self.assertIsNone(execute(self.engine, scenario.spec, state, candidate))
        self.assertEqual(fingerprint(state), before)

    def check_reader(self, scenario, state, event, focus, text, support):
        doc = render(scenario.spec, state)
        answer = Reader(doc).ask("authority", focus, event_id=event)
        self.assertTrue(answer.supported)
        self.assertIn(text, answer.answer)
        self.assertIn(support, answer.statement_ids)
        for hidden in answer.statement_ids:
            self.assertFalse(Reader(doc.mask([hidden])).ask("authority", focus, event_id=event).supported)
        retained = replay_selection(self.engine, scenario.spec, state, answer.event_ids)
        self.assertEqual(render(scenario.spec, retained),
                         render(scenario.spec, state, visible={e.id for e in retained.events}))
        self.assertEqual(Reader(render(scenario.spec, retained)).ask("authority", focus, event_id=event), answer)

    def test_place_is_optional_but_when_present_must_identify_a_place(self):
        x = harbor_scoped_lending_story()
        for invalid in ("prop", "receiver", "missing"):
            records = {**x.spec.records, "grants": tuple(replace(g, place=invalid) for g in x.spec.records["grants"])}
            with self.subTest(place=invalid), self.assertRaises(CapabilityError):
                self.engine.initial(replace(x.spec, records=records))
        document = json.loads(dumps(x.spec))
        for row in document["records"]["grants"]:
            row.pop("place")
        loaded = loads(self.engine, json.dumps(document))
        self.assertTrue(all(g.place is None for g in loaded.records["grants"]))

    def test_reviewer_probe_acceptance_and_readiness_do_not_extend_grant_to_launch(self):
        for unrestricted in (False, True):
            with self.subTest(unrestricted=unrestricted):
                x = harbor_scoped_return_story(unrestricted=unrestricted)
                prefix = x.path[:x.path.index("receiver_aboard") + 1]
                aboard = replay(self.engine, x.spec, prefix)
                self.assertEqual(aboard.get("parents", "receiver").parent, "launch")
                self.assertEqual(aboard.get("parents", "borrower").parent, "launch")
                self.assertEqual(aboard.get("parents", "prop").parent, "borrower")
                self.assertEqual(aboard.get("return_offers", "second_return").status, "accepted")
                self.assertFalse(aboard.get("readiness", "return_ready2").consumed)
                if not unrestricted:
                    self.reject(x, aboard, "finish2")
                    self.assertEqual(aboard.get("loans", "A1").status, "active")
                    self.assertIsNone(aboard.get("receipts", "finish2:1"))
                final = replay(self.engine, x.spec, x.path)
                self.assertEqual(final.get("loans", "A1").settlement_receipt, "finish2:1")
                self.assertEqual(final.get("parents", "receiver").parent, "launch" if unrestricted else "room")
                self.check_reader(x, final, "finish2:1", "settle1",
                                  "without restricting the place" if unrestricted else "only at the dry bench",
                                  "finish2:1/placement/prop")

    def test_lending_at_bench_and_unrestricted_lending_use_the_same_operations(self):
        for unrestricted in (False, True):
            with self.subTest(unrestricted=unrestricted):
                x = harbor_scoped_lending_story(unrestricted=unrestricted)
                if not unrestricted:
                    self.reject(x, self.engine.initial(x.spec), "offer2")
                final = replay(self.engine, x.spec, x.path)
                self.assertEqual(final.get("loans", "A2").status, "active")
                self.assertEqual(final.get("parents", "prop").parent, "borrower")
                self.assertEqual(final.get("ownership", "prop").owner, "owner")
                self.assertEqual(final.get("parents", "borrower").parent, "launch" if unrestricted else "room")
                self.check_reader(x, final, "offer2:1", "O2",
                                  "did not restrict" if unrestricted else "limited this lending and release to the dry bench",
                                  "offer2:1/loan_offer/O2")
                if not unrestricted:
                    placed = replay(self.engine, x.spec, x.path + ("put_in_tray",))
                    self.assertEqual(placed.get("parents", "prop").parent, "tray")
                    self.assertEqual(placed.get("loans", "A2"), final.get("loans", "A2"))

    def test_lending_rechecks_place_after_consent_and_before_collection(self):
        for unrestricted in (False, True):
            with self.subTest(unrestricted=unrestricted):
                x = harbor_scoped_lending_story(unrestricted=unrestricted)
                extra = tuple(action(f"{actor}_aboard", "travel", actor, route="aboard")
                              for actor in ("borrower", "receiver"))
                x = replace(x, spec=replace(x.spec, actions=x.spec.actions + extra))
                prefix = ("borrower_inside", "lender_inside", "offer2", "understand2", "accept2", "ready2",
                          "borrower_aboard", "receiver_aboard")
                before = replay(self.engine, x.spec, prefix)
                if unrestricted:
                    final = replay(self.engine, x.spec, prefix + ("collect2",))
                    self.assertEqual(final.get("loans", "A2").status, "active")
                else:
                    self.reject(x, before, "collect2")
                    self.assertIsNone(before.get("loans", "A2"))
                    self.assertFalse(before.get("readiness", "ready2").consumed)

    def test_accessible_original_shelf_cannot_replace_designated_dry_bench_site(self):
        x = harbor_site_return_story()
        engine = registry()
        before = replay(engine, x.spec, x.path[:x.path.index("to_return_site")])
        self.assertEqual(before.get("parents", "borrower").parent, "room")
        self.assertTrue(before.get("containers", "shelf").open)
        self.assertTrue(before.get("grants", "deposit_grant").active)
        original = fingerprint(before)
        actions = {a.id: a for a in x.spec.actions}
        self.assertIsNone(execute(engine, x.spec, before, actions["wrong_site"]))
        self.assertIsNone(execute(engine, x.spec, before, actions["deposit"]))  # Correct box is still remote.
        self.assertEqual(fingerprint(before), original)
        state = replay(engine, x.spec, x.path)
        self.assertEqual(state.get("parents", "item").parent, "cabinet")
        self.assertEqual(state.get("parents", "cabinet").parent, "yard")
        self.assertEqual(state.get("loans", "L").status, "discharged")
        self.assertIsNone(state.get("receipts", "deposit:1").recipient)
        self.assertEqual(state.get("ownership", "item").owner, "owner")
        retained = replay_selection(engine, x.spec, state, ["deposit:1", "assess:1"])
        doc = render(x.spec, retained)
        self.assertEqual(doc, render(x.spec, state, visible={e.id for e in retained.events}))
        answer = Reader(doc).ask("location", "item", event_id="deposit:1")
        self.assertTrue(answer.supported)
        self.assertIn("dry-bench return box at the dry bench", answer.answer)
        self.assertFalse(Reader(doc.mask(["deposit:1/placement/item"])).ask("location", "item", event_id="deposit:1").supported)


if __name__ == "__main__":
    unittest.main()
