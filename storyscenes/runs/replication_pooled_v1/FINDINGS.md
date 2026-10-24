# Three-script storytelling baseline

The requested 10 -> 30 -> 100 ladder now has complete story assessments for
harbor, greenhouse and theater from both authorized judges. Every final set
contains seeds 10000-10099, without filtering or replacement. All 300 saved
worlds replay. This is hand-authored feasibility work, not an automated source
generation benchmark or a production training corpus.

## Hundred-story results

Scores are 0-9, Terra / Luna. Both judges see all hundred positions together.

| Script | Storytelling | Diversity | Exact texts / 100 | Whole-set XZ bytes/story |
| --- | ---: | ---: | ---: | ---: |
| Harbor v9 | 7.79 / 7.78 | 5 / 5 | 96 | 69.60 |
| Greenhouse v2 | 7.94 / 7.94 | 4 / 3 | 26 | 36.16 |
| Theater v2 | 7.73 / 7.89 | 3 / 4 | 25 | 33.84 |

Storytelling reliably clears seven in this experiment. Exact uniqueness is not
semantic uniqueness: harbor's 96 texts are mostly variations within a few
authored purposes. The greenhouse and theater finite-choice audit goes further:
at most 34 and 28 texts respectively, across all their Boolean conditions and
renderer choices. Additional seeds cannot escape those limits.

## Across scripts

Compression includes **all 300 stories**, including duplicates. There are
**147 exact texts**. UTF-8 JSON strings, shuffled with seed 777, XZ preset 9:

- Raw: 353,860 bytes.
- Pooled archive: 12,944 bytes, **3.66% of raw**, **43.15 bytes/story**.
- Separate archives total: 13,960 bytes. Pooling saves another **7.28%**.

Most lexical redundancy is within scripts, not between the three settings.
Compression is not a semantic score or a prediction of training benefit.

Semantic comparison uses **90 stories**, not all 300: the predeclared first
thirty positions, seeds 10000-10029, from each final hundred. Both judges receive
the same shuffled set. Only the rubric's scope changes from one world to three
scripts; calibration, quality dimensions, diversity dimensions and full ID
partition remain. No QA is rejudged in this pooled comparison.

| Judge | Storytelling | Overall story quality | Pooled diversity | Causal groups |
| --- | ---: | ---: | ---: | ---: |
| Terra | 7.900 | 8.000 | 4 | 26 |
| Luna | 7.956 | 7.989 | 6 | 34 |

Neither judge puts stories from different scripts into the same causal group,
but Terra still penalizes the shared problem/observe/adjust/success progression
and repeated language. Luna gives more credit to the different problems and
outcomes. Group counts and overall diversity are not interchangeable. This
disagreement is retained; it is not evidence that diversity is solved.

## QA and reliability

| Script | Terra rated / planned; usable | Luna rated / planned; usable |
| --- | --- | --- |
| Harbor | 566 / 596; 554 | 477 / 596; 446 |
| Greenhouse | 600 / 600; 599 | 540 / 600; 512 |
| Theater | 600 / 600; 599 | 600 / 600; 583 |

Harbor has four unknown-timeout QA requests and one Flex-unavailable request.
Greenhouse has one Flex-unavailable and one returned but incomplete QA response.
No uncertain request was retried or silently moved to standard service.
The sampler uses up to six supported questions; four declined-loan harbor cases
have five. All QA is single-turn. Judge labels are not audited gold labels:
the theater thirty's manual review records ordinary inferences Luna rejected,
including a rejection whose own explanation says the answer is supported.

A real theater QA defect was fixed after freezing its hundred: a source answer
said the cutout was near the lamp after it had moved farther away. It now says
"lit by the lamp." Two other answer phrases were narrowed. All hundred theater
story texts and trace hashes remain identical; the old QA and scores are kept.

## What this supports

Purposeful simulation plus authored scene-sized prose can produce readable
stories with dialogue, consequences and endings without a runtime LLM. This
combined intervention is not a controlled attribution of every quality gain to
prose alone. World-state replay and paragraph provenance also do not prove
every English assertion automatically.

The present scripts are **not a hundredfold meaningful-data multiplier**.
Adding synonyms or drawing more seeds would conceal that rather than fix it.
The next useful experiment is interacting goals: a choice must change resources,
time, obligations or knowledge that alter a later problem's possible resolution.
Merely concatenating two independent scenes is not that test. Preserve this
baseline and judge new structural work on fresh positions with the same rubric.

## Cost and artifacts

The pooled comparison cost an estimated **$0.06753110** from returned usage.
Across this campaign and the earlier authorized judging, returned priced usage
totals **$2.16081530**. Conservatively retained reservations total **$1.601142**,
including explicit unavailable responses. Combined commitment is
**$3.76195730 of $5**, leaving **$1.23804270**. No judge process remains active
at this checkpoint; retained reservations are not claims of active requests.
Coding-agent usage is separate from these API estimates, which are not invoices.

`compression.json`, `all_300_stories.jsonl.xz`, the balanced `attempts.jsonl`,
source and input hashes, planned/actual requests, raw responses and validated
results are preserved here. Parent hundred-story directories contain their
serialized worlds, traces, complete samples, QA and frozen runtimes.
