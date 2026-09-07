import math
import unittest
from unittest.mock import patch

import dataset_score as score


class DatasetScoreTest(unittest.TestCase):
    def setUp(self):
        self.checks = [dict(script="a", final=dict(ok=True), verify=dict(ok=True)),
                       dict(script="b", final=dict(ok=True), verify=dict(ok=True))]
        self.groups = [[dict(story=f"Ann found cup {i}.") for i in range(10)],
                       [dict(story=f"Bo planted tree {i}.") for i in range(10)]]
        self.ratings = {name: dict(ok=True, rating=dict(overall=8)) for name in ("a", "b")}

    def test_geometric_formula_equal_weight_and_coverage(self):
        with patch.object(score, "compression_retention", return_value=dict(retention=.25)):
            result = score.score_dataset(self.checks, self.ratings, self.groups, 10)
            self.assertAlmostEqual(result["score"], 100 * math.sqrt(8 / 9 * .25))
            self.groups[1] = self.groups[1][:5]
            result = score.score_dataset(self.checks, self.ratings, self.groups, 10)
            self.assertEqual(result["yield_fraction"], .75)
            self.assertAlmostEqual(result["score"], .75 * 100 * math.sqrt(8 / 9 * .25))

    def test_floor_excludes_bad_prose_from_compression_and_yield(self):
        self.ratings["b"]["rating"]["overall"] = 5
        with patch.object(score, "compression_retention", return_value=dict(retention=.25)) as compression:
            result = score.score_dataset(self.checks, self.ratings, self.groups, 10)
        self.assertEqual(result["quality_rejected_worlds"], 1)
        self.assertEqual(result["yield_fraction"], .5)
        self.assertEqual(result["quality_mean"], 8)
        self.assertAlmostEqual(result["score"], .5 * 100 * math.sqrt(8 / 9 * .25))
        self.assertEqual(compression.call_args.args[0], [row["story"] for row in self.groups[0]])

    def test_missing_rating_is_not_zero_or_silently_excluded(self):
        for invalid in ({}, dict(ok=False), dict(ok=True, rating=None),
                        dict(ok=True, rating=dict(overall=float("nan")))):
            self.ratings["b"] = invalid
            result = score.score_dataset(self.checks, self.ratings, self.groups, 10)
            self.assertIsNone(result["score"])
            self.assertEqual(result["status"], "unrated")
            self.assertEqual(result["unrated_worlds"], 1)

    def test_failed_world_reduces_yield_without_needing_judge(self):
        self.checks[1]["verify"]["ok"] = False
        del self.ratings["b"]
        result = score.score_dataset(self.checks, self.ratings, self.groups, 10)
        self.assertEqual(result["yield_fraction"], .5)
        self.assertEqual(result["status"], "complete")
        self.checks[0]["final"]["ok"] = False
        result = score.score_dataset(self.checks, {}, self.groups, 10)
        self.assertEqual(result["score"], 0)
        self.assertEqual(result["diversity"], 0)

    def test_overproduction_does_not_inflate_yield(self):
        self.groups[0] *= 2
        result = score.score_dataset(self.checks, self.ratings, self.groups, 10)
        self.assertEqual(result["usable_samples"], 20)
        self.assertEqual(result["yield_fraction"], 1)

    def test_quality_weighting_matches_contributing_samples(self):
        self.ratings["b"]["rating"]["overall"] = 6
        self.groups[1] = self.groups[1][:5]
        result = score.score_dataset(self.checks, self.ratings, self.groups, 10)
        self.assertAlmostEqual(result["quality_mean"], (8 * 10 + 6 * 5) / 15)

    def test_pooled_redundancy_not_average_of_world_scores(self):
        first = score.score_dataset(self.checks[:1], self.ratings, self.groups[:1], 10)
        self.groups[1] = self.groups[0]
        combined = score.score_dataset(self.checks, self.ratings, self.groups, 10)
        self.assertEqual(combined["diversity"], first["diversity"])
        self.assertEqual(combined["yield_fraction"], .5)
        self.assertEqual(combined["score"], first["score"] / 2)

    def test_repeating_output_cannot_improve_the_score(self):
        self.groups = [[dict(story="A single story.")], []]
        result = score.score_dataset(self.checks, self.ratings, self.groups, 10)
        self.groups[0] *= 10
        duplicated = score.score_dataset(self.checks, self.ratings, self.groups, 10)
        self.assertEqual(result["score"], duplicated["score"])
        self.assertEqual(duplicated["exact_duplicates_removed"], 9)

    def test_duplicate_text_uses_conservative_rating(self):
        self.groups[1] = self.groups[0]
        self.ratings["b"]["rating"]["overall"] = 6
        result = score.score_dataset(self.checks, self.ratings, self.groups, 10)
        self.assertEqual(result["quality_mean"], 6)

    def test_compression_recipe_order_invariance_and_duplicates(self):
        stories = [f"Child {i} found a {i * 37}-year-old map near the hill." for i in range(40)]
        result = score.compression_retention(stories)
        self.assertEqual(result, score.compression_retention(list(reversed(stories))))
        self.assertEqual(result["independent_bytes"], sum(map(score.individual_size, stories)))
        repeated = score.compression_retention([stories[0]] * 40)
        self.assertLess(repeated["retention"], result["retention"])
        self.assertEqual(score.compression_retention([stories[0]])["retention"], 1)
        data = score.encode_story(stories[0])
        self.assertEqual(score.compressed_size(data, 65536), score.compressed_size(data, score.DICTIONARY_BYTES))

    def test_input_and_policy_validation(self):
        for floor in (-1, 10, float("nan")):
            with self.assertRaises(ValueError):
                score.policy(floor)
        with self.assertRaises(ValueError):
            score.score_dataset(self.checks, self.ratings, [], 10)
        with self.assertRaises(ValueError):
            score.score_dataset(self.checks * 2, self.ratings, self.groups * 2, 10)
        with self.assertRaises(ValueError):
            score.compression_retention([""])


if __name__ == "__main__":
    unittest.main()
