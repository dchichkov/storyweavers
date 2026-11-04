from copy import deepcopy
from dataclasses import asdict
import unittest

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .world import Parameters, SCENES, generate, guard, initial, play_scene, replay, validate


OPTIONAL = {'tidepool_pause', 'fisher_pause', 'windbreak_pause'}


class SeasidePathTests(unittest.TestCase):
    def check_row(self, row):
        params = Parameters(**row['parameters'])
        episodes = replay(params, row['path'])
        self.assertEqual(episodes, row['episodes'])
        self.assertEqual(row['story'], '\n\n'.join(ep['text'] for ep in episodes))
        self.assertEqual(row['scene_count'], len(episodes))
        self.assertEqual(row['final_state'], episodes[-1]['after'])
        self.assertTrue(row['final_state']['story.ended'])
        self.assertTrue(row['final_state']['story.outcome'])
        state = initial(params)
        for scene_id, episode in zip(row['path'], episodes):
            self.assertEqual(scene_id, episode['id'])
            self.assertEqual(state, episode['before'])
            self.assertTrue(guard(scene_id, state))
            self.assertTrue(episode['events'])
            for event in episode['events']:
                for key, value in event['requires'].items():
                    self.assertEqual(state[key], value)
                self.assertTrue(event['changes'])
                for key, change in event['changes'].items():
                    self.assertEqual(state[key], change['before'])
                    self.assertNotEqual(change['before'], change['after'])
                    state[key] = deepcopy(change['after'])
                validate(state)
            self.assertEqual(state, episode['after'])
            words = len(episode['text'].split())
            self.assertGreaterEqual(words, 40, (scene_id, words))
            self.assertLessEqual(words, 70, (scene_id, words))

    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        self.assertEqual(len(set(SCENES)), len(SCENES))
        for seed in range(100):
            for count in (7, 8):
                with self.subTest(seed=seed, count=count):
                    row = generate(seed, count=count)
                    self.check_row(row)
                    self.assertEqual(row, generate(seed, count=count))
                    self.assertEqual(row['path'], [episode['id'] for episode in replay(
                        Parameters(**row['parameters']), row['path'])])

    def test_length_seven_omits_optional_scenes_and_eight_uses_one(self):
        for seed in range(20):
            seven = generate(seed, count=7)
            eight = generate(seed, count=8)
            self.assertFalse(OPTIONAL.intersection(seven['path']))
            self.assertEqual(len(OPTIONAL.intersection(eight['path'])), 1)

    def test_endings_follow_tide_counterfactual(self):
        common = dict(wind='calm', map_rotated=False, legend_faded=False)
        low = Parameters(tide='low', **common)
        rising = Parameters(tide='rising', **common)
        cove = generate(41, count=7, params=low)
        harbor = generate(41, count=7, params=rising)
        self.assertEqual(cove['path'][-1], 'ending_cove')
        self.assertEqual(harbor['path'][-1], 'ending_harbor')
        self.assertNotEqual(cove['final_state']['party.location'], harbor['final_state']['party.location'])
        self.assertIn('Crescent Cove', cove['final_state']['story.outcome'])
        self.assertIn('harbor awning', harbor['final_state']['story.outcome'])

    def test_map_orientation_and_legend_change_local_actions(self):
        rotated = Parameters(tide='low', map_rotated=True, legend_faded=False)
        upright = Parameters(tide='low', map_rotated=False, legend_faded=True)
        rotated_state = replay(rotated, ('borrow_map', 'follow_white_gull'))[-1]['after']
        upright_state = replay(upright, ('borrow_map', 'follow_white_gull'))[-1]['after']
        rotated_play = play_scene(rotated, rotated_state, 'compare_landmarks')
        faded_play = play_scene(upright, upright_state, 'compare_landmarks')
        rotated_actions = [event['action'] for event in rotated_play['events']]
        faded_actions = [event['action'] for event in faded_play['events']]
        self.assertIn('turn_map_north', rotated_actions)
        self.assertNotIn('turn_map_north', faded_actions)
        self.assertIn('trace_coastline_on_faded_map', faded_actions)
        self.assertEqual(rotated_play['after']['map.clue_source'], 'legend')
        self.assertEqual(faded_play['after']['map.clue_source'], 'coastline')

    def test_fisher_vignette_is_optional_but_its_clue_persists(self):
        params = Parameters(tide='rising')
        after_follow = replay(params, ('borrow_map', 'follow_white_gull'))[-1]['after']
        saved = deepcopy(after_follow)
        fisher = play_scene(params, after_follow, 'fisher_pause')
        self.assertEqual(after_follow, saved)
        self.assertTrue(fisher['after']['fisher.helped'])
        self.assertTrue(fisher['after']['fisher.clue'])
        compare = play_scene(params, fisher['after'], 'compare_landmarks')
        self.assertEqual(compare['after']['map.clue_source'], 'fisher')
        self.assertIn('use_fishers_landing_clue', [e['action'] for e in compare['events']])

    def test_wind_changes_picnic_actions_and_anchor(self):
        for wind, expected in (('calm', 'calm_air'), ('gusty', 'bench')):
            params = Parameters(tide='rising', wind=wind)
            path = ('borrow_map', 'follow_white_gull', 'compare_landmarks',
                    'choose_safe_route', 'reach_shelter')
            at_shelter = replay(params, path)[-1]['after']
            picnic = play_scene(params, at_shelter, 'picnic')
            actions = [event['action'] for event in picnic['events']]
            self.assertEqual(picnic['after']['blanket.anchor'], expected)
            self.assertIn('weight_blanket_against_gusts' in actions, wind == 'gusty')
            self.assertTrue(picnic['after']['party.picnic_done'])

    def test_object_location_and_borrowed_map_usefulness_continue(self):
        params = Parameters(tide='low')
        row = generate(9, count=8, params=params)
        final = row['final_state']
        self.assertEqual(final['map.holder'], 'aunt')
        self.assertEqual(final['map.location'], 'kiosk')
        self.assertFalse(final['map.borrowed'])
        self.assertTrue(final['map.corrected'])
        self.assertTrue(final['map.correction'])
        self.assertEqual(final['blanket.location'], 'older')
        if 'tidepool_pause' in row['path']:
            self.assertEqual(final['shell.holder'], 'younger')
        if 'fisher_pause' in row['path']:
            self.assertEqual(final['fisher.float'], 'returned')
            self.assertTrue(final['fisher.helped'])

    def test_failed_scenes_and_local_actions_do_not_mutate_callers(self):
        params = Parameters()
        state = initial(params)
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(params, state, 'picnic')
        self.assertEqual(state, saved)
        play = LocalPlay(state, actors=('older',), validate=validate)
        play_state, events = deepcopy(play.state), deepcopy(play.events)
        with self.assertRaises(StoryError):
            play.act('illegal_try', {'party.location': 'crescent_cove'}, **{'party.goal': 'sheltered_picnic'})
        self.assertEqual(play.state, play_state)
        self.assertEqual(play.events, events)

    def test_invalid_parameters_and_counts_are_rejected(self):
        for kwargs in (
            {'older_name': 'Niko'}, {'younger_name': 'bad name'},
            {'tide': 'high'}, {'wind': 'storm'}, {'map_rotated': 1},
            {'legend_faded': 'false'},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        for count in (True, 6, 9):
            with self.subTest(count=count), self.assertRaises(ValueError):
                generate(0, count=count)

    def test_unique_scene_ids_and_repeated_replay_are_rejected(self):
        self.assertEqual(len(SCENES), len(set(SCENES)))
        with self.assertRaises(StoryError):
            replay(Parameters(), ('borrow_map', 'borrow_map'))


if __name__ == '__main__':
    unittest.main()
