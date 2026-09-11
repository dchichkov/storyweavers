import asyncio
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, AsyncMock

from . import kernel_patches as kp


def edit(path, old, new):
    return f'*** Begin Patch\n*** Update File: {path}\n@@\n-{old}\n+{new}\n*** End Patch\n'


def response(text):
    return {'status': 'completed', 'output': [{'type': 'function_call',
            'name': 'apply_patch', 'arguments': json.dumps({'patch': text})}]}


class KernelPatchTests(unittest.TestCase):
    def test_kernel_gate(self):
        source = 'Lily(Character, girl, Curious)\nLoss(Lily, eraser)\n'
        result, _ = kp.validate_kernel_patch(source, edit('kernel.txt', 'Loss(Lily, eraser)', 'Loss(Lily, pencil)'))
        self.assertIn('pencil', result)
        for bad in [edit('story.json', 'x', 'y'),
                    edit('kernel.txt', 'missing', 'x'),
                    edit('kernel.txt', 'Loss(Lily, eraser)', 'Loss(Lily, eraser)'),
                    edit('kernel.txt', 'Loss(Lily, eraser)', 'import os'),
                    edit('kernel.txt', 'Loss(Lily, eraser)', 'UnknownKernelXYZ(Lily)')]:
            with self.assertRaises((ValueError, SyntaxError)):
                kp.validate_kernel_patch(source, bad)

    def test_exact_and_ambiguous(self):
        for source, old in [('Fear(Lily, dog)\nFear(Lily, dog)\n', 'Fear(Lily, dog)'),
                            ('Fear(Lily, "dog")\n', 'Fear(Lily, “dog”)')]:
            with self.assertRaises(ValueError):
                kp.validate_kernel_patch(source, edit('kernel.txt', old, 'Brave(Lily)'))

    def test_text_contract(self):
        value = {'title': 'Lily', 'story': 'Lily lost an eraser.',
                 'qa': [{'question': 'What?', 'answer': 'An eraser.'}]}
        raw = json.dumps(value)
        changed = raw.replace('eraser', 'pencil')
        _, result = kp.validate_text_patch(raw, edit('story.json', raw, changed))
        self.assertIn('pencil', result['qa'][0]['answer'])
        for bad in [edit('../story.json', raw, changed), edit('story.json', raw, '{}'),
                    edit('story.json', raw, raw)]:
            with self.assertRaises(ValueError):
                kp.validate_text_patch(raw, bad)

    def test_stable_prefix_and_single_tool(self):
        bundle = {'kernel.txt': 'Happy\n', 'story.json': '{}'}
        opts = dict(stage='text', model='local', thinking=False, max_tokens=500)
        first = kp.request(bundle, 'VALIDATED KERNEL PATCH:\na', **opts)
        second = kp.request(bundle, 'VALIDATED KERNEL PATCH:\nb', **opts)
        self.assertEqual(first['input'][0], second['input'][0])
        self.assertEqual(first['input'][1]['content'][:-1], second['input'][1]['content'][:-1])
        self.assertEqual(first['tools'], [kp.TOOL])
        self.assertEqual(kp.extract(response('patch')), 'patch')
        bad = response('patch')
        bad['output'].append({'type': 'function_call', 'name': 'read_file'})
        with self.assertRaises(ValueError):
            kp.extract(bad)

    def test_seeded_cues(self):
        source = 'Fear(Lily, dog) + Brave(Lily)\n'
        self.assertEqual(kp.choose_cue(source, 42, 'remove'), kp.choose_cue(source, 42, 'remove'))
        self.assertIn('rain', kp.choose_cue(source, 42, 'word', 'rain'))
        with self.assertRaises(ValueError):
            kp.choose_cue(source, 42, 'word')

    def test_two_stage_and_invalid_kernel_stops(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            base = root / 'base'
            base.mkdir()
            source = 'Lily(Character, girl, Curious)\nLoss(Lily, eraser)\n'
            story = json.dumps({'title': 'Lily', 'story': 'Lily lost an eraser.',
                               'qa': [{'question': 'What?', 'answer': 'An eraser.'}]})
            kp.save_text(base / 'kernel.txt', source)
            kp.save_text(base / 'story.json', story)
            kernel_patch = edit('kernel.txt', 'Loss(Lily, eraser)', 'Loss(Lily, pencil)')
            args = kp.parser().parse_args(['--base', str(base), '--out', str(root / 'run'), '--cue', 'Use a pencil'])
            mock = AsyncMock(side_effect=[response(kernel_patch), response(edit('story.json', story, story.replace('eraser', 'pencil')))])
            with patch.object(kp, 'dispatch', mock):
                asyncio.run(kp.run(args))
            self.assertEqual(mock.await_count, 2)
            text_body = mock.await_args_list[1].args[3]
            self.assertIn(source, text_body['input'][1]['content'])
            self.assertIn(kernel_patch, text_body['input'][1]['content'])
            self.assertTrue((root / 'run' / 'story.md').exists())
            args.out = root / 'invalid'
            with patch.object(kp, 'dispatch', AsyncMock(return_value=response(edit('kernel.txt', 'absent', 'Happy')))) as mock:
                with self.assertRaises(ValueError):
                    asyncio.run(kp.run(args))
                self.assertEqual(mock.await_count, 1)

    def test_dispatch_resume(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            client = AsyncMock()
            saved = response('patch')
            kp.save_json(out / 'kernel.request.json', {'a': 1})
            kp.save_json(out / 'kernel.response.json', saved)
            self.assertEqual(asyncio.run(kp.dispatch(client, out, 'kernel', {'a': 1})), saved)
            client.responses.create.assert_not_called()
            with self.assertRaises(ValueError):
                asyncio.run(kp.dispatch(client, out, 'kernel', {'a': 2}))
            kp.save_json(out / 'text.attempt.json', {})
            with self.assertRaises(ValueError):
                asyncio.run(kp.dispatch(client, out, 'text', {}))


if __name__ == '__main__':
    unittest.main()
