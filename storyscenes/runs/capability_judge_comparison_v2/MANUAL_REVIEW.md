# Revised capability stories: judged, still not finished prose

2026-10-22. Source: `../capability_prose_review_v4/fresh_seeds.jsonl`.
These are the current purposeful plots, not the old-path rendering ablation.
All 30 saved positions were replayed before dispatch. The same 30 seed IDs as
the historical selection remain, but they now collapse to three visible texts.
Ten positions per world were retained without deduplication for set judging.
Both prose and plots changed, so before/after differences do not isolate either.

## Scores

All scores are 0-9. Same story-set and conversation rubrics, Flex, reasoning
`none`, `store=false`; only model differs between paired requests. Judges see
visible stories and questions/answers, not scripts, traces or evidence metadata.

| Measurement | Terra before | Terra revised | Luna before | Luna revised |
| --- | ---: | ---: | ---: | ---: |
| Story overall | 2.667 | 4.000 | 3.000 | 4.000 |
| Coherence | 5.600 | 6.667 | 5.167 | 7.667 |
| Style | 1.000 | 2.000 | 1.667 | 2.667 |
| Storytelling | 2.033 | 3.333 | 2.433 | 3.333 |
| Set diversity | 0.333 | 0.000 | 0.667 | 0.000 |
| QA overall | 8.978 | 9.000* | 8.606 | 8.889 |
| QA marked usable | 180/180 | 150/150* | 168/180 | 179/180 |

Every revised story position received **4/9 from both judges**, across library,
harbor and observatory. All 60 story grades are present; all remain below 6.
These are three distinct stories, not 30 independent literary observations.

*Terra QA is incomplete: one five-story request was rejected twice by Flex,
leaving 30 of the planned 180 conversations ungraded. Its 9.0 is conditional on
the 150 returned grades, not a score for all 180. Luna graded all 180. The new
selection has 198 turns, including 18 follow-ups, versus 193/13 historically;
this is not the same QA content before and after. No missing scores are imputed.

## Reading the stories and the judges together

I read all three distinct revised texts and both judges' comments for each.
The judges independently agree on technical, repetitive event-log narration.
The causal chains are clearer, but coherence is not the same as storytelling.

- **Library:** the atlas has an actual use now. Nevertheless, repeated loan
  acknowledgments and return administration dominate the reading. Finding the
  garden changes a report but has no further consequence for a character's goal.
  Repeated names, long object labels and the technical explanation of settlement
  are plainly visible in the prose, not just judge preferences.
- **Harbor:** a changed location produces corrected information and a successful
  retrieval. This is the strongest reusable story mechanism of the three. But
  repeated timestamp disclaimers explain the epistemology to the reader instead
  of letting a character encounter the consequences of stale information.
  The final holding statement confirms success without much narrative payoff.
- **Observatory:** delaying a handoff until a reading makes lateness explicable.
  Neither the missed deadline nor the final refusal has a demonstrated cost to
  Vale. A fulfilled/breached flag alone is not a dramatic consequence. The judge
  specifically notes that the ending does not show what the missed promise means.

The fixed plots' collapse to one text each is real. Removing irrelevant reorderings
improved clarity while exposing the lack of substantive sampled alternatives.
Synonyms would raise exact uniqueness without fixing this.

## QA disagreement review

All three Luna defect annotations were checked against their supplied stories
and conversations. Grades are preserved, not edited to match this review.

- `library:19288/c000` is a clear false rejection. Paragraph 10 says Nia picked
  up the bag **from the courtyard**, exactly as the supplied answer says. Luna
  incorrectly claims the answer describes paragraph 7's earlier pickup.
- `observatory:19564/c005` and `observatory:19044/c005` expose a genuine awkward
  follow-up: after asking what time the clock reached, "Why?" receives Noor's
  reason for waiting for a reading. That is not a cause of time passing. Same-event
  provenance alone does not establish a sensible causal follow-up. Luna flags
  both as unhelpful but still marks them usable. Terra grades both exchanges 9/9
  without defects, despite the mismatch between waiting and time passing.

The high QA scores measure easy supported questions about controlled text.
They neither certify literary quality nor establish that either judge is gold.
Record `wrong_causal_followup` for a later QA fix; do not mutate this scored batch.

## Cost, availability and preservation

- 18 logical requests planned. First dispatch: 15 completed, three explicit
  `429 flex_unavailable` rejections. No SDK retries or standard-tier fallback.
- Each rejection was manually retried once, with identical payloads and concurrency
  one: two completed, one was rejected again. **21 dispatches, 17 completed, four
  explicit availability rejections.** No successful grade was replaced.
- Original rejected inputs/requests/results and the first partial report/ledger
  are preserved in `rejected_flex_attempt_1/`. The latest failure remains in the
  primary results. The runner does not automatically retry it on resume.
- Returned-usage estimate: **$0.10625885**, comprising Terra **$0.101187** and
  Luna **$0.00507185**. All completed responses report the requested model and Flex.
- The ledger conservatively retains **$0.501287** for four rejected dispatches,
  so its committed upper bound is **$0.60754585** against this pass's $1 cap.
  These are saved reservations, not additional observed charges. Official
  [Flex documentation](https://developers.openai.com/api/docs/guides/flex-processing)
  says resource-unavailable 429s are not charged; no invoice reconciliation was done.
- Including the prior campaign, returned-usage spend is **$0.23233390** and the
  conservative combined commitment is **$0.73362090**, below the shared $5 cap.
- `comparison.json` counts the 18 current logical result slots; `budget.json`
  retains all 21 dispatch reservations. Its four unresolved entries are these
  explicit rejections, not four missing response timeouts.

Sources, selected inputs, raw requests/responses and all grades are saved.
The new saved-review runner refuses changed sources, altered replay/story/QA,
missing seed positions, changed frozen settings and excess combined spending.
**410 StoryScenes tests pass.** No runtime or historical corpus was changed in
this judging pass; StoryWorlds tests were not rerun.

## Decision

Do not export these repetitions as a training corpus. Do not add more simulation
capabilities just to raise literary quality. Test a scene-level realization layer
on the existing traces, then improve the plots independently. The proposed
experiment and acceptance gates are in [CAPABILITIES.md](../../CAPABILITIES.md#next-prose-experiment).
The older StoryScenes catalog produced much stronger prose but weaker story-only
QA; the useful direction is to combine its scene-level writing with this runtime's
evidence discipline, not assume either half already solves both.
