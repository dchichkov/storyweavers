# The Two Pegs: museum shadow-exhibit adventure

This offline pack follows Mara and Tavi, who borrow a museum torch to understand why the shadow exhibit does not match its label. The executable world uses the supplied `LocalPlay` action recorder and shared `transition` engine. It makes no API calls and has no non-standard-library dependencies.

## Run it

From the repository root:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 17 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py .
```

The module prints the selected prose. `generate(seed, count=7 or 8, params=...)` returns the path, local event traces, state snapshots, story text, and bounded-search attempt count. `replay(params, path)` reproduces episodes in order. The seven-scene route contains one optional vignette; the eight-scene route contains both. Vignettes have no offstage effects.

## Explicit ending recipes

The parameter dataclass is keyword-only. These complete examples work in Python:

```python
from storyscenes.mini_adventures.kite.world import Parameters, generate

# Readable evidence agrees with the label; leave the tested exhibit ready.
accurate = Parameters(label_target='near_torch', room_ambient=False,
                      torch_charge=3, screen_distance_cm=120, figure_kind='card')
row = generate(0, count=7, params=accurate)
assert row['final_state']['story.outcome'] == 'accurate_demonstration'

# The printed peg is reversed; the children correct it using readable evidence.
corrected = Parameters(label_target='near_screen', room_ambient=False,
                       torch_charge=3, screen_distance_cm=120, figure_kind='card')
row = generate(0, count=8, params=corrected)
assert row['final_state']['story.outcome'] == 'corrected_label'

# A weak torch leaves both readings too faint; they post a truthful limitation note.
honest = Parameters(label_target='near_torch', room_ambient=False,
                    torch_charge=1, screen_distance_cm=120, figure_kind='card')
row = generate(0, count=7, params=honest)
assert row['final_state']['story.outcome'] == 'honest_inconclusive'
```

For the command line, save any parameter overrides as JSON and pass `--params FILE`. For example, a file containing `{"label_target":"near_screen","room_ambient":false,"torch_charge":3,"screen_distance_cm":120,"figure_kind":"card"}` selects the corrected-label conditions. Overrides are merged with the seeded defaults, then fully validated. The three ending recipes above are independent of the seed.

## Parameters and state

Five validated parameters have physical consequences: `label_target` selects the peg named by the printed card; `room_ambient` determines whether the initial screen is washed by daylight; `torch_charge` and `figure_kind` jointly determine whether an outline is readable; and `screen_distance_cm` changes the recorded optical magnification. After the first trial, the children can draw the window shade if necessary. The physical model is deliberately small: a figure 25 cm from the torch produces the larger magnification, while the screen-side peg is 15 cm from the screen. A readable comparison supports the near-torch inference; unreadable evidence does not.

The local plays explicitly record borrowing, switching, reading, moving the figure, optional sketching or visitor reassurance, comparing observations, and returning the torch. State keys preserve custody, locations, measured distances, observations, label knowledge, and the selected ending. Failed actions use `LocalPlay`’s atomic transition and do not mutate the caller. The bounded scene search commits only the chosen path.

## Limitations

The optics and visibility thresholds are scenario rules, not a general light simulator. The two tested pegs and three possible endings are authored possibilities; the generator does not invent new scientific explanations. It does not model museum staffing schedules, battery discharge, or arbitrary object interactions. Prose is rendered per scene from enacted state, not assembled from whole-story variants. The reference story is an authored successful correction route; generated honest-inconclusive routes are complete alternate outcomes, not rewrites of that reference.

The reference has approximately 1,000 prose words excluding its heading; the inventory lists twenty encounters and explains where they share executable local plays. No execution tools were available for this single-response run. The tests and integration check are therefore **unexecuted**; no pass result is claimed. Run the commands above in the supplied repository to verify them.