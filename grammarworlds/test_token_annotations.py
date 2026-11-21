import unittest

from .grammar import Node, choice, seq, text
from .world import Frame
from .storytelling.runtime import SCENARIOS, generate, replay
from .storytelling.surface import detokenize
from .storytelling.token_annotations import TokenAnnotations
from .symbolic_heads.positions import Position, SymbolicRotary


class TokenAnnotationTests(unittest.TestCase):
    def test_all_worlds_preserve_generation_and_align_tokens(self):
        for scenario in SCENARIOS:
            for tense, mode, heads in [('past', 'original', False),
                                       ('present', 'expanded', True)]:
                with self.subTest(scenario=scenario, tense=tense):
                    kwargs = dict(tense=tense, continuations=mode, symbolic_heads=heads)
                    plain = generate(scenario, 7, **kwargs)
                    annotated = generate(scenario, 7, token_annotations=True, **kwargs)
                    annotation = annotated.pop('token_annotations')
                    self.assertEqual(plain, annotated)
                    self.assertTrue(replay(annotated))
                    tokens = annotation['tokens']
                    expected = [p['selected'] for t in plain['trace'] for p in t['word_trace']
                                if p['selected'] != '<END>']
                    self.assertEqual(expected, [t['token'] for t in tokens])
                    self.assertEqual(plain['story'], detokenize(expected))
                    for index, token in enumerate(tokens):
                        position = Position(**token['position'])
                        self.assertEqual(index, position.token)
                        self.assertEqual(SymbolicRotary().encode(position), token['rotary'])
                        self.assertLessEqual(token['event_context']['anchor_token'], index)
                        for entity in token['entities']:
                            self.assertIn(entity, plain['initial_world']['entities'])
                            self.assertEqual(token['entity_state'][entity]['scope'],
                                             'scene_boundary_observation')

    def test_ambiguity_does_not_invent_token_binding(self):
        collector = TokenAnnotations()
        node = choice('ambiguous', seq('referent:a', 'it'), seq('referent:b', 'it'))
        state = {'a': {}, 'b': {}}
        collector.append(node, ('it',), Frame('look_again', 'a'), state, state, 0)
        token = collector.finish('test')['tokens'][0]
        self.assertEqual(token['entities'], [])
        self.assertNotIn('referent:a', token['grammar_tags'])

    def test_repeat_names_quotes_multiword_and_silent_event(self):
        collector = TokenAnnotations()
        node = Node('text', 'test', ('picked up', '.', '”'))
        for i in range(2):
            collector.append(node, node.children, Frame('obtain_tool', 'a'), {}, {}, i)
        collector.append(None, (), Frame('wait', 'a'), {}, {}, 2)
        result = collector.finish('test')
        tokens = result['tokens']
        self.assertEqual(tokens[0]['event_context']['name'], tokens[3]['event_context']['name'])
        self.assertNotEqual(tokens[0]['event_context']['anchor_token'], tokens[3]['event_context']['anchor_token'])
        self.assertEqual([0, 0, 0, 1, 1, 1], [t['position']['sentence'] for t in tokens])
        self.assertEqual(tokens[3]['position']['in_sentence'], 0)
        self.assertEqual(result['unnarrated_operations'][0]['before_next_token'], 6)

    def test_state_observation_keeps_boundary_and_does_not_alias(self):
        collector = TokenAnnotations()
        before = {'scissors': {'location': 'table'}}
        after = {'scissors': {'location': 'lili'}}
        collector.append(seq('referent:scissors', text('scissors')), ('scissors',),
                         Frame('obtain_tool', 'lili'), before, after, 0)
        after['scissors']['location'] = 'drawer'
        token = collector.finish('test')['tokens'][0]
        self.assertEqual(token['entity_state']['scissors']['before']['location'], 'table')
        self.assertEqual(token['entity_state']['scissors']['after']['location'], 'lili')

    def test_mismatched_surface_fails(self):
        with self.assertRaises(ValueError):
            TokenAnnotations().append(text('took'), ('gave',), Frame('take', 'a'), {}, {}, 0)


if __name__ == '__main__':
    unittest.main()
