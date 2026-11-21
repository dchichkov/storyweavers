import argparse
import json
from .runtime import SCENARIOS, generate
from .qa import questions


def main():
    p = argparse.ArgumentParser(description="Short stories with dialogue and grounded reading questions")
    p.add_argument("--scenario", choices=(*SCENARIOS, "all"), default="all")
    p.add_argument("--seed", type=int, default=7)
    p.add_argument('--edition',choices=('original','crafted'),default='original')
    p.add_argument('--story-choice',help='Condition a crafted decision branch by its event name')
    p.add_argument("--samples", type=int, default=1)
    p.add_argument("--tense", choices=("past", "present"), default="past")
    p.add_argument("--qa", action="store_true")
    p.add_argument("--qa-limit", type=int, default=6)
    p.add_argument("--json", action="store_true")
    p.add_argument("--raw", action="store_true", help="Show the native story body without title/opening/closing")
    p.add_argument("--token-annotations", action="store_true",
                   help="Include token provenance, entity state and rotary positions in JSON")
    p.add_argument("--surface-only", action="store_true",
                   help="Ablate joint attribute prediction and use the legacy word sampler")
    p.add_argument("--evidence", action="store_true")
    p.add_argument("--heads", action="store_true", help="Enable prefix/world symbolic word reranking")
    p.add_argument("--multiscale", action="store_true", help="Track larger events and sampled world-time durations")
    p.add_argument("--plot-annotations", action="store_true", help="Include authored plot roles in candidate token attributes")
    p.add_argument('--beat-budget',type=int,default=0,help='Maximum optional scene beats (0 disables; try 2 or 6)')
    p.add_argument("--continuations", choices=("original", "expanded"), default="original")
    p.add_argument("--head-profile", choices=("seed", "manual", "tuned"), default="manual")
    p.add_argument("--head-strength", type=float, default=1.0)
    p.add_argument("--head-ids", nargs="+", help="Optional subset, for example P023 P059")
    args = p.parse_args()
    if args.samples < 1 or args.qa_limit < 0:
        p.error("samples must be positive and QA limit nonnegative")
    results = []
    from .revisions import NAMES as CRAFTED_SCENARIOS
    if args.edition=='crafted':
        if args.tense!='past':p.error('crafted prototypes currently support past tense only')
        if args.multiscale or args.plot_annotations or args.beat_budget:
            p.error('crafted prototypes have their own authored beats; legacy beat/plot/scale wrappers are not supported')
        if args.scenario not in (*CRAFTED_SCENARIOS,'all'):
            p.error('crafted edition supports pottery, music and greenhouse')
    if args.story_choice and (args.edition!='crafted' or args.scenario=='all'):
        p.error('--story-choice needs one crafted scenario')
    scenarios=CRAFTED_SCENARIOS if args.edition=='crafted' else SCENARIOS
    for scenario in scenarios if args.scenario == "all" else (args.scenario,):
        for i in range(args.samples):
            row = generate(scenario, args.seed + i, tense=args.tense, symbolic_heads=args.heads,
                           head_profile=args.head_profile, head_strength=args.head_strength,
                           head_ids=args.head_ids, continuations=args.continuations,
                           token_annotations=args.token_annotations, predict_attributes=not args.surface_only,
                           presentation=not args.raw,
                           **({'edition':'crafted'} if args.edition=='crafted' else {}),
                           **({'choice':args.story_choice} if args.story_choice else {}),
                           **({'multiscale':True} if args.multiscale else {}),
                           **({'plot_annotations':True} if args.plot_annotations else {}),
                           **({'beat_budget':args.beat_budget} if args.beat_budget else {}))
            if args.qa:
                row["qa"] = questions(row, args.qa_limit)
            results.append(row)
    if args.json:
        print(json.dumps(results, indent=2))
        return
    for row in results:
        story=row['story'] if args.raw else row['presented_story']
        print(f"\n[{row['scenario']} | seed {row['seed']}]\n{story}")
        for pair in row.get("qa", []):
            print(f"\nQ: {pair['question']}\nA: {pair['answer']}")
            if args.evidence:
                print("Evidence: " + " ".join(e["text"] for e in pair["evidence"]))


if __name__ == "__main__":
    main()
