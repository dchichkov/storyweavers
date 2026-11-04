from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import luna_xhigh_batch as batch


class BatchTests(unittest.TestCase):
    def test_distinct_tasks_frozen_sources_and_output_limit(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            with patch.object(batch, "HERE", root), patch.object(batch, "MANIFEST", root / "manifest.json"):
                batch.prepare()
                with self.assertRaises(FileExistsError):
                    batch.prepare()
                manifest = json.loads((root / "manifest.json").read_text())
                self.assertEqual(len({e["task_seed"] for e in manifest["entries"]}), 20)
                self.assertEqual(len({tuple(e["words"]) for e in manifest["entries"]}), 20)
                for entry in manifest["entries"]:
                    arm = root / entry["arm"]
                    request = json.loads((arm / "request.json").read_text())
                    settings = json.loads((arm / "settings.json").read_text())
                    self.assertEqual(request["max_output_tokens"], 128000)
                    self.assertEqual(request["reasoning"], {"effort": "xhigh"})
                    self.assertEqual(settings["timeout_seconds"], 1800)
                    supplied = json.loads(request["input"][1]["content"].split("\n", 1)[1])
                    self.assertEqual(request["input"][0]["content"], supplied["TASK.md"])
                    self.assertIn(str(entry["task_seed"]), supplied["TASK.md"])
                    for name, expected in settings["source_hashes"].items():
                        self.assertEqual(batch.api.digest((arm / "input" / name).read_bytes()), expected)
                        if name != "TASK.md":
                            self.assertEqual((arm / "input" / name).read_bytes(), (batch.BASE / "input" / name).read_bytes())

    def test_parallel_budget_reservations_and_settlements_do_not_clobber(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            def spend(i):
                ledger = batch.api.Ledger(root)
                index = ledger.reserve(str(i), .15)
                ledger.settle(index, .02, marker=i)
                return index
            with ThreadPoolExecutor(max_workers=20) as pool:
                indexes = list(pool.map(spend, range(20)))
            rows = batch.api.Ledger(root).data["entries"]
            self.assertEqual(len(set(indexes)), 20)
            self.assertEqual({r["marker"] for r in rows}, set(range(20)))
            self.assertAlmostEqual(sum(r["reserved_usd"] for r in rows), .4)

    def test_parallel_reservations_enforce_shared_cap(self):
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            batch.api.save(root / "budget.json", dict(authorized_usd=1, entries=[]))
            def reserve(i):
                try:
                    batch.api.Ledger(root).reserve(str(i), .25)
                    return True
                except ValueError:
                    return False
            with ThreadPoolExecutor(max_workers=20) as pool:
                results = list(pool.map(reserve, range(20)))
            self.assertEqual(sum(results), 4)
            self.assertEqual(len(batch.api.Ledger(root).data["entries"]), 4)


if __name__ == "__main__":
    unittest.main()
