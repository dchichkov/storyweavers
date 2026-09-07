# Canonical Story-Set Baseline

Seven reference StoryWorlds, ten randomly selected stories each, selection seed
777. These are the existing canonical generators, not 21 newly generated Luna
worlds. Samples come from `canonical_compression_20260907_v2`; no source edits,
new world generation, or repairs are part of this reference baseline.

Live judge: `gpt-5.6-terra`, reasoning `none`, Flex,
`story_set_quality_v1`. Earlier Mini evaluations and compression reports remain
unchanged. Raw inputs, exact requests, responses, and ratings are retained in
`canonical_set_quality_20260907_terra/`.

## Measured Baseline

All seven calls completed on the requested Terra/Flex tier, with no retries or
reasoning tokens. All 70 individual ratings and all seven plot partitions
passed schema/ID validation. The seven unchanged source files also passed a
fresh local `--verify`; this is the scripts' own check, not proof of prose or
QA correctness. Source hashes and selected sample-pool hashes were rechecked.

Quality and semantic diversity are on **0-9** scales. Compression retention is
raw-LZMA2 size of the qualified exact-deduplicated pool divided by the sum of
independently compressed story sizes. Geometric score is **0-100**, with the
previously fixed formula `100 * usable_unique_yield * sqrt(quality/9 * retention)`.
Semantic diversity remains a separate diagnostic, not a hidden score factor.

| World | Returned / Requested | Exact Unique | Mean Quality | Semantic Diversity | Plot Groups In Ten | Compression Retention | Geometric Score |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Puddles | 1000 / 1000 | 1000 | 8.00 | 4 | 5 | 5.55% | 22.22 |
| Pirates | 1000 / 1000 | 1000 | 8.00 | 3 | 3 | 5.59% | 22.28 |
| Quesadilla | 1000 / 1000 | 997 | 8.00 | 1 | 6 | 3.79% | 18.31 |
| Thud | 600 / 1000 | 600 | 7.90 | 4 | 6 | 4.41% | 11.80 |
| Dining | 1000 / 1000 | 999 | 7.00 | 3 | 6 | 4.44% | 18.57 |
| Garnet | 1000 / 1000 | 1000 | 8.90 | 5 | 6 | 3.71% | 19.15 |
| Grocery | 1000 / 1000 | 1000 | 7.40 | 3 | 6 | 4.35% | 18.90 |

Across seven worlds: **mean quality 7.8857/9**, **mean semantic diversity
3.2857/9**. All world means pass the current 6/9 quality floor. The 70 story
ratings were 17 sevens, 44 eights, and 9 nines; none fell below six.

The complete scoring pool contains **6,596 distinct stories / 7,000 requested**,
giving yield **94.23%**. Its assigned mean quality is **7.8849**, pooled
compression retention **5.0786%**, and geometric score **19.8761**. These use
the complete pool, not averages of the seven world-level composites. This
retention ratio differs from the earlier all-text XZ/input ratio of 2.88%.

## Cost And Timing

Actual returned usage: **27,652 input + 7,098 output tokens**, including 27,631
cache-write input tokens, zero cache reads, and zero reasoning tokens. At the
saved Terra/Flex rates, the seven calls cost **$0.07714775** in token-based
estimation. Individual calls took **8.49-10.77 seconds**; concurrency was five.
This is not an account invoice reconciliation or a general latency promise.

| Projection For One 21-World Trial | Estimated Cost |
| --- | ---: |
| Luna generation, scaled from 25 recent actual responses | $0.0800 |
| Ten-story Terra judging, scaled from these seven actual calls | $0.2314 |
| Combined empirical projection | **$0.3114** |
| Frozen-prompt planning estimate with measured judge token means | **$0.293-$0.321** |

Use **about $0.32 per attempt**, retaining $1 of planning headroom. This is not
a spending cap: longer generated stories/scripts, errors, retries, or explicit
re-evaluations can increase cost. Generated-world judge costs may differ from
these reference-world lengths. The pricing reference and full usage breakdown
are in the retained `cost_projection.json` and `summary.json`.

## Manual Reading Before Scores

All 70 selected stories were read before opening Terra's results. These are
qualitative observations, not a second independent numerical judge or a blind
human evaluation. The reviewing coding assistant knows the project and source
history. Story IDs below are zero-based positions in each world's retained
sample pool, as recorded in the judge inputs.

| World | Reading Assessment | Concrete Evidence |
| --- | --- | --- |
| Puddles | Complete, child-friendly stories with genuine state-dependent branches, but repetitive prose and occasional state-to-language mismatch. | `s000234` chooses drawing after forgetting gear; `s000770` retrieves gear and resumes play. `s000344` gets shoes rain-wet, then touches and washes a "mark" that was never established. Repeated "at the backyard" is awkward. |
| Pirates | A complete, engaging cautionary arc with three major outcomes, but extensive shared paragraphs and missed continuity. | `s000344` avoids lighting the flame; `s000234` has a contained fire; `s000456` loses the home. In the latter, "quiet afternoon" becomes "cold night air" without elapsed time. `s000344` clicks on glow sticks; space-play variants retain "whole cave" in a head-lamp description. |
| Quesadilla | Smooth bedtime prose and concrete closing images; weak semantic diversity despite nearly all exact strings being unique. | Every selected story follows snack missing -> clues -> adult moved it -> explanation -> shared snack. `s000377` and `s000276` repeat the warming-drawer case. In `s000550`, adding apple slices explains snack composition, not why it needed moving to the study. A spoon pointing toward a drawer is a convenient cue rather than an established causal clue. |
| Thud | Strong economical storytelling: a physical problem, complementary actions, visible repair. Several genuinely different microplots, despite heavy repetition within each one. | Wagon rescue (`s000377`, `s000550`, `s000560`); train/bridge repair (`s000234`, `s000589`, `s000398`); runaway cart, puppet stage, den, and birdhouse are distinct problems. Some rhymes/metre are uneven, but the prose is much less abstract than Dining/Grocery. |
| Dining | Several physical mechanisms, but an overly narrated detective template. Some evidence and character roles are not convincingly connected. | `s000234` tells an unnamed partner to watch, then calls them an alliance. `s000276` and `s000851` suspect a "clumsy spoon" without making it an agent. `s000344` proposes wind, then says they blamed a spoon. Repeated claims that the cause explains both the decorative display and wilting overstate what the clue proves. |
| Garnet | Strongest voice and playful causal developments in this selection. Different physical roles for the stone generate materially different problems and endings. | Leak/plug (`s000234`), reflected spot (`s000377`), stolen ornament/trade (`s000589`), seasonal map (`s000276`), shadow scare (`s000851`), bell balance (`s000770`). "The leak had no calendar" is purposeful humor, not generic connective prose. These remain fixed authored branches with interchangeable details. |
| Grocery | Meaningful logistics problems, but formulaic moral exposition and detachable secondary conflicts. Weaker story-specific grounding than the polished surface suggests. | `s000377` introduces a damaged marker without showing the damaging event, promises replacement, then resolves weighing without showing that repair. `s000851` concerns spilled rice but ends with oats supposedly rescued from that trouble. Many moral conclusions and safety checks can be swapped across cases without changing the physical resolution. |

The key expected distinction is **story quality versus corpus diversity**.
Quesadilla can read well individually while supplying little new narrative
structure. Conversely, Thud's smaller returned corpus should not hide that its
few core plots are more distinct than a much larger set of cosmetic variants.

No source or judge prompt was changed in response to these observations.

## Does The Scoring Make Sense?

**For diagnosing broad differences, yes. For final acceptance or a single
narrative-quality leaderboard, not yet.**

- The semantic ordering agrees with the manual reading: Garnet strongest,
  Puddles/Thud next, Quesadilla clearly weakest. Quesadilla's quality 8 versus
  diversity 1 is exactly the distinction that exact dedup misses.
- Terra notices Dining's case-report prose, arbitrary spoon suspicion and
  changing initial blame. It also notices Grocery's mechanically attached
  marker subplot. Those are useful, story-specific observations.
- Absolute quality is generous and coarse. Every selected Puddles, Pirates and
  Quesadilla story gets overall 8, despite the continuity defects above. The
  unchanged 6/9 floor rejects none of this reference sample. Seventy ratings
  come from seven shared-context calls, not seventy independent judge trials;
  clustering may reflect both similar stories and set-level anchoring.
- Some positive rationales invent stronger grounding than the text supports.
  Grocery `s000377` says they agreed to replace the marker, but does not show
  them doing it; Terra credits "replacing it" as a completed repair. In
  `s000550`, the newcomer is promised a role, but never contributes the missing
  knowledge on the page. Do not equate confident judge prose with verification.
- **Plot-group counts are not a comparable plot-diversity metric.** Terra gives
  Quesadilla six groups by relocation reason while correctly scoring its
  diversity only 1. Pirates' three groups are much more consequential. Group
  granularity is inconsistent across worlds. Even the evidence prose contains
  counting slips: Garnet says "five" while listing six structures; Dining's
  evidence omits the cabinet variant that appears in its valid six-group list.
  Use the actual structured groups for inspection, not claimed counts in prose.
- LZMA measures text reuse, not story meaning. Garnet is the best-read and most
  semantically diverse set here, yet has the lowest compression retention and
  ranks below Pirates/Puddles in the composite. This is not an arithmetic bug:
  Garnet repeats long authored passages within a small set of branches. Its
  quality/semantic benefit is not fully represented by a lexical-reuse metric.
- Thud's score is reduced by its 600/1000 yield. Holding its other measured
  components fixed would give 19.67 at unit yield rather than 11.80. That is an
  intentional dataset-yield penalty, not a claim that its individual stories
  are worse than Dining or Quesadilla. Do not pad it with duplicates to win back
  the missing yield.

## Next Calibration

Keep this baseline and protocol frozen. Recommended next judge version:

1. Require explicit checks for time/object continuity and distinguish proposed
   actions from actions actually completed before assigning high quality.
2. Define plot-group granularity with paired examples: relocation-reason swaps
   versus a different problem, intervention, or consequential outcome. Retain
   semantic scores and evidence; do not optimize the raw group count.
3. Pin these observed failures and matched corrected controls, then compare the
   old/new judge on identical inputs. Include same-story and cosmetic-swap
   controls for diversity, plus clearly different causal plots. A seven-world
   positive reference sample alone cannot calibrate the 6/9 rejection floor.
4. Compare the same-sized natural-story control and a second sample seed before
   changing compression normalization or the composite weights. Report quality,
   semantic diversity, retention and yield separately while doing so.

## Artifacts And Scope

Snapshot archive:
[`canonical_set_quality_20260907_terra.tar.gz`](../batch_archives/canonical_set_quality_20260907_terra.tar.gz),
with an adjacent SHA-256 sidecar, under the repository's existing Git LFS rule.
It retains the new evaluation, this report, and scoring code. The full 6,600
sample corpus remains in the earlier `canonical_compression_20260907.tar.gz`
archive; it is referenced rather than duplicated here.

- `canonical_set_quality_20260907_terra/inputs.json`: all 70 reviewed stories and
  their source indices, selection seed and pool hashes.
- `requests.jsonl`, `attempts.jsonl`, `response_*.json`, `quality.jsonl`: exact
  paid inputs, durable attempts, raw responses, and validated ratings.
- `source_checks.json`, `dataset_scores.json`, `baseline_table.json`: local
  verification, source fingerprints, and reproducible full-pool score.
- `analyze.py`: offline reproduction of the score and cost projection, using
  the separately retained `canonical_compression_20260907_v2` corpus.
- `cost_projection.json`: measured usage and the 21-world budget projection.

The subsequent 21-world Luna generation attempt was blocked before execution
by automatic approval review, pending explicit authorization for the expanded
generation-plus-judging scope. No new 21-world scripts or generation charges
were produced in this reference-baseline run.
