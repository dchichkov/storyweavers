"""Discover, generate, and audit story-first mini-adventures without API calls."""
import argparse
import json
from pathlib import Path

from .inventory import PACKS, catalogue, load
from .review import audit


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    listing = commands.add_parser("list")
    listing.add_argument("--scenes", action="store_true")
    run = commands.add_parser("run")
    run.add_argument("pack", choices=PACKS)
    run.add_argument("--seed", type=int, default=0)
    run.add_argument("--scenes", type=int, choices=(7, 8), default=8)
    run.add_argument("--params", type=Path)
    review = commands.add_parser("audit")
    review.add_argument("pack", choices=PACKS)
    review.add_argument("--seed", type=int, default=0)
    review.add_argument("--count", type=int, default=50, help="Seeds per length; both seven and eight scenes")
    review.add_argument("--out", required=True, type=Path)
    args = parser.parse_args()
    if args.command == "list":
        print(json.dumps([catalogue(p) if args.scenes else {"pack": p, **info}
                          for p, info in PACKS.items()], indent=2))
    elif args.command == "run":
        module = load(args.pack)
        params = module.Parameters(**json.loads(args.params.read_text())) if args.params else None
        row = module.generate(args.seed, count=args.scenes, params=params)
        print(row["story"])
    else:
        if not 1 <= args.count <= 1000:
            parser.error("--count must be in [1, 1000]")
        summary = audit(args.pack, seeds=list(range(args.seed, args.seed + args.count)), out=args.out)
        print(json.dumps(summary, indent=2))
        if summary["failures"] or summary["inventory_error"] or not summary["source_unchanged"]:
            raise SystemExit(1)


if __name__ == "__main__":
    main()
