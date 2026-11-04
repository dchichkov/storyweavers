# Story-Set Quality

story_set_quality_v1; gpt-5.6-terra; Flex; reasoning none.
Ten random sample positions per world, duplicates retained. Scores are 0-9.

| World | Rated | Quality | Min quality | Diversity | Plot groups |
| --- | ---: | ---: | ---: | ---: | ---: |
| floodgate | 10 | 7.20 | 7 | 1 | 1 |
| orchard | 10 | 7.40 | 7 | 1 | 2 |

## floodgate

All ten stories share the same flooded grain-store emergency, Ren's wrongful blame and clearing, bent retaining pin, partial rescue of twenty-four sacks, and identical flooded-step ending. s000017 and s000019 add a successful sluice test, while s000014 and s000002 use incomplete reading and s000028, s000038, s000023, s000021, s000037, and s000024 use an inaccessible diagram; these are minor route variations within one plot.

## orchard

All ten stories share the same orchard frost threat, correction of blame toward bees, blankets and fork, and ribbon-centered dawn accounting. s000017 and s000019 materially branch into a tested shelter and partial rescue, while s000014, s000028, s000038, s000023, s000021, s000002, s000037, and s000024 end in total loss after the method cannot be used; small differences in notebook access or Ivo's availability do not alter that causal structure.

Returned-usage cost estimate: $0.0267-$0.0267; 0 requests unpriced. Not invoice reconciliation.


Each pool contains all eight boolean configurations at five seeds, in config-major order. Ten positions selected uniformly with seed 777; duplicate texts retained. Only prose and standard calibration were sent. No source, traces, QA, or manual reviews were sent to the judge. No generator edits, automatic paid retries, or cross-campaign budget changes. This evaluates the current repaired authors; it is not a fresh-author or revised-prompt trial. Cost uses the historical repository rate table, not invoice reconciliation.

## Detailed quality scores

All scores use the standard 0–9 scale. Values are means over ten selected positions, including repeated texts.

| World | Coherence | Style | Grammar | Storytelling | Overall |
| --- | ---: | ---: | ---: | ---: | ---: |
| Floodgate | 8.0 | 7.0 | 9.0 | 7.2 | 7.2 |
| Orchard | 7.4 | 7.2 | 9.0 | 6.6 | 7.4 |

| World | Premise diversity | Causal path | Ending | Language | Overall diversity |
| --- | ---: | ---: | ---: | ---: | ---: |
| Floodgate | 1 | 2 | 0 | 1 | 1 |
| Orchard | 1 | 2 | 2 | 1 | 1 |

The judge found clear physical constraints, readable prose, and concrete endings.
Floodgate's learned-method-without-help branch scored 8 overall; its other
selected branches scored 7. Orchard's two-row partial rescue scored 9 overall
and 9 for storytelling; its total-loss branches scored 7 overall and 6 for
storytelling. Each high-scoring branch appeared twice as identical text, so
these are not independent examples of a broad high-quality class.

The orchard criticism was specifically about lost agency: identifying the cause
and failing the test are clear, but the remaining action stalls when the method
is unavailable. Floodgate's loss ending was coherent and concrete, although
the judge considered its tone bleak and adult for the rubric's young audience.

## Local diversity evidence and sampling limits

| World | Positions in full grid | Exact texts in grid | Outcomes in grid | Exact texts judged | Outcomes judged |
| --- | ---: | ---: | --- | ---: | --- |
| Floodgate | 40 | 4 | 35 partial grain loss; 5 full rescue | 3 | 10 partial grain loss |
| Orchard | 40 | 6 | 30 total loss; 5 two-row rescue; 5 full rescue | 5 | 8 total loss; 2 two-row rescue |

Every grid configuration passed the existing evaluator and deterministic replay
comparison during preparation. For each fixed configuration, seeds 0–4 produced
identical prose. These are balanced configuration sweeps, not an inferred
distribution of how users would choose settings. Input combinations often
collapse into the same prose and outcome.

The fixed random sample missed full rescue in both worlds. Therefore the
judge's zero ending-diversity score for floodgate does not mean its generator
has only one ending. We retained the selected sample rather than changing the
seed or replacing duplicates after inspecting it. Full-grid counts supplement
the standard sample score; they do not substitute for another judge rating.
Ten siblings and one judge call per world cannot establish a reliable 0.2-point
quality ranking or the diversity of a larger library.

## Implications for the next authoring trial

This is evidence for readable bounded worlds, with weak variation within each
world. More seeds alone will not increase this library. A useful next prompt
experiment would require several materially different solutions, a new action
after an unsuccessful test, and partial outcomes caused by allocation choices.
Changing the problem, applicable actions, causal route, and relationship
consequence matters more than rewriting the same sequence in different words.
Orchard's two-row rescue is a concrete exemplar to preserve: action still
matters even when the protagonist cannot save everything.

These are recommendations from interpreting the judge and local evidence, not
changes made to either generator. QA correctness was not assessed by the prose
judge. The earlier mechanical QA checks remain separate evidence.

## Execution and retained evidence

Both successful responses report `gpt-5.6-terra`, Flex, completed status, and all
ten requested ratings with valid plot partitions. The two calls used 16,177 input
tokens and 1,759 output tokens; the repository's historical rate table estimates
$0.026731. No claim of current price or invoice reconciliation is made.

Initial sandbox calls failed immediately with connection errors; an independent
probe showed DNS resolution blocked. Their artifacts remain in
`sandbox_connection_failure/`. Automatic approval review then rejected external
submission for lack of explicit disclosure permission. The user explicitly
approved sending these 20 story texts to OpenAI, after which the same frozen
requests succeeded. No automatic paid retry or model/tier fallback occurred.

`inputs.json` holds the exact selected stories; `provenance.json` maps their IDs
to configurations and seeds. Complete local pools, frozen sources and hashes,
planned requests, actual requests, raw responses, validated results, and the
local budget ledger are retained alongside this report.
