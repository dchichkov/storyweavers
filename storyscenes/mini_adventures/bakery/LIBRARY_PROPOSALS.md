# Round 1

No shared-library changes requested. The pack uses `runtime.transition` for
every committed local action. Carrying, baking time, wick repair, and lamp fuel
are deliberately scenario-local, not proposed as universal physics.

## Round 3 Contribution: Stable Atomic Recorder

Implemented the parent-requested `storyscenes/mini_adventures/local_play.py`,
with `test_local_play.py`. API: `LocalPlay(state, *, actors, validate)`,
`act(name, requires=None, **changes)`, `.state`, `.events`. Bakery now consumes
it through its existing scenario-specific subclass. Preconditions, invariants,
and no-ops reject without changing state or events; nested payloads are detached.

Concrete second consumer: greenhouse's duplicate atomic action/trace recorder
can be replaced in Round 4 while retaining its own movement and world rules.
Regression gate: nine shared helper tests plus bakery's exact replay and
state/event equality against all 100 frozen Round 2 positions. Shared tests
include initial/candidate validation and mutable alias isolation in both
directions, including validator-held snapshots.

No additional shared changes requested. Parent snapshots must include the new
`mini_adventures/local_play.py` dependency. Greenhouse files were not modified
or adopted concurrently. API is ready for the parent to confirm as stable.
