# Agent-guided Storyformer learning emulation — 2026-11-09

We ran forward passes, inspected training evidence, proposed grammar changes, fitted output weights, and rejected or adopted revisions. This continues the saved synthetic baseline; it is not a fresh model or a production training scheduler. The agent supplied the structural hypotheses after inspecting each round. No live Luna/API calls were made.

## Data and learning protocol

- 192 training stories, 64 validation stories, and 64 test stories; the existing subject/verb-pair split keeps combinations disjoint. All words are known in training. The same test split was evaluated by the earlier baseline experiment; it supplied no examples, counts, or adoption decisions in this continuation.
- Targets contain token and POS only. Every causal position is scored, including empty prefixes and END. The model has context 16, one layer with 16 head slots, and a 19-token vocabulary.
- Three 64-story batches supply 433, 447, and 431 target positions. Proposal counts accumulate over 64, then 128, then 192 stories. Weight updates replay all 192 previously seen training stories, avoiding forgetting caused by fitting only the current batch.
- Each candidate and its weight-only control receive 80 full-batch output-log-weight steps at learning rate 4. Head weights remain fixed. Cached derivations are rebuilt after structural edits; full joint probabilities are used before top-ten truncation.
- Adoption compares validation loss against both the equally trained control and unchanged checkpoint, with a fixed complexity charge of 0.00001 nats per additional grammar node. Validation is used for selection; its examples are excluded from proposal evidence.
- The final checkpoint was frozen before test evaluation. No changes were selected from the test results.

## What inspection changed

1. All seven original heads copied POS into private booleans. Their consumers now read canonical POS directly. Comparing every training and validation prefix found exactly zero probability difference; seven head slots were freed.
2. The first new head copied the preceding verb across determiners/adjectives into `preceding_verb_surface`. Its readout productions counted each verb/current-POS continuation separately. This helped likelihood but added too much grammar for the gain.
3. Pooling two batches and omitting redundant null outputs still failed the complexity-adjusted acceptance gate.
4. The accepted proposal separates **when a noun occurs** from **which noun occurs**. It preserves the old total noun mass for each POS condition and redistributes that mass using smoothed verb/noun counts pooled across modifiers. One head and 12 replacement readout rules implement this; no extra output rules are needed. The noun sets/preferences come from training counts, not an authored list of tools or foods. The structural factorization and feature name were proposed by the agent.

| Revision | Candidate validation NLL | Equal-fit control NLL | Added complexity charge | Decision |
|---|---:|---:|---:|---|
| Separate continuation tables | 1.035956 | 1.041751 | 0.00598 | Keep weight-only update |
| Pooled evidence, compact outputs | 1.036118 | 1.039438 | 0.00450 | Keep weight-only update |
| Factored noun choice | 1.017961 | 1.037964 | 0.00142 | Adopt grammar |

The three comparison rounds took 25.6 seconds total in the recorded run, including fitting, evaluation and artifact writes; setup, initial diagnostics, compaction checks, and final test evaluation are outside that timer.

An earlier [batch-only pilot](pilot_batch_only/disposition.json) fitted just 64 stories and regressed against the starting checkpoint, although it beat its equally degraded control. It is superseded and retained for inspection. That failure prompted both training replay and the unchanged-checkpoint guard, now also applied to the existing single-neuron review evaluator.

## Frozen test results

64 stories, 433 prediction targets. Lower NLL is better. Accuracy is joint token/POS top-one accuracy; coverage means the target has nonzero probability, not that its prediction is correct.

| Model | Joint NLL | Perplexity | Joint accuracy | Coverage |
|---|---:|---:|---:|---:|
| initial | 1.060334 | 2.8873 | 52.42% | 100% |
| weights_only | 1.052050 | 2.8635 | 52.42% | 100% |
| revised | 1.027688 | 2.7946 | 53.35% | 100% |
| carrier_ablated | 1.426569 | 4.1644 | 49.65% | 100% |
| carrier_values_permuted | 1.168045 | 3.2157 | 51.04% | 100% |

The final model has **one active head, 19 output neurons, and 171 output rules** (172 rules including the head). The original had seven active heads and 178 total rules. POS accuracy remains 83.83%; this revision improves lexical noun selection rather than demonstrating broader syntax learning.

Conditioning on a noun being next, the probability assigned to tools after `ate` fell from 52.89% to 2.10%; fruit after `used` fell from 46.79% to 1.54%. These diagnostics cover only seven `ate` and eight `used` test targets. The report records them more conservatively as mass on verb/noun pairs absent from training. They are not universal semantic restrictions.

Removing the new head disables its consumers, which worsens loss but also changes their activation coverage. A second intervention preserves head firing and permutes its copied verb values (alphabetically reversed mapping). Its test NLL is 1.168045 with POS accuracy unchanged, supporting that the copied information matters, beyond head presence alone. These interventions do not retrain the model.

## Inspection artifacts

- [Starting all-position diagnostics](initial_diagnostics.json)
- [Compaction proposals](replay/compact_proposals.json) and [equivalence check](replay/compact_evaluation.json)
- [Accepted paired head/readout proposal and training counts](replay/carrier_revision_03.json)
- [Final head evidence, ablations, examples and consumers](replay/final_head_profile.json)
- [Frozen model](replay/final_model.json)
- [Full test metrics, six fixed prediction samples and eight fixed-seed generations](replay/final_evaluation.json)
- [Exact replay verification](replay/reproducibility.json)

Generation is still limited. One of the eight saved samples is `Tom found the red small pears . <END>`, exceeding the synthetic teacher's one-adjective template. All samples are retained; no test-driven repair was made. Actor, object, event, and other rich annotation fields have not been learned in this experiment. Generic English grammar, multi-sentence state tracking, and automatic structural proposal scheduling remain open.

## Reproduce and verify

```sh
.venv/bin/python -m storyformers.learning_emulation --out /tmp/storyformer-learning
.venv/bin/python -m unittest storyformers.test_learning storyformers.test_transformer storyformers.test_induction storyformers.test_neuron_review
```

Use a fresh output directory. The reviewed structural revisions are replayed explicitly, so this command does not make new LLM proposals. The original induction checkpoint is read-only. **54 tests passed**, covering numerical full-joint gradients, causal/windowed execution, stale evidence, rich typed target support, safe POS rewiring after serialization, the factored noun-mass invariant, and regression rejection against an unchanged checkpoint.

A separate fresh end-to-end replay produced an exactly matching checkpoint fingerprint and identical test metrics. See `replay/reproducibility.json` for the verification record.
