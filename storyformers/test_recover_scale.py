"""Unknown API outcomes stay fully budgeted when a later retry is prepared."""

import asyncio
import fcntl
import json
from pathlib import Path
import tempfile
import unittest

from .online_teacher import Budget,BudgetExceeded,atomic_json
from .recover_scale import prepare


class RecoveryTests(unittest.TestCase):
    def test_unknown_attempt_is_preserved_and_still_limits_retry_spending(self):
        async def trial(folder):
            root=Path(folder);step=root/'run_01_b08/step_000'
            attempt=step/'attempts/001';attempt.mkdir(parents=True)
            body=dict(input='x',max_output_tokens=8192)
            atomic_json(step/'request.json',body)
            atomic_json(attempt/'error.json',dict(type='APITimeoutError',before_send=False,status=None,code=None))
            identifier='run_01_b08/step_000'
            budget=Budget(root/'budget.json',.06)
            await budget.reserve(identifier,body)
            original=budget.data['calls'][identifier]['accounted_usd']
            self.assertEqual(prepare(root),[identifier])
            self.assertEqual(prepare(root),[])
            restored=Budget(root/'budget.json',.06)
            entry=restored.data['calls'][identifier+'/unresolved_001']
            self.assertEqual(entry['accounted_usd'],original)
            self.assertEqual(entry['state'],'unresolved')
            self.assertNotIn(identifier,restored.data['calls'])
            self.assertTrue((step/'uncertain_attempts/001/001/error.json').exists())
            with self.assertRaises(BudgetExceeded):await restored.reserve(identifier,body)
        with tempfile.TemporaryDirectory() as folder:asyncio.run(trial(folder))

    def test_recovery_cannot_race_a_live_suite(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            with (root/'.lock').open('w') as lock:
                fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
                with self.assertRaises(BlockingIOError):prepare(root)


if __name__=='__main__':unittest.main()
