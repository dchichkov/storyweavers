"""Trusted offline integration check for isolated generated kite packs."""
from collections import Counter
import importlib
import json
from pathlib import Path
import sys
import unittest


def main():
    root = Path(sys.argv[1]).resolve()
    sys.path.insert(0, str(root))
    from storyscenes.mini_adventures.review import verify_row, describe
    pack = root / "storyscenes/mini_adventures/kite"
    report = {"attempts": [], "import_error": None}
    try:
        module = importlib.import_module("storyscenes.mini_adventures.kite.world")
        entries = json.loads((pack / "scene_inventory.json").read_text())["scenes"]
        ids = [s["id"] for s in entries]
        mapped = {i for e in entries for i in e["implemented_ids"]}
        report["inventory_ok"] = len(ids) == len(set(ids)) and mapped == set(module.SCENES)
        prose = "\n".join(line for line in (pack / "reference_story.md").read_text().splitlines()
                          if not line.startswith("#"))
        report["reference_words"] = len(prose.split())
        report["reference_length_ok"] = 900 <= report["reference_words"] <= 1100
        good = []
        for count in (7, 8):
            for seed in range(5000, 5050):
                attempt = {"seed": seed, "count": count, "ok": False}
                try:
                    row = verify_row(module, module.generate(seed, count=count), seed, count)
                    good.append(row)
                    attempt.update(ok=True, row=row)
                except Exception as exc:
                    attempt["error"] = f"{type(exc).__name__}: {exc}"
                report["attempts"].append(attempt)
        report["corpus"] = describe(good)
        suite = unittest.defaultTestLoader.discover(str(pack), pattern="test_*.py", top_level_dir=str(root))
        result = unittest.TextTestRunner(stream=sys.stderr, verbosity=1).run(suite)
        report["tests"] = {"run": result.testsRun, "passed": result.wasSuccessful(),
                           "failures": len(result.failures), "errors": len(result.errors)}
    except Exception as exc:
        report["import_error"] = f"{type(exc).__name__}: {exc}"
    report["passed"] = (len(report["attempts"]) == 100 and all(r["ok"] for r in report["attempts"])
                        and report.get("inventory_ok", False) and report.get("reference_length_ok", False)
                        and report.get("tests", {}).get("passed", False)
                        and report.get("tests", {}).get("run", 0) > 0)
    (root / "check.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: v for k, v in report.items() if k != "attempts"}, indent=2))


if __name__ == "__main__":
    main()
