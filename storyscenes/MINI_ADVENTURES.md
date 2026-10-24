# Mini-Adventures: Local Plays, Global Continuity

Design and prototype checkpoint, October 24, 2026.

## The Change In Scale

The unit of authorship is a small playable encounter, usually about fifty words
when rendered. A longer story is a compatible sequence of those encounters.
Think of movement between game scenes, with a little gameplay inside each one,
or a theater production whose sets each permit a small play to unfold.

The previous experiments spent substantial effort on long chains of simulated
actions, provenance, and QA. Correct execution did not ensure satisfying prose,
and reassuring judge averages did not reliably match the user's reading of the
examples. The response here is a narrower authoring boundary, not a claim that
a more elaborate simulator will automatically become a better writer.

**Author a good interaction; simulate its bounded possibilities; preserve its
consequences when choosing the next interaction.**

## Two Levels

### The Adventure

The outer scenario owns the cast, setting, physical parameters, initial wants,
compatible scene pool, and possible endings. Shared state persists across scenes.

Entering a house makes indoor scenes and exiting the house possible. Exiting
makes indoor scenes unavailable again. A wet sleeve stays wet; a borrowed object
does not become owned; learning something should change which later dialogue
makes sense. Prefer current-state conditions to a blanket rule that scene B
requires scene A to have appeared somewhere earlier.

Not everything needs a causal dependency. A recollection or a teasing exchange
may be entirely optional, sharing only characters and a suitable context with
the surrounding story. These scenes can provide characterization without
unlocking a task or advancing a physical objective.

There are also narrative constraints distinct from physical legality. It may be
physically possible to enter a room and leave immediately, but a selected visit
should contain something worth reading. Endings need to fit the selected middle,
and the length budget must leave room to reach one.

### The Mini-Play

Each scene has a small set, cast, props, intentions, interactions, and stopping
points. Its prose is not merely a canned paragraph selected by a flag. Local
actions change the world, and those outcomes determine the rendered variant.

For example, switching off a light is not synonymous with making a room dark:

| Situation | Local play | Consequence |
| --- | --- | --- |
| Closed shutters, no daylight | Light off; a child gets frightened; asks for light; the other restores it and apologizes | Fear is relieved; the apology can matter in the ending |
| Daylight through open shutters | Light off; the room stays bright; the children play with shadows | No invented fright or apology; a different ending remains eligible |

A bridge test can similarly succeed or fail depending on span and material.
Failure can leave wet hands, which matter when opening a tin several scenes
later. These are small symbolic simulations, not a universal physical model.

Both levels use the same persistent state. Scene boundaries limit the scope of
simulation; they do not reset possessions, locations, emotions, or knowledge.
This follows the repository's embedded-state direction: relevant properties
belong to characters, props, or their physical group, rather than free-floating
concepts that surface as narrative fragments.

## Story-First Authoring

The intended authoring process is:

1. Write a coherent reference story, roughly 1,000 words, with dialogue, motives,
   complications, and an earned ending. Read it before implementing anything.
2. Identify about twenty short interactions. The exact boundaries can change
   when making shorter routes; fifty words is a scale, not a padding quota.
3. Separate essential developments, optional vignettes, branch-sensitive scenes,
   and endings. Explicitly identify callbacks and state dependencies.
4. Author readable shorter routes and alternate local outcomes. Do not assume
   any seven paragraphs from the reference will make a story.
5. Implement only the local rules and shared state those routes require.
6. Generate, read, and test complete stories, including transitions and endings.
   Preserve parameters, traces, and source snapshots so failures are reproducible.

The reference is one good playthrough, not a mandatory twenty-scene chain.
Future scenario packs may add alternate encounters or endings that never occur
in that reference. Removing a scene must not silently execute its useful events
offstage. Any essential replacement or transition must be enacted and made
understandable in the shorter story.

## The Smallest Sea

The [reference story](design/mini_adventure_20261023/reference_story.md) adapts the
domestic pirate-play premise and the clothing problem from Pirates and Puddles.
It has 1,011 words across twenty provisional scenes. Tom wants the treasure and
the authority of being captain; Lily wants a real say in their adventure.

The implemented scenario has fifteen scene definitions, including three endings.
Some adjacent reference beats are combined to leave space for optional scenes.
Its five core functions are launch, crossing, treasure recovery, sharing, and
return/ending. Two or three additional scenes make a seven- or eight-scene story.

The implementation reuses the existing atomic `runtime.transition` function.
It does not modify the shared engine or add a runtime LLM. A seeded bounded
search chooses compatible scenes and checks that the requested length can still
reach an ending. It is not a collection of prewritten whole-story routes.
Each committed local event records its preconditions and state changes;
speculative search branches are not narrated.

| Component | Implementation |
| --- | --- |
| Global parameters, state, local rules, selection, replay, export | [smallest_sea.py](smallest_sea.py) |
| Authored prose conditioned on enacted outcomes | [smallest_sea_prose.py](smallest_sea_prose.py) |
| Physical and narrative boundary tests | [test_smallest_sea.py](test_smallest_sea.py) |
| Scene inventory, detailed rules, commands, measurements | [Prototype README](design/mini_adventure_20261023/README.md) |

Start with the outputs, not the implementation:

- [Two seven-scene stories](design/mini_adventure_20261023/generated_v1/seven/stories.md).
- [Two eight-scene stories](design/mini_adventure_20261023/generated_v1/eight/stories.md).
- [Dark summerhouse and its matching ending](design/mini_adventure_20261023/generated_v1/dark_cave/stories.md).

The first four use consecutive seeds 0 and 1 at both lengths. Seed 41 was
selected explicitly to illustrate the fear/apology branch. None of the saved
story text was manually edited after generation. Each batch includes JSONL
state/event traces, a manifest, and frozen source copies. The complete prototype
and its examples are small text files; no large data archive is needed here.

```bash
./.venv/bin/python -m storyscenes.smallest_sea --seed 41 --scenes 8
./.venv/bin/python -m storyscenes.smallest_sea --seed 0 --scenes 7 --count 3
./.venv/bin/python -m storyscenes.smallest_sea --seed 0 --scenes 8 --params storyscenes/design/mini_adventure_20261023/example_parameters.json
```

## What The Checkpoint Shows

On seeds 0-99, seven-scene stories average 354.3 words and eight-scene stories
400.2 words, with individual scenes ranging from 38 to 70 words. The same local
scene can have different physical outcomes; optional scenes can be absent;
later actions and endings account for the path actually executed.

Fifteen prototype tests cover 200 seeded routes plus 1,024 routes across a
512-configuration corner grid at both lengths, along with targeted invalid-action
and counterfactual cases. Twenty existing runtime tests also pass. The grid is
not exhaustive over every permitted numeric parameter. The tests check execution,
conservation, atomic failures, continuity, determinism, and exact replay; they do
not measure whether a story is enjoyable.

The five saved examples were read locally. The user's response was that this
looked more reasonable than the preceding approach. That is encouraging feedback
on direction, not a blinded comparison or calibrated quality score. No new paid
judging was performed, and there is no measured authoring-cost advantage yet.

## Limits And Next Gates

All current routes still find and share the same treasure. Alternate endings
reflect the crossing or the apology, not fundamentally different objectives or
success/failure outcomes. The party never splits; scenes cannot repeat; the
detour is always available. Physical rules are scenario-specific abstractions,
and incidental gestures are not individually simulated. QA and training export
are not integrated into this prototype.

Exact text counts and shuffled optional-scene orders must not be presented as
equivalent to meaningful new stories. Large sample counts would quickly amplify
the same authored material. Likewise, compatibility proves only that a route is
allowed, not that every transition reads naturally or every vignette earns its
space.

The next useful gates are bounded:

1. Compare a few generated routes with the reference and existing good examples,
   using human reading before relying on a numeric judge threshold.
2. Add one genuinely different middle/outcome, with its own earned ending,
   rather than more interchangeable names or adjectives.
3. Try a second small scenario without changing the shared runtime. Track the
   authoring and repair effort to test whether this approach actually amortizes.
4. When adding QA, distinguish simulated facts from facts the selected prose
   reveals. A correct hidden trace alone does not make a question answerable.

These are proposed next experiments, not implemented features or commitments to
scale. The immediate deliverable is a reproducible, readable prototype at the
smaller scene boundary.
