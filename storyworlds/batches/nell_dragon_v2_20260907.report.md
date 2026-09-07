# Nell V2: State-Driven Worlds and Independent Tellings

## Result

A separate [v2 script](../worlds/nell_and_the_dragon_v2.py) now separates the
world simulation from its telling. The [previously evaluated original](../worlds/nell_and_the_dragon.py)
has not changed. [Read four complete stories and their QA](../NELL_V2_SAMPLES.md).

Local checks pass. **No generation or judge API calls were made for v2**, and no
new overall quality score is assigned. The previous Terra 9/9 quality and 1/9
diversity ratings belong to v1 only.

## What Changes

- Actions have actor, knowledge, physical-resource, and ownership prerequisites.
  Questions and observation establish facts before the recovery plan can use them.
- Four outcomes: exchange; explicit requested return after the bird keeps both
  ornaments; cooperative repair; recognition that the jewel was a gift.
- Missing material requires a trip home. Tarnished brass needs polishing; an
  unfinished brace needs a stick and sufficient cord. Taking, carrying, installing,
  releasing, and recovering an object are separate causal steps.
- The repair must bear the load independently. The dragon actually withdraws
  his temporary support before the ending claims success.
- A second RNG controls authored sentence variants, complete dialogue exchanges,
  optional dialogue, voice, detail, and optional embellishments. It cannot affect
  the simulated events. No LLM or word-by-word synonym replacement runs locally.

The policy is domain-specific and bounded, not a generic planner. Observation
reads physical relations rather than another character's private belief. Safety
checks read physical nest requirements and support strength, not belief flags.
The ASP twin checks registry and physical detachment/ownership guard parity;
it is not a full temporal proof of every narrative.

## Matched Experiment

Final batch: `nell_dragon_v2_20260907_r2/`; pool seed **20260907**.
Each arm contains **1,000 samples**, including any duplicates. All v2 arms keep
voice dry, dialogue conversational, detail normal, and flourish budget 2.

| Arm | Exact unique | Coarse causal signatures | Story words, mean | Story + QA words, mean | Story-only XZ/raw | Dedup compression retention |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Historical v1 pool | 72 | Not instrumented | 501.2 | 705.0 | 0.80% | 4.04% |
| One fixed v2 world, varied prose | 1,000 | 1 | 432.6 | 649.6 | 1.60% | 3.42% |
| Mixed v2 worlds, fixed prose seed | 441 | 22 | 352.3 | 563.5 | 1.33% | 3.35% |
| Same mixed worlds, varied prose | 999 | 22 | 356.1 | 567.3 | 2.33% | 4.82% |

The fixed world uses `StoryParams(world_seed=777)` and prose seeds 42 through
1041. Mixed worlds come from the CLI sampler; the fixed-prose control replaces
only their prose seeds with 42. The two mixed arms have identical full trace
hashes **row for row**. The v1 pool is reused unchanged from its historical batch,
not generated again or matched on nonexistent v2 parameters.

Resolution counts in either mixed arm: **486 gift recognitions, 259 repairs,
128 exchanges, 127 requested returns**. Uniform parameter sampling is not
uniform outcome sampling: gift ownership ends the conflict before several other
parameters matter. Shorter mean length partly reflects those shorter gift stories.
Mean dialogue turns in the full v2 pool: **20.0**.

The full mixed pool is **2,092,378 bytes to 48,844 bytes** under story-only XZ
measurement. The deduplicated pool retains **48,765 / 1,010,844 = 4.82%** of the
bytes needed to compress its stories independently.

## Interpret Carefully

Exact dedup now reports 999 unique strings, but the one-world control reports
1,000. Slot normalization is also fooled: that control still has 1,000 distinct
skeleton strings. Lexical variation is real, but those are not independent plots.

The coarse signature uses event kinds, actors, and parent event kinds. It ignores
names, jewel names, and ordering among independent events. **22 signatures are
not 22 wholly different plots**: some differ only by a failed offer, material
preparation, or investigation performed before recognizing a gift. The larger
761 full trace count includes cosmetic and unobserved state differences.

There is genuine causal improvement over v1, particularly the changed ownership
resolution and the repair dependency chain. Nevertheless, the setting, cast,
problem family, and payment ending remain narrow. LZMA still predicts most of
the corpus. Higher exact yield would inflate the existing composite even if the
judge quality stayed unchanged; do not interpret that as a proportionate increase
in useful training information. No hypothetical composite is reported here.

XZ/raw uses the existing preset-6, sorted-then-shuffled compact JSON story-array
measurement. Retention uses the existing raw LZMA2 protocol: pooled 64 MiB
dictionary versus independently compressed stories, after exact dedup and
subtracting empty-stream overhead. Both exclude prompts, parameters, and QA.
The saved `.stories.jsonl.xz` files retain sampling order and JSONL framing, so
their file sizes differ from the scorecard's shuffled JSON-array measurement.

QA intentionally does not gain random paraphrases: the full mixed pool has
6,599 pairs but only 58 unique pairs. For the frozen world, 7,000 pairs collapse
to seven. Repeated QA would require separate deduplication in a training export.

## Verification and Reading

**90 related tests pass**, including 15 new v2 tests. Coverage includes all
48 world configurations across three world seeds, the rendering-control matrix,
same-trace QA equality, invalid action guards, missing resources, ownership,
physical support, non-repeated failed offers, all CLI modes, and hash-seed replay.
The final 1,000-sample CLI output replays byte-for-byte with `PYTHONHASHSEED=99`;
`--verify` passes its 48-case exercise and ASP parity checks. All 3,000 v2
control-arm samples complete with final-state checks.

Manual reading covered the eight `--all` configurations, raw-material repair,
an initially mistaken gift claim, a home-fetch/requested-return sequence, and
contrasting renderings of the identical default trace. Reading caught an
ambiguous pronoun at the offering handoff and repeated size descriptions; both
were corrected before the final batch. An earlier safety review also corrected
belief-based support checking and strengthened the permanent-repair guard.

The gift ending changes what success means; the repair ending visibly tests the
change. Both read coherently in the inspected samples. The repair remains more
procedural and longer than the supplied story; character voices share some
dialogue banks, so plain/dry/playful are partial voice shifts, not independent
authors. Semantic evidence tags check that required event blocks were rendered,
not independent natural-language entailment. Human or judge review still matters.

For a training contribution, stratify by resolution/causal pattern and cap the
number of retellings per pattern. Do not retain 1,000 just because exact dedup
allows it. A fresh ten-story Terra quality/diversity evaluation remains unrun.

## Retained Data

- `nell_dragon_v2_20260907/`: first local run, preserved before the final wording fix.
- `nell_dragon_v2_20260907_r2/`: final three control pools, copied historical v1
  pool, per-row event signatures, previews and full preview traces, compression
  metrics, CLI replay/verification, and source/test/helper snapshots.
- [Archive](../batch_archives/nell_dragon_v2_20260907.tar.gz) and
  [SHA-256](../batch_archives/nell_dragon_v2_20260907.tar.gz.sha256) retain both runs,
  this report, the public preview, and the current source/tests.

Reproduce from the repository root into a **new** output directory:

```bash
./.venv/bin/python storyworlds/batches/nell_dragon_v2_20260907/audit.py --out storyworlds/batches/nell_dragon_v2_repeat
env PYTHONPATH=storyworlds ./.venv/bin/python -m unittest storyworlds/test_nell_and_the_dragon_v2.py storyworlds/test_nell_and_the_dragon.py storyworlds/test_dialogue_worlds.py storyworlds/test_world_set_quality.py storyworlds/test_dataset_score.py storyworlds/test_prompt_trials.py storyworlds/test_factory_examples.py storyworlds/test_puddles.py
```

The driver imports the current repository helpers; use its recorded code hashes
and snapshots when comparing against this frozen result. It refuses to overwrite
an output directory containing completed metrics. The historical v1 pool must
also be present (or restored from its own retained archive).
