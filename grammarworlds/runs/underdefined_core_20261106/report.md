# Underdefined world: what the current shared core can generate

Input: Ada and Omar are in a garden. Ada holds a torn book and wants to repair
it. Tape is on a reachable bench in the same garden. Both people can carry
objects and offer help; Omar is willing to help. Ada has carrier-bound Desire,
Fear and Trust magnitudes; Omar has Care and Trust. There is no story text,
event sequence, repair procedure, ending, or reference-story retrieval.

## Literal current-runtime baseline

The existing storytelling forest builder, supplied with this world and an empty
event pack, produces **no text** and raises `ValueError: no available event`.
This happens with event attention both off and on. Word attention is downstream
of forest construction and is never reached.

The shared layer has grammatical constructors and reusable effect helpers, but
no automatic world-to-event proposer. The ordinary runtime also dispatches
scene plans by one of seven known scenario names. Its existing story packs
normally provide both legal events and their semantic scene bindings.

## Separately added unordered adapter

To inspect the reusable components beyond that empty baseline, the experiment
adds an isolated role-binding adapter in `grammarworlds/underdefined_probe.py`.
**The following samples are from that new adapter, not the unmodified runtime.**
Production code and weights remain byte-for-byte unchanged.

The adapter supplies four existing shared scene families with arguments:

- Express the input goal using `say_intent`.
- Offer help between co-located people with an input `can_help` capability.
- Fetch a portable object from a reachable surface in the same location, using
  `fetch_scene` and a shared physical location change.
- Transfer a held object between co-located people using `can_transfer`, the
  shared transfer scene, and a physical location change.

These bindings are enumerated again after each event. They have equal prior
mass **per binding**, not per family. There is no prescribed ordering, goal
reward, repetition penalty, invented repair effect, ending rule, or successful
sample filtering. Statements of intent are permitted to repeat. Fetching and
transfers update the persistent world through the shared validated commit
protocol; offers do not secretly repair anything.

Rendering and word sampling reuse the expanded typed grammar, finite forest,
and existing manual symbolic heads. No event-level attention preferences were
invented for the new bindings. This comparison isolates existing **word heads**
off/on; it is not a test of a newly authored event planner.

## Actual output

Seed 0, heads on, eight sampled events, no prose repair:

> Omar said, “I can help you.” Ada gave the book to Omar. Ada told Omar, “I could help you.” Ada said, “I can help you.” Omar said, “Let me help you.” He gave the book to Ada. Ada fetched the tape from the bench. Omar told Ada, “I can help you.”

This output is identical with heads off at seed 0. [All preselected samples](samples.md)
show seeds 0–4, off/on, without rerolls. Full traces for seeds 0–19 are saved in
`traces.jsonl.gz`.

## Measurements

Twenty fixed seeds × heads off/on × an eight-event cap = 40 fragments / 320
events. The input world is identical across seeds. The cap is a measurement
boundary, not a generated ending.

| Measure | Heads off | Heads on |
|---|---:|---:|
| Fragments | 20 | 20 |
| Distinct texts | 20 | 20 |
| Token steps with choices | 592 / 1,650 (35.88%) | 592 / 1,650 (35.88%) |
| Steps with at least four choices | 161 | 161 |
| Word distributions changed by heads | 0 | 82 |
| Goals reached | 0 | 0 |

Heads change **one of twenty** paired texts. P001, P002 and P059 activate; the
state receiver can affect wording. P023 has no guard-approved instrument-use
event to attend to: the tape's existence alone does not authorize repair.

The higher choice frequency is not directly comparable to the earlier 10.82%
on complete stories: this is a different world and an intentionally unstructured
candidate set. It demonstrates that more choice can coexist with worse narrative
organization.

Zero goal completions are **structurally inevitable here**, not an empirical
failure rate for a capable repair planner. The shared families expose fetching
and transfer, but no general repair operator with prerequisites/effects.
The word `repair` is grammatical inside a wish; that does not make repair an
executable action. Attention cannot assign probability to an absent event.

## Interpretation and checks

The local output is grammatical and object possession is consistent, but it
repeats offers, restates goals and passes objects back and forth. Missing
beginning/turn/ending and event-log prose are expected quality defects, not
accepted complete-story behavior. There is no independent literary judge or
new QA generator in this experiment.

All 40 fragments replay exactly. All word distributions are normalized and
positive; zero head strength reproduces the heads-off sample and final world.
960 carrier-removal/forged-actor guard interventions and two extra checks for
reachability/co-location pass. The prior shared-core evaluation's production
source hashes are unchanged. The 18 shared-core, continuation and story-head
regression tests also pass. Results are in `verification.json`.

This gives a useful starting point for event-chain transfer: the missing pieces
are a reusable set of executable actions and a policy that connects those
actions to the goal. Retrieved chains could rank and organize those actions;
they cannot substitute for missing physical semantics.

Reproduce with:

```sh
.venv/bin/python -m grammarworlds.underdefined_probe \
  --out /tmp/underdefined-core --count 20 --steps 8
```

Input data, summary, source hashes, probe-source snapshot, full traces and
preselected raw samples are stored alongside this report.
