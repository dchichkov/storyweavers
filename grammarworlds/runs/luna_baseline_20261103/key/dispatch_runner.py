"""Offline sampling plus the repository's story-set rubric, evaluated by Luna.

Generation remains classical. Only the explicit `run` phase calls an LLM.
"""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import statistics
import sys
import time
import uuid

from .engine import generate
from .world import SCENARIOS

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "storyscenes/evaluation"))
import openai_world_set_quality as quality
from storyscenes import harbor_judge_protocol as protocol

MODEL = "gpt-6-luna"


def save(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")


def read(path):
    return json.loads(path.read_text())


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sample_pool(scenario, count, seed):
    rows = []
    for offset in range(count):
        generated = generate(scenario, seed + offset)
        rows.append(dict(scenario=scenario, seed=seed + offset, story=generated["story"],
            frames=[sentence["frame"] for sentence in generated["sentences"]],
            initial_world=generated["initial_world"],
            final_world={k: v for k, v in generated["final_world"].items() if k != "history"}))
    return rows


def diversity_metrics(rows):
    """Descriptive support measures, never substitutes for semantic diversity."""
    texts = Counter(row["story"] for row in rows)
    paths = Counter(" > ".join(frame["kind"] for frame in row["frames"]) for row in rows)
    sentence_counts = Counter(sentence.strip() for row in rows
                              for sentence in re.split(r"(?<=[.!?])\s+", row["story"]))
    tokens = [re.findall(r"\b[\w']+\b", row["story"].lower()) for row in rows]
    trigrams = [{tuple(words[i:i + 3]) for i in range(len(words) - 2)} for words in tokens]
    similarities = [len(left & right) / len(left | right) if left | right else 1.0
                    for i, left in enumerate(trigrams) for right in trigrams[i + 1:]]
    return dict(samples=len(rows), exact_unique_texts=len(texts),
        exact_duplicate_fraction=1 - len(texts) / len(rows),
        unique_event_kind_paths=len(paths), largest_event_path_fraction=max(paths.values()) / len(rows),
        event_kind_paths=dict(paths.most_common()),
        mean_pairwise_trigram_jaccard=statistics.mean(similarities) if similarities else None,
        sentence_occurrences=sum(sentence_counts.values()), unique_sentences=len(sentence_counts),
        mean_words=statistics.mean(map(len, tokens)),
        most_repeated_sentences=[dict(sentence=s, occurrences=n) for s, n in sentence_counts.most_common(5)])


def prepare(out, *, pool_size=100, judge_count=20, seed=777):
    if not 2 <= judge_count <= pool_size or judge_count > 100:
        raise ValueError("Require 2 <= judge_count <= pool_size and judge_count <= 100")
    out.mkdir(parents=True, exist_ok=False)
    metrics = {}
    for scenario in SCENARIOS:
        directory = out / scenario
        directory.mkdir()
        rows = sample_pool(scenario, pool_size, seed)
        item = quality.select_set(scenario, rows, seed, count=judge_count)
        body = protocol.request_body(quality, item)
        body.update(model=MODEL, store=False)
        save(directory / "pool.json", rows)
        save(directory / "input.json", item)
        save(directory / "request.json", body)
        metrics[scenario] = diversity_metrics(rows)
        (directory / "stories.md").write_text("# Random judge sample\n\n" + "\n\n".join(
            f"## {s['id']} — seed {rows[s['source_index']]['seed']}\n\n{s['story']}"
            for s in item["stories"]) + "\n")
    save(out / "mechanical.json", metrics)
    sources = list((ROOT / "grammarworlds").glob("*.py")) + [
        Path(module.__file__) for module in (quality, protocol, quality.legacy,
                                             quality.trial_cost, quality.api_requests)]
    for source in sources:
        target = out / "_source" / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    manifest = {str(path.relative_to(out)): digest(path) for path in sorted(out.rglob("*")) if path.is_file()}
    save(out / "settings.json", dict(model=MODEL, service_tier="flex", reasoning_effort="none",
        protocol=quality.PROTOCOL, output_format="harbor_story_set_v2", pool_per_scenario=pool_size,
        judge_per_scenario=judge_count, seed=seed, scenarios=list(SCENARIOS),
        selection="uniform positions without replacement; duplicates retained; same seed schedule per scenario",
        generation=dict(tense="past", attention=True, temperature=1),
        max_retries=0, timeout_seconds=900, manifest=manifest,
        notes=["Judge sees prose only, with the existing calibration and unchanged rubric.",
               "Quality averages pool the judged stories. Diversity is assessed within each scenario.",
               "Event-kind paths include optional beats; they are not counts of distinct causal plots.",
               "No comparative baseline, independent judge repeat, or population diversity claim."]))
    report(out)


def verify_artifacts(out):
    settings = read(out / "settings.json")
    for name, expected in settings["manifest"].items():
        if digest(out / name) != expected:
            raise ValueError(f"Prepared artifact changed: {name}")
    # Validate with the same evaluator that prepared the request.
    for module in (quality, protocol, quality.legacy, quality.api_requests):
        source = Path(module.__file__)
        if digest(source) != digest(out / "_source" / source.relative_to(ROOT)):
            raise ValueError(f"Shared judge source changed: {source.name}")
    return settings


def assess(response, item):
    served = response.get("model", "")
    if served != MODEL and not served.startswith(MODEL + "-"):
        raise ValueError("Returned model is not the requested Luna judge")
    if response.get("service_tier") != "flex" or response.get("status") != "completed":
        raise ValueError("Judge did not return a completed Flex response")
    return protocol.validate(quality, json.loads(quality.final_text(response)), item)


def retry_unavailable(directory):
    """Archive a definite Flex rejection; never retry an uncertain outcome."""
    previous = read(directory / "result.json")
    # The string fallback supports the initial adapter's saved rejection format.
    unavailable = (previous.get("http_status") == 429 and previous.get("error_code") == "flex_unavailable")
    legacy_error = previous.get("error", "")
    unavailable |= (legacy_error.startswith("RateLimitError: Error code: 429 - ")
                    and "'code': 'flex_unavailable'" in legacy_error)
    if previous.get("ok") or (directory / "response.json").exists() or not unavailable:
        raise ValueError("Only an explicit 429 flex_unavailable rejection can be retried")
    attempts = directory / "rejected_attempts"
    attempts.mkdir(exist_ok=True)
    archive = attempts / str(len(list(attempts.iterdir())) + 1)
    archive.mkdir()
    for name in ("dispatch.json", "result.json"):
        (directory / name).rename(archive / name)


async def run(out, key_file=None, *, retry_flex_unavailable=False):
    settings = verify_artifacts(out)
    from openai import AsyncOpenAI
    key = os.environ.get("OPENAI_API_KEY")
    if key_file is not None:
        key = key_file.read_text().strip()
    elif not key and (ROOT / ".API_KEY").is_file():
        key = (ROOT / ".API_KEY").read_text().strip()
    # The dispatch marker is exclusive: interrupted/uncertain calls never retry.
    async with AsyncOpenAI(api_key=key, base_url="https://api.openai.com/v1",
                           timeout=900, max_retries=0) as client:
        async def one(scenario):
            directory = out / scenario
            response_path = directory / "response.json"
            item, body = read(directory / "input.json"), read(directory / "request.json")
            result = dict(scenario=scenario, ok=False)
            started = time.monotonic()
            try:
                if not response_path.exists():
                    if retry_flex_unavailable and (directory / "dispatch.json").exists():
                        retry_unavailable(directory)
                    request_id = str(uuid.uuid4())
                    with (directory / "dispatch.json").open("x") as handle:
                        json.dump(dict(started_at=time.time(), idempotency_key=request_id,
                                       request_sha256=digest(directory / "request.json"),
                                       runner_sha256=digest(Path(__file__))), handle)
                    shutil.copyfile(__file__, directory / "dispatch_runner.py")
                    response = await asyncio.wait_for(client.responses.create(
                        **quality.api_requests.sdk_kwargs(body),
                        extra_headers={"Idempotency-Key": request_id}), timeout=900)
                    save(response_path, response.model_dump(mode="json"))
                response = read(response_path)
                result.update(assessment=assess(response, item), ok=True)
            except Exception as exc:
                result["error"] = ("Already dispatched without a saved response; no automatic retry"
                                   if isinstance(exc, FileExistsError) else f"{type(exc).__name__}: {exc}")
                if key:
                    result["error"] = result["error"].replace(key, "[redacted]")
                result["http_status"] = getattr(exc, "status_code", None)
                result["error_code"] = getattr(exc, "code", None)
            if response_path.exists():
                response = read(response_path)
                result["response"] = {k: response.get(k) for k in ("id", "model", "service_tier", "status", "usage")}
            result["elapsed_seconds"] = round(time.monotonic() - started, 3)
            save(directory / "result.json", result)
            print(f"{scenario}: {'OK' if result['ok'] else result['error']}", flush=True)
        await asyncio.gather(*(one(scenario) for scenario in settings["scenarios"]))
    return report(out)


def report(out):
    settings = verify_artifacts(out)
    results = [read(out / name / "result.json") for name in settings["scenarios"]
               if (out / name / "result.json").exists()]
    good = [r for r in results if r["ok"]]
    ratings = [s for r in good for s in r["assessment"]["story_ratings"]]
    metrics = read(out / "mechanical.json")
    summary = dict(model=settings["model"], complete=len(good) == len(settings["scenarios"]),
        sampled=sum(m["samples"] for m in metrics.values()), judged=len(ratings),
        mean_quality={k: statistics.mean(s["rating"][k] for s in ratings) if ratings else None
                      for k in quality.legacy.RATING_KEYS},
        mean_within_scenario_diversity={k: statistics.mean(r["assessment"]["diversity"][k] for r in good)
                                      if good else None for k in quality.DIVERSITY_KEYS},
        stories_below_six=sum(s["rating"]["overall"] < 6 for s in ratings),
        usage={k: sum((r.get("response", {}).get("usage") or {}).get(k, 0) for r in results)
               for k in ("input_tokens", "output_tokens", "total_tokens")}, results=results)
    save(out / "summary.json", summary)
    lines = ["# Grammarworlds: Luna quality and diversity", "",
        f"Judge: {settings['model']}; Flex; reasoning none; existing calibrated 0–9 rubric.",
        f"{summary['sampled']} generated stories; {summary['judged']} judged. Complete: {summary['complete']}.",
        "Random positions, no deduplication or quality filtering. Generation is classical and unchanged.", "",
        "| Scenario | Quality / 9 | Diversity / 9 | Plot groups | Exact unique texts | Event-kind paths |",
        "| --- | ---: | ---: | ---: | ---: | ---: |"]
    by_scenario = {r["scenario"]: r for r in good}
    for name, metric in metrics.items():
        result = by_scenario.get(name)
        a = result["assessment"] if result else None
        scores = (f"{a['rating']['overall']:.2f} | {a['diversity']['overall']} | {len(a['plot_groups'])}"
                  if a else "pending/failed | — | —")
        lines.append(f"| {name} | {scores} | {metric['exact_unique_texts']}/{metric['samples']} | {metric['unique_event_kind_paths']} |")
    lines += ["", "## Quality dimensions", "", "| Dimension | Mean / 9 |", "| --- | ---: |"]
    for key, value in summary["mean_quality"].items():
        lines.append(f"| {key} | {value:.2f} |" if value is not None else f"| {key} | pending |")
    lines += ["", "## Diversity dimensions (mean within scenario)", "", "| Dimension | Mean / 9 |", "| --- | ---: |"]
    for key, value in summary["mean_within_scenario_diversity"].items():
        lines.append(f"| {key} | {value:.2f} |" if value is not None else f"| {key} | pending |")
    for result in results:
        name = result["scenario"]
        lines += ["", f"## {name}", ""]
        if not result["ok"]:
            lines.append(result["error"])
            continue
        a = result["assessment"]
        lines += [a["diversity_evidence"], "", "Causal plot groups:", ""]
        for group in a["plot_groups"]:
            lines.append(f"- {len(group['story_ids'])} stories: {group['summary']}")
        lines += ["", "Lowest-rated samples (ties retain judge order):", ""]
        for story in sorted(a["story_ratings"], key=lambda s: s["rating"]["overall"])[:3]:
            lines.append(f"- {story['id']} ({story['rating']['overall']}/9): {story['note']}")
    lines += ["", "## Scope", "",
        f"Each diversity score describes {settings['judge_per_scenario']} sampled positions per scenario, not the full generator. "
        "These three authored recovery situations share much of their machinery. No cross-scenario semantic diversity score is claimed. "
        "Exact unique strings and different event-kind sequences do not establish different plots; optional goal/thanks beats can inflate path counts. "
        "Trigram overlap and repeated sentences are available in mechanical.json; they measure surface reuse, not quality. "
        "One Luna judgment per set is a diagnostic baseline, not an independently calibrated human evaluation or confidence interval. "
        "Requests, untouched samples, responses, token usage, and source snapshots are saved for audit. No price estimate is claimed.", ""]
    (out / "report.md").write_text("\n".join(lines))
    return summary


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "run", "report"))
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--pool-size", type=int, default=100)
    parser.add_argument("--judge-count", type=int, default=20)
    parser.add_argument("--seed", type=int, default=777)
    parser.add_argument("--api-key-file", type=Path)
    parser.add_argument("--retry-unavailable", action="store_true",
                        help="Retry only saved, explicit Flex-capacity rejections; preserve prior attempts")
    args = parser.parse_args()
    if args.phase == "prepare":
        prepare(args.out, pool_size=args.pool_size, judge_count=args.judge_count, seed=args.seed)
    elif args.phase == "run":
        summary = asyncio.run(run(args.out, args.api_key_file, retry_flex_unavailable=args.retry_unavailable))
        if not summary["complete"]:
            raise SystemExit("Some judge calls failed; see saved results. No automatic retries.")
    else:
        report(args.out)
    print(args.out / "report.md")


if __name__ == "__main__":
    main()
