# 100 fresh stories with conversational QA

Generated and evaluated **100 story samples**, 50 each from the retained
library-parade and pond-concert worlds, using fresh seeds 19000–19049. These
are new samples from two existing generators, **not 100 newly authored worlds**.
Every sample has six three-turn conversations: **600 conversations / 1,800 QA
pairs**. All 100 stories and all 600 conversations received semantic ratings.

## Quality

| Measurement | Result |
| --- | ---: |
| Story overall, unchanged 0–9 rubric | **7.81 / 9** |
| Historical two-world pilot | 7.75 / 9 |
| Library-parade story score, 50 stories | 7.88 |
| Pond-concert story score, 50 stories | 7.74 |
| Story ratings | 81 rated 8; 19 rated 7; none below 6 |
| Set diversity | 3.00 / 9 |
| Distinct story texts | 85 / 100 (35 library; 50 pond) |
| Conversation overall | **6.81 / 9** |
| Conversation grounding / continuity | 6.85 / 7.07 |
| Conversation naturalness / usefulness | 7.94 / 6.64 |
| Dialogue-starting conversations, 100 | **7.13 / 9** |
| Conversations marked usable by Terra | 314 / 600, **52.3%** |
| Deterministic evidence/replay defects | 0 |

The story result is close to the retained benchmark. It is a new seed sample
and a stochastic judge run, not proof of a 0.06 improvement or of quality across
new worlds. Duplicates were retained; the low diversity rating remains visible.

Conversation scores use a new, separate protocol: grounding, continuity,
naturalness, usefulness and overall on 0–9, plus strict story-only usability.
The judge saw the story and conversation, not hidden simulation facts. The
314 usability labels are model judgments, not certified training acceptance:
manual review found both real defects and judge false positives.

| Conversation starter | Count | Overall | Marked usable |
| --- | ---: | ---: | ---: |
| Knowledge | 100 | 7.26 | 57 |
| Dialogue | 100 | 7.13 | 62 |
| State change | 100 | 7.10 | 64 |
| Desire | 100 | 6.77 | 41 |
| Location | 100 | 6.59 | 50 |
| Ownership | 100 | 6.03 | 40 |

Scores apply to complete conversations grouped by their first question, not
isolated question kinds. Library conversations average 7.18; pond conversations
6.44. Exact per-sample ratings and notes are in [assessments.jsonl](assessments.jsonl).

## What needs work

Manual reading covered six preselected complete samples and their conversations
(indices 0, 17, 33, 50, 67, 99), followed by spot checks of judge findings.

1. **Stale physical locations.** In `library_parade:19000/c000`, QA says the book
   remains at the library after Nell receives it in the square. The trace passes
   replay checks but disagrees with the prose. Carried objects and actors need
   consistent state updates; strict trace grounding alone does not solve this.
2. **Hidden facts presented as story evidence.** In `library_parade:19017/c000`,
   QA locates Ada at the library while she learns Nell's wish, although the
   narrated passage does not establish that location. Similar answers add Ben's
   garden location even when the story only states his wish to help.
3. **Skipped dialogue.** In `pond_concert:19049/c000`, “What was said next?” jumps
   from Ada's quiet observation to her report to Frog, skipping intervening Frog
   dialogue. The importer indexes only 225 of 741 raw quote spans (30.4%). This
   is coverage, not an accuracy measure; the interface needs to acknowledge gaps
   or consume more complete authored speech records.
4. **Weak explanations.** Some “Why?” answers describe an old move's mechanical
   preconditions instead of explaining the current possession/location or the
   character's purpose. For example, `pond_concert:19000/c004` discusses Ada
   having the invitation in the garden after asking about Mira's invitation at
   the porch. The facts are individually recorded but the explanation is poor.
5. **Speech/event alignment.** In `pond_concert:19017/c004`, a quotation in Frog's
   observation is connected to his following Tell action and labeled as addressed
   to Ada. Exact span matching does not prove a listener or event assignment.

**Judge caveat:** `pond_concert:19027/c002` was marked contradictory because the
invitation is in Mira's hands “rather than at the porch.” The story explicitly
says Mira stayed on the porch. These locations are compatible, so that rejection
is a false positive. The same issue affects another conversation in that sample.
Some prior-knowledge findings are also tagged as invented motives, which is an
imprecise classification. Raw scores and labels have not been edited to remove
these findings; they should guide review, not act as unquestioned acceptance.

The judge tagged 154 not-in-story issues, 78 misleading sequences, 72 invented
motives, 64 contradictions, 27 wrong-time issues, 12 lost-focus issues, four
wrong-quote issues and two wrong-listener issues. Counts are flags, not unique
failed conversations; classifications include the caveats above.

## Costs and caching

| Phase | API calls | Input tokens | Output tokens | Estimated USD |
| --- | ---: | ---: | ---: | ---: |
| Offline story + QA generation | 0 | 0 | 0 | **0** |
| Story grading | 10 | 59,824 | 9,468 | 0.116632 |
| Conversation grading | 20 | 133,045 | 49,084 | 0.427549 |
| Total | **30** | **192,869** | **58,552** | **0.544181** |

All **30 returned responses report Flex**. There were **zero cache reads and
zero cache writes**. Requests preserve the story rubric and disable one-use
cache writes; the conversation evaluator uses the same transport policy. No
automatic retry, Standard fallback, or stronger-model authoring was used.

Prices were checked against current official documentation: Terra Flex is
$1/M ordinary input, $0.10/M cache reads, $1.25/M cache writes and $6/M output.
Luna Flex remains $0.10/$0.01/$0.125/$0.60 respectively, although this sample
run made no Luna calls. [OpenAI pricing](https://developers.openai.com/api/docs/pricing),
[Flex processing](https://developers.openai.com/api/docs/guides/flex-processing).
The same uncached token volumes at Standard rates would cost $1.088362.
These are returned-usage estimates, not invoice reconciliation.

Generation took **3.80 seconds** locally; CPU time is not priced here. The paid
evaluation costs about **$0.00544 per story with its six conversations**, or
$5.44 per 1,000 such fully evaluated samples at this token mix. Further offline
samples add no API cost. Upfront world authoring costs were incurred earlier and
were **not remeasured** in this trial; do not extrapolate these figures to 20,000
new world generators.

The current trial has no unknown outcomes or unresolved reservations. The
existing $15 campaign ledger now commits **$2.308264**, including earlier work
and historical reservations.

## Verification and artifacts

- **117 tests pass**, including new judge-schema, complete-ID coverage, unchanged
  story-rubric, hidden-trace exclusion and persistent-budget checks.
- All 100 frozen-generator story strings were identical after current prose
  indexing; original traces were retained. Runtime generation used no API key.
- Exactly 100 distinct sample IDs were graded once in the story protocol and
  once in the conversation protocol; exactly 600 conversation IDs were covered.
- One completed judge response repeated one rating object identically, producing
  31 rather than 30 entries. Its original raw response is preserved. Removing
  that one byte-equivalent duplicate made the original strict validator pass,
  with no new API call and no rating change. See
  [recovery provenance](qa_quality/batch_05.recovery.json). The initial log records
  that schema failure; the final summary includes the validated normalization.
- Authored worlds, prose, QA rules and responses were not tuned after seeing
  this trial's grades. The limitations above remain outstanding.

[Final evaluation summary](evaluation_summary.json) ·
[Mechanical checks](mechanical_checks.json) ·
[World/kind analysis](analysis.json) ·
[Source stories and conversations](samples.jsonl) ·
[Six manually read samples](manual_samples.md) ·
[Review-only chat export](chat_review.jsonl) ·
[Test output](tests.txt).
