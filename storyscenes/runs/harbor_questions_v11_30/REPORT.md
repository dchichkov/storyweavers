# Terra versus Luna: matched capability-story judging

Same selected stories, order, rubric, schema, token limits and reasoning=none; both Flex with store=false.
The requested Luna 6.1 ID was not listed; this comparison uses the explicitly confirmed gpt-6-luna.

| Judge | Stories graded | Story overall / 9 | Set diversity / 9 | QA overall / 9 | QA usable | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-terra | 30 | 8.000 | 5.000 | 8.902 | 169 / 174 | $0.11537-$0.11537 |
| gpt-6-luna | 30 | 7.700 | 5.000 | 8.839 | 170 / 174 | $0.00512-$0.00512 |

## Paired agreement

Deltas are Luna minus Terra; Terra is a comparator, not ground truth.

- story: 30 paired items; mean delta -0.300; mean absolute difference 0.300; within one point 1.000.
- qa: 174 paired items; mean delta -0.063; mean absolute difference 0.224; within one point 0.971.

## Scope and cost

One harbor_questions generator, 30 predeclared seed positions, no literary filtering.
Local outputs: 24 exact unique; 23 mechanical signatures; outcomes {'help_after_failed_lift': 2, 'delivery_confirmed_afterward': 3, 'self_delivered': 3, 'opened_without_asking': 2, 'kept_for_sign': 1, 'long_way': 1, 'help_completed': 5, 'divided_after_refusal': 2, 'self_repaired_delivery': 1, 'known_lane': 1, 'carried_alone': 3, 'rerouted_after_attempt': 1, 'bridge': 1, 'tool_after_failed_pull': 1, 'wrong_delivery_repaired': 2, 'untied': 1}.
Up to six uniform supported questions per story, single-turn only; unchanged story and QA rubrics.
Each judge sees the ENTIRE story set in one request for quality and diversity; QA uses five-story batches.
Same literary rubric and rating dimensions, with output budget scaled to the required ratings.
Output format v2 attaches plot-group membership to each mandatory story rating; literary rubric unchanged.
Story and QA assessment.
Exact duplicates remain. LZMA is a redundancy diagnostic, not a calibrated semantic score.
The budget below is shared across all replication iterations, not a fresh allowance for every version.

Combined returned-usage estimate $0.12048-$0.12048; $4.09767 committed including unknown reservations, within $9.27.
Both arms reserve at conservative Terra rates before dispatch. Actual Luna costs use its own rates.
Rates: [official pricing](https://developers.openai.com/api/docs/pricing), checked 2026-10-22; estimates are not invoice reconciliation.
No automatic paid retries or fallback tiers. Failed/unknown requests remain saved.

Full grades, costs, paired disagreements and usability decisions: `comparison.json`.

Including the previous campaign: $4.83129 committed against the shared $10.00 authorization.
