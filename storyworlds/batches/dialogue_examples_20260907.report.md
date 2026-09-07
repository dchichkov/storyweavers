# Dialogue Example Audit

Three hand-authored, standalone StoryWorld references, with no generation or
judge API calls. The aim is substantial character-to-character conversation
that changes what the characters know, agree to, and do. This is not a claim
that these small generators solve our dataset-diversity problem.

## Local Measurements

Each script emitted 1,000 stories with QA at seed `20260907`. Sampling retained
duplicates. Word counts use whitespace splitting; the dialogue fraction counts
words inside double quotation marks, excluding speaker tags. It measures the
amount of dialogue, not its quality.

| World | Returned | Mean story words | Mean story + QA words | Mean dialogue words | Speaking turns | Exact unique | Slot-normalized unique | Story-only XZ/raw |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Library Words | 1,000 | 252.8 | 350.3 | 55.8% | 14-17 | 455 | 18 | 1.56% |
| One Cart, Two Plans | 1,000 | 326.2 | 427.0 | 53.6% | 19-21 | 455 | 18 | 0.96% |
| Bridge Builders | 1,000 | 346.2 | 438.9 | 53.5% | 18-21 | 455 | 18 | 1.34% |

Each world has **three core problems**, two conversation approaches, and three
item choices. Names and item substitutions explain much of the exact-string
variation. The 18 slot-normalized strings are not 18 independent plots.
Matching parameter spaces and sampling procedures explain the identical unique
counts. Compression uses `prompt_trials.sample_metrics`, separately per world;
the last column is compressed size divided by uncompressed story-only size.
These very low retention ratios confirm that the examples remain templated.

## Verification and Manual Review

- All three `--verify` commands passed: 18 parameterized states each, 54 total,
  plus parity between the Python and inline ASP compatibility-pair registries.
  This parity check is not a formal proof of the whole physical simulation.
- Replayed all 3,000 samples under another `PYTHONHASHSEED`; outputs matched.
- Read all six problem/approach variants per world together with their QA,
  using fixed characters and items: 18 stories manually reviewed.
- Focused regression tests exercise information-transfer guards, agreement vs.
  merely hearing a proposal, capacity limits, actual completion of both loads,
  bridge repair prerequisites, failed/successful trials, full-sentence grounded
  QA, keyword dataclass calls, deterministic sampling, and CLI modes.
- All 64 tests passed across dialogue examples, set judging, dataset scoring,
  prompt trials, factory examples, and Puddles (11 new dialogue tests).

Manual review caught and corrected speech-tag punctuation, a reply that lacked
its preceding question, awkward book-title insertion, QA exposing an unstated
page number, and a steep-bridge description inconsistent with its repair.
The remaining limitations are deliberate small plot spaces and some atomic
physical operations, such as a whole delivery trip represented by one event.
No numerical human or API quality score has been assigned.

Conversation has three distinct jobs here:

- Library: separate the intended meaning from the listener's interpretation,
  then transfer a useful memory or location before acting.
- Cart: make conflicting needs explicit, obtain agreement, and follow through
  on every promised load. Hearing a plan alone does not authorize delivery.
- Bridge: state an objection grounded in an observed physical fault, revise the
  relevant property, and prove the repair with a successful crossing.

## Artifacts

- [Readable preview collection](../DIALOGUE_SAMPLES.md): three complete stories
  with their QA and reproduction commands, not thousands of Markdown files.
- Raw batch: `storyworlds/batches/dialogue_examples_20260907/`.
- Each world subfolder contains `source.py`, `samples.jsonl`, `run.json`,
  `metrics.json`, and `preview.json`; the batch has `summary.json` and `audit.py`.
- Retention archive: `storyworlds/batch_archives/dialogue_examples_20260907.tar.gz`
  and its `.sha256` sidecar. Includes the sampled batch, source scripts, test,
  preview, and this report. It is covered by the existing Git LFS archive rule.

No canonical reference registry, generation default, or scoring formula was
changed for these examples.
