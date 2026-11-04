# Greenhouse Progress

## Round 1: reference complete

Reference prose saved first in reference_story.md. Seed ingredients: 822263077,
allotment greenhouse, waxed paper parcel, winning back a friend's trust.
Inventory and executable local plays follow next. No shared files changed.

## Round 1: simulator complete

Nineteen executable scenes, twenty inventory mappings, six validated parameters,
four optional encounters, three outcome families. Atomic runtime transitions,
bounded exact-length selection, dictionary episodes, exact replay and CLI ready.
Two cross-scene chains: tape availability changes seed carrier and repair image;
honesty/crop survival/readiness changes planting, access and departure.

## Round 1: tests complete

`.venv/bin/python -m unittest storyscenes.mini_adventures.greenhouse.test_world`
passes ten tests, including 200 seeded and 128 parameter-grid routes. The CLI
command with assignment seed and eight scenes also passes. Read six unfiltered
consecutive first draws and four explicitly targeted diagnostic stories.
Found and corrected a shelter/deflection repair-dialogue contradiction; retained
the original first_draws artifacts and added a regression. Corrected samples
are first_draws_v2. See README.md for evidence and limits. No shared proposal,
API use, agents, commits, or writes outside this pack. Ready for parent review.

## Round 2: local simulation and prose revised

Read round_01/GREENHOUSE_REVIEW.md. Reference and all round-1 samples preserved.
Metadata corrected to 997 prose words, twenty inventory entries and nineteen
executable IDs. The failed choice now explicitly considers available tape or
parcel string and chooses a slower pot relay. Parcel shelter changes no plant
state. Two bounded fifteen-minute batches move twelve rooted pots; stress then
partial injury occurs during exposure, not instant wholesale death. Wind snaps
two stems; heat scorches leaves on two living plants. Usable tape remains a real
missed opportunity, checked against a repaired counterfactual.

Wooden-stay location, inspection, seating, support and fastening are recorded.
Timber carries the raised pane; waxed paper is a rain screen or foot padding.
Sowing now visibly waters the pots. Storage shows borrowing/opening or identifies
the already-open tin, in the same order as the local event chain.

## Round 2: regression and sample verification complete

`.venv/bin/python -m unittest storyscenes.mini_adventures.greenhouse.test_world`
passes nineteen tests (200 seeded routes, 128 parameter-grid routes, and targeted
regressions). Independent `review.verify_row` and `check_inventory` pass on all
100 positions from the parent's frozen first-round stories.jsonl. Every path
and outcome category is unchanged: 42 supervised trials, 40 separations, 18 joint
care. Current scenes in that batch run 47-68 words. These are mechanical checks,
not literary grades. Read seeds 0/1 at both lengths in full, all eight
weather/tape/damp repair-settlement variants, and the no-tape failure cases.

New round_02_samples artifacts preserve the revised draws and explicitly targeted
variants without overwriting previous samples. Byte equality against the frozen
reference was confirmed. README.md details changed rules and remaining limits:
fixed spine, fixed mistaken choice policy, coarse damage timing, no long-term
plant recovery or diversity claim. No APIs, commits, agents, shared edits or
library proposals. Ready for parent round-2 review.

Final integration check:
`.venv/bin/python -m unittest storyscenes.mini_adventures.greenhouse.test_world storyscenes.mini_adventures.test_review`
passes all twenty-nine tests. Revised sample evidence contains four unfiltered
first draws and sixteen explicitly targeted configurations. Prior samples and
reference hashes were checked again after artifact generation. Changed source
paths: world.py, prose.py, test_world.py, scene_inventory.json, README.md and this
PROGRESS.md; added only round_02_samples/ generated evidence inside ownership.

## Round 3: attribution and ordinary transfers revised

Read round_02/REVIEW.md and BOARD.md. The shelter proposal explicitly belongs
to Mara. Ivo joins in a separate guarded event after her decision, and the prose
shows his participation. Store and joint-ending replies also name speakers.
Tea now uncaps, pours, consumes both half-cup servings, and recaps; cups no longer
remain filled after the characters drink. An invariant conserves the two
servings and rejects spontaneous refills. The ordinary-action audit also found
Ivo's exit occurring after the door closed. Joint/trial departures now move
both people through the open door before closing it; separation leaves Ivo inside.
Tin opening/custody, empty paper placement, watering and the spare key were
checked without adding state for every incidental gesture.

## Round 3: recipes, tests and reading complete

README.md includes explicit diagnostic parameter recipes for all three outcomes
and an authoring note limiting the future shared-helper replacement to action
application/trace infrastructure. The new helper was neither edited nor adopted;
round 4 waits for parent release. Tests check each documented recipe at both
lengths. New targeted checks cover speaker/choice ownership, Ivo's participation,
tea conservation/consumption/omission, atomic illegal refill, and exit ordering.

`.venv/bin/python -m unittest storyscenes.mini_adventures.greenhouse.test_world storyscenes.mini_adventures.test_review`
passes thirty-four tests (twenty-four pack, ten shared-review). Existing 200
seeded and 128 parameter-grid routes remain green. Independent verify_row plus
inventory validation pass all 100 frozen round-2 positions, with the same paths
and outcome categories: 42 supervised, 40 apart, 18 joint-care. All eleven tea
stories end with empty cups and two servings consumed. Current scenes in those
positions run 47-73 words. These are mechanical results, not literary grades.

Read all eight full generated stories at seeds 0/1/3/6 and both lengths after
revision. New round_03_samples contains those fixed review draws, labeled
diagnostic recipes, same-position summary and preservation hashes. Reference
byte equality against the frozen round-2 source was confirmed; prior samples
remain untouched. Changes stay in world.py, prose.py, test_world.py, inventory,
README.md, LIBRARY_PROPOSALS.md, this progress lane and new generated evidence.
No API calls, commits, agents, shared files or sampling-distribution changes.
Fixed spine and coarse plant timing remain known limits. Ready for parent review.

## Round 4: shared helper adopted and release checks complete

Read round_03/REVIEW.md and BOARD.md. Parent-approved shared helper is now the
base of world.LocalPlay. The adapter only supplies greenhouse actors and validate;
its inherited act replaces the duplicated transition/diff/commit implementation.
The local relay method, guards, scene execution, renderer, parameters and search
are unchanged. No shared-helper files were edited.

Added focused tests for inherited delegation through the shared transition,
correct actors and event schema, rejection preserving an existing trace, and
invalid initial-state rejection without mutating caller state.

`.venv/bin/python -m unittest storyscenes.mini_adventures.greenhouse.test_world storyscenes.mini_adventures.test_local_play storyscenes.mini_adventures.test_review`
passes all 45 tests (26 pack, nine helper, ten review). Exact comparison against
all 100 frozen round-3 rows passes for complete generate dictionaries using saved
parameters and again using seed-sampled parameters. All 100 serialized paths
replay to exactly the saved episodes. Independent verify_row/check_inventory
also pass. No migration defect or prose/semantic adjustment was required.

README.md documents the now-available minimal action API and subclass boundary.
round_04_verification.json records equality counts, frozen-input/helper hashes
and preservation evidence. Reference, prose and inventory bytes equal round 3;
historical sample hashes remain intact. No old artifacts were overwritten and
no new story batch was generated for export. Held-out seeds 1000-1049 were not
sampled; parent retains held-out/full-suite checks. Only world.py, test_world.py,
README.md, LIBRARY_PROPOSALS.md, this lane and the new verification report changed.
No API calls, agents, commits or writes outside ownership. Ready for release review.
