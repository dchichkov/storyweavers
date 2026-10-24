"""Withdrawal is not an implicit reverse request or promise release (D08)."""
import unittest

from storyscenes.capabilities.api import registry
from storyscenes.capabilities.core import execute, replay, replay_selection
from storyscenes.capabilities.examples import separate_return_request_story
from storyscenes.capabilities.reading import Reader
from storyscenes.capabilities.realize import render


class SeparateReturnRequestTests(unittest.TestCase):
    def setUp(self):
        self.scenario = separate_return_request_story()
        self.engine = registry()
        self.actions = {a.id: a for a in self.scenario.spec.actions}

    def test_withdrawal_preserves_acceptance_then_distinct_return_is_completed(self):
        x = self.scenario
        withdrawn = replay(self.engine, x.spec, x.path[:5])
        self.assertIsNone(execute(self.engine, x.spec, withdrawn, self.actions["walk"]))
        self.assertEqual(withdrawn.get("requests", "out").response, "accepted")
        self.assertEqual(withdrawn.get("requests", "out").withdrawal_event, "withdraw_out:1")
        self.assertIsNone(withdrawn.get("requests", "back"))
        self.assertEqual(withdrawn.get("parents", "caliper").parent, "jules")
        self.assertEqual(withdrawn.get("promises", "P").status, "active")
        state = replay(self.engine, x.spec, x.path)
        self.assertEqual(state.get("requests", "back").response, "accepted")
        self.assertEqual(state.get("requests", "back").completion_receipt, "bring_back:1")
        self.assertEqual(state.get("parents", "caliper").parent, "neri")
        self.assertIsNone(state.get("requests", "out").completion_receipt)
        self.assertEqual(state.get("promises", "P").status, "breached")
        self.assertIsNone(state.get("promises", "P").release_event)

    def test_withdrawn_work_can_be_physically_done_but_not_completed_as_request(self):
        x = self.scenario
        state = replay(self.engine, x.spec, x.path[:5] + ("ivo_arrives", "ready_out", "deliver_caliper"))
        self.assertEqual(state.get("parents", "caliper").parent, "ivo")
        self.assertIsNone(execute(self.engine, x.spec, state, self.actions["complete_out"]))
        after = execute(self.engine, x.spec, state, self.actions["close"])
        after = execute(self.engine, x.spec, after, self.actions["assess"])
        self.assertEqual(after.get("promises", "P").status, "fulfilled")

    def test_story_and_qa_name_return_request_and_preserve_replay_and_masks(self):
        x = self.scenario
        state = replay(self.engine, x.spec, x.path)
        reader = Reader(render(x.spec, state))
        self.assertIn("hand the caliper to Neri", reader.ask("request", "back").answer)
        self.assertIn("accepted", reader.ask("response", "back").answer)
        self.assertIn("completed", reader.ask("request_status", "back").answer)
        self.assertIn("Ivo", reader.ask("withdrawal", "out").answer)
        self.assertIn("breached", reader.ask("promise_status", "P").answer)
        for hidden in ("deliver_back:1/request/back", "accept_back:1/response/back"):
            self.assertFalse(Reader(render(x.spec, state).mask([hidden])).ask("request_status", "back").supported)
        retained = replay_selection(self.engine, x.spec, state, ["complete_back:1", "withdraw_out:1", "assess:1"])
        self.assertEqual(render(x.spec, retained), render(x.spec, state, visible={e.id for e in retained.events}))


if __name__ == "__main__":
    unittest.main()
