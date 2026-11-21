"""Offline integrity checks for the text-only Luna QA evaluation."""
from copy import deepcopy
import json
import unittest

from .storytelling.evaluate import qa_request, validate_qa


class StorytellingEvalTests(unittest.TestCase):
    def fixture(self):
        item = {'stories': [{'id': 's1', 'story': 'Nora repaired the kite.', 'qa': [
            {'id': 's1:q0', 'question': 'Who repaired the kite?', 'answer': 'Nora repaired it.',
             'evidence': ['Nora repaired the kite.']},
            {'id': 's1:q1', 'question': 'What did Nora repair?', 'answer': 'The kite.',
             'evidence': ['Nora repaired the kite.']}]}]}
        result = {'pairs': [dict(id=q['id'], answerable=True, grounded=True,
                                evidence_sufficient=True, usable=True, overall=7,
                                defects=[], note='Supported.') for q in item['stories'][0]['qa']],
                  'stories': [dict(id='s1', variety=3, note='Literal recall.')]}
        return item, result

    def test_exact_ids_and_consistent_usability(self):
        item, result = self.fixture()
        self.assertEqual(validate_qa(result, item), result)
        for kind in ['missing', 'duplicate', 'foreign', 'score', 'boolean', 'usable', 'defect']:
            bad = deepcopy(result)
            if kind == 'missing': bad['pairs'].pop()
            elif kind == 'duplicate': bad['pairs'][1]['id'] = bad['pairs'][0]['id']
            elif kind == 'foreign': bad['stories'][0]['id'] = 'other'
            elif kind == 'score': bad['pairs'][0]['overall'] = True
            elif kind == 'boolean': bad['pairs'][0]['grounded'] = 1
            elif kind == 'usable': bad['pairs'][0]['grounded'] = False
            elif kind == 'defect': bad['pairs'][0]['defects'] = ['invented_tag']
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                validate_qa(bad, item)

    def test_request_preserves_text_and_requires_every_pair(self):
        item, _ = self.fixture()
        body = qa_request(item)
        self.assertEqual(json.loads(body['input'][1]['content']), item)
        self.assertEqual(body['model'], 'gpt-6-luna')
        self.assertEqual(body['service_tier'], 'flex')
        self.assertFalse(body['store'])
        schema = body['text']['format']['schema']
        self.assertEqual(schema['properties']['pairs']['minItems'], 2)
        self.assertEqual(schema['properties']['pairs']['maxItems'], 2)
        self.assertIn('EVERY material assertion', body['input'][0]['content'])


if __name__ == '__main__':
    unittest.main()
