import argparse
import json
import random

from ..__main__ import show_prediction
from ..grammar import tokenize
from .runtime import SCENARIOS, generate, setup, sample_sentence, build_forest
from ..storytelling.runtime import SCENARIOS as STORY_SCENARIOS, generate as short_story
from ..storytelling.qa import questions


def main():
    parser = argparse.ArgumentParser(description="GF/Codeco-derived Python rules; no GF runtime")
    parser.add_argument("--scenario", choices=(*STORY_SCENARIOS, "heldout", "all"), default="all")
    parser.add_argument("--style", choices=("short", "full"), default="short")
    parser.add_argument("--qa", action="store_true")
    parser.add_argument("--qa-limit", type=int, default=6)
    parser.add_argument("--evidence", action="store_true")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--samples", type=int, default=1)
    parser.add_argument("--tense", choices=("past", "present"), default="past")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--complete")
    parser.add_argument("--after", type=int, default=0)
    parser.add_argument("--trace", action="store_true")
    args = parser.parse_args()
    if args.samples < 1 or args.after < 0 or args.qa_limit < 0:
        parser.error("samples must be positive; after and QA limit must be nonnegative")
    if args.complete is not None:
        if args.scenario not in (*SCENARIOS, "heldout") or args.style != "full":
            parser.error("prefix inspection uses the full baseline: specify --style full and a baseline scenario")
        if args.scenario == "all":
            parser.error("completion requires a single scenario")
        pack, world = setup(args.scenario, args.seed)
        rng = random.Random(args.seed)
        for _ in range(args.after):
            sample_sentence(pack, world, rng, tense=args.tense)
        prediction = build_forest(pack, world, tense=args.tense).predict(tokenize(args.complete))
        if args.json:
            print(json.dumps(prediction, indent=2))
        else:
            for event in world.history:
                print(event["sentence"])
            print(f"Prefix: {args.complete!r}")
            show_prediction(prediction, 4)
        return
    if args.style == "full" and (args.qa or args.scenario not in {*SCENARIOS, "heldout", "greenhouse", "all"}):
        parser.error("QA and new authored worlds use --style short")
    scenarios = (STORY_SCENARIOS if args.style == "short" else SCENARIOS) if args.scenario == "all" else (args.scenario,)
    generator = short_story if args.style == "short" else generate
    results = [generator("greenhouse" if scenario == "heldout" and args.style == "short" else
                         "heldout" if scenario == "greenhouse" and args.style == "full" else scenario,
                         args.seed + i, tense=args.tense)
               for scenario in scenarios for i in range(args.samples)]
    if args.qa:
        for result in results:
            result["qa"] = questions(result, args.qa_limit)
    if args.json:
        print(json.dumps(results, indent=2))
        return
    for result in results:
        print(f"\n[{result['scenario']} | seed {result['seed']} | {result['tense']}]\n{result['story']}")
        for pair in result.get("qa", []):
            print(f"\nQ: {pair['question']}\nA: {pair['answer']}")
            if args.evidence:
                print("Evidence: " + " ".join(e["text"] for e in pair["evidence"]))
        if args.trace:
            for sentence in result.get("sentences", result.get("trace", [])):
                print(f"\n{sentence['frame']['kind']}: {sentence.get('text', 'narrated' if sentence.get('narrated') else 'internal physical step')}")
                for prediction in sentence["word_trace"]:
                    print(f"  {' '.join(prediction['prefix'])!r} -> {prediction['selected']}")
                    show_prediction(prediction, 4)


if __name__ == "__main__":
    main()
