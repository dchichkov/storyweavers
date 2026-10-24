# Terra versus Luna: matched capability-story judging

Same selected stories, order, rubric, schema, token limits and reasoning=none; both Flex with store=false.
The requested Luna 6.1 ID was not listed; this comparison uses the explicitly confirmed gpt-6-luna.

| Judge | Stories graded | Story overall / 9 | Set diversity / 9 | QA overall / 9 | QA usable | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-terra | 30 | 2.667 | 0.333 | 8.978 | 180 / 180 | $0.12055-$0.12055 |
| gpt-6-luna | 30 | 3.000 | 0.667 | 8.606 | 168 / 180 | $0.00553-$0.00553 |

## Paired agreement

Deltas are Luna minus Terra; Terra is a comparator, not ground truth.

- story: 30 paired items; mean delta 0.333; mean absolute difference 0.467; within one point 0.967.
- qa: 180 paired items; mean delta -0.372; mean absolute difference 0.394; within one point 0.933.

## Scope and cost

This is a small three-world comparison, conditional on successful bounded generation.
The fourth demo had only one returned story and is not set-graded. Duplicate sample positions remain.
QA has 180 conversations but only 13 follow-ups; it is not a general multi-turn judge benchmark.
All four worlds fail the baseline's all-seeds mechanical gate, so the strict geometric index is zero
regardless of judge. Do not use it to compare these judges.

Combined returned-usage estimate $0.12608-$0.12608; $0.12608 committed including unknown reservations, within $5.00.
Both arms reserve at conservative Terra rates before dispatch. Actual Luna costs use its own rates.
Rates: [official pricing](https://developers.openai.com/api/docs/pricing), checked 2026-10-22; estimates are not invoice reconciliation.
No automatic paid retries or fallback tiers. Failed/unknown requests remain saved.

Full grades, costs, paired disagreements and usability decisions: `comparison.json`.
