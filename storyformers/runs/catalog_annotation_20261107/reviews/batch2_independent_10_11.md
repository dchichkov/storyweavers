# Independent review: camp and pottery, frozen v2

Reviewed 2026-11-07 by the independent linguistic/catalog agent. Read all 40 camp paragraphs (779 words) and all 29 pottery paragraphs (709 words), then their assembled lexical records, event/entity/proposition/scope registries, contextual semantic fields, and feedback. Checked role/subject mappings separately. This is a semantic reading, not an inference from a clean structural validator.

## Corrections sent to the authors

### 10_camp

1. **w580–581, negative prohibition content.** `negation_scope_id=p31` correctly targets the positive action “Theo moves closer to recovery branch.” However, the physical prohibition utterance `ev121` also uses `utterance_content_id=p31`, omitting the negative instruction from its content. Preserve the positive operator/obligation target and add an exact negative/prohibition content record for the utterance. This follows v2's distinction between operator target and the proposition actually communicated.
2. **w104, affect field meaning.** `affect_self_report` currently stores “cannot_search_in_darkening_woods.” Theo explicitly reports inability and darkening woods, not a named emotion. The existing modal/utterance fields express the supported content. Omit this affect field or represent an explicitly uncertain fear interpretation with an observer/candidate field and evidence.
3. **w65, spatial adverb versus recurrence.** `everywhere` carries `temporal_frequency_class=habitual`, but this catalog field denotes a recurrence cue expressed by the current adverb. “Everywhere” specifies spatial extent. Habituality is supported by the encompassing “took Moss everywhere” construction; attach it appropriately to the predicate/context or omit this particular field.

Material checks passed: the prospective search/return conditions are separate from completed events; no active avoidance goal is inferred solely from “don’t want”; quotation ancestry survives nested prohibited content; branch/shadow, actual/silhouette ears, three sound occurrences, and remembered unknown “we” remain distinct. Joint finding credit includes a contribution bridge rather than treating Nora as identical to the group. Moss's animate/toy status, visible patch identity, and the unreported lantern transfer back to Nora remain explicitly unresolved. No invented permanent fear recovery is asserted.

### 11_pottery

1. **w259–265, reversed conditional consequent.** `conditional_consequent_id=p14` points to “There is time for the replacement cup to dry and be fired before the birthday,” while the source says there **would not** be time. `w264.negation_scope_id=p14` is correct locally. Add a separate negative consequent proposition and point the conditional link to it; retain positive p14 as the negation target.
2. **w201–210, exact warning content.** `utterance_content_id=p9` currently denotes “Bea makes a hole through the clay wall,” although Ivo's warning is conditional and possible: continued pushing might make a hole. Keep p9 as the positive hazard/possibility target, and use a full conditional-possible warning proposition as the expressed utterance content. Including the preceding reassurance in a compound utterance record is acceptable; it must not turn the possible consequence into an unconditional claim.

Material checks passed: old mug/new cup/replacement cup/store-bought alternative retain distinct identities; contemplated repairs and conditional time failure are not asserted completions; wall inspection does not claim a definite all-around thickness result. The report of lending reuses the original borrowing with an inverse-role bridge. The dent-to-thumb-rest report is supported by the actual easing/orientation events. Actual first and second firings remain separate, and the schedule contradiction is documented. Final bench/table layout, unreported pickup, water-to-tea transition, and missing handle construction are preserved as source gaps. Thumb personification, body-part grammatical subjects, reflected sunlight and the physical water bead are handled explicitly.

## Status

Corrections were sent directly to the camp and pottery authors and to the parent agent. No story source or annotation files were edited by this reviewer.

**Pottery resolved and verified:** regenerated w259 points to negative p33; w264 retains positive p14 as its negation target. W201 points to p34, the full conditional-possible warning, with p9 retained as hazard target. Final 709 words / 1,570 tokens, 63 entities, 123 events, 32 scopes, 34 propositions, 187 distinct fields, zero validation errors. All material findings are resolved; the documented source ambiguities remain.

**Camp resolved and verified:** regenerated w581 expresses negative prohibition p45 while w580/w581 retain positive p31 as the operator/obligation target. W104 retains the inability report in its modal fields without `affect_self_report`. Habitual interpretation is attached to the narrated predicate at w63, not spatial adverb w65. Final 779 words / 1,753 tokens, 76 entities, 157 events, 38 scopes, 45 propositions, 176 distinct fields, zero validation errors. All material findings are resolved.

Both stories are accepted after semantic review and bounded verification of the corrections. Structural validation supports shape/link integrity only; documented ambiguities remain intentionally unresolved.
