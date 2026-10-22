# Viable StoryWorld Training Dataset Plan

Proposed 2026-09-06. Planning only: no generation, judge, or training jobs have
been launched for this plan, and no API budget has been spent on it.

## Objective And Recommendation

Build a dataset for the existing roughly 60M-parameter model that teaches fluent
short children's stories, follows the requested characters and events, and
answers questions grounded in the preceding story. Keep the existing tokenizer,
chat envelope, and model architecture for the first comparison.

Use the existing GPT-4 TinyStories export as the language base, new independent
Luna stories for variety and instruction following, and a filtered StoryWorld
slice for executable state and grounded QA. Spend the first $10 testing the
teacher and data format. Spend the remainder in small, audited batches after
that test passes.

The initial mixture to test is approximately 70% TinyStories, 20% new teacher
stories, and 10% curated StoryWorld conversations, measured by assistant tokens
that contribute to loss. These are experimental starting weights, not quotas
that justify including weak data. New teacher stories can include grounded QA;
cap answer tokens at about 5-10% of the total and standalone world-fact answers
at no more than 1%. Do not fill that allocation by repeating a small fact pool.

A working size is 300-450M serialized training tokens, broadly comparable to
the existing experiment. Measure the assistant/story/answer breakdown before
choosing the exact size. This is a practical experiment size, not an established
optimum for 60M parameters. At the lower budget, reduce the new-teacher share
or corpus size if acceptance is lower than expected.

## Evidence Behind The Change

- The existing production train export has 410,187,389 serialized tokens,
  596,966 rows, and about 531,850 distinct story samples from 6,516 worlds.
- The matched TinyStories export has 410,186,394 tokens and 1,132,573 stories.
  StoryWorld rows average 8.14 assistant turns versus one for TinyStories.
  The existing comparison changes story count and QA allocation as well as
  prose source; it does not isolate a single cause of the performance gap.
- `train_chat.py` masks system and user content. Serialized tokens are not
  supervised tokens, and neither figure equals independent story information.
- The completed repair campaign covered 117 deliberately selected worst
  contributors. It is not a representative quality estimate of all worlds.
  The repaired code also does not update an already materialized JSONL corpus.
- `story_skeleton()` substitutes parameter values and numbers. Different
  openings or interchangeable sentence forms can still produce distinct hashes
  for the same plot. High normalized uniqueness is a screening result, not
  proof of independent plots or a measured quality improvement.
- No fresh API quality sweep established a post-repair mean for the 117 worlds.
- The BOS-corrected 16-prompt StoryWorld run averaged 2.25 overall; references
  averaged 6.0. One reference received 8/10 despite literal `friend_a` and
  `friend_b` placeholders. Judge scores need deterministic checks and manual
  calibration. Sixteen prompts are also too few for a stable final benchmark.

Evidence: [training record](README.md),
[repair ledger](../../storyworlds/WORST_CONTRIBUTORS_REPAIR.md),
[diversity analyzer](analyze_world_contributors.py), and the preserved
`vibe_runs/dev16_seed20260905.bos.*` reports. The local training record documents
the TinyStories control setup; this plan does not assume an unrecorded final
TinyStories quality score.

## 1. Audit And Reuse Existing Material

1. Count serialized, unmasked assistant, story, and answer tokens with the
   production tokenizer and the trainer's actual label construction. Track
   independent source stories and repeated story prefixes separately.
2. Re-export repaired train worlds into a new versioned candidate shard. Keep
   their original source-family split assignments. Repairs to a dev world do
   not make it eligible for training.
3. Screen existing candidates with exact hashes, slot normalization, and word
   shingle similarity. Use embeddings or a plot-level judge on suspicious
   clusters, with thresholds calibrated by reading pairs. Similar topic alone
   is not sufficient reason to deduplicate.
4. Begin with 5-20 accepted stories per world. Increase only when additional
   samples bring distinct events, choices, and outcomes. Cap related source
   copies together, including original/repaired versions and copied scripts.
5. Sample the wider corpus across quality coverage, world size, duplicate rate,
   and genre. Missing historical quality ratings mean unknown quality.
6. Remove incomplete stories, unresolved placeholders, broken role sequences,
   contradictory required facts, and invalid QA. Review difficult seed terms
   for the intended child audience instead of requiring arbitrary vocabulary.

The old corpus remains an immutable snapshot. The new selection records why
each row was included or rejected. Exclusion is a reasonable outcome; another
large repair campaign is not a prerequisite for this dataset.

## 2. Run A Small Matched Teacher Pilot

Prepare 400 new briefs, separate from final evaluation: 200 ordinary story
requests and 200 grounded requests spanning several worlds and causal patterns.
Generate the same briefs using Luna with reasoning `none`, Luna with `low`,
and Qwen3.8-27B without thinking if local serving is practical. Skip Qwen rather
than make model installation a dependency of the API pilot.

Use `gpt-5.4-mini` as the fixed judge, preserving the existing story-quality
rubric and recording its model identifier, settings, and prompt hash. Blind
teacher identity. Add separate checks for constraint adherence, QA support, and
diversity; do not silently redefine the historical overall score. Manually read
at least 50 representative and suspicious cases to calibrate the checks.

Record accepted examples per dollar, accepted assistant tokens per dollar,
generation time, duplicate clusters, rubric dimensions, and factual errors.
Include rejected candidates and billed reasoning in the cost denominator.

Provisional gates, to calibrate on the pilot:

- At least 80% of candidates survive the combined format/content/diversity
  checks. Lower yield requires rebudgeting before scale-up.
- Accepted stories average at least 7/10 overall, with grammar and coherence
  meeting their own thresholds. Verify obvious defects are rejected even when
  the scalar score is high.
- Grounded QA is supported by both the story and its source trace; aim for at
  least 95% support on the pilot audit, with unsupported rows rejected.
- No handful of concrete plot clusters dominates the pilot. Inspect repeated
  opening, conflict, solution, and ending patterns across teachers and genres.

These gates indicate a promising teacher; downstream student evaluation decides
whether the dataset is useful. If Luna fails, test a better teacher on a small
matched subset and purchase fewer accepted examples within the same budget.

## 3. Generate Independent Stories And Grounded Conversations

Use a balanced brief sampler covering everyday goals, relationships, obstacles,
mistakes, discoveries, emotional changes, dialogue levels, and several lengths.
Start around 150-300 words, fitting the existing context budget. Limit unusual
word constraints; do not force every story to state a moral or follow an
identical outline. One fresh brief normally produces one training story.

For grounded examples, provide the offline teacher a compact executed trace:
named entities, initial state, actions, consequences, and final state. Ask it
to render the trace as natural prose and include only 1-3 useful questions when
the events support them. The teacher may not invent an unsupported answer.
Prefer existing trace-derived QA targets and verify the prose actually states
the evidence needed to answer them.

Include causal, temporal, ownership, and changed-state questions, plus a small
number of appropriate "the story does not say" cases. Keep source facts and
evidence IDs as metadata; validate alignment between prose and trace before
accepting a conversation. Direct stories without a trace need answer support
in the text itself and should not claim executable-world verification.

Keep the student-facing `Task: write_story`, `Prompt:`, and `Params:` envelope.
Use consistent parameter keys and only parameters that affect the requested
story; new data can retain random seed and provenance in metadata. Match the
evaluation format, and ensure required facts given to the teacher also appear
in the student input when the student is expected to obey them. A private
teacher outline can guide a free story without becoming a hidden student task.

Do not attach hundreds of lexical rewrites to one trace. Keep an initial cap of
1-3 renderings per underlying event sequence and sample on new traces rather
than names alone. Cap cross-world plot clusters too. LLM rendering here is an
offline dataset operation; the StoryWorld runtime remains classical execution.

## 4. Budget And Throughput

The official short-context Luna rates checked on 2026-09-06 are $0.20/M input,
$0.02/M cached input, $0.25/M cache writes, and $1.20/M output. Batch and Flex
list $0.10/M input and $0.60/M output. Luna supports reasoning `none`; do not
assume that a nano-tier price establishes story quality.

Sources: [Luna model](https://developers.openai.com/api/docs/models/gpt-5.6-luna),
[pricing](https://developers.openai.com/api/docs/pricing),
[Batch](https://developers.openai.com/api/docs/guides/batch), and
[Flex](https://developers.openai.com/api/docs/guides/flex-processing).

| Allocation | $100 envelope | $200 envelope |
| --- | ---: | ---: |
| Teacher pilot and calibration | $10 | $10 |
| Fresh generation, including any QA generation | $60 | $140 |
| Mini audits and student evaluation | $20 | $30 |
| Retries, rejects beyond forecast, and contingency | $10 | $20 |
| Total maximum | $100 | $200 |

For an illustrative candidate averaging 800 input and 400 output tokens with
no reasoning, generation costs $64 per 100,000 candidates at standard rates,
or $32 with Batch/Flex. If all 800 input tokens instead attract cache-write
pricing, standard cost becomes $68. Cache hits can improve this, but the
estimate does not depend on them.

| Generation envelope | Standard: accepted at 80% yield | Batch/Flex: accepted at 80% yield |
| --- | ---: | ---: |
| $60 | about 75,000 / 30M output tokens | about 150,000 / 60M output tokens |
| $140 | about 175,000 / 70M output tokens | about 350,000 / 140M output tokens |

These are planning estimates, not promised yields. API output tokens are not
the same as tokens under the production 16k tokenizer. Any QA, JSON overhead,
or reasoning reduces the fraction available as story supervision. Recompute
from actual pilot usage, retained content, and tokenizer counts before launch.

Use Batch for bulk work if available on the account, or Flex with bounded
retries and 900-second timeouts. Do not automatically retry on a more expensive
tier. Keep a spend ledger including in-flight reservations and failed/truncated
attempts; stop dispatch when the relevant allocation would be exceeded.

Grade the complete pilot, then stratified random samples of every production
shard plus suspicious rows and low-yield clusters. The audit allocation does
not pay for Mini to judge every candidate. Log judge coverage and estimated
defect rates for unjudged cohorts; reject or expand inspection of weak cohorts.

Qwen is a possible source of diversity and an independent screening model,
conditional on quality and measured throughput. Its official model card
supports non-thinking mode via `chat_template_kwargs.enable_thinking=false`
in compatible local servers. A 4-bit 27B model has a roughly 13.5GB idealized
weight payload; scales, unquantized layers, runtime memory, and KV cache add to
that. A 24GB GPU needs an actual fit and throughput test with short contexts.
At a hypothetical sustained 50 output tokens/second, 50M tokens take 11.6 days
before other overhead. Local inference is not automatically the better trade
for this budget, especially if it occupies the training GPU.
Source: [official Qwen3.8-27B card](https://huggingface.co/Qwen/Qwen3.8-27B).

## 5. Freeze Splits, Train, And Make The Decision

Create validation and final-test groups before expansion. Group by world family,
trace/brief ancestry, and near-duplicate cluster, including matches across data
sources. Keep all descendants in the same split. Existing 16 prompts remain a
historical diagnostic; create a fresh 500-prompt held-out test with ordinary
story requests, grounded requests, and QA tasks. Include both familiar prompt
formats and held-out world/compositional combinations. Keep final-test prompts
out of teacher generation inputs and selection decisions.

Run small matched experiments at about 25-50M unmasked assistant-token exposures:

1. TinyStories-only reference slice, with its existing story-only protocol.
2. Curated StoryWorld story text alone, separating prose from QA effects.
3. Proposed source mixture with stories only.
4. The same mixture with the proposed small QA allocation.

Use the same 60M initialization, tokenizer, BOS handling, chat format, optimizer,
and generation settings. Match assistant-token exposure and keep optimizer
updates as close as practical; report serialized tokens and task allocation as
well. Do not infer quality from training loss alone. Log story and QA validation
losses separately and assess diversity/constraint adherence in generated text.

The mixture should improve prompt adherence and grounded answers over the
matched story-only base while preserving its fluency. Use paired judgments and
confidence intervals, inspect failures, and choose on validation results. If
it fails, change the source weights or discard weak sources before more bulk
generation. Run the selected full corpus for up to two epochs, evaluate during
training, and choose a checkpoint on validation. Use the fresh test once for
the final comparison; do not select checkpoints on it.

## Artifacts And Implementation Order

Implement only after agreeing on this direction:

1. Extend export reporting to count actual supervised story/answer tokens and
   source-family/plot-cluster contributions.
2. Add a versioned curation stage around the existing exporter and finalizer.
3. Add an offline direct-story/trace-rendering generator that produces the
   existing chat JSONL schema, plus separate usage and provenance manifests.
4. Extend the existing Mini evaluation harness with independent constraint and
   evidence checks, retaining the original quality score for comparison.
5. Run the pilot, create training slices, then release generation budget in
   approximately 5,000-candidate shards after the pilot gates pass.

Preserve immutable raw response JSONL, accepted/rejected JSONL, manifest, prompt
snapshot, model/tier/settings, token usage, source ancestry, script hash,
checksums, split decisions, and sampled quality reports for every batch.
Archive compressed dataset snapshots through the existing Git LFS process.

If the objective instead requires a primarily new, independent StoryWorld
corpus, keep TinyStories only as a separate control and apply the same gates
to accepted teacher stories and traces. The affordable result may be only tens
to low hundreds of millions of new assistant tokens. Repeating those examples
can supply more training exposures but must not be reported as more diversity.
