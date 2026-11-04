# The Book Between Returns

An offline, standard-library-only mini-adventure. Lio borrows a neighbourhood-library book trolley and promises Nia he will find her missing picture book before closing. The executable pack uses local atomic actions, guarded scenes, and a bounded seeded route search. There is no runtime language model, network access, or non-standard dependency.

## Run it

From the repository root:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 41 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py .
```

The command prints the story prose. To supply explicit parameters, save a JSON object such as the following and pass its path with `--params`:

```json
{"closing_minutes":14,"book_location":"returns_cart","catalog_current":true,"ladder_stable":true,"staff_available":true,"trolley_wheel_ok":true}
```

`count` is exactly seven or eight scenes. The generated row contains the seed, validated parameters, scene path, per-scene events and states, joined story, final state, and bounded-search attempt count. `replay(params, path)` re-enacts the supplied compatible path and reproduces its state, event traces, and prose.

## Explicit ending recipes

These recipes intentionally use `replay` so the selected ending is reproducible rather than relying on a seed happening to choose a particular route.

```python
from storyscenes.mini_adventures.kite.world import Parameters, replay

success = Parameters(closing_minutes=14, book_location='returns_cart',
    catalog_current=True, ladder_stable=True, staff_available=True,
    trolley_wheel_ok=True)
success_path = ('promise', 'catalog', 'returns_search', 'bookmark_vignette',
    'window_vignette', 'friend_vignette', 'ending_found')
print(replay(success, success_path)[-1]['after']['story.outcome'])
# promise_kept

failure = Parameters(closing_minutes=14, book_location='top_shelf',
    catalog_current=True, ladder_stable=False, staff_available=False,
    trolley_wheel_ok=False)
failure_path = ('promise', 'catalog', 'librarian', 'returns_search',
    'window_vignette', 'bookmark_vignette', 'ending_miss')
print(replay(failure, failure_path)[-1]['after']['story.outcome'])
# promise_not_kept_honestly
```

For an eight-scene version, add `shelf_vignette` before the ending in the success recipe, and `friend_vignette` before the ending in the failure recipe. The failure route exhausts the places the children can safely check; it does not pretend the book was found. The trolley and any shared bookmark are returned in either ending.

## State and scene design

Six validated parameters affect the adventure: closing time, the book’s actual spot, catalogue accuracy, ladder stability, staff availability, and trolley-wheel condition. The catalogue can point to an outdated shelf. A high-shelf search requires an available staff member and a stable ladder. A squeaky trolley costs time. Two optional relationship vignettes and two further optional characterization/search encounters have persistent, enacted effects: Nia’s bookmark can travel into the recovered book, and Nia’s picture-label knowledge can unlock a low-shelf search. Omitted scenes do not execute their actions.

Every local action goes through `storyscenes.mini_adventures.local_play.LocalPlay`. Its copied state, guarded `requires` mappings, validation, and detached events keep rejected or speculative actions from changing the caller. The route search is finite, seed-deterministic, and explores only compatible scene compositions; it commits and narrates only the chosen route. Book location, bookmark custody, trolley ownership/use, and the promise outcome are validated throughout.

The inventory contains twenty reference encounters but maps consolidated encounters to twelve executable IDs. It describes the grouping rather than claiming every reference beat has a separate implementation.

## Limitations and verification status

The library is a small authored model, not a catalog integration or full building simulation. It has fixed characters and a small set of possible book locations. The prose is deliberately scene-sized and parameter-conditioned, not a claim of unlimited semantic diversity. A successful search requires the actual location to be reachable before closing; the failure ending is complete but cannot return the missing book. Ladder safety is conservative: a child never climbs without staff supervision.

**Execution status:** no execution tools were available for this single-response run. I did not run the unit tests, `check_pack.py`, the CLI, or sample-story inspection, and I do not claim that they passed. The tests are included for the parent harness to run against the untouched pack. The reference story is intended to contain 900–1100 prose words, excluding its heading; that word count was not executed here.
