# Twenty Xhigh Packs: Results

October 24, 2026. Twenty distinct prompt seeds, word sets and premises; Luna
xhigh/Flex, 128k output ceiling, twenty concurrent requests. All inputs, raw
outputs and failures preserved. No repair, normalization, retry or tier fallback.

## Yield

| Gate | Result |
| --- | ---: |
| Requests dispatched | 20 |
| Complete bundles returned | 19 |
| API errors | 1 (bakery, HTTP 500, usage unknown) |
| Checker preflight failure | 1 (snow, invalid scene-inventory JSON) |
| Packs with 100/100 runnable positions | 5 |
| Partly runnable | 2 (trail 98/100, festival 3/100) |
| Executed packs with 0/100 runnable | 11 |
| All mechanical requirements passed | 1 (library) |
| Successful sampled positions | 601 / 1,800 actually attempted |
| Standard judge completed | 5 packs, 50 stories |

Thus untouched full-runtime yield is **5/20 requests (25%)**, or 5/19 returned
bundles. Full mechanical acceptance is **1/20 (5%)**. Snow was not sampled; do
not count its missing positions or the API error as observed runtime exceptions.
Full acceptance includes reference length, inventory and generated tests, not
just executability. It does not establish semantic or literary correctness.

[Complete per-pack table](LUNA_XHIGH_128K_20_TABLE.md),
[structured summary](luna_xhigh_128k_20_summary.json),
[protocol and reproduction](LUNA_XHIGH_128K_20_PROTOCOL.md).

## Tokens And Cost

Returned usage totals **920,445 output tokens**, including **611,987 reasoning
tokens**, across nineteen responses. None is truncated or reaches 128k.
Only library exceeds the old 64k ceiling: **69,349 output**, including 52,379
reasoning tokens. Other completed attempts use 38,598-60,204 output tokens.
The extra allowance was used by one pack; it cannot explain the other failures.
There is no matched 64k rerun of these same seeds, so this is not a causal
ablation of output limits or reasoning settings.

Known generation-only cost at published short-context
[Flex rates](https://developers.openai.com/api/docs/pricing) is approximately
**$0.2724-$0.3148 total**, with the range reflecting unreported cache-write TTL.
This excludes the HTTP 500's unknown usage, judging and repair labor. Reasoning
is included in output, not charged twice. Requests took about 9.3-22.7 minutes.

The deliberately conservative batch ledger accounts for **$0.913699**:
$0.629549 returned generation allowances, $0.134150 judge allowances and a
$0.15 held reservation for bakery. These are not invoice totals. Campaign-wide
accounting is **$6.43547868/$10**, including the previous $5 unknown Sol-agent
reservation. No new managed agents or cloud sandboxes were created.

## Quality

Same Terra/Flex/none protocol: ten uniform saved positions per 100/100-runnable
pack, selection seed 777, duplicates retained. All five judges completed.

| Pack | Quality /9 | Storytelling /9 | Diversity /9 |
| --- | ---: | ---: | ---: |
| Greenhouse | 8 | 8 | 2 |
| Library | 8 | 7.6 | 3 |
| Music | 7 | 7.2 | 2 |
| Market | 8 | 8 | 3 |
| Repair | 8 | 8 | 2 |
| Mean | 7.8 | 7.76 | 2.4 |

These means are **conditional on the runtime gate**, not quality estimates for
all twenty requests. Different premises give cross-pack variety, but the low
within-pack diversity scores still warn against treating every sampled story
as independent training value.

Read [one reproducible successful story per available pack](LUNA_XHIGH_128K_20_SAMPLES.md)
and [manual notes](LUNA_XHIGH_128K_20_MANUAL.md). All seven such samples were read,
including the two partially runnable packs. Manual reading finds defects that
the judge or replay checks miss: a literal `{child}` placeholder, repeated
completed deliveries, an unexplained decision not to search a known book
location, and weakly justified physical transitions. Library's mechanical pass
is therefore not an unqualified data-quality approval.

## Failure Slices

The main class is **local atomic actions versus global invariants**. Pottery
transfers the gift before setting the final outcome, while its invariant forbids
a transferred gift in an unended story. The validator runs between actions, so
the legal intended ending is unreachable. Puppets, picnic, orchard, pond,
laundry, festival, camp and biscuit have related preparation, movement or
completion invariant errors in their saved reports; exact fixes need code review,
not blanket removal of validators.

Other clear slices: missing state key (seaside); route exhaustion (museum and
costume); no-op agreement (some costume cases); scene-length guard (two trail
positions); malformed inventory JSON (snow). Reference lengths and generated
test assertions are additional independent failures. Among the runnable packs:
greenhouse passes its tests but has an 809-word reference; music fails object
usefulness; market fails a counterfactual assertion; repair exceeds scene length;
library passes all current gates.

## Takeaway

Luna xhigh is inexpensive enough to draft many candidates, but extra output
headroom is not a substitute for execution feedback. This run supports testing
**draft -> run checker -> bounded code repair -> prose/state review**, while
preserving raw and repaired yield separately. It does not support unattended
one-shot production of accepted packs. Repair should preserve real invariants
and model valid intermediate states, not weaken checks until tests turn green.

The next useful experiment is bounded repair of these saved failures, especially
the repeated invariant class, rather than another larger-token one-shot batch.
