# repaired100_canonical_luna_20260907

1000 Luna/Flex requests across 106 reference scripts.
Seed 2026090710; disjoint tasks; prompt custom_tool_python_v12; addendum None.
Raw and repaired sources, frozen requests, reference preflights, compressed samples, and judge responses are retained.
The per-world lineage/metrics catalog is `qc/worlds.jsonl` within the retained trial directory.

## Outcome

- Generated 998 distinct sources from 1,000 distinct task seeds. Two generation
  requests failed with Flex capacity errors. Luna used no reasoning and concurrency 50.
- Local QC attempted every world. The 1,000-sample command succeeded for 809;
  684 also passed verification; 566 additionally returned the full count, ran
  standalone, and replayed deterministically. The general repair pass accepted
  36 changes. A separate import-only pass accepted 589 changes, raising the
  sample-plus-verify count from 624 to 684 without changing existing sample pools.
- Terra/Flex attempted 683 eligible story sets and successfully rated **631
  worlds / 6,302 stories**. Mean quality is **5.900/9**; mean semantic diversity
  is **2.222/9**. There are 2,326 judged stories below 6/9 (36.9%).
- **52 worlds remain unrated:** 50 requests timed out after the Mac slept, and
  two returned invalid plot-group partitions. Failed/raw responses are retained;
  no judge request was resubmitted. The full-batch geometric score is withheld,
  not zero. In the raw score JSON, aggregate fields are uncomputed while status
  is `unrated`; use the separate candidate catalog for known yield counts.
- 339 worlds meet the world-average quality floor of 6/9, contributing 304,920
  returned positions and 237,237 distinct texts. Of these worlds, 274 also pass
  every strict local check; 263 of those did not need general automatic repairs.
  These are **curation candidates, not training-certified worlds**.
- Across all returned pools, 735,858 stories become 588,686 exact-unique texts,
  removing 20.0%. Story-only shuffled LZMA2/XZ compression is **1,063,611,670 to
  25,357,992 bytes (2.384%)**. After exact deduplication it is **853,523,617 to
  21,698,288 bytes (2.542%)**. Exact uniqueness therefore hides considerable
  reusable structure and wording; it does not establish distinct plots.
- Average length is **250.0 story words**, or **386.1 story-plus-story-QA words**.
  These averages cover all returned samples, including worlds that failed verify.
- Returned-usage cost is **$3.8847 generation + $7.1482 judging = $11.0329**.
  The two invalid judge responses are included. Timeout billing and underlying
  generation transport retries cannot be reconciled from returned usage alone.

## Interpretation

Do not train on this entire batch unchanged. The manual review finds repeated
name/role drift, grammar errors at template boundaries, and apparent endings
that do not resolve the stated problem. Some QA introduces unsupported facts
even when the story quality score is good. Terra judges story text, not QA.
Of the 36 general repairs, 27 include a guard-weakening rule and warrant special
review. Import-only repairs have a separate, stricter unchanged-output audit.

There are 104 syntax failures, all from completed, non-truncated API responses;
16 sampling timeouts; and 137 nonempty but underfilled pools. At least one
timeout comes from trying indefinitely to find 1,000 unique stories in a small
variation space. Some generated CLIs deduplicate internally, so returned pools
are not necessarily independent raw draws. No sampler was padded or rewritten
to hide that limitation.

The judge is broadly useful for separating prose quality from plot repetition,
but is sometimes generous about name drift and punctuation. Keep its evidence,
the local gates, and manual QA review together. Reference arms have only nine
or ten **different** seed tasks each; this is not a matched comparison of examples,
and aggregate compression is not directly comparable to a 21-world corpus.

Retained evidence under
`storyworlds/batches/prompt_trials/repaired100_canonical_luna_20260907/`:

- `manual_review.md`, plus raw/early/final reviewed sample JSON files.
- `qc/worlds.jsonl`: one lineage/metrics record per planned world, using only its
  effective sample pool. Raw/repaired snapshots are not extra training records.
- `qc/failure_census.json`, `qc/judge_failures.json`, and
  `qc/qualified_candidates.json`: actionable failure/candidate lists.
- `qc/set_judge/pass_001/`: exact judge requests, raw responses, attempt ledger,
  structured ratings, and the judge's per-world report.
- `qc/all_shuffled.stories.jsonl.xz` and `qc/exact_deduplicated.stories.jsonl.xz`:
  story-only compression artifacts, not filtered training exports.

Pipeline regression tests: **105 passed**. This tests the tooling, not the
correctness of all generated worlds. Historical batches were not overwritten.

## Local Gates

| Check | Worlds |
| --- | ---: |
| Materialized | 998/1000 |
| Raw ten-sample runnable | 756/1000 |
| Accepted automatic repairs | 36/1000 |
| Accepted import-path-only repairs | 589/1000 |
| Sample command + verify | 684/1000 |
| Also complete count, standalone CLI and deterministic replay | 566/1000 |
| Successfully judged | 631/1000 |

Quality is conditional on successfully judged worlds. Semantic diversity is a separate ten-story diagnostic.
The original geometric formula is unchanged; the stricter CLI/replay/count tally is reported separately.
Scoring also requires the judge's minimum of two returned stories; smaller sets are counted separately as ineligible, not assigned invented ratings.

| Example | Worlds | Sample + verify | Quality /9 | Diversity /9 | Exact unique draws | Composite /100 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| puddles | 10 | 6 | 5.883 | 0.333 | 1620 | 0.790 |
| pirates | 10 | 3 | 5.333 | 0.333 | 1202 | 0.780 |
| library | 10 | 6 | 5.050 | 1.000 | 1368 | 0.178 |
| cart | 10 | 5 | 6.620 | 0.800 | 880 | 0.885 |
| bridge | 10 | 7 | 6.357 | 0.571 | 2608 | 2.849 |
| nell | 10 | 5 | 6.720 | 0.200 | 679 | 0.207 |
| repaired_001 | 10 | 9 | 5.856 | 0.778 | 3495 | 2.480 |
| repaired_002 | 10 | 6 | 5.550 | 1.667 | 4625 | 2.310 |
| repaired_003 | 10 | 9 | 6.500 | 1.333 | 6937 | 8.551 |
| repaired_004 | 10 | 9 | 5.900 | 1.889 | 2942 | 3.147 |
| repaired_005 | 10 | 10 | 6.100 | 1.900 | 4133 | 2.769 |
| repaired_006 | 10 | 6 | 5.383 | 1.500 | 6281 | 3.523 |
| repaired_007 | 10 | 7 | 7.529 | 3.286 | 927 | 1.978 |
| repaired_008 | 10 | 9 | 5.644 | 2.333 | 4728 | 3.924 |
| repaired_009 | 10 | 9 | 5.989 | 2.222 | 9738 | 6.615 |
| garnet | 10 | 8 | 7.237 | 2.750 | 8000 | 13.039 |
| repaired_011 | 10 | 7 | 6.357 | 3.000 | 8000 | 7.609 |
| repaired_012 | 10 | 5 | 7.620 | 3.000 | 5081 | 6.180 |
| repaired_013 | 10 | 8 | 6.350 | 3.625 | 5598 | 8.111 |
| repaired_014 | 10 | 7 | 4.900 | 1.571 | 4842 | 0.094 |
| repaired_015 | 10 | 10 | 5.700 | 1.700 | 7233 | 5.052 |
| repaired_016 | 10 | 8 | 5.862 | 2.625 | 8025 | 6.284 |
| repaired_017 | 10 | 6 | 6.440 | 2.800 | 5995 | unrated |
| repaired_018 | 10 | 9 | 6.475 | 2.000 | 9262 | unrated |
| repaired_019 | 10 | 8 | 5.525 | 1.750 | 8755 | unrated |
| repaired_020 | 10 | 3 | 7.900 | 2.000 | 3553 | unrated |
| repaired_021 | 10 | 7 | 7.000 | 2.000 | 7097 | unrated |
| repaired_022 | 10 | 6 | 5.900 | 2.000 | 7384 | unrated |
| repaired_023 | 10 | 4 | - | - | 8026 | unrated |
| repaired_024 | 10 | 7 | - | - | 6056 | unrated |
| repaired_025 | 10 | 7 | - | - | 5545 | unrated |
| repaired_026 | 10 | 3 | - | - | 6135 | unrated |
| repaired_027 | 10 | 7 | 6.000 | 3.000 | 7296 | unrated |
| repaired_028 | 10 | 7 | 5.400 | 2.857 | 9139 | 3.217 |
| repaired_029 | 10 | 9 | 6.156 | 1.556 | 4017 | 3.603 |
| repaired_030 | 10 | 8 | 5.250 | 2.125 | 8608 | 2.949 |
| repaired_031 | 10 | 7 | 5.933 | 1.833 | 8543 | unrated |
| repaired_032 | 10 | 7 | 5.557 | 1.429 | 5440 | 0.835 |
| repaired_033 | 10 | 3 | 4.433 | 2.000 | 8000 | 0.000 |
| repaired_034 | 10 | 9 | 6.133 | 3.111 | 8911 | 7.716 |
| repaired_035 | 10 | 5 | 6.200 | 2.000 | 5063 | 3.561 |
| repaired_036 | 10 | 8 | 4.963 | 1.875 | 7138 | 2.178 |
| repaired_037 | 10 | 9 | 6.433 | 2.556 | 8160 | 10.582 |
| repaired_038 | 10 | 5 | 4.880 | 2.000 | 6000 | 2.642 |
| repaired_039 | 10 | 6 | 5.467 | 2.500 | 4232 | 3.205 |
| repaired_040 | 10 | 5 | 5.700 | 2.500 | 6925 | 3.288 |
| repaired_041 | 9 | 7 | 6.186 | 2.714 | 8576 | 5.710 |
| repaired_042 | 9 | 6 | 5.017 | 2.833 | 5003 | 0.000 |
| repaired_043 | 9 | 7 | 5.657 | 2.429 | 6633 | 6.605 |
| repaired_044 | 9 | 4 | 5.950 | 2.250 | 1504 | 0.639 |
| repaired_045 | 9 | 7 | 5.243 | 1.714 | 7695 | 5.520 |
| repaired_046 | 9 | 5 | 5.640 | 2.000 | 5340 | 3.095 |
| repaired_047 | 9 | 5 | 6.300 | 3.000 | 6144 | 7.155 |
| repaired_048 | 9 | 6 | 5.900 | 2.333 | 6215 | 6.293 |
| repaired_049 | 9 | 6 | 6.450 | 2.500 | 6405 | 7.086 |
| repaired_050 | 9 | 3 | 5.667 | 3.000 | 4810 | 0.955 |
| repaired_051 | 9 | 8 | 6.213 | 2.875 | 8000 | 8.474 |
| repaired_052 | 9 | 7 | 6.086 | 2.714 | 8000 | 7.229 |
| repaired_053 | 9 | 4 | 5.600 | 2.000 | 5801 | 3.011 |
| repaired_054 | 9 | 5 | 5.620 | 3.000 | 6982 | 1.927 |
| repaired_055 | 9 | 7 | 5.986 | 2.286 | 5891 | 4.858 |
| repaired_056 | 9 | 5 | 6.320 | 3.000 | 5987 | 7.016 |
| repaired_057 | 9 | 6 | 6.133 | 3.167 | 5220 | 4.661 |
| repaired_058 | 9 | 6 | 5.233 | 2.500 | 6000 | 3.532 |
| repaired_059 | 9 | 5 | 5.140 | 2.800 | 2237 | 0.684 |
| repaired_060 | 9 | 7 | 6.086 | 3.000 | 6800 | 7.163 |
| repaired_061 | 9 | 5 | 6.220 | 1.800 | 4647 | 2.377 |
| repaired_062 | 9 | 4 | 6.525 | 2.750 | 5672 | 6.943 |
| repaired_063 | 9 | 4 | 6.325 | 2.250 | 4000 | 3.860 |
| repaired_064 | 9 | 9 | 6.322 | 2.778 | 8256 | 9.979 |
| repaired_065 | 9 | 3 | 4.767 | 2.667 | 5978 | 0.000 |
| repaired_066 | 9 | 7 | 5.743 | 2.571 | 7995 | 7.867 |
| repaired_067 | 9 | 6 | 5.417 | 3.000 | 7380 | 2.836 |
| repaired_068 | 9 | 9 | 5.422 | 2.556 | 5801 | 2.437 |
| repaired_069 | 9 | 8 | 6.200 | 2.875 | 9000 | 9.617 |
| repaired_070 | 9 | 5 | 4.960 | 2.000 | 3272 | 0.702 |
| repaired_071 | 9 | 7 | 5.700 | 2.000 | 5166 | 4.123 |
| repaired_072 | 9 | 7 | 5.243 | 2.571 | 1921 | 1.591 |
| repaired_073 | 9 | 5 | 5.760 | 3.200 | 6675 | 3.591 |
| repaired_074 | 9 | 4 | 6.300 | 1.000 | 2939 | 3.029 |
| repaired_075 | 9 | 6 | 5.867 | 2.167 | 4304 | 3.104 |
| repaired_076 | 9 | 6 | 5.467 | 2.333 | 3035 | 3.489 |
| repaired_077 | 9 | 6 | 6.400 | 2.333 | 5689 | 3.201 |
| repaired_078 | 9 | 7 | 5.257 | 2.429 | 4170 | 3.142 |
| repaired_079 | 9 | 8 | 6.412 | 2.375 | 5611 | 6.036 |
| repaired_080 | 9 | 4 | 5.525 | 3.000 | 3984 | 3.131 |
| repaired_081 | 9 | 7 | 6.786 | 2.143 | 7600 | 9.267 |
| repaired_082 | 9 | 8 | 7.251 | 1.000 | 353 | 0.660 |
| repaired_083 | 9 | 7 | 6.250 | 2.667 | 5802 | unrated |
| repaired_084 | 9 | 8 | 5.388 | 2.625 | 7337 | 2.523 |
| repaired_085 | 9 | 5 | 5.600 | 2.200 | 4324 | 4.637 |
| repaired_086 | 9 | 8 | 5.438 | 1.750 | 8000 | 3.337 |
| repaired_087 | 9 | 9 | 5.633 | 1.556 | 3119 | 2.300 |
| repaired_088 | 9 | 4 | 4.950 | 3.000 | 3166 | 0.000 |
| repaired_089 | 9 | 7 | 5.600 | 1.857 | 7000 | 5.613 |
| repaired_090 | 9 | 7 | 6.900 | 3.286 | 4013 | 6.141 |
| repaired_091 | 9 | 6 | 6.317 | 2.500 | 2051 | 1.102 |
| repaired_092 | 9 | 8 | 5.487 | 2.500 | 8408 | 4.781 |
| repaired_093 | 9 | 3 | 7.067 | 2.000 | 3733 | 4.364 |
| repaired_094 | 9 | 8 | 5.787 | 1.500 | 2877 | 3.310 |
| repaired_095 | 9 | 7 | 5.243 | 2.429 | 6925 | 4.356 |
| repaired_096 | 9 | 7 | 5.129 | 1.714 | 3959 | 2.090 |
| repaired_097 | 9 | 6 | 6.133 | 2.500 | 3989 | 3.729 |
| repaired_098 | 9 | 7 | 6.114 | 3.143 | 6204 | 6.388 |
| repaired_099 | 9 | 6 | 5.883 | 1.000 | 2066 | 1.329 |
| repaired_100 | 9 | 6 | 5.633 | 2.333 | 8800 | 6.273 |

## Summary

```json
{
  "quality": {
    "protocol": "story_set_quality_v1",
    "model": "gpt-5.6-terra",
    "service_tier": "flex",
    "reasoning_effort": "none",
    "worlds": 683,
    "rated_worlds": 631,
    "rated_stories": 6302,
    "stories_below_six": 2326,
    "mean_quality": {
      "coherence": 6.182164392256427,
      "style": 5.365756902570612,
      "grammar": 6.062202475404633,
      "storytelling": 6.283243414788956,
      "overall": 5.900190415741035
    },
    "mean_diversity": {
      "premise": 2.6323296354992074,
      "causal_path": 2.294770206022187,
      "ending": 2.683042789223455,
      "language": 1.8684627575277337,
      "overall": 2.2218700475435815
    },
    "cost": {
      "pricing_date": "2026-09-07",
      "pricing_url": "https://developers.openai.com/api/docs/pricing",
      "requests": 683,
      "priced_requests": 633,
      "unpriced_requests": 50,
      "input_tokens": 2760797,
      "output_tokens": 616285,
      "usd_low": 7.1482315,
      "usd_high": 7.1482315,
      "note": "Returned-usage estimate only; unknown outcomes/retries may add cost. Missing cache writes are bounded."
    }
  },
  "dataset": {
    "policy": {
      "protocol": "quality_diversity_geometric_v1",
      "minimum_quality": 6.0,
      "formula": "100 * usable_unique_yield * sqrt(mean_quality/9 * compression_retention)",
      "duplicates": "exact story strings count once; use lowest qualifying source-world rating",
      "compression": "raw LZMA2, preset 6, empty-stream bytes subtracted",
      "dictionary_bytes": 67108864,
      "shuffle_seed": 0
    },
    "planned_worlds": 1000,
    "usable_worlds": 339,
    "unrated_worlds": 52,
    "runtime_rejected_worlds": 316,
    "quality_rejected_worlds": 292,
    "requested_samples": 1000000,
    "usable_samples": 0,
    "yield_fraction": null,
    "quality": null,
    "quality_mean": null,
    "diversity": null,
    "score": null,
    "status": "unrated",
    "insufficient_sample_set_worlds": 1,
    "minimum_samples_for_set_judge": 2
  },
  "pooled": {
    "dictionary_bytes": 67108864,
    "shuffle_seed": 0,
    "format": "XZ, story-only UTF-8 JSONL, LZMA2 preset 6",
    "variants": {
      "all_shuffled": {
        "stories": 735858,
        "input_bytes": 1063611670,
        "xz_bytes": 25357992,
        "ratio": 0.023841400687151168,
        "bytes_per_story": 34.460442096165295,
        "sha256": "19e04e5217b3269887cc6117f4c16ab5353add8b7513178f7d47b4c99e09c546"
      },
      "exact_deduplicated": {
        "stories": 588686,
        "input_bytes": 853523617,
        "xz_bytes": 21698288,
        "ratio": 0.02542201242921202,
        "bytes_per_story": 36.85884835039393,
        "sha256": "b5f7a2663e4038eadb15ac1e0e6fba23d2c242cf498b315e240183473d480bc1"
      }
    }
  },
  "lengths": {
    "mean_story_words": 249.9658480304624,
    "mean_story_qa_words": 386.11719788328725
  },
  "costs": {
    "generation": {
      "pricing_date": "2026-09-07",
      "pricing_url": "https://developers.openai.com/api/docs/pricing",
      "requests": 1000,
      "priced_requests": 998,
      "unpriced_requests": 2,
      "input_tokens": 10389720,
      "output_tokens": 4369438,
      "usd_low": 3.884660655,
      "usd_high": 3.884660655,
      "note": "Returned-usage estimate only; unknown outcomes/retries may add cost. Missing cache writes are bounded."
    },
    "judge": {
      "pricing_date": "2026-09-07",
      "pricing_url": "https://developers.openai.com/api/docs/pricing",
      "requests": 683,
      "priced_requests": 633,
      "unpriced_requests": 50,
      "input_tokens": 2760797,
      "output_tokens": 616285,
      "usd_low": 7.1482315,
      "usd_high": 7.1482315,
      "note": "Returned-usage estimate only; unknown outcomes/retries may add cost. Missing cache writes are bounded."
    }
  }
}
```
