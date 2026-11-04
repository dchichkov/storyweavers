from copy import deepcopy
from dataclasses import replace
from itertools import product
import json
from pathlib import Path
import unittest

from storyscenes.runtime import StoryError
from .world import Parameters, SCENES, LocalPlay, generate, guard, initial, play_scene, replay, validate


class GreenhouseTests(unittest.TestCase):
    def check(self, row):
        p = Parameters(**row["parameters"])
        self.assertEqual(replay(p, row["path"]), row["episodes"])
        self.assertEqual(len(row["path"]), row["scene_count"])
        self.assertEqual(len(row["path"]), len(set(row["path"])))
        self.assertEqual(row["story"], "\n\n".join(e["text"] for e in row["episodes"]))
        state = initial(p)
        for e in row["episodes"]:
            self.assertEqual(e["before"], state)
            self.assertTrue(guard(e["id"], state))
            for event in e["events"]:
                for k, v in event["requires"].items():
                    self.assertEqual(state[k], v)
                self.assertTrue(event["changes"])
                for k, change in event["changes"].items():
                    self.assertEqual(state[k], change["before"])
                    state[k] = deepcopy(change["after"])
                validate(state)
            self.assertEqual(e["after"], state)
            self.assertGreaterEqual(len(e["text"].split()), 40)
            self.assertLessEqual(len(e["text"].split()), 75)
        self.assertEqual(state, row["final_state"])
        self.assertTrue(state["story.ended"])
        json.dumps(row, allow_nan=False)

    def test_hundred_seeds_both_lengths(self):
        seen, outcomes = set(), set()
        for seed, count in product(range(100), (7, 8)):
            row = generate(seed, count=count)
            self.check(row)
            seen.update(row["path"])
            outcomes.add(row["final_state"]["story.outcome"])
            self.assertEqual(row, generate(seed, count=count))
        self.assertEqual(seen, set(SCENES))
        self.assertEqual(outcomes, {"joint_care", "supervised_trial", "separation"})

    def test_full_parameter_grid(self):
        for i, values in enumerate(product(("wind", "heat"), (True, False), (True, False),
                                           (True, False), (True, False), ("patch", "shelter"))):
            p = Parameters(**dict(zip(("weather", "tape", "damp_seeds", "honest", "receptive", "strategy"), values)))
            for count in (7, 8):
                self.check(generate(i, params=p, count=count))

    def test_atomic_rejection_and_impossible_actions(self):
        p = Parameters()
        s = initial(p)
        saved = deepcopy(s)
        for sid in set(SCENES) - {"gate"}:
            with self.assertRaises(StoryError):
                play_scene(p, s, sid)
            self.assertEqual(s, saved)
        x = LocalPlay(s)
        with self.assertRaises(StoryError):
            x.act("teleport", {"door.open": True}, **{"party.location": "inside"})
        self.assertEqual(x.state, saved)
        with self.assertRaises(StoryError):
            replay(p, ["gate", "measuring", "measuring"])

    def test_omitted_vignettes_do_not_run(self):
        row = generate(0, count=7, params=Parameters())
        s = row["final_state"]
        self.assertFalse(s["mara.remembers_height"])
        self.assertEqual(s["snail.location"], "pot_rim")
        self.assertTrue(s["flask.full"])
        self.assertFalse(s["ledger.written"])
        self.assertNotIn("notebook", row["story"])

    def test_tape_changes_later_seed_carrier(self):
        p = Parameters(tape=False)
        without = generate(1, count=7, params=p)
        with_tape = generate(1, count=7, params=replace(p, tape=True))
        self.assertIn("patch_parcel", without["path"])
        self.assertIn("patch_tape", with_tape["path"])
        self.assertEqual(without["final_state"]["parcel.location"], "vent")
        self.assertEqual(with_tape["final_state"]["parcel.location"], "bench")
        self.assertIn("from the sandwich tin", without["story"])
        self.assertIn("from the parcel she opened", with_tape["story"])
        patch = next(e for e in without["episodes"] if e["id"] == "patch_parcel")
        self.assertIn("test_tape_roll", [e["action"] for e in patch["events"]])

    def test_honesty_and_damage_change_outcome(self):
        p = Parameters()
        good = generate(2, count=7, params=p)
        for changed in (replace(p, damp_seeds=True), replace(p, strategy="shelter"), replace(p, receptive=False)):
            row = generate(2, count=7, params=changed)
            self.assertEqual(row["final_state"]["story.outcome"], "supervised_trial")
            self.assertEqual(row["final_state"]["key.owner"], "ivo")
        lost = generate(2, count=7, params=replace(p, honest=False))
        self.assertEqual(lost["final_state"]["story.outcome"], "separation")
        self.assertEqual(lost["final_state"]["beans.location"], "mara_pocket")
        self.assertEqual(good["final_state"]["story.outcome"], "joint_care")
        self.assertEqual(good["final_state"]["key.owner"], "mara")

    def test_lost_tomatoes_do_not_earn_repair_dialogue(self):
        row = generate(822263078, count=7)
        self.assertEqual(row["final_state"]["tomatoes.state"], "lost")
        self.assertNotIn("That was help", row["story"])
        self.assertIn("You saved the present", row["story"])

    def test_missing_seeds_cannot_be_sown(self):
        row = generate(0, count=7, params=Parameters())
        s = deepcopy(next(e["before"] for e in row["episodes"] if e["id"] == "sow"))
        s["tin.location"] = "elsewhere"
        saved = deepcopy(s)
        with self.assertRaises(StoryError):
            play_scene(Parameters(), s, "sow")
        self.assertEqual(s, saved)

    def test_locations_and_compatible_endings(self):
        for p in (Parameters(), Parameters(honest=False), Parameters(damp_seeds=True)):
            row = generate(0, params=p, count=7)
            state = row["episodes"][-1]["before"]
            for sid in ("ending_joint", "ending_trial", "ending_apart"):
                self.assertEqual(guard(sid, state), sid == row["path"][-1])
            for e in row["episodes"][2:-1]:
                self.assertEqual(e["before"]["party.location"], "inside")
            self.assertFalse(row["final_state"]["door.open"])
            if p.honest:
                self.assertEqual(row["final_state"]["ivo.location"], "path")
            else:
                self.assertEqual(row["final_state"]["ivo.location"], "inside")

    def test_validation_and_inventory(self):
        for kwargs in ({"weather": "rain"}, {"strategy": "magic"}, {"tape": 1}, {"honest": "yes"}):
            with self.assertRaises(ValueError):
                Parameters(**kwargs)
        for count in (6, 9, True):
            with self.assertRaises(ValueError):
                generate(count=count)
        inventory = json.loads(Path(__file__).with_name("scene_inventory.json").read_text())
        self.assertEqual(set(SCENES), {sid for s in inventory["scenes"] for sid in s["implemented_ids"]})


if __name__ == "__main__":
    unittest.main()
