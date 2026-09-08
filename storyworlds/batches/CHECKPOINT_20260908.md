# StoryWorld Checkpoint: 2026-09-08

This checkpoint preserves the large reference-seeded run, the selected top-20
reference set, the matched Mini/Luna comparisons, and the explicit-cache trial.
It includes the generation/repair/ranking code, tests, reports, and 1,298
materialized Python scripts. Unrelated training work is not part of this checkpoint.

## Data Snapshots

The four existing compressed snapshots were verified against every live member
before checkpointing: no changed, missing, or unarchived run files were found.
They total **296,910,731 bytes** (296.9 MB), with 15,066 archived files. Each has
a SHA-256 sidecar. The archives use the existing Git LFS rule in `.gitattributes`;
raw JSON/JSONL remains ignored in the working tree rather than added to normal Git.

| Run | Attempts | Materialized scripts | Archive bytes | Snapshot |
| --- | ---: | ---: | ---: | --- |
| Repaired-100 + canonical Luna references | 1,000 | 998 | 221,015,484 | [Archive](../batch_archives/prompt_trial_repaired100_canonical_luna_20260907_20260907T231046Z.tar.gz) |
| Top-20 Mini | 100 | 100 | 25,020,150 | [Archive](../batch_archives/prompt_trial_top20_mini100_20260907_20260908T041554Z.tar.gz) |
| Top-20 Luna | 100 | 100 | 26,376,987 | [Archive](../batch_archives/prompt_trial_top20_luna100_20260907_20260908T043557Z.tar.gz) |
| Top-20 Luna, explicit caching | 100 | 100 | 24,498,110 | [Archive](../batch_archives/prompt_trial_top20_luna100_cached_20260907_20260908T055618Z.tar.gz) |

Archives retain frozen requests, attempt/response ledgers, original and repaired
source, local checks, compressed samples, available judge results, and runtime
snapshots. The caching trial intentionally has **no paid judge results**.
Generated sources also remain directly available under `storyworlds/worlds/prompt_trials/`.
Materialized does not mean valid: known failed scripts and minor generated
whitespace artifacts are preserved byte-for-byte to match their archived audits.

## Results and Code

- [Large-run report](repaired100_canonical_luna_20260907.report.md)
- [Reference rankings](repaired100_canonical_luna_20260907.reference_rankings.md)
- [Top-20 selection](repaired100_canonical_luna_20260907.top20.md) and
  [reusable manifest](../reference_sets/luna_top20_20260907.json)
- [Mini run](top20_mini100_20260907.notes.md)
- [Matched Luna comparison](top20_luna100_20260907.notes.md)
- [Explicit-cache results and repairs](top20_luna100_cached_20260907.notes.md)
- [Pipeline commands](../QUALITY_ITERATION_PIPELINE.md)

Explicit caching is opt-in through `--prompt-cache-mode explicit`, with
`--cache-warmup` in prompt trials. All 80 warmed requests hit the cache in the
100-world test. Generation cost was $0.3152; 90 worlds ran after repairs, 76
passed sampling plus verification, and 64 passed the full local gate. These
are execution checks, not story quality estimates.

## Restore Raw Data

After pulling this checkpoint on another machine, fetch the LFS objects:

```bash
git lfs pull --include="storyworlds/batch_archives/*.tar.gz"
```

For example, restore the caching trial's ignored data directory from the repo
root. The generated scripts are already tracked, so extract only the data subtree:

```bash
tar -xzf storyworlds/batch_archives/prompt_trial_top20_luna100_cached_20260907_20260908T055618Z.tar.gz \
  storyworlds/batches/prompt_trials/top20_luna100_cached_20260907
```

Only extract into a fresh or unchanged trial directory. Historical runs and
ratings must not be overwritten by later repairs or evaluations.
