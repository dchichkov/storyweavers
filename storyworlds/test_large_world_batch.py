import asyncio
import contextlib
import io
import random
import unittest
from unittest.mock import AsyncMock, patch

import dataset_score
import large_world_batch as large
import prompt_trials as trials
import test_prompt_trials as base_tests


class LargeBatchTest(unittest.TestCase):
    setUp = base_tests.PromptTrialsTest.setUp
    prepare = base_tests.PromptTrialsTest.prepare
    fake_row = base_tests.PromptTrialsTest.fake_row

    def test_reference_catalog_is_unique_and_keeps_current_canonical(self):
        entries = large.references()
        self.assertEqual(len(entries), 106)
        self.assertEqual(len({entry["source"] for entry in entries}), 106)
        self.assertEqual(sum("repaired" in entry["kind"] for entry in entries), 100)
        labels = {entry["label"] for entry in entries}
        self.assertTrue(set(large.canonical_examples.CANONICAL_EXAMPLES) <= labels)

    def test_custom_manifest_disjoint_balanced_tasks(self):
        manifest = self.root / "examples.json"
        entries = [dict(label=label, source=trials.relative(path))
                   for label, path in list(large.canonical_examples.CANONICAL_EXAMPLES.items())[:2]]
        trials.save(manifest, entries)
        _, config = self.prepare("--example-manifest", str(manifest), "--unique-tasks", "--total", "5")
        requests = [trials.jsonl(large.ROOT / arm["requests"]) for arm in config["arms"]]
        self.assertEqual(list(map(len, requests)), [3, 2])
        self.assertEqual([r["job"]["seed"] for group in requests for r in group], list(range(2026090605, 2026090610)))
        for group, entry in zip(requests, entries):
            self.assertIn((large.ROOT / entry["source"]).read_text(), group[0]["body"]["input"][0]["content"][0]["text"])

    def test_compact_compressed_audit_resume(self):
        directory, config = self.prepare("--examples", "puddles", "--per-example", "1", "--local-samples", "4",
                                         "--model", "gpt-5.4-mini")
        config.update(compact_checks=True, compress_samples=True, local_workers=1)

        async def fake_call(client, args, job, semaphore, *, request):
            return self.fake_row(job)

        with patch.object(trials.service, "make_client", return_value=AsyncMock()), \
                patch.object(trials.service, "call_one", side_effect=fake_call), contextlib.redirect_stdout(io.StringIO()):
            asyncio.run(trials.generate(directory, config))
            large.audit(directory, config, streaming=True)
        tasks = large.tasks_for(directory, config)
        check = trials.read(directory / "qc/checks.json")[0]
        self.assertNotIn("stdout", check["final"])
        self.assertGreater(check["final"]["stdout_bytes"], 0)
        self.assertEqual(len(trials.jsonl(large.sample_path(tasks[0]))), 4)
        self.assertFalse((tasks[0][2] / "samples.jsonl").exists())
        with patch.object(trials, "audit_one", side_effect=AssertionError("must reuse completed audit")):
            self.assertEqual(large.audit_cached(tasks[0]), check)
        self.assertEqual(len(list(large.SampleGroups(tasks))), 1)
        self.assertEqual(len(trials.read(directory / "qc/judge_inputs.json")), 1)
        ratings_dir = directory / "qc/set_judge"
        ratings_dir.mkdir()
        rating = {key: 7 for key in trials.quality.RATING_KEYS}
        trials.append(ratings_dir / "quality.jsonl", dict(script=check["script"], ok=True,
            rating=rating, story_ratings=[dict(rating=rating)] * 4, judged_stories=4,
            diversity={key: 2 for key in trials.set_quality.DIVERSITY_KEYS}, plot_groups=[]))
        config["name"] = self.root.name
        report = large.ROOT / "storyworlds/batches" / f"{config['name']}.report.md"
        self.addCleanup(report.unlink, missing_ok=True)
        with contextlib.redirect_stdout(io.StringIO()):
            large.summarize(directory, config)
            large.summarize(directory, config)
        self.assertEqual(len(trials.jsonl(directory / "qc/worlds.jsonl")), 1)
        self.assertEqual(trials.read(directory / "qc/global_score.json")["usable_samples"], 4)
        self.assertEqual(trials.read(directory / "qc/lengths.json")["samples"], 4)
        self.assertEqual((directory / "report.md").read_bytes(), report.read_bytes())
        self.assertIn("Sample command + verify", report.read_text())
        self.assertIn("gpt-5.4-mini/Flex requests", report.read_text())
        self.assertIn("matched tasks across references", report.read_text())

    def test_streaming_compression_preserves_original_score(self):
        stories = ["One small story. " * 10, "Two different words. " * 12, "One small story. " * 10]
        ordered = sorted(stories)
        random.Random(0).shuffle(ordered)
        expected = dataset_score.compressed_size(b"".join(map(dataset_score.encode_story, ordered)),
                                                  dataset_score.DICTIONARY_BYTES)
        result = dataset_score.compression_retention(stories)
        self.assertEqual(result["pooled_bytes"], expected)
        import compression_review
        _, expected_metrics = compression_review.pack(stories, shuffle=True)
        actual = large.pack_stream(stories, self.root / "stories.xz")
        self.assertEqual(actual, expected_metrics)

    def test_judge_resume_does_not_retry_unknown_billed_attempt(self):
        root = self.root / "judge"
        path = root / "pass_001"
        path.mkdir(parents=True)
        inputs = [dict(script="started"), dict(script="waiting")]
        trials.save(path / "inputs.json", inputs)
        trials.append(path / "attempts.jsonl", dict(script="started"))
        rows = large.recover_judgements(root, inputs)
        self.assertEqual(set(rows), {"started"})
        self.assertFalse(rows["started"]["ok"])
        self.assertIn("not automatically retried", rows["started"]["error"])
        self.assertEqual(large.recover_judgements(root, inputs), rows)
        self.assertEqual(len(trials.jsonl(path / "quality.jsonl")), 1)

    def test_judge_resume_recovers_saved_response_without_api(self):
        root = self.root / "judge"
        path = root / "pass_001"
        path.mkdir(parents=True)
        inputs = [dict(script="saved")]
        trials.save(path / "inputs.json", inputs)
        trials.append(path / "attempts.jsonl", dict(script="saved"))
        trials.save(path / "response_000.json", dict(status="completed", id="already_billed", usage={}))
        with patch.object(trials.set_quality, "final_text", return_value="{}"), \
                patch.object(trials.set_quality, "validate", return_value=dict(rating=dict(overall=7))):
            rows = large.recover_judgements(root, inputs)
        self.assertTrue(rows["saved"]["ok"])
        self.assertEqual(rows["saved"]["response"]["id"], "already_billed")

    def test_stream_waits_for_complete_response_record(self):
        directory, config = self.prepare("--examples", "puddles", "--per-example", "1")
        path = (large.ROOT / config["arms"][0]["manifest"]).parent / "responses.jsonl"
        path.write_text('{"target":"one"}\n{"target":')
        positions = {}
        self.assertEqual(large.terminal_targets(config, positions), {"one"})
        self.assertEqual(large.terminal_targets(config, positions), set())
        with path.open("a") as handle:
            handle.write('"two"}\n')
        self.assertEqual(large.terminal_targets(config, positions), {"two"})

    def test_stream_defers_partial_utf8_character(self):
        directory, config = self.prepare("--examples", "puddles", "--per-example", "1")
        path = (large.ROOT / config["arms"][0]["manifest"]).parent / "responses.jsonl"
        path.write_bytes(b'{"target":"one"}\n{"target":"caf\xc3')
        positions = {}
        self.assertEqual(large.terminal_targets(config, positions), {"one"})
        self.assertEqual(large.terminal_targets(config, positions), set())
        with path.open("ab") as handle:
            handle.write(b'\xa9"}\n')
        self.assertEqual(large.terminal_targets(config, positions), {"caf\u00e9"})

    def test_import_repair_preserves_completed_sample_pool_and_original_audit(self):
        directory, config = self.prepare("--examples", "puddles", "--per-example", "1", "--local-samples", "4")
        config.update(compact_checks=True, compress_samples=True, local_workers=1)

        async def fake_call(client, args, job, semaphore, *, request):
            row = self.fake_row(job)
            row["response"]["body"]["output"][0]["content"][0]["text"] = base_tests.SOURCE.replace(
                "import argparse\n", "from __future__ import annotations\nimport argparse\nfrom results import StoryError\n")
            return row

        with patch.object(trials.service, "make_client", return_value=AsyncMock()), \
                patch.object(trials.service, "call_one", side_effect=fake_call), contextlib.redirect_stdout(io.StringIO()):
            asyncio.run(trials.generate(directory, config))
            large.audit(directory, config)
            old = trials.read(directory / "qc/checks.json")[0]
            self.assertTrue(old["final"]["ok"])
            self.assertFalse(old["standalone"]["ok"])
            large.repair_imports(directory, config)
        task = large.tasks_for(directory, config)[0]
        result = trials.read(directory / "qc/checks.json")[0]
        self.assertTrue(result["standalone"]["ok"])
        self.assertTrue(result["import_repair_accepted"])
        self.assertTrue(result["existing_sample_pool_unchanged"])
        self.assertEqual(trials.read(task[2] / "check.json"), old)
        self.assertEqual(trials.jsonl(task[2] / "samples.jsonl.gz"), trials.jsonl(large.sample_path(task)))
        with patch.object(trials, "audit_one", side_effect=AssertionError("must reuse import-repaired audit")):
            self.assertEqual(large.audit_cached(task), result)
        source = (large.ROOT / task[0]["target"]).read_text()
        self.assertTrue(source.startswith("#!/usr/bin/env python3\n"))
        self.assertEqual(large.import_bootstrap(source), source)

    def test_single_story_is_ineligible_not_an_unfinished_judge_pass(self):
        checks = [dict(script="one", final=dict(ok=True), verify=dict(ok=True), samples=1)]
        groups = [[dict(story="One complete but unvarying story.")]]
        result = large.score_sample_sets(checks, {}, groups,
            dict(local_samples=1000, score_policy=dataset_score.policy()))
        self.assertEqual(result["status"], "complete")
        self.assertEqual(result["insufficient_sample_set_worlds"], 1)
        self.assertEqual(result["runtime_rejected_worlds"], 0)
        self.assertEqual(result["unrated_worlds"], 0)
        self.assertEqual(result["score"], 0)
        self.assertTrue(checks[0]["final"]["ok"])


if __name__ == "__main__":
    unittest.main()
