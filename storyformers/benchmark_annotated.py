"""Local wiring and timing probe over the causal story and reviewed corrections.

Uses the existing catalog seeds and synthetic learner, without training or API
calls. A separate 256-context copy widens only wildcard gaps. Full-story forward
timing uses independent context-sized segments; rolling timing uses predict().
"""
import argparse
from collections import Counter
from copy import deepcopy
import cProfile
from dataclasses import replace
import hashlib
import json
import math
from pathlib import Path
import platform
import pstats
import resource
import statistics
import time

from .annotated_demo import CATALOG_FIELDS, CHECKPOINT
from .catalog.api import CatalogIndex, prepare_context
from .catalog_prefix_v3 import META, validate_record
from .grammar import GrammarNeuron, Gap, Present, Ref, Rule, Seq, Token
from .transformer import Storyformer

ROOT = Path(__file__).resolve().parent
ANNOTATIONS = ROOT / "runs/prefix_catalog_full_story_20261108/000000_744d68e4483a/annotations.json"
CORRECTIONS = ROOT / "runs/prefix_reconciliation_20261109/reconciled_records.json"


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_inputs(annotations, corrections):
    rows = json.loads(annotations.read_text())
    story = "".join(r["token"] for r in rows)
    snapshots, replaced = {}, set()
    for corrected in json.loads(corrections.read_text()):
        index = corrected["index"]
        if index in replaced or not 0 <= index < len(rows) or rows[index]["index"] != index:
            raise ValueError("correction index must identify one original lossless span")
        original = rows[index]
        validate_record(story[:original["end"]], corrected)
        metadata = {k: original[k] for k in ("index", "token", "start", "end", "kind", "position")}
        rows[index] = {**{k: v for k, v in corrected.items() if k not in META}, **metadata}
        snapshots[str(index)] = {k: v for k, v in corrected.items() if k in META}
        replaced.add(index)
    return prepare_context(rows), snapshots, replaced


def wildcard_bound(pattern, size):
    children = tuple(wildcard_bound(child, size) for child in pattern.children)
    wildcard = (pattern.kind == "repeat" and pattern.minimum == 0 and len(children) == 1
                and children[0].kind == "token" and not children[0].tests and not children[0].bind)
    return replace(pattern, children=children, maximum=size if wildcard else pattern.maximum)


def make_model(checkpoint, size=None):
    learned, catalog = Storyformer.load(checkpoint), CatalogIndex()
    original_context = learned.context_size
    if size is not None and size != original_context:
        neurons = list(learned.projection.neurons.values())
        neurons += [h.neuron for layer in learned.layers for h in layer.heads if h is not None]
        for neuron in neurons:
            for rule in neuron.rules:
                rule.pattern = wildcard_bound(rule.pattern, size)
    ids = [catalog.by_key[key]["producer_head_ids"][0] for key in CATALOG_FIELDS]
    model = Storyformer(learned.projection, layers=(catalog.block(ids), *learned.layers),
                        context_size=original_context if size is None else size, top_k=10,
                        features={**learned.features, **catalog.feature_registry(CATALOG_FIELDS)})
    return model, dict(context_size=model.context_size, saved_context_size=original_context,
                       wildcard_bounds_widened=model.context_size != original_context,
                       head_slots=[len(l.heads) for l in model.layers],
                       populated_heads=[sum(h is not None for h in l.heads) for l in model.layers],
                       head_rules=sum(len(h.neuron.rules) for l in model.layers for h in l.heads if h),
                       catalog_heads=ids, vocabulary=len(model.projection.neurons),
                       projection_rules=sum(len(n.rules) for n in model.projection.neurons.values()))


def timed(call, repeats):
    times, result = [], None
    for _ in range(repeats):
        start = time.perf_counter()
        result = call()
        times.append(time.perf_counter() - start)
    return result, dict(samples_seconds=times, median_seconds=statistics.median(times),
                        min_seconds=min(times), max_seconds=max(times))


def check_result(inputs, result):
    assert len(inputs) == len(result.residual_stream) == len(result.predictions)
    written = {key for event in result.trace for key in event["values"]}
    for before, after, prediction in zip(inputs, result.residual_stream, result.predictions):
        for key, value in before.items():
            if key not in written:
                assert after[key] == value, (before["index"], key)
        assert before["token"] == after["token"] and before["position"] == after["position"]
        assert len(prediction.probabilities) <= 10 and prediction.probabilities
        assert math.isclose(sum(prediction.probabilities.values()), 1, abs_tol=1e-10)
        assert math.isclose(sum(c["probability"] for c in prediction.joint), 1, abs_tol=1e-10)


def run(args):
    args.out.mkdir(parents=True, exist_ok=True)
    fingerprints = {str(p): digest(p) for p in (args.annotations, args.corrections, args.checkpoint)}
    started = time.perf_counter()
    context, snapshots, corrected_indices = load_inputs(args.annotations, args.corrections)
    original = deepcopy(context)
    checkpoint, architecture16 = make_model(args.checkpoint)
    model, architecture = make_model(args.checkpoint, args.context_size)
    setup = time.perf_counter() - started
    save(args.out / "input.json", context)
    save(args.out / "corrected_reference_snapshots.json", snapshots)
    report = dict(source_sha256=fingerprints, corrected_indices=sorted(corrected_indices),
                  input=dict(records=len(context), kinds=dict(Counter(r["kind"] for r in context)),
                             top_level_fields=sum(len(r) for r in context),
                             plot_records=sum("plot" in r for r in context),
                             depiction_records=sum("depiction" in r for r in context)),
                  architecture=architecture, checkpoint_architecture=architecture16,
                  environment=dict(platform=platform.platform(), machine=platform.machine(),
                                   processor=platform.processor(), python=platform.python_version()),
                  setup_seconds=setup, timings={}, checks={}, notes=[
                      "Original causal v2 records with exactly 17 reviewed v3 replacements at their real source positions; not a uniformly reannotated v3 corpus.",
                      "Spaces omitted; original lossless indices and positions remain unchanged. Punctuation consumes context slots.",
                      "Three authored catalog seeds plus seven synthetic-data-learned heads; remaining slots are NOOP. No new training.",
                      "The 256-context copy widens wildcard matching bounds only; it was not trained on long contexts.",
                      "Full forward timings use independent segments, resetting context between them. They are not a rolling 256-context decode benchmark.",
                      "Exact rolling decode timing uses the saved 16-context checkpoint and recomputes each window; there is no KV cache.",
                      "The readout has 19 toy tokens and token/POS supervision, not the story vocabulary or full rich-latent prediction ability.",
                      "Reference tables remain companion evidence; the loaded heads do not query those tables or interpret plot/depiction.",
                      "Wall times include residual and trace creation but exclude JSON artifact writes and input/model loading. CPU Python, no LLM/GPU calls.",
                  ])

    # Bound expansion must leave original-length behavior unchanged.
    short = context[:min(16, len(context))]
    old, new = checkpoint.forward(short), model.forward(short)
    assert old.residual_stream == new.residual_stream
    assert [p.to_dict() for p in old.predictions] == [p.to_dict() for p in new.predictions]
    report["checks"]["widening_preserves_short_context_outputs"] = True
    for size in (5, 16, 64):
        if size > len(context) or size > model.context_size:
            continue
        sample = context[-size:]
        result, timing = timed(lambda: model.forward(sample), args.repeats)
        check_result(sample, result)
        report["timings"][f"forward_{size}"] = timing
        _, timing = timed(lambda: model.predict(sample), args.repeats)
        report["timings"][f"predict_{size}"] = timing
        print(f"{size} records: forward {report['timings'][f'forward_{size}']['median_seconds']:.3f}s, "
              f"last readout {timing['median_seconds']:.3f}s", flush=True)

    final_context = context[-model.context_size:]
    next_latent, timing = timed(lambda: model.predict(final_context), args.repeats)
    report["timings"][f"predict_{len(final_context)}"] = timing
    report["last_distribution"] = next_latent.to_dict()
    save(args.out / "progress.json", report)
    print(f"{len(final_context)}-context last readout: {timing['median_seconds']:.3f}s", flush=True)

    # Batch-style full-story pass: every position, never silently truncating to
    # just the final window. Persist each segment before advancing.
    segments, counts, additions, changed, rich_checks = [], Counter(), Counter(), 0, 0
    for start in range(0, len(context), model.context_size):
        inputs = context[start:start + model.context_size]
        result, timing = timed(lambda: model.forward(inputs), 1)
        check_result(inputs, result)
        for before, after in zip(inputs, result.residual_stream):
            changed += any(before.get(k) != v for k, v in after.items())
            additions.update(k for k in after if k not in before and after[k] is not None)
            for field in ("plot", "depiction"):
                if field in before:
                    assert before[field] == after[field]
                    rich_checks += 1
        counts.update(e["neuron"] for e in result.trace)
        number = len(segments)
        save(args.out / f"segment_{number:02d}.json", dict(
            start_record=start, source_indices=[r["index"] for r in inputs],
            residual_stream=result.residual_stream, trace=result.trace,
            predictions=[dict(source_index=r["index"], **p.to_dict()) for r, p in zip(inputs, result.predictions)]))
        segments.append(dict(start_record=start, records=len(inputs), words=sum(r["kind"] == "word" for r in inputs),
                             seconds=timing["median_seconds"], activations=len(result.trace)))
        report["segments"] = segments
        save(args.out / "progress.json", report)
        print(f"Segment {number+1}: {len(inputs)} records, {timing['median_seconds']:.3f}s, {len(result.trace)} head matches", flush=True)
    seconds = sum(s["seconds"] for s in segments)
    full_windows = [s["seconds"] for s in segments if s["records"] == model.context_size]
    if full_windows:
        report["timings"][f"forward_{model.context_size}"] = dict(
            samples_seconds=full_windows, median_seconds=statistics.median(full_windows),
            min_seconds=min(full_windows), max_seconds=max(full_windows),
            sampling="different story segments, same context size; not repeated identical input")
    report["segmented_forward"] = dict(seconds=seconds, records_per_second=len(context)/seconds,
                                       words_per_second=sum(r["kind"] == "word" for r in context)/seconds,
                                       head_activations=dict(counts), added_fields=dict(additions), changed_positions=changed)
    report["checks"]["rich_bundles_preserved"] = rich_checks
    report["checks"]["all_positions_predicted_and_normalized"] = len(context)

    # Real rolling inference with the unchanged saved context bound.
    start = time.perf_counter()
    rolling = []
    for i, row in enumerate(context):
        window = context[max(0, i + 1 - checkpoint.context_size):i + 1]
        prediction = checkpoint.predict(window)
        assert prediction.probabilities and math.isclose(sum(prediction.probabilities.values()), 1, abs_tol=1e-10)
        rolling.append(dict(source_index=row["index"], **prediction.to_dict()))
        if (i+1) % 200 == 0:
            print(f"Rolling {checkpoint.context_size}: {i+1}/{len(context)} positions", flush=True)
    seconds = time.perf_counter() - start
    report["rolling_checkpoint"] = dict(context_size=checkpoint.context_size, positions=len(context),
                                         seconds=seconds, records_per_second=len(context)/seconds,
                                         milliseconds_per_step=1000*seconds/len(context))
    save(args.out / "rolling_predictions.json", rolling)

    # Direct nested-bundle matching/copying is possible with the same neuron
    # type. These diagnostic neurons are not installed in the measured model.
    copied = []
    for field in ("plot", "depiction"):
        neuron = GrammarNeuron("diagnostic_copy_"+field, (Rule(
            Seq(Gap(model.context_size), Token(**{field: Present()})), {field: Ref("query."+field)}),))
        for i, row in enumerate(context):
            if field in row:
                activation = neuron.activate(context[max(0, i+1-model.context_size):i+1])
                assert len(activation) == 1 and activation[0].value[field] == row[field]
                copied.append(dict(source_index=row["index"], field=field))
    report["checks"]["diagnostic_grammar_copies"] = copied

    # Check masking with a representative small prefix, outside timing.
    result = model.forward(short)
    assert all(model.forward(short[:i]).residual_stream == result.residual_stream[:i] for i in (1, 5, len(short)))
    report["checks"]["sampled_block_prefix_invariance"] = True
    assert context == original and all(digest(Path(p)) == h for p, h in fingerprints.items())
    report["checks"]["inputs_and_checkpoint_unchanged"] = True

    # Profile only a separate 64-position run; profiling is excluded from times.
    profiler = cProfile.Profile()
    profiler.runcall(model.forward, context[-min(64, model.context_size):])
    profiler.dump_stats(str(args.out / "forward.prof"))
    with (args.out / "profile.txt").open("w") as stream:
        pstats.Stats(profiler, stream=stream).strip_dirs().sort_stats("cumulative").print_stats(30)
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    report["peak_process_rss_mib"] = peak / (1024**2 if platform.system() == "Darwin" else 1024)
    save(args.out / "report.json", report)
    print(json.dumps({k: report[k] for k in ("architecture", "segmented_forward", "rolling_checkpoint", "peak_process_rss_mib")}, indent=2), flush=True)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--annotations", type=Path, default=ANNOTATIONS)
    parser.add_argument("--corrections", type=Path, default=CORRECTIONS)
    parser.add_argument("--checkpoint", type=Path, default=CHECKPOINT)
    parser.add_argument("--context-size", type=int, default=256)
    parser.add_argument("--repeats", type=int, default=3)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    if not 16 <= args.context_size <= 256 or args.repeats < 1:
        parser.error("context size must be between 16 and 256, and repeats positive")
    run(args)


if __name__ == "__main__":
    main()
