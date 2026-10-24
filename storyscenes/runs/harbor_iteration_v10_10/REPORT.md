# Terra versus Luna: matched capability-story judging

Same selected stories, order, rubric, schema, token limits and reasoning=none; both Flex with store=false.
The requested Luna 6.1 ID was not listed; this comparison uses the explicitly confirmed gpt-6-luna.

| Judge | Stories graded | Story overall / 9 | Set diversity / 9 | QA overall / 9 | QA usable | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-terra | 10 | 7.900 | 5.000 | 8.967 | 59 / 60 | $0.03892-$0.03892 |
| gpt-6-luna | 10 | 8.000 | 6.000 | 8.783 | 58 / 60 | $0.00178-$0.00178 |

## Paired agreement

Deltas are Luna minus Terra; Terra is a comparator, not ground truth.

- story: 10 paired items; mean delta 0.100; mean absolute difference 0.100; within one point 1.000.
- qa: 60 paired items; mean delta -0.183; mean absolute difference 0.183; within one point 1.000.

## Scope and cost

One harbor generator, 10 predeclared seed positions, no literary filtering.
Local outputs: 10 exact unique; 8 mechanical signatures; outcomes {'rack': 1, 'two_trips': 2, 'timely_return': 1, 'labels_fixed': 2, 'both_plans': 2, 'pool': 1, 'late_return': 1}.
Up to six uniform supported questions per story, single-turn only; unchanged story and QA rubrics.
Each judge sees the ENTIRE story set in one request for quality and diversity; QA uses five-story batches.
Same literary rubric and rating dimensions, with output budget scaled to the required ratings.
Output format v2 attaches plot-group membership to each mandatory story rating; literary rubric unchanged.
Story and QA assessment.
Exact duplicates remain. LZMA is a redundancy diagnostic, not a calibrated semantic score.
The budget below is shared across all replication iterations, not a fresh allowance for every version.

Combined returned-usage estimate $0.04070-$0.04070; $3.06903 committed including unknown reservations, within $4.27.
Both arms reserve at conservative Terra rates before dispatch. Actual Luna costs use its own rates.
Rates: [official pricing](https://developers.openai.com/api/docs/pricing), checked 2026-10-22; estimates are not invoice reconciliation.
No automatic paid retries or fallback tiers. Failed/unknown requests remain saved.

Full grades, costs, paired disagreements and usability decisions: `comparison.json`.

Including the previous campaign: $3.80266 committed against the shared $5.00 authorization.
