"""Behavioral checks for shared composition, frozen prose and the authoring pipeline."""
import asyncio
from dataclasses import replace
import json
from pathlib import Path
import tempfile
import unittest

import runtime as r
from runtime import Condition as C, Effect as E, Scene, Rule, WorldSpec
import worker
import factory


def fixture():
    entities = {k: {"name": k.title(), "kind": "child" if k in ("ada", "ben") else "prop"}
                for k in ("ada", "ben", "box", "key")}
    return WorldSpec("The borrowed key", entities,
        {"ada.memes.Curiosity": 2, "ben.memes.Care": 1,
         "box.stuck": True, "box.open": False, "box.latch": "left",
         "ada.knows.box.latch": None, "ben.knows.box.latch": None,
         "key.owner": "ben", "key.used": False},
        (r.observe("look", "ada", "box.latch", requires=(C("ada.memes.Curiosity", "gt", 0),), summary="Ada inspected the latch"),
         r.tell("explain", "ada", "ben", "box.latch", summary="Ada explained the latch"),
         r.transfer("lend", "ben", "ada", "key", requires=(C("ben.knows.box.latch", "eq", "left"), C("ben.memes.Care", "ge", 1)), summary="Ben lent Ada the key"),
         Scene("unlock", "Solve", ("ada",), (C("key.owner", "eq", "ada"), C("ada.knows.box.latch", "eq", "left")),
               (E("box.open", True), E("box.stuck", False), E("key.used", True)), "Ada opened the box")),
        (C("box.open", "eq", True),),
        (Rule("key ownership", (C("key.owner", "in", ("ada", "ben")),)),))


class RuntimeTests(unittest.TestCase):
    def test_composition_uses_shared_state_and_causal_dependencies(self):
        spec = fixture()
        result = r.solve(spec, 21)
        self.assertEqual([e["scene"] for e in result["events"]], ["look", "explain", "lend", "unlock"])
        self.assertEqual([e["causes"] for e in result["events"]], [[], [1], [2], [1, 3]])
        self.assertTrue(result["final"]["box.open"])
        self.assertFalse(spec.initial["box.open"])

    def test_removing_communication_blocks_downstream_solution(self):
        spec = fixture()
        with self.assertRaisesRegex(r.StoryError, "No valid composition"):
            r.solve(replace(spec, scenes=tuple(s for s in spec.scenes if s.id != "explain")))

    def test_meme_magnitude_gates_action(self):
        spec = fixture()
        initial = dict(spec.initial, **{"ben.memes.Care": 0})
        with self.assertRaisesRegex(r.StoryError, "No valid composition"):
            r.solve(replace(spec, initial=initial))

    def test_recombines_alternative_solution(self):
        spec = fixture()
        alternate = Scene("help_directly", "Care", ("ben",), (C("ben.knows.box.latch", "eq", "left"),),
                          (E("box.open", True), E("box.stuck", False)), "Ben lifted the latch")
        spec = replace(spec, scenes=spec.scenes + (alternate,))
        paths = {tuple(e["scene"] for e in r.solve(spec, seed)["events"]) for seed in range(30)}
        self.assertTrue(any(p[-1] == "help_directly" for p in paths))
        self.assertTrue(any(p[-1] == "unlock" for p in paths))

    def test_atomic_failure_leaves_original_intact(self):
        state = {"cup.water": 3, "jug.water": 1}
        scene = Scene("pour", "Transfer", ("cup",), (), (E("cup.water", -4, "inc"), E("jug.water", 4, "inc")), "poured")
        self.assertIsNone(r.transition(state, scene, (Rule("nonnegative", (C("cup.water", "ge", 0),)),)))
        self.assertEqual(state, {"cup.water": 3, "jug.water": 1})

    def test_copy_reads_prestate(self):
        scene = Scene("swap", "Swap", ("x",), (), (E("x.a", "x.b", "copy"), E("x.b", "x.a", "copy")), "swapped")
        self.assertEqual(r.transition({"x.a": 1, "x.b": 2}, scene), {"x.a": 2, "x.b": 1})

    def test_unembedded_scene_rejected(self):
        spec = fixture()
        bad = replace(spec.scenes[0], actors=())
        with self.assertRaisesRegex(r.StoryError, "carrier"):
            r.solve(replace(spec, scenes=(bad,) + spec.scenes[1:]))

    def test_unknown_guard_is_not_hidden_behind_false_guard(self):
        spec = fixture()
        bad = replace(spec.scenes[0], requires=(C("box.open", "eq", True), C("ghost.value", "eq", 1)))
        with self.assertRaisesRegex(r.StoryError, "Unknown condition"):
            r.solve(replace(spec, scenes=(bad,) + spec.scenes[1:]))

    def test_search_backtracks_from_valid_but_dead_end(self):
        spec = fixture()
        trap = Scene("lose_key", "Mistake", ("ben",), (C("key.owner", "eq", "ben"),),
                     (E("key.owner", "box"),), "Ben put the key away", weight=1000)
        spec = replace(spec, rules=(), scenes=(trap,) + spec.scenes)
        result = r.solve(spec, 1)
        self.assertGreater(result["search"]["backtracks"], 0)
        self.assertNotIn("lose_key", [e["scene"] for e in result["events"]])

    def test_bounded_search(self):
        with self.assertRaisesRegex(r.StoryError, "budget exhausted"):
            r.solve(fixture(), max_nodes=1)

    def test_renderer_cannot_change_world(self):
        result = r.solve(fixture())
        def render(run, rng):
            run["final"]["box.open"] = False
        with self.assertRaisesRegex(r.StoryError, "mutated"):
            r.realize(result, render)

    def test_renderer_must_cover_every_event(self):
        result = r.solve(fixture())
        def render(run, rng):
            return [dict(text="A beginning.", event_ids=[], kind="beginning"),
                    dict(text="An action.", event_ids=[1], kind="scene"),
                    dict(text="An ending.", event_ids=[4], kind="ending")]
        with self.assertRaisesRegex(r.StoryError, "Unnarrated"):
            r.realize(result, render)

    def test_prose_randomness_does_not_change_simulation(self):
        trace = r.solve(fixture())
        def render(run, rng):
            return [dict(text=f"Opening choice {rng.randrange(1000000)}.", event_ids=[], kind="beginning"),
                    dict(text="They worked together.", event_ids=[e["id"] for e in run["events"]], kind="scene"),
                    dict(text="The box stood open.", event_ids=[4], kind="ending")]
        first, second = r.realize(trace, render, 1), r.realize(trace, render, 2)
        self.assertNotEqual(first["story"], second["story"])
        self.assertEqual(first["trace"], second["trace"])

    def test_qa_references_actual_events(self):
        result = r.solve(fixture())
        qa = r.qa_from_trace(result)
        self.assertEqual(qa[-1]["cause_ids"], [1, 3])
        self.assertIn("false to true", qa[-1]["answer"])
        self.assertEqual(qa[-1]["event_ids"], [4])


class PipelineTests(unittest.TestCase):
    def test_io_source_rejected(self):
        for source in ("import os", "open('secret')", "x.__class__", "__import__('os')"):
            with self.assertRaises(r.StoryError):
                worker.check_source(source)

    def test_budget_reservation_survives_restart_and_caps_requests(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "budget.json"
            b = factory.Budget(path, .03)
            req = dict(model="gpt-5.6-luna", max_output_tokens=10000)
            b.reserve("one", req)
            b = factory.Budget(path, .03)
            with self.assertRaisesRegex(ValueError, "Budget cap"):
                b.reserve("two", req)

    def test_cached_api_response_needs_no_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            body = factory.request("plan", plan=True)
            factory.save(root / "plan.request.json", body)
            factory.save(root / "plan.response.json", {"status": "completed", "output": [{"type": "message", "content": [{"type": "output_text", "text": "cached"}]}]})
            self.assertEqual(asyncio.run(factory.api_artifact(None, None, root, "plan", body)), "cached")
            with self.assertRaisesRegex(ValueError, "differs"):
                asyncio.run(factory.api_artifact(None, None, root, "plan", factory.request("different", plan=True)))

    def test_uncertain_paid_outcome_does_not_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            body = factory.request("x")
            factory.save(root / "stage.request.json", body)
            with self.assertRaisesRegex(ValueError, "uncertain paid outcome"):
                asyncio.run(factory.api_artifact(None, None, root, "stage", body))

    def test_quality_retains_duplicates_and_checks_partition(self):
        item = factory.quality.select_set("fixture", [{"story": "Same story."}] * 20, 777)
        self.assertEqual(len(item["stories"]), 10)
        self.assertEqual(len({s["story"] for s in item["stories"]}), 1)
        ids = [s["id"] for s in item["stories"]]
        score = dict(zip(factory.quality.legacy.RATING_KEYS, [7] * 5))
        value = dict(stories=[dict(id=i, rating=score, note="A complete story.") for i in ids],
                     diversity=dict(zip(factory.quality.DIVERSITY_KEYS, [0] * 5)),
                     diversity_evidence="All stories are identical.",
                     plot_groups=[dict(story_ids=ids, summary="One plot.")])
        self.assertIn("rating", factory.quality.validate(value, item))
        value["plot_groups"][0]["story_ids"] = ids[:-1]
        with self.assertRaises(ValueError):
            factory.quality.validate(value, item)

    def test_completed_evaluation_is_reused_without_another_reservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            world = root / "world"
            world.mkdir()
            pool = [{"story": "A complete little story."}] * 10
            (world / "samples.jsonl").write_text("\n".join(json.dumps(r) for r in pool))
            factory.save(root / "summary.json", [dict(world="world", ok=True,
                generator_sha256="generator", simulation_sha256="simulation")])
            item = factory.quality.select_set("world", pool, 777)
            item.update(source_sha256="generator", simulation_sha256="simulation")
            dest = root / "quality"
            dest.mkdir()
            factory.save(dest / "inputs.json", [item])
            factory.save(dest / "summary.json", {})
            (dest / "quality.jsonl").write_text(json.dumps(dict(script="world", ok=True)) + "\n")
            self.assertTrue(asyncio.run(factory.evaluate(root, None, 1))[0]["ok"])
            pool[0]["story"] = "Changed source story."
            (world / "samples.jsonl").write_text("\n".join(json.dumps(r) for r in pool))
            with self.assertRaisesRegex(ValueError, "different"):
                asyncio.run(factory.evaluate(root, None, 1))


if __name__ == "__main__":
    unittest.main()
