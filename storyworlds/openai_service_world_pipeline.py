#!/usr/bin/env python3
"""Generate service storyworlds, run evals, and write a Markdown report."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace
from typing import Any

import openai_batch_world_factory as batch_factory
import openai_story_quality
import qa_static_check
import repair_batch_output


ROOT = Path(__file__).resolve().parents[1]
STORYWORLDS_DIR = Path(__file__).resolve().parent
BATCH_DIR = STORYWORLDS_DIR / "batches"
FACTORY = STORYWORLDS_DIR / "openai_service_world_factory.py"
QUALITY = STORYWORLDS_DIR / "openai_story_quality.py"
MANIFEST_RE = re.compile(r"Wrote (?P<path>storyworlds/batches/\S+\.manifest\.json)")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "One-command direct-service storyworld run: generate worlds, run "
            "OpenAI quality ratings, run duplicate/static QA checks, and write "
            "a Markdown report."
        )
    )
    parser.add_argument("-n", "--count", type=int, default=100, help="storyworld count; default: 100")
    parser.add_argument("--seed", type=int, default=None, help="base generation seed")
    parser.add_argument("--model", default=os.environ.get("OPENAI_MODEL", batch_factory.DEFAULT_MODEL))
    parser.add_argument("--base-url", default=os.environ.get("OPENAI_BASE_URL"))
    parser.add_argument("--api-key-env", default="OPENAI_API_KEY")
    parser.add_argument("--reasoning-effort", default=batch_factory.DEFAULT_REASONING_EFFORT)
    parser.add_argument("--max-output-tokens", type=int, default=32000)
    parser.add_argument("--concurrency", type=int, default=5)
    parser.add_argument("--words-per-seed", type=int, default=None)
    parser.add_argument("--features-per-seed", type=int, default=None)
    parser.add_argument(
        "--prompt-addendum",
        type=Path,
        default=None,
        help="optional extra prompt instructions appended to every storyworld request",
    )
    parser.add_argument("--overwrite", action="store_true")
    parser.add_argument("--allow-incomplete", action="store_true")
    parser.add_argument("--target-dir", type=Path, default=None)
    parser.add_argument("--output-dir", type=Path, default=BATCH_DIR)
    parser.add_argument("--quality-batch-size", type=int, default=openai_story_quality.DEFAULT_BATCH_SIZE)
    parser.add_argument("--quality-sample-timeout", type=float, default=openai_story_quality.DEFAULT_SAMPLE_TIMEOUT)
    parser.add_argument("--quality-sample-concurrency", type=int, default=openai_story_quality.DEFAULT_SAMPLE_CONCURRENCY)
    parser.add_argument("--quality-seed", type=int, default=777)
    parser.add_argument("--quality-out", type=Path, default=None)
    parser.add_argument("--qa-variants", type=int, default=3)
    parser.add_argument("--qa-seed", type=int, default=42)
    parser.add_argument("--qa-timeout", type=float, default=30.0)
    parser.add_argument("--qa-top", type=int, default=20)
    parser.add_argument("--report-out", type=Path, default=None)
    parser.add_argument(
        "--repair-failures",
        action="store_true",
        help="apply scripted repairs only to scripts that fail local runnable checks before eval",
    )
    parser.add_argument(
        "--from-manifest",
        type=Path,
        default=None,
        help="skip generation and run eval/report from an existing manifest",
    )
    parser.add_argument("--skip-quality", action="store_true", help="skip OpenAI quality ratings")
    parser.add_argument("--skip-qa-static", action="store_true", help="skip duplicate/static QA check")
    parser.add_argument("--dry-run", action="store_true", help="preview factory request only")
    return parser


def now_stamp() -> str:
    return datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ")


def rel(path: Path | str | None) -> str:
    if path is None:
        return ""
    p = Path(path)
    try:
        return p.resolve().relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def command_text(cmd: list[str]) -> str:
    return " ".join(cmd)


def run_command(cmd: list[str], *, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=ROOT,
        env=env,
        text=True,
        capture_output=True,
    )


def find_manifest(factory_stdout: str, *, seed: int | None, count: int, output_dir: Path) -> Path | None:
    matches = [ROOT / match.group("path") for match in MANIFEST_RE.finditer(factory_stdout)]
    if matches:
        return matches[-1]
    if seed is None:
        pattern = f"storyworld_service_*_n{count}.manifest.json"
    else:
        pattern = f"storyworld_service_*_seed{seed}_n{count}.manifest.json"
    candidates = sorted(output_dir.glob(pattern), key=lambda path: path.stat().st_mtime)
    return candidates[-1] if candidates else None


def load_json(path: Path | None) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}
    return payload if isinstance(payload, dict) else {}


def factory_command(args: argparse.Namespace) -> list[str]:
    cmd = [
        sys.executable,
        str(FACTORY),
        "-n",
        str(args.count),
        "--model",
        args.model,
        "--reasoning-effort",
        args.reasoning_effort,
        "--max-output-tokens",
        str(args.max_output_tokens),
        "--concurrency",
        str(args.concurrency),
        "--output-dir",
        str(args.output_dir),
        "--api-key-env",
        args.api_key_env,
    ]
    if args.seed is not None:
        cmd += ["--seed", str(args.seed)]
    if args.base_url:
        cmd += ["--base-url", args.base_url]
    if args.words_per_seed is not None:
        cmd += ["--words-per-seed", str(args.words_per_seed)]
    if args.features_per_seed is not None:
        cmd += ["--features-per-seed", str(args.features_per_seed)]
    if args.target_dir is not None:
        cmd += ["--target-dir", str(args.target_dir)]
    if args.prompt_addendum is not None:
        cmd += ["--prompt-addendum", str(args.prompt_addendum)]
    if args.overwrite:
        cmd.append("--overwrite")
    if args.allow_incomplete:
        cmd.append("--allow-incomplete")
    if args.dry_run:
        cmd.append("--dry-run")
    return cmd


def service_prompt(job: dict[str, Any], args: argparse.Namespace) -> str:
    story_job_fields = batch_factory.StoryworldJob.__dataclass_fields__
    story_job = batch_factory.StoryworldJob(
        **{key: value for key, value in job.items() if key in story_job_fields}
    )
    addendum_path = args.prompt_addendum
    if addendum_path is None and isinstance(job.get("prompt_addendum"), str):
        addendum_path = Path(str(job["prompt_addendum"]))
    prompt = batch_factory.build_storyworld_prompt(
        story_job,
        prompt_addendum=addendum_path,
    )
    return prompt


def write_prompt_files(manifest_path: Path, manifest: dict[str, Any], args: argparse.Namespace) -> dict[str, Path]:
    stem = manifest_path.name.removesuffix(".manifest.json")
    prompt_dir = manifest_path.with_name(f"{stem}.prompts")
    prompt_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    for job in manifest.get("jobs", []):
        if not isinstance(job, dict) or not isinstance(job.get("name"), str):
            continue
        path = prompt_dir / f"{job['name']}.prompt.md"
        path.write_text(service_prompt(job, args), encoding="utf-8")
        if isinstance(job.get("custom_id"), str):
            out[job["custom_id"]] = path
    return out


def sample_env() -> dict[str, str]:
    env = os.environ.copy()
    existing = env.get("PYTHONPATH")
    parts = [str(STORYWORLDS_DIR)]
    if existing:
        parts.append(existing)
    env["PYTHONPATH"] = os.pathsep.join(parts)
    return env


def parse_json_story(raw: str) -> str | None:
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(payload, list):
        payload = next((item for item in payload if isinstance(item, dict)), {})
    if isinstance(payload, dict) and isinstance(payload.get("story"), str):
        return payload["story"].strip()
    return None


def sample_one_story(script: Path, seed: int, timeout: float) -> tuple[bool, str]:
    cmd = [sys.executable, str(script), "--json", "--seed", str(seed)]
    last_error = ""
    for attempt in range(3):
        try:
            proc = subprocess.run(
                cmd,
                cwd=ROOT,
                env=sample_env(),
                text=True,
                capture_output=True,
                timeout=timeout,
            )
        except subprocess.TimeoutExpired:
            return False, f"timed out after {timeout:g}s"
        except OSError as exc:
            last_error = str(exc)
            if getattr(exc, "errno", None) == 35 and attempt < 2:
                continue
            return False, last_error
        if proc.returncode:
            return False, proc.stderr.strip() or f"returncode={proc.returncode}"
        story = parse_json_story(proc.stdout)
        if story:
            return True, story
        return False, "missing_story_or_invalid_json"
    return False, last_error or "unknown_error"


def probe_script(script: Path, *, seed: int, variants: int, timeout: float) -> tuple[bool, str]:
    compile_cmd = [sys.executable, "-m", "py_compile", str(script)]
    proc = None
    for attempt in range(3):
        try:
            proc = subprocess.run(
                compile_cmd,
                cwd=ROOT,
                env=sample_env(),
                text=True,
                capture_output=True,
            )
            break
        except OSError as exc:
            if getattr(exc, "errno", None) == 35 and attempt < 2:
                time.sleep(0.25 * (attempt + 1))
                continue
            return False, str(exc)
    if proc is None:
        return False, "py_compile did not run"
    if proc.returncode:
        return False, proc.stderr.strip() or proc.stdout.strip() or "py_compile failed"

    run_cmd = [
        sys.executable,
        str(script),
        "-n",
        str(variants),
        "--seed",
        str(seed),
        "--json",
    ]
    proc = None
    for attempt in range(3):
        try:
            proc = subprocess.run(
                run_cmd,
                cwd=ROOT,
                env=sample_env(),
                text=True,
                capture_output=True,
                timeout=timeout,
            )
            break
        except subprocess.TimeoutExpired:
            return False, f"timed out after {timeout:g}s: {' '.join(run_cmd)}"
        except OSError as exc:
            if getattr(exc, "errno", None) == 35 and attempt < 2:
                time.sleep(0.25 * (attempt + 1))
                continue
            return False, str(exc)
    if proc is None:
        return False, "sample command did not run"
    if proc.returncode:
        return False, proc.stderr.strip() or proc.stdout.strip() or f"returncode={proc.returncode}"
    try:
        payload = qa_static_check.parse_json_samples(proc.stdout)
    except json.JSONDecodeError as exc:
        return False, f"invalid JSON: {exc}"
    if len(payload) < 1:
        return False, "no JSON story samples"
    return True, "ok"


def repair_failures(manifest: dict[str, Any], args: argparse.Namespace) -> list[str]:
    if not args.repair_failures:
        return []
    print("Running scripted repair pass over locally failing scripts", flush=True)
    log: list[str] = []
    for job in manifest.get("jobs", []):
        if not isinstance(job, dict) or not isinstance(job.get("target"), str):
            continue
        name = str(job.get("name") or job["target"])
        path = ROOT / str(job["target"])
        ok, detail = probe_script(
            path,
            seed=args.quality_seed,
            variants=max(1, args.qa_variants),
            timeout=args.qa_timeout,
        )
        if ok:
            continue
        source = path.read_text(encoding="utf-8")
        repaired, changes = repair_batch_output.repair_source(source)
        if not changes:
            line = f"- {name}: failed: no scripted repair matched: {detail.splitlines()[0] if detail else detail}"
            log.append(line)
            print(line, flush=True)
            continue
        path.write_text(repaired.rstrip() + "\n", encoding="utf-8")
        repaired_ok, repaired_detail = probe_script(
            path,
            seed=args.quality_seed,
            variants=max(1, args.qa_variants),
            timeout=args.qa_timeout,
        )
        status = "ok" if repaired_ok else "failed"
        final_detail = "ok" if repaired_ok else (repaired_detail.splitlines()[0] if repaired_detail else repaired_detail)
        if not repaired_ok:
            path.write_text(source.rstrip() + "\n", encoding="utf-8")
            final_detail = f"{final_detail}; rolled back"
        line = f"- {name}: {status}: {', '.join(changes)}; {final_detail}"
        log.append(line)
        print(line, flush=True)
    if not log:
        log.append("scripted repair: no failing scripts")
    return log


def write_story_files(manifest_path: Path, manifest: dict[str, Any], args: argparse.Namespace) -> dict[str, Path]:
    stem = manifest_path.name.removesuffix(".manifest.json")
    story_dir = manifest_path.with_name(f"{stem}.stories")
    story_dir.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    for index, job in enumerate(manifest.get("jobs", [])):
        if not isinstance(job, dict):
            continue
        custom_id = job.get("custom_id")
        target = job.get("target")
        name = job.get("name")
        if not isinstance(custom_id, str) or not isinstance(target, str) or not isinstance(name, str):
            continue
        ok, text = sample_one_story(ROOT / target, args.quality_seed + index, args.quality_sample_timeout)
        suffix = "story.md" if ok else "error.txt"
        path = story_dir / f"{name}.{suffix}"
        if ok:
            path.write_text(f"# {name}\n\n{text}\n", encoding="utf-8")
        else:
            path.write_text(text.rstrip() + "\n", encoding="utf-8")
        out[custom_id] = path
    return out


def quality_paths(manifest_path: Path, args: argparse.Namespace) -> tuple[Path, Path]:
    if args.quality_out is not None:
        quality_out = args.quality_out
    else:
        stem = manifest_path.name.removesuffix(".manifest.json")
        quality_out = BATCH_DIR / f"{stem}.quality.jsonl"
    summary_out = quality_out.with_suffix(".summary.json") if quality_out.suffix == ".jsonl" else quality_out.with_name(f"{quality_out.name}.summary.json")
    return quality_out, summary_out


def quality_command(manifest_path: Path, quality_out: Path, summary_out: Path, args: argparse.Namespace) -> list[str]:
    cmd = [
        sys.executable,
        str(QUALITY),
        "--manifest",
        str(manifest_path),
        "--limit",
        str(args.count),
        "--batch-size",
        str(args.quality_batch_size),
        "--sample-timeout",
        str(args.quality_sample_timeout),
        "--sample-concurrency",
        str(args.quality_sample_concurrency),
        "--seed",
        str(args.quality_seed),
        "--model",
        args.model,
        "--out",
        str(quality_out),
        "--summary-out",
        str(summary_out),
        "--api-key-env",
        args.api_key_env,
    ]
    if args.base_url:
        cmd += ["--base-url", args.base_url]
    return cmd


def run_qa_static(worlds_dir: Path, args: argparse.Namespace) -> tuple[qa_static_check.CheckResult, str]:
    check_args = SimpleNamespace(
        worlds_dir=worlds_dir,
        include_tmp=False,
        recursive=False,
        count=args.count,
        seed=args.qa_seed,
        allow_repeat=False,
        variants=args.qa_variants,
        timeout=args.qa_timeout,
        python=sys.executable,
    )
    result = qa_static_check.build_result(check_args)
    qa_static_check.attach_source_hits(result)
    lines: list[str] = []
    total_samples = sum(run.samples for run in result.runs)
    lines.append(
        f"Sampled {len(result.runs)} world script(s), {total_samples} generated sample(s). "
        f"Duplicate story QA pair groups: {len(result.duplicates)}."
    )
    if result.failures:
        lines.append("Run failures:")
        for path, code, stderr in result.failures[: args.qa_top]:
            first = stderr.splitlines()[0] if stderr else "(no stderr)"
            lines.append(f"- {qa_static_check.display_path(path)}: rc={code}: {first}")
    if result.duplicates:
        lines.append("Duplicate QA groups:")
        ranked = sorted(
            result.duplicates.items(),
            key=lambda item: (-len(item[1]), item[1][0].question),
        )
        for index, (key, occs) in enumerate(ranked[: args.qa_top], 1):
            first = occs[0]
            lines.append(f"{index}. seen {len(occs)} times")
            lines.append(f"   Q: {first.question}")
            lines.append(f"   A: {first.answer}")
            hits = result.source_hits.get(key, [])
            for hit in sorted(hits, key=lambda h: (qa_static_check.display_path(h.path), h.line))[:3]:
                lines.append(f"   - {qa_static_check.display_path(hit.path)}:{hit.line}: {hit.snippet}")
    return result, "\n".join(lines)


def summarize_quality(summary: dict[str, Any]) -> list[str]:
    if not summary:
        return ["Quality summary was not produced."]
    lines = [
        f"Rows: {summary.get('rows', 0)}; ok: {summary.get('ok', 0)}; failed: {summary.get('failed', 0)}.",
    ]
    averages = summary.get("averages") or {}
    if isinstance(averages, dict) and averages:
        order = ("coherence", "style", "grammar", "storytelling", "overall")
        score_bits = [f"{key}={averages.get(key)}" for key in order]
        lines.append("Averages: " + ", ".join(score_bits) + ".")
    errors = summary.get("error_counts") or {}
    if errors:
        lines.append("Errors: " + ", ".join(f"{k}={v}" for k, v in errors.items()) + ".")
    return lines


def render_report(
    *,
    args: argparse.Namespace,
    report_path: Path,
    factory_cmd: list[str],
    factory_proc: subprocess.CompletedProcess[str],
    manifest_path: Path | None,
    manifest: dict[str, Any],
    prompt_files: dict[str, Path],
    story_files: dict[str, Path],
    quality_cmd: list[str] | None,
    quality_proc: subprocess.CompletedProcess[str] | None,
    quality_out_path: Path | None,
    quality_summary_path: Path | None,
    quality_summary: dict[str, Any],
    qa_result: qa_static_check.CheckResult | None,
    qa_text: str,
    repair_log: list[str],
) -> str:
    target_dir = Path(manifest["target_dir"]) if manifest.get("target_dir") else None
    response_jsonl = ROOT / manifest["response_jsonl"] if manifest.get("response_jsonl") else None
    jobs = manifest.get("jobs") if isinstance(manifest.get("jobs"), list) else []
    generated_ok = manifest.get("ok", 0)
    generated_failed = manifest.get("failed", 0)
    quality_ok = quality_summary.get("ok") if quality_summary else None
    qa_failures = len(qa_result.failures) if qa_result else None
    qa_duplicates = len(qa_result.duplicates) if qa_result else None

    lines = [
        f"# Storyworld Service Run Report",
        "",
        f"Generated at: {now_stamp()}",
        "",
        "## Summary",
        "",
        f"- Model: `{args.model}`",
        f"- Requested worlds: {args.count}",
        f"- Generated worlds: {generated_ok}/{len(jobs) or args.count}",
        f"- Generation failures: {generated_failed}",
        f"- Repair log lines: {len(repair_log)}",
        f"- Quality-rated stories: {quality_ok if quality_ok is not None else 'skipped'}",
        f"- QA static run failures: {qa_failures if qa_failures is not None else 'skipped'}",
        f"- Duplicate story-QA groups: {qa_duplicates if qa_duplicates is not None else 'skipped'}",
        "",
        "## Artifacts",
        "",
    ]
    if manifest_path:
        lines.append(f"- Manifest: `{rel(manifest_path)}`")
    if response_jsonl:
        lines.append(f"- Raw service responses: `{rel(response_jsonl)}`")
    if target_dir:
        lines.append(f"- World directory: `{rel(ROOT / target_dir)}`")
    if quality_summary_path:
        lines.append(f"- Quality summary: `{rel(quality_summary_path)}`")
    if quality_out_path and quality_out_path.exists():
        lines.append(f"- Quality rows: `{rel(quality_out_path)}`")
    if prompt_files:
        first_prompt_dir = next(iter(prompt_files.values())).parent
        lines.append(f"- Prompt files: `{rel(first_prompt_dir)}`")
    if story_files:
        first_story_dir = next(iter(story_files.values())).parent
        lines.append(f"- Story sample files: `{rel(first_story_dir)}`")
    lines.append(f"- Report: `{rel(report_path)}`")

    if jobs:
        lines += ["", "## Produced Files", ""]
        lines.append("| # | Script | Prompt | Story Sample | Seed |")
        lines.append("|---:|---|---|---|---:|")
        for index, job in enumerate(jobs, 1):
            if not isinstance(job, dict):
                continue
            custom_id = str(job.get("custom_id") or "")
            target = job.get("target")
            name = str(job.get("name") or f"job-{index}")
            script_link = f"[{name}]({rel(ROOT / str(target))})" if isinstance(target, str) else name
            prompt_path = prompt_files.get(custom_id)
            story_path = story_files.get(custom_id)
            prompt_link = f"[prompt]({rel(prompt_path)})" if prompt_path else ""
            story_label = "story" if story_path and story_path.suffix == ".md" else "error"
            story_link = f"[{story_label}]({rel(story_path)})" if story_path else ""
            lines.append(
                f"| {index} | {script_link} | {prompt_link} | {story_link} | {job.get('seed', '')} |"
            )

    lines += [
        "",
        "## Repair",
        "",
    ]
    if repair_log:
        lines.append("```text")
        lines.extend(repair_log)
        lines.append("```")
    else:
        lines.append("Skipped.")

    lines += [
        "",
        "## Commands",
        "",
        "```bash",
        command_text(factory_cmd),
        "```",
        "",
    ]
    if quality_cmd is not None:
        lines += ["```bash", command_text(quality_cmd), "```", ""]
    if target_dir and not args.skip_qa_static:
        lines += [
            "```bash",
            (
                f"{sys.executable} {STORYWORLDS_DIR / 'qa_static_check.py'} "
                f"--worlds-dir {ROOT / target_dir} -n {args.count} "
                f"--variants {args.qa_variants} --seed {args.qa_seed} --timeout {args.qa_timeout:g}"
            ),
            "```",
            "",
        ]

    lines += ["## Quality", ""]
    lines.extend(summarize_quality(quality_summary))
    if quality_proc is not None and quality_proc.returncode != 0:
        lines.append(f"Quality command exit code: {quality_proc.returncode}.")
    lines += ["", "## Duplicate / Static QA", ""]
    lines.append("```text")
    lines.append(qa_text or "Skipped.")
    lines.append("```")
    lines += ["", "## Generation Log", ""]
    lines.append(f"Factory exit code: {factory_proc.returncode}.")
    lines.append("```text")
    lines.append((factory_proc.stdout or "").strip() or "(no stdout)")
    if factory_proc.stderr.strip():
        lines.append("\n[stderr]\n" + factory_proc.stderr.strip())
    lines.append("```")
    return "\n".join(lines) + "\n"


def main() -> int:
    args = build_parser().parse_args()
    output_dir = args.output_dir if args.output_dir.is_absolute() else ROOT / args.output_dir

    factory_cmd = factory_command(args)
    if args.from_manifest is not None:
        manifest_path = args.from_manifest if args.from_manifest.is_absolute() else ROOT / args.from_manifest
        factory_proc = subprocess.CompletedProcess(factory_cmd, 0, stdout="(generation skipped: --from-manifest)\n", stderr="")
    else:
        print(f"Running generation: {command_text(factory_cmd)}", flush=True)
        factory_proc = run_command(factory_cmd)
        print(factory_proc.stdout, end="")
        if factory_proc.stderr:
            print(factory_proc.stderr, end="", file=sys.stderr)
        manifest_path = find_manifest(
            factory_proc.stdout,
            seed=args.seed,
            count=args.count,
            output_dir=output_dir,
        )
    manifest = load_json(manifest_path)
    if args.dry_run:
        return factory_proc.returncode
    if manifest_path is None or not manifest:
        raise SystemExit("Generation did not produce a readable manifest; cannot run eval report.")
    if args.prompt_addendum is None and isinstance(manifest.get("prompt_addendum"), str):
        args.prompt_addendum = Path(str(manifest["prompt_addendum"]))

    report_path = args.report_out
    if report_path is None:
        report_path = manifest_path.with_name(f"{manifest_path.name.removesuffix('.manifest.json')}.report.md")
    if not report_path.is_absolute():
        report_path = ROOT / report_path

    repair_log = repair_failures(manifest, args)

    prompt_files = write_prompt_files(manifest_path, manifest, args)
    story_files = write_story_files(manifest_path, manifest, args)

    quality_proc: subprocess.CompletedProcess[str] | None = None
    quality_out: Path | None = None
    quality_summary_path: Path | None = None
    quality_summary: dict[str, Any] = {}
    quality_cmd: list[str] | None = None
    if not args.skip_quality:
        quality_out, quality_summary_path = quality_paths(manifest_path, args)
        quality_cmd = quality_command(manifest_path, quality_out, quality_summary_path, args)
        print(f"Running quality eval: {command_text(quality_cmd)}", flush=True)
        quality_proc = run_command(quality_cmd)
        print(quality_proc.stdout, end="")
        if quality_proc.stderr:
            print(quality_proc.stderr, end="", file=sys.stderr)
        quality_summary = load_json(quality_summary_path)

    qa_result: qa_static_check.CheckResult | None = None
    qa_text = ""
    if not args.skip_qa_static:
        worlds_dir = ROOT / manifest["target_dir"]
        print(f"Running duplicate/static QA check over {worlds_dir}", flush=True)
        qa_result, qa_text = run_qa_static(worlds_dir, args)
        print(qa_text)

    report = render_report(
        args=args,
        report_path=report_path,
        factory_cmd=factory_cmd,
        factory_proc=factory_proc,
        manifest_path=manifest_path,
        manifest=manifest,
        prompt_files=prompt_files,
        story_files=story_files,
        quality_cmd=quality_cmd,
        quality_proc=quality_proc,
        quality_out_path=quality_out,
        quality_summary_path=quality_summary_path,
        quality_summary=quality_summary,
        qa_result=qa_result,
        qa_text=qa_text,
        repair_log=repair_log,
    )
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(report, encoding="utf-8")
    print(f"Wrote report {rel(report_path)}")

    if factory_proc.returncode != 0:
        return factory_proc.returncode
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
