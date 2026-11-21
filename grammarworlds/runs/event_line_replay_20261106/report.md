# Attached local event-line replay

The underdefined adapter now executes supplied entity-local lines through a
small portable operation vocabulary. The tested source is the annotated kite
story's **fetch tape → mend** segment. Its worker/item/tool/supply roles can bind
to Ada/book/tape/bench or, with explicit handoffs, Omar/book/tape/bench.

## Actual cooperative output

Seed 0, existing manual word heads on, no rerolls or prose repair:

> Ada said, “I want to repair the book.” Omar fetched the tape from the bench. Omar said, “Let me help you.” Ada gave the book to Omar. With the tape, Omar repaired the book. He handed the book to Ada.

Four attached lines generate this fragment:

| Entity | Ordered local events |
|---|---|
| Ada | wish → offer heard → give book → receive book |
| Omar | fetch tape → offer help → receive book → patch → return book |
| Book | wish's object → change holder → become repaired → change holder |
| Tape | fetched → used for patch |

The handoff IDs are shared references, not duplicate transfer operations. One
handoff advances Ada, Omar and the book together. Ada's wish and Omar's fetching
are independently ready and appear in either order across seeds. No global
sentence/event ordering is specified beyond these local orders and joins.

The source supplies the fetch/patch segment. The wish, offer and two handoffs
are an explicitly authored extension for this experiment. They were not inferred
automatically from the underdefined world or retrieved by attention.

## Outcomes

Seeds 0–19, heads off/on, maximum eight events per run:

| Case | Runs | Completed local lines | Book repaired | Result |
|---|---:|---:|---:|---|
| Ada, supported paper-repair fixture | 40 | 40 | 40 | Ada fetches and patches |
| Omar, coordinated handoffs | 40 | 40 | 40 | Book repaired and returned to Ada |
| Omar, no handoff supplied | 40 | 0 | 0 | Stops after fetching: Ada still holds the book |
| Original bare fixture | 40 | 0 | 0 | Stops after fetching: material/capability undeclared |

The solo line has nine distinct texts per 20 seeds and one event order. The
cooperative line has 20 distinct texts and two event orders per 20 seeds, both
with and without heads. Heads alter 12 solo and 45 cooperative word
distributions. These small samples do not establish a quality advantage from
heads. Source-story text is never substituted into the target output.

The successful fixture explicitly adds **paper material** to the book and
**paper-patching capability** to Ada/Omar. The replay layer adds one physical
operation, `patch_paper`, alongside existing intent/offer/fetch/transfer families.
This is not a controlled 0%-to-100% improvement from attention alone: operation
coverage, fixture capabilities and local guidance changed together. An unguided
comparison with identical operation support is still needed to isolate the
benefit of the local-line controller.

## What transfers and what does not

Annotated source effects identify the tool moved by fetching and the item's
`torn → repaired` transition. The source fetch frame's coarse patient is the
kite, so using only that frame would bind the wrong object. The annotations
resolve that ambiguity.

Two reviewed source-event ports translate these meanings into target operations.
The target guards require accessible supplies, co-location, declared materials/
capabilities and held tools/items. Source global flags, scenario-specific guard
conditions, unrelated entity changes, motives, endings and QA answers are not
copied. Their untranslated context is retained in the template's provenance.

Unsupported source events fail explicitly. Even a known mend event is rejected
if its annotated effects unexpectedly include, for example, making the item fly.
The adapter accepts arbitrary supplied orders/compositions of its five supported
operations; it cannot yet replay an arbitrary annotated story line without ports.

## Checks and current limits

- **160 runs / 400 committed events** replay exactly.
- **1,600 guard interventions** reject missing carriers, forged actors and forced
  blocked continuations without changing state or line cursors for those events.
- **116 tests pass** across the existing 104-test suite and 12 new replay tests.
  Coverage includes shared-event single commitment, independently ready actions,
  invalid bindings, missing joins, ordering cycles, reversed prerequisites,
  renamed entity IDs, original baseline preservation and attachment after an
  existing history prefix.
- The earlier storytelling source/weights remain unchanged; the only existing
  adapter change is an opt-in `--line` path. There is no runtime model call.

Blocked runs retain their legal completed prefix in the returned clone. The
caller's world is unchanged. Successful local replay does not mark the whole
world ended or invent an epilogue. These outputs are short task fragments, not
an evaluated collection of complete literary stories; no new QA generator or
independent Luna evaluation was added.

The next useful test is to propose or retrieve a compatible local line instead
of supplying it, using the same operator vocabulary for guided and unguided
conditions. More source-event ports must preserve explicit permission,
obligation, material and resource semantics rather than copying observed diffs.

## Artifacts and reproduction

- [Solo samples](solo/samples.md)
- [Cooperative samples](cooperative/samples.md)
- [Missing-handoff samples](wrong_holder/samples.md)
- [Original-fixture samples](original_fixture/samples.md)
- [Editable cooperative input](inputs/cooperative.json)
- [Adapter/schema guide](../../ATTACHED_LINES.md)

```sh
.venv/bin/python -m grammarworlds.underdefined_probe \
  --line grammarworlds/runs/event_line_replay_20261106/inputs/cooperative.json \
  --out /tmp/local-line-replay --count 20 --steps 8
```

Each case contains the complete input, summary, preselected samples and full
compressed traces. Source snapshots, `manifest.json` and `verification.json`
are stored alongside this report.
