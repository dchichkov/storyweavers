'''Mechanical, continuity, and counterfactual tests for the pottery adventure.'''
from copy import deepcopy
from dataclasses import asdict
from itertools import product
import unittest

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .world import Parameters, SCENES, generate, guard, initial, parameters, play_scene, replay, validate


class PotteryAdventureTests(unittest.TestCase):
    def check_row(self, row):
        p = Parameters(**row['parameters'])
        episodes = replay(p, row['path'])
        self.assertEqual(episodes, row['episodes'])
        self.assertEqual('\n\n'.join(ep['text'] for ep in episodes), row['story'])
        self.assertEqual(len(episodes), row['scene_count'])
        self.assertEqual(len(row['path']), len(set(row['path'])))
        state = initial(p)
        for ep in episodes:
            self.assertEqual(ep['before'], state)
            self.assertTrue(guard(ep['id'], state))
            self.assertGreaterEqual(40, 0)
            self.assertGreaterEqual(len(ep['text'].split()), 40)
            self.assertLessEqual(len(ep['text'].split()), 70)
            self.assertTrue(ep['events'])
            for event in ep['events']:
                for key, value in event['requires'].items():
                    self.assertEqual(state[key], value)
                self.assertTrue(event['changes'])
                for key, change in event['changes'].items():
                    self.assertEqual(state[key], change['before'])
                    self.assertNotEqual(change['before'], change['after'])
                    state[key] = change['after']
                validate(state)
            self.assertEqual(state, ep['after'])
        self.assertEqual(state, row['final_state'])
        self.assertTrue(state['story.ended'])
        self.assertTrue(state['story.outcome'])

    def test_both_lengths_one_hundred_seeds_and_exact_replay(self):
        for seed, count in product(range(100), (7, 8)):
            with self.subTest(seed=seed, count=count):
                row = generate(seed, count=count)
                self.check_row(row)
                self.assertEqual(row, generate(seed, count=count))
                self.assertEqual(len(row['path']), count)
                self.assertEqual(set(row['path']) & {'ending_kept', 'ending_repaired', 'ending_cracked'},
                                 {row['path'][-1]})

    def test_parameters_are_keyword_only_and_strict(self):
        with self.assertRaises(TypeError):
            Parameters(240)
        for kwargs in (
            {'clay_grams': True}, {'clay_grams': 179}, {'clay_grams': 281},
            {'sponge_damp': 1}, {'wheel_level': 'yes'}, {'kiln_even': 0},
            {'finish_choice': 'hide_it'},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        with self.assertRaises(ValueError):
            parameters(True)

    def test_scene_ids_and_illegal_actions_are_safe(self):
        self.assertEqual(len(SCENES), len(set(SCENES)))
        p = Parameters()
        state = initial(p)
        saved = deepcopy(state)
        for name in ('shape_cup', 'fire_cup', 'ending_kept', 'unlisted'):
            with self.assertRaises(StoryError):
                play_scene(p, state, name)
            self.assertEqual(state, saved)
        x = LocalPlay(state, actors=('Mina',), validate=validate)
        snapshot, trace = deepcopy(x.state), deepcopy(x.events)
        with self.assertRaises(StoryError):
            x.act('illegal_noop', **{'story.ended': False})
        self.assertEqual(x.state, snapshot)
        self.assertEqual(x.events, trace)
        with self.assertRaises(StoryError):
            x.act('illegal_requirement', {'missing.key': True}, **{'story.ended': True})
        self.assertEqual(x.state, snapshot)

    def test_optional_vignettes_can_each_be_omitted(self):
        p = Parameters(clay_grams=240, wheel_level=True, kiln_even=True, finish_choice='keep')
        paths = (
            ('borrow_rib', 'old_handle_memory', 'wedge_clay', 'shape_cup',
             'decide_flaw', 'fire_cup', 'ending_kept'),
            ('borrow_rib', 'wedge_clay', 'shape_cup', 'sheltered_shelf',
             'decide_flaw', 'fire_cup', 'ending_kept'),
        )
        for path in paths:
            with self.subTest(path=path):
                eps = replay(p, path)
                self.assertEqual(len(eps), 7)
                self.assertEqual(eps[-1]['after']['story.outcome'], 'crooked_rim_cup_in_use')
        self.assertNotIn('mina.knows_thumb_rest', replay(p, paths[1])[2]['after'])
        self.assertFalse(replay(p, paths[0])[3]['after']['cup.slow_dried'])

    def test_tool_and_cup_location_custody_continuity(self):
        p = Parameters()
        path = ('borrow_rib', 'old_handle_memory', 'wedge_clay', 'shape_cup',
                'decide_flaw', 'fire_cup', 'ending_kept')
        eps = replay(p, path)
        self.assertEqual(eps[0]['after']['rib.owner'], 'Mina')
        self.assertEqual(eps[0]['after']['rib.location'], 'worktable')
        self.assertEqual(eps[3]['after']['cup.location'], 'drying_shelf')
        self.assertEqual(eps[5]['after']['cup.location'], 'cooling_rack')
        final = eps[-1]['after']
        self.assertEqual((final['rib.owner'], final['rib.location']), ('Vale', 'peg'))
        self.assertTrue(final['rib.clean'] and final['rib.usable'])
        self.assertEqual((final['cup.owner'], final['cup.location']), ('Grandpa', 'Grandpa_table'))
        self.assertTrue(final['grandpa.used_gift'])

    def test_paired_counterfactuals_change_choice_and_physical_outcome(self):
        common = ('borrow_rib', 'old_handle_memory', 'wedge_clay', 'shape_cup')
        level = replay(Parameters(clay_grams=240, wheel_level=True, kiln_even=True),
                       common + ('decide_flaw', 'fire_cup', 'ending_kept'))
        tilted = replay(Parameters(clay_grams=240, wheel_level=False, kiln_even=True),
                        common + ('decide_flaw', 'fire_cup', 'ending_kept'))
        self.assertEqual(level[3]['after']['cup.rim'], 'wavy')
        self.assertEqual(tilted[3]['after']['cup.rim'], 'crooked')
        risk = Parameters(clay_grams=190, wheel_level=False, kiln_even=False, finish_choice='keep')
        exposed = replay(risk, common + ('decide_flaw', 'fire_cup', 'ending_cracked'))
        protected_path = common + ('sheltered_shelf', 'decide_flaw', 'fire_cup', 'ending_kept')
        protected = replay(risk, protected_path)
        self.assertEqual(exposed[-2]['after']['cup.stage'], 'cracked')
        self.assertEqual(protected[-2]['after']['cup.stage'], 'fired')
        self.assertNotEqual(exposed[-1]['after']['cup.use'], protected[-1]['after']['cup.use'])

    def test_all_three_endings_are_executable_and_complete(self):
        cases = (
            (Parameters(clay_grams=240, wheel_level=False, kiln_even=True, finish_choice='keep'),
             ('borrow_rib', 'old_handle_memory', 'wedge_clay', 'shape_cup', 'decide_flaw', 'fire_cup', 'ending_kept'),
             'crooked_rim_cup_in_use'),
            (Parameters(clay_grams=250, wheel_level=False, kiln_even=False, finish_choice='repair'),
             ('borrow_rib', 'old_handle_memory', 'wedge_clay', 'shape_cup', 'sheltered_shelf',
              'decide_flaw', 'fire_cup', 'ending_repaired'), 'smoothed_cup_in_use'),
            (Parameters(clay_grams=190, wheel_level=False, kiln_even=False, finish_choice='keep'),
             ('borrow_rib', 'old_handle_memory', 'wedge_clay', 'shape_cup', 'decide_flaw', 'fire_cup', 'ending_cracked'),
             'cracked_cup_repurposed_as_pencil_holder'),
        )
        for p, path, outcome in cases:
            with self.subTest(outcome=outcome):
                final = replay(p, path)[-1]['after']
                self.assertEqual(final['story.outcome'], outcome)
                validate(final)

    def test_repair_needs_real_material_and_failed_scene_does_not_mutate(self):
        p = Parameters(clay_grams=210, finish_choice='repair')
        state = initial(p)
        for scene in ('borrow_rib', 'wedge_clay', 'shape_cup'):
            state = play_scene(p, state, scene)['after']
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(p, state, 'decide_flaw')
        self.assertEqual(state, saved)

    def test_sponge_condition_changes_local_actions(self):
        dry = Parameters(sponge_damp=False)
        wet = Parameters(sponge_damp=True)
        dry_ep = play_scene(dry, play_scene(dry, initial(dry), 'borrow_rib')['after'], 'wedge_clay')
        wet_ep = play_scene(wet, play_scene(wet, initial(wet), 'borrow_rib')['after'], 'wedge_clay')
        dry_actions = [event['action'] for event in dry_ep['events']]
        wet_actions = [event['action'] for event in wet_ep['events']]
        self.assertIn('wet_and_wring_sponge', dry_actions)
        self.assertIn('set_damp_sponge_by_wheel', wet_actions)
        self.assertTrue(dry_ep['after']['sponge.damp'])


if __name__ == '__main__':
    unittest.main()
