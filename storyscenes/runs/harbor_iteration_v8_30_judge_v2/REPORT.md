# Terra versus Luna: matched capability-story judging

Same selected stories, order, rubric, schema, token limits and reasoning=none; both Flex with store=false.
The requested Luna 6.1 ID was not listed; this comparison uses the explicitly confirmed gpt-6-luna.

| Judge | Stories graded | Story overall / 9 | Set diversity / 9 | QA overall / 9 | QA usable | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-terra | 30 | 7.767 | 5.000 | unrated | 0 / 0 | $0.02496-$0.02496 |
| gpt-6-luna | 30 | 7.133 | 4.000 | unrated | 0 / 0 | $0.00118-$0.00118 |

## Paired agreement

Deltas are Luna minus Terra; Terra is a comparator, not ground truth.

- story: 30 paired items; mean delta -0.633; mean absolute difference 0.633; within one point 1.000.
- qa: 0 paired items; mean delta unrated; mean absolute difference unrated; within one point unrated.

## Scope and cost

One harbor generator, 30 predeclared seed positions, no literary filtering.
Local outputs: 30 exact unique; 16 mechanical signatures; outcomes {'pool': 4, 'helped_delivery': 5, 'timely_return': 5, 'labels_fixed': 6, 'rack': 2, 'two_trips': 3, 'declined': 1, 'correct_delivery': 1, 'basin': 2, 'late_return': 1}.
Six uniform supported questions per story, single-turn only; unchanged story and QA rubrics.
Each judge sees the ENTIRE story set in one request for quality and diversity; QA uses five-story batches.
Same literary rubric and rating dimensions, with output budget scaled to the required ratings.
Output format v2 attaches plot-group membership to each mandatory story rating; literary rubric unchanged.
Story-only assessment; no new QA requests.
Exact duplicates remain. LZMA is a redundancy diagnostic, not a calibrated semantic score.
The budget below is shared across harbor iterations, not a fresh allowance for every version.

Combined returned-usage estimate $0.02614-$0.02614; $0.61779 committed including unknown reservations, within $4.27.
Both arms reserve at conservative Terra rates before dispatch. Actual Luna costs use its own rates.
Rates: [official pricing](https://developers.openai.com/api/docs/pricing), checked 2026-10-22; estimates are not invoice reconciliation.
No automatic paid retries or fallback tiers. Failed/unknown requests remain saved.

Full grades, costs, paired disagreements and usability decisions: `comparison.json`.

Including the previous campaign: $1.35141 committed against the shared $5.00 authorization.
