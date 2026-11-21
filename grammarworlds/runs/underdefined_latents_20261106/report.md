# Underdefined story: latent stream inspection

Fresh seed-7 runs, heads enabled. No rerolls, text edits, new rules, or engine changes.

## Mapped generation

Ada fetched the tape from the bench. She used the tape to repair the book.

The target has no authored event sequence. The source fetch/mend segment is explicitly selected from the annotated kite story; automatic source-segment retrieval is not involved.
Target role bindings are inferred. The existing paper-world fixture declares paper material for the book and paper-patching capability for Ada and Omar.

| Stage | Latent event | Probability | Physical consequence |
|---|---|---:|---|
| Mapping | fetch → paper repair; Ada/book/tape/bench | 100% | Only feasible complete binding |
| Scene 1 | fetch(actor=Ada, item=tape, source=bench) | 100% | Tape: bench → Ada |
| Scene 2 | patch_paper(actor=Ada, item=book, tool=tape) | 100% | Book: torn → repaired |

Omar is rejected because he does not hold the book. Kite repair is rejected because compatible carriers/capabilities are absent.
The committed segment completes and replays; it does not set a whole-story ending flag.

## Word-level uncertainty

There are 19 sampler steps including punctuation and two END markers. Only two steps have more than one possible word; heads change one distribution.
At the start of repair: she 40%, Using 25%, With 25%, Ada 10%.
After selecting she, three annotation bundles survive: use tape to repair (50%), repair with tape (25%), fix with tape (25%). All bind the same actor, object, tool and physical event.
At the following step, head reweighting gives used 41.18%, fixed 29.41%, repaired 29.41%. Selecting used resolves the remaining construction ambiguity.

## Attribute inspection

- Tape is observed at the bench during fetch and at Ada during repair.
- Book remains observed as torn during pre-commit token generation; repaired is a proposed effect until the event commits.
- She resolves to Ada; the imported source name and kite-only properties are absent from live target entity attributes.
- The repair verb is tagged as an embedded action with book as its object.
- Defect: the book token has syntax_role=predicate despite correct entity=book and action.arguments.object=book. The shallow syntax role is inherited incorrectly under the embedded construction.
- The bench mention is a nominal description without a token-local entity binding; the enclosing event correctly binds source=bench. Role-complete event metadata does not imply every mention has a local referent.

## Original unordered controller

Ada said, “I would like to repair the book.” Ada said, “I could help you.” She fetched the tape from the bench. Ada said, “I can help you.” Ada handed Omar the tape. Omar handed the tape to Ada. Omar told Ada, “I could help you.” Ada said, “I want to repair the book.”

Latent events: intent → offer → fetch → offer → transfer → transfer → offer → intent.
It reaches the eight-event limit with the book still torn. Its available operations do not include repair.
Running mapping on the unchanged original world yields zero feasible mappings because paper material and repair capabilities are undeclared; these are not silently invented.

## Assessment

The mapping makes an imported repair sequence executable and grounded. It has not yet produced an open-ended event predictor: source sequence selection is supplied, mapping selects one complete program, and each scene here has one ready event.
The resulting segment lacks a narrated premise, turn, dialogue and ending image. Text quality remains limited by the supplied event sequence; additional annotation richness alone does not supply story structure.
