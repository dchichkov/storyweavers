from copy import deepcopy
from itertools import product
import unittest

from storyscenes.runtime import StoryError
from .world import Parameters, SCENES, generate, guard, initial, parameters, play_scene, replay, validate


OPTIONAL = {'fern_vignette', 'lace_vignette'}


class WoodlandWorldTests(unittest.TestCase):
    def audit_row(self, row):
        p = Parameters(**row['parameters'])
        episodes = replay(p, row['path'])
        self.assertEqual(episodes, row['episodes'])
        self.assertEqual(len(row['path']), row['scene_count'])
        self.assertEqual(len(set(row['path'])), row['scene_count'])
        self.assertEqual(row['story'], '\n\n'.join(ep['text'] for ep in episodes))
        state = initial(p)
        for ep in episodes:
            self.assertEqual(ep['before'], state)
            self.assertTrue(guard(ep['id'], state))
            self.assertTrue(40 <= len(ep['text'].split()) <= 70)
            self.assertTrue(ep['events'])
            for event in ep['events']:
                for key, value in event['requires'].items():
                    self.assertEqual(state[key], value)
                self.assertTrue(event['changes'])
                for key, change in event['changes'].items():
                    self.assertEqual(state[key], change['before'])
                    self.assertNotEqual(change['before'], change['after'])
                    state[key] = deepcopy(change['after'])
                validate(state)
            self.assertEqual(state, ep['after'])
        self.assertEqual(state, row['final_state'])
        self.assertTrue(state['story.ended'])
        self.assertTrue(state['story.outcome'])
        self.assertEqual(state['compass.holder'], 'Inez')
        self.assertTrue(state['compass.returned'])
        self.assertTrue(state['compass.useful_reported'])
        self.assertTrue(state['friend.included'])

    def test_both_lengths_over_one_hundred_seeds_and_replay(self):
        outcomes = set()
        for seed, count in product(range(100), (7, 8)):
            with self.subTest(seed=seed, count=count):
                row = generate(seed, count=count)
                self.audit_row(row)
                outcomes.add(row['final_state']['story.outcome'])
                optionals = OPTIONAL.intersection(row['path'])
                self.assertEqual(len(optionals), count - 6)
        self.assertEqual(outcomes, {
            'found_pool_together', 'missed_pool_found_frogs_together',
        })

    def test_parameters_are_seeded_and_validated(self):
        self.assertEqual(parameters(19), parameters(19))
        for kwargs in (
            {'compass_drift': True}, {'compass_drift': 2},
            {'shortcut_open': 1}, {'rain': 'yes'},
            {'puddle_depth': True}, {'puddle_depth': 4},
            {'pace_gap': 0}, {'pool_window': 29}, {'pool_window': 91},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        for count in (True, 6, 9):
            with self.subTest(count=count), self.assertRaises(ValueError):
                generate(count=count)

    def test_failed_scene_does_not_mutate_caller(self):
        p = Parameters()
        state = initial(p)
        saved = deepcopy(state)
        for scene_id in ('ridge_walk', 'puddle_cross', 'ending_pool', 'not_a_scene'):
            with self.subTest(scene=scene_id), self.assertRaises(StoryError):
                play_scene(p, state, scene_id)
            self.assertEqual(state, saved)

    def test_optional_vignettes_are_only_enacted_when_selected(self):
        for count in (7, 8):
            row = generate(31, count=count)
            chosen = OPTIONAL.intersection(row['path'])
            self.assertEqual(len(chosen), count - 6)
            state = initial(Parameters(**row['parameters']))
            for ep in row['episodes']:
                state = ep['after']
            self.assertEqual(state['trail.fern_seen'], 'fern_vignette' in chosen)
            self.assertEqual(state['friend.heel_supported'], 'lace_vignette' in chosen)
        base = initial(Parameters(compass_drift=1))
        after_borrow = play_scene(Parameters(compass_drift=1), base, 'borrow_compass')['after']
        self.assertFalse(after_borrow['compass.calibrated'])
        after_fern = play_scene(Parameters(compass_drift=1), after_borrow, 'fern_vignette')['after']
        self.assertTrue(after_fern['compass.calibrated'])
        self.assertEqual(base['compass.holder'], 'Inez')

    def test_compass_custody_and_friends_locations_remain_continuous(self):
        row = generate(4, count=8)
        state = initial(Parameters(**row['parameters']))
        self.assertEqual(state['compass.holder'], 'Inez')
        for ep in row['episodes']:
            self.assertEqual(ep['before'], state)
            self.assertEqual(state['lead.location'], state['friend.location'])
            if state['compass.borrowed'] and not state['compass.returned']:
                self.assertEqual(state['compass.holder'], 'Nia')
            state = ep['after']
        self.assertEqual(state['compass.holder'], 'Inez')
        self.assertEqual(state['compass.owner'], 'Inez')
        self.assertEqual(state['story.location'], 'trailhead')

    def test_paired_counterfactuals_change_route_and_ending(self):
        base = dict(compass_drift=0, shortcut_open=True, rain=False,
                    puddle_depth=1, pace_gap=1, pool_window=70)
        fast = generate(9, count=8, params=Parameters(**base))
        rainy = generate(9, count=8, params=Parameters(**(base | {'rain': True})))
        self.assertEqual(fast['final_state']['story.outcome'], 'found_pool_together')
        self.assertEqual(rainy['final_state']['story.outcome'], 'missed_pool_found_frogs_together')
        self.assertIn('shortcut', fast['final_state']['story.route'])
        late = generate(9, count=8, params=Parameters(**(base | {'pool_window': 30})))
        self.assertEqual(late['final_state']['story.outcome'], 'missed_pool_found_frogs_together')
        ridge = generate(9, count=8, params=Parameters(**(base | {'shortcut_open': False})))
        self.assertEqual(ridge['final_state']['story.route'], 'ridge')

    def test_endings_are_guarded_by_enacted_discovery(self):
        p = Parameters(rain=True)
        state = initial(p)
        for scene_id in ('borrow_compass', 'fern_vignette', 'lace_vignette',
                         'route_choice', 'puddle_cross', 'ridge_walk'):
            state = play_scene(p, state, scene_id)['after']
        self.assertFalse(guard('ending_pool', state))
        with self.assertRaises(StoryError):
            play_scene(p, state, 'ending_pool')
        state = play_scene(p, state, 'discovery')['after']
        self.assertTrue(guard('ending_shelter', state))
        self.assertFalse(guard('ending_pool', state))
        validate(state)

    def test_scene_ids_are_unique_and_generation_is_json_native(self):
        self.assertEqual(len(SCENES), len(set(SCENES)))
        row = generate(0, count=7)
        self.assertEqual(row['scene_count'], len(row['episodes']))
        self.assertEqual(row['path'], [ep['id'] for ep in row['episodes']])
        self.assertGreater(row['search_attempts'], 0)
        self.assertEqual(row, generate(0, count=7))


if __name__ == '__main__':
    unittest.main()
