"""Continuation probabilities, guarded prefixes, persistent state and annotations."""
import unittest

from .event_line_replay import paper_world
from .memory_continuation import continue_story
from .story_memory import annotate
from .storytelling.runtime import generate, SCENARIOS
from .storytelling.surface import detokenize
from .underdefined_probe import initial_world


class MemoryContinuationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.docs = [annotate(generate(s, 3000, continuations='expanded', symbolic_heads=True)) for s in SCENARIOS]

    def test_sampled_requery_repairs_without_supplied_operation_plan(self):
        world = paper_world(); before = world.to_dict()
        result = continue_story(self.docs, world, prefix=[dict(op='intent', actor='ada', item='book')], seed=7)
        self.assertEqual(world.to_dict(), before)
        self.assertTrue(all(result['goals_satisfied']))
        self.assertEqual(result['status'], 'sampled_stop')
        operations = [d['candidates'][d['selected']]['event']['op'] for d in result['decisions']]
        self.assertIn('fetch', operations)
        self.assertIn('patch_paper', operations)
        for decision in result['decisions']:
            self.assertAlmostEqual(sum(c['probability'] for c in decision['candidates']), 1.)
            self.assertEqual(decision['candidates'][-1]['event']['op'], 'STOP')
        previous = before
        for segment in result['segments']:
            self.assertEqual(segment['initial_world'], previous)
            previous = segment['final_world']
        self.assertEqual(previous, result['final_world'])

    def test_prefix_guards_fail_without_mutating_input(self):
        world = paper_world(); before = world.to_dict()
        with self.assertRaisesRegex(ValueError, 'blocked'):
            continue_story(self.docs, world, prefix=[dict(op='patch_paper', actor='ada', item='book', tool='tape')])
        self.assertEqual(world.to_dict(), before)

    def test_final_placement_is_rewarded_after_transformation(self):
        result = continue_story(self.docs, paper_world(), seed=1,
            prefix=[dict(op='intent', actor='ada', item='book')],
            goals=[dict(entity='book', field='state', value='repaired'),
                   dict(entity='book', field='location', value='bench')])
        self.assertEqual(result['decisions'][0]['active_goals'], [True, False])
        early_put = next(c for c in result['decisions'][0]['candidates'] if c['event']['op']=='put_item')
        self.assertEqual(early_put['factors']['goal_progress'], 1.)
        self.assertEqual(result['goals_satisfied'], [True, True])
        self.assertTrue(any(d['active_goals'] == [True, True] for d in result['decisions']))

    def test_no_unearned_ability_and_unresolved_goal_not_reported_complete(self):
        result = continue_story(self.docs, initial_world(),
            prefix=[dict(op='intent', actor='ada', item='book')], max_events=3, seed=7)
        self.assertEqual(result['goals_satisfied'], [False])
        self.assertIn('torn', result['final_world']['entities']['book']['state'])
        self.assertNotIn('can_patch_paper', result['final_world']['entities']['ada']['properties'])
        self.assertLessEqual(len(result['segments']), 4)

    def test_tokens_have_global_positions_and_correct_scene_attribute_tables(self):
        result = continue_story(self.docs, paper_world(), prefix=[dict(op='intent', actor='ada', item='book')], seed=7)
        tokens = result['attribute_generation']['tokens']
        self.assertEqual(detokenize([t['token'] for t in tokens]), result['story'])
        self.assertEqual([t['position']['token'] for t in tokens], list(range(len(tokens))))
        for token in tokens:
            table = result['trace'][token['scene_index']]['attribute_table']
            for c in token['candidates']:
                self.assertIn(c['attributes'], table)
            self.assertAlmostEqual(sum(c['probability'] for c in token['candidates']), 1.)

    def test_duplicate_documents_do_not_change_action_probabilities(self):
        a = continue_story(self.docs, paper_world(), max_events=1, seed=3)
        b = continue_story(self.docs * 2, paper_world(), max_events=1, seed=3)
        self.assertEqual(a['story'], b['story'])
        x, y = a['decisions'][0], b['decisions'][0]
        self.assertEqual([c['probability'] for c in x['candidates']], [c['probability'] for c in y['candidates']])
        events = [str(c['event']) for c in x['candidates']]
        self.assertEqual(len(events), len(set(events)))

    def test_fixed_seed_reproducible_and_different_seeds_can_choose_differently(self):
        kwargs = dict(prefix=[dict(op='intent', actor='ada', item='book')], max_events=2, policy='plain')
        a = continue_story(self.docs, paper_world(), seed=0, **kwargs)
        self.assertEqual(a, continue_story(self.docs, paper_world(), seed=0, **kwargs))
        b = continue_story(self.docs, paper_world(), seed=1, **kwargs)
        self.assertNotEqual([d['selected'] for d in a['decisions']], [d['selected'] for d in b['decisions']])

    def test_stop_is_only_outcome_when_no_mapping_is_feasible(self):
        world = paper_world(); world.flags.add('ended')
        result = continue_story(self.docs, world)
        self.assertEqual(result['status'], 'exhausted')
        self.assertEqual(result['story'], '')
        self.assertEqual(result['decisions'][0]['candidates'][0]['probability'], 1.)
        self.assertEqual(result['initial_world'], result['final_world'])

    def test_zero_limit_keeps_prefix_and_invalid_policy_is_rejected(self):
        result = continue_story(self.docs, paper_world(), max_events=0,
            prefix=[dict(op='intent', actor='ada', item='book')])
        self.assertEqual(result['decisions'], [])
        self.assertEqual(len(result['segments']), 1)
        self.assertEqual(result['status'], 'limit')
        with self.assertRaises(ValueError):
            continue_story(self.docs, paper_world(), policy='unknown')


if __name__ == '__main__':
    unittest.main()
