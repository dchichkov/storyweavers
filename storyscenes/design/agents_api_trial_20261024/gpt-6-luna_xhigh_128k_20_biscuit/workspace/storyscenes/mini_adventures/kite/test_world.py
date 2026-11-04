from copy import deepcopy
from dataclasses import asdict, replace
import json
import subprocess
import sys
import unittest

from storyscenes.runtime import StoryError
from storyscenes.mini_adventures.kite.world import (
    Parameters, SCENES, generate, guard, initial, play_scene, replay, validate,
)


class KitchenAdventureTests(unittest.TestCase):
    def assert_row_replays(self, row):
        params = Parameters(**row['parameters'])
        episodes = replay(params, row['path'])
        self.assertEqual([asdict(e) | {'events': list(e.events)} for e in episodes], row['episodes'])
        self.assertEqual((chr(10) * 2).join(e.text for e in episodes), row['story'])
        self.assertEqual(episodes[-1].after, row['final_state'])
        self.assertTrue(row['final_state']['story.ended'])
        self.assertTrue(row['final_state']['story.outcome'])
        self.assertEqual(len(row['path']), row['scene_count'])
        self.assertEqual(len(row['path']), len(set(row['path'])))
        state = initial(params)
        for episode in episodes:
            self.assertEqual(state, episode.before)
            self.assertTrue(guard(episode.id, state))
            self.assertTrue(40 <= len(episode.text.split()) <= 70)
            self.assertTrue(episode.events)
            for event in episode.events:
                self.assertTrue(event['changes'])
                for key, value in event['requires'].items():
                    self.assertEqual(state[key], value)
                for key, values in event['changes'].items():
                    self.assertEqual(state[key], values['before'])
                    self.assertNotEqual(values['before'], values['after'])
                    state[key] = values['after']
                validate(state)
            self.assertEqual(state, episode.after)
        json.dumps(row, ensure_ascii=False)

    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        for count in (7, 8):
            for seed in range(100):
                with self.subTest(count=count, seed=seed):
                    row = generate(seed, count=count)
                    self.assert_row_replays(row)
                    self.assertEqual(len(row['path']), count)
                    self.assertEqual(set(row['path']) & {'ending_gift', 'ending_note'},
                                     {row['path'][-1]})

    def test_optional_vignettes_are_selected_not_silently_applied(self):
        for seed in range(20):
            seven = generate(seed, count=7)
            eight = generate(seed, count=8)
            seven_vignettes = set(seven['path']) & {'flour_memory', 'timer_song'}
            eight_vignettes = set(eight['path']) & {'flour_memory', 'timer_song'}
            self.assertFalse(seven_vignettes)
            self.assertEqual(len(eight_vignettes), 1)
            state7 = seven['final_state']
            if 'flour_memory' not in seven['path']:
                self.assertFalse(state7['memory.shared'])
            if 'timer_song' not in seven['path']:
                self.assertFalse(state7['kitchen.timer_song'])

    def test_parameter_validation_is_strict(self):
        for kwargs in (
            {'dough_grams': True}, {'dough_grams': 69}, {'dough_grams': 181},
            {'dough_chilled': 1}, {'flour_available': 'yes'},
            {'cutters_tacky': 0}, {'oven_preheated': None}, {'share_plan': 'mostly'},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        with self.assertRaises(TypeError):
            Parameters(100)
        for count in (True, 6, 9):
            with self.assertRaises(ValueError):
                generate(count=count)

    def test_illegal_scenes_and_actions_do_not_mutate_caller(self):
        params = Parameters()
        state = initial(params)
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(params, state, 'bake')
        self.assertEqual(state, saved)
        first = play_scene(params, state, 'start')
        self.assertEqual(state, saved)
        local = __import__('storyscenes.mini_adventures.local_play', fromlist=['LocalPlay']).LocalPlay(
            initial(params), actors=('mara', 'eli'), validate=validate)
        before_state, before_events = deepcopy(local.state), deepcopy(local.events)
        with self.assertRaises(StoryError):
            local.act('illegal', requires={'dough.prepared': True}, **{'dough.grams': 90})
        self.assertEqual(local.state, before_state)
        self.assertEqual(local.events, before_events)
        self.assertEqual(first.before, saved)

    def test_cutters_and_dough_have_continuous_physical_state(self):
        params = Parameters(dough_grams=140, dough_chilled=True, flour_available=True,
                           cutters_tacky=True, oven_preheated=False, share_plan='equal')
        row = generate(13, count=7, params=params)
        state = initial(params)
        for episode in replay(params, row['path']):
            if episode.id == 'borrow_cutters':
                self.assertEqual(episode.after['cutters.carrier'], 'siblings')
                self.assertEqual(episode.after['cutters.location'], 'family_counter')
                self.assertTrue(episode.after['cutters.clean'])
            if episode.id == 'wrap_box':
                self.assertTrue(episode.after['cutters.ready'])
                self.assertEqual(episode.after['cutters.carrier'], 'siblings')
            state = episode.after
        final = row['final_state']
        self.assertEqual(final['cutters.owner'], 'Mrs Flores')
        self.assertEqual(final['cutters.carrier'], 'Mrs Flores')
        self.assertEqual(final['cutters.location'], 'neighbor_counter')
        self.assertTrue(final['cutters.returned'] and final['neighbor.cutter_used'])
        self.assertEqual(final['dough.for_gift'] + final['dough.for_home'], final['dough.grams'])

    def test_paired_counterfactuals_change_both_choice_and_ending(self):
        good = Parameters(dough_grams=140, dough_chilled=True, flour_available=True,
                          cutters_tacky=False, oven_preheated=True, share_plan='gift_first')
        bad = replace(good, dough_grams=80, dough_chilled=False, flour_available=False,
                      share_plan='equal')
        successful = generate(4, count=7, params=good)
        fallback = generate(4, count=7, params=bad)
        self.assertEqual(successful['path'][-1], 'ending_gift')
        self.assertEqual(fallback['path'][-1], 'ending_note')
        self.assertNotEqual(successful['final_state']['story.outcome'], fallback['final_state']['story.outcome'])
        equal = generate(4, count=7, params=replace(good, share_plan='equal'))
        self.assertNotEqual(successful['final_state']['dough.for_gift'], equal['final_state']['dough.for_gift'])
        self.assertEqual(successful['path'][:-1], equal['path'][:-1])

    def test_vignette_effects_are_persistent_and_path_specific(self):
        params = Parameters()
        base_path = ('start', 'borrow_cutters', 'prepare_dough', 'divide_dough', 'bake', 'wrap_box', 'ending_gift')
        base = replay(params, base_path)[-1].after
        with_memory = replay(params, ('start', 'borrow_cutters', 'flour_memory', 'prepare_dough',
                                      'divide_dough', 'bake', 'wrap_box', 'ending_gift'))[-1].after
        self.assertFalse(base['memory.shared'])
        self.assertTrue(with_memory['memory.shared'])
        self.assertGreater(with_memory['siblings.trust'], base['siblings.trust'])
        with_song = replay(params, ('start', 'borrow_cutters', 'prepare_dough', 'timer_song',
                                    'divide_dough', 'bake', 'wrap_box', 'ending_gift'))[-1].after
        self.assertTrue(with_song['kitchen.timer_song'])
        self.assertFalse(base['kitchen.timer_song'])

    def test_seeded_parameters_and_cli(self):
        self.assertEqual(Parameters(**asdict(__import__(
            'storyscenes.mini_adventures.kite.world', fromlist=['parameters']).parameters(9))),
            __import__('storyscenes.mini_adventures.kite.world', fromlist=['parameters']).parameters(9))
        result = subprocess.run(
            [sys.executable, '-m', 'storyscenes.mini_adventures.kite.world', '--seed', '0', '--scenes', '8'],
            capture_output=True, text=True, check=True)
        self.assertTrue(result.stdout.strip())


if __name__ == '__main__':
    unittest.main()
