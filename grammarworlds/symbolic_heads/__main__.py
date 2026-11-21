"""Inspect the library or sample an eight-word sentence from weighted grammar."""

import argparse
import json
import math
import random

from ..grammar import Derivation, Forest, choice, detokenize, expand, seq
from ..world import Frame
from . import HeadContext, Source, load_library, predict, sample


def demo(seed=7):
    grammar = seq("river.sentence", "the river",
                  choice("river.verb", "flows", "sings", "freezes", "sparkles",
                         weights=(4, 1, 3, 2)), "beside the old stone bridge", ".")
    frame = Frame("illustration", "river")
    forest = Forest([Derivation(words, p, frame, rules) for words, p, rules in expand(grammar)], {})
    library = load_library()
    memory = (Source("river:water", "active_context_feature", "river-clause", "water"),)
    rng, prefix, trace, selected_probs = random.Random(seed), (), [], []
    for _ in range(max(len(d.tokens) for d in forest.derivations) + 1):
        requests = [HeadContext("P059", "river", "river-clause")] if prefix == ("the", "river") else []
        prediction = predict(forest, prefix, library, requests, memory)
        word = sample(prediction, rng)
        selected_probs.append(next(c["probability"] for c in prediction["choices"] if c["word"] == word))
        trace.append({"prefix": list(prefix), "choices": prediction["choices"],
                      "heads": prediction["symbolic_heads"], "selected": word})
        if word == "<END>":
            break
        prefix += (word,)
    else:
        raise RuntimeError("finite grammar did not terminate")
    return {"sentence": detokenize(prefix), "words": sum(w.isalpha() for w in prefix),
            "sequence_probability": math.prod(selected_probs),
            "semantic_support": bool(forest.event_posterior(prefix)), "trace": trace}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--head", help="show description, tables, and ten examples for P001–P064")
    parser.add_argument("--demo", action="store_true")
    parser.add_argument("--seed", type=int, default=7)
    args = parser.parse_args()
    library = load_library()
    if args.demo:
        print(json.dumps(demo(args.seed), indent=2))
    elif args.head:
        try:
            spec = library.describe(args.head)
        except KeyError:
            parser.error(f"unknown head {args.head}")
        print(json.dumps(spec, indent=2, ensure_ascii=False))
    else:
        for head_id in library.ids:
            spec = library.describe(head_id)
            print(f'{head_id}  {spec["status"]:17} {spec["name"]}')
        print("\nUse --head P059 for ten examples and editable table rows; --demo for word sampling.")


if __name__ == "__main__":
    main()
