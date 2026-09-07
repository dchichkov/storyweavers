# Canonical Compression Review

No generation or judge API calls. Canonical source files were sampled without
repairs: 1,000 requested per world, seed 777. All seven also passed their own
`--verify` before the audit. Thud returned 600, not 1,000: its CLI deduplicates
internally and exhausted its 50,000 sampling attempts. No padding was added.

## Main Result

**6,600 stories, 6,596 exact uniques: 8.26 MiB -> 243.3 KiB (2.88%).**

Almost every string is distinct, but the pooled story text compresses about
35-fold. Exact deduplication barely changes the ratio: **2.87%**. This is strong
evidence of repeated wording and structure that exact-string dedup misses.
It is not, by itself, a measurement of narrative quality or training utility.

| Reference | Returned | Exact Unique | Slot-Normalized Unique | XZ/Input | Compressed Bytes/Story |
| --- | ---: | ---: | ---: | ---: | ---: |
| Puddles | 1,000 | 1,000 | 363 | 3.22% | 33.6 |
| Pirates | 1,000 | 1,000 | 984 | 3.03% | 59.2 |
| Quesadilla | 1,000 | 997 | 6 | 2.16% | 23.6 |
| Thud | 600 | 600 | 12 | 2.99% | 16.2 |
| Dining | 1,000 | 999 | 952 | 2.46% | 36.6 |
| Garnet | 1,000 | 1,000 | 128 | 2.20% | 23.3 |
| Grocery | 1,000 | 1,000 | 988 | 2.41% | 41.0 |

Grocery and Dining look diverse under slot normalization, but remain highly
compressible. This diagnostic still misses many repeated phrases or sentence
arrangements. Quesadilla and Thud are clearly collapsed under both measures.
Puddles has the highest compressed/input ratio here, but Pirates has more
compressed bytes per story; neither establishes a quality winner.

## Corpus Controls

| Corpus | Stories | Text MiB | XZ KiB | XZ/Input |
| --- | ---: | ---: | ---: | ---: |
| Grouped by world | 6,600 | 8.26 | 217.0 | 2.56% |
| Shuffled across worlds | 6,600 | 8.26 | 243.3 | 2.88% |
| Exact-deduplicated, shuffled | 6,596 | 8.26 | 243.0 | 2.87% |
| All slot-normalized stories | 6,600 | 7.78 | 135.5 | 1.70% |
| Unique slot-normalized stories | 3,433 | 5.29 | 104.6 | 1.93% |
| Word order destroyed, same vocabulary | 6,600 | 8.22 | 2,392.3 | 28.44% |

The last row is a negative control, not proposed training data. Destroying word
order makes the corpus about ten times less compressible without improving
stories. Compression should therefore be an important diversity objective
behind a prose-quality gate, not an unconstrained target.

## Sampling Growth

| Up To Stories/World | Returned Stories | XZ KiB | XZ/Input | Compressed Bytes/Story |
| --- | ---: | ---: | ---: | ---: |
| 10 | 70 | 17.4 | 20.34% | 254.5 |
| 50 | 350 | 34.7 | 7.99% | 101.6 |
| 100 | 700 | 48.7 | 5.60% | 71.3 |
| 250 | 1,750 | 85.5 | 3.94% | 50.0 |
| 500 | 3,500 | 141.9 | 3.27% | 41.5 |
| 1,000 | 6,600 | 243.3 | 2.88% | 37.8 |

Repeated sampling contributes progressively less compressed information per
story. The next useful calibration is a matched natural-story corpus, with
the same number and comparable lengths of stories, before fixing score weights
or an absolute compression threshold. The proposed 21-world Luna baseline is
paused pending this review; no API budget was spent on it.

## Reproduction And Data

```bash
./.venv/bin/python storyworlds/compression_review.py \
  --out storyworlds/batches/canonical_compression_review --count 1000 --seed 777
```

Compression uses LZMA2 preset 6, an explicit 64 MiB dictionary, XZ containers,
and UTF-8 JSONL containing only a story string on each line. Shuffled corpora
are sorted then shuffled with seed 0. Params, QA, traces, filenames, and other
metadata do not enter the compressor. Raw samples, source snapshots, exact byte
counts, actual XZ files, and both audit revisions are retained in the LFS
archive `storyworlds/batch_archives/canonical_compression_20260907.tar.gz`.

Full report with archive links:
[canonical_compression_20260907_v2/report.md](canonical_compression_20260907_v2/report.md).
