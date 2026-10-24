# Terra versus Luna: matched capability-story judging

Same selected stories, order, rubric, schema, token limits and reasoning=none; both Flex with store=false.
The requested Luna 6.1 ID was not listed; this comparison uses the explicitly confirmed gpt-6-luna.

| Judge | Stories graded | Story overall / 9 | Set diversity / 9 | QA overall / 9 | QA usable | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-terra | 90 | 8.000 | 4.000 | unrated | 0 / 0 | $0.06280-$0.06280 |
| gpt-6-luna | 90 | 7.989 | 6.000 | unrated | 0 / 0 | $0.00474-$0.00474 |

## Paired agreement

Deltas are Luna minus Terra; Terra is a comparator, not ground truth.

- story: 90 paired items; mean delta -0.011; mean absolute difference 0.011; within one point 1.000.
- qa: 0 paired items; mean delta unrated; mean absolute difference unrated; within one point unrated.

## Scope and cost

Cross-script assessment, not directly the same experiment as within-script diversity.
Compression uses all 300 positions. Semantic judging uses seeds 10000-10029 from each script, 90 total.
No score selection or deduplication. No new QA calls. Same story calibration and rating dimensions.
Only the scope sentences change from one shared world to a pooled three-script set.
Uses the existing shared $5 campaign cap. No automatic retries or fallback tiers.

Combined returned-usage estimate $0.06753-$0.06753; $3.02834 committed including unknown reservations, within $4.27.
Both arms reserve at conservative Terra rates before dispatch. Actual Luna costs use its own rates.
Rates: [official pricing](https://developers.openai.com/api/docs/pricing), checked 2026-10-22; estimates are not invoice reconciliation.
No automatic paid retries or fallback tiers. Failed/unknown requests remain saved.

Full grades, costs, paired disagreements and usability decisions: `comparison.json`.

Including the previous campaign: $3.76196 committed against the shared $5.00 authorization.
