# Retrieving authored event fragments from short lines

The event pool extends entity retrieval with **reusable programs**. A brief can
name a goal and two objects; a matching program brings its supporting cast,
props, prerequisite actions, physical mechanism, dialogue and ending.

```python
from grammarworlds.event_pool import generate

brief = {
    'schema': 'event-pool-v1',
    'intent': 'reveal',
    'roles': {'rabbit': 'my_rabbit', 'hat': 'my_hat'},
}
row, attachment = generate(brief, existing_world, seed=3)
print(row['story'])
```

For a world assembled from defaults:

```json
{
  "schema": "event-pool-v1",
  "setting": "garden",
  "intent": "reveal",
  "roles": {
    "rabbit": {},
    "hat": {"properties": ["portal_hat"]}
  }
}
```

This retrieves the authored bound-hat program: a promised trick, an unsuccessful
attempt, discovery of a tied ribbon, untying, magical transport, ears appearing,
the reveal, a reaction, and a carrot ending. The actor defaults to Merlin; an
explicit new name such as Merlinus can inherit the prototype. Source flavor such
as June, a hutch, the wand, ribbon and carrot is allowed to travel with the
fragment. Every import is recorded.

## Pool contents

There are currently **five selectable recipes**, assembled from six reusable
subfragments plus existing portable operations:

| Recipe | Primitive events | Source |
|---|---:|---|
| Bound magical hat | 13 | New authored Merlin example |
| Already-open magical hat | 10 | Shorter variant of that example |
| Ordinary stage hat | 12 | Alternative placement/reveal mechanism |
| Repair and fly a kite | 4 | Existing kite ports |
| Draw from a moon atlas | 1 | Existing library port |

The six shared subfragments are setup, unbinding a hat, magical arrival,
stage arrival, rabbit reveal, and the care/ending sequence. They take typed role
variables; they contain no fixed character IDs or saved English continuation.
The reveal and ending are identical reusable subprograms across both physical
explanations. The hat example is an isolated authored addition, not another
registered member of the seven-world storytelling CLI.

## How selection and expansion work

1. Match the requested intent and required anchor roles against recipe signatures.
2. Bind existing compatible entities, preferring the world's protagonist/helper
   when those roles resolve a tie. Otherwise instantiate the recipe's catalog
   defaults. Unknown roles and unresolved ambiguous local bindings fail explicitly.
3. Expand parameterized subfragment calls with variable substitution. Validate
   signatures, recursion and the expansion bound. Store the source path of every
   expanded event.
4. Place newly imported objects according to the authored bundle, with explicit
   provenance. Existing entities retain their initial state and locations.
   A local rabbit's current place can supply the source role, and the hat's
   current place can supply the stage role.
5. Dry-run the program on a clone using physical guards and effects. Reject
   physically incompatible programs; do not invent missing mechanics.
6. Assign compatible recipes manual weights plus optional cue matches, normalize
   them into a distribution, and sample. These are authored preference weights,
   not learned probabilities. Keep the candidate distribution and rejection reasons.
7. Project the expanded program onto participant-local lines. Shared events
   synchronize those lines, and the existing grammar samples words before each
   commit. Runtime guards recheck the actual world state.

A magical portal moves the **existing rabbit** from its source place into the
hat; it does not create a rabbit. That mechanism requires a portal-capable hat,
a capable actor, a held wand and an open brim. The ordinary-hat program instead
closes the spectator's eyes, puts the rabbit inside, and reopens their eyes.
A pre-existing ordinary hat is never granted portal physics by retrieval.

A physically open but otherwise under-specified *new* hat can admit either
explanation. The corresponding candidate worlds differ in imported defaults;
the sampled recipe's world is the one actually used. A bound magical hat admits
the obstacle/recovery variant, and an already-open one skips that obstacle.

## Authoring another reusable fragment

Imported events now carry [target-adapted token attributes](ATTRIBUTE_TRANSFER.md).
Brief roles can also provide weighted candidate bindings; feasibility filters
complete alternatives before one attachment is selected.

`pool_fragments.py` contains the entity exports, subfragments and recipe data.
A subfragment lists `params` and `steps`; a call supplies an explicit `bind`
mapping from these parameters to enclosing roles. A recipe defines typed roles,
required properties/states, default prototypes, placement relations, retrieval
intent/cues and a sequence of calls or primitive operations.

`pool_mechanics.py` registers the new physical operations and typed realizations.
Adding arbitrary source code or state diffs to a catalog is not enough to make
it executable. The older catalog-backed kite/drawing operations are reused via
`CatalogLines`; its original API and behavior are unchanged.

`event_pool.py` implements assembly, expansion, candidate selection and replay.
`pool_qa.py` derives a few mechanism/cause/outcome checks directly from bound
roles and event history. These are diagnostics for our own output, not a natural
language QA parser.

## What is and is not inferred

The input omits a detailed event chain, and the retrieved authored program supplies
one. It can also supply supporting people, objects, initial placements and some
source flavor. This is retrieval and recombination of reviewed narrative
knowledge, not synthesis of arbitrary new physical rules.

The full source mechanism and narrative scaffolding were authored. We ported
selected existing sequences rather than automatically factorizing every old
storyworld. One brief currently selects one root recipe; subfragments compose
within that root. Open-ended composition of multiple retrieved recipes, repeated
entity-local goals and automatic repair of conflicting plans remain future work.
Distinct program roles still cannot alias the same entity; for example, a target
that wants one place to fill both stage and source needs a differently factored
recipe. The dry-run proves one legal schedule, not a general theorem that every
possible schedule finishes.

Default source placements are assembly assumptions, not fetching/travel events.
Physical capacities are qualitative; this is not a detailed geometry simulator.
Current word heads have no effective special treatment for hats/rabbits; the
improvement here comes from the event pool. Source flavor is allowed, but known
physical contradictions remain blocking conditions.

The implementation moves toward `story.py`: event programs bind to physical
carriers, actions update persistent state, and compatible embedded capabilities
determine what can happen. It does not yet implement the full memeplex algebra
or use concept magnitudes to score retrieved plots.

## Reproduce and inspect

```bash
.venv/bin/python -m grammarworlds.event_pool --out /tmp/hat-pool --count 20
.venv/bin/python -m grammarworlds.event_pool --mode stage --out /tmp/stage-pool
.venv/bin/python -m grammarworlds.event_pool --brief brief.json --out /tmp/custom-pool
.venv/bin/python -m grammarworlds.event_pool_experiment --out /tmp/pool-comparison
.venv/bin/python -m unittest grammarworlds.test_event_pool -q
```

See the [experiment report](runs/event_pool_20261106/report.md),
[transferred magic samples](runs/event_pool_20261106/magic_local_cast/samples.md),
[ordinary-hat samples](runs/event_pool_20261106/stage_local_cast/samples.md), and
[serialized fragment pool](runs/event_pool_20261106/pool.json).
