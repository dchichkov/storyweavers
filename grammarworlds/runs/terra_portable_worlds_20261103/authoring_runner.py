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


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("command", choices=("prepare", "run", "check", "repair", "author"))
    p.add_argument("--out", type=Path, default=DEFAULT_OUT)
    p.add_argument("--scenario", choices=tuple(SOURCES), default="library")
    p.add_argument("--round", default="round1")
    args = p.parse_args()
    if args.command == "prepare": prepare(args.out)
    elif args.command == "run": asyncio.run(run(args.out))
    elif args.command == "author": asyncio.run(author(args.out, args.scenario, args.round))
    elif args.command == "check": check(args.out, args.scenario, args.round)
    else: repair(args.out, args.scenario, read(args.out / args.scenario / "round1/check.json"))


if __name__ == "__main__":
    main()
