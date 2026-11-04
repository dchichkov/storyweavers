# Expansion checkpoint — October 24, 2026

This is local architectural evidence and a reading review, not a human study or
a reproduction of the papers' quality scores. The initial mini's generated
artifacts remain in `baseline_v1/`. The current artifacts regenerate from
`python3 -m storybook_mini demo`.

## What changed

The initial prototype handled short event sequences with two aggregation rules
and one-sentence reference context. The expansion adds structured goals and
speech, two-sentence reference competition, local reflexives, mass/plural noun
phrases, ownership from event-time state, explicit companions, bounded tense and
negation, five revision relations, and paragraph organization. Every condition
uses the same sentence planner and realizer; condition-specific story scripts
are absent.

Two longer streams exercise the same resource premise: Nell and Ada borrow
Iris's lamp to bake a leaving-supper loaf. Three measures permit two baking
intervals and a usable return. One measure must be reserved for Iris's cellar
steps, so supper is abandoned and breakfast remains only a question. Lending
preserves ownership, an invitation is given outright, and future speech records
an intention without performing its action.

These are two paths through one small family. Their extensive shared text is
intentional for the experiment and must not be counted as broad plot diversity.
The content author remains responsible for every effect and causal link; the
prose pipeline does not discover physical or narrative truth.

## Reading review

Read both full tellings, the supper's all-off telling, and the scarce-oil story's
no-revision/no-marker tellings. Checked the shorter stories after the shared
changes. The full tellings show the intended differences: shortened descriptions,
active-conversation listener ellipsis, structured `I`/`you` speech, relative
descriptions, shared-verb contraction, and a contrast that becomes `However`
when its clauses cannot be combined.

The central resource consequence survives all conditions: no fuel is invented,
the borrowed lamp remains Iris's, it returns usable, and the loaf stays unbaked
on the scarce-oil path. Companions now travel explicitly. The room is windowless;
an early draft's gratuitous shutter-closing and cold-oven wording were removed
after reading because they weakened the scene's physical sense.

Specific implementation defects found and repaired:

- Object pronouns could carry across scene boundaries despite subject-focus
  reset. Accessibility now checks that the antecedent belongs to the scene.
- Same-gender competition disappeared after one intervening sentence. A bounded
  two-sentence window retains it.
- A descriptive relative clause could attach to a later target or companion.
  Such aggregations are blocked; the modified object is realized explicitly.
- Shared-verb contraction under negation could change its scope. It is blocked.
- A speaker with singular `they` could produce `I are`; speaker number and
  third-person pronoun agreement are now distinguished.
- Quoted future actions and desires need their own semantic roles; the audit
  now catches dropping those embedded roles as well as top-level roles.

Remaining storytelling defects:

- `event_log_prose`: some narration still reads like checked actions, especially
  the repeated baking and return checks.
- `repeated_name`: three female characters deliberately force conservative
  references. Names and speech tags remain conspicuous.
- `weak_turn`: the scarce-oil choice is intelligible, but a printed `Because`
  does not supply a richer experience of disappointment.
- `too_shallow`: lexical variation remains a small verb vocabulary; changing
  `checked` to `examined` is not evidence of better writing.
- Short action paragraphs still occur at scene boundaries. A paragraph budget
  alone does not establish good narrative rhythm.

No claim that the new prose surpasses the authored mini-adventure passages is
supported. This is a shared realization experiment, not a replacement for
scene-level authorship.

## Verification

54 deterministic tests pass. They cover all four streams across seven
configurations, exact ordered fact coverage, every top-level and embedded entity
role, unchanged snapshots, state-driven emotion wording, incompatible actions,
negation, relative attachment, scene/topic/dialogue barriers, same-gender
interruptions, ownership/custody, plural and deictic agreement, JSON round-trips,
and frozen text outputs.

The study generator creates twenty blank, blinded ten-reading packets for the
longer pair. Position and directed adjacent-pair balance are tested. Human-rating
validation and paired arithmetic are tested with synthetic fixtures only.
An empty response folder produces no preference claim. Source and stimulus hashes
are frozen in each study manifest; rating analysis uses that frozen design.

The local HTML notebook contains story/configuration selectors and expandable
sentence/reference tables. The generated HTML and its export are checked by the
test suite. Browser visual/interaction inspection was not completed: the browser
security policy rejected the local `file:` URL. No alternate browser route was
used. Read the local notebook directly to review its layout and controls.

## Next measurable gates

1. Collect actual blinded human ratings for the longer pair. Inspect comments
   and per-story paired differences; do not substitute pronoun/sentence counts
   for preference or claim significance from the descriptive report.
2. Author one independent held-out content family using only JSON and the shared
   lexicon. Require correct preservation of facts, roles, speaker/hearer binding,
   and ownership before adapting the renderer to it. Read every condition.
3. Compare current authored scene prose with shared realization on a frozen
   narrated-content specification, including dialogue and relevant incidental
   details. Holding world state fixed alone is insufficient.
4. Test more than a single greedy revision pass: enumerate bounded alternatives
   within a paragraph and evaluate attachment, length, repetition, and rhythm.
   Add event migration only with explicit temporal and causal constraints.
5. Extend the morphology and reference cases from observed failures; retain the
   independent counterexamples and manual reading gate rather than merely
   updating goldens to whatever the engine emits.
