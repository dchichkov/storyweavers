"""Read-only analysis of saved artifacts; write a reproducible batch summary."""
from collections import Counter
import json
from pathlib import Path
import random

import luna_xhigh_batch as batch

HERE = batch.HERE


def read(path):
    return json.loads(path.read_text()) if path.exists() else None


def flex_cost_range(usage):
    details = usage.get("input_tokens_details") or {}
    read_tokens = details.get("cached_tokens", 0)
    written = details.get("cache_write_tokens")
    if written is None:
        return None
    plain = usage["input_tokens"] - read_tokens - written
    if plain < 0:
        return None
    base = plain * .05 + read_tokens * .005 + usage["output_tokens"] * .25
    return [(base + written * rate) / 1e6 for rate in (.0625, .125)]


def report():
    manifest = read(batch.MANIFEST)
    records, samples = [], []
    for entry in manifest["entries"]:
        arm = HERE / entry["arm"]
        response, check, judged = read(arm / "response.json"), read(arm / "check.json"), read(arm / "quality/result.json")
        record = {**entry, "dispatched": (arm / "dispatch.json").exists(),
            "returned": response is not None, "error": read(arm / "error.json"),
            "generation_status": response.get("status") if response else None,
            "runnable": None, "accepted": None, "judged": judged is not None}
        if response:
            usage = response.get("usage") or {}
            record.update(usage=usage, generation_cost_range_usd=flex_cost_range(usage),
                          elapsed_seconds=(read(arm / "outcome.json") or {}).get("elapsed_seconds"))
        if check:
            successes = [r["row"] for r in check["attempts"] if r["ok"]]
            record.update(runnable=len(successes), attempted=len(check["attempts"]),
                          accepted=check["passed"], reference_words=check.get("reference_words"),
                          check_preflight_error=check.get("import_error"),
                          tests=check.get("tests"), corpus=check.get("corpus"),
                          failures=dict(Counter(str(r.get("error")) for r in check["attempts"] if not r["ok"])))
            if successes:
                chosen = random.Random(entry["task_seed"]).choice(successes)
                sample = dict(arm=entry["arm"], task_seed=entry["task_seed"], words=entry["words"],
                              selection="One uniform successful position; conditional on runtime success", row=chosen)
                samples.append(sample)
        if judged:
            record.update(quality=judged["rating"], diversity=judged["diversity"],
                          plot_groups=judged["plot_groups"], judged_stories=judged["judged_stories"])
        records.append(record)
    completed = [r for r in records if r["returned"]]
    checked = [r for r in records if r["runnable"] is not None]
    judged = [r for r in records if r["judged"]]
    ranges = [r["generation_cost_range_usd"] for r in completed if r.get("generation_cost_range_usd")]
    outputs = [r["usage"]["output_tokens"] for r in completed if "output_tokens" in r["usage"]]
    total = dict(requested=len(records), dispatched=sum(r["dispatched"] for r in records),
        generation_failures=sum(r["error"] is not None for r in records),
        returned=len(completed), checked=len(checked), fully_runnable=sum(r["runnable"] == 100 for r in checked),
        accepted=sum(bool(r["accepted"]) for r in checked), judged=len(judged),
        successful_positions=sum(r["runnable"] for r in checked),
        attempted_positions=sum(r["attempted"] for r in checked),
        check_preflight_failures=sum(bool(r.get("check_preflight_error")) for r in checked),
        outputs_above_64k=sum(n > 64000 for n in outputs),
        outputs_at_128k=sum(n >= 128000 for n in outputs),
        max_output_tokens=max(outputs, default=0),
        quality_mean=sum(r["quality"]["overall"] for r in judged) / len(judged) if judged else None,
        diversity_mean=sum(r["diversity"]["overall"] for r in judged) / len(judged) if judged else None,
        output_tokens=sum(r["usage"].get("output_tokens", 0) for r in completed),
        reasoning_tokens=sum((r["usage"].get("output_tokens_details") or {}).get("reasoning_tokens", 0) for r in completed),
        estimated_generation_cost_range_usd=[sum(r[i] for r in ranges) for i in (0, 1)],
        costed_responses=len(ranges),
        warning="Quality is conditional on 100/100 runnable packs; no repairs. One prompt per distinct scenario; no matched 64k control batch.")
    batch.api.save(HERE / "luna_xhigh_128k_20_summary.json", dict(totals=total, packs=records))
    batch.api.save(HERE / "luna_xhigh_128k_20_manual_samples.json", samples)
    finished = all(r["returned"] or r["error"] for r in records)
    lines = ["# Luna Xhigh: Twenty Distinct Seeds", "", ("Completed" if finished else "Live") + " artifact summary; raw outputs remain untouched.", "",
        f"Returned {total['returned']}/20; checked {total['checked']}; fully runnable {total['fully_runnable']}; "
        f"full mechanical acceptance {total['accepted']}; judged {total['judged']}.", "",
        "| Pack | Seed words | Generation | Runtime /100 | Tests | Reference words | Quality /9 | Diversity /9 | Output tokens |",
        "| --- | --- | --- | ---: | --- | ---: | ---: | ---: | ---: |"]
    for r in records:
        test = r.get("tests") or {}
        test_label = "pass" if test.get("passed") else "fail" if test else "-"
        status = "error" if r["error"] else r["generation_status"] or "pending"
        runtime = "not tested" if r.get("check_preflight_error") else r['runnable'] if r['runnable'] is not None else '-'
        lines.append(f"| {r['index']+1:02d} {r['arm'].split('_')[-1]} | {', '.join(r['words'])} | "
            f"{status} | {runtime} | {test_label} | {r.get('reference_words', '-')} | "
            f"{r.get('quality', {}).get('overall', '-')} | {r.get('diversity', {}).get('overall', '-')} | "
            f"{r.get('usage', {}).get('output_tokens', '-')} |")
    lines += ["", total["warning"], "", "See `luna_xhigh_128k_20_summary.json` for failures, outcomes, usage and costs.",
              "See `LUNA_XHIGH_128K_20_SAMPLES.md` for a separate manual-reading sample, not the paid judge selection.",
              "Snow's inventory JSON fails checker preflight; its runtime is untested, not 100 observed runtime failures."]
    (HERE / "LUNA_XHIGH_128K_20_TABLE.md").write_text("\n".join(lines) + "\n")
    text = ["# One Random Runnable Story Per Pack", "", "Selection is conditional on success; see JSON for states, parameters and traces."]
    for s in samples:
        row = s["row"]
        text += ["", f"## {s['arm']}", "", f"Task seed {s['task_seed']}; sample seed {row['seed']}; {row['scene_count']} scenes.", "", row["story"]]
    (HERE / "LUNA_XHIGH_128K_20_SAMPLES.md").write_text("\n".join(text) + "\n")
    print(json.dumps(total, indent=2))


if __name__ == "__main__":
    report()
