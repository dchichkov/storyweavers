# Pilot preflight review

Reviewed by `sae_research` on 2026-11-07. Scope: the complete bakery and puppet
stories (854 and 841 words), current prompt/helper, catalog feature definitions
relevant to the pilots, and both in-progress `author.py` files. This is semantic
review, not approval based on structural validation. The first pass preceded the
completed annotation outputs; findings below distinguish established conventions
from author corrections awaiting verification.

## Shared conventions now addressed

- `patients` and `instruments` contain registered entity IDs. The run's catalog
  override corrects the original name-array descriptions and preserves the
  existing annotation pipeline's convention.
- Multiple predicates at one word retain correlated `event_bindings`; secondary
  events must not overwrite the primary event's scalar participants. A repeated
  mention of an underlying event uses `mention_event`, whereas separate knocks,
  readings and tests remain separate actual event instances.
- Trigger scopes are assigned before events. Whole-story retrospective evidence
  may resolve identity, but does not transfer a later state to an earlier time,
  or a narrator's knowledge into a character's belief.
- Zero-based word ordinals, lossless token indices and catalog `tN` anchors are
  different units. Evidence/support uses word ordinals; `a.anchor(w)` produces
  one-based nonspace token anchors, including punctuation.
- The prompt now distinguishes asserted teacher facts, attributed character
  claims and candidate interpretations. Fictional assertions stay within their
  fictional world. Sparse omission never means false; there is no feature quota.
  Root additionally requires exactly `asserted`, `attributed_claim` or `candidate`
  for every `assertion_status`, including nested bundles. Desired/hypothetical
  content and promised/conditional status remain separate factuality, scope or
  commitment fields; they are not promoted to actual world states.
- Contractions retain their leading component's POS/lemma plus an explicit
  contextual expansion. This policy needs to be applied to the pilots' initial
  lexical tables, which predated the clarification.

## Concrete pilot findings sent to authors

| Pilot | Finding | Required correction / verification |
|---|---|---|
| Bakery | `mended` w52, `fixing` w62 and `fixed` w504 initially created separate repairs. | Reuse one underlying kite repair; preserve the distinct later utterances and recall mentions. Review repeated birthday statements and return instructions on the same basis. |
| Bakery | Initial contraction lemmas mapped `I'd` to `would`, `I'm`/`You're`/`It's` to `be`, and `I'll`/`we'll` to `will`. | Follow the new leading-component convention, including contextual POS. |
| Bakery | Offers at w744/w757 have patient e64 (flower-topped slice), but patient-role words w746/w759 denote e20 (icing flower). | Use the literal flower patient, or explicitly retain the metonymic part/whole bridge; an unexplained ID mismatch is not a correlated role annotation. |
| Puppets | e1 Nia initially included w408/w413 `We`. | These are e7, the three friends, not Nia alone. The author acknowledged the correction. |
| Puppets | Initial `It's` w262/w368 and `It'll` w469 used auxiliary POS/lemmas; `There's` w277 also needs its leading component. | Apply the shared contraction policy. `star's` w118 is a contracted predicate, unlike possessive `Mouse's`; document `is`/`has` ambiguity if retained. |
| Puppets | p21 said Lila *fears* an appearance of forgetting, while the text explicitly says she does not want that appearance. | Preserve the stated desire; stronger affect requires an explicitly marked inference. The author acknowledged the correction. |
| Puppets | ev27/ev71/ev100 have fictional gift e18 as patient, while their patient mentions w147/w380/w502 denote physical props e16/e17. | Supply explicit realization/enactment bridges or separate coherent physical and fictional projections. Do not silently substitute the prop for the fictional participant. |
| Puppets | ev66 has patient e46 button, but its patient-role word w355 denotes the stamped flower image e47. | Bind the button occurrence w358 as patient and the flower as result/depicted content, or otherwise make the intended frame explicit. |
| Puppets | `The Moon can't be lonely forever` and `don't cut the curtain` risk being treated as factual negative events. | Preserve the deontic objection/desired ending and prohibition respectively; neither sentence alone establishes an actual absence of loneliness or cutting. Check the completed modality/scoping annotations. |

These observations were made while authors were adding features. They are not a
claim that the final outputs retain the defects.

## Cross-pilot lexical convention clarified

The initial pilots disagreed on modal and personal-pronoun lemmas. Root resolved
this as a v0 clarification, relayed to both authors: `could→can`, `would→will`,
`should→shall`, `might→may`, with force/tense retained in features; objective
`me→I`, `him→he`, `her→she`, `us→we`, `them→they`; subject `I` capitalized.
Possessive determiners keep `her/his/my/our/their`, and reflexives and independent
possessives keep their forms. Contextual object `her` must therefore be
distinguished from determiner `her`. Lowercasing alone is not lemmatization.

## Whole-story checks for the completed pilots

For bakery, nine coins minus two returned supports seven paid only as an explicit
arithmetic inference; the text supplies copper coins, not cents or dollars. The
extra half hour is a route difference, not measured total travel time. Returning
the basket tomorrow remains an intention at the end. Deictic `today` in Tessa's
retelling of a spring conversation must not become an invented dated event.
Three knocks are distinct; remembered kite repair is not three repairs. The
smudged flower and wandering letter are figurative, while the damaged icing is a
real physical state. Smile behavior does not by itself warrant a rich inferred
emotion bundle.

For puppets, keep the missing silver original, gray replacement and fictional
gift distinct. Keep Lila, her physical Mouse puppet and the enacted Mouse
character distinct; similarly do not assign loneliness to cardboard. Separate
actual speech/readings/tests from their scripted content and from merely proposed
handling plans. The text calls the audience event a rehearsal; do not silently
rename it a public performance. The Moon's physical manipulator is not identified
merely because Nia voices it. Trembling and smiling are narrated behavior; stronger
affect needs a note. The original star stays missing and the replacement succeeds;
neither later fact changes earlier local state.

## Remaining validator limits

The validator checks lossless structure, top-level types, registered fields,
entity/event/scope existence, many canonical nested IDs, scope parent cycles,
evidence ranges and primary actor/recipient agreement. It cannot establish that
the evidence supports a semantic claim. In particular:

- Event-role membership does not ensure that the mention's entity is the event's
  corresponding actor/patient, nor explain a metonymic or representational bridge.
- Primary patients, instruments, event type and factuality are not all compared
  against the event registry; a later manual feature overwrite can drift.
- Scope existence and acyclicity do not ensure correct nesting, quote boundaries,
  local time, holder knowledge or fictional-world separation.
- Nested-link checking recognizes numeric `eN`, `evN`, `pN`, `sN`/`qN` strings;
  arbitrary named IDs and metadata references are not a complete typed graph.
- Feature counts and words with some semantic annotation are coverage indicators,
  not proof that a substantive predicate/operator has been interpreted correctly.

## First bakery output review

The first emitted bakery output has 854 words, 1,941 lossless tokens, 68 entities,
162 events, 46 scopes and 29 propositions; its structural validator reports no
errors. These are an interim snapshot, not final counts. Reading the emitted
records verifies that w52/w62/w504 now share the repair event and w65/w508 share
the birthday telling. The extra half-hour, future basket return, limited meaning
of an empty basket and visual metaphors are preserved explicitly.

Further concrete corrections sent to the author:

- At w501, `You did` was assigned Tessa as event actor and grammatical subject,
  although `You` denotes Hobb and the ellipsis recalls his earlier telling.
  Reuse that telling; retain the actual outer Tessa answer as a separate turn.
- At w816, appending a reference to Pike's original instruction did not remove
  the separately created event for that same prior telling. Reuse the underlying
  event as well as keeping Tessa's actual later report.
- `I don't want a cake` was labeled an active avoidance goal. Absence of desire
  does not establish desire for avoidance. Keep the negated desire attribution.
- Goal/promise/cooperation content propositions should describe the desired or
  committed state/action, rather than recursively describing the wanting,
  offering or proposing event. Keep full attitude propositions separately when
  needed as objects of someone else's knowledge or report.

The emitted feedback still described the superseded auxiliary-based contraction
policy; the author is updating lexical annotations and their documentation.
Completed-output verification will be extended after both authors finish.

Second bakery snapshot verifies the material corrections: w501 uses Hobb and the
original telling event; w816 uses the original instruction; w746/w759 retain
explicit decoration-for-slice metonymy; no active avoidance polarity is inferred
from the negated desire; goal/promise/cooperation contents now state their target
actions or states. All examined contractions follow the leading-component policy.
This snapshot has 160 events and no validation errors under the then-current
checks. Recursive assertion-status enforcement was added immediately afterward;
the author is updating those values before the final run.

## First puppet output review

The first puppet output has 841 words, 1,899 lossless tokens, 61 entities, 165
events, 45 scopes and 42 propositions. Its intermediate validation run caught
27 uses of the superseded assertion statuses after root added the new constraint;
the author is repairing these rather than treating the snapshot as complete.

The emitted records verify the group-pronoun corrections, contraction policy,
explicit physical/fictional star bridges at w147/w380/w502, separate realized
play events beside physical handling at w747/w759, and stamped-image versus
button-carrier roles. Moon's loneliness remains fictional, its manipulator
remains unknown, and the missing original is not confused with the replacement.
The five-minute expectation is a duration; three o'clock does not acquire an
invented meridiem.

Two additional corrections were requested and acknowledged: pocket lining is a
part/boundary, not contents of the pocket; and the group commitment ev61 must be
explicitly related to Ben's realizing utterance ev62 rather than counted as two
unrelated actual utterances. The author is also separating goal/promise content
from the wanting/promising attribution, following the bakery correction.

## Final independent verification

The final read-only rerun uses the updated helper, including recursive
assertion-status validation. Both pilots pass with zero errors:

| Story | Words | Lossless tokens | Entities | Events | Scopes | Propositions | Distinct fields |
|---|---:|---:|---:|---:|---:|---:|---:|
| 01_bakery | 854 | 1,941 | 68 | 160 | 46 | 30 | 226 |
| 02_puppets | 841 | 1,899 | 63 | 165 | 45 | 42 | 204 |

All material findings above were corrected or resolved with explicit, locally
reviewable interpretations. The final puppet records remove lining-as-contents,
link the group commitment to its single realizing utterance, use target-only
goal/promise contents, preserve negated desire without an active avoidance goal,
and mark Lila's goal bundle as attributed. The final reread also verifies separate
cue instructions versus their list carrier, and the singular puppet-bearing hand
versus the later hands group. Deleted operator events leave no stale memberships.
Status normalization retains conditional/hypothetical/desired factuality and
purpose scopes rather than asserting that proposed actions happened.

No remaining must-fix material meaning or identity error was identified in this
bounded independent review. This conclusion covers the full source stories and
the pilot authors' entity/event/scope analyses, with targeted emitted-record
verification of the substantive corrections. It is not a proof of exhaustive
linguistic annotation or a canonical event segmentation. The pilots deliberately
retain documented alternatives, coarse referent extents, inferred narrative
interpretations and unknown participants. Field counts include grammatical and
structural annotation fields and should not be presented as semantic completeness.
