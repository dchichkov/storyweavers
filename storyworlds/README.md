# Storyworlds

`storyworlds/` holds standalone simulated story sketches. Each script in
`worlds/` models one small story domain with typed state, a reasonableness gate,
grounded Q&A, and an inline ASP twin for self-checking.

For authoring rules, use [`AGENTS.md`](AGENTS.md). This README is for practical
workflow notes that are useful to humans coordinating batches of worlds.

## Subagent Swarm Notes

On 2026-06-16, a 10-task storyworld generation batch was run with Codex
subagents using the `gpt-5.3-codex-spark` model override.

The attempted pattern was:

```text
spawn_agent(
  agent_type="worker",
  model="gpt-5.3-codex-spark",
  message="In /Users/dmitry/storyweavers, create one file only: ..."
)
```

Important findings:

- Explicit `model="gpt-5.3-codex-spark"` worked only when `fork_context` was not
  used. A full-history fork forced inheritance of the parent model/agent type.
- The observed concurrency ceiling was about 6 running subagents. Attempts to
  start all 10 at once produced `agent thread limit reached` for the excess.
- Completed agents still counted against the concurrency limit until closed, so
  closing finished workers was necessary before launching more.
- Long prompts caused some Spark workers to fail with a context-window error.
  Retrying the same assignment with a shorter, self-contained prompt worked.
- The robust pattern was to launch about 6 workers, wait for completions, close
  each completed worker, then refill the pool with the remaining tasks.

The successful short prompt shape was:

```text
In /Users/dmitry/storyweavers, create one file only:
storyworlds/worlds/<name>.py. You are not alone in the codebase; do not revert
others' changes. Follow the storyworld pattern: standalone stdlib script,
imports storyworlds/results.py, StoryParams dataclass, build_parser,
resolve_params, generate, emit, -n, --all, --seed, --trace, --qa, --json,
--asp, --verify, --show-asp. Include Python valid_combos plus inline ASP twin;
--verify must exit 0 using /Users/dmitry/storyweavers/.venv/bin/python. Domain:
<domain>. Final answer: changed file and verification result.
```

After the workers finished, the parent thread re-ran every new world's
`--verify` command directly with `./.venv/bin/python` as a final cross-check.

## Codex SDK One-Shot World Factory

If `openai_codex` is installed in `./.venv`, `codex_world_factory.py` can launch
a single SDK-backed Codex job to create one new world file. It uses the same
one-file prompt shape as the subagent swarm, but sends it through
`AsyncCodex.thread_start(...).run(...)`.

Preview the exact prompt first:

```bash
./.venv/bin/python storyworlds/codex_world_factory.py moss_cookie_v2 \
  --words moss cookie --features misunderstanding kindness --dry-run
```

Omit `--dry-run` to launch the SDK job. Defaults are conservative:
`model=gpt-5.4`, `sandbox=workspace-write`, and `approval-mode=deny_all`.
The generated prompt asks Codex to create exactly
`storyworlds/worlds/<name>.py`, run `--verify`, sample 10 `--qa` stories, check
JSON output, and finish with `git diff --check`.

## Review and Cleanup Notes

`--verify` is necessary but not sufficient. It checks that a world's Python gate
and inline ASP twin agree, but it does not exercise every renderer branch. After
generation, also run a small deterministic sample sweep with `--qa`; this catches
missing format variables, role/entity lookup mistakes, and child-facing prose
artifacts.

A practical review loop:

```bash
./.venv/bin/python storyworlds/worlds/<name>.py --verify
for s in 0 1 2 3 4 5 6 7 8 9; do
  ./.venv/bin/python storyworlds/worlds/<name>.py -n 1 --seed "$s" --qa >/tmp/storyworld.out
done
```

To read across the whole collection, use the repo-level sampler:

```bash
./.venv/bin/python storyworlds/sample_worlds.py -n 10 --seed 42
./.venv/bin/python storyworlds/sample_worlds.py -n 10 --seed 42 --no-qa
```

It discovers `storyworlds/worlds/*.py`, picks random worlds without replacement,
and runs one seeded sample from each. QA is included by default because it tends
to expose story-quality defects alongside the prose.

Common cleanup defects from the Spark batch:

- Verified scripts can still crash during rendering if a template branch needs a
  field that the renderer did not pass.
- Role names such as `hero` and `parent` should not be used as entity IDs unless
  the world really stores entities under those IDs.
- Internal IDs and debug traces should stay in `--trace`, not in the story or
  child-facing Q&A.
- Registry phrases and renderers need one clear article strategy to avoid output
  such as `a a bright beach ball` or `the a caring librarian`.

## Random QA Pass Notes

On 2026-06-17, a randomized story+QA sweep used `./.venv/bin/python` with
`-n 1 --seed <seed> --qa` over 20 randomly selected scripts. The initial pass
found three hard failures and several sampled quality issues:

- `icy_rusty_fence.py` crashed because the hero entity was created with a stale
  `pronoun=` keyword; its cherished prize also was not marked as worn, so the
  predicted warning could disappear.
- `loud_street_bench_detective.py` used the display phrase `soft cloth` where
  later lookup expected the registry key.
- `crystal_river_hover.py` had a list/tuple syntax typo and was missing the
  `Entity.phrase` field its renderer used.
- `cozy_bridge_lamp.py` had the same missing `Entity.phrase` field and several
  template joins such as doubled articles, `little little`, and bad plural
  wording.
- `harbor_search.py`, `market_lost_coin.py`, and `clocktower_search.py` ran but
  exposed role/pronoun drift, terse QA, or token-specific story mismatches.

After cleanup, the same deterministic 20-script sweep had no crashes. The only
remaining scanner flags were false positives from ordinary phrases such as
`his dad` / `her mom`, so regex lint should stay advisory and be paired with
human reading of the sampled story and QA.

On 2026-06-18, a second random QA pass sampled all 55 scripts in
`storyworlds/worlds/` once each with `./.venv/bin/python <script> -n 1 --seed
<seed> --qa`. The first run returned `53/55` successful samples. The two hard
failures were syntax typos in `river_mist_quest.py` and
`whispering_field.py`; after fixing those, the pass exposed a stale
`setup_lamp` call and an ASP import/path issue in `river_mist_quest.py`, plus an
ASP rule mismatch in `whispering_field.py`. The same pass also caught
child-facing wording drift in `museum_search.py`.

The final rerun of the same 55 seeds returned `55/55` successful `--qa` samples.
The only scanner flag left was a false positive in `rusty_door_icy_pond.py` for
the normal sentence "Touching or shaking them can scare the animals...", which
again confirms that regex hints need human review.

A follow-up QA-depth pass on the same date targeted worlds whose sampled answers
were dominated by terse one-sentence responses. The pass expanded answers to
include grounded cause/effect or safety context in `beach_tide.py`,
`campfire_caution.py`, `library_rescue.py`, `train_station_wait.py`,
`river_mist_quest.py`, `whispering_field.py`, `museum_search.py`,
`rooftop_kite.py`, `market_lost_coin.py`, `icy_rusty_fence.py`, and
`clocktower_search.py`; it also fixed a `library_rescue.py` helper/method
consistency issue where a volunteer could narrate a librarian-only rescue.

After that QA-depth pass, a 10-world targeted sample with three seeds per world
reported `shortA=0` for every sampled world and `oneSent=0` for the touched
cluster. A final all-world sweep still returned `55/55` successful samples. The
remaining weak-QA backlog is concentrated in older worlds such as `pirates.py`,
`puddles.py`, `bakery_kindness.py`, `crystal_river_hover.py`,
`mystery_spill.py`, and `theater_prop.py`.

On 2026-06-19, a broader storytelling/QA cleanup pass used five parallel
workers plus a local overflow lane to revisit the remaining worlds in
approximately 10-variation `--qa` batches. The pass raised the floor on story
shape and QA grounding across the older backlog, including the reference
`puddles.py` / `pirates.py` worlds and many search, mystery, kindness, caution,
and quest worlds.

The integrated verification after that pass:

```bash
# all 65 worlds
./.venv/bin/python storyworlds/worlds/<name>.py --verify
./.venv/bin/python storyworlds/worlds/<name>.py -n 1 --seed 31000 --qa
git diff --check
```

Results: `65/65` worlds passed `--verify`; `65/65` passed the seeded `--qa`
smoke; the normal story/QA artifact scan reported no scaffold leaks for
`world model`, raw meter language, unresolved template fields, doubled articles,
or underscored tokens. The remaining work is mostly artful-variety polish:
several worlds are coherent and grounded but still template-like.
