from copy import deepcopy
from dataclasses import asdict
from itertools import product
import unittest

from storyscenes.runtime import StoryError
from storyscenes.mini_adventures.local_play import LocalPlay
from .world import Parameters, SCENES, generate, guard, initial, replay, validate


class KitePondTests(unittest.TestCase):
    def assert_row(self, row):
        params = Parameters(**row['parameters'])
        episodes = replay(params, row['path'])
        self.assertEqual(episodes, row['episodes'])
        self.assertEqual('\n\n'.join(ep['text'] for ep in episodes), row['story'])
        self.assertEqual(episodes[-1]['after'], row['final_state'])
        self.assertEqual(len(row['path']), row['scene_count'])
        self.assertEqual(len(row['path']), len(set(row['path'])))
        state = initial(params)
        for ep in episodes:
            self.assertEqual(ep['before'], state)
            self.assertTrue(guard(ep['id'], state))
            self.assertTrue(40 <= len(ep['text'].split()) <= 70, (ep['id'], len(ep['text'].split())))
            for event in ep['events']:
                self.assertTrue(event['action'])
                self.assertTrue(event['changes'])
                for key, value in event['requires'].items():
                    self.assertIn(key, state)
                    self.assertEqual(state[key], value)
                for key, change in event['changes'].items():
                    self.assertEqual(state[key], change['before'])
                    self.assertNotEqual(change['before'], change['after'])
                    state[key] = deepcopy(change['after'])
                validate(state)
            self.assertEqual(state, ep['after'])
            self.assertEqual(ep['after']['mara.place'], 'bank')
            self.assertEqual(ep['after']['jules.place'], 'bank')
        self.assertTrue(row['final_state']['story.ended'])
        self.assertTrue(row['final_state']['story.outcome'])

    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        endings = set()
        for seed, count in product(range(100), (7, 8)):
            with self.subTest(seed=seed, count=count):
                row = generate(seed, count=count)
                self.assert_row(row)
                endings.add(row['final_state']['story.outcome'])
        self.assertEqual(endings, {'boat_recovered', 'boat_left_in_pond'})

    def test_parameters_are_strict_and_reach_both_outcomes(self):
        for kwargs in (
            {'net_reach_cm': True}, {'boat_distance_cm': 241},
            {'net_mesh': 'holey'}, {'wind': 'storm'}, {'weeds': 1},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        with self.assertRaises(ValueError):
            generate(0, count=True)
        success = Parameters(net_reach_cm=190, boat_distance_cm=130, net_mesh='intact', wind='calm', weeds=False)
        failure = Parameters(net_reach_cm=90, boat_distance_cm=190, net_mesh='intact', wind='calm', weeds=False)
        self.assertEqual(generate(3, params=success)['final_state']['story.outcome'], 'boat_recovered')
        self.assertEqual(generate(3, params=failure)['final_state']['story.outcome'], 'boat_left_in_pond')

    def test_optional_scenes_can_be_omitted_or_composed(self):
        p = Parameters(net_reach_cm=190, boat_distance_cm=130, weeds=False)
        seven_memory = ('spot_boat', 'remember_boat', 'borrow_net', 'bank_plan', 'cast_net', 'return_net', 'ending_boat_home')
        seven_sightline = ('spot_boat', 'read_reeds', 'borrow_net', 'bank_plan', 'cast_net', 'return_net', 'ending_boat_home')
        eight = ('spot_boat', 'remember_boat', 'read_reeds', 'borrow_net', 'bank_plan', 'cast_net', 'return_net', 'ending_boat_home')
        self.assertEqual(len(replay(p, seven_memory)), 7)
        self.assertEqual(len(replay(p, seven_sightline)), 7)
        self.assertEqual(len(replay(p, eight)), 8)
        row = generate(12, count=8, params=p)
        self.assertTrue({'remember_boat', 'read_reeds'} <= set(row['path']))
        self.assertEqual(set(SCENES), {scene for scene in SCENES})

    def test_reed_observation_is_a_paired_counterfactual(self):
        p = Parameters(net_reach_cm=190, boat_distance_cm=130, net_mesh='intact', wind='calm', weeds=True)
        with_gap = ('spot_boat', 'read_reeds', 'borrow_net', 'bank_plan', 'cast_net', 'return_net', 'ending_boat_home')
        without_gap = ('spot_boat', 'remember_boat', 'borrow_net', 'bank_plan', 'cast_net', 'return_net', 'ending_boat_left')
        a = replay(p, with_gap)[-1]['after']
        b = replay(p, without_gap)[-1]['after']
        self.assertEqual(a['boat.location'], 'friend')
        self.assertEqual(b['boat.location'], 'pond')
        self.assertNotEqual(a['story.outcome'], b['story.outcome'])

    def test_parameters_change_retrieval_and_physical_continuity(self):
        common = dict(boat_distance_cm=130, net_mesh='intact', wind='calm', weeds=False)
        near = generate(4, params=Parameters(net_reach_cm=190, **common))
        far = generate(4, params=Parameters(net_reach_cm=100, **common))
        self.assertEqual(near['final_state']['story.outcome'], 'boat_recovered')
        self.assertEqual(far['final_state']['story.outcome'], 'boat_left_in_pond')
        for row in (near, far):
            self.assertTrue(row['final_state']['net.returned'])
            self.assertEqual(row['final_state']['net.owner'], 'keeper')
            self.assertEqual(row['final_state']['net.location'], 'shed')
            self.assertEqual(row['final_state']['mara.place'], 'bank')
            self.assertEqual(row['final_state']['jules.place'], 'bank')
        self.assertEqual(near['final_state']['boat.location'], 'friend')
        self.assertEqual(far['final_state']['boat.location'], 'pond')

    def test_failed_scene_and_atomic_local_action_do_not_mutate_callers(self):
        p = Parameters()
        state = initial(p)
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            from .world import play_scene
            play_scene(p, state, 'borrow_net')
        self.assertEqual(state, saved)
        play = LocalPlay(state, actors=('Mara', 'Jules'), validate=validate)
        prior_state, prior_events = deepcopy(play.state), deepcopy(play.events)
        with self.assertRaises(StoryError):
            play.act('illegal_loan', {'net.owner': 'Mara'}, **{'net.owner': 'keeper'})
        self.assertEqual(play.state, prior_state)
        self.assertEqual(play.events, prior_events)
        with self.assertRaises(StoryError):
            play.act('unknown_effect', **{'not.a.real.key': True})
        self.assertEqual(play.state, prior_state)
        self.assertEqual(play.events, prior_events)

    def test_invalid_scene_and_repeated_scene_fail(self):
        with self.assertRaises(StoryError):
            guard('not_a_scene', initial(Parameters()))
        p = Parameters()
        with self.assertRaises(StoryError):
            replay(p, ('spot_boat', 'spot_boat'))

    def test_safety_and_distinct_failure_plays(self):
        cases = (
            Parameters(net_reach_cm=190, boat_distance_cm=130, wind='gusty'),
            Parameters(net_reach_cm=190, boat_distance_cm=130, net_mesh='torn'),
            Parameters(net_reach_cm=190, boat_distance_cm=130, weeds=True),
            Parameters(net_reach_cm=90, boat_distance_cm=190),
        )
        for i, p in enumerate(cases):
            row = generate(i, params=p)
            self.assertEqual(row['final_state']['story.outcome'], 'boat_left_in_pond')
            self.assertTrue(row['final_state']['net.returned'])
            self.assertFalse(row['final_state']['net.in_water'])
            self.assertEqual(row['final_state']['mara.place'], 'bank')
            self.assertEqual(row['final_state']['jules.place'], 'bank')


if __name__ == '__main__':
    unittest.main()
