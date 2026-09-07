# Nell and the Dragon: Protocol Evaluation

## Status

Completed after the user explicitly authorized the external submission.
**One API call** to `gpt-5.6-terra` completed on Flex, with no retries or
reasoning tokens. All ten story ratings and the plot-group partition passed
validation. The earlier approval rejection occurred before execution and made
no API request; its local report is retained separately.

The frozen request uses the unchanged `story_set_quality_v1`: ten uniformly
sampled raw positions, selection seed 777, no deduplication, reasoning `none`,
900-second timeout, no automatic retry or standard-tier fallback. Only stories
and the standard calibration enter the request, not source code, QA, or traces.
Returned usage was **9,428 input + 894 output tokens**, including 9,425
cache-write tokens, no cache reads, and no reasoning tokens. The token-based
cost estimate using the saved protocol rates is **$0.01714825**. The request
took 8.962 seconds. This is a usage estimate, not invoice reconciliation.

## Judge Results

| Quality Dimension | Mean / 9 |
| --- | ---: |
| Coherence | 9 |
| Style | 8 |
| Grammar | 9 |
| Storytelling | 9 |
| Overall | **9** |

All ten overall ratings were 9: minimum 9, standard deviation 0, none below
the 6/9 floor. The rubric calls 9 "good"; this does not prove flawless writing.
These ten ratings share one request context and are not ten independent judge
replications. They are slightly above Garnet's earlier 8.9 and above Puddles'
8.0, but the 0.1 difference from Garnet is not evidence of a reliable ranking.

| Semantic Diversity Dimension | Score / 9 |
| --- | ---: |
| Premise | 1 |
| Causal path | 2 |
| Ending | 1 |
| Language | 2 |
| Overall | **1** |

Terra grouped **all ten stories into one plot group**. It recognized that wire,
wool, and button change the bird's immediate need, but the request, observation,
exchange, returned jewel, and story-payment coda remain the same. Its positive
notes emphasize witty dialogue, character, a consequential useful-object
exchange, and a visible resolution in the dragon's claw.

This agrees with the manual distinction: strong individual prose, little new
narrative structure across the set. The judge did not flag the manually noted
underexplained anchor in the wire-loop repair. Keep the evidence and source
checks alongside the generous numerical ratings.

## Local Results

The retained 1,000-story pool uses seed `20260907`, rather than the canonical
reference pool's generation seed 777. Selection seed and scoring algorithms are
matched. A fresh 1,000-story run reproduced the retained pool exactly. A bare
CLI replay with a different `PYTHONHASHSEED` also matched. Source hashes match;
the source was not edited or repaired for this evaluation.

| Metric | Result |
| --- | ---: |
| Runtime samples | 1,000 / 1,000 |
| Own verification | 18 states passed; Python/ASP offer eligibility agrees |
| Exact unique story strings | 72 / 1,000 (7.2%) |
| Slot-normalized unique strings | 18 |
| All-story XZ / raw | 0.795% |
| Cross-story compression retention D | 4.0374% |
| Mean story words | 501.2 |
| Mean story + QA words | 705.0 |
| QA pairs / unique normalized pairs | 5,505 / 14 |
| Static duplicate QA groups | 14 |
| Static source-matching hits | 0 |
| Quality / semantic diversity | 9/9 / 1/9 |
| Geometric composite | **1.4467 / 100** |

The 14 repeated QA groups are across the full pool, not 14 duplicate questions
inside each story. Zero static source hits does not mean the answers lack
templated text: they are assembled through recorded events, which the source
matcher cannot resolve into exact strings. The Terra protocol grades story
prose and cross-story diversity; it does not grade QA correctness.

The compression term uses **4,052 pooled bytes / 100,361 independently compressed
bytes** for the 72 distinct stories. It is not the all-text XZ/raw ratio.
The measured world quality of 9/9 passes the quality floor, so all 72 distinct
stories qualify. The current index is:

```text
100 * 0.072 * sqrt(1 * 0.04037424896) = 1.4467 / 100
```

This is the measured dataset composite, not an individual story-quality score.
Semantic diversity 1/9 is reported separately; it is not a hidden factor in
this formula. The index strongly penalizes repeatedly sampling a generator
with only 72 possible exact strings: 928 repetitions are discarded, and
substantial reuse remains among the distinct strings. It should not be read
as a claim that the individual story is poor.
For context, the earlier reference run scored Puddles 22.22, Pirates 22.28,
and Garnet 19.15, with much higher exact-unique yields.

## Reading Assessment

All ten selected texts were read before the attempted judge submission. The
authoring assistant's reading is favorable on voice, dialogue, and the coherent
problem/solution arc, but it is not an independent blind judgment. Most text is
shared. Every sample follows request, unsuitable ruby, observation, useful
small offer, space and patience, nest replacement, catch, and promised story.
The fastener branch could explain the loop's physical anchor more explicitly.

The sample includes five fastener cases, three soft-lining cases, and two shiny
button cases. Five include the interruption. It covers five of the six authored
need/approach combinations; shine/patient is absent. Names and jewels add no
independent plot. The subsequent numerical results match that qualitative
expectation of good individual prose with low narrative diversity.

## Retained Artifacts

New evaluation directory: `storyworlds/batches/nell_dragon_quality_20260907/`.
It holds `evaluate.py`, unchanged source and scoring-module snapshots, fresh
checks, static QA findings, pooled compression archives, selected stories,
exact request preflight, cost estimate, manual notes written before judging,
and the completed `dataset_score.json`. `terra/` holds the exact submitted
request, durable attempt record, raw response, validated ratings, and usage
summary. `report_before_authorization.md` and `preauthorization_local_result.json`
preserve the earlier blocked status as historical snapshots.

The full source/sample pool remains in `nell_dragon_20260907/` and its verified
existing archive, described in the [local adaptation report](nell_dragon_20260907.report.md).
The source/sample archive and previous canonical scores remain unchanged.
This evaluation is archived separately as
`storyworlds/batch_archives/nell_dragon_quality_20260907_terra.tar.gz`, with a
SHA256 sidecar and the repository's existing Git LFS rule. It contains the new
evaluation directory and this report; the full 1,000-story source pool remains
in its existing archive rather than being copied again.
