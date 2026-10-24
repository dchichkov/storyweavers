# Terra versus Luna: matched capability-story judging

Same selected stories, order, rubric, schema, token limits and reasoning=none; both Flex with store=false.
The requested Luna 6.1 ID was not listed; this comparison uses the explicitly confirmed gpt-6-luna.

| Judge | Stories graded | Story overall / 9 | Set diversity / 9 | QA overall / 9 | QA usable | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-terra | 10 | 7.500 | 5.000 | 8.867 | 58 / 60 | $0.04100-$0.04100 |
| gpt-6-luna | 10 | 7.600 | 5.000 | 8.767 | 59 / 60 | $0.00193-$0.00193 |

## Paired agreement

Deltas are Luna minus Terra; Terra is a comparator, not ground truth.

- story: 10 paired items; mean delta 0.100; mean absolute difference 0.500; within one point 1.000.
- qa: 60 paired items; mean delta -0.100; mean absolute difference 0.233; within one point 0.967.

## Scope and cost

One harbor_questions generator, 10 predeclared seed positions, no literary filtering.
Local outputs: 10 exact unique; 10 mechanical signatures; outcomes {'stopped_after_attempt': 1, 'kept_for_sign': 2, 'bridge': 1, 'deferred': 2, 'waiting_for_help': 1, 'self_repaired_delivery': 1, 'rerouted_after_attempt': 1, 'opened_without_asking': 1}.
Up to six uniform supported questions per story, single-turn only; unchanged story and QA rubrics.
Each judge sees the ENTIRE story set in one request for quality and diversity; QA uses five-story batches.
Same literary rubric and rating dimensions, with output budget scaled to the required ratings.
Output format v2 attaches plot-group membership to each mandatory story rating; literary rubric unchanged.
Story and QA assessment.
Exact duplicates remain. LZMA is a redundancy diagnostic, not a calibrated semantic score.
The budget below is shared across all replication iterations, not a fresh allowance for every version.

Combined returned-usage estimate $0.04293-$0.04293; $3.93453 committed including unknown reservations, within $4.27.
Both arms reserve at conservative Terra rates before dispatch. Actual Luna costs use its own rates.
Rates: [official pricing](https://developers.openai.com/api/docs/pricing), checked 2026-10-22; estimates are not invoice reconciliation.
No automatic paid retries or fallback tiers. Failed/unknown requests remain saved.

Full grades, costs, paired disagreements and usability decisions: `comparison.json`.

Including the previous campaign: $4.66815 committed against the shared $5.00 authorization.
