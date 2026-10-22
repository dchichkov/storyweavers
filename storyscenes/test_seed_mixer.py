import random
import unittest
from seed_mixer import POOLS, WORDS, VOCAB_PATH, load_words, briefs_for, prose_directions


class SeedMixerTests(unittest.TestCase):
    def test_ten_distinct_pools_and_valid_combinations(self):
        self.assertEqual(len(POOLS), 10)
        for entries in POOLS.values():
            self.assertGreaterEqual(len(entries), 10)
            self.assertEqual(len(entries), len({key for key, _ in entries}))
        for brief in briefs_for(777, 100):
            self.assertEqual(len(brief['seed_mix']), 3)
            self.assertTrue(set(brief['seed_mix']) <= set(POOLS))
            for pool, choices in brief['seed_mix'].items():
                self.assertTrue(all((c['id'], c['hint']) in POOLS[pool] for c in choices))
                self.assertEqual(len(choices), len({c['id'] for c in choices}))
                self.assertEqual(len(choices), 1)
            self.assertNotIn('both kernels', brief['premise'])
            self.assertNotIn('two endings', brief['premise'])

    def test_repeatability_prefix_stability_and_rng_isolation(self):
        state = random.getstate()
        a = briefs_for(777, 1000)
        self.assertEqual(random.getstate(), state)
        self.assertEqual(a[:10], briefs_for(777, 10))
        self.assertGreater(len({b['premise'] for b in a}), 950)
        self.assertEqual({k for b in a for k in b['seed_mix']}, set(POOLS))
        self.assertEqual(len({b['world_id'] for b in a}), 1000)
        self.assertNotEqual(a[:10], briefs_for(778, 10))

    def test_prose_stage_retains_style_and_kernel_references(self):
        for brief in briefs_for(42, 30):
            directions = prose_directions(brief)
            import json
            self.assertEqual(json.loads(directions.split('\n')[-1]),
                             dict(ingredients=brief['seed_mix'], required_words=brief['words']))
            for pool in brief['seed_mix']:
                for choice in brief['seed_mix'][pool]:
                    self.assertIn(choice['id'], directions)
                    self.assertIn(choice['hint'], directions)
        self.assertEqual(prose_directions(dict(premise='Old theater seed.')), '')

    def test_required_words_are_distinct_childes_words_in_both_stages(self):
        lengths = set()
        for brief in briefs_for(20260909, 100):
            words = brief['words']; lengths.add(len(words))
            self.assertEqual(len(words), len(set(words)))
            self.assertTrue(set(words) <= set(WORDS))
            self.assertIn('Required words: ' + ', '.join(words), brief['premise'])
            for word in words:
                self.assertIn(word, prose_directions(brief))
            self.assertEqual(len(brief['seed_mix']), 3)
        self.assertEqual(lengths, {1, 2, 3})
        self.assertTrue(all('\t' not in word for word in WORDS))
        source = VOCAB_PATH.parent.parent / 'storyworlds/data/childes/childes_eng_na_vocab.txt'
        self.assertEqual(WORDS, load_words(source))


if __name__ == '__main__': unittest.main()
