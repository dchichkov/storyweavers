# Library proposal (not implemented)

Consider a small shared `replay_local_events(initial_state, events, validate)` helper for offline auditing of `LocalPlay` traces. It could check each equality precondition, verify every recorded `before` value, apply only recorded `after` values to a detached copy, reject no-op events, and run a validator after each event. Scenario-specific invariants and prose would remain with the pack. This pack performs that audit in its tests; no shared files or APIs were changed.
