# Bakery Release Check: Round 4

Release candidate verified against frozen Round 3. No generation, renderer,
inventory, parameter, sampling, or test changes this round. No missing boundary
was found that justified another regression. The helper implementation remains frozen;
greenhouse adoption and final external verification belong to the other worker
and parent respectively.

## Commands And Results

```sh
.venv/bin/python -m unittest storyscenes.mini_adventures.test_local_play storyscenes.mini_adventures.bakery.test_world
.venv/bin/python -m storyscenes.mini_adventures.bakery.world --seed 6 --scenes 7
.venv/bin/python -m storyscenes.mini_adventures.bakery.world --seed 6 --scenes 8
.venv/bin/python -m storyscenes.mini_adventures.bakery.world --seed 42 --scenes 7
.venv/bin/python -m storyscenes.mini_adventures.bakery.world --seed 757654805 --scenes 8
```

- 27 focused tests pass in 7.391 seconds: nine shared and eighteen bakery tests.
- All four CLI outputs equal API-generated prose plus its trailing newline;
  stderr is empty. `--help` succeeds; unsupported `--scenes 6` rejects.
- All 100 frozen Round 3 rows reproduce exactly through current generation and
  saved-path replay, including prose, episodes, parameters, state, and search
  counts. The same rows also reproduce from frozen source in a fresh interpreter.
- All three diagnostic recipes in `README.md` were executed verbatim and reach
  their stated outcomes. They are explicit counterfactuals, not random samples.
- All 24 earlier saved sample rows reproduce from their corresponding frozen
  rounds, and their Markdown contains the saved prose. No samples were replaced.
- The reference is byte-identical to every Round 1/2/3 frozen reference. Current
  bakery generation sources, inventory, tests, and shared helper implementation
  are byte-identical to frozen Round 3. `release_checks.json` records checks and
  hashes, plus the concurrent shared-test exception described below.

The shared test file initially matched its frozen bytes. During the final hash
check, an external concurrent edit changed two mock targets from a literal module
path to `LocalPlay.__module__`. The bakery worker did not make or revert that
edit. Its exact two-line scope is verified and recorded separately; the helper
implementation remains unchanged. The focused suite was rerun after observing
the change and still passes all 27 tests.

The stable shared API remains `LocalPlay(state, *, actors, validate)` with
`act(name, requires=None, **changes)`, `.state`, and `.events`. Bakery's adapter
remains `world.LocalPlay(state)` with its local movement and loan operations.
Keyword-only parameters and these signatures were checked directly.

## Remaining Limits

The frozen 100-position batch still contains 89 postponements, eight surprise
suppers, and three shared suppers. No attempt was made to improve that headline
by filtering or adjusting probabilities. The three IDs describe a narrow family:
two supper variants and an unfinished loaf with a tentative invitation.
`breakfast_instead` does not mean breakfast occurred. Story backbone, symbolic
fuel/time rules, and limited optional-crown payoffs remain as previously reported.

Focused tests and reproduction establish mechanics, not literary quality or
unattended dataset readiness. Public helper state/events are mutable and copying
favors correctness over throughput. Seeds 1000-1049 were not sampled. Held-out
reading, final snapshots, and the complete StoryScenes suite remain the parent's
external release gate, not results claimed here.
