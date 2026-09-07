"""Regression checks for the generation example's causal and CLI contract."""

from __future__ import annotations

import ast
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest

from worlds import puddles as p


class PuddlesTests(unittest.TestCase):
    def sample(self, **changes):
        fields = dict(place="park", activity="puddles", prize="socks", name="Robin",
                      gender="girl", parent="mother", trait="curious")
        fields.update(changes)
        return p.generate(p.StoryParams(**fields))

    def test_eight_paths_with_identical_characters_and_setting(self):
        signatures, stories = set(), set()
        for problem, solutions in p.SOLUTIONS.items():
            for solution in solutions:
                sample = self.sample(problem=problem, solution=solution)
                p.check_sample(sample)
                signatures.add(tuple(e.kind for e in sample.world.history))
                stories.add(sample.story)
        self.assertEqual(len(signatures), 8)
        self.assertEqual(len(stories), 8)

    def test_prediction_leaves_real_world_unchanged(self):
        world = self.sample().world
        original = copy.deepcopy((world.entities, world.turn, world.zone,
                                  world.fired, world.history, world.paragraphs))
        prediction = p.predict_mess(world, world.facts["hero"],
                                    world.facts["activity"], "prize")
        self.assertFalse(prediction["soiled"])
        self.assertEqual(original, (world.entities, world.turn, world.zone,
                                    world.fired, world.history, world.paragraphs))

    def test_cleaned_prize_can_get_dirty_again(self):
        world = self.sample(problem="splash", solution="clean").world
        hero, prize, parent = (world.facts[k] for k in ("hero", "prize", "parent"))
        self.assertEqual(prize.meters["dirty"], 0)
        self.assertEqual(parent.meters["workload"], 0)
        for item in world.worn_items(hero):
            if item.id != prize.id:
                item.worn_by = None
        p._do_activity(world, hero, world.facts["activity"], narrate=False)
        self.assertEqual(prize.meters["dirty"], 1)
        self.assertEqual(parent.meters["workload"], 1)
        p.propagate(world, narrate=False)
        self.assertEqual(prize.meters["dirty"], 1)
        self.assertEqual(parent.meters["workload"], 1)

    def test_cover_must_block_the_actual_mess(self):
        world = self.sample(place="playroom", activity="paint", prize="shirt").world
        hero = world.facts["hero"]
        for item in world.worn_items(hero):
            if item.protective:
                item.guards = {"wet"}
        p._do_activity(world, hero, world.facts["activity"], narrate=False)
        self.assertGreater(world.facts["prize"].meters["painted"], 0)

    def test_changing_does_not_wash_or_waterproof_clothes(self):
        world = self.sample(problem="splash", solution="change").world
        prize = world.facts["prize"]
        self.assertIsNone(prize.worn_by)
        self.assertEqual(prize.meters["stored"], 1)
        self.assertGreater(prize.meters["dirty"], 0)
        self.assertGreater(world.get("spares").meters["dirty"], 0)
        self.assertFalse(world.get("spares").protective)

    def test_drawing_does_not_execute_the_messy_activity(self):
        sample = self.sample(problem="missing_gear", solution="dry_game")
        self.assertEqual(sample.world.turn, 0)
        self.assertEqual(sample.world.get("picture").meters["finished"], 1)
        self.assertFalse(sample.world.facts["played"])
        self.assertNotIn("finally enjoyed", sample.story)
        self.assertIn("draw", [e.kind for e in sample.world.history])

    def test_questions_do_not_repeat_the_answer_in_the_question(self):
        for problem, solutions in p.SOLUTIONS.items():
            for solution in solutions:
                sample = self.sample(problem=problem, solution=solution)
                for qa in sample.story_qa:
                    self.assertLessEqual(len(qa.question.split()), 14)
                    self.assertNotIn("Robin", qa.question)
                    self.assertNotIn("torso", qa.answer)
                    self.assertIn(qa.answer, [f"{e.cause} {e.result}" for e in sample.world.history])

    def test_invalid_direct_parameters_raise_story_error(self):
        for changes in (dict(activity="paint"), dict(problem="missing_gear", solution="clean"),
                        dict(name="kit"), dict(prize="jacket")):
            with self.subTest(changes=changes), self.assertRaises(p.StoryError):
                self.sample(**changes)

    def test_cli_replay_across_hash_seeds(self):
        command = [sys.executable, str(Path(p.__file__).resolve()),
                   "-n", "100", "--seed", "20260904", "--qa", "--json"]
        first = subprocess.check_output(command, env={**os.environ, "PYTHONHASHSEED": "1"})
        second = subprocess.check_output(command, env={**os.environ, "PYTHONHASHSEED": "2"})
        self.assertEqual(first, second)
        rows = json.loads(first)
        self.assertEqual(len(rows), 100)
        self.assertEqual(len({r["story"] for r in rows}), 100)
        self.assertEqual(len({(r["params"]["problem"], r["params"]["solution"]) for r in rows}), 8)

    def test_invalid_cli_exits_unsuccessfully(self):
        command = [sys.executable, str(Path(p.__file__).resolve()), "--json",
                   "--problem", "missing_gear", "--solution", "clean"]
        result = subprocess.run(command, capture_output=True, text=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(result.stdout, "")

    def test_example_uses_keyword_dataclass_construction(self):
        tree = ast.parse(Path(p.__file__).read_text())
        dataclasses = {n.name for n in tree.body if isinstance(n, ast.ClassDef)
                       and any(isinstance(d, ast.Name) and d.id == "dataclass" for d in n.decorator_list)}
        dataclasses.update({"QAItem", "StorySample"})
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in dataclasses:
                self.assertFalse(node.args, f"Positional {node.func.id} at line {node.lineno}")


if __name__ == "__main__":
    unittest.main()
