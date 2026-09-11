import asyncio
import json
from pathlib import Path
import tempfile
import unittest

from storypatches.artifacts import save_json
from storypatches.kernel_author import parse_kernel, parser, request_body, run, validate_result


EXAMPLE = Path(__file__).parent / "examples/lily.kernel"


class KernelAuthorTests(unittest.TestCase):
    def test_declarative_kernel_without_executing_python(self):
        parse_kernel(EXAMPLE.read_text())
        parse_kernel("Lily.Fear += dog\nLove(Lily, Mom) / 2")
        for source in ("# no expressions", "import os", "while True: pass", "x = 3", "__import__('os')", "Lily.__class__", "[x for x in y]"):
            with self.subTest(source=source), self.assertRaises(ValueError):
                parse_kernel(source)

    def test_request_contains_only_source_and_authoring_contract(self):
        source = EXAMPLE.read_text()
        body = request_body(source, model="local-test", questions=3, max_tokens=8000, thinking=False)
        self.assertEqual(body["input"][1]["content"], "KERNEL:\n" + source)
        self.assertNotIn("tools", body)
        self.assertNotIn("service_tier", body)
        self.assertNotIn("required words", body["input"][0]["content"])
        self.assertFalse(body["extra_body"]["chat_template_kwargs"]["enable_thinking"])

    def test_json_contract_and_duplicate_questions(self):
        value = {"title": "Lily", "story": "Mom found Lily's eraser.",
                 "qa": [{"question": "Who found it?", "answer": "Mom found it."}]}
        validate_result(value, 1)
        value["qa"].append(dict(value["qa"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            validate_result(value, 2)

    def test_dry_run_and_unknown_outcome_are_distinct(self):
        with tempfile.TemporaryDirectory() as folder:
            out = Path(folder) / "run"
            args = parser().parse_args(["--kernel", str(EXAMPLE), "--out", str(out), "--dry-run"])
            asyncio.run(run(args))
            self.assertFalse((out / "attempt.json").exists())
            self.assertEqual((out / "kernel.txt").read_text(), EXAMPLE.read_text())
            save_json(out / "attempt.json", {"started_at": "test"})
            args.dry_run = False
            with self.assertRaisesRegex(ValueError, "already dispatched"):
                asyncio.run(run(args))
            self.assertFalse((out / "response.json").exists())


if __name__ == "__main__":
    unittest.main()
