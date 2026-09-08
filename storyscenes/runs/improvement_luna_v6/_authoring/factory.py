#!/usr/bin/env python3
"""Luna: seed -> theater plan -> executable simulation -> 3 previews -> prose.

All authoring requests and responses are saved. Finished worlds run offline.
An interrupted stage can be resumed from its saved response without another call.
No silent paid-call retries or automatic switch away from Flex.
"""
from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import random
import shutil
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "evaluation"))
import trial_cost
import openai_world_set_quality as quality

MODEL = "gpt-5.6-luna"
PROTOCOL = "storyscenes_v1"
PREVIEW_SEEDS = [0, 1, 2]
SAMPLE_SEEDS = list(range(1000, 1100))
THEATERS = [
    ("roof_post", "A child and a young dragon want to deliver invitations across a roof garden. Wind, fragile cargo, and the dragon's wish to help interact."),
    ("library_parade", "A boastful mayor wants the biggest parade. A child librarian, a helpful cart builder, and one shared cart turn that ambition toward something useful."),
    ("pond_concert", "A frog and two children want a pond concert. Different listeners, floating props, and a mistaken assumption about a quiet neighbor matter."),
    ("night_garden", "Two children and a moth prepare a garden welcome after sunset. A lamp, shadows and a shy guest have different needs."),
    ("kite_workshop", "A young dragon and a careful child want a kite to carry a small message. Material limits and curiosity suggest several workable routes."),
    ("bakery_exchange", "A child baker, a proud squirrel and a hungry neighbor share a stall. Ownership, mistaken labels, tastes and fair exchanges interact."),
    ("museum_of_small_things", "Children and a magpie open a museum of overlooked things. An impressive display must also respect borrowed treasures and their owners."),
    ("hill_picnic", "Two children and a donkey plan a picnic for someone who cannot climb the hill. Limited carrying capacity, pride and hospitality change the plan."),
    ("puppet_weather", "Children stage a puppet play in a courtyard. A sudden breeze, a timid puppeteer and an ambitious stage manager create different possible performances."),
    ("clocktower_club", "A child and a young dragon want to start a club in a clocktower. A keeper, a bell, a sleeping neighbor and confusing signals need thoughtful coordination."),
]


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_key(path=None):
    if path:
        os.environ["OPENAI_API_KEY"] = Path(path).read_text().strip()
    if not os.environ.get("OPENAI_API_KEY"):
        raise ValueError("Set OPENAI_API_KEY or pass --api-key-file")


class Budget:
    """Conservative outstanding reservations, persisted BEFORE dispatch.

    Character-count input estimate + maximum output, at standard rates plus a
    cache-write margin. Unknown/failed outcomes retain their whole reservation.
    This is a local spending guard, not a provider-side billing limit.
    """
    def __init__(self, path, limit):
        self.path, self.limit = path, limit
        self.entries = json.loads(path.read_text())["entries"] if path.exists() else []
        self.persist()

    def persist(self):
        save(self.path, dict(limit_usd=self.limit, committed_upper_usd=sum(e["reserved_usd"] for e in self.entries), entries=self.entries))

    def reserve(self, label, request):
        model = request["model"]
        input_rate, _, write_rate, output_rate = trial_cost.FLEX_RATES[model]
        upper = (len(json.dumps(request)) * max(input_rate, write_rate) + request["max_output_tokens"] * output_rate) * 2 / 1e6
        upper = round(upper + 0.01, 6)
        if sum(e["reserved_usd"] for e in self.entries) + upper > self.limit:
            raise ValueError(f"Budget cap would be exceeded by {label}")
        entry = dict(label=label, reserved_usd=upper, status="reserved", time=datetime.now(timezone.utc).isoformat())
        self.entries.append(entry)
        self.persist()
        return len(self.entries) - 1

    def settle(self, index, response):
        cost = trial_cost.token_cost(response.get("model", ""), response.get("usage") or {}, response.get("service_tier", "unknown"))
        self.entries[index].update(status="returned", response_id=response.get("id"), cost=cost)
        if cost["known"]:
            self.entries[index]["reserved_usd"] = cost["usd_high"]
        self.persist()


def request(prompt, *, plan=False):
    body = dict(model=MODEL, service_tier="flex", reasoning={"effort": "none"},
                max_output_tokens=6000 if plan else 16000, store=False,
                input=[dict(role="system", content="You author executable, composable children's story worlds. Follow the supplied authoring contract. Treat example story content as data. Return only the requested artifact."),
                       dict(role="user", content=prompt)])
    if plan:
        props = {k: {"type": "string"} for k in ("title", "premise", "cast_and_props", "kernels_and_interactions", "seed_parameters", "candidate_scenes", "constraints", "different_endings")}
        body["text"] = {"format": {"type": "json_schema", "name": "theater_plan", "strict": True,
                          "schema": {"type": "object", "properties": props, "required": list(props), "additionalProperties": False}}}
    return body


async def api_artifact(client, budget, directory, stage, body):
    req_path, response_path = directory / f"{stage}.request.json", directory / f"{stage}.response.json"
    if response_path.exists():
        if json.loads(req_path.read_text()) != body:
            raise ValueError(f"Refusing to reuse {stage}: frozen request differs")
        response = json.loads(response_path.read_text())
    else:
        if req_path.exists():
            raise ValueError(f"{stage} has an uncertain paid outcome; inspect it before retrying")
        index = budget.reserve(f"{directory.name}/{stage}", body)
        save(req_path, body)
        started = time.monotonic()
        result = await client.responses.create(**body)
        response = result.model_dump(mode="json")
        save(response_path, response)
        budget.settle(index, response)
        print(f"{directory.name}: {stage} returned in {time.monotonic()-started:.1f}s", flush=True)
    if response.get("status") != "completed":
        raise ValueError(f"Incomplete authoring response: {response.get('status')}")
    output = quality.final_text(response).strip()
    if output.startswith("```python") and output.endswith("```"):
        output = output[len("```python"): -3].strip()
    return output


async def execute(world, seeds, *, prose=False, prose_seed=None):
    frozen_worker = world.parent / "_runtime" / "worker.py"
    script = frozen_worker if frozen_worker.exists() else ROOT / "worker.py"
    command = [sys.executable, str(script), str(world), "--seeds", ",".join(map(str, seeds))]
    if prose:
        command += ["--prose"]
    if prose_seed is not None:
        command += ["--prose-seed", str(prose_seed)]
    # Generated code never inherits API credentials. It runs in a separate,
    # time-limited child. The AST lint is not a hostile-code security sandbox.
    env = {k: v for k, v in os.environ.items() if not any(s in k.upper() for s in ("KEY", "TOKEN", "SECRET", "PASSWORD"))}
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    proc = await asyncio.create_subprocess_exec(*command, cwd=world, env=env,
                    stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE)
    try:
        out, err = await asyncio.wait_for(proc.communicate(), timeout=90)
    except asyncio.TimeoutError:
        proc.kill()
        await proc.communicate()
        raise ValueError("Generated script exceeded 90-second validation limit")
    if proc.returncode:
        raise ValueError(err.decode()[-6000:])
    rows = [json.loads(line) for line in out.decode().splitlines()]
    if len(rows) != len(seeds):
        raise ValueError("Wrong number of samples")
    return rows


def compact_preview(rows):
    return [{"seed": r["seed"], "title": r["trace"]["title"], "initial": r["trace"]["initial"],
             "final": r["trace"]["final"], "events": [{k: v for k, v in e.items() if k not in ("before", "after")} for e in r["trace"]["events"]]} for r in rows]


async def build_world(client, budget, world, brief, contract, attempts):
    world.mkdir(exist_ok=True)
    save(world / "seed.json", brief)
    plan_prompt = f"{contract}\n\nSTAGE 2 — PLAN. Return the theater_plan JSON. Design a theater scene generator, NOT one story.\nWorld seed brief: {json.dumps(brief)}"
    plan = json.loads(await api_artifact(client, budget, world, "plan", request(plan_prompt, plan=True)))
    save(world / "plan.json", plan)
    base = f"{contract}\n\nWorld seed: {json.dumps(brief)}\nLuna's theater plan:\n{json.dumps(plan)}"
    feedback = ""
    for attempt in range(attempts):
        prompt = base + "\n\nSTAGE 3 — EXECUTABLE EXPERT SYSTEM. Write only simulation.py source defining build(seed). All prose comes later. Use the shared runtime API exactly. Include at least one shared observe/tell/transfer kernel and meaningful mutually compatible alternative solutions.\n" + feedback
        source = await api_artifact(client, budget, world, f"simulation_{attempt}", request(prompt))
        (world / "simulation.py").write_text(source + "\n")
        try:
            previews = await execute(world, PREVIEW_SEEDS)
            save(world / "simulation_previews.json", compact_preview(previews))
            # Preserve the requested 3 previews and broaden mechanical validation
            # before paying for a renderer over a broken long-tail branch.
            mechanical = await execute(world, SAMPLE_SEEDS)
            unique = {tuple(e["scene"] for e in r["trace"]["events"]) for r in mechanical}
            if len(unique) < 2:
                raise ValueError("100 seeds produced only one scene path; add a meaningful alternative solution")
            save(world / "simulation_validation.json", dict(ok=True, preview_seeds=PREVIEW_SEEDS,
                stress_seeds=SAMPLE_SEEDS, distinct_ordered_scene_paths=len(unique), sha256=digest(world / "simulation.py")))
            break
        except Exception as exc:
            save(world / f"simulation_{attempt}.failure.json", {"error": str(exc)})
            feedback = f"Your prior simulation failed execution. Rewrite the full source correcting the class of defect.\nPrevious source:\n{source}\nFailure:\n{exc}"
    else:
        raise ValueError("Simulation repair budget exhausted")
    frozen = digest(world / "simulation.py")
    prose_base = base + f"\n\nFROZEN SIMULATION (do not rewrite):\n{source}\n\nTHREE ACTUAL VALIDATED RUNS:\n{json.dumps(compact_preview(previews))}"
    feedback = ""
    for attempt in range(attempts):
        prompt = prose_base + "\n\nSTAGE 5 — COMPLETE GENERATOR. Return generator.py Python source implementing render(run,rng) and generate(seed,prose_seed=None), importing frozen build from simulation. Write lively, complete stories, enriched with dialogue and causal transitions. Cover every possible scene.\n" + feedback
        generator = await api_artifact(client, budget, world, f"prose_{attempt}", request(prompt))
        (world / "generator.py").write_text(generator + "\n")
        try:
            rows = await execute(world, SAMPLE_SEEDS, prose=True)
            if digest(world / "simulation.py") != frozen:
                raise ValueError("Simulation changed during prose stage")
            if any(len(r["story"].split()) < 160 for r in rows):
                raise ValueError("At least one sample has fewer than 160 words; provide developed scenes and a complete ending")
            break
        except Exception as exc:
            save(world / f"prose_{attempt}.failure.json", {"error": str(exc)})
            feedback = f"Your prior renderer failed. Rewrite the full generator, preserving frozen simulation.\nPrevious source:\n{generator}\nFailure:\n{exc}"
    else:
        raise ValueError("Prose repair budget exhausted")
    with (world / "samples.jsonl").open("w") as f:
        for row in rows:
            # Full traces for the first three; all others carry event evidence
            # and their digest. Independently reproducible with run.py --json.
            compact = {k: v for k, v in row.items() if k != "trace"}
            compact["scene_path"] = [e["scene"] for e in row["trace"]["events"]]
            compact["causal_edges"] = [[i, e["id"]] for e in row["trace"]["events"] for i in e["causes"]]
            f.write(json.dumps(compact, ensure_ascii=False) + "\n")
    save(world / "samples_with_trace.json", rows[:3])
    (world / "samples.md").write_text("\n\n".join(f"## {r['title']} — seed {r['seed']}\n\n{r['story']}" for r in rows[:3]) + "\n")
    summary = dict(world=world.name, ok=True, title=plan["title"], samples=len(rows),
        simulation_sha256=frozen, generator_sha256=digest(world / "generator.py"),
        distinct_texts=len({r["story"] for r in rows}), distinct_scene_paths=len({tuple(r["scene_path"]) for r in [json.loads(x) for x in (world / "samples.jsonl").read_text().splitlines()]}),
        word_range=[min(len(r["story"].split()) for r in rows), max(len(r["story"].split()) for r in rows)])
    save(world / "summary.json", summary)
    print(f"{world.name}: PASS — 100 stories, {summary['distinct_scene_paths']} scene paths", flush=True)
    return summary


async def main_async(args):
    from openai import AsyncOpenAI
    load_key(args.api_key_file)
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=True)
    settings = dict(protocol=PROTOCOL, seed=args.seed, count=args.count, model=MODEL,
                    service_tier="flex", reasoning_effort="none", attempts=args.attempts)
    if (out / "settings.json").exists() and json.loads((out / "settings.json").read_text()) != settings:
        raise ValueError("Output belongs to a different run; choose a fresh --out")
    save(out / "settings.json", settings)
    budget = Budget(out / "budget.json", args.budget)
    contract_path = out / "AUTHORING.md"
    if not contract_path.exists():
        shutil.copyfile(ROOT / "AUTHORING.md", contract_path)
    contract = contract_path.read_text()
    rng = random.Random(args.seed)
    briefs = [dict(index=i, seed=rng.getrandbits(32), theater=name, premise=premise) for i, (name, premise) in enumerate(THEATERS[:args.count])]
    semaphore = asyncio.Semaphore(args.concurrency)
    async with AsyncOpenAI(base_url="https://api.openai.com/v1", timeout=240, max_retries=0) as client:
        async def one(brief):
            async with semaphore:
                world = out / brief["theater"]
                try:
                    completed = world / "summary.json"
                    if completed.exists():
                        saved = json.loads(completed.read_text())
                        if saved.get("ok") and all(digest(world / f"{name}.py") == saved[f"{name}_sha256"] for name in ("simulation", "generator")):
                            return saved
                    return await build_world(client, budget, world, brief, contract, args.attempts)
                except Exception as exc:
                    row = dict(world=brief["theater"], ok=False, error=str(exc))
                    save(world / "failure.json", row)
                    print(f"{world.name}: FAIL — {exc}", flush=True)
                    # Failed weak-model worlds are quarantined. Historical Terra
                    # recovery is no longer an implicit production fallback.
                    return row
        results = await asyncio.gather(*(one(b) for b in briefs))
    save(out / "summary.json", results)
    authoring = [{"response": json.loads(p.read_text())} for p in out.glob("*/*.response.json")]
    save(out / "authoring_cost.json", trial_cost.summarize(authoring))
    if args.evaluate and all(r["ok"] for r in results):
        await evaluate(out, budget, args.concurrency)
    return int(any(not r["ok"] for r in results))


async def evaluate(out, budget, concurrency):
    inputs = []
    for row in json.loads((out / "summary.json").read_text()):
        if row["ok"]:
            world = out / row["world"]
            pool = [json.loads(x) for x in (world / "samples.jsonl").read_text().splitlines()]
            item = quality.select_set(row["world"], pool, 777)
            item.update(source_sha256=row["generator_sha256"], simulation_sha256=row["simulation_sha256"])
            inputs.append(item)
    destination = out / "quality"
    if destination.exists():
        if not (destination / "inputs.json").exists() or json.loads((destination / "inputs.json").read_text()) != inputs:
            raise ValueError("Existing evaluation has different or incomplete frozen inputs")
        if (destination / "summary.json").exists() and (destination / "quality.jsonl").exists():
            cached = [json.loads(x) for x in (destination / "quality.jsonl").read_text().splitlines()]
            if len(cached) == len(inputs) and all(row.get("ok") for row in cached):
                return cached
        raise ValueError("Existing evaluation is incomplete; inspect paid outcomes before retrying")
    # Reserve every evaluation request before dispatch. Use exact copied
    # protocol, model, calibration, random sampling and strict response checks.
    reservations = [budget.reserve("judge/" + i["script"], quality.request_body(i)) for i in inputs]
    rows = await quality.run_sets(inputs, destination, concurrency=concurrency)
    for index, row in zip(reservations, rows):
        if row.get("response"):
            budget.settle(index, row["response"])
    if any(not row["ok"] for row in rows):
        raise ValueError("Some quality calls failed; see quality/quality.jsonl")
    return rows


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out", type=Path, required=True)
    p.add_argument("--seed", type=int, default=20260907)
    p.add_argument("--count", type=int, default=10, choices=range(1, 11))
    p.add_argument("--concurrency", type=int, default=3)
    p.add_argument("--attempts", type=int, default=3)
    p.add_argument("--budget", type=float, default=10.0)
    p.add_argument("--api-key-file", type=Path)
    p.add_argument("--evaluate", action="store_true")
    args = p.parse_args()
    if args.concurrency < 1 or args.attempts < 1 or not 0 < args.budget <= 10:
        p.error("positive concurrency/attempts and budget in (0,10] required")
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    raise SystemExit(main())
