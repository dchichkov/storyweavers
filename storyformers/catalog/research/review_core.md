# Cross-review of the core catalog shard

Reviewed the 256-record `sources/core.py` shard on 2026-11-07. This is a semantic and integration review, not evidence that the contracts have been learned. I read every family and executed targeted native counterexamples. The root author fixed selected-sense gates, sense-ID composition and suppression; the reviewing author then made focused witness, quantity-bundle and claim-alignment repairs in the source. The initial defects are retained below as a review trail; final verification and remaining limits follow them.

## Initial findings, subsequently repaired

1. **Selected senses did not constrain several raw-token native lookups.** The initial rules activated when an input explicitly supplied an incompatible sense. Reproduced before repair:

   | Grammar | Counterexample query | Actual activation |
   |---|---|---|
   | G0100, `measure_unit` | `{"token":"seconds","lexical_sense_id":"second:extra_serving","pos":"n"}` | `{"measure_unit":"s"}` |
   | G0067, `temporal_granularity` | `{"token":"second","lexical_sense_id":"second:ordinal","pos":"adj"}` | `{"temporal_granularity":"second"}` |
   | G0071, `temporal_bound_cue` | `{"token":"since","lexical_sense_id":"since:causal"}` | `{"temporal_bound_cue":"lower_bound"}` |
   | G0102, `quantity_approximation_cue` | `{"token":"about","lexical_sense_id":"about:topic"}` | `{"quantity_approximation_cue":"approximate"}` |

   **Resolved:** these lookup families now require selected lexical-sense IDs. Known incompatible senses abstain in the catalog integration checks. The sense-selection step itself remains an upstream requirement; changing the key does not implement general word-sense disambiguation.

2. **The sense namespace broke intended composition.** G0021 emitted `scissors.n.01`, while the lexical family used `scissors:tool` for the same intended tool sense. Passing the former into G0177 `lexical_gloss` produced no activation; rabbit had the equivalent mismatch. **Resolved:** the authored lookup constructor normalizes these two aliases to WordNet IDs. Executed lemma/POS → sense → ontological type/supersense/hypernym for both words, plus scissors → gloss. Other colon IDs remain explicitly authored examples, not an exported WordNet inventory.

3. **Some interval witnesses overstated precision or endpoint conventions.** **Resolved:** `quantity_interval` now uses explicit at-least/at-most wording and separate endpoint flags plus counted domain. `event_time_interval` supplies morning/local-clock wording and retains a day anchor, clock convention, scope and factuality; it does not invent an absolute date or time zone. Elapsed/remaining-duration witnesses now state compatible same-day clock frames. These are contract-example repairs, not claims of an implemented temporal parser.

4. **Promised bundle guarantees were absent from some outputs.** **Resolved:** normalized measures retain original magnitude/unit, target dimension and conversion factor/table; ratios bind each magnitude to its domain; quantity changes retain owner/event/scope/factuality. Totals retain source operands and units; remaining amounts retain owner/event/scope; balances, uncertainty and comparisons retain the stated domains/base values/units; zero counts retain the basket restriction and assertion scope. The invented conversion-table name is an adapter contract resource, not a claim that a conversion engine already exists.

5. **Event identity is weaker than claim identity for provenance copying.** **Resolved for these bounded carriers:** all twelve provenance carriers now require an already aligned source claim in addition to event and scope. The `source_claim_id` head reads a query's explicitly selected correlated anchor rather than inferring identity from event similarity. The atomic `evidence_anchor_bundle` now includes claim identity. Same-event/same-scope but different-claim examples abstain; extra mismatched-event, mismatched-scope and missing-claim probes also abstain. These heads still do not select among distant sources, prove freshness, or make arbitrary independent multi-head writes correlated.

6. **Some contrastive examples had another valid value of the same field.** **Repaired for the identified quantity cases:** normalized-measure contrast now lacks a numeric magnitude; measure-entity contrast lacks an entity; count-domain contrast stops at an unresolved numeral; endpoint-inclusion contrast lacks an explicit boundary convention. More broadly, declarative contrastive fixtures are illustrations of the stated construction/reading, not exhaustive negative training labels for every producer of that attribute. Native empty expectations are checked as actual no-activation cases.

7. **Correction/retraction metadata was not itself inhibition.** **Resolved:** the shard now contains six actual `suppress` heads: four native claim/rule-keyed operations and two adapter operations for licensed reference/role exclusion. They lower only the exact targeted field/value rather than suppressing valid holder/source/scope metadata or asserting the opposite value. Their control records must already have been correctly resolved from causal evidence.

8. **Additional focused semantic repairs.** Same-name entity resolution now has an explicit “that same Lily” witness; name spelling alone is not the evidence. A counterexample to a red-cup rule now states “not red”; a blue object need not be exclusively blue. `lexical_implicativity` now represents the ordinary two-way `manage to` signature: positive matrix assertion supports its complement, negative matrix assertion supports the negated complement. This is a selected construction's lexical signature, with actual episodic scope and ordinary negation required before inference; it does not infer complement truth from a standalone word. See Karttunen's primary [Simple and Phrasal Implicatives](https://aclanthology.org/S12-1020/).

## Family coverage and positive findings

| Family | Sampled closely | Assessment |
|---|---|---|
| `identity_annotation` | entity ID, event ID, actor/name copy, location, lexical sense, group membership | Distinguishes labels, IDs, roles, and existence. Actor/name copy checks identity; entity-ID witness now supplies explicit same-reference evidence. Canonical sense chains checked. |
| `reference_resolution` | antecedent alternatives, accessibility under negation, reflexives, split antecedents, donkey reference, quotation shift | Strong coverage beyond nearest-noun copying. Hypothetical introduction is explicitly separated from actual existence. Ensure selected antecedent fields are not used before alternative resolution; the contracts mostly state this correctly. |
| `temporal_semantics` | bounds, recurrence, overlap, deadline, conflict, unresolved anchor | Distinguishes deadline from completion, narrative order from world time, and unknown anchors from machine date. Polysemy gates and explicit clock examples repaired. |
| `quantity_measurement` | native bounds, range, ratio, count domain, change, conservation, distribution | Dimensional compatibility and explicit zero remain distinct from missing data. The reviewed bundle examples now retain their promised domain/owner/provenance. |
| `semantic_evidence` | provenance carriers, independence, retraction, missing premises, freshness, exceptions | Absence is not false. Bounded carriers require claim alignment; general tuple correlation and freshness still need declared support. |
| `lexical_semantics` | sense candidates, type relations, selection preferences, collectivity, modifier mode, factivity | Lexical type evidence remains separate from world assertion; selection preferences remain soft. Shared sense chains and the selected `manage to` signature repaired. |
| `contextual_retrieval` | equality-key native heads, causal successor retrieval, definitions, correction, two-hop containment, evidence union | Native alignments retain source/query positions and avoid claiming nearest selection. Relation composition requires explicit licensed types. Repeated source evidence is correctly distinguished from independent support. |
| `logical_semantics` | scoped proposition, negation, quantifier variables, necessary/sufficient conditions, counterfactuals, contradiction, defaults | Useful explicit scope discipline and no automatic converse inference. `proposition_content` is appropriately distinct from assertion commitment. Negative/default/absence reasoning is reserved for declared adapters rather than hidden in the finite matcher. |

## Final verification and remaining work

The final core source produces exactly **256 attributes, 256 heads and 256 grammars**, eight families of 32, with unique keys and valid example types. Support is **98 native / 158 adapter-required**. All **196 native positive/contrastive fixtures** pass. All twelve provenance carriers pass **36 additional event/scope/missing-claim contrasts**, besides their stored same-event/different-claim contrasts. The two canonical sense pipelines pass. Operation counts are **250 add / 6 suppress**.

The 158 declarative adapters are still design contracts; text-only examples are not parsed or semantically executed by the catalog validator. Learned accuracy, coverage across paraphrases, full causal annotation and cross-head competition remain unmeasured. Source-claim identity must be supplied by a trustworthy earlier annotation or adapter. A future implementation must preserve alternative tuples across multiple independent heads, distinguish a logical contrast from a universal negative label, and ensure narrator correction does not overwrite a character's uninformed belief. The mental-domain review supplies that last distinction explicitly.

No aliases were found that duplicate a different real registry field name in this snapshot. The separate lexical relation fields are meaningful even when they share a lookup mechanism; the tables should remain candidate resources rather than a claim of discovered SAE units.
