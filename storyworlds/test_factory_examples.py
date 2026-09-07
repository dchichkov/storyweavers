import asyncio
import contextlib
from dataclasses import asdict
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import canonical_examples
import openai_batch_world_factory as batch
import openai_service_world_factory as service
import openai_service_world_pipeline as pipeline


class FactoryExamplesTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=batch.ROOT)
        self.addCleanup(self.temp.cleanup)
        self.example = Path(self.temp.name) / "example.py"
        self.example.write_text("# custom example marker\n")
        self.relative = self.example.relative_to(batch.ROOT)
        self.job = batch.StoryworldJob(
            custom_id="test", name="test", target="storyworlds/worlds/test.py",
            seed=42, words=["clue"], setting="library", features=["mystery"],
            style="bedtime", domain="library mystery",
        )

    def test_custom_replaces_bundled_examples(self):
        prompt = batch.build_storyworld_prompt(self.job, example_files=[self.relative])
        self.assertIn("# custom example marker", prompt)
        self.assertNotIn("### storyworlds/worlds/puddles.py", prompt)
        self.assertNotIn("### storyworlds/worlds/pirates.py", prompt)

    def test_default_selection_unchanged(self):
        self.assertEqual(batch.example_world_paths("puddles"), (batch.WORLDS_DIR / "puddles.py",))
        self.assertEqual(batch.example_world_paths(), batch.EXAMPLE_WORLD_PATHS)

    def test_addendum_follows_example_and_seed_once(self):
        addendum = self.example.with_name("addendum.md")
        addendum.write_text("Final trial guidance marker.\n")
        for mode in batch.EMIT_MODES:
            prompt = batch.build_storyworld_prompt(self.job, example_files=[self.relative],
                                                  prompt_addendum=addendum, emit_mode=mode)
            self.assertEqual(prompt.count("Final trial guidance marker."), 1)
            self.assertGreater(prompt.index("Final trial guidance marker."), prompt.index("- Style: bedtime"))
            self.assertGreater(prompt.index("- Style: bedtime"), prompt.index("# custom example marker"))
            self.assertTrue(prompt.endswith("Final trial guidance marker.\n"))
        before = batch.prompt_cache_key(example_files=[self.relative], prompt_addendum=addendum)
        addendum.write_text("Different final guidance.\n")
        self.assertNotEqual(before, batch.prompt_cache_key(example_files=[self.relative], prompt_addendum=addendum))

    def test_dialogue_required_without_dialogue_seed_feature(self):
        original_job = asdict(self.job)
        for mode in batch.EMIT_MODES:
            with self.subTest(mode=mode):
                prompt = batch.build_storyworld_prompt(self.job, emit_mode=mode,
                                                      example_files=[self.relative])
                self.assertIn("Every sample should include a brief back-and-forth exchange of spoken dialogue", prompt)
                self.assertIn("Inner monologue, quoted notes, and narrator summaries do not count.", prompt)
                self.assertIn("current contract above where an older example differs.", prompt)
        self.assertEqual(asdict(self.job), original_job)
        self.assertNotIn("Dialogue", self.job.features)

    def test_contract_changes_invalidate_prompt_cache(self):
        before = batch.prompt_cache_key(example_files=[self.relative])
        read = batch.read_prompt_file

        def changed_contract(path):
            content = read(path)
            return content + "\nNew contract requirement." if path == batch.STORY_CONTRACT_PATH else content

        with patch.object(batch, "read_prompt_file", side_effect=changed_contract):
            self.assertNotEqual(before, batch.prompt_cache_key(example_files=[self.relative]))

    def test_current_and_retired_names_resolve_in_all_three_clis(self):
        for name, source in canonical_examples.EXAMPLE_SOURCES.items():
            with self.subTest(name=name):
                self.assertEqual(batch.example_world_paths(name), (source,))
                flags = ["--example-worlds", name]
                self.assertEqual(batch.build_parser().parse_args(["prepare", *flags]).example_worlds, name)
                args = service.build_parser().parse_args(flags)
                body = service.request_body(args, self.job)
                expected = batch.build_storyworld_prompt(self.job, example_worlds=name)
                self.assertEqual(body["input"][0]["content"][0]["text"], expected)
                pa = pipeline.build_parser().parse_args(flags)
                self.assertEqual(pipeline.service_prompt(asdict(self.job), pa), expected)
                self.assertIn(source.read_text(), expected)

    def test_cache_tracks_paths_and_content(self):
        first = batch.prompt_cache_key(example_files=[self.relative])
        self.assertEqual(first, batch.prompt_cache_key(example_files=[self.example]))
        self.assertNotEqual(first, batch.prompt_cache_key(example_worlds="puddles"))
        self.example.write_text("# modified example marker\n")
        self.assertNotEqual(first, batch.prompt_cache_key(example_files=[self.example]))

    def test_multiple_examples_and_order(self):
        second = self.example.with_name("second.py")
        second.write_text("# second example marker\n")
        prompt = batch.build_storyworld_prompt(self.job, example_files=[self.example, second])
        self.assertLess(prompt.index("# custom example marker"), prompt.index("# second example marker"))
        self.assertNotEqual(batch.prompt_cache_key(example_files=[self.example, second]),
                            batch.prompt_cache_key(example_files=[second, self.example]))

    def test_reject_invalid_paths(self):
        for paths in ([], [self.example, self.example], [Path("missing.py")], [Path("/etc/passwd")]):
            with self.subTest(paths=paths), self.assertRaises(ValueError):
                batch.example_world_paths(example_files=paths)

    def test_mutually_exclusive_cli(self):
        for parser, prefix in [(batch.build_parser(), ["prepare"]),
                               (service.build_parser(), []), (pipeline.build_parser(), [])]:
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                parser.parse_args(prefix + ["--example-worlds", "puddles", "--example-file", str(self.relative)])

    def test_factories_and_pipeline_use_same_prompt(self):
        flags = ["--example-file", str(self.relative)]
        args = service.build_parser().parse_args(flags)
        body = service.request_body(args, self.job)
        expected = batch.build_storyworld_prompt(self.job, example_files=[self.example])
        self.assertEqual(body["input"][0]["content"][0]["text"], expected)
        pa = pipeline.build_parser().parse_args(flags)
        self.assertEqual(pipeline.service_prompt(asdict(self.job), pa), expected)
        self.assertIn(str(self.relative), pipeline.factory_command(pa))
        self.assertEqual(pa.quality_model, "gpt-5.4-mini")
        ba = batch.build_parser().parse_args(["prepare", "--dry-run", *flags])
        with patch.object(batch, "make_jobs", return_value=(42, [self.job])), contextlib.redirect_stdout(io.StringIO()):
            result = batch.prepare_files(ba)
        self.assertEqual(result["requests"][0]["body"]["input"][0]["content"][0]["text"], expected)

    def test_manifest_replay_preserves_custom_examples(self):
        args = service.build_parser().parse_args([
            "-n", "1", "--seed", "42", "--dry-run", "--example-file", str(self.relative),
        ])
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            asyncio.run(service.run(args))
        preview = json.loads(output.getvalue())
        manifest = preview["manifest"]
        self.assertEqual(manifest["example_files"], [self.relative.as_posix()])
        manifest_path = Path(self.temp.name) / "run.manifest.json"
        manifest_path.write_text(json.dumps(manifest))
        with patch("sys.argv", ["pipeline", "--from-manifest", str(manifest_path),
                                "--skip-quality", "--skip-qa-static"]), \
             patch.object(pipeline, "write_story_files", return_value={}), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(pipeline.main(), 0)
        prompt_path = next((Path(self.temp.name) / "run.prompts").glob("*.prompt.md"))
        self.assertEqual(prompt_path.read_text(), preview["first_request"]["input"][0]["content"][0]["text"])

    def test_quality_outputs_stay_with_each_manifest(self):
        args = pipeline.build_parser().parse_args([])
        outputs = []
        for arm in ("first", "second"):
            manifest = Path(self.temp.name) / arm / "matched.manifest.json"
            quality, summary = pipeline.quality_paths(manifest, args)
            self.assertEqual(quality, manifest.parent / "matched.quality.jsonl")
            self.assertEqual(summary, manifest.parent / "matched.quality.summary.json")
            outputs.append(quality)
        self.assertNotEqual(*outputs)

    def test_quality_output_override_preserved(self):
        output = Path(self.temp.name) / "custom.jsonl"
        args = pipeline.build_parser().parse_args(["--quality-out", str(output)])
        self.assertEqual(pipeline.quality_paths(Path("run.manifest.json"), args),
                         (output, output.with_suffix(".summary.json")))

    def test_source_extraction_ignores_commentary(self):
        source = "#!/usr/bin/env python3\nprint('world')"
        commentary = {"type": "message", "phase": "commentary", "content": [
            {"type": "output_text", "text": "I will write the source now."}]}
        for phase in (None, "final_answer"):
            answer = {"type": "message", "content": [
                {"type": "output_text", "text": source}]}
            if phase:
                answer["phase"] = phase
            row = {"response": {"body": {"output": [commentary, answer]}}}
            self.assertEqual(batch.extract_python_source(row, self.job.target),
                             (source, "raw_python_source"))
        row = {"response": {"body": {"output": [commentary]}}}
        self.assertEqual(batch.extract_python_source(row, self.job.target),
                         (None, "missing_output"))


if __name__ == "__main__":
    unittest.main()
