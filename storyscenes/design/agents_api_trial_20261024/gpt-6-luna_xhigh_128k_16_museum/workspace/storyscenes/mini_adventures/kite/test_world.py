from copy import deepcopy
from dataclasses import asdict
from itertools import product
import json
import unittest

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .world import (
    SCENES, Parameters, generate, guard, initial, parameters, play_scene, replay, validate,
)


class MuseumShadowTests(unittest.TestCase):
    def route(self, params, path):
        state = initial(params)
        episodes = []
        for scene_id in path:
            episode = play_scene(params, state, scene_id)
            episodes.append(episode)
            state = episode.after
        return state, tuple(episodes)

    def row_episodes(self, episodes):
        return [{
            'id': episode.id, 'before': episode.before, 'after': episode.after,
            'events': list(episode.events), 'text': episode.text,
        } for episode in episodes]

    def assert_row_replays(self, row):
        params = Parameters(**row['parameters'])
        episodes = replay(params, row['path'])
        self.assertEqual(self.row_episodes(episodes), row['episodes'])
        self.assertEqual(episodes[-1].after, row['final_state'])
        self.assertEqual('\n\n'.join(episode.text for episode in episodes), row['story'])
        self.assertEqual(len(episodes), row['scene_count'])
        self.assertTrue(row['final_state']['story.ended'])
        self.assertTrue(row['final_state']['story.outcome'])
        self.assertEqual(len(row['path']), len(set(row['path'])))
        self.assertTrue(all(40 <= len(episode.text.split()) <= 70 for episode in episodes))

        state = initial(params)
        for episode in episodes:
            self.assertEqual(episode.before, state)
            self.assertTrue(guard(episode.id, state))
            self.assertTrue(episode.events)
            for event in episode.events:
                self.assertTrue(event['action'])
                self.assertTrue(event['changes'])
                for key, value in event['requires'].items():
                    self.assertIn(key, state)
                    self.assertEqual(state[key], value)
                for key, change in event['changes'].items():
                    self.assertEqual(state[key], change['before'])
                    self.assertNotEqual(change['before'], change['after'])
                    state[key] = change['after']
                validate(state)
            self.assertEqual(state, episode.after)
        json.dumps(row)

    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        endings = set()
        for seed, count in product(range(100), (7, 8)):
            with self.subTest(seed=seed, count=count):
                row = generate(seed, count=count)
                self.assert_row_replays(row)
                endings.add(row['final_state']['story.outcome'])
                selected = set(row['path'])
                vignettes = selected & {'vignette_visitor', 'vignette_sketch'}
                self.assertEqual(len(vignettes), count - 6)
        self.assertEqual(endings, {'accurate_demonstration', 'corrected_label', 'honest_inconclusive'})

    def test_scene_ids_and_local_prose_lengths(self):
        self.assertEqual(len(SCENES), len(set(SCENES)))
        self.assertEqual(len(generate(0, count=7)['path']), 7)
        self.assertEqual(len(generate(0, count=8)['path']), 8)

    def test_parameters_reject_wrong_types_and_ranges(self):
        for kwargs in (
            {'label_target': 'middle'}, {'room_ambient': 1}, {'torch_charge': True},
            {'torch_charge': 0}, {'screen_distance_cm': 161},
            {'screen_distance_cm': True}, {'figure_kind': 'glass'},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        for count in (True, 6, 9):
            with self.assertRaises(ValueError):
                generate(count=count)
        with self.assertRaises(ValueError):
            generate(seed=True)
        with self.assertRaises(ValueError):
            parameters(False)

    def test_illegal_scenes_and_actions_do_not_mutate_caller(self):
        params = Parameters()
        state = initial(params)
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(params, state, 'retest')
        self.assertEqual(state, saved)

        play = LocalPlay(state, actors=('Mara', 'Tavi'), validate=validate)
        saved_play = deepcopy(play.state)
        saved_events = deepcopy(play.events)
        with self.assertRaises(StoryError):
            play.act('try_to_switch_on_unborrowed_torch', {'torch.owner': 'children'},
                     **{'torch.on': True})
        self.assertEqual(play.state, saved_play)
        self.assertEqual(play.events, saved_events)
        self.assertEqual(state, saved)

    def test_optional_vignettes_have_only_enacted_effects(self):
        params = Parameters()
        before, _ = self.route(params, ('borrow_torch', 'first_demo', 'read_label'))
        visitor = play_scene(params, before, 'vignette_visitor')
        changed = {key for key in before if before[key] != visitor.after[key]}
        self.assertEqual(changed, {'visitor.present', 'visitor.location', 'visitor.reassured'})
        sketch = play_scene(params, before, 'vignette_sketch')
        changed = {key for key in before if before[key] != sketch.after[key]}
        self.assertEqual(changed, {'sketch.made', 'sketch.location', 'sketch.first_observation',
                                   'sketch.first_magnification'})
        row7, row8 = generate(17, count=7), generate(17, count=8)
        self.assertEqual(len(set(row7['path']) & {'vignette_visitor', 'vignette_sketch'}), 1)
        self.assertEqual(set(row8['path']) & {'vignette_visitor', 'vignette_sketch'},
                         {'vignette_visitor', 'vignette_sketch'})
        final7 = row7['final_state']
        omitted = {'visitor.present': 'vignette_visitor' not in row7['path'],
                   'sketch.made': 'vignette_sketch' not in row7['path']}
        for key, expected in omitted.items():
            if expected:
                self.assertFalse(final7[key])

    def test_borrowed_object_and_locations_remain_continuous(self):
        params = Parameters(label_target='near_screen', room_ambient=True, torch_charge=3,
                            screen_distance_cm=140, figure_kind='card')
        row = generate(4, count=8, params=params)
        state = initial(params)
        for episode in replay(params, row['path']):
            self.assertEqual(episode.before, state)
            for event in episode.events:
                for key, change in event['changes'].items():
                    self.assertEqual(state[key], change['before'])
                    state[key] = change['after']
            self.assertEqual(state, episode.after)
            validate(state)
        self.assertEqual(state['torch.owner'], 'museum')
        self.assertEqual(state['torch.location'], 'return_desk')
        self.assertFalse(state['torch.on'])
        self.assertTrue(state['torch.borrowed'])
        self.assertEqual(state['torch.last_use'], 'paired comparison')
        self.assertEqual(state['figure.location'], 'activity_table')
        self.assertEqual(state['screen.location'], 'north_wall')

    def test_paired_counterfactuals_change_inference_and_physical_trace(self):
        common = dict(room_ambient=False, torch_charge=3, screen_distance_cm=120, figure_kind='card')
        good, _ = self.route(Parameters(label_target='near_torch', **common),
                             ('borrow_torch', 'first_demo', 'read_label', 'inspect_setup', 'retest', 'ending_show'))
        corrected, _ = self.route(Parameters(label_target='near_screen', **common),
                                  ('borrow_torch', 'first_demo', 'read_label', 'inspect_setup', 'retest',
                                   'ending_correct_label'))
        self.assertEqual(good['story.outcome'], 'accurate_demonstration')
        self.assertEqual(corrected['story.outcome'], 'corrected_label')
        self.assertTrue(corrected['label.corrected'])
        self.assertFalse(good['label.corrected'])

        bright = Parameters(label_target='near_torch', room_ambient=True, torch_charge=3,
                            screen_distance_cm=120, figure_kind='card')
        dim = Parameters(label_target='near_torch', room_ambient=False, torch_charge=3,
                         screen_distance_cm=120, figure_kind='card')
        _, bright_eps = self.route(bright, ('borrow_torch', 'first_demo'))
        _, dim_eps = self.route(dim, ('borrow_torch', 'first_demo'))
        self.assertNotEqual(bright_eps[-1].after['shadow.first_observation'],
                            dim_eps[-1].after['shadow.first_observation'])

        short = Parameters(label_target='near_torch', room_ambient=False, torch_charge=3,
                           screen_distance_cm=80, figure_kind='card')
        long = Parameters(label_target='near_torch', room_ambient=False, torch_charge=3,
                          screen_distance_cm=160, figure_kind='card')
        _, short_eps = self.route(short, ('borrow_torch', 'first_demo'))
        _, long_eps = self.route(long, ('borrow_torch', 'first_demo'))
        self.assertNotEqual(short_eps[-1].after['shadow.first_magnification'],
                            long_eps[-1].after['shadow.first_magnification'])

    def test_low_power_has_an_honest_complete_ending(self):
        params = Parameters(label_target='near_torch', room_ambient=False, torch_charge=1,
                            screen_distance_cm=120, figure_kind='card')
        state, episodes = self.route(params, ('borrow_torch', 'first_demo', 'read_label', 'inspect_setup',
                                              'retest', 'ending_honest'))
        self.assertEqual(state['story.outcome'], 'honest_inconclusive')
        self.assertTrue(state['exhibit.note_posted'])
        self.assertIn('inconclusive', state['label.note'])
        self.assertEqual(state['torch.location'], 'return_desk')
        self.assertEqual(len(episodes), 6)
        with self.assertRaises(StoryError):
            play_scene(params, episodes[-2].after, 'ending_show')

    def test_replay_rejects_repeats_and_wrong_parameter_world(self):
        params = Parameters()
        with self.assertRaises(StoryError):
            replay(params, ('borrow_torch', 'borrow_torch'))
        state = initial(params)
        changed = Parameters(torch_charge=2)
        with self.assertRaises(StoryError):
            play_scene(changed, state, 'borrow_torch')


if __name__ == '__main__':
    unittest.main()
