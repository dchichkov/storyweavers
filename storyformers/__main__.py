"""Frequency baseline. For grammar layers/projection: python -m storyformers.demo."""

import argparse
from dataclasses import asdict
from itertools import islice
import json
from pathlib import Path

from .model import Storyformer


def documents(path: Path, text_key: str):
    """Text: one document per nonempty line. JSONL: one string field per row."""
    with path.open(encoding="utf-8") as source:
        for line_number, line in enumerate(source, 1):
            if not line.strip():
                continue
            if path.suffix == ".jsonl":
                row = json.loads(line)
                value = row.get(text_key)
                if not isinstance(value, str):
                    raise ValueError(f"{path}:{line_number}: expected string field {text_key!r}")
                yield value
            else:
                yield line.strip()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--train", type=Path, action="append", help="text or JSONL corpus; repeatable")
    parser.add_argument("--text-key", default="story", help="JSONL training field (default: story)")
    parser.add_argument("--limit", type=int, help="maximum training documents per file")
    parser.add_argument("--load", type=Path)
    parser.add_argument("--save", type=Path)
    parser.add_argument("--prompt", default="the rabbit")
    parser.add_argument("--context-size", type=int)
    parser.add_argument("--blocks", type=int)
    parser.add_argument("--top-k", type=int)
    parser.add_argument("--trace", action="store_true", help="include residual dictionaries and per-position readouts")
    args = parser.parse_args()
    if args.limit is not None and args.limit < 1:
        parser.error("--limit must be positive")
    try:
        if args.load:
            if args.context_size is not None or args.blocks is not None:
                parser.error("--load uses the saved context size and block count")
            model = Storyformer.load(args.load)
            if args.top_k is not None:
                if args.top_k < 1:
                    parser.error("--top-k must be positive")
                model.top_k = args.top_k
        else:
            model = Storyformer(context_size=args.context_size if args.context_size is not None else 256,
                                num_blocks=args.blocks if args.blocks is not None else 2,
                                top_k=args.top_k if args.top_k is not None else 10)
        corpora = args.train or ([] if args.load else [Path(__file__).parent / "data" / "demo.txt"])
        for corpus in corpora:
            model.fit(islice(documents(corpus, args.text_key), args.limit))
        if args.save:
            model.save(args.save)
        result = model.forward(args.prompt)
        output = {
            "prompt": args.prompt,
            "context_size": model.context_size,
            "blocks": len(model.blocks),
            "visible_tokens": len(result.residual_stream),
            "next_token": asdict(result.next_token),
        }
        if args.trace:
            output["residual_stream"] = result.residual_stream
            output["position_readouts"] = [asdict(row) for row in result.predictions]
        print(json.dumps(output, indent=2, ensure_ascii=False))
    except (OSError, RuntimeError, ValueError) as error:
        parser.exit(1, f"storyformers: {error}\n")


if __name__ == "__main__":
    main()
