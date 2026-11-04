'''Mechanical, replay, counterfactual, and continuity tests for the library pack.'''
from copy import deepcopy
import unittest

from storyscenes.runtime import StoryError
from storyscenes.mini_adventures.local_play import LocalPlay
from .world import Parameters, SCENES, generate, guard, initial, play_scene, replay, validate


class LibraryAdventureTests(unittest.TestCase):
    def audit_row(self, row):
        p = Parameters(**row['parameters'])
        episodes = replay(p, row['path'])
        self.assertEqual(episodes, row['episodes'])
        self.assertEqual(len(row['path']), row['scene_count'])
        self.assertEqual(len(set(row['path'])), len(row['path']))
        self.assertEqual(row['story'], '\n\n'.join(e['text'] for e in episodes))
        self.assertEqual(row['final_state'], episodes[-1]['after'])
        state = initial(p)
        for episode in episodes:
            self.assertEqual(episode['before'], state)
            self.assertTrue(guard(episode['id'], state))
            self.assertTrue(episode['events'])
            for event in episode['events']:
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
            self.assertEqual(state, episode['after'])
            self.assertGreaterEqual(len(episode['text'].split()), 40)
            self.assertLessEqual(len(episode['text'].split()), 70)
        self.assertTrue(state['story.ended'])
        self.assertTrue(state['story.outcome'])

    def test_both_lengths_over_one_hundred_seeds_and_exact_replay(self):
        endings = set()
        for seed in range(100):
            for count in (7, 8):
                row = generate(seed, count=count)
                self.audit_row(row)
                self.assertEqual(row, generate(seed, count=count))
                endings.add(row['final_state']['story.outcome'])
        self.assertEqual(endings, {'promise_kept', 'promise_not_kept_honestly'})

    def test_inventory_scene_ids_are_unique_and_complete(self):
        import json
        from pathlib import Path
        inventory = json.loads((Path(__file__).with_name('scene_inventory.json')).read_text(encoding='utf-8'))
        entries = inventory['scenes']
        ids = [entry['id'] for entry in entries]
        mapped = {scene for entry in entries for scene in entry['implemented_ids']}
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(mapped, set(SCENES))
        for entry in entries:
            for key in ('role', 'location', 'prerequisites', 'actions', 'consequences', 'prose_obligations', 'implemented_ids'):
                self.assertIn(key, entry)

    def test_parameters_reject_wrong_types_and_ranges(self):
        for kwargs in (
            {'closing_minutes': True}, {'closing_minutes': 6}, {'closing_minutes': 17},
            {'book_location': 'roof'}, {'catalog_current': 1}, {'ladder_stable': 'yes'},
            {'staff_available': 0}, {'trolley_wheel_ok': None},
        ):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                Parameters(**kwargs)
        for count in (True, 6, 9):
            with self.subTest(count=count), self.assertRaises(ValueError):
                generate(0, count=count)

    def test_illegal_actions_fail_without_mutating_caller_or_local_trace(self):
        p = Parameters()
        state = initial(p)
        saved = deepcopy(state)
        with self.assertRaises(StoryError):
            play_scene(p, state, 'returns_search')
        self.assertEqual(state, saved)
        play = LocalPlay(state, actors=('Lio',), validate=validate)
        local_state, local_events = deepcopy(play.state), deepcopy(play.events)
        with self.assertRaises(StoryError):
            play.act('borrow_without_permission', requires={'promise.status': 'made'}, **{'trolley.owner': 'Lio'})
        self.assertEqual(play.state, local_state)
        self.assertEqual(play.events, local_events)

    def test_optional_bookmark_is_not_secretly_executed(self):
        p = Parameters(book_location='returns_cart', closing_minutes=14)
        with_bookmark = (
            'promise', 'catalog', 'returns_search', 'bookmark_vignette',
            'window_vignette', 'friend_vignette', 'ending_found',
        )
        without_bookmark = (
            'promise', 'catalog', 'returns_search', 'window_vignette',
            'friend_vignette', 'shelf_vignette', 'ending_found',
        )
        with_state = replay(p, with_bookmark)[-1]['after']
        without_state = replay(p, without_bookmark)[-1]['after']
        self.assertTrue(with_state['friend.bookmark_vignette'])
        self.assertEqual(with_state['bookmark.location'], 'book')
        self.assertFalse(without_state['friend.bookmark_vignette'])
        self.assertEqual(without_state['bookmark.location'], 'Nia')
        self.assertNotEqual(with_state['friend.trust'], without_state['friend.trust'])

    def test_success_and_failure_preserve_object_location_and_trolley_use(self):
        success_params = Parameters(book_location='returns_cart', closing_minutes=14)
        success_path = ('promise', 'catalog', 'returns_search', 'bookmark_vignette',
                        'window_vignette', 'friend_vignette', 'ending_found')
        success = replay(success_params, success_path)[-1]['after']
        self.assertEqual(success['book.location'], 'Nia')
        self.assertEqual(success['book.borrower'], 'Nia')
        self.assertEqual(success['bookmark.location'], 'book')
        self.assertEqual(success['trolley.owner'], 'library')
        self.assertEqual(success['trolley.location'], 'return_bay')
        self.assertTrue(success['trolley.useful'])
        failure_params = Parameters(book_location='top_shelf', catalog_current=True,
                                    staff_available=False, ladder_stable=False, closing_minutes=14)
        failure_path = ('promise', 'catalog', 'librarian', 'returns_search',
                        'window_vignette', 'bookmark_vignette', 'ending_miss')
        failure = replay(failure_params, failure_path)[-1]['after']
        self.assertEqual(failure['book.location'], 'top_shelf')
        self.assertFalse(failure['book.found'])
        self.assertEqual(failure['friend.substitute_book'], 'The Cloud Garden')
        self.assertEqual(failure['bookmark.location'], 'Nia')
        self.assertEqual(failure['trolley.location'], 'return_bay')
        self.assertEqual(failure['story.outcome'], 'promise_not_kept_honestly')

    def test_paired_staff_and_ladder_counterfactual_changes_ending(self):
        unsafe = Parameters(book_location='top_shelf', catalog_current=True,
                            staff_available=False, ladder_stable=True, closing_minutes=14)
        safe = Parameters(book_location='top_shelf', catalog_current=True,
                          staff_available=True, ladder_stable=True, closing_minutes=14)
        failure = replay(unsafe, ('promise', 'catalog', 'librarian', 'returns_search',
                                  'window_vignette', 'bookmark_vignette', 'ending_miss'))[-1]['after']
        success = replay(safe, ('promise', 'catalog', 'librarian', 'ladder_search',
                                'bookmark_vignette', 'window_vignette', 'ending_found'))[-1]['after']
        self.assertFalse(failure['book.found'])
        self.assertTrue(success['book.found'])
        self.assertEqual(failure['story.outcome'], 'promise_not_kept_honestly')
        self.assertEqual(success['story.outcome'], 'promise_kept')

    def test_book_location_counterfactual_uses_same_scene_path(self):
        path = ('promise', 'catalog', 'returns_search', 'window_vignette',
                'bookmark_vignette', 'friend_vignette', 'ending_found')
        p_cart = Parameters(book_location='returns_cart', closing_minutes=14)
        p_window = Parameters(book_location='window_nook', closing_minutes=14)
        cart_eps = replay(p_cart, path)
        window_eps = replay(p_window, path)
        self.assertTrue(cart_eps[2]['after']['book.found'])
        self.assertFalse(window_eps[2]['after']['book.found'])
        self.assertTrue(window_eps[3]['after']['book.found'])
        self.assertNotEqual(cart_eps[3]['events'], window_eps[3]['events'])

    def test_catalogue_and_ladder_guards_change_available_actions(self):
        p = Parameters(book_location='top_shelf', catalog_current=True,
                       staff_available=True, ladder_stable=True)
        state = replay(p, ('promise', 'catalog'))[-1]['after']
        self.assertFalse(guard('ladder_search', state))
        state = replay(p, ('promise', 'catalog', 'librarian'))[-1]['after']
        self.assertTrue(guard('ladder_search', state))
        unsafe = Parameters(book_location='top_shelf', catalog_current=True,
                           staff_available=True, ladder_stable=False)
        unsafe_state = replay(unsafe, ('promise', 'catalog', 'librarian'))[-1]['after']
        self.assertFalse(guard('ladder_search', unsafe_state))

    def test_bad_replay_and_repeated_scene_are_rejected(self):
        p = Parameters()
        with self.assertRaises(StoryError):
            replay(p, ('promise', 'promise'))
        with self.assertRaises(StoryError):
            replay(p, ('promise', 'catalog', 'ending_found'))


if __name__ == '__main__':
    unittest.main()
