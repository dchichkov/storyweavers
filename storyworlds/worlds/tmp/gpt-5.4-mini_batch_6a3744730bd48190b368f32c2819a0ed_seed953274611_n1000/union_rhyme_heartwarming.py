#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/union_rhyme_heartwarming.py
===========================================================

A tiny heartwarming storyworld about a small union project: two children,
a torn banner, a patient helper, and a cheerful rhyme that helps them join
pieces into something new.

The core premise is simple:
- a little team tries to make a word-banner for a community fair,
- one part falls apart,
- they pause, choose gentle work instead of rushing,
- and they finish with a bright, proud union of pieces.

The story engine is simulated, state-driven, and supports:
- --trace
- --qa
- --json
- --asp
- --verify
- --show-asp
- -n / --all / --seed

The style is meant to stay warm, child-facing, and lightly rhymed.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Task:
    id: str
    thing: str
    place: str
    verb: str
    rhyme: str
    trouble: str
    repaired: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Helper:
    id: str
    label: str
    skill: str
    gentle: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    sense: int
    power: int
    text: str
    tag: str = ""


class World:
    def __init__(self) -> None:
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World()
        clone.entities = {k: _copy_entity(v) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _copy_entity(e: Entity) -> Entity:
    clone = Entity(id=e.id, kind=e.kind, type=e.type, label=e.label, role=e.role, attrs=dict(e.attrs))
    clone.meters = defaultdict(float, dict(e.meters))
    clone.memes = defaultdict(float, dict(e.memes))
    return clone


def rhyme_line(a: str, b: str) -> str:
    return f"{a}, {b}." if not a.endswith((".", "!", "?")) else f"{a} {b}"


def _r_union(world: World) -> list[str]:
    out: list[str] = []
    banner = world.entities.get("banner")
    if banner and banner.meters["torn"] >= THRESHOLD and banner.meters["mended"] >= THRESHOLD:
        sig = ("union",)
        if sig not in world.fired:
            world.fired.add(sig)
            banner.meters["joined"] += 1
            out.append("__union__")
    return out


def _r_smile(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.entities.values():
        if ent.memes["relief"] >= THRESHOLD and ent.id not in {"Mia", "Noah", "Aunt"}:
            sig = ("smile", ent.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            ent.memes["joy"] += 1
            out.append("")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for fn in (_r_union, _r_smile):
            sents = fn(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def brave_tremor(task: Task) -> bool:
    return task.thing in {"banner", "garland", "ribbon"} and task.place in {"hall", "porch", "garden"}


def can_fix(task: Task, fix: Fix) -> bool:
    return fix.power >= (2 if task.thing == "banner" else 1)


def can_join(task: Task, helper: Helper) -> bool:
    return helper.gentle and task.thing == "banner"


def build_scene(world: World, a: Entity, b: Entity, helper: Entity, task: Task) -> None:
    a.memes["hope"] += 1
    b.memes["hope"] += 1
    world.say(
        f"On a bright little morning, {a.id} and {b.id} set out to help at the fair, "
        f"where {task.thing} was waiting by the door."
    )
    world.say(
        f"They meant to make a neat {task.label} for the hall, and the plan felt light as a song."
    )


def trouble_scene(world: World, a: Entity, b: Entity, task: Task) -> None:
    a.memes["care"] += 1
    b.memes["care"] += 1
    world.say(
        f"But when the corner snagged and the {task.thing} tore, the tidy little work went wrong."
    )
    world.say(
        f'"Oh no," said {a.id}. "A seam is weak; we need to think, not rush."'
    )
    world.say(
        f'"We can fix it," said {b.id}, "with steady hands and a gentle touch."'
    )


def gentle_help(world: World, helper: Entity, task: Task) -> None:
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.id} came over with a smile and showed them how to smooth each edge and tuck each fold.'
        .replace(\"'\", \"'\")"
    )


def repair(world: World, fix: Fix, task: Task, a: Entity, b: Entity) -> None:
    banner = world.get("banner")
    banner.meters["mended"] += 1
    world.say(
        f'{a.id} and {b.id} used {fix.label}, and {fix.text}.'
    )
    world.say(
        f'The torn part grew neat and whole, as if a small storm had been told to go home.'
    )


def end_image(world: World, a: Entity, b: Entity, task: Task) -> None:
    for kid in (a, b):
        kid.memes["relief"] += 1
        kid.memes["joy"] += 1
    world.say(
        f"In the end, the banner hung straight and proud, and the word on it shone like a little sun."
    )
    world.say(
        f"{a.id} and {b.id} laughed together, pleased that their union of pieces had made something better than before."
    )


def tell(task: Task, helper: Helper, fix: Fix, a_name: str, a_type: str,
         b_name: str, b_type: str) -> World:
    world = World()
    a = world.add(Entity(id=a_name, kind="character", type=a_type, role="maker"))
    b = world.add(Entity(id=b_name, kind="character", type=b_type, role="maker"))
    h = world.add(Entity(id=helper.id, kind="character", type="mother", label=helper.label, role="helper"))
    banner = world.add(Entity(id="banner", type="thing", label=task.label))
    banner.meters["torn"] = 1
    world.facts.update(task=task, helper=helper, fix=fix, a=a, b=b, banner=banner)

    build_scene(world, a, b, h, task)
    world.para()
    trouble_scene(world, a, b, task)
    world.para()

    if not brave_tremor(task):
        raise StoryError("This task never gets interesting enough for a union story.")
    if not can_join(task, helper):
        raise StoryError("This helper cannot support a warm union story for this task.")
    if not can_fix(task, fix):
        raise StoryError("This fix is too small to mend the torn banner.")

    gentle_help(world, h, task)
    repair(world, fix, task, a, b)
    propagate(world, narrate=True)
    world.para()
    end_image(world, a, b, task)
    banner.meters["joined"] = 1
    world.facts["outcome"] = "joined"
    return world


TASKS = {
    "banner": Task(
        id="banner",
        thing="banner",
        place="hall",
        verb="hang",
        rhyme="glow",
        trouble="torn",
        repaired="joined",
        tags={"union", "rhyme", "heartwarming"},
    ),
    "garland": Task(
        id="garland",
        thing="garland",
        place="porch",
        verb="string",
        rhyme="sparkle",
        trouble="snagged",
        repaired="mended",
        tags={"union", "rhyme", "heartwarming"},
    ),
    "ribbon": Task(
        id="ribbon",
        thing="ribbon",
        place="garden",
        verb="tie",
        rhyme="bright",
        trouble="split",
        repaired="knit",
        tags={"union", "rhyme", "heartwarming"},
    ),
}

HELPERS = {
    "Aunt": Helper(id="Aunt", label="Aunt Lila", skill="steady hands", gentle=True, tags={"helper"}),
    "Mom": Helper(id="Mom", label="Mom", skill="kind patience", gentle=True, tags={"helper"}),
    "Grandma": Helper(id="Grandma", label="Grandma", skill="warm guidance", gentle=True, tags={"helper"}),
}

FIXES = {
    "tape": Fix(id="tape", label="soft tape", sense=3, power=2, text="the edges held, neat and bright"),
    "stitch": Fix(id="stitch", label="a few careful stitches", sense=4, power=3, text="the seam was stitched tight and light"),
    "knot": Fix(id="knot", label="a tidy knot", sense=2, power=2, text="the knot sat snug and did its part"),
}

NAMES_GIRL = ["Mia", "Luna", "Ada", "Nia", "Zoe"]
NAMES_BOY = ["Noah", "Eli", "Ben", "Owen", "Kai"]


@dataclass
class StoryParams:
    task: str
    helper: str
    fix: str
    a_name: str
    a_type: str
    b_name: str
    b_type: str
    seed: Optional[int] = None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for task in TASKS:
        for helper in HELPERS:
            for fix in FIXES:
                if can_join(TASKS[task], HELPERS[helper]) and can_fix(TASKS[task], FIXES[fix]):
                    combos.append((task, helper, fix))
    return combos


KNOWLEDGE = {
    "union": [("What does union mean?",
               "Union means joining parts together so they work as one. It can mean a kind, careful coming-together.")],
    "rhyme": [("What is a rhyme?",
              "A rhyme is when words sound alike at the end, like bright and light.")],
    "banner": [("What is a banner?",
                "A banner is a cloth sign that can hang up and show a message.")],
    "stitch": [("What are stitches for?",
                "Stitches hold torn cloth together so it stays strong.")],
    "tape": [("What does tape do?",
              "Tape sticks things together for a little while or sometimes for a craft project.")],
    "knot": [("What is a knot?",
               "A knot is a tied loop that helps hold string or ribbon in place.")],
}

KNOWLEDGE_ORDER = ["union", "rhyme", "banner", "stitch", "tape", "knot"]


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("sense", fid, f.sense))
        lines.append(asp.fact("power", fid, f.power))
    return "\n".join(lines)


ASP_RULES = r"""
compatible(T,H,F) :- task(T), helper(H), fix(F), T="banner", H="Aunt"; H="Mom"; H="Grandma", F="tape"; F="stitch"; F="knot".
safe_fix(F) :- fix(F), sense(F,S), S >= 2.
valid(T,H,F) :- task(T), helper(H), fix(F), safe_fix(F).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    rc = 0
    if py == cl:
        print(f"OK: ASP matches valid_combos() ({len(py)} combos).")
    else:
        rc = 1
        print("MISMATCH between ASP and Python.")
        if py - cl:
            print("  only in python:", sorted(py - cl))
        if cl - py:
            print("  only in ASP:", sorted(cl - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(task=None, helper=None, fix=None, name1=None, name2=None), random.Random(777)))
        assert sample.story
        print("OK: generate() smoke test passed.")
    except Exception as e:
        rc = 1
        print(f"SMOKE TEST FAILED: {e}")
    return rc


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming union-and-rhyme storyworld.")
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--a-name")
    ap.add_argument("--b-name")
    ap.add_argument("--a-type", choices=["girl", "boy"])
    ap.add_argument("--b-type", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def _pick_name(rng: random.Random, typ: str) -> str:
    return rng.choice(NAMES_GIRL if typ == "girl" else NAMES_BOY)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    task = args.task or rng.choice(list(TASKS))
    helper = args.helper or rng.choice(list(HELPERS))
    fix = args.fix or rng.choice(list(FIXES))
    if task not in TASKS or helper not in HELPERS or fix not in FIXES:
        raise StoryError("Unknown choice for task/helper/fix.")
    if not can_join(TASKS[task], HELPERS[helper]):
        raise StoryError("That helper cannot guide this union story.")
    if not can_fix(TASKS[task], FIXES[fix]):
        raise StoryError("That fix is too small to mend this story.")
    a_type = args.a_type or rng.choice(["girl", "boy"])
    b_type = args.b_type or ("boy" if a_type == "girl" else "girl")
    a_name = args.a_name or _pick_name(rng, a_type)
    b_name = args.b_name or _pick_name(rng, b_type)
    if a_name == b_name:
        b_name = _pick_name(rng, b_type)
    return StoryParams(
        task=task,
        helper=helper,
        fix=fix,
        a_name=a_name,
        a_type=a_type,
        b_name=b_name,
        b_type=b_type,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = f["task"]
    return [
        f'Write a heartwarming rhyme story that uses the word "union" and shows {task.label} being mended with gentle help.',
        f"Tell a warm story for a young child where {f['a'].id} and {f['b'].id} repair a torn {task.thing} and learn about union.",
        f'Create a short story with a soft rhyme feel about a broken {task.thing}, a kind helper, and a happy union of pieces.',
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    f = world.facts
    task: Task = f["task"]
    a: Entity = f["a"]
    b: Entity = f["b"]
    helper: Helper = f["helper"]
    fix: Fix = f["fix"]
    return [
        ("What were the children making?",
         f"They were making a {task.label} for the fair. It needed a gentle repair before it could hang right."),
        ("What went wrong?",
         f"The {task.thing} tore, so the work could not stay neat on its own. The tear made the children slow down and ask for help."),
        ("Who helped them?",
         f"{helper.label} helped them with calm, kind guidance. {helper.skill.capitalize()} made the fix feel easy and safe."),
        ("How did they solve the problem?",
         f"They used {fix.label} and worked together until the torn part was whole again. That was the little union that made the banner strong."),
        ("How did they feel at the end?",
         f"{a.id} and {b.id} felt proud and happy, and their smiles came back bright. The finished piece proved they could make something lovely by staying gentle."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    tags = set(world.facts["task"].tags)
    out: list[tuple[str, str]] = []
    for key in KNOWLEDGE_ORDER:
        if key in tags:
            out.extend(KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    for name, tbl, value in [
        ("task", TASKS, params.task),
        ("helper", HELPERS, params.helper),
        ("fix", FIXES, params.fix),
    ]:
        if value not in tbl:
            raise StoryError(f"Invalid {name}: {value}")
    task = TASKS[params.task]
    helper = HELPERS[params.helper]
    fix = FIXES[params.fix]
    world = tell(task, helper, fix, params.a_name, params.a_type, params.b_name, params.b_type)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(question=q, answer=a) for q, a in story_qa(world)],
        world_qa=[QAItem(question=q, answer=a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


CURATED = [
    StoryParams(task="banner", helper="Mom", fix="stitch", a_name="Mia", a_type="girl", b_name="Noah", b_type="boy"),
    StoryParams(task="garland", helper="Grandma", fix="knot", a_name="Ada", a_type="girl", b_name="Eli", b_type="boy"),
    StoryParams(task="ribbon", helper="Aunt", fix="tape", a_name="Luna", a_type="girl", b_name="Ben", b_type="boy"),
]


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
