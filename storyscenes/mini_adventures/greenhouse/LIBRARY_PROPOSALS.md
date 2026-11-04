# Shared Library Proposals

None required for round 1. The pack calls runtime.transition for every local
operation. Bounded exact-length search, prose and physical rules stay local.
No engine, registry, export or other worker files were edited.

## Round 3: deferred shared-helper migration

The parent assigned bakery ownership of the shared action helper and its tests.
Greenhouse does not edit or adopt it during round 3. Concrete consumer: the
state/event initialization and act method in world.LocalPlay. Those duplicate
atomic transition, candidate validation, state diff and trace recording. The
announced LocalPlay(state, *, actors, validate) API can replace only that generic
portion after parent release in round 4. relay_pots and all tea, weather, custody,
location, scene-selection and narrative logic remain pack-local.

Consumer migration regressions: full parameter grid and exact replay; rejected
conditions/invariants leave state and events unchanged; empty cups cannot be
consumed or refilled without a source; Ivo exits while the door is still open.
No additional shared API is requested.

## Round 4: approved helper adopted

Following parent release, world.LocalPlay now subclasses the shared LocalPlay,
passing actors=("mara", "ivo") and the greenhouse validate callback. Its act
implementation is inherited unchanged. relay_pots and all scenario rules remain
local. No shared files were edited. Twenty-six pack tests and nine helper tests
pass, along with ten shared-review tests. All 100 frozen round-3 full rows and
their saved-path episodes reproduce exactly. No helper migration defect or
further shared API change is proposed. README.md documents the authoring API.
