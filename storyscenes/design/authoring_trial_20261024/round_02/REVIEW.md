# Round 2 Parent Review And Round 3 Tasks

Both matched batches again pass 100/100 independent trace/replay checks.
Read seeds 0/1 at both lengths and the first remaining outcome examples
(bakery 6 and 42; greenhouse 3 and 6) in full, with the changed code.

| Pack | Exact texts | Outcomes | Pooled XZ ratio |
| --- | ---: | --- | ---: |
| Bakery | 73 | 89 postponed, 8 surprise suppers, 3 shared suppers | 1.83% |
| Greenhouse | 45 | 42 supervised, 40 apart, 18 joint-care | 1.80% |

The reported round-1 defects are materially improved: usable light is reserved,
the van constraint no longer disappears, future baking is conditional, crop
damage follows a visible attempt over elapsed time, and the wrapping is not a
magic structural support. Important limits remain: fixed spines, narrow outcome
families, and very high compressibility. More distinct strings are not evidence
of more distinct narratives. Bakery's revised constraints expose strong failure
skew; do not hide it with filtering or change probabilities merely to improve a
headline number.

## Bakery: Round 3

1. Contribute one genuinely shared utility: both packs duplicate atomic action
   application and trace recording. You additionally own
   `storyscenes/mini_adventures/local_play.py` and `test_local_play.py` for this
   round. Keep the API tiny: `LocalPlay(state, *, actors, validate)` with
   `act(name, requires=None, **changes)`, `.state`, and `.events`. Reuse
   `runtime.transition`, construct its dataclasses with keywords, validate both
   initial and candidate states, and commit state/events only after success.
   Deep-copy mutable state/event payloads. Preconditions and invariant failures
   must leave both state and events unchanged; reject no-ops. Do not add a
   planner, story rules, or actor-specific behavior to this helper.
2. Adapt only bakery to it now. Preserve replay and all existing state rules;
   test nested alias isolation, invalid initial states, rejected conditions,
   rejected invariant changes, no-ops, and a valid trace. Greenhouse will adopt
   the stable API in round 4, not concurrently edit it.
3. Read successful endings aloud: "usable lantern" and "Now it's returned"
   sound like audit labels. Keep the enacted checks, but make the short final
   exchange sound like these characters. Do not add unsupported actions.
4. Document an explicit parameter recipe for each outcome in the pack README,
   labeled diagnostic rather than first-draw samples. Preserve outcome skew.
   Run tests; report the shared API and changed paths. No prior batches edited.

## Greenhouse: Round 3

1. Attribute the mistaken-choice reply. Current shelter text has Ivo propose
   tape/string immediately followed by "Moving them will be quicker" without
   a speaker change. The local state attributes the proposal to Mara; prose
   should make that clear and Ivo's participation understandable.
2. Audit the small everyday state transfers, not just dramatic ones. For example,
   tea is poured and explicitly drunk, but `cups.filled` remains true forever.
   Record consumption and any other concrete end-state contradictions you find;
   do not simulate every incidental gesture. Add focused tests for what changes.
3. Add explicit, labeled parameter recipes for all outcomes and an authoring note
   identifying which operations the shared atomic-action helper can replace.
   Do not write the shared file while the bakery worker owns it. Preserve tests,
   reference and old samples. Read the changed full stories before reporting.

## Round 4 Release Gate

Use the stable shared helper in both packs. Freeze new matched batches and
held-out seeds 1000-1049 at both lengths. Verify from independent source trees;
read held-out complete stories; run the complete repository StoryScenes suite.
Do not silently promote this supervised trial into an unattended or scalable
dataset-generation claim. This schedules four rounds total, within the requested
three-to-five range.
