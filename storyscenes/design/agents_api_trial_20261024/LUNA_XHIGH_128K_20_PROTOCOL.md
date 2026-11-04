# Twenty Distinct Xhigh Packs

October 24, 2026. User requested 128k output headroom, xhigh, twenty stories and
different seeds. Interpreted explicitly as twenty independent complete two-level
StoryScene packs, not twenty samples from one pack. All requests remain inside
the previously authorized $10 campaign budget and source-upload scope.

## Inputs

`luna_xhigh_128k_20_manifest.json` records twenty distinct numeric task seeds
(2026102402-2026102421), three seed words each, settings and premises. Seeds and
words are actual prompt text; no unsupported API randomness seed is supplied.
Both copies of TASK.md in the request are updated consistently.

The thirteen frozen project sources, checker, reference example and output
schema are otherwise identical to the single xhigh control. The generic `kite/`
module path is retained only for isolated harness compatibility, and the prompt
explicitly says to write the new scenario, not a kite story. Each arm has its
own workspace so they cannot overwrite each other. No previous generated pack,
repair feedback or judge notes are added to prompts.

This changes scenario and output ceiling together. It measures varied-task
feasibility, not the causal benefit of 128k over 64k. Keep the manifest for a
later matched comparison. Seeds are not randomized draws from a defined domain
population: the twenty distinct premises were authored for breadth.

## Execution

- `gpt-6-luna`, Responses API, `reasoning.effort=xhigh`, Flex, `store=false`.
- `max_output_tokens=128000`, including reasoning. No forced minimum length.
- Twenty concurrent generation requests; thirty-minute timeout per request.
- No automatic retry or Standard fallback. Unknown usage keeps its reservation.
- Generation reserves $0.15 per pack; preparation checks a conservative token
  bound against that reservation. The shared ledger uses atomic locked reloads
  for concurrent reserve/settle, separately from the campaign-wide process lock.
- Local checks and paid judging each use at most four workers.
- Generated code runs only through the existing isolated sandbox checker, with
  no credentials, network or access to unrelated user files.
- Raw failures stay raw. No repair or duplicate normalization in this batch.

Each returned valid bundle is checked at seeds 5000-5049 and lengths seven/eight:
100 requested positions, exact replay, reference/inventory and generated tests.
Only packs runnable at all 100 positions receive the unchanged ten-story Terra
Flex/none judge (selection seed 777, duplicates retained). Length/test failures
do not prevent prose judging when all 100 positions are runnable, matching the
prior Sol and xhigh handling. Quality averages must be labelled conditional on
this runtime gate, not averages over all requested packs.

The same checker seed values across packs are intentional for evaluation;
the task seeds, words and premises used to author the packs are all different.

## Evidence

Raw request/response, usage, source hashes, bundle, independent checks and judge
artifacts stay in each `gpt-6-luna_xhigh_128k_NN_NAME/` directory. Runner snapshots
are in `luna_xhigh_128k_20_runner/`. The input manifest refuses overwrites and the
runner refuses automatic redispatch. Campaign budget retains the earlier
$5 unknown Sol-agent reservation.

Commands from repository root:

```bash
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/luna_xhigh_batch.py prepare
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/luna_xhigh_batch.py run --api-key-file .API_KEY
./.venv/bin/python storyscenes/design/agents_api_trial_20261024/luna_xhigh_batch_report.py
./.venv/bin/python -m unittest discover -s storyscenes/design/agents_api_trial_20261024 -p 'test_luna*.py'
./.venv/bin/python -m unittest storyscenes.test_authoring_api
```

Offline verification before dispatch: nine high/xhigh/batch helper tests and
fourteen runner tests passed. New tests cover distinct seeds, unchanged context,
consistent TASK.md copies, 128k limit, thirty-minute timeout, concurrent ledger
updates and budget-cap enforcement. No shared story-engine behavior changed.

## Status

All twenty requests resolved locally: nineteen returned complete bundles and
bakery returned HTTP 500. Five packs run 100/100 positions; library alone passes
all mechanical requirements. Five paid judge calls completed. No retries or
repairs. See [final review](LUNA_XHIGH_128K_20_REVIEW.md), generated
`LUNA_XHIGH_128K_20_TABLE.md` and `luna_xhigh_128k_20_summary.json` for evidence.
`LUNA_XHIGH_128K_20_SAMPLES.md` selects one successful story per returned pack
using its task seed; this manual sample is explicitly conditional on success.
