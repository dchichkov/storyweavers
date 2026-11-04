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
        self.assertGreaterEqual(s["lantern.fuel"], 1)
        self.assertTrue(s["loan.usable_checked"])
        self.assertTrue(s["vale.cellar_light_secured"])
        self.assertEqual(s["lantern.fuel_used"], 2 if s["table.served"] else
                         1 if s["loaf.location"] == "oven" else 0)

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
            p = Parameters(fuel=3, early_van=early, decision="request_extension")
            row = generate(1, count=7, params=p)
            self.assertEqual(row["final_state"]["story.outcome"], outcome)
            decision = row["episodes"][4]
            self.assertEqual(decision["after"]["loan.extended"], not early)
            self.assertEqual(decision["after"]["lantern.holder"], "vale" if early else "nell")

    def test_fuel_and_optional_refill_change_later_outcome(self):
        p = Parameters(fuel=2, decision="confess")
        base = ["launch", "borrow", "bake", "knock", "confess"]
        low = replay(p, base)[-1].after
        self.assertFalse(guard("finish_together", low))
        self.assertTrue(guard("postpone", low))
        high = replay(p, ["launch", "borrow", "refill", "bake", "knock", "confess"])[-1].after
        self.assertTrue(guard("finish_together", high))
        self.assertFalse(high["oil.available"])
        self.assertFalse(guard("postpone", high))
        self.assertEqual(low["lantern.fuel"], 1)
        self.assertEqual(high["lantern.fuel"], 2)
        failed = play_scene(p, low, "postpone")
        self.assertEqual(failed.after["lantern.fuel"], 1)
        self.assertFalse(failed.after["oven.on"])
        self.assertFalse(failed.after["loaf.ready"])
        final = play_scene(p, high, "finish_together")
        self.assertEqual(final.after["lantern.holder"], "vale")
        self.assertFalse(final.after["loan.returned"])
        self.assertEqual(final.after["lantern.fuel"], 1)
        self.assertTrue(final.after["loaf.ready"])

    def test_choice_changes_knowledge_and_ending(self):
        p = Parameters(fuel=3)
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
        p = Parameters(fuel=3)
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

    def test_early_van_cannot_be_overruled_by_confession(self):
        for decision in ("confess", "request_extension"):
            p = Parameters(fuel=3, early_van=True, decision=decision)
            row = generate(0, count=7, params=p)
            episode = next(e for e in row["episodes"] if e["id"] == decision)
            self.assertFalse(episode["after"]["loan.extended"])
            self.assertTrue(episode["after"]["loan.returned"])
            self.assertEqual(episode["after"]["lantern.holder"], "vale")
            self.assertEqual(row["final_state"]["story.outcome"], "breakfast_instead")
            self.assertNotIn("cellar can wait", row["story"])
            # The same fuel and choice can finish only when the actual deadline permits.
            late = generate(0, count=7, params=Parameters(fuel=3, decision=decision))
            self.assertTrue(late["final_state"]["table.served"])

    def test_one_measure_is_not_burned_even_to_start(self):
        p = Parameters(fuel=1, spare_oil=False)
        row = generate(2, count=7, params=p)
        s = row["final_state"]
        self.assertEqual(s["lantern.fuel"], 1)
        self.assertEqual(s["lantern.fuel_used"], 0)
        self.assertEqual(s["loaf.location"], "tin")
        self.assertEqual(s["oven.minutes_left"], 20)
        bake = next(e for e in row["episodes"] if e["id"] == "bake")
        self.assertIn("decline_to_burn_cellar_reserve", [e["action"] for e in bake["events"]])
        self.assertNotIn("light_lantern", [e["action"] for e in bake["events"]])
        self.assertIn("loaf stayed outside", bake["text"])

    def test_temporary_holding_is_not_settlement_and_empty_return_is_illegal(self):
        p = Parameters(fuel=3)
        s = self.through(p, "launch", "borrow", "bake", "knock", "confess")
        finished = play_scene(p, s, "finish_together")
        handed = next(e for e in finished.events if e["action"] == "hand_lantern_to_vale")
        self.assertNotIn("loan.returned", handed["changes"])
        self.assertFalse(finished.after["loan.returned"])
        ended = play_scene(p, finished.after, "ending_together")
        self.assertTrue(ended.after["loan.returned"])
        self.assertTrue(ended.after["lantern.resting"])
        self.assertEqual(ended.after["crown.location"], "table")
        x = LocalPlay(s)
        x.hand("vale")
        before = deepcopy(x.state)
        with self.assertRaises(StoryError):
            x.act("burn_owners_last_oil", **{"lantern.fuel": 0,
                  "lantern.fuel_used": x.state["fuel.initial_total"] - x.state["oil.units"]})
        self.assertEqual(x.state, before)
        # A forged zero-fuel snapshot cannot be accepted as a completed loan.
        bad = deepcopy(ended.after)
        bad["lantern.fuel_used"] += bad["lantern.fuel"]
        bad["lantern.fuel"] = 0
        with self.assertRaises(StoryError):
            validate(bad)

    def test_postponement_is_only_a_request_and_cups_are_physically_placed(self):
        for fuel in (1, 2):
            row = generate(1, count=7, params=Parameters(fuel=fuel, decision="return_now"))
            s = row["final_state"]
            self.assertFalse(s["loaf.ready"])
            self.assertFalse(s["invitation.accepted"])
            self.assertEqual(s["baker.location"], "town")
            self.assertEqual(s["baker_request.location"], "counter")
            self.assertEqual(s["cups.location"], "counter")
            self.assertEqual(s["crown.location"], "counter")
            self.assertIn("Can this loaf be saved?", row["story"])
            self.assertIn("before you leave tomorrow", row["story"])
            self.assertNotIn("baker would finish", row["story"])
            self.assertIn("unanswered note", row["story"])

    def test_reference_count_uses_prose_only(self):
        text = Path(__file__).with_name("reference_story.md").read_text()
        self.assertEqual(len(text.split()), 963)
        self.assertEqual(len("\n".join(text.splitlines()[1:]).split()), 957)

    def test_documented_diagnostic_outcome_recipes(self):
        recipes = {
            "surprise_supper": Parameters(fuel=3, early_van=False, decision="request_extension"),
            "shared_supper": Parameters(fuel=3, early_van=False, decision="confess"),
            "breakfast_instead": Parameters(fuel=1, early_van=False, decision="return_now", spare_oil=False),
        }
        for expected, p in recipes.items():
            with self.subTest(expected=expected):
                row = generate(0, count=7, params=p)
                self.check_row(row)
                self.assertEqual(row["final_state"]["story.outcome"], expected)

    def test_successful_endings_keep_checks_without_audit_label_dialogue(self):
        from storyscenes.mini_adventures.local_play import LocalPlay as AtomicLocalPlay
        self.assertTrue(issubclass(LocalPlay, AtomicLocalPlay))
        for decision in ("confess", "request_extension"):
            row = generate(0, count=7, params=Parameters(fuel=3, decision=decision))
            ending = row["episodes"][-1]
            self.assertNotIn("usable lantern", ending["text"])
            self.assertNotIn("Now it's returned", ending["text"])
            self.assertIn("check_usable_lantern_and_settle_loan",
                          [event["action"] for event in ending["events"]])
            self.assertTrue(ending["after"]["vale.cellar_light_secured"])
            self.assertTrue(ending["after"]["loan.returned"])
            self.assertTrue(ending["after"]["lantern.resting"])

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
