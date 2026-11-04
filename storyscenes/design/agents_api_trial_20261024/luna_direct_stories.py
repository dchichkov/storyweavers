"""Matched direct-prose baseline; immutable requests, no paid retries or repairs."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import json
from pathlib import Path
import shutil
import statistics
import time
import uuid

import judge_stories as judge
from luna_xhigh_batch_report import flex_cost_range

api, quality, protocol = judge.api, judge.quality, judge.protocol
HERE, ROOT = judge.HERE, judge.ROOT
OUT = HERE / "luna_high_direct_20"
MANIFEST = HERE / "luna_xhigh_128k_20_manifest.json"


def read(path):
    return json.loads(path.read_text())


def request(entry):
    prompt = (
        "Write one complete children's story of about 800 words (aim for 750-850). "
        "Write the story directly, not code, an outline, a simulation, or scene instructions. "
        "Give the characters specific wants, natural dialogue, a complication, a consequential "
        "choice, and an earned ending shown through a concrete final image. Keep physical "
        "actions, motives, object ownership, and the sequence of events coherent. "
        "Let the story show what changes rather than ending with an explanation of its moral. "
        "Use the seed words naturally. Return only the story, without a title or commentary.\n\n"
        f"Task seed (an identifying label): {entry['task_seed']}\n"
        f"Seed words: {', '.join(entry['words'])}\n"
        f"Setting: {entry['setting']}\nPremise: {entry['premise']}\n"
    )
    return dict(model="gpt-6-luna", reasoning=dict(effort="high"), service_tier="flex",
                max_output_tokens=32000, store=False, input=prompt)


def prepare():
    OUT.mkdir(exist_ok=False)
    original = read(MANIFEST)
    entries = original["entries"]
    assert len(entries) == 20 and len({e["task_seed"] for e in entries}) == 20
    sources = [Path(__file__), Path(api.__file__), Path(judge.__file__),
               Path(protocol.__file__), Path(quality.__file__), Path(quality.legacy.__file__),
               Path(quality.trial_cost.__file__), Path(quality.api_requests.__file__)]
    hashes = {}
    for source in sources:
        name = str(source.relative_to(ROOT))
        target = OUT / "_source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        hashes[name] = api.digest(source.read_bytes())
    for entry in entries:
        arm = OUT / f"{entry['index'] + 1:02d}_{entry['arm'].split('_')[-1]}"
        body = request(entry)
        api.save(arm / "request.json", body)
        api.save(arm / "settings.json", dict(entry=entry, idempotency_key=str(uuid.uuid4()),
            request_sha256=api.digest((arm / "request.json").read_bytes())))
    api.save(OUT / "manifest.json", dict(entries=entries, source_hashes=hashes,
        original_manifest_sha256=api.digest(MANIFEST.read_bytes()), concurrency=20,
        generation_reservation_each_usd=.03, judge="gpt-5.6-terra", judge_tier="flex",
        note="Same task seeds/words/settings/premises, not an API sampling seed. All first draws retained. "
             "One story per scenario; diversity is cross-scenario, not within-pack."))
    print("Prepared 20 direct-prose requests; no API calls.", flush=True)


def verify():
    manifest = read(OUT / "manifest.json")
    for name, digest in manifest["source_hashes"].items():
        if api.digest((ROOT / name).read_bytes()) != digest:
            raise ValueError(f"Changed source: {name}")
    if api.digest(MANIFEST.read_bytes()) != manifest["original_manifest_sha256"]:
        raise ValueError("Changed seed manifest")
    return manifest


def generate_one(arm, key):
    if (arm / "dispatch.json").exists():
        raise ValueError(f"Already dispatched: {arm.name}; no automatic retries")
    settings = read(arm / "settings.json")
    if api.digest((arm / "request.json").read_bytes()) != settings["request_sha256"]:
        raise ValueError("Changed prepared request")
    body = read(arm / "request.json")
    ledger = api.Ledger(HERE)
    reservation = ledger.reserve("direct_" + arm.name, .03)
    started = time.time()
    api.save(arm / "dispatch.json", dict(started_at=started, reservation_index=reservation,
        idempotency_key=settings["idempotency_key"]))
    client = api.API(key)
    outcome = dict(arm=arm.name, ok=False)
    try:
        response = client.request("POST", "responses", json=body, timeout=1800,
            headers={"Idempotency-Key": settings["idempotency_key"]}).json()
        api.save(arm / "response.json", response)
        served = response.get("model", "")
        if response.get("service_tier") != "flex" or not (
                served == body["model"] or served.startswith(body["model"] + "-")):
            raise ValueError("Unexpected served model/tier; reservation retained")
        cost = api.usage_cost(body["model"], response.get("usage"))
        ledger.settle(reservation, cost, usage=response.get("usage"))
        text = quality.final_text(response).strip()
        (arm / "story.txt").write_text(text + "\n", encoding="utf-8")
        if response.get("status") != "completed" or not text:
            raise ValueError("Incomplete or empty story")
        outcome.update(ok=True, story=text, words=len(text.split()),
            entry=settings["entry"], usage=response["usage"], conservative_cost_usd=cost,
            flex_cost_range_usd=flex_cost_range(response["usage"]))
    except Exception as exc:
        outcome["error"] = f"{type(exc).__name__}: {exc}"
        api.save(arm / "error.json", dict(error=outcome["error"]))
    finally:
        client.client.close()
    outcome["elapsed_seconds"] = time.time() - started
    api.save(arm / "outcome.json", outcome)
    print(json.dumps({k: v for k, v in outcome.items() if k in
          ("arm", "ok", "words", "error", "elapsed_seconds")}), flush=True)
    return outcome


def generate(key):
    verify()
    arms = sorted(p.parent for p in OUT.glob("*/settings.json"))
    if any((p / "dispatch.json").exists() for p in arms):
        raise ValueError("Batch already dispatched; inspect saved outcomes instead of repeating it")
    ledger = api.Ledger(HERE)
    if sum(e["reserved_usd"] for e in ledger.data["entries"]) + .6 + .5 > ledger.data["authorized_usd"]:
        raise ValueError("Insufficient campaign headroom for generation plus judging")
    with ThreadPoolExecutor(max_workers=20) as pool:
        results = [f.result() for f in as_completed([pool.submit(generate_one, p, key) for p in arms])]
    results.sort(key=lambda r: r["arm"])
    api.save(OUT / "outcomes.json", results)
    good = [r for r in results if r["ok"]]
    api.save(OUT / "stories.json", good)
    (OUT / "STORIES.md").write_text("# Luna High: Direct Stories\n\n" + "\n\n".join(
        f"## {r['arm']} | Seed {r['entry']['task_seed']} | {r['words']} words\n\n{r['story']}"
        for r in good) + "\n", encoding="utf-8")


def prepare_judge():
    manifest = verify()
    rows = read(OUT / "stories.json")
    if len(rows) < 2:
        raise ValueError("Need at least two completed stories")
    out = OUT / "quality"
    out.mkdir(exist_ok=False)
    item = quality.select_set("luna_high_direct_matched_scenarios", rows, 777, count=len(rows))
    body = protocol.request_body(quality, item)
    old = "Evaluate a random sample of stories from ONE procedural StoryWorld."
    assert body["input"][0]["content"].startswith(old)
    body["input"][0]["content"] = body["input"][0]["content"].replace(old,
        "Evaluate directly written stories across different everyday children's-story scenarios. "
        "This is a cross-scenario set, not variations from one procedural world.", 1)
    body["store"] = False
    api.save(out / "input.json", item)
    api.save(out / "request.json", body)
    api.save(out / "settings.json", dict(model=quality.DEFAULT_MODEL,
        source_hashes=manifest["source_hashes"], service_tier="flex", reasoning="none",
        source_sha256=api.digest((OUT / "stories.json").read_bytes()),
        input_sha256=api.digest((out / "input.json").read_bytes()),
        request_sha256=api.digest((out / "request.json").read_bytes()),
        idempotency_key=str(uuid.uuid4()), requested_stories=20, completed_stories=len(rows),
        pricing_note="Same conservative Terra allowance as existing standard judge; not invoice.",
        rubric_change="Only opening scope sentence changed from one procedural world to cross-scenario direct prose; scores/calibration unchanged."))


def report():
    rows = read(OUT / "stories.json")
    result = read(OUT / "quality/result.json")
    ratings = {int(r["id"][1:]): r for r in result["story_ratings"]}
    ranges = [r["flex_cost_range_usd"] for r in rows if r["flex_cost_range_usd"]]
    summary = dict(requested=20, completed=len(rows), judged=result["judged_stories"],
        quality=result["rating"], diversity_cross_scenario=result["diversity"],
        words=dict(mean=statistics.mean(r["words"] for r in rows),
                   minimum=min(r["words"] for r in rows), maximum=max(r["words"] for r in rows)),
        generation_flex_cost_range_usd=[sum(r[i] for r in ranges) for i in (0, 1)],
        costed_generations=len(ranges), judge_conservative_cost_usd=result["budget_estimate_usd"],
        output_tokens=sum(r["usage"]["output_tokens"] for r in rows),
        reasoning_tokens=sum(r["usage"]["output_tokens_details"]["reasoning_tokens"] for r in rows))
    api.save(OUT / "summary.json", summary)
    lines = ["# Direct Prose Baseline", "", "gpt-6-luna, high, Flex; matched 20 task seeds; target 800 words.",
        "Standard gpt-5.6-terra/Flex/none judge, unchanged calibration and scoring rubric.",
        "Only the rubric's opening scope sentence identifies this as a cross-scenario set.", "",
        f"Completed {len(rows)}/20; judged {result['judged_stories']}. All completed first attempts included.",
        f"Quality: {result['rating']}. Cross-scenario diversity: {result['diversity']}.", "",
        "| Scenario | Words | Overall /9 | Storytelling /9 | Judge note |",
        "| --- | ---: | ---: | ---: | --- |"]
    for index, row in enumerate(rows):
        rating = ratings[index]
        lines.append(f"| {row['arm']} | {row['words']} | {rating['rating']['overall']} | "
                     f"{rating['rating']['storytelling']} | {rating['note'].replace('|', '/')} |")
    lines += ["", "## Interpretation Limits", "",
        "One direct story per premise, not a reusable simulator or pack. No grounded QA or replay tests.",
        "Cross-scenario diversity is NOT comparable to within-pack diversity. Longer stories and high "
        "rather than xhigh reasoning also differ from the pack run. Pack judge scores were conditional "
        "on runtime success; this baseline includes every completed direct story.", "",
        "See summary.json for usage and estimated costs; STORIES.md for all untouched prose."]
    (OUT / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "generate", "prepare-judge", "judge", "report"))
    parser.add_argument("--api-key-file", type=Path)
    args = parser.parse_args()
    with api.campaign_lock(HERE):
        if args.phase == "prepare":
            prepare()
        elif args.phase == "generate":
            generate(args.api_key_file.read_text().strip())
        elif args.phase == "prepare-judge":
            prepare_judge()
        elif args.phase == "judge":
            judge.judge(args.api_key_file.read_text().strip(), source=OUT / "stories.json",
                        out=OUT / "quality", ledger_arm="luna_direct_20_standard_judge")
        else:
            report()
