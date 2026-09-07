"""Dialogue must exchange information and lead to completed physical actions."""

import ast
import copy
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import unittest

from worlds import library_words_dialogue as library
from worlds import one_cart_dialogue as cart
from worlds import bridge_builders_dialogue as bridge


MODULES = (library, cart, bridge)


class DialogueWorldTests(unittest.TestCase):
    def params(self, module, **changes):
        problem, solution = module.valid_combos()[0]
        fields = dict(problem=problem, solution=solution, item=next(iter(module.ITEMS)))
        fields.update(changes)
        return module.StoryParams(**fields)

    def cli(self, module, *flags, hash_seed="1"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed)
        env.pop("PYTHONPATH", None)
        return subprocess.run([sys.executable, str(Path(module.__file__).resolve()), *flags],
                              env=env, text=True, capture_output=True, timeout=30)

    def test_all_states_have_dialogue_grounded_qa_and_endings(self):
        for module in MODULES:
            signatures = set()
            for problem, solution in module.valid_combos():
                for approach in module.APPROACHES:
                    for item in module.ITEMS:
                        with self.subTest(world=module.__name__, problem=problem, approach=approach, item=item):
                            sample = module.generate(self.params(module, problem=problem, solution=solution,
                                                                 approach=approach, item=item))
                            module.check_sample(sample)
                            signatures.add(tuple((event.kind, event.speaker, event.revealed) for event in sample.world.history))
                            utterances = re.findall(r'"([^"]+)"', sample.story)
                            fraction = sum(len(text.split()) for text in utterances) / len(sample.story.split())
                            self.assertGreaterEqual(len(utterances), 14)
                            self.assertGreater(fraction, .45)
                            self.assertLess(len(sample.story.split()), 450)
                            self.assertEqual(sample.world.history[0].kind, "beginning")
                            self.assertEqual(sample.world.history[-1].kind, "ending")
                            self.assertNotRegex(sample.story, r'\." [A-Z][a-z]+ (said|asked|whispered|blurted)\.')
                            self.assertNotIn("no The ", sample.story)
                            self.assertNotIn("{", sample.story)
                            self.assertEqual(len({pair.question for pair in sample.story_qa}), len(sample.story_qa))
                            for pair in sample.story_qa:
                                self.assertIn(pair.answer, [f"{e.cause} {e.result}" for e in sample.world.history if e.question])
                                self.assertGreaterEqual(len(re.findall(r'[.!?](?:\s|$)', pair.answer)), 2)
            self.assertEqual(len(signatures), 6)

    def test_source_uses_only_keyword_dataclasses(self):
        for module in MODULES:
            tree = ast.parse(Path(module.__file__).read_text())
            names = {node.name for node in tree.body if isinstance(node, ast.ClassDef)
                     and any(isinstance(d, ast.Name) and d.id == "dataclass" for d in node.decorator_list)}
            names.update(("QAItem", "StorySample"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in names:
                    self.assertFalse(node.args, f"{module.__name__}:{node.lineno}")

    def test_unknown_fact_cannot_be_told_or_learned(self):
        for module in MODULES:
            world = module.build_world(self.params(module))
            before = copy.deepcopy(world.snapshot())
            with self.assertRaises(module.StoryError):
                world.say("hero", "I know the answer.", to="friend", reveal="unknown")
            self.assertEqual(world.snapshot(), before)

    def test_learning_is_recorded_at_the_speaking_turn(self):
        world = library.build_world(self.params(library))
        self.assertNotIn("picture", world.entities["friend"].beliefs)
        with self.assertRaises(library.StoryError):
            library.recover_page(world)
        world.say("hero", "I remember a silver sail.", to="friend", reveal="picture")
        self.assertEqual(world.history[-1].state["friend"]["beliefs"]["picture"], "a silver sail")
        library.recover_page(world)
        self.assertEqual(world.entities["book"].meters["bookmark_page"], 12)

    def test_library_cannot_claim_unperformed_fixes(self):
        for problem, solution in library.valid_combos():
            world = library.build_world(self.params(library, problem=problem, solution=solution))
            with self.assertRaises(library.StoryError):
                library.check_ending(world)
        world = library.build_world(self.params(library, problem="quiet", solution="whisper"))
        with self.assertRaises(library.StoryError):
            library.read_softly(world)

    def test_hearing_a_proposal_is_not_accepting_it(self):
        world = cart.build_world(self.params(cart))
        world.entities["hero"].beliefs["proposal"] = "turns"
        with self.assertRaises(cart.StoryError):
            cart.accept_plan(world)
        world.say("hero", "Let's take turns.", to="friend", reveal="proposal")
        with self.assertRaises(cart.StoryError):
            cart.move_load(world, "plants", 1, "shady_bench")
        cart.accept_plan(world)
        cart.move_load(world, "plants", 1, "shady_bench")
        self.assertEqual(world.entities["plants"].location, "shady_bench")
        with self.assertRaises(cart.StoryError):
            cart.check_ending(world)

    def test_cart_limits_and_cargo_accounting(self):
        for problem, solution in (("heavy", "split"), ("gate", "carry")):
            world = cart.build_world(self.params(cart, problem=problem, solution=solution))
            for who in ("hero", "friend"):
                world.entities[who].beliefs["proposal"] = solution
            cart.accept_plan(world)
            with self.assertRaises(cart.StoryError):
                cart.move_load(world, "blocks", 4 if problem == "heavy" else 1, "play_mat")
            if problem == "heavy":
                cart.move_load(world, "blocks", 2, "play_mat")
                self.assertNotEqual(world.entities["blocks"].location, "play_mat")
                cart.move_load(world, "blocks", 2, "play_mat")
                with self.assertRaises(cart.StoryError):
                    cart.move_load(world, "blocks", 1, "play_mat")

    def test_bridge_requires_evidence_and_a_real_test(self):
        for problem, solution in bridge.valid_combos():
            world = bridge.build_world(self.params(bridge, problem=problem, solution=solution))
            self.assertEqual(bridge.cross(world), problem)
            self.assertEqual(world.entities["parcel"].meters["delivered"], 0)
            with self.assertRaises(bridge.StoryError):
                bridge.revise(world)
            world.entities["friend"].beliefs["obstacle"] = bridge.obstacle(world)
            world.say("friend", "Look at the bridge.", to="hero", reveal="obstacle")
            bridge.revise(world)
            self.assertEqual(world.entities["parcel"].meters["delivered"], 0)
            self.assertEqual(bridge.cross(world), "")
            self.assertEqual(world.entities["parcel"].location, "station")

    def test_invalid_direct_parameters(self):
        for module in MODULES:
            wrong_solution = next(s for s in module.SOLUTIONS if s != module.valid_combos()[0][1])
            for changes in (dict(solution=wrong_solution), dict(hero="Ben"), dict(hero='not a name'),
                            dict(approach="unknown"), dict(item="missing")):
                with self.subTest(world=module.__name__, changes=changes), self.assertRaises(module.StoryError):
                    module.generate(self.params(module, **changes))

    def test_cli_json_default_and_hash_seed_replay(self):
        for module in MODULES:
            self.assertEqual(self.cli(module).returncode, 0)
            first = self.cli(module, "-n", "100", "--seed", "20260907", "--json", "--qa")
            second = self.cli(module, "-n", "100", "--seed", "20260907", "--json", "--qa", hash_seed="2")
            self.assertEqual(first.returncode, 0, first.stderr)
            self.assertEqual(first.stdout, second.stdout)
            rows = json.loads(first.stdout)
            self.assertEqual(len(rows), 100)
            self.assertEqual(len({row["params"]["problem"] for row in rows}), 3)
            self.assertTrue(all(row["params"]["hero"] != row["params"]["friend"] for row in rows))

    def test_cli_asp_all_verify_trace_and_invalid_options(self):
        for module in MODULES:
            self.assertEqual(set(module.valid_combos()), module.asp_combos())
            for flags in (("--verify",), ("--asp",), ("--show-asp",), ("--trace", "--qa")):
                result = self.cli(module, *flags)
                self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(len(json.loads(self.cli(module, "--all", "--json").stdout)), 6)
            wrong = next(s for s in module.SOLUTIONS if s != module.valid_combos()[0][1])
            for flags in (("-n", "0"), ("--hero", "Mia", "--friend", "Mia"),
                          ("--problem", module.valid_combos()[0][0], "--solution", wrong),
                          ("--all", "--problem", module.valid_combos()[0][0], "--solution", wrong)):
                result = self.cli(module, *flags)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
