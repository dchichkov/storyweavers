#!/usr/bin/env python3
"""Frozen fresh-seed capability trial using the existing story and QA judges.

Run prepare first (offline), then evaluate explicitly. Never replace failed
seed positions or retry an uncertain paid request. No generator edits occur.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
import gzip
import json
import lzma
from pathlib import Path
import random
import shutil
import signal
import statistics
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT.parent))
import factory as f
import conversation_quality as cq
from storyworlds import dataset_score
from storyscenes.capabilities.api import registry
from storyscenes.capabilities.codec import dumps
from storyscenes.capabilities.core import fingerprint, plain, replay, solve
from storyscenes.capabilities.choices import competing_promise_story
from storyscenes.capabilities.reading import Reader
from storyscenes.capabilities.realize import render_story
from storyscenes.capabilities.story_examples import delayed_report_story, loan_story, promise_story

PROTOCOL = "capability_scoring_v2"
BUILDERS = dict(library=loan_story, harbor=delayed_report_story,
                observatory=promise_story, choice=competing_promise_story)


def sources():
    paths = list((ROOT / "capabilities").glob("*.py"))
    paths += [ROOT / name for name in ("__init__.py", "capability_trial.py", "factory.py", "api_requests.py",
              "evaluation/conversation_quality.py", "evaluation/openai_world_set_quality.py",
              "evaluation/openai_story_quality.py", "evaluation/trial_cost.py")]
    paths.append(ROOT.parent / "storyworlds/dataset_score.py")
    return {str(path.relative_to(ROOT.parent)): path for path in paths}


def assert_sources(out):
    hashes = json.loads((out / "source_hashes.json").read_text())
    for name, path in sources().items():
        if hashes.get(name) != f.digest(path):
            raise ValueError(f"Source changed since trial preparation: {name}")


def read_rows(path):
    return [json.loads(line) for line in path.read_text().splitlines()] if path.exists() else []


def append(stream, row):
    stream.write(json.dumps(row, ensure_ascii=False) + "\n")
    stream.flush()


def conversations(document, seed, count=6):
    """Uniform supported QA anchors; add a same-event why only when available.

    This measures supported-answer quality, not unanswerable-query coverage or
    the old generator's conversation distribution. No hidden trace is sent.
    """
    questions = Reader(document).questions()
    chosen = random.Random(seed).sample(questions, min(count, len(questions)))
    result = []
    for index, answer in enumerate(chosen):
        target = [s for s in document.statements if s.id in answer.statement_ids
                  and s.answer == answer.answer and s.question and answer.question.startswith(s.question)][-1]
        reader = Reader(document)
        reader.ask(target.kind, target.focus, event_id=target.event_ids[0],
                   reference_tick=target.reference_tick)
        turns = [plain(answer)]
        if target.kind != "why":
            why = reader.follow_up("why")
            if why.supported:
                turns.append({**plain(why), "question": "Why?"})
        result.append(dict(id=f"c{index:03d}", turns=turns))
    return result


class CPUTimeout(BaseException):
    """Escape search exception handlers; the supervising process is the backstop."""


def _deadline(signum, frame):
    raise CPUTimeout("Per-seed CPU time limit exceeded")


def sample_one(job):
    world, seed, max_nodes, cpu_seconds = job
    started, cpu = time.monotonic(), time.process_time()
    row = dict(world=world, seed=seed, sample_id=f"{world}:{seed}", ok=False)
    trace = None
    previous = signal.signal(signal.SIGPROF, _deadline)
    try:
        signal.setitimer(signal.ITIMER_PROF, cpu_seconds, 0.05)
        engine, spec = registry(), BUILDERS[world]().spec
        state = solve(engine, spec, seed, max_nodes=max_nodes)
        # The sampling limit does not interrupt validation of a found outcome.
        signal.setitimer(signal.ITIMER_PROF, 0)
        path = [e.action.id for e in state.events]
        if replay(engine, spec, path) != state:
            raise ValueError("Seeded outcome failed exact replay")
        doc = render_story(spec, state)  # No pinned-path opening or ending.
        if not doc.story.strip():
            raise ValueError("Empty narrative")
        qa = Reader(doc).questions()
        row.update(ok=True, story=doc.story, story_sha256=fingerprint(doc.story), path=path,
                   trace_sha256=fingerprint(state), qa=plain(qa), conversations=conversations(doc, seed),
                   words=len(doc.story.split()), events=len(state.events),
                   event_multiset=sorted(Counter(path).items()))
        trace = dict(sample_id=row["sample_id"], trace=plain(state), statements=plain(doc.statements), spans=doc.spans())
    except (Exception, CPUTimeout) as exc:
        row.update(error_type=type(exc).__name__, error=str(exc))
    finally:
        signal.setitimer(signal.ITIMER_PROF, 0)
        signal.signal(signal.SIGPROF, previous)
    row.update(wall_seconds=round(time.monotonic() - started, 4), cpu_seconds=round(time.process_time() - cpu, 4))
    return row, trace


def supervise(job, wall_seconds):
    """One disposable child per seed; kill and reap even if its timer fails."""
    started = time.monotonic()
    row = dict(world=job[0], seed=job[1], sample_id=f"{job[0]}:{job[1]}", ok=False, cpu_seconds=None)
    try:
        child = subprocess.run([sys.executable, str(Path(__file__).resolve()), "_sample"],
                               input=json.dumps(job), capture_output=True, text=True,
                               timeout=wall_seconds, check=True)
        return json.loads(child.stdout)
    except subprocess.TimeoutExpired:
        row.update(error_type="WallTimeout", error=f"Child killed after {wall_seconds}s wall limit")
    except (subprocess.CalledProcessError, ValueError) as exc:
        row.update(error_type="WorkerError", error=str(exc))
        if isinstance(exc, subprocess.CalledProcessError):
            row["stderr"] = exc.stderr[-4000:]
    row["wall_seconds"] = round(time.monotonic() - started, 4)
    return row, None


def prepare(out, *, count=1000, seed=19000, workers=6, max_nodes=6000, cpu_seconds=2.0, wall_seconds=6.0, stop_after=0):
    settings = dict(protocol=PROTOCOL, worlds=list(BUILDERS), requested_per_world=count,
                    seed=seed, max_nodes=max_nodes, cpu_seconds=cpu_seconds, wall_seconds=wall_seconds,
                    timeout="repeating child CPU signal plus parent-enforced wall kill; startup counts toward wall limit",
                    generation="fresh seeded author-side DFS, full trace, no pinned flourishes",
                    failures="all attempted positions retained; never replace or deduplicate",
                    judge_count=10, selection_seed=777, qa_selection="six uniform supported anchors, same-event why when supported",
                    judge_model=f.quality.DEFAULT_MODEL, service_tier="flex", reasoning_effort="none")
    if out.exists():
        if json.loads((out / "settings.json").read_text()) != settings:
            raise ValueError("Refusing changed trial settings")
        assert_sources(out)
    else:
        out.mkdir(parents=True)
        f.save(out / "settings.json", settings)
        snapshot = out / "_source"
        for name, source in sources().items():
            target = snapshot / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, target)
        f.save(out / "source_hashes.json", {name: f.digest(path) for name, path in sources().items()})
        (out / "worlds").mkdir()
        for name, builder in BUILDERS.items():
            (out / "worlds" / f"{name}.json").write_text(dumps(builder().spec), encoding="utf-8")
    attempts = read_rows(out / "attempts.jsonl")
    done = {r["sample_id"] for r in attempts}
    if len(done) != len(attempts):
        raise ValueError("Duplicate attempt IDs")
    jobs = [(world, s, max_nodes, cpu_seconds) for s in range(seed, seed + count)
            for world in BUILDERS if f"{world}:{s}" not in done]
    if stop_after:
        jobs = jobs[:stop_after]
    if jobs:
        with (out / "attempts.jsonl").open("a", encoding="utf-8") as attempts_file, \
             gzip.open(out / "traces.jsonl.gz", "at", encoding="utf-8") as traces_file:
            pool = ThreadPoolExecutor(max_workers=workers)
            futures = [pool.submit(supervise, job, wall_seconds) for job in jobs]
            try:
                for future in as_completed(futures):
                    row, trace = future.result()
                    # Trace first; a crash can leave an orphan trace, never a successful row with no trace.
                    if trace is not None:
                        append(traces_file, trace)
                    append(attempts_file, row)
                    attempts.append(row)
                    if len(attempts) % 40 == 0:
                        print(f"Generated {len(attempts)}/{count * len(BUILDERS)} positions; "
                              f"{sum(r['ok'] for r in attempts)} replay-verified stories", flush=True)
            finally:
                pool.shutdown(wait=True, cancel_futures=True)
    assert_sources(out)
    report = mechanical_summary(attempts, count)
    f.save(out / "mechanical_summary.json", report)
    if report["complete"]:
        # One corpus archive, story text only. Duplicate positions are retained.
        ordered = sorted((r for r in attempts if r["ok"]), key=lambda r: r["sample_id"])
        payload = b"".join(dataset_score.encode_story(r["story"]) for r in ordered)
        (out / "stories.jsonl.xz").write_bytes(lzma.compress(payload, preset=6))
        f.save(out / "all_text_compression.json", dict(stories=len(ordered), utf8_bytes=len(payload),
                xz_bytes=len((out / "stories.jsonl.xz").read_bytes()),
                unique_retention=dataset_score.compression_retention(sorted({r["story"] for r in ordered})),
                note="All returned text, before quality gating. XZ/raw ratio is not compression retention."))
    return report


def mechanical_summary(rows, requested):
    worlds = {}
    for world in BUILDERS:
        attempts = [r for r in rows if r["world"] == world]
        good = [r for r in attempts if r["ok"]]
        worlds[world] = dict(attempts=len(attempts), requested=requested, returned=len(good),
            failures=dict(Counter(r["error_type"] for r in attempts if not r["ok"])),
            exact_unique=len({r["story"] for r in good}),
            action_order_unique=len({tuple(r["path"]) for r in good}),
            action_multiset_unique=len({json.dumps(r["event_multiset"]) for r in good}),
            mean_words=statistics.mean(r["words"] for r in good) if good else None,
            measured_cpu_seconds=sum(r["cpu_seconds"] or 0 for r in attempts),
            unmeasured_cpu_attempts=sum(r["cpu_seconds"] is None for r in attempts))
    return dict(worlds=worlds, complete=all(w["attempts"] == requested for w in worlds.values()),
                requested=requested * len(BUILDERS), returned=sum(w["returned"] for w in worlds.values()),
                generation_api_cost_usd=0)


def jobs_for(rows):
    jobs, selections = [], []
    for world in BUILDERS:
        pool = sorted((r for r in rows if r["world"] == world and r["ok"]), key=lambda r: r["seed"])
        if len(pool) < 2:
            continue
        item = f.quality.select_set(world, pool, 777, count=10)
        selected = [pool[s["source_index"]] for s in item["stories"]]
        for story, row in zip(item["stories"], selected):
            story["sample_id"] = row["sample_id"]
        selections += selected
        jobs.append(dict(phase="story_quality", stage=world, input=item,
                         body=f.quality.request_body(item, cache_prompts=True)))
        for offset in range(0, len(selected), 5):
            batch = selected[offset:offset + 5]
            jobs.append(dict(phase="qa_quality", stage=f"{world}_{offset // 5:02d}", input=batch,
                             body=cq.request_body(batch)))
    return jobs, selections


async def evaluate(out, *, budget_limit, api_key_file, concurrency=4):
    from openai import AsyncOpenAI
    assert_sources(out)
    settings = json.loads((out / "settings.json").read_text())
    rows = read_rows(out / "attempts.jsonl")
    mechanical = mechanical_summary(rows, settings["requested_per_world"])
    if not mechanical["complete"]:
        raise ValueError("Finish the planned sampling positions before judging")
    jobs, selections = jobs_for(rows)
    f.save(out / "judge_samples.json", selections)
    f.save(out / "judge_manifest.json", [dict(phase=j["phase"], stage=j["stage"], request_sha256=fingerprint(j["body"])) for j in jobs])
    budget_path = out / "budget.json"
    if budget_path.exists() and json.loads(budget_path.read_text())["limit_usd"] != budget_limit:
        raise ValueError("Refusing to change the authorized spending cap on resume")
    budget = f.Budget(budget_path, budget_limit)
    f.load_key(api_key_file)
    semaphore = asyncio.Semaphore(concurrency)
    async with AsyncOpenAI(base_url="https://api.openai.com/v1", timeout=900.0, max_retries=0) as client:
        async def one(job):
            async with semaphore:
                directory = out / job["phase"]
                directory.mkdir(exist_ok=True)
                result_path = directory / f"{job['stage']}.result.json"
                # Saved failures are not automatic authorization to spend again.
                if result_path.exists():
                    return json.loads(result_path.read_text())
                f.save(directory / f"{job['stage']}.input.json", job["input"])
                result = dict(phase=job["phase"], stage=job["stage"], ok=False)
                try:
                    text = await f.api_artifact(client, budget, directory, job["stage"], job["body"])
                    body = json.loads((directory / f"{job['stage']}.response.json").read_text())
                    if body.get("service_tier") != "flex":
                        raise ValueError("Unexpected service tier; no fallback authorized")
                    value = json.loads(text)
                    result["assessment"] = (f.quality.validate(value, job["input"]) if job["phase"] == "story_quality"
                                             else cq.validate(value, job["input"]))
                    result["ok"] = True
                except Exception as exc:
                    result["error"] = str(exc)
                response_path = directory / f"{job['stage']}.response.json"
                if response_path.exists():
                    body = json.loads(response_path.read_text())
                    result["response"] = {k: body.get(k) for k in ("id", "model", "status", "service_tier", "usage")}
                f.save(result_path, result)
                print(f"Judged {job['phase']}/{job['stage']}: {'OK' if result['ok'] else 'FAILED (see artifact)'}", flush=True)
                return result
        results = await asyncio.gather(*(one(job) for job in jobs))
    return summarize(out, rows, results, budget)


def summarize(out, rows, results, budget):
    settings = json.loads((out / "settings.json").read_text())
    requested = settings["requested_per_world"]
    mechanical = mechanical_summary(rows, requested)
    stories = [dict(r, **r.get("assessment", {})) for r in results if r["phase"] == "story_quality"]
    ratings = {r["stage"]: r for r in stories}
    groups = [[r for r in rows if r["world"] == w and r["ok"]] for w in BUILDERS]
    # A fully passing mechanical gate requires every requested position, not just survivors.
    checks = [dict(script=w, final=dict(ok=len(group) == requested), verify=dict(ok=all(r["trace_sha256"] for r in group)))
              for w, group in zip(BUILDERS, groups)]
    score = dataset_score.score_dataset(checks, ratings, groups, requested)
    per_world = {w: dataset_score.score_dataset([check], ratings, [group], requested)
                 for w, check, group in zip(BUILDERS, checks, groups)}
    report = dict(protocol=PROTOCOL, mechanical=mechanical,
        story_quality=f.quality.summarize(stories),
        qa_quality=cq.summarize([r for r in results if r["phase"] == "qa_quality"]),
        geometric_score=score, per_world_scores=per_world, cost=f.trial_cost.summarize(results),
        reserved_upper_usd=sum(e["reserved_usd"] for e in budget.entries), budget_usd=budget.limit,
        unresolved_reservations=sum(e["status"] != "returned" or not e.get("cost", {}).get("known") for e in budget.entries),
        returned_tiers=dict(Counter(r["response"]["service_tier"] for r in results if r.get("response"))),
        failures=[dict(phase=r["phase"], stage=r["stage"], error=r.get("error")) for r in results if not r["ok"]])
    f.save(out / "evaluation_summary.json", report)
    lines = ["# Fresh capability-story baseline", "", "Scores 0-9; unchanged Terra/Flex story and conversation rubrics.",
             "Quality is conditional on returned samples. Timeouts and failed seeds remain in yield denominators.", "",
             "| Demo | Returned / planned | Exact unique | Action multisets | Quality | Semantic diversity | QA overall |",
             "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for w, m in mechanical["worlds"].items():
        rating = ratings.get(w, {})
        qa = cq.summarize([r for r in results if r["phase"] == "qa_quality" and r["stage"].startswith(w + "_")])
        def number(v):
            return "unrated" if v is None else f"{v:.2f}"
        lines.append(f"| {w} | {m['returned']} / {requested} | {m['exact_unique']} | {m['action_multiset_unique']} | "
                     f"{number(rating.get('rating', {}).get('overall'))} | {number(rating.get('diversity', {}).get('overall'))} | "
                     f"{number(qa['mean_quality']['overall'])} |")
    lines += ["", f"Strict geometric index: {score['score']} / 100. Requires every planned seed to pass replay and mean quality >= 6.",
              "The formula is unchanged; mechanical gate adapts script verification to typed-world validation and exact replay.",
              "Semantic diversity is separate, not another geometric-score factor.", "",
              f"Returned-usage estimated cost: ${report['cost']['usd_low']:.4f}-${report['cost']['usd_high']:.4f}; "
              f"${report['reserved_upper_usd']:.4f} committed including uncertain reservations, under ${budget.limit:.2f} local cap.",
              "Local guard is not provider-side invoice reconciliation. No automatic paid retries or tier fallback.", "",
              "QA uses six uniformly sampled supported questions per selected story, adding same-event why follow-ups when supported.",
              "This is not the same conversation mix as the older benchmark, nor an evaluation of arbitrary unanswerable prompts.",
              "The full seeded trace is rendered, without pinned-path openings/endings. Search uses fixed authored goals,",
              "so sampled variation measures this bounded author-side planner, not autonomous character behavior.", ""]
    for r in stories:
        if r.get("ok"):
            lines += [f"## {r['stage']}", "", r["diversity_evidence"], ""]
            lines += [f"- {s['id']}: {s['rating']['overall']}/9. {s['note']}" for s in r["story_ratings"]]
            lines.append("")
    (out / "REPORT.md").write_text("\n".join(lines), encoding="utf-8")
    return report


def main():
    if sys.argv[1:] == ["_sample"]:
        print(json.dumps(sample_one(json.load(sys.stdin)), ensure_ascii=False))
        return
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "evaluate"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--seed", type=int, default=19000)
    parser.add_argument("--workers", type=int, default=6)
    parser.add_argument("--max-nodes", type=int, default=6000)
    parser.add_argument("--cpu-seconds", type=float, default=2.0)
    parser.add_argument("--wall-seconds", type=float, default=6.0)
    parser.add_argument("--stop-after", type=int, default=0, help="Checkpoint after this many new local attempts")
    parser.add_argument("--budget", type=float, default=5.0)
    parser.add_argument("--api-key-file", type=Path)
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    if min(args.count, args.workers, args.max_nodes, args.cpu_seconds, args.wall_seconds, args.concurrency) <= 0 or args.stop_after < 0 or not 0 < args.budget <= 5:
        parser.error("Positive limits required; authorized scoring cap is at most $5")
    if args.phase == "prepare":
        report = prepare(args.out, count=args.count, seed=args.seed, workers=args.workers,
                         max_nodes=args.max_nodes, cpu_seconds=args.cpu_seconds, wall_seconds=args.wall_seconds, stop_after=args.stop_after)
    else:
        report = asyncio.run(evaluate(args.out, budget_limit=args.budget, api_key_file=args.api_key_file,
                                      concurrency=args.concurrency))
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
