# Terra versus Luna: matched capability-story judging

Same selected stories, order, rubric, schema, token limits and reasoning=none; both Flex with store=false.
The requested Luna 6.1 ID was not listed; this comparison uses the explicitly confirmed gpt-6-luna.

| Judge | Stories graded | Story overall / 9 | Set diversity / 9 | QA overall / 9 | QA usable | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-terra | 10 | 7.000 | 3.000 | 8.950 | 59 / 60 | $0.03868-$0.03868 |
| gpt-6-luna | 10 | 7.100 | 3.000 | 8.767 | 56 / 60 | $0.00179-$0.00179 |

## Paired agreement

Deltas are Luna minus Terra; Terra is a comparator, not ground truth.

- story: 10 paired items; mean delta 0.100; mean absolute difference 0.100; within one point 1.000.
- qa: 60 paired items; mean delta -0.183; mean absolute difference 0.250; within one point 0.917.

## Scope and cost

One harbor generator, ten predeclared seed positions, no literary filtering.
Local outputs: 10 exact unique; 7 mechanical signatures; outcomes {'pool': 8, 'basin': 1, 'rack': 1}.
Six uniform supported questions per story, single-turn only; unchanged story and QA rubrics.
Compare storytelling and semantic diversity first. These ten samples do not establish large-pool diversity.
The budget below is shared across harbor iterations, not a fresh allowance for every version.

Combined returned-usage estimate $0.04047-$0.04047; $0.04047 committed including unknown reservations, within $4.27.
Both arms reserve at conservative Terra rates before dispatch. Actual Luna costs use its own rates.
Rates: [official pricing](https://developers.openai.com/api/docs/pricing), checked 2026-10-22; estimates are not invoice reconciliation.
No automatic paid retries or fallback tiers. Failed/unknown requests remain saved.

Full grades, costs, paired disagreements and usability decisions: `comparison.json`.

Including the previous campaign: $0.77409 committed against the shared $5.00 authorization.
