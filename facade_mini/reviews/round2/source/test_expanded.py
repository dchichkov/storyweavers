"""Regression checks for actual new narrative affordances, not just output shape."""
import json
from pathlib import Path
import threading
import unittest
from urllib.error import HTTPError
from urllib.request import Request, build_opener, HTTPCookieProcessor

from engine import Session, replay
from play import run_demo
from serve import DramaServer, view
from test_drama import assert_world


def play(*commands):
    session = Session()
    session.start()
    for command in commands:
        session.step(command)
    return session


class ExpandedDramaTests(unittest.TestCase):
    def test_private_fact_does_not_reach_absent_partner(self):
        for who, other, fact in (("mara", "eli", "letter"), ("eli", "mara", "receipt")):
            with self.subTest(who=who):
                s = play("listen", "talk " + who, "ask work")
                self.assertTrue(s.state['people']['player']['knows'][fact])
                self.assertFalse(s.state['people'][other]['knows'][fact])
                self.assertFalse(s.state['people'][who]['disclosed'])
                event = s.events[-1]
                self.assertEqual(event['audience'], sorted([who, 'player']))
                self.assertFalse(any(line.startswith(other.title() + ':') for line in event['lines']))
                assert_world(self, s)

    def test_private_listening_does_not_execute_public_goals(self):
        s = play('listen', 'talk mara')
        current = s.active, s.cursor
        s.step('ask work')
        s.step('ask fear')
        self.assertEqual(current, (s.active, s.cursor))
        self.assertEqual(s.state['people']['eli']['location'], 'dining_room')

    def test_private_topic_tiers_belong_to_individual_characters(self):
        s = play('listen', 'talk mara', 'ask work', 'return', 'talk eli', 'ask work')
        self.assertEqual(s.private_tiers['mara']['work'], 1)
        self.assertEqual(s.private_tiers['eli']['work'], 1)
        self.assertTrue(s.state['people']['player']['knows']['receipt'])
        self.assertFalse(s.state['people']['mara']['knows']['receipt'])

    def test_promised_owner_disclosure_is_not_betrayal(self):
        s = play('empathize mara', 'talk mara', 'ask work', 'promise privacy', 'encourage honesty', 'return')
        self.assertTrue(s.state['people']['eli']['knows']['letter'])
        self.assertFalse(s.state['people']['player']['betrayal'])
        self.assertEqual(s.events[-1]['source'], 'mara.voluntary_disclosure')

    def test_betrayal_preempts_topic_and_apology_does_not_erase_it(self):
        s = play('empathize mara', 'talk mara', 'ask work', 'promise privacy', 'return')
        old = s.active
        s.step('tell mara')
        self.assertIn(old, s.aborted)
        self.assertEqual(s.phase(), 'crisis')
        s.step('apologize')
        self.assertEqual(s.active, 'privacy_crisis')
        self.assertTrue(s.state['people']['mara']['privacy_breached'])
        self.assertIn('broke a confidence', '\n'.join(s.transcript))
        while not s.outcome:
            s.step('listen')
        self.assertEqual(s.outcome, 'broken_confidence')
        self.assertNotIn('cold_dinner', s.completed)

    def test_breach_without_explicit_promise_is_still_recorded(self):
        s = play('listen', 'talk eli', 'ask work', 'return', 'tell eli')
        self.assertTrue(s.state['people']['player']['betrayal'])
        self.assertFalse(s.state['people']['player']['promises']['eli'])
        self.assertIn("wasn't yours to announce", '\n'.join(s.transcript))

    def test_new_offense_accepts_new_apology_but_old_one_cannot_be_farmed(self):
        s = play('blame mara', 'apologize')
        first = s.state['people']['mara']['trust_player']
        s.step('apologize')
        self.assertEqual(first, s.state['people']['mara']['trust_player'])
        s.step('blame mara')
        self.assertEqual(s.state['people']['mara']['offenses'], 2)
        s.step('apologize')
        self.assertEqual(s.state['people']['mara']['forgiven'], 2)
        self.assertEqual(s.state['people']['eli']['forgiven'], 0)
        self.assertLessEqual(s.state['people']['mara']['trust_player'], first)

    def test_owner_initiative_can_repair_without_reflect_or_mediate(self):
        for name in ('initiative', 'private'):
            s = run_demo(name)
            self.assertEqual(s.outcome, 'repair')
            self.assertFalse(any(c.startswith('reflect') or c == 'mediate' for c in s.commands))
            self.assertIn('mutual_proposal', [e['source'] for e in s.events])

    def test_practical_route_needs_details_but_not_empathy_or_reflection(self):
        s = run_demo('practical')
        self.assertEqual(s.outcome, 'practical')
        self.assertFalse(any(c.startswith(('reflect', 'empathize')) for c in s.commands))
        self.assertTrue(all(s.state['people'][who]['commitment'] for who in ('mara', 'eli')))
        blocked = play('listen', 'ask letter', 'ask letter', 'ask receipt', 'ask receipt', 'plan refund', 'plan visit')
        self.assertFalse(any(blocked.state['people'][who]['commitment'] for who in ('mara', 'eli')))

    def test_responsibility_cannot_be_awarded_twice_via_different_routes(self):
        s = play('empathize mara', 'empathize eli', 'open floor', 'listen')
        self.assertTrue(s.state['people']['mara']['accountable'])
        before = s.state['people']['eli']['trust_partner']
        lines = s.step('reflect mara')
        self.assertEqual(before, s.state['people']['eli']['trust_partner'])
        self.assertNotIn('first time', '\n'.join(lines))

    def test_private_silence_has_progression_and_character_returns(self):
        s = play('listen', 'talk mara')
        one = s.step('listen')
        two = s.step('listen')
        three = s.step('listen')
        self.assertNotEqual(one, two)
        self.assertIsNone(s.private_with)
        self.assertTrue(any('go back' in line for line in three))
        assert_world(self, s)

    def test_private_deadline_and_departure_return_to_shared_room_first(self):
        for forced in (False, True):
            s = play('listen', 'talk mara', 'ask work')
            if forced:
                s.step('leave')
            else:
                while not s.outcome:
                    s.step('ask work')
            self.assertIsNone(s.private_with)
            self.assertEqual(s.state['people']['mara']['location'], 'dining_room')
            self.assertEqual(s.state['people']['player']['location'], 'hallway')
            self.assertEqual(s.outcome, 'left' if forced else 'unresolved')
            assert_world(self, s)

    def test_partial_save_replays_private_room_and_memory(self):
        s = play('empathize mara', 'talk mara', 'ask work', 'promise privacy')
        restored = replay(json.loads(json.dumps(s.export())))
        self.assertEqual(restored.export(), s.export())
        for command in ('encourage honesty', 'return', 'listen'):
            self.assertEqual(restored.step(command), s.step(command))
        self.assertEqual(restored.export(), s.export())

    def test_browser_suggestions_do_not_spoil_unrevealed_terms(self):
        s = play()
        public = view(s)
        self.assertNotIn('plan refund', public['actions'])
        self.assertNotIn('plan visit', public['actions'])
        self.assertNotIn('reflect mara', public['actions'])
        self.assertNotIn('world', public)
        self.assertNotIn('before', public['events'][0])


class BrowserServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = DramaServer(('127.0.0.1', 0))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = 'http://127.0.0.1:' + str(cls.server.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.thread.join()
        cls.server.server_close()

    def setUp(self):
        self.client = build_opener(HTTPCookieProcessor())

    def get(self, path):
        return self.client.open(self.url + path).read()

    def post(self, path, body, token=True):
        headers = {'Content-Type': 'application/json'}
        if token:
            headers['X-Drama-Token'] = self.server.csrf
        request = Request(self.url + path, json.dumps(body).encode(), headers)
        return json.loads(self.client.open(request).read())

    def test_action_save_load_and_session_isolation(self):
        self.get('/')
        self.post('/api/action', {'command': 'listen'})
        saved = json.loads(self.get('/api/trace'))
        self.post('/api/new', {'seed': 4})
        restored = self.post('/api/load', {'record': saved})
        self.assertEqual(restored['turn'], 1)
        other = build_opener(HTTPCookieProcessor())
        independent = json.loads(other.open(self.url + '/api/state').read())
        self.assertEqual(independent['turn'], 0)

    def test_reject_bad_replay_and_cross_site_mutation(self):
        self.get('/')
        with self.assertRaises(HTTPError) as error:
            self.post('/api/action', {'command': 'leave'}, token=False)
        self.assertEqual(error.exception.code, 403)
        with self.assertRaises(HTTPError) as error:
            self.post('/api/load', {'record': {'schema': 2, 'seed': 0, 'commands': ['made up']}})
        self.assertEqual(error.exception.code, 400)
        state = json.loads(self.get('/api/state'))
        self.assertEqual(state['turn'], 0)

    def test_unsupported_action_is_not_an_implicit_social_act(self):
        self.get('/')
        with self.assertRaises(HTTPError) as error:
            self.post('/api/action', {'command': 'not support mara'})
        self.assertEqual(error.exception.code, 409)
        self.assertEqual(json.loads(self.get('/api/state'))['turn'], 0)


if __name__ == '__main__':
    unittest.main()
