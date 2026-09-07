import asyncio
import contextlib
import io
import json
import lzma
from pathlib import Path
import tempfile
import unittest
from unittest.mock import AsyncMock, Mock, patch

import canonical_examples
import compression_review
import openai_batch_world_factory as batch
import openai_service_world_factory as service
import prompt_trials as trials


SOURCE = '''#!/usr/bin/env python3
import argparse
import json
p = argparse.ArgumentParser()
p.add_argument('-n', type=int, default=1)
p.add_argument('--verify', action='store_true')
a, _ = p.parse_known_args()
if a.verify:
    print('OK')
else:
    print(json.dumps([dict(story=f'Name{i} found the lost cup and brought it home.',
                          params=dict(name=f'Name{i}'), story_qa=[])
                      for i in range(a.n)]))
'''


class PromptTrialsTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=batch.WORLDS_DIR, prefix="_test_trials_")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for attr, value in (("TRIALS", self.root / "data"), ("TARGETS", self.root / "worlds")):
            patcher = patch.object(trials, attr, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def prepare(self, *flags):
        args = trials.build_parser().parse_args(["prepare", "test", "--seed", "2026090605", *flags])
        directory = trials.prepare(args)
        return directory, trials.read(directory / "trial.json")

    def test_seven_names_available_in_existing_factories(self):
        self.assertEqual(list(canonical_examples.CANONICAL_EXAMPLES),
                         ["puddles", "pirates", "garnet", "library", "cart", "bridge", "nell"])
        self.assertEqual(canonical_examples.CANONICAL_EXAMPLES["puddles"], batch.WORLDS_DIR / "puddles.py")
        self.assertEqual(canonical_examples.CANONICAL_EXAMPLES["nell"], batch.WORLDS_DIR / "nell_and_the_dragon_v2.py")
        for name, path in canonical_examples.CANONICAL_EXAMPLES.items():
            self.assertTrue(path.is_file())
            self.assertEqual(batch.example_world_paths(name), (path,))
        self.assertEqual(len(batch.example_world_paths("all")), 2)

    def test_prepare_21_frozen_requests_matched_tasks_no_api(self):
        with patch.object(service, "make_client", side_effect=AssertionError("no API during prepare")):
            directory, config = self.prepare()
        self.assertEqual(len(config["arms"]), 7)
        self.assertEqual([arm["label"] for arm in config["arms"]], list(canonical_examples.CANONICAL_EXAMPLES))
        self.assertEqual(config["example_set"], "dialogue_v2")
        self.assertEqual(config["local_samples"], 1000)
        self.assertEqual(config["judge"], "gpt-5.6-terra")
        self.assertEqual(config["judge_stories"], 10)
        baseline = None
        for arm in config["arms"]:
            self.assertEqual(trials.read(batch.ROOT / arm["manifest"])["example_set"], "dialogue_v2")
            requests = trials.jsonl(batch.ROOT / arm["requests"])
            self.assertEqual(len(requests), 3)
            tasks = [{key: job[key] for key in ("seed", "words", "features", "setting", "style", "domain")}
                     for job in (item["job"] for item in requests)]
            baseline = baseline or tasks
            self.assertEqual(tasks, baseline)
            self.assertEqual(requests[0]["body"]["model"], "gpt-5.6-luna")
            self.assertEqual(requests[0]["body"]["reasoning"], {"effort": "none"})
            self.assertEqual(requests[0]["body"]["service_tier"], "flex")
            self.assertIn(str(canonical_examples.CANONICAL_EXAMPLES[arm["label"]].relative_to(batch.ROOT)),
                          requests[0]["body"]["input"][0]["content"][0]["text"])
            snapshot = directory / "inputs" / canonical_examples.CANONICAL_EXAMPLES[arm["label"]].relative_to(batch.ROOT)
            self.assertEqual(snapshot.read_bytes(), canonical_examples.CANONICAL_EXAMPLES[arm["label"]].read_bytes())
        with self.assertRaises(ValueError):
            self.prepare()
        self.assertTrue((directory / "inputs/storyworlds/STORY.md").exists())
        cost = trials.budget("test")
        self.assertEqual(cost["worlds"], 21)
        self.assertGreater(cost["total_usd_high"], cost["total_usd_low"])
        self.assertGreater(cost["output_caps_scenario_usd"], cost["total_usd_high"])

    def test_legacy_prepared_trial_retains_old_judge_label(self):
        directory, config = self.prepare("--examples", "puddles", "--per-example", "1")
        config["judge"] = "gpt-5.4-mini"
        config.pop("judge_protocol")
        config.pop("judge_stories")
        config.pop("example_set")
        trials.save(directory / "trial.json", config)
        self.assertEqual(trials.load_trial("test")[1]["judge"], "gpt-5.4-mini")
        self.assertIn("judge gpt-5.4-mini", trials.report(["test"]))
        self.assertIn("example set legacy/unversioned", trials.report(["test"]))

    def test_retired_references_can_prepare_explicit_custom_trial(self):
        _, config = self.prepare("--examples", *canonical_examples.RETIRED_EXAMPLES, "--per-example", "1")
        self.assertEqual(config["example_set"], "custom")
        self.assertEqual([arm["label"] for arm in config["arms"]], list(canonical_examples.RETIRED_EXAMPLES))
        for arm in config["arms"]:
            request = trials.jsonl(batch.ROOT / arm["requests"])[0]
            source = canonical_examples.RETIRED_EXAMPLES[arm["label"]]
            self.assertIn(source.read_text(), request["body"]["input"][0]["content"][0]["text"])

    def test_tampered_requests_refused(self):
        _, config = self.prepare("--examples", "puddles", "--per-example", "1")
        request = batch.ROOT / config["arms"][0]["requests"]
        request.write_text(request.read_text() + "\n")
        with self.assertRaisesRegex(ValueError, "frozen requests changed"):
            trials.load_trial("test")

    def test_compression_measures_collapse(self):
        rows = [dict(story=f"Name{i} found a cup.", params=dict(name=f"Name{i}"), story_qa=[]) for i in range(1000)]
        metrics = trials.sample_metrics(rows, 1000)
        self.assertEqual(metrics["exact_unique"], 1000)
        self.assertEqual(metrics["skeleton_unique"], 1)
        duplicates = trials.sample_metrics([rows[0]] * 1000, 1000)
        self.assertLess(duplicates["lzma_all"]["ratio"], metrics["lzma_all"]["ratio"])
        self.assertEqual(duplicates["exact_unique_fraction"], .001)
        self.assertEqual(trials.compression_metrics([])["ratio"], 0)
        self.assertEqual(trials.compression_metrics([r["story"] for r in rows]),
                         trials.compression_metrics([r["story"] for r in reversed(rows)]))

    def test_pooled_archive_is_story_text_only_and_roundtrips(self):
        rows = [dict(story="One story.", params=dict(private_marker="not story text")),
                dict(story="A different story.", params={}), dict(story="One story.", params={})]
        output = self.root / "pooled"
        result = compression_review.pooled_review(rows, output, groups=[rows[:2], rows[2:]])
        stored = lzma.decompress((output / "all_shuffled.stories.jsonl.xz").read_bytes()).decode()
        self.assertEqual(sorted(map(json.loads, stored.splitlines())), sorted(row["story"] for row in rows))
        self.assertNotIn("private_marker", stored)
        self.assertEqual(result["variants"]["exact_deduplicated"]["stories"], 2)
        self.assertEqual(result["dictionary_bytes"], 64 * 1024 * 1024)
        self.assertEqual(result["growth_curve"][-1]["stories"], 3)

    def fake_row(self, job):
        return dict(custom_id=job.custom_id, target=job.target, error=None,
                    response=dict(body=dict(status="completed", output=[dict(type="message", content=[
                        dict(type="output_text", text=SOURCE)])])))

    def test_generation_resume_and_local_pipeline(self):
        directory, config = self.prepare("--examples", "puddles", "pirates", "--per-example", "1", "--local-samples", "4")
        client = AsyncMock()
        calls = []

        async def fake_call(client, args, job, semaphore, *, request):
            calls.append(request)
            return self.fake_row(job)

        with patch.object(service, "make_client", return_value=client), patch.object(service, "call_one", side_effect=fake_call), \
             contextlib.redirect_stdout(io.StringIO()):
            asyncio.run(trials.generate(directory, config))
            asyncio.run(trials.generate(directory, config))
        self.assertEqual(len(calls), 2)
        for arm in config["arms"]:
            parent = (batch.ROOT / arm["manifest"]).parent
            self.assertEqual(len(trials.jsonl(parent / "received.jsonl")), 1)
            self.assertEqual(len(trials.jsonl(parent / "responses.jsonl")), 1)
            self.assertEqual(len(list((parent / "raw").glob("*.py"))), 1)
        with patch.object(trials.set_quality, "run_sets", side_effect=AssertionError("no judge requested")), \
             contextlib.redirect_stdout(io.StringIO()):
            output = asyncio.run(trials.evaluate(directory, config, skip_quality=True))
        checks = trials.read(output / "checks.json")
        self.assertEqual(len(checks), 2)
        self.assertTrue(all(row["final"]["ok"] and row["verify"]["ok"] for row in checks))
        self.assertTrue(all(row["hash_seed_replay_equal"] for row in checks))
        self.assertEqual([row["exact_unique"] for row in checks], [4, 4])
        self.assertTrue(all(row["geometric_score"] is None for row in checks))
        self.assertIsNone(trials.read(output / "dataset_scores.json")["ALL"]["score"])
        report = trials.report(["test"])
        self.assertIn("LZMA", report)
        self.assertIn("| ALL | 2 |", report)

        async def fake_ratings(inputs, path, *, concurrency):
            path.mkdir()
            for item in inputs:
                self.assertEqual(len(item["stories"]), 4)
                trials.append(path / "quality.jsonl", dict(ok=True, script=item["script"],
                    rating={key: 7.5 for key in trials.quality.RATING_KEYS}, judged_stories=4,
                    story_ratings=[dict(rating={key: score for key in trials.quality.RATING_KEYS}) for score in (7, 8, 7, 8)],
                    diversity={key: 2 for key in trials.set_quality.DIVERSITY_KEYS}, plot_groups=[{}]))

        with patch.object(trials.set_quality, "run_sets", side_effect=fake_ratings), \
             contextlib.redirect_stdout(io.StringIO()):
            rated_output = asyncio.run(trials.evaluate(directory, config, skip_quality=False))
        scores = trials.read(rated_output / "dataset_scores.json")
        self.assertEqual(scores["ALL"]["usable_samples"], 4)
        self.assertEqual(scores["ALL"]["yield_fraction"], .5)
        self.assertEqual(scores["ALL"]["score"], scores["puddles"]["score"] / 2)
        self.assertIn("quality_diversity_geometric_v1", trials.report(["test"]))
        self.assertIn("Semantic diversity", trials.report(["test"]))
        self.assertEqual(trials.read(rated_output / "summary.json")["mean_quality"]["overall"], 7.5)
        self.assertEqual(trials.read(rated_output / "settings.json")["judge"], "gpt-5.6-terra")

    def test_interrupted_attempt_not_rebilled_and_received_recovered(self):
        directory, config = self.prepare("--examples", "puddles", "--per-example", "2")
        arm = config["arms"][0]
        parent = (batch.ROOT / arm["manifest"]).parent
        jobs = [batch.StoryworldJob(**item["job"]) for item in trials.jsonl(batch.ROOT / arm["requests"])]
        for job in jobs:
            trials.append(parent / "attempts.jsonl", dict(custom_id=job.custom_id))
        trials.append(parent / "received.jsonl", self.fake_row(jobs[1]))
        with patch.object(service, "make_client", side_effect=AssertionError("must not retry")):
            asyncio.run(trials.generate(directory, config))
        rows = trials.jsonl(parent / "responses.jsonl")
        self.assertIn("outcome unknown", rows[0]["error"])
        self.assertTrue(rows[1]["materialized"])

    def test_missing_world_is_zero_not_a_silently_dropped_case(self):
        directory, config = self.prepare("--examples", "puddles", "--per-example", "1", "--local-samples", "4")
        arm = config["arms"][0]
        parent = (batch.ROOT / arm["manifest"]).parent
        job = trials.jsonl(batch.ROOT / arm["requests"])[0]["job"]
        trials.append(parent / "attempts.jsonl", dict(custom_id=job["custom_id"]))
        with patch.object(service, "make_client", side_effect=AssertionError("must not retry")):
            asyncio.run(trials.generate(directory, config))
        with patch.object(trials.set_quality, "run_sets", side_effect=AssertionError("no stories to judge")), \
             contextlib.redirect_stdout(io.StringIO()):
            output = asyncio.run(trials.evaluate(directory, config, skip_quality=False))
        row = trials.read(output / "checks.json")[0]
        self.assertFalse(row["raw_runnable"])
        self.assertEqual(row["geometric_score"], 0)
        self.assertEqual(trials.evaluation_exit_code(output, skip_quality=False), 1)

    def test_call_one_sends_frozen_body(self):
        client = Mock()
        client.with_options.return_value = client
        client.responses.create = AsyncMock(return_value={"status": "completed"})
        job = batch.StoryworldJob(custom_id="test", target="x.py", name="x", seed=1, words=[], setting="", features=[], style="", domain="")
        request = dict(model="frozen", input=[])
        with patch.object(service, "request_body", side_effect=AssertionError("must use snapshot")):
            asyncio.run(service.call_one(client, Mock(), job, asyncio.Semaphore(1), request=request))
        client.responses.create.assert_awaited_once_with(**request)

    def test_process_lock(self):
        directory, _ = self.prepare("--examples", "puddles", "--per-example", "1")
        with trials.trial_lock(directory):
            with self.assertRaisesRegex(ValueError, "another process"), trials.trial_lock(directory):
                self.fail("second lock should fail")


if __name__ == "__main__":
    unittest.main()
