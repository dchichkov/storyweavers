# Entity-specific event lines

`event_lines.factorize(row)` projects a generated story onto separate lines for
its physical entities. A line belongs to an entity ID, so it follows the same
cup when the cup becomes a bowl. Shared events retain one ID across all lines.
This is a first representation for local narrative substitution or retrieval;
it does not yet replace the global planner or execute independent local plans.

```python
from grammarworlds.storytelling.runtime import generate
from grammarworlds.storytelling.event_lines import factorize, local_slice

row = generate("library", 3000, continuations="expanded", symbolic_heads=True)
graph = factorize(row)
book_line = graph["entities"]["book"]["line"]
book_segment = local_slice(graph, "book", start=0, stop=3)
```

Export all seven worlds:

```sh
.venv/bin/python -m grammarworlds.storytelling.event_lines \
  --out /tmp/entity-lines --seed 3000 --count 20
```

The exporter writes full structured graphs to compressed JSONL, summary/coverage
counts, and Markdown/JSON examples for the first seed of every world.

## Tags and evidence

| Tags | Source and interpretation |
|---|---|
| `frame.actor`, `frame.patient`, `frame.instrument`, `frame.destination` | Original coarse frame slots; not a complete cast for compound scenes |
| `grammatical_subject` | Explicit entity or coordinated entities in the typed clause; a subject is not necessarily an intentional agent |
| `speaker`, `listener` | Explicit paired dialogue bindings, including listeners omitted from the selected words |
| `changed`, `moved`, `renamed` | Full entity differences from replay, including fields omitted by compact world snapshots |
| `state.add:*`, `state.remove:*`, `concept.changed:*` | Actual changes on a physical carrier |
| `source_holder`, `destination_holder` | Person from/to whom an object moves; physical possession, not legal ownership or willingness |
| `mentioned`, `qa_context`, `causal_context` | Contextual references; these alone do not count as participation |

Each tag has structured provenance. The annotation never parses English to
guess who did what. Listener and subject labels are zero-text grammar metadata;
they add no choices and do not alter word probabilities or physical effects.
Possessors are not mistaken for subjects: in “Grandpa's hand was stiff,” the
subject tag does not identify Grandpa as the grammatical subject.

An event includes physical movements, per-entity field changes, paired dialogue,
declared dependencies and global flag inputs/outputs. An entity's line includes
its own before/after state and references to the same event IDs. Context-only
entries remain available but are excluded from `local_slice` by default.

For example, library checkout has three simultaneous projections:

- Librarian: source holder / frame actor / grammatical subject.
- Jun: destination holder.
- Book: moves from librarian to Jun, gains `checked_out`.

There is one checkout event, not three independently sampled events.

## Local slices and replacement boundaries

`local_slice(graph, entity, start, stop)` takes positions in the entity's
**participating** line and returns:

- its entry/exit physical state and local events;
- shared-event joins, counterpart entities, dialogue and movements;
- declared dependencies entering or leaving the segment;
- affected global flags and their requirements/exclusions.

Required flags link to their last producer, where known. Declared location,
state and concept causes link to the most recent writer of that entity field.
These are coarse field dependencies, not proofs that a particular state bit was
introduced by that writer. World-premise facts remain explicit external inputs.

The result says `independently_executable: false` and
`requires_guard_revalidation: true`. Existing Python guards can read more than
the declared dependencies, and discourse focus and global flags still couple
the story. A matching entry/exit state alone cannot establish that a swap is
safe. In particular, a replacement must not lose another character's consent,
object availability or outstanding obligation.

The intended next step is to retrieve or propose a local line, bind its entity
roles, and test candidate events through the real guards while coordinating
shared joins. That could guide one character's continuation without selecting
a whole global story. This annotation API supplies boundary data; it does not
itself implement that planner or automatic inference. The subsequent
[attached-line prototype](../ATTACHED_LINES.md) adds guarded replay and explicit
role binding for five portable operations, with two reviewed source-event ports.
It still does not authorize arbitrary state-diff replay or general local swaps.

## Validation

The [first audit](../runs/entity_event_lines_20261106/report.md) covers all 119
pack-qualified event kinds across seven worlds. Tests cover shared handoffs,
unrecorded-by-frame movers, compound grammatical subjects, speaker/listener
pairing, cup-to-bowl identity, local boundary dependencies, invalid traces,
annotation purity and unchanged sampled word distributions. Full replay checks
effects before exposing a graph. Older saved traces lack the new grammatical
subject/listener labels; regenerate them to obtain those roles.

Physical state and concept magnitudes stay attached to entity carriers. This
follows the memeplex design: local event lines describe the carriers' actual
changes rather than treating abstract concepts as independent story actors.
