# Batch 2 prompt notes — provisional until all six reviews finish

Do not release v3 or start batch 3 until stories 09–14, all feedback and all
independent findings have been reviewed. Frozen v2 remains the batch-2 prompt.

Current evidence from reviewed market, camp, pottery and orchard:

- A negation operator needs positive content, but a conditional edge or complete
  utterance may need a distinct negative proposition. Pottery's restart condition
  leads to **insufficient** time; camp's utterance prohibits moving closer. Do not
  silently drop negation when composing propositions.
- A warning utterance must retain its condition and possibility. The possible
  hole from a proposed repair is not simply an asserted hole proposition.
- Retain instrument indication, measured property and character claim as
  different kinds of evidence. A true observation of a faulty scale is not a
  false observation; its inferred mass may be false. Preserve each time phase.
- Bound quantification over particular objects is not kind-level generic
  reference. `Each oatcake` ranges over the actual pair. Two pieces per cake does
  not assert that every piece produced was placed, or that portions were equal.
- An ability can be asserted while its underlying event remains hypothetical.
  Label the underlying action plainly and attach the capacity/modal separately.
- Modal ellipsis can retain a positive predicate while changing polarity:
  `She might` after `She won't want it` means possible wanting, not possible
  non-wanting.
- An unresolved role referent, such as Willa's selected pear, may denote one of
  two existing objects. It does not create an additional physical fruit.
- Preserve source gaps: camp's lantern handoff, pottery's handle construction,
  kiln schedule and final cup layout, market's final scale location. Do not make
  a plausible transition into a narrated event.
- Search existing meanings before proposing a name: orchard edibility is already
  covered by `affordance_eating`; ripeness and freshness are different dimensions.
- A discovered defect is not automatically caused by the preceding action.
  Orchard's bruise is noticed after picking/carrying, with no established cause.
- An explicit inability report is not automatically an emotion self-report.
  Camp's fear-like context does not make `cannot search` a named affect predicate.
- Attach dimensions to their actual cue: `everywhere` supplies spatial extent;
  any habitual interpretation belongs to the recurring action construction,
  not a temporal-frequency label on that spatial adverb.

Five corrected example candidates are saved in `batch2_example_candidates.json`.
They include their current source annotation hashes and referenced entity,
event, proposition and scope records. They remain draft until the six-story gate.

Possible vocabulary follow-up: pottery's person/body-part/object ergonomic fit
is narrower than generic graspability. Current annotation uses existing fields
and explicit legacy description; no new canonical field has been accepted.

Await costume and pond feedback, final review of all corrections, and concrete
corrected examples before freezing the next prompt.

## Final gate

All six stories accepted. Costume adds content-arrow paraphrase checks: retain
spoken need/knowledge, omit unspoken outer wrappers, and keep a requested
prohibition negative while its operator target remains positive. Pond adds the
imperative speaker/subject distinction and unawareness content versus negated
noticing. The released v3 bundle contains seven examples and unchanged six-field
extension registry. The earlier provisional notes above record the draft stage.
