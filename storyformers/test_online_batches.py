"""Batch repairs must improve all revealed targets, with resumable branch state."""

import asyncio
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from .online import backward_batch, choose, empty_patch
from .online_batches import batch_packet, train_batches
from .neuron_review import model_fingerprint
from .test_online import toy


class BatchOnlineTests(unittest.TestCase):
    def test_repair_cannot_improve_only_representative_at_batch_expense(self):
        model=toy()
        pairs=[([],dict(token='a',pos='n')),([],dict(token='b',pos='n'))]
        weighted,gradient=backward_batch(model,pairs)
        self.assertEqual(model_fingerprint(model),model_fingerprint(weighted))
        patch=empty_patch(weighted)
        patch['outputs']=[dict(token='a',append=[],scale=[dict(rule=0,factor=20.)])]
        selected,decision=choose(model,weighted,patch,pairs[0],[],current_pairs=pairs)
        self.assertEqual(decision['adopted'],'unchanged')
        self.assertGreater(decision['scores']['teacher']['current']['joint_nll'],
                           decision['scores']['unchanged']['current']['joint_nll'])
        evidence=batch_packet(weighted,pairs,model,gradient,[],[[pairs[0][1]],[pairs[1][1]]],None)
        self.assertEqual(evidence['batch_summary']['targets'],2)
        self.assertEqual(evidence['batch_target_counts'],{'a':1,'b':1})

    def test_batch_resume_preserves_control_and_does_not_recall_teacher(self):
        async def experiment(folder):
            calls=[]
            async def teacher(evidence,directory):
                calls.append(evidence)
                return deepcopy(evidence['patch_template'])
            docs=[[dict(token='a',pos='n'),dict(token='b',pos='n')] for _ in range(20)]
            out=Path(folder)/'branch'
            await train_batches(out,toy(),docs,list(range(20)),2,[],teacher)
            report=json.loads((out/'training_report.json').read_text())
            self.assertEqual(report['observations'],40)
            self.assertEqual(len(calls),10)
            await train_batches(out,toy(),docs,list(range(20)),2,[],teacher)
            self.assertEqual(len(calls),10)
            self.assertTrue(all(e['batch_document_count']==2 for e in calls))
        with tempfile.TemporaryDirectory() as folder:
            asyncio.run(experiment(folder))


if __name__=='__main__':
    unittest.main()
