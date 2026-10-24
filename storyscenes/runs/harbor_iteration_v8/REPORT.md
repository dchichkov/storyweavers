# Terra versus Luna: matched capability-story judging

Same selected stories, order, rubric, schema, token limits and reasoning=none; both Flex with store=false.
The requested Luna 6.1 ID was not listed; this comparison uses the explicitly confirmed gpt-6-luna.

| Judge | Stories graded | Story overall / 9 | Set diversity / 9 | QA overall / 9 | QA usable | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-terra | 10 | 8.000 | 5.000 | 8.983 | 59 / 60 | $0.03923-$0.03923 |
| gpt-6-luna | 10 | 7.900 | 5.000 | 8.583 | 57 / 60 | $0.00175-$0.00175 |

## Paired agreement

Deltas are Luna minus Terra; Terra is a comparator, not ground truth.

- story: 10 paired items; mean delta -0.100; mean absolute difference 0.100; within one point 1.000.
- qa: 60 paired items; mean delta -0.400; mean absolute difference 0.400; within one point 0.950.

## Scope and cost

One harbor generator, 10 predeclared seed positions, no literary filtering.
Local outputs: 10 exact unique; 10 mechanical signatures; outcomes {'rack': 1, 'two_trips': 2, 'timely_return': 2, 'labels_fixed': 2, 'basin': 1, 'pool': 1, 'helped_delivery': 1}.
Six uniform supported questions per story, single-turn only; unchanged story and QA rubrics.
Each judge sees the ENTIRE story set in one request for quality and diversity; QA uses five-story batches.
Same rubric and schema, with an output budget scaled to the number of required story ratings.
Exact duplicates remain. LZMA is a redundancy diagnostic, not a calibrated semantic score.
The budget below is shared across harbor iterations, not a fresh allowance for every version.

Combined returned-usage estimate $0.04098-$0.04098; $0.47692 committed including unknown reservations, within $4.27.
Both arms reserve at conservative Terra rates before dispatch. Actual Luna costs use its own rates.
Rates: [official pricing](https://developers.openai.com/api/docs/pricing), checked 2026-10-22; estimates are not invoice reconciliation.
No automatic paid retries or fallback tiers. Failed/unknown requests remain saved.

Full grades, costs, paired disagreements and usability decisions: `comparison.json`.

Including the previous campaign: $1.21054 committed against the shared $5.00 authorization.
