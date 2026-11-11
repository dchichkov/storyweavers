# Independent review: 05_library, prompt v1

Reviewed all 32 source paragraphs and all 759 indexed words against the assembled annotations, event/entity/scope/proposition tables, authoring decisions and feedback. This is a semantic review; the clean structural validation is useful but does not establish the conclusions below. No library annotation files were changed by this reviewer.

## Corrections

1. **w356 `says`, ev357: the obligation group is incorrectly reused as the speech recipient.** The event has actor `e3` (Grandma) and recipient `e72` (Jun and Grandma). The group is appropriate for the subject of w360 `go` and the debtors of the reported obligation, but it makes Grandma an addressee of her own instruction. Use Jun (`e2`) as the contextually supported recipient, or omit the recipient if a stricter explicit-only policy is desired. Retain `e72` for the departure requirement. The outer Jun-to-Mina report at w355/ev356 is already separate and correct.

2. **w266 `said`, ev267: the utterance target loses the specific rejection.** Jun says “Not my whale” after the mitten, board books and crayon are found. The content event at w264/ev265 and the negation marker w262 correctly target the proposition that these objects include Jun's selected book (`p41`, positive content). However, the utterance's `utterance_content_id` is `p4`, “Jun cannot locate his selected whale book.” That is the broader search problem, not the proposition this utterance expresses. Add a negative proposition such as “The just-found objects do not include Jun's selected whale book,” scoped to `s9`, and use it as ev267's utterance content. Keep the positive `p41` as the target of the negation operator. Do not simply point the utterance to unnegated `p41`. No change to the broad narrative problem `p4` is needed.

## Checks that passed

- **P0–P4:** The initial atlas desire, conditional borrowing/sketching plan, Jun's retrospective account, scheduled six-o'clock closure, and Mina's promise are distinct. No atlas checkout is invented. The goal and promise contents describe their targets rather than recursively describing the wanting or promising.
- **P5–P8:** The named book, its title, its depicted whale and the physical library remain distinct. The trolley permission has the children as recipients and Alvarez as grantor; handle handoff has an explicit part-to-whole bridge. Actual use establishes the temporary trolley loan. The empty-load interpretation does not imply absence of trolley parts.
- **P9–P12:** Search locations are represented as queried regions rather than assertions that the missing book occupies each place. Found items and the collected-book group remain distinct from the missing book. The negative cover result is restricted to the examined collection. The as-if answering book is hypothetical personification, not physical speech. The recurring squeak/stop sequence and steadying hand are grounded.
- **P13–P19:** Jun and Grandma's departure group is separate from Mina and Jun's search group, apart from the recipient error above. The floor bookmark identity is maintained with an explicit continuity warning. Clue identification remains tentative for Mina, despite retrospective identification. The source does not settle whether “can't climb” is physical inability or a safety constraint, and the annotation preserves that ambiguity.
- **P20–P24:** Imagined home study, the considered reservation, the actual atlas retrieval, the request to reshelve it, and Alvarez's announced ladder action remain separate. No completed reservation, atlas loan or unseen reshelving performer is asserted.
- **P25–P28:** Jun's earlier belief and current report have their own scopes. The two mentions of his earlier book placement reuse `ev585`; the book's title singing reuses `ev127`, while Alvarez's physical title-reading utterance is `ev650`. The copied title event retains whale actor `e21` and moon recipient `e70`. Jun's inability to reach is distinguished from the positive reach proposition used by negation. The depicted stars motivate his reported shelf choice without literal stars being placed in the library.
- **P29–P31:** The physical handoff to Jun, library checkout and trolley return are supported. The final atlas-on-shelf state is recorded without an invented transition. The bookmark's “still inside” contradiction is preserved as a source continuity gap rather than repaired with an unseen reinsertion or second bookmark. The final whale and tail belong to the represented picture, with an explicit bridge from physical bookmark contact to the printed page region.

## Retained uncertainties and prompt lessons

The existing feedback adequately records the bookmark gap, display table versus display shelf, the clue question's possible readings, climbing modality, `book's gone` expansion ambiguity and the initially unspecified illustration location. These should remain uncertainties, not be converted into extra events.

For v2, add two short checks: **the subject of reported content is not automatically the recipient of the report**, and **an utterance-content link should preserve the local proposition and its polarity, rather than substitute the broader discourse problem**. A positive proposition used under a negation operator and the negative proposition expressed by a whole utterance may need separate IDs.

Review result: the story's central identity, scope, permission, loan and depicted-world semantics are sound; correct the two local role/content links above before freezing the batch.

## Resolution verification

Rechecked the fresh assembled outputs after the root's corrections: w356 and `ev357` now have recipient `e2`; w358's obligation debtor and w360's subject/actor remain `e72`. At w266, `utterance_content_id` now points to negative proposition `p43` in `s9`; w262 still targets positive `p41` under negation. Structural validation remains clean. Both review findings are resolved.
