# Direct Prose: Twenty Matched Scenarios

Requested follow-up to the twenty-pack xhigh/128k experiment. The user asked for
twenty approximately 800-word stories written directly by Luna at high reasoning,
using the same seeds, followed by the standard judge.

## Generation

- Model: `gpt-6-luna`; reasoning `high`; service tier `flex`.
- Twenty requests, concurrency twenty, 32,000 output-token ceiling per request.
  This ceiling includes reasoning; it is not the requested story length.
- Identical task seeds, seed words, settings, and premises from
  `../luna_xhigh_128k_20_manifest.json`. These are prompt identifiers, not a
  deterministic API sampling seed.
- Target 800 words, guidance 750-850. All first attempts retained; no editing,
  quality-based selection, resampling, hidden retries, or length-based exclusion.
- No source-code examples, engine files, or procedural constraints in the prompt.
- Preserve each request, raw response, story, usage, timing, and terminal outcome.
- Shared campaign ledger enforces the existing $10 authorization. Reserve $0.03
  per generation, settle against conservative returned-usage estimates, and keep
  reservations for unknown usage. No new agent sessions.

## Judging

Every completed story goes into one deterministically shuffled set (seed 777).
Judge: `gpt-5.6-terra`, Flex, reasoning `none`, using the existing calibration,
0-9 quality rubric, diversity rubric, structured output, and validation code.
Only the opening scope sentence changes: these are different direct-story
scenarios, not samples from ONE procedural StoryWorld. The judge sees story text
and calibration, not the generator model or prior numerical results.

Cross-scenario diversity must not be compared numerically to within-pack
diversity. Quality comparisons also differ in length and reasoning effort;
the old pack scores exclude packs that failed the runtime gate. Direct prose
does not provide simulation state, replay guarantees, grounded QA, or reusable
variation. This is a prose-quality and cost baseline, not a replacement engine.

## Commands

From the repository root, using the same campaign budget and local API key:

```bash
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/luna_direct_stories.py prepare
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/luna_direct_stories.py generate --api-key-file .API_KEY
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/luna_direct_stories.py prepare-judge
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/luna_direct_stories.py judge --api-key-file .API_KEY
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/luna_direct_stories.py report
```

These commands are an audit trail, not a request to rerun paid phases. Existing
dispatch markers prevent automatic repeated spending. Prepared request and source
hashes must remain unchanged. Tests run without API calls:

```bash
./.venv/bin/python -m unittest discover -s storyscenes/design/agents_api_trial_20261024 -p test_luna_direct_stories.py
```
