# Luna High: Cheap Draft, Not Untouched Success

October 24, 2026. One matched kite-workshop task, not a model-wide yield estimate.
Same frozen source/task/schema as Luna low; high reasoning and 64k output ceiling
replaced low and 32k. Actual output was below 32k. No prior failure feedback was
included. Earlier experiment artifacts remain unchanged.

## Mechanical Results

The raw completed response repeats `reference_story.md` byte-for-byte. Strict
bundle validation rejected it. The `..._normalized` arm removes only that record:
17/100 independent positions run; 43 fail because an action requires comfort
exactly 2 despite its scene allowing >=2; 40 fail because transferring the reel
to its current holder is a forbidden no-op.

The separate `..._repaired` arm fixes those two code fragments only. The comfort
threshold remains in the scene guard; the action records current comfort. An
already-satisfied transfer is skipped. No prose, tests, checker or task changed.
`repair.json` records exact replacements and parent/content hashes.

After repair: **100/100** independent positions, **8/8** generated test methods
pass, reference **1,091 words**, scenes **51-63 words**. Generated tests also
exercise 200 seed/length cases, deterministic replay and paired counterfactuals.
The checker is unchanged and isolated locally without credentials or network.
This establishes tested executability, not exhaustive semantic correctness.

| Diagnostic (100 positions) | Sol low, untouched | Luna high, two fixes |
| --- | ---: | ---: |
| Exact texts | 30 | 43 |
| Distinct paths | 6 | 15 |
| Mean story words | 352 | 430 |
| Approximate quoted-word fraction | 11.2% | 17.7% |
| LZMA ratio | 1.25% | 1.21% |
| Outcome counts | Drawing 90, flight 10 | Guided flight 39, shared flight 33, safe landing 28 |

More paths do not establish better semantic diversity. Both corpora are highly
compressible, and these are 100-position diagnostics, not the 1,000-sample protocol.

## Standard Judge

Same Terra/Flex/none rubric and ten uniform positions selected with seed 777;
duplicates retained. [Stories](gpt-6-luna_high_oneshot_repaired/quality/STORIES.md)
and [raw validated scores](gpt-6-luna_high_oneshot_repaired/quality/result.json).

| Score, out of 9 | Sol low | Luna high, repaired |
| --- | ---: | ---: |
| Quality | 8.1 | 8.0 |
| Storytelling | 8.1 | 8.0 |
| Coherence | 8.1 | 8.0 |
| Diversity | 2 | 1 |

All ten Luna stories scored 8. The selected positions contain six guided and four
shared flights, **no safe-landing stories**, despite 28 such cases in the full
corpus. Do not infer that every branch scored 8 or that a 0.1 difference matters.
The judge grouped all ten into one plot. It correctly notices repetition but
incorrectly calls s000068/s000005 exact duplicates: they have different scene
counts. Exact duplication should be computed, not delegated to a judge.

## Manual Assessment

Read all ten selected stories, the renderer, tests and a deliberately selected
failed-flight/Nia-holder story. Strengths: a clear invitation motive, substantial
dialogue, short readable scenes, an actual shared activity, and a returned loan.
Practice and ribbon affect simulated flight success, unlike purely cosmetic inserts.

Remaining defects, deliberately **not** repaired in this trial:

- `practice` says Nia lets Pavel keep the reel, but state still places it with
  Nia. The following scene offers it again or says Nia kept it. This affects
  all 76 practice-containing positions.
- `ribbon` reaches into a workshop basket after the preceding invitation places
  both children in the field. No carrier or return trip explains the prop; this
  scene appears in 74 positions.
- Failed-flight prose always says Pavel holds the reel, including 16 positions
  whose state and prior scene assign it to Nia. It also produces capitalization
  errors such as "but The worn line". These branches were absent from judging.
- Opening prose always describes fraying, including the zero-wear parameter.
- Most prose is fixed scene text. Paths and optional ordering add surface
  combinations without many genuinely different plots or emotional resolutions.

The Terra score is too forgiving of continuity. Passing replay only proves the
renderer repeats its own output, not that every sentence matches the trace.
Before scaling, add explicit prose/state continuity checks and branch-stratified
diagnostic reading alongside the unchanged uniform comparative judge sample.

## Cost And Conclusion

Returned usage: 35,572 input, 35,569 cache-write, zero cache-read, 29,761 output
including 15,020 reasoning tokens. At the published short-context
[Flex rates](https://developers.openai.com/api/docs/pricing), generation is
**$0.009663-$0.011887**, depending on unreported cache-write TTL. Not an invoice;
excludes repair labor and judging. Reasoning is already included in output.

The conservative ledger charges $0.0237735 for this generation and $0.0266805 for
the judge. Total campaign accounting is **$5.45745768/$10**, including the
unchanged **$5 unknown Sol-agent reservation**. Cancellation does not establish
zero billing. These allowances are intentionally higher than expected charges.

Luna high is a plausible inexpensive draft model for a draft/check/repair pipeline.
This attempt needed duplicate normalization and two small human code repairs;
it did **not** independently complete a correct pack. Prose continuity and
diversity still need work. Multiple fresh tasks are needed to measure repair
yield and total cost before selecting a production model.
