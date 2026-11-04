# StoryScenes: Negative-Result Checkpoint

October 24, 2026. This preserves the capability, harbor, greenhouse, theater,
and literary-calibration experiments before the story-first mini-adventure
prototype. It is a research checkpoint, not a production-data release.

## What Did Not Work

The working hypothesis was that a richer executable world, composed actions,
and state-grounded prose could cheaply yield many good, distinct stories.
These experiments did not establish that result. Mechanical correctness was
achievable; convincing prose needed substantial hand-authoring, and sampling
mostly revisited small families of authored plots. High judge averages did
not reliably capture the weaknesses visible to a reader.

| Experiment | Evidence | Interpretation |
| --- | --- | --- |
| Physical, epistemic, and social capabilities | [Acceptance](design/capabilities_20261021/implementation/ACCEPTANCE.md); first paired story scores 2.67/3.00 out of 9 despite high QA scores | Valid custody, beliefs, and promises do not by themselves make a story. |
| Purpose and selective narration | [Revised paired review](runs/capability_judge_comparison_v2/MANUAL_REVIEW.md): 4.00/4.00 storytelling, 0/0 diversity, three distinct stories across thirty positions | Better causality helped, but event-log prose and fixed plots remained. |
| Hand-authored harbor, greenhouse, and theater | [Pooled findings](runs/replication_pooled_v1/FINDINGS.md): 300 stories, 147 exact texts, pooled compression ratio 3.66%; storytelling around 7.7-7.9 | Scene-level writing improved the judged prose, but did not demonstrate a large diversity multiplier. |
| Composed goals | [Local audit](runs/harbor_composition_v2_100_local/LOCAL_REVIEW.md): 576 configurations, 48 texts, all achieving the same three goals | Executable dependencies and different action orders are not necessarily different stories. |
| Persistent trade-offs and favor networks | [Trade-offs](runs/harbor_tradeoffs_v1_10_local/FINDINGS.md) and [favors](runs/harbor_favors_v2_10/FINDINGS.md): diversity 3/4 and 3/3 | More resource conflicts or longer borrowing chains did not remove repeated narrative structure. |
| Question-led recovery | [Findings](runs/harbor_questions_v11_10/FINDINGS.md): thirty-story scores 7.733/6.900; local hundred has 55 texts and 83.23% repeated-paragraph word positions | More enacted repairs still left weak turns, instructional dialogue, and insufficiently integrated subplots. |
| Literary comparison | [Diagnostic](runs/literary_calibration_v1/README.md): Puddles/Nell beat the criticized harbor examples in both orders for both judges; six of fifteen complete order checks flipped winners | The old scores were too reassuring for these examples; the replacement comparison is also uncalibrated. |

Scores above preserve the original protocols and denominators. They are not a
single comparable leaderboard. Some revisions were local-only or had incomplete
QA judging. Exact text uniqueness is not semantic diversity, and compression
ratios depend on corpus size and serialization. Neither is a standalone quality
measure. The linked reports retain the failed, partial, and unjudged cases.

## What Is Worth Keeping

- Atomic physical operations, explicit custody versus ownership, evidence-time
  beliefs, and request/promise/refusal semantics with replayable tests.
- Counterfactual checks that a changed observation, resource, or prior promise
  actually changes later possibilities.
- QA grounded in recorded state, with separate checks for what the reader can
  see. High QA scores must not substitute for prose assessment.
- Frozen sources, raw responses, budget reservations, and order-sensitivity
  diagnostics. Revisions do not retroactively acquire earlier grades.

This moves toward the project's physical-carrier/world-state model, but also
shows its limit: accurate state is a foundation for narration, not a substitute
for selecting an interesting premise, turn, and payoff. No gen6 or gen7 changes
are part of this checkpoint.

## Why Change Scale

The [mini-adventure direction](MINI_ADVENTURES.md) starts with a coherent authored
story, then models short playable scenes with global compatibility rules.
Local simulation handles a small encounter; scene selection handles travel,
optional vignettes, persistent consequences, and compatible endings.

That is the next hypothesis, not a proven cure. It still needs a second scenario,
genuinely different outcomes, human-read samples, and a measured authoring cost.
The earlier work does not prove all StoryScenes approaches impossible, nor does
the new prototype yet establish economical training-data production. No agent
compute-cost accounting was collected here, so this checkpoint makes no numeric
claim about authoring efficiency.

## Preserved Evidence

Source, tests, implementation reviews, and Markdown run reports are directly
browsable in Git. Raw runs and frozen sources are preserved in the verified
Git LFS snapshot described in [run_archives/README.md](run_archives/README.md).
Restore it before reproducing historical artifact-dependent checks. Existing
local files are not deleted, rewritten, or replaced by the archive.

The detailed [campaign log](runs/harbor_iteration_campaign/README.md),
[capability documentation](CAPABILITIES.md), and [TODO](TODO.md) retain the
chronology and earlier proposed next steps. Read those proposals as historical
research notes, not authorization to resume paid calls or broad optimization.

## Checkpoint Verification

The full local StoryScenes suite passed on October 24: **597 tests in 274 seconds**,
including the new mini-adventure tests. This is a mechanical regression result,
not a renewed prose assessment. Run it with:

```bash
./.venv/bin/python -m unittest discover -s storyscenes -p 'test_*.py'
```

The snapshot contains 10,693 files across 89 run directories and the capability
implementation evidence; all members passed checksum read-back verification.
Secret-pattern scanning found no matches in the preexisting checkpoint inputs.
No generator behavior changed and no paid API calls were made during archival.
