# Terra versus Luna: matched capability-story judging

Same selected stories, order, rubric, schema, token limits and reasoning=none; both Flex with store=false.
The requested Luna 6.1 ID was not listed; this comparison uses the explicitly confirmed gpt-6-luna.

| Judge | Stories graded | Story overall / 9 | Set diversity / 9 | QA overall / 9 | QA usable | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-terra | 100 | 8.000 | 4.000 | 8.978 | 599 / 600 | $0.34015-$0.34015 |
| gpt-6-luna | 100 | 8.000 | 3.000 | 8.780 | 512 / 540 | $0.01483-$0.01483 |

## Paired agreement

Deltas are Luna minus Terra; Terra is a comparator, not ground truth.

- story: 100 paired items; mean delta 0.000; mean absolute difference 0.000; within one point 1.000.
- qa: 540 paired items; mean delta -0.198; mean absolute difference 0.202; within one point 0.998.

## Scope and cost

One greenhouse generator, 100 predeclared seed positions, no literary filtering.
Local outputs: 26 exact unique; 9 mechanical signatures; outcomes {'both_ready': 94, 'one_waits': 6}.
Six uniform supported questions per story, single-turn only; unchanged story and QA rubrics.
Each judge sees the ENTIRE story set in one request for quality and diversity; QA uses five-story batches.
Same literary rubric and rating dimensions, with output budget scaled to the required ratings.
Output format v2 attaches plot-group membership to each mandatory story rating; literary rubric unchanged.
Story and QA assessment.
Exact duplicates remain. LZMA is a redundancy diagnostic, not a calibrated semantic score.
The budget below is shared across all replication iterations, not a fresh allowance for every version.

Combined returned-usage estimate $0.35498-$0.35498; $2.60899 committed including unknown reservations, within $4.27.
Both arms reserve at conservative Terra rates before dispatch. Actual Luna costs use its own rates.
Rates: [official pricing](https://developers.openai.com/api/docs/pricing), checked 2026-10-22; estimates are not invoice reconciliation.
No automatic paid retries or fallback tiers. Failed/unknown requests remain saved.

Full grades, costs, paired disagreements and usability decisions: `comparison.json`.

Including the previous campaign: $3.34261 committed against the shared $5.00 authorization.
