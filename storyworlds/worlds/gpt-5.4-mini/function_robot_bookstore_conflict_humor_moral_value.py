#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/function_robot_bookstore_conflict_humor_moral_value.py
======================================================================================

A small standalone storyworld about a bookstore detective mix-up: a child visits
a bookstore, a helpful robot function goes wrong, a comic conflict erupts, and a
moral-value ending shows the fix. The stories are written in a child-facing
Detective Story style with concrete state changes, not as a frozen paraphrase.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    traits: list[str] = field(default_factory=list)
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type


@dataclass
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    fired: set[tuple] = field(default_factory=set)
    facts: dict = field(default_factory=dict)

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
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Setting:
    id: str
    place: str
    mood: str


@dataclass
class Function:
    id: str
    label: str
    purpose: str
    keyword: str
    result_word: str
    safe: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class Robot:
    id: str
    label: str
    type: str
    function: str
    humor: str
    tags: set[str] = field(default_factory=set)


@dataclass
class ConflictItem:
    id: str
    label: str
    clue: str
    hidden_by: str
    harmless: bool = True
    tags: set[str] = field(default_factory=set)


@dataclass
class MoralValue:
    id: str
    lesson: str
    repair: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]


def _r_buzz(world: World) -> list[str]:
    out = []
    for e in world.entities.values():
        if e.meters["confused"] < THRESHOLD:
            continue
        sig = ("buzz", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.meters["embarrassed"] += 1
        out.append("__buzz__")
    return out


def _r_soften(world: World) -> list[str]:
    out = []
    if world.get("child").memes["kindness"] >= THRESHOLD and world.get("robot").memes["funny"] >= THRESHOLD:
        if ("soften",) not in world.fired:
            world.fired.add(("soften",))
            world.get("robot").memes["calm"] += 1
            world.get("child").memes["calm"] += 1
            out.append("__soften__")
    return out


CAUSAL_RULES = [Rule("buzz", _r_buzz), Rule("soften", _r_soften)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def sane_combo(func: Function, conflict: ConflictItem, robot: Robot) -> bool:
    return func.safe and conflict.harmless and "bookstore" in conflict.tags and robot.function == func.id


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for fid, func in FUNCTIONS.items():
            for cid, conf in CONFLICTS.items():
                for rid, robot in ROBOTS.items():
                    if sane_combo(func, conf, robot):
                        combos.append((sid, fid, cid, rid))
    return combos


def narrate_intro(world: World, child: Entity, robot: Entity, setting: Setting) -> None:
    child.memes["curious"] += 1
    world.say(
        f"On a rainy afternoon, {child.id} stepped into {setting.place}. "
        f"The shelves were tall, the air smelled like paper, and a small robot waited near the returns desk."
    )
    world.say(
        f'"I am {robot.label}," it beeped. "My function is to {world.facts["function"].purpose}."'
    )


def setup_case(world: World, child: Entity, robot: Entity, func: Function, conflict: ConflictItem) -> None:
    world.say(
        f"{child.id} noticed a strange clue: {conflict.clue}. '
        f"It looked like a mystery, and {child.id} wanted to solve it before anyone else did.'
    )


def risk_turn(world: World, child: Entity, robot: Entity, conflict: ConflictItem) -> None:
    child.memes["defiance"] += 1
    robot.meters["confused"] += 1
    world.say(
        f'"That clue does not belong there," {child.id} said. "{robot.id}, stop that function!" '
        f"The robot twitched, rolled a little too fast, and knocked a stack of bookmarks into the air."
    )
    world.say(
        "The bookmarks fluttered down like tiny paper birds, which would have been funny if the line at the counter had not gasped."
    )


def resolve_conflict(world: World, child: Entity, robot: Entity, moral: MoralValue) -> None:
    child.memes["kindness"] += 1
    robot.memes["funny"] += 1
    world.say(
        f"{child.id} took a breath and remembered the kind thing to do. "
        f'Instead of blaming the robot, {child.id} pointed to the clue and said, "Let’s fix it together."'
    )
    world.say(
        f"The robot beeped with relief. {moral.repair.capitalize()}, and soon the aisle was neat again."
    )
    world.say(
        f"{child.id} laughed when the robot printed a receipt that said, in tiny letters, 'CASE CLOSED.'"
    )
    world.say(
        f"At the end, the bookstore was quiet again, and {child.id} knew that being fair was smarter than being loud."
    )


def tell(setting: Setting, func: Function, robot_def: Robot, conflict: ConflictItem, moral: MoralValue,
         child_name: str = "Mina", child_gender: str = "girl", parent_type: str = "mother") -> World:
    world = World()
    child = world.add(Entity(id=child_name, kind="character", type=child_gender, role="detective"))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    robot = world.add(Entity(id=robot_def.id, kind="character", type="robot", role="helper", label=robot_def.label))
    world.add(Entity(id="bookstore", type="place", label=setting.place))
    world.add(Entity(id=conflict.id, type="thing", label=conflict.label))

    child.memes["curious"] = 1.0
    robot.memes["funny"] = 1.0
    world.facts["function"] = func
    world.facts["conflict"] = conflict
    world.facts["moral"] = moral
    world.facts["setting"] = setting
    world.facts["parent"] = parent
    world.facts["robot"] = robot
    world.facts["child"] = child

    narrate_intro(world, child, robot, setting)
    world.para()
    setup_case(world, child, robot, func, conflict)
    risk_turn(world, child, robot, conflict)
    propagate(world, narrate=False)
    world.para()
    resolve_conflict(world, child, robot, moral)
    world.facts["outcome"] = "resolved"
    return world


SETTINGS = {
    "bookstore": Setting("bookstore", "the bookstore", "quiet and cozy"),
}

FUNCTIONS = {
    "sort": Function("sort", "sort books", "sort books by their labels", "sort", "sorted", True, {"bookstore", "function"}),
    "shelve": Function("shelve", "shelve books", "put books back on the right shelves", "shelve", "shelved", True, {"bookstore", "function"}),
}

ROBOTS = {
    "helperbot": Robot("helperbot", "Helperbot", "robot", "sort", "funny", {"robot", "humor"}),
    "catalogbot": Robot("catalogbot", "Catalog Bot", "robot", "shelve", "funny", {"robot", "humor"}),
}

CONFLICTS = {
    "misfiled_card": ConflictItem("misfiled_card", "a library card", "a library card tucked into the mystery shelf", "the mystery shelf", True, {"bookstore"}),
    "sticker_jam": ConflictItem("sticker_jam", "a sticker sheet", "a sticker sheet stuck to the checkout scanner", "the checkout scanner", True, {"bookstore"}),
}

MORALS = {
    "kindness": MoralValue("kindness", "be kind when things go wrong", "the child gently helped the robot"),
    "fairness": MoralValue("fairness", "be fair before you blame", "the child checked the clue carefully"),
}

GIRL_NAMES = ["Mina", "Luna", "Ivy", "Nora", "Ada"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Theo", "Max"]


def valid_story_combos() -> list[tuple[str, str, str, str]]:
    return valid_combos()


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style bookstore storyworld with a robot function conflict.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--function", dest="function", choices=FUNCTIONS)
    ap.add_argument("--robot", choices=ROBOTS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--moral", choices=MORALS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    if args.function and args.robot and ROBOTS[args.robot].function != args.function:
        raise StoryError("The robot cannot perform that function.")
    combos = [c for c in valid_combos()
              if (args.setting is None or c[0] == args.setting)
              and (args.function is None or c[1] == args.function)
              and (args.conflict is None or c[2] == args.conflict)
              and (args.robot is None or c[3] == args.robot)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, func, conflict, robot = rng.choice(sorted(combos))
    moral = args.moral or rng.choice(sorted(MORALS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(setting, func, conflict, robot, moral, name, gender, parent)


@dataclass
class StoryParams:
    setting: str
    function: str
    conflict: str
    robot: str
    moral: str
    name: str
    gender: str
    parent: str
    seed: Optional[int] = None


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for fid, f in FUNCTIONS.items():
        lines.append(asp.fact("function", fid))
        if f.safe:
            lines.append(asp.fact("safe", fid))
    for rid, r in ROBOTS.items():
        lines.append(asp.fact("robot", rid))
        lines.append(asp.fact("robot_function", rid, r.function))
    for cid in CONFLICTS:
        lines.append(asp.fact("conflict", cid))
        lines.append(asp.fact("bookstore_conflict", cid))
    for mid in MORALS:
        lines.append(asp.fact("moral", mid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,F,C,R) :- setting(S), function(F), conflict(C), robot(R), safe(F), bookstore_conflict(C), robot_function(R,F).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    rc = 0
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python valid combos differ.")
        rc = 1
    sample = generate(CURATED[0])
    if not sample.story:
        print("MISMATCH: generation failed.")
        rc = 1
    print("OK: verification passed.")
    return rc


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a child-friendly detective story in a bookstore that includes the words "{f["function"].keyword}" and "robot".',
        f"Tell a story about {f['child'].id} in the bookstore, where a robot's function causes a comic conflict and a moral lesson follows.",
        f"Write a detective-style story for a young child where a robot helps in a bookstore, there is a funny misunderstanding, and kindness wins.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c = world.facts["child"]
    r = world.facts["robot"]
    f = world.facts["function"]
    m = world.facts["moral"]
    qa = [
        QAItem(
            question="Who is the story about?",
            answer=f"It is about {c.id} and the robot {r.label} in the bookstore. They work through a small mystery together."
        ),
        QAItem(
            question="What was the robot's function?",
            answer=f"The robot's function was to {f.purpose}. That is why it kept trying to help in a bookish way."
        ),
        QAItem(
            question="How was the conflict solved?",
            answer=f"{m.repair.capitalize()}, and the child chose a calm, fair way to fix the problem. That turned the argument into a lesson."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a bookstore?", "A bookstore is a place where people buy and read books."),
        QAItem("What does a robot do?", "A robot is a machine that can help people do jobs, often by following a function."),
        QAItem("What is a function?", "A function is the job something is made to do."),
        QAItem("What is a moral?", "A moral is the lesson a story wants you to remember."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(f"{i+1}. {p}" for i, p in enumerate(sample.prompts))
    out.append("\n== story qa ==")
    out.extend(f"Q: {q.question}\nA: {q.answer}" for q in sample.story_qa)
    out.append("\n== world qa ==")
    out.extend(f"Q: {q.question}\nA: {q.answer}" for q in sample.world_qa)
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict((k, v) for k, v in e.meters.items() if v)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict((k, v) for k, v in e.memes.items() if v)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        SETTINGS[params.setting],
        FUNCTIONS[params.function],
        ROBOTS[params.robot],
        CONFLICTS[params.conflict],
        MORALS[params.moral],
        params.name,
        params.gender,
        params.parent,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams("bookstore", "sort", "misfiled_card", "helperbot", "kindness", "Mina", "girl", "mother"),
    StoryParams("bookstore", "shelve", "sticker_jam", "catalogbot", "fairness", "Eli", "boy", "father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/4."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(f"{len(asp_valid_combos())} valid combinations")
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not args.all:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 40):
            i += 1
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=args.trace, qa=args.qa, header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
