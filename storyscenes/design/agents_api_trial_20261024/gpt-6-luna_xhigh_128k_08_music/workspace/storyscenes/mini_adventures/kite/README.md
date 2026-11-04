# The Beat Between Us

An offline, stateful mini-adventure set in a community music room. Mara borrows a small drum and hopes a nervous newcomer, June, will join her. June can choose one beat or choose to listen; neither route is treated as a failure. Each scene is a short local play using `storyscenes.mini_adventures.local_play.LocalPlay` and its atomic action traces.

## Run it

From the repository root, with the repository on `PYTHONPATH` if needed:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 14 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py .
```

The CLI prints prose only. `--scenes` is exactly 7 or 8. To override the seed-derived environment, place a JSON object in a file and pass `--params path/to/parameters.json`, for example:

```json
{"room_busy": true, "ribbon_length_cm": 18, "chairs_ready": false, "drum_head_taut": false}
```

Names are optional overrides too: `child` and `newcomer` must be distinct short names. The four world parameters are validated: `drum_head_taut` changes how Mara can make a call, `ribbon_length_cm` changes where the visual cue can be placed, `room_busy` determines whether a cue or demonstration is needed before joining is available, and `chairs_ready` determines whether Mara must move a stool.

## Explicit ending recipes

Generation selects a compatible route from the seed and parameters. For a guaranteed ending, replay an explicit compatible path. These recipes use the default names and seven scenes; paste either snippet at the repository root:

```python
from storyscenes.mini_adventures.kite.world import Parameters, replay

params = Parameters(room_busy=False, chairs_ready=True, drum_head_taut=True,
                    ribbon_length_cm=48)
path = ('borrow_drum', 'newcomer_arrives', 'make_space', 'open_invitation',
        'accept_beat', 'duet', 'ending_duet')
print('\n\n'.join(scene['text'] for scene in replay(params, path)))
```

That recipe ends in **a freely chosen duet**. The other ending can be replayed even in a busy room because passing never requires a cue:

```python
from storyscenes.mini_adventures.kite.world import Parameters, replay

params = Parameters(room_busy=True, chairs_ready=False, drum_head_taut=False,
                    ribbon_length_cm=18)
path = ('borrow_drum', 'newcomer_arrives', 'make_space', 'open_invitation',
        'pass_for_now', 'listening_pattern', 'ending_listening')
print('\n\n'.join(scene['text'] for scene in replay(params, path)))
```

That recipe ends in **a welcome without a duet**. June’s choice is respected, Mara still uses the borrowed drum to make music, and the drum is returned. In a busy room, the joining response becomes available if either optional vignette supplies a demonstration or a visible ribbon cue.

## Interface and design

`world.py` exports `Parameters`, `parameters(seed)`, `initial(params)`, `validate(state)`, `SCENES`, `guard(scene_id, state)`, `play_scene(params, state, scene_id)`, `generate(seed=0, *, count=8, params=None)`, and `replay(params, path)`. Generated rows contain JSON-native parameters, path, episode states, local action requirements and changes, joined story text, final state, and bounded-search attempt count. A generated episode has 40–70 whitespace-separated words. A complete route has exactly seven or eight distinct compatible scenes.

The optional vignettes are `ribbon_cue` and `quiet_demo`. They change persistent state only if selected. Search is bounded and explores detached candidate states; only the chosen route is returned. Failed local actions raise without committing an event or changing the caller’s state. Endings require a completed music exchange and return the borrowed drum and any placed ribbon.

## Limitations and verification status

This is a small scenario-specific model, not a general music or consent simulator. A busy room uses a simple boolean; the visual ribbon and a quiet demonstration are simplified accessibility cues. The scene selector chooses among authored encounters, not arbitrary new plots. The two endings differ in the newcomer’s actual participation, but this pack does not model every social response, musical skill, or future relationship. The fixed prose renderer is local to each scene; it does not use an LLM, network, or external dependency.

**Tests were not executed for this single-response run because no execution tools were available.** The 100-seed tests at both lengths, replay checks, invalid-action checks, optional-scene checks, object continuity, counterfactuals, CLI command, and `check_pack.py` are provided as reproducible commands, not claimed results.
