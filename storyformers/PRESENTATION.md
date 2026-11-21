# Learning story presentation separately

`presentation.py` builds a new corpus and trains a fresh grammar model. It reads
the saved sentence-training splits under `runs/induction_baseline/` without
changing them, their checkpoint, or the later sentence-learning checkpoint.
This is an additional experiment, not a replacement for sentence training.

```sh
.venv/bin/python -m storyformers.presentation --out /tmp/storyformer-presentation
.venv/bin/python -m unittest storyformers.test_presentation
```

The output directory must be empty. `--seed`, `--heads`, and `--weight-steps`
control presentation assignment, head capacity, and output-weight fitting.
`--source` can select another saved token/POS sentence corpus with
`train.jsonl`, `validation.jsonl`, `test.jsonl`, and `model.json`.

## Training examples

Each original sentence is copied into a document with a title, opening phrase,
body, closing, and one END target. The default corpus has 192 training documents,
64 validation documents, and 64 test documents. One actual training example is:

```text
Ben's red apples

Once upon a time, Ben ate the red apples.

The End.
```

Titles use four styles: a name and object, an object title, a possessive title,
and “A day with [name]”. Names, objects, and adjectives come from the copied
sentence, so the training title and body agree.

The six openings are “Once upon a time,”, “One day,”, “One morning,”, “Long ago,”,
“On a sunny day,”, and “In a little village,”. The six closings are “The End.”,
“And that was the end.”, “That is all for now.”, “Until next time!”,
“And so the story ended.”, and “This is where our story ends.”

The files contain only `token` and `pos`. A paragraph break is the literal token
`"\n\n"` with POS `space`. It is a next-token target like every word and
punctuation mark. Ordinary inter-word spaces are restored by the display helper;
no opening, closing, or line break is inserted after generation. `<END>` remains
the separate stopping token, after the closing punctuation.

`metadata.json` contains section spans, template IDs, source row numbers, and
readable text for inspection and scoring. These fields never enter the model.
In particular, the learner does not receive an oracle “now write the closing”
attribute. Position features are still computed locally by the existing model.

## Training protocol

1. Preserve the existing subject/verb train, validation, and test partitions.
   Also separate opening/closing pairs: `(opening_id + closing_id) % 4` assigns
   groups 0–1 to training, 2 to validation, and 3 to test. Individual openings,
   closings, and all token/POS labels occur in training; held-out combinations
   and sentence pairs test composition. No full document crosses splits.
2. Propose token/POS equalities and conjunctions from training prefixes using
   the existing ILP-inspired inducer. The teacher's text templates are not
   supplied as executable grammars. Every target is excluded from its context.
3. Use one layer with 16 head slots, a 32-record context, three-position
   lookback, at most two literals per condition, and at most 16 selected
   conditions. An empty-context condition uses the readout directly rather than
   a head slot. Validation vetoes non-improving structural proposals.
4. Fit output log weights for 80 steps at the inducer's default learning rate
   of 4. Vocabulary, rule support, and weight updates come from training only.
   Freeze the checkpoint before evaluating test data.
5. Compare full joint token/POS likelihood and accuracy against the training
   unigram, lexical bigram, and the same checkpoint with heads removed. Report
   losses separately for titles, openings, bodies, closings, both paragraph
   boundaries, and END. Section scoring retains each target's complete causal
   prefix; it does not restart the model at a section boundary.
6. Generate six unprompted samples with seeds 0–5, plus three continuations
   after a held-out title and three just before a held-out closing. Use the
   model's normal top-ten joint sampling, capped at 56 new tokens. Retain all
   outputs without rejection or repairs, including malformed and truncated ones.

The report includes corpus/checkpoint hashes, learned rules with support and
gains, selection losses, held-out metrics, timings, and raw generated latent
records. The framing check requires three nonempty paragraphs, a known opening,
a known closing, and END. It measures the learned format, not title/body
agreement, sentence grammar, or narrative quality. Prompted results include
supplied framing and must be distinguished from unprompted success.

Scoring caches joint token/POS distributions by the last three input records.
This is exact for these particular induced models: all head predicates read
only those offsets, and output productions consume the resulting flags on the
last residual. Each cache miss still executes the full causal prefix. A test
compares cached and uncached section scores. This shortcut is not applicable
to arbitrary future models with longer-range heads.

This first pass learns token/POS presentation patterns. It does not train rich
semantic labels, plots, or a persistent presentation-phase attribute. Its
one-sentence bodies are deliberately kept small so failures of the framing
model are visible.

## Capacity follow-up

The 16-condition run used its budget mostly on broad POS transitions and had
31.1% validation accuracy. That evidence motivated a second run on identical
data with 64 head slots and a 64-condition budget:

```sh
.venv/bin/python -m storyformers.presentation --heads 64 --out /tmp/storyformer-presentation-64
```

The larger candidate reached 58.2% validation accuracy and reduced validation
joint NLL from 1.790 to 1.069. The [selection record](runs/presentation_20261110/comparison.json)
chooses it by validation likelihood with full coverage, without using test scores
or generations as selection criteria. It has 63 active heads plus one learned
empty-context condition in the readout. This changes head capacity within this
isolated experiment; it does not implement multiple experts per head or alter
the original sentence model.

The first run lives in [`runs/presentation_20261110/`](runs/presentation_20261110/),
and the selected checkpoint and samples are under
[`runs/presentation_20261110_capacity64/`](runs/presentation_20261110_capacity64/).
