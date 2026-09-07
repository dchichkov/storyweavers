"""World changes must change consequences; prose changes must not."""

import ast
import copy
from dataclasses import asdict, replace
import itertools
import json
import os
from pathlib import Path
import statistics
import subprocess
import sys
import unittest

from worlds import nell_and_the_dragon_v2 as story


class NellV2Tests(unittest.TestCase):
    def step_until(self, kind, **params):
        world = story.build_world(story.StoryParams(**params))
        for _ in range(story.MAX_ACTIONS):
            action = story.choose_action(world)
            if action.kind == kind:
                return world, action
            story.execute(world, action)
        self.fail(f"Never reached {kind}")

    def cli(self, *flags, hash_seed="1"):
        env = dict(os.environ, PYTHONHASHSEED=hash_seed)
        env.pop("PYTHONPATH", None)
        return subprocess.run([sys.executable, str(Path(story.__file__).resolve()), *flags],
                              env=env, capture_output=True, text=True, timeout=60)

    def test_complete_world_matrix_and_event_causality(self):
        outcomes = set()
        for use, owner, supplies, temper, slots, seed in itertools.product(
                story.USES, story.OWNERS, story.SUPPLIES, story.TEMPERS, (1, 2), (7, 42, 777)):
            params = story.StoryParams(use=use, owner=owner, supplies=supplies,
                                       temper=temper, nest_slots=slots, world_seed=seed)
            with self.subTest(params=params):
                sample = story.generate(params)
                w = sample.world
                story.validate_world(w)
                outcomes.add(w.outcome)
                self.assertLessEqual(len(w.history), story.MAX_ACTIONS + 1)
                self.assertEqual(w.history[-1].kind, "close")
                self.assertGreaterEqual(len(sample.story_qa), 4)
                self.assertNotIn("{", sample.story)
                self.assertEqual(len({q.question for q in sample.story_qa}), len(sample.story_qa))
                self.assertEqual(w.entities["jewel"].owner, owner)
                self.assertFalse(any(parent >= e.id for e in w.history for parent in e.causes))
        self.assertEqual(outcomes, {"exchange", "requested_return", "cooperative_repair", "gift_honored"})

    def test_same_trace_all_rendering_controls(self):
        for use, owner in story.valid_combos():
            p = story.StoryParams(use=use, owner=owner, supplies="raw", nest_slots=2, world_seed=7)
            world = story.simulate(p)
            before = story.trace_signature(world)
            original_qa = story.Teller(world.history, p).run().qa
            tellings = set()
            for voice, dialogue, detail, budget in itertools.product(story.VOICES, story.DIALOGUE_LEVELS, story.DETAIL_LEVELS, (0, 2)):
                options = replace(p, voice=voice, dialogue_level=dialogue, detail_level=detail, flourish_budget=budget, prose_seed=123)
                rendered = story.Teller(world.history, options).run()
                self.assertEqual(rendered.qa, original_qa)
                self.assertEqual(story.trace_signature(world), before)
                self.assertEqual(story.trace_signature(story.simulate(options)), before)
                self.assertEqual(set(rendered.evidence), set(world.fact_events))
                self.assertLessEqual(rendered.flourishes, budget)
                if detail == "compact":
                    self.assertEqual(rendered.flourishes, 0)
                tellings.add(rendered.story)
            self.assertGreater(len(tellings), 12)

    def test_synonyms_and_flourishes_are_seeded_not_world_mutations(self):
        p = story.StoryParams(world_seed=777)
        world = story.simulate(p)
        trace = copy.deepcopy(world.history)
        texts = {story.Teller(world.history, replace(p, prose_seed=seed)).run().story for seed in range(30)}
        self.assertEqual(len(texts), 30)
        self.assertEqual(world.history, trace)
        plain = replace(p, prose_seed=12, voice="plain", flourish_budget=0)
        self.assertEqual(story.generate(plain).to_dict(), story.generate(plain).to_dict())

    def test_offering_does_not_assign_nells_action_to_the_bird(self):
        p = story.StoryParams(dialogue_level="spare", flourish_budget=0)
        for seed in range(50):
            text = story.generate(replace(p, prose_seed=seed)).story
            self.assertNotIn("\n\nShe set the tin dish", text)

    def test_style_controls_have_observable_effects(self):
        p = story.StoryParams(use="support", supplies="raw", nest_slots=2)
        world = story.simulate(p)
        counts = {}
        for level in story.DIALOGUE_LEVELS:
            counts[level] = statistics.mean(story.Teller(world.history, replace(p, prose_seed=seed, dialogue_level=level)).run().dialogue_turns for seed in range(10))
        self.assertLess(counts["spare"], counts["balanced"])
        self.assertLess(counts["balanced"], counts["conversational"])
        compact = statistics.mean(len(story.Teller(world.history, replace(p, prose_seed=i, detail_level="compact")).run().story.split()) for i in range(10))
        rich = statistics.mean(len(story.Teller(world.history, replace(p, prose_seed=i, detail_level="rich")).run().story.split()) for i in range(10))
        self.assertLess(compact, rich)

    def test_partial_knowledge_and_observation_from_relations(self):
        w = story.build_world(story.StoryParams(use="display", owner="bird"))
        self.assertNotIn("origin", w.entities["nell"].beliefs)
        self.assertNotIn("use", w.entities["nell"].beliefs)
        before = w.snapshot()
        with self.assertRaises(story.StoryError):
            story.execute(w, story.Action(kind="honor_gift", actor="nell"))
        self.assertEqual(before, w.snapshot())
        # A hidden belief cannot alter what Nell sees on the physical level.
        w.entities["bird"].beliefs["use"] = "support"
        self.assertTrue(story.supported(w))
        story.execute(w, story.Action(kind="observe", actor="nell"))
        self.assertEqual(w.entities["nell"].beliefs["use"], "display")
        story.execute(w, story.Action(kind="ask_history", actor="nell"))
        self.assertEqual(story.choose_action(w).kind, "honor_gift")

    def test_counterfactuals_change_plan_and_outcome(self):
        base = story.StoryParams(world_seed=777)
        one = story.simulate(base)
        two = story.simulate(replace(base, nest_slots=2))
        self.assertNotEqual(one.outcome, two.outcome)
        self.assertIn("keep_both", [e.kind for e in two.history])
        self.assertIn("request_return", [e.kind for e in two.history])
        gift = story.simulate(replace(base, owner="bird"))
        self.assertEqual(gift.outcome, "gift_honored")
        self.assertFalse(any(e.kind in ("offer", "catch", "collect") for e in gift.history))
        repair = story.simulate(replace(base, use="support"))
        self.assertIn("steady", [e.kind for e in repair.history])
        self.assertIn("withdraw_support", [e.kind for e in repair.history])
        self.assertNotIn("catch", [e.kind for e in repair.history])

    def test_material_fetch_and_crafting_are_real(self):
        p = story.StoryParams(use="support", supplies="home")
        world = story.simulate(p)
        self.assertIn("fetch", [e.kind for e in world.history])
        raw = story.simulate(replace(p, supplies="raw"))
        self.assertIn("assemble", [e.kind for e in raw.history])
        self.assertEqual(raw.entities["cord"].location, "brace")
        self.assertEqual(raw.entities["stick"].location, "brace")
        w, action = self.step_until("prepare_material", use="support", supplies="raw")
        w.entities["cord"].meters["length"] = 0
        with self.assertRaises(story.StoryError):
            story.execute(w, action)
        button = story.simulate(story.StoryParams(supplies="raw"))
        self.assertIn("polish", [e.kind for e in button.history])

    def test_known_failures_not_repeated(self):
        world = story.simulate(story.StoryParams())
        self.assertEqual(sum(e.kind == "ruby_refused" for e in world.history), 1)
        careful = story.simulate(story.StoryParams(temper="careful"))
        self.assertNotIn("ruby_refused", [e.kind for e in careful.history])

    def test_no_early_refund_and_no_unagreed_return(self):
        w, take = self.step_until("take", nest_slots=2)
        story.execute(w, take)
        self.assertEqual(w.entities["jewel"].location, "nest")
        with self.assertRaises(story.StoryError):
            story.execute(w, story.Action(kind="collect", actor="dragon"))
        story.execute(w, story.choose_action(w))
        story.execute(w, story.choose_action(w))
        self.assertIn("kept_both", w.fact_events)
        self.assertEqual(w.entities["jewel"].location, "nest")
        with self.assertRaises(story.StoryError):
            story.execute(w, story.Action(kind="release", actor="bird"))
        story.execute(w, story.choose_action(w))
        story.execute(w, story.choose_action(w))
        self.assertEqual(w.entities["jewel"].location, "dish")

    def test_nest_support_is_not_just_a_flag(self):
        w = story.build_world(story.StoryParams(use="support"))
        w.entities["bird"].beliefs["use"] = "display"
        self.assertFalse(story.supported(w, without=("jewel",)))
        w, release = self.step_until("release", use="support", supplies="raw")
        w.relations.remove(("brace", "supports", "nest"))
        w.relations.remove(("dragon", "supports", "nest"))
        before = w.snapshot()
        with self.assertRaises(story.StoryError):
            story.execute(w, release)
        self.assertEqual(w.snapshot(), before)
        w, release = self.step_until("release", use="support")
        w.entities["brace"].meters["strength"] = 1
        before = w.snapshot()
        with self.assertRaises(story.StoryError):
            story.execute(w, release)
        self.assertEqual(w.snapshot(), before)
        w, withdraw = self.step_until("withdraw_support", use="support")
        w.entities["brace"].meters["strength"] = 1
        with self.assertRaises(story.StoryError):
            story.execute(w, withdraw)
        self.assertIn(("dragon", "supports", "nest"), w.relations)

    def test_safety_and_wrong_actor_guards(self):
        for key, value in (("distance", 0), ("teeth", 1), ("volume", 1)):
            w, take = self.step_until("take")
            w.entities["dragon"].meters[key] = value
            with self.assertRaises(story.StoryError):
                story.execute(w, take)
            self.assertEqual(w.entities["button"].location, "dish")
        w = story.build_world(story.StoryParams())
        with self.assertRaises(story.StoryError):
            story.execute(w, story.Action(kind="ask_history", actor="bird"))

    def test_invalid_controls_fail_closed(self):
        for fields in (dict(use="missing"), dict(owner="missing"), dict(prose_seed="x"),
                       dict(nest_slots=0), dict(flourish_budget=-1), dict(voice="missing"),
                       dict(dialogue_level="missing"), dict(detail_level="missing"), dict(hero="???")):
            with self.subTest(fields=fields), self.assertRaises(story.StoryError):
                story.generate(story.StoryParams(**fields))

    def test_cli_modes_and_hash_seed_independence(self):
        for flags in ((), ("--verify",), ("--asp",), ("--show-asp",), ("--trace", "--qa")):
            result = self.cli(*flags)
            self.assertEqual(result.returncode, 0, result.stderr)
        first = self.cli("-n", "100", "--seed", "42", "--json", "--qa")
        other = self.cli("-n", "100", "--world-seed", "42", "--json", hash_seed="8")
        self.assertEqual(first.returncode, 0, first.stderr)
        self.assertEqual(first.stdout, other.stdout)
        self.assertEqual(len(json.loads(first.stdout)), 100)
        self.assertEqual(len(json.loads(self.cli("--all", "--json").stdout)), 8)
        one = json.loads(self.cli("--world-seed", "777", "--prose-seed", "1", "--json").stdout)
        two = json.loads(self.cli("--world-seed", "777", "--prose-seed", "2", "--json").stdout)
        self.assertNotEqual(one["story"], two["story"])
        self.assertEqual(one["story_qa"], two["story_qa"])

    def test_keyword_dataclasses_and_old_reference_unchanged(self):
        tree = ast.parse(Path(story.__file__).read_text())
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ("Entity", "Event", "Action", "StoryParams", "Rendering", "QAItem", "StorySample"):
                self.assertFalse(node.args, node.lineno)
        import hashlib
        original = Path(story.__file__).with_name("nell_and_the_dragon.py")
        self.assertEqual(hashlib.sha256(original.read_bytes()).hexdigest(),
                         "2f441355e020e17f183f90d3804f8c836b3eb0500880ef81bf41d83cf31c162a")


if __name__ == "__main__":
    unittest.main()
