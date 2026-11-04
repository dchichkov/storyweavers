from copy import deepcopy
import json
import subprocess
import sys
import unittest

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .world import Parameters, SCENES, generate, guard, initial, parameters, play_scene, replay, validate


class WashingLineTests(unittest.TestCase):
    def through(self, p, *path):
        state = initial(p)
        episodes = []
        for scene_id in path:
            episode = play_scene(p, state, scene_id)
            episodes.append(episode)
            state = episode.after
        return state, episodes

    def check_row(self, row):
        p = Parameters(**row['parameters'])
        self.assertEqual(row['scene_count'], len(row['path']))
        self.assertEqual(len(row['path']), len(set(row['path'])))
        self.assertTrue(set(row['path']) <= set(SCENES))
        self.assertEqual(row['story'], '\n\n'.join(e['text'] for e in row['episodes']))
        state = initial(p)
        for scene_id, episode in zip(row['path'], row['episodes']):
            self.assertEqual(episode['id'], scene_id)
            self.assertEqual(episode['before'], state)
            self.assertTrue(guard(scene_id, state))
            self.assertTrue(episode['events'])
            for event in episode['events']:
                self.assertTrue(event['action'])
                self.assertTrue(event['changes'])
                for key, value in event['requires'].items():
                    self.assertEqual(state[key], value)
                for key, change in event['changes'].items():
                    self.assertEqual(state[key], change['before'])
                    self.assertNotEqual(change['before'], change['after'])
                    state[key] = deepcopy(change['after'])
                validate(state)
            self.assertEqual(episode['after'], state)
        self.assertEqual(row['final_state'], state)
        self.assertTrue(state['story.ended'])
        self.assertTrue(state['story.outcome'])
        reproduced = replay(p, row['path'])
        replay_rows = [
            {'id': e.id, 'before': e.before, 'after': e.after,
             'events': list(e.events), 'text': e.text}
            for e in reproduced
        ]
        self.assertEqual(replay_rows, row['episodes'])

    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        for seed in range(100):
            for count in (7, 8):
                with self.subTest(seed=seed, count=count):
                    self.check_row(generate(seed, count=count))

    def test_invalid_parameters_are_rejected(self):
        for kwargs in (
            {'peg_count': True}, {'peg_count': 3}, {'peg_count': 13},
            {'shower_after': False}, {'shower_after': 2}, {'shower_after': 7},
            {'windy': 1}, {'line_strength': 'yes'}, {'shelter_open': 0},
            {'sheet_heavy': None}, {'priority': 'towel'},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        for count in (True, 6, 9):
            with self.assertRaises(ValueError):
                generate(count=count)
        with self.assertRaises(ValueError):
            parameters(True)

    def test_illegal_scene_and_atomic_action_do_not_mutate_caller(self):
        p = Parameters()
        source = initial(p)
        saved = deepcopy(source)
        with self.assertRaises(StoryError):
            play_scene(p, source, 'hang_wash')
        self.assertEqual(source, saved)
        local = LocalPlay(source, actors=('Nia', 'Mae'), validate=validate)
        local_state = deepcopy(local.state)
        with self.assertRaises(StoryError):
            local.act('cannot_clip_before_borrowing', requires={'peg_bag.owner': 'Nia'},
                      **{'sheet.location': 'line'})
        self.assertEqual(local.state, local_state)
        self.assertEqual(local.events, [])

    def test_optional_vignettes_can_be_omitted_and_are_local_when_selected(self):
        p = Parameters()
        seven = generate(11, count=7, params=p)
        self.assertFalse({'save_snail', 'peg_rhyme_vignette'} & set(seven['path']))
        eight = generate(11, count=8, params=p)
        self.assertEqual(len({'save_snail', 'peg_rhyme_vignette'} & set(eight['path'])), 1)
        borrowed, _ = self.through(p, 'borrow_bag')
        saved = deepcopy(borrowed)
        snail = play_scene(p, borrowed, 'save_snail')
        changed = {key for key in saved if saved[key] != snail.after[key]}
        self.assertEqual(changed, {'snail.location', 'snail.safe', 'vignette.snail_done'})
        self.assertEqual(borrowed, saved)

    def test_object_locations_and_peg_conservation_through_endings(self):
        recipes = (
            Parameters(peg_count=8, shower_after=6, windy=False, line_strength=True,
                       shelter_open=True, sheet_heavy=False, priority='sheet'),
            Parameters(peg_count=8, shower_after=3, windy=False, line_strength=True,
                       shelter_open=True, sheet_heavy=False, priority='sheet'),
            Parameters(peg_count=5, shower_after=3, windy=True, line_strength=False,
                       shelter_open=False, sheet_heavy=True, priority='small'),
        )
        expected = ('hung_before_shower', 'covered_in_shed', 'caught_then_rehung')
        for p, outcome in zip(recipes, expected):
            row = generate(27, count=7, params=p)
            self.assertEqual(row['final_state']['story.outcome'], outcome)
            final = row['final_state']
            self.assertTrue(final['peg_bag.returned'])
            self.assertEqual(final['peg_bag.owner'], 'Mae')
            self.assertTrue(final['peg_bag.used'])
            self.assertEqual(final['peg_bag.pegs'] + final['pegs.in_use'], p.peg_count)
            if outcome == 'hung_before_shower':
                self.assertTrue(all(final[f'{item}.location'] == 'line' for item in ('sheet', 'shirt', 'towel', 'socks')))
            elif outcome == 'covered_in_shed':
                self.assertTrue(all(final[f'{item}.location'] == 'shelter_rack' for item in ('sheet', 'shirt', 'towel', 'socks')))
            else:
                self.assertTrue(all(final[f'{item}.location'] == 'indoor_rack' for item in ('sheet', 'shirt', 'towel', 'socks')))

    def test_limited_peg_priority_is_a_paired_counterfactual(self):
        common = dict(peg_count=5, shower_after=6, windy=False, line_strength=True,
                      shelter_open=True, sheet_heavy=False)
        sheet_first = Parameters(**common, priority='sheet')
        small_first = Parameters(**common, priority='small')
        path = ('borrow_bag', 'sky_signs', 'prepare_wash', 'hang_wash')
        a = replay(sheet_first, path)[-1].after
        b = replay(small_first, path)[-1].after
        self.assertEqual(a['sheet.location'], 'line')
        self.assertEqual(b['sheet.location'], 'basket')
        self.assertNotEqual(a['socks.location'], b['socks.location'])

    def test_shelter_parameter_changes_the_recovery_outcome(self):
        common = dict(peg_count=8, shower_after=3, windy=False, line_strength=True,
                     sheet_heavy=False, priority='sheet')
        sheltered = generate(5, count=7, params=Parameters(**common, shelter_open=True))
        exposed = generate(5, count=7, params=Parameters(**common, shelter_open=False))
        self.assertEqual(sheltered['final_state']['story.outcome'], 'covered_in_shed')
        self.assertEqual(exposed['final_state']['story.outcome'], 'caught_then_rehung')

    def test_repeated_or_incompatible_scenes_fail_without_state_changes(self):
        p = Parameters()
        state = initial(p)
        saved = deepcopy(state)
        for scene_id in ('sky_signs', 'prepare_wash', 'ending_line'):
            with self.assertRaises(StoryError):
                play_scene(p, state, scene_id)
        self.assertEqual(state, saved)
        state, _ = self.through(p, 'borrow_bag')
        with self.assertRaises(StoryError):
            play_scene(p, state, 'borrow_bag')

    def test_cli_prints_prose(self):
        result = subprocess.run(
            [sys.executable, '-m', 'storyscenes.mini_adventures.kite.world', '--seed', '0', '--scenes', '8'],
            check=True, capture_output=True, text=True,
        )
        self.assertIn('Nia', result.stdout)
        self.assertGreater(len(result.stdout.split()), 250)


if __name__ == '__main__':
    unittest.main()
