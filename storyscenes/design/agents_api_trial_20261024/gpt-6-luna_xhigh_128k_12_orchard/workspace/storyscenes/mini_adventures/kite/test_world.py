from copy import deepcopy
from dataclasses import asdict
import json
import unittest

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .world import Parameters, SCENES, _episode_json, generate, guard, initial, play_scene, replay, validate


class OrchardWorldTests(unittest.TestCase):
    def run_path(self, params, path):
        state = initial(params)
        episodes = []
        for scene_id in path:
            self.assertTrue(guard(scene_id, state))
            episode = play_scene(params, state, scene_id)
            episodes.append(episode)
            state = episode.after
        return state, episodes

    def check_row(self, row):
        params = Parameters(**row['parameters'])
        episodes = replay(params, row['path'])
        self.assertEqual([_episode_json(episode) for episode in episodes], row['episodes'])
        self.assertEqual(episodes[-1].after, row['final_state'])
        self.assertEqual('\n\n'.join(episode.text for episode in episodes), row['story'])
        self.assertEqual(len(episodes), row['scene_count'])
        self.assertTrue(row['final_state']['story.ended'])
        self.assertTrue(row['final_state']['story.outcome'])
        self.assertEqual(len(row['path']), len(set(row['path'])))

        state = initial(params)
        for episode in episodes:
            self.assertEqual(episode.before, state)
            self.assertTrue(guard(episode.id, state))
            self.assertTrue(episode.events)
            self.assertGreaterEqual(len(episode.text.split()), 40)
            self.assertLessEqual(len(episode.text.split()), 70)
            for event in episode.events:
                self.assertTrue(event['action'])
                for key, value in event['requires'].items():
                    self.assertEqual(state[key], value)
                self.assertTrue(event['changes'])
                for key, change in event['changes'].items():
                    self.assertEqual(state[key], change['before'])
                    self.assertNotEqual(change['before'], change['after'])
                    state[key] = deepcopy(change['after'])
                validate(state)
            self.assertEqual(state, episode.after)
        json.dumps(row)

    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        self.assertEqual(len(SCENES), len(set(SCENES)))
        for seed in range(100):
            for count in (7, 8):
                with self.subTest(seed=seed, count=count):
                    row = generate(seed, count=count)
                    self.check_row(row)
                    self.assertEqual(row, generate(seed, count=count))

    def test_invalid_parameters_and_count_types(self):
        for kwargs in (
            {'reach_cm': True}, {'reach_cm': 99}, {'windy': 1},
            {'low_ripe': 0}, {'low_ripe': True}, {'windfalls': 4},
            {'basket_handle': 'broken'}, {'crate_level': 0},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        for count in (True, 6, 9):
            with self.subTest(count=count), self.assertRaises(ValueError):
                generate(count=count)
        with self.assertRaises(ValueError):
            Parameters(160)

    def test_illegal_scenes_and_failed_local_actions_do_not_mutate_callers(self):
        params = Parameters()
        state = initial(params)
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(params, state, 'survey_tree')
        self.assertEqual(state, saved)

        play = LocalPlay(state, actors=('mira', 'theo'), validate=validate)
        local_state, local_events = deepcopy(play.state), deepcopy(play.events)
        with self.assertRaises(StoryError):
            play.act('not_a_borrow', requires={'basket.owner': 'someone_else'}, **{'basket.owner': 'friends'})
        self.assertEqual(play.state, local_state)
        self.assertEqual(play.events, local_events)
        with self.assertRaises(StoryError):
            play.act('no_op', **{'story.location': 'shed_gate'})
        self.assertEqual(play.state, local_state)
        self.assertEqual(play.events, local_events)

    def test_optional_vignettes_are_optional_and_do_not_run_offstage(self):
        seven = generate(17, count=7)
        eight = generate(17, count=8)
        optional = {'vignette_crate', 'vignette_memory'}
        self.assertEqual(len(optional.intersection(seven['path'])), 1)
        self.assertEqual(optional.intersection(eight['path']), optional)
        for row in (seven, eight):
            final = row['final_state']
            self.assertEqual(final['friends.memory'], 'vignette_memory' in row['path'])
            self.assertEqual(final['crate.tested'], 'vignette_crate' in row['path'])
            if 'vignette_crate' not in row['path']:
                self.assertEqual(final['picnic.surface'], 'cloth')

    def test_object_location_continuity_and_basket_use(self):
        params = Parameters(reach_cm=160, windy=False, low_ripe=3, windfalls=1, basket_handle='sound')
        row = generate(6, count=8, params=params)
        state = initial(params)
        for episode in replay(params, row['path']):
            state = episode.after
            if state['basket.borrowed'] and not state['basket.returned']:
                self.assertEqual(state['basket.location'], state['story.location'])
        self.assertTrue(state['basket.returned'])
        self.assertEqual(state['basket.owner'], 'Vale')
        self.assertEqual(state['basket.location'], 'shed')
        self.assertTrue(state['basket.cleaned'])
        self.assertTrue(state['snack.done'])
        self.assertGreater(state['snack.pear_halves'], 0)
        self.assertFalse(state['tree.damaged'])

    def test_paired_counterfactuals_reach_handle_crate_and_wind(self):
        path = ('borrow_basket', 'survey_tree', 'choose_harvest', 'pick_fruit')
        high = Parameters(reach_cm=160, windy=False, low_ripe=3, windfalls=1, basket_handle='sound')
        short = Parameters(reach_cm=120, windy=False, low_ripe=3, windfalls=1, basket_handle='sound')
        high_state, _ = self.run_path(high, path)
        short_state, _ = self.run_path(short, path)
        self.assertEqual(high_state['harvest.source'], 'low_branch')
        self.assertEqual(short_state['harvest.source'], 'windfalls')
        self.assertNotEqual(high_state['harvest.count'], short_state['harvest.count'])

        frayed = Parameters(reach_cm=160, windy=False, low_ripe=3, windfalls=1, basket_handle='frayed')
        frayed_state, _ = self.run_path(frayed, path)
        self.assertEqual(frayed_state['harvest.count'], 1)
        self.assertGreater(high_state['harvest.count'], frayed_state['harvest.count'])

        stable = Parameters(crate_level=True)
        unstable = Parameters(crate_level=False)
        stable_state, _ = self.run_path(stable, ('borrow_basket', 'vignette_crate'))
        unstable_state, _ = self.run_path(unstable, ('borrow_basket', 'vignette_crate'))
        self.assertEqual(stable_state['picnic.surface'], 'crate')
        self.assertEqual(unstable_state['picnic.surface'], 'cloth')

        breezy = Parameters(reach_cm=160, windy=True, low_ripe=3, windfalls=2, basket_handle='sound')
        breezy_state, _ = self.run_path(breezy, path)
        self.assertEqual(breezy_state['harvest.source'], 'windfalls')

    def test_both_endings_have_explicit_parameter_recipes(self):
        full = Parameters(reach_cm=160, windy=False, low_ripe=3, windfalls=1,
                          basket_handle='sound', crate_level=True)
        small = Parameters(reach_cm=120, windy=True, low_ripe=3, windfalls=1,
                           basket_handle='frayed', crate_level=False)
        full_row = generate(0, count=7, params=full)
        small_row = generate(0, count=8, params=small)
        self.assertEqual(full_row['path'][-1], 'ending_full')
        self.assertEqual(full_row['final_state']['story.outcome'], 'shared_harvest')
        self.assertEqual(small_row['path'][-1], 'ending_small')
        self.assertEqual(small_row['final_state']['story.outcome'], 'small_shared_snack')

    def test_replay_rejects_incomplete_repeated_or_incompatible_paths(self):
        params = Parameters()
        for path in (('borrow_basket',), ('borrow_basket',) * 7,
                     ('survey_tree', 'borrow_basket', 'survey_tree', 'choose_harvest', 'pick_fruit', 'share_snack', 'ending_full')):
            with self.subTest(path=path), self.assertRaises(StoryError):
                replay(params, path)


if __name__ == '__main__':
    unittest.main()
