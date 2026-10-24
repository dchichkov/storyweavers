#!/usr/bin/env python3
"""Paired judges on a frozen capability trial. Prepare offline; run explicitly."""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
from copy import deepcopy
import json
from pathlib import Path
import shutil
import statistics
import time

import capability_trial as trial

f, cq = trial.f, trial.cq
MODELS = ("gpt-5.6-terra", "gpt-6-luna")
PROTOCOL = "capability_judge_comparison_v1"
PRICING_URL = "https://developers.openai.com/api/docs/pricing"


def response_cost(response):
    model, usage = response.get("model", ""), response.get("usage") or {}
    tier = response.get("service_tier", "unknown")
    if model != "gpt-6-luna" and not model.startswith("gpt-6-luna-"):
        return f.trial_cost.token_cost(model, usage, tier)
    # Reuse usage validation without modifying the frozen historical price table.
    cost = f.trial_cost.token_cost("gpt-5.6-terra", usage, tier)
    if not cost["known"]:
        return cost
    inputs, outputs, cached = cost["input_tokens"], cost["output_tokens"], cost["cached_input_tokens"]
    writes = cost["cache_write_tokens"] or 0
    factor = 1 if tier == "flex" else 2
    base = factor * ((inputs - cached - writes) * .05 + cached * .005 + writes * .0625 + outputs * .25) / 1e6
    premium = factor * (inputs - cached) * .0125 / 1e6 if cost["cache_write_tokens"] is None else 0
    return dict(cost, usd_low=base, usd_high=base + premium)


class Budget(f.Budget):
    """Reserve BOTH arms at the higher Terra ceiling; settle at actual rates."""
    def reserve(self, label, request):
        if request["model"] not in MODELS:
            raise ValueError("Unapproved judge model")
        return super().reserve(request["model"] + "/" + label, dict(request, model=MODELS[0]))

    def settle(self, index, response):
        cost = response_cost(response)
        self.entries[index].update(status="returned", response_id=response.get("id"), cost=cost)
        if cost["known"]:
            self.entries[index]["reserved_usd"] = cost["usd_high"]
        self.persist()


def cost_summary(results):
    costs = [response_cost(r.get("response") or {}) for r in results]
    known = [c for c in costs if c["known"]]
    return dict(requests=len(results), priced_requests=len(known), unpriced_requests=len(costs) - len(known),
                usd_low=sum(c["usd_low"] for c in known), usd_high=sum(c["usd_high"] for c in known),
                input_tokens=sum(c["input_tokens"] for c in known), output_tokens=sum(c["output_tokens"] for c in known))


def paired_jobs(rows):
    originals, selected = trial.jobs_for(rows)
    jobs = []
    for original in originals:
        for model in MODELS:
            job = deepcopy(original)
            job["body"].update(model=model, store=False)
            job["model"] = model
            jobs.append(job)
    return jobs, selected


def prepare(baseline, out, limit):
    if not 0 < limit <= 5:
        raise ValueError("Combined authorized cap must be positive and at most $5")
    trial.assert_sources(baseline)
    # This comparison owns the single paid campaign; do not start a second ledger
    # after a standalone baseline judge has already reserved or spent money.
    old_budget = baseline / "budget.json"
    if old_budget.exists() and json.loads(old_budget.read_text())["entries"]:
        raise ValueError("Standalone baseline already has paid reservations; reconcile before comparing")
    rows = trial.read_rows(baseline / "attempts.jsonl")
    requested = json.loads((baseline / "settings.json").read_text())["requested_per_world"]
    if not trial.mechanical_summary(rows, requested)["complete"]:
        raise ValueError("Incomplete local sampling")
    jobs, selected = paired_jobs(rows)
    if selected != json.loads((baseline / "judge_samples.json").read_text()):
        raise ValueError("Frozen judge selection changed")
    settings = dict(protocol=PROTOCOL, baseline=str(baseline.resolve()), models=list(MODELS),
        budget_usd=limit, service_tier="flex", reasoning_effort="none", store=False,
        requests=len(jobs), selected_stories=len(selected),
        conversations=sum(len(r["conversations"]) for r in selected),
        source_sha256=f.digest(Path(__file__)), attempts_sha256=f.digest(baseline / "attempts.jsonl"),
        selection_sha256=trial.fingerprint(selected),
        manifest=[dict(model=j["model"], phase=j["phase"], stage=j["stage"],
            request_sha256=trial.fingerprint(j["body"])) for j in jobs],
        pricing=dict(checked="2026-10-22", url=PRICING_URL,
            luna_flex_input_cached_write_output=[.05, .005, .0625, .25],
            terra_flex_input_cached_write_output=list(f.trial_cost.FLEX_RATES[MODELS[0]])))
    freeze(out, jobs, selected, settings)
    return jobs, settings


def freeze(out, jobs, selected, settings):
    if out.exists():
        if json.loads((out / "settings.json").read_text()) != settings:
            raise ValueError("Frozen comparison settings, requests or sources changed")
    else:
        out.mkdir(parents=True)
        f.save(out / "settings.json", settings)
        shutil.copyfile(__file__, out / Path(__file__).name)
        f.save(out / "judge_samples.json", selected)
        for job in jobs:
            directory = out / job["model"] / job["phase"]
            directory.mkdir(parents=True, exist_ok=True)
            f.save(directory / f"{job['stage']}.planned.json", job["body"])


def prepare_review(review, out, limit, previous):
    """Judge saved revised plots, without reusing historical grades or sampling."""
    if not 0 < limit <= 5:
        raise ValueError("Combined authorized cap must be positive and at most $5")
    ledger = json.loads((previous / "budget.json").read_text())
    committed = sum(e["reserved_usd"] for e in ledger["entries"])
    if any(e["status"] != "returned" or not e.get("cost", {}).get("known") for e in ledger["entries"]):
        raise ValueError("Reconcile previous unknown reservations before another campaign")
    if committed + limit > 5:
        raise ValueError("Previous spend plus new cap exceeds the shared $5 authorization")
    trial.assert_sources(review)
    hashes = json.loads((review / "source_hashes.json").read_text())
    for name, digest in hashes.items():
        if f.digest(review / "_source" / name) != digest:
            raise ValueError(f"Frozen review source changed: {name}")
    settings = json.loads((review / "settings.json").read_text())
    original = Path(settings["baseline"]) / "judge_samples.json"
    if f.digest(original) != settings["selection_sha256"]:
        raise ValueError("Historical seed selection changed")
    old = json.loads(original.read_text())
    rows = trial.read_rows(review / "fresh_seeds.jsonl")
    expected = {r["sample_id"] for r in old}
    if len(rows) != len(expected) or {r["sample_id"] for r in rows} != expected or not all(r["ok"] for r in rows):
        raise ValueError("Review must contain every matched successful seed exactly once")
    from storyscenes.capabilities.codec import loads
    specs = {world: loads(trial.registry(), (review / "worlds" / f"{world}.json").read_text())
             for world in {r["world"] for r in rows}}
    for row in rows:
        state = trial.replay(trial.registry(), specs[row["world"]], row["path"])
        document = trial.render_story(specs[row["world"]], state)
        if (row["sample_id"] != f"{row['world']}:{row['seed']}"
                or row["trace_sha256"] != trial.fingerprint(state)
                or row["story"] != document.story
                or row["story_sha256"] != trial.fingerprint(document.story)
                or row["conversations"] != trial.conversations(document, row["seed"])
                or row["qa"] != trial.plain(trial.Reader(document).questions())):
            raise ValueError(f"Saved review does not reproduce: {row['sample_id']}")
    # Hidden state stays in the local review, not the judge inputs or selections.
    rows = [{k: r[k] for k in ("world", "seed", "sample_id", "ok", "story", "conversations")} for r in rows]
    jobs, selected = paired_jobs(rows)
    unique = {world: len({r["story"] for r in rows if r["world"] == world}) for world in specs}
    followups = sum(max(0, len(c["turns"]) - 1) for r in selected for c in r["conversations"])
    settings = dict(protocol=PROTOCOL, source_kind="prose_review", review=str(review.resolve()),
        previous_comparison=str(previous.resolve()), previous_committed_usd=committed,
        previous_budget_sha256=f.digest(previous / "budget.json"), combined_authorized_usd=5,
        models=list(MODELS), budget_usd=limit, service_tier="flex", reasoning_effort="none", store=False,
        requests=len(jobs), selected_stories=len(selected), unique_stories_by_world=unique,
        conversations=sum(len(r["conversations"]) for r in selected), followups=followups,
        source_sha256=f.digest(Path(__file__)), attempts_sha256=f.digest(review / "fresh_seeds.jsonl"),
        review_source_hashes_sha256=f.digest(review / "source_hashes.json"),
        worlds_sha256={w: f.digest(review / "worlds" / f"{w}.json") for w in specs},
        selection_sha256=trial.fingerprint(selected),
        manifest=[dict(model=j["model"], phase=j["phase"], stage=j["stage"],
            request_sha256=trial.fingerprint(j["body"])) for j in jobs],
        scope_notes=[
            f"Revised plots: {len(selected)} matched seed positions, {sum(unique.values())} distinct visible stories; duplicates retained.",
            f"QA: {sum(len(r['conversations']) for r in selected)} conversations, {followups} follow-up turns.",
            "These are fixed authored profiles, not independent stories or a diverse dataset.",
            "Both prose and executable plots changed; historical deltas do not isolate a renderer effect.",
            "The fourth conformance demo was not part of this prose review. No population yield or geometric score is claimed."],
        pricing=dict(checked="2026-10-22", url=PRICING_URL,
            luna_flex_input_cached_write_output=[.05, .005, .0625, .25],
            terra_flex_input_cached_write_output=list(f.trial_cost.FLEX_RATES[MODELS[0]])))
    freeze(out, jobs, selected, settings)
    return jobs, settings


async def evaluate(jobs, out, limit, key, concurrency, *, budget=None, story_validator=None):
    from openai import AsyncOpenAI
    budget = budget if budget is not None else Budget(out / "budget.json", limit)
    f.load_key(key)
    semaphore = asyncio.Semaphore(concurrency)
    async with AsyncOpenAI(base_url="https://api.openai.com/v1", timeout=900.0, max_retries=0) as client:
        async def one(job):
            async with semaphore:
                directory = out / job["model"] / job["phase"]
                result_path = directory / f"{job['stage']}.result.json"
                if result_path.exists():
                    return json.loads(result_path.read_text())
                result = {k: job[k] for k in ("model", "phase", "stage")}
                result["ok"] = False
                started = time.monotonic()
                response_path = directory / f"{job['stage']}.response.json"
                result["reused_response"] = response_path.exists()
                f.save(directory / f"{job['stage']}.input.json", job["input"])
                try:
                    output = await asyncio.wait_for(
                        f.api_artifact(client, budget, directory, job["stage"], job["body"]), timeout=900)
                    response = json.loads(response_path.read_text())
                    served = response.get("model", "")
                    if response.get("service_tier") != "flex" or not (
                            served == job["model"] or served.startswith(job["model"] + "-")):
                        raise ValueError("Unexpected returned model/tier; no fallback authorized")
                    validator = (story_validator or f.quality.validate) if job["phase"] == "story_quality" else cq.validate
                    result.update(ok=True, assessment=validator(json.loads(output), job["input"]))
                except Exception as exc:
                    result["error"] = ("Hard 900-second request deadline; outcome unknown, reservation retained"
                                       if isinstance(exc, TimeoutError) else str(exc))
                if response_path.exists():
                    response = json.loads(response_path.read_text())
                    result["response"] = {k: response.get(k) for k in ("id", "model", "status", "service_tier", "usage")}
                result["elapsed_seconds"] = round(time.monotonic() - started, 3)
                f.save(result_path, result)
                print(f"{job['model']} {job['phase']}/{job['stage']}: {result['ok']}", flush=True)
                return result
        results = await asyncio.gather(*(one(j) for j in jobs))
    return summarize(results, out, budget)


def paired_scores(left, right):
    ids = sorted(left.keys() & right.keys())
    deltas = [right[k]["rating"]["overall"] - left[k]["rating"]["overall"] for k in ids]
    comparisons = [dict(id=k, terra=left[k], luna=right[k]) for k in ids]
    disagreements = sorted(comparisons, key=lambda r: abs(r["luna"]["rating"]["overall"] - r["terra"]["rating"]["overall"]), reverse=True)
    return dict(paired=len(ids), terra_only=len(left.keys() - right.keys()), luna_only=len(right.keys() - left.keys()),
        mean_delta=statistics.mean(deltas) if deltas else None,
        mean_absolute_difference=statistics.mean(abs(d) for d in deltas) if deltas else None,
        within_one_fraction=sum(abs(d) <= 1 for d in deltas) / len(ids) if ids else None,
        usability_counts=dict(Counter(f"terra={left[k]['usable']},luna={right[k]['usable']}" for k in ids if "usable" in left[k])),
        largest_disagreements=disagreements[:10])


def summarize(results, out, budget):
    settings = json.loads((out / "settings.json").read_text())
    arms, story_maps, qa_maps = {}, {}, {}
    for model in MODELS:
        arm = [r for r in results if r["model"] == model]
        story = [dict(r, **r.get("assessment", {})) for r in arm if r["phase"] == "story_quality"]
        qa = [r for r in arm if r["phase"] == "qa_quality"]
        quality = f.quality.summarize(story)
        quality.update(model=model, cost=cost_summary(story))
        arms[model] = dict(story=quality, qa=cq.summarize(qa), cost=cost_summary(arm),
            failures=[dict(phase=r["phase"], stage=r["stage"], error=r.get("error")) for r in arm if not r["ok"]],
            returned_tiers=dict(Counter(r["response"]["service_tier"] for r in arm if r.get("response"))))
        story_maps[model] = {r["stage"] + "/" + s["id"]: s for r in story if r["ok"] for s in r["story_ratings"]}
        qa_maps[model] = {s["id"] + "/" + c["id"]: c for r in qa if r["ok"]
                          for s in r["assessment"]["stories"] for c in s["conversations"]}
    report = dict(protocol=PROTOCOL, arms=arms, cost=cost_summary(results),
        story_agreement=paired_scores(*(story_maps[m] for m in MODELS)),
        qa_agreement=paired_scores(*(qa_maps[m] for m in MODELS)),
        committed_upper_usd=sum(e["reserved_usd"] for e in budget.entries), budget_usd=budget.limit,
        unresolved_reservations=sum(e["status"] != "returned" or not e.get("cost", {}).get("known") for e in budget.entries))
    f.save(out / "comparison.json", report)
    def number(v):
        return "unrated" if v is None else f"{v:.3f}"
    lines = ["# Terra versus Luna: matched capability-story judging", "",
        "Same selected stories, order, rubric, schema, token limits and reasoning=none; both Flex with store=false.",
        "The requested Luna 6.1 ID was not listed; this comparison uses the explicitly confirmed gpt-6-luna.", "",
        "| Judge | Stories graded | Story overall / 9 | Set diversity / 9 | QA overall / 9 | QA usable | Estimated USD |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for model, arm in arms.items():
        s, q, c = arm["story"], arm["qa"], arm["cost"]
        lines.append(f"| {model} | {s['rated_stories']} | {number(s['mean_quality']['overall'])} | "
            f"{number(s['mean_diversity']['overall'])} | {number(q['mean_quality']['overall'])} | "
            f"{q['usable']} / {q['rated_conversations']} | ${c['usd_low']:.5f}-${c['usd_high']:.5f} |")
    lines += ["", "## Paired agreement", "", "Deltas are Luna minus Terra; Terra is a comparator, not ground truth.", ""]
    for name in ("story", "qa"):
        p = report[name + "_agreement"]
        lines.append(f"- {name}: {p['paired']} paired items; mean delta {number(p['mean_delta'])}; "
                     f"mean absolute difference {number(p['mean_absolute_difference'])}; "
                     f"within one point {number(p['within_one_fraction'])}.")
    scope_notes = settings.get("scope_notes", ["This is a small three-world comparison, conditional on successful bounded generation.",
        "The fourth demo had only one returned story and is not set-graded. Duplicate sample positions remain.",
        "QA has 180 conversations but only 13 follow-ups; it is not a general multi-turn judge benchmark.",
        "All four worlds fail the baseline's all-seeds mechanical gate, so the strict geometric index is zero",
        "regardless of judge. Do not use it to compare these judges."])
    lines += ["", "## Scope and cost", "", *scope_notes, "",
        f"Combined returned-usage estimate ${report['cost']['usd_low']:.5f}-${report['cost']['usd_high']:.5f}; "
        f"${report['committed_upper_usd']:.5f} committed including unknown reservations, within ${budget.limit:.2f}.",
        "Both arms reserve at conservative Terra rates before dispatch. Actual Luna costs use its own rates.",
        f"Rates: [official pricing]({PRICING_URL}), checked 2026-10-22; estimates are not invoice reconciliation.",
        "No automatic paid retries or fallback tiers. Failed/unknown requests remain saved.", "",
        "Full grades, costs, paired disagreements and usability decisions: `comparison.json`.", ""]
    if "previous_committed_usd" in settings:
        lines += [f"Including the previous campaign: ${settings['previous_committed_usd'] + report['committed_upper_usd']:.5f} "
                  f"committed against the shared ${settings['combined_authorized_usd']:.2f} authorization.", ""]
    (out / "REPORT.md").write_text("\n".join(lines))
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "evaluate"))
    source = parser.add_mutually_exclusive_group(required=True)
    source.add_argument("--baseline", type=Path)
    source.add_argument("--review", type=Path, help="Saved matched fresh_seeds.jsonl from the local prose review")
    parser.add_argument("--previous-comparison", type=Path, help="Previous paid ledger under the shared $5 cap; required for --review")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--budget", type=float, default=5)
    parser.add_argument("--api-key-file", type=Path)
    parser.add_argument("--concurrency", type=int, default=4)
    args = parser.parse_args()
    if args.concurrency < 1:
        parser.error("Positive concurrency required")
    if args.review and not args.previous_comparison:
        parser.error("--review requires --previous-comparison for shared budget accounting")
    jobs, settings = (prepare_review(args.review, args.out, args.budget, args.previous_comparison)
                      if args.review else prepare(args.baseline, args.out, args.budget))
    if args.phase == "evaluate":
        report = asyncio.run(evaluate(jobs, args.out, args.budget, args.api_key_file, args.concurrency))
        print(json.dumps({k: report[k] for k in ("cost", "committed_upper_usd", "unresolved_reservations")}, indent=2))
    else:
        print(json.dumps({k: settings[k] for k in ("models", "requests", "selected_stories", "conversations", "budget_usd")}, indent=2))


if __name__ == "__main__":
    main()
