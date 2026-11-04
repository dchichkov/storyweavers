# The Gull Was Not the Cove

An offline, standard-library-only mini-adventure pack for the seaside path. The siblings borrow Aunt June’s map, mistake a ferry-landing marker for their picnic landmark, correct the mistake, and finish a sheltered picnic. The map is returned with useful information for the next traveler.

## Run

From the repository root:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py .
```

The first command prints prose. Every generated story has exactly seven or eight compatible scenes. Seven-scene routes contain the seven core scenes; an eight-scene route adds exactly one optional vignette. Search is seeded, bounded, and speculative branches do not alter the returned state or event trace.

To override parameters, provide a JSON object file with `--params`. For example, a file containing `{"tide":"low","wind":"gusty","map_rotated":true,"legend_faded":true}` can be used with:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 17 --scenes 7 --params /tmp/cove.json
```

### Explicit ending recipes

The routes and endings are tide-guarded. These recipes work with either scene count and any valid settings for the other fields:

- **Crescent Cove ending:** `Parameters(tide='low', wind='calm', map_rotated=False, legend_faded=False)`. The low strand is available, and the final scene is `ending_cove`.
- **Harbor-awning ending:** `Parameters(tide='rising', wind='gusty', map_rotated=True, legend_faded=True)`. The children choose the safe bluff route; the final scene is `ending_harbor`.

For direct Python use:

```python
from storyscenes.mini_adventures.kite.world import Parameters, generate

cove = generate(17, count=7, params=Parameters(tide='low'))
harbor = generate(17, count=8, params=Parameters(tide='rising', wind='gusty'))
print(cove['path'][-1], harbor['path'][-1])
```

Names may also be set with `older_name` and `younger_name`; names are personalization, not story diversity. The four consequential environmental parameters are `tide` (`low` or `rising`), `wind` (`calm` or `gusty`), `map_rotated` (boolean), and `legend_faded` (boolean). Tide controls which route and ending are possible; wind changes the blanket-securing action; orientation and legend condition change the map-reading actions.

## Design and limits

The executable scene pool has eleven IDs: seven core beats including two mutually exclusive endings, plus three optional vignettes. The low-tide tidepool pause, fisher exchange, and shelter-side seat choice are independently guarded; the exact-length selector admits only one vignette in an eight-scene story and none in a seven-scene story. Local actions use `storyscenes.mini_adventures.local_play.LocalPlay`, so requirements and non-no-op changes are recorded atomically. State validation checks map custody and location, the route/tide relationship, picnic completion, blanket security, and ending completeness.

The two endings differ in actual destination and route, not merely names or wording. At low tide the children can reach the mapped cove. At rising tide they choose the bluff and picnic beneath the harbor awning instead. The map is returned in both endings with a correction that reflects the route taken. The story does not simulate detailed tides, weather, walking time, food quantities, or every incidental handoff; those are intentionally small scenario abstractions. The fisher and Aunt June are represented only to the extent needed by these encounters. No runtime LLM, network access, shared-file changes, or non-standard-library dependency is used.

`reference_story.md` was authored as the story-first reference. Its heading is separate from the prose word-count target of 900–1100 words. The pack includes the heading as the only Markdown heading so the supplied integration check can count the prose independently.

## Tests and execution status

Tests are provided in `test_world.py`, including both lengths over 100 seeds, exact replay, invalid parameters, failed-action atomicity, optional-scene omission, object continuity, and tide, wind, map-orientation, legend, and fisher counterfactuals. The supplied read-only integration check can be run with the command above.

**Tests were not executed for this response:** no execution tools were available. No test result or integration-check success is claimed.