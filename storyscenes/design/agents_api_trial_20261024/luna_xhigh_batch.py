"""Twenty separately seeded xhigh packs with frozen context and shared accounting."""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from copy import deepcopy
import json
from pathlib import Path
import shutil
import subprocess
import sys
from threading import Lock, Semaphore
import time
import uuid

import luna_xhigh_trial as control
import judge_stories as judge

api = control.api
HERE = control.HERE
BASE = control.ARM
MANIFEST = HERE / "luna_xhigh_128k_20_manifest.json"
SCENARIOS = [
    ("bakery", ["basket", "icing", "uneven"], "a village bakery", "a child borrows a delivery basket and wants a birthday cake to reach a lonely neighbour intact"),
    ("puppets", ["curtain", "button", "whisper"], "a school puppet theatre", "two friends borrow a sewing kit to rescue a rehearsal when the shy puppeteer loses a prop"),
    ("greenhouse", ["seedling", "shade", "thirsty"], "a community greenhouse", "a child borrows a watering can and wants to protect another gardener's seedlings during a hot afternoon"),
    ("seaside", ["map", "tide", "mistake"], "a seaside path", "siblings borrow a map to find a sheltered picnic place and discover they have followed the wrong landmark"),
    ("library", ["bookmark", "ladder", "promise"], "a neighbourhood library", "a child borrows a book trolley and promises to find a younger friend's missing picture book before closing"),
    ("snow", ["sled", "mittens", "patient"], "a snowy village square", "a child borrows a sled to bring supplies to an older neighbour but a friend wants to race"),
    ("picnic", ["blanket", "crumbs", "gust"], "a riverside picnic meadow", "two cousins borrow a picnic blanket and try to make a welcoming lunch for a cousin who arrives late"),
    ("music", ["drum", "ribbon", "hesitate"], "a community music room", "a child borrows a small drum and wants a nervous newcomer to join a duet without being pressured"),
    ("market", ["scale", "apples", "honest"], "a fruit market", "a young helper borrows a weighing scale and discovers a mistake while filling a neighbour's order"),
    ("camp", ["lantern", "shadow", "brave"], "a family campsite", "a child borrows a lantern to help a frightened sibling find a missing toy before dark"),
    ("pottery", ["clay", "sponge", "crooked"], "a pottery workshop", "a child borrows a shaping tool to make a useful cup as a gift and must decide what to do with a flaw"),
    ("orchard", ["pear", "crate", "reach"], "a small orchard", "two friends borrow a picking basket to gather fruit for a shared snack without damaging the tree"),
    ("costume", ["cape", "mirror", "borrow"], "a costume cupboard before a school play", "a child borrows a cape and tries to help a friend whose costume does not fit the role they were promised"),
    ("pond", ["boat", "net", "stuck"], "a shallow park pond", "a child borrows a long-handled net to retrieve a friend's toy boat while keeping both children safely on the bank"),
    ("repair", ["wheel", "spanner", "rattle"], "a courtyard repair bench", "a child borrows a spanner to fix a shared toy cart and discovers that the first diagnosis was wrong"),
    ("museum", ["torch", "label", "puzzled"], "a local museum activity room", "two children borrow a torch for a shadow exhibit and try to understand why their demonstration differs from the label"),
    ("laundry", ["peg", "sheet", "shelter"], "a shared garden washing line", "a child borrows a peg bag and wants to finish hanging a neighbour's washing before an approaching shower"),
    ("trail", ["compass", "puddle", "shortcut"], "a woodland discovery trail", "two friends borrow a compass and must choose a route that includes a slower companion rather than abandoning them"),
    ("festival", ["bunting", "string", "welcome"], "a village welcome festival", "a child borrows a spool of string and wants to hang decorations where a new neighbour can help without climbing"),
    ("biscuit", ["cutter", "flour", "share"], "a busy family kitchen", "siblings borrow biscuit cutters to make a thank-you gift and disagree about how to divide the last dough"),
]


def arm_for(index):
    return HERE / f"gpt-6-luna_xhigh_128k_{index + 1:02d}_{SCENARIOS[index][0]}"


def prepare():
    if MANIFEST.exists() or any(arm_for(i).exists() for i in range(len(SCENARIOS))):
        raise FileExistsError("Batch already prepared or partially present; refusing overwrite")
    settings = json.loads((BASE / "settings.json").read_text())
    original = json.loads((BASE / "request.json").read_text())
    if api.digest((BASE / "request.json").read_bytes()) != settings["request_sha256"]:
        raise ValueError("Control request changed")
    for name, expected in settings["source_hashes"].items():
        if api.digest((BASE / "input" / name).read_bytes()) != expected:
            raise ValueError(f"Frozen input changed: {name}")
    assert original["model"] == "gpt-6-luna" and original["reasoning"] == {"effort": "xhigh"}
    prefix = "Supplied read-only files:\n"
    content = original["input"][1]["content"]
    if not content.startswith(prefix):
        raise ValueError("Unexpected context format")
    supplied = json.loads(content[len(prefix):])
    old_opening = "Create a complete runnable mini-adventure pack from these ingredients:\nseed 2026102401; a village kite workshop; a borrowed string reel; a child wants\nto include a shy new neighbour in the afternoon's kite flying."
    task = supplied["TASK.md"]
    if task.count(old_opening) != 1 or original["input"][0]["content"] != task:
        raise ValueError("Control task mismatch")
    entries = []
    for index, (slug, words, setting, premise) in enumerate(SCENARIOS):
        seed = 2026102402 + index
        new_task = task.replace(old_opening,
            "Create a complete runnable mini-adventure pack from these ingredients:\n"
            f"Task seed: {seed}\nSeed words: {', '.join(words)}\n"
            f"Setting: {setting}\nPremise: {premise}.\n"
            "The required kite/ module path is only the isolated harness name; write this new scenario, not a kite story.")
        files = {**supplied, "TASK.md": new_task}
        request = deepcopy(original)
        request["max_output_tokens"] = 128000
        request["input"] = [dict(role="developer", content=new_task),
                            dict(role="user", content=prefix + json.dumps(files, ensure_ascii=False))]
        # Bound input tokens by request bytes plus framing and output by its cap.
        conservative_ceiling = 2 * ((len(json.dumps(request).encode()) + 4000) * .125 + 128000 * .25) / 1e6
        if conservative_ceiling > .15:
            raise ValueError("Request exceeds the existing generation reservation")
        arm = arm_for(index)
        arm.mkdir()
        shutil.copytree(BASE / "input", arm / "input")
        (arm / "input/TASK.md").write_text(new_task, encoding="utf-8")
        api.save(arm / "request.json", request)
        updated = deepcopy(settings)
        updated.update(parent_arm=BASE.name, max_output_tokens=128000, timeout_seconds=1800,
                       idempotency_key=str(uuid.uuid4()), request_sha256=api.digest((arm / "request.json").read_bytes()))
        updated["source_hashes"]["TASK.md"] = api.digest(new_task.encode())
        api.save(arm / "settings.json", updated)
        entry = dict(index=index, arm=arm.name, task_seed=seed, words=words, setting=setting, premise=premise,
                     generation_reservation_usd=.15, conservative_ceiling_usd=conservative_ceiling)
        api.save(arm / "seed.json", entry)
        entries.append(entry)
    runner_hashes = {}
    for source in (Path(__file__).resolve(), Path(api.__file__).resolve(), Path(judge.__file__).resolve()):
        target = HERE / "luna_xhigh_128k_20_runner" / source.name
        target.parent.mkdir(exist_ok=True)
        shutil.copyfile(source, target)
        runner_hashes[str(source.relative_to(api.ROOT))] = api.digest(source.read_bytes())
    api.save(MANIFEST, dict(model="gpt-6-luna", reasoning="xhigh", service_tier="flex",
        max_output_tokens=128000, concurrency=20, judge_concurrency=4, entries=entries,
        runner_hashes=runner_hashes,
        note="20 distinct prompt seeds/premises, not an API seed parameter; same frozen engine/example/checker."))
    print(f"Prepared {len(entries)} independent packs", flush=True)


def run_all(key):
    manifest = json.loads(MANIFEST.read_text())
    for name, expected in manifest["runner_hashes"].items():
        if api.digest((api.ROOT / name).read_bytes()) != expected:
            raise ValueError(f"Prepared runner changed: {name}")
    ledger = api.Ledger(HERE)
    if sum(e["reserved_usd"] for e in ledger.data["entries"]) + .15 * 20 > ledger.data["authorized_usd"]:
        raise ValueError("Insufficient headroom to reserve all twenty generation requests")
    check_slots, judge_slots, output_lock = Semaphore(4), Semaphore(4), Lock()

    def log(arm, stage, **details):
        record = dict(arm=arm.name, stage=stage, time=time.time(), **details)
        with output_lock:
            print(json.dumps(record), flush=True)
            with (HERE / "luna_xhigh_128k_20_progress.jsonl").open("a") as f:
                f.write(json.dumps(record) + "\n")

    def work(entry):
        arm = HERE / entry["arm"]
        if (arm / "dispatch.json").exists():
            return dict(arm=arm.name, skipped="already dispatched; no automatic paid retry")
        try:
            log(arm, "generation_start")
            api.run(arm, key)
            log(arm, "generation_returned")
        except Exception as exc:
            log(arm, "generation_failed", error=str(exc))
            return dict(arm=arm.name, generation_error=str(exc))
        with check_slots:
            checked = subprocess.run([sys.executable, str(Path(__file__).resolve()), "check-one", "--index", str(entry["index"])],
                capture_output=True, text=True, timeout=240)
            api.save(arm / "check_runner_output.json", dict(returncode=checked.returncode, stdout=checked.stdout, stderr=checked.stderr))
        if not (arm / "check.json").exists():
            log(arm, "check_failed_without_report")
            return dict(arm=arm.name, check_error="No report")
        check = json.loads((arm / "check.json").read_text())
        runnable = sum(row["ok"] for row in check["attempts"])
        log(arm, "checked", runnable=runnable, passed=check["passed"])
        if runnable == 100 and len(check["attempts"]) == 100:
            with judge_slots:
                try:
                    judge.prepare(source=arm / "check.json", out=arm / "quality", label=arm.name)
                    judge.judge(key, source=arm / "check.json", out=arm / "quality", ledger_arm=arm.name + "_judge")
                    log(arm, "judged")
                except Exception as exc:
                    log(arm, "judge_failed", error=str(exc))
        return dict(arm=arm.name, runnable=runnable, passed=check["passed"],
                    judged=(arm / "quality/result.json").exists())

    results = []
    with ThreadPoolExecutor(max_workers=20) as pool:
        futures = {pool.submit(work, e): e for e in manifest["entries"]}
        for future in as_completed(futures):
            try:
                results.append(future.result())
            except Exception as exc:
                results.append(dict(arm=futures[future]["arm"], worker_error=str(exc)))
            api.save(HERE / "luna_xhigh_128k_20_outcomes.json", results)
    print(json.dumps(results, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "run", "check-one"))
    parser.add_argument("--api-key-file", type=Path)
    parser.add_argument("--index", type=int)
    args = parser.parse_args()
    if args.phase == "check-one":
        api.check(arm_for(args.index))
    else:
        with api.campaign_lock(HERE):
            if args.phase == "prepare":
                prepare()
            else:
                run_all(args.api_key_file.read_text().strip())
