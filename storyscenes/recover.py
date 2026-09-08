#!/usr/bin/env python3
"""Explicit second-pass repair: Terra repairs failed mechanics, Luna adds prose.

Uses a separate capped ledger, keeps the original no-reasoning attempts, and
does not repeat completed plans. Run after the requested world's factory task
has failed; never repair a world while its authoring task is still active.
"""
import argparse
import asyncio
import json
from pathlib import Path
import random
import sys

import factory as f


def request(prompt, model):
    body = f.request(prompt)
    body["model"] = model
    body["reasoning"] = {"effort": "medium" if model == "gpt-5.6-terra" else "low"}
    return body


async def repair(client, budget, world):
    contract = (world.parent / "AUTHORING.md").read_text()
    world.mkdir(exist_ok=True)
    if not (world / "plan.json").exists():
        settings = json.loads((world.parent / "settings.json").read_text())
        rng = random.Random(settings["seed"])
        briefs = {name: dict(index=i, seed=rng.getrandbits(32), theater=name, premise=premise)
                  for i, (name, premise) in enumerate(f.THEATERS)}
        brief = briefs[world.name]
        f.save(world / "seed.json", brief)
        body = f.request(contract + "\n\nReturn the theater_plan JSON for this seeded world: " + json.dumps(brief), plan=True)
        plan = json.loads(await f.api_artifact(client, budget, world, "recovery_plan", body))
        f.save(world / "plan.json", plan)
    plan = json.loads((world / "plan.json").read_text())
    source = (world / "simulation.py").read_text() if (world / "simulation.py").exists() else "No simulation was completed. Implement the plan from scratch."
    failures = "\n".join(p.read_text() for p in sorted(world.glob("simulation_*.failure.json")))
    base = f"{contract}\n\nPLAN:\n{json.dumps(plan)}"
    for attempt in range(3):
        prompt = base + f"\n\nRepair this Luna-authored simulation against the exact API. Preserve its theater and meaningful branching, but simplify overcomplicated or unreachable machinery. Return only full simulation.py source.\n{source}\n\nRecorded validation failures:\n{failures}\n\nCheck every state prefix has an entity, every used key is declared, Effect arguments are (key, value, op), Rule arguments are (name, must_tuple, when_tuple). Avoid abstract unembedded phase counters. Ensure ALL seeds 0,1,2 and 1000..1099 have valid completed stories, with multiple causal solutions. Every important final physical outcome must have a state key."
        stage = f"repair_sim_{attempt}"
        saved_request = world / f"{stage}.request.json"
        body = json.loads(saved_request.read_text()) if saved_request.exists() else request(prompt, "gpt-5.6-terra")
        source = await f.api_artifact(client, budget, world, stage, body)
        (world / "simulation.py").write_text(source + "\n")
        try:
            previews = await f.execute(world, f.PREVIEW_SEEDS)
            mechanical = await f.execute(world, f.SAMPLE_SEEDS)
            paths = {tuple(e["scene"] for e in r["trace"]["events"]) for r in mechanical}
            if len(paths) < 2:
                raise ValueError("Only one scene path")
            f.save(world / "simulation_previews.json", f.compact_preview(previews))
            f.save(world / "simulation_validation.json", dict(ok=True, preview_seeds=f.PREVIEW_SEEDS,
                stress_seeds=f.SAMPLE_SEEDS, distinct_ordered_scene_paths=len(paths), sha256=f.digest(world / "simulation.py"), repair_model="gpt-5.6-terra"))
            break
        except Exception as exc:
            failures = str(exc)
            f.save(world / f"repair_sim_{attempt}.failure.json", {"error": failures})
    else:
        raise ValueError(f"{world.name}: Terra repair attempts exhausted")
    frozen = f.digest(world / "simulation.py")
    prompt_base = base + f"\n\nFROZEN VALIDATED SIMULATION:\n{source}\n\nTHREE EXECUTED PREVIEWS:\n{json.dumps(f.compact_preview(previews))}"
    feedback = ""
    for attempt in range(3):
        prompt = prompt_base + "\n\nWrite the complete generator.py, importing build from simulation and solve/realize from runtime. Implement render(run,rng) and generate(seed,prose_seed=None) exactly as contracted. Keep the simulation unchanged. Narrate every possible scene ID, with rich but grounded prose, including dialogue exchanges, a clear premise and a concrete ending proving what actually changed. Aim for 250–450 words per sample. Read before/after state for continuity when independent scenes change order. Never describe a plan as an accomplished action. Return Python source only.\n" + feedback
        stage = f"repair_prose_{attempt}"
        saved_request = world / f"{stage}.request.json"
        body = json.loads(saved_request.read_text()) if saved_request.exists() else request(prompt, "gpt-5.6-luna")
        source_prose = await f.api_artifact(client, budget, world, stage, body)
        (world / "generator.py").write_text(source_prose + "\n")
        try:
            rows = await f.execute(world, f.SAMPLE_SEEDS, prose=True)
            if min(len(r["story"].split()) for r in rows) < 160:
                raise ValueError("Some stories have fewer than 160 words; develop the scenes")
            if frozen != f.digest(world / "simulation.py"):
                raise ValueError("Simulation changed")
            break
        except Exception as exc:
            f.save(world / f"repair_prose_{attempt}.failure.json", {"error": str(exc)})
            feedback = f"Fix the full generator. Previous source:\n{source_prose}\nFailure: {exc}"
    else:
        raise ValueError(f"{world.name}: prose repair attempts exhausted")
    with (world / "samples.jsonl").open("w") as out:
        for row in rows:
            compact = {k: v for k, v in row.items() if k != "trace"}
            compact["scene_path"] = [e["scene"] for e in row["trace"]["events"]]
            compact["causal_edges"] = [[i, e["id"]] for e in row["trace"]["events"] for i in e["causes"]]
            out.write(json.dumps(compact, ensure_ascii=False) + "\n")
    f.save(world / "samples_with_trace.json", rows[:3])
    (world / "samples.md").write_text("\n\n".join(f"## {r['title']} — seed {r['seed']}\n\n{r['story']}" for r in rows[:3]) + "\n")
    summary = dict(world=world.name, ok=True, title=plan["title"], samples=len(rows),
        simulation_sha256=frozen, generator_sha256=f.digest(world / "generator.py"),
        distinct_texts=len({r["story"] for r in rows}),
        distinct_scene_paths=len({tuple(e["scene"] for e in r["trace"]["events"]) for r in rows}),
        word_range=[min(len(r["story"].split()) for r in rows), max(len(r["story"].split()) for r in rows)],
        repair_model="gpt-5.6-terra", prose_model="gpt-5.6-luna", prose_reasoning="low")
    f.save(world / "summary.json", summary)
    print(f"{world.name}: RECOVERED — {summary['distinct_scene_paths']} paths", flush=True)
    return summary


async def main_async(args):
    from openai import AsyncOpenAI
    f.load_key(args.api_key_file)
    root = args.run.resolve()
    # The initial authoring process must have stopped before this full recovery.
    # Its uncertain reservations stay charged. Leave $2 of the user's total
    # $10 ceiling available for final judging.
    original = json.loads((root / "budget.json").read_text())["committed_upper_usd"]
    budget = f.Budget(root / "recovery_budget.json", max(0, 8.0 - original))
    semaphore = asyncio.Semaphore(args.concurrency)
    async with AsyncOpenAI(base_url="https://api.openai.com/v1", timeout=240, max_retries=0) as client:
        async def one(name):
            async with semaphore:
                world = root / name
                if (world / "summary.json").exists() and json.loads((world / "summary.json").read_text()).get("ok"):
                    return json.loads((world / "summary.json").read_text())
                try:
                    return await repair(client, budget, world)
                except Exception as exc:
                    print(f"{name}: RECOVERY FAILED — {exc}", flush=True)
                    return dict(world=name, ok=False, error=str(exc))
        rows = await asyncio.gather(*(one(name) for name in args.worlds))
    return int(any(not row["ok"] for row in rows))


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--run", type=Path, required=True)
    p.add_argument("--worlds", nargs="+", required=True)
    p.add_argument("--concurrency", type=int, default=3)
    p.add_argument("--api-key-file", type=Path)
    raise SystemExit(asyncio.run(main_async(p.parse_args())))
