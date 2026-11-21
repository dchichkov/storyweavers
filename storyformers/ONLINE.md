# Online teacher-directed grammar learning

This prototype makes a teacher proposal after each individual symbolic
backward pass. It is separate from the saved sentence and presentation
experiments; their data and checkpoints are read-only inputs.

## One observation at a time

1. Predict the next complete latent from its causal prefix and record the full
   joint target probability **before updating anything**.
2. Reveal that target. `LearningBatch(..., pairs=[(prefix, target)])` takes one
   output log-weight gradient step. Prefix tokens are context, not additional
   training observations in that step.
3. Give the teacher the prefix, revealed target, before/after predictions,
   largest weight changes, residuals, active head trace, head definitions,
   relevant output grammars, typed feature registry, and earlier replay cases.
4. The teacher returns a bounded JSON patch. It can revise up to two heads,
   introduce up to four typed fields, and append/reweight productions in up to
   eight vocabulary roots. A head and its consumers are staged atomically.
   Existing attribute meanings and observed fields remain protected.
5. Compare the unchanged model, the weight-only update, and the teacher patch.
   Require better probability for the current target, full replay support,
   no additional observed-field conflicts, and at most 0.02 nats of average
   replay regression per observation. Penalize added syntax by 0.001 nats per
   node. Select the best eligible candidate; a no-op or rejection is legitimate.
6. Commit the checkpoint and decision journal, then advance to the next target.

This is provisional one-example learning. The replay gate limits forgetting;
it does not prove generalization. Small tolerated regressions can accumulate,
and a finite replay buffer cannot protect every prior behavior. Before-update
loss is the online metric; improved probability after seeing the answer is a
repair diagnostic. The teacher can use English knowledge to generalize, so this
is not grammar induction solely from one observed sentence.

`online.py` contains the local algorithm; `online_teacher.py` contains API and
budget handling; `online_experiment.py` runs the reproducible pilot.

## Pilot setup

Start from the existing sentence-learning checkpoint, expand its context from
16 to 32 by widening wildcard gaps, and declare the presentation corpus's known
token/POS inventory. New lexical outputs receive uniform mass 0.01, without
using presentation outcome counts or the previously trained presentation model.
This is a warm-start experiment with known vocabulary, not learning all words
from scratch.

Without a curriculum, the default 24 steps expose exactly the first presentation
training story, one next-token label at a time. The ten-iteration live experiment
uses `data/online_presentation_10.json`: one selected prefix/target from each of
ten training stories, covering titles, openings, bodies, closings and boundaries.
The schedule was selected using initial training errors before any teacher calls.
The loader verifies each prefix and target against its source document. The
teacher never sees the rest of that story early.
Two already-known sentence-training examples seed the replay buffer; each step
also checks the latest 16 online observations. These anchors are separate from
the new presentation examples and are recorded explicitly.

An independent weight-only model sees the same online observations and replay
gate. Freeze the final checkpoints before evaluating the first eight validation
and eight test stories. Generate seeds 0–2 from all three models: initial,
weight-only, and teacher-trained. No held-out outcomes enter teacher packets or
adoption decisions. Unlike the earlier finite-suffix inducer, these teacher
grammars may read the entire context, so evaluation uses full prefixes.

## Model, cache, Flex, and spending

On 2026-11-13, the account returned `404 model_not_found` for the requested
`gpt-6.1-luna` and successfully retrieved `gpt-6-luna`. The
[official Luna model page](https://developers.openai.com/api/docs/models/gpt-6-luna)
also identifies `gpt-6-luna`. The prototype does not silently substitute models.
The user subsequently approved `gpt-6-luna`; it is now the default. Ten live
iterations completed on 2026-11-15. See the
[measured results](runs/online_20261115_live/REPORT.md).

Every live request specifies `service_tier="flex"`, with no Standard/Fast
fallback. The static instructions, grammar syntax, abstract example, and
declared vocabulary precede the changing evidence. An explicit breakpoint after
that shared prefix, a stable `prompt_cache_key`, and
`prompt_cache_options={"mode":"explicit","ttl":"30m"}` configure reuse.
The initial request warms that prefix naturally; later requests preserve it
exactly. See the [caching documentation](https://developers.openai.com/api/docs/guides/prompt-caching)
and [Flex documentation](https://developers.openai.com/api/docs/guides/flex-processing).
Real cache hits must be checked in returned usage, not inferred from request
settings. In the live run, the first call wrote 2,758 prefix tokens and all nine
subsequent calls reused those tokens. All ten responses reported Flex.

The budget ledger reserves a conservative upper estimate **before** each API
dispatch. It cannot be configured above $10. The bound uses request UTF-8 byte
length plus framing allowance, the maximum output-token count, and rates much
higher than Luna Flex. Completed usage settles that reservation using the
verified Luna Flex profile; accounting prices every noncached input token at
the cache-write rate as a conservative upper estimate. The separate estimated
cost field uses the returned read/write breakdown. Current reference rates are
recorded in code and come from [API pricing](https://developers.openai.com/api/docs/pricing).

Incomplete or malformed responses are still charged to the ledger. Unknown
outcomes retain the entire reservation. SDK retries are disabled; the existing
journaled dispatcher retries only definite, free `flex_unavailable` responses
and stays on Flex. An ambiguous interrupted dispatch is not automatically sent
again. Responses, request fingerprints, idempotency IDs, and receipts support
safe resumption. API keys are read through the existing environment/key-file
mechanism and never saved in experiment artifacts.

The teacher interface is asynchronous, and budget reservations serialize through
an async lock. Model commits use exact snapshot fingerprints; stale proposals
are rejected. The pilot deliberately makes one teacher call at a time. Parallel
proposals could share a snapshot and budget, but would still need serialized
selection/revalidation. Multiple processes cannot own the same run directory.

## Commands and artifacts

Prepare without API calls:

```sh
.venv/bin/python -m storyformers.online_experiment \
  --model gpt-6-luna --prepare-only --out /tmp/storyformer-online-prepared
```

Run the ten-observation curriculum in a new directory:

```sh
.venv/bin/python -m storyformers.online_experiment \
  --model gpt-6-luna --budget 10 --steps 10 \
  --curriculum storyformers/data/online_presentation_10.json \
  --out /tmp/storyformer-online-live
```

Repeat the same command to resume. Increasing `--steps` continues from committed
observations; reducing it below the committed step count is rejected. Budget
and source/model settings cannot change under the same journal. Do not use
held-out evaluation feedback to choose further training and then describe the
same test split as fresh.

Each step retains `evidence.json`, `proposal.json` when valid JSON was returned,
`receipt.json`, `decision.json`, and selected/control checkpoints. Provider
request/response caches follow the repository's existing local-only policy.
The run saves a manifest, replay anchors, final checkpoints, pre-update metrics,
budget accounting, frozen evaluation results, and unfiltered samples.

Local checks:

```sh
.venv/bin/python -m unittest storyformers.test_online storyformers.test_learning
```

Tests cover explicit one-target gradients, coordinated head/readout edits,
generalization across different token values, stale revision rejection,
observed-attribute conflicts, replay rejection of memorizing updates, resumption
without re-calling the teacher, stable cache prefixes, concurrent reservations,
and accounting for invalid paid responses.

## Live pilot result (2026-11-15)

Ten calls took 199.6 seconds including training and replay, and cost an estimated
$0.006812 (conservative ledger total $0.007653). Six teacher patches and four
weight-only updates were accepted. The patches added twelve output productions;
no heads or attributes were introduced. Test joint NLL on eight held-out stories
fell from 5.134 to 4.388, versus 4.945 for the independent weight-only control.
Accuracy rose from 22.2% to 25.1%. This small pilot is not a broad benchmark.

Unprompted seeds 0–2 still generated only the old sentence form, with no complete
presentation framing. One valid paragraph-break proposal was rejected by an
internal whitespace-name parsing bug. The adapter is fixed and regression-tested;
a saved counterfactual check passes the original replay gate, but the historical
run and final checkpoint deliberately retain the original decision. The report
links every proposal, decision, checkpoint, usage receipt, and sample.

## Larger ten-iteration batch comparisons

`online_batches.py` compares 1, 4, and 12 complete training stories per backward
pass, with exactly ten teacher calls per run. All causal positions in each batch
contribute to the averaged gradient and the adoption score. The teacher sees
batch statistics, frequent target counts, representative errors, starts and
boundaries, and revealed training documents. Each learned grammar still receives
only the causal prefix for its prediction. This increases training data per
iteration; the model remains one layer, 16 head slots, context 32, and 60 tokens.

Each branch starts independently from the same sentence checkpoint, using a
fixed shuffled document order (nested 10/40/120-story subsets). Its replay gate
uses the 12 sentence anchors plus a deterministic sample of up to 64 previously
observed targets. The independent weight-only control uses exactly the same
batches and gate. No single highlighted error can override a regression in
whole-batch mean loss. The tests check this explicitly.

The three branches overlap API waits via asynchronous tasks. They share one
teacher prefix and one persistent budget ledger, with the earlier pilot's
conservative spend subtracted from $10. Model updates remain serial within each
branch. Every update journals its selected and control fingerprints; interrupted
runs can resume without repeating committed teacher calls. The runner evaluates
all branches only after all training has finished, using validation/test stories
8–23, outside the first pilot's evaluated subset. It also saves five unfiltered
empty-prompt generations per teacher/control model and the initial model.

```sh
.venv/bin/python -m storyformers.online_batches \
  --out storyformers/runs/online_batches_20261115
```

The command above resumes the saved experiment when it already exists. A new
output directory makes new paid requests. The shared budget applies to that
suite and the recorded earlier pilot; launching unrelated output directories
creates separate ledgers and is not a global account spending limit.

The [completed comparison](runs/online_batches_20261115/REPORT.md) accepted
6/10, 10/10, and 9/10 teacher edits respectively. Test accuracy was 28.0%, 45.5%,
and 35.2%, versus 17.6% initially. The four-story batch learned a new
`preceding_person_token` retrieval feature; removing its head reduced test
accuracy to 42.1%. All 15 teacher-model generations still failed complete
framing, often producing fragments despite better next-token loss. New API
spend was about $0.047, with 29/30 cache-hit responses, all served on Flex.

## Ten larger continuation runs

`online_scale.py` continues the best previous four-story checkpoint in ten
independent branches. Five paired shuffle seeds each use batches of 8 and 16
stories, with ten gradient/teacher iterations per branch: 100 teacher calls and
1,200 story exposures drawn from the existing 192-story training pool. These
are repeated exposures across runs, not 1,200 unique new stories. All causal
positions in each batch contribute to learning; the underlying model capacity
stays context 32, one layer and 16 head slots.

The teacher additionally sees the previous gate's actual scores and one
40-token-limit free-generation diagnostic. Generated tokens are not labels.
Adoption still measures whole-batch likelihood, bounded replay regression,
attribute conflicts and added syntax. The teacher can now see why a prior
candidate was rejected, but generated-story quality is not a direct gate.

Three branches overlap their API waits. A branch failure leaves the others
running; completed steps are resumable. A separate dispatcher retries only
explicit free Flex rejections and connection-establishment failures, reusing
the idempotency key and retaining every attempt record. Read/write timeouts or
other ambiguous outcomes keep their reservations and do not automatically
redispatch. All branches share one budget ledger, subtracting earlier online
experiments' conservative spending from the $10 ceiling.

All 100 training decisions must exist before evaluation. Frozen models and
independent weight-only controls are evaluated on validation/test rows 24–47,
outside the earlier online pilot subsets, and five unfiltered generations are
saved per teacher model and for the starting checkpoint. Generation errors are
recorded as failures, not silently omitted. No held-out feedback is used to
change the training schedule.

```sh
.venv/bin/python -m storyformers.online_scale \
  --out storyformers/runs/online_scale_20261119 --concurrency 3
.venv/bin/python -m storyformers.scale_report \
  storyformers/runs/online_scale_20261119
```

The second command audits all 100 decisions and receipts, source hashes, model
and control checkpoint chains, the common cache prefix, all evaluations and
all 55 generations before producing `audit.json`, `summary.json` and
`REPORT.md`. A partial suite does not pass this completion audit. The live
protocol source hashes are frozen in the manifest; changing training code
mid-run requires an explicit new protocol, not silently resuming old evidence.

If a transport timeout leaves an unknown billing outcome, the affected branch
stops while other branches continue. After the suite process has exited,
`recover_scale.py` can prepare an explicitly accounted retry: it archives the
original attempt unchanged and retains its full reserved cost under an
`unresolved` ledger entry. The next request needs an additional reservation.
No provider deduplication or absence of charges is assumed. Recovery holds the
same exclusive suite lock and cannot race live accounting.

```sh
.venv/bin/python -m storyformers.recover_scale \
  storyformers/runs/online_scale_20261119
# Then resume online_scale with the same original arguments.
```

The completion audit distinguishes 100 completed logical teacher steps from
any additional unresolved attempts. It includes both settled spending and
all unresolved reservations when checking the $10 ceiling, and reports the
unknown spending separately. Original failures are historical records, not
silently replaced by successful responses.

For a long suite, `scale_supervise.py` can wait for an identified existing
experiment process, then resume only after that process has exited. It leaves
live requests alone, prepares separately budgeted retries for unknown outcomes,
resumes from committed decisions, and invokes the audit after completion. A
separate supervisor lock prevents duplicate supervisors. Unclassified failures,
evaluation failures, or exhausted recovery cycles stop for inspection rather
than resetting the experiment. The API adapter still enforces the shared budget.

```sh
.venv/bin/python -m storyformers.scale_supervise \
  --out storyformers/runs/online_scale_20261119 --wait-pid CURRENT_EXPERIMENT_PID
```

`CURRENT_EXPERIMENT_PID` must identify the actual live experiment. Once no
experiment is running, omit `--wait-pid`. `supervisor.json` is a status journal,
not proof that a process is live; check the tool session or actual PID before
restarting anything.

## Completed larger-run results

The [2026-11-19 suite](runs/online_scale_20261119/REPORT.md) finished all ten
runs and 100 iterations. The completion audit verified all checkpoint chains,
100 Luna/Flex receipts, 42 held-out evaluations, and 55 unfiltered generations
(50 trained-model samples plus five starting-checkpoint samples). There were no
evaluation execution errors. The existing verification record contains 159
passing tests, including recovery and budget-preservation checks.

On the same 24-story, 520-target test slice:

| Model | Mean next-token accuracy | Mean joint NLL |
|---|---:|---:|
| Starting checkpoint | 46.7% | 1.900 |
| Batch 8, teacher (five seeds) | 53.2% | 1.347 |
| Batch 8, weights only | 47.4% | 1.893 |
| Batch 16, teacher (five seeds) | 53.0% | 1.341 |
| Batch 16, weights only | 47.5% | 1.893 |

All ten teacher models beat their controls on test accuracy and loss. Doubling
batch size did not produce a clear average advantage on this small synthetic
task; the report includes the seed ranges. These are continuations of the best
previous checkpoint, not independent training from scratch. The 1,200 story
exposures reuse a 192-story pool across runs.

The teacher gate accepted 67 of 100 proposals, adding 18–35 output rules per
model. All models retained the starting two heads and acquired no new fields.
Three proposals did attempt new heads: a conjoined-determiner phrase feature
([run 3, step 5](runs/online_scale_20261119/run_03_b08/step_004/decision.json)),
a possessive-context feature
([run 5, step 10](runs/online_scale_20261119/run_05_b08/step_009/decision.json)),
and an introductory-item retrieval feature
([run 10, step 9](runs/online_scale_20261119/run_10_b16/step_008/decision.json)).
All three improved current-batch and replay loss, with no conflicts, but lost
to the weight-only alternative after the `0.001 * added syntax nodes` penalty.
Their batch NLL gains over weights alone were 0.0383, 0.0314, and 0.00183;
their complexity charges were 0.070, 0.052, and 0.043. Thus the absence of new
heads is partly an acceptance-objective result, not simply a failure to propose
them. A useful next ablation would vary that penalty or account for feature
reuse while retaining replay protection, using fresh held-out examples. No
penalty change or retrospective adoption was made in this suite.

Prediction improved, but free generation still often stops after fragments,
mixes opening/closing phrases into the body, or repeats noun phrases. For
example, one sample is `Tom's scissors\n\nOne morning.`; another is
`The small the small red the time.` All 50 trained-model samples ended, but
none passed the exact-template complete-framing check. Reading all samples
confirms substantial quality defects beyond that check; lower token loss alone
has not solved story presentation.

Known-response usage estimates total $0.150849, with prefix-cache hits on
96/100 responses. Nine timeout outcomes remain billing-uncertain; their full
$1.123604 conservative reservations are retained. Total conservative accounting
is $1.295171 for this suite, or $1.355084 including the earlier experiments,
within the $10 ceiling. This is usage-based accounting, not a billing invoice.
Three malformed proposals were rejected without applying their edits.
All attempts, proposals, decisions, models, controls, data indices, and samples
are preserved in the report's linked artifacts. The supervisor and temporary
idle-sleep prevention exited after the completion audit passed.
