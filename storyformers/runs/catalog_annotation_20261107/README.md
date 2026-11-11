# Whole-story catalog annotation trial

This run annotates the 20 stories from
`storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/STORIES.md`
with sparse per-word dictionaries drawn from the full 1,024-attribute catalog.
It is deliberately retrospective: later story text may resolve earlier
references, while beliefs, alternatives, fictional worlds and time-specific
states retain their own scopes. Prefix-only annotation is a separate experiment.

All 20 stories are annotated and independently reviewed: 15,326 words and 34,367
lossless token records. The run uses 535 distinct canonical fields sparsely, with
seven agreed provisional extensions. Status and validation counts are recorded
in `manifest.json` and `reviews/progress.json`; the final completion gate is
`reviews/completion_audit.json`.

The reusable final prompt is [annotate_v4.md](prompts/annotate_v4.md), accompanied
by the full catalog, [extension registry](prompts/extension_registry_v4.json) and
[eight final-batch examples](prompts/batch3_examples_v4.json). Historical examples
remain available, giving 25 reviewed examples across the prompt revisions.

## Layout

- `inputs/STORY_ID/`: exact story text, lossless tokens, indexed words and paragraphs.
- `annotations/STORY_ID/annotations.jsonl`: one record per lossless token,
  including synthetic spaces and punctuation. Every word has POS and lemma;
  supported semantic and grammatical fields are sparse. Omitted is not false.
- `entities.json`, `events.json`, `propositions.json`, `scopes.json`: the
  story-local records referenced from word features. IDs must not be joined
  across stories without their story ID.
- `evidence.json`: supports and explanations for substantial interpretations.
- `new_attributes.json`: provisional extension definitions used in that story.
- `feedback.json`: ambiguities, feature gaps, prompt feedback and self-review.
- `author.py`: reproducible manual labels assembled with `authoring.py`.
- `metadata.json` and `validation.json`: provenance and structural validation.
- `prompts/`: frozen prompt versions, complete catalog descriptions, agreed
  extensions and concrete corrected examples.
- `reviews/`: independent semantic reviews, batch decisions and source/catalog
  auditing. `phase_log.jsonl` records prompt releases and batch scheduling.

The base catalog's `patients`/`instruments` descriptions originally specified
display names. `prompts/catalog_overrides.json` records the trial's correction:
both arrays contain registered entity IDs. The other catalog meanings and types
remain unchanged. Shared extensions are reviewed and versioned rather than
silently added to the canonical 1,024-field catalog.

## Prompt sequence

| Annotation group | Frozen prompt | Review informs |
| --- | --- | --- |
| Two pilots, 01–02 | `prompts/annotate_v0.md` | v1 |
| Batch 1, 03–08 | `prompts/annotate_v1.md` | v2 |
| Batch 2, 09–14 | `prompts/annotate_v2.md` | v3 |
| Batch 3, 15–20 | `prompts/annotate_v3.md` | v4, the reusable final revision |

Each six-story batch uses one frozen prompt. Reviews and corrections precede
the next release. Original prompt versions are retained; older annotations are
not relabeled with a newer prompt version. The catalog is available in four
256-definition files throughout, with no feature-count quota per word.

The session supports three concurrent workers plus the coordinator. Repeated
simultaneous capacity checks rejected a fourth worker. The requested six-story
logical batches therefore use worker waves, with coordinator authoring and
independent review where useful. No external annotation API was called.

The final consistency pass corrected seven modal-class labels in story 12 and
one reflection-frame label in story 13. Their earlier frozen prompt examples
remain unchanged and resolve to the original reviewed snapshots indexed by
`reviews/annotation_snapshots.json`. Current annotation folders contain the
corrected records; `reviews/final_consistency_12_13.md` records the bounded
independent comparison. Earlier prompts also retain their original, sometimes
coarser lexical-family labels; the final prompt specifies the next-run convention.

## Reading the records

`word_index` counts words from zero. `index` and `position.token` count all
lossless tokens, including spaces. Catalog `tN` anchors count nonspace tokens
from one, including punctuation. Evidence/support lists use `word_index`.
Reconstruct the exact source by concatenating every record's `token` in order.

The singular `event_id`/`role` is a primary association; `event_bindings` preserves
all associations for a word. A speech event, its content proposition and the
positive target of a local negation can be separate records. Assertion status
(`asserted`, `attributed_claim`, `candidate`) is separate from event factuality
(`asserted`, `reported`, `desired`, `hypothetical`, `negated`). A fact can be
asserted within a fictional scope without becoming a physical-world fact.

## Verification

From the repository root:

```bash
.venv/bin/python storyformers/runs/catalog_annotation_20261107/review_run.py
.venv/bin/python storyformers/runs/catalog_annotation_20261107/reviews/source_catalog_audit.py
.venv/bin/python storyformers/runs/catalog_annotation_20261107/reviews/completion_audit.py
```

These checks cover token reconstruction, types, registered identity links,
prompt/source provenance, extension consistency and exact source/catalog copies.
Read their completed-story counts as well as their error lists: pending folders
are reported separately. Machine checks do not establish semantic correctness;
the story and batch review files record that separate review. Sparse annotations
do not claim exhaustive coverage of all possible meanings or all 1,024 fields.
The completion audit additionally requires all 20 reviewed stories, the final
prompt revision, unchanged logged prompt bundles and examples that still match
their source annotations. It exits unsuccessfully while that gate is incomplete.
