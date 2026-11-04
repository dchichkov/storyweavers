from copy import deepcopy
import unittest
from unittest.mock import patch

from storyscenes.runtime import StoryError, transition
from .local_play import LocalPlay


def validate(state):
    if state["lamp.fuel"] < 1:
        raise StoryError("Keep the cellar reserve")


class LocalPlayTests(unittest.TestCase):
    def make_play(self):
        return LocalPlay({"lamp.fuel": 2, "bag.items": [{"name": "key"}]},
                         actors=("borrower",), validate=validate)

    def assert_rejected(self, play, callback):
        state, events = deepcopy(play.state), deepcopy(play.events)
        with self.assertRaises(StoryError):
            callback()
        self.assertEqual(play.state, state)
        self.assertEqual(play.events, events)

    def test_valid_trace_uses_shared_transition(self):
        x = self.make_play()
        with patch("storyscenes.mini_adventures.local_play.transition", wraps=transition) as call:
            x.act("burn_one", {"lamp.fuel": 2}, **{"lamp.fuel": 1})
        self.assertEqual(x.state["lamp.fuel"], 1)
        self.assertEqual(x.events, [{"action": "burn_one", "requires": {"lamp.fuel": 2},
                                   "changes": {"lamp.fuel": {"before": 2, "after": 1}}}])
        self.assertEqual(call.call_count, 1)
        action = call.call_args.args[1]
        self.assertEqual(action.actors, ("borrower",))
        self.assertEqual(action.requires[0].key, "lamp.fuel")
        self.assertEqual(action.effects[0].value, 1)

    def test_invalid_initial_state_is_validated_without_mutating_input(self):
        source = {"lamp.fuel": 0, "bag.items": [{"name": "key"}]}
        saved = deepcopy(source)
        with self.assertRaises(StoryError):
            LocalPlay(source, actors=("borrower",), validate=validate)
        self.assertEqual(source, saved)

    def test_rejected_condition_preserves_existing_trace(self):
        x = self.make_play()
        x.act("burn_one", **{"lamp.fuel": 1})
        self.assert_rejected(x, lambda: x.act("burn_again", {"lamp.fuel": 2}, **{"lamp.fuel": 0}))

    def test_rejected_invariant_preserves_existing_trace(self):
        x = self.make_play()
        x.act("burn_one", **{"lamp.fuel": 1})
        self.assert_rejected(x, lambda: x.act("burn_reserve", **{"lamp.fuel": 0}))

    def test_noops_and_unknown_keys_do_not_commit(self):
        x = self.make_play()
        for callback in (
            lambda: x.act("nothing"),
            lambda: x.act("same", **{"lamp.fuel": 2, "bag.items": [{"name": "key"}]}),
            lambda: x.act("unknown_effect", **{"new.key": True}),
            lambda: x.act("unknown_condition", {"missing": True}, **{"lamp.fuel": 1}),
        ):
            with self.subTest(callback=callback):
                self.assert_rejected(x, callback)

    def test_initial_nested_state_and_actors_are_detached(self):
        source = {"lamp.fuel": 2, "bag.items": [{"name": "key"}]}
        actors = ["borrower"]
        x = LocalPlay(source, actors=actors, validate=validate)
        source["bag.items"][0]["name"] = "changed"
        actors.append("stranger")
        self.assertEqual(x.state["bag.items"], [{"name": "key"}])
        with patch("storyscenes.mini_adventures.local_play.transition", wraps=transition) as call:
            x.act("burn_one", **{"lamp.fuel": 1})
        self.assertEqual(call.call_args.args[1].actors, ("borrower",))
        x.state["bag.items"][0]["name"] = "changed inside"
        self.assertEqual(source["bag.items"], [{"name": "changed"}])

    def test_nested_arguments_state_and_events_do_not_alias(self):
        x = self.make_play()
        requires = {"bag.items": [{"name": "key"}]}
        changed = [{"name": "ribbon", "colors": ["green"]}]
        x.act("exchange", requires, **{"bag.items": changed})
        requires["bag.items"][0]["name"] = "outside mutation"
        changed[0]["colors"].append("outside mutation")
        event = x.events[0]
        self.assertEqual(event["requires"], {"bag.items": [{"name": "key"}]})
        self.assertEqual(x.state["bag.items"][0]["colors"], ["green"])
        x.state["bag.items"][0]["colors"].append("state mutation")
        self.assertEqual(event["changes"]["bag.items"]["after"][0]["colors"], ["green"])
        event["changes"]["bag.items"]["after"][0]["colors"].append("event mutation")
        self.assertEqual(x.state["bag.items"][0]["colors"], ["green", "state mutation"])
        event["requires"]["bag.items"][0]["name"] = "requirement mutation"
        self.assertEqual(event["changes"]["bag.items"]["before"], [{"name": "key"}])

    def test_later_events_do_not_alias_earlier_snapshots(self):
        x = self.make_play()
        x.act("exchange", **{"bag.items": [{"name": "ribbon"}]})
        first = deepcopy(x.events[0])
        x.act("exchange_again", **{"bag.items": [{"name": "button"}]})
        x.events[1]["changes"]["bag.items"]["before"][0]["name"] = "mutated"
        self.assertEqual(x.events[0], first)

    def test_validator_gets_detached_initial_and_candidate_snapshots(self):
        seen = []
        def inspecting_validator(state):
            seen.append(state)
            state["bag.items"][0]["name"] = "validator mutation"
            validate(state)
        source = {"lamp.fuel": 2, "bag.items": [{"name": "key"}]}
        x = LocalPlay(source, actors=("borrower",), validate=inspecting_validator)
        x.act("burn_one", **{"lamp.fuel": 1})
        self.assertEqual(len(seen), 2)
        self.assertEqual(x.state["bag.items"], [{"name": "key"}])
        self.assertEqual(source["bag.items"], [{"name": "key"}])
        seen[-1]["lamp.fuel"] = 99
        self.assertEqual(x.state["lamp.fuel"], 1)
        self.assert_rejected(x, lambda: x.act("burn_reserve", **{"lamp.fuel": 0}))


if __name__ == "__main__":
    unittest.main()
