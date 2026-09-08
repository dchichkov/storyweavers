# Storyscenes: Luna-only improvement pass

Ten theater generators use Luna for all authoring and repair. Saved generators make no API calls. The same judge rated 100 uniformly sampled stories across 10 worlds.

| Metric /9 | Original prototype | Luna improvement | Change |
|---|---:|---:|---:|
| Overall | 6.68 | 6.94 | +0.26 |
| Coherence | 6.75 | 6.76 | +0.01 |
| Style | 5.93 | 6.77 | +0.84 |
| Grammar | 7.63 | 8.29 | +0.66 |
| Storytelling | 6.80 | 6.61 | -0.19 |
| Within-world diversity | 2.20 | 3.20 | +1.00 |

Stories below 6 overall: **17 → 6 of 100**.

| World | Quality before → after | Diversity before → after | Judged plot groups | Scene sets /100 | Outcomes /100 |
|---|---:|---:|---:|---:|---:|
| [bakery_exchange](bakery_exchange/samples.md) | 5.30 → 6.60 | 1 → 3 | 3 | 4 | 4 |
| [clocktower_club](clocktower_club/samples.md) | 6.90 → 7.10 | 3 → 2 | 2 | 4 | 4 |
| [hill_picnic](hill_picnic/samples.md) | 8.00 → 6.50 | 3 → 4 | 4 | 12 | 3 |
| [kite_workshop](kite_workshop/samples.md) | 6.60 → 6.70 | 2 → 3 | 5 | 8 | 6 |
| [library_parade](library_parade/samples.md) | 5.80 → 6.60 | 2 → 3 | 3 | 10 | 3 |
| [museum_of_small_things](museum_of_small_things/samples.md) | 5.30 → 7.70 | 2 → 3 | 2 | 6 | 4 |
| [night_garden](night_garden/samples.md) | 7.10 → 7.10 | 1 → 3 | 4 | 13 | 3 |
| [pond_concert](pond_concert/samples.md) | 7.00 → 8.00 | 2 → 4 | 3 | 3 | 3 |
| [puppet_weather](puppet_weather/samples.md) | 7.00 → 7.00 | 3 → 4 | 3 | 3 | 3 |
| [roof_post](roof_post/samples.md) | 7.80 → 6.10 | 3 → 3 | 5 | 6 | 8 |

## What changed

The planner slices away irrelevant preparation, then replays the retained actions against guards and invariants. Intended outcome fields must change in some sampled path, catching goals that stop before a delivery, performance or response. Knowledge and ownership use shared kernels; keyword APIs and safe state-key renames reduce authoring friction.

A common data-only renderer selects complete text cards from initial/before/after state, groups routine bridges, and expands explicit grammatical phrase mappings. Endings are conditional on final facts. It rejects missing cards, raw state leakage, unresolved alternatives, repeated words and contradictory/future fact bindings. Free English assertions still require semantic review.

All current authoring and routine repair uses Luna. Initial mechanics are written once per draft; subsequent repairs return bounded source edits or catalog edits. The measured second pass inherits Luna drafts rather than paying to regenerate them. Their costs, including failed attempts and abandoned catalogs, are included below. Terra only performs separate evaluation. The earlier Terra-heavy experiment was stopped and is accounted for as development overhead.

These changes move toward the memeplex model: immutable definitions compose over mutable state on physical carriers; beliefs and motives gate compatible behavior; realization reads that state. This is still a small operational subset, not a universal algebra or a proven kernel library distilled from storyscripts.

## Cost and 20,000-world projection

| Scope | Returned input tokens | Returned output tokens | Estimated USD |
|---|---:|---:|---:|
| Luna authoring, including inherited failed drafts | 997,403 | 125,608 | $0.1955 |
| Separate evaluation for this final batch | 94,322 | 12,384 | $0.1922 |

Current-run stage breakdown (the linked cost audit separates inherited draft costs):

| Model and stage | Requests | Input tokens | Output tokens | USD |
|---|---:|---:|---:|---:|
| gpt-5.6-luna / prose_patch | 11 | 172,593 | 7,345 | $0.0260 |
| gpt-5.6-terra / set_judge | 10 | 51,303 | 9,434 | $0.1207 |

Measured authoring cost: **$0.0196 per mechanically successful world**. A straight-line projection is **$391 for 20,000 worlds**. Repeating both the three-story trace review and the ten-story Terra set judge for every world would add approximately **$384**. Runtime sampling itself uses no paid model tokens. The evaluated protocol includes bounded review feedback; its quality is not established for unreviewed authoring at the authoring-only price.

This includes failed and superseded Luna attempts; it does not assume that the first response succeeds. It is a small-batch estimate, not a quotation: a lower literary acceptance rate, different world complexity, unknown API outcomes, operational costs or changed prices will change it. Output totals include reasoning. Costs use returned model and service tier, not merely requested Flex.

Full improvement campaign, including the stopped Terra experiment: **$0.9067** in returned-usage estimates; **$1.1991** accounted for including 4 uncertain outcomes/reservations, under the **$15** authorization. These figures exclude the earlier prototype's separate budget and are not invoice reconciliation.

## Validation and comparison limits

Offline verification: 10/10 worlds; 1000 fresh samples and 30 pinned replays. The baseline hash/pin audit is saved in the campaign directory.

The theater briefs, design seed, sample seeds and uniform judging seed match the baseline. Plans, model allocation, runtime and prose interface changed together, so this measures the combined intervention rather than isolating one cause. The same judge/rubric/calibration were used. This is neither a matched one-stage control nor evidence of production-level acceptance. Ordered paths, scene sets and distinct scalar outcomes are diagnostics; only the plot-group judge estimates semantic diversity.

Artifacts: [manual readings](manual_review.md), [judge report](quality/report.md), [exact judge inputs](quality/inputs.json), [verification](verification.json), [request/token audit](cost_audit.json), [machine-readable comparison](comparison.json).
