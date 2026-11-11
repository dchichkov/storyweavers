# Independent semantic review: greenhouse and seaside

Reviewer: `sae_research`, 2026-11-07. This review used the frozen v1 prompt, the original complete stories, every paragraph of assembled word annotations, entity/event/scope/proposition registries, evidence and feedback. Word references below are zero-based word ordinals, not lossless-token positions. No annotation files were edited by this reviewer.

## Coverage and result

- **03_greenhouse:** all 31 paragraphs, 738 words / 1,643 lossless tokens; 76 entities, 129 events, 32 scopes, 15 propositions. The material quotation-recipient discrepancies found below have been repaired by the owner and independently verified. No remaining material finding from this bounded review.
- **04_seaside:** all 32 paragraphs, 806 words / 1,796 lossless tokens; 70 entities, 142 events, 37 scopes, finally 40 propositions and 180 distinct feature keys. All six semantic/syntactic corrections below were repaired by the owner and independently verified in the regenerated output, along with the proposed affordance's value shape. No remaining material finding from this bounded review.
- Both reported zero validator errors when inspected. Entity mention registries and per-word entity IDs agreed in a reciprocal check. Actor/recipient bindings agreed with event participants, including individual members of explicitly registered groups. These checks supplement the manual reading; they do not establish semantic correctness.

## Greenhouse findings — verified repaired

1. **Contradictory quotation audiences, w90–92 and w551–560.** `q2.addressee_ids` originally named Nia (`e1`) as the audience of her own “They look thirsty,” although `ev16` and w94 correctly identified Bell (`e2`). `q15`/`q16` likewise named Nia as audience of her own snap/umbrella explanation to Okafor, although `ev97` and w554 correctly identified Okafor (`e3`). Verified current scopes now use `q2 → e2`, `q15/q16 → e3`.
2. **Written-label attribution, w84–89.** `q1` originally retained the description “authorship inferred from named owner,” contradicting its null holder and the feedback's appropriate refusal to infer authorship. Verified current wording: “Written label names an owner; the author is unknown.” No named author is asserted.

The main chronology and identity distinctions are represented coherently: Nia waters the tomatoes with the limited rainwater before the shade failure; umbrella shade is temporary; the clip/cloth repair precedes closing the umbrella; the sunflower's drooping ceases in shade while its soil remains dry; its actual watering occurs only after the tap repair. Broken clip `e35` and replacement clip `e67` are distinct. The pebble-filled “empty” pot is empty of a plant, not universally empty. Watering-can “rose” is an attachment, not a flower. The ambiguous snap/slip report is not silently equated with an earlier failure, and no completed departure or home journey is invented.

The avoided splash at w687–691 is negated inside explicitly registered `s10` (`avoided_action`), with an avoidance goal and an evidence note denying any guaranteed outcome. That combined representation preserves the intended distinction; its `factuality=negated` must not be flattened into narrator proof that no splash occurred.

## Seaside findings — verified repaired

### 1. False belief content used as an actual cause — w383

Source: Tessa “had been so sure she'd spotted the landmark that she hadn't looked closely.” The current asserted `causal_parent` has `cause: p17`, whose text is “Tessa identified the correct landmark before choosing.” That is the content of her mistaken belief, not a true event that caused the failure to inspect. `p17` belongs to `belief1`, but the causal bundle is in `s0` and carries no attitude/holder wrapper for its cause.

Use the actual certainty attitude `ev62` as the cause. Keep `p17` as the content of that attitude. The narration licenses certainty causing inadequate checking; it does not license correct identification causing it.

### 2. Negation pointers select corrected or already negative contents — w368, w382, w419

`negation_scope_id` is A0228, the identity of content governed by a negation operator.

- **w368 “not down here” → p16:** p16 says the route follows the upper path “rather than the lower shelf route.” Negation applies to the lower route constituent, not the whole corrected route proposition. Introduce/select positive content such as “The dotted map route follows the lower shelf route.”
- **w382 “hadn't” → p18:** p18 already says Tessa did **not** inspect closely. The operator should target positive close-inspection content, while the existing negative proposition may remain useful as the narrated result.
- **w419 “no” → p20:** p20 already says **No** path around the point is drawn. Use positive map-content existence, such as “The map depicts a path around the point.” Keep the explicit zero count representation-scoped.

These are scope/polarity defects in symbolic supervision, even though the prose labels allow a human to recover the intended reading.

### 3. A contingent requirement becomes an explicit intention — w491

Source: taking the upper route “would mean” Tessa “would have to admit” her error. Current fields include `intention_holder_id=e1`, `intention_content_id=p24`, and `plan_commitment_status=considered_requirement` in `option1`. A0802/A0807 require an explicitly intended action. The sentence describes a consequence or obligation of the considered option, not an adopted intention to admit.

Keep the conditional route and requirement, using modal/obligation fields or the existing consequence event. Remove the explicit intention claim unless another supported intention construction is supplied.

### 4. Downward restraint is encoded as carrier support — w740

Source: Milo “used two apples to keep [the map's] corners down.” The `spatial_support` bundle is `{held_down_by: e50}` for corners `e52`. A0523 identifies a figure's supporting carrier and its direction; the apples restrain the paper from above rather than carry it from below.

The existing `event_instrument_binding` already correctly connects the apples to this action. Use a bound stability/holding-down description for the additional result, or omit the redundant result field. The map's support by the picnic cloth at w728 is a separate, appropriate support relation.

### 5. Conjunctive watching goal is declared met after opening only — w704

`p2` explicitly combines finding a pool and watching Captain **open and close**. The story shows the anemone opening/blooming (w690/w706); no closing is narrated. Current `narrative_resolution_evidence` points to p2 and labels it `watching_goal_met_recognition_attributed`, with p30 (Milo's recognition) as outcome.

Mark the observed opening/watch subgoal or partial satisfaction. Recognition and watching opening do not establish the closing conjunct. Retain the separate uncertainty about biological identity across summers.

### 6. Prepositional complement labeled as direct object — w216

Source: “Milo peered **at** the map.” `grammatical_object_id=e10` treats the map as a direct object, whereas A0290 is specifically the entity denoted by a direct object. Remove that field or represent the prepositional complement. The semantic perception patient can remain the map.

### Final verification

The current assembled output and registries have all six corrections:

- w383 uses actual certainty event ev62 as the cause and separately retains p17 as `attitude_content`.
- w368/w382/w419 now point to positive p37/p38/p39 (lower map route, close inspection, depicted path). Their actual negation operators remain on the word records.
- w491 carries the conditional requirement in `modal_base` with p24 content and p23 condition; the unsupported intention fields are absent.
- w740 retains the actual apples' instrument binding and no longer emits carrier support.
- w704 selects p40, Milo watching the recognized anemone opening, and explicitly records partial satisfaction with closing unshown. Recognition remains separately attributed through p30.
- w216 has no direct-object label; w217 carries `prepositional_object_id=e10`.

The regenerated validator reports no errors. These checks inspect the actual outputs rather than relying on the owner's repair summary.

## Proposed `affordance_supporting`

The proposed meaning is a legitimate narrow gap: a particular surface can support a particular object even when placement never occurs. The existing catalog distinguishes actual carrier support (A0523), an actor carrying (A0689), bodily sitting (A0692), containment (A0693), and climbing support for an actor (A0691). None directly expresses the unperformed basket-on-wall capability stated at w648–656.

The name follows the existing `affordance_*` gerund pattern, and the definition correctly avoids asserting placement. Recommend the example/value use an explicit capability, e.g. `{"object_id":"e14","can_support":true}`, with the existing bound surface/entity, scope and assertion status. Omit `placement_occurred:null`: unobserved placement is already expressed by omission and by keeping the hypothetical placement event distinct. Do not generalize this basket-specific textual affordance to arbitrary weights, all future surface states, or actual support.

Verified final usage at w648 and the proposal's `example_value` now use exactly that bound capability form, without a null placement assertion.

## Preserved seaside distinctions and limits

The wrong bathhouse chimney pair `e17` remains distinct from rock landmark `e8`; Tessa's local name and incorrect belief are explicit. Map marks and the final sketch have separate IDs and representation links. Static path descriptions do not create walking events. The missing marked path is not converted into absence of a physical shore passage. Rising water and narrowed clearance do not receive invented measurements. The scramble is proposed and rejected, while the climb back to the fork is actual. The promised return before two is not marked completed. Wind weakens without becoming universally absent. The basket's potential resting place does not generate an unseen placement/unpacking event, and the anemone metaphor does not create a literal flower.

This review does not certify a complete ontology or every possible fine-grained POS choice. It prioritizes trainable semantic distinctions: evidence attribution, holder/content separation, stable identity, correct role binding, local time, and the difference between intended, observed and completed actions.
