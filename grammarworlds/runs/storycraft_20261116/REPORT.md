# From added beats to consequential stories

Three opt-in rewritten story families now run through the existing classical
word/attribute sampler. Each offers three authored outcomes. This campaign
changed story content as well as its execution contracts; it is not evidence
that adding annotation labels alone improves storytelling.

The default twenty-world generator remains available unchanged. Use
`--edition crafted` for these prototypes. [Usage and architecture](../../STORYCRAFT.md).

## What reads differently

- **Pottery:** Bea wants a perfect birthday surprise. She hides a dent, learns
  what starting again would cost, reveals the gift and discovers Grandpa's
  practical need. Keeping the dent, remaking a wider handle and making a bowl
  produce different final objects and costs. The drawing changes from an ideal
  to something she sets aside—or an interim birthday present.
- **Music:** Nia writes down two names before confirming two performers. Mateo
  refuses the audience, not the music. Nia can relinquish the public slot,
  perform alone, or negotiate permission to use his written rhythm with credit.
  The opening answering beat returns with a different source at the ending.
- **Greenhouse:** A flower-show plan competes with thirsty seedlings and one can
  of water. Partial watering is uncertain and requires shade. The helper has an
  afternoon trip duty and actually leaves. A wrong first allocation can leave
  permanent damage; fixing the shade does not restore the water or the leaf.

The useful pattern is not a fixed number of beats. It is a desire that encounters
resistance, an attempted response, changed possibilities, a consequential choice
and an ending that visibly answers the original situation. These stories retain
legitimate mixed outcomes instead of rewarding every helpful act with all goals.

## Archived progression

| Stage | Change / inspection |
|---|---|
| [round01](round01/report.md) | First pottery rewrite; review found missing visible premises, mismatched conceal/reveal and overlong finishing steps. |
| [round02](round02/report.md) | Three pottery outcomes; disclosure and deadline grounding; silent physical finishing plus concise transition. |
| [round03](round03/report.md) | Music's refusal, negotiation, actual permission/credit and three arrangements. |
| [round04](round04/report.md) | Greenhouse's finite water and three retained-cost branches. |
| [round05](round05/report.md) | Better grip diagnosis, authored titles, immediate opening, speech-act annotations and validation. |
| round06: [pottery](round06/pottery/report.md), [music](round06/music/report.md), [greenhouse](round06/greenhouse/report.md) | Two new seeds across all nine branches; physical helper departure and executed-action QA evidence. |
| [round07](round07/summary.json) | Sixty unconditioned generations plus three symbolic-head smoke samples; diversity and unresolved annotation audit. |
| [round08](round08/report.md) | Afternoon-trip duration, uncertainty and cautious seedlings choice address review findings. |
| round09: [pottery](round09/pottery/report.md), [music](round09/music/report.md), [greenhouse](round09/greenhouse/report.md) | Final source snapshots and nine examples; repetitive QA reduced while keeping transitive execution evidence. |

These are nine archived stages, including audits—not ten independent literary
improvements. Failures and earlier versions are retained rather than relabeled
as final output. Each experiment includes source snapshots and hashes for the
files changed in that stage; it is not a complete environment lockfile.

## Review and measurement

An independent subagent reviewed the prose and QA. The [first content review](CONTENT_REVIEW.md)
found meaningful causal and citation defects that were corrected. The
[round06 review](FINAL_REVIEW.md) preferred the revision in 16 of 18 pairs,
with two ties and no original preferences. It explicitly knew the conditions;
these were related authored branches, and six original bodies were reused.

The revised pair set contained **3,874 body words versus 1,728** (+124%). This is
not a matched-length gain, a calibrated Luna evaluation, or proof that attention
caused the improvement. Later corrections in rounds08–09 were sampled and
validated but are not retroactively credited to the round06 review scores.

The sixty-story unconditioned round07 audit reached every branch:

| World | Branch counts | Mean body words | Steps offering multiple words |
|---|---|---:|---:|
| Pottery | thumb hollow 5; remake 2; bowl 13 | 189.9 | 4.0% |
| Music | private 12; solo 3; written 5 | 202.0 | 2.8% |
| Greenhouse | share 6; flower 6; seedlings 8 | 246.0 | 2.1% |

These token-step fractions include punctuation and END transitions. Word counts
here use whitespace splitting; paired reports use the harness's word tokenizer.
The important limit is clear: most wording and most within-branch event order is
authored. Surface variation and nine endings are not open-ended story invention.

## What verification establishes

- Full grammarworlds discovery: **364 tests passed** (`tests.log`), before the
  final two additional prototype checks and small QA/content corrections.
- Final prototype suite: **10 tests passed** (`storycraft_tests.log`); the final
  combined prototype/storytelling/beat-QA/presentation run passed **41 tests**
  (`final_targeted_tests.log`). CLI generation and `git diff --check` also passed.
- All nine branches complete and replay. Annotating them preserves generated
  distributions; candidate metadata reads only earlier events and pre-event state.
- Counterfactual checks reject hot-clay delivery, unfulfilled privacy/credit
  conditions, unsupported umbrella tying, remote speech, invalid bindings and
  premature endings without mutating the world.
- Every greenhouse snapshot conserves its two half-can units. Dry plants do not
  acquire water through narrative repair, and the brown leaf remains brown.
- QA tests require actual writing, waiting, door closure, request/holding and
  surprise-setup evidence. Supporting claims can remain in the evidence graph
  without becoming extra reader questions. Exact offsets and semantic support
  are separate checks.

## Remaining work

The strongest new content is still hand-authored. It should now be factored into
reusable **decision structures**, not multiplied into thousands of nearly
identical heads. Candidate examples: conceal/reveal; request/refusal/alternative;
failed attempt/revised plan; promise/costly fulfillment; allocation under
uncertainty; and an early object returning with changed meaning.

A useful attention layer could retrieve the unresolved request, the earlier
mistake or the object carrying a promise and raise the probability of compatible
next beats. It cannot supply continuations absent from the grammar. The next
experiment should increase those grounded alternatives and compare equally
concise outputs. Transfer into a less authored world remains unproven.

Known defects/limits: `event_log_prose` in some logistical stretches,
`repeated_subject`, coarse fragment semantics rather than full lexical parses,
low surface-choice density, fixed major branch order, and no general belief or
uncertainty model. Human-readable uncertainty in one story is not such a model.
Paragraph rhythm, less repetitive dialogue attribution and tighter greenhouse
prose remain worthwhile editorial work.
