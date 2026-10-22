# StoryScenes Run Archives

`storyscenes_runs_20261021.tar.gz` preserves the nine previously uncommitted
StoryScenes run directories below, including generated worlds, samples, saved
API requests/responses, evaluation results, and frozen authoring/runtime code.
It does not delete or modify the local runs. Python caches and other files
already excluded by Git ignore rules are omitted.

The snapshot contains 5,815 files: 352,294,603 original bytes compressed to
30,153,936 bytes. Every archived file was read back and checked against its
manifest checksum and the unchanged local source.

- `cached_prose_ablation_v1`
- `cached_prose_ablation_v2`
- `cached_prose_full_v1`
- `compact_cached_v1`
- `compact_cached_v2`
- `compact_cached_v3`
- `conversation_100_v1`
- `mixed_seed_v1`
- `worlds_100_v1`

These snapshots are stored with Git LFS. Selected Markdown reports and manual
reviews are also committed at their original paths so they remain browsable.
Raw run files are ignored to avoid committing a second, uncompressed copy.
Existing, previously tracked runs are unaffected.

## Restore

From the repository root:

```bash
git lfs pull --include='storyscenes/run_archives/*.tar.gz'
shasum -a 256 -c storyscenes/run_archives/storyscenes_runs_20261021.tar.gz.sha256
# -k preserves any files already present in the checkout.
tar -xkzf storyscenes/run_archives/storyscenes_runs_20261021.tar.gz storyscenes/runs
```

The archive contains a root `ARCHIVE_MANIFEST.json` with every member's size
and SHA-256. The adjacent verification JSON records a complete read-back
comparison against the source files at checkpoint time. Restoring these files
is local and does not submit new paid API requests.
