from copy import deepcopy
from itertools import product
import json
import unittest

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .world import Parameters, SCENES, generate, guard, initial, parameters, play_scene, replay, validate


def episode_row(episode):
    return {'id': episode.id, 'before': episode.before, 'after': episode.after,
            'events': list(episode.events), 'text': episode.text}


class KiteWorldTests(unittest.TestCase):
    def check_row(self, row):
        self.assertEqual(len(row['path']), row['scene_count'])
        self.assertEqual(len(set(row['path'])), len(row['path']))
        self.assertEqual(len(row['episodes']), row['scene_count'])
        self.assertEqual(row['story'], '\n\n'.join(e['text'] for e in row['episodes']))
        self.assertTrue(row['final_state']['story.ended'])
        self.assertTrue(row['final_state']['story.outcome'])
        self.assertEqual(row['path'], [e['id'] for e in row['episodes']])
        state = initial(Parameters(**row['parameters']))
        for episode in row['episodes']:
            self.assertEqual(episode['before'], state)
            self.assertTrue(guard(episode['id'], state))
            self.assertTrue(episode['events'])
            for event in episode['events']:
                for key, value in event['requires'].items():
                    self.assertIn(key, state)
                    self.assertEqual(state[key], value)
                self.assertTrue(event['changes'])
                for key, change in event['changes'].items():
                    self.assertIn(key, state)
                    self.assertEqual(state[key], change['before'])
                    self.assertNotEqual(change['before'], change['after'])
                    state[key] = change['after']
                validate(state)
            self.assertEqual(state, episode['after'])
            self.assertGreaterEqual(len(episode['text'].split()), 40)
            self.assertLessEqual(len(episode['text'].split()), 70)
        self.assertEqual(state, row['final_state'])
        replayed = replay(Parameters(**row['parameters']), row['path'])
        self.assertEqual([episode_row(e) for e in replayed], row['episodes'])
        json.dumps(row, allow_nan=False)

    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        for seed, count in product(range(100), (7, 8)):
            with self.subTest(seed=seed, count=count):
                self.check_row(generate(seed, count=count))

    def test_seeded_parameters_and_unique_scene_ids(self):
        self.assertEqual(parameters(91), parameters(91))
        self.assertEqual(len(SCENES), len(set(SCENES)))
        self.assertEqual(set(SCENES), {
            'notice', 'borrow_can', 'read_labels', 'talk_to_rosa', 'fill_and_water',
            'make_shade', 'return_can', 'ending_stable', 'ending_cuttings',
        })

    def test_parameter_types_ranges_and_keyword_only_constructor(self):
        invalid = (
            {'heat': 'warm'}, {'can_leak': 1}, {'shade_cloth': 'false'},
            {'water_units': True}, {'water_units': 0}, {'water_units': 4},
            {'soil_dryness': False}, {'soil_dryness': 3},
        )
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ValueError):
                Parameters(**values)
        with self.assertRaises(TypeError):
            Parameters('hot')
        for count in (True, 6, 9):
            with self.subTest(count=count), self.assertRaises(ValueError):
                generate(0, count=count)
        with self.assertRaises(ValueError):
            generate(True)

    def test_illegal_scenes_and_local_actions_do_not_mutate_callers(self):
        p = Parameters()
        state = initial(p)
        original = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(p, state, 'fill_and_water')
        self.assertEqual(state, original)
        local = LocalPlay(state, actors=('Mina',), validate=validate)
        local_before = deepcopy(local.state)
        events_before = deepcopy(local.events)
        with self.assertRaises(StoryError):
            local.act('not_allowed', {'can.holder': 'Mina'}, **{'story.goal': 'invented'})
        self.assertEqual(local.state, local_before)
        self.assertEqual(local.events, events_before)

    def test_optional_vignettes_are_enacted_only_when_selected(self):
        p = Parameters(heat='mild', can_leak=False, water_units=2,
                       soil_dryness=1, shade_cloth=True)
        rosa_path = ('notice', 'borrow_can', 'talk_to_rosa', 'fill_and_water',
                     'make_shade', 'return_can', 'ending_stable')
        rosa = replay(p, rosa_path)
        self.assertFalse(rosa[1].after['labels.read'])
        self.assertTrue(rosa[2].after['neighbor.advice'])
        self.assertFalse(rosa[2].after['band.available'])
        labels_path = ('notice', 'borrow_can', 'read_labels', 'fill_and_water',
                       'make_shade', 'return_can', 'ending_cuttings')
        labels = replay(p, labels_path)
        self.assertTrue(labels[2].after['labels.read'])
        self.assertFalse(labels[2].after['neighbor.visited'])
        self.assertTrue(labels[2].after['band.available'])
        both_path = ('notice', 'borrow_can', 'read_labels', 'talk_to_rosa',
                     'fill_and_water', 'make_shade', 'return_can', 'ending_stable')
        both = replay(p, both_path)
        self.assertEqual(len(both), 8)
        self.assertTrue(both[3].after['neighbor.advice'])

    def test_borrowed_can_water_conservation_and_location_continuity(self):
        p = Parameters(heat='mild', can_leak=True, water_units=3,
                       soil_dryness=1, shade_cloth=True)
        path = ('notice', 'borrow_can', 'read_labels', 'talk_to_rosa',
                'fill_and_water', 'make_shade', 'return_can', 'ending_stable')
        episodes = replay(p, path)
        final = episodes[-1].after
        self.assertEqual(final['can.owner'], 'Ivo')
        self.assertEqual(final['can.holder'], 'Ivo')
        self.assertEqual(final['can.location'], 'rack')
        self.assertTrue(final['can.borrowed'])
        self.assertTrue(final['can.returned'])
        self.assertTrue(final['can.rinsed'])
        self.assertEqual(final['tank.units'] + final['can.water'] + final['water.spilled']
                         + final['seedling.watered_units'], final['water.original'])
        self.assertEqual(final['screen.location'], 'over_tray')
        self.assertEqual(final['seedling.location'], 'propagation_bench')
        self.assertFalse(final['band.used'])
        self.assertEqual(final['band.location'], 'label_clip')

    def test_paired_counterfactuals_change_the_ending(self):
        path_to_return = ('notice', 'borrow_can', 'talk_to_rosa', 'fill_and_water',
                          'make_shade', 'return_can')
        adequate = Parameters(heat='mild', can_leak=False, water_units=2,
                              soil_dryness=1, shade_cloth=True)
        scarce = Parameters(heat='hot', can_leak=True, water_units=1,
                            soil_dryness=2, shade_cloth=True)
        good = replay(adequate, path_to_return)
        poor = replay(scarce, path_to_return)
        self.assertEqual(good[-1].after['seedling.status'], 'stable')
        self.assertEqual(poor[-1].after['seedling.status'], 'sheltered')
        self.assertTrue(guard('ending_stable', good[-1].after))
        self.assertFalse(guard('ending_stable', poor[-1].after))
        good_final = play_scene(adequate, good[-1].after, 'ending_stable')
        poor_final = play_scene(scarce, poor[-1].after, 'ending_cuttings')
        self.assertEqual(good_final.after['story.outcome'], 'seedlings_stable')
        self.assertEqual(poor_final.after['story.outcome'], 'cuttings_rooted')
        self.assertTrue(poor_final.after['cuttings.rooted'])

    def test_scene_guard_and_parameters_change_local_actions(self):
        p = Parameters(heat='mild', can_leak=True, water_units=3,
                       soil_dryness=1, shade_cloth=True)
        prefix = ('notice', 'borrow_can', 'read_labels')
        state = replay(p, prefix)[-1].after
        water = play_scene(p, state, 'fill_and_water')
        actions = [event['action'] for event in water.events]
        self.assertIn('bind_split_seam_with_label_band', actions)
        self.assertEqual(water.after['water.spilled'], 0)
        no_label = replay(p, ('notice', 'borrow_can'))[-1].after
        other_water = play_scene(p, no_label, 'fill_and_water')
        self.assertNotIn('bind_split_seam_with_label_band',
                         [event['action'] for event in other_water.events])
        self.assertEqual(other_water.after['water.spilled'], 1)
        self.assertFalse(guard('make_shade', state))

    def test_deterministic_generation_and_replay_rejects_repeated_scene(self):
        first = generate(31, count=8)
        self.assertEqual(first, generate(31, count=8))
        with self.assertRaises(StoryError):
            replay(Parameters(), ('notice', 'notice'))


if __name__ == '__main__':
    unittest.main()
