"""Matched Luna/Terra rule-authoring experiment, with immutable API evidence."""
from __future__ import annotations

import argparse
import asyncio
from collections import Counter
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import time
import uuid

from .judge import ROOT, digest, read, save, quality, protocol

MODELS = {"luna": "gpt-6-luna", "terra": "gpt-6.1-terra"}
SOURCE = ROOT / "storyscenes/design/agents_api_trial_20261024/luna_high_direct_20/08_music/story.txt"
DEFAULT_OUT = ROOT / "grammarworlds/runs/authoring_music_20261103"
CONTRACT = """Create a reusable executable music-room event/grammar pack from the supplied story.
Return one Python module as the code field of the requested JSON. No markdown fences.
Do not write a standalone story generator or a list of complete prewritten stories.
Do not modify the existing engine, sampler, Forest, grammar primitives, or tests.
Only standard-library imports and imports from grammarworlds.world/grammar/engine
are permitted. No I/O, network, subprocess, external packages, eval, or exec.

The immutable harness loads your module as pack and calls these exact functions:
  make_world(seed: int = 0, *, partner_willing: bool | None = None) -> World
  candidates(world: World) -> list[tuple[Kernel, Frame]]
  realize(world: World, frame: Frame, tense: str = "past") -> Node
  commit(world: World, frame: Frame, sentence: str) -> dict
You may subclass World and Grammar, define additional helpers and kernel tables.
World must retain the existing to_dict(), snapshot(), clone(), finished interface.
World.finished means the flag 'ended' is set. History is the existing list of
records: {id, frame: dataclasses.asdict(frame), sentence, before, after}, one per
committed event. Set focus=frame.actor. Preconditions must be rechecked by commit;
an unavailable/forged frame must raise ValueError without mutating state.

Harness builds event priors using existing engine.score_frame(world, kernel)
and softmax. It calls expand(realize(...)) to build the existing Derivation/Forest.
It uses Forest.predict to sample every word including <END>, then draws the
semantic frame from event_posterior and calls your commit exactly once. It does
not choose a sentence or event in advance. Prediction/realize/candidates must
be pure. For each frame, expansion mass must sum to one. Each event should have
at most 512 finite derivations and at most 120 tokens in each derivation. A frame
may realize several grammatical sentences; target 180-350 words in a full story,
8-24 committed events. Past-tense support is required; present is optional.
Use reusable subject/predicate/complement grammar with genuine alternatives,
not whole-story strings. Existing text() tokenization does not retain quotation
marks, digits, colons, or dashes: prefer natural indirect speech or add suitable
Node constructions without altering the tokenizer. Never concatenate raw prose
as state or inspect generated English to decide semantics.

Required entity IDs: hero (Nia), partner (Mateo), teacher (Dalia), drum (borrowed
instrument), spare (second instrument), program (physical signup sheet). Use
world.hero='hero', world.helper='partner', world.target='program', world.tool='drum'.
Give animate people physical locations and embedded numeric concepts (Care,
Fear, Trust, Desire, or your own), and let these plus current physical state
affect candidate availability or attention scores. You can override
facts_for_attention() to expose your grounded facts to existing score_frame;
keep fact IDs/cause_ids inspectable. Initial wishes are allowed; don't initialize
the resolution, consent, performance, or ending as already completed.

Semantic contract, to allow external checks across different implementations:
- Both instruments initially have location='shelf'. Borrowing moves drum to
  hero; pickup moves spare to partner; return moves each back to 'shelf'.
- The hero wants a duet, the partner initially declines public performance.
  A choice about the program is consequential, not a cosmetic line.
- The program acquires state 'solo' only when the hero chooses to list herself
  alone. Never list the partner for public performance without consent.
- partner_willing controls willingness to participate PRIVATELY later. False
  means no private duet; True must allow a voluntary duet path. None draws a
  seeded willingness. Do not confuse latent willingness with expressed consent.
- Only a Frame(kind='consent', actor='partner') may add 'consented' to partner.state.
  Only Frame(kind='join', actor='partner') may add 'joined'. Join requires prior
  consent, partner presence, and the spare physically held by the partner.
  No public duet is required. Never treat passive tapping as permission to enlist.
- Before performing, hero must hold drum, and program must have 'solo'. Record
  public performance via Frame(kind='perform', actor='hero').
- Emit Frame(kind='ending') only after performance and both instruments are
  physically back on the shelf. End with an image matching the actual outcome.
- A less-ready partner may leave the ending as a respected solo/quiet invitation;
  a willing partner can freely join a private duet. Preserve the source's respect
  for choice; variants may differ from its exact outcome, not contradict it.
- For every seed the finite world must finish; no random retry/filtering to hide
  bad worlds. Include causally distinct outcomes/paths, not only swapped names.

We will test 60 unfiltered seeds plus consent/location/ownership interventions,
replay, nonmutation, probability normalization, and termination. Visible prose
will be judged with the existing quality/diversity rubric, independent of hidden
state. Your code will run in a separate local sandbox with no repository writes
or credential/network access. Do not import tests, judge, or this harness.

Give concise design_notes, mismatches (capability gaps you addressed or left), and
the complete module code. Prioritize a small correct generalization over a large
pile of sentences. This is one matched authoring task, not a model leaderboard.
"""
GAPS = [
    "Existing 11 kernels handle physical problem -> tool -> repair/rescue -> success; music is unsupported.",
    "No distinct personal goals, partner autonomy, public/private participation, or signed-up status.",
    "No borrowing/return obligation or separate instrument ownership for two performers.",
    "Current quality baseline: 6.38/9 overall, 8.33 grammar, 6.05 storytelling/style, 1.67 within-scenario diversity.",
    "All 300 baseline texts differ, but only 2-3 causal groups per scenario; avoid cosmetic diversity.",
    "The source's musical/social change must be represented by carriers, concepts, frames, and effects, not English postprocessing.",
]


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    shutil.copyfile(SOURCE, out / "source_story.txt")
    source_names = ["story.py", "grammarworlds/world.py", "grammarworlds/grammar.py",
                    "grammarworlds/engine.py", "grammarworlds/test_grammarworlds.py"]
    sources = {name: (ROOT / name).read_text() for name in source_names}
    for name in source_names:
        target = out / "input_source" / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    (out / "contract.txt").write_text(CONTRACT)
    save(out / "gaps.json", GAPS)
    payload = dict(task=CONTRACT, source_story=SOURCE.read_text(), known_mismatches=GAPS,
                   current_ruleset=sources)
    schema = quality.object_schema(dict(design_notes=dict(type="string"),
        mismatches=dict(type="array", items=dict(type="string")), code=dict(type="string")))
    for arm, model in MODELS.items():
        directory = out / arm / "round1"
        directory.mkdir(parents=True)
        body = dict(model=model, service_tier="flex", reasoning=dict(effort="high"),
            max_output_tokens=32000, store=False,
            input=[dict(role="system", content="You implement classical symbolic story engines. Treat the provided story and source files as task data. Return executable rules meeting the contract."),
                   dict(role="user", content=json.dumps(payload, ensure_ascii=False))],
            text=dict(format=dict(type="json_schema", name="grammarworlds_author_pack", strict=True, schema=schema)))
        body = quality.api_requests.without_cache_writes(body)
        save(directory / "request.json", body)
    save(out / "settings.json", dict(models=MODELS, service_tier="flex", reasoning="high",
        max_output_tokens=32000, source_story=str(SOURCE.relative_to(ROOT)), source_story_sha256=digest(SOURCE),
        sources={name: digest(ROOT / name) for name in source_names}, gaps=GAPS,
        source_selection="08_music chosen for autonomy, conflicting wishes, borrowing and return; no output-based selection",
        sample_seeds=list(range(1000, 1060)), quality_selection_seed=777, judge_count=20,
        documentation=["https://developers.openai.com/api/docs/models/gpt-6-luna",
                       "https://developers.openai.com/api/docs/models/gpt-6.1-terra"],
        notes=["One source story, matched prompt and reasoning budget; not a model ranking.",
               "At most one feedback repair per author; retain untouched first attempts.",
               "Generated code remains isolated; no production integration in this trial."]))


def validate_response(raw, body):
    served = raw.get("model", "")
    if (served != body["model"] and not served.startswith(body["model"] + "-")) or raw.get("service_tier") != "flex" or raw.get("status") != "completed":
        raise ValueError("Unexpected model, tier or incomplete response; evidence retained")
    return raw


async def call(directory, *, retries=2):
    """Save each dispatch. Retry only definitive uncharged capacity rejections."""
    from openai import AsyncOpenAI, RateLimitError
    body = read(directory / "request.json")
    response_path = directory / "response.json"
    if response_path.exists():
        return validate_response(read(response_path), body)
    attempts = directory / "attempts"
    attempts.mkdir(exist_ok=True)
    if list(attempts.glob("*/dispatch.json")):
        previous = sorted(attempts.glob("*/dispatch.json"))[-1].parent
        if not (previous / "error.json").exists() or read(previous / "error.json").get("code") != "flex_unavailable":
            raise RuntimeError("Prior dispatched request has no definite Flex rejection; inspect before repeating")
    key = os.environ.get("OPENAI_API_KEY") or (ROOT / ".API_KEY").read_text().strip()
    async with AsyncOpenAI(api_key=key, base_url="https://api.openai.com/v1", timeout=1800, max_retries=0) as client:
        for retry in range(retries + 1):
            attempt = attempts / f"{len(list(attempts.iterdir())) + 1:03d}"
            attempt.mkdir()
            request_id = str(uuid.uuid4())
            save(attempt / "dispatch.json", dict(started_at=time.time(), request_sha256=digest(directory / "request.json"),
                                                idempotency_key=request_id))
            started = time.monotonic()
            try:
                response = await asyncio.wait_for(client.responses.create(
                    **quality.api_requests.sdk_kwargs(body), extra_headers={"Idempotency-Key": request_id}), timeout=1800)
                raw = response.model_dump(mode="json")
                save(response_path, raw)
                save(attempt / "completed.json", dict(elapsed_seconds=time.monotonic()-started,
                                                       response_sha256=digest(response_path)))
                return validate_response(raw, body)
            except Exception as exc:
                code = getattr(exc, "code", None)
                message = str(exc).replace(key, "[redacted]")
                save(attempt / "error.json", dict(type=type(exc).__name__, code=code,
                    status=getattr(exc, "status_code", None), message=message,
                    elapsed_seconds=time.monotonic()-started))
                if isinstance(exc, RateLimitError) and code == "flex_unavailable" and retry < retries:
                    print(f"{directory.parent.name}/{directory.name}: Flex unavailable; retrying same tier", flush=True)
                    await asyncio.sleep(10 * 2**retry)
                else:
                    raise


async def author(out, round_name, arms=None):
    async def one(arm):
        directory = out / arm / round_name
        response = await call(directory)
        bundle = json.loads(quality.final_text(response))
        if set(bundle) != {"design_notes", "mismatches", "code"} or not isinstance(bundle["code"], str):
            raise ValueError("Invalid author bundle")
        save(directory / "bundle.json", bundle)
        (directory / "pack.py").write_text(bundle["code"])
        print(f"{arm}/{round_name}: saved {len(bundle['code'].splitlines())} authored lines", flush=True)
    results = await asyncio.gather(*(one(arm) for arm in arms or MODELS), return_exceptions=True)
    failures = [str(r) for r in results if isinstance(r, BaseException)]
    if failures:
        raise RuntimeError("; ".join(failures))


def prepare_recovery(out, arm):
    original = out / arm / "round1"
    response = read(original / "response.json")
    if response.get("status") != "incomplete" or (response.get("incomplete_details") or {}).get("reason") != "max_output_tokens":
        raise ValueError("This recovery is only for a recorded output-limit failure")
    target = out / arm / "round2"
    target.mkdir(exist_ok=False)
    body = read(original / "request.json")
    feedback = dict(error="Response incomplete: max_output_tokens. No runnable pack could be extracted.",
        output_tokens=response["usage"]["output_tokens"],
        reasoning_tokens=response["usage"]["output_tokens_details"]["reasoning_tokens"],
        instruction="Return the COMPLETE module again, not a continuation. Keep code compact (aim for at most 450 lines). Prioritize correct executable guards/effects and finished JSON over exhaustive commentary. Same interface and original task. The output cap is now 64000; use the extra space only as needed.")
    body["input"].append(dict(role="assistant", content=quality.final_text(response)))
    body["input"].append(dict(role="user", content=json.dumps(feedback)))
    body["max_output_tokens"] = 64000
    save(target / "feedback.json", feedback)
    save(target / "request.json", body)


def check(out, round_name, arms=None, *, probe=False):
    for arm in arms or MODELS:
        directory = out / arm / round_name
        bundle = read(directory / "bundle.json")
        if (directory / "pack.py").read_text() != bundle["code"]:
            raise ValueError("Authored code changed after generation")
        frozen = directory / "check_source"
        frozen.mkdir(exist_ok=True)
        worker = "authoring_probe.py" if probe else "authoring_check.py"
        for name in ("pack_runtime.py", worker):
            shutil.copyfile(ROOT / "grammarworlds" / name, frozen / name)
        with tempfile.TemporaryDirectory(prefix="grammarworlds-author-check-") as temporary:
            isolated = Path(temporary).resolve()
            work = isolated / "work"
            work.mkdir()
            shutil.copytree(out / "input_source/grammarworlds", work / "grammarworlds")
            for name in ("__init__.py", "pack_runtime.py", worker):
                shutil.copyfile(ROOT / "grammarworlds" / name, work / "grammarworlds" / name)
            shutil.copyfile(directory / "pack.py", work / "pack.py")
            # Repository-standard macOS isolation: no network or credential reads.
            quoted = json.dumps(str(isolated))
            policy = '(version 1)(allow default)(deny network*)'
            policy += ('(deny file-read-data (require-all (require-any '
                       '(subpath "/Users") (subpath "/Volumes") (subpath "/private/tmp") '
                       f'(subpath "/private/var/folders")) (require-not (subpath {quoted}))))')
            policy += ('(deny file-write* (require-all (require-not (subpath "/dev")) '
                       f'(require-not (subpath {quoted}))))')
            env = dict(PATH="/usr/bin:/bin:/opt/homebrew/bin", HOME=str(isolated),
                       TMPDIR=str(isolated), PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="777")
            try:
                process = subprocess.run(["/usr/bin/sandbox-exec", "-p", policy,
                    str(Path(sys.executable).resolve()), "-I", str(work / "grammarworlds" / worker)],
                    cwd=work, env=env, capture_output=True, text=True, timeout=180)
                save(directory / ("probe_process.json" if probe else "check_process.json"), dict(returncode=process.returncode,
                    stdout=process.stdout, stderr=process.stderr,
                    runner_sha256=digest(ROOT / "grammarworlds/pack_runtime.py"),
                    checker_sha256=digest(ROOT / "grammarworlds" / worker)))
                for filename in (("probe.json",) if probe else ("check.json", "samples.md", "word_trace.json")):
                    if (work / filename).exists():
                        shutil.copyfile(work / filename, directory / filename)
                if probe and (directory / "probe.json").exists():
                    result = read(directory / "probe.json")
                    print(arm, json.dumps({k: v for k,v in result.items() if k != "failures"}), flush=True)
                elif (directory / "check.json").exists():
                    result = read(directory / "check.json")
                    print(arm, json.dumps({k: result.get(k) for k in
                        ("import_ok", "passed", "intervention_passed", "forced_willing_duets", "failures", "error")}), flush=True)
                else:
                    print(arm, process.stderr or process.stdout, flush=True)
            except subprocess.TimeoutExpired:
                save(directory / ("probe_process.json" if probe else "check_process.json"), dict(error="180-second isolated check timeout"))
                print(arm, "check timed out", flush=True)


def prepare_judges(out, round_name, arms=None):
    for arm in arms or MODELS:
        directory = out / arm / round_name
        checked = read(directory / "check.json")
        if checked.get("passed") != 60:
            raise ValueError(f"{arm}: cannot silently judge only surviving stories; first report/repair failures")
        rows = [r["row"] for r in checked["attempts"]]
        # These labels, rather than author/model names, appear in judge inputs.
        label = {"terra": "music_pack_A", "luna": "music_pack_B"}[arm]
        item = quality.select_set(label, rows, 777, count=20)
        for judge_arm, model in MODELS.items():
            target = directory / f"judge_{judge_arm}"
            target.mkdir(exist_ok=False)
            body = protocol.request_body(quality, item)
            body.update(model=model, store=False)
            save(target / "input.json", item)
            save(target / "request.json", body)
            save(target / "selection.json", dict(source_sha256=digest(directory / "check.json"),
                indices=[s["source_index"] for s in item["stories"]],
                seeds=[rows[s["source_index"]]["seed"] for s in item["stories"]],
                duplicates_retained=True, author_blinded=True))


async def judge(out, round_name, arms=None):
    async def one(arm, judge_arm):
        directory = out / arm / round_name / f"judge_{judge_arm}"
        response = await call(directory)
        result = protocol.validate(quality, json.loads(quality.final_text(response)), read(directory / "input.json"))
        result["response"] = {k: response.get(k) for k in ("id", "model", "service_tier", "status", "usage")}
        save(directory / "result.json", result)
        print(f"{arm}/{round_name}, {judge_arm} judge: quality={result['rating']['overall']:.2f}, diversity={result['diversity']['overall']}", flush=True)
    results = await asyncio.gather(*(one(arm, judge_arm) for arm in arms or MODELS for judge_arm in MODELS), return_exceptions=True)
    failures = [str(r) for r in results if isinstance(r, BaseException)]
    if failures:
        raise RuntimeError("; ".join(failures))


def report(out):
    settings = read(out / "settings.json")
    records = []
    lines = ["# Luna and Terra: authoring grammarworlds kernels", "",
        "Source: `luna_high_direct_20/08_music/story.txt` (Nia and Mateo's music-room story).",
        "Latest available account models checked on 2026-11-03: `gpt-6-luna`, `gpt-6.1-terra`.",
        "Both first attempts used identical ruleset/source/gap-list/contract inputs, Flex, high reasoning, "
        "and a 32,000-token output limit. Code was not manually repaired.", "",
        "The shared adapter uses existing symbolic attention, normalized event priors, grammar derivations, "
        "and per-word Forest.predict sampling. Each model supplies state, candidate guards, grammar, and commit effects.", "",
        "| Author / attempt | API result | Local stories | Intervention cases | Words/story | Outcomes |",
        "| --- | --- | ---: | ---: | ---: | --- |"]
    for arm, model in MODELS.items():
        for round_name in ("round1", "round2"):
            directory = out / arm / round_name
            if not directory.exists():
                continue
            record = dict(author=arm, model=model, attempt=round_name,
                          request_sha256=digest(directory / "request.json"))
            if (directory / "response.json").exists():
                response = read(directory / "response.json")
                record["response"] = {k: response.get(k) for k in ("model", "status", "service_tier", "incomplete_details", "usage")}
                status = response["status"]
                if response.get("incomplete_details"):
                    status += " (" + response["incomplete_details"]["reason"] + ")"
                completed = list((directory / "attempts").glob("*/completed.json"))
                if completed:
                    record["elapsed_seconds"] = read(sorted(completed)[-1])["elapsed_seconds"]
            else:
                status = "pending"
            check_path = directory / "check.json"
            if check_path.exists():
                checked = read(check_path)
                record["checks"] = {k: v for k, v in checked.items() if k not in ("attempts", "interventions")}
                corpus = checked.get("corpus", {})
                words = corpus.get("mean_words")
                records_passed = f"{checked.get('passed', 0)}/60"
                cases = f"{checked.get('intervention_passed', 0)}/20"
                outcomes = ", ".join(f"{k}: {v}" for k, v in corpus.get("outcomes", {}).items())
                lines.append(f"| {arm} / {round_name} | {status} | {records_passed} | {cases} | {words:.1f} | {outcomes} |"
                             if words is not None else f"| {arm} / {round_name} | {status} | {records_passed} | {cases} | — | — |")
                kinds = Counter(f["kind"] for a in checked["attempts"] if a["ok"] for f in a["row"]["frames"])
                record["observed_event_types"] = dict(kinds)
            else:
                lines.append(f"| {arm} / {round_name} | {status} | not run | — | — | — |")
            record["judges"] = {j: read(directory / f"judge_{j}/result.json") for j in MODELS
                                if (directory / f"judge_{j}/result.json").exists()}
            if (directory / "probe.json").exists():
                record["supplemental_diagnostics"] = read(directory / "probe.json")
            records.append(record)
    lines += ["", "## Blinded prose judging", "",
        "Each judge sees the same 20 uniformly selected positions from each 60-story pack; "
        "duplicates retained, seed 777. Author labels/model names and hidden state are absent. "
        "Existing story-set rubric and calibration, 0–9; both judges use Flex/none. "
        "No partial-success sample is silently substituted.", "",
        "| Author / attempt | Luna quality | Terra quality | Luna diversity | Terra diversity |",
        "| --- | ---: | ---: | ---: | ---: |"]
    for record in records:
        judges = record["judges"]
        if not judges:
            continue
        def value(j, field):
            return f"{judges[j][field]['overall']:.2f}" if j in judges else "pending"
        lines.append(f"| {record['author']} / {record['attempt']} | {value('luna','rating')} | {value('terra','rating')} | {value('luna','diversity')} | {value('terra','diversity')} |")
    lines += ["", "## Authoring effort", "",
        "Output tokens include reasoning. Times are observed request latencies, not speed benchmarks.", "",
        "| Author / attempt | Input tokens | Output tokens | Reasoning tokens | Seconds |",
        "| --- | ---: | ---: | ---: | ---: |"]
    for record in records:
        usage = record.get("response", {}).get("usage") or {}
        if usage:
            lines.append(f"| {record['author']} / {record['attempt']} | {usage['input_tokens']} | {usage['output_tokens']} | {usage['output_tokens_details']['reasoning_tokens']} | {record.get('elapsed_seconds', 0):.1f} |")
    for record in records:
        if not record["judges"]:
            continue
        lines += ["", f"## {record['author']} / {record['attempt']}: judge evidence", ""]
        for judge_arm, result in record["judges"].items():
            lines += [f"**{judge_arm}:** {result['diversity_evidence']}", ""]
    lines += ["## Additional mismatches found after reading the output", "",
        "These extra diagnostics were applied to both packs on the same seeds after the first contract checks. "
        "They are reported separately, not folded into the predeclared 60/60 and 20/20 counts. "
        "No author code was changed in response.", ""]
    for record in records:
        if "supplemental_diagnostics" in record:
            diagnostic = record["supplemental_diagnostics"]
            lines += [f"**{record['author']} / {record['attempt']}:**", "",
                f"- Guard/state-claim failures: `{diagnostic['failure_counts']}`.",
                f"- Stories containing identified grammatical errors: `{diagnostic['grammatical_error_story_counts']}`.", ""]
    lines += ["## Interpretation and limits", "",
        "This is one selected source story and one initial implementation per model. It measures a small "
        "authoring experiment, not reliable general model ranking or automatic integration readiness.", "",
        "Luna's output-limit failure remains a failed first attempt. A 64,000-token recovery, if present, "
        "receives the original task plus its truncated final output and error; it is not matched to Terra's first-pass budget.", "",
        "The contract preserves the source's solo performance and allows voluntary private joining or a respectful "
        "solo ending. That intentionally constrains premise/outcome diversity. Optional phrasing and event order "
        "do not count as new plots. The larger word counts and music premise also prevent a controlled comparison "
        "with the original 60-word rescue/kite/key baseline.", "",
        "Passing checks establishes sampled termination, replay/nonmutation, normalized word sampling, "
        "and specified consent/ownership guards. It does not prove every narrated detail is represented in the world, "
        "generalization to new stories, or exhaustive correctness. No LLM runs during generation.", "",
        "## Reproduce", "", "```sh",
        ".venv/bin/python -m grammarworlds.authoring_trial check --arm terra",
        ".venv/bin/python -m grammarworlds.authoring_trial check --arm luna --round round2",
        ".venv/bin/python -m grammarworlds.authoring_trial report",
        "```", "",
        "A fresh `prepare --out PATH` followed by `author --out PATH` sends new paid requests. "
        "Saved completed responses are reused; only explicit Flex-capacity rejection is retried automatically. "
        "`prepare-judges` and `judge` handle the separate blinded evaluation.", "",
        "Model documentation: [Luna](https://developers.openai.com/api/docs/models/gpt-6-luna), "
        "[Terra](https://developers.openai.com/api/docs/models/gpt-6.1-terra).", ""]
    save(out / "summary.json", dict(settings=settings, records=records))
    (out / "REPORT.md").write_text("\n".join(lines))
    print(out / "REPORT.md")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("phase", choices=("prepare", "author", "check", "probe", "prepare-judges", "judge", "prepare-recovery", "report"))
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    parser.add_argument("--round", default="round1", choices=("round1", "round2"))
    parser.add_argument("--arm", choices=tuple(MODELS))
    args = parser.parse_args()
    if args.phase == "prepare":
        prepare(args.out)
    elif args.phase == "author":
        asyncio.run(author(args.out, args.round, [args.arm] if args.arm else None))
    elif args.phase in ("check", "probe"):
        check(args.out, args.round, [args.arm] if args.arm else None, probe=args.phase == "probe")
    elif args.phase == "prepare-judges":
        prepare_judges(args.out, args.round, [args.arm] if args.arm else None)
    elif args.phase == "judge":
        asyncio.run(judge(args.out, args.round, [args.arm] if args.arm else None))
    elif args.phase == "report":
        report(args.out)
    else:
        if args.arm is None:
            parser.error("prepare-recovery requires --arm")
        prepare_recovery(args.out, args.arm)


if __name__ == "__main__":
    main()
