# Independent semantic review: snow

Reviewer: `sae_research`, 2026-11-07. Reviewed the complete source story, all 36 paragraphs / 849 assembled word records, and the entity, event, scope, proposition, evidence and feedback registries under frozen prompt v1. References below are zero-based word ordinals. The reviewer did not edit the annotation.

## Coverage and result

The final inspected output contains 1,903 lossless tokens, 84 entities, 156 events, 36 scopes, 32 propositions and 166 distinct feature keys, with zero reported validator errors. Every paragraph was checked for role/coreference, scope, factuality, event identity, time and unsupported outcomes. A supplementary actor/recipient binding check found only the expected individual members Tomas and Nia attached to their joint lineup event.

All seven findings below have been repaired by the owner and independently verified in the regenerated output. The owner also split the combined holding/lifting proposal into its two action contents. No material issue remains from this bounded review. These semantic checks are independent of the clean shape validator.

## Findings — verified repaired

1. **An information goal was a desired test outcome — w135–143.** “I want to see if your red sled can keep up” originally made the desired goal `p5`, the red sled keeping up. This does not follow: Tomas wants to learn the result, not necessarily for Nia's sled to succeed. Current `goal_content_id=p29` correctly denotes learning whether it can keep up; p5 remains an open test content in s3.
2. **Ability evaluator and ability bearer were conflated — w142.** The modal bundle originally named Nia as holder despite Tomas making the proposal and the red sled bearing the tested ability. Verified current `modal_base` distinguishes holder Tomas (`e2`) from `ability_bearer_id=e22`.
3. **Nested quotation content lost attribution — w58 and w143.** The anticipated deeper snow and open keep-up question sit in child scopes s1/s3 of quotations. They originally received narrator `asserted` status because their immediate IDs did not start with q. Verified current rows retain hypothetical factuality and `assertion_status=attributed_claim`, while their quotation references remain intact. The related polite help request at w381 now also distinguishes Nia as request holder from Tomas as requested actor.

## Final corrections — verified repaired

4. **“Tomas helped” points to a result without a helper — w584.** `q19` has `utterance_content_id=p12`, whose entire content is “The red sled is free.” That loses the individual contribution asserted by Nia. Use a positive Tomas-helped proposition, with support from the actual report and narrated contribution; the existing p10 has the appropriate action meaning but is registered as the earlier request. Keep the q19 attribution distinct from the narrator's evidence.

   The w585 event reuse itself has a useful bridge: it recalls joint event ev441, gives the local grammatical subject Tomas, and supplies `event_divided_labor` with reported helper e2, shared ev441, individual pressing event ev447 and other actor e1. It does not need a fabricated second freeing event. The utterance-content pointer must preserve the same individual contribution.

5. **Tomas's failure to finish targets the collective successful start — w754.** `event_failure.affected_event_id=ev228` selects “children start racing,” an actual successful start with actor e6. Tomas's statement is about his own completion. Select his finishing predicate ev755 or an appropriately bounded individual participation episode, without making the whole group fail to start or finish.

6. **Stopping location is overprecise — w412.** “Then he planted his boots” supports a stopping/bracing action. The current asserted `motion_stopping_location` says `beside_jammed_red_sled`, although the next sentence has him “hurrying over.” Omit the unsupported exact stopping location, or retain only a location justified by the text. The evidence note already says coordinates are unspecified, but the emitted value contradicts that restraint.

7. **Reused quote action mentions lack local evidence status — w581 and w585.** These rows correctly reuse the previously narrated jam/freeing events and retain q18/q19 plus Nia as speaker, but unlike new quoted predicates they have no `assertion_status`. Explicitly give their local mentions `attributed_claim`; their original events may keep narrator-established actual factuality. This avoids depending on consumers to infer quotation attribution from a missing scalar.

Final verification: w584 now selects p32, “Tomas helped Nia free the red sled,” supported by the actual narrated contribution and q19 report; w754 now targets ev755; w412 no longer emits the unsupported stopping location; and w581/w585 explicitly carry `attributed_claim` while retaining the actual original event's factuality.

The owner additionally split the joint p11 proposal (“Nia holds the basket while Tomas lifts the sled back”) into separate positive holding and lifting contents. Verified w427 selects p31, “Nia holds the basket,” and w434/w435 select p30, “Tomas lifts the back of the red sled.” The holding instruction and lifting offer can still participate in one joint plan without exchanging agents or requested actions.

## Important distinctions preserved

- Wren's original request has no invented original addressee; Vale's later report is separate. Nia's past promise is distinct from her current report of it and from later fulfillment.
- The earlier race and Tomas's snow excuse remain historical; the excuse is his attributed explanation, not narrator-confirmed causation. The first village race and the later shared race have separate identities, and the final bell is a new occurrence.
- The runner jam, basket tipping, partly displaced loaf, restored loaf and later carrot have stable identities. The failed solitary attempt precedes the shared freeing; Tomas presses while Nia pulls. A hiss approaching is not an extra motion by unseen runners.
- The carrot disappearing under snow, the basket tipping again, and the visitors knocking are anticipated or avoided contents, not completed incidents. “Before they knocked” does not produce a later knock.
- Wren's road-swallowing thought is figurative and attributed. Eyes moving toward the sled use an explicit body-part/person bridge rather than assigning independent agency to eyes.
- Tea supplies and served tea have separate material identities; the gift bread is not forced to be a proven part of the delivered loaf. Initial custody of the red sled does not establish ownership or a prior loan.
- The delivery and later permission are actual. The final race begins, while its winner and the instructed return before dark remain unstated. The closing warmth and shared play are narrative interpretation candidates rather than compulsory literal morals.

## Limits

This is a bounded manual semantic review, not a claim of exhaustive lexical or ontology coverage. Remaining quality limits include conventionalized internal keys in object bundles, fine-grained event-part modeling, and sparse features whose absence must not be interpreted as false. The validator verifies shapes and links; it cannot detect a correctly typed pointer to the wrong proposition, a group/individual event mismatch, or an unsupported physical location.
