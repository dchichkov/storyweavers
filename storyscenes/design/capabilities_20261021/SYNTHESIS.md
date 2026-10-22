# StoryScenes capability design: approval checkpoint

2026-10-21. Design round complete; implementation is not yet authorized.

## Delivered

Nine `gpt-6.1-sol` agents at high reasoning produced nine capability proposals
and 27 story outlines, one per capability in each of three settings. The session
allowed six concurrent agents, so three assignments started in a second wave.
Three workers then cross-reviewed neighboring capabilities. All workers are now
closed. The coordinator read all nine proposals and reconciled the reviews.

The corpus includes 54 proposed interventions and 81 illustrative QA pairs.
These are design examples, not executed tests, rendered stories, quality scores,
or accepted training data. No generation/judge API calls, runtime implementation,
commits or pushes were made in this round.

- [All 27 outlines](INDEX.md)
- [Reconciled decisions and explicit story corrections](DECISIONS.md)
- [Physical review](reviews/physical.md), [epistemic review](reviews/epistemic.md),
  [social review](reviews/social.md)
- [Existing-code compatibility map](COMPATIBILITY.md)
- [Proposed cross-capability integration tests](INTEGRATION_GATES.md)

Original agent proposals and messages are retained unchanged after their first
pass. DECISIONS.md is the resolution layer: its explicit corrections supersede
conflicting draft passages. This is not unanimous approval or independent blind
grading. Exact storage, compiler, and adapter choices remain implementation work.

## What the exercise established

The capabilities can be described using shared interfaces rather than nine
unrelated simulators. Reuse is plausible across genuinely different situations:
moving nested contents, a loan accepted but never collected, delayed information,
source-dependent uncertainty, and competing promises. Whether the mechanics
actually compose is still an empirical question for the implementation tests.

The messageboard was useful because it exposed concrete conflicts early:

| Conflict | Reconciled direction |
| --- | --- |
| A receive-only proxy accepts an object, then someone settles the loan later | One physical receipt; later settlement must not invent a second handover. Delay that policy until the immediate-return slice works. |
| A book is left on a bench while its borrower remains responsible | Derived physical holder, borrower, keeper and legal owner are different roles. |
| Observation, communication and mistake discovery all write beliefs | One shared belief-update operation; capabilities supply explicit decisions and evidence. |
| A failed inspection silently makes an accepted belief uncertain | Keep the prior belief unless an explicit supported disposition changes it. |
| A dated accurate report is called a mistake | Separate historical truth, present applicability and reference time. |
| Declining a request erases an earlier acceptance or promise | Typed response ownership; withdrawal, refusal, release and breach stay separate. |
| "Before eight" is assessed as "by eight" | Explicit strict/inclusive terms and matching prose/QA. |

The most important limitation remains prose/trace agreement. Structured evidence
does not certify arbitrary English. Narration and QA must share selected evidence,
and their wording still needs semantic review. We should not claim this design
alone fixes the earlier 53.7% conversation usability result.

## Recommended architecture

Keep Python and the existing composition idea. Add one opt-in capability-world
schema with typed records and operations, not nine independent runtimes or a
wholesale rewrite of legacy worlds.

The narrow shared core needs:

1. Physical parent/containment and derived location/holder queries, distinct from
   ownership and social responsibility.
2. Timed propositions, evidence and belief history, with one validated writer.
3. Identified requests, loans and explicit commitments whose lifecycles do not
   overwrite each other.
4. Bounded action specifications and domain performance receipts. Validate a
   composed physical/social transaction against one pre-state and commit once.
5. Events that retain actual actions, responses, reasons and evidence even when
   physical state is unchanged. Rejected search candidates remain non-events.
6. A narrative selection layer whose support is used by both prose and reading
   QA. Simulator-only facts are a separate debugging view.

Python can implement complex bounded calculations behind named contracts. The
engine must still see their declared reads, effects and resulting events. Avoid
arbitrary predicates smuggled through strings or independent hidden mutation.
Character intentions use accessible beliefs/goals; physical results use world
state. A promise can be broken without making the physical action illegal.

## Implementation sequence to approve

### Slice 1: Physical continuity and loans

Implement the version boundary, bounded records/events, physical parent paths,
pickup/put/travel/handoff, and simple consent/loan/return operations. Use finite
predeclared grants and terms, one object per active loan, simple containers and
single-person carrying. Separate agreement acceptance from physical receipt.

Demonstrate the same operations in all three settings, including contained-object
travel, accepted-but-uncollected equipment, and an authorized deposit. Include
reader-grounded location/loan QA and legacy replay protection from the start.
Receive-only handoffs remain outstanding; delayed settlement is explicitly
unsupported until its separate policy is implemented.

### Slice 2: Evidence, communication and revision

Add accessible observations, claims/receipts, explicit adoption and the shared
belief writer. Exercise hidden movement, delayed messages, incomplete inspection,
and repeated reports from one source. Apply D06's specific outline corrections.
No automatic omniscient updates, truth-by-inscription, or general trust model.

### Slice 3: Requests, promises and refusals

Add single-addressee requests and typed offer-response adapters, explicit
undertakings, finite checkpoints, declines and requester withdrawal. Validate
on-time performance, breach, release, and late repair. Replace commitment terms
through explicit release/new undertaking rather than rewriting history.

Across slices, grow a few integrated worlds instead of implementing 27 bespoke
programs. The outlines are design cases and regression candidates. At least one
cross-family combination should be held out from implementation demos.

## Gates before scaling

- Deterministic replay and legacy preservation; no conflicting effect writers.
- Intervention changes behavior for the expected reason, not just wording.
- The same operation definitions transfer between settings without title checks.
- World truth, character belief and reader evidence remain distinguishable.
- Failure, refusal and unresolved outcomes remain valid, not filtered away.
- Rendered stories and QA are inspected together; hiding required evidence
  removes or abstains from the corresponding comprehension answer.
- Report semantic outcomes separately from duplicates, compression and literary
  scores. Paid evaluation is a later explicit approval, not part of this round.

Recommendation: approve Slice 1 first, with the shared event/evidence interfaces
designed to accommodate the other families. Preserve the remaining outlines and
falsifiers as constraints; do not implement every proposed feature at once.
