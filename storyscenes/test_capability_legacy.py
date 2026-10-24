"""Pinned legacy replays for the opt-in capability boundary (offline only).

Expected digests are observed snapshots in legacy_baseline.json, never rebuilt by
these tests. Frozen and current workers run in separate interpreters: importing
an archived worker in-process would reuse today's cached `runtime`/`prose`.
"""
from copy import deepcopy
from functools import lru_cache
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parent
BASELINE = ROOT / "design/capabilities_20261021/implementation/legacy_baseline.json"
MODULES = ("runtime", "worker", "simulation", "generator", "algebra", "prose")


def digest(value):
    encoded = json.dumps(value, sort_keys=True, ensure_ascii=False,
                         separators=(",", ":"), allow_nan=False).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def fingerprints(row):
    return {
        "trace_sha256": digest(row["trace"]),
        "prose_sha256": digest({key: row[key] for key in
                                ("title", "prose_seed", "story", "paragraphs")}),
        "qa_sha256": digest(row["qa"]),
        "row_sha256": digest(row),
    }


@lru_cache(maxsize=None)
def replay(world_path, seed, prose_seed, mode, hash_seed=0):
    world = ROOT / world_path
    if mode == "current":
        command = [sys.executable, "-B", str(ROOT / "worker.py"), str(world),
                   "--seeds", str(seed), "--prose"]
    else:
        entry = world.parent / "_runtime/run.py" if mode == "frozen" else ROOT / "run.py"
        command = [sys.executable, "-B", str(entry), str(world),
                   "--seed", str(seed), "--json"]
    if prose_seed is not None:
        command += ["--prose-seed", str(prose_seed)]
    env = dict(os.environ, PYTHONHASHSEED=str(hash_seed), PYTHONDONTWRITEBYTECODE="1")
    # The script directory, not a caller's PYTHONPATH, selects the runtime.
    for key in ("PYTHONPATH", "PYTHONHOME"):
        env.pop(key, None)
    result = subprocess.run(command, cwd=ROOT.parent, env=env, capture_output=True,
                            text=True, encoding="utf-8", timeout=30, check=True)
    rows = [json.loads(line) for line in result.stdout.splitlines() if line.strip()]
    if len(rows) != 1:
        raise AssertionError(f"Expected one replay row: {command!r}: {result.stdout}")
    return rows[0]


class CapabilityLegacyReplayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.baseline = json.loads(BASELINE.read_text(encoding="utf-8"))

    def setUp(self):
        self.modules_before = {name: sys.modules.get(name) for name in MODULES}

    def tearDown(self):
        for name, module in self.modules_before.items():
            self.assertIs(sys.modules.get(name), module, f"Replay replaced {name}")

    def assert_pinned(self, row, case, profile):
        self.assertEqual(row["seed"], case["seed"])
        ps = case["seed"] if case["prose_seed"] is None else case["prose_seed"]
        self.assertEqual(row["prose_seed"], ps)
        self.assertTrue(row["trace"]["events"])
        self.assertTrue(row["story"])
        self.assertTrue(row["paragraphs"])
        self.assertTrue(row["qa"])
        # Check the runtime's own trace checksum, but do not trust it as the pin.
        trace_bytes = json.dumps(row["trace"], sort_keys=True,
                                 ensure_ascii=False).encode("utf-8")
        self.assertEqual(row["trace_sha256"], hashlib.sha256(trace_bytes).hexdigest())
        self.assertEqual(fingerprints(row), case[profile])

    def test_baseline_has_both_generations_and_several_fixed_seeds(self):
        self.assertEqual(self.baseline["schema_version"], 1)
        fixtures = self.baseline["fixtures"]
        self.assertEqual({f["world"].split("/")[1] for f in fixtures},
                         {"compact_algebra_v2", "improvement_luna_v6"})
        self.assertEqual(len({f["world"] for f in fixtures}), 4)
        for fixture in fixtures:
            self.assertTrue(fixture["semantic_surfaces"])
            self.assertEqual({c["seed"] for c in fixture["cases"]}, {0, 1, 5, 777})
            self.assertEqual(len(fixture["cases"]), 5)
            for name in ("simulation.py", "generator.py"):
                self.assertTrue((ROOT / fixture["world"] / name).is_file())
            self.assertTrue((ROOT / fixture["world"]).parent.joinpath("_runtime/run.py").is_file())

    def test_frozen_replays_match_pins_across_hash_seeds(self):
        for fixture in self.baseline["fixtures"]:
            for case in fixture["cases"]:
                for hash_seed in (0, 23):
                    with self.subTest(world=fixture["world"], seed=case["seed"],
                                      prose_seed=case["prose_seed"], hash_seed=hash_seed):
                        row = replay(fixture["world"], case["seed"], case["prose_seed"],
                                     "frozen", hash_seed)
                        self.assert_pinned(row, case, "frozen")

    def test_public_cli_preserves_frozen_dispatch(self):
        for fixture in self.baseline["fixtures"]:
            for case in fixture["cases"]:
                with self.subTest(world=fixture["world"], seed=case["seed"],
                                  prose_seed=case["prose_seed"]):
                    row = replay(fixture["world"], case["seed"], case["prose_seed"], "public")
                    self.assert_pinned(row, case, "frozen")

    def test_current_legacy_worker_matches_its_observed_pins(self):
        for fixture in self.baseline["fixtures"]:
            for case in fixture["cases"]:
                with self.subTest(world=fixture["world"], seed=case["seed"],
                                  prose_seed=case["prose_seed"]):
                    row = replay(fixture["world"], case["seed"], case["prose_seed"], "current")
                    self.assert_pinned(row, case, "current")

    def test_prose_seed_does_not_change_simulation_or_qa(self):
        for fixture in self.baseline["fixtures"]:
            for mode in ("frozen", "current"):
                with self.subTest(world=fixture["world"], mode=mode):
                    first = replay(fixture["world"], 0, None, mode)
                    second = replay(fixture["world"], 0, 777, mode)
                    self.assertEqual(first["trace"], second["trace"])
                    self.assertEqual(first["qa"], second["qa"])
                    self.assertNotEqual(fingerprints(first)["prose_sha256"],
                                        fingerprints(second)["prose_sha256"])

    def test_pins_detect_trace_prose_evidence_and_qa_reference_changes(self):
        fixture = self.baseline["fixtures"][0]
        case = fixture["cases"][0]
        original = replay(fixture["world"], case["seed"], case["prose_seed"], "frozen")
        mutations = (
            ("trace_sha256", lambda r: r["trace"]["events"][0]["after"].update({"cart.owner": "mayor"})),
            ("trace_sha256", lambda r: r["trace"]["events"][-1]["causes"].append(999)),
            ("prose_sha256", lambda r: r.update(story=r["story"] + " Changed.")),
            ("prose_sha256", lambda r: r["paragraphs"][0]["facts"][0].update(value="changed")),
            ("qa_sha256", lambda r: r["qa"][0].update(answer="Changed answer.")),
            ("qa_sha256", lambda r: r["qa"][0]["event_ids"].append(999)),
            ("qa_sha256", lambda r: r["qa"][0]["cause_ids"].append(999)),
        )
        for index, (surface, mutate) in enumerate(mutations):
            with self.subTest(surface=surface, mutation=index):
                changed = deepcopy(original)
                mutate(changed)
                self.assertNotEqual(fingerprints(changed)[surface], case["frozen"][surface])
                self.assertNotEqual(fingerprints(changed)["row_sha256"], case["frozen"]["row_sha256"])


if __name__ == "__main__":
    unittest.main()
