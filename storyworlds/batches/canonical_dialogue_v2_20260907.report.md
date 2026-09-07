# Canonical Reference Set: Dialogue V2

On 2026-09-07, the user approved replacing weaker canonical references with
dialogue-rich examples before prompt optimization. The latest Puddles was
explicitly retained. The matrix stays **seven examples x three matched tasks =
21 generated worlds** per trial; each request contains one example.

## Current Set

| CLI name | Reference | Why keep/include it |
| --- | --- | --- |
| `puddles` | Latest Puddles, unchanged | Compact state-driven problem/response paths and grounded QA |
| `pirates` | Pirates, unchanged | Contrasting consequences, safety decisions, existing simulation/ASP example |
| `garnet` | Garnet, unchanged | Strong voice and distinct physical mechanisms in the prior manual/judge review |
| `library` | Library Words | Clarification, interpretation, and transfer of useful information |
| `cart` | One Cart, Two Plans | Conflicting needs, negotiated agreement, completion of both promised deliveries |
| `bridge` | Bridge Builders | Evidence-based objections, compatible physical repair, successful test |
| `nell` | Nell and the Dragon v2 | Dialogue-driven claim revision, ownership, repair, independently seeded tellings |

The registry is [canonical_examples.py](../canonical_examples.py), version
`dialogue_v2`. All four dialogue sources are standalone scripts, not imports of
another world. Preview: [Library/Cart/Bridge](../DIALOGUE_SAMPLES.md),
[Nell v2](../NELL_V2_SAMPLES.md).

## Replacements and Tradeoffs

The retired default references are Quesadilla, Thud, Dining, and Grocery.
The [original baseline review](canonical_set_quality_20260907.report.md) found
Quesadilla's mystery structure collapsed, and recurring causal/continuity defects
in Dining and Grocery. Thud was a good economical physical-story reference, not
simply bad prose; its rhyme-specific template and capped 600/1,000 output make
it the fourth replacement when prioritizing dialogue and keeping seven slots.
Bridge retains the physical-repair teaching role with sustained conversation.

The replacements were selected from manual reading and local state/QA checks,
not a new numerical judge ranking. Nell v1's 9/9 rating is not a v2 rating.
Library, Cart, Bridge, and Nell v2 are not freshly API-rated. Small authored
plot spaces and repeated wording remain explicit limitations. This is a
curation change for generation examples, not a claim that the new references
themselves yield a better large training corpus.

## Compatibility

`CANONICAL_EXAMPLES` selects the seven current default arms. `EXAMPLE_SOURCES`
also includes the four retired names, so explicit factory/pipeline selections
and custom trials with `quesadilla`, `thud`, `dining`, or `grocery` still work.
No historical file, source, prepared request, or evaluation was overwritten.
The standalone factory's `all` option still means Puddles + Pirates; it is not
an alias for concatenating all seven new examples.

New full-matrix trial manifests and compression reviews record
`example_set=dialogue_v2`. Custom selections are labeled `custom`; historical
unversioned trials remain loadable and are labeled `legacy/unversioned` in
reports. Source/request hashes remain the exact provenance. The judge prompt,
quality thresholds, and score formula were not changed by this curation step.

## Local Verification

- **92 related tests passed**, covering the dialogue worlds, original Nell,
  Nell v2, Puddles, factory selectors, matched trial preparation, and scoring.
- All seven current source scripts passed their own `--verify`.
- Latest Puddles is byte-for-byte unchanged, SHA-256
  `c64ae1bd909e6c8414ae399d58c7f7d932325aeeaf09331297504a86f0cf3a58`.
- A new local pool requested 1,000 samples per reference at seed 777: all
  **7,000 returned with nonempty story text and QA**. Duplicates are retained.
- The pool has **5,311 exact unique stories**. Story-only pooled XZ/raw is
  **2.25%**, or **2.67% after exact dedup**. These are not quality ratings.
- Library, Cart, and Bridge each return 437 distinct texts in this seed's
  1,000 samples; their equal parameter spaces explain the matching counts.
  Nell returns 1,000 distinct texts at this seed, unlike 999 at seed 20260907.

The raw pool, per-world source snapshots and measurements, grouped/shuffled/
deduplicated controls, and growth curve are in `canonical_dialogue_v2_20260907/`.
Its [generated compression report](canonical_dialogue_v2_20260907/report.md)
contains all byte counts. `verification.json` retains the seven verification
outputs and prepared-request checks; `verify.py` records how those checks ran.

## Prepared Baseline

`prompt_trials/dialogue_v2_baseline_20260907/` contains **21 frozen request
bodies**, matched task seed **2026090605**, source/helper snapshots and hashes.
The exact current source of each reference appears in its three requests;
all seven arms have identical task seed/words/features/setting/style/domain
tuples by task index. No requests have been submitted and no generated-world
or new judge results are claimed.

The prepared settings remain Luna, no reasoning, Flex, concurrency 5, no
addendum; the trial's subsequent evaluator uses ten-story Terra/Flex judging
and 1,000 local samples per generated world.

```bash
# Inspect the new frozen plan; no API call.
./.venv/bin/python storyworlds/prompt_trials.py report dialogue_v2_baseline_20260907
./.venv/bin/python storyworlds/prompt_trials.py cost dialogue_v2_baseline_20260907

# Paid generation and evaluation, when proceeding with the new baseline.
OPENAI_API_KEY="$(cat .API_KEY)" ./.venv/bin/python storyworlds/prompt_trials.py run dialogue_v2_baseline_20260907
```

The [retention archive](../batch_archives/canonical_dialogue_v2_20260907.tar.gz)
and [SHA-256 sidecar](../batch_archives/canonical_dialogue_v2_20260907.tar.gz.sha256)
preserve this curation record, local pool, prepared trial, and changed tests.
No generation or judge API budget was spent on this step.
