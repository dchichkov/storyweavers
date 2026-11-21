# Event correspondence grammar bank

The source-event importer now obtains correspondences from
[`mapping_bank/core.json`](mapping_bank/core.json), interpreted by
[`event_mapping.py`](event_mapping.py). Source matching, role correspondence,
target requirements, target operations and prior weights are rule data. There
is no scenario-specific fetch/mend branch in `project_source` anymore.

The original core has three rules; default loading now adds fourteen rules from
[`mapping_bank/story_tokens.json`](mapping_bank/story_tokens.json) and six typed
movement rules from [`mapping_bank/seed_stories.json`](mapping_bank/seed_stories.json),
for 23 rules total. The latter expose fetch, put and handoff events from the
16 new seed worlds, while still requiring an exact complete source entity diff. The
[intact-story memory layer](STORY_MEMORY.md) exposes their source annotations
without splitting the story text. The original three are:

| Rule | Source evidence | Target construction | Prior weight |
|---|---|---|---:|
| `fetch.portable_tool` | A `fetch_tape` event moves one tool from a supply to its actor, with no other entity changes. | `fetch(actor, item, source)` | 1 |
| `repair.paper` | A `mend` event changes exactly torn → repaired on its patient. | `patch_paper(actor, item, tool)` | 2 |
| `repair.kite` | The same repair evidence. | `mend_kite(actor, item, tool)` | 1 |

The two repair rules compete when both can bind to compatible carriers. The
original core rules do not use the source story's identity or English sentence
as matching criteria. New source-specific ports can declare `source.scenarios`.
Source kind labels still need an authored match in `source.kinds`; this is not
an English parser or automatic discovery of equivalent meanings.

## Use

```python
from grammarworlds.event_mapping import mapping_distribution, generate_mapped

# graph is an entity-event-lines-v1 export; ids select an ordered actor segment.
distribution = mapping_distribution(graph, "hero", ids, receiving_world)
for candidate in distribution["candidates"]:
    print(candidate["rules"], candidate["bindings"], candidate["probability"])

result, attachment = generate_mapped(
    graph, "hero", ids, receiving_world, seed=7,
    # Optional partial binding: other roles are inferred.
    bindings={"worker": "ada"},
    # Optional context/attention receiver factors; omitted rules get factor 1.
    rule_factors={"repair.kite": 4},
)
```

Supply `bank=load_bank(path)` to use another JSON bank. Adding a new source label,
role correspondence, or alternative targeting an existing operation requires
rule data only. A genuinely new physical operation still needs a guarded kernel
and typed realization; rule data cannot introduce arbitrary executable effects.

`event_line_replay.project_source()` is a compatibility entry point using the
unambiguous `paper` profile. It returns an unbound template as before; its normal
replay reports blocked execution if supplied bindings are unsuitable. The new
`mapping_distribution` checks feasibility before sampling a target attachment.

## Matching and composition

Each rule has `source.kinds`, `source.bind` paths and `source.equals` patterns.
Paths such as `frame.actor` and `movements.0.item` extract source identities.
`$worker` references a bound source role inside a pattern. `changes` normalizes
entity effects: state differences become sorted `add`/`remove` sets; other
concept changes become individual `memes.NAME` deltas; other fields retain
before/after values. Exact comparison of the complete change list
rejects unreviewed extra effects. Unchanged source states are not transfer facts.

Optional `source.role_kinds` checks source carrier types, while `source.absent`
requires evidence paths to be absent (for example, a place-fetch is not a loan
from a person). `source_entities` paths can bind a known contextual carrier,
such as the atlas that supplies a drawing reference. Source and target kinds may
differ when the rule explicitly declares that correspondence.

`target.event` names an existing typed operation and maps its slots to the
corresponding roles. `target.roles` supplies required kinds and properties.
Validation checks signatures, kinds, variables and positive finite weights.

The interpreter composes one matching rule per selected event. Shared role names
must refer to the same source entity throughout the segment; conflicting matches
are rejected. It then enumerates compatible existing target carriers, keeping
distinct roles distinct. Full target programs execute on a clone to check state,
location, ownership and capabilities at the appropriate step. Thus a tool may
start on a bench and become available to the repair event after the fetch.

Every participating role gets a local event line, including supply roles. Source
event IDs, rule IDs, source profiles and untransferred contracts remain in the
trace. Target attributes still follow the [attribute transfer policy](ATTRIBUTE_TRANSFER.md):
current carrier state is authoritative, grammar regenerates linguistic features,
and proposed effects do not assert an event has already occurred.

## Distribution and execution

For each feasible complete mapping:

```text
score = product(rule prior weights) × product(context rule factors)
probability = score / sum(scores of all feasible complete mappings)
```

Bindings have equal weight within a rule derivation. Consequently a derivation
with more feasible bindings receives more total mass. Distinct derivations stay
separate even when they produce identical words. These weights are authored
preferences, not calibrated probabilities. Context factors cannot bypass guards;
there is no new learned attention head in this change.

One complete mapping is sampled before local word generation. Its candidate
distribution and rejection reasons are retained under
`source.mapping_distribution`. The selected program then uses the existing
joint annotated-token sampler, heads, guarded commits and replay verification.
The input world, source graph and bank remain unchanged.

## Deliberate boundaries

- Matching consumes replay-grounded event evidence, including references from
  the new annotated token-memory documents; it does not parse raw prose.
  Pool recipe retrieval and catalog instantiation
  keep their existing paths; they have not all been converted into this bank.
- Source segments are ordered and require the selected focal actor. One source
  event maps to one target operation; event insertion, deletion, group roles,
  and arbitrary many-to-many factoring are not implemented.
- Binding inference reuses existing target entities. Catalog imports can prepare
  a world first, but the mapper itself creates no entities or capabilities.
- Candidate expansion is bounded (default 256); exceeding it raises an explicit
  error, rather than silently truncating and distorting the distribution.
- Source world flags, motives, global dependencies and prose do not become
  target facts. A complete imported segment need not be a complete story.

This moves toward the memeplex north star by binding reused meanings to physical
carriers and letting compatible persistent state govern execution. It does not
implement the full story algebra or claim a new prose-quality gain.

See the [60-run experiment and samples](runs/event_mapping_20261106/report.md).

```sh
.venv/bin/python grammarworlds/runs/event_mapping_20261106/run.py
.venv/bin/python -m unittest grammarworlds.test_event_mapping -q
```

## A broader alternative: import the source mechanics

[Native transfer](NATIVE_TRANSFER.md) adds a second path for events outside these
23 strict rules. It brings source carriers and guarded mechanics with a referenced
annotated event, rebinds people/objects, and executes that source program against
the receiving state. The twenty-world audit exercises 249 kinds, compared with
49 source kinds exposed by strict rules in the same corpus. This broader number
includes supporting prefixes and imported context; it does not mean 249 mutually
interchangeable, context-free receiver operations.
