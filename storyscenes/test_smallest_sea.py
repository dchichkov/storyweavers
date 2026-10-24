from copy import deepcopy
from dataclasses import asdict
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from storyscenes.runtime import StoryError, holds
from storyscenes.smallest_sea import (
    LocalPlay, Parameters, conditions, generate, guard, initial, play_scene, replay, validate,
)


class SmallestSeaTests(unittest.TestCase):
    def through(self, p, *path):
        return replay(p, path)[-1].after

    def check_row(self, row):
        p = Parameters(**row["parameters"])
        episodes = replay(p, row["path"])
        self.assertEqual([asdict(e) | {"events": list(e.events)} for e in episodes], row["episodes"])
        self.assertEqual(episodes[-1].after, row["final_state"])
        self.assertEqual("\n\n".join(e.text for e in episodes), row["story"])
        self.assertEqual(len(episodes), row["scene_count"])
        self.assertTrue(episodes[-1].after["party.ended"])
        self.assertEqual(len(row["path"]), len(set(row["path"])))
        state = initial(p)
        for episode in episodes:
            self.assertEqual(episode.before, state)
            self.assertTrue(guard(episode.id, state))
            for event in episode.events:
                self.assertTrue(holds(state, conditions(**event["requires"])))
                self.assertTrue(event["changes"])
                for key, values in event["changes"].items():
                    self.assertEqual(values["before"], state[key])
                    state[key] = values["after"]
                validate(state)
            self.assertEqual(state, episode.after)

    def test_two_hundred_seeded_routes_replay(self):
        endings = set()
        lengths = set()
        for seed, count in product(range(100), (7, 8)):
            row = generate(seed, count=count)
            self.check_row(row)
            endings.add(row["path"][-1])
            lengths.add(len(row["path"]))
            if "enter_summerhouse" in row["path"]:
                self.assertIn("exit_summerhouse", row["path"])
                self.assertLess(row["path"].index("exit_summerhouse"), row["path"].index("crossing"))
                self.assertTrue({"lights", "height_marks"} & set(row["path"]))
        self.assertEqual(lengths, {7, 8})
        self.assertEqual(endings, {"ending_bridge", "ending_explorer", "ending_together"})

    def test_parameter_grid(self):
        # Full 2^9 corner grid for the sampled dimensions, not the numeric domain.
        for i, values in enumerate(product((80, 140), (True, False), (True, False), (True, False),
                                            (1, 3), (True, False), (True, False), (True, False), (True, False))):
            p = Parameters(**dict(zip(("board_cm", "board_sound", "daylight", "sticky_door", "pot_mass",
                                      "tight_lid", "change_coat", "grab_whole", "map_upside_down"), values)))
            with self.subTest(parameters=p):
                for count in (7, 8):
                    self.check_row(generate(i, count=count, params=p))

    def test_deterministic_with_parameter_overrides(self):
        p = Parameters(captain="Nora", explorer="Ben", board_cm=150)
        a = generate(3, params=p)
        self.assertEqual(a, generate(3, params=p))
        self.assertIn("Nora", a["story"])
        self.assertIn("Ben", a["story"])
        self.assertNotIn("Tom", a["story"])
        self.assertNotIn("Lily", a["story"])

    def test_compatible_entry_exit_and_no_teleport(self):
        p = Parameters()
        state = self.through(p, "launch")
        for scene in ("lights", "exit_summerhouse", "treasure", "share", "ending_explorer"):
            with self.assertRaises(StoryError):
                play_scene(p, state, scene)
        inside = play_scene(p, state, "enter_summerhouse").after
        with self.assertRaises(StoryError):
            play_scene(p, inside, "crossing")
        with self.assertRaises(StoryError):
            LocalPlay(inside).move("tree")
        outside = play_scene(p, inside, "exit_summerhouse").after
        self.assertEqual(outside["party.location"], "garden")
        self.assertFalse(outside["summerhouse.light_on"])
        self.assertFalse(outside["summerhouse.door_open"])

    def test_same_lights_scene_different_physical_outcomes(self):
        for daylight in (True, False):
            p = Parameters(daylight=daylight)
            # Including clothing first also checks independent local request flags.
            inside = self.through(p, "launch", "change_clothes", "enter_summerhouse")
            episode = play_scene(p, inside, "lights")
            self.assertEqual(episode.after["summerhouse.apology"], not daylight)
            self.assertFalse(episode.after["explorer.afraid"])
            self.assertTrue(episode.after["summerhouse.light_on"])
            if daylight:
                self.assertNotIn("ask_for_light", [e["action"] for e in episode.events])
                self.assertIn("sunny", episode.text)
            else:
                self.assertIn("ask_for_light", [e["action"] for e in episode.events])
                self.assertIn("Sorry", episode.text)

    def test_darkness_rejects_height_reading(self):
        p = Parameters()
        x = LocalPlay(self.through(p, "launch", "enter_summerhouse"))
        x.light(False)
        with self.assertRaises(StoryError):
            play_scene(p, x.state, "height_marks")

    def test_board_support_threshold_and_material(self):
        for length, sound, expected in ((119, True, "detour"), (120, True, "board"), (160, False, "detour")):
            p = Parameters(board_cm=length, board_sound=sound, gap_cm=100)
            episode = replay(p, ("launch", "crossing"))[-1]
            self.assertEqual(episode.after["party.route"], expected)
            self.assertEqual(episode.after["captain.sleeve_wet"], expected == "detour")
            self.assertEqual(episode.after["board.location"], "puddle" if expected == "board" else "bank")
            actions = [e["action"] for e in episode.events]
            self.assertLess(actions.index("test_board"), actions.index("walk:garden:tree"))

    def test_broken_return_bridge_cannot_be_crossed(self):
        p = Parameters(board_cm=160)
        state = self.through(p, "launch", "crossing", "treasure", "share")
        state["board.supported"] = False
        state["board.sound"] = False
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(p, state, "ending_bridge")
        self.assertEqual(state, saved)

    def test_heavy_pot_and_wet_hands_have_actual_local_actions(self):
        p = Parameters(pot_mass=3, tight_lid=True)
        state = self.through(p, "launch", "crossing")
        episode = play_scene(p, state, "treasure")
        actions = [e["action"] for e in episode.events]
        for action in ("try_lift_pot", "lift_pot_together", "set_pot_aside", "pick_up_tin",
                       "try_lid", "dry_hands", "brace_tin", "open_tin"):
            self.assertIn(action, actions)
        self.assertLess(actions.index("set_pot_aside"), actions.index("pick_up_tin"))
        self.assertTrue(episode.after["party.knows_contents"])
        self.assertFalse(episode.after["pot.raised"])
        self.assertFalse(episode.after["captain.hands_wet"])
        self.assertTrue(state["captain.hands_wet"])

    def test_impossible_lift_is_atomic(self):
        p = Parameters()
        state = self.through(p, "launch", "crossing")
        state["pot.mass"] = 5
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(p, state, "treasure")
        self.assertEqual(state, saved)

    def test_memory_is_optional_and_has_only_local_effects(self):
        p = Parameters()
        base = self.through(p, "launch")
        memory = play_scene(p, base, "old_flag")
        changed = {k for k in base if base[k] != memory.after[k]}
        self.assertEqual(changed, {"explorer.remembers_ship", "flag.location"})
        without = self.through(p, "launch", "crossing", "treasure", "share", "ending_explorer")
        with_memory = self.through(p, "launch", "old_flag", "crossing", "treasure", "share", "ending_explorer")
        self.assertEqual({k for k in without if without[k] != with_memory[k]}, changed)

    def test_endings_require_their_actual_middle(self):
        for p, middle, ending in (
            (Parameters(), (), "ending_explorer"),
            (Parameters(board_cm=150), (), "ending_bridge"),
            (Parameters(), ("enter_summerhouse", "lights", "exit_summerhouse"), "ending_together"),
        ):
            state = self.through(p, "launch", *middle, "crossing", "treasure", "share")
            for candidate in ("ending_explorer", "ending_bridge", "ending_together"):
                self.assertEqual(guard(candidate, state), candidate == ending)
            final = play_scene(p, state, ending).after
            self.assertFalse(guard("launch", final))

    def test_omitted_scene_has_no_invented_callback(self):
        p = Parameters()
        path = ("launch", "crossing", "treasure", "share", "ending_explorer")
        ending = replay(p, path)[-1].text
        self.assertNotIn("Should have changed", ending)
        self.assertNotIn("green jacket", ending)
        self.assertNotIn("making it dark", ending)
        x = self.through(p, "launch", "change_clothes", "crossing")
        self.assertEqual(x["captain.coat"], "green")
        end = self.through(p, "launch", "change_clothes", "crossing", "treasure", "share", "ending_explorer")
        self.assertEqual(end["captain.coat"], "none")
        self.assertEqual(end["green_jacket.location"], "hook")
        self.assertEqual(end["red_coat.location"], "hook")
        self.assertEqual(end["hat.owner"], "explorer")

    def test_invalid_parameters_counts_and_repeated_scenes(self):
        for kwargs in ({"captain": "Lily"}, {"explorer": "Mom"}, {"board_cm": True},
                       {"pot_mass": 5}, {"daylight": "false"}, {"captain": "<b>"}):
            with self.assertRaises(ValueError):
                Parameters(**kwargs)
        for count in (True, 6, 9):
            with self.assertRaises(ValueError):
                generate(count=count)
        with self.assertRaises(StoryError):
            replay(Parameters(), ("launch", "old_flag", "old_flag"))

    def test_cli_export_is_reproducible_and_does_not_overwrite(self):
        with tempfile.TemporaryDirectory() as root:
            out = Path(root) / "batch"
            cmd = [sys.executable, "-m", "storyscenes.smallest_sea", "--seed", "0", "--count", "2", "--out", str(out)]
            subprocess.run(cmd, check=True, capture_output=True, text=True)
            rows = [json.loads(line) for line in (out / "stories.jsonl").read_text().splitlines()]
            self.assertEqual(rows, [generate(0), generate(1)])
            self.assertNotEqual(subprocess.run(cmd, capture_output=True).returncode, 0)
            frozen = subprocess.run([sys.executable, "-m", "source.smallest_sea", "--seed", "0"],
                                    cwd=out, capture_output=True, text=True, check=True)
            self.assertIn(rows[0]["story"], frozen.stdout)


if __name__ == "__main__":
    unittest.main()
