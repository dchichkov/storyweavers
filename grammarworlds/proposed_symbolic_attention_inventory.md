# Proposed symbolic attention behavior inventory

**Status: design proposals, not extracted transformer heads.** This document prioritizes diverse operations for a classical story generator. It is separate from the [research evidence inventory](attention_head_inventory.md), which preserves published model/layer/head instances and their qualifications.

**Initial size: 64 proposed behaviors in eight groups.** This is the starting design inventory toward the requested 1,024-behavior direction, not a claim that 1,024 distinct behaviors have already been identified. The research catalog's 1,024 entries cannot be used as that count.

## What counts as a distinct behavior

A proposal specifies `query condition → source selector → transmitted feature → probability consumer`. Changing a character, object, model, or layer number does not create another behavior. A different selector, information transformation, or downstream use can justify a separate entry when a contrastive example distinguishes it.

These are proposed **symbolic modules**. Some require several retrieval/processing stages; no claim is made that one neural attention head can implement each module. Similar proposals should be merged if they prove redundant in evaluation.

Every P-number below has status **PROPOSED / UNTESTED**. Its payload and effect describe intended implementation behavior, not a measured neural representation or causal result.

## Reading the examples

- All examples are invented. *Italics* mark the information the proposed selector should use.
- `⟦…⟧` marks the current generation point, not a literal token. Bracketed comments describe the intended context.
- Some examples abbreviate structured world records as English. These records are assumed available from the grammar, committed event frames, and persistent world state; extracting them from arbitrary prose is a separate problem.
- Several examples summarize a whole prefix or planned frame. They do not reveal future sampled words: only information already present in the prefix, world, or explicitly supplied plan is available.
- Payloads can be distributions over referents, states, or interpretations. A symbolic representation need not force a single answer.
- “Favor” and “downweight” mean changing scores among candidates. They do not mean selecting a word deterministically or guaranteeing an entire sentence.

## Proposed behaviors

### Local form and grammatical expectations

| Number / status | Behavior | Query and source selector | Example 1 | Example 2 | Proposed transmitted feature | Proposed downstream effect |
| --- | --- | --- | --- | --- | --- | --- |
| P001 · Proposed | Subject-number retrieval | Current clause → grammatical subject → number | The *boats* near the pier ⟦…⟧ | The *boat* beside the rocks ⟦…⟧ | {subject, number} | Reweight singular/plural verb forms. |
| P002 · Proposed | Person agreement | Current finite verb slot → subject's discourse person | *I* ⟦…⟧ ready. | *She* ⟦…⟧ ready. | {person, number} | Prefer am/is/are as appropriate. |
| P003 · Proposed | Tense anchoring | Current event → governing temporal frame | *Yesterday* Mira ⟦…⟧ | *Tomorrow* Theo will ⟦…⟧ | {event_time, tense_context} | Reweight tense-compatible forms. |
| P004 · Proposed | Auxiliary complement | Unfinished verb phrase → nearest governing auxiliary | Mira has *been* ⟦…⟧ | Theo *can* ⟦…⟧ | {auxiliary_chain, required_form} | Prefer compatible participles or infinitives. |
| P005 · Proposed | Determiner completion | Unfinished noun phrase → active determiner | She carried *a* ⟦…⟧ | He moved *these* ⟦…⟧ | {countability, number_constraints} | Reweight noun forms. |
| P006 · Proposed | Verb argument expectation | Current predicate → its unfilled argument slots | Mira *put the cup* ⟦…⟧ | Theo *gave Nia* ⟦…⟧ | {predicate, remaining_roles} | Favor a location or transferred object. |
| P007 · Proposed | Coordination parallelism | After conjunction → first conjunct's structure | She liked *singing* and ⟦…⟧ | He was *quiet* but ⟦…⟧ | {category, inflection, coordination} | Favor a parallel continuation. |
| P008 · Proposed | Clause-boundary tracking | Current prefix → unmatched clause openers | *Although it rained*, ⟦…⟧ | *If the latch breaks*, ⟦…⟧ | {open_clause, completion_state} | Favor a main clause when still required. |

### Lexical retrieval and reference

| Number / status | Behavior | Query and source selector | Example 1 | Example 2 | Proposed transmitted feature | Proposed downstream effect |
| --- | --- | --- | --- | --- | --- | --- |
| P009 · Proposed | Repeated-prefix continuation | Current suffix → earlier matching suffix and successor | brass *bell* … brass ⟦…⟧ | quiet *garden* … quiet ⟦…⟧ | {continuation_counts, match_length} | Boost observed continuations proportionally. |
| P010 · Proposed | Entity-name retrieval | Current entity ID → previous surface names | *Mira* hid the key. [same entity] ⟦…⟧ | *Theo* repaired the boat. [same entity] ⟦…⟧ | {entity_id, aliases, frequencies} | Favor established names over new ones. |
| P011 · Proposed | Pronoun antecedent distribution | Current pronoun slot → compatible salient entities | *Mira* arrived. ⟦…⟧ smiled. | *Theo and Nia* arrived. ⟦…⟧ waved. | {candidate_referents, probabilities} | Favor compatible pronouns; retain ambiguity. |
| P012 · Proposed | Lexical repetition suppression | Current candidate → recent uses and their predicted mass | *lantern … lantern … lantern* ⟦…⟧ | *quiet … quiet … quiet* ⟦…⟧ | {recent_frequency, overprediction_score} | Reduce excess repetition, without a blanket ban. |
| P013 · Proposed | Sense disambiguation | Ambiguous word → nearby sense-bearing relations | The *river* reached the bank. ⟦…⟧ | She *deposited coins* at the bank. ⟦…⟧ | {sense_distribution, supporting_mentions} | Reweight sense-compatible words. |
| P014 · Proposed | Whole-name completion | Partial established name → remaining name tokens | They reached *Silver* ⟦…⟧ [known: Silver Cove] | She opened *Old* ⟦…⟧ [known: Old Mill] | {name_id, next_component} | Favor the remaining name component. |
| P015 · Proposed | Ordered successor | Current sequence item → configured ordering | *Tuesday* passed; the next day was ⟦…⟧ | Step *two* finished; step ⟦…⟧ | {ordering, successor_distribution} | Favor a successor in that ordering. |
| P016 · Proposed | Register continuity | Current passage → recent register-bearing choices | *Greetings, honored guest*, ⟦…⟧ | *Hey, pal*, ⟦…⟧ | {register_distribution, scope} | Favor locally compatible diction. |

### Entities, objects, and physical state

| Number / status | Behavior | Query and source selector | Example 1 | Example 2 | Proposed transmitted feature | Proposed downstream effect |
| --- | --- | --- | --- | --- | --- | --- |
| P017 · Proposed | Current location | Entity-focused query → latest valid location event | Mira *entered the shed*. She was ⟦…⟧ | Theo *walked into the orchard*. He was ⟦…⟧ | {entity, location, event_id} | Favor grounded location words. |
| P018 · Proposed | Current ownership | Object-focused query → latest valid transfer | Mira *gave the cup to Nia*. It was ⟦…⟧ | Theo *returned the map to Omar*. It was ⟦…⟧ | {object, owner, transfer_id} | Favor the current owner. |
| P019 · Proposed | Object condition | Proposed action → latest state of its patient | The *door was locked*. Mira ⟦…⟧ | The *cup was cracked*. Theo ⟦…⟧ | {object, state, provenance} | Downweight unsupported state-dependent actions. |
| P020 · Proposed | Containment chain | Object query → nested container relations | The *key was in a box inside the shed*. ⟦…⟧ | The *ring was in a pouch inside the chest*. ⟦…⟧ | {object, container_path} | Favor reachable containment descriptions. |
| P021 · Proposed | Reachability | Proposed interaction → actor/object positions and barriers | *Mira stood outside the locked shed; the key lay inside*. ⟦…⟧ | *Theo held the cup in his hand*. ⟦…⟧ | {reachable, path, obstacles} | Reweight immediate manipulation versus approach. |
| P022 · Proposed | Resource sufficiency | Proposed action → required and available quantities | *Two boards remained; the repair needed three*. ⟦…⟧ | *One candle remained; the room needed one*. ⟦…⟧ | {required, available, deficit} | Favor acquisition or feasible action. |
| P023 · Proposed | Instrument suitability | Action query → available tools and typed affordances | *A hammer and a brush lay beside the loose nail*. ⟦…⟧ | *A needle and a spoon lay beside the torn cloth*. ⟦…⟧ | {tool_candidates, suitability} | Favor an applicable instrument. |
| P024 · Proposed | Physical concept carrier | Concept-conditioned query → entities carrying that concept | *Mira's fear rose after the growl*. ⟦…⟧ | *Theo's envy grew when Nia won*. ⟦…⟧ | {carrier_id, concept, magnitude} | Favor the carrier's manifestation; emit nothing from an unembedded concept. |

### Events, time, and causality

| Number / status | Behavior | Query and source selector | Example 1 | Example 2 | Proposed transmitted feature | Proposed downstream effect |
| --- | --- | --- | --- | --- | --- | --- |
| P025 · Proposed | Latest state override | Property query → ordered updates to that property | The gate was open, then *Mira closed it*. ⟦…⟧ | The cup was empty, then *Theo filled it*. ⟦…⟧ | {latest_value, superseded_events} | Favor current rather than stale state. |
| P026 · Proposed | Precondition satisfaction | Action query → explicit prerequisites | *The latch remained fastened*. She tried to open the lid ⟦…⟧ | *The knot had been untied*. He lifted the sack ⟦…⟧ | {met, missing, prerequisite_ids} | Reweight success, failure, or preparation. |
| P027 · Proposed | Causal-parent retrieval | Why-query or explanation → recorded cause edge | The *gust pushed the shutter*, which slammed. ⟦…⟧ | The *rope snapped*, so the bucket fell. ⟦…⟧ | {event, cause_ids} | Favor an evidenced explanation. |
| P028 · Proposed | Consequence retrieval | Event-focused continuation → recorded resulting changes | *The spill soaked the letter*. ⟦…⟧ | *The repair sealed the leak*. ⟦…⟧ | {event, resulting_states} | Favor consequences already supported by the world. |
| P029 · Proposed | Temporal precedence | Two-event query → before/after relations | Mira *lit the lamp before entering*. ⟦…⟧ | Theo *washed the cup after drinking*. ⟦…⟧ | {earlier, later, relation_confidence} | Favor consistent ordering words. |
| P030 · Proposed | Duration compatibility | Ongoing event → start time and elapsed interval | *The paint was applied a moment ago*. ⟦…⟧ | *The seeds were planted that morning*. ⟦…⟧ | {elapsed, duration_model} | Downweight implausibly immediate completion. |
| P031 · Proposed | Simultaneous-event consistency | Action query → actor's overlapping commitments | *Mira was carrying a heavy chest with both hands*. ⟦…⟧ | *Theo was holding the ladder steady*. ⟦…⟧ | {busy_resources, interval_overlap} | Downweight incompatible simultaneous actions. |
| P032 · Proposed | Undo and restoration | Current goal → reversible prior change and inverse action | *Mira tied the sack shut*. To reopen it, ⟦…⟧ | *Theo covered the window*. To let light in, ⟦…⟧ | {change, inverse_candidates} | Favor state-restoring actions. |

### Goals, knowledge, and uncertainty

| Number / status | Behavior | Query and source selector | Example 1 | Example 2 | Proposed transmitted feature | Proposed downstream effect |
| --- | --- | --- | --- | --- | --- | --- |
| P033 · Proposed | Active goal | Actor-focused continuation → unsatisfied goal record | *Mira wanted the lost key*. ⟦…⟧ | *Theo hoped to mend the sail*. ⟦…⟧ | {goal, progress, priority} | Favor goal-relevant actions. |
| P034 · Proposed | Goal blocker | Active goal → recorded obstacle | Mira wanted to leave, but *the bridge was broken*. ⟦…⟧ | Theo needed water, but *the well was dry*. ⟦…⟧ | {goal, blocker, dependency} | Favor resolving or routing around the blocker. |
| P035 · Proposed | Plan frontier | Current plan → first eligible unfinished step | *Find wood; patch boat; launch*—wood found. ⟦…⟧ | *Fetch flour; mix dough; bake*—flour fetched. ⟦…⟧ | {eligible_steps, prerequisites} | Favor an executable next step. |
| P036 · Proposed | Character-specific belief | Character viewpoint → their latest observation or report | *Mira saw the key in the drawer*, then left before it moved. ⟦…⟧ | *Theo heard the gate was open*, before Nia closed it. ⟦…⟧ | {observer, believed_state, evidence_time} | Favor viewpoint-consistent statements. |
| P037 · Proposed | Witness access | Knowledge query → visibility and presence at an event | *Nia watched Mira hide the map*. ⟦…⟧ | *Omar was asleep when Theo left*. ⟦…⟧ | {agent, event_access, modality} | Downweight unexplained knowledge. |
| P038 · Proposed | Information source reliability | Conflicting report → source track record and directness | *Nia guessed* the bridge was safe. ⟦…⟧ | *Mira inspected* the broken plank. ⟦…⟧ | {claim, source, reliability_estimate} | Reweight certainty and attribution. |
| P039 · Proposed | Unresolved uncertainty | Factual question → competing supported possibilities | *The sound could be rain or footsteps*. ⟦…⟧ | *Either Mira or Theo had the spare key*. ⟦…⟧ | {hypotheses, probabilities, missing_evidence} | Favor hedging or investigation over invented certainty. |
| P040 · Proposed | Promise obligation | Actor action query → active commitments to others | *Mira promised Nia she would return the cup*. ⟦…⟧ | *Theo agreed to keep watch until dawn*. ⟦…⟧ | {promisor, beneficiary, obligation, deadline} | Favor fulfillment or explicitly motivated breach. |

### Dialogue and conversational structure

| Number / status | Behavior | Query and source selector | Example 1 | Example 2 | Proposed transmitted feature | Proposed downstream effect |
| --- | --- | --- | --- | --- | --- | --- |
| P041 · Proposed | Speaker continuity | Quote continuation → current turn's speaker | *Mira said*, “I ⟦…⟧” | *Theo whispered*, “My ⟦…⟧” | {speaker, turn_id} | Resolve first-person references consistently. |
| P042 · Proposed | Addressee resolution | Second-person reference → intended listener | Mira told *Nia*, “You ⟦…⟧” | Theo asked *Omar*, “Your ⟦…⟧” | {addressee_distribution} | Bind second-person descriptions. |
| P043 · Proposed | Question-answer focus | Reply → unresolved question slot | “*Where is the lantern?*” “It is ⟦…⟧” | “*Who moved the crate?*” “⟦…⟧” | {requested_role, focus_entity} | Favor an answer to the actual question. |
| P044 · Proposed | Adjacency-pair expectation | Reply → previous speech act | “*Could you help me?*” “⟦…⟧” | “*Thank you for coming.*” “⟦…⟧” | {speech_act, response_types} | Favor acceptance/refusal or acknowledgment. |
| P045 · Proposed | Conversation repair | Current turn → disputed or corrected phrase | “The red cup?” “*No, the blue one*. ⟦…⟧” | “At noon?” “*I meant dusk*. ⟦…⟧” | {replaced_value, correction, scope} | Favor the corrected referent. |
| P046 · Proposed | Shared knowledge | Explanatory turn → overlap in interlocutors' knowledge | *Both saw the bridge collapse*. Mira said, ⟦…⟧ | *Only Mira saw the crack*. She explained, ⟦…⟧ | {shared_facts, listener_gaps} | Reweight reminders versus explanations. |
| P047 · Proposed | Speech intention | Dialogue continuation → speaker's communicative goal | *Mira wanted to warn Nia about the ice*. “⟦…⟧” | *Theo wanted to apologize for the spill*. “⟦…⟧” | {speaker, intended_speech_act, target} | Favor warning or apology language. |
| P048 · Proposed | Turn-taking | Next utterance → previous turn and response obligation | *Mira asked Theo a question*. ⟦…⟧ | *Nia invited Omar to explain*. ⟦…⟧ | {next_speaker_candidates, obligation} | Favor a relevant respondent. |

### Narrative organization and emotional continuity

| Number / status | Behavior | Query and source selector | Example 1 | Example 2 | Proposed transmitted feature | Proposed downstream effect |
| --- | --- | --- | --- | --- | --- | --- |
| P049 · Proposed | Premise completion | Opening → missing participant/place/problem slots | *Mira arrived at the mill*, but no problem is established. ⟦…⟧ | *The village well was dry*, but no actor is established. ⟦…⟧ | {introduced_slots, missing_slots} | Favor completing the premise. |
| P050 · Proposed | Unresolved-thread retrieval | Scene continuation → salient unfinished event | *A strange knock went unanswered*. ⟦…⟧ | *The missing ring had not been found*. ⟦…⟧ | {thread_id, salience, unresolved_state} | Favor returning to a live thread. |
| P051 · Proposed | Emotional cause continuity | Actor description → emotion-changing events | *Mira heard the growl and became afraid*. ⟦…⟧ | *Theo recovered the keepsake and felt relieved*. ⟦…⟧ | {carrier, emotion, magnitude, cause} | Favor a state-consistent reaction. |
| P052 · Proposed | Emotion regulation | Actor action → current emotion and learned coping behavior | *Mira was frightened and remembered slow breathing*. ⟦…⟧ | *Theo was angry and chose to step outside*. ⟦…⟧ | {carrier, emotion, available_coping_actions} | Favor grounded changes in emotional state. |
| P053 · Proposed | Relationship-specific behavior | Interaction → pair's accumulated relationship state | *Mira trusted Nia after repeated help*. ⟦…⟧ | *Theo distrusted Omar after the broken promise*. ⟦…⟧ | {actor_pair, trust, history} | Reweight disclosure, cooperation, or caution. |
| P054 · Proposed | State-driven turning point | Narrative midpoint → a change enabling a previously blocked option | *The discovered key unlocked the only exit*. ⟦…⟧ | *Nia's arrival supplied the missing skill*. ⟦…⟧ | {changed_state, newly_enabled_action} | Favor a consequential turn. |
| P055 · Proposed | Resolution verification | Closing passage → initial goal and present world state | *The boat was repaired and carried them home*. ⟦…⟧ | *The lost child was safely reunited with her family*. ⟦…⟧ | {initial_goal, outcome, remaining_conflicts} | Favor closure only when supported. |
| P056 · Proposed | Final-image selection | Ending → concrete objects whose states show the change | *The repaired lantern now lit the doorstep*. ⟦…⟧ | *The once-empty bench now held both friends*. ⟦…⟧ | {physical_carrier, before_state, after_state} | Favor an ending image that demonstrates the outcome. |

### Distributional evidence and control

| Number / status | Behavior | Query and source selector | Example 1 | Example 2 | Proposed transmitted feature | Proposed downstream effect |
| --- | --- | --- | --- | --- | --- | --- |
| P057 · Proposed | Predicate-filtered retrieval | Query predicate → matching past items only | *red cup*, blue bowl; retrieve red items ⟦…⟧ | small box, *large crate*; retrieve large items ⟦…⟧ | {matching_items, weights} | Favor continuations grounded in the selected subset. |
| P058 · Proposed | Abstract-role transfer | Current relation pattern → analogous earlier role mapping | *Mira gave Nia a cup*; Theo gave Omar a map. Recipient: ⟦…⟧ | *The bird carried a twig*; the child carried a rope. Carrier: ⟦…⟧ | {role_mapping, candidate_bindings} | Favor the same role rather than the same surface token. |
| P059 · Proposed | Conditional continuation counts | Current word and active feature → matching corpus contexts | Current word: gave; *recipient slot active*. ⟦…⟧ | Current word: was; *fear magnitude high*. ⟦…⟧ | {feature_bucket, next_word_counts, support} | Apply a smoothed empirical probability adjustment. |
| P060 · Proposed | Counterevidence retrieval | Candidate claim → facts inconsistent with it | Candidate: entered easily; *the door was locked*. ⟦…⟧ | Candidate: thanked warmly; *trust had just collapsed*. ⟦…⟧ | {candidate, contradicting_evidence, strength} | Reduce unsupported candidates without automatically forbidding them. |
| P061 · Proposed | Evidence freshness | Retrieved fact → age and intervening relevant events | *The bridge was checked before the storm*. ⟦…⟧ | *The latch was tested after the repair*. ⟦…⟧ | {fact, age, invalidating_events} | Discount stale evidence. |
| P062 · Proposed | Correlated-evidence discount | Active features → shared supporting event IDs | *One gift* activates kindness, gratitude, and friendship cues. ⟦…⟧ | *One warning* activates danger, fear, and caution cues. ⟦…⟧ | {shared_provenance, dependence_groups} | Avoid counting the same evidence three times. |
| P063 · Proposed | Sparse-context backoff | Feature-conditioned predictor → effective sample support | *Recipient feature has only one corpus match*. ⟦…⟧ | *Locked-door feature has hundreds of matches*. ⟦…⟧ | {sample_support, shrinkage_weight} | Back off toward grammar/base statistics when evidence is sparse. |
| P064 · Proposed | Null-evidence abstention | Query → whether any supported source exists | *No location has been established for the key*. ⟦…⟧ | *No cause is recorded for the noise*. ⟦…⟧ | {no_match, uncertainty} | Apply no factual boost; favor supported uncertainty where appropriate. |
## Relationship to the research catalog

The following are design inspirations, not evidence that the proposals have been extracted from models. Consult the linked research-catalog sections for their original citations and limitations.

| Proposed entries | Research analogy | What remains our proposal |
| --- | --- | --- |
| P009 | [Induction and continuation retrieval](attention_head_inventory.md#retrieval-patterns-and-mechanisms) | Explicit symbolic match lengths, counts, and smoothing. |
| P012 | [Copy suppression](attention_head_inventory.md#retrieval-patterns-and-mechanisms) | A configurable repetition feature for our generator; repetition alone does not diagnose neural copy suppression. |
| P015 | [Successor behavior](attention_head_inventory.md#retrieval-patterns-and-mechanisms) | An explicit ordering registry and uncertainty over successors. |
| P036–P037 | [Belief lookbacks](attention_head_inventory.md#belief-tracking-three-lookback-circuit-families) | Persistent observer-indexed facts and explicit witness-access checks. |
| P057 | [List filtering](attention_head_inventory.md#filtering-a-collection-using-a-portable-predicate) | Typed predicates over our entity/event store. |
| P058 | [Symbol abstraction and retrieval](attention_head_inventory.md#abstract-symbols-and-concrete-tokens-identity-rule-tasks) | Role mapping between story frames. |

Other entries are authored design candidates. This document does not attach a paper to a proposal merely because it contains related vocabulary. Grammar constraints, world-state retrieval, and narrative policies may be useful without a known neural analogue.

## A common interface

Each module should return:

`{feature_id, value_distribution, source_ids, confidence, support, scope}`

- **value_distribution:** alternatives such as owner IDs or grammatical numbers, with normalized weights where meaningful.
- **source_ids:** supporting tokens, entities, or events; required for checking grounding and correlated evidence.
- **confidence:** uncertainty in the selector or interpretation.
- **support:** corpus evidence available for estimating the feature's predictive effect; different from confidence.
- **scope:** applicable clause, speaker, viewpoint, event, or scene.

Keep grammar-derived features separate from world-derived features in the record so we can identify missing inputs. Read concept magnitudes only from physical carriers. A head reads committed state; it does not mutate the world merely because one candidate word receives a higher probability.

## Distributional reranking

Let C be the current grammar-supported word set and p₀ its base distribution. A possible first experiment is:

`score(w) = log p₀(w) + Σₕ gateₕ · Δₕ(w)`

`p(w | prefix, world) = softmax over C of score(w)`

Estimate a module's adjustment from corpus counts such as:

`Δₕ(w) = log p_smoothed(w | current_word, featureₕ) − log p_smoothed(w | current_word)`

This implements the proposed “current word, attention feature, next word” idea. The feature can summarize distant context; it is not necessarily the preceding token. With several features, the additive score is a model assumption, not an assertion that those features are statistically independent. P062 and fitted weights can limit repeated evidence.

Use training-only counts, smoothing/backoff, and held-out evaluation. Limit rare or extreme adjustments. Grammar exclusions remain excluded unless the grammar's own candidate-generation policy is deliberately changed.

Prefer scoring the full grammar candidate set before displaying four possibilities. If only four candidates are offered, normalize their displayed probabilities and separately report how much full-distribution mass they retain. Sampling those four defines a truncated distribution; it may discard the eventual best word if pruning happens too early.

## Evaluation and expansion rule

Start with a small subset that exercises genuinely different operations—for example P001, P009, P019, P024, P027, P036, P043, P054, P059, and P064. Dependencies can be supplied directly in fixtures before building automatic selectors.

For each proposal, create paired contexts that change only the source fact relevant to that proposal. The predicted probability shift should change accordingly. Add distractor cases and no-match cases. Test the selected source, payload, and word ranking separately.

Compare grammar-only, corpus-only reranking, and combined predictions on held-out text. Measure next-word loss, candidate coverage, calibration, story quality, diversity, and grounded consistency. A plausible hand-written example is not evidence of improved generation.

Promote an entry from **Proposed** to **Implemented**, then to **Evaluated**, only with the corresponding artifact and results. “Research-supported” should describe a specific cited observation, not an upgrade earned by our own prototype.

When expanding toward 1,024, record the closest existing proposal and the contrast that makes the addition different. Parameter variants belong under their parent unless they demonstrably implement a different operation. Keep the research evidence catalog and this proposed design inventory separate.

