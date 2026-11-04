from copy import deepcopy
from dataclasses import asdict
from itertools import product
import unittest

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .world import Parameters, SCENES, generate, guard, initial, play_scene, replay, validate


class VillageFestivalTests(unittest.TestCase):
    def check_row(self, row):
        params = Parameters(**row['parameters'])
        episodes = replay(params, row['path'])
        expected = []
        for episode in episodes:
            data = asdict(episode)
            data['events'] = list(episode.events)
            expected.append(data)
        self.assertEqual(expected, row['episodes'])
        self.assertEqual(len(row['path']), row['scene_count'])
        self.assertEqual(len(row['path']), len(set(row['path'])))
        self.assertEqual(row['story'], '\n\n'.join(e.text for e in episodes))
        self.assertEqual(row['final_state'], episodes[-1].after)
        self.assertTrue(row['final_state']['story.ended'])
        self.assertTrue(row['final_state']['story.outcome'])
        state = initial(params)
        for episode in episodes:
            self.assertEqual(episode.before, state)
            self.assertTrue(guard(episode.id, state))
            self.assertTrue(episode.events)
            for event in episode.events:
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
            self.assertGreaterEqual(len(episode.text.split()), 40)
            self.assertLessEqual(len(episode.text.split()), 70)

    def test_two_lengths_over_one_hundred_seeds_and_exact_replay(self):
        for seed, count in product(range(100), (7, 8)):
            with self.subTest(seed=seed, count=count):
                row = generate(seed, count=count)
                self.check_row(row)
                self.assertEqual(row, generate(seed, count=count))
                optional = {'color_vignette', 'knot_vignette'} & set(row['path'])
                self.assertEqual(len(optional), count - 7)
                self.assertEqual(row['path'][-1], 'ending_square' if row['final_state']['layout.mode'] == 'square'
                                 else 'ending_hall')

    def test_explicit_parameter_recipes_reach_both_endings(self):
        square = Parameters(spool_length_cm=240, gusty=False, rainy=False,
                            posts_sturdy=True, jo_reach_cm=70, knot_slips=False)
        hall = Parameters(spool_length_cm=180, gusty=False, rainy=True,
                          posts_sturdy=True, jo_reach_cm=70, knot_slips=False)
        self.assertEqual(generate(17, count=7, params=square)['final_state']['story.outcome'], 'shared_square')
        self.assertEqual(generate(17, count=7, params=hall)['final_state']['story.outcome'], 'sheltered_hall')

    def test_every_parameter_is_validated_and_consequential(self):
        invalid = (
            {'spool_length_cm': True}, {'spool_length_cm': 99}, {'spool_length_cm': 321},
            {'jo_reach_cm': False}, {'jo_reach_cm': 44}, {'gusty': 1},
            {'rainy': 'false'}, {'posts_sturdy': 0}, {'knot_slips': None},
        )
        for values in invalid:
            with self.subTest(values=values), self.assertRaises(ValueError):
                Parameters(**values)
        safe = Parameters(spool_length_cm=240, gusty=False, rainy=False,
                          posts_sturdy=True, jo_reach_cm=70, knot_slips=False)
        slippery = Parameters(spool_length_cm=240, gusty=False, rainy=False,
                              posts_sturdy=True, jo_reach_cm=70, knot_slips=True)
        self.assertEqual(generate(5, count=7, params=safe)['final_state']['story.outcome'], 'shared_square')
        self.assertEqual(generate(5, count=7, params=slippery)['final_state']['story.outcome'], 'sheltered_hall')
        short = Parameters(spool_length_cm=120, gusty=False, rainy=False,
                           posts_sturdy=True, jo_reach_cm=70, knot_slips=False)
        low_reach = Parameters(spool_length_cm=240, gusty=False, rainy=False,
                               posts_sturdy=True, jo_reach_cm=50, knot_slips=False)
        weak = Parameters(spool_length_cm=240, gusty=False, rainy=False,
                          posts_sturdy=False, jo_reach_cm=70, knot_slips=False)
        windy = Parameters(spool_length_cm=240, gusty=True, rainy=False,
                           posts_sturdy=True, jo_reach_cm=70, knot_slips=False)
        for params in (short, low_reach, weak, windy):
            self.assertEqual(generate(5, count=7, params=params)['final_state']['story.outcome'], 'sheltered_hall')

    def test_optional_vignettes_are_enacted_and_omittable(self):
        params = Parameters()
        base = generate(4, count=7, params=params)
        self.assertFalse({'color_vignette', 'knot_vignette'} & set(base['path']))
        after_meeting = replay(params, ('borrow_spool', 'meet_neighbor'))[-1].after
        colors = play_scene(params, after_meeting, 'color_vignette')
        self.assertEqual(colors.after['bunting.pattern'], 'blue-and-gold')
        self.assertTrue(colors.after['Jo.chose_colors'])
        practiced = play_scene(params, after_meeting, 'knot_vignette')
        self.assertTrue(practiced.after['knot.practiced'])
        self.assertEqual(practiced.after['spool.remaining_cm'], after_meeting['spool.remaining_cm'] - 10)
        with_color = replay(params, ('borrow_spool', 'meet_neighbor', 'color_vignette'))[-1].after
        without_color = after_meeting
        self.assertNotEqual(with_color['bunting.pattern'], without_color['bunting.pattern'])

    def test_borrowed_object_and_locations_remain_consistent(self):
        params = Parameters(spool_length_cm=240)
        row = generate(8, count=8, params=params)
        state = initial(params)
        for episode in row['episodes']:
            self.assertEqual(episode['before'], state)
            for event in episode['events']:
                for key, change in event['changes'].items():
                    state[key] = change['after']
                validate(state)
            self.assertEqual(state, episode['after'])
            if state['layout.mode'] == 'hall':
                self.assertEqual(state['festival.place'], 'hall')
                if not state['bunting.hung']:
                    self.assertEqual(state['bunting.location'], 'basket:hall')
        final = row['final_state']
        self.assertEqual(final['spool.owner'], 'Mrs Bell')
        self.assertEqual(final['spool.holder'], 'Mrs Bell')
        self.assertEqual(final['spool.location'], 'bell_shed')
        self.assertTrue(final['spool.returned'])
        self.assertEqual(final['spool.remaining_cm'] + final['spool.used_cm'], final['spool.length_cm'])
        self.assertEqual(final['bunting.location'], 'square_line' if final['layout.mode'] == 'square' else 'hall_rail')
        self.assertGreater(final['string.display_cm'], 0)

    def test_illegal_scene_and_failed_local_action_do_not_mutate_caller(self):
        params = Parameters()
        state = initial(params)
        original = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(params, state, 'choose_layout')
        self.assertEqual(state, original)
        play = LocalPlay(state, actors=('Leni',), validate=validate)
        saved_state, saved_events = deepcopy(play.state), deepcopy(play.events)
        with self.assertRaises(StoryError):
            play.act('illegal_unknown_change', **{'not.a.state.key': True})
        self.assertEqual(play.state, saved_state)
        self.assertEqual(play.events, saved_events)

    def test_scene_guards_and_endings_follow_the_selected_middle(self):
        square = Parameters(spool_length_cm=240, gusty=False, rainy=False,
                            posts_sturdy=True, jo_reach_cm=70, knot_slips=False)
        state = replay(square, ('borrow_spool', 'meet_neighbor', 'choose_layout',
                                'hang_bunting', 'welcome', 'return_spool'))[-1].after
        self.assertTrue(guard('ending_square', state))
        self.assertFalse(guard('ending_hall', state))
        finished = play_scene(square, state, 'ending_square').after
        self.assertFalse(guard('borrow_spool', finished))
        with self.assertRaises(StoryError):
            play_scene(square, state, 'ending_hall')

    def test_scene_ids_are_unique_and_replay_rejects_repetition(self):
        self.assertEqual(len(SCENES), len(set(SCENES)))
        with self.assertRaises(StoryError):
            replay(Parameters(), ('borrow_spool', 'borrow_spool'))


if __name__ == '__main__':
    unittest.main()
