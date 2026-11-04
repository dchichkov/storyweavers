from copy import deepcopy
from dataclasses import asdict
from itertools import product
import json
from pathlib import Path
import unittest

from storyscenes.runtime import StoryError
from .world import (LocalPlay, OPTIONAL, SCENES, Parameters, generate, guard, initial,
                    parameters, play_scene, replay, validate)


class BakeryTests(unittest.TestCase):
    def through(self, p, *path):
        return replay(p, path)[-1].after

    def check_row(self, row):
        p = Parameters(**row["parameters"])
        episodes = replay(p, row["path"])
        self.assertEqual([asdict(e) for e in episodes], row["episodes"])
        self.assertEqual(episodes[-1].after, row["final_state"])
        self.assertEqual("\n\n".join(e.text for e in episodes), row["story"])
        self.assertEqual(row["scene_count"], len(row["path"]))
        self.assertEqual(len(set(row["path"])), len(row["path"]))
        json.dumps(row)
        s = initial(p)
        for ep in episodes:
            self.assertEqual(ep.before, s)
            self.assertTrue(guard(ep.id, s))
            for event in ep.events:
                for k, v in event["requires"].items():
                    self.assertEqual(s[k], v)
                self.assertTrue(event["changes"])
                for k, change in event["changes"].items():
                    self.assertEqual(s[k], change["before"])
                    s[k] = change["after"]
                validate(s)
            self.assertEqual(s, ep.after)
            self.assertGreaterEqual(len(ep.text.split()), 40)
            self.assertLessEqual(len(ep.text.split()), 70)
        self.assertTrue(s["story.ended"])
        self.assertTrue(s["loan.returned"])
        self.assertEqual(s["lantern.owner"], "vale")

    def test_hundred_seeds_both_lengths(self):
        outcomes, optional = set(), set()
        for seed, count in product(range(100), (7, 8)):
            row = generate(seed, count=count)
            self.check_row(row)
            outcomes.add(row["final_state"]["story.outcome"])
            optional.update(set(row["path"]) & set(OPTIONAL))
            self.assertEqual(len(set(row["path"]) & set(OPTIONAL)), count - 7)
        self.assertEqual(outcomes, {"surprise_supper", "shared_supper", "breakfast_instead"})
        self.assertEqual(optional, set(OPTIONAL))

    def test_parameter_corner_grid(self):
        for fuel, early, decision, stuck, oil, torn in product(
                (1, 2, 3), (False, True), ("confess", "request_extension", "return_now"),
                (False, True), (False, True), (False, True)):
            p = Parameters(fuel=fuel, early_van=early, decision=decision, wick_stuck=stuck,
                           spare_oil=oil, torn_crown=torn)
            for count in (7, 8):
                self.check_row(generate(42, count=count, params=p))

    def test_deterministic(self):
        self.assertEqual(generate(757654805), generate(757654805))
        self.assertEqual(parameters(3), parameters(3))

    def test_illegal_scenes_do_not_mutate(self):
        p = Parameters()
        s = initial(p)
        for scene in SCENES:
            if scene == "launch":
                continue
            before = deepcopy(s)
            with self.assertRaises(StoryError):
                play_scene(p, s, scene)
            self.assertEqual(s, before)
        with self.assertRaises(StoryError):
            replay(p, ("launch", "launch"))
        with self.assertRaises(StoryError):
            play_scene(p, s, "unknown")

    def test_spatial_and_prop_guards(self):
        p = Parameters()
        s = self.through(p, "launch", "borrow")
        self.assertEqual(s["lantern.location"], "bakery")
        with self.assertRaises(StoryError):
            LocalPlay(s).move("workshop")
        baked = play_scene(p, s, "bake")
        self.assertEqual(baked.after["lantern.holder"], "shelf")
        self.assertEqual(baked.after["lantern.location"], "oven_room")
        with self.assertRaises(StoryError):
            play_scene(p, baked.after, "return_now")
        asked = play_scene(p, baked.after, "knock")
        self.assertEqual(asked.after["lantern.location"], "bakery")
        self.assertEqual(asked.after["lantern.fuel"], p.fuel - 1)
        self.assertIn("try_wick_wheel_failed", [e["action"] for e in baked.events])
        smooth = self.through(Parameters(wick_stuck=False), "launch", "borrow", "bake")
        self.assertFalse(smooth["lantern.wick_stuck"])
        bad = deepcopy(s)
        bad["lantern.location"] = "workshop"
        with self.assertRaises(StoryError):
            play_scene(p, bad, "bake")
        self.assertEqual(bad["lantern.location"], "workshop")

    def test_deadline_changes_later_outcome(self):
        for early, outcome in ((False, "surprise_supper"), (True, "breakfast_instead")):
            p = Parameters(early_van=early, decision="request_extension")
            row = generate(1, count=7, params=p)
            self.assertEqual(row["final_state"]["story.outcome"], outcome)
            decision = row["episodes"][4]
            self.assertEqual(decision["after"]["loan.extended"], not early)
            self.assertEqual(decision["after"]["lantern.holder"], "vale" if early else "nell")

    def test_fuel_and_optional_refill_change_later_outcome(self):
        p = Parameters(fuel=1, decision="confess")
        base = ["launch", "borrow", "bake", "knock", "confess"]
        low = replay(p, base)[-1].after
        self.assertFalse(guard("finish_together", low))
        self.assertTrue(guard("postpone", low))
        high = replay(p, ["launch", "borrow", "refill", "bake", "knock", "confess"])[-1].after
        self.assertTrue(guard("finish_together", high))
        self.assertFalse(high["oil.available"])
        self.assertFalse(guard("postpone", high))
        self.assertEqual(low["lantern.fuel"], 0)
        self.assertEqual(high["lantern.fuel"], 1)
        failed = play_scene(p, low, "postpone")
        self.assertIn("try_relight_empty_lantern", [e["action"] for e in failed.events])
        self.assertTrue(failed.after["lantern.relight_failed"])
        final = play_scene(p, high, "finish_together")
        self.assertEqual(final.after["lantern.holder"], "vale")
        self.assertEqual(final.after["lantern.fuel"], 0)
        self.assertTrue(final.after["loaf.ready"])

    def test_choice_changes_knowledge_and_ending(self):
        p = Parameters()
        s = self.through(p, "launch", "borrow", "bake", "knock")
        honest = play_scene(p, s, "confess").after
        secret = play_scene(p, s, "request_extension").after
        self.assertTrue(guard("finish_together", honest))
        self.assertFalse(guard("finish_secret", honest))
        self.assertTrue(guard("finish_secret", secret))
        self.assertFalse(guard("finish_together", secret))
        self.assertEqual(honest["nell.memes.Secrecy"], 0)
        self.assertEqual(secret["nell.memes.Secrecy"], 2)
        a = play_scene(p, honest, "finish_together").after
        b = play_scene(p, secret, "finish_secret").after
        self.assertTrue(guard("ending_together", a))
        self.assertFalse(guard("ending_secret", a))
        self.assertTrue(guard("ending_secret", b))

    def test_optional_omission_no_ghost_effects(self):
        p = Parameters(fuel=2)
        path = ["launch", "borrow", "bake", "knock", "confess", "finish_together", "ending_together"]
        without = replay(p, path)
        with_darn = replay(p, path[:2] + ["darn"] + path[2:])
        self.assertNotIn("blue darn", without[-1].text)
        self.assertIn("blue darn", with_darn[-1].text)
        final = without[-1].after
        self.assertEqual(final["glove.location"], "counter")
        self.assertFalse(final["cloth.darn_visible"])
        self.assertFalse(final["nell.knows_wick"])
        self.assertTrue(final["oil.available"])
        self.assertFalse(final["notice.hidden"])

    def test_inventory_actual_ids_and_complete_coverage(self):
        inventory = json.loads(Path(__file__).with_name("scene_inventory.json").read_text())
        self.assertEqual(len(inventory["scenes"]), 20)
        ids = {i for s in inventory["scenes"] for i in s["implemented_ids"]}
        self.assertEqual(ids, set(SCENES))

    def test_validation(self):
        for kw in ({"fuel": True}, {"fuel": 0}, {"fuel": 4}, {"decision": "steal"},
                   {"early_van": 1}, {"spare_oil": "yes"}, {"torn_crown": None}):
            with self.assertRaises(ValueError):
                Parameters(**kw)
        for count in (True, 6, 9):
            with self.assertRaises(ValueError):
                generate(count=count)
        p = Parameters(spare_oil=False)
        s = self.through(p, "launch", "borrow")
        before = deepcopy(s)
        with self.assertRaises(StoryError):
            play_scene(p, s, "refill")
        self.assertEqual(s, before)


if __name__ == "__main__":
    unittest.main()
