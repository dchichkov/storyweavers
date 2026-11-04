import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from storyscenes import authoring_api as api


def bundle():
    return {"files": [{"path": api.PREFIX + name, "content": ""} for name in
        ("__init__.py", "world.py", "test_world.py", "reference_story.md", "scene_inventory.json", "README.md")]}


class AuthoringAPITests(unittest.TestCase):
    def test_bundle_paths(self):
        self.assertEqual(len(api.validate_bundle(bundle())), 6)
        for bad in ("/tmp/x.py", api.PREFIX + "../other.py", api.PREFIX + "a/../../x.py",
                    api.PREFIX + ".env.py", api.PREFIX + "sub\\bad.py", api.PREFIX + "x.sh"):
            value = bundle()
            value["files"].append({"path": bad, "content": "x"})
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                api.validate_bundle(value)

    def test_duplicate_missing_and_oversized(self):
        value = bundle()
        value["files"].append(value["files"][0])
        with self.assertRaises(ValueError):
            api.validate_bundle(value)
        value = bundle()
        value["files"].pop()
        with self.assertRaises(ValueError):
            api.validate_bundle(value)
        value = bundle()
        value["files"][0]["content"] = "x" * 2_000_001
        with self.assertRaises(ValueError):
            api.validate_bundle(value)

    def test_budget_keeps_unknown_reservations(self):
        with tempfile.TemporaryDirectory() as td:
            ledger = api.Ledger(Path(td))
            index = ledger.reserve("unknown", 9)
            ledger.settle(index, None)
            with self.assertRaises(ValueError):
                ledger.reserve("next", 2)
            ledger.settle(index, .2)
            ledger.reserve("next", 2)
            self.assertEqual(len(api.Ledger(Path(td)).data["entries"]), 2)

    def test_usage_unknown_not_free(self):
        self.assertIsNone(api.usage_cost("gpt-6-luna", None))
        self.assertIsNone(api.usage_cost("gpt-6-luna", {}))
        self.assertIsNone(api.usage_cost("gpt-6-luna", {"input_tokens": -1, "output_tokens": 10}))
        self.assertGreater(api.usage_cost("gpt-6-luna", {"input_tokens": 1000, "output_tokens": 100}), 0)

    def test_prepare_explicit_inputs_and_flex(self):
        with tempfile.TemporaryDirectory() as td:
            arm = api.prepare(Path(td), "gpt-6-luna", "agent")
            request = json.loads((arm / "request.json").read_text())
            self.assertEqual(request["agent"]["service_tier"], "flex")
            self.assertEqual(request["agent"]["reasoning"], {"effort": "low"})
            self.assertFalse(request["agent"]["multi_agent"]["enabled"])
            self.assertEqual(request["environment"]["network"], {"access": "disabled"})
            names = {r["path"] for r in request["environment"]["files"]}
            self.assertEqual(names, {"/workspace/" + n for n in (*api.INPUTS, "TASK.md", "check_pack.py")})
            self.assertNotIn(".API_KEY", str(names))
            with self.assertRaises(FileExistsError):
                api.prepare(Path(td), "gpt-6-luna", "agent")

    def test_dispatch_guard_prevents_paid_retry(self):
        with tempfile.TemporaryDirectory() as td:
            arm = api.prepare(Path(td), "gpt-6-luna", "oneshot")
            api.save(arm / "dispatch.json", {"unknown": True})
            with patch.object(api, "API") as client, self.assertRaises(ValueError):
                api.run(arm, "unused")
            client.assert_not_called()

    def test_request_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            arm = api.prepare(Path(td), "gpt-6-luna", "agent")
            api.save(arm / "request.json", {})
            with patch.object(api, "API") as client, self.assertRaises(ValueError):
                api.run(arm, "unused")
            client.assert_not_called()

    def test_validation_input_tampering_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            arm = api.prepare(Path(td), "gpt-6-luna", "agent")
            api.save(arm / "bundle.json", bundle())
            (arm / "input/check_pack.py").write_text("print('pretend success')")
            with self.assertRaisesRegex(ValueError, "Validation source changed"):
                api.check(arm)

    def test_recovery_never_creates_session(self):
        with tempfile.TemporaryDirectory() as td:
            arm = api.prepare(Path(td), "gpt-6-luna", "agent")
            api.save(arm / "dispatch.json", {})
            with patch.object(api, "API") as factory:
                factory.return_value.pages.return_value = []
                with self.assertRaisesRegex(RuntimeError, "Found 0 matching sessions"):
                    api.recover(arm, "unused")
                factory.return_value.request.assert_not_called()

    def test_validation_sandbox_receives_no_credentials(self):
        if not Path("/usr/bin/sandbox-exec").exists():
            self.skipTest("macOS only")
        with tempfile.TemporaryDirectory() as td:
            arm = api.prepare(Path(td), "gpt-6-luna", "agent")
            api.save(arm / "bundle.json", bundle())
            with patch.dict("os.environ", {"OPENAI_API_KEY": "never-share"}), patch.object(api.subprocess, "run") as run:
                def complete(*args, **kwargs):
                    api.save(Path(kwargs["cwd"]) / "check.json", {"passed": False})
                    return api.subprocess.CompletedProcess([], 0, "", "")
                run.side_effect = complete
                api.check(arm)
                self.assertNotIn("OPENAI_API_KEY", run.call_args.kwargs["env"])
                self.assertEqual(run.call_args.args[0][0], "/usr/bin/sandbox-exec")
                self.assertIn('(deny file-read-data', run.call_args.args[0][2])
                self.assertIn("(deny network*)", run.call_args.args[0][2])

    def test_pagination(self):
        client = object.__new__(api.API)
        pages = [{"data": [{"id": "a"}], "has_more": True, "last_id": "a"},
                 {"data": [{"id": "b"}], "has_more": False}]
        class Response:
            def __init__(self, value):
                self.value = value
            def json(self):
                return self.value
        with patch.object(client, "request", side_effect=[Response(p) for p in pages]) as request:
            self.assertEqual([r["id"] for r in client.pages("example")], ["a", "b"])
            self.assertEqual(request.call_args.kwargs["params"]["after"], "a")


if __name__ == "__main__":
    unittest.main()
