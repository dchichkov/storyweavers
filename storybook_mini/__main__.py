import argparse
import json
from pathlib import Path
from .content import STORIES, SUITES
from .experiment import evaluate, export_comparison, make_study
from .model import simulate
from .pipeline import CONFIGS, generate
from .story_io import load_story


def main():
    parser = argparse.ArgumentParser(description="Fixed-content STORYBOOK mini reproduction")
    commands = parser.add_subparsers(dest="command", required=True)
    show = commands.add_parser("show", help="Print one story/version")
    show.add_argument("story", choices=STORIES)
    show.add_argument("--version", choices=CONFIGS, default="full")
    show.add_argument("--trace", action="store_true")
    render = commands.add_parser("render", help="Render declarative story JSON through the same pipeline")
    render.add_argument("path", type=Path)
    render.add_argument("--version", choices=CONFIGS, default="full")
    render.add_argument("--trace", action="store_true")
    demo = commands.add_parser("demo", help="Export stories, traces, comparison and research notebook")
    demo.add_argument("--out", type=Path, default=Path(__file__).parent / "examples")
    demo.add_argument("--suite", choices=SUITES, default="all")
    study = commands.add_parser("study", help="Create blinded rating packets; no ratings are invented")
    study.add_argument("--out", type=Path, required=True)
    study.add_argument("--participants", type=int, default=20)
    study.add_argument("--seed", type=int, default=2001)
    study.add_argument("--suite", choices=SUITES, default="extended")
    ratings = commands.add_parser("evaluate", help="Validate and summarize completed human packets")
    ratings.add_argument("--study", type=Path, required=True)
    ratings.add_argument("--responses", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command in {"show", "render"}:
            story = STORIES[args.story] if args.command == "show" else load_story(args.path)
            result = generate(simulate(story), args.version)
            print(json.dumps(result, indent=2) if args.trace else result["text"])
        elif args.command == "demo":
            export_comparison(args.out, SUITES[args.suite])
            print(f"Wrote {args.out.resolve() / 'research.html'}")
        elif args.command == "study":
            if args.participants < 1:
                parser.error("--participants must be positive")
            manifest = make_study(args.out, args.participants, args.seed, SUITES[args.suite])
            print(f"Created {args.participants} blinded packets in {args.out.resolve()}")
            if not manifest["position_balanced"]:
                print("Partial counterbalancing cycle: use a multiple of the reading count for exact balance.")
        else:
            if not args.responses.is_dir():
                parser.error("--responses must be an existing directory")
            print(json.dumps(evaluate(args.study, args.responses), indent=2))
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"Error: {exc}\n")


if __name__ == "__main__":
    main()
