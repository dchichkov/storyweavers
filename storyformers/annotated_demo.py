"""Run reviewed story latents through existing catalog heads and learned grammars.

This is a wiring probe, not training or a causal language-model evaluation.
The source annotations are retrospective; the saved learner has a toy vocabulary.
"""

import argparse
from copy import deepcopy
import hashlib
import json
from pathlib import Path

from .catalog.api import CatalogIndex, prepare_context
from .transformer import Storyformer


ROOT = Path(__file__).resolve().parent
ANNOTATIONS = ROOT / "runs/catalog_annotation_20261107/annotations/10_camp/annotations.jsonl"
CHECKPOINT = ROOT / "runs/induction_baseline/model.json"
CATALOG_FIELDS = ("determiner_kind", "definiteness", "cardinal_value")


def select_span(records, start_word, words):
    """Select consecutive words and intervening punctuation; retain source IDs."""
    if start_word < 0 or words < 1:
        raise ValueError("start_word must be nonnegative and words positive")
    lexical = [row for row in records if row.get("kind") == "word"]
    selected = [row for row in lexical if start_word <= row["word_index"] < start_word + words]
    if len(selected) != words:
        raise ValueError("requested word span is outside the annotation")
    first, last = selected[0]["index"], selected[-1]["index"]
    return prepare_context(row for row in records if first <= row["index"] <= last)


def run_probe(annotation_path=ANNOTATIONS, checkpoint_path=CHECKPOINT, *, start_word=585, words=5):
    annotation_path, checkpoint_path = Path(annotation_path), Path(checkpoint_path)
    source = annotation_path.read_bytes()
    records = [json.loads(line) for line in source.decode().splitlines()]
    context = select_span(records, start_word, words)
    original = deepcopy(context)
    learned = Storyformer.load(checkpoint_path)
    if len(context) > learned.context_size:
        raise ValueError(f"span has {len(context)} nonspace records; checkpoint context is {learned.context_size}")

    catalog = CatalogIndex()
    head_ids = [catalog.by_key[key]["producer_head_ids"][0] for key in CATALOG_FIELDS]
    # One authored seed block, followed by the unchanged saved learned block(s).
    model = Storyformer(learned.projection, layers=(catalog.block(head_ids), *learned.layers),
                        context_size=learned.context_size, top_k=10,
                        features={**learned.features, **catalog.feature_registry(CATALOG_FIELDS)})
    result = model.forward(context)
    changes = []
    for before, after in zip(context, result.residual_stream):
        changed = {key: {"before": before.get(key), "after": value}
                   for key, value in after.items() if value != before.get(key)}
        if changed:
            changes.append(dict(token=before["token"], position=before["position"], fields=changed))

    # A separate ablation demonstrates reconstruction rather than reinforcement
    # of labels already supplied by the annotator. The source stays intact.
    masked = deepcopy(context)
    removed = []
    for i, row in enumerate(masked):
        for key in CATALOG_FIELDS:
            if key in row:
                removed.append((i, key, row.pop(key)))
    reconstructed = model.forward(masked)
    recovery = [dict(token=context[i]["token"], position=context[i]["position"],
                     field=key, expected=value, actual=reconstructed.residual_stream[i].get(key),
                     recovered=reconstructed.residual_stream[i].get(key) == value)
                for i, key, value in removed]
    # This checks block masking, not causal validity of retrospective input labels.
    prefix_invariant = all(
        model.forward(context[:i + 1]).residual_stream == result.residual_stream[:i + 1]
        for i in range(len(context)))
    checks = dict(input_unmodified=context == original,
                  source_file_unmodified=source == annotation_path.read_bytes(),
                  residual_length_preserved=len(result.residual_stream) == len(context),
                  source_positions_preserved=all(a["position"] == b["position"]
                                                for a, b in zip(context, result.residual_stream)),
                  block_prefix_invariance=prefix_invariant)
    if not all(checks.values()):
        raise AssertionError(checks)
    return dict(
        annotation_path=str(annotation_path.resolve()), annotation_sha256=hashlib.sha256(source).hexdigest(),
        checkpoint_path=str(checkpoint_path.resolve()),
        checkpoint_sha256=hashlib.sha256(checkpoint_path.read_bytes()).hexdigest(),
        source_text="".join(row["token"] for row in records
                            if context[0]["index"] <= row["index"] <= context[-1]["index"]),
        word_span={"start": start_word, "count": words}, input=context,
        architecture=dict(context_size=model.context_size, visible_records=len(context),
                          head_slots=[len(layer.heads) for layer in model.layers],
                          active_heads=[sum(h is not None for h in layer.heads) for layer in model.layers],
                          catalog_head_ids=head_ids, vocabulary_size=len(model.projection.neurons)),
        residual_stream=result.residual_stream, changes=changes, trace=result.trace,
        predictions=[dict(after_token=row["token"], source_position=row["position"],
                          **prediction.to_dict())
                     for row, prediction in zip(context, result.predictions)],
        next_latent=result.next_latent.to_dict(),
        masked_feature_probe=dict(fields=list(CATALOG_FIELDS), recovery=recovery,
                                  trace=reconstructed.trace), checks=checks,
        limitations=[
            "Whole-story retrospective labels: this is not a leakage-free next-token evaluation.",
            "Three authored catalog seeds precede the unchanged synthetic-data learner; no training occurs.",
            "The learned projection has only 19 toy tokens and token/POS supervision; it does not generate the rich story annotations.",
            "Entity/event IDs remain story-local references; companion tables are not automatically read by grammar heads.",
            "Input source positions are preserved; generated positions use the runtime supplied-stream convention, without whitespace rendering.",
        ])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, default=ANNOTATIONS)
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT)
    parser.add_argument("--start-word", type=int, default=585)
    parser.add_argument("--words", type=int, default=5)
    parser.add_argument("--out", type=Path, help="save full inputs, residuals, traces and joint outputs")
    args = parser.parse_args()
    report = run_probe(args.annotations, args.checkpoint, start_word=args.start_word, words=args.words)
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(report, ensure_ascii=False, indent=2, allow_nan=False) + "\n")
    print(json.dumps({key: report[key] for key in
                      ("source_text", "architecture", "changes", "checks")}, ensure_ascii=False, indent=2))
    print(json.dumps(dict(next_tokens=report["next_latent"]["probabilities"],
                          masked_feature_recovery=report["masked_feature_probe"]["recovery"]),
                     ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
