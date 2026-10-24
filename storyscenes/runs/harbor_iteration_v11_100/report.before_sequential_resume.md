# Terra versus Luna: matched capability-story judging

Same selected stories, order, rubric, schema, token limits and reasoning=none; both Flex with store=false.
The requested Luna 6.1 ID was not listed; this comparison uses the explicitly confirmed gpt-6-luna.

| Judge | Stories graded | Story overall / 9 | Set diversity / 9 | QA overall / 9 | QA usable | Estimated USD |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| gpt-5.6-terra | 100 | 8.000 | 5.000 | 8.978 | 90 / 90 | $0.11665-$0.11665 |
| gpt-6-luna | 0 | unrated | unrated | 8.850 | 56 / 60 | $0.00132-$0.00132 |

## Paired agreement

Deltas are Luna minus Terra; Terra is a comparator, not ground truth.

- story: 0 paired items; mean delta unrated; mean absolute difference unrated; within one point unrated.
- qa: 60 paired items; mean delta -0.133; mean absolute difference 0.133; within one point 1.000.

## Scope and cost

One harbor generator, 100 predeclared seed positions, no literary filtering.
Local outputs: 85 exact unique; 35 mechanical signatures; outcomes {'basin': 11, 'helped_delivery': 16, 'timely_return': 11, 'labels_fixed': 16, 'flat_chart_and_sailing': 3, 'pool': 5, 'both_plans': 16, 'late_return': 8, 'correct_delivery': 4, 'rack': 4, 'declined': 1, 'two_trips': 4, 'shortened_display_and_sailing': 1}.
Up to six uniform supported questions per story, single-turn only; unchanged story and QA rubrics.
Each judge sees the ENTIRE story set in one request for quality and diversity; QA uses five-story batches.
Same literary rubric and rating dimensions, with output budget scaled to the required ratings.
Output format v2 attaches plot-group membership to each mandatory story rating; literary rubric unchanged.
Story and QA assessment.
Exact duplicates remain. LZMA is a redundancy diagnostic, not a calibrated semantic score.
The budget below is shared across all replication iterations, not a fresh allowance for every version.

Combined returned-usage estimate $0.11797-$0.11797; $3.30296 committed including unknown reservations, within $4.27.
Both arms reserve at conservative Terra rates before dispatch. Actual Luna costs use its own rates.
Rates: [official pricing](https://developers.openai.com/api/docs/pricing), checked 2026-10-22; estimates are not invoice reconciliation.
No automatic paid retries or fallback tiers. Failed/unknown requests remain saved.

Full grades, costs, paired disagreements and usability decisions: `comparison.json`.

Including the previous campaign: $4.03658 committed against the shared $5.00 authorization.
