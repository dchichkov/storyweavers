import unittest

import rank_reference_worlds as ranking


def world(name, *, quality=7, diversity=3, rated=True, samples=1000, runtime=True):
    return dict(script=name, runtime_ok=runtime, verify_ok=runtime, standalone_ok=runtime,
                replay_equal=True, samples=samples, requested_samples=1000, judge_ok=rated,
                quality=dict(overall=quality), diversity=dict(overall=diversity),
                exact_unique=samples, automatic_repair_accepted=False)


class ReferenceRankingTest(unittest.TestCase):
    def aggregate(self, worlds, **kwargs):
        return ranking.aggregate(dict(label="example", source="example.py"), worlds,
                                 dict(score=2, diversity=0.04), **kwargs)

    def test_means_are_world_weighted_and_failures_stay_in_yield_denominator(self):
        rows = [world("a", quality=8), world("b", quality=4, samples=4),
                world("failed", rated=False, samples=0, runtime=False)]
        r = self.aggregate(rows)
        self.assertEqual(r["quality_mean"], 6)
        self.assertEqual(r["strict_joint_successes"], 1)
        self.assertEqual(r["strict_joint_observed_bounds"], [1 / 3, 1 / 3])
        self.assertEqual(r["unrated_eligible"], 0)

    def test_missing_rating_is_unknown_not_zero_or_a_runtime_failure(self):
        r = self.aggregate([world("a"), world("unknown", rated=False)])
        self.assertEqual(r["quality_mean"], 7)
        self.assertEqual(r["strict_joint_unknown"], 1)
        self.assertEqual(r["strict_joint_observed_bounds"], [0.5, 1])
        self.assertIsNone(r["strict_joint_wilson95"])
        self.assertFalse(r["screening_eligible"])

    def test_unrated_non_strict_world_cannot_improve_strict_yield(self):
        r = self.aggregate([world("unknown", rated=False, samples=10)])
        self.assertIsNone(r["quality_mean"])
        self.assertEqual(r["strict_joint_unknown"], 0)

    def test_quality_and_diversity_must_pass_on_the_same_world(self):
        r = self.aggregate([world("quality", quality=8, diversity=1), world("diversity", quality=4, diversity=5)])
        self.assertEqual(r["strict_joint_successes"], 0)

    def test_incomplete_and_small_groups_do_not_win_primary_rankings(self):
        enough = self.aggregate([world(str(i)) for i in range(5)])
        singleton = self.aggregate([world("high", quality=9, diversity=9)])
        self.assertEqual(ranking.rankings([singleton, enough])["quality"], [enough])

    def test_wilson_and_sensitivity(self):
        lo, hi = ranking.wilson(7, 10)
        self.assertAlmostEqual(lo, 0.396778, places=5)
        self.assertAlmostEqual(hi, 0.892209, places=5)
        r = self.aggregate([world("a", quality=6, diversity=4), world("b", quality=7, diversity=3)])
        self.assertEqual(r["strict_q6_d4"], 1)
        self.assertEqual(r["strict_q7_d3"], 1)


if __name__ == "__main__":
    unittest.main()
