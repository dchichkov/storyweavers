# Terra versus Luna: matched capability-story judging

Same selected stories, order, rubric, schema, token limits and reasoning=none; both Flex with store=false.
The requested Luna 6.1 ID was not listed; this comparison uses the explicitly confirmed gpt-6-luna.

| Judge | Stories graded | Story overall / 9 | Set diversity / 9 | QA overall / 9 | QA usable | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-terra | 10 | 7.800 | 3.000 | 8.983 | 60 / 60 | $0.03933-$0.03933 |
| gpt-6-luna | 10 | 8.000 | 3.000 | 8.900 | 60 / 60 | $0.00177-$0.00177 |

## Paired agreement

Deltas are Luna minus Terra; Terra is a comparator, not ground truth.

- story: 10 paired items; mean delta 0.200; mean absolute difference 0.200; within one point 1.000.
- qa: 60 paired items; mean delta -0.083; mean absolute difference 0.117; within one point 1.000.

## Scope and cost

One harbor generator, ten predeclared seed positions, no literary filtering.
Local outputs: 10 exact unique; 10 mechanical signatures; outcomes {'rack': 2, 'pool': 3, 'basin': 5}.
Six uniform supported questions per story, single-turn only; unchanged story and QA rubrics.
Compare storytelling and semantic diversity first. These ten samples do not establish large-pool diversity.
The budget below is shared across harbor iterations, not a fresh allowance for every version.

Combined returned-usage estimate $0.04111-$0.04111; $0.08157 committed including unknown reservations, within $4.27.
Both arms reserve at conservative Terra rates before dispatch. Actual Luna costs use its own rates.
Rates: [official pricing](https://developers.openai.com/api/docs/pricing), checked 2026-10-22; estimates are not invoice reconciliation.
No automatic paid retries or fallback tiers. Failed/unknown requests remain saved.

Full grades, costs, paired disagreements and usability decisions: `comparison.json`.

Including the previous campaign: $0.81519 committed against the shared $5.00 authorization.
