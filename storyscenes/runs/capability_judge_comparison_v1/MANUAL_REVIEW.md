# Judge comparison: interpretation and disagreement review

Both judges received the same 30 frozen outputs and 180 conversations (193 turns),
without hidden state or generator code. Both used Flex and reasoning `none`.
The user confirmed `gpt-6-luna`, the available Luna model, rather than the
unlisted `gpt-6.1-luna`. No new stories were generated or rewritten for this test.

## Main result

**These outputs are mostly event logs, not finished children's stories.** Both
judges recognize that. Their high QA scores must not be mistaken for high story
quality or permission to put these outputs into the training corpus.

| Measure | GPT-5.6 Terra | GPT-6 Luna |
| --- | ---: | ---: |
| Story overall, 0-9 | 2.667 | 3.000 |
| Story style | 1.000 | 1.667 |
| Storytelling | 2.033 | 2.433 |
| Set diversity | 0.333 | 0.667 |
| QA overall | 8.978 | 8.606 |
| QA marked usable | 180/180 | 168/180 |
| Returned-usage estimated cost | $0.120550 | $0.005525 |

Total: **$0.126075**, no unresolved requests, all 18 returned tiers Flex.
Luna cost **21.8 times less** for this workload. Both arms used 43,816 input
tokens; Terra returned 12,789 output tokens, Luna 13,337. Current prices are
recorded in `settings.json`; these are usage-based estimates, not invoices.

| Demo | Terra story | Luna story | Terra diversity | Luna diversity | Terra QA | Luna QA |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Library | 2.9 | 4.0 | 0 | 1 | 9.00 | 8.57 |
| Harbor | 3.0 | 3.0 | 0 | 0 | 9.00 | 8.28 |
| Observatory | 2.1 | 2.0 | 1 | 1 | 8.93 | 8.97 |

Story overall grades differ by at most one point on **29/30 samples**; mean
absolute difference is **0.467**. Every judged story is below the quality threshold of
six under either judge. This agreement on a low-quality, low-diversity population
does not establish that the judges agree on strong stories or subtle differences
near an acceptance threshold. There are only three judged world clusters.

## Review of all 12 QA usability disagreements

Read the 12 rejected conversations and their ten full stories against the saved
judge inputs. This is a manual coding-agent review, not an independent human
gold set. The original grades and requests remain unchanged.

**Nine cases reveal real temporal/reference underspecification.** Questions such
as "Where was the instrument case at this point?" or "What did Ari's inspection
establish?" are presented after the whole story with no preceding dialogue that
identifies a moment or which inspection. The saved answer is true of one event,
but the reader cannot uniquely recover that event from the question.

- `harbor:19283/c003`, `harbor:19283/c005`
- `harbor:19890/c005`
- `harbor:19395/c003`
- `harbor:19582/c001`, `harbor:19582/c003`
- `harbor:19051/c001`
- `library:19576/c004`, `library:19042/c002`

Luna is useful for flagging these, but its evidence often overreaches: it assumes
the question must refer to the final state/latest inspection and declares the
earlier true answer contradicted. The defensible diagnosis is an ambiguous
question, not necessarily a false world fact. Terra accepted all nine.

**Two clear false rejections:**

- `library:19396/c004`: Luna claims Nia's acceptance answered the loan offer,
  not the request. The story explicitly says: "Yes, I accept," Nia answered
  Inez's request to return the atlas to the return cabinet. The answer correctly
  identifies acceptance of that request; Luna conflated two interactions despite
  their explicit labels.
- `library:19808/c005`: "Who was responsible for returning the atlas?" is
  answered with Nia's responsibility. Luna rejects it because the loan is later
  settled. That later settlement does not erase who was responsible before it,
  and the question is explicitly past-tense. The answer is story-supported.

**One rejection has invalid contradiction evidence:**

- `library:19288/c003`: Luna says "at the reading room" contradicts "inside
  the carrying bag at the reading room." These locations are compatible, and
  the shorter statement appears verbatim in the story. The question's "at this
  point" can still be ambiguous; omitted container detail is not a contradiction.

Terra's perfect usability rate is therefore not a gold standard. Luna's lower
usability rate is not proof it is more accurate either. Both accept many raw
event-ID/time-qualified questions and assign them very high naturalness scores.
The earlier local reading already identified that as a reader-facing weakness.

## What this means for the pipeline

Luna is a promising inexpensive first-pass judge here: it reaches the same broad
story-quality verdict for around half a cent. Keep richer disagreements and
occasional second-judge/manual audits; do not make rejection/acceptance entirely
dependent on either model before testing a small labeled set of both good and
bad stories, ambiguous questions, false answers and genuine follow-up chains.

The main generator work remains story-level planning and literary realization
over the validated state model. Legal execution plus exhaustive narration does
not produce a clear motive, consequential turn or satisfying ending. The old
Luna-authored StoryScenes pipeline's 7.183/9 result is not a paired comparison
with this new direct diagnostic renderer.

Next QA work should replace hidden event IDs and unanchored "this point" with
natural, visible event descriptions; explicitly distinguish initial/final facts
and first/later inspections. Preserve the state/evidence model underneath.
Only 13 of these 180 conversations have a follow-up, so high scores here do not
establish robust multi-turn quality.

The baseline's strict geometric score is zero under either judge because every
world fails its all-seeds mechanical gate. It is not useful for ranking judges.

## Artifacts and checks

- [Generated numerical report](REPORT.md), [full comparison](comparison.json),
  [integrity audit](integrity.json), and per-model raw requests/responses/grades.
- [Frozen local baseline and sampling failures](../capability_scoring_v2/LOCAL_REVIEW.md).
- All nine request pairs are identical except the model ID. All 18 raw responses
  revalidate; saved usage reconciles to the single $5 ledger. No paid retries.
- Frozen sources, selection and baseline corpus unchanged; **385 StoryScenes
  tests pass** (seven new comparison tests). The prior 123 StoryWorlds tests
  remain the latest run for that unchanged package.
