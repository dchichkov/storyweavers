# Local architecture and catalog audit

Inspected 2026-11-07 in the current worktree. This report describes local implementations and design material. It does not independently validate the external research cited by the older catalog. No directory or file named `grammarformers` was found; the relevant implementation is `grammarworlds/`, alongside the separate `storyformers/` experiment.

## The three existing inventories are different things

| Artifact | Current contents | Appropriate reuse |
| --- | --- | --- |
| [Attention-head research inventory](/Users/dmitry/storyweavers/grammarworlds/attention_head_inventory.md:1) | 1,024 numbered entries, stated to draw on 134 sources. Entries mix physical head instances, task-conditioned behaviors, broad families, toy circuits, and SAE/output associations. Examples are explicitly invented illustrations. | Evidence and inspiration. Do not relabel all 1,024 as distinct executable algorithms or causally established semantic features. |
| [Proposed symbolic inventory](/Users/dmitry/storyweavers/grammarworlds/proposed_symbolic_attention_inventory.md:1) | 64 proposed symbolic behaviors across eight families. It requires query, selector, payload, and consumer, and warns that changing an object/model/layer alone is not a new behavior. | A useful compact seed taxonomy and operational contract. |
| [Symbolic head library](/Users/dmitry/storyweavers/grammarworlds/symbolic_heads/README.md:1) and [editable data](/Users/dmitry/storyweavers/grammarworlds/symbolic_heads/data/P001.json) | Verified by reading all 64 JSON records: **15 table heads and 49 `program_required` contracts**. Ten examples per entry are authored fixtures. | Reuse actual lookup semantics where applicable; preserve explicit status for programs that do not yet exist. |
| [Portable construction registry](/Users/dmitry/storyweavers/grammarworlds/portable/catalog.py:12) | Importing `grammarworlds.portable.language` registers **29** GF-inspired, Codeco-inspired, or local constructions. | Typed construction distinctions and source mappings, not a complete GF implementation. |

The head library is an existing-word-distribution reranker. Storyformers is a residual attribute system with a joint next-latent readout. These are related design sources but their JSON contracts are not interchangeable.

## Complete symbolic-head seed map

`table` means the finite lookup tables run on already structured, correctly scoped inputs. It does not mean the module parses those inputs from arbitrary text. `program` means activation raises `ProgramRequired`.

| IDs | Behaviors in order | Status in local library |
| --- | --- | --- |
| P001–P008 | Subject-number retrieval; person agreement; tense anchoring; auxiliary complement; determiner completion; verb argument expectation; coordination parallelism; clause-boundary tracking | P001–P007 table; P008 program |
| P009–P016 | Repeated-prefix continuation; entity-name retrieval; pronoun antecedent distribution; lexical repetition suppression; sense disambiguation; whole-name completion; ordered successor; register continuity | P013/P015/P016 table; remainder program |
| P017–P024 | Current location; current ownership; object condition; containment chain; reachability; resource sufficiency; instrument suitability; physical concept carrier | P023 table; remainder program |
| P025–P032 | Latest state override; precondition satisfaction; causal-parent retrieval; consequence retrieval; temporal precedence; duration compatibility; simultaneous-event consistency; undo/restoration | P032 table; remainder program |
| P033–P040 | Active goal; goal blocker; plan frontier; character-specific belief; witness access; source reliability; unresolved uncertainty; promise obligation | All program |
| P041–P048 | Speaker continuity; addressee resolution; question-answer focus; adjacency-pair expectation; conversation repair; shared knowledge; speech intention; turn-taking | P044/P047 table; remainder program |
| P049–P056 | Premise completion; unresolved-thread retrieval; emotional cause continuity; emotion regulation; relationship-specific behavior; state-driven turning point; resolution verification; final-image selection | All program |
| P057–P064 | Predicate-filtered retrieval; abstract-role transfer; conditional continuation counts; counterevidence retrieval; evidence freshness; correlated-evidence discount; sparse-context backoff; null-evidence abstention | P059 table; remainder program |

Only **six** have active storytelling adapters: P001, P002, P007, P013, P023, P059, as declared in [head_adapter.py](/Users/dmitry/storyweavers/grammarworlds/storytelling/head_adapter.py:19). The adapter deliberately abstains for unavailable structural/intent inputs rather than fabricating activity. For example, tools are supplied from guard-approved candidate actions; pronouns require a sufficiently grounded subject. The annotated path uses the previous token's attribute posterior plus committed world state, not arbitrary attention over all annotated history.

## Actual lookup-head computation

[Source](/Users/dmitry/storyweavers/grammarworlds/symbolic_heads/runtime.py:30) records contain `id`, `channel`, `scope`, `key`, `confidence`. A request contains `head_id`, `query`, `scope`, and `strength`. Selection is exact and case-sensitive; channel and scope must agree. Selection weights times source confidence normalize over matching records. Projection maps each selected source to a distribution over symbolic feature strings. Missing selection/projection support abstains.

The three stages in [HeadLibrary](/Users/dmitry/storyweavers/grammarworlds/symbolic_heads/runtime.py:102) are:

1. Selection table: `(query, source_key) -> positive weight`.
2. Projection: `(source_key, feature)` with an exact `(query, source_key, feature)` override.
3. Receiver: `(feature, next_word)` with query-conditioned override, interpreted as a multiplier or smoothed count.

[rerank](/Users/dmitry/storyweavers/grammarworlds/symbolic_heads/runtime.py:167) adds gated log-score adjustments over the existing grammar candidate set. It cannot revive an excluded word. Missing multiplier rows mean factor one. Count receivers use the current grammar prior as a pseudocount. Supporting IDs and attention weights survive in the trace. Source confidence is used both in attention selection and the final confidence gate; normalized attention one does not turn a weak source into full evidence.

None of this writes entity ownership, emotion, events, or residual attributes. A proposed Storyformer head needs an explicit adaptation specifying what its emitted feature means and where it is consumed.

The newer [entity event-line exporter](/Users/dmitry/storyweavers/grammarworlds/storytelling/event_lines.py:21) is especially useful for physical/causal supervision. It replays real guarded events and records stable entity lines, shared event IDs, full before/after field changes, movements, participants, paired dialogue, declared dependencies, and global flags. It distinguishes `frame.*` roles, grammatical subjects, `changed`/`moved`/`renamed`, `state.add:*`/`state.remove:*`, `concept.changed:*`, and source/destination holders. Mention, QA-context, and causal-context tags alone do not imply participation. It explicitly marks guard reads incomplete and local lines not independently executable. A before/after diff can supervise a state-change feature; it is not permission to replay arbitrary changes. See the [event-line contract](/Users/dmitry/storyweavers/grammarworlds/storytelling/EVENT_LINES.md:29).

## Existing semantic bundles and important aliases

[candidate_attributes](/Users/dmitry/storyweavers/grammarworlds/storytelling/attribute_grammar.py:139) emits these top-level fields:

`pos`, `syntax_role`, `entity`, `entity_features`, `state_scope`, `nominal`, `clause`, `action`, `action_scope`, `assertion`, `quoted`, `speaker`, `listener`, `modifier`, `event`, `unresolved`.

Useful nested concepts include:

- `nominal`: description type, lemma, modifiers, mass/countability, determiner, number, person, owner, alternatives, coordinated members.
- `clause`: subject binding, predicate, tense, polarity.
- `action`: lemma, construction, modality, arguments (`object`, `recipient`, embedded `action`, `reported_clause`), modifiers, copular complement.
- `event`: candidate scene name/kind, scope/status, coarse roles (`actor`, `patient`, `instrument`, `destination`), declared causes, attention tags.
- `entity_features`: actual before-scene carrier state, including location, properties, and meme magnitudes.

[SemanticRules](/Users/dmitry/storyweavers/grammarworlds/storytelling/semantic_rules.py:59) attaches these at typed construction time. It does not infer the referent of a common noun by spelling. An NP's grammatical object is not automatically a scene-frame patient, and an embedded reported/desire predicate is not automatically a committed event.

| Current names | Semantic mismatch / proposed migration treatment |
| --- | --- |
| Storyformers `entity`; Grammarworlds `entity` | Storyformers annotation uses a category such as `girl` or `scissors`. Grammarworlds uses a physical entity ID. Map Grammarworlds `entity` to Storyformers `entity_id`; never alias these blindly. |
| `entity_id`, `actor_id`, `recipient_id` | Storyformers IDs are span-derived `eN`; Grammarworlds world IDs need a stable conversion. Keep human names separate from IDs. |
| Storyformers `pos`; Grammarworlds `pos` | Storyformers uses compact tags (`n`, `v`, etc.) and merges common/proper nouns. Grammarworlds uses UPOS-like `NOUN`, `PROPN`, `AUX`, etc., plus a composite `PRON+AUX`. A conversion needs a declared loss policy; properness and auxiliary status deserve separate retained features. |
| Storyformers `event`; Grammarworlds `event` | Storyformers `event` is a string phrase with separate `event_id` and `event_type`; Grammarworlds `event` is a candidate-scene object. Preserve scene context separately from predicate event identity. |
| `role`, `syntax_role`, `action.arguments`, `event.roles` | Token semantic role, syntactic dependency/constituent role, predicate argument, and coarse scene role are distinct axes. A single role field cannot encode all four without scope. |
| `location`, `owner`, `holder`, `container` | These are different relations. A location string naming Lily is not enough to establish legal ownership, current possession, or physical containment. |
| `assertion`, `factuality`, `modality`, `quoted` | Related but not synonymous. `reported` identifies an attribution frame; it is not a truth value. `desired` is not an actual-state claim. Retain event/proposition/speaker scope. |
| `number`, `person`, `pronoun` | Agreement features belong to a bound NP/entity or clause controller; they are not properties of every nearby noun. |
| `__grammar_i` | Private learned predicate, not a semantic category. Rename or bind it to a canonical feature only after checking every reader and writer and demonstrating compatible scope and meaning. |

The full-story annotation schema [currently requires string-valued attribute pairs](/Users/dmitry/storyweavers/storyformers/annotation.py:62). The residual registry already admits booleans, strings, numbers, arrays, objects, entity references, and generic JSON in [neuron_spec.py](/Users/dmitry/storyweavers/storyformers/neuron_spec.py:10). Thus new catalog type definitions can be richer than the annotation exporter, but should declare the adapter requirement rather than claim immediate end-to-end ingestion.

## Causality and candidate-versus-observed meaning

Grammarworlds' [joint sampler](/Users/dmitry/storyweavers/grammarworlds/storytelling/attribute_sampler.py:15) preserves whole word/attribute alternatives and correlations between terminals. Candidate plans may already hypothesize future participants, but those remain **proposed latent alternatives**, not an observed teacher annotation of the eventual chosen future. Conditioning a visible word does not force one latent analysis; event commit occurs only after END.

Storyformers' [causal annotation path](/Users/dmitry/storyweavers/storyformers/prefix_annotation.py:128) receives only the prefix ending at the current word. A later patient may link to a preceding trigger; it must not be inserted retroactively into that trigger's earlier annotation. Deterministic positions, spaces, and punctuation are local metadata. An attribute catalog should distinguish:

- observed/prefix-supported facts;
- inferred but unresolved hypotheses;
- expectations about missing future arguments;
- hypothetical, negated, desired, reported, and observer-relative propositions;
- physical state and concept magnitudes attached to identified carriers.

For example, after `Lily took`, `expects_patient=true` is causally available given a suitable parse; `patient_id=scissors` is unavailable as an observed fact. A generated latent can entertain a candidate patient distribution, but should identify it as a hypothesis and preserve alternatives. An emotional or narrative feature must name its carrier/scope rather than create an unembedded abstract story fact, consistent with [story.py](/Users/dmitry/storyweavers/story.py:37).

## Storyformer grammar-neuron contract and actual limits

[GrammarNeuron.activate](/Users/dmitry/storyweavers/storyformers/grammar.py:144) matches the **entire supplied context**, returning all weighted derivations that project a dictionary. A leading/trailing bounded `Gap` provides selective matching; a bare token pattern matches a one-record context only. `query` is the last visible record. Captures bind whole terminal records, while `Ref` reads a capture/query field, including nested dotted paths. Matching field-to-`Ref` supports equality joins between entity IDs or other observed fields.

Supported operations are literal typed equality, finite `OneOf`, `Present`, sequence, weighted alternative, finite repetition/gap, capture, copy via `Ref`, and declared-table `Lookup`. Tables can use canonical JSON keys for composite nonstring lookup inputs. Missing references or table entries abstain. A repeated capture name requires equality of the **entire record**, not merely the same entity; use distinct captures plus ID equality for repeated mentions.

[parse_neuron](/Users/dmitry/storyweavers/storyformers/neuron_spec.py:112) caps a proposal at 64 rules, 512 syntax units, bounded nesting, finite repetition no longer than the context, and a match-state budget (default 20,000). This is a bounded pattern language, not arbitrary recursive CFG/PCFG, full GF, a general ILP interpreter, or a graph query engine.

Important unsupported or limited behaviors:

- No explicit NOT, absent-key test, inequality, numeric comparison, arithmetic, count aggregation, argmax/latest/nearest selector, causal graph traversal, unit conversion, or variable-length output construction.
- `Present` means non-null. An absent field and a present null behave differently for exact null matching. Boolean false is not null and not numeric zero.
- Multiple gap alignments and multiple matching rules contribute separate masses; they can accidentally multiply one underlying fact's influence. Match provenance helps diagnose this but there is no automatic dependence discount.
- A future-facing encoder relation must be recast as a current expectation. A causal head cannot read the future noun to label its earlier determiner.
- Read tests may address nested fields, but emissions write whole top-level attributes. An emitted key containing a dot is not automatically a nested update operation.
- A `Ref` can copy an entire object/list, but the language does not implement arbitrary list append, set union, deletion of a nested element, or joins over collections.
- Whole-context hard matching cannot read a distribution over field values: blocks expose each residual attribute's winning view. Competing scores remain stored but downstream grammars see one value.
- `OneOf` is safe for literal alternatives; its runtime comparison does not resolve each entry as a dynamic capture expression.

## Residual and readout implications for the new catalogs

[GrammarHead](/Users/dmitry/storyweavers/storyformers/transformer.py:55) has one neuron, one operation (`add` or `suppress`), a strength, and null mass. All activated rules/alignments currently combine; 64-neuron banks with top-one routing are not implemented. For each match, its signed delta is `strength * match_mass / (null_mass + total_match_mass)`.

[StoryformerBlock.forward](/Users/dmitry/storyweavers/storyformers/transformer.py:87) makes every head in a layer read the same pre-layer snapshot. Query position `i` sees only `0..i` and writes only `i`. Consequently, copied `actor_id` may describe the current token/event context; a head cannot patch the earlier actor token or erase a past annotation. Later layers can read earlier-layer writes. Observed token and positional fields are protected.

New attributes are supported: an emitted key creates a new evidence table. “Suppress” subtracts score for a particular value; it does not delete a dictionary key, prove the opposite boolean, or globally retract a world fact. Unknown/null stays the zero-score alternative. A known observed non-null value begins at score one; with default strength one, a single new match has delta below one, so an override can require additional evidence or a stronger head. Novel features need only positive evidence to beat null.

[GrammarProjection](/Users/dmitry/storyweavers/storyformers/transformer.py:153) evaluates vocabulary-root neurons and emits complete bundles; it normalizes joint mass, then groups words for top-k presentation. All bundle alternatives for a kept word survive. The current learner fits fixed output rule weights, while the separate induction/review code proposes structures and performs bounded revisions. A catalog entry should not claim its head weight, selector, or semantic definition has already been learned.

The new files can therefore be **plausible design specifications with an optional executable seed**, with explicit support labels such as `current_dsl`, `requires_precomputed_feature`, `requires_selector_extension`, or `requires_state_module`. Supplying a precomputed latest-owner field is a legitimate baseline, but it is not evidence the grammar itself computed ownership chronology.

## A taxonomy broad enough for 1,024 useful specifications

Use semantic family and computational mechanism as independent tags. The following 32 families offer coverage; **do not force 32 mechanically generated synonyms into each**. More productive families can receive more entries while small ones remain small. Each head needs a contrastive behavioral distinction, and several heads may legitimately read/write the same canonical attribute.

| Family | Useful distinctions for attributes, selectors, and grammatical constructions |
| --- | --- |
| 1. Token form and phrase boundaries | Word/space/punctuation, compound/name continuation, clause/quote/sentence boundary, partial versus complete constituents |
| 2. Morphology and agreement | Person, grammatical number, countability, tense, aspect, mood, voice, polarity, inflectional form, controller identity |
| 3. Noun-phrase construction | Definiteness, quantification, possessor, adjective scope, apposition, partitive, coordinated referents, nominal versus physical entity |
| 4. Predicate valency | Intransitive, transitive, ditransitive, locative, copular, infinitival, clausal and object-control complements; filled versus expected slots |
| 5. Argument identity and role | Agent, experiencer, theme, patient, instrument, beneficiary, recipient, source, goal, stimulus; predicate-relative binding |
| 6. Clause linking and extraction | Coordination, subordination, relative attachment, condition, concession, comparison, control, raising, ellipsis |
| 7. Reference and accessibility | Antecedent identity, alias, coreference candidate, number compatibility, binding domain, discourse scope, contrastive disambiguation |
| 8. Lexical semantics | Sense, category, part/whole, synonymy, antonymy, affordance, selectional compatibility, ordered category successor |
| 9. Spatial position | Place, source, destination, path, orientation, relative position, deictic center, viewpoint frame |
| 10. Containment and access | Container, support, enclosure, barriers, reachability, visibility, access prerequisites, nested containment |
| 11. Possession and exchange | Owner, holder, borrower, beneficiary, transfer source/goal, loan versus gift, failed versus completed transfer |
| 12. Object condition | Integrity, shape, material, cleanliness, openness, attachment, functionality, temperature, freshness, repairability |
| 13. Quantity and resources | Count, amount, unit, capacity, requirement, deficit, surplus, reservation, depletion, replenishment |
| 14. Event structure | Trigger, participants, phase, completion, repetition, interruption, restart, cancellation, result state |
| 15. Temporal relations | Before/after, overlap, containment, onset/end, duration, recurrence, reference time, flashback scope |
| 16. Causal relations | Cause, enablement, prevention, explanation, motivation, direct versus inferred consequence, alternative causes |
| 17. Modality and assertion | Ability, permission, obligation, intention, desire, possibility, counterfactual, negation, reported versus asserted |
| 18. Goals and planning | Active goal, priority, blocker, prerequisite, eligible step, means-end link, attempt, success, failure, abandonment |
| 19. Perception and evidence | Observer, modality, witness access, source, directness, report chain, confidence, freshness, defeater |
| 20. Beliefs and knowledge | Knower, believed proposition, false belief, ignorance, nested viewpoint, belief revision, common ground |
| 21. Emotion and appraisal | Carrier, valence, intensity, cause, target, anticipated event, relief, shame/pride, regulation, mixed states |
| 22. Relationships and social roles | Directed trust, affiliation, rivalry, kinship, authority, dependency, cooperation, deception, repair |
| 23. Dialogue roles | Speaker, addressee, turn, first/second-person binding, quotation nesting, vocative, floor allocation |
| 24. Speech acts and commitments | Question, request, offer, warning, promise, refusal, acceptance, apology, acknowledgment, fulfillment/release |
| 25. Question and answer structure | Requested role, focus, presupposition, answerability, contrast set, short answer, follow-up anchoring, repair |
| 26. Information structure | Topic, focus, givenness, contrast, salience, background, foreground, emphasis, discourse center |
| 27. Narrative structure | Premise, inciting change, unresolved thread, attempt, setback, enabling turn, partial resolution, concrete final image |
| 28. Style and presentation | Register, politeness, viewpoint distance, narrative tense continuity, sensory specificity, repetition purpose |
| 29. Analogies and in-context learning | Exact/fuzzy prefix reuse, structural role mapping, relation transfer, exemplar choice, task cue, exception |
| 30. Uncertainty and competition | Ambiguous entity/sense/attachment, alternative hypotheses, no evidence, conflicting evidence, abstention, calibrated expectation |
| 31. Evidence combination | Provenance sharing, independent support, reliability gating, stale evidence discount, normalization, backoff support |
| 32. Prediction and residual control | Candidate support, suppression target, forbidden protected writes, layer readiness, feature alias consistency, expected future category |

A common record contract should retain stable ID, canonical name, typed value semantics, applicable scope, missing-value meaning, causal availability, source evidence, examples/counterexamples, consumers/dependencies, and implementation status. Head records additionally need query/selector/projection/write policy. Grammar records need a bounded match pattern and projection or an explicit abstract construction plus required extensions. Keep human-readable names separate from stable IDs so LLM renaming does not silently change meaning or break consumers.

For realistic smoke checks, include at least a positive case, a one-fact contrast, a distractor, and an unknown/no-match case per mechanism. Add examples where the same entity appears twice, negation scopes over a desired/reported event, and a later state contradicts an earlier state. Those expose the highest-risk shortcuts in literal suffix matching.
