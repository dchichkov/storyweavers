"""Larger experiment scheduling, feedback, and conservative transport recovery."""

import asyncio
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest
from unittest.mock import AsyncMock,patch
import httpx

from .online_batches import train_batches
from .online_scale import before_send_failure,safe_dispatch,settings
from .test_online import toy


class ScaleTests(unittest.TestCase):
    def test_ten_runs_have_ten_larger_batches_and_paired_data_orders(self):
        runs=settings()
        self.assertEqual(len(runs),10)
        for small,large in zip(runs[::2],runs[1::2]):
            self.assertEqual((small['batch_size'],large['batch_size']),(8,16))
            self.assertEqual(len(small['document_indices']),80)
            self.assertEqual(len(large['document_indices']),160)
            self.assertEqual(small['document_indices'],large['document_indices'][:80])
            self.assertEqual(len(set(large['document_indices'])),160)

    def test_only_connection_establishment_is_known_before_send(self):
        self.assertTrue(before_send_failure(httpx.ConnectError('TLS failed')))
        self.assertTrue(before_send_failure(httpx.ConnectTimeout('connect timed out')))
        self.assertFalse(before_send_failure(httpx.ReadTimeout('unknown response outcome')))
        self.assertFalse(before_send_failure(httpx.WriteError('possibly partial request')))

    def test_safe_retry_keeps_idempotency_and_cached_response_is_not_resent(self):
        async def trial(folder):
            calls=[]
            async def create(**kwargs):
                calls.append(kwargs)
                if len(calls)==1:
                    raise httpx.ConnectError('before HTTP')
                return SimpleNamespace(model_dump=lambda **kw: {'status':'completed'})
            client=SimpleNamespace(responses=SimpleNamespace(create=create))
            path=Path(folder)
            with patch('storyformers.online_scale.asyncio.sleep',new_callable=AsyncMock):
                result=await safe_dispatch(path,{'model':'gpt-6-luna','prompt_cache_options':{'mode':'explicit','ttl':'30m'}},client)
                self.assertEqual(await safe_dispatch(path,{'model':'gpt-6-luna','prompt_cache_options':{'mode':'explicit','ttl':'30m'}},client),result)
            self.assertEqual(len(calls),2)
            self.assertEqual(calls[0]['extra_headers'],calls[1]['extra_headers'])
            error=json.loads((path/'attempts/001/error.json').read_text())
            self.assertTrue(error['before_send'])
        with tempfile.TemporaryDirectory() as folder: asyncio.run(trial(folder))

    def test_ambiguous_failure_cannot_be_automatically_resent(self):
        async def trial(folder):
            create=AsyncMock(side_effect=httpx.ReadTimeout('unknown'))
            client=SimpleNamespace(responses=SimpleNamespace(create=create))
            with self.assertRaises(httpx.ReadTimeout):await safe_dispatch(Path(folder),{'prompt_cache_options':{'mode':'explicit','ttl':'30m'}},client)
            with self.assertRaisesRegex(RuntimeError,'ambiguous'):await safe_dispatch(Path(folder),{'prompt_cache_options':{'mode':'explicit','ttl':'30m'}},client)
            self.assertEqual(create.call_count,1)
        with tempfile.TemporaryDirectory() as folder:asyncio.run(trial(folder))

    def test_rollout_feedback_adds_no_training_targets_and_resumes(self):
        async def trial(folder):
            observed=[]
            async def teacher(evidence,directory):
                observed.append(deepcopy(evidence))
                return deepcopy(evidence['patch_template'])
            docs=[[dict(token='a',pos='n'),dict(token='b',pos='n')] for _ in range(20)]
            out=Path(folder)/'branch'
            await train_batches(out,toy(),docs,list(range(20)),2,[],teacher,feedback=True)
            await train_batches(out,toy(),docs,list(range(20)),2,[],teacher,feedback=True)
            self.assertEqual(len(observed),10)
            self.assertEqual(json.loads((out/'training_report.json').read_text())['observations'],40)
            self.assertIn('free_generation',observed[0])
            self.assertIn('candidate_scores',observed[1]['previous_decision'])
        with tempfile.TemporaryDirectory() as folder:asyncio.run(trial(folder))


if __name__=='__main__':unittest.main()
