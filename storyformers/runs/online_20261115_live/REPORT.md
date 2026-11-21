# Ten live online grammar-learning iterations — 2026-11-15

Ten real teacher calls completed, using the user-approved `gpt-6-luna` model. Six patches were accepted, adding twelve output grammar productions. Four iterations kept only their weight updates. No new heads or attributes were proposed. The results support small local repairs, not complete one-shot story learning.

## Protocol

Each iteration predicts one target latent from a strictly causal prefix, records that prediction, reveals the target, takes one output log-weight gradient step, asks Luna for a structured grammar patch, then compares unchanged/weight-only/teacher candidates against the current observation and replay. Generation itself makes no LLM calls. This is discrete teacher-directed program repair following an ordinary weight backward pass; it is not differentiation through the teacher.

The warm start is the existing sentence checkpoint, expanded to context 32 and a declared 60-token/POS inventory with uniform tiny mass for new outputs. There is one layer with 16 head slots and one occupied head. The separate sentence dataset and source checkpoints were not edited. No presentation outcome counts from the earlier trained presentation model were imported.

The [ten-example curriculum](../../data/online_presentation_10.json) was fixed before live calls: one observation in each of ten training stories, chosen by initial-model loss within a planned presentation section. Each call sees its prefix and target, not ten full stories or their future suffixes. The gate uses 12 anchor positions from two original sentence examples plus up to 16 prior online observations. The teacher packet includes the most recent eight replay examples. The teacher brings pretrained English knowledge; these are not discoveries solely from ten labels.

The gate requires improved current-target probability, full replay coverage, no additional observed-field conflicts, and at most 0.02 nats average replay regression relative to the pre-update model. It penalizes added syntax. This finite replay gate is provisional and cannot establish generalization or prevent all cumulative forgetting.

## All ten iterations

Probabilities below are for the observed token/POS target. “After” has already used the answer and is a repair diagnostic, not a test prediction.

| Iteration | Target | Adopted | Probability before → after | Change |
|---|---|---|---|---|
| [1](step_000/decision.json) | `and` | weights_only | 0.000198 → 0.000254 | No structural proposal: conjunction after a name is ambiguous. |
| [2](step_001/decision.json) | paragraph break | weights_only | 0.000062 → 0.000092 | No structural proposal: noun phrase does not establish a title boundary. |
| [3](step_002/decision.json) | `,` | teacher | 0.000075 → 0.646532 | Added comma after “Once upon a time”. |
| [4](step_003/decision.json) | `Ben` | teacher | 0.000165 → 0.107355 | Added proper-name alternatives after a comma, across all four names. |
| [5](step_004/decision.json) | paragraph break | weights_only | 0.000092 → 0.000136 | Valid paragraph-break rule rejected by adapter bug; weight update retained. |
| [6](step_005/decision.json) | `!` | teacher | 0.000091 → 0.497289 | Added exclamation after “Until next time”. |
| [7](step_006/decision.json) | `ago` | teacher | 0.000185 → 0.280505 | Added “ago” after “Long”. |
| [8](step_007/decision.json) | `ended` | teacher | 0.000111 → 0.252770 | Added “ended” after “story”. |
| [9](step_008/decision.json) | `<END>` | weights_only | 0.990967 → 0.990984 | No structural proposal: END was already strongly predicted. |
| [10](step_009/decision.json) | `Ben` | teacher | 0.119436 → 0.171185 | Added four proper-name alternatives after “Once upon a time,”. |

Mean loss recorded before each update: **7.486 nats**, accuracy **10.0%**. The curriculum deliberately selects difficult training positions, so this is not an unbiased corpus estimate. Total live training/replay time: **199.6 seconds**.

## Frozen held-out evaluation

The model was frozen before evaluating the first eight validation and first eight test stories. An independent weight-only control receives the same observations and replay gate. Loss is joint token/POS NLL in nats (lower is better); accuracy measures the highest-probability joint latent.

| Split | Targets | Initial NLL / accuracy | Weight-only NLL / accuracy | Teacher NLL / accuracy |
|---|---:|---:|---:|---:|
| validation | 184 | 4.825 / 23.4% | 4.648 / 23.4% | 4.258 / 25.0% |
| test | 171 | 5.134 / 22.2% | 4.945 / 22.2% | 4.388 / 25.1% |

All evaluated models retained 100% target coverage and zero observed-field conflicts. The test improvement over the weight-only control is 0.557 nats and 2.9 percentage points of accuracy. The sample is small and from one synthetic presentation generator; it does not establish general language learning. See [raw evaluation](evaluation.json).

## Unfiltered generation

Empty prompt, seeds 0–2, maximum 40 new tokens, stopping on END. Each row below is the full rendered output; no hand-picked replacements.

| Model | Seed | Output |
|---|---:|---|
| initial | 0 | Tom found the red needles. |
| initial | 1 | Ben took the red pears. |
| initial | 2 | Tom took red apples. |
| weights_only | 0 | Tom found the red needles. |
| weights_only | 1 | Ben took the red pears. |
| weights_only | 2 | Tom used red needles. |
| teacher | 0 | Tom found the red needles. |
| teacher | 1 | Ben took the red pears. |
| teacher | 2 | Tom used red needles. |

**Complete title/opening/closing framing: 0/3 for every model.** The teacher learned useful conditional continuations, but the samples never reach those contexts on their own. Title and boundary observations were insufficient to establish a reusable document-phase representation. The next experiment should test a learned phase feature with coordinated head/readout edits, additional boundary evidence, and independent held-out stories. No such feature was authored into this run. [Full latent samples](samples.json).

## Adapter defect and separate recheck

Iteration 5 proposed a paragraph separator after punctuation when an earlier separator was visible. Its output root is literally whitespace. The internal rule-fragment parser incorrectly reused that whitespace as a neuron name, then rejected it as blank. Fixed the adapter to parse the fragment under a temporary descriptive name while preserving the actual output token/root. A regression test covers whitespace outputs.

The [counterfactual check](adapter_repair_check.json) reconstructs the exact original post-gradient snapshot and replays the saved proposal with the fixed adapter. It would pass the original gate (target probability about 0.498; replay NLL 2.130 versus 2.123 before the update). This used no API call and did not modify the historical decisions or final model. The reported six adoptions and evaluation therefore exclude this repair.

## API usage, cache and budget

- Ten completed, settled calls; served model `gpt-6-luna`, service tier `flex` on every response. No Standard fallback or unsettled reservations.
- Identical instruction/syntax/example/vocabulary prefix first, explicit breakpoint, stable cache key, 30-minute TTL. First call wrote **2,758 tokens**; subsequent **9/9** calls read that prefix, totaling **24,822 cached tokens**.
- Total input **94,859 tokens**; total output including reasoning **12,606 tokens**.
- Estimated API cost **$0.006812**; conservative settled ledger **$0.007653**, under the user-approved **$10** ceiling. These are usage-based estimates, not a billing invoice.
- The run is serial. The async API adapter supports concurrent requests with shared budget reservations; proposals require exact model snapshots, so future parallel adoption still needs revalidation and serialized commits.

Pricing uses the [official Luna model rates](https://developers.openai.com/api/docs/models/gpt-6-luna) and Flex discount, verified for this run: per million tokens, $0.05 input, $0.005 cache reads, $0.0625 cache writes, $0.25 output. [Budget ledger](budget.json), [audit](audit.json), and each step’s receipt preserve the measured usage. Raw requests/responses stay local under the repository’s existing cache policy.

## Reproduction and checks

```sh
.venv/bin/python -m storyformers.online_experiment \
  --model gpt-6-luna --budget 10 --steps 10 \
  --curriculum storyformers/data/online_presentation_10.json \
  --out /tmp/storyformer-online-new-run
```

This makes a new paid run, whose teacher proposals may differ. The adapter fix also changes handling of whitespace proposals relative to this historical run. Reusing the original directory resumes its committed decisions rather than resubmitting the ten calls. Do not extend training based on these test results and continue treating this same test subset as fresh.

All **150 Storyformer tests passed**. The audit verifies every source hash, the ten-checkpoint model chain, request fingerprints, usage receipts, shared cache prefix, and final checkpoint fingerprint. Original data and checkpoint hashes match the [manifest](manifest.json).

[Training report](training_report.json) · [final model](final_model.json) · [weight-only model](weights_only_model.json) · [algorithm and API protocol](../../ONLINE.md)
