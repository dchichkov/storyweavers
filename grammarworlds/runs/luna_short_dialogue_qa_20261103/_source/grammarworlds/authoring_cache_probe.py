"""Two small real Terra authoring calls to measure shared-prefix cache reuse.

Uses the production request builder and dispatch/evidence recorder. This is a
cache diagnostic, not a full event-pack quality evaluation. Never executes the
returned code. Existing output directories cannot be overwritten.
"""
import argparse
import asyncio
from pathlib import Path

from .authoring_trial import ROOT, SOURCE, MODELS, author_request, call, save, digest


async def probe(out):
    out.mkdir(parents=True, exist_ok=False)
    names = ["story.py", "grammarworlds/world.py", "grammarworlds/grammar.py",
             "grammarworlds/engine.py", "grammarworlds/test_grammarworlds.py"]
    sources = {name: (ROOT / name).read_text() for name in names}
    save(out / "settings.json", dict(model=MODELS["terra"], tier="flex", reasoning="high",
        sources={name: digest(ROOT / name) for name in names},
        purpose="Two small authoring tasks sharing the real engine prefix; no full pack rerun",
        builder_sha256=digest(ROOT / "grammarworlds/authoring_trial.py")))
    rows = []
    for index, noun in enumerate(("drum", "sheet"), 1):
        directory = out / f"request{index}"
        directory.mkdir()
        contract = ("This is a tiny authoring/cache diagnostic, not a full pack task. "
            "Return a Python module containing only an import from grammarworlds.grammar "
            "and a function phrase() returning a Node with two weighted noun-phrase "
            f"alternatives referring to the physical {noun} in the story. Use the existing "
            "choice/text API exactly. No world mutations. Keep code under 12 lines, "
            "design_notes under 30 words and mismatches empty. Return JSON fields "
            "design_notes, mismatches, code. Do not analyze unrelated engine changes.")
        body = author_request(MODELS["terra"], sources, SOURCE.read_text(),
                              contract=contract, gaps=[], max_output_tokens=2048)
        save(directory / "request.json", body)
        raw = await call(directory)
        usage = raw["usage"]
        details = usage["input_tokens_details"]
        rows.append(dict(request=index, model=raw["model"], service_tier=raw["service_tier"],
            status=raw["status"], input_tokens=usage["input_tokens"],
            cached_tokens=details["cached_tokens"], cache_write_tokens=details.get("cache_write_tokens"),
            cached_fraction=details["cached_tokens"] / usage["input_tokens"],
            output_tokens=usage["output_tokens"]))
        save(out / "summary.json", dict(requests=rows, verified_hit=len(rows) == 2 and rows[-1]["cached_tokens"] > 0))
        print(rows[-1], flush=True)
    if not rows[-1]["cached_tokens"]:
        raise RuntimeError("Second request did not hit cache; inspect evidence before another paid probe")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    asyncio.run(probe(args.out))
