# Dialogue QA extension

Storyscenes now supports questions about quoted words, speaker, addressee,
speech sequence, explicit replies, and why a character spoke. This is offline
execution over attributed speech records and world facts; it adds no API calls
or required model output tokens.

The physical speaker is the carrier. Speech records attach exact text spans to
that carrier and a scene; reasons reference the speaker's embedded belief/goal
prerequisites. The assertion and the world's actual state remain separate.
This moves toward the memeplex model without using prose to invent world state.

## Behavior and evidence

- `What did Ada tell Frog?` retrieves the actual words “Mira wants quiet today.”
  `Who were they talking to?` identifies Frog. `Why did she say that?` gives the
  recorded speaker/listener knowledge context, explicitly noting that the story
  does not state a more specific motive. [Actual CLI example](example.txt).
- Optional annotations specify speaker/listener, quote indices, reply links,
  factual claims and reason keys. Reasons must be the speaker's goal or belief
  and a scene prerequisite. Claims can be checked before or after their event.
  In the changed-box fixture, Ada passes on an outdated belief: the answer
  explains her belief, identifies her information source, then correctly says
  the box was open. It does not label her a liar. Ben's explicitly linked reply
  becomes the next speech focus. [Annotated fixture example](annotated_example.txt).
- Current prose rendering indexes named speech before bridge concatenation,
  retaining event identity and exact quote offsets. Optional author annotations
  preserve richer reasons and replies through the same path. Frozen stories can
  be read by the same conservative importer at QA time.
- Quotes are evidence about what was said. They never update the physical
  simulation or automatically establish that their assertions are true.

## Validation

**113 tests pass**, including 20 dialogue tests. Six dialogue conversations pin
wording/focus/evidence, while the six original trace-only pins remain intact.
Tests cover exact spans, interrupted speech, unknown speakers, ambiguous repeats,
named question aliases, explicit replies, unknown motives, false beliefs,
before/after claims, goal-based explanations, future/invalid evidence, quote
tampering, unchanged story input, and renderer bridge preservation.

Replayed the current renderer against all **36 saved stories** from the two
compact benchmark worlds and ten earlier worlds. All 36 story strings and world
traces were exactly unchanged. No new story quality score is claimed; the
original 7.75 benchmark's prose is preserved.

| Check | Result |
| --- | ---: |
| Broad saved-story sample | 200 conversations; 495 supported answers |
| Three-pair conversations | 159 |
| Broad sample evidence/replay defects | 0 |
| Indexed speech records | 22, across 14 of the 36 stories |
| Current renderer's precise speech/event links | 18 / 22 |
| Targeted speech exercises | 22 four-question conversations |
| Targeted supported answers / explicit abstentions | 42 / 46 |
| Targeted evidence/replay defects | 0 |
| Added API requests / cost | 0 / $0 |

The targeted exercise deliberately asks reason, listener and next-speech
questions even when that information is missing. It includes six supported
Tell-context answers; explicit motives, claims and reply annotations are
exercised by the behavioral fixtures, since the frozen catalogs lack them.
Only 31% of supported targeted answers have two substantive sentences: many
are short direct quotations, and the old texts have little annotated context.
The broad sample is 66.5%; the compact six-story smoke remains above 70%.
These are coverage and deterministic correctness checks, not a literary judge.

## Manual review and remaining limits

Reviewed all distinct imported quote/speaker combinations. A puppet-weather
passage initially attached Bo's “My grand finale begins with a parade!” to
Mara's next line. The importer now indexes only Mara's explicitly introduced
“A parade needs feet.” in that construction; a regression test uses the original
saved passage. Unsupported interrupted vocatives such as “Tomas,” are omitted
instead of becoming misleading one-word answers.

Most older dialogue uses pronouns or adjacent actions rather than explicit
named speech tags. Those lines remain unindexed unless annotated. This is a
material coverage limitation: the next *indexed* speech may skip other dialogue,
and an unknown reply is not evidence that nobody replied. No motive is inferred
from proximity, and a Tell prerequisite is labeled context rather than treated
as a proven psychological reason. Numbered speech questions count indexed
records, not every spoken line.

Authored reason/claim/reply metadata is structurally checked, but its semantic
agreement with the wording still needs review. Existing prose/trace mismatches
also remain. Draft chat exports keep their story-alignment-review status.

## Reproduce

```bash
.venv/bin/python -m unittest discover -s storyscenes -p 'test_*.py'
.venv/bin/python storyscenes/qa_trial.py \
  --run storyscenes/runs/compact_algebra_v2 \
  --run storyscenes/runs/improvement_luna_v6 \
  --out /tmp/storyscenes-dialogue-trial
.venv/bin/python storyscenes/improvements/dialogue_qa_v1/replay_renderer.py
```

[Usage and annotation schema](../../CONVERSATIONAL_QA.md) ·
[Saved-story checks](checks.json) · [Renderer replay checks](renderer_replay_checks.json) ·
[Targeted story/dialogue review](targeted_dialogue.md) · [Test output](tests.txt).
