# Mini-Adventure: Story-First Prototype

For the rationale, authoring workflow, and next experimental gates, see the
[mini-adventure design write-up](../../MINI_ADVENTURES.md).

## Reference Playthrough

Read [The Smallest Sea](reference_story.md) as a complete story first. Hidden
Markdown comments mark twenty provisional scene boundaries without adding
scene labels to the rendered prose. This is an authored reference playthrough,
not output from a simulator and not an evaluated generator.

It adapts the domestic pirate-play premise and Lily/Tom cast from
[`pirates.py`](../../../storyworlds/worlds/pirates.py), and the treasured-clothes
versus muddy-play problem from
[`puddles.py`](../../../storyworlds/worlds/puddles.py). The garden expedition,
dialogue, and outcome are newly written. Neither source script is modified.
The original Pirates fire episode is not part of this adventure.

Tom wants both the treasure and the authority of being captain. Lily wants a
real part in choosing the adventure. Physical problems give them opportunities
to listen, cooperate, and share; the ending changes how they plan the next game.

## Provisional Scene Inventory

These are authoring notes, not executable contracts or claims that arbitrary
subsets already compose. Optional means optional to the central treasure hunt;
callbacks, transitions, and local dependencies still need handling.

| ID | Small interaction | Role / continuity to preserve |
| --- | --- | --- |
| 01 | Negotiate roles in the game | Establishes the relationship and shared play |
| 02 | Receive a map and a boundary | Establishes treasure, destination, no damaged flowers |
| 03 | Orient the map against the garden | Optional; Lily takes custody of the map here |
| 04 | Recall an earlier game over a found flag | Optional vignette; no required plot unlock |
| 05 | Test whether boots protect a coat | Optional clothing episode; paired with 06 in this path |
| 06 | Negotiate and change the captain's clothes | Changes worn/stored garments; later sleeve/coat details depend on it |
| 07 | Dodge a gutter drip and refold the hat | Leaves the house; optional hat damage has a final callback |
| 08 | Enter and inspect the summerhouse | Optional excursion; enables indoor scenes |
| 09 | Switch off the light, frighten, restore it | Optional local interaction; depends on being inside with the light on |
| 10 | Read height marks and remember a younger child | Optional vignette within the summerhouse |
| 11 | Exit, switch off the light, latch a sticky door | Required exit after an entered summerhouse, not after every route |
| 12 | Test reach across a puddle | Establishes this route's physical obstacle |
| 13 | Test and retrieve a board that cannot span it | Optional failed attempt; leaves a wet sleeve and later callbacks |
| 14 | Reject a flower-bed shortcut and choose a path | Finds a permitted route; Tom follows Lily's suggestion |
| 15 | Locate and retrieve the hidden tin | Establishes possession through a physical retrieval |
| 16 | Open a tight lid with dry hands and a partner | Reveals edible contents and their uneven condition |
| 17 | Negotiate shares and divide the biscuits | Resolves the local fairness problem; biscuits are eaten |
| 18 | Return by the known path and name it | Returns from the garden; board dialogue requires 13 |
| 19 | Remove muddy gear and talk to Mom | Restores indoor context; clothing/bridge details are path-specific |
| 20 | Offer the captaincy and choose together | This reference ending pays off the role dispute and cooperation |

## Executable Prototype

The reference above is preserved. The new offline prototype is
[`smallest_sea.py`](../../smallest_sea.py), with authored mini-plays in
[`smallest_sea_prose.py`](../../smallest_sea_prose.py) and focused
[tests](../../test_smallest_sea.py). It reuses the existing `runtime.transition`
for atomic local actions; no shared engine or old generator was changed.

Read the actual generated stories:

| Examples | Selection | What to compare |
| --- | --- | --- |
| [Two seven-scene stories](generated_v1/seven/stories.md) | Consecutive seeds 0 and 1 | Sound bridge versus failed board, wet hands, and a detour |
| [Two eight-scene stories](generated_v1/eight/stories.md) | The same seeds 0 and 1 | Optional summerhouse visit versus indoor clothing/map/memory scenes |
| [Dark summerhouse](generated_v1/dark_cave/stories.md) | Seed 41, explicitly selected to show the fear/apology branch | A different local light outcome and its compatible ending |

These are runtime outputs, not edited excerpts. Each batch contains readable
Markdown, `stories.jsonl` with parameters, scene pre/post states and local event
changes, and a manifest with hashes of its three frozen runtime source files.
The fixed-seed examples are illustrative, not a quality-filtered success rate.
There were **no API calls or paid judging**.

### Global Selection

There are fifteen scene definitions, including three conditional endings.
To leave room for optional mini-plays, some adjacent reference beats are combined:
roles and map become `launch`; crossing contains the board test and route choice;
treasure recovery includes lifting and opening; returning home belongs to the
ending. This is not arbitrary deletion of paragraphs from the long reference.

Every route includes launch, a crossing, treasure recovery, sharing, and one
ending. The remaining two or three slots are selected from compatible optional
scenes. A seeded bounded search checks the current state, avoids repeated scenes,
and looks ahead to an attainable ending at exactly seven or eight scenes.
It searches a scene pool, not a list of prewritten complete story routes.

- Indoor preparation cannot happen after departure.
- Indoor summerhouse play requires actual entry; leaving is required before
  crossing the garden. A selected visit must include either the lights mini-play
  or the height-mark recollection. This is an authored narrative constraint,
  separate from the physical permission to leave immediately.
- The summerhouse visit takes three slots, so this prototype includes it only
  in eight-scene routes. The independent flag recollection remains optional.
- Treasure cannot be retrieved before reaching the tree; sharing requires the
  tin to have been opened and its contents observed.
- The bridge ending requires a successful supported crossing. The explorer
  ending follows the detour. An enacted apology in the dark scene instead
  enables the together ending, which remembers that interaction.
- Return movement checks that the chosen crossing still works. The ending
  requires both characters home, boots off, tin on the table, biscuits shared
  and eaten, and any visited summerhouse shut with its light off.

### Local Simulation

Local actions execute on a copied state using the existing atomic transition
function. Every committed event records its preconditions and changed values;
illegal scenes/actions fail without changing the caller's state. Prose is
rendered from the executed scene's before/after states. Speculative search
branches never appear in the output trace.

| Mini-play | Local rules and persistent consequences |
| --- | --- |
| Clothing | A choice changes which coat is worn and which is on its hook; later splashes affect the selected garment |
| Gutter | Water wets the hat; folding it changes its physical state |
| Lights | Switching off creates darkness only without daylight; darkness causes fear, a request, restored light, and an apology |
| Door | A sticky latch fails on the first close and needs the door lifted; a free latch closes directly |
| Board | Sound material and at least 10 cm support on each bank are required; failure wets hands/sleeve, retrieves the board, and leads to the long path |
| Treasure | A heavy pot needs combined strength; wet hands need drying, and a tight lid needs a partner to brace the tin |
| Sharing | A claim can provoke objection; the final allocation conserves eight quarter-biscuit units, four eaten by each child |

Physical parameters are sampled once per adventure, not independently in each
scene. Names, board length/condition, puddle width, daylight, latch condition,
pot mass, lid tightness, clothing choice, sharing behavior, and map orientation
are explicit global parameters. Characters remain a co-located party. State
keys attach properties, memories, trust, and cooperation to physical props or
characters, consistent with the repository's embedded-state design.

### Run And Reproduce

From the repository root:

```bash
./.venv/bin/python -m storyscenes.smallest_sea --seed 41 --scenes 8
./.venv/bin/python -m storyscenes.smallest_sea --seed 0 --scenes 7 --count 3
./.venv/bin/python -m storyscenes.smallest_sea --seed 0 --scenes 8 --params storyscenes/design/mini_adventure_20261023/example_parameters.json
./.venv/bin/python -m storyscenes.smallest_sea --seed 100 --scenes 8 --count 5 --out /tmp/smallest-sea-new-batch
```

`--params` merges a JSON object over that seed's sampled parameters. Output
directories must be new; the exporter refuses to overwrite prior batches.
Replay a saved batch from its frozen source, independently of working edits:

```bash
PYTHONPATH=storyscenes/design/mini_adventure_20261023/generated_v1/dark_cave ./.venv/bin/python -m source.smallest_sea --seed 41 --scenes 8
```

For programmatic replay, use `replay(Parameters(**row["parameters"]), row["path"])`.
It reproduces each scene's text, events, and state, not just the final ending.

### Verification And Review

Fifteen new tests pass. They include 200 seeded complete routes and 1,024
complete routes across a 512-configuration corner grid at both lengths.
The grid varies nine sampled dimensions with puddle width fixed at 100 cm;
it is not exhaustive over all permitted numeric values. Separate tests cover
the exact board-support threshold, wrong-location actions, conservation,
atomic failure, incompatible endings, optional-memory independence, parameter
overrides, callbacks, deterministic replay, and frozen-source/no-overwrite export.
All twenty existing `test_storyscenes.py` tests also pass.

```bash
./.venv/bin/python -m unittest discover -s storyscenes -p 'test_smallest_sea.py'
./.venv/bin/python -m unittest discover -s storyscenes -p 'test_storyscenes.py'
```

Local sampling of seeds 0-99, without prose-based filtering:

| Length | Story words min/mean/max | Mean scene words | Distinct scene paths | Exact texts |
| --- | --- | --- | --- | --- |
| 7 scenes | 321 / 354.3 / 377 | 50.6 | 17 | 85/100 |
| 8 scenes | 364 / 400.2 / 424 | 50.0 | 26 | 96/100 |

Individual scenes range from 38 to 70 words. The seven-scene sample has 30 bridge
and 70 explorer endings; the eight-scene sample has 27 bridge, 66 explorer, and
7 together endings. These counts measure local variation, **not literary quality
or a demonstrated training-data multiplier**. Reordering optional scenes counts
as a different path but may provide little substantive novelty.

Manual reading of all five saved stories found a complete treasure-hunt arc,
visible cause/effect at the crossing, and endings that refer to events actually
included. A first draft's repeated names and unsupported clothing callback were
repaired before export. The selector was also changed to avoid empty enter/exit
visits. This is author review, not an independent human verdict or a judge score.

Limitations: the same five core functions appear in every story, the children
always obtain and share the same treasure, and the alternate endings remain
within that successful expedition. The setting, detour, and prop repertoire are
bounded; these are symbolic scenario rules, not a general physics engine.
Incidental gestures and every word of dialogue are not individually simulated.
No QA/training exporter integration or new scoring protocol is implemented here.
