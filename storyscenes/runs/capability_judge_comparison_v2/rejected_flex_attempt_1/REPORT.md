# Terra versus Luna: matched capability-story judging

Same selected stories, order, rubric, schema, token limits and reasoning=none; both Flex with store=false.
The requested Luna 6.1 ID was not listed; this comparison uses the explicitly confirmed gpt-6-luna.

| Judge | Stories graded | Story overall / 9 | Set diversity / 9 | QA overall / 9 | QA usable | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-terra | 20 | 4.000 | 0.000 | 9.000 | 120 / 120 | $0.07778-$0.07778 |
| gpt-6-luna | 30 | 4.000 | 0.000 | 8.889 | 179 / 180 | $0.00507-$0.00507 |

## Paired agreement

Deltas are Luna minus Terra; Terra is a comparator, not ground truth.

- story: 20 paired items; mean delta 0.000; mean absolute difference 0.000; within one point 1.000.
- qa: 120 paired items; mean delta -0.117; mean absolute difference 0.117; within one point 0.992.

## Scope and cost

Revised plots: 30 matched seed positions, 3 distinct visible stories; duplicates retained.
QA: 180 conversations, 18 follow-up turns.
These are fixed authored profiles, not independent stories or a diverse dataset.
Both prose and executable plots changed; historical deltas do not isolate a renderer effect.
The fourth conformance demo was not part of this prose review. No population yield or geometric score is claimed.

Combined returned-usage estimate $0.08285-$0.08285; $0.45197 committed including unknown reservations, within $1.00.
Both arms reserve at conservative Terra rates before dispatch. Actual Luna costs use its own rates.
Rates: [official pricing](https://developers.openai.com/api/docs/pricing), checked 2026-10-22; estimates are not invoice reconciliation.
No automatic paid retries or fallback tiers. Failed/unknown requests remain saved.

Full grades, costs, paired disagreements and usability decisions: `comparison.json`.

Including the previous campaign: $0.57804 committed against the shared $5.00 authorization.
