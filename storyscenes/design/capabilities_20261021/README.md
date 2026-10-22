# Capability design checkpoint

Date: 2026-10-21. Design round complete; engine implementation is not authorized.

Start with [the synthesis](SYNTHESIS.md) or [the 27-story index](INDEX.md).

## Scope

Nine `gpt-6.1-sol` agents with high reasoning, three shared settings each:
neighborhood library, harbor workshop, mountain observatory. The deliverables are
27 story outlines, reusable capability contracts, a durable messageboard, bounded
cross-review, and a reconciled implementation recommendation.

No production generation, API judging, runtime code edits, or git publication.
Existing repository changes and historical semantics are preserved.

## Progress

| Capability | Assignment status | Proposal |
| --- | --- | --- |
| carrying | draft and cross-review complete | proposals/carrying.md |
| lending | draft complete | proposals/lending.md |
| returning | draft complete | proposals/returning.md |
| observing | draft and cross-review complete | proposals/observing.md |
| informing | draft complete | proposals/informing.md |
| discovering_mistake | draft complete | proposals/discovering_mistake.md |
| requesting | draft complete | proposals/requesting.md |
| promising | draft and cross-review complete | proposals/promising.md |
| refusing | draft complete | proposals/refusing.md |

- [x] Shared brief and write boundaries prepared.
- [x] Nine proposals and 27 outlines completed.
- [x] Cross-review and shared decisions reconciled.
- [x] Artifact completeness and preservation checked.
- [ ] User approval of implementation scope (later checkpoint).

## Reading Order

1. [Final synthesis](SYNTHESIS.md) and [story index](INDEX.md).
2. [Shared decisions](DECISIONS.md), including explicit corrections to drafts.
3. Agent proposals and message files in the table above; messages are first-pass
   proposals, not proof of peer agreement. Decisions contain their dispositions.
4. [Physical](reviews/physical.md), [epistemic](reviews/epistemic.md) and
   [social](reviews/social.md) cross-reviews.
5. [Compatibility map](COMPATIBILITY.md), [integration gates](INTEGRATION_GATES.md)
   and the original [worker brief](BRIEF.md).

Agent IDs and actual scheduling are recorded in [dispatch.json](dispatch.json).
The live session accepted six concurrent agents; the other three assignments
started as completed workers released their slots. All nine workers are closed.
Native subagent messaging provides coordination; message files preserve the
questions and decisions beyond individual agent contexts. Concurrency is bounded
by the live session; a queued assignment is not counted as a running agent.

## Verification

[Artifact verification](verification.json) confirms nine proposal files, 27
setting-specific outlines, 27 interface messages, three reviews, all nine workers
closed, and valid local Markdown links. The 11 recorded source/test files match
their starting SHA-256 values. No runtime tests were run: this round changes only
design documents, and its acceptance tests remain proposals.
