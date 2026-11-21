import argparse
import json
from .runtime import SCENARIOS, generate
from .qa import questions


def main():
    p = argparse.ArgumentParser(description="Short stories with dialogue and grounded reading questions")
    p.add_argument("--scenario", choices=(*SCENARIOS, "all"), default="all")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument("--samples", type=int, default=1)
    p.add_argument("--tense", choices=("past", "present"), default="past")
    p.add_argument("--qa", action="store_true")
    p.add_argument("--qa-limit", type=int, default=6)
    p.add_argument("--json", action="store_true")
    p.add_argument("--evidence", action="store_true")
    p.add_argument("--heads", action="store_true", help="Enable prefix/world symbolic word reranking")
    p.add_argument("--continuations", choices=("original", "expanded"), default="original")
    p.add_argument("--head-profile", choices=("seed", "manual", "tuned"), default="manual")
    p.add_argument("--head-strength", type=float, default=1.0)
    p.add_argument("--head-ids", nargs="+", help="Optional subset, for example P023 P059")
    args = p.parse_args()
    if args.samples < 1 or args.qa_limit < 0:
        p.error("samples must be positive and QA limit nonnegative")
    results = []
    for scenario in SCENARIOS if args.scenario == "all" else (args.scenario,):
        for i in range(args.samples):
            row = generate(scenario, args.seed + i, tense=args.tense, symbolic_heads=args.heads,
                           head_profile=args.head_profile, head_strength=args.head_strength,
                           head_ids=args.head_ids, continuations=args.continuations)
            if args.qa:
                row["qa"] = questions(row, args.qa_limit)
            results.append(row)
    if args.json:
        print(json.dumps(results, indent=2))
        return
    for row in results:
        print(f"\n[{row['scenario']} | seed {row['seed']}]\n{row['story']}")
        for pair in row.get("qa", []):
            print(f"\nQ: {pair['question']}\nA: {pair['answer']}")
            if args.evidence:
                print("Evidence: " + " ".join(e["text"] for e in pair["evidence"]))


if __name__ == "__main__":
    main()
