# Exporting Storyscenes for training

`export_training.py` adapts a frozen, evaluated Storyscenes batch to the existing
`training/storyworld_chat` chat JSONL contract. It invokes that directory's
finalizer and actual training dataset loader. This optional integration needs
the repository's training scaffold; ordinary story/QA sampling remains standalone.

```bash
.venv/bin/python -m pip install tokenizers==0.22.2
.venv/bin/python storyscenes/export_training.py storyscenes/runs/worlds_100_v1 \
  --out training/storyworld_chat/data/storyscenes_100_branch_v1 \
  --tokenizer training/storyworld_chat/tokenizers/storyworld-16k-production \
  --jobs 4
.venv/bin/python storyscenes/export_training_report.py \
  training/storyworld_chat/data/storyscenes_100_branch_v1
```

The production tokenizer is preserved in
`training/storyworld_chat/data_archives/storyworld_chat_production_20260904_tokenizer.tar.gz`.
Restore its `training/storyworld_chat/tokenizers/storyworld-16k-production/`
members if the directory is absent. The exporter uses the tokenizer locally;
it makes no model/API requests and needs neither PyTorch nor Transformers.

## Output and acceptance

New exports default to `--prompt-mode branch`: each request adds the selected
`trace.premise` facts, checked against initial state, to the world premise.
This is deterministic and needs no LLM calls. The facts and renderer hash are
recorded for audit. Unsupported fields fail explicitly instead of falling back
to a generic prompt. Trait magnitudes are described qualitatively; the prompt
controls starting circumstances, not every subsequent ordering choice.

`--prompt-mode premise` retains the original generic prompt behavior. Use a new
output directory when changing modes. The historical `storyscenes_100_20260909`
files remain unchanged. Two full branch examples are in
[`examples/branch_prompts_v1/examples.md`](examples/branch_prompts_v1/examples.md).

- `candidate.train.jsonl`, `candidate.dev.jsonl`: the full, mechanically valid,
  deduplicated candidate material, including ungraded stories and QA.
- `judge_screened.train.jsonl`, `judge_screened.dev.jsonl`: only exact stories
  with saved overall >=6/9; QA additionally requires its own saved `usable=true`.
  A retained story can have no passing QA. These are model-screened candidates,
  not a guarantee of semantic correctness or prompt adherence.
- `sources/*.jsonl.gz`: full stories, traces, ordered conversations and evidence,
  replayed using the batch's frozen runtime. All saved stories/paragraphs/trace
  hashes must match; graded samples must also reproduce their QA exactly.
- `decisions.jsonl`: inclusion, duplicates, individual saved grades, mechanical
  QA defects and packing losses, including samples that produced no chat row.
- `manifest.json`, `split.json`, source receipts, checksums, finalization
  manifests and `REPORT.md`: coverage, exact token/loss counts, split policy,
  reproducibility and outstanding quality issues.

Each chat row begins with system, a natural-language story request, and the
complete story as an assistant response. It then contains zero or more intact
conversation chains. A chain's questions and answers remain in their original
order; independent chains can share a row. When the context fills up, a new row
starts with the complete story. A chain that cannot fit with the story is
excluded and recorded, never split into orphan follow-ups or silently truncated.

Tokens are counted using the trainer's segmented encoding and BOS handling.
System/user tokens are masked; assistant content and turn terminators contribute
to loss. The manifest distinguishes serialized, supervised story, and supervised
answer tokens, so repeated story prefixes cannot masquerade as more distinct
stories. No changes to the trainer or the older exporter are required.

The diagnostic `qa` field is deliberately unused. Internal state, evidence and
grades live outside message content. This does not remove semantic mistakes or
awkward phrasing already present in the source story/conversation.

## Splits and reproducibility

All descendants of a theme/shared seed premise stay in the same split. The first
export assigns families deterministically before content filtering. Preserve
that assignment when expanding:

```bash
# Add to the export command for the next batch:
--split-manifest training/storyworld_chat/data/storyscenes_100_20260909/split.json
```

An unknown family in a supplied manifest is an error; assign new families
explicitly before expansion. Exact story deduplication is global across this
batch, with duplicate exclusions recorded. Among duplicate seeds within a world,
an already graded sample is preferred, without transferring its grade to other
samples. Cross-corpus and near-duplicate plot screening are still needed.

Replay caches require matching source/runtime/QA hashes and output checksums.
Only mechanically accepted worlds enter the export. API credentials are removed
from the replay subprocess environment. There are no runtime LLM calls and no
attempt to replace the state-grounded engine with QA generated from English.

Run the integration and packing tests with:

```bash
.venv/bin/python -m unittest discover -s storyscenes -p 'test_export_training.py' -v
```

The current trial's report is
[`storyscenes_100_20260909/REPORT.md`](../training/storyworld_chat/data/storyscenes_100_20260909/REPORT.md).
Training data and restored tokenizers are ignored by Git; keep these generated
artifacts with the source run when archiving the experiment.
