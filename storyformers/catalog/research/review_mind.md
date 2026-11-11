# Cross-review of the mental and narrative catalog

Reviewed 2026-11-07 by the GF/linguistic author against the current
`sources/mind.py`, `sources/core.py`, and residual implementation in
`storyformers/transformer.py`. This review checks semantic claims and witnesses,
not just whether the finite grammar parses. Findings were sent to the owning
author and the resulting corrections were rechecked against the modified source.
Final verification status is recorded at the end.

## Coverage

The full source was read, with targeted inspection of every family:

| Family | Sampled operations and principal check |
| --- | --- |
| Epistemic attitude | Knowledge claims, nested belief, self-knowledge, revision, disputed testimony: lack of direct checking is not lack of knowledge. |
| Goals and intentions | Criteria, decomposition, dependencies, tradeoffs, revision, closure: a narrator-attributed goal does not imply public communication or an unstated helpful motive. |
| Affect and appraisal | Mixed affect, responsibility, coping, regulation: preserve attributed source and avoid upgrading plausible behavior into explicit psychological purpose. |
| Social relations | Obligations, bounded permission, institutional authority, cooperation, consent: the witnesses generally supply explicit grants/commitments and reject inference from proximity or silence. |
| Dialogue and communication | Finite say seed, request/promise, warning/offer/apology, disclosure, repair: distinguish written from spoken communication and bind each act to its own speaker. |
| Discourse cohesion | Contrast, packaging, elaboration, topic navigation, indirect answers: current open-question state must reflect answers already present in the prefix. |
| Reasoning and memory | Hypothesis selection, analogy, counterfactuals, episodic recall, source checking: do not add recency or an absolute weak-thread premise from a relative comparison. |
| Narrative perspective | Narrator position, viewpoint/time changes, problem threads, resolution, motif/closure: slow speech is not necessarily expanded narrative granularity, and a repeated image does not imply an unstated transformation. |

The ordinary reference-sensitive distinctions are largely sound: belief versus
narrator fact, intended versus performed action, consent versus silence, memory
vividness versus accuracy, and local viewpoint versus global omniscience are
explicitly separated. Their adapter status is also explicit.

## Concrete corrections requested

| Field or operation | Defect found in the initial source | Correction requested |
| --- | --- | --- |
| `communication_channel` native cue | Generic `say` with communication event type emits `speech`, including the valid prefix “In her letter, Mia says”. No native guard establishes the channel. | Retrieve an explicitly known channel or leave channel unresolved; generic saying must not supply speech. |
| `knowledge_gap_content_id` | “She has never checked it herself” permits knowledge through testimony; it does not establish ignorance of the gate state. | Explicitly state that she does not know the state, or target the narrower direct-verification question. |
| `intention_publicity` | The tradeoff witness narrates wants/choices but emits `communicated`. | Add an explicit telling/speaking act or weaken the value. |
| `goal_motivation` | Wanting to repair Ben's kite does not by itself state the motivation `help_with_kite`. | Add the explicit helping purpose or leave motivation unknown. |
| `affect_action_tendency` | “Wants to run” is upgraded to `run_away`. | State running away or emit the weaker run tendency. |
| `affect_regulation_strategy` | Slow breathing is present, but its deliberate affect-regulation purpose is not explicit. | State that the breathing is used to calm herself. |
| Promise projection binding | The request/promise group gives every row `speaker_id=e1`, although Ben (`e2`) speaks the promise. | Use per-row act bindings; Mia remains request speaker and promise beneficiary, Ben becomes promise speaker. |
| `concealment_content_id` | Hiding a broken cup does not establish concealment of the *fact* that it is broken from a specified audience. | State the withheld fact and audience/purpose explicitly. |
| `discourse_question_stack` | The example retains the thread-location question as currently open after “Ben answers that question”. | Stop the positive prefix before the answer or update the stack after it. |
| `reasoning_selection_criterion` | `recent_witness_report` is emitted without a recency cue. | State recency or remove it from the value. |
| `mental_counterfactual_change` | “Stronger thread” supplies relative increase, not necessarily the asserted baseline `thread_weak`. | Explicitly supply a weak baseline or represent strength increase without an absolute weak premise. |
| `narrative_pace` | “Retells slowly” yields `expanded_scene`, which confuses delivery speed with story-time/discourse-time granularity. | State scene expansion or use a delivery-speed value. |
| `narrative_motif_link` | The witness says a mended-cloth image returns; the output invents an earlier torn-cloth image and a transformed return. | Supply the earlier torn image or represent repetition without transformation. |

These are witness/guard problems, not an objection to including the dimensions.
Stronger explicitly grounded examples make them useful candidates for later
learning and evaluation.

## Confirmed residual binding limitation

The earlier native carry helper warned that independent residual fields can lose
correlation. A direct execution through `StoryformerBlock` confirmed it. Give the
`belief_content_id` carry head two earlier asserted records with the same holder
and scope:

```text
source 1: belief_content_id=p_zebra, event_id=ev_a
source 2: belief_content_id=p_apple, event_id=ev_b
query:    entity_id=e1, scope_id=s1
```

Both derivations activate. Equal-score field selection produces:

```text
belief_content_id=p_apple, event_id=ev_a
```

That pair occurred in neither source. The final catalog therefore classifies all
64 formerly native heads as `adapter_required`, retaining their executable
finite matchers only under `contract.seed_matcher`. Their declared requirements
include `correlated_hypothesis_routing` and `scoped_candidate_storage`; cue
constructions also require subject/holder role binding. The contracts must retain
whole alternatives rather than flattening the seed emission into residual
fields. This fixes the catalog's runtime-support claim without claiming to have
implemented the missing adapter. The same direct execution retains the observed
`assertion_status=asserted` despite adding candidate-status evidence: status is
another independently competing field, not a guaranteed qualifier on every new
attribute. The revised contracts put candidate status inside the interpretation
envelope; the eight cue scope bundles also carry their own candidate status.

The field `event_id` is defined in the core shard as the event linking a
predicate and its attached participants. Carrying a prior attitude's event ID
onto every later mention is therefore a historical-evidence interpretation,
not necessarily the new mention's current event. A future adapter should
distinguish `source_event_id` inside evidence from the query's current event
attachment instead of silently overwriting one with the other.

## Naming and operation recommendations

- `belief_polarity` denotes acceptance/rejection, while
  `belief_acceptance_status` denotes uptake of a received claim. This distinction
  can be maintained, but document it carefully; neither should become a synonym
  for grammatical/propositional negation. A commitment-direction name may be
  clearer during a future registry cleanup.
- `narration_person` is not a duplicate of token-level `grammatical_person`:
  its scope is the teller's narration. Likewise source kind and access mode can
  coexist if source provenance and sensory modality remain different dimensions.
- Genuine suppression should target a contradicted feature/value, for example
  stale belief content after explicit revision. Do not simply change a whole
  multi-field carry head's operation to suppress: that would also suppress valid
  holder, scope, and event metadata emitted by that head.
- Adapter witnesses currently put tokens in a shared illustrative `s1` scope.
  Their scope-resolution requirements must construct nested proposition scopes
  before interpreting quoted, imagined, conditional, or attributed content.
  These fixtures are not complete rich causal annotation examples ready for
  training ingestion.

## Verification status

All thirteen listed witness/guard corrections were checked in the modified
source. Communication channel is now copied only from explicit earlier evidence;
the written-letter saying prefix produces no channel activation. Promise content
and beneficiary examples now bind Ben as speaker (`e2`) and Mia as addressee
(`e1`). The remaining corrections strengthen their positive witnesses with the
previously missing explicit evidence. The stale topic-navigation predicate was
also corrected: the positive witness leaves the question unanswered.

The final shard contains **256 linked triples, all 256 `adapter_required`**.
Exactly **64 contracts retain executable `seed_matcher` grammars**, and all
**128 positive/contrastive seed fixtures** pass when run through `parse_neuron`
and `activate`. These checks establish finite matching/projection behavior only;
they do not establish the complete adapter's semantic behavior or broad coverage.

Four contracts now specify distinct, exact-target suppression operations:

| Applicability concept | Lowered residual evidence | Required difference |
| --- | --- | --- |
| `belief_revision` | The old `belief_content_id` value | The same holder explicitly replaces the belief after receiving evidence. |
| `belief_error_status` | `belief_polarity=accepts` for the aligned claim | The holder acknowledges the error and withdraws acceptance; narrator-only contradiction is insufficient. |
| `epistemic_resolution_status` | The old unresolved `epistemic_alternatives` set | The holder settles the same question; suppressing the set does not declare every member false. |
| `epistemic_time_scope` | The explicitly expired `belief_content_id` value | The holder's attitude has an explicit end; elapsed time alone does not expire it. |

Each head writes only the target field, leaves holder/scope/event metadata alone,
requires a known earlier exact value, and yields NOOP when the holder has not
received the update. The applicability attribute is correctly associated with
the inhibitory head rather than claimed as an emitted output. Examples identify
the value whose evidence should decrease, not a new assertion or an edit to
earlier latents. These remain adapter contracts because claim identity, holder
knowledge, scope and time alignment are not supplied by the finite matcher.

The demonstrated correlation and historical-event attachment limitations are
now explicitly reasons for adapter classification, rather than caveats attached
to a native label. No claim is made that the 256 contracts have executable
semantic parsers or verified general coverage.
