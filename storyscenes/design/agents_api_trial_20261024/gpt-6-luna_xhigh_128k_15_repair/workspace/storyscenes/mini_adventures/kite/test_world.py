from copy import deepcopy
from dataclasses import asdict
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .world import Parameters, SCENES, generate, guard, initial, play_scene, replay, validate


def serial_episode(e):
    return {
        "id": e.id, "before": e.before, "after": e.after,
        "events": list(e.events), "text": e.text,
    }


class CourtyardCartTests(unittest.TestCase):
    def check_row(self, row):
        p = Parameters(**row["parameters"])
        episodes = replay(p, row["path"])
        self.assertEqual([serial_episode(e) for e in episodes], row["episodes"])
        self.assertEqual(len(episodes), row["scene_count"])
        self.assertEqual(row["story"], "\n\n".join(e.text for e in episodes))
        self.assertEqual(episodes[-1].after, row["final_state"])
        self.assertTrue(row["final_state"]["story.ended"])
        self.assertTrue(row["final_state"]["story.outcome"])
        self.assertEqual(len(row["path"]), len(set(row["path"])))
        self.assertTrue(set(row["path"]) <= set(SCENES))
        state = initial(p)
        for episode in episodes:
            self.assertEqual(episode.before, state)
            self.assertTrue(guard(episode.id, state))
            self.assertTrue(40 <= len(episode.text.split()) <= 70, (episode.id, len(episode.text.split())))
            for event in episode.events:
                self.assertTrue(event["action"])
                self.assertTrue(event["changes"])
                for key, value in event["requires"].items():
                    self.assertEqual(state[key], value)
                for key, change in event["changes"].items():
                    self.assertEqual(state[key], change["before"])
                    state[key] = deepcopy(change["after"])
                validate(state)
            self.assertEqual(state, episode.after)

    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        outcomes = set()
        optional_seen = set()
        for seed, count in product(range(100), (7, 8)):
            row = generate(seed, count=count)
            self.check_row(row)
            self.assertEqual(row, generate(seed, count=count))
            outcomes.add(row["final_state"]["story.outcome"])
            optional_seen.update(set(row["path"]) & {"chalk_names", "measure_story"})
            if count == 7:
                self.assertFalse(set(row["path"]) & {"chalk_names", "measure_story"})
            else:
                self.assertEqual(len(set(row["path"]) & {"chalk_names", "measure_story"}), 1)
        self.assertIn("cart_repaired_and_seedlings_delivered", outcomes)
        self.assertIn("cart_parked_safely_and_seedlings_delivered_by_hand", outcomes)
        self.assertEqual(optional_seen, {"chalk_names", "measure_story"})

    def test_all_endings_have_explicit_parameter_recipes(self):
        cases = (
            (Parameters(washer_available=True, admission_style="early"), "ending_repaired"),
            (Parameters(washer_available=True, admission_style="late"), "ending_rebuilt"),
            (Parameters(washer_available=False, admission_style="early"), "ending_stopped"),
        )
        for p, ending in cases:
            row = generate(17, count=7, params=p)
            self.check_row(row)
            self.assertEqual(row["path"][-1], ending)

    def test_parameters_change_actions_and_physical_outcomes(self):
        base_path = ("borrow", "first_attempt", "reinspect", "admit_error",
                     "repair", "test_roll", "ending_repaired")
        fit = Parameters(washer_available=True, spanner_fits=True, cart_load=2, bench_level=True)
        wrong_size = Parameters(washer_available=True, spanner_fits=False, cart_load=2, bench_level=True)
        fit_first = replay(fit, base_path)[1]
        swap_first = replay(wrong_size, base_path)[1]
        self.assertNotIn("ask_len_for_adjustable_spanner", [e["action"] for e in fit_first.events])
        self.assertIn("ask_len_for_adjustable_spanner", [e["action"] for e in swap_first.events])
        self.assertTrue(swap_first.after["spanner.fits"])

        sloped = Parameters(washer_available=True, spanner_fits=True, cart_load=3, bench_level=False)
        row = generate(2, count=7, params=sloped)
        repair = row["episodes"][row["path"].index("repair")]
        self.assertEqual(repair["after"]["cart.load"], 2)
        self.assertEqual(repair["after"]["extra_pot.location"], "bench_shelf")
        self.assertIn("steady_cart_with_wedge", [e["action"] for e in row["episodes"][1]["events"]])
        self.assertEqual(row["final_state"]["mina.delivery"], "done_by_cart_plus_hand")

    def test_paired_counterfactual_washer_changes_ending(self):
        fixed = dict(spanner_fits=True, cart_load=2, bench_level=True, admission_style="early")
        working = generate(8, count=7, params=Parameters(washer_available=True, **fixed))
        stopped = generate(8, count=7, params=Parameters(washer_available=False, **fixed))
        self.assertEqual(working["path"][-1], "ending_repaired")
        self.assertEqual(stopped["path"][-1], "ending_stopped")
        self.assertEqual(working["final_state"]["wheel.rattle"], False)
        self.assertEqual(stopped["final_state"]["wheel.rattle"], True)
        self.assertEqual(stopped["final_state"]["cart.current_use"], "display")
        self.assertEqual(stopped["final_state"]["mina.delivery"], "done_by_hand")

    def test_optional_omission_has_no_hidden_effect(self):
        p = Parameters()
        row = generate(12, count=7, params=p)
        self.assertFalse(set(row["path"]) & {"chalk_names", "measure_story"})
        self.assertFalse(row["final_state"]["cart.name_marked"])
        self.assertFalse(row["final_state"]["jo.heard_tip"])
        optional = generate(12, count=8, params=p)
        self.assertEqual(len(set(optional["path"]) & {"chalk_names", "measure_story"}), 1)
        if "chalk_names" not in optional["path"]:
            self.assertFalse(optional["final_state"]["cart.name_marked"])
        if "measure_story" not in optional["path"]:
            self.assertFalse(optional["final_state"]["jo.heard_tip"])

    def test_borrowed_objects_and_locations_remain_continuous(self):
        good = generate(29, count=7, params=Parameters(washer_available=True, cart_load=2))
        first = good["episodes"][0]["after"]
        self.assertEqual((first["spanner.owner"], first["spanner.location"]), ("jo", "jo.hand"))
        self.assertEqual(good["final_state"]["spanner.owner"], "len")
        self.assertEqual(good["final_state"]["spanner.location"], "toolbox")
        self.assertTrue(good["final_state"]["bench.vise_secure"])
        self.assertEqual(good["final_state"]["washer.location"], "axle")
        self.assertEqual(good["final_state"]["cart.location"], "bench")
        failed = generate(29, count=7, params=Parameters(washer_available=False, cart_load=2))
        self.assertEqual(failed["final_state"]["washer.location"], "none")
        self.assertEqual(failed["final_state"]["cart.location"], "bench")
        self.assertEqual(failed["final_state"]["cart.status"], "parked")

    def test_illegal_scene_and_failed_local_action_do_not_mutate_caller(self):
        p = Parameters()
        state = initial(p)
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(p, state, "first_attempt")
        self.assertEqual(state, saved)
        play = LocalPlay(state, actors=("jo",), validate=validate)
        before = deepcopy(play.state)
        events = deepcopy(play.events)
        with self.assertRaises(StoryError):
            play.act("illegal_borrow", {"spanner.owner": "jo"}, **{"story.started": True})
        self.assertEqual(play.state, before)
        self.assertEqual(play.events, events)
        self.assertEqual(state, saved)

    def test_invalid_parameters_counts_and_repeated_scenes(self):
        for kwargs in (
            {"washer_available": 1}, {"spanner_fits": "yes"}, {"cart_load": True},
            {"cart_load": 4}, {"bench_level": 0}, {"admission_style": "never"},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        for count in (True, 6, 9):
            with self.assertRaises(ValueError):
                generate(count=count)
        with self.assertRaises(StoryError):
            replay(Parameters(), ("borrow", "borrow"))

    def test_cli_prints_a_story(self):
        result = subprocess.run(
            [sys.executable, "-m", "storyscenes.mini_adventures.kite.world", "--seed", "0", "--scenes", "8"],
            capture_output=True, text=True, check=True,
        )
        self.assertGreater(len(result.stdout.split()), 250)


if __name__ == "__main__":
    unittest.main()
