#!/usr/bin/env python3
"""Resumable large reference-seeded runs using the canonical trial protocol."""

from __future__ import annotations

import argparse
import ast
import asyncio
from concurrent.futures import ThreadPoolExecutor, wait, FIRST_COMPLETED
import json
import lzma
from pathlib import Path
import random
import re
import shutil
import statistics
import subprocess
import time

import canonical_examples
import dataset_score
import prompt_trials as trials

ROOT = trials.ROOT
LEDGER = ROOT / "storyworlds/WORST_CONTRIBUTORS_REPAIR.md"


def references(count=100):
    names = re.findall(r"^\| \d+ \| verified \| `([^`]+)`", LEDGER.read_text(), re.M)
    if len(names) < count:
        raise ValueError("not enough verified repair-ledger entries")
    tracked = subprocess.check_output(["git", "ls-files", "storyworlds/worlds"], cwd=ROOT, text=True).splitlines()
    paths = [ROOT / name for name in tracked if name.endswith(".py") and not any(
        part in name for part in ("/tmp/", "/prompt_trials/", "/luna_repaired_examples_"))]
    selected = []
    for index, name in enumerate(names[:count]):
        matches = [path for path in paths if path.name == name]
        if len(matches) != 1:
            raise ValueError(f"ambiguous repair-ledger entry: {name}: {matches}")
        selected.append(dict(label=f"repaired_{index + 1:03d}", source=trials.relative(matches[0]),
                             kind="manually_repaired", ledger_index=index + 1))
    # Canonical labels take precedence when the same source is in both sets.
    canonical = {trials.relative(path): label for label, path in canonical_examples.CANONICAL_EXAMPLES.items()}
    for entry in selected:
        if entry["source"] in canonical:
            entry.update(label=canonical[entry["source"]], kind="canonical_and_repaired")
    selected = [dict(label=label, source=source, kind="canonical") for source, label in canonical.items()
                if not any(entry["source"] == source for entry in selected)] + selected
    hashes = [trials.digest(ROOT / entry["source"]) for entry in selected]
    if len(set(hashes)) != len(hashes):
        raise ValueError("different source paths contain identical examples")
    return selected


def preflight_entry(entry):
    script = ROOT / entry["source"]
    run, rows = trials.sample(script, 100, 777, 120)
    replay, repeated = trials.sample(script, 100, 777, 120)
    verify = trials.local_run(script, ["--verify"], 120)
    for status in (run, replay, verify):
        trials.compact_run(status)
    result = dict(**entry, sha256=trials.digest(script), sample=run, verify=verify,
                  samples=len(rows), exact_unique=len({row["story"] for row in rows}),
                  replay_equal=replay["ok"] and rows == repeated,
                  ok=run["ok"] and len(rows) == 100 and verify["ok"] and replay["ok"] and rows == repeated)
    print(f"Reference {entry['label']}: {'PASS' if result['ok'] else 'FAIL'}", flush=True)
    return result


def prepare(args):
    catalog = ROOT / "storyworlds/batches" / f"{args.name}.references.json"
    if catalog.exists() or trials.trial_path(args.name).exists():
        raise ValueError("run or reference manifest already exists")
    entries = references()
    with ThreadPoolExecutor(max_workers=args.local_workers) as pool:
        checks = list(pool.map(preflight_entry, entries))
    trials.save(catalog.with_suffix(".preflight.json"), checks)
    if any(not entry["ok"] for entry in checks):
        raise ValueError("reference preflight failed; review the saved report before generation")
    trials.save(catalog, entries)
    flags = ["prepare", args.name, "--seed", str(args.seed), "--example-manifest", str(catalog),
             "--unique-tasks", "--total", str(args.count), "--concurrency", str(args.concurrency),
             "--local-samples", "1000"]
    if args.prompt_addendum:
        flags += ["--prompt-addendum", str(args.prompt_addendum)]
    directory = trials.prepare(trials.build_parser().parse_args(flags))
    config = trials.read(directory / "trial.json")
    config.update(large_batch_protocol="reference_batch_v1", local_workers=args.local_workers,
                  compress_samples=True, compact_checks=True)
    for source in (Path(__file__).resolve(), LEDGER, catalog.with_suffix(".preflight.json")):
        destination = directory / "inputs" / trials.relative(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        config["snapshots"].append(dict(source=trials.relative(source), snapshot=trials.relative(destination),
                                        sha256=trials.digest(destination)))
    trials.save(directory / "trial.json", config)
    estimate = trials.budget(args.name, generation_output=6000, judge_input=5000, judge_output=1600)
    trials.save(directory / "budget.json", estimate)
    print(json.dumps(estimate, indent=2), flush=True)


def tasks_for(directory, config):
    tasks = []
    for arm in config["arms"]:
        manifest = ROOT / arm["manifest"]
        for job in trials.read(manifest)["jobs"]:
            tasks.append((job, manifest.parent, directory / "qc" / arm["label"] / job["name"],
                          config, job["seed"] - config["seed"]))
    return tasks


def sample_path(task):
    return effective_output(task) / "samples.jsonl.gz"


def effective_output(task):
    repaired = task[2] / "import_repair"
    return repaired if (repaired / "check.json").exists() else task[2]


def audit_cached(task):
    output = effective_output(task)
    path = output / "check.json"
    if path.exists():
        check = trials.read(path)
        script = ROOT / task[0]["target"]
        if script.exists() and (not (output / "after.py").exists()
                                or trials.digest(script) != trials.digest(output / "after.py")):
            raise ValueError(f"source changed after audit: {script}")
        if not sample_path(task).exists():
            raise ValueError(f"missing archived samples: {path}")
        return check
    if task[2].exists():
        # Preserve an interrupted audit rather than append another sample draw to it.
        task[2].rename(task[2].with_name(task[2].name + ".interrupted_" + trials.service.now_stamp()))
    return trials.audit_one(task)


def terminal_targets(config, positions):
    targets = set()
    for arm in config["arms"]:
        path = (ROOT / arm["manifest"]).parent / "responses.jsonl"
        if not path.exists():
            continue
        with path.open("rb") as handle:
            handle.seek(positions.get(path, 0))
            while True:
                position = handle.tell()
                line = handle.readline()
                if not line or not line.endswith(b"\n"):
                    positions[path] = position
                    break
                targets.add(json.loads(line)["target"])
    return targets


def audit(directory, config, *, streaming=False):
    if not streaming and any(not trials.read(ROOT / arm["manifest"]).get("completed_at") for arm in config["arms"]):
        raise ValueError("generation is not complete")
    tasks = tasks_for(directory, config)
    pending = {index: task for index, task in enumerate(tasks)}
    ready = set() if streaming else {task[0]["target"] for task in tasks}
    positions = {}
    checks = [None] * len(tasks)
    completed = 0
    with ThreadPoolExecutor(max_workers=config["local_workers"]) as pool:
        futures = {}
        while pending or futures:
            if streaming:
                ready.update(terminal_targets(config, positions))
            for index, task in list(pending.items()):
                if len(futures) >= config["local_workers"] * 2:
                    break
                if task[0]["target"] in ready:
                    futures[pool.submit(audit_cached, task)] = index
                    del pending[index]
            if not futures:
                time.sleep(2)
                continue
            done, _ = wait(futures, timeout=2, return_when=FIRST_COMPLETED)
            for future in done:
                checks[futures.pop(future)] = future.result()
                completed += 1
                if completed % 25 == 0:
                    trials.save(directory / "qc/progress.json", dict(completed=completed, planned=len(tasks)))
                    print(f"Local QC {completed}/{len(tasks)}", flush=True)
    trials.save(directory / "qc/checks.json", checks)
    inputs = []
    for check, task in zip(checks, tasks):
        if check["final"]["ok"] and check["verify"]["ok"] and check["samples"] >= 2:
            rows = trials.jsonl(sample_path(task))
            inputs.append(dict(trials.set_quality.select_set(check["script"], rows, check["seed"]),
                               source_sha256=trials.digest(effective_output(task) / "after.py"),
                               sample_file=trials.relative(sample_path(task))))
    trials.save(directory / "qc/judge_inputs.json", inputs)
    trials.save(directory / "qc/settings.json", dict(judge=trials.JUDGE,
        judge_protocol=trials.set_quality.PROTOCOL, judge_stories=trials.set_quality.DEFAULT_COUNT,
        reasoning="none", service_tier="flex", local_samples=config["local_samples"],
        score_policy=config["score_policy"], minimum_samples_for_set_judge=2,
        source_sha256=trials.digest(Path(__file__))))
    print(f"Local QC complete: {len(inputs)}/{len(tasks)} eligible for ten-story judging", flush=True)


def import_bootstrap(source):
    marker = "# Locate the shared StoryWorld helpers from any batch depth."
    if marker in source:
        return source
    tree = ast.parse(source)
    position = tree.body[0].lineno - 1 if tree.body else 0
    for node in tree.body:
        if (isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str)
                or isinstance(node, ast.ImportFrom) and node.module == "__future__"):
            position = node.end_lineno
        else:
            break
    block = ("\n" + marker + "\nfrom pathlib import Path as _StoryPath\nimport sys as _StorySys\n"
             "_storyworlds_root = next(parent for parent in _StoryPath(__file__).resolve().parents\n"
             "                        if (parent / 'results.py').is_file() and (parent / 'asp.py').is_file())\n"
             "_StorySys.path.insert(0, str(_storyworlds_root.parent))\n"
             "_StorySys.path.insert(0, str(_storyworlds_root))\n\n")
    lines = source.splitlines(keepends=True)
    lines[position:position] = [block]
    result = "".join(lines)
    ast.parse(result)
    return result


def repair_import_one(task):
    old = audit_cached(task)
    if old.get("import_repair_accepted"):
        return old
    error = old["standalone"].get("stderr", "")
    if not any(f"No module named '{name}'" in error for name in ("results", "storyworlds", "asp")):
        return old
    script = ROOT / task[0]["target"]
    original = script.read_bytes()
    candidate = import_bootstrap(original.decode("utf-8"))
    output = task[2] / f"import_attempt_{len(list(task[2].glob('import_attempt_*'))) + 1:03d}"
    old_rows = trials.jsonl(sample_path(task))
    try:
        script.write_text(candidate)
        config = dict(task[3], skip_repairs=True)
        new = trials.audit_one((task[0], task[1], output, config, task[4]))
        new_rows = trials.jsonl(output / "samples.jsonl.gz")
        unchanged = not old_rows or old_rows == new_rows
        accepted = (new["final"]["ok"] and new["standalone"]["ok"] and unchanged
                    and (not old["verify"]["ok"] or new["verify"]["ok"]))
        if accepted:
            new.update(before=old["before"], raw_runnable=old["raw_runnable"],
                       repair_changes=old["repair_changes"], repair_accepted=old["repair_accepted"],
                       import_repair_accepted=True, existing_sample_pool_unchanged=unchanged,
                       pre_import_check_sha256=trials.digest(task[2] / "check.json"))
            trials.save(output / "check.json", new)
            output.rename(task[2] / "import_repair")
            print(f"Import repair accepted: {script.name}", flush=True)
            return new
        trials.save(output / "rejected.json", dict(sample_pool_unchanged=unchanged))
    except Exception:
        script.write_bytes(original)
        raise
    script.write_bytes(original)
    return old


def repair_imports(directory, config):
    if (directory / "qc/set_judge").exists():
        raise ValueError("import repair must precede paid judging; preserve an already-judged pass")
    baseline = directory / "qc/checks.before_import_repair.json"
    if not baseline.exists():
        shutil.copyfile(directory / "qc/checks.json", baseline)
    with ThreadPoolExecutor(max_workers=config["local_workers"]) as pool:
        list(pool.map(repair_import_one, tasks_for(directory, config)))
    # Refresh aggregate checks and frozen judge sets from the accepted, cached audits.
    audit(directory, config)


async def judge(directory, config):
    inputs = trials.read(directory / "qc/judge_inputs.json")
    for item in inputs:
        if trials.digest(ROOT / item["script"]) != item["source_sha256"]:
            raise ValueError("a source changed after judge-set selection")
    root = directory / "qc/set_judge"
    root.mkdir(exist_ok=True)
    by_script = recover_judgements(root, inputs)
    pending = [item for item in inputs if item["script"] not in by_script]
    if pending:
        output = root / f"pass_{len(list(root.glob('pass_*'))) + 1:03d}"
        rows = await trials.set_quality.run_sets(pending, output, concurrency=config["concurrency"])
        by_script.update({row["script"]: row for row in rows})
    temporary = root / "quality.jsonl.tmp"
    with temporary.open("w", encoding="utf-8") as handle:
        for item in inputs:
            handle.write(json.dumps(by_script[item["script"]], ensure_ascii=False) + "\n")
    temporary.replace(root / "quality.jsonl")
    trials.save(root / "completed.json", dict(completed_at=trials.service.now_stamp(), worlds=len(inputs)))


def recover_judgements(root, inputs):
    expected = {item["script"]: item for item in inputs}
    completed = {}
    for path in sorted(root.glob("pass_*/inputs.json")):
        saved_inputs = trials.read(path)
        recorded = {row["script"]: row for row in trials.jsonl(path.parent / "quality.jsonl")}
        started = {row["script"] for row in trials.jsonl(path.parent / "attempts.jsonl")}
        for index, item in enumerate(saved_inputs):
            script = item["script"]
            if expected.get(script) != item:
                raise ValueError("judge inputs changed after a paid attempt")
            if script in completed:
                raise ValueError("duplicate attempted judge world across passes")
            if script in recorded:
                completed[script] = recorded[script]
            elif script in started:
                row = dict(script=script, protocol=trials.set_quality.PROTOCOL, model=trials.JUDGE, ok=False)
                response_path = path.parent / f"response_{index:03d}.json"
                if response_path.exists():
                    body = trials.read(response_path)
                    row["response"] = {key: body.get(key) for key in ("id", "model", "status", "service_tier", "usage")}
                    try:
                        if body.get("status") != "completed":
                            raise ValueError(f"incomplete response: {body.get('status')}")
                        row.update(trials.set_quality.validate(json.loads(trials.set_quality.final_text(body)), item), ok=True)
                    except (ValueError, KeyError, TypeError) as exc:
                        row["error"] = str(exc)
                else:
                    row["error"] = "interrupted judge attempt: billing outcome unknown; not automatically retried"
                trials.append(path.parent / "quality.jsonl", row)
                completed[script] = row
    return completed


class SampleGroups:
    """Re-iterable disk-backed groups; only one world's QA is loaded at a time."""
    def __init__(self, tasks):
        self.tasks = tasks

    def __len__(self):
        return len(self.tasks)

    def __iter__(self):
        for task in self.tasks:
            yield trials.jsonl(sample_path(task))


def pack_stream(stories, path):
    ordered = sorted(stories)
    random.Random(0).shuffle(ordered)
    input_bytes = 0
    with lzma.open(path, "wb", format=lzma.FORMAT_XZ, filters=[dict(
            id=lzma.FILTER_LZMA2, preset=6, dict_size=dataset_score.DICTIONARY_BYTES)]) as output:
        for story in ordered:
            encoded = dataset_score.encode_story(story)
            input_bytes += len(encoded)
            output.write(encoded)
    size = path.stat().st_size
    return dict(stories=len(ordered), input_bytes=input_bytes, xz_bytes=size,
                ratio=size / input_bytes if input_bytes else None,
                bytes_per_story=size / len(ordered) if ordered else None,
                sha256=trials.digest(path))


def score_sample_sets(checks, ratings, groups, config):
    rejected = sum(check["final"]["ok"] and check["verify"]["ok"] and check["samples"] < 2 for check in checks)
    aligned = [dict(check, final=dict(check["final"], ok=check["final"]["ok"] and check["samples"] >= 2))
               for check in checks]
    result = dataset_score.score_dataset(aligned, ratings, groups, config["local_samples"],
                                         minimum_quality=config["score_policy"]["minimum_quality"])
    result["runtime_rejected_worlds"] -= rejected
    result.update(insufficient_sample_set_worlds=rejected, minimum_samples_for_set_judge=2)
    return result


def summarize(directory, config):
    tasks = tasks_for(directory, config)
    checks = trials.read(directory / "qc/checks.json")
    ratings = trials.jsonl(directory / "qc/set_judge/quality.jsonl")
    expected = trials.read(directory / "qc/judge_inputs.json")
    if {row["script"] for row in ratings} != {row["script"] for row in expected}:
        raise ValueError("judge pass is incomplete; resume judging before scoring")
    by_script = {row["script"]: row for row in ratings}
    signature = dict(checks_sha256=trials.digest(directory / "qc/checks.json"),
                     ratings_sha256=trials.digest(directory / "qc/set_judge/quality.jsonl"),
                     score_sha256=trials.digest(Path(dataset_score.__file__)),
                     runner_sha256=trials.digest(Path(__file__)),
                     policy=config["score_policy"])
    signature_path = directory / "qc/score_inputs.json"
    if signature_path.exists() and trials.read(signature_path) != signature:
        raise ValueError("scoring inputs changed; preserve this QC pass and create a new scoring pass")
    trials.save(signature_path, signature)
    scores = {}
    for arm in config["arms"]:
        selected = [(check, task) for check, task in zip(checks, tasks) if task[2].parent.name == arm["label"]]
        path = directory / "qc" / arm["label"] / "score.json"
        if path.exists():
            scores[arm["label"]] = trials.read(path)
        else:
            scores[arm["label"]] = score_sample_sets(
                [check for check, _ in selected], by_script, SampleGroups([task for _, task in selected]),
                config)
            trials.save(path, scores[arm["label"]])
        print(f"Scored {arm['label']}: {scores[arm['label']]['score']}", flush=True)
    global_path = directory / "qc/global_score.json"
    if not global_path.exists():
        trials.save(global_path, score_sample_sets(checks, by_script, SampleGroups(tasks), config))
    scores["ALL"] = trials.read(global_path)
    trials.save(directory / "qc/dataset_scores.json", scores)
    pooled_path = directory / "qc/pooled.json"
    if not pooled_path.exists():
        unique_texts = {}
        stories = []
        for group in SampleGroups(tasks):
            for row in group:
                story = row["story"]
                stories.append(unique_texts.setdefault(story, story))
        pooled = dict(dictionary_bytes=dataset_score.DICTIONARY_BYTES, shuffle_seed=0,
                      format="XZ, story-only UTF-8 JSONL, LZMA2 preset 6", variants={})
        for label, texts in (("all_shuffled", stories), ("exact_deduplicated", sorted(unique_texts))):
            pooled["variants"][label] = pack_stream(texts, directory / "qc" / f"{label}.stories.jsonl.xz")
        trials.save(pooled_path, pooled)
    summary = trials.set_quality.summarize(ratings)
    generation_rows = [row for arm in config["arms"] for row in trials.jsonl(
        (ROOT / arm["manifest"]).parent / "responses.jsonl")]
    costs = dict(generation=trials.trial_cost.summarize(generation_rows),
                 judge=trials.trial_cost.summarize(ratings))
    trials.save(directory / "qc/costs.json", costs)
    trials.save(directory / "qc/summary.json", summary)
    catalog = directory / "qc/worlds.jsonl"
    with catalog.with_suffix(".jsonl.tmp").open("w", encoding="utf-8") as handle:
        for check, task in zip(checks, tasks):
            source = ROOT / check["script"]
            snapshot = effective_output(task) / "after.py"
            raw = task[1] / "raw" / source.name
            rating = by_script.get(check["script"], {})
            manifest = trials.read(task[1] / "generation.manifest.json")
            record = dict(script=check["script"], generation_seed=task[0]["seed"], sample_seed=check["seed"],
                example=task[1].name, reference_sources=manifest.get("example_files"),
                raw_source=trials.relative(raw) if raw.exists() else None,
                effective_source_snapshot=trials.relative(snapshot) if snapshot.exists() else None,
                source_sha256=trials.digest(source) if source.exists() else None,
                samples_file=trials.relative(sample_path(task)), samples_sha256=trials.digest(sample_path(task)),
                raw_runnable=check["raw_runnable"], automatic_repair_accepted=check["repair_accepted"],
                repair_changes=check["repair_changes"], import_repair_accepted=check.get("import_repair_accepted", False),
                runtime_ok=check["final"]["ok"], verify_ok=check["verify"]["ok"],
                standalone_ok=check["standalone"]["ok"], replay_equal=check["hash_seed_replay_equal"],
                samples=check["samples"], requested_samples=config["local_samples"],
                exact_unique=check["exact_unique"], skeleton_unique=check["skeleton_unique"],
                qa_pairs=check["qa_pairs"], unique_qa_pairs=check["unique_qa_pairs"],
                mean_story_words=check["mean_story_words"], mean_story_qa_words=check["mean_story_qa_words"],
                judge_ok=rating.get("ok", False), quality=rating.get("rating"), diversity=rating.get("diversity"))
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    catalog.with_suffix(".jsonl.tmp").replace(catalog)
    sample_count = sum(check["samples"] for check in checks)
    length_stats = {key: (sum((check[key] or 0) * check["samples"] for check in checks) / sample_count
                         if sample_count else None) for key in ("mean_story_words", "mean_story_qa_words")}
    trials.save(directory / "qc/lengths.json", dict(samples=sample_count, **length_stats))
    task_design = "disjoint tasks" if config.get("unique_tasks") else "matched tasks across references"
    lines = [f"# {config['name']}", "", f"{len(tasks)} {config['model']}/Flex requests across {len(config['arms'])} reference scripts.",
             f"Seed {config['seed']}; {task_design}; prompt {config['prompt_protocol']}; addendum {config['prompt_addendum']}.",
             "Raw and repaired sources, frozen requests, reference preflights, compressed samples, and judge responses are retained.",
             "The per-world lineage/metrics catalog is `qc/worlds.jsonl` within the retained trial directory.",
             "", "| Check | Worlds |", "| --- | ---: |"]
    for label, value in (("Materialized", sum(bool(row.get("materialized")) for row in generation_rows)),
                         ("Raw ten-sample runnable", sum(check["raw_runnable"] is True for check in checks)),
                         ("Accepted automatic repairs", sum(check["repair_accepted"] for check in checks)),
                         ("Accepted import-path-only repairs", sum(check.get("import_repair_accepted", False) for check in checks)),
                         ("Sample command + verify", sum(check["final"]["ok"] and check["verify"]["ok"] for check in checks)),
                         ("Also complete count, standalone CLI and deterministic replay", sum(
                             check["final"]["ok"] and check["verify"]["ok"] and check["complete_sample_count"]
                             and check["standalone"]["ok"] and check["hash_seed_replay_equal"] for check in checks)),
                         ("Successfully judged", sum(row.get("ok", False) for row in ratings))):
        lines.append(f"| {label} | {value}/{len(tasks)} |")
    lines += ["", "Quality is conditional on successfully judged worlds. Semantic diversity is a separate ten-story diagnostic.",
              "The original geometric formula is unchanged; the stricter CLI/replay/count tally is reported separately.",
              "Scoring also requires the judge's minimum of two returned stories; smaller sets are counted separately as ineligible, not assigned invented ratings.",
              "", "| Example | Worlds | Sample + verify | Quality /9 | Diversity /9 | Exact unique draws | Composite /100 |",
              "| --- | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for arm in config["arms"]:
        group = [check for check, task in zip(checks, tasks) if task[2].parent.name == arm["label"]]
        rated = [by_script[c["script"]] for c in group if by_script.get(c["script"], {}).get("ok")]
        q = f"{statistics.mean(r['rating']['overall'] for r in rated):.3f}" if rated else "-"
        d = f"{statistics.mean(r['diversity']['overall'] for r in rated):.3f}" if rated else "-"
        value = scores[arm["label"]]["score"]
        score = f"{value:.3f}" if value is not None else "unrated"
        lines.append(f"| {arm['label']} | {len(group)} | {sum(c['final']['ok'] and c['verify']['ok'] for c in group)} | "
                     f"{q} | {d} | {sum(c['exact_unique'] for c in group)} | {score} |")
    lines += ["", "## Summary", "", "```json", json.dumps(dict(quality=summary, dataset=scores["ALL"],
              pooled=trials.read(pooled_path), lengths=length_stats, costs=costs), indent=2), "```", ""]
    report = ROOT / "storyworlds/batches" / f"{config['name']}.report.md"
    report.write_text("\n".join(lines))
    shutil.copyfile(report, directory / "report.md")
    trials.save(directory / "qc/completed.json", dict(completed_at=trials.service.now_stamp()))
    print(f"Report: {report}", flush=True)


def snapshot_runtime(directory, phase):
    output = directory / "runtime" / f"{phase}_{trials.service.now_stamp()}"
    output.mkdir(parents=True)
    records = []
    for module in (trials, trials.service, trials.batch, trials.qa, trials.repair_batch_output,
                   trials.set_quality, trials.quality, trials.trial_cost, dataset_score):
        source = Path(module.__file__).resolve()
        shutil.copyfile(source, output / source.name)
        records.append(dict(source=trials.relative(source), sha256=trials.digest(source)))
    source = Path(__file__).resolve()
    shutil.copyfile(source, output / source.name)
    records.append(dict(source=trials.relative(source), sha256=trials.digest(source)))
    trials.save(output / "sources.json", records)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=["prepare", "generate", "audit", "audit-stream", "repair-imports", "judge", "summarize", "archive"])
    parser.add_argument("name")
    parser.add_argument("--seed", type=int, default=2026090710)
    parser.add_argument("--count", type=int, default=1000)
    parser.add_argument("--concurrency", type=int, default=50)
    parser.add_argument("--local-workers", type=int, default=4)
    parser.add_argument("--prompt-addendum", type=Path)
    args = parser.parse_args()
    if args.command == "prepare":
        prepare(args)
        return
    directory, config = trials.load_trial(args.name)
    lock_directory = directory / "qc" if args.command in ("audit", "audit-stream", "repair-imports", "judge", "summarize") else directory
    lock_directory.mkdir(exist_ok=True)
    with trials.trial_lock(lock_directory):
        snapshot_runtime(directory, args.command)
        if args.command == "generate":
            asyncio.run(trials.generate(directory, config))
        elif args.command in ("audit", "audit-stream"):
            audit(directory, config, streaming=args.command == "audit-stream")
        elif args.command == "repair-imports":
            repair_imports(directory, config)
        elif args.command == "judge":
            asyncio.run(judge(directory, config))
        elif args.command == "summarize":
            summarize(directory, config)
        elif args.command == "archive":
            print(trials.archive(args.name))


if __name__ == "__main__":
    main()
