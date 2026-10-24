from copy import deepcopy
import json
import unittest

import replication_comparison as experiment


class ReplicationComparisonTests(unittest.TestCase):
    def test_balanced_all_positions_and_scope_only_change(self):
        rows = [dict(world=w, sample_id=f"{w}:{i}", story="Same story.", hidden="DO NOT SEND")
                for w in experiment.WORLD_ORDER for i in range(30)]
        jobs = experiment.pooled_jobs(rows)
        a, b = deepcopy(jobs[0]["body"]), deepcopy(jobs[1]["body"])
        a.pop("model")
        b.pop("model")
        self.assertEqual(a, b)
        self.assertEqual(len(jobs[0]["input"]["stories"]), 90)
        self.assertEqual(len(json.loads(a["input"][1]["content"])["stories"]), 90)
        self.assertNotIn("DO NOT SEND", json.dumps(a))
        self.assertIn("THREE independent", a["input"][0]["content"])
        self.assertNotIn("ONE procedural", a["input"][0]["content"])
        self.assertIn("Names, colors, objects swapped", a["input"][0]["content"])
        with self.assertRaises(ValueError):
            experiment.pooled_jobs(rows[:-1])

    def test_compression_keeps_duplicates_and_is_deterministic(self):
        rows = [dict(story="Same story.") for _ in range(100)]
        first, archive = experiment.corpus_stats(rows)
        self.assertEqual(experiment.corpus_stats(rows), (first, archive))
        self.assertEqual(first["positions"], 100)
        self.assertEqual(first["exact_unique"], 1)
        self.assertEqual(len(experiment.lzma.decompress(archive).splitlines()), 100)


if __name__ == "__main__":
    unittest.main()
