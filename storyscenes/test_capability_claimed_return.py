"""A live integrated claim/adoption cannot supply physical return or authority."""
from dataclasses import replace
import unittest

from storyscenes.capabilities.api import registry
from storyscenes.capabilities.core import execute, fingerprint, replay, replay_selection
from storyscenes.capabilities.examples import claimed_return_story, loan_story
from storyscenes.capabilities.reading import Reader
from storyscenes.capabilities.realize import render


class ClaimedReturnTests(unittest.TestCase):
    def test_heard_and_adopted_delivery_claim_does_not_return_or_grant_authority(self):
        engine = registry()
        scenario = claimed_return_story()
        state = replay(engine, scenario.spec, scenario.path)
        self.assertEqual(state.get("loans", "L").status, "active")
        self.assertEqual(state.get("parents", "item").parent, "bag")
        self.assertFalse(state.get("grants", "deposit_grant").active)
        self.assertEqual(state.get("beliefs", state.get("belief_heads", "owner_return").belief).proposition,
                         "settled_claim")
        self.assertIsNone(state.get("receipts", "deposit:1"))
        before = fingerprint(state)
        self.assertIsNone(execute(engine, scenario.spec, state,
                                 next(a for a in scenario.spec.actions if a.id == "deposit")))
        self.assertEqual(fingerprint(state), before)
        doc = render(scenario.spec, state)
        reader = Reader(doc)
        self.assertTrue(reader.ask("claim", "claimed_return").supported)
        self.assertIn("settled", reader.ask("belief", "owner_return").answer)
        self.assertFalse(reader.ask("loan_status", "L", event_id="claim_return:1").supported)
        self.assertIn("outstanding", reader.ask("loan_status", "L", event_id="rest:1").answer)
        self.assertFalse(Reader(doc.mask(["claim_return:1/claim/claimed_return"]))
                         .ask("receipt", "claimed_return").supported)
        self.assertFalse(Reader(doc.mask(["claim_return:1/claim/claimed_return"]))
                         .ask("belief", "owner_return").supported)
        retained = replay_selection(engine, scenario.spec, state, ["accept_claim:1", "decline:1"])
        self.assertEqual(render(scenario.spec, retained), render(scenario.spec, state,
                         visible={e.id for e in retained.events}))

    def test_wrong_loan_integrated_deposit_is_atomic(self):
        engine = registry()
        scenario = loan_story()
        actions = tuple(replace(a, args={**a.args, "loan_id": "another_loan"}) if a.id == "deposit" else a
                        for a in scenario.spec.actions)
        spec = replace(scenario.spec, actions=actions)
        state = replay(engine, spec, scenario.path[:scenario.path.index("deposit")])
        before = fingerprint(state)
        self.assertIsNone(execute(engine, spec, state, next(a for a in actions if a.id == "deposit")))
        self.assertEqual(fingerprint(state), before)
        self.assertEqual(state.get("loans", "L").status, "active")
        self.assertEqual(state.get("parents", "item").parent, "bag")
        self.assertFalse(state.get("containers", "cabinet").latched)


if __name__ == "__main__":
    unittest.main()
