# Storyworld Contract

Use this contract when creating or reviewing one `storyworlds/worlds/*.py`
script. A storyworld is a standalone, classical simulation of one small
TinyStories-style domain.

## Shape

- Create exactly one self-contained stdlib script under `storyworlds/worlds/`.
- Import `storyworlds/results.py` eagerly for `QAItem`, `StoryError`, and
  `StorySample`; import `storyworlds/asp.py` lazily inside ASP helpers.
- Define `StoryParams`, parameter registries, `build_parser`, `resolve_params`,
  `generate`, `emit`, and `main`.
- Support default run, `-n`, `--all`, `--seed`, `--trace`, `--qa`, `--json`,
  `--asp`, `--verify`, and `--show-asp`.

## World Model

- Model typed entities with physical `meters` and emotional `memes`.
- Let simulated state drive prose. Do not render one frozen paragraph with
  swapped nouns.
- Start from the seed by imagining a short source tale, then implement the
  premise, tension, turn, and resolution as world state.
- Use constraints over coverage: fewer plausible variants are better than one
  weak problem/fix pair.
- Explicit invalid choices should raise `StoryError` with a legible reason.

## ASP Twin

- Include a Python reasonableness gate and an inline `ASP_RULES` twin.
- Emit registry facts with `asp_facts()`.
- `--verify` must compare ASP/Python parity and exercise generated stories.

## Story Quality

- Every sample should read like a complete story: clear beginning, state-driven
  middle turn, and an ending image proving what changed.
- Avoid event-log prose, raw fact fragments, generic endings, missing endings,
  and weak turns.
- Keep prose child-facing, concrete, and authored.
- Never leak internal ids, raw meter/debug language, unresolved template fields,
  doubled articles, or scaffold phrases into story text or child-facing QA.

## QA

- Generate three sets from world state, not by parsing rendered English:
  prompts, story-grounded QA, and world-knowledge QA.
- Story-grounded answers should be full natural-language explanations, usually
  two short sentences when cause/effect is available.
- Prefer causal second sentences tied to world trace facts: risk, method, gear,
  helper, location, material, ownership, or later consequence.

## Required Checks

Run these before finishing a new world:

```bash
./.venv/bin/python storyworlds/worlds/<name>.py --verify
./.venv/bin/python storyworlds/worlds/<name>.py -n 10 --seed 777 --qa
./.venv/bin/python storyworlds/worlds/<name>.py --json
git diff --check -- storyworlds/worlds/<name>.py
```

Useful extra checks:

```bash
./.venv/bin/python storyworlds/worlds/<name>.py --all --qa
./.venv/bin/python storyworlds/worlds/<name>.py --trace --seed 777
```
