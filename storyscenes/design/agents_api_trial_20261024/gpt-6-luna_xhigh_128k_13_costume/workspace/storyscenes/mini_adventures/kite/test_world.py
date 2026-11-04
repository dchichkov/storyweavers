from copy import deepcopy
from dataclasses import asdict
import json
import subprocess
import sys
import unittest

from storyscenes.runtime import StoryError
from .world import Parameters, SCENES, generate, guard, initial, play_scene, replay, validate


OPTIONAL = {"mirror_vignette", "ribbon_vignette"}


class StormCostumeTests(unittest.TestCase):
    def assert_row_replays(self, row):
        p = Parameters(**row["parameters"])
        episodes = replay(p, row["path"])
        serialized = [asdict(e) | {"events": list(e.events)} for e in episodes]
        self.assertEqual(serialized, row["episodes"])
        self.assertEqual(episodes[-1].after, row["final_state"])
        self.assertEqual("\n\n".join(e.text for e in episodes), row["story"])
        self.assertEqual(len(row["path"]), row["scene_count"])
        self.assertEqual(len(set(row["path"])), len(row["path"]))
        state = initial(p)
        for episode in episodes:
            self.assertEqual(state, episode.before)
            self.assertTrue(guard(episode.id, state))
            for event in episode.events:
                self.assertTrue(event["action"])
                self.assertTrue(event["changes"])
                for key, value in event["requires"].items():
                    self.assertEqual(state[key], value)
                for key, changes in event["changes"].items():
                    self.assertEqual(state[key], changes["before"])
                    self.assertNotEqual(changes["before"], changes["after"])
                    state[key] = changes["after"]
                validate(state)
            self.assertEqual(state, episode.after)
            words = len(episode.text.split())
            self.assertGreaterEqual(words, 40)
            self.assertLessEqual(words, 70)
        self.assertIs(row["final_state"]["story.ended"], True)
        self.assertTrue(row["final_state"]["story.outcome"])

    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        for seed in range(100):
            for count in (7, 8):
                with self.subTest(seed=seed, count=count):
                    row = generate(seed, count=count)
                    self.assert_row_replays(row)
                    self.assertEqual(set(row["path"]) & {"ending_fit", "ending_improvised"},
                                     {row["path"][-1]})

    def test_optional_vignettes_are_optional_and_have_no_offstage_effects(self):
        p = Parameters()
        seven = generate(4, count=7, params=p)
        eight = generate(4, count=8, params=p)
        self.assertFalse(set(seven["path"]) & OPTIONAL)
        self.assertEqual(len(set(eight["path"]) & OPTIONAL), 1)
        start = initial(p)
        after_opening = play_scene(p, start, "opening").after
        saved = deepcopy(after_opening)
        mirror = play_scene(p, after_opening, "mirror_vignette")
        self.assertEqual(after_opening, saved)
        self.assertTrue(mirror.after["mirror.used"])
        self.assertTrue(mirror.after["jo.saw_fit_issue"])
        ribbon = play_scene(p, play_scene(p, after_opening, "borrow_cape").after, "ribbon_vignette")
        self.assertEqual(ribbon.after["ribbon.location"], "cape_edge")
        self.assertEqual(ribbon.after["cape.holder"], "ada")
        self.assertFalse(after_opening["ribbon.chosen"])

    def test_each_ending_has_an_explicit_parameter_recipe(self):
        fixed = Parameters(teacher_available=True, minutes_left=2)
        improvised = Parameters(teacher_available=False, minutes_left=1,
                                seam_allowance=0, pins_available=False)
        a = generate(11, count=7, params=fixed)
        b = generate(11, count=7, params=improvised)
        self.assertEqual(a["path"][-1], "ending_fit")
        self.assertEqual(a["final_state"]["story.outcome"], "storm_costume_restored")
        self.assertEqual(b["path"][-1], "ending_improvised")
        self.assertEqual(b["final_state"]["story.outcome"], "storm_reimagined")
        self.assertNotEqual(a["final_state"]["jo.performance_style"],
                            b["final_state"]["jo.performance_style"])

    def test_parameter_counterfactuals_change_the_enacted_local_play(self):
        ready = Parameters(teacher_available=True, minutes_left=2, stage_lamp=True)
        no_coat = Parameters(teacher_available=False, minutes_left=1, seam_allowance=0,
                             pins_available=False, stage_lamp=False)
        a = replay(ready, ("opening", "borrow_cape", "consult_teacher", "refit_costume"))[-1]
        b = replay(no_coat, ("opening", "borrow_cape", "consult_teacher", "refit_costume"))[-1]
        self.assertTrue(a.after["jo.costume_fits"])
        self.assertFalse(b.after["jo.costume_fits"])
        self.assertIn("exchange_for_fitting_storm_coat", [e["action"] for e in a.events])
        self.assertIn("decline_the_tight_tunic", [e["action"] for e in b.events])
        self.assertEqual(b.after["minutes.left"], 0)

    def test_mirror_and_stage_lamp_parameters_have_local_effects(self):
        dusty = Parameters(mirror_clear=False)
        state = play_scene(dusty, initial(dusty), "opening").after
        mirror = play_scene(dusty, state, "mirror_vignette")
        self.assertIn("wipe_cupboard_mirror", [e["action"] for e in mirror.events])
        dark_lamp = Parameters(teacher_available=False, minutes_left=1, seam_allowance=0,
                               pins_available=False, stage_lamp=False)
        path = ("opening", "borrow_cape", "consult_teacher", "refit_costume", "rehearse")
        rehearsal = replay(dark_lamp, path)[-1]
        self.assertEqual(rehearsal.after["jo.plan"], "storm_sail")
        self.assertEqual(rehearsal.after["cape.use"], "wind_sail")

    def test_illegal_actions_fail_without_mutating_the_caller(self):
        p = Parameters()
        state = initial(p)
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(p, state, "borrow_cape")
        self.assertEqual(state, saved)
        opened = play_scene(p, state, "opening").after
        saved_opened = deepcopy(opened)
        with self.assertRaises(StoryError):
            play_scene(p, opened, "performance")
        self.assertEqual(opened, saved_opened)
        with self.assertRaises(StoryError):
            play_scene(p, opened, "opening")
        self.assertEqual(opened, saved_opened)

    def test_borrowed_object_and_costume_locations_remain_consistent(self):
        p = Parameters(teacher_available=False, minutes_left=1, seam_allowance=0, pins_available=False)
        row = generate(2, count=8, params=p)
        states = [row["episodes"][0]["before"]] + [e["after"] for e in row["episodes"]]
        borrowed = [s for s in states if s["cape.borrowed"]]
        self.assertTrue(borrowed)
        self.assertTrue(all(s["cape.holder"] == "ada" and s["cape.location"] == "ada_hands" for s in borrowed))
        final = row["final_state"]
        self.assertEqual(final["cape.owner"], "school")
        self.assertEqual(final["cape.holder"], "wardrobe")
        self.assertEqual(final["cape.location"], "cupboard_hook")
        self.assertTrue(final["cape.used"])
        self.assertTrue(final["cape.returned"])
        self.assertFalse(final["jo.wears_costume"])
        self.assertEqual(final["jo.role_performed"], "Storm")

    def test_scene_ids_and_invalid_parameters(self):
        self.assertEqual(len(SCENES), len(set(SCENES)))
        for kwargs in (
            {"seam_allowance": True}, {"seam_allowance": 3}, {"minutes_left": 0},
            {"pins_available": 1}, {"teacher_available": "yes"}, {"mirror_clear": 0},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        for count in (True, 6, 9):
            with self.subTest(count=count), self.assertRaises(ValueError):
                generate(0, count=count)
        with self.assertRaises(StoryError):
            replay(Parameters(), ("opening", "opening"))
        with self.assertRaises(StoryError):
            guard("not_a_scene", initial(Parameters()))

    def test_cli_prints_a_complete_story(self):
        result = subprocess.run(
            [sys.executable, "-m", "storyscenes.mini_adventures.kite.world", "--seed", "0", "--scenes", "8"],
            capture_output=True, text=True, check=True,
        )
        self.assertGreaterEqual(len(result.stdout.split("\n\n")), 8)
        self.assertIn("Storm", result.stdout)


if __name__ == "__main__":
    unittest.main()
