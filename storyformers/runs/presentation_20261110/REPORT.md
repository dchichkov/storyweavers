# Story-presentation learning pass

Added a separate presentation corpus and trained two new checkpoints. The existing sentence datasets and both sentence checkpoints are unchanged. No LLM or runtime authoring was used.

## Data and protocol

192 training documents (4,219 targets), 64 validation documents (1,420 targets), and 64 test documents (1,374 targets); 60 word/control tokens. Each copied sentence gets one of four title styles, six openings, and six closings. Literal paragraph breaks are predicted tokens.

The original subject/verb split is retained. Opening/closing combinations are also disjoint between splits; all individual forms occur in training. Only token/POS records reach the learner. Section spans and template IDs are evaluation metadata.

Example from the training corpus:

```text
Ben's red apples

Once upon a time, Ben ate the red apples.

The End.
```

Both runs use the existing data-only grammar inducer: one residual layer, context 32, suffix lookback 3, up to two literals per condition, and 80 output-weight updates. The smaller run exhausted its 16-condition budget mostly on POS predicates. Its validation failures motivated the 64-condition run; no authored presentation grammar was added.

The [validation selection record](comparison.json) selects the larger model. Its 64 conditions comprise 63 active heads and one empty-context readout condition. This is a larger bank of heads, not multiple experts per head. The training files are byte-identical between these two runs.

## Held-out results

Full joint token/POS likelihood is scored before top-ten truncation. Lower NLL is better.

| Model | Validation NLL | Test NLL | Test joint accuracy |
| --- | ---: | ---: | ---: |
| Unigram | 3.824 | 3.829 | 9.3% |
| Lexical bigram | 1.143 | 1.198 | 49.9% |
| 16-condition Storyformer | 1.790 | 1.827 | 30.7% |
| 64-condition Storyformer | 1.069 | 1.103 | 57.0% |
| 64-condition model, heads removed | 3.724 | 3.727 | 10.5% |

All models cover every test target. Section accuracies retain the preceding story context:

| Section | 16 conditions | 64 conditions |
| --- | ---: | ---: |
| title | 24.9% | 45.1% |
| title break | 0.0% | 87.5% |
| opening | 20.0% | 56.7% |
| body | 44.2% | 41.7% |
| closing break | 0.0% | 65.6% |
| closing | 26.2% | 66.7% |
| end | 100.0% | 100.0% |

## Generation assessment

Neither model passed the complete-framing check on any of the six fixed unprompted seeds (0/6 each). The larger model produces recognizable opening and closing phrases but still mixes their words, changes protagonists between title and body, repeats paragraph breaks, or stops before the closing. Better teacher-forced likelihood has not yet become reliable whole-story formatting.

The largest improvement is in presentation tokens; body accuracy falls from 44.2% to 41.7% in this experiment. This is not a regression to the existing sentence checkpoint, which was never updated. A future joint training experiment should explicitly retain sentence quality.

The exact-template framing check is deliberately narrow: a novel grammatical closing can fail it. It also does not check title/body agreement or body grammar. The unfiltered text below shows why this result should still be described as fragments rather than successful story framing.

For example, the first prompted closing is “That is where our story ended.”
This is a grammatical recombination of the training closings, despite failing
the exact-template check. Its title, opening, and body were supplied as context.

The next learning target is persistent knowledge of which section is being written, plus carrying title entities into the body. Merely increasing the context limit would not do that: these induced predicates still read only the last three records. This follow-up was not implemented in this pass.

## Timing and checks

Grammar selection and weight fitting took 9.0s for 16 conditions and 14.7s for 64. Including evaluation and generation, the runs took 219.0s and 225.7s respectively. The first run used full-prefix evaluation caching; the larger run caches joint scores by the known three-record read scope, so end-to-end times are not a like-for-like scaling benchmark.

139 Storyformers tests pass, including new split-isolation, literal-layout, checkpoint, causal-prefix, and cache-equivalence checks. Source hashes match before and after both runs; Git also confirms no changes to the sentence corpus, generator, or learning checkpoints.

## Artifacts and reproduction

- [Training protocol and implementation notes](../../PRESENTATION.md)
- [Training records](train.jsonl), [validation records](validation.jsonl), [test records](test.jsonl), and [human-readable corpus metadata](metadata.json)
- [Small-model report](report.json) and [raw small-model samples](samples.json)
- [Selected checkpoint](../presentation_20261110_capacity64/model.json), [learned rules and support](../presentation_20261110_capacity64/rules.json), [report](../presentation_20261110_capacity64/report.json), and [raw samples](../presentation_20261110_capacity64/samples.json)

```sh
.venv/bin/python -m storyformers.presentation --out /tmp/presentation-16
.venv/bin/python -m storyformers.presentation --heads 64 --out /tmp/presentation-64
```

## All selected-model samples

Each case uses the normal model generator, top-ten token/bundle sampling, and at most 56 new tokens. No rejection, repairs, or insertion of missing formatting. Prompted cases contain a supplied title or supplied body and must not be treated as unprompted generation. Raw prompt and generated records are retained in samples.json.

### unprompted, seed 0

END reached: True. Complete framing: False.

```text
Mia's small needles

One morning, Lily and the small needles

In a time ended apples ended the end.
```

### unprompted, seed 1

END reached: True. Complete framing: False.

```text
A day with a

One day, Ben quickly took the end with a

And that was red apples.

And so the red day.

And so the story ended small
```

### unprompted, seed 2

END reached: True. Complete framing: False.

```text
Tom took red apples.

On a sunny pears, Ben slowly found the story ends.
```

### unprompted, seed 3

END reached: True. Complete framing: False.

```text
A day with Lily

Long ago, Lily quickly used the needles.
```

### unprompted, seed 4

END reached: True. Complete framing: False.

```text
A End with a small day, Tom ate small pears.

And so found the needles. Tom And that was pears with now

On a little day,

found the red scissors.

That is where, Lily quickly found the red apples.

The End.
```

### unprompted, seed 5

END reached: True. Complete framing: False.

```text
Ben's apples ended the scissors.

This is all for now our story ended red pears.

Until next time!
```

### after_title, seed 0

END reached: True. Complete framing: False.

```text
Tom and the scissors

On a sunny day, Lily found the small pears

One day, Mia quickly used.
```

### before_closing, seed 0

END reached: True. Complete framing: False.

```text
Tom and the scissors

One morning, Tom slowly took the scissors.

That is where our story ended.
```

### after_title, seed 1

END reached: True. Complete framing: False.

```text
The needles

Once upon a time, Lily's apples! Ben ate the end with a

And that was red apples.

And so the red day.

And so the story ended small
```

### before_closing, seed 1

END reached: True. Complete framing: False.

```text
The needles

On a sunny day, Mia slowly found the needles.

And that was where end.
```

### after_title, seed 2

END reached: True. Complete framing: False.

```text
Tom's red scissors

Until End sunny day.

On a sunny pears, Ben slowly found the story ends.
```

### before_closing, seed 2

END reached: True. Complete framing: False.

```text
Tom's red scissors

One day, Tom took red scissors.

This was red apples.

On a sunny pears, Ben slowly found the story ends.
```
