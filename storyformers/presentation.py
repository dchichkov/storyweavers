"""Separate title/opening/closing corpus and a data-only grammar training pass."""

import argparse
from collections import defaultdict
from copy import deepcopy
from hashlib import sha256
from itertools import product
import json
import math
from pathlib import Path
import random
from time import perf_counter

from .grammar import canonical
from .induction import induce
from .neuron_review import model_fingerprint
from .refine import load_documents
from .synthetic import BigramBaseline, predict_joint


ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "runs/induction_baseline"
BREAK = {"token": "\n\n", "pos": "space"}
END = {"token": "<END>", "pos": "special"}


def phrase(text, tags):
    words, tags = text.split(), tags.split()
    if len(words) != len(tags):
        raise ValueError("one POS tag is required per token")
    return [dict(token=word, pos=pos) for word, pos in zip(words, tags)]


# These are the synthetic teacher's examples, never grammar rules given to the learner.
OPENINGS = (
    phrase("Once upon a time ,", "adv prep det n punct"),
    phrase("One day ,", "det n punct"),
    phrase("One morning ,", "det n punct"),
    phrase("Long ago ,", "adv adv punct"),
    phrase("On a sunny day ,", "prep det adj n punct"),
    phrase("In a little village ,", "prep det adj n punct"),
)
CLOSINGS = (
    phrase("The End .", "det n punct"),
    phrase("And that was the end .", "conj pron v det n punct"),
    phrase("That is all for now .", "pron v pron prep adv punct"),
    phrase("Until next time !", "prep adj n punct"),
    phrase("And so the story ended .", "conj adv det n v punct"),
    phrase("This is where our story ends .", "pron v adv det n v punct"),
)
TITLE_STYLES = ("name_and_object", "the_object", "possessive_object", "a_day_with_name")


def render(records):
    """Only detokenize; never repair, insert, or reorder generated content."""
    text = ""
    for row in records:
        token = row["token"]
        if token == "<END>":
            continue
        if token.isspace() or token in {".", ",", "!", "?", "'s"}:
            text += token
        else:
            text += (" " if text and not text[-1].isspace() else "") + token
    return text


def make_corpus(bodies, *, seed=19):
    """Wrap copies of the existing splits; hold out opening/closing pairings too.

    Section labels/spans are evaluation metadata only. Latents have token/POS,
    including literal paragraph breaks, and contain no future-aware phase flag.
    """
    rng = random.Random(seed)
    pools = defaultdict(list)
    for opening, closing in product(range(len(OPENINGS)), range(len(CLOSINGS))):
        group = (opening + closing) % 4
        pools["train" if group < 2 else "validation" if group == 2 else "test"].append((opening, closing))
    corpus, metadata = {}, {}
    for split in ("train", "validation", "test"):
        pairs = pools[split][:]
        rng.shuffle(pairs)
        corpus[split], metadata[split] = [], []
        for index, original in enumerate(bodies[split]):
            if not original or original[-1] != END:
                raise ValueError("each source sentence must end with the token/POS END record")
            body = deepcopy(original[:-1])
            name = body[0]
            noun = next(row for row in reversed(body) if row["pos"] == "n")
            adjectives = [row for row in body if row["pos"] == "adj"]
            object_rows = [*adjectives, noun]
            titles = (
                [name, *phrase("and the", "conj det"), *object_rows],
                [*phrase("The", "det"), *object_rows],
                [name, *phrase("'s", "poss"), *object_rows],
                [*phrase("A day with", "det n prep"), name],
            )
            style = index % len(titles)
            opening, closing = pairs[index % len(pairs)]
            parts = [("title", titles[style]), ("title_break", [BREAK]),
                     ("opening", OPENINGS[opening]), ("body", body),
                     ("closing_break", [BREAK]), ("closing", CLOSINGS[closing]), ("end", [END])]
            document, spans = [], {}
            for section, rows in parts:
                spans[section] = [len(document), len(document) + len(rows)]
                document.extend(deepcopy(rows))
            corpus[split].append(document)
            metadata[split].append(dict(source_row=index, title_style=TITLE_STYLES[style],
                                        opening=opening, closing=closing, spans=spans, text=render(document)))
    vocabulary = {canonical(row) for document in corpus["train"] for row in document}
    if any(canonical(row) not in vocabulary for split in ("validation", "test")
           for document in corpus[split] for row in document):
        raise ValueError("training split must cover the presentation vocabulary; use more source sentences")
    return corpus, metadata


def evaluate(model, documents, metadata, *, context_size=32, cache_suffix=None):
    """Score all causal positions and sections, without resetting section prefixes.

    Set cache_suffix only for models known to read that suffix exclusively, as
    our inducer's one-layer, fixed-lookback programs do. Each cache miss still
    executes the real model on the full causal prefix. Positions are not scored.
    """
    cache, buckets = {}, defaultdict(lambda: dict(targets=0, covered=0, correct=0, loss=0.))
    for document, meta in zip(documents, metadata):
        sections = {index: section for section, (start, stop) in meta["spans"].items()
                    for index in range(start, stop)}
        for index, target in enumerate(document):
            context = document[max(0, index - context_size):index]
            key = canonical(context[-cache_suffix:] if cache_suffix else context)
            if key not in cache:
                cache[key] = predict_joint(model, context)
            distribution = cache[key]
            label = target["token"], target["pos"]
            probability = distribution.get(label, 0.)
            best = min(distribution, key=lambda pair: (-distribution[pair], pair)) if distribution else None
            for section in ("all", sections[index]):
                bucket = buckets[section]
                bucket["targets"] += 1
                bucket["covered"] += probability > 0
                bucket["correct"] += best == label
                bucket["loss"] += -math.log(probability) if probability else 0.
    def metrics(row):
        count = row["targets"]
        return dict(targets=count, coverage=row["covered"] / count, joint_accuracy=row["correct"] / count,
                    joint_nll=row["loss"] / count if row["covered"] == count else None)
    return {**metrics(buckets.pop("all")), "by_section": {name: metrics(row) for name, row in buckets.items()}}


def framing_checks(records):
    """An exact-template framing check, not a judge of narrative quality."""
    tokens = [row["token"] for row in records]
    paragraphs = [[]]
    for token in tokens:
        if token == "\n\n":
            paragraphs.append([])
        elif token != "<END>":
            paragraphs[-1].append(token)
    three = len(paragraphs) == 3 and all(paragraphs)
    opening = bool(three and any(paragraphs[1][:len(rows)] == [r["token"] for r in rows] for rows in OPENINGS))
    closing = bool(three and any(paragraphs[2] == [r["token"] for r in rows] for rows in CLOSINGS))
    ended = bool(tokens and tokens[-1] == "<END>")
    return dict(ended=ended, three_nonempty_paragraphs=bool(three), known_opening=opening,
                known_closing=closing, complete_framing=bool(ended and three and opening and closing))


def sample(model, documents, metadata, *, count=6, steps=56):
    cases = [("unprompted", seed, []) for seed in range(count)]
    for index in range(min(3, len(documents))):
        for kind, section in (("after_title", "opening"), ("before_closing", "closing")):
            stop = metadata[index]["spans"][section][0]
            cases.append((kind, index, documents[index][:stop]))
    outputs = []
    for kind, seed, prefix in cases:
        records = model.generate(prefix, steps, seed=seed)
        outputs.append(dict(kind=kind, seed=seed, prompt_records=prefix, prompt=render(prefix),
                            records=records, text=render(records), max_new_tokens=steps,
                            **framing_checks(records)))
    return outputs


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False, allow_nan=False) + "\n")


def run(out, *, source=SOURCE, seed=19, heads=16, weight_steps=80):
    """Train a new checkpoint; the sentence corpus/model is only read, never updated."""
    out, source = Path(out), Path(source)
    if out.exists() and any(out.iterdir()):
        raise ValueError("use an empty output directory to preserve previous experiments")
    paths = [source / f"{split}.jsonl" for split in ("train", "validation", "test")]
    paths += [source / "model.json"]
    source_hashes = {str(path): sha256(path.read_bytes()).hexdigest() for path in paths}
    bodies = {split: load_documents(source / f"{split}.jsonl") for split in ("train", "validation", "test")}
    corpus, metadata = make_corpus(bodies, seed=seed)
    out.mkdir(parents=True, exist_ok=True)
    for split, documents in corpus.items():
        (out / f"{split}.jsonl").write_text("".join(json.dumps(doc, ensure_ascii=False) + "\n" for doc in documents))
    save(out / "metadata.json", metadata)
    settings = dict(context_size=32, lookback=3, max_literals=2, max_rules=heads,
                    num_heads=heads, weight_steps=weight_steps)
    protocol = dict(seed=seed, source_sha256=source_hashes, settings=settings,
                    splits={key: len(rows) for key, rows in corpus.items()},
                    split_policy="Source subject/verb pairs and opening/closing pairs are disjoint across splits.",
                    inputs="Only token/POS records; paragraph breaks are predicted tokens. No section metadata is input.",
                    training="Fresh data-derived grammar proposals and output log-weight fitting on training only. "
                             "Validation vetoes rules; final checkpoint is frozen before test evaluation.",
                    decoding="Top-ten joint token/bundle sampling; fixed seeds, no filtering or repairs.",
                    evaluation_cache="Joint token/POS probabilities cached by the last three records: "
                                     "all induced conditions read only those offsets. Cache misses run the full causal prefix.",
                    limitations="One-sentence bodies; no learned plot or semantic annotation. Framing checks do not judge story quality.")
    save(out / "protocol.json", protocol)
    started = perf_counter()
    print(f"Inducing presentation grammars from {len(corpus['train'])} documents ({heads} head slots)...", flush=True)
    result = induce(corpus["train"], validation_documents=corpus["validation"], **settings)
    training_seconds = perf_counter() - started
    result.model.save(out / "model.json")
    frozen = model_fingerprint(result.model)
    save(out / "rules.json", result.rules)
    print(f"Frozen {len(result.rules)} learned conditions after {training_seconds:.1f}s; evaluating...", flush=True)
    ablated = deepcopy(result.model)
    ablated.layers[0].heads = (None,) * heads
    models = dict(unigram=result.unigram, lexical_bigram=BigramBaseline(corpus["train"]),
                  induced=result.model, heads_removed=ablated)
    metrics = {}
    for split in ("validation", "test"):
        metrics[split] = {}
        for name, model in models.items():
            print(f"Scoring {split}/{name}...", flush=True)
            metrics[split][name] = evaluate(model, corpus[split], metadata[split], cache_suffix=settings["lookback"])
            save(out / "metrics.json", metrics)
    print("Sampling fixed seeds and held-out continuations...", flush=True)
    samples = sample(result.model, corpus["test"], metadata["test"])
    save(out / "samples.json", samples)
    assert model_fingerprint(result.model) == frozen
    assert all(sha256(Path(path).read_bytes()).hexdigest() == digest for path, digest in source_hashes.items())
    report = dict(protocol=protocol, model_sha256=frozen, vocabulary=result.vocabulary,
                  training_targets=result.training_examples, proposals=result.proposals,
                  learned_conditions=len(result.rules), learned_heads=sum(h is not None for h in result.model.layers[0].heads),
                  selection_train_nll=result.history, selection_validation_nll=result.validation_history,
                  training_seconds=training_seconds, total_seconds=perf_counter() - started, metrics=metrics,
                  unprompted_framing_passes=sum(s["complete_framing"] for s in samples if s["kind"] == "unprompted"),
                  unprompted_samples=sum(s["kind"] == "unprompted" for s in samples), source_unchanged=True)
    save(out / "report.json", report)
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--source", type=Path, default=SOURCE)
    parser.add_argument("--seed", type=int, default=19)
    parser.add_argument("--heads", type=int, default=16)
    parser.add_argument("--weight-steps", type=int, default=80)
    report = run(**vars(parser.parse_args()))
    print(json.dumps({key: report[key] for key in ("training_seconds", "learned_heads", "unprompted_framing_passes", "unprompted_samples")}, indent=2))
    for name, metrics in report["metrics"]["test"].items():
        print(f"{name}: NLL={metrics['joint_nll']:.3f}, joint accuracy={metrics['joint_accuracy']:.1%}")


if __name__ == "__main__":
    main()
