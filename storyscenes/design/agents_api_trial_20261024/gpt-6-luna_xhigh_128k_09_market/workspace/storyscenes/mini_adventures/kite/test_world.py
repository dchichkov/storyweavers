from copy import deepcopy
from dataclasses import asdict
from itertools import product
import json
import unittest

from storyscenes.runtime import StoryError
from storyscenes.mini_adventures.local_play import LocalPlay
from .world import (
    Parameters, SCENES, generate, guard, initial, play_scene, replay, validate,
)


CORE = (
    'market_order', 'fill_order', 'inspect_scale', 'tell_neighbor',
    'settle_order', 'return_scale', 'ending',
)


def row_episode(episode):
    return {
        'id': episode.id,
        'before': episode.before,
        'after': episode.after,
        'events': list(episode.events),
        'text': episode.text,
    }


class FruitMarketTests(unittest.TestCase):
    def test_one_hundred_seeds_at_both_lengths_and_exact_replay(self):
        for seed, count in product(range(100), (7, 8)):
            with self.subTest(seed=seed, count=count):
                row = generate(seed, count=count)
                p = Parameters(**row['parameters'])
                episodes = replay(p, row['path'])
                self.assertEqual([row_episode(e) for e in episodes], row['episodes'])
                self.assertEqual(len(row['path']), count)
                self.assertEqual(len(row['path']), len(set(row['path'])))
                self.assertEqual(row['story'], '\n\n'.join(e['text'] for e in row['episodes']))
                self.assertEqual(row['final_state'], episodes[-1].after)
                self.assertTrue(row['final_state']['story.ended'])
                self.assertTrue(row['final_state']['story.outcome'])
                self.assertTrue(set(row['path']) <= set(SCENES))
                optional = {'vignette_bruised_apple', 'vignette_pear_sample'} & set(row['path'])
                self.assertEqual(len(optional), count - 7)
                state = initial(p)
                for episode in episodes:
                    self.assertEqual(episode.before, state)
                    self.assertTrue(guard(episode.id, state))
                    for event in episode.events:
                        self.assertTrue(event['action'])
                        self.assertTrue(event['changes'])
                        for key, value in event['requires'].items():
                            self.assertEqual(state[key], value)
                        for key, change in event['changes'].items():
                            self.assertEqual(state[key], change['before'])
                            state[key] = change['after']
                        validate(state)
                    self.assertEqual(state, episode.after)
                    self.assertTrue(40 <= len(episode.text.split()) <= 70, episode.text)

    def test_all_endings_have_explicit_parameter_and_path_recipes(self):
        recipes = (
            (Parameters(scale_bias_units=2, order_units=12, apples_stock_units=20,
                        neighbor_will_mix=False), 'tell_neighbor', 'honest_full'),
            (Parameters(scale_bias_units=2, order_units=12, apples_stock_units=11,
                        neighbor_will_mix=True), 'tell_neighbor', 'honest_mixed'),
            (Parameters(scale_bias_units=2, order_units=12, apples_stock_units=11,
                        neighbor_will_mix=False), 'tell_neighbor', 'honest_refunded'),
            (Parameters(scale_bias_units=2, order_units=12, apples_stock_units=20,
                        neighbor_will_mix=False), 'conceal_error', 'repaired_after_concealment_full'),
        )
        for p, choice, expected in recipes:
            path = CORE[:3] + (choice,) + CORE[4:]
            final = replay(p, path)[-1].after
            self.assertEqual(final['story.outcome'], expected)

    def test_optional_scenes_have_only_their_enacted_effects(self):
        p = Parameters(scale_bias_units=2, order_units=12, apples_stock_units=20)
        base = initial(p)
        after_order = play_scene(p, base, 'market_order').after
        child = play_scene(p, after_order, 'vignette_bruised_apple')
        self.assertEqual(child.after['apples.available'], after_order['apples.available'] - 1)
        self.assertTrue(child.after['child.received_apple'])
        pear = play_scene(p, after_order, 'vignette_pear_sample')
        self.assertEqual(pear.after['pears.available'], after_order['pears.available'] - 1)
        self.assertTrue(pear.after['neighbor.will_mix'])
        untouched = play_scene(p, after_order, 'fill_order').after
        self.assertFalse(untouched['child.received_apple'])
        self.assertEqual(untouched['apples.total'], p.apples_stock_units)
        self.assertEqual(untouched['pears.available'], 24)

    def test_two_optional_vignettes_are_independently_replayable(self):
        p = Parameters(scale_bias_units=2, order_units=12, apples_stock_units=20)
        common = ('market_order', 'fill_order', 'inspect_scale', 'tell_neighbor',
                  'settle_order', 'return_scale', 'ending')
        for vignette in ('vignette_bruised_apple', 'vignette_pear_sample'):
            path = ('market_order', vignette) + common[1:]
            episodes = replay(p, path)
            self.assertEqual(len(episodes), 8)
            self.assertEqual(episodes[-1].after['story.ended'], True)

    def test_scale_bias_and_wobble_change_enacted_events(self):
        steady = Parameters(scale_bias_units=1, order_units=12, apples_stock_units=20,
                            scale_wobbles=False)
        wobbly = Parameters(scale_bias_units=3, order_units=12, apples_stock_units=20,
                            scale_wobbles=True)
        path = ('market_order', 'fill_order', 'inspect_scale', 'tell_neighbor',
                'settle_order', 'return_scale', 'ending')
        a = replay(steady, path)
        b = replay(wobbly, path)
        self.assertNotEqual(a[1].after['scale.reading_units'], b[1].after['scale.reading_units'])
        self.assertIn('steady_wobbling_dial', [e['action'] for e in b[1].events])
        self.assertIn('steady_scale_for_reference_weight', [e['action'] for e in b[2].events])
        self.assertNotIn('steady_wobbling_dial', [e['action'] for e in a[1].events])

    def test_stock_and_preference_counterfactuals_change_the_outcome(self):
        path = ('market_order', 'fill_order', 'inspect_scale', 'tell_neighbor',
                'settle_order', 'return_scale', 'ending')
        enough = Parameters(scale_bias_units=2, order_units=12, apples_stock_units=12,
                            neighbor_will_mix=False)
        short_refused = Parameters(scale_bias_units=2, order_units=12, apples_stock_units=11,
                                   neighbor_will_mix=False)
        short_accepted = Parameters(scale_bias_units=2, order_units=12, apples_stock_units=11,
                                    neighbor_will_mix=True)
        self.assertEqual(replay(enough, path)[-1].after['story.outcome'], 'honest_full')
        self.assertEqual(replay(short_refused, path)[-1].after['story.outcome'], 'honest_refunded')
        self.assertEqual(replay(short_accepted, path)[-1].after['story.outcome'], 'honest_mixed')

    def test_borrowed_scale_and_fruit_locations_remain_continuous(self):
        p = Parameters(scale_bias_units=2, order_units=12, apples_stock_units=20)
        row = generate(17, count=8, params=p)
        state = initial(p)
        for episode in replay(p, row['path']):
            state = episode.after
            self.assertEqual(state['scale.location'], state['scale.owner'])
            self.assertEqual(state['apples.available'] + state['child.apple_units'] + state['order.apples'], state['apples.total'])
            self.assertEqual(state['pears.available'] + state['neighbor.sample_units'] + state['order.pears'], state['pears.total'])
        self.assertEqual(state['scale.owner'], 'keeper')
        self.assertTrue(state['scale.verified'])
        self.assertEqual(state['scale.bias_units'], 0)

    def test_illegal_scenes_and_local_actions_do_not_mutate_callers(self):
        p = Parameters()
        state = initial(p)
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(p, state, 'inspect_scale')
        self.assertEqual(state, saved)
        local = LocalPlay(state, actors=('Nella',), validate=validate)
        before_state, before_events = deepcopy(local.state), deepcopy(local.events)
        with self.assertRaises(StoryError):
            local.act('illegal_transfer', {'scale.owner': 'keeper'}, **{'scale.owner': 'helper'})
        self.assertEqual(local.state, before_state)
        self.assertEqual(local.events, before_events)

    def test_invalid_parameters_counts_and_repeated_scenes(self):
        for kwargs in (
            {'scale_bias_units': True}, {'scale_bias_units': 0},
            {'order_units': 21}, {'apples_stock_units': 7},
            {'scale_wobbles': 1}, {'neighbor_will_mix': 'yes'},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        for count in (True, 6, 9):
            with self.subTest(count=count), self.assertRaises(ValueError):
                generate(count=count)
        with self.assertRaises(StoryError):
            replay(Parameters(), ('market_order', 'market_order'))

    def test_json_native_output_and_replay_rejects_parameter_mismatch(self):
        row = generate(5, count=8)
        json.dumps(row, allow_nan=False)
        p = Parameters(**row['parameters'])
        state = initial(p)
        other = Parameters(scale_bias_units=1, order_units=p.order_units,
                           apples_stock_units=p.apples_stock_units,
                           scale_wobbles=p.scale_wobbles,
                           neighbor_will_mix=p.neighbor_will_mix)
        with self.assertRaises(StoryError):
            play_scene(other, state, 'market_order')


if __name__ == '__main__':
    unittest.main()
