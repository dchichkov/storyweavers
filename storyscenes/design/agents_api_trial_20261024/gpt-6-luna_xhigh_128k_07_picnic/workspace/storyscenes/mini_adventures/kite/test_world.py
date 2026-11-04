from copy import deepcopy
from dataclasses import asdict
import subprocess
import sys
import unittest

from storyscenes.mini_adventures.kite.world import (
    LocalPlay, Parameters, SCENES, generate, guard, initial, parameters,
    play_scene, replay, validate,
)
from storyscenes.runtime import StoryError


CORE = ('borrow_blanket', 'spread_picnic', 'prepare_lunch', 'gust_response',
        'arrival', 'share_lunch')


class PicnicWorldTests(unittest.TestCase):
    def check_row(self, row):
        self.assertEqual(row['scene_count'], len(row['path']))
        self.assertEqual(len(row['path']), len(set(row['path'])))
        self.assertTrue(set(row['path']) <= set(SCENES))
        p = Parameters(**row['parameters'])
        episodes = replay(p, row['path'])
        reproduced = [asdict(ep) | {'events': list(ep.events)} for ep in episodes]
        self.assertEqual(reproduced, row['episodes'])
        self.assertEqual('\n\n'.join(ep.text for ep in episodes), row['story'])
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
                self.assertTrue(event['action'])
                self.assertTrue(event['changes'])
                for key, value in event['requires'].items():
                    self.assertEqual(state[key], value)
                for key, values in event['changes'].items():
                    self.assertEqual(state[key], values['before'])
                    self.assertNotEqual(values['before'], values['after'])
                    state[key] = deepcopy(values['after'])
                validate(state)
            self.assertEqual(state, episode.after)
        return episodes

    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        for seed in range(100):
            for count in (7, 8):
                with self.subTest(seed=seed, count=count):
                    row = generate(seed, count=count)
                    episodes = self.check_row(row)
                    self.assertEqual(len(episodes), count)
                    self.assertEqual(row['path'][:6], list(CORE))
                    if count == 7:
                        self.assertFalse({'reed_whistle', 'crumb_sparrows'} & set(row['path']))
                    else:
                        self.assertEqual(len({'reed_whistle', 'crumb_sparrows'} & set(row['path'])), 1)

    def test_parameter_validation_and_seeded_parameters(self):
        self.assertEqual(parameters(17), parameters(17))
        for kwargs in (
            {'blanket_weight': True}, {'blanket_weight': 0}, {'gust_force': 4},
            {'basket_latched': 1}, {'priority': 'either'}, {'bread_rolls': True},
            {'bread_rolls': 5}, {'delay_minutes': 31},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        for count in (True, 6, 9):
            with self.subTest(count=count), self.assertRaises(ValueError):
                generate(count=count)
        with self.assertRaises(ValueError):
            generate(seed=True)

    def test_illegal_scene_and_atomic_local_action_do_not_mutate_callers(self):
        p = Parameters()
        state = initial(p)
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(p, state, 'gust_response')
        self.assertEqual(state, saved)
        play = LocalPlay(state, actors=('Mara', 'Kit'), validate=validate)
        play_state, events = deepcopy(play.state), deepcopy(play.events)
        with self.assertRaises(StoryError):
            play.act('illegal_move', {'party.location': 'meadow'}, **{'story.ended': True})
        self.assertEqual(play.state, play_state)
        self.assertEqual(play.events, events)

    def test_three_parameter_recipes_reach_distinct_complete_endings(self):
        cases = (
            (Parameters(blanket_weight=3, gust_force=1, basket_latched=True,
                        priority='blanket', bread_rolls=3), 'ending_feast'),
            (Parameters(blanket_weight=1, gust_force=3, basket_latched=True,
                        priority='lunch', bread_rolls=3), 'ending_damp'),
            (Parameters(blanket_weight=3, gust_force=3, basket_latched=False,
                        priority='blanket', bread_rolls=3), 'ending_apples'),
        )
        for p, expected in cases:
            with self.subTest(ending=expected):
                row = generate(9, count=7, params=p)
                self.assertEqual(row['path'][-1], expected)
                self.check_row(row)

    def test_paired_counterfactual_changes_both_gust_effects_and_ending(self):
        blanket_first = Parameters(blanket_weight=1, gust_force=3, basket_latched=False,
                                   priority='blanket', bread_rolls=3)
        lunch_first = Parameters(blanket_weight=1, gust_force=3, basket_latched=False,
                                 priority='lunch', bread_rolls=3)
        a = generate(3, count=7, params=blanket_first)
        b = generate(3, count=7, params=lunch_first)
        self.assertEqual(a['path'][-1], 'ending_apples')
        self.assertEqual(b['path'][-1], 'ending_damp')
        self.assertTrue(a['final_state']['gust.blanket_wet'] is False)
        self.assertTrue(b['final_state']['gust.blanket_wet'])
        self.assertEqual(a['final_state']['food.lost'], 3)
        self.assertEqual(b['final_state']['food.lost'], 0)
        self.assertNotEqual(a['story'], b['story'])

    def test_optional_vignettes_are_guarded_and_have_only_enacted_effects(self):
        p = Parameters()
        base = initial(p)
        for scene_id in ('reed_whistle', 'crumb_sparrows'):
            with self.assertRaises(StoryError):
                play_scene(p, base, scene_id)
        after_core_start = replay(p, ('borrow_blanket', 'spread_picnic'))[-1].after
        reed = play_scene(p, after_core_start, 'reed_whistle')
        self.assertTrue(reed.after['reed.whistled'])
        self.assertEqual(after_core_start['cousins.mood'], 'steady')
        arrival_path = CORE[:5]
        before_arrival = replay(p, arrival_path)[-1].after
        arrived = play_scene(p, before_arrival, 'arrival').after
        crumbs = play_scene(p, arrived, 'crumb_sparrows')
        self.assertTrue(crumbs.after['sparrows.fed'])
        self.assertEqual(arrived['sparrows.fed'], False)

    def test_borrowed_object_and_locations_remain_continuous(self):
        p = Parameters(blanket_weight=2, gust_force=1, basket_latched=True)
        states = [initial(p)]
        state = states[0]
        for scene_id in CORE + ('ending_feast',):
            episode = play_scene(p, state, scene_id)
            state = episode.after
            states.append(state)
        self.assertEqual(states[1]['blanket.owner'], 'Aunt Salma')
        self.assertEqual(states[1]['blanket.holder'], 'Mara')
        self.assertEqual(states[2]['blanket.location'], 'meadow')
        self.assertEqual(states[-1]['blanket.location'], 'porch')
        self.assertEqual(states[-1]['blanket.holder'], 'Aunt Salma')
        self.assertFalse(states[-1]['blanket.borrowed'])
        self.assertTrue(states[-1]['blanket.clean'] and states[-1]['blanket.dry'])
        self.assertEqual(states[-1]['basket.location'], 'home')
        self.assertEqual(states[-1]['cousin.location'], 'home')

    def test_omitted_scenes_do_not_run_hidden_effects(self):
        row = generate(2, count=7, params=Parameters())
        self.assertFalse({'reed_whistle', 'crumb_sparrows'} & set(row['path']))
        state = row['final_state']
        self.assertFalse(state['reed.whistled'])
        self.assertFalse(state['sparrows.fed'])
        self.assertFalse(state['vignette.used'])

    def test_cli_prints_prose(self):
        result = subprocess.run(
            [sys.executable, '-m', 'storyscenes.mini_adventures.kite.world',
             '--seed', '0', '--scenes', '8'],
            check=True, capture_output=True, text=True,
        )
        self.assertGreater(len(result.stdout.split()), 250)
        self.assertIn('Rowan', result.stdout)


if __name__ == '__main__':
    unittest.main()
