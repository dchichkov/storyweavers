# Reference Sets

Explicit candidate manifests for `prompt_trials.py --example-manifest`. These
do not change `canonical_examples.py` or include every source in every prompt:
each source is a separate arm, and each generation request receives one example.

## Luna Top 20

[`luna_top20_20260907.json`](luna_top20_20260907.json) selects 20 references from
the 106-reference Luna run: 18 core candidates plus Thud and Loop/Ginger as
higher-quality, lower-yield probes. It preserves the earlier eight-candidate
shortlist. The [selection report](../batches/repaired100_canonical_luna_20260907.top20.md)
contains all 20 sources, child quality/diversity, success counts, and limitations.

Selection is exploratory, based on nine or ten unmatched generation tasks per
reference. Each selected arm has at least five valid judge results and no
missing eligible ratings. The 18 core choices are the first 18 in the existing
strict joint-delivery ranking after excluding the two probes and requiring
conditional mean quality >=6. Strict joint delivery requires full local checks,
quality >=6, and semantic diversity >=3 on the same generated world.

The manifest records `label`, repository-relative `source`, source `sha256`,
and `role` (`core` or `quality_probe`). Hashes were checked against the original
reference snapshots when selecting this set. The trial factory currently reads
`label` and `source`, then snapshots the current files; recheck the recorded
hashes if sources change before a paid run. Keep manifests versioned instead
of silently editing a selected set. These files live outside the ignored batch
data directory so they can be included in a normal code commit.

Example offline preparation, with the same three fresh tasks in each arm:

```bash
./.venv/bin/python storyworlds/prompt_trials.py prepare top20_trial_01 \
  --seed <fresh-seed> \
  --example-manifest storyworlds/reference_sets/luna_top20_20260907.json \
  --per-example 3
```

That would prepare 60 requests, not submit them. Omit `--unique-tasks` for
matched comparisons. A stronger confirmation uses more matched tasks per arm.
The latest Puddles remains unchanged as a possible separate control; neither
this selection nor the example command replaces the canonical registry.
