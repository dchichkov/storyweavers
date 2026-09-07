"""The magpie chooses a usable object; her acceptance is not an instant refund."""

import ast
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

from worlds import nell_and_the_dragon as story


class NellAndDragonTests(unittest.TestCase):
    def ready(self, need="shine", solution="trinkets"):
        world = story.build_world(story.StoryParams(need=need, solution=solution))
        world.entities["nell"].beliefs["need"] = need
        story.set_dish(world)
        story.step_back(world)
        return world

    def cli(self, *flags, hash_seed="1"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed)
        env.pop("PYTHONPATH", None)
        return subprocess.run([sys.executable, str(Path(story.__file__).resolve()), *flags],
                              env=env, capture_output=True, text=True, timeout=60)

    def test_default_preserves_source_beats_and_spare_dialogue(self):
        sample = story.generate(story.StoryParams())
        for fragment in ("Nell's window at half past four", "I require a thief", "Pea-sized",
                         "kingdom-sized pocket", "approached this as a dragon", "She took the button",
                         "Wait", "A story. A true one", "I'll ask questions"):
            self.assertIn(fragment, sample.story)
        lines = [event for event in sample.world.history if event.kind == "speech"]
        self.assertGreaterEqual(len(lines), 35)
        self.assertGreater(sum(event.text.endswith('"') for event in lines), len(lines) / 2)
        self.assertNotIn('But..,', sample.story)
        self.assertIn('"But..."', sample.story)
        self.assertEqual(sample.world.entities["dragon"].beliefs["payment_promised"], "a true story about his travels")
        self.assertNotIn("payment_delivered", sample.world.entities["dragon"].beliefs)

    def test_all_states_have_grounded_qa_and_completed_exchange(self):
        chosen = set()
        for need, solution in story.valid_combos():
            for approach in story.APPROACHES:
                for jewel in story.JEWELS:
                    with self.subTest(need=need, approach=approach, jewel=jewel):
                        sample = story.generate(story.StoryParams(need=need, solution=solution,
                                                                 approach=approach, jewel=jewel))
                        story.check_sample(sample)
                        world = sample.world
                        chosen.add(world.entities["bird"].beliefs["selected"])
                        events = {e.kind: e for e in world.history}
                        for kind in ("take_offer", "return_to_nest"):
                            self.assertEqual(events[kind].state["jewel"]["location"], "nest")
                        self.assertEqual(events["replace_jewel"].state["jewel"]["location"], "falling")
                        self.assertEqual(events["catch"].state["jewel"]["location"], "dragon_claw")
                        self.assertEqual("interrupted" in events, approach == "hasty")
                        if approach == "hasty":
                            self.assertEqual(events["interrupted"].state["bird"]["memes"]["fear"], 1)
                        self.assertEqual(world.entities["bird"].memes["fear"], 0)
                        self.assertEqual(world.entities["ruby"].location, "dragon_claw")
                        self.assertEqual(events["ending"].kind, world.history[-1].kind)
                        self.assertNotIn("{", sample.story)
                        for pair in sample.story_qa:
                            self.assertIn(pair.answer, [f"{e.cause} {e.result}" for e in world.history if e.question])
                            self.assertGreaterEqual(len(re.findall(r'[.!?](?:\s|$)', pair.answer)), 2)
        self.assertEqual(chosen, {"button", "hoop", "wool"})

    def test_affordances_choose_the_offer_not_the_plot_label(self):
        world = self.ready()
        world.entities["button"].meters["shine"] = 1
        self.assertIsNone(story.preferred_offer(world))
        world.entities["glass"].meters["shine"] = 7
        self.assertEqual(story.preferred_offer(world), "glass")
        self.assertEqual(story.visit_dish(world), "glass")

    def test_expensive_but_uncarryable_ruby_is_ineligible(self):
        world = self.ready()
        world.entities["ruby"].location = "dish"
        self.assertEqual(story.preferred_offer(world), "button")
        world.entities["ruby"].meters["weight"] = 1
        self.assertEqual(story.preferred_offer(world), "ruby")

    def test_bad_distance_noise_or_teeth_prevent_taking(self):
        for who, key, value in (("dragon", "distance", 4), ("nell", "distance", 4),
                                ("dragon", "teeth", 1), ("dragon", "volume", 1)):
            with self.subTest(who=who, key=key):
                world = self.ready()
                world.entities[who].meters[key] = value
                self.assertIsNone(story.visit_dish(world))
                self.assertEqual(world.entities["button"].location, "dish")
                self.assertEqual(world.entities["jewel"].location, "nest")
                story.step_back(world)
                self.assertEqual(story.visit_dish(world), "button")

    def test_jewel_returns_only_after_installation_and_catch(self):
        world = self.ready()
        for operation in (story.return_to_nest, story.install_offer, story.catch_jewel):
            with self.assertRaises(story.StoryError):
                operation(world)
        story.visit_dish(world)
        for operation in (story.visit_dish, story.install_offer, story.catch_jewel):
            with self.assertRaises(story.StoryError):
                operation(world)
        story.return_to_nest(world)
        self.assertEqual(world.entities["jewel"].location, "nest")
        story.install_offer(world)
        self.assertEqual(world.entities["jewel"].location, "falling")
        with self.assertRaises(story.StoryError):
            story.install_offer(world)
        world.entities["dragon"].meters["distance"] = 99
        with self.assertRaises(story.StoryError):
            story.catch_jewel(world)
        story.step_back(world)
        story.catch_jewel(world)
        with self.assertRaises(story.StoryError):
            story.catch_jewel(world)

    def test_guard_rejects_a_replacement_that_stopped_being_useful(self):
        world = self.ready()
        story.visit_dish(world)
        story.return_to_nest(world)
        world.entities["button"].meters["shine"] = 0
        with self.assertRaises(story.StoryError):
            story.install_offer(world)
        self.assertEqual(world.entities["jewel"].location, "nest")

    def test_observation_information_and_physical_reach(self):
        world = story.build_world(story.StoryParams())
        before = copy.deepcopy(world.snapshot())
        with self.assertRaises(story.StoryError):
            story.set_dish(world)
        with self.assertRaises(story.StoryError):
            world.say("nell", "I know what she wants.", to="dragon", reveal="need")
        self.assertEqual(before, world.snapshot())
        self.assertFalse(story.can_reach_without_damage(world))
        world.entities["dragon"].meters["claw_width"] = 1
        self.assertTrue(story.can_reach_without_damage(world))

    def test_invalid_params_are_not_silently_replaced(self):
        for fields in (dict(need="fasten"), dict(need="unknown"), dict(solution="missing"),
                       dict(approach="missing"), dict(jewel="missing"), dict(hero="not a name")):
            with self.subTest(fields=fields), self.assertRaises(story.StoryError):
                story.generate(story.StoryParams(**fields))

    def test_cli_default_modes_and_repeatable_sampling(self):
        self.assertEqual(self.cli().returncode, 0)
        for mode in ("--verify", "--asp", "--show-asp", "--trace"):
            result = self.cli(mode, "--qa")
            self.assertEqual(result.returncode, 0, result.stderr)
        baseline = json.loads(self.cli("--json").stdout)
        self.assertEqual(baseline["params"], vars(story.StoryParams()))
        all_rows = json.loads(self.cli("--all", "--json").stdout)
        self.assertEqual(len(all_rows), 6)
        first = self.cli("-n", "100", "--seed", "12345", "--json", "--qa")
        second = self.cli("-n", "100", "--seed", "12345", "--json", hash_seed="2")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, second.stdout)
        rows = json.loads(first.stdout)
        self.assertEqual(len(rows), 100)
        self.assertEqual({row["params"]["need"] for row in rows}, set(story.NEEDS))
        self.assertNotEqual(first.stdout, self.cli("-n", "100", "--seed", "54321", "--json").stdout)
        for flags in (("-n", "0"), ("--need", "fasten", "--solution", "trinkets"),
                      ("--all", "--need", "softness", "--solution", "repairs")):
            result = self.cli(*flags)
            self.assertNotEqual(result.returncode, 0)
            self.assertEqual(result.stdout, "")

    def test_asp_parity_and_keyword_dataclass_calls(self):
        self.assertEqual(set(story.valid_combos()), story.asp_combos())
        tree = ast.parse(Path(story.__file__).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                if node.func.id in ("Entity", "Event", "StoryParams", "StorySample", "QAItem"):
                    self.assertFalse(node.args, f"positional dataclass at line {node.lineno}")


if __name__ == "__main__":
    unittest.main()
