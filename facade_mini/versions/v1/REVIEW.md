# Prototype review — October 24, 2026

This is a self-review by the implementing agent, not an independent literary
evaluation. The delivery reproduces a small set of architectural ideas in an
original drama; it does not reproduce the full historical systems or measure
their authoring economics.

## Verified result

- 15 unit tests passed under Python 3.9.6.
- 500 seeded random sessions terminated within 24 accepted moves. Every session
  passed the world invariants and exact replay comparison. All eight sequenced
  beats were reached across the sample, with 83 distinct selected-beat paths.
- Random outcomes: 204 departures, 45 ejections, 138 nights apart, and 113
  unresolved evenings. **Zero random sessions reached repair.** These frequencies
  describe the specified random policy, not human play or dramatic diversity.
- Six scripted sessions witness all five outcomes and reproduce exactly.
- A fresh copy of the directory ran from an unrelated temporary working
  directory. Demo execution, replay in a new process, and interactive help,
  numbered input, unsupported input, and leaving all passed.

The inventory contains eight sequenced beats, 23 within-beat goals, five terminal
outcomes, three two-tier clue topics, 11 social-exchange bindings, and 66 authored
performance slots. There are 130 unique content lines across 137 line slots.
These units are much smaller than a production drama's performance units.
Inventory counting excludes engine-level scaffolding; consult `audit.json` for
the complete definition and current counts.

## Causal comparison

The repair and distrust scripts change the guest's first and fourth moves from
`empathize` to `blame`. Both expose the same papers, then ask both hosts to own
their choices and propose the same conversation tomorrow.

| Same later intervention | Earlier empathy | Earlier blame |
| --- | --- | --- |
| Ask Mara to take responsibility | Accepted | Refused due to low trust |
| Ask Eli to take responsibility | Accepted | Refused due to low trust |
| Propose a conversation tomorrow | Accepted | Refused because responsibility has not been taken |
| Director's remaining arc | Advances to decision | Continues into another topic and the crisis |
| Final image | Chairs together; both papers between the plates | Chairs opposite; papers exposed but dinner untouched |

The repair run lasts 11 moves and the distrust run 17. This is a concrete,
replayable causal difference, but the checks are authored for a known small
mechanic. They are not evidence that arbitrary conversation yields meaningful
global agency.

## Reading and repairs

Read all six demonstration transcripts in full, plus random seeds 0, 17, and 41
before the final apology correction. Seed 17 leaves immediately; it was retained
as an honest sample, not replaced with a longer or better story. Automated
traversal was then rerun after the correction.

Two repeated defects were repaired during implementation:

1. A successful mediation originally fed into another accusation and a crisis
   that asked how to solve an already-agreed problem. Agreements now change the
   director phase and can explicitly abort an unfinished topic. Letter and
   receipt disputes also have alternatives for acknowledged responsibility.
2. Apologizing before doing anything wrong originally earned trust and drew an
   inappropriate request to start over. A new variant now says the argument
   isn't the guest's to apologize for, changes no trust, and leaves a later
   contextual apology available.

Physical review also caught the overnight bag missing from the world inventory
and generic endings moving Mara's key without saying so. The bag is now a carrier
with location/state changes, and only the night-apart ending moves her key.

## Remaining limitations

- The successful route is narrow: disclosure, trust, two explicit responsibility
  prompts, and mediation. Random traversal did not discover it. This may feel
  like finding a prescribed solution rather than holding a flexible conversation.
- Some empathetic and defensive lines are shared across the hosts. They sound
  repetitive when issued back to back. Dynamic re-entry is mechanically sound
  but occasionally feels like an actor receiving a stage cue.
- Only whole hidden truths are tracked as knowledge. Partial hints, uncertainty,
  and disagreement about an interpretation are not separately modeled.
- Each successful social exchange can affect state once. This prevents farming
  but does not distinguish a new offense from an old one, so repeated genuine
  repair is limited.
- “Take a night apart” has unconditional willingness in this particular scene.
  It is a simple boundary route, not a general model of consent to social plans.
- One director coordinates both characters; intentions are authored within
  performances. There is no concurrent planning, free-text understanding,
  speech animation, voice performance, or interruption inside an exchange.
- There is one premise, a fixed phase arc, and five ending categories. Eighty-three
  traversed beat sequences do not amount to 83 independently authored stories.
- The code and content were built together in this task. Neither human-equivalent
  authoring hours nor a coding-agent speedup was measured. Content source length
  is an inventory measure, not a substitute for authoring effort.

The next discriminating test is a fixed extension brief with timed authoring,
preserved failures, and independent quality review, as specified in `TODO.md`.
