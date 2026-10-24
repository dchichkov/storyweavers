# Terra versus Luna: matched capability-story judging

Same selected stories, order, rubric, schema, token limits and reasoning=none; both Flex with store=false.
The requested Luna 6.1 ID was not listed; this comparison uses the explicitly confirmed gpt-6-luna.

| Judge | Stories graded | Story overall / 9 | Set diversity / 9 | QA overall / 9 | QA usable | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-terra | 30 | 8.100 | 5.000 | 8.961 | 178 / 179 | $0.11290-$0.11290 |
| gpt-6-luna | 30 | 7.967 | 4.000 | 8.832 | 168 / 179 | $0.00523-$0.00523 |

## Paired agreement

Deltas are Luna minus Terra; Terra is a comparator, not ground truth.

- story: 30 paired items; mean delta -0.133; mean absolute difference 0.200; within one point 1.000.
- qa: 179 paired items; mean delta -0.128; mean absolute difference 0.184; within one point 0.978.

## Scope and cost

One harbor generator, 30 predeclared seed positions, no literary filtering.
Local outputs: 28 exact unique; 18 mechanical signatures; outcomes {'pool': 3, 'helped_delivery': 4, 'late_return': 4, 'labels_fixed': 5, 'clip_preserves_both': 4, 'basin': 3, 'two_trips': 2, 'timely_return': 2, 'released_deadline_and_basin': 1, 'correct_delivery': 1, 'flat_chart_and_sailing': 1}.
Up to six uniform supported questions per story, single-turn only; unchanged story and QA rubrics.
Each judge sees the ENTIRE story set in one request for quality and diversity; QA uses five-story batches.
Same literary rubric and rating dimensions, with output budget scaled to the required ratings.
Output format v2 attaches plot-group membership to each mandatory story rating; literary rubric unchanged.
Story and QA assessment.
Exact duplicates remain. LZMA is a redundancy diagnostic, not a calibrated semantic score.
The budget below is shared across all replication iterations, not a fresh allowance for every version.

Combined returned-usage estimate $0.11813-$0.11813; $3.72362 committed including unknown reservations, within $4.27.
Both arms reserve at conservative Terra rates before dispatch. Actual Luna costs use its own rates.
Rates: [official pricing](https://developers.openai.com/api/docs/pricing), checked 2026-10-22; estimates are not invoice reconciliation.
No automatic paid retries or fallback tiers. Failed/unknown requests remain saved.

Full grades, costs, paired disagreements and usability decisions: `comparison.json`.

Including the previous campaign: $4.45725 committed against the shared $5.00 authorization.
