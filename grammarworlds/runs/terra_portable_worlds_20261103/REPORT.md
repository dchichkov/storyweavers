# Two Terra-authored portable grammar worlds

Terra (`gpt-6.1-terra`, Flex/high) authored library and pottery from two preselected Luna source stories. Each received one feedback revision. No generated code was manually edited.

The shared prefix contains 15,552 characters of public interfaces, vocabulary and 20 retrieved contracts (the contract retrieval itself is bounded to 4,500 characters). There is no full grammar-source dump, GF runtime, or LLM at generation time. World modules remain isolated experimental packs.

| World | Kernels | New lexical entries | Checked stories | Guard checks | Texts | Luna quality /9 | Diversity /9 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| library | 17 | 28 | 120/120 | 3666 | 112 | 6.00 | 1 |
| pottery | 24 | 39 | 120/120 | 6000 | 86 | 5.40 | 1 |

Each checker used seeds 0–59 in past and present, without filtering. It checks replay, rejected forged/stale frames, prediction purity, physical interventions, and word/sentence probability agreement through the existing sampler. Pottery also passes 120 interventions verifying that raising Care increases the thumb-design preference. These are targeted checks, not a proof of full English-to-world semantic fidelity.

Luna judged 20 uniformly selected past-tense positions per world (seed 777), retaining duplicates. It saw prose only and no author identity. One judge run per world; scores are not a model ranking.

## Attempts and cache evidence

Library's first attempt passed all 120 structural cases but had repetitive prose, a confusing pronoun and inactive attention coefficients. Its revision preserves the checks and increases distinct texts from 30 to 112. Pottery's first attempt failed all 120 at the missing cup-state wall inspection; review also found wrong entity IDs and inactive attention. Terra repaired these. The revision checker adds explicit ID and attention checks; both checker versions are retained.

| Request | Input | Cached | Cache writes | Output (including reasoning) |
| --- | ---: | ---: | ---: | ---: |
| library/round1 | 7044 | 0 | 4750 | 12114 |
| library/round2 | 12657 | 4750 | 0 | 12539 |
| pottery/round1 | 7068 | 4750 | 0 | 16020 |
| pottery/round2 | 15943 | 4750 | 0 | 11940 |

The first request wrote the 4,750-token shared prefix; every subsequent authoring request reused it with no additional writes. Repairs append prior output and feedback after the stable boundary. Cache reuse is observed usage, not inferred from configuration.

## Limits and next experiment

Both worlds support two checked final-state branches, but most text variation is surface wording or action ordering. Library remains a narrow search-and-retrieval family; pottery remains a mostly fixed manufacturing sequence. Raw event-path counts do not establish plot diversity.

Manual reading still finds event-log prose, repeated names, thin emotional development, and awkward phrasing such as ‘poured tea from the teapot in the cup’ and nested possessives. Physical guards alone do not ensure natural storytelling. Library's deadline/grandmother and pottery's time gaps/home delivery are simplified; see each bundle's mismatches. Next gate: improve discourse/scene realization and causal alternatives while preserving all physical checks, then rerun this same blinded judge selection. Shared grammar unchanged: True.

## Artifacts

- [Library final pack](library/round2/pack.py) · [unfiltered samples](library/round2/samples.md) · [judge](library/round2/judge_luna/result.json)
- [Pottery final pack](pottery/round2/pack.py) · [unfiltered samples](pottery/round2/samples.md) · [judge](pottery/round2/judge_luna/result.json)
- Both round1 directories retain original responses, code, checks and feedback history.

Reproduce local checks (no model calls):

```sh
.venv/bin/python -m grammarworlds.portable_authoring check --scenario library --round round2
.venv/bin/python -m grammarworlds.portable_authoring check --scenario pottery --round round2
```
