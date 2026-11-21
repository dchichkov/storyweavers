# Replaying local lines in the underdefined adapter

The underdefined-world adapter now accepts explicit local event lines with typed
role bindings. A small scheduler offers legal next events from those lines to
the existing grammar and word heads. It does not select an entire global story
or copy source prose/state diffs into the target world.

```sh
.venv/bin/python -m grammarworlds.underdefined_probe \
  --line grammarworlds/runs/event_line_replay_20261106/inputs/cooperative.json \
  --out /tmp/cooperative-replay --count 20 --steps 32
```

Without `--line`, the earlier unordered experiment is unchanged. A line input
contains `world`, `template`, and `bindings`; the saved examples are complete,
editable inputs. File input starts from an initial world. The Python replay API
also supports attaching a line to an existing in-memory world/history.

## What a line specifies

The template declares typed roles and an event dictionary. Each event refers to
roles, not character names. Each attached entity has an ordered list of event
IDs. There is no separate global ordering. For the cooperative example:

```text
owner (Ada):   wish → offer → hand_in → hand_out
worker (Omar): fetch → offer → hand_in → patch → hand_out
item (book):   wish → hand_in → patch → hand_out
tool (tape):   fetch → patch
```

`wish` and `fetch` may occur in either order. `hand_in` is one shared event,
`transfer(owner, item, worker)`, referenced by three lines. It is offered only
when all participating attached lines are ready for that ID and its physical
guards pass. One commit advances all three cursors exactly once.

The loader rejects missing bindings, incompatible role types, aliased roles,
unknown operations, unused events, missing shared-event references and ordering
cycles. Every event involving an attached role must appear on that role's line.
Unattached entities can participate through explicit bindings and physical
guards; they do not acquire an inferred local plan.

## Supported operations

| Operation | Guard/effect summary |
|---|---|
| `intent(actor, item)` | Express the supplied repair goal for a torn item; no physical change |
| `offer(actor, listener)` | Co-located people and explicit `can_help`; no implied repair |
| `fetch(actor, item, source)` | Portable item on the bound reachable surface in the same location; moves item to actor |
| `transfer(actor, item, recipient)` | Held portable object, co-located people able to carry; moves item to recipient |
| `patch_paper(actor, item, tool)` | Paper material, torn item, patching capability, repair tool and item both held by actor; replaces `torn` with `repaired` |

Fetching/transfers reuse the existing shared physical helpers. `patch_paper` is
the new portable physical operation. It is deliberately narrower than a generic
repair ability. It models a patchable paper tear; tape consumption, structural
testing and arbitrary damage types are not modeled. Completion of the two-step
repair line does not imply the source kite would subsequently fly successfully.

The original bare world does not declare paper material or patching capability.
`paper_world()` explicitly adds `book.properties: paper` and
`ada/omar.properties: can_patch_paper`. The original fixture still blocks repair.
These added facts are assumptions of the successful experiment, not inferred
from the nouns or obtained automatically from attention.

## Importing an annotated source segment

`project_source(graph, focus, event_ids)` currently has two reviewed ports:
`kite:fetch_tape` and `kite:mend`. It checks the observed physical effects, derives
the moved tool from the annotations, and emits the portable operations above.
This matters because the coarse fetch frame names the kite as its patient,
whereas the actual moved entity is the tape.

The projected template records source event IDs, source text hash, role origins,
and source contracts/dependencies that were not transferred. Target guards
replace scenario-specific source guards such as meadow location and `prepared`
flags. Source attributes are retained as provenance; live attributes are
[regenerated for target roles](ATTRIBUTE_TRANSFER.md). Motives, endings and QA
text are not copied.
Unsupported events or unexpected extra source effects fail explicitly.

```python
from grammarworlds.event_line_replay import project_source, paper_world, replay

template = project_source(graph, "hero", selected_event_ids)
result = replay(paper_world(), template, {
    "worker": "ada", "item": "book", "tool": "tape", "supply": "bench",
})
```

`cooperative(template)` is an explicitly supplied example extension: a wish,
help offer and two shared handoffs around the imported fetch/patch segment.
Those extra events are authored input, not automatic prerequisite inference.

`project_source` now obtains its correspondences from the
[event mapping grammar bank](EVENT_MAPPING.md), using the paper profile for
compatibility. The bank's target-grounded entry point can infer role bindings
and return a distribution over alternative complete mappings.

Arbitrary supplied arrangements of the **supported operations** can replay,
including lines unrelated to repair such as a single help offer. This is not a
general compiler for all 119 annotated event kinds.

## Sampling, progress and failure

Each legal ready event starts with equal mass. Existing expanded grammar and
manual word heads sample its wording; final text resolves to a frame before
commitment. Heads cannot bypass guards or advance a blocked line. This is a
guarded partial-order replay, not learned event-line attention or automatic
retrieval of a suitable line.

Replay clones the input world. It returns `complete`, `blocked`, or `limit`,
local cursors, explicit blocking reasons, full world history and word traces.
`complete` means all supplied local lines finished, not that an arbitrary goal
was achieved or a whole story ended. Completed prefixes remain in the returned
clone when a later event blocks; the failed event changes neither state nor
cursors. The caller's world is unchanged. Verification reconstructs the replay
and preserves any existing history prefix.

This moves toward carrier-bound local story composition: people and objects
attach to lines, and joint physical events synchronize them. Broader event
ports, automatic line retrieval/binding, inferred missing steps, and quality
evaluation against an unguided controller with the same action support remain
future work. See the [measured experiment](runs/event_line_replay_20261106/report.md).
