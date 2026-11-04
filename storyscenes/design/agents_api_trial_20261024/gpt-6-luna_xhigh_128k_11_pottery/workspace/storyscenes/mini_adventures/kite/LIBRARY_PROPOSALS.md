# Concrete library proposal

No shared library file was modified. The pack currently uses `LocalPlay.act` with equality-only `requires` mappings, while guards and scenario code separately express thresholds such as a minimum clay reserve.

A small, backward-compatible extension would let `LocalPlay.act` accept an optional tuple of `Condition` objects (or a documented condition mapping) in addition to its existing equality mapping. The helper would evaluate those conditions against the same detached pre-state before calling `runtime.transition`, and would keep the present atomicity guarantee: failed conditions record no event and mutate neither state nor trace. For example, a reusable `Condition('clay.remaining', 'ge', 30)` could represent the repair prerequisite directly.

This is a proposal only. The pack deliberately performs its material threshold in a scene guard and records all successful local mutations through the supplied `LocalPlay`; it does not monkey-patch or replace shared behavior.