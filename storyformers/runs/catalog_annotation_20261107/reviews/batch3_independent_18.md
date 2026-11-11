# Independent review: 18_trail, frozen v3

Reviewed 2026-11-07 against the frozen v3 prompt and catalog definitions. Read all 29 source paragraphs, all 753 assembled lexical records including contextual POS, lemma, identities, roles and sparse semantic fields, and all 91 entities, 134 events, 29 scopes, 35 propositions and eight evidence notes. This reviewer did not edit the author's source or outputs.

## Findings sent to the author

1. **Seven utterances include their own speaker as an addressee.** At w233, w305 and w411, Felix's `addressee_ids=[e5]` includes Felix because e5 is all three friends. Use Nia and Leni (e1/e3). At w242, w311, w481 and w566, Nia's listeners should exclude Nia: Felix and Leni (e2/e3). Ivo's later e5 addressee is appropriate.
2. **Lexical auxiliary class and contextual modal meaning are conflated.** At w62, 116, 153, 277, 286, 304, 310, 410, 448, 480 and 497, `modal_auxiliary_class` contains contextual ability or epistemic meanings. A0418 describes a lexical auxiliary class that does not choose a contextual sense. Use a consistent lexical class and retain ability/possibility/expectation in the existing `modal_base` bundles.
3. **w156 “passed” is a participle.** In “might otherwise have passed,” `verb_form=base` is incorrect; the form is participial.
4. **w564 / ev565 scopes the actual praise inside the quoted content.** “Felix praises Leni observation” is an actual outer speech event, while “Good eyes” is its quoted content. Move the speech event to s0 using a separate/secondary binding, preserving q12 on the quote. The existing secondary ev901–904 pattern already demonstrates this distinction.
5. **e14's display name reverses the mistaken interpretation.** “New trail mistaken for bend” reverses “mistake a bend for a new trail.” The event and proposition are already correct. Rename the entity to a new-trail interpretation of a bend and synchronize mention labels.
6. **w363 and w722 `spatial_frame_kind=reflection` use the wrong catalog meaning.** A0515 describes intrinsic, observer-relative or geographical directional frames, not optical representations. The reflection events are already explicit; use those and an appropriate representation/figurative field if needed. Update the evidence field list accordingly. The w722 instance was caught during bounded verification of the first correction.
7. **Two standalone spatial bundles lose their operators.** W624 `spatial_distance_band=too_close` is the prohibited target of “Don't get too close,” not a present distance claim; q14 identifies a quotation but does not itself supply prohibition. W481 `spatial_configuration=left_of` belongs to “should be,” an expectation, not an unqualified present relation. Preserve the hypothetical/prohibited or epistemic operator and relevant proposition/event provenance inside these correlated bundles or remove the redundant bundles. The utterance and event records already preserve the intended distinctions.
8. **w428 evidence lists an absent speed attribute.** Remove `motion_speed_class` from the evidence field list. The note correctly says speed is unspecified, and the actual record only supplies sliding manner.

Minor optional clarification: e20 at w85, “every station,” refers metonymically to completion of the station-stamp collection. A collection label or explicit bridge would avoid an ownership reading over physical stations.

## Material checks passed

- The last known blue marker e66 and the subsequently discovered triangle e91 remain distinct. The earlier concealed detour sign e64 is only a possible match for e91; map indication, expected sign function and actual concealed sign state are separated.
- Nia/Felix pair e6 and all-three group e5 preserve the promise, proposed departure, actual retracing, pacing and stopping participants. Leni's contextual inability to sprint or climb safely does not become a permanent inability to walk the trail.
- Shortcut and loop times are sign estimates. Felix's remaining-time report stays attributed, with no fabricated stopwatch, derived actual duration or unsupported reason for arriving just in time.
- The brass compass retains its identity across borrowing, rain protection, map use, handing to Leni and return. The final dry cover under Felix's jacket is explicit, while unreported custody transitions remain gaps rather than fabricated handoffs.
- Nia's wish to lead without asking for help remains an active goal rather than a proved final achievement. Felix's final stamped square and Leni's observed drawing support their completed goals. No unmentioned stamp operator is invented.
- The actual salamander e74 is distinct from the desired salamander role e21 and the drawn salamander e89. The final drawn triangle belongs to the picture world; it does not relocate the real animal beneath a trail marker.
- The antler comparison does not introduce a physical antler. The final three-person reflection and sketchbook image preserve the explicit ending without converting it into a permanent inferred character trait.

## Status

All findings are resolved and independently verified in regenerated outputs. Audiences now exclude the speaker; modal lexical classes retain their separate contextual senses; w156 is a past participle with perfect aspect; ev565 is a secondary actual s0 speech event while q12 remains quoted content. E14's direction is corrected and the station-collection metonymy is explicit. Both optical reflections now use the actual reflection events and lexical glosses rather than a directional frame. The two spatial bundles preserve their expectation/prohibition operators and positive-target/full-content proposition links. The absent speed feature is no longer cited as evidence.

Accepted after semantic review and bounded verification: 753 words / 1,673 tokens, 91 entities, 134 events, 29 scopes, 35 propositions, 132 distinct fields, 753 words with contextual semantic fields and maximum 30 fields per word. Independently reran the read-only validator: zero errors. Lossless concatenation exactly matches the source text. Documented source gaps and identity uncertainty remain. Structural validation supports shape and reference integrity; it does not establish semantic correctness by itself.
