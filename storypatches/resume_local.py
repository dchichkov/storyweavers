"""Resume selected local story slots, preserving completed artifacts."""
import argparse
import asyncio
import json
from pathlib import Path

from openai import AsyncOpenAI
from .artifacts import Budget, save_json
from .catalog import sample_seed
from .pipeline import author_story, parser, official_openai


async def main():
    cli = argparse.ArgumentParser(description=__doc__)
    cli.add_argument("--run", type=Path, required=True)
    cli.add_argument("--indices", type=int, nargs="+", required=True)
    cli.add_argument("--attempts", type=int, default=8)
    cli.add_argument("--concurrency", type=int, default=4)
    cli.add_argument("--fast-patches", action="store_true")
    opts = cli.parse_args()
    settings = json.loads((opts.run / "settings.json").read_text())
    if official_openai(settings["base_url"]):
        raise ValueError("this recovery command is only for local generation")
    args = parser().parse_args(["--out", str(opts.run)])
    for key, value in settings.items():
        if hasattr(args, key):
            setattr(args, key, value)
    args.patch_attempts = opts.attempts
    args.concurrency = opts.concurrency
    args.fast_patches = opts.fast_patches
    args.reasoning_effort = None
    args.service_tier = None
    async with AsyncOpenAI(api_key="local", base_url=args.base_url, timeout=900, max_retries=0) as client:
        async def one(index):
            if not 0 <= index < settings["count"]:
                raise ValueError("index outside saved run")
            budget = Budget(opts.run / f"resume_budget_{index}.json", settings["budget"])
            try:
                result = await author_story(client, budget, opts.run.resolve(), sample_seed(args.seed, index).to_dict(), args)
            except Exception as exc:
                result = {"ok": False, "story": f"story_{index:03d}", "error": str(exc)}
            save_json(opts.run / f"resume_result_{index}.json", result)
            print(result, flush=True)
            return result
        await asyncio.gather(*(one(index) for index in opts.indices))
    summaries = []
    for index in range(settings["count"]):
        path = opts.run / f"story_{index:03d}" / "summary.json"
        if not path.exists():
            path = opts.run / f"resume_result_{index}.json"
        summaries.append(json.loads(path.read_text()) if path.exists() else {"ok": False, "story": f"story_{index:03d}"})
    save_json(opts.run / "summary.json", summaries)
    from storyscenes.evaluation import trial_cost
    responses = [{"response": json.loads(path.read_text())} for path in opts.run.glob("story_*/*.response.json")]
    save_json(opts.run / "cost.json", trial_cost.summarize(responses))


if __name__ == "__main__":
    asyncio.run(main())
