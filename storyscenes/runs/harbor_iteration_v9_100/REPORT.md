# Terra versus Luna: matched capability-story judging

Same selected stories, order, rubric, schema, token limits and reasoning=none; both Flex with store=false.
The requested Luna 6.1 ID was not listed; this comparison uses the explicitly confirmed gpt-6-luna.

| Judge | Stories graded | Story overall / 9 | Set diversity / 9 | QA overall / 9 | QA usable | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-terra | 100 | 8.000 | 5.000 | 8.910 | 554 / 566 | $0.34493-$0.34493 |
| gpt-6-luna | 100 | 7.960 | 5.000 | 8.694 | 446 / 477 | $0.01392-$0.01392 |

## Paired agreement

Deltas are Luna minus Terra; Terra is a comparator, not ground truth.

- story: 100 paired items; mean delta -0.040; mean absolute difference 0.040; within one point 1.000.
- qa: 477 paired items; mean delta -0.220; mean absolute difference 0.275; within one point 0.960.

## Scope and cost

One harbor generator, 100 predeclared seed positions, no literary filtering.
Local outputs: 96 exact unique; 30 mechanical signatures; outcomes {'rack': 9, 'two_trips': 3, 'late_return': 11, 'correct_delivery': 2, 'helped_delivery': 22, 'labels_fixed': 23, 'basin': 5, 'timely_return': 10, 'pool': 11, 'declined': 4}.
Six uniform supported questions per story, single-turn only; unchanged story and QA rubrics.
Each judge sees the ENTIRE story set in one request for quality and diversity; QA uses five-story batches.
Same literary rubric and rating dimensions, with output budget scaled to the required ratings.
Output format v2 attaches plot-group membership to each mandatory story rating; literary rubric unchanged.
Story and QA assessment.
Exact duplicates remain. LZMA is a redundancy diagnostic, not a calibrated semantic score.
The budget below is shared across all replication iterations, not a fresh allowance for every version.

Combined returned-usage estimate $0.35886-$0.35886; $2.12040 committed including unknown reservations, within $4.27.
Both arms reserve at conservative Terra rates before dispatch. Actual Luna costs use its own rates.
Rates: [official pricing](https://developers.openai.com/api/docs/pricing), checked 2026-10-22; estimates are not invoice reconciliation.
No automatic paid retries or fallback tiers. Failed/unknown requests remain saved.

Full grades, costs, paired disagreements and usability decisions: `comparison.json`.

Including the previous campaign: $2.85402 committed against the shared $5.00 authorization.
