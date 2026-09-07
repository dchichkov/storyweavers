# Nell and the Dragon: Local Adaptation Check

[Source script](../worlds/nell_and_the_dragon.py), adapted from the story supplied
in the conversation. No generation or judge API was used. No canonical example
registry, scoring formula, or generation default was changed.

## Behavior

The default preserves Nell, the emerald, the cabbage-sized ruby, the brass
button, and the promised payment in true stories. Dialogue tags are omitted
where the alternating speakers are clear; speaker IDs remain in every speech
event. The final image is added to show the recovered jewel and Nell preparing
a question. The dragon has promised a story, not already delivered one.

Three needs select physically useful offers: a shiny display object, a fastener
for a loose twig, or soft nest lining. A hasty approach adds an aborted visit
when the dragon comes too close. These are six variations of one narrative,
not six independent plots. Names and jewel colors are cosmetic substitutions.

Offer selection checks carrying capacity and the individual bird's preference,
not monetary worth. Visiting also requires sufficient distance, quiet, and no
visible teeth. Picking up an offer, carrying it home, installing it, and catching
the displaced jewel are separate state changes. The original jewel remains in
the nest until installation; both the tree and nest remain intact.

## Results

| Check | Result |
| --- | ---: |
| Requested / returned, seed `20260907` | 1,000 / 1,000 |
| Exact unique story strings | 72 |
| Slot-normalized unique strings | 18 |
| Speaking turns per story | 37-46 |
| Mean words in quotes / story words | 36.0% |
| Mean story words | 501.2 |
| Mean story + QA words | 705.0 |
| Story-only XZ / raw | 24,392 / 3,067,634 bytes (0.80%) |
| Own verification | 18 states; Python/ASP offer-eligibility parity |
| Replay with another `PYTHONHASHSEED` | Identical |
| Focused regression tests | 11 passed |
| Broader regression suite, including prior dialogue examples | 75 passed |

All six fixed-name, emerald variants were manually read with QA. Their high
compressibility is expected: this is a faithful small reference adaptation,
not evidence that its variation multiplier is suitable for a large dataset.
There is no API quality score. The ASP twin covers offer eligibility, not the
full temporal simulation; regression tests check ordering and counterfactual
failure states separately.

## Reproduction and Retention

```bash
./.venv/bin/python storyworlds/worlds/nell_and_the_dragon.py --qa
./.venv/bin/python storyworlds/worlds/nell_and_the_dragon.py --all --qa
./.venv/bin/python storyworlds/worlds/nell_and_the_dragon.py -n 1000 --seed 20260907 --qa --json
./.venv/bin/python storyworlds/worlds/nell_and_the_dragon.py --verify
env PYTHONPATH=storyworlds ./.venv/bin/python -m unittest storyworlds/test_nell_and_the_dragon.py
```

Raw batch: `storyworlds/batches/nell_dragon_20260907/`, containing the exact source
snapshot, 1,000 samples in `samples.jsonl`, six manually reviewed variants in
`six_variants.jsonl`, the default sample and full trace, raw CLI result, and
`summary.json`. There are no per-story Markdown files.

Archive: `storyworlds/batch_archives/nell_dragon_20260907.tar.gz`, with a SHA256
sidecar, covered by the existing Git LFS rule. It also contains this report, the
source script, and its regression tests.
