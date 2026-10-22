from copy import deepcopy
import unittest

import world_batch as batch
from test_conversation_quality import sample, assessment


class WorldBatchTests(unittest.TestCase):
    def test_independent_balanced_predeclared_briefs(self):
        briefs = batch.briefs_for(17, 40)
        self.assertEqual(len(briefs), 400)
        self.assertEqual(len({b['world_id'] for b in briefs}), 400)
        self.assertEqual(len({b['seed'] for b in briefs}), 400)
        self.assertEqual(briefs, batch.briefs_for(17, 40))
        self.assertEqual(set(batch.Counter(b['theater'] for b in briefs).values()), {40})

    def test_three_uniform_positions_not_unique_text_selection(self):
        pool = [dict(story='Same story.') for _ in range(100)]
        selected = batch.f.quality.select_set('world', pool, 777, count=3)
        self.assertEqual(len(selected['stories']), 3)
        self.assertEqual(len({s['source_index'] for s in selected['stories']}), 3)

    def test_identical_duplicates_audited_without_changing_ratings(self):
        row = sample()
        value = assessment(row)
        value['stories'][0]['conversations'].append(deepcopy(value['stories'][0]['conversations'][0]))
        normalized, removed = batch.normalize_identical_duplicates(value)
        self.assertEqual(len(removed), 1)
        self.assertEqual(normalized, assessment(row))
        self.assertEqual(len(value['stories'][0]['conversations']), 2)
        batch.cq.validate(normalized, [row])

    def test_conflicting_duplicates_and_missing_ratings_still_fail(self):
        row = sample()
        value = assessment(row)
        duplicate = deepcopy(value['stories'][0]['conversations'][0])
        duplicate['rating']['overall'] = 3
        value['stories'][0]['conversations'].append(duplicate)
        normalized, removed = batch.normalize_identical_duplicates(value)
        self.assertFalse(removed)
        with self.assertRaises(ValueError): batch.cq.validate(normalized, [row])
        with self.assertRaises(ValueError): batch.cq.validate(dict(stories=[]), [row])


if __name__ == '__main__': unittest.main()
