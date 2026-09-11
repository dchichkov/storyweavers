import copy
import json
import unittest
import tempfile
import asyncio
from pathlib import Path
from unittest.mock import patch, AsyncMock

from .span_patches import bundle, apply_edits, apply_pair, make_pair, digest, story_value
from .compose_patches import compose
from .kernel_patches import request, extract
from . import kernel_patches as author
from . import compose_patches as offline
from .artifacts import save_json, save_text


def edit(target, old, new):
    return {'target': target, 'old': old, 'new': new}


def fixture(n=6):
    kernel = '\n'.join(f'Joy(Hero{i:03d})' for i in range(n)) + '\n'
    story = {'title': 'Friends', 'story': ' '.join(f'Hero{i:03d} smiled.' for i in range(n)),
             'qa': [{'question': f'Who smiled in scene {i}?', 'answer': f'Hero{i:03d} smiled.'} for i in range(n)]}
    base = bundle(kernel, story)
    pairs = []
    for i in range(n):
        old, new = f'Hero{i:03d}', f'Friend{i:03d}'
        pairs.append(make_pair(base, kernel.replace(old, new),
                     [edit('story', old, new), edit(f'qa/q{i+1:04d}/answer', old, new)]))
    return base, pairs


class SpanTests(unittest.TestCase):
    def test_independent_edits_same_line(self):
        base, pairs = fixture()
        result = apply_pair(apply_pair(base, pairs[0]), pairs[1])
        self.assertIn('Friend000 smiled. Friend001 smiled.', result['story'])
        self.assertEqual(result, apply_pair(apply_pair(base, pairs[1]), pairs[0]))

    def test_atomic_conflict_and_wrong_stage(self):
        base, pairs = fixture()
        snapshot = copy.deepcopy(base)
        with self.assertRaises(ValueError):
            apply_edits(base, [edit('story', 'Hero000', 'Sam'), edit('story', 'absent', 'Sam')], stage='text')
        self.assertEqual(base, snapshot)
        with self.assertRaises(ValueError):
            apply_pair(apply_pair(base, pairs[0]), pairs[0])
        for bad in [edit('kernel', 'Hero000', 'Sam'), edit('../story', 'Hero000', 'Sam'),
                    edit('story', 'smiled.', 'laughed.'), edit('story', '', 'new')]:
            with self.assertRaises(ValueError):
                apply_edits(base, [bad], stage='text')

    def test_stable_qa_ids_and_add_remove(self):
        base, _ = fixture()
        first = json.dumps(base['qa']['q0001'])
        result = apply_edits(base, [edit('qa/q0001', first, ''),
                     edit('qa/q0002/answer', 'Hero001', 'Sam'),
                     edit('qa/new_unique', '', json.dumps({'question': 'New?', 'answer': 'Yes.'}))], stage='text')
        self.assertNotIn('q0001', result['qa'])
        self.assertEqual(result['qa']['q0002']['answer'], 'Sam smiled.')
        with self.assertRaises(ValueError):
            apply_edits(result, [edit('qa/new_unique', '', first)], stage='text')

    def test_reproducible_exhaustion_and_base_check(self):
        base, pairs = fixture(4)
        one, report = compose(base, pairs, count=20, minimum=3, maximum=3)
        two, _ = compose(base, list(reversed(pairs)), count=20, minimum=3, maximum=3)
        self.assertEqual(one, two)
        self.assertEqual(len(one), 4)
        self.assertFalse(report['complete'])
        bad = copy.deepcopy(pairs[0])
        bad['base_sha256'] = 'wrong'
        rows, report = compose(base, [bad], count=1)
        self.assertEqual(rows, [])
        self.assertEqual(len(report['invalid_pairs']), 1)

    def test_conflicting_pairs_are_rejected(self):
        base, pairs = fixture(3)
        other = make_pair(base, base['kernel'].replace('Hero000', 'Other'),
                          [edit('story', 'Hero000', 'Other')])
        rows, report = compose(base, [pairs[0], other], count=1, minimum=2, maximum=2)
        self.assertFalse(rows)
        self.assertEqual(report['conflicts'], 1)

    def test_span_tool_prefix(self):
        base, _ = fixture(3)
        original = {'kernel.txt': base['kernel'], 'story.json': json.dumps(story_value(base))}
        opts = dict(stage='text', model='local', thinking=False, max_tokens=100, span_edits=True)
        a, b = request(original, 'PATCH A', **opts), request(original, 'PATCH B', **opts)
        self.assertEqual(a['input'][1]['content'][:-1], b['input'][1]['content'][:-1])
        self.assertIn('q0001', a['input'][1]['content'])
        self.assertIn('edits', a['tools'][0]['parameters']['properties'])
        edits = [edit('story', 'Hero000', 'Sam')]
        response = {'status': 'completed', 'output': [{'type': 'function_call', 'name': 'apply_patch',
                    'arguments': json.dumps({'edits': edits})}]}
        self.assertEqual(extract(response, span_edits=True), edits)

    def test_5000_from_100_pairs(self):
        base, pairs = fixture(100)
        rows, report = compose(base, pairs, count=5000, max_attempts=20000)
        self.assertEqual(len(rows), 5000)
        self.assertTrue(report['complete'])
        self.assertEqual(report['llm_calls'], 0)
        self.assertEqual(len({digest(story_value(row['bundle'])) for row in rows}), 5000)

    def test_author_exports_pair_and_cli_partial_output(self):
        base, pairs = fixture(3)
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            original = root / 'base'
            save_text(original / 'kernel.txt', base['kernel'])
            save_json(original / 'story.json', story_value(base))
            args = author.parser().parse_args(['--base', str(original), '--out', str(root / 'pairs' / 'one'),
                                              '--cue', 'Rename Hero000', '--span-edits'])
            kernel_patch = '*** Begin Patch\n*** Update File: kernel.txt\n@@\n-Joy(Hero000)\n+Joy(Friend000)\n*** End Patch\n'
            def response(value):
                return {'status': 'completed', 'output': [{'type': 'function_call', 'name': 'apply_patch',
                        'arguments': json.dumps(value)}]}
            with patch.object(author, 'dispatch', AsyncMock(side_effect=[response({'patch': kernel_patch}),
                      response({'edits': pairs[0]['text_edits']})])):
                asyncio.run(author.run(args))
            saved = json.loads((args.out / 'pair.json').read_text())
            self.assertEqual(saved['base_sha256'], digest(base))
            for i, pair in enumerate(pairs[1:]):
                save_json(root / 'pairs' / f'other{i}' / 'pair.json', pair)
            argv = ['compose', '--base', str(original), '--pairs', str(root / 'pairs'),
                    '--out', str(root / 'variants'), '--count', '5', '--min-patches', '2', '--max-patches', '2']
            with patch('sys.argv', argv):
                self.assertEqual(offline.main(), 2)
            report = json.loads((root / 'variants' / 'summary.json').read_text())
            self.assertEqual(report['generated'], 3)
            self.assertTrue((root / 'variants' / 'v00000' / 'story.md').exists())


if __name__ == '__main__':
    unittest.main()
