from copy import deepcopy
from dataclasses import asdict
from itertools import product
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .world import (
    OPTIONAL, Parameters, SCENES, generate, guard, initial, parameters,
    play_scene, replay, validate,
)


def episode_json(episode):
    return {
        'id': episode.id, 'before': deepcopy(episode.before), 'after': deepcopy(episode.after),
        'events': deepcopy(list(episode.events)), 'text': episode.text,
    }


class KiteWorldTests(unittest.TestCase):
    def verify_row(self, row):
        params = Parameters(**row['parameters'])
        episodes = replay(params, row['path'])
        self.assertEqual([episode_json(e) for e in episodes], row['episodes'])
        self.assertEqual(episodes[-1].after, row['final_state'])
        self.assertEqual('\n\n'.join(e.text for e in episodes), row['story'])
        self.assertEqual(len(row['path']), row['scene_count'])
        self.assertEqual(len(set(row['path'])), len(row['path']))
        self.assertTrue(row['final_state']['story.ended'])
        self.assertTrue(row['final_state']['story.outcome'])
        state = initial(params)
        for episode in episodes:
            self.assertEqual(episode.before, state)
            self.assertTrue(guard(episode.id, state))
            self.assertTrue(episode.events)
            for event in episode.events:
                self.assertTrue(event['action'])
                self.assertTrue(event['changes'])
                for key, value in event['requires'].items():
                    self.assertEqual(state[key], value)
                for key, change in event['changes'].items():
                    self.assertEqual(state[key], change['before'])
                    self.assertNotEqual(change['before'], change['after'])
                    state[key] = deepcopy(change['after'])
                validate(state)
            self.assertEqual(state, episode.after)
        return row['final_state']['story.outcome']

    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        endings = set()
        for seed, count in product(range(100), (7, 8)):
            with self.subTest(seed=seed, count=count):
                row = generate(seed, count=count)
                endings.add(self.verify_row(row))
                optional_in_path = OPTIONAL.intersection(row['path'])
                self.assertEqual(len(optional_in_path), 1 if count == 7 else 2)
                self.assertEqual(row, generate(seed, count=count))
        self.assertIn('fox_recovered', endings)
        self.assertIn('comforted_with_fox_missing', endings)

    def test_parameters_are_strict_and_seeded(self):
        self.assertEqual(parameters(4), parameters(4))
        invalid = (
            {'toy_site': 'lake'}, {'kit_memory': None}, {'daylight_minutes': True},
            {'daylight_minutes': 3}, {'lantern_charge': False}, {'lantern_charge': 0},
            {'toy_covered': 1}, {'ground_wet': 'yes'}, {'search_policy': 'always'},
        )
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ValueError):
                Parameters(**values)
        for bad_seed in (True, '2'):
            with self.subTest(seed=bad_seed), self.assertRaises(ValueError):
                parameters(bad_seed)
        for count in (True, 6, 9):
            with self.subTest(count=count), self.assertRaises(ValueError):
                generate(count=count)

    def test_failed_scene_and_failed_local_action_do_not_mutate_caller(self):
        params = Parameters()
        state = initial(params)
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(params, state, 'search_fox')
        self.assertEqual(state, saved)
        play = LocalPlay(state, actors=('Mira', 'Kit'), validate=validate)
        local_before = deepcopy(play.state)
        events_before = deepcopy(play.events)
        with self.assertRaises(StoryError):
            play.act('illegal_light', requires={'lantern.charge': 99}, **{'lantern.lit': True})
        self.assertEqual(play.state, local_before)
        self.assertEqual(play.events, events_before)
        with self.assertRaises(StoryError):
            play_scene(params, state, 'not_a_scene')
        self.assertEqual(state, saved)

    def test_optional_vignettes_have_no_offstage_effects(self):
        params = Parameters(toy_site='tent_edge', kit_memory='tent_edge', daylight_minutes=2,
                            lantern_charge=2, toy_covered=False, ground_wet=False,
                            search_policy='conserve')
        base = replay(params, ('borrow_lantern', 'tell_about_fox'))[-1].after
        self.assertFalse(base['shadow.played'])
        self.assertFalse(base['trail.marked'])
        no_shadow = replay(params, ('borrow_lantern', 'tell_about_fox', 'trail_vignette'))[-1].after
        self.assertFalse(no_shadow['shadow.played'])
        self.assertTrue(no_shadow['trail.marked'])
        no_trail = replay(params, ('borrow_lantern', 'tell_about_fox', 'shadow_vignette'))[-1].after
        self.assertTrue(no_trail['shadow.played'])
        self.assertFalse(no_trail['trail.marked'])
        for omitted_path in (
            ('borrow_lantern', 'tell_about_fox', 'choose_search', 'search_fox', 'return_to_camp', 'ending_found'),
            ('borrow_lantern', 'tell_about_fox', 'shadow_vignette', 'choose_search', 'search_fox', 'return_to_camp', 'ending_found'),
            ('borrow_lantern', 'tell_about_fox', 'trail_vignette', 'choose_search', 'search_fox', 'return_to_camp', 'ending_found'),
        ):
            final = replay(params, omitted_path)[-1].after
            self.assertFalse(final['shadow.played'] if 'shadow_vignette' not in omitted_path else False)
            self.assertFalse(final['trail.marked'] if 'trail_vignette' not in omitted_path else False)

    def test_paired_counterfactuals_change_search_outcome(self):
        base = dict(toy_site='fern_hollow', kit_memory='tent_edge', daylight_minutes=0,
                    lantern_charge=1, toy_covered=True, ground_wet=False, search_policy='sweep')
        dark = Parameters(**base)
        more_daylight = Parameters(**(base | {'daylight_minutes': 2}))
        dark_row = generate(8, params=dark)
        light_row = generate(8, params=more_daylight)
        self.assertEqual(dark_row['final_state']['story.outcome'], 'comforted_with_fox_missing')
        self.assertEqual(light_row['final_state']['story.outcome'], 'fox_recovered')
        conserve = Parameters(**(base | {'lantern_charge': 2, 'search_policy': 'conserve'}))
        sweep = Parameters(**(base | {'lantern_charge': 2, 'search_policy': 'sweep'}))
        self.assertEqual(generate(9, params=conserve)['final_state']['story.outcome'], 'comforted_with_fox_missing')
        self.assertEqual(generate(9, params=sweep)['final_state']['story.outcome'], 'fox_recovered')

    def test_covered_toy_requires_an_enacted_recovery_action(self):
        for covered in (False, True):
            params = Parameters(toy_site='tent_edge', kit_memory='tent_edge', daylight_minutes=1,
                                lantern_charge=2, toy_covered=covered, ground_wet=False,
                                search_policy='conserve')
            episodes = replay(params, ('borrow_lantern', 'tell_about_fox', 'choose_search', 'search_fox'))
            actions = [event['action'] for event in episodes[-1].events]
            self.assertEqual('lift_cover_from_fox' in actions, covered)
            self.assertEqual(episodes[-1].after['fox.location'], 'kit_hand')

    def test_locations_and_borrowed_object_remain_continuous(self):
        for count in (7, 8):
            row = generate(37, count=count)
            params = Parameters(**row['parameters'])
            state = initial(params)
            for episode in replay(params, row['path']):
                for key in ('camp.location', 'mira.location', 'kit.location'):
                    self.assertEqual(state['camp.location'], state[key])
                self.assertEqual(state['lantern.owner'], 'dad')
                expected_lantern_location = {
                    'none': 'camp_table', 'mira': 'mira_hand', 'kit': 'kit_hand', 'dad': 'dad_hand'
                }[state['lantern.holder']]
                self.assertEqual(state['lantern.location'], expected_lantern_location)
                if state['fox.recovered']:
                    self.assertIn(state['fox.location'], ('kit_hand', 'kit_bedroll'))
                else:
                    self.assertIn(state['fox.location'], ('tent_edge', 'fern_hollow'))
                state = deepcopy(episode.after)
            self.assertTrue(state['lantern.returned'])

    def test_endings_require_their_actual_middle(self):
        for params, ending in (
            (Parameters(toy_site='fern_hollow', kit_memory='fern_hollow', lantern_charge=1,
                        daylight_minutes=0, search_policy='conserve'), 'ending_found'),
            (Parameters(toy_site='fern_hollow', kit_memory='tent_edge', lantern_charge=1,
                        daylight_minutes=0, search_policy='sweep'), 'ending_lost'),
        ):
            state = initial(params)
            for scene_id in ('borrow_lantern', 'tell_about_fox', 'choose_search', 'search_fox', 'return_to_camp'):
                state = play_scene(params, state, scene_id).after
            self.assertTrue(guard(ending, state))
            other = 'ending_lost' if ending == 'ending_found' else 'ending_found'
            self.assertFalse(guard(other, state))
            final = play_scene(params, state, ending).after
            self.assertTrue(final['story.ended'])
            self.assertTrue(final['story.outcome'])

    def test_cli_prints_a_complete_story(self):
        result = subprocess.run(
            [sys.executable, '-m', 'storyscenes.mini_adventures.kite.world', '--seed', '0', '--scenes', '8'],
            check=True, capture_output=True, text=True,
        )
        self.assertTrue(result.stdout.strip())
        self.assertGreaterEqual(len(result.stdout.split()), 280)


if __name__ == '__main__':
    unittest.main()
