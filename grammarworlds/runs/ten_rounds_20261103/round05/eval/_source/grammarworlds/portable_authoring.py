"""Terra authors new worlds against frozen portable grammar contracts."""
from __future__ import annotations

import argparse
import asyncio
import inspect
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

from .authoring_trial import ROOT, MODELS, author_request, call, read, save, digest, quality
from .judge import protocol
from . import world
from .portable.language import load_lexicon
from .portable.catalog import context

DEFAULT_OUT = ROOT / "grammarworlds/runs/terra_portable_worlds_20261103"
SOURCES = {"library": "05_library", "pottery": "11_pottery"}
CONTRACT = """Author one executable world module, not a prewritten story.
Return JSON {design_notes: string, mismatches: string[], code: string}.
Use only standard-library dataclasses/copy/random/math and imports from
grammarworlds.world and grammarworlds.portable.language/features. No I/O,
network, filesystem, eval/exec, runtime LLM, tests or harness imports.
Do not alter shared grammar or runtime. No raw prose Nodes/sentence templates.
Expose LEXICON (dict of NEW entries only), KERNELS (dict of Kernel objects),
make_world(seed=0)->World, candidates(w)->list[(Kernel,Frame)],
plan(w,frame,tense='past')->Sentence, commit(w,frame,sentence)->dict.

World must be a World subclass retaining all inherited fields and methods.
Override facts_for_attention: return grounded Fact objects from current carrier
locations, states, numeric memes and prior events. Base implementation expects
old rescue-world facts, so do not call it. Use Care, Fear, Trust etc on people to
affect event availability or Kernel.preferences, not just fixed ordering.
Frame.cause_ids must name existing facts returned by facts_for_attention.
Record only physical/semantic state; never infer effects by parsing prose.
Every person is kind='person', explicit pronoun and properties={'animate','can_hold'}.
Location can be an entity ID (holder) or a place string. No invisible remote actions.

Build Language(w,tense) in plan, then set g.lexicon to a deep copy of
load_lexicon() merged with LEXICON. Never mutate the shared cached lexicon.
LEXICON has categories nouns/adjectives/prepositions/adverbs/verbs/names; use
dict entries for all categories, no duplicates of supplied vocabulary. Entity
nouns for nonpeople must exist. Names of people need no lexical registration.
Use explicit verb forms [base,past,participle] to avoid heuristic mistakes.
Existing verb valencies cannot be extended by redeclaring a duplicate.
g.ref has keywords subject/first/adjectives; g.s(ref-or-id,VP). g.be(str) means
an adjective, NOT a location (use g.be(g.pp('in',g.n('workshop')))). No arbitrary
English clauses in lexical entries. 'it' is an object pronoun; physical objects
with plural number need pronoun='they'. Use g.sequence/reporting for local
coreference rather than ambiguous bare pronouns. g.either alternatives must
describe the SAME actual event, without inventing actions or states.

candidates and plan must not mutate anything. Each Kernel requires/excludes is
checked in candidates (the runtime does NOT do it). commit rechecks exact Frame
membership, raising ValueError without mutation for forged/stale frames, then
applies effects and Kernel.adds, sets w.focus=frame.actor, records
{id:len(w.history)+1, frame:asdict(frame), sentence:sentence, before:w.snapshot()
BEFORE effects, after:w.snapshot() AFTER effects} and appends it to w.history.
Ended means 'ended' in flags and candidates must then be empty.

Use the original wordwise Forest sampler via plan; do not sample sentences or
events inside the pack. Every seed must finish within 24 events, each event at
most 512 derivations. Aim for 12-20 events / 140-260 words with a clear beginning,
state-driven turn, and physical ending image. Favor joined typed clauses and
specific objects over a bare event log. Initial desires are allowed, initial
resolution/choice/completion is not. Include two meaningful reachable branches
with different actions/state consequences, not only paraphrases/order changes.
Stay faithful to the source's values, while variants may change exact outcomes.
We sample 60 unfiltered seeds in both tenses, replay frames, test physical guard
interventions and inspect prose. This task needs only the provided facade and
rule contracts, not the complete grammar implementation. Keep code compact,
ideally under 400 lines. Report unsupported constructions in mismatches.
"""
DOMAIN = {
    "library": """Required scenario='library'. IDs: hero=Mina, helper=Ms Alvarez,
friend=Jun, book=whale book, atlas=moon atlas, tool=book trolley, ladder=ladder.
Initial all people in 'library', book at 'high_shelf', atlas at 'hero', tool at
'station', ladder at 'store'. Children must never climb/retrieve high books.
The beginning introduces Mina's atlas wish and Jun's missing book before searches.
Before retrieval she explicitly chooses either reserving the atlas (flag
'atlas_reserved') or relinquishing it ('atlas_released'); mutually exclusive
branches, each with a material atlas effect. Released atlas moves to 'display';
reserved atlas stays at 'desk' until later checked out and returned to hero.
Search uses trolley held by hero, both children present, and yields a 'clue'
flag. Borrowing the trolley requires librarian presence. Include a failed
search before finding the clue; don't make failure or success just a paraphrase.
Only kind='retrieve', actor='helper' can move book off high_shelf. Requires
clue, atlas decision, helper and children in library, ladder physically in
'library'. Ladder must first be fetched by helper from store. Retrieve moves
book to helper. kind='checkout', actor='helper' moves book to friend and adds
'checked_out' to book.state; requires book held by helper and friend present.
kind='ending' requires checked-out book at friend, trolley back at station,
ladder back at store, and atlas either released at display or reserved and
checked_out at hero. Finish with a shared reading image, grounded in possession.
No checkout/ending initially. Do not simulate exact wall-clock minutes or claim
a timed deadline check you didn't implement; closing may supply narrative urgency.
""",
    "pottery": """Required scenario='pottery'. IDs: hero=Bea, helper=Mr Ivo,
grandpa=Grandpa Len, cup=cup, tool=shaping rib, sponge=sponge, kiln=kiln.
All people start at 'workshop' (compact adaptation; disclose this simplification).
cup initially at 'bench', state={'wet','thick','stable','wide_handle'};
tool at hero, sponge at bench, kiln at workshop. The rib is borrowed.
The beginning explains Grandpa's grip needs and Bea's gift goal. A later
kind='slip' event with hero holding rib and wet cup at bench adds 'dented'.
No abstract lessons as unembedded noun entities. After inspecting the actual
wall, represent two design branches: retaining the dent as a thumb rest
(flag 'thumb_design', cup.state 'thumb_rest') versus carefully smoothing it
while retaining a useful wide handle ('smooth_design', state 'smoothed').
Each requires thick/stable wet cup and sponge held by hero; mutually exclusive
design flags. Both add 'safe_edges' and 'wall_checked' only after inspection.
Design effects must persist through firing. Prefer thumb design when Care is
high, while both branches remain possible. No magical reset of the damage.
kind='dry' removes wet/adds dry; requires chosen design and wall_checked.
kind='bisque' (helper) requires dry and adds bisque; kind='glaze' requires
bisque and adds glazed; kind='fire' (helper) requires glazed and adds fired.
Heat handling is by helper in workshop with kiln present. Move the cup between
bench and kiln if your events narrate it; never narrate transport without effect.
Only kind='give' may move finished cup to grandpa, after fired, safe_edges,
stable and wide_handle, with both people present. Only kind='use' may add
'tea' to cup.state, after give/fired and held by grandpa. Return rib to helper
and sponge to bench before kind='ending'. Ending requires cup held by grandpa,
tea, fired and branch-appropriate grip; image must differ by the actual design.
Do not drink from wet/unfinished cup. No initial completion/design/tea flags.
""",
}


def prepare(out):
    out.mkdir(parents=True, exist_ok=False)
    api = "\n\n".join(inspect.getsource(x) for x in
                        (world.Entity, world.Fact, world.Frame, world.World, world.Kernel, world.kernel))
    retrieval = context("agreement complement reference coordination possession", budget=4500)
    sources = {"world_api.py": "from __future__ import annotations\nfrom copy import deepcopy\nfrom dataclasses import dataclass, field, asdict\n" + api,
        "AUTHORING.md": (ROOT / "grammarworlds/portable/AUTHORING.md").read_text(),
        "grammar_contracts.txt": retrieval["context"],
        "vocabulary.json": quality.api_requests.compact(load_lexicon())}
    save(out / "shared_context.json", sources)
    save(out / "retrieval.json", retrieval)
    (out / "contract.txt").write_text(CONTRACT)
    save(out / "domains.json", DOMAIN)
    shutil.copyfile(__file__, out / "authoring_runner.py")
    shutil.copyfile(ROOT / "grammarworlds/portable_authoring_check.py", out / "checker.py")
    for scenario, source in SOURCES.items():
        story = ROOT / "storyscenes/design/agents_api_trial_20261024/luna_high_direct_20" / source / "story.txt"
        directory = out / scenario / "round1"
        directory.mkdir(parents=True)
        shutil.copyfile(story, out / scenario / "source_story.txt")
        body = author_request(MODELS["terra"], sources, story.read_text(),
                              contract=CONTRACT + DOMAIN[scenario], gaps=[], max_output_tokens=32000)
        save(directory / "request.json", body)
    save(out / "settings.json", dict(model=MODELS["terra"], tier="flex", reasoning="high",
        scenarios=list(SOURCES), source_selection="library promise/safety and pottery design/material transformation; chosen before output",
        context_characters=sum(map(len, sources.values())), catalog_contracts=retrieval["selected"],
        shared_grammar_sha256=read(ROOT / "grammarworlds/portable/sources/pre_holdout_freeze.json")["sha256"],
        seeds=list(range(60)), tenses=["past", "present"], max_repairs=1))


async def author(out, scenario, round_name):
    directory = out / scenario / round_name
    response = await call(directory)
    bundle = json.loads(quality.final_text(response))
    if set(bundle) != {"design_notes", "mismatches", "code"} or not isinstance(bundle["code"], str):
        raise ValueError("Invalid author bundle")
    save(directory / "bundle.json", bundle)
    (directory / "pack.py").write_text(bundle["code"])
    print(scenario, round_name, response["usage"], flush=True)


def check(out, scenario, round_name):
    directory = out / scenario / round_name
    assert (directory / "pack.py").read_text() == read(directory / "bundle.json")["code"]
    with tempfile.TemporaryDirectory(prefix="portable-author-check-") as temporary:
        isolated = Path(temporary).resolve()
        work = isolated / "work"
        work.mkdir()
        shutil.copytree(ROOT / "grammarworlds", work / "grammarworlds",
                        ignore=shutil.ignore_patterns("runs", "__pycache__"))
        shutil.copyfile(ROOT / "grammarworlds/portable_authoring_check.py", directory / "checker.py")
        shutil.copyfile(directory / "pack.py", work / "pack.py")
        quoted = json.dumps(str(isolated))
        policy = ('(version 1)(allow default)(deny network*)'
            '(deny file-read-data (require-all (require-any (subpath "/Users") (subpath "/Volumes") '
            '(subpath "/private/tmp") (subpath "/private/var/folders")) '
            f'(require-not (subpath {quoted}))))'
            '(deny file-write* (require-all (require-not (subpath "/dev")) '
            f'(require-not (subpath {quoted}))))')
        process = subprocess.run(["/usr/bin/sandbox-exec", "-p", policy,
            str(Path(sys.executable).resolve()), "-I", str(work / "grammarworlds/portable_authoring_check.py"), scenario],
            cwd=work, env=dict(PATH="/usr/bin:/bin", HOME=str(isolated), TMPDIR=str(isolated),
                             PYTHONDONTWRITEBYTECODE="1", PYTHONHASHSEED="777"),
            capture_output=True, text=True, timeout=240)
        save(directory / "check_process.json", dict(returncode=process.returncode, stdout=process.stdout,
                                                    stderr=process.stderr))
        for filename in ("check.json", "stories.jsonl", "samples.md", "word_trace.json"):
            if (work / filename).exists():
                shutil.copyfile(work / filename, directory / filename)
        if process.returncode or not (directory / "check.json").exists():
            raise RuntimeError(process.stderr or process.stdout or "checker failed")
        result = read(directory / "check.json")
        print(scenario, round_name, json.dumps(result), flush=True)
        return result


def repair(out, scenario, feedback):
    original = out / scenario / "round1"
    target = out / scenario / "round2"
    target.mkdir(exist_ok=False)
    body = read(original / "request.json")
    body["input"].append(dict(role="assistant", content=quality.final_text(read(original / "response.json"))))
    body["input"].append(dict(role="user", content="Repair the complete module using this independent checker feedback. "
        "Preserve the original contract, no imports from tests or harness. Return the same JSON schema.\n" + json.dumps(feedback)))
    save(target / "feedback.json", feedback)
    save(target / "request.json", body)


async def run(out):
    # Sequential dispatch deliberately warms the common prefix before world two.
    for scenario in SOURCES:
        await author(out, scenario, "round1")


async def judge(out, scenario, round_name):
    directory = out / scenario / round_name
    checked = read(directory / "check.json")
    if checked["passed"] != checked["requested"] or not checked["both_branches_observed"]:
        raise ValueError("Cannot judge only surviving outputs or silently missing branches")
    target = directory / "judge_luna"
    if not target.exists():
        target.mkdir()
        rows = [r for r in map(json.loads, (directory / "stories.jsonl").read_text().splitlines()) if r["tense"] == "past"]
        item = quality.select_set(scenario + "_portable_pack", rows, 777, count=20)
        body = protocol.request_body(quality, item)
        body.update(model=MODELS["luna"], store=False)
        save(target / "input.json", item)
        save(target / "request.json", body)
        save(target / "selection.json", dict(stories_sha256=digest(directory / "stories.jsonl"),
            seeds=[rows[s["source_index"]]["seed"] for s in item["stories"]],
            source_pool="60 past-tense samples", duplicates_retained=True, author_blinded=True))
    response = await call(target)
    result = protocol.validate(quality, json.loads(quality.final_text(response)), read(target / "input.json"))
    result["response"] = {k: response.get(k) for k in ("model", "service_tier", "status", "usage")}
    save(target / "result.json", result)
    print(scenario, "Luna judge", result["rating"], result["diversity"], flush=True)


def report(out):
    freeze = read(ROOT / "grammarworlds/portable/sources/pre_holdout_freeze.json")
    unchanged = all(digest(ROOT / "grammarworlds/portable" / name) == expected
                    for name, expected in freeze["sha256"].items())
    result = dict(shared_grammar_unchanged=unchanged, worlds={}, requests=[])
    lines = ["# Two Terra-authored portable grammar worlds", "",
        "Terra (`gpt-6.1-terra`, Flex/high) authored library and pottery from two preselected "
        "Luna source stories. Each received one feedback revision. No generated code was manually edited.", "",
        "The shared prefix contains 15,552 characters of public interfaces, vocabulary and 20 retrieved "
        "contracts (the contract retrieval itself is bounded to 4,500 characters). "
        "There is no full grammar-source dump, GF runtime, or LLM at generation time. "
        "World modules remain isolated experimental packs.", "",
        "| World | Kernels | New lexical entries | Checked stories | Guard checks | Texts | Luna quality /9 | Diversity /9 |",
        "| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |"]
    for scenario in SOURCES:
        directory = out / scenario / "round2"
        checked = read(directory / "check.json")
        judged = read(directory / "judge_luna/result.json")
        result["worlds"][scenario] = dict(selected_round="round2", check=checked, judge=judged,
            author_notes=read(directory / "bundle.json")["design_notes"],
            mismatches=read(directory / "bundle.json")["mismatches"])
        lines.append(f"| {scenario} | {checked['kernels']} | {checked['new_lexicon_entries']} | "
            f"{checked['passed']}/{checked['requested']} | {checked['guard_checks']} | {checked['unique_texts']} | "
            f"{judged['rating']['overall']:.2f} | {judged['diversity']['overall']} |")
    lines += ["", "Each checker used seeds 0–59 in past and present, without filtering. "
        "It checks replay, rejected forged/stale frames, prediction purity, physical interventions, "
        "and word/sentence probability agreement through the existing sampler. "
        "Pottery also passes 120 interventions verifying that raising Care increases the thumb-design preference. "
        "These are targeted checks, not a proof of full English-to-world semantic fidelity.", "",
        "Luna judged 20 uniformly selected past-tense positions per world (seed 777), retaining duplicates. "
        "It saw prose only and no author identity. One judge run per world; scores are not a model ranking.", "",
        "## Attempts and cache evidence", "",
        "Library's first attempt passed all 120 structural cases but had repetitive prose, a confusing "
        "pronoun and inactive attention coefficients. Its revision preserves the checks and increases "
        "distinct texts from 30 to 112. Pottery's first attempt failed all 120 at the missing cup-state "
        "wall inspection; review also found wrong entity IDs and inactive attention. Terra repaired these. "
        "The revision checker adds explicit ID and attention checks; both checker versions are retained.", "",
        "| Request | Input | Cached | Cache writes | Output (including reasoning) |",
        "| --- | ---: | ---: | ---: | ---: |"]
    for scenario in SOURCES:
        for round_name in ("round1", "round2"):
            path = out / scenario / round_name / "response.json"
            raw = read(path)
            usage = raw["usage"]
            details = usage["input_tokens_details"]
            row = dict(scenario=scenario, round=round_name, model=raw["model"], tier=raw["service_tier"], usage=usage)
            result["requests"].append(row)
            lines.append(f"| {scenario}/{round_name} | {usage['input_tokens']} | {details['cached_tokens']} | "
                         f"{details['cache_write_tokens']} | {usage['output_tokens']} |")
    lines += ["", "The first request wrote the 4,750-token shared prefix; every subsequent authoring "
        "request reused it with no additional writes. Repairs append prior output and feedback after "
        "the stable boundary. Cache reuse is observed usage, not inferred from configuration.", "",
        "## Limits and next experiment", "",
        "Both worlds support two checked final-state branches, but most text variation is surface wording "
        "or action ordering. Library remains a narrow search-and-retrieval family; pottery remains a mostly "
        "fixed manufacturing sequence. Raw event-path counts do not establish plot diversity.", "",
        "Manual reading still finds event-log prose, repeated names, thin emotional development, "
        "and awkward phrasing such as ‘poured tea from the teapot in the cup’ and nested possessives. "
        "Physical guards alone do not ensure natural storytelling. Library's deadline/grandmother and "
        "pottery's time gaps/home delivery are simplified; see each bundle's mismatches. "
        "Next gate: improve discourse/scene realization and causal alternatives while preserving all "
        "physical checks, then rerun this same blinded judge selection. Shared grammar unchanged: " + str(unchanged) + ".", "",
        "## Artifacts", "",
        "- [Library final pack](library/round2/pack.py) · [unfiltered samples](library/round2/samples.md) · [judge](library/round2/judge_luna/result.json)",
        "- [Pottery final pack](pottery/round2/pack.py) · [unfiltered samples](pottery/round2/samples.md) · [judge](pottery/round2/judge_luna/result.json)",
        "- Both round1 directories retain original responses, code, checks and feedback history.", "",
        "Reproduce local checks (no model calls):", "", "```sh",
        ".venv/bin/python -m grammarworlds.portable_authoring check --scenario library --round round2",
        ".venv/bin/python -m grammarworlds.portable_authoring check --scenario pottery --round round2", "```", ""]
    save(out / "summary.json", result)
    (out / "REPORT.md").write_text("\n".join(lines))
    save(out / "manifest.json", {str(p.relative_to(out)): digest(p) for p in sorted(out.rglob("*"))
                                 if p.is_file() and p.name != "manifest.json"})


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("prepare", "run", "check", "repair", "author", "judge", "report"))
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--scenario", choices=tuple(SOURCES), default="library")
    p.add_argument("--round", default="round1")
    args = p.parse_args()
    if args.command == "prepare": prepare(args.out)
    elif args.command == "run": asyncio.run(run(args.out))
    elif args.command == "author": asyncio.run(author(args.out, args.scenario, args.round))
    elif args.command == "judge": asyncio.run(judge(args.out, args.scenario, args.round))
    elif args.command == "report": report(args.out)
    elif args.command == "check": check(args.out, args.scenario, args.round)
    else: repair(args.out, args.scenario, read(args.out / args.scenario / "round1/check.json"))


if __name__ == "__main__":
    main()
