"""Reproducible small-vocabulary token/POS induction experiment; no API calls."""

import argparse
from collections import Counter, defaultdict
from copy import deepcopy
from itertools import product
import json
import math
from pathlib import Path
import random

from .grammar import canonical
from .induction import examples, induce


def make_corpus(seed=7, train=192, validation=64, test=64):
    """Disjoint name/verb pairs; every word and POS is observed in training.

    This generator is the synthetic teacher. None of its vocabulary groups,
    templates, or split rules are passed to the grammar learner.
    """
    if any(type(count) is not int or count < 1 for count in (train, validation, test)):
        raise ValueError("split sizes must be positive integers")
    names = ("Lily", "Ben", "Mia", "Tom")
    verbs = ("took", "found", "used", "ate")
    objects = {"took": ("scissors", "needles", "apples", "pears"),
               "found": ("scissors", "needles", "apples", "pears"),
               "used": ("scissors", "needles"), "ate": ("apples", "pears")}
    pools = {key: [] for key in ("train", "validation", "test")}
    for name_index, name in enumerate(names):
        for verb_index, verb in enumerate(verbs):
            group = (name_index + verb_index) % 4
            split = "train" if group < 2 else "validation" if group == 2 else "test"
            for adverb, determiner, adjective, noun in product(
                    (None, "slowly", "quickly"), (None, "the"), (None, "small", "red"), objects[verb]):
                words = [(name, "pn"), (adverb, "adv"), (verb, "v"), (determiner, "det"),
                         (adjective, "adj"), (noun, "n"), (".", "punct"), ("<END>", "special")]
                pools[split].append([dict(token=word, pos=pos) for word, pos in words if word is not None])
    rng = random.Random(seed)
    for split, count in (("train", train), ("validation", validation), ("test", test)):
        rng.shuffle(pools[split])
        if count > len(pools[split]):
            raise ValueError(f"{split} has at most {len(pools[split])} unique documents")
        pools[split] = pools[split][:count]
    return pools


class BigramBaseline:
    """A smoothed lexical bigram over joint token/POS targets, for comparison."""

    def __init__(self, documents, smoothing=1.):
        self.counts, self.prior, self.smoothing = defaultdict(Counter), Counter(), smoothing
        for context, target in examples(documents):
            label = target["token"], target["pos"]
            self.prior[label] += 1
            self.counts[context[-1]["token"] if context else None][label] += 1

    def predict_joint(self, context):
        counts = self.counts.get(context[-1]["token"] if context else None, {})
        total, prior_total = sum(counts.values()), sum(self.prior.values())
        return {label: (counts.get(label, 0) + self.smoothing * count / prior_total) / (total + self.smoothing)
                for label, count in self.prior.items()}


def predict_joint(model, context):
    if isinstance(model, BigramBaseline):
        return model.predict_joint(context)
    probabilities = defaultdict(float)
    for row in model.predict(context).joint:
        probabilities[row["latent"]["token"], row["latent"]["pos"]] += row["probability"]
    return dict(probabilities)


def evaluate(model, documents, context_size=16):
    """Use the compiled model and untruncated joint probabilities, never top-k loss."""
    cache, losses, correct, pos_correct, covered, total = {}, [], 0, 0, 0, 0
    for context, target in examples(documents, context_size):
        key = canonical(context)
        if key not in cache:
            cache[key] = predict_joint(model, context)
        probabilities = cache[key]
        probability = probabilities.get((target["token"], target["pos"]), 0.)
        total += 1
        covered += probability > 0
        if probability:
            losses.append(-math.log(probability))
        if probabilities:
            best = min(probabilities, key=lambda label: (-probabilities[label], label))
            correct += best == (target["token"], target["pos"])
            pos_mass = defaultdict(float)
            for (_, pos), mass in probabilities.items():
                pos_mass[pos] += mass
            pos_correct += min(pos_mass, key=lambda pos: (-pos_mass[pos], pos)) == target["pos"]
    nll = math.fsum(losses) / total if covered == total and total else None
    return dict(targets=total, coverage=covered / total if total else None, joint_nll=nll,
                perplexity=math.exp(nll) if nll is not None else None,
                joint_accuracy=correct / total if total else None,
                pos_accuracy=pos_correct / total if total else None)


def run(*, seed=7, train=192, validation=64, test=64, max_rules=16, lookback=3,
        max_literals=2, weight_steps=80, out=None):
    corpus = make_corpus(seed, train, validation, test)
    result = induce(corpus["train"], validation_documents=corpus["validation"], max_rules=max_rules, lookback=lookback,
                    max_literals=max_literals, weight_steps=weight_steps)
    bigram = BigramBaseline(corpus["train"])
    # Removing the learned heads leaves their readout productions unsupported.
    ablated = deepcopy(result.model)
    ablated.layers[0].heads = (None,) * ablated.layers[0].num_heads
    report = dict(seed=seed, layers=1, head_slots=16,
                  learned_heads=sum(head is not None for head in result.model.layers[0].heads),
                  learned_rules=len(result.rules), proposals=result.proposals,
                  vocabulary=result.vocabulary, splits={key: len(value) for key, value in corpus.items()},
                  split_policy="Disjoint subject/verb pairs; no duplicate documents across splits.",
                  training_examples=result.training_examples,
                  settings=dict(lookback=lookback, max_literals=max_literals, max_rules=max_rules,
                                weight_steps=weight_steps, context_size=16),
                  selection_train_nll=result.history, selection_validation_nll=result.validation_history,
                  validation_policy="Rule proposals and weights use training only; validation vetoes non-improving rules.",
                  metrics={})
    for split in ("validation", "test"):
        report["metrics"][split] = {
            "unigram": evaluate(result.unigram, corpus[split]),
            "lexical_bigram": evaluate(bigram, corpus[split]),
            "induced": evaluate(result.model, corpus[split]),
            "heads_removed": evaluate(ablated, corpus[split]),
        }
    report["rules"] = result.rules
    report["samples"] = []
    for document in corpus["test"][:4]:
        # Show the prediction after the verb, before the object or its modifiers.
        stop = next(i for i, row in enumerate(document) if row["pos"] == "v") + 1
        context = document[:stop]
        distribution = result.model.predict(context)
        report["samples"].append(dict(context=context, target=document[stop],
                                      distribution=distribution.to_dict()))
    report["generated"] = [[{key: row[key] for key in ("token", "pos")} for row in
                             result.model.generate([], 12, seed=seed + index)] for index in range(3)]
    if out is not None:
        folder = Path(out)
        folder.mkdir(parents=True, exist_ok=True)
        for split, documents in corpus.items():
            (folder / f"{split}.jsonl").write_text("".join(json.dumps(doc) + "\n" for doc in documents))
        result.model.save(folder / "model.json")
        (folder / "report.json").write_text(json.dumps(report, indent=2, allow_nan=False) + "\n")
    return report, result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("storyformers/runs/induction_baseline"))
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--train", type=int, default=192)
    parser.add_argument("--validation", type=int, default=64)
    parser.add_argument("--test", type=int, default=64)
    parser.add_argument("--max-rules", type=int, default=16)
    parser.add_argument("--lookback", type=int, default=3)
    parser.add_argument("--max-literals", type=int, default=2)
    parser.add_argument("--weight-steps", type=int, default=80)
    args = parser.parse_args()
    report, _ = run(**vars(args))
    print(json.dumps({key: report[key] for key in ("layers", "learned_heads", "learned_rules", "proposals")}, indent=2))
    print("Test metrics (joint token/POS, before top-ten truncation):")
    for name, metrics in report["metrics"]["test"].items():
        nll = f"{metrics['joint_nll']:.3f}" if metrics['joint_nll'] is not None else "unsupported targets"
        print(f"  {name:16s} NLL={nll}  accuracy={metrics['joint_accuracy']:.1%}  POS={metrics['pos_accuracy']:.1%}")
    print("Learned conditions:")
    for rule in report["rules"]:
        print(f"  {rule['condition']}  (support={rule['support']}, gain={rule['gain_nats']:.1f})")
    print(f"Saved corpus, model and report to {args.out}")


if __name__ == "__main__":
    main()
