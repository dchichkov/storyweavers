# Bare-world attachment from three donor stories

The input starts with zero entities and an authored seven-event line. The
resolver retrieves ten entities from the library, kite and music worlds,
constructs a meadow from the supplied context and a sky from the flight
requirement, then executes the line using classical grammar and world state.

| Input mention / missing role | Retrieved prototype | What it brings |
|---|---|---|
| Mino | Library Mina | Moon-sketch capability; paper, pencil, moon atlas dependencies |
| Sammy | Kite Sam | Repair/help capabilities |
| kite | Kite target | Torn/grounded state; tape and string dependencies; repair/flight port |
| Niah | Music Nia | Drumming capability; little drum dependency |

No explicit donor IDs or object definitions appear in the input line. Name
similarity selects among candidates satisfying the action-derived requirements.
Prototype links and portable physics were authored for this experiment, based
on existing source entities/guards/effects. This is not automatic extraction of
arbitrary behavior from Python or prose.

## Unfiltered seed 0

> Mino located the torn kite in the meadow. Mino said, “I would like to fly the kite.” Sammy said, “I could help you.” Using the tape, Sammy fixed the kite. Mino held the moon atlas. With the pencil, Mino sketched the moon on the paper. She flew the kite with the string. Niah beat the little drum. The kite flew in the sky.

Seeds 0–4 are in [samples.md](samples.md). The complete world, inferred bindings,
local lines and provenance are in [resolved.json](resolved.json).

## Measurements

| Measure | Word heads off | Word heads on |
|---|---:|---:|
| Seeds | 0–19 | 0–19 |
| Completed | 20/20 | 20/20 |
| Distinct texts | 20 | 20 |
| Token steps including sentence end | 1,735 | 1,735 |
| Steps with multiple choices | 225 (12.97%) | 225 (12.97%) |
| Distributions changed by heads | 0 | 24 |

Across the two conditions there are two event orders: drawing may precede or
follow repair. Only one of twenty paired texts changes with word attention.
The main new capability is retrieval/assembly, not stronger word attention.
All forty histories were reconstructed and verified against their final worlds.
Completeness here means completion of the supplied local lines, not an
independently judged story-quality score.

## Ablations

- Empty catalog: unresolved visitor.
- Dependency inference disabled: missing repair tool.
- Remove any one of the three source worlds: unresolved corresponding entity.
- Remove wind: 20/20 block at flight after successful repair.
- Remove tape repair affordance: 20/20 block at repair.
- Remove the kite's embedded physics marker: 20/20 block before the premise.
- Move drum away from Niah: 20/20 block at the finale.
- Make kite fragile: 20/20 block at flight; the source failure branch is not ported.

The 100 execution-ablation histories also pass reconstruction verification.
Results and blocking reasons are in [ablations.json](ablations.json). These
interventions establish prerequisite enforcement within this supplied example;
they do not measure open-ended retrieval accuracy.

## Validation and interpretation

The full grammarworlds suite passes: **140 tests**, including 12 new catalog
checks. Checks cover source isolation, three-source retrieval, omitted dependency
completion, local entity reuse, unknown/ambiguous matches, missing physics,
rejected commits, existing replay behavior, and a separate drawing-only line
with different role names. Frozen portable grammar and source story packs were
not edited.

The output has a premise, help dialogue, a repaired-to-flying state change and
an ending image. The moon drawing remains weakly integrated into that outcome.
Objects are placed as part of world assembly, with explicit provenance; no
fetching or travel is implied. Donor flags/history/goals are not imported.

This supports the proposed architecture on a bounded example:

**annotated line → role requirements → compatible prototypes → object/physics
dependencies → local instances → guarded replay.**

It does not yet demonstrate arbitrary source-rule extraction, full relationship
closure, new physics synthesis, or spontaneous plot construction. The three
portable behavior families and event line were supplied by us.
