from copy import deepcopy
from dataclasses import asdict
import json
import unittest

from storyscenes.runtime import StoryError
from storyscenes.mini_adventures.local_play import LocalPlay
from .world import (
    Parameters, SCENES, generate, guard, initial, parameters, play_scene, replay, validate,
)


class KitePackTests(unittest.TestCase):
    def assert_row_replays(self, row):
        p = Parameters(**row["parameters"])
        episodes = replay(p, row["path"])
        encoded = [asdict(ep) | {"events": list(ep.events)} for ep in episodes]
        self.assertEqual(encoded, row["episodes"])
        self.assertEqual([ep.id for ep in episodes], row["path"])
        self.assertEqual("\n\n".join(ep.text for ep in episodes), row["story"])
        self.assertEqual(episodes[-1].after, row["final_state"])
        self.assertTrue(row["final_state"]["story.ended"])
        self.assertTrue(row["final_state"]["story.outcome"])
        self.assertEqual(len(row["path"]), len(set(row["path"])))

        state = initial(p)
        for ep in episodes:
            self.assertEqual(ep.before, state)
            self.assertTrue(guard(ep.id, state))
            self.assertGreaterEqual(len(ep.text.split()), 40)
            self.assertLessEqual(len(ep.text.split()), 70)
            self.assertTrue(ep.events)
            for event in ep.events:
                for key, value in event["requires"].items():
                    self.assertIn(key, state)
                    self.assertEqual(state[key], value)
                self.assertTrue(event["changes"])
                for key, change in event["changes"].items():
                    self.assertIn(key, state)
                    self.assertEqual(change["before"], state[key])
                    self.assertNotEqual(change["before"], change["after"])
                    state[key] = deepcopy(change["after"])
                validate(state)
            self.assertEqual(ep.after, state)
        self.assertEqual(state, row["final_state"])

    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        for count in (7, 8):
            for seed in range(100):
                with self.subTest(count=count, seed=seed):
                    row = generate(seed, count=count)
                    self.assertEqual(row, generate(seed, count=count))
                    self.assertEqual(len(row["path"]), count)
                    optional = {"button_vignette", "whisper_vignette"} & set(row["path"])
                    self.assertEqual(len(optional), count - 6)
                    self.assert_row_replays(row)

    def test_parameter_validation_and_seeded_parameters(self):
        self.assertEqual(parameters(17), parameters(17))
        invalid = (
            {"needle": "soft"}, {"thread": "infinite"}, {"button_strength": "weak"},
            {"curtain_weight": "invisible"}, {"minutes": True}, {"minutes": 3},
            {"minutes": 9}, {"spare_button": 1},
        )
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        with self.assertRaises(ValueError):
            generate(0, count=True)
        with self.assertRaises(ValueError):
            generate(0, count=6)

    def test_illegal_scene_and_local_action_fail_without_mutation(self):
        p = Parameters()
        source = initial(p)
        saved = deepcopy(source)
        with self.assertRaises(StoryError):
            play_scene(p, source, "test_moon")
        self.assertEqual(source, saved)

        play = LocalPlay(source, actors=("leni", "jo", "ivo"), validate=validate)
        before_state, before_events = deepcopy(play.state), deepcopy(play.events)
        with self.assertRaises(StoryError):
            play.act("illegal_borrow", requires={"kit.owner": "friends"}, **{"story.ended": True})
        self.assertEqual(play.state, before_state)
        self.assertEqual(play.events, before_events)

    def test_optional_scenes_have_only_enacted_effects(self):
        p = Parameters(button_strength="cracked", minutes=4, spare_button=True)
        state = initial(p)
        state = play_scene(p, state, "borrow_kit").after
        state = play_scene(p, state, "find_moon").after
        no_vignette = deepcopy(state)
        self.assertFalse(no_vignette["button.checked"])
        self.assertFalse(no_vignette["ivo.heard"])
        after_repair_without = play_scene(p, no_vignette, "repair_moon").after
        self.assertEqual(after_repair_without["button.location"], "kit")
        self.assertFalse(after_repair_without["ivo.confidence"])
        with_button = play_scene(p, state, "button_vignette").after
        self.assertEqual(with_button["button.location"], "friends")
        self.assertFalse(with_button["ivo.confidence"])
        with_whisper = play_scene(p, state, "whisper_vignette").after
        self.assertTrue(with_whisper["ivo.confidence"])
        self.assertEqual(with_whisper["button.location"], "kit")

    def test_parameter_counterfactual_changes_repair_and_ending(self):
        sturdy = Parameters(needle="sharp", thread="long", button_strength="sound",
                           curtain_weight="heavy", minutes=4, spare_button=False)
        fragile = Parameters(needle="blunt", thread="short", button_strength="cracked",
                             curtain_weight="heavy", minutes=4, spare_button=False)
        good_row = generate(2, count=8, params=sturdy)
        bad_row = generate(2, count=8, params=fragile)
        self.assertEqual(good_row["path"][-1], "ending_rod")
        self.assertEqual(bad_row["path"][-1], "ending_shadow")
        self.assert_row_replays(good_row)
        self.assert_row_replays(bad_row)
        self.assertNotEqual(good_row["final_state"]["story.outcome"], bad_row["final_state"]["story.outcome"])

    def test_spare_button_and_rehearsal_time_can_enable_a_secure_repair(self):
        p = Parameters(needle="sharp", thread="long", button_strength="cracked",
                       curtain_weight="light", minutes=4, spare_button=True)
        state = initial(p)
        for scene in ("borrow_kit", "find_moon", "button_vignette"):
            state = play_scene(p, state, scene).after
        repaired = play_scene(p, state, "repair_moon").after
        self.assertEqual(repaired["prop.repair"], "secure")
        self.assertEqual(repaired["prop.fastener"], "spare_button")
        self.assertEqual(repaired["button.location"], "sewn")

        time_p = Parameters(needle="sharp", thread="long", button_strength="cracked",
                            curtain_weight="light", minutes=8, spare_button=False)
        time_state = initial(time_p)
        for scene in ("borrow_kit", "find_moon"):
            time_state = play_scene(time_p, time_state, scene).after
        time_repair = play_scene(time_p, time_state, "repair_moon").after
        self.assertEqual(time_repair["prop.fastener"], "cloth_loop")
        self.assertEqual(time_repair["prop.repair"], "secure")

    def test_prop_kit_and_button_location_continuity_through_endings(self):
        p = Parameters()
        row = generate(9, count=8, params=p)
        state = initial(p)
        for ep in replay(p, row["path"]):
            state = ep.after
            if state["kit.owner"] == "friends":
                self.assertEqual(state["kit.location"], "friends")
            if state["button.location"] == "sewn":
                self.assertEqual(state["prop.fastener"], "spare_button")
            if state["prop.location"] == "rod":
                self.assertTrue(state["prop.attached"])
        final = row["final_state"]
        self.assertEqual(final["kit.owner"], "teacher")
        self.assertEqual(final["kit.location"], "costume_room")
        self.assertTrue(final["kit.returned"])
        self.assertTrue(final["kit.used"])

    def test_ending_recipes_are_complete(self):
        show = Parameters(needle="sharp", thread="long", button_strength="sound",
                          curtain_weight="heavy", minutes=4, spare_button=False)
        show_row = generate(0, count=8, params=show)
        self.assertEqual(show_row["path"][-1], "ending_rod")
        self.assertTrue(show_row["final_state"]["ivo.confidence"])

        shadow = Parameters(needle="blunt", thread="short", button_strength="cracked",
                            curtain_weight="heavy", minutes=4, spare_button=False)
        shadow_row = generate(0, count=8, params=shadow)
        self.assertEqual(shadow_row["path"][-1], "ending_shadow")
        self.assertEqual(shadow_row["final_state"]["story.outcome"], "rehearsal_saved_as_shadow_story")
        self.assertTrue(shadow_row["final_state"]["ivo.performed"])
        self.assert_row_replays(show_row)
        self.assert_row_replays(shadow_row)

    def test_scene_ids_are_unique_and_replay_rejects_repetition(self):
        self.assertEqual(len(SCENES), len(set(SCENES)))
        with self.assertRaises(StoryError):
            replay(Parameters(), ("borrow_kit", "borrow_kit"))


if __name__ == "__main__":
    unittest.main()
