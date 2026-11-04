# The Rope in the Snow

A standard-library-only mini-adventure for the supplied `storyscenes.mini_adventures.local_play.LocalPlay`. The H1 is not part of the reference prose word count; the reference body is approximately 1,000 words. The reference story was written before the simulator and is intentionally preserved as a separate authored playthrough.

## Run

From the repository root:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 8
python -m storyscenes.mini_adventures.kite.world --seed 17 --scenes 7
python -m unittest storyscenes.mini_adventures.kite.test_world
python check_pack.py /path/to/repository
```

The command prints the selected story prose. `--scenes` accepts exactly 7 or 8. `--params` accepts a JSON object of overrides; unspecified fields are filled from the seeded parameter recipe. Names are fixed rather than used as a diversity mechanism.

## Ending recipes

Each command below selects seven scenes, so neither optional vignette is required for the ending. The race recipes explicitly set the physical conditions that decide whether the soup arrives.

Patient delivery:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7 --params '{\u0022route_choice\u0022:\u0022patient\u0022}'
```

Safe race, intact delivery:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7 --params '{\u0022route_choice\u0022:\u0022race\u0022,\u0022snow_cm\u0022:3,\u0022runner_condition\u0022:\u0022sound\u0022,\u0022load_kg\u0022:1,\u0022has_mittens\u0022:true}'
```

Unsafe race, spilled soup but salvaged provisions:

```bash
python -m storyscenes.mini_adventures.kite.world --seed 0 --scenes 7 --params '{\u0022route_choice\u0022:\u0022race\u0022,\u0022snow_cm\u0022:15,\u0022runner_condition\u0022:\u0022sound\u0022,\u0022load_kg\u0022:3,\u0022has_mittens\u0022:true}'
```

The `ending_patient` route refuses the race and gets all provisions delivered. `ending_race` is eligible only with sound runners, snow at most 7 cm, a load at most 2 kg, and warm mitten grip. Other race attempts spill the soup; bread and oil are gathered and delivered, and the ending acknowledges the loss rather than reversing it. The sled is returned to Dima and checked or repaired in all endings.

## Parameters and scenes

`Parameters` validates six consequential values: `route_choice` (`patient` or `race`), `snow_cm` (0–20), `runner_condition` (`sound` or `loose`), `load_kg` (1–4), `has_mittens` (boolean), and `friend_race_pressure` (1–3). Snow and route knowledge affect patient travel; the four race-safety factors affect whether the basket remains intact; pressure changes Jo’s response and whether Jo initially follows or catches up to help.

The two optional vignettes are `mittens_vignette` and `bell_vignette`. The first may lend Jo’s mittens, which are actually used and returned. The second records knowledge of the baker’s swept lane, which can reduce fatigue on a deep-snow patient route. Omitting either scene does not perform its effects. Seven-scene stories use the seven core encounters; eight-scene stories add exactly one vignette.

The world search is deterministic for a seed, bounded to 5,000 scene attempts, and explores detached episode states. Local actions go through `LocalPlay`; failed actions do not commit to the caller. Episode traces retain equality preconditions and changed values. There are no network calls, runtime language models, or third-party dependencies.

## Limitations and test status

This is a small authored scenario, not a general snow or sled physics engine. Route choice is an explicit parameter rather than interactive player input. The cast, prose, and scene pool are fixed; valid paths are not evidence of broad semantic diversity. The race threshold is a scenario rule, and incidental gestures are not all simulated. The spill ending delivers bread and oil but cannot recover the soup.

**Tests were not executed in this single-response run because no execution tools were available.** The unittest module is included for independent execution; no test results or `check_pack.py` success are claimed here.