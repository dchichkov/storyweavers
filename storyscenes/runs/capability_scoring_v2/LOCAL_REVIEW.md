# Fresh capability-world baseline: local review

Paid follow-up completed after explicit authorization: the
[paired Terra/Luna review](../capability_judge_comparison_v1/MANUAL_REVIEW.md)
scores these same selected outputs at **2.667/9 and 3.000/9** story quality,
respectively. Total estimated judging cost: **$0.126075**. The original local
observations and pre-authorization status below are retained as historical notes.

2026-10-22. Four fixed CLI demo specifications, 1,000 solver seeds per demo
(19000-19999), six workers, 6,000 search nodes, two CPU seconds per search,
and a parent-enforced six-second wall limit per child including startup.
Sources and world definitions are frozen alongside this report. The generator,
renderer, QA rules and judge rubrics were not tuned during this measurement.

This tests the current bounded author-side solver and diagnostic renderer. It
does not test new LLM-authored worlds, all 50 conformance scenarios, randomized
builder parameters, or autonomous character policies. Successful paths render
deterministically; timeout outcomes can depend on hardware/load. The exact
observed attempt set is retained rather than assumed reproducible from seeds
alone. Pinned-path introductions and endings are deliberately not grafted onto
fresh paths that might not support them.

## Sampling and compression

| Demo | Returned / 1,000 | Exact unique texts | Distinct action multisets | Mean words | Unique-text LZMA retention |
| --- | ---: | ---: | ---: | ---: | ---: |
| Library | 954 | 939 | 16 | 442.8 | 4.82% |
| Harbor | 235 | 51 | 1 | 269.0 | 4.82% |
| Observatory | 783 | 633 | 12 | 155.3 | 4.36% |
| Competing promises | 1 | 1 | 1 | 405.0 | Not informative with one sample |
| Total | **1,973 / 4,000 (49.3%)** | **1,624** | Not a plot count | | **5.07% pooled** |

All 2,027 failures were CPU timeouts, not proven impossible scenarios or failed
replays. The competing-promises demo therefore has too few returned positions
for the unchanged set-diversity judge. It is ungraded, not assigned zero quality.
Every returned position passed exact replay during preparation. A single XZ
archive retains all 1,973 returned story texts, including 349 exact duplicates.

- Story-only JSONL: **3,609,197 bytes (3.44 MiB)**.
- Single XZ archive: **43,412 bytes (42.4 KiB), 1.20% of raw bytes**.
- Separate normalized diversity measure on 1,624 unique texts: **42,830 pooled
  raw-LZMA2 bytes / 844,967 independently compressed bytes = 5.07% retention**.
- The raw XZ ratio and normalized retention are different measurements. The
  latter uses the existing 64 MiB dictionary/shuffle protocol. Neither makes
  exact uniqueness or action-order changes evidence of meaningful plot variety.

## Manual reading

Read the first two selected positions from each judgeable demo in full, including
all 36 selected conversations: `library:19245`, `library:19478`, `harbor:19248`,
`harbor:19493`, `observatory:19287`, `observatory:19564`. Additional exploratory
reading included the first returned story per demo except competing promises.
These notes were written before receiving paid grades. Full selected texts and
conversations are in `judge_samples.json`.

1. **Event-log prose dominates.** The library repeatedly restates location,
   carrier, owner, responsibility and outstanding-loan status after each move.
   A real custody distinction is preserved, but the rendered result resembles
   a transaction transcript. The reason for needing the atlas outside is absent.
2. **Action legality is not narrative motivation.** In `observatory:19287`, Noor
   hands over the chart before promising to hand it over, then is marked in
   breach. In `observatory:19564`, the handoff even precedes the chart request.
   Receipt matching correctly does not count pre-promise performance. What is
   missing is a story-level reason for this strange new undertaking, not simply
   an accounting rule declaring that any earlier handoff fulfills it.
3. **The harbor has temporal substance but little plot variation.** Both read
   samples distinguish an old report from a current inspection. Their material
   difference is the position of Cy's belief adoption relative to Ari's actions.
   All 235 returned stories use the same action multiset. Explicit numeric times
   and repeated recorded-basis sentences make the prose technical.
4. **Dialogue exists, but is administrative.** Requests, readiness, consent,
   promises and refusals are direct speech. They do not yet provide varied voices,
   emotionally meaningful exchanges or a strong premise/turn/ending.
5. **QA supports auditing better than natural conversation.** For example,
   library questions expose `Event relift:1; reference time 0`, but those event
   identifiers are not part of the reader's story. Repeated questions about
   physical holders and locations need natural event descriptions and selective
   focus. Harbor belief-basis questions can repeat the same vague answer about
   the gauge; referent-free "this request" questions can be ambiguous.

No numerical human quality ratings are substituted for the API judge. The
earlier [100-world trial](../worlds_100_v1/REPORT.md) scored 7.183/9 story quality
and 6.430/9 conversation quality, but used newly authored worlds and a different
conversation mix. Any numerical comparison is descriptive, not a paired test.

## Evaluation and provenance

The frozen selection contains **30 stories, 180 conversations and 193 turns**:
ten returned positions from each of three demos, duplicates retained, selection
seed 777. One selected text is an exact duplicate. QA uses six supported anchors
per story; just 13 conversations have a same-event why follow-up. This is not
equivalent to the older mostly-three-turn conversation benchmark, nor a test of
arbitrary unsupported queries.

Nine prepared requests use the unchanged Terra/Flex story-set and conversation
rubrics. Hidden states, traces and source code are excluded from judge payloads.
The user authorized a $5 cap. The first dispatch was blocked by the approval
reviewer before execution, pending explicit authorization to send these stories
and conversations to OpenAI. **No scoring API calls had been sent when this
local review was written.** Later paid results, if authorized, belong in
`REPORT.md`, raw request/response files and the persistent `budget.json` ledger.

`offline_audit.json` verifies all 4,000 unique planned IDs, all 1,973 trace hashes,
rendered texts and QA statement references, and the single-archive contents.
All 30 selected paths were replayed again. This verifies provenance, not general
English entailment. Tests: **378 StoryScenes + 123 StoryWorlds pass**.

The interrupted [v1 sampler diagnostic](../capability_scoring_v1/INTERRUPTED.md)
retains 2,663 positions separately. None were reused here or sent for judging.

## Next development targets

1. Improve bounded planning: avoid spending most search on irrelevant orderings
   and dead ends, while preserving genuine speech, evidence and temporal meaning.
2. Add story-level purposes, consequential alternatives and prerequisite-aware
   beats over the atomic operations. Preserve the legal state model as validator;
   do not mistake arbitrary legal permutations for interesting narratives.
3. Realize a selective, state-supported beginning, turn and ending. Turn custody
   bookkeeping into prose only when it matters; preserve evidence for selected QA.
4. Replace raw event IDs in reader-facing questions with natural descriptions,
   reduce redundant anchors, and test richer follow-up conversations separately.
5. Re-run matched frozen worlds/seeds and unchanged rubrics. Measure search
   yield, literary quality, semantic diversity and compression separately before
   treating this prototype as a training-data generator.
