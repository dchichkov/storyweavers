from copy import deepcopy
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
import unittest

from storyscenes.runtime import StoryError
from storyscenes.mini_adventures.local_play import LocalPlay
from .world import Parameters, SCENES, generate, guard, initial, play_scene, replay, validate


class KiteWorldTests(unittest.TestCase):
    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        for seed, count in product(range(100), (7, 8)):
            with self.subTest(seed=seed, count=count):
                row = generate(seed, count=count)
                self.assertEqual(len(row["path"]), count)
                self.assertEqual(len(set(row["path"])), count)
                self.assertTrue(set(row["path"]) <= set(SCENES))
                episodes = replay(Parameters(**row["parameters"]), row["path"])
                encoded = [{"id": e.id, "before": e.before, "after": e.after,
                            "events": list(e.events), "text": e.text} for e in episodes]
                self.assertEqual(encoded, row["episodes"])
                self.assertEqual("\n\n".join(e["text"] for e in row["episodes"]), row["story"])
                self.assertTrue(row["final_state"]["story.ended"])
                self.assertTrue(row["final_state"]["story.outcome"])
                state = initial(Parameters(**row["parameters"]))
                for ep in row["episodes"]:
                    self.assertEqual(ep["before"], state)
                    self.assertTrue(guard(ep["id"], state))
                    self.assertTrue(ep["events"])
                    self.assertTrue(40 <= len(ep["text"].split()) <= 70, ep["text"])
                    for event in ep["events"]:
                        self.assertTrue(event["changes"])
                        for key, expected in event["requires"].items():
                            self.assertEqual(state[key], expected)
                        for key, change in event["changes"].items():
                            self.assertEqual(state[key], change["before"])
                            state[key] = change["after"]
                        validate(state)
                    self.assertEqual(state, ep["after"])
                self.assertEqual(row["final_state"], state)

    def test_invalid_parameters_and_lengths(self):
        invalid = ({"wind": True}, {"wind": 0}, {"wind": 4}, {"reel_wear": -1},
                   {"frame_strength": 4}, {"shyness": "2"})
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        for count in (True, 6, 9):
            with self.subTest(count=count), self.assertRaises(ValueError):
                generate(count=count)
        with self.assertRaises(ValueError):
            generate(seed=True)

    def test_rejected_scenes_and_local_actions_do_not_mutate_callers(self):
        p = Parameters()
        state = initial(p)
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(p, state, "launch")
        self.assertEqual(state, saved)
        with self.assertRaises(StoryError):
            play_scene(p, state, "not_a_scene")
        self.assertEqual(state, saved)
        play = LocalPlay(state, actors=("nia",), validate=validate)
        before, events = deepcopy(play.state), deepcopy(play.events)
        with self.assertRaises(StoryError):
            play.act("no_change")
        self.assertEqual(play.state, before)
        self.assertEqual(play.events, events)
        with self.assertRaises(StoryError):
            play.act("illegal_change", {"weather.wind": 99}, **{"story.stage": "borrowed"})
        self.assertEqual(play.state, before)
        self.assertEqual(play.events, events)

    def test_optional_vignettes_are_independent_and_omission_is_real(self):
        p = Parameters(wind=1, reel_wear=0, frame_strength=3, shyness=1)
        base = replay(p, ("workshop", "build", "invite"))[-1].after
        ribbon = play_scene(p, base, "ribbon")
        practice = play_scene(p, base, "practice")
        self.assertTrue(ribbon.after["kite.ribbon"])
        self.assertFalse(ribbon.after["practice.done"])
        self.assertTrue(practice.after["practice.done"])
        self.assertFalse(practice.after["kite.ribbon"])
        omitted_path = ("workshop", "build", "invite", "keep_reel", "launch", "ending_airborne_guided")
        # A legal seven-scene route includes one vignette; the shorter replay here
        # isolates the state boundary and is intentionally not a generated story.
        omitted = replay(p, omitted_path[:-1])[-1].after
        self.assertFalse(omitted["kite.ribbon"])
        self.assertFalse(omitted["practice.done"])

    def test_borrowed_reel_changes_hands_and_returns_useful(self):
        p = Parameters(wind=1, reel_wear=0, frame_strength=3, shyness=1)
        path = ("workshop", "build", "invite", "practice", "hand_reel", "launch",
                "ending_airborne_shared")
        episodes = replay(p, path)
        self.assertEqual(episodes[0].after["reel.owner"], "Tamsin")
        self.assertEqual(episodes[0].after["reel.location"], "Nia")
        self.assertEqual(episodes[4].after["reel.location"], "Pavel")
        self.assertEqual(episodes[5].after["reel.usefulness"], "held a flying line")
        final = episodes[-1].after
        self.assertEqual(final["reel.owner"], "Tamsin")
        self.assertEqual(final["reel.location"], "workshop")
        self.assertTrue(final["reel.returned"])
        self.assertEqual(final["reel.usefulness"], "ready for another flight")

    def test_paired_counterfactuals_change_flight_and_participation(self):
        shared = ("workshop", "build", "invite", "practice", "keep_reel", "launch",
                  "ending_airborne_guided")
        calm = Parameters(wind=1, reel_wear=2, frame_strength=1, shyness=1)
        stronger_wind = Parameters(wind=2, reel_wear=2, frame_strength=1, shyness=1)
        self.assertEqual(replay(calm, shared)[-2].after["flight.result"], "aloft")
        self.assertEqual(replay(stronger_wind, shared[:-1] + ("ending_grounded",))[-2].after["flight.result"], "grounded")
        shy = Parameters(wind=1, reel_wear=0, frame_strength=3, shyness=3)
        after_invite = replay(shy, ("workshop", "build", "invite"))[-1].after
        self.assertFalse(guard("hand_reel", after_invite))
        after_practice = play_scene(shy, after_invite, "practice").after
        self.assertTrue(guard("hand_reel", after_practice))

    def test_every_scene_id_is_unique_and_ending_is_complete(self):
        self.assertEqual(len(SCENES), len(set(SCENES)))
        for seed in range(20):
            row = generate(seed)
            self.assertIn(row["final_state"]["story.outcome"],
                          {"shared_flight", "guided_flight", "safe_landing"})
            self.assertEqual(row["final_state"]["reel.location"], "workshop")

    def test_cli_prints_prose(self):
        result = subprocess.run([sys.executable, "-m", "storyscenes.mini_adventures.kite.world",
                                 "--seed", "0", "--scenes", "8"],
                                capture_output=True, text=True, check=True)
        self.assertGreater(len(result.stdout.split()), 250)


if __name__ == "__main__":
    unittest.main()
