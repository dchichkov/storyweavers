# Matched local repairs after the trade-off evaluation

The [v1 findings](../harbor_tradeoffs_v1_10_local/FINDINGS.md) and all raw judge
responses remain unchanged. This version has no new paid assessment. Do not
copy v1's QA usability counts onto the corrected answers, or its ten-story
scores onto a larger sample.

## Corrections

- Delivery QA names the removed rope and subsequent delivery without asserting
  a load-weight explanation absent from the visible paragraph.
- Lantern QA describes its visible placement and light without adding a bulb
  or an unmentioned shutter.
- Lists of chosen goals use conjunctions; two deferred goals are called plans,
  not a singular comma-spliced plan.
- A lantern visits the window "again" only if the trace actually contains an
  earlier window placement. A chart is expected to return only if it was
  previously mounted. The empty shelf is otherwise described directly.
- The opening's persistent-light requirement explicitly cites its initial
  darkness premise. This is provenance bookkeeping, not proof that every
  English assertion is entailed.

## Matched Checks

| Batch | Seeds | Returned/replayed | Changed stories vs v1 | Changed QA sets | Exact texts | XZ bytes |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| `../harbor_tradeoffs_v3_10_local` | 8000-8009 | 10/10 | 0 | 10 | 10 | 2,212 |
| `../harbor_tradeoffs_v3_30_local` | 9000-9029 | 30/30 | 1 | 30 | 22 | 2,832 |
| This hundred | 50000-50099 | 100/100 | 5 | 100 | 70 | 4,120 |

All 140 trace hashes match v1 exactly. The changed thirty-story seed is 9011.
The changed hundred-story seeds are 50017, 50037, 50057, 50066 and 50068.
The hundred's archive is 4,120 / 191,112 bytes (2.156%), or 41.20 bytes/story.
This does not change the conclusion about a narrow premise and repeated prose.

The intermediate v2 remains preserved. It corrected QA and the chart wording,
but still assumed that a lantern moved from the jetty had previously been at
the window. Regression tests now distinguish first visits from actual returns.
The old composed-harbor renderer shares these corrections; its previous
snapshots remain the authoritative sources for their historical text and QA.

The exhaustive 2,304-configuration audit belongs to v1. V3 has the matched
140-sample serialized-replay checks and focused negative/counterfactual tests,
not a repeated claim of exhaustive re-audit. The physical rules and planner
were not changed by these prose/QA corrections.

Verification: all 507 StoryScenes tests pass, including 20 focused composed
harbor/trade-off tests. `matched_v1_checks.json` records the per-seed text,
QA, path and trace comparison. No paid requests remain active from this check;
the original campaign authorization and uncertain reservations are unchanged.
