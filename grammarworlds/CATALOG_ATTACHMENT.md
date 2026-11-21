# Event lines that pull entities into a bare world

`catalog_attachment.py` adds a bounded resolver before `event_line_replay.py`.
It takes a structured event line, assembles a local world from compatible donor
entities and reviewed dependency links, and uses the existing word sampler and
shared-event synchronization to execute it. No LLM runs during retrieval,
assembly, or generation. This is an isolated grammarworlds experiment.

```bash
.venv/bin/python -m grammarworlds.catalog_attachment \
  --out /tmp/catalog-example --count 20
# Optional: --line path/to/catalog-line-v1.json
```

See the [measured experiment](runs/catalog_attachment_20261106/report.md),
[editable input](runs/catalog_attachment_20261106/input_line.json), and
[generated samples](runs/catalog_attachment_20261106/samples.md).

## Input and resolution

The example supplies names `Mino`, `Sammy`, `Niah`, the noun `kite`, a windy
meadow context, and seven structured events. It supplies no entity definitions,
prototype IDs, tape, string, paper, pencil, atlas, drum, or sky.

```text
find torn kite → want to fly → offer help → repair
                                      ↘ draw moon
repair + drawing → fly kite → drum celebration
```

The actual input is an ordered list of event dictionaries. Each participant's
projection becomes its own ordered line. This permits independent events to
interleave: repair and drawing can trade places. The order is supplied, not
learned or planned from a goal. The full input format is illustrated by the
saved JSON; operations and their slots are enumerated in `SPECS`.

1. Collect hard kind/capability requirements across every use of a role.
2. Fill omitted operation slots from reviewed prototype dependencies.
3. Reuse compatible local entities where possible; otherwise rank compatible
   catalog prototypes by lexical name similarity. Keep target character names
   and record source identity separately. Scores are similarity scores, **not
   calibrated probabilities**. Near ties and weak matches are unresolved.
4. Follow dependencies recursively with cycle detection and instance memoization.
   For example, the kite's repair operation requests its repair tool; the
   library artist requests paper, a pencil, and an atlas.
5. Instantiate local copies and log relocations, defaults, capability additions,
   discarded source context, dependency reasons, and alternative matches.
6. Validate the attached local lines and execute only currently legal events.

The blank input world has no entities. The setting is constructed from explicit
line context; the sky is constructed from the flight destination requirement.
New ordinary people or unknown magical objects are not synthesized. A name such
as `Merlinus` stays unresolved until an appropriate prototype/behavior exists.

## Where the knowledge comes from

| Donor | Retrieved prototypes | Reviewed export semantics |
|---|---|---|
| Library | Mina, paper, pencil, moon atlas | Artist capability and drawing-material links; copying the atlas's moon image onto blank paper |
| Kite | Sam, kite, tape, string | Help capability; kite repair-tool/tether links; torn-to-repaired change and restricted flight |
| Music | Nia, little drum | Drumming capability and instrument link; performance/sound state |

Entity nouns, types, material affordances, initial object states and concept
magnitudes come from the current donor setup functions at seed 1. The catalog
covers all entities in these three setups; the experiment retrieves only ten.
Export profiles explicitly add the capability names and dependency links missing
from the original packs. These additions are authored knowledge, not facts
inferred from names or learned by attention.

The operation ports are narrower than the complete source story kernels:

- Repair accepts a local accessible torn kite and accessible repair tape.
- Flight needs an embedded kite physics marker, repaired non-fragile flyable
  kite, held string, local airspace and explicit wind. Fragile flight blocks;
  the source's failed-flight branch is not ported here.
- Drawing requires held blank paper, a drawing pencil and an atlas carrying a
  moon picture. The paper receives a `moon_drawing` state.
- Drumming requires the musician's capability and the held instrument's physics
  marker. The finale also requires a visible flying kite.

Source scene flags, history, person goals such as `wants_duet`, and relational
properties such as `borrowed` are not copied. This creates new local instances,
not a continuation of donor-world loans or obligations. Persons and loose
objects are placed in the new scene; artist equipment and the drum are placed
with their actors, and the string with its user. These are logged assembly
assumptions, not narrated fetching events. Source geography is not inferred.
Existing entities are not silently moved or granted missing capabilities.

## Carrier-bound execution and limits

Physics remains executable Python in a reviewed port registry. Catalog imports
activate a port's affordances on specific physical carriers; merely enabling a
module does not make every object fly or sound. Removing a required carrier,
capability, tool location or environmental condition blocks commitment. This
moves toward `story.py`'s carrier-bound composition and compatible transitions.
It is not yet the full memeplex algebra.

The replay extension uses overridable operation fields, type constraints and
physical effects, plus an optional `driver_class` in `replay`/`verify`. Original
attached-line behavior remains the default. Catalog histories also record all
bound roles, including reference objects omitted by the coarse Frame schema.

The resolver clones its input. Failed assembly changes nothing in the caller;
failed execution returns its legal prefix and blocking reasons. It does not
repair incomplete input by inventing new operators or prerequisite events.
Explicitly bound local actors without catalog provenance may need their object
roles supplied explicitly: matching a name does not prove an ownership link.

Word attention reranks existing grammatical support after assembly. It does not
retrieve prototypes or create physics. Base `World.facts_for_attention` still
assumes the older scenario roles; this experiment uses word heads, not that
scenario-specific event-attention interface.

Narrative limitation: the drawing is a side activity, rather than a causal part
of fixing/flying the kite. The result demonstrates cross-world assembly and
execution, not automatic plot invention, learned analogies, or established
quality gains. The next useful extension is explicit alternatives for bundles
and physical explanations, followed by goal-driven selection of event lines.
