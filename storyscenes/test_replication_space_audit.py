import unittest
from types import SimpleNamespace
from unittest.mock import patch

from replication_space_audit import audit_composition, audit_questions, composition_axes, favor_axes, question_axes, texts


class SpaceAuditTests(unittest.TestCase):
    def test_favor_permutation_audit_is_explicitly_not_the_full_space(self):
        from math import prod
        from dataclasses import fields
        from storyscenes.harbor_favors_story import Conditions
        axes = favor_axes()
        self.assertEqual(set(axes), {f.name for f in fields(Conditions)})
        self.assertEqual(prod(len(v) for v in axes.values()), 972)
        self.assertNotIn(("boat",) * 3, axes["projects"])
        self.assertNotIn(("ari",) * 3, axes["owners"])
        self.assertIn(("work_first",) * 3, axes["policies"])

    def test_question_grid_covers_all_declared_fields(self):
        from dataclasses import fields
        from math import prod
        from storyscenes.harbor_questions_story import Conditions
        axes = question_axes()
        self.assertEqual(set(axes), {f.name for f in fields(Conditions)})
        self.assertEqual(prod(len(v) for v in axes.values()), 512)
        for name, values in axes.items():
            self.assertIn(getattr(Conditions(), name), values)

    def test_question_audit_retains_failures(self):
        def fail(*, config):
            raise ValueError("deliberate audit failure")
        module = SimpleNamespace(__file__=__file__, Conditions=dict, generate=fail)
        with patch("replication_space_audit.harness.generator", return_value=module), \
                patch("replication_space_audit.question_axes", return_value=dict(actual=(False, True))):
            result = audit_questions()
        self.assertEqual(result["configurations"], 2)
        self.assertEqual(result["returned"], 0)
        self.assertEqual(result["serialized_replays"], 0)
        self.assertEqual(result["exact_texts"], 0)
        self.assertEqual([r["conditions"]["actual"] for r in result["failures"]], [False, True])
        self.assertTrue(all("deliberate audit failure" in r["error"] for r in result["failures"]))

    def test_composed_and_tradeoff_grids_cover_declared_condition_fields(self):
        from dataclasses import fields
        from math import prod
        from storyscenes.harbor_composition_story import Conditions
        from storyscenes.harbor_tradeoffs_story import Conditions as TradeoffConditions

        for tradeoffs, model, total in ((False, Conditions, 576), (True, TradeoffConditions, 2304)):
            axes = composition_axes(tradeoffs=tradeoffs)
            self.assertEqual(set(axes), {f.name for f in fields(model)})
            self.assertEqual(prod(len(v) for v in axes.values()), total)
            for name, values in axes.items():
                self.assertIn(getattr(model(), name), values)

    def test_failed_configurations_are_retained_not_counted_as_replayed(self):
        def fail(*, config):
            raise ValueError("deliberate audit failure")

        module = SimpleNamespace(__file__=__file__, Conditions=dict, generate=fail)
        with patch("replication_space_audit.harness.generator", return_value=module), \
                patch("replication_space_audit.composition_axes", return_value=dict(clip=(False, True))):
            result = audit_composition(tradeoffs=True)
        self.assertEqual(result["configurations"], 2)
        self.assertEqual(result["returned"], 0)
        self.assertEqual(result["serialized_replays"], 0)
        self.assertEqual(result["exact_texts"], 0)
        self.assertEqual([r["conditions"]["clip"] for r in result["failures"]], [False, True])
        self.assertTrue(all("deliberate audit failure" in r["error"] for r in result["failures"]))

    def test_exhausts_conditional_choice_tree_not_random_draws(self):
        prose = SimpleNamespace(random=None)

        def render(spec, state, config, seed):
            rng = prose.random.Random(seed)
            first = rng.choice(("a", "b"))
            second = rng.choice(("x", "y", "z")) if first == "a" else "q"
            return SimpleNamespace(story=first + second)

        prose.render = render
        self.assertEqual(texts(prose, None, None, None), {"ax", "ay", "az", "bq"})
        self.assertIsNone(prose.random)

    def test_named_renderer_is_exhausted_without_changing_world(self):
        prose = SimpleNamespace(random=None)
        sentinel = object()

        def special(spec, state, config, seed):
            self.assertIs(state, sentinel)
            return SimpleNamespace(story=prose.random.Random(seed).choice(("left", "right")))

        prose.special = special
        self.assertEqual(texts(prose, None, sentinel, None, render_name="special"), {"left", "right"})
        self.assertIsNone(prose.random)


if __name__ == "__main__":
    unittest.main()
