# StoryScenes capability design round

Date: 2026-10-21. Status: design only; implementation requires a new user approval.
Requested worker model: `gpt-6.1-sol`, high reasoning.

## Objective and boundaries

The user wants an extensible offline world simulator/expert system, with prose
and QA derived from its state and events. This round produces nine reusable
capability proposals and 27 story outlines, NOT 27 independent generators.
Success means the same mechanics explain three distinct settings and compose
with neighboring capabilities without setting-specific repair rules.

You are one of nine agents working in parallel. The coordinator owns the shared
contract and integration. Do not launch additional agents, make API requests,
modify runtime code, run paid judges, install dependencies, or commit/push.
There are substantial pre-existing changes in this repository; leave them alone.
Use apply_patch for your own new design documents only. No runtime LLM calls.

## Read first

Repository-relative paths (repository: `/Users/dmitry/storyweavers`):

- `AGENTS.md` and the north-star sketch in `story.py`.
- `storyscenes/README.md`, `COMPACT.md`, `CONVERSATIONAL_QA.md`.
- `storyscenes/runtime.py`, `algebra.py`, and `test_algebra.py` for existing semantics.
- Relevant parts of `storyscenes/conversation.py`, `dialogue.py`, and `prose.py`.
- `storyscenes/runs/worlds_100_v1/REPORT.md` and `storyscenes/TODO.md` for defects.

Read selectively after understanding the existing architecture; do not scan raw
batch corpora. Cite repository files/functions when claiming existing behavior.

## Existing architecture and evidence

Definitions compose candidate actions, not preordered scripts. Actions have guards
and atomic effects; a seeded bounded search finds a path to an authored goal.
Persistent state and before/after events supply evidence for prose and QA.
`Observe` copies a fact into a belief slot. `Tell` copies a speaker's stored belief.
Existing `Transfer` changes `.owner`; `Lend`/`Return` reuse that slot plus
`.loaned_by`. `Move` updates an object's location, not the carrier's location.
These are historical semantics, not a sufficient ontology to preserve in the new
design. Never propose silently changing old world interpretation.

Prose cards are selected using facts, but their English may assert more than those
facts justify. Trace dependency is not necessarily character motivation. The
100-world trial graded 300 stories at 7.183/9; only 967/1800 conversations were
judged usable despite zero deterministic evidence-check defects. Common problems:
offstage questions, stale location/custody, repeated or premature actions, branch
facts leaking into text, unindexed dialogue, and weak causal explanations.

## Provisional shared distinctions

Use these as design constraints, not an imposed final schema. Flag improvements.

- Separate ownership, possession/custody, and physical location.
- Separate world truth, each character's beliefs, and reader-visible evidence.
- Separate requests, acceptance, promises, and actual performance.
- Preconditions enable actions; motives explain choices. Do not equate them.
- Physical invariants differ from preferences and social obligations. A refusal,
  broken promise, false belief, or failed attempt must be representable.
- Unknown is not false. A communicated claim need not be true or accepted.
- Concepts/feelings must be embedded in carriers and affect choices/state, not
  float as bare abstract events. Do not impose a universal moral-success goal.
- Python is the host; meaningful reads, effects, events, and explanations should
  remain inspectable. Prefer a narrow reusable contract to a universal framework.
- Preserve old data/runtime through an explicit opt-in/versioned future extension.

## Team and write ownership

Each agent owns only `proposals/<capability>.md` and
`messages/<capability>.md` below this directory. All other files are read-only.

| Capability | Responsibility | Primary peers |
| --- | --- | --- |
| carrying | Taking, carrying, movement, putting down, location | lending, returning |
| lending | Permission, temporary custody, lender, obligation | carrying, returning |
| returning | Correct recipient, loan discharge, failed return | carrying, lending |
| observing | Evidence access, noticing, belief acquisition | informing, discovering_mistake |
| informing | Claims, sources, delivery and belief acceptance | observing, discovering_mistake |
| discovering_mistake | Conflicting evidence, belief revision, corrective action | observing, informing |
| requesting | Request content, pending state, acceptance vs completion | promising, refusing |
| promising | Commitments, fulfillment, breach, conflicts | requesting, refusing |
| refusing | Declining with grounded reasons and consequences | requesting, promising |

## Three shared settings

Every agent outlines one story in each setting. Settings are shared to make later
composition possible. Characters and concrete plots are your choice.

1. Neighborhood library: books, reservations, shared equipment, opening times.
2. Harbor workshop: tools, deliveries, repairs, weather, departure deadlines.
3. Mountain observatory: instruments, observations, messages, limited supplies.

These must be three distinct causal situations, not noun-swapped versions of the
same story. The focal capability must drive a consequential turn. Use neighbors
as dependencies rather than reimplementing their responsibilities. Aim for warm,
readable stories with meaningful dialogue, but not compulsory moral lessons.

## Required proposal structure

Keep the complete proposal approximately 1800-2400 words. Be concrete, not verbose.

1. **Scope and existing behavior:** what is reused, missing, or incompatible.
2. **Reusable contract:** participants, state read/written, legal prerequisites,
   atomic effects, event/evidence fields, failure cases, and explicit non-goals.
   Distinguish proposed semantics from behavior already implemented.
3. **Three story outlines**, with exact headings:
   `## Story 1: Library - <title>`
   `## Story 2: Harbor - <title>`
   `## Story 3: Observatory - <title>`
   Each must contain:
   - Premise, character goals, complication, consequential choice, ending image.
   - Initial world facts, beliefs, and the evidence the reader receives.
   - A 5-8 beat event outline with relevant prerequisites, changes, and motives.
   - A short exchange (2-6 lines) whose speech actually does something.
   - Two concrete interventions and their expected changed outcomes.
   - Three QA pairs, including a causal question and a linked follow-up. State
     the evidence required in the rendered story. Do not rely on hidden facts.
4. **Cross-capability composition:** at least one interaction outside your peer
   group; identify who owns each effect and what interface you need.
5. **Acceptance tests:** positive, negative, intervention, and transfer tests;
   distinguish semantic variety from renamed props or cosmetic wording.
6. **Open decisions:** smallest implementable slice versus deferred extensions.

An outline's declared outcome is a design example, not a hardwired execution
route. Do not claim the new contracts are implemented or have passed tests.

## Messageboard protocol

Create your message file early with up to three important interface proposals or
questions. Each entry has an ID (`<capability>-01`), recipient, issue, proposed
resolution, affected stories/contracts, and status (`proposed`, `answered`, or
`unresolved`). You may read other agents' files if visible, but edit only yours.
If a peer file is not yet available, record the dependency and continue; do not
poll or block. The coordinator relays messages and records agreed decisions.
No automatic shared filesystem/message delivery assumptions are required.

There will be a bounded cross-review after the first proposals. Do not wait for
it: finish your first assignment and report paths, story titles, and unresolved
interfaces to the coordinator. Final decision records will live in DECISIONS.md;
the coordinator alone edits that file and the campaign README/compatibility map.
