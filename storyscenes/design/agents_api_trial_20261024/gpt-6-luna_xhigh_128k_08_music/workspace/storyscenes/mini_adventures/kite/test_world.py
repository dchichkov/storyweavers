from copy import deepcopy
import unittest

from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.runtime import StoryError
from .world import Parameters, SCENES, generate, guard, initial, play_scene, replay, validate


class MusicRoomTests(unittest.TestCase):
    def check_row(self, row):
        params = Parameters(**row['parameters'])
        self.assertEqual(len(row['path']), row['scene_count'])
        self.assertEqual(len(set(row['path'])), len(row['path']))
        self.assertEqual(set(row['path']), set(row['path']) & set(SCENES))
        self.assertEqual(row['story'], '\n\n'.join(e['text'] for e in row['episodes']))
        self.assertTrue(row['final_state']['story.ended'])
        self.assertTrue(row['final_state']['story.outcome'])
        state = initial(params)
        for scene_id, episode in zip(row['path'], row['episodes']):
            self.assertEqual(episode['id'], scene_id)
            self.assertEqual(episode['before'], state)
            self.assertTrue(guard(scene_id, state))
            self.assertGreaterEqual(len(episode['text'].split()), 40)
            self.assertLessEqual(len(episode['text'].split()), 70)
            self.assertTrue(episode['events'])
            for event in episode['events']:
                for key, value in event['requires'].items():
                    self.assertIn(key, state)
                    self.assertEqual(state[key], value)
                self.assertTrue(event['changes'])
                for key, change in event['changes'].items():
                    self.assertEqual(state[key], change['before'])
                    self.assertNotEqual(change['before'], change['after'])
                    state[key] = deepcopy(change['after'])
                validate(state)
            self.assertEqual(state, episode['after'])
        self.assertEqual(state, row['final_state'])
        self.assertEqual(replay(params, row['path']), row['episodes'])
        self.assertEqual(generate(row['seed'], count=row['scene_count'], params=params), row)

    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        for count in (7, 8):
            for seed in range(100):
                with self.subTest(count=count, seed=seed):
                    self.check_row(generate(seed, count=count))

    def test_invalid_parameters_and_request_types(self):
        for kwargs in (
            {'child': 'June', 'newcomer': 'June'},
            {'ribbon_length_cm': True},
            {'ribbon_length_cm': 9},
            {'room_busy': 1},
            {'chairs_ready': 'yes'},
            {'drum_head_taut': 0},
            {'child': '<Mara>'},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        for count in (True, 6, 9):
            with self.subTest(count=count), self.assertRaises(ValueError):
                generate(count=count)
        with self.assertRaises(ValueError):
            generate(seed=True)

    def test_illegal_actions_and_scenes_leave_the_caller_unchanged(self):
        params = Parameters()
        state = initial(params)
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(params, state, 'duet')
        self.assertEqual(state, saved)
        play = LocalPlay(state, actors=('Mara',), validate=validate)
        saved_state, saved_events = deepcopy(play.state), deepcopy(play.events)
        with self.assertRaises(StoryError):
            play.act('wrong_owner', {'drum.owner': 'Mara'}, **{'story.ended': True})
        self.assertEqual(play.state, saved_state)
        self.assertEqual(play.events, saved_events)

    def test_optional_vignettes_are_optional_and_length_bounded(self):
        seven = generate(0, count=7)
        self.assertFalse({'ribbon_cue', 'quiet_demo'} & set(seven['path']))
        for seed in range(20):
            eight = generate(seed, count=8)
            self.assertEqual(len({'ribbon_cue', 'quiet_demo'} & set(eight['path'])), 1)
        state = initial(Parameters())
        for scene in ('borrow_drum', 'newcomer_arrives', 'make_space', 'open_invitation',
                      'pass_for_now', 'listening_pattern', 'ending_listening'):
            state = play_scene(Parameters(), state, scene)['after']
        self.assertFalse(state['vignette.ribbon_done'])
        self.assertFalse(state['newcomer.heard_demo'])

    def test_borrowed_object_location_and_usefulness_are_continuous(self):
        params = Parameters()
        state = initial(params)
        states = [state]
        for scene in ('borrow_drum', 'newcomer_arrives', 'make_space', 'open_invitation',
                      'accept_beat', 'duet', 'ending_duet'):
            state = play_scene(params, state, scene)['after']
            states.append(state)
        self.assertTrue(states[1]['drum.borrowed'])
        self.assertEqual((states[1]['drum.owner'], states[1]['drum.location']), ('Mara', 'child'))
        self.assertTrue(states[5]['music.completed'])
        self.assertEqual(states[5]['music.outcome'], 'duet')
        self.assertEqual((state['drum.owner'], state['drum.location']), ('Ms Vale', 'shelf'))
        self.assertFalse(state['drum.borrowed'])
        self.assertTrue(state['story.ended'])

    def test_busy_room_counterfactual_changes_join_availability(self):
        params = Parameters(room_busy=True)
        state = initial(params)
        for scene in ('borrow_drum', 'newcomer_arrives', 'make_space', 'open_invitation'):
            state = play_scene(params, state, scene)['after']
        self.assertFalse(guard('accept_beat', state))
        self.assertTrue(guard('pass_for_now', state))
        state = play_scene(params, state, 'pass_for_now')['after']
        self.assertEqual(state['newcomer.choice'], 'listen')

        supported = initial(params)
        for scene in ('borrow_drum', 'newcomer_arrives', 'make_space', 'quiet_demo', 'open_invitation'):
            supported = play_scene(params, supported, scene)['after']
        self.assertTrue(guard('accept_beat', supported))
        self.assertEqual(play_scene(params, supported, 'accept_beat')['after']['newcomer.choice'], 'join')

    def test_drum_and_ribbon_parameters_change_enacted_actions(self):
        base_path = ('borrow_drum', 'newcomer_arrives', 'make_space', 'open_invitation', 'accept_beat')
        action_lists = []
        for taut in (True, False):
            params = Parameters(drum_head_taut=taut)
            state = initial(params)
            for scene in base_path:
                state = play_scene(params, state, scene)['after']
            action_lists.append([event['action'] for event in play_scene(params, state, 'duet')['events']])
        self.assertNotEqual(action_lists[0], action_lists[1])
        ribbon_actions = []
        for length in (18, 48):
            params = Parameters(ribbon_length_cm=length)
            state = initial(params)
            for scene in ('borrow_drum', 'newcomer_arrives', 'make_space', 'ribbon_cue'):
                episode = play_scene(params, state, scene)
                state = episode['after']
            ribbon_actions.append(episode['events'][0]['action'])
        self.assertNotEqual(ribbon_actions[0], ribbon_actions[1])

    def test_both_endings_are_distinct_and_replayable(self):
        params = Parameters(room_busy=False)
        duet_path = ('borrow_drum', 'newcomer_arrives', 'make_space', 'open_invitation',
                     'accept_beat', 'duet', 'ending_duet')
        listen_path = ('borrow_drum', 'newcomer_arrives', 'make_space', 'open_invitation',
                       'pass_for_now', 'listening_pattern', 'ending_listening')
        duet = replay(params, duet_path)[-1]['after']
        listen = replay(params, listen_path)[-1]['after']
        self.assertEqual(duet['story.outcome'], 'a freely chosen duet')
        self.assertEqual(listen['story.outcome'], 'a welcome without a duet')
        self.assertNotEqual(duet['music.outcome'], listen['music.outcome'])
        self.assertTrue(duet['story.ended'] and listen['story.ended'])


if __name__ == '__main__':
    unittest.main()
