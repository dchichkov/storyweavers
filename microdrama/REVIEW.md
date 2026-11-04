# Proof-of-concept review — 24 October 2026

This is a working adaptation of the supplied two-part fable, with a separate
world kernel, encounter library, discourse layer, and grounded question layer.
The useful finding is that **belief correction, practical skill, coordinated
action, and control of an institution can be different outcomes**. Mira can
recognize a false accusation without changing the pigs' story; two capable
workers can still fail to defend a public space when they have not learned to
act together.

## Mechanical evidence

The reproducible commands are in `README.md`. `audit.json` records every checked
configuration and seed, exact state/text hashes, selected encounters, five matched
counterfactuals, and the unfiltered sample recipe. `verification.json` records the
test result and the independent portability check.

The final suite contains 27 tests, including a finite-grid test with **240 runs**
and **2,880 question answers**. The grid comprises 48 declared combinations at
seeds 0–4. Its outcomes are 30 libraries, 30 night schools, and 180 closed palaces.
The 14 encounter paths reflect ordering and optional scenes, not 14 independent
plots. Output length ranges from 1,263 to 1,855 words, including the title.

Tests inspect intermediate states as well as endings: physical failure causes,
continued false accusations, remote/locked transmission rejection, ownership
versus occupation, skill acquired only after a successful physical trial,
state-dependent objections, and explicit restitution. Replay checks exact bases,
read dependencies, patches, and result hashes. Invalid and unrecorded effects
are rejected without committing the encounter. QA facts are checked against
historical event snapshots; reader questions cannot use unrevealed future events.

A copy of the folder was run in a temporary parent outside the repository on
Python 3.9.6, with site packages disabled and `PYTHONPATH` removed. Generation,
the question output, and an interactive follow-up session worked. Its absolute
imports are all standard library modules. No legacy engine, external dataset,
model service, or installation is needed to run it.

## Reading the stories

This is author self-review, not a blind independent evaluation. I read the common
opening spine, the complete library/night-school/locked/interrupted examples,
and every changing scene from the five unfiltered samples alongside their QA.

| Case | Reading observation |
|---|---|
| `examples/library` | The drain and bridge give the two objections distinct, concrete reasons. The shared signals connect earlier work to the confrontation. Explicit agreement about the cottage makes Wolf's return earned within the modeled settlement. The stove and library windows close the story. |
| `examples/night_school` | Half attention plus separate jobs leaves Mira able to use her book and Tansy unable to complete his trial. The isolated objection fails, but carrying one book creates a smaller ending. The private lamplight and continued occupation of the cottage show what changed and what did not. |
| `examples/locked` | Removing access removes reading and trials, shortening the middle naturally. The blocked cupboards are visible before the ending. Warm soup can change Mira's regard for Wolf without providing technical competence. |
| `examples/interrupted` | Both trials fail despite a brief demonstration. The wet bricks and bowed plank make failure concrete; the scalar account of why learning failed remains coarse. The changed final image supports an unhappy ending rather than an unexplained stop. |
| `samples/seed0` | Mira witnesses the theft, yet half-attention reading without teaching leaves the practical trials unsuccessful. Personal doubt does not magically persuade the rulers or supply missing competence. |
| `samples/seed1` | Locked books; the paper encounter occurs and lunch does not. The ending remains intelligible without the optional sympathetic scene. |
| `samples/seed2` | Same input conditions as seed1, with lunch included. This is a different telling of the same institutional outcome, not new plot diversity. |
| `samples/seed3` | Tansy reads before Mira; the paper arrives between their failed trials. References remain clear across that order. |
| `samples/seed4` | Locked books, with lunch before the paper. The final image remains physical and grounded; the earlier witness changes only the local belief. |

All five unfiltered samples ended in closed palaces. They were not replaced with
more favorable seeds. This reveals the dominance of the closed-palace branch in
the chosen parameter space; it is not evidence that five unrelated stories were
invented. The distinct example recipes expose the less frequent alternatives.

During reading I repaired a plural protest description that did not fit the
one-objector case, repeated interruption wording, and a final viewpoint that
implied seeing an indoor cupboard from outside. During verification I repaired
Python 3.9 annotation compatibility and a short failure answer. Input conditions
now live in physical world state, so changing a renderer's parameter argument
cannot rewrite what happened. See `TODO.md` for retained qualitative limitations.

## Acceptance audit

The eight requirements below are the original checklist in `DESIGN.md`.

| Requirement | Current evidence and interpretation |
|---|---|
| 1. Isolated, classical, runnable | Nine local Python modules, standard-library import inspection, temporary-copy execution, runnable CLI, saved stories/traces/questions. No sibling imports or changes to gen6/gen7. |
| 2. Preserve the inspirational causal spine | `palace.py` records all three material failures separately from false claims, exile, occupation, coercion, village construction, Fox's theft and prestige intervention, book delivery, practical learning, and settlement. The generated library story was read against both supplied parts. |
| 3. Embedded, composable content | Algebra/transmission tests; per-carrier magnitudes and access/location checks; actual attention amounts recorded as transfers. Encounter effects persist in physical participants. World truth and local belief are distinct. This is the explicit subset of the memeplex north star described in the README, not its full executable algebra. |
| 4. Bounded composition and consequences | Admission conditions and seeded local alternatives in the trace; shared reading/testing practice bindings; optional lunch and paper; three state-derived settlements. Five matched comparisons change one input each. The ten-encounter opening remains authored and fixed. |
| 5. Physical and social continuity | Separate owner/occupant fields, access checks, demonstrable trial conditions, actual book movement, continuing coercion in the night school, and an explicit concession before Wolf returns home. Counterfactual and intermediate-state tests cover these. |
| 6. Separate execution and narration | Pure historical renderer; event-linked paragraphs; tests for rollback, unrecorded effects, and independence from later state or parameter changes. Manual reading confirms a premise, state-driven turn, and ending image in every reviewed variant. |
| 7. Grounded QA and follow-ups | Twelve questions with historical fact tuples and supporting paragraph IDs; catalog and follow-up transcripts beside each saved story. Reader-prefix tests and unsupported-question refusal. The finite grammar and authored exposure annotations are explicit boundaries. |
| 8. Verification and honest sampling | 27 tests; exhaustive declared parameter grid at five seeds; exact replay; all five predetermined samples saved; manual reading notes above. Outcome imbalance and fixed-spine limitations are retained rather than hidden by selecting better runs. |

## Assessment

The proof of concept supports building and testing stories from executable local
situations while retaining authored literary expression. Its strongest feature
is inspectable consequence: a book's accessibility affects learning, learning
affects what a character can demonstrate, and shared experience affects what the
characters can do together. Questions use those same records rather than guessing
from polished prose.

The largest unresolved question is authoring scale. Most of the expressive work
here is still authored, and the broad dramatic shape is supplied by the user's
fable. This prototype establishes a concrete unit to extend and evaluate. It does
not establish that thousands of independently authored units will compose cheaply,
or that their output will improve a trained model.
