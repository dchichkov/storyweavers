from copy import deepcopy
import unittest
from storyscenes.runtime import StoryError
from storyscenes.mini_adventures.local_play import LocalPlay
from storyscenes.mini_adventures.review import verify_row
from storyscenes.mini_adventures.kite import world as w


class KiteTests(unittest.TestCase):
    def test_hundred_seeds_both_lengths(self):
        for seed in range(100):
            for count in (7, 8):
                row = w.generate(seed, count=count)
                verify_row(w, row, seed, count)
                for e in row['episodes']:
                    self.assertTrue(38 <= len(e['text'].split()) <= 75)
                    w.validate(e['after'])
                self.assertEqual(row['final_state']['reel.owner'], 'nan')
                self.assertEqual(row['final_state']['reel.holder'], 'nan')
                self.assertEqual(row['final_state']['party.location'], 'workshop')

    def test_illegal_atomic(self):
        s = w.initial(w.Parameters())
        saved = deepcopy(s)
        with self.assertRaises(StoryError):
            w.play_scene(w.Parameters(), s, 'field')
        self.assertEqual(s, saved)
        x = LocalPlay(s, actors=('mara',), validate=w.validate)
        with self.assertRaises(StoryError):
            x.act('steal', **{'reel.owner': 'mara'})
        self.assertEqual(x.state, saved)
        self.assertEqual(x.events, [])

    def test_invalid(self):
        for kw in ({'wind': True}, {'wind': 3}, {'gentle': 1}, {'frayed': 'yes'}, {'mend': None}):
            with self.assertRaises(ValueError):
                w.Parameters(**kw)
        for count in (6, 9, True):
            with self.assertRaises(ValueError):
                w.generate(count=count)

    def test_counterfactuals(self):
        base = w.Parameters(wind=1, gentle=True, frayed=True, mend=True)
        self.assertEqual(w.generate(params=base)['final_state']['story.outcome'], 'shared_flight')
        for p in (w.Parameters(wind=0), w.Parameters(gentle=False), w.Parameters(mend=False)):
            row = w.generate(params=p)
            self.assertEqual(row['final_state']['story.outcome'], 'shared_table')
            self.assertFalse(row['final_state']['kite.flew'])
            self.assertTrue(row['final_state']['reel.sound'])
        deferred = w.replay(w.Parameters(mend=False), ['welcome', 'borrow'])[-1]
        self.assertFalse(deferred['after']['reel.sound'])

    def test_optional_omission(self):
        p = w.Parameters()
        prefix = ['welcome', 'borrow', 'invite']
        end = ['field', 'return', 'ending_air']
        without = w.replay(p, prefix + end)[-1]['after']
        self.assertFalse(without['ivo.bird_seen'])
        self.assertFalse(without['kite.decorated'])
        for optional, key in [('bird', 'ivo.bird_seen'), ('window', 'kite.decorated')]:
            with_it = w.replay(p, prefix + [optional] + end)[-1]['after']
            self.assertEqual({k for k in without if without[k] != with_it[k]}, {key})
        with self.assertRaises(StoryError):
            w.replay(p, prefix + ['bird', 'bird'])


if __name__ == '__main__':
    unittest.main()
