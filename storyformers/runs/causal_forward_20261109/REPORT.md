# Causal story through Storyformer

Run on 2026-11-09, locally on macOS ARM64 with Python 3.12.13. No annotation API
calls, training, GPU computation or changes to the saved checkpoint.

**The complete story passed through:** 753 words plus 170 punctuation records,
with 750 spaces omitted from the model stream. Original lossless positions and
IDs remain intact. The 17 reviewed records replace their corresponding source
positions; they are not concatenated into a fictitious 17-word context.

## Actual model used

- Two layers, each with 16 slots: **3 catalog seed heads + 7 learned heads**,
  with 22 unused slots. The catalog seeds derive determiner kind, definiteness
  and cardinal value. The learned heads come from the existing synthetic run.
- **10 head rules**, plus **171 output rules across 19 vocabulary neurons**.
- The saved learner's context bound is 16. A separate in-memory model widens
  wildcard `Gap` bounds to 256; weights, projections and other conditions stay
  the same. Identical original-length inputs produce identical outputs.
- Input is the causal Luna v2 story with 17 reviewed v3 replacements. This is a
  wiring/performance dataset, not a uniformly regenerated v3 training corpus.

This measures the existing prototype, not the proposed 24-layer system with
64 grammars per head and a 32k-token vocabulary. No large-model timing is inferred.

## Timings

Measured wall time includes residuals and traces. Input/model loading and artifact
writes are excluded. Setup took 0.17 seconds. These are local development-machine
measurements, not an isolated hardware benchmark.

| Context records | Next-token distribution only | Predictions at every position |
|---:|---:|---:|
| 5 | 7.8 ms | 18.7 ms |
| 16 | 35.0 ms | 134.9 ms |
| 64 | 313.9 ms | 1.663 s |
| 256 | 4.692 s | 30.927 s |

For 5/16/64 and the 256-context next-token call, values are medians of three
repetitions on the same trailing context. The 256-position forward value is the
median of three different full-size story segments: 31.124, 30.176 and 30.927
seconds. The fourth segment had 155 positions and took 10.771 seconds.

**Whole-story forward:** 102.999 seconds for all 923 positions, or 8.96 records/s
(7.31 words/s). This is a batch-style pass over **four independent segments**:
256 + 256 + 256 + 155. Context resets at segment boundaries. It is not a rolling
256-context decoding run, and calling `forward()` on the entire story would only
return its final context window in the current runtime.

**Whole-story rolling prediction, unchanged 16-context checkpoint:** 28.779
seconds for 923 steps, or 32.07 records/s (31.18 ms/step). This runs an actual
bounded sliding window at each position. It recomputes layers; no KV cache exists.

Peak process resident memory was **98.5 MiB**, including retained results and
profiling. This is not a model-weights-only memory estimate.

## What happened to the latents

All 923 positions produced nonempty, normalized joint distributions and top-ten
token distributions. Sequence length, source tokens and positions survived.
All input fields not written by the installed heads survived unchanged, including
the **9 plot bundles and 2 depiction bundles**. Inputs and checkpoint files
remained unchanged, verified by content hashes.

There were **945 head activations**, changing 757 positions:

| Learned or catalog feature | New fields / activations |
|---|---:|
| Noun detector `__grammar_1` | 223 |
| Punctuation detector `__grammar_2` | 170 |
| Verb detector `__grammar_4` | 153 |
| Adjective detector `__grammar_5` | 53 |
| Adverb detector `__grammar_6` | 28 |
| Determiner detector `__grammar_7` | 130 |
| Newly supplied `definiteness` | 23 (91 total activations) |
| Newly supplied `determiner_kind` | 8 (92 total activations) |
| Cardinal-value projection | 5 activations, reinforcing existing fields |

The proper-name detector `__grammar_3` did not activate: the synthetic checkpoint
expects `pos="pn"`, while the annotation contract uses `pos="n"` for proper nouns.
That convention mismatch needs reconciliation in future training; this probe
does not silently retag the annotated story.

At `wanted`, the verb head adds `__grammar_4=true` while the existing goal and
`plot.role="desire"` remain intact. At the final drawn salamander/triangle, the
depiction objects survive with their distinct carrier/image/reference IDs.

Separate diagnostic neurons successfully matched and copied all 11 nested
`plot`/`depiction` bundles using the normal `GrammarNeuron`/`Ref` mechanism. These
copy probes were not installed in the timed model. The measured heads themselves
do not reason over these bundles or query the companion entity/event tables.

## Output quality and dimensions

Residuals are still **one sparse dictionary per supplied position**, with
variable field counts. The readout returns up to ten token probabilities and
their complete candidate dictionaries per position, with full joint mass retained
internally before truncation. It is not a dense 1,033-dimensional numeric vector.

The distribution is structurally valid but still uses the **19-word synthetic
vocabulary** and token/POS supervision. For example, after `wanted`, it predicts
`the` at about 50.2%, `small` at 19.8%, and `red` at 15.0%; the story's next word
`to` is outside its vocabulary. At a noun it strongly predicts a full stop.
The final punctuation yields about 99.34% END, which is the synthetic pattern,
not evidence that the model understood the story's resolution.

Output candidates contain the required core keys, but rich semantic fields are
not reconstructed by this learned projection. Passing rich annotated inputs
through the residual stream does not yet give rich autonomous generation.

## Where the time goes

The separate [64-position profile](profile.txt) took 6.06 seconds with profiling
enabled, versus 1.66 seconds unprofiled; profile times are excluded from the table.
About **82% of profiled cumulative time was under the output readout**, with
about 18% under the two blocks.

The profile recorded 2,185 calls to position calculation and about 3.97 million
recursive `deepcopy` calls. Each output grammar activation currently recomputes
positions over the history and copies its dictionaries before identical output
bundles are merged. Grammar matching also repeatedly scans/enumerates wildcard
prefixes. These costs grow rapidly with context length.

The first optimization targets are to reuse positional state across candidate
activations, share immutable residual snapshots instead of copying every prefix
for every head, and compile/cache the query-anchored grammar matches. None of
those optimizations has been applied here; these are measurements of the current
implementation. The architectural feature count cannot be used to extrapolate
transformer-equivalent throughput from this interpreter.

## Reproduce and inspect

```sh
.venv/bin/python -m storyformers.benchmark_annotated \
  --out storyformers/runs/my_causal_forward
```

- [Machine-readable report](report.json): samples, configurations, checks, hashes and memory.
- [Input latents](input.json): exact nonspace stream used in the model.
- [Segment 1](segment_00.json), [2](segment_01.json), [3](segment_02.json),
  [4](segment_03.json): residual dictionaries, every head firing and per-position
  top-ten candidate distributions.
- [Rolling predictions](rolling_predictions.json): all 923 outputs from the
  original 16-context checkpoint.
- [Corrected reference snapshots](corrected_reference_snapshots.json): supporting
  tables for the 17 reviewed replacements. Other tables remain in the original
  prefix annotation run; no retrospective global table was inserted into inputs.

The probe checked input preservation, normalized distributions, protected
positions, nested-bundle survival/copying, short-context equivalence after
widening, and sampled block prefix invariance. **28 existing transformer/catalog
tests passed.** Core model code and saved weights were not changed.
