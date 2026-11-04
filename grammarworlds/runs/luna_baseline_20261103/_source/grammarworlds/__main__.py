from __future__ import annotations

import argparse
import json
import math
import sys

from .engine import advance, build_forest, generate
from .grammar import tokenize
from .world import SCENARIOS


def show_prediction(prediction: dict, top: int) -> None:
    choices = prediction["choices"]
    shown = choices[:top]
    print("  " + " | ".join(f"{c['word']} {c['probability']:.1%}" for c in shown))
    if len(choices) > top:
        omitted = sum(c["probability"] for c in choices[top:])
        print(f"  + {len(choices) - top} other choices, {omitted:.1%} probability mass")


def main() -> None:
    p = argparse.ArgumentParser(description="Grammarworlds: classical grammar + world state + word probabilities")
    p.add_argument("--scenario", choices=(*SCENARIOS, "all"), default="rescue")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--samples", type=int, default=1)
    p.add_argument("--tense", choices=("past", "present"), default="past")
    p.add_argument("--attention", choices=("on", "off"), default="on")
    p.add_argument("--temperature", type=float, default=1, help="temperature on event logits; grammar rule weights remain authored")
    p.add_argument("--fear", type=float, help="intervene on the hero's initial Fear (0..1)")
    p.add_argument("--care", type=float, help="intervene on the hero's initial Care (0..1)")
    p.add_argument("--trace", action="store_true", help="show next-symbol distributions, including punctuation and stopping")
    p.add_argument("--top", type=int, default=4, help="display limit only; sampling uses the full distribution")
    p.add_argument("--json", action="store_true", help="full world, evidence, and word distributions")
    p.add_argument("--complete", metavar="PREFIX", help="inspect the next-word distribution without sampling it")
    p.add_argument("--after", type=int, default=0, help="generate this many sentences before inspecting completion")
    p.add_argument("--verify", action="store_true", help="run grammarworlds' local regression suite")
    args = p.parse_args()
    if args.verify:
        import unittest
        suite = unittest.defaultTestLoader.discover("grammarworlds", pattern="test_*.py", top_level_dir=".")
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        sys.exit(not result.wasSuccessful())
    if args.samples < 1 or args.top < 1 or args.after < 0:
        p.error("samples/top must be positive and after must be nonnegative")
    if not math.isfinite(args.temperature) or args.temperature <= 0:
        p.error("temperature must be finite and positive")
    options = dict(tense=args.tense, attention=args.attention == "on", temperature=args.temperature,
                   fear=args.fear, care=args.care)
    try:
        if args.complete is not None:
            if args.scenario == "all":
                p.error("completion requires one scenario")
            world = advance(args.scenario, args.seed, args.after, **options)
            forest = build_forest(world, **{k: options[k] for k in ("tense", "attention", "temperature")})
            prediction = forest.predict(tokenize(args.complete))
            result = dict(world=world.to_dict(), prediction=prediction, event_evidence=forest.evidence)
            if args.json:
                print(json.dumps(result, indent=2, allow_nan=False))
            else:
                print(f"Hero: {world.entities[world.hero].noun}; after {args.after} sentences.")
                for event in world.history:
                    print(event["sentence"])
                print(f"\nPrefix: {args.complete!r}")
                show_prediction(prediction, args.top)
                if prediction.get("error"):
                    print(prediction["error"])
            return
        scenarios = SCENARIOS if args.scenario == "all" else (args.scenario,)
        results = [generate(scenario, args.seed + i, **options)
                   for scenario in scenarios for i in range(args.samples)]
    except ValueError as error:
        p.error(str(error))
    if args.json:
        print(json.dumps(results, indent=2, allow_nan=False))
        return
    for result in results:
        print(f"\n[{result['scenario']} | seed {result['seed']}]")
        print(result["story"])
        if args.trace:
            for sentence in result["sentences"]:
                print(f"\nEvent {sentence['event_id']}: {sentence['frame']['kind']} | {sentence['text']}")
                for kind, evidence in sentence["event_evidence"].items():
                    print(f"  event prior {kind}: {evidence['prior_probability']:.1%}; logit {evidence['logit']:.3f}")
                for i, prediction in enumerate(sentence["word_trace"], 1):
                    print(f" {i}. {' '.join(prediction['prefix'])!r} -> {prediction['selected']}")
                    show_prediction(prediction, args.top)


if __name__ == "__main__":
    main()
