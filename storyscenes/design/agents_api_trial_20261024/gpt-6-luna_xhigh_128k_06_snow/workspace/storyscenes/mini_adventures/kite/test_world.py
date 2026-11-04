'''Mechanical and counterfactual tests for the snowy square adventure.'''
from copy import deepcopy
import unittest

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .world import Parameters, SCENES, generate, guard, initial, parameters, play_scene, replay, validate


class KiteAdventureTests(unittest.TestCase):
    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        endings = set()
        for count in (7, 8):
            for seed in range(100):
                row = generate(seed, count=count)
                self.assertEqual(row['scene_count'], count)
                self.assertEqual(len(row['path']), count)
                self.assertEqual(len(set(row['path'])), count)
                self.assertEqual(row['story'], '\n\n'.join(ep['text'] for ep in row['episodes']))
                self.assertEqual(replay(Parameters(**row['parameters']), row['path']), row['episodes'])
                self.assertTrue(row['final_state']['story.ended'])
                self.assertTrue(row['final_state']['story.outcome'])
                for episode in row['episodes']:
                    self.assertGreaterEqual(len(episode['text'].split()), 40)
                    self.assertLessEqual(len(episode['text'].split()), 70)
                endings.add(row['final_state']['story.outcome'])
        self.assertEqual(set(SCENES), set(SCENES))
        self.assertTrue({'patient_delivery', 'race_delivery', 'spill_recovery'} <= endings)

    def test_invalid_parameters_are_rejected(self):
        invalid = (
            {'route_choice': 'sprint'}, {'snow_cm': True}, {'snow_cm': 21},
            {'runner_condition': 'broken'}, {'load_kg': 0}, {'has_mittens': 1},
            {'friend_race_pressure': 0}, {'friend_race_pressure': True},
        )
        for kwargs in invalid:
            with self.subTest(kwargs=kwargs):
                with self.assertRaises(ValueError):
                    Parameters(**kwargs)
        with self.assertRaises(ValueError):
            parameters(True)
        for count in (True, 6, 9):
            with self.assertRaises(ValueError):
                generate(count=count)

    def test_illegal_scene_and_failed_local_action_do_not_mutate_caller(self):
        p = Parameters()
        state = initial(p)
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(p, state, 'prepare_supplies')
        self.assertEqual(state, saved)
        play = LocalPlay(state, actors=('Mina',), validate=validate)
        old_state, old_events = deepcopy(play.state), deepcopy(play.events)
        with self.assertRaises(StoryError):
            play.act('unknown_effect', {}, **{'new.key': True})
        self.assertEqual(play.state, old_state)
        self.assertEqual(play.events, old_events)

    def test_optional_vignettes_are_optional_and_have_enacted_effects(self):
        p = Parameters(route_choice='patient', has_mittens=False)
        state = initial(p)
        borrowed = play_scene(p, state, 'borrow_sled')['after']
        mitten = play_scene(p, borrowed, 'mittens_vignette')
        changed = {key for key in borrowed if borrowed[key] != mitten['after'][key]}
        self.assertEqual(changed, {'mittens.location', 'mittens.worn', 'mittens.borrowed', 'mittens.secured'})
        bell = play_scene(p, borrowed, 'bell_vignette')
        self.assertEqual({key for key in borrowed if borrowed[key] != bell['after'][key]}, {'friend.knows_lane'})
        for count in (7, 8):
            row = generate(4, count=count, params=p)
            chosen = set(row['path']) & {'mittens_vignette', 'bell_vignette'}
            self.assertEqual(len(chosen), count - 7)
            final = row['final_state']
            if 'mittens_vignette' not in row['path']:
                self.assertFalse(final['mittens.borrowed'])
                self.assertEqual(final['mittens.location'], 'friend')
            if 'bell_vignette' not in row['path']:
                self.assertFalse(final['friend.knows_lane'])

    def test_prop_and_location_continuity_through_every_event(self):
        p = Parameters(route_choice='race', snow_cm=15, load_kg=3, has_mittens=True)
        row = generate(9, count=8, params=p)
        state = initial(p)
        for episode in row['episodes']:
            self.assertEqual(episode['before'], state)
            self.assertTrue(guard(episode['id'], state))
            for event in episode['events']:
                self.assertTrue(event['changes'])
                for key, expected in event['requires'].items():
                    self.assertEqual(state[key], expected)
                for key, change in event['changes'].items():
                    self.assertEqual(state[key], change['before'])
                    state[key] = change['after']
                validate(state)
            self.assertEqual(state, episode['after'])
        self.assertEqual(state, row['final_state'])
        self.assertEqual(state['bundle.location'], 'neighbor')
        self.assertEqual(state['bundle.owner'], 'neighbor')
        self.assertTrue(state['sled.used_for_delivery'])
        self.assertTrue(state['sled.returned'])
        self.assertEqual(state['sled.owner'], 'stallkeeper')
        self.assertEqual(state['sled.location'], 'stall')
        self.assertTrue(state['sled.checked'])

    def test_paired_counterfactuals_change_the_race_and_ending(self):
        safe = Parameters(route_choice='race', snow_cm=3, runner_condition='sound', load_kg=1,
                          has_mittens=True, friend_race_pressure=1)
        unsafe = Parameters(route_choice='race', snow_cm=15, runner_condition='sound', load_kg=1,
                            has_mittens=True, friend_race_pressure=1)
        good = generate(12, count=7, params=safe)
        bad = generate(12, count=7, params=unsafe)
        self.assertEqual(good['path'][-1], 'ending_race')
        self.assertEqual(good['final_state']['story.outcome'], 'race_delivery')
        self.assertEqual(bad['path'][-1], 'ending_spill')
        self.assertEqual(bad['final_state']['story.outcome'], 'spill_recovery')
        self.assertTrue(good['final_state']['neighbor.received_soup'])
        self.assertFalse(bad['final_state']['neighbor.received_soup'])
        self.assertTrue(bad['final_state']['neighbor.received_supplies'])

    def test_patience_is_a_distinct_complete_ending(self):
        p = Parameters(route_choice='patient', snow_cm=15, runner_condition='loose',
                       load_kg=4, has_mittens=False, friend_race_pressure=3)
        row = generate(27, count=7, params=p)
        self.assertEqual(row['path'][-1], 'ending_patient')
        self.assertEqual(row['final_state']['story.outcome'], 'patient_delivery')
        self.assertTrue(row['final_state']['neighbor.received_soup'])
        self.assertTrue(row['final_state']['friend.helped'])
        self.assertTrue(row['final_state']['sled.repaired'])

    def test_parameter_factory_is_deterministic(self):
        for seed in range(20):
            self.assertEqual(parameters(seed), parameters(seed))

    def test_replay_rejects_repeated_or_incomplete_scenes(self):
        p = Parameters()
        with self.assertRaises(StoryError):
            replay(p, ('borrow_sled',) * 7)
        with self.assertRaises(StoryError):
            replay(p, ('borrow_sled',))


if __name__ == '__main__':
    unittest.main()
