"""The retained evidence bundle verifies replay and refuses replacement."""
import hashlib
import json
import os
from pathlib import Path
import tempfile
import subprocess
import sys
import unittest

from storyscenes.capabilities.verify import verify


class EvidenceWriterTests(unittest.TestCase):
    def test_manifest_masks_replays_and_rejected_interventions(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "evidence"
            result = verify(destination)
            self.assertGreaterEqual(result["cases"], 50)
            self.assertEqual(result["blocked"], 10)
            manifest = json.loads((destination / "manifest.json").read_text())
            for item in manifest["files"]:
                payload = (destination / item["path"]).read_bytes()
                self.assertEqual(len(payload), item["bytes"])
                self.assertEqual(hashlib.sha256(payload).hexdigest(), item["sha256"])
            row = json.loads((destination / "library_return.json").read_text())
            self.assertTrue(row["retained"]["trace"]["events"])
            self.assertTrue(row["masked_answers"])
            self.assertTrue(all(not m["answer"]["supported"] for m in row["masked_answers"]))
            script = """import json,sys
from pathlib import Path
from storyscenes.capabilities.api import registry
from storyscenes.capabilities.codec import loads
from storyscenes.capabilities.core import fingerprint,replay
root=Path(sys.argv[1]); engine=registry()
for path in sorted(root.glob('*.world.json')):
    name=path.name.removesuffix('.world.json')
    record=json.loads((root/(name+'.json')).read_text())
    world=loads(engine,path.read_text())
    state=replay(engine,world,record['path'])
    assert fingerprint(state)==record.get('trace_sha256',record.get('before_sha256')),name
print('frozen replay OK')
"""
            env = dict(os.environ, PYTHONPATH=str(destination / "runtime"), PYTHONDONTWRITEBYTECODE="1")
            result = subprocess.run([sys.executable, "-c", script, str(destination)],
                                    cwd=directory, env=env, text=True, capture_output=True, timeout=60)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertIn("frozen replay OK", result.stdout)
            for case in ("library_missing_return_grant", "library_wrong_loan", "observatory_missing_latch",
                         "harbor_lending_outside_grant_place", "harbor_return_outside_grant_place"):
                record = json.loads((destination / f"{case}.json").read_text())
                self.assertEqual(record["before_sha256"], record["after_sha256"])
            before = (destination / "manifest.json").read_bytes()
            with self.assertRaises(FileExistsError):
                verify(destination)
            self.assertEqual((destination / "manifest.json").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
