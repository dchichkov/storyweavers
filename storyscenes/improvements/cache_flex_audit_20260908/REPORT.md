# Storyscenes cache and Flex audit — 2026-09-08

All 267 unique saved API responses report `service_tier: flex`. The local cost
calculator uses the actual returned model/tier and includes cache reads and
cache-write premiums. Its rates match the current official pricing table.
No new paid API calls were made for this audit; generation code is unchanged.

| Scope | Responses | Input tokens | Cache-read tokens | Cache-read share |
| --- | ---: | ---: | ---: | ---: |
| All saved runs, deduplicated | 267 | 2,066,924 | 54,533 | 2.64% |
| Latest compact authoring, including both recovery runs | 13 | 67,561 | 4,708 | 6.97% |
| Latest compact evaluation | 2 | 12,558 | 0 | 0% |

There were only nine requests with any cache hit. Every hit matches another
saved prompt with the same model, reasoning setting, and output format. The
three latest authoring hits repeat the corresponding compact-v1 world-design
prompts. No partial cross-world shared-prefix reuse is visible in these responses.

## Rates and accounting

USD per million tokens, Flex:

| Model | Ordinary input | Cache read | Cache write | Output |
| --- | ---: | ---: | ---: | ---: |
| GPT-5.6 Luna | $0.10 | $0.01 | $0.125 | $0.60 |
| GPT-5.6 Terra | $1.00 | $0.10 | $1.25 | $6.00 |

These are half the corresponding Standard rates. Cache reads and Flex combine.
The saved usage implies $1.90369943 at Flex list prices, versus $3.80739886
for identical usage at Standard rates. This covers all historical saved runs,
including the original prototype, not just the latest improvement budget.
Unknown/interrupted responses are excluded from these measured totals.

Relative to processing the same input without caching, cache reads save
$0.00490797 but writes add $0.131184, a net $0.12627603 premium. This is a
counterfactual calculation from usage, not a measured alternative run.

This is not invoice reconciliation. Response billing metadata varies:
198 say `payer: openai`, 68 say `payer: developer`, and one has no payer metadata.
No account billing ledger or invoice was queried; the amounts above are model
list-price equivalents, not verified charges to the user's account.

## Why reuse is poor

`factory.request` creates a short system message followed by a single user
message. In compact world authoring, that user message concatenates the fixed
contract and changing seed. Repairs append changing world definitions and
failure details. The current requests have no explicit cache breakpoints.
All 268 saved authoring request files also omit cache-key/options settings.

GPT-5.6's default implicit breakpoint is at the last eligible message ending.
The observed full-prompt writes and exact-repeat hits fit this layout: the
stable interior contract is not given its own reusable boundary. Changing
per-world output schemas in compact prose is an additional potential prefix
change. Cache keys alone cannot repair either problem.

## Next improvement

Put stable instructions, API contracts, and calibration examples before dynamic
content, with an explicit breakpoint at the stable boundary. Use explicit-only
mode so one-use seeds, failures, previews and stories incur ordinary input cost
without a cache-write premium. Use stable per-stage cache keys and consistent
model/reasoning/schema settings. Cacheable prefixes must meet the 1,024-visible-
token minimum; avoid arbitrary padding simply to raise the cache-hit percentage.

World-specific strict prose schemas need separate attention: preserve exact-ID
validation while testing whether a stable response schema can improve reuse.
Keep per-stage token counts and write/read costs visible, then compare a fresh
set of different seeds. Do not count repeated-prompt hits as evidence for the
20,000-world production workload.

Sources: [OpenAI pricing](https://developers.openai.com/api/docs/pricing),
[prompt caching](https://developers.openai.com/api/docs/guides/prompt-caching),
[Flex processing](https://developers.openai.com/api/docs/guides/flex-processing).

`audit.json` contains per-response usage, deduplication paths, prompt-match
checks, totals, counterfactuals, billing metadata counts, and source links.
