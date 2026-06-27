# Storyworld Batch Catalog

Last audited: 2026-06-26.

This catalog inventories the JSONL artifacts under `storyworlds/batches/` and
records whether each generation artifact is original or repaired/fixed, plus
where the generated Python worlds and sampled story files are materialized.

## Reading Notes

- `responses.jsonl` files are direct-service Responses API outputs. These are
  original model outputs unless the filename explicitly says `repaired`.
- `storyworld_batch_*.jsonl` files are old Batch API request JSONLs, not model
  outputs.
- `batch_*.output.jsonl` files are old Batch API model outputs. Files with
  `.repaired` or `.repaired_mechanical` are fixed JSONLs derived from an original
  output.
- `Stories story/error` counts are current files in the `.stories` directory.
  Error files are retained after later repairs, so story plus error can exceed
  `N`.
- The latest 5k run has original response JSONL but repaired materialized Python
  files in-place, plus manual timeout repairs documented in its report.

## Summary

| Family | Count | Meaning |
|---|---:|---|
| All `*.jsonl` files in `storyworlds/batches` | 163 | Raw generation, repair, sample, and quality artifacts |
| Direct-service `storyworld_service_*.responses.jsonl` | 48 | Responses API generation outputs |
| Old Batch API request `storyworld_batch_*.jsonl` | 18 | Batch request payloads |
| Old Batch API output `batch_*.output.jsonl` | 15 | Batch output payloads, including repaired derivatives |
| Quality judgment JSONLs | 46 | Mini-judge quality outputs |
| Sample / QA worksheet JSONLs | 36 | Local runnable/QA sample sweeps |

## Unrepaired / Materialized Status

Using "unrepaired" to mean "no repaired sibling JSONL exists":

| Category | Count | Meaning |
|---|---:|---|
| Unrepaired original generation JSONLs with materialized world folders | 44 | Original output exists and a world folder exists, but no repaired JSONL sibling exists. This includes most direct-service runs; some may still have repaired Python files in-place. |
| Unrepaired original generation JSONLs without materialized world folders | 7 | Mostly failed or empty one-off service attempts. |
| Original generation JSONLs with repaired sibling JSONLs | 6 | Keep the original, but prefer the repaired JSONL or repaired materialized folder for analysis. |

The 44 unrepaired-but-materialized JSONLs break down as:

- 39 direct-service `storyworld_service_*.responses.jsonl` runs, including the current 5k run. For the 5k run, the JSONL is original but the materialized Python files have been repaired in-place.
- 5 old small Batch API output files without repaired siblings:
  `batch_6a36416fe08c819098819e4c58d57884.output.jsonl`,
  `batch_6a3644da9a508190b6fec9406d4d06e8.output.jsonl`,
  `batch_6a364e04bb508190b7656a696206bd49.output.jsonl`,
  `batch_6a36503e22b88190be3a31960ad20c0a.output.jsonl`,
  `batch_6a36532e0f0481908f5f5502e13f9bfe.output.jsonl`.

The 7 unrepaired and not-materialized JSONLs are:

- `storyworld_service_20260621T213739Z_seed1055341754_n10.responses.jsonl`
- `storyworld_service_20260621T235038Z_seed1389694357_n10.responses.jsonl`
- `storyworld_service_20260624T070515Z_seed424242_n1.responses.jsonl`
- `storyworld_service_20260624T082039Z_seed424242_n1.responses.jsonl`
- `storyworld_service_20260624T085320Z_seed424242_n1.responses.jsonl`
- `storyworld_service_20260624T085938Z_seed424242_n1.responses.jsonl`
- `storyworld_service_20260624T092801Z_seed424242_n1.responses.jsonl`

## Current High-Value Runs

| Run | Status | Model | N | Materialized worlds | Stories story/error | Notes |
|---|---|---|---:|---|---:|---|
| `storyworld_service_20260626T060043Z_seed274930118_n5000` | original JSONL, repaired in materialized files | `gpt-5.4-mini` | 5000 | `storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000` | 4561/624 | Puddles-only, flex, concurrency 100. Report includes repair passes and manual timeout repair addendum. |
| `storyworld_service_20260626T055509Z_seed1837429065_n100` | original | `gpt-5.4-mini` | 100 | `storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100` | 88/12 | Puddles-only, flex, concurrency 100, quality run present. |
| `storyworld_service_20260626T055019Z_seed926384711_n100` | original | `gpt-5.4-mini` | 100 | `storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100` | 90/10 | Puddles-only, flex, concurrency 50, quality run present. |
| `storyworld_service_20260624T090150Z_seed197402754_n1000` | original | `gpt-5.4-mini` | 1000 | `storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000` | 904/96 | Earlier 1k direct-service run. |
| `batch_6a3744730bd48190b368f32c2819a0ed.repaired_mechanical.output.jsonl` | repaired output | `gpt-5.4-mini` | 1000 | `storyworlds/worlds/gpt-5.4-mini_batch_6a3744730bd48190b368f32c2819a0ed_seed953274611_n1000_repaired` | - | Best older repaired mini Batch API artifact. |
| `batch_6a375c8eb2d0819087f55a14681f3b59.repaired_mechanical.output.jsonl` | repaired output | `gpt-5.4` | 1000 | `storyworlds/worlds/gpt-5.4_batch_6a375c8eb2d0819087f55a14681f3b59_seed1607971764_n1000_repaired` | - | Best older repaired full-model Batch API artifact. |

## Direct-Service Generation JSONLs

| Run | Role | Model | Seed | N | Examples / addendum | Lines | Materialized worlds | Stories story/error | Notes |
|---|---|---|---:|---:|---|---:|---|---:|---|
| `storyworld_service_20260621T213739Z_seed1055341754_n10` | original | `gpt-5.4-mini` | 1055341754 | 10 | - / - | 10 | `storyworlds/worlds/gpt-5.4-mini_service_20260621T213739Z_seed1055341754_n10` | - | c5; ok 0, fail 10 |
| `storyworld_service_20260621T222722Z_seed1055341754_n10` | original | `gpt-5.4-mini` | 1055341754 | 10 | - / - | 10 | `storyworlds/worlds/gpt-5.4-mini_service_20260621T222722Z_seed1055341754_n10` | 1/9 | c5; ok 10, fail 0 |
| `storyworld_service_20260621T235038Z_seed1389694357_n10` | original | `gpt-5.4-mini` | 1389694357 | 10 | - / `gpt54mini_service_reliability_v1.md` | 10 | `storyworlds/worlds/gpt-5.4-mini_service_20260621T235038Z_seed1389694357_n10` | 0/10 | c5; ok 0, fail 10 |
| `storyworld_service_20260621T235055Z_seed1389694357_n10` | original | `gpt-5.4-mini` | 1389694357 | 10 | - / `gpt54mini_service_reliability_v1.md` | 10 | `storyworlds/worlds/gpt-5.4-mini_service_20260621T235055Z_seed1389694357_n10` | 1/9 | c5; ok 10, fail 0 |
| `storyworld_service_20260622T000000Z_seed1245732883_n10` | original | `gpt-5.4-mini` | 1245732883 | 10 | - / - | 10 | `storyworlds/worlds/gpt-5.4-mini_service_20260622T000000Z_seed1245732883_n10` | 4/6 | c5; ok 10, fail 0 |
| `storyworld_service_20260622T011547Z_seed2023889374_n10` | original | `gpt-5.4-mini` | 2023889374 | 10 | - / - | 10 | `storyworlds/worlds/gpt-5.4-mini_service_20260622T011547Z_seed2023889374_n10` | 5/5 | c5; ok 10, fail 0 |
| `storyworld_service_20260622T021641Z_seed1855084837_n10` | original | `gpt-5.4-mini` | 1855084837 | 10 | - / - | 10 | `storyworlds/worlds/gpt-5.4-mini_service_20260622T021641Z_seed1855084837_n10` | 10/5 | c5; ok 10, fail 0 |
| `storyworld_service_20260622T025926Z_seed953308428_n10` | original | `gpt-5.4-mini` | 953308428 | 10 | - / - | 10 | `storyworlds/worlds/gpt-5.4-mini_service_20260622T025926Z_seed953308428_n10` | 6/4 | c5; ok 10, fail 0 |
| `storyworld_service_20260622T034914Z_seed1855084837_n10` | original | `gpt-5.4-mini` | 1855084837 | 10 | - / - | 10 | `storyworlds/worlds/gpt-5.4-mini_service_20260622T034914Z_seed1855084837_n10` | 6/5 | c5; ok 10, fail 0 |
| `storyworld_service_20260622T035136Z_seed1855084837_n10` | original | `gpt-5.4-mini` | 1855084837 | 10 | - / - | 10 | `storyworlds/worlds/gpt-5.4-mini_service_20260622T035136Z_seed1855084837_n10` | 6/4 | c5; ok 10, fail 0 |
| `storyworld_service_20260622T035344Z_seed1855084837_n10` | original | `gpt-5.4-mini` | 1855084837 | 10 | - / - | 10 | `storyworlds/worlds/gpt-5.4-mini_service_20260622T035344Z_seed1855084837_n10` | 9/1 | c5; ok 10, fail 0 |
| `storyworld_service_20260622T035527Z_seed1855084837_n10` | original | `gpt-5.4-mini` | 1855084837 | 10 | - / - | 10 | `storyworlds/worlds/gpt-5.4-mini_service_20260622T035527Z_seed1855084837_n10` | 2/8 | c5; ok 10, fail 0 |
| `storyworld_service_20260622T035719Z_seed829048975_n10` | original | `gpt-5.4-mini` | 829048975 | 10 | - / - | 10 | `storyworlds/worlds/gpt-5.4-mini_service_20260622T035719Z_seed829048975_n10` | 6/4 | c5; ok 10, fail 0 |
| `storyworld_service_20260622T042304Z_seed1855084837_n10` | original | `gpt-5.4-mini` | 1855084837 | 10 | - / - | 10 | `storyworlds/worlds/gpt-5.4-mini_service_20260622T042304Z_seed1855084837_n10` | 9/1 | c5; ok 10, fail 0 |
| `storyworld_service_20260622T045816Z_seed1855084837_n10` | original | `gpt-5.4-mini` | 1855084837 | 10 | - / - | 10 | `storyworlds/worlds/gpt-5.4-mini_service_20260622T045816Z_seed1855084837_n10` | 8/2 | c5; ok 10, fail 0 |
| `storyworld_service_20260623T034741Z_seed623010101_n100` | original | `gpt-5.4-mini` | 623010101 | 100 | - / - | 100 | `storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100` | 94/45 | c5; ok 100, fail 0 |
| `storyworld_service_20260623T054043Z_seed1907342701_n100` | original | `gpt-5.4-mini` | 1907342701 | 100 | - / `gpt54mini_service_reliability_v3.md` | 100 | `storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100` | 79/21 | c50; ok 100, fail 0 |
| `storyworld_service_20260623T071419Z_seed779406221_n50` | original | `gpt-5.4-mini` | 779406221 | 50 | - / `gpt54mini_service_reliability_v4.md` | 50 | `storyworlds/worlds/gpt-5.4-mini_service_20260623T071419Z_seed779406221_n50` | 43/7 | c50; ok 50, fail 0 |
| `storyworld_service_20260623T072428Z_seed779406221_n50` | original | `gpt-5.4-mini` | 779406221 | 50 | - / - | 50 | `storyworlds/worlds/gpt-5.4-mini_service_20260623T072428Z_seed779406221_n50` | 38/12 | c50; ok 50, fail 0 |
| `storyworld_service_20260623T073042Z_seed779406221_n50` | original | `gpt-5.4-mini` | 779406221 | 50 | - / `gpt54mini_service_reliability_v5.md` | 50 | `storyworlds/worlds/gpt-5.4-mini_service_20260623T073042Z_seed779406221_n50` | 44/6 | c50; ok 50, fail 0 |
| `storyworld_service_20260623T073613Z_seed779406221_n50` | original | `gpt-5.4-mini` | 779406221 | 50 | - / `gpt54mini_service_reliability_v6.md` | 50 | `storyworlds/worlds/gpt-5.4-mini_service_20260623T073613Z_seed779406221_n50` | 40/10 | c50; ok 50, fail 0 |
| `storyworld_service_20260623T074326Z_seed779406221_n50` | original | `gpt-5.4-mini` | 779406221 | 50 | pirates / - | 50 | `storyworlds/worlds/gpt-5.4-mini_service_20260623T074326Z_seed779406221_n50` | 42/8 | c50; ok 50, fail 0 |
| `storyworld_service_20260623T074642Z_seed779406221_n50` | original | `gpt-5.4-mini` | 779406221 | 50 | puddles / - | 50 | `storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50` | 45/5 | c50; ok 50, fail 0 |
| `storyworld_service_20260624T063717Z_seed1230577450_n50` | original | `gpt-5.4-mini` | 1230577450 | 50 | puddles / - | 50 | `storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50` | 45/5 | c50; ok 50, fail 0 |
| `storyworld_service_20260624T070515Z_seed424242_n1` | original | `nvidia/nemotron-3-ultra-550b-a55b:free` | 424242 | 1 | puddles / - | 1 | `storyworlds/worlds/nvidia_nemotron-3-ultra-550b-a55b_free_service_20260624T070515Z_seed424242_n1` | - | c1; ok 0, fail 1 |
| `storyworld_service_20260624T081143Z_seed2038046945_n100` | original | `gpt-5.4-mini` | 2038046945 | 100 | puddles / - | 100 | `storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100` | 90/10 | c50; ok 100, fail 0 |
| `storyworld_service_20260624T082039Z_seed424242_n1` | original | `nvidia/nemotron-3-ultra-550b-a55b:free` | 424242 | 1 | puddles / - | 0 | `storyworlds/worlds/nvidia_nemotron-3-ultra-550b-a55b_free_service_20260624T082039Z_seed424242_n1` | - | c1 |
| `storyworld_service_20260624T082828Z_seed779406221_n50` | original | `gpt-5.4-mini` | 779406221 | 50 | puddles / - | 50 | `storyworlds/worlds/gpt-5.4-mini_service_20260624T082828Z_seed779406221_n50` | 41/9 | c50; ok 50, fail 0 |
| `storyworld_service_20260624T083233Z_seed1230577450_n50` | original | `gpt-5.4-mini` | 1230577450 | 50 | puddles / - | 50 | `storyworlds/worlds/gpt-5.4-mini_service_20260624T083233Z_seed1230577450_n50` | 44/6 | c50; ok 50, fail 0 |
| `storyworld_service_20260624T084545Z_seed1746935730_n100` | original | `gpt-5.4-mini` | 1746935730 | 100 | puddles / - | 100 | `storyworlds/worlds/gpt-5.4-mini_service_20260624T084545Z_seed1746935730_n100` | 100/11 | tier flex; c50; ok 100, fail 0 |
| `storyworld_service_20260624T085320Z_seed424242_n1` | original | `nvidia/nemotron-3-super-120b-a12b:free` | 424242 | 1 | puddles / - | 0 | `storyworlds/worlds/nvidia_nemotron-3-super-120b-a12b_free_service_20260624T085320Z_seed424242_n1` | - | tier flex; c1 |
| `storyworld_service_20260624T085938Z_seed424242_n1` | original | `nvidia/nemotron-3-super-120b-a12b` | 424242 | 1 | puddles / - | 0 | `storyworlds/worlds/nvidia_nemotron-3-super-120b-a12b_service_20260624T085938Z_seed424242_n1` | - | tier flex; c1 |
| `storyworld_service_20260624T090150Z_seed197402754_n1000` | original | `gpt-5.4-mini` | 197402754 | 1000 | puddles / - | 1000 | `storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000` | 904/96 | tier flex; c100; ok 1000, fail 0 |
| `storyworld_service_20260624T092446Z_seed2085103064_n10` | original | `gpt-5.4` | 2085103064 | 10 | puddles / - | 10 | `storyworlds/worlds/gpt-5.4_service_20260624T092446Z_seed2085103064_n10` | 10/0 | tier flex; c10; ok 10, fail 0 |
| `storyworld_service_20260624T092801Z_seed424242_n1` | original | `deepseek/deepseek-v4-flash` | 424242 | 1 | puddles / - | 1 | `storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T092801Z_seed424242_n1` | - | tier flex; c1; ok 0, fail 1 |
| `storyworld_service_20260624T093506Z_seed424242_n1` | original plus repaired sibling | `deepseek/deepseek-v4-flash` | 424242 | 1 | puddles / - | 1 | `storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T093506Z_seed424242_n1` | - | tier flex; c1; ok 1, fail 0 |
| `storyworld_service_20260624T093506Z_seed424242_n1.repaired.responses.jsonl` | repaired responses | `deepseek/deepseek-v4-flash` | 424242 | 1 | puddles / - | 1 | `storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T093506Z_seed424242_n1` | - | fixed sibling of previous row |
| `storyworld_service_20260624T094246Z_seed424242_n50` | original | `deepseek/deepseek-v4-flash` | 424242 | 50 | puddles / - | 50 | `storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T094246Z_seed424242_n50` | 29/21 | tier flex; c50; ok 50, fail 0 |
| `storyworld_service_20260624T185554Z_seed424242_n50` | original | `deepseek/deepseek-v4-flash` | 424242 | 50 | puddles / - | 50 | `storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260624T185554Z_seed424242_n50` | 25/25 | tier flex; c50; ok 48, fail 2 |
| `storyworld_service_20260624T220402Z_seed424242_n50` | original | `gpt-5.4-mini` | 424242 | 50 | puddles / - | 50 | `storyworlds/worlds/gpt-5.4-mini_service_20260624T220402Z_seed424242_n50` | 2/48 | tier flex; c50; ok 3, fail 47 |
| `storyworld_service_20260624T221217Z_seed424242_n50` | original | `minimax/minimax-m3` | 424242 | 50 | puddles / - | 50 | `storyworlds/worlds/minimax_minimax-m3_service_20260624T221217Z_seed424242_n50` | 1/49 | tier flex; c50; ok 1, fail 49 |
| `storyworld_service_20260625T020146Z_seed424242_n50` | original | `mistralai/mistral-small-2603` | 424242 | 50 | puddles / - | 50 | `storyworlds/worlds/mistralai_mistral-small-2603_service_20260625T020146Z_seed424242_n50` | 7/43 | tier flex; c50; ok 50, fail 0 |
| `storyworld_service_20260625T022423Z_seed424242_n1` | original | `minimax/minimax-m3` | 424242 | 1 | puddles / - | 1 | `storyworlds/worlds/minimax_minimax-m3_service_20260625T022423Z_seed424242_n1` | - | tier flex; c1; ok 1, fail 0 |
| `storyworld_service_20260625T022909Z_seed424242_n50` | original | `minimax/minimax-m3` | 424242 | 50 | puddles / - | 50 | `storyworlds/worlds/minimax_minimax-m3_service_20260625T022909Z_seed424242_n50` | 24/26 | tier flex; c50; ok 47, fail 3 |
| `storyworld_service_20260625T031134Z_seed424242_n50` | original | `deepseek/deepseek-v4-flash` | 424242 | 50 | puddles / - | 50 | `storyworlds/worlds/deepseek_deepseek-v4-flash_service_20260625T031134Z_seed424242_n50` | 36/14 | tier flex; c50; ok 49, fail 1 |
| `storyworld_service_20260626T055019Z_seed926384711_n100` | original | `gpt-5.4-mini` | 926384711 | 100 | puddles / - | 100 | `storyworlds/worlds/gpt-5.4-mini_service_20260626T055019Z_seed926384711_n100` | 90/10 | tier flex; c50; ok 100, fail 0 |
| `storyworld_service_20260626T055509Z_seed1837429065_n100` | original | `gpt-5.4-mini` | 1837429065 | 100 | puddles / - | 100 | `storyworlds/worlds/gpt-5.4-mini_service_20260626T055509Z_seed1837429065_n100` | 88/12 | tier flex; c100; ok 100, fail 0 |
| `storyworld_service_20260626T060043Z_seed274930118_n5000` | original JSONL, repaired in materialized files | `gpt-5.4-mini` | 274930118 | 5000 | puddles / - | 5000 | `storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000` | 4561/624 | tier flex; c100; ok 5000, fail 0 |

## Old Batch API JSONLs

| JSONL | Role | Paired manifest | Model | Seed | N | Lines | Materialized worlds | Notes |
|---|---|---|---|---:|---:|---:|---|---|
| `storyworld_batch_20260620T072522Z_seed42_n10.jsonl` | original request | `storyworld_batch_20260620T072522Z_seed42_n10.manifest.json` | `gpt-5.3-codex-spark` | 42 | 10 | 10 | `storyworlds/worlds/gpt-5.3-codex-spark` | no output JSONL found |
| `storyworld_batch_20260620T072528Z_seed42_n10.jsonl` | original request | `storyworld_batch_20260620T072528Z_seed42_n10.manifest.json` | `gpt-5.3-codex-spark` | 42 | 10 | 10 | `storyworlds/worlds/gpt-5.3-codex-spark` | no output JSONL found |
| `storyworld_batch_20260620T072559Z_seed42_n10.jsonl` | original request | `storyworld_batch_20260620T072559Z_seed42_n10.manifest.json` | `gpt-5.3-codex-spark` | 42 | 10 | 10 | `storyworlds/worlds/gpt-5.3-codex-spark` | no output JSONL found |
| `storyworld_batch_20260620T072633Z_seed42_n10.jsonl` | original request | `storyworld_batch_20260620T072633Z_seed42_n10.manifest.json` | `gpt-5.3-codex-spark` | 42 | 10 | 10 | `storyworlds/worlds/gpt-5.3-codex-spark` | no output JSONL found |
| `storyworld_batch_20260620T072721Z_seed42_n10.jsonl` | original request | `storyworld_batch_20260620T072721Z_seed42_n10.manifest.json` | `gpt-5.3-codex-spark` | 42 | 10 | 10 | `storyworlds/worlds/gpt-5.3-codex-spark` | batch id `batch_6a3640dc202c8190be6500b8536e53aa`; no output JSONL found |
| `storyworld_batch_20260620T072950Z_seed42_n10.jsonl` | original request | `storyworld_batch_20260620T072950Z_seed42_n10.manifest.json` | `gpt-5.4-mini` | 42 | 10 | 10 | `storyworlds/worlds/gpt-5.4-mini` | output `batch_6a36416fe08c819098819e4c58d57884.output.jsonl` |
| `storyworld_batch_20260620T074125Z_seed42_n10.jsonl` | original request | `storyworld_batch_20260620T074125Z_seed42_n10.manifest.json` | `gpt-5.4-mini` | 42 | 10 | 10 | `storyworlds/worlds/gpt-5.4-mini` | no output JSONL found |
| `storyworld_batch_20260620T074225Z_seed42_n10.jsonl` | original request | `storyworld_batch_20260620T074225Z_seed42_n10.manifest.json` | `gpt-5.4-mini` | 42 | 10 | 10 | `storyworlds/worlds/gpt-5.4-mini` | no output JSONL found |
| `storyworld_batch_20260620T074425Z_seed42_n10.jsonl` | original request | `storyworld_batch_20260620T074425Z_seed42_n10.manifest.json` | `gpt-5.4-mini` | 42 | 10 | 10 | `storyworlds/worlds/gpt-5.4-mini` | output `batch_6a3644da9a508190b6fec9406d4d06e8.output.jsonl` |
| `storyworld_batch_20260620T080201Z_seed42_n10.jsonl` | original request | `storyworld_batch_20260620T080201Z_seed42_n10.manifest.json` | `gpt-5.4-mini` | 42 | 10 | 10 | `storyworlds/worlds/gpt-5.4-mini` | batch id present; no output JSONL found |
| `storyworld_batch_20260620T082331Z_seed580420970_n10.jsonl` | original request | `storyworld_batch_20260620T082331Z_seed580420970_n10.manifest.json` | `gpt-5.4-mini` | 580420970 | 10 | 10 | `storyworlds/worlds/gpt-5.4-mini` | output `batch_6a364e04bb508190b7656a696206bd49.output.jsonl` |
| `storyworld_batch_20260620T083259Z_seed1143934598_n10.jsonl` | original request | `storyworld_batch_20260620T083259Z_seed1143934598_n10.manifest.json` | `gpt-5.4-mini` | 1143934598 | 10 | 10 | `storyworlds/worlds/gpt-5.4-mini` | output `batch_6a36503e22b88190be3a31960ad20c0a.output.jsonl` |
| `storyworld_batch_20260620T084532Z_seed325818274_n10.jsonl` | original request | `storyworld_batch_20260620T084532Z_seed325818274_n10.manifest.json` | `gpt-5.4-mini` | 325818274 | 10 | 10 | `storyworlds/worlds/gpt-5.4-mini` | output `batch_6a36532e0f0481908f5f5502e13f9bfe.output.jsonl` |
| `storyworld_batch_20260620T092945Z_seed184114977_n1000.jsonl` | original request | `storyworld_batch_20260620T092945Z_seed184114977_n1000.manifest.json` | `gpt-5.4-mini` | 184114977 | 1000 | 1000 | `storyworlds/worlds/gpt-5.4-mini` | output plus `batch_6a365d...repaired.output.jsonl` |
| `storyworld_batch_20260620T221838Z_seed912640337_n100.jsonl` | original request | `storyworld_batch_20260620T221838Z_seed912640337_n100.manifest.json` | `gpt-5.4` | 912640337 | 100 | 100 | `storyworlds/worlds/gpt-5.4` | output plus `.repaired_mechanical.output.jsonl` |
| `storyworld_batch_20260620T232532Z_seed678402913_n1000.jsonl` | original request | `storyworld_batch_20260620T232532Z_seed678402913_n1000.manifest.json` | `gpt-5.4` | 678402913 | 1000 | 1000 | `storyworlds/worlds/gpt-5.4` | output plus `.repaired_mechanical.output.jsonl` |
| `storyworld_batch_20260621T015439Z_seed953274611_n1000.jsonl` | original request | `storyworld_batch_20260621T015439Z_seed953274611_n1000.manifest.json` | `gpt-5.4-mini` | 953274611 | 1000 | 1000 | `storyworlds/worlds/gpt-5.4-mini` | output plus `.repaired_mechanical.output.jsonl` |
| `storyworld_batch_20260621T033735Z_seed1607971764_n1000.jsonl` | original request | `storyworld_batch_20260621T033735Z_seed1607971764_n1000.manifest.json` | `gpt-5.4` | 1607971764 | 1000 | 1000 | `storyworlds/worlds/gpt-5.4` | output plus `.repaired_mechanical.output.jsonl` |

## Old Batch API Output JSONLs

| Output JSONL | Role | Paired manifest | Model | Seed | N | Lines | Materialized worlds |
|---|---|---|---|---:|---:|---:|---|
| `batch_6a36416fe08c819098819e4c58d57884.output.jsonl` | original output | `storyworld_batch_20260620T072950Z_seed42_n10.manifest.json` | `gpt-5.4-mini` | 42 | 10 | 10 | `storyworlds/worlds/gpt-5.4-mini` |
| `batch_6a3644da9a508190b6fec9406d4d06e8.output.jsonl` | original output | `storyworld_batch_20260620T074425Z_seed42_n10.manifest.json` | `gpt-5.4-mini` | 42 | 10 | 10 | `storyworlds/worlds/gpt-5.4-mini` |
| `batch_6a364e04bb508190b7656a696206bd49.output.jsonl` | original output | `storyworld_batch_20260620T082331Z_seed580420970_n10.manifest.json` | `gpt-5.4-mini` | 580420970 | 10 | 10 | `storyworlds/worlds/gpt-5.4-mini` |
| `batch_6a36503e22b88190be3a31960ad20c0a.output.jsonl` | original output | `storyworld_batch_20260620T083259Z_seed1143934598_n10.manifest.json` | `gpt-5.4-mini` | 1143934598 | 10 | 10 | `storyworlds/worlds/gpt-5.4-mini` |
| `batch_6a36532e0f0481908f5f5502e13f9bfe.output.jsonl` | original output | `storyworld_batch_20260620T084532Z_seed325818274_n10.manifest.json` | `gpt-5.4-mini` | 325818274 | 10 | 10 | `storyworlds/worlds/gpt-5.4-mini` |
| `batch_6a365d9a796c8190b61af021aaa75d29.output.jsonl` | original output | `storyworld_batch_20260620T092945Z_seed184114977_n1000.manifest.json` | `gpt-5.4-mini` | 184114977 | 1000 | 1000 | `storyworlds/worlds/gpt-5.4-mini` |
| `batch_6a365d9a796c8190b61af021aaa75d29.repaired.output.jsonl` | repaired output | `storyworld_batch_20260620T092945Z_seed184114977_n1000.manifest.json` | `gpt-5.4-mini` | 184114977 | 1000 | 1000 | `storyworlds/worlds/gpt-5.4-mini` |
| `batch_6a3711c1d7108190a838dee650b9103b.output.jsonl` | original output | `storyworld_batch_20260620T221838Z_seed912640337_n100.manifest.json` | `gpt-5.4` | 912640337 | 100 | 100 | `storyworlds/worlds/gpt-5.4` |
| `batch_6a3711c1d7108190a838dee650b9103b.repaired_mechanical.output.jsonl` | repaired output | `storyworld_batch_20260620T221838Z_seed912640337_n100.manifest.json` | `gpt-5.4` | 912640337 | 100 | 100 | `storyworlds/worlds/gpt-5.4` |
| `batch_6a372179eacc8190a39e4ad27b242f70.output.jsonl` | original output | `storyworld_batch_20260620T232532Z_seed678402913_n1000.manifest.json` | `gpt-5.4` | 678402913 | 1000 | 1000 | `storyworlds/worlds/tmp/gpt-5.4_batch_6a372179eacc8190a39e4ad27b242f70_seed678402913_n1000` |
| `batch_6a372179eacc8190a39e4ad27b242f70.repaired_mechanical.output.jsonl` | repaired output | `storyworld_batch_20260620T232532Z_seed678402913_n1000.manifest.json` | `gpt-5.4` | 678402913 | 1000 | 1000 | `storyworlds/worlds/gpt-5.4_batch_6a372179eacc8190a39e4ad27b242f70_seed678402913_n1000_repaired` |
| `batch_6a3744730bd48190b368f32c2819a0ed.output.jsonl` | original output | `storyworld_batch_20260621T015439Z_seed953274611_n1000.manifest.json` | `gpt-5.4-mini` | 953274611 | 1000 | 1000 | `storyworlds/worlds/tmp/gpt-5.4-mini_batch_6a3744730bd48190b368f32c2819a0ed_seed953274611_n1000_repaired_mechanical` |
| `batch_6a3744730bd48190b368f32c2819a0ed.repaired_mechanical.output.jsonl` | repaired output | `storyworld_batch_20260621T015439Z_seed953274611_n1000.manifest.json` | `gpt-5.4-mini` | 953274611 | 1000 | 1000 | `storyworlds/worlds/gpt-5.4-mini_batch_6a3744730bd48190b368f32c2819a0ed_seed953274611_n1000_repaired` |
| `batch_6a375c8eb2d0819087f55a14681f3b59.output.jsonl` | original output | `storyworld_batch_20260621T033735Z_seed1607971764_n1000.manifest.json` | `gpt-5.4` | 1607971764 | 1000 | 1000 | `storyworlds/worlds/gpt-5.4` |
| `batch_6a375c8eb2d0819087f55a14681f3b59.repaired_mechanical.output.jsonl` | repaired output | `storyworld_batch_20260621T033735Z_seed1607971764_n1000.manifest.json` | `gpt-5.4` | 1607971764 | 1000 | 1000 | `storyworlds/worlds/gpt-5.4_batch_6a375c8eb2d0819087f55a14681f3b59_seed1607971764_n1000_repaired` |

## Derived Sample / QA JSONLs

These are not generation batches. They are local sampler or QA worksheet outputs.

| Family | Count | Files |
|---|---:|---|
| `gpt54_batch_6a372179_repaired_live_seed777_qa*` | 15 | Iterative runnable/QA sweeps over repaired `batch_6a372179...`; each has 1000 lines. |
| `storyworld_batch_20260620T092945...samples*` | 9 | Iterative sample sweeps over the old 1k mini batch. |
| `storyworld_batch_20260620T221838...samples*` | 3 | Raw/mechanical/no-fallback sample sweeps over the old 100 full-model batch. |
| `storyworld_batch_20260620T232532...samples*` | 2 | Raw and repaired-mechanical sample sweeps over old 1k full-model batch. |
| `storyworld_batch_20260621T015439...samples*` | 2 | Raw and repaired-mechanical sample sweeps over old 1k mini batch. |
| `storyworld_batch_20260621T033735...samples*` | 5 | Staged compile/main/storyparams/tell-signature/mechanical sample sweeps. |

## Derived Quality JSONLs

These are mini-judge ratings, not generation batches.

| Family | Count | Notes |
|---|---:|---|
| `storyworld_service_*.quality.jsonl` | 36 | Quality ratings paired with direct-service runs; row counts match successfully sampled stories, not always requested `N`. |
| `story_quality_*.jsonl` | 10 | Ad hoc or comparison quality runs, including older repaired Batch API artifacts and current example-world checks. |

Important standalone quality artifacts:

- `storyworld_service_20260626T055019Z_seed926384711_n100.quality.jsonl` has 90 ratings.
- `storyworld_service_20260626T055509Z_seed1837429065_n100.quality.jsonl` has 88 ratings.
- `storyworld_service_20260624T090150Z_seed197402754_n1000.quality.jsonl` has 904 ratings.
- `story_quality_service_20260623T034741Z_seed623010101_n100.repaired_final.jsonl` has 100 ratings for the repaired-final variant of that run.

## Open Questions / Caveats

- Some early Batch API request manifests have no matching downloaded
  `batch_*.output.jsonl`; they are catalogued as request-only.
- Some old repaired outputs were materialized into shared model folders instead
  of a uniquely named repaired folder. Where a unique repaired folder exists, it
  is listed explicitly.
- Direct-service repaired state is often in the materialized Python files and
  report, not in a new JSONL. The 5k run is the main example: its response JSONL
  is original, but the world directory contains repaired files.
