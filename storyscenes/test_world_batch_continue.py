import json
from pathlib import Path
import tempfile
import unittest

from world_batch_continue import resume_pauses


class ContinuationTests(unittest.TestCase):
    def test_only_explicit_drain_pause_with_complete_responses_resumes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for name, status in [('saved', 'completed'), ('unknown', None), ('capped', 'incomplete')]:
                world = root / name
                world.mkdir()
                (world / 'seed.json').write_text('{}')
                (world / 'world_0.request.json').write_text('{}')
                if status:
                    (world / 'world_0.response.json').write_text(json.dumps(dict(status=status)))
                (world / 'failure.json').write_text(json.dumps(dict(
                    paid_stage_stopped=True, error='text_0: Run stopped before dispatch')))
            ledger = root / 'budget.json'
            ledger.write_text('{"reserved_usd":0.04}')
            before = ledger.read_bytes()
            resume_pauses(root)
            self.assertFalse((root / 'saved/failure.json').exists())
            self.assertTrue((root / 'saved/drain_pause.json').exists())
            for name in ('unknown', 'capped'):
                self.assertTrue((root / name / 'failure.json').exists())
                self.assertTrue((root / name / 'replacement_provenance.json').exists())
            self.assertEqual(ledger.read_bytes(), before)
            self.assertFalse((root / 'unknown/world_0.response.json').exists())

    def test_semantic_failure_is_not_silently_repaired_or_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            world = root / 'failed'
            world.mkdir()
            (world / 'seed.json').write_text('{}')
            failure = world / 'failure.json'
            failure.write_text(json.dumps(dict(paid_stage_stopped=False, error='Repair limit exhausted')))
            original = failure.read_bytes()
            resume_pauses(root)
            self.assertEqual(failure.read_bytes(), original)
            self.assertEqual(json.loads((root / 'continuation_audit.json').read_text()), [])


if __name__ == '__main__': unittest.main()
