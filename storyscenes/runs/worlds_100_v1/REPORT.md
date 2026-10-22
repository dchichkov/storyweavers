# 100 independent Storyscenes worlds — three stories per world

Authored **100 new world generators** across ten predeclared themes, from **131 total attempts**. Each completed generator produced 100 local samples: **10,000 stories** in all. Three uniformly selected positions per world yielded **300 evaluation stories**. Exactly **300 stories** received valid story grades.

Those stories produced **1,800 conversations / 5,284 QA turns**, including 1,684 complete three-pair conversations. All 1,800 graded conversations were evaluated using their English story and dialogue only, without access to hidden simulation facts.

| Measurement | Result |
| --- | ---: |
| Story overall (0–9) | **7.183** |
| Earlier two-world pilot (20 stories) | 7.75 |
| Earlier fresh sample from those same two worlds (100 stories) | 7.81 |
| Stories below 6 | 14 / 300 |
| Set diversity (three-story sets) | 2.450 |
| Conversation overall | **6.430** |
| Conversation grounding / continuity | 6.479 / 6.949 |
| Conversation naturalness / usefulness | 7.438 / 6.240 |
| Conversations marked usable by Terra | 967 / 1,800 (53.7%) |
| Unique selected story texts | 298 / 300 |

The retained 7.75 result came from only two generators. This trial tests a broader set of newly authored worlds; it is not a paired before/after engine comparison. The current authoring settings do not establish that 7.75 is maintained across this larger population. The judge rubric is unchanged, but it sees sets of three rather than ten stories, so especially the diversity scores are not directly comparable with the earlier runs. Scores and usability labels are model judgments.

The world-cluster bootstrap interval for story overall is 7.027–7.330 (95%, 5,000 resamples, fixed seed). This reflects sampling variation among accepted worlds, not judge bias, per-world quality certainty, or generalization beyond these ten themes.

| Theme | Worlds | Story overall | QA overall |
| --- | ---: | ---: | ---: |
| bakery_exchange | 10 | 6.500 | 6.894 |
| clocktower_club | 10 | 7.200 | 6.378 |
| hill_picnic | 10 | 7.267 | 6.361 |
| kite_workshop | 10 | 7.100 | 5.794 |
| library_parade | 10 | 7.433 | 7.044 |
| museum_of_small_things | 10 | 6.933 | 6.017 |
| night_garden | 10 | 7.633 | 6.956 |
| pond_concert | 10 | 7.233 | 6.800 |
| puppet_weather | 10 | 7.533 | 6.756 |
| roof_post | 10 | 7.000 | 5.300 |

| Conversation starter | Count | Overall | Marked usable |
| --- | ---: | ---: | ---: |
| change | 192 | 5.885 | 92 |
| desire | 353 | 6.575 | 194 |
| dialogue | 214 | 6.449 | 110 |
| knowledge | 291 | 7.089 | 176 |
| location | 313 | 6.387 | 177 |
| ownership | 437 | 6.135 | 218 |

## What the manual review found

The first selected story from the first accepted world in each theme was read in full, with one or two conversations spot-checked per story. Two low-QA-score cases and three low-story-score cases from distinct bakery worlds were also read against their full stories, followed by the first selected stories from the recovered museum grade and the final picnic world. Exact examples are in [manual notes](manual_notes.md); [the review worksheet](manual_samples.md) includes full conversations and additional low-story-score samples. The worksheet contains more material than the manual-read claim above.

- **Shared text leaks facts between branches.** A bakery payment paragraph refers to a honey bun after the story delivered a nut tart; multiple worlds describe still air in a windy path.
- **Repeated or premature actions.** Separate passages narrate the same handover twice. A museum certifies returned objects before borrowing them, and its ending still displays objects after return.
- **Internal state wording reaches the prose.** “Copied fact,” “nearby fact,” and explicit signal-state changes weaken otherwise warm, playful passages.
- **QA asks about facts the reader never received.** Low-scoring roof-post conversations quiz the reader about unused ribbon/basket props and then jump to unrelated invitation events. Stale custody and location information compound the mismatch.
- **Dialogue coverage and causal explanations remain incomplete.** Speech navigation can skip unindexed lines; Why answers often state old guards rather than the relevant motive or cause.

Deterministic replay/evidence checks found **0 defects**, despite the lower semantic QA scores. This is evidence that trace grounding alone does not establish story-only answerability. The chat exports remain review artifacts, not automatically accepted training data. No engine, prose, QA rule, or accepted grade was revised to improve this batch’s score.

## Cost and service

| Phase | Returned calls | Input tokens | Output tokens | Estimated USD |
| --- | ---: | ---: | ---: | ---: |
| authoring | 427 | 3,128,766 | 876,269 | 0.838638 |
| story | 100 | 243,278 | 40,784 | 0.487982 |
| qa | 100 | 420,949 | 150,100 | 1.321549 |
| **Total** | **627** | **3,792,993** | **1,067,153** | **2.648169** |

All returned tiers: `{"flex": 627}`. Cache reads: **0 tokens**; cache writes: **0 tokens**. Sampling and QA generation were offline and added **$0 API cost**. Luna authored and repaired worlds; Terra only graded stories/conversations, without generator scripts.

There are **4 saved requests without returned usage**. Their original conservative reservations remain in the ledger: **$0.170773**. The whole $15 campaign, including prior work and all reservations, now commits **$5.127206**. These estimates are based on returned usage and list prices, not invoice reconciliation; missing responses are not assumed free.

Flex rates per million ordinary input/cache-read/cache-write/output tokens: Luna $0.10/$0.01/$0.125/$0.60; Terra $1.00/$0.10/$1.25/$6.00. [Official pricing](https://developers.openai.com/api/docs/pricing) and [Flex documentation](https://developers.openai.com/api/docs/guides/flex-processing); pricing checked 2026-09-07.

Including failed attempts, returned authoring cost is **$0.00839 per mechanically accepted world**. A straight-line 20,000-world authoring estimate is **$167.73**, before evaluation and any literary rejection. With this run’s grading, returned cost is **$0.02648 per world**. These projections exclude unresolved charges, human review, hosting/storage and changes in yield or pricing. Mechanical acceptance is not acceptance at the user’s 7.75 quality target.

## Reproducibility and recovery

- 31 failed world attempts remain alongside completed worlds; no grade-based replacements.
- Seed manifest was written before paid dispatch. First ten accepted generators per theme; three uniform positions from each 100-story pool, seed 777, without replacement or deduplication.
- Current cache-only authoring, original compact contract, medium mechanics reasoning and low prose reasoning. Per-world authoring dispatch cap $0.15; shared campaign cap $15; SDK automatic retries disabled.
- Scheduler handoff drained in-flight calls, reused saved completed responses, retained all uncertain reservations and quarantined failed/capped drafts before selecting new predeclared seeds. Engine and authoring snapshots stayed fixed. See [continuation audit](continuation_audit.json).
- Any explicit 429 judge recovery uses the original payload, preserves the rejected request/reservation, and replaces no valid grade. Recovery responses and provenance remain beside the original artifacts.
- **123 tests pass**, including recovery, budgeting, selection, dialogue, conversation and legacy authoring checks.
- All 100 world definitions are distinct; generator, simulation and world-file hashes match their saved records. Every world has its 100-story pool. Every selected story and conversation was graded exactly once, with exactly three selected story IDs per world.

[Evaluation summary](evaluation_summary.json) · [Analysis and integrity checks](analysis.json) · [All selected stories and traces](selected_samples.jsonl) · [Raw assessments](assessments.jsonl) · [Story ratings](story_ratings.jsonl) · [Conversation ratings](conversation_ratings.jsonl) · [Test log](tests.txt).
