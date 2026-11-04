from copy import deepcopy
from dataclasses import asdict
import unittest

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .world import (
    Parameters, SCENES, generate, guard, initial, parameters, play_scene, replay, validate,
)


class KiteWorldTests(unittest.TestCase):
    def normalized(self, episodes):
        return [
            {'id': episode.id, 'before': episode.before, 'after': episode.after,
             'events': list(episode.events), 'text': episode.text}
            for episode in episodes
        ]

    def audit_row(self, row):
        p = Parameters(**row['parameters'])
        episodes = replay(p, row['path'])
        self.assertEqual(self.normalized(episodes), row['episodes'])
        self.assertEqual([episode.id for episode in episodes], row['path'])
        self.assertEqual(row['story'], '\n\n'.join(episode.text for episode in episodes))
        self.assertEqual(episodes[-1].after, row['final_state'])
        self.assertTrue(row['final_state']['story.ended'])
        self.assertTrue(row['final_state']['story.outcome'])
        state = initial(p)
        for episode in episodes:
            self.assertEqual(episode.before, state)
            self.assertTrue(guard(episode.id, state))
            self.assertTrue(episode.events)
            self.assertGreaterEqual(len(episode.text.split()), 40)
            self.assertLessEqual(len(episode.text.split()), 70)
            for event in episode.events:
                for key, value in event['requires'].items():
                    self.assertEqual(state[key], value)
                self.assertTrue(event['changes'])
                for key, change in event['changes'].items():
                    self.assertEqual(state[key], change['before'])
                    self.assertNotEqual(change['before'], change['after'])
                    state[key] = change['after']
                validate(state)
            self.assertEqual(state, episode.after)
        return row

    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        outcomes = set()
        for seed in range(100):
            for count in (7, 8):
                row = self.audit_row(generate(seed, count=count))
                self.assertEqual(row['scene_count'], count)
                self.assertEqual(len(row['path']), count)
                self.assertEqual(len(row['path']), len(set(row['path'])))
                self.assertIn(row['path'][-1], {'ending_flight', 'ending_grounded'})
                outcomes.add(row['final_state']['story.outcome'])
        self.assertEqual(outcomes, {'shared_flight', 'shared_grounded_kite'})

    def test_parameter_validation_and_seed_determinism(self):
        self.assertEqual(parameters(2026102401), parameters(2026102401))
        invalid = (
            {'wind': True}, {'gust': 5}, {'reel_length': 11},
            {'frame_sound': 1}, {'tail_weight': 0}, {'shyness': 5},
        )
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ValueError):
                Parameters(**values)
        for count in (True, 6, 9):
            with self.subTest(count=count), self.assertRaises(ValueError):
                generate(count=count)

    def test_failed_scene_and_failed_local_action_do_not_mutate_caller(self):
        p = Parameters()
        state = initial(p)
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(p, state, 'ending_flight')
        self.assertEqual(state, saved)

        play = LocalPlay(state, actors=('Nia',), validate=validate)
        play_state, play_events = deepcopy(play.state), deepcopy(play.events)
        with self.assertRaises(StoryError):
            play.act('borrow_without_a_guard', {'reel.borrowed': True}, **{'story.phase': 'broken'})
        self.assertEqual(play.state, play_state)
        self.assertEqual(play.events, play_events)

    def test_optional_vignettes_are_optional_and_not_run_offstage(self):
        seven = generate(12, count=7)
        eight = generate(12, count=8)
        vignettes = {'vignette_mark', 'vignette_ribbon'}
        self.assertFalse(vignettes.intersection(seven['path']))
        self.assertEqual(len(vignettes.intersection(eight['path'])), 1)

        p = Parameters()
        plain_path = ('workshop', 'invite', 'prepare_kite', 'walk_to_commons',
                      'first_flight', 'response', 'ending_grounded')
        plain = replay(p, plain_path)[-1].after
        self.assertFalse(plain['story.mark_seen'])
        self.assertFalse(plain['wind.observed'])
        self.assertEqual(plain['kite.mark'], '')

    def test_borrowed_reel_location_and_string_are_continuous(self):
        p = Parameters(wind=3, gust=1, reel_length=32, frame_sound=False,
                       tail_weight=2, shyness=2)
        row = generate(6, count=8, params=p)
        state = initial(p)
        for episode in replay(p, row['path']):
            for event in episode.events:
                for key, change in event['changes'].items():
                    state[key] = change['after']
                validate(state)
        final = row['final_state']
        self.assertEqual(final['reel.owner'], 'Tomas')
        self.assertEqual(final['reel.location'], 'workshop')
        self.assertFalse(final['reel.borrowed'])
        self.assertTrue(final['reel.used_for_flight'])
        self.assertEqual(final['reel.line_out'], 0)
        self.assertEqual(final['reel.remaining'] + final['reel.patch_used'], final['reel.length'])
        self.assertEqual(final['neighbor.location'], 'workshop')

    def test_paired_counterfactuals_change_ending_and_agency(self):
        p = Parameters(wind=3, gust=1, reel_length=32, frame_sound=True,
                       tail_weight=2, shyness=4)
        with_mark = ('workshop', 'invite', 'vignette_mark', 'prepare_kite',
                     'walk_to_commons', 'first_flight', 'response', 'ending_flight')
        without_mark = ('workshop', 'invite', 'prepare_kite', 'walk_to_commons',
                        'first_flight', 'response', 'ending_grounded')
        marked = replay(p, with_mark)[-1].after
        unmarked = replay(p, without_mark)[-1].after
        self.assertEqual(marked['story.outcome'], 'shared_flight')
        self.assertEqual(unmarked['story.outcome'], 'shared_grounded_kite')
        self.assertEqual(marked['neighbor.role'], 'reel')
        self.assertEqual(unmarked['neighbor.role'], 'tail')

        good_weather = Parameters(wind=3, gust=1, reel_length=32, frame_sound=True,
                                  tail_weight=2, shyness=2)
        bad_weather = Parameters(wind=5, gust=1, reel_length=32, frame_sound=True,
                                 tail_weight=2, shyness=2)
        self.assertEqual(generate(9, count=7, params=good_weather)['final_state']['story.outcome'], 'shared_flight')
        self.assertEqual(generate(9, count=7, params=bad_weather)['final_state']['story.outcome'], 'shared_grounded_kite')

    def test_generated_inventory_mapping_is_complete(self):
        self.assertEqual(len(SCENES), len(set(SCENES)))
        mapped = {
            scene_id
            for entry in __import__('json').loads(
                __import__('pathlib').Path(__file__).with_name('scene_inventory.json').read_text(encoding='utf-8')
            )['scenes']
            for scene_id in entry['implemented_ids']
        }
        self.assertEqual(mapped, set(SCENES))


if __name__ == '__main__':
    unittest.main()
