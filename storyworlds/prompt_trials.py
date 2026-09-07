#!/usr/bin/env python3
"""Prepare, run, evaluate, compare, and archive matched canonical-example trials."""

from __future__ import annotations

import argparse
import asyncio
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from dataclasses import asdict
import fcntl
import hashlib
import json
import lzma
import os
from pathlib import Path
import re
import random
import shutil
import statistics
import subprocess
import sys
import tarfile

import canonical_examples
import dataset_score
import openai_batch_world_factory as batch
import openai_service_world_factory as service
import openai_story_quality as quality
import openai_world_set_quality as set_quality
import qa_static_check as qa
import repair_batch_output
import trial_cost

ROOT = batch.ROOT
TRIALS = ROOT / "storyworlds/batches/prompt_trials"
TARGETS = ROOT / "storyworlds/worlds/prompt_trials"
JUDGE = set_quality.DEFAULT_MODEL
sys.path.insert(0, str(ROOT))
from training.storyworld_chat.analyze_world_contributors import story_skeleton


def relative(path: Path) -> str:
    return path.resolve().relative_to(ROOT).as_posix()


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n")
    temporary.replace(path)


def read(path: Path):
    return json.loads(path.read_text())


def jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.exists() else []


def append(path: Path, row: dict) -> None:
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def trial_path(name: str) -> Path:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_-]*", name):
        raise ValueError("trial name must contain only letters, digits, underscores, and hyphens")
    return TRIALS / name


@contextmanager
def trial_lock(directory: Path):
    with (directory / ".lock").open("a") as handle:
        try:
            fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError("another process is already running this trial") from exc
        yield


def prepare(args) -> Path:
    score_policy = dataset_score.policy(args.minimum_quality)
    directory = trial_path(args.name)
    target_root = TARGETS / args.name
    if directory.exists() or target_root.exists():
        raise ValueError("trial already exists; use a new name or run the existing prepared trial")
    if args.per_example < 1 or args.concurrency < 1 or args.local_samples < 1 or args.timeout <= 0:
        raise ValueError("counts, concurrency, sample count, and timeout must be positive")
    labels = args.examples or list(canonical_examples.CANONICAL_EXAMPLES)
    if len(set(labels)) != len(labels):
        raise ValueError("duplicate example names")
    factory_args = service.build_parser().parse_args([
        "--model", args.model, "--reasoning-effort", args.reasoning_effort,
        "--service-tier", "flex", "--concurrency", str(args.concurrency),
        "--seed", str(args.seed), "-n", str(args.per_example),
    ])
    factory_args.prompt_addendum = args.prompt_addendum
    service.validate_args(factory_args)
    # Build every request before creating a trial or contacting the service.
    prepared = []
    for label in labels:
        factory_args.example_worlds = label
        factory_args.target_dir = target_root / label
        _, target_dir, jobs = service.make_jobs(factory_args, stamp="prepared")
        requests = [{"job": asdict(job), "body": service.request_body(factory_args, job)} for job in jobs]
        prepared.append((label, target_dir, requests))
    directory.mkdir(parents=True)
    sources = [canonical_examples.EXAMPLE_SOURCES[label] for label in labels]
    sources += [batch.STORY_CONTRACT_PATH, batch.RESULTS_PATH, batch.ASP_PATH,
                Path(batch.__file__), Path(service.__file__), Path(quality.__file__),
                Path(qa.__file__), Path(repair_batch_output.__file__),
                Path(canonical_examples.__file__), Path(__file__),
                ROOT / "storyworlds/compression_review.py",
                Path(dataset_score.__file__),
                Path(set_quality.__file__), Path(trial_cost.__file__),
                ROOT / "storyworlds/seed.py",
                ROOT / "training/storyworld_chat/analyze_world_contributors.py"]
    if args.prompt_addendum:
        sources.append(args.prompt_addendum.resolve())
    snapshots = []
    for source in dict.fromkeys(sources):
        destination = directory / "inputs" / relative(source)
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)
        snapshots.append({"source": relative(source), "snapshot": relative(destination), "sha256": digest(destination)})
    config = dict(name=args.name, created_at=service.now_stamp(), model=args.model,
                  example_set=canonical_examples.CANONICAL_SET_ID if labels == list(canonical_examples.CANONICAL_EXAMPLES) else "custom",
                  reasoning_effort=args.reasoning_effort, service_tier="flex", judge=JUDGE,
                  judge_protocol=set_quality.PROTOCOL, judge_stories=set_quality.DEFAULT_COUNT,
                  seed=args.seed, per_example=args.per_example, concurrency=args.concurrency,
                  local_samples=args.local_samples, sample_seed=777, timeout=args.timeout,
                  score_policy=score_policy,
                  prompt_addendum=relative(args.prompt_addendum) if args.prompt_addendum else None,
                  prompt_protocol=batch.PROMPT_PROTOCOL, snapshots=snapshots, arms=[])
    for label, target_dir, requests in prepared:
        arm_dir = directory / label
        arm_dir.mkdir()
        request_path = arm_dir / "requests.jsonl"
        for request in requests:
            append(request_path, request)
        manifest_path = arm_dir / "generation.manifest.json"
        manifest = dict(count=len(requests), base_seed=args.seed, model=args.model,
                        example_set=config["example_set"],
                        reasoning_effort=args.reasoning_effort, service_tier="flex", emit_mode="source",
                        example_worlds=label, example_files=None,
                        prompt_addendum=config["prompt_addendum"], target_dir=relative(target_dir),
                        response_jsonl=relative(arm_dir / "responses.jsonl"),
                        jobs=[item["job"] for item in requests])
        save(manifest_path, manifest)
        config["arms"].append(dict(label=label, manifest=relative(manifest_path),
                                   requests=relative(request_path), requests_sha256=digest(request_path)))
    save(directory / "trial.json", config)
    return directory


def load_trial(name: str) -> tuple[Path, dict]:
    directory = trial_path(name)
    config = read(directory / "trial.json")
    for arm in config["arms"]:
        if digest(ROOT / arm["requests"]) != arm["requests_sha256"]:
            raise ValueError(f"frozen requests changed for {arm['label']}; prepare a new trial")
    return directory, config


async def generate(directory: Path, config: dict) -> None:
    pending = []
    for arm in config["arms"]:
        parent = (ROOT / arm["manifest"]).parent
        responses = jsonl(parent / "responses.jsonl")
        completed = {row["custom_id"] for row in responses}
        if len(completed) != len(responses):
            raise ValueError(f"duplicate response IDs in {parent}")
        started = {row["custom_id"] for row in jsonl(parent / "attempts.jsonl")}
        received = {row["custom_id"]: row for row in jsonl(parent / "received.jsonl")}
        for item in jsonl(ROOT / arm["requests"]):
            job = batch.StoryworldJob(**item["job"])
            if job.custom_id in completed:
                continue
            if job.custom_id in received:
                finish_response(parent, job, received[job.custom_id])
                continue
            if job.custom_id in started:
                # An interrupted call may have been billed. Never silently resubmit it.
                append(parent / "responses.jsonl", dict(custom_id=job.custom_id, target=job.target,
                    materialized=False, error="interrupted attempt: outcome unknown; not automatically retried"))
                continue
            if (ROOT / job.target).exists():
                raise ValueError(f"target already exists without a response record: {job.target}")
            pending.append((parent, job, item["body"]))
    if pending:
        args = service.build_parser().parse_args([])
        args.base_url = None
        client = service.make_client(args)
        semaphore = asyncio.Semaphore(config["concurrency"])

        async def one(parent, job, request):
            async with semaphore:
                append(parent / "attempts.jsonl", dict(custom_id=job.custom_id, started_at=service.now_stamp()))
                row = await service.call_one(client, args, job, asyncio.Semaphore(1), request=request)
                # Keep the response durably before touching the materialized source.
                append(parent / "received.jsonl", row)
                finish_response(parent, job, row)
                print(f"{parent.name}: {job.name}: {'written' if row['materialized'] else 'failed'}", flush=True)

        async with client:
            await asyncio.gather(*(one(*item) for item in pending))
    for arm in config["arms"]:
        manifest_path = ROOT / arm["manifest"]
        manifest = read(manifest_path)
        rows = jsonl(manifest_path.parent / "responses.jsonl")
        manifest.update(completed_at=service.now_stamp(), ok=sum(bool(row.get("materialized")) for row in rows),
                        failed=sum(not row.get("materialized") for row in rows))
        save(manifest_path, manifest)


def finish_response(parent: Path, job, row: dict) -> None:
    row["materialized"] = False
    if not row.get("error"):
        try:
            source, _ = batch.extract_python_source(row, job.target)
            target = ROOT / job.target
            completed = ((row.get("response") or {}).get("body") or {}).get("status") == "completed"
            expected = source.rstrip() + "\n" if source else None
            if completed and expected and target.exists() and target.read_text() == expected:
                ok, detail = True, "recovered existing materialization from saved response"
            else:
                ok, detail = service.materialize_row(row, overwrite=False, allow_incomplete=False)
            row.update(materialized=ok, materialize_detail=detail)
            if ok:
                raw = parent / "raw" / f"{job.name}.py"
                raw.parent.mkdir(exist_ok=True)
                shutil.copyfile(target, raw)
        except OSError as exc:
            row["materialize_detail"] = str(exc)
    append(parent / "responses.jsonl", row)


def local_run(script: Path, flags: list[str], timeout: float, *, standalone=False, hash_seed="0") -> dict:
    env = {key: value for key, value in os.environ.items()
           if not any(word in key.upper() for word in ("KEY", "TOKEN", "SECRET"))}
    env["PYTHONHASHSEED"] = hash_seed
    env.pop("PYTHONPATH", None)
    if not standalone:
        env["PYTHONPATH"] = str(ROOT / "storyworlds")
    try:
        proc = subprocess.run([sys.executable, str(script), *flags], cwd=ROOT, env=env,
                              text=True, capture_output=True, timeout=timeout)
        return dict(ok=proc.returncode == 0, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr)
    except (subprocess.TimeoutExpired, OSError) as exc:
        return dict(ok=False, error=str(exc))


def sample(script: Path, count: int, seed: int, timeout: float) -> tuple[dict, list[dict]]:
    result = local_run(script, ["-n", str(count), "--seed", str(seed), "--qa", "--json"], timeout)
    rows = []
    if result["ok"]:
        try:
            rows = qa.parse_json_samples(result["stdout"])
            if not rows or any(not isinstance(row.get("story"), str) or not row["story"].strip() for row in rows):
                raise ValueError("empty or missing story")
            if any(not isinstance(row.get("story_qa", []), list) for row in rows):
                raise ValueError("story_qa must be a list")
        except (ValueError, TypeError) as exc:
            result.update(ok=False, error=str(exc))
    return result, rows if result["ok"] else []


def compression_metrics(stories: list[str]) -> dict:
    if not stories:
        return dict(input_bytes=0, xz_bytes=0, ratio=0.0)
    stories = sorted(stories)
    random.Random(0).shuffle(stories)
    data = json.dumps(stories, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    compressed = lzma.compress(data, format=lzma.FORMAT_XZ, preset=6)
    return dict(input_bytes=len(data), xz_bytes=len(compressed), ratio=len(compressed) / len(data))


def sample_metrics(rows: list[dict], requested: int) -> dict:
    exact = {row["story"]: row for row in rows}
    skeletons = {story_skeleton(row["story"], row.get("params", {})) for row in exact.values()}
    pairs = [(str(item.get("question") or ""), str(item.get("answer") or ""))
             for row in rows for item in row.get("story_qa", []) if isinstance(item, dict)]
    return dict(samples=len(rows), complete_sample_count=len(rows) == requested,
                exact_unique=len(exact), skeleton_unique=len(skeletons),
                exact_unique_fraction=len(exact) / requested, skeleton_unique_fraction=len(skeletons) / requested,
                lzma_all=compression_metrics([row["story"] for row in rows]),
                lzma_deduplicated=compression_metrics(list(exact)),
                lzma_skeletons=compression_metrics(sorted(skeletons)),
                qa_pairs=len(pairs), unique_qa_pairs=len({(qa.normalize(q), qa.normalize(a)) for q, a in pairs}),
                mean_story_words=statistics.mean(len(row["story"].split()) for row in rows) if rows else None,
                mean_story_qa_words=statistics.mean(len(row["story"].split()) + sum(
                    len(str(item.get("question", "")).split()) + len(str(item.get("answer", "")).split())
                    for item in row.get("story_qa", []) if isinstance(item, dict)) for row in rows) if rows else None)


def audit_one(task) -> dict:
    job, arm_dir, output, config, index = task
    script = ROOT / job["target"]
    seed = config["sample_seed"] + index
    timeout = config["timeout"]
    output.mkdir(parents=True)
    before, _ = sample(script, 10, seed, timeout)
    raw_path = arm_dir / "raw" / script.name
    raw_check_path = arm_dir / f"{job['name']}.raw_check.json"
    if script.exists():
        shutil.copyfile(script, output / "before.py")
    if raw_path.exists() and script.exists() and digest(raw_path) == digest(script):
        save(raw_check_path, before)
    raw_ok = read(raw_check_path)["ok"] if raw_check_path.exists() else (False if not script.exists() else None)
    changes = []
    accepted = False
    if not before["ok"] and script.exists():
        original = script.read_bytes()
        repaired, changes = repair_batch_output.repair_source(original.decode("utf-8"))
        if changes:
            script.write_text(repaired.rstrip() + "\n")
            repaired_check, _ = sample(script, 10, seed, timeout)
            accepted = repaired_check["ok"]
            if not accepted:
                script.write_bytes(original)
    final, rows = sample(script, config["local_samples"], seed, timeout)
    verify = local_run(script, ["--verify"], timeout)
    standalone = local_run(script, ["-n", "1", "--seed", str(seed), "--json"], timeout, standalone=True)
    replay = local_run(script, ["-n", str(config["local_samples"]), "--seed", str(seed), "--qa", "--json"],
                       timeout, hash_seed="1") if rows else {"ok": False}
    replay_equal = False
    if replay["ok"]:
        try:
            replay_equal = qa.parse_json_samples(replay["stdout"]) == rows
        except ValueError:
            pass
    if script.exists():
        shutil.copyfile(script, output / "after.py")
    for row in rows:
        append(output / "samples.jsonl", row)
    # Use the existing static-QA source analysis on the already collected samples.
    static = qa.CheckResult()
    qa.collect_occurrences(static, script, seed, rows)
    static.duplicates = {key: hits for key, hits in static.duplicates.items() if len(hits) > 1}
    qa.attach_source_hits(static)
    result = dict(script=job["target"], seed=seed, raw_runnable=raw_ok,
                  before=before, repair_changes=changes, repair_accepted=accepted,
                  final=final, verify=verify, standalone=standalone, hash_seed_replay_equal=replay_equal,
                  static_qa_duplicate_groups=len(static.duplicates),
                  static_qa_source_hits=sum(len(hits) for hits in static.source_hits.values()),
                  **sample_metrics(rows, config["local_samples"]))
    save(output / "check.json", result)
    print(f"Checked {script.name}: runnable={final['ok']}, verify={verify['ok']}", flush=True)
    return result


async def evaluate(directory: Path, config: dict, *, skip_quality: bool) -> Path:
    if any(not read(ROOT / arm["manifest"]).get("completed_at") for arm in config["arms"]):
        raise ValueError("generation is incomplete; run the trial first")
    output = directory / f"eval_{len(list(directory.glob('eval_*'))) + 1:03d}"
    output.mkdir()
    minimum_quality = config.get("score_policy", {}).get("minimum_quality", dataset_score.DEFAULT_MINIMUM_QUALITY)
    save(output / "settings.json", dict(judge=JUDGE, judge_protocol=set_quality.PROTOCOL,
                                        judge_stories=set_quality.DEFAULT_COUNT, judge_reasoning="none",
                                        judge_service_tier="flex", skip_quality=skip_quality,
                                        sample_seed=config["sample_seed"], local_samples=config["local_samples"],
                                        score_policy=dataset_score.policy(minimum_quality), lzma_preset=6,
                                        code_sha256={relative(Path(module.__file__)): digest(Path(module.__file__))
                                                     for module in (quality, set_quality, qa, repair_batch_output, dataset_score, trial_cost)}))
    tasks = []
    for arm in config["arms"]:
        manifest_path = ROOT / arm["manifest"]
        for index, job in enumerate(read(manifest_path)["jobs"]):
            tasks.append((job, manifest_path.parent, output / arm["label"] / job["name"], config, index))
    with ThreadPoolExecutor(max_workers=config["concurrency"]) as pool:
        checks = list(pool.map(audit_one, tasks))
    save(output / "checks.json", checks)
    from compression_review import pooled_review
    groups = [jsonl(task[2] / "samples.jsonl") for task in tasks]
    pooled_review([row for group in groups for row in group], output / "pooled", groups=groups)
    inputs = [dict(set_quality.select_set(check["script"], group, check["seed"]),
                   source_sha256=digest(task[2] / "after.py"), sample_file=relative(task[2] / "samples.jsonl"))
              for check, group, task in zip(checks, groups, tasks)
              if check["final"]["ok"] and check["verify"]["ok"] and len(group) >= 2]
    save(output / "judge_inputs.json", inputs)
    if not skip_quality and inputs:
        await set_quality.run_sets(inputs, output / "set_judge", concurrency=config["concurrency"])
    ratings = jsonl(output / "set_judge/quality.jsonl")
    by_script = {row["script"]: row for row in ratings}
    for check, samples in zip(checks, groups):
        check["geometric_score"] = dataset_score.score_dataset(
            [check], by_script, [samples], config["local_samples"], minimum_quality=minimum_quality)["score"]
    scores = {}
    for arm in config["arms"]:
        targets = {job["target"] for job in read(ROOT / arm["manifest"])["jobs"]}
        selected = [(check, samples) for check, samples in zip(checks, groups) if check["script"] in targets]
        scores[arm["label"]] = dataset_score.score_dataset(
            [check for check, _ in selected], by_script, [samples for _, samples in selected],
            config["local_samples"], minimum_quality=minimum_quality)
    scores["ALL"] = dataset_score.score_dataset(checks, by_script, groups, config["local_samples"],
                                                  minimum_quality=minimum_quality)
    save(output / "dataset_scores.json", scores)
    save(output / "checks.json", checks)
    save(output / "summary.json", set_quality.summarize(ratings))
    generation_rows = [row for arm in config["arms"]
                       for row in jsonl((ROOT / arm["manifest"]).parent / "responses.jsonl")]
    save(output / "costs.json", dict(generation=trial_cost.summarize(generation_rows),
                                     this_judge_pass=trial_cost.summarize(ratings)))
    save(output / "completed.json", dict(completed_at=service.now_stamp()))
    return output


def report(names: list[str]) -> str:
    lines = ["# Canonical Prompt Trials", "",
             "Each arm uses the same tasks. Quality and semantic-diversity scores are conditional on successful ratings, on a 0-9 scale.",
             "Geometric score: 100 * usable-unique-story yield * sqrt(quality/9 * pooled compression retention).",
             "Only runtime/verify-passing worlds meeting the configured quality floor contribute. Missing ratings leave the score uncomputed.",
             "Compression retention = pooled compressed size / sum of independently compressed story sizes, using raw LZMA2 on qualified exact-deduplicated text.",
             "Skeletons remove parameter values; they are a repetition diagnostic, not a count of causal plots.",
             "LZMA ratio is compressed/input bytes of shuffled story-only text: higher means less compressible, not necessarily better prose.", ""]
    for name in names:
        directory, config = load_trial(name)
        completed = sorted(directory.glob("eval_*/completed.json"))
        checks = read(completed[-1].parent / "checks.json") if completed else []
        settings = read(completed[-1].parent / "settings.json") if completed else config
        rating_path = completed[-1].parent / "set_judge/quality.jsonl" if completed else None
        if rating_path and not rating_path.exists():
            rating_path = completed[-1].parent / "quality.jsonl"
        ratings = {row["script"]: row for row in jsonl(rating_path)} if rating_path else {}
        score_path = completed[-1].parent / "dataset_scores.json" if completed else None
        dataset_scores = read(score_path) if score_path and score_path.exists() else {}
        lines += [f"## {name}", "",
                  "| Example | Worlds | Raw runnable | Repaired | Runnable | Verify | CLI | Rated worlds | Quality | Geometric /100 |",
                  "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
        pending_judge_upgrade = not completed and config.get("judge") != JUDGE
        diversity = ["| Example | Returned / requested | Median exact / skeletons | Median LZMA all / dedup | Mean story / story+QA words |",
                     "| --- | ---: | ---: | ---: | ---: |"]
        semantic = ["| Example | Stories judged | Semantic diversity /9 | Mean plot groups / judged set |",
                    "| --- | ---: | ---: | ---: |"]
        arms = [(arm["label"], read(ROOT / arm["manifest"])["jobs"]) for arm in config["arms"]]
        arms.append(("ALL", [job for _, jobs in arms for job in jobs]))
        for label, jobs in arms:
            targets = {job["target"] for job in jobs}
            rows = [row for row in checks if row["script"] in targets]
            scores = [ratings[target]["rating"]["overall"] for target in targets if ratings.get(target, {}).get("ok")]
            sets = [ratings[target] for target in targets if ratings.get(target, {}).get("ok")
                    and "diversity" in ratings[target]]
            if sets:
                semantic.append(f"| {label} | {sum(row['judged_stories'] for row in sets)} | "
                                f"{statistics.mean(row['diversity']['overall'] for row in sets):.2f} | "
                                f"{statistics.mean(len(row['plot_groups']) for row in sets):.2f} |")
            valid = [row for row in rows if row["final"]["ok"]]
            average = lambda key: f"{statistics.mean(row[key] for row in valid):.1f}" if valid else "-"
            median = lambda key: f"{statistics.median(row[key] for row in valid):g}" if valid else "-"
            raw = str(sum(row["raw_runnable"] is True for row in rows)) if rows and all(row["raw_runnable"] is not None for row in rows) else "-"
            score = f"{statistics.mean(scores):.2f}" if scores else "-"
            composite_value = dataset_scores.get(label, {}).get("score")
            composite = f"{composite_value:.2f}" if composite_value is not None else "-"
            fields = [label, len(jobs), raw,
                      sum(row["repair_accepted"] for row in rows), len(valid),
                      sum(row["verify"]["ok"] for row in rows), sum(row["standalone"]["ok"] for row in rows),
                      f"{len(scores)}/{len(jobs)}", score, composite]
            lines.append("| " + " | ".join(map(str, fields)) + " |")
            ratios = [f"{statistics.median(row[key]['ratio'] for row in valid):.4f}" if valid else "-"
                      for key in ("lzma_all", "lzma_deduplicated")]
            diversity.append(f"| {label} | {sum(row['samples'] for row in rows)} / {len(jobs) * config['local_samples']} | "
                             f"{median('exact_unique')} / {median('skeleton_unique')} | {' / '.join(ratios)} | "
                             f"{average('mean_story_words')} / {average('mean_story_qa_words')} |")
        lines += ["", *diversity]
        if len(semantic) > 2:
            lines += ["", *semantic, "", "Semantic diversity is a separate small-sample diagnostic, not an extra factor in the geometric score."]
        if dataset_scores:
            lines += ["", "| Scoring Pool | Usable Unique Yield | Qualified Quality | Compression Retention | Quality-Rejected Worlds |",
                      "| --- | ---: | ---: | ---: | ---: |"]
            for label, values in dataset_scores.items():
                number = lambda key, fmt: format(values[key], fmt) if values.get(key) is not None else "-"
                lines.append(f"| {label} | {number('yield_fraction', '.1%')} | {number('quality_mean', '.2f')} | "
                             f"{number('diversity', '.2%')} | {values['quality_rejected_worlds']} |")
            lines += ["", f"Scoring protocol: {dataset_scores['ALL']['policy']['protocol']}; quality floor: {dataset_scores['ALL']['policy']['minimum_quality']:g}/9. "
                      "Arm and whole-trial scores recompress their own pooled stories; they are not averages of per-world scores."]
        elif completed:
            lines += ["", "This older evaluation has no geometric scores. Its original weighted scores remain in checks.json; they are not relabeled or overwritten."]
        if completed and (completed[-1].parent / "pooled/compression.json").exists():
            pooled = read(completed[-1].parent / "pooled/compression.json")
            stats = pooled["variants"]["all_shuffled"]
            if stats["stories"]:
                lines += ["", f"**Pooled story-only corpus:** {stats['stories']} stories, "
                          f"{stats['input_bytes'] / 2**20:.2f} MiB -> {stats['xz_bytes'] / 1024:.1f} KiB, "
                          f"XZ/input {stats['ratio']:.2%}; {stats['bytes_per_story']:.1f} compressed bytes/story. "
                          "Explicit 64 MiB LZMA2 dictionary; grouped, deduplicated, and skeleton controls are retained."]
        lines += ["", f"`{name}`: seed {config['seed']}, {config['model']}, reasoning {config['reasoning_effort']}, "
                  f"example set {config.get('example_set', 'legacy/unversioned')}; "
                  f"Flex; judge {settings.get('judge', config.get('judge'))}; "
                  f"{settings.get('judge_protocol', quality.PROMPT_PROTOCOL)}; "
                  f"{settings.get('judge_stories', 1)} judge stories/world; {config['local_samples']} local samples requested per world.", ""]
        if pending_judge_upgrade:
            lines += [f"No completed evaluation yet. The saved plan above predates the judge upgrade; the next evaluation uses "
                      f"{JUDGE}, {set_quality.PROTOCOL}, {set_quality.DEFAULT_COUNT} stories/world and records new settings.", ""]
        cost_path = completed[-1].parent / "costs.json" if completed else None
        if cost_path and cost_path.exists():
            for label, cost in read(cost_path).items():
                lines.append(f"{label}: returned-usage estimate ${cost['usd_low']:.4f}-${cost['usd_high']:.4f}; "
                             f"{cost['unpriced_requests']} requests unpriced. Generation is a one-time cost; each explicit re-evaluation adds a judge pass.")
    return "\n".join(lines) + "\n"


def budget(name: str, *, generation_output=4200, judge_input=3950, judge_output=1014) -> dict:
    if min(generation_output, judge_input, judge_output) < 1:
        raise ValueError("token estimates must be positive")
    _, config = load_trial(name)
    requests = [row["body"] for arm in config["arms"] for row in jsonl(ROOT / arm["requests"])]
    if any(body.get("service_tier") != "flex" for body in requests):
        raise ValueError("this budget command assumes frozen Flex requests")
    def generation_cost(outputs):
        values = [trial_cost.estimate(body["model"], max(1, round(len(json.dumps(body["input"])) / 4)), count)
                  for body, count in zip(requests, outputs)]
        if not all(value["known"] for value in values):
            raise ValueError("no budget rates for this generation model")
        return {key: sum(value[key] for value in values) for key in ("usd_low", "usd_high")}
    generation = generation_cost([generation_output] * len(requests))
    capped_generation = generation_cost([body["max_output_tokens"] for body in requests])
    judge = trial_cost.estimate(JUDGE, judge_input, judge_output)
    judge_cap = trial_cost.estimate(JUDGE, judge_input, set_quality.MAX_OUTPUT_TOKENS)
    if not judge["known"] or not judge_cap["known"]:
        raise ValueError("no budget rates for this judge input size")
    for value in (judge, judge_cap):
        for key in ("usd_low", "usd_high"):
            value[key] *= len(requests)
    return dict(worlds=len(requests), generation=generation, judge=judge,
                total_usd_low=generation["usd_low"] + judge["usd_low"],
                total_usd_high=generation["usd_high"] + judge["usd_high"],
                output_caps_scenario_usd=capped_generation["usd_high"] + judge_cap["usd_high"],
                assumptions=dict(service_tier="flex", pricing_date=trial_cost.PRICING_DATE,
                    pricing_url=trial_cost.PRICING_URL, generation_input="frozen input JSON characters / 4, approximate",
                    generation_output_tokens=generation_output, judge_input_tokens=judge_input,
                    judge_output_tokens=judge_output, judge_model=JUDGE, judged_stories_per_world=set_quality.DEFAULT_COUNT,
                    caching="no reads assumed; range covers zero to all input being cache writes",
                    warning="Estimate, not a spend limit. Output-cap scenario still assumes estimated inputs. Excludes retries and further evaluations."))


def archive(name: str) -> Path:
    directory, _ = load_trial(name)
    destination = ROOT / "storyworlds/batch_archives" / f"prompt_trial_{name}_{service.now_stamp()}.tar.gz"
    with tarfile.open(destination, "x:gz") as handle:
        for root in (directory, TARGETS / name):
            if root.exists():
                for path in sorted(root.rglob("*")):
                    if path.is_file() and "__pycache__" not in path.parts:
                        handle.add(path, arcname=relative(path), recursive=False)
    destination.with_suffix(destination.suffix + ".sha256").write_text(f"{digest(destination)}  {destination.name}\n")
    return destination


def build_parser():
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    plan = commands.add_parser("prepare", help="freeze requests and sources; no API calls")
    plan.add_argument("name")
    plan.add_argument("--seed", type=int, required=True)
    plan.add_argument("--examples", nargs="+", choices=list(canonical_examples.EXAMPLE_SOURCES),
                      help="explicit reference names, including retired examples; default: current seven-world canonical set")
    plan.add_argument("--per-example", type=int, default=3)
    plan.add_argument("--model", default="gpt-5.6-luna")
    plan.add_argument("--reasoning-effort", default="none", choices=["none", "low", "medium", "high", "xhigh"])
    plan.add_argument("--concurrency", type=int, default=5)
    plan.add_argument("--local-samples", type=int, default=1000)
    plan.add_argument("--timeout", type=float, default=120)
    plan.add_argument("--prompt-addendum", type=Path)
    plan.add_argument("--minimum-quality", type=float, default=dataset_score.DEFAULT_MINIMUM_QUALITY)
    run = commands.add_parser("run", help="generate pending requests, then repair and evaluate once")
    run.add_argument("name")
    run.add_argument("--generation-only", action="store_true")
    run.add_argument("--skip-quality", action="store_true")
    evaluate_parser = commands.add_parser("evaluate", help="new repair/eval pass; generation is never rerun")
    evaluate_parser.add_argument("name")
    evaluate_parser.add_argument("--skip-quality", action="store_true")
    compare = commands.add_parser("report", help="compare trials without API calls")
    compare.add_argument("names", nargs="+")
    cost = commands.add_parser("cost", help="estimate one trial's generation and ten-story Terra judge cost; no API calls")
    cost.add_argument("name")
    cost.add_argument("--generation-output-tokens", type=int, default=4200)
    cost.add_argument("--judge-input-tokens", type=int, default=3950)
    cost.add_argument("--judge-output-tokens", type=int, default=1014)
    commands.add_parser("archive", help="preserve data in an LFS-ready archive").add_argument("name")
    return parser


def evaluation_exit_code(output: Path, *, skip_quality: bool) -> int:
    checks = read(output / "checks.json")
    return int(any(not row["final"]["ok"] or not row["verify"]["ok"] or
                   (not skip_quality and row.get("geometric_score", row.get("weighted_score")) is None) for row in checks))


def main() -> int:
    args = build_parser().parse_args()
    if args.command == "prepare":
        directory = prepare(args)
        config = read(directory / "trial.json")
        print(f"Prepared {len(config['arms']) * config['per_example']} requests: {relative(directory)}. No API calls made.")
    elif args.command == "report":
        print(report(args.names))
    elif args.command == "cost":
        if min(args.generation_output_tokens, args.judge_input_tokens, args.judge_output_tokens) < 1:
            raise ValueError("token estimates must be positive")
        print(json.dumps(budget(args.name, generation_output=args.generation_output_tokens,
                                judge_input=args.judge_input_tokens, judge_output=args.judge_output_tokens), indent=2))
    elif args.command == "archive":
        with trial_lock(trial_path(args.name)):
            print(relative(archive(args.name)))
    else:
        directory, config = load_trial(args.name)
        with trial_lock(directory):
            if args.command == "run":
                asyncio.run(generate(directory, config))
                if args.generation_only:
                    return int(any(read(ROOT / arm["manifest"])["failed"] for arm in config["arms"]))
                if list(directory.glob("eval_*")):
                    print("Existing evaluation retained. Use 'evaluate' explicitly for another paid judge pass.")
                    completed = sorted(directory.glob("eval_*/completed.json"))
                    if not completed:
                        return 1
                    previous = completed[-1].parent
                    return evaluation_exit_code(previous, skip_quality=read(previous / "settings.json")["skip_quality"])
            output = asyncio.run(evaluate(directory, config, skip_quality=args.skip_quality))
            (output / "report.md").write_text(report([args.name]))
            print(f"Wrote {relative(output / 'report.md')}")
            return evaluation_exit_code(output, skip_quality=args.skip_quality)
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (ValueError, FileNotFoundError) as exc:
        raise SystemExit(str(exc)) from exc
