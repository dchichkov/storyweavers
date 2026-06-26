#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/loom_spine_problem_solving_kindness_moral_value.py
========================================================================================================

A small storyworld about a child, a loom, a sore spine, and a kind fix.

The seed tale behind this world:
---
A child notices that the family loom has tangled threads, and a grandparent's
spine aches. Instead of giving up, the child asks for help, tidies the loom,
and weaves a soft wrap. Kindness makes the problem easier, and the ending proves
the repair mattered.

This world keeps the prose child-facing and rhythmic, with a gentle rhyme-like
cadence, while still driving narration from state changes in the simulation.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


@dataclass
class Person:
    id: str
    kind: str = "character"
    type: str = "child"
    label: str = ""
    traits: list[str] = field(default_factory=list)
    meters: dict[str, float] = field(default_factory=lambda: {"help": 0.0, "care": 0.0, "mess": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"kindness": 0.0, "worry": 0.0, "joy": 0.0})
    holds: list[str] = field(default_factory=list)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class ObjectThing:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    broken: bool = False
    repaired: bool = False
    meters: dict[str, float] = field(default_factory=lambda: {"tangled": 0.0, "soft": 0.0, "clean": 0.0})
    memes: dict[str, float] = field(default_factory=lambda: {"value": 0.0})


@dataclass
class Setting:
    place: str
    mood: str
    kind: str = "home"


@dataclass
class StoryParams:
    setting: str
    child: str
    elder: str
    item: str
    problem: str
    helper: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, object] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[str] = set()

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
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
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "attic": Setting(place="the attic", mood="dusty"),
    "workroom": Setting(place="the workroom", mood="busy"),
    "sunroom": Setting(place="the sunroom", mood="bright"),
}

CHILDREN = ["Mina", "Noor", "Toby", "Iris", "Levi", "Pia"]
ELDERS = ["Grandma", "Grandpa", "Auntie", "Uncle"]
HELPERS = ["friend", "neighbor", "sibling"]

ITEMS = {
    "loom": {"label": "loom", "phrase": "the old wooden loom", "problem": "tangled threads"},
    "spine_wrap": {"label": "soft wrap", "phrase": "a soft wrap for a sore spine", "problem": "aching spine"},
}

PROBLEMS = {
    "tangle": "tangled threads",
    "ache": "aching spine",
}

ASP_RULES = r"""
problem(loom_tangle) :- tangled(loom).
problem(spine_ache) :- aching(spine).
needs_help(loom_tangle) :- problem(loom_tangle).
needs_help(spine_ache) :- problem(spine_ache).
kind_fix(loom_tangle) :- help(_), tidy(_).
kind_fix(spine_ache) :- care(_), wrap(_).
happy_end :- kind_fix(loom_tangle), kind_fix(spine_ache).
#show problem/1.
#show needs_help/1.
#show kind_fix/1.
#show happy_end/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join(
        [
            asp.fact("tangled", "loom"),
            asp.fact("aching", "spine"),
            asp.fact("help", "child"),
            asp.fact("care", "child"),
            asp.fact("tidy", "child"),
            asp.fact("wrap", "child"),
        ]
    )


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    atoms = set((s.name, len(s.arguments)) for s in model)
    ok = ("happy_end", 0) in atoms
    if ok:
        print("OK: ASP rules derive the happy ending.")
        return 0
    print("MISMATCH: ASP rules failed to derive the happy ending.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about a loom, a spine, and a kind fix.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--child", choices=CHILDREN)
    ap.add_argument("--elder", choices=ELDERS)
    ap.add_argument("--item", choices=list(ITEMS))
    ap.add_argument("--problem", choices=list(PROBLEMS))
    ap.add_argument("--helper", choices=HELPERS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = args.setting or rng.choice(list(SETTINGS))
    item = args.item or rng.choice(list(ITEMS))
    problem = args.problem or ("tangle" if item == "loom" else "ache")
    if item == "loom" and problem != "tangle":
        raise StoryError("The loom story needs tangled threads.")
    if item != "loom" and problem != "ache":
        raise StoryError("The spine story needs an aching spine.")
    return StoryParams(
        setting=setting,
        child=args.child or rng.choice(CHILDREN),
        elder=args.elder or rng.choice(ELDERS),
        item=item,
        problem=problem,
        helper=args.helper or rng.choice(HELPERS),
    )


def _add_story_beat(world: World, text: str) -> None:
    world.say(text)


def generate(params: StoryParams) -> StorySample:
    setting = SETTINGS[params.setting]
    world = World(setting)
    child = world.add(Person(id=params.child, type="child", traits=["kind", "curious"]))
    elder = world.add(Person(id=params.elder, type="elder", traits=["gentle", "wise"]))
    helper = world.add(Person(id=params.helper, type="helper", traits=["helpful"]))

    item_data = ITEMS[params.item]
    thing = world.add(ObjectThing(
        id=params.item,
        type=params.item,
        label=item_data["label"],
        phrase=item_data["phrase"],
        owner=elder.id,
        caretaker=elder.id,
        location=setting.place,
    ))
    if params.problem == "tangle":
        thing.meters["tangled"] = 1.0
        child.memes["worry"] += 1
    else:
        thing.meters["soft"] = 1.0
        elder.memes["worry"] += 1

    world.facts.update(child=child, elder=elder, helper=helper, thing=thing, params=params)

    world.say(f"In {setting.place}, the day was {setting.mood} and mild, with a hum and a smile.")
    world.say(f"{child.id} saw {thing.phrase} and knew a snag could make the room feel quite sad.")
    world.say(f"One kind little note in the air said, \"If we think, we can mend it with care.\"")

    world.para()
    if params.problem == "tangle":
        _add_story_beat(world, f"The loom had tangled threads that would not sing; they looped and they loped and refused to lean.")
        _add_story_beat(world, f"{child.id} did not pout or push away; {child.pronoun('subject').capitalize()} asked for help right away.")
        child.memes["kindness"] += 1
        child.meters["help"] += 1
        _add_story_beat(world, f"Together they picked each knot with a gentle grip, and the messy thread gave way with a little flip.")
        thing.broken = False
        thing.repaired = True
        thing.meters["tangled"] = 0.0
        thing.meters["clean"] = 1.0
    else:
        _add_story_beat(world, f"{elder.id}'s spine ached low, so slow, so sore; each bend felt heavy, more and more.")
        _add_story_beat(world, f"{child.id} brought a soft wrap, warm and light, and offered it kindly to make things right.")
        child.memes["kindness"] += 1
        child.meters["care"] += 1
        thing.repaired = True
        thing.meters["soft"] = 1.0
        child.memes["joy"] += 1

    world.para()
    _add_story_beat(world, f"{helper.id} joined in with a steady cheer: \"A small good act can brighten the year.\"")
    _add_story_beat(world, f"The fix was simple, the lesson was grand: kind hands and wise hearts go hand in hand.")
    _add_story_beat(world, f"By the end, the {thing.label} was ready again, and {child.id} stood tall with a grin like rain.")
    _add_story_beat(world, f"The day felt bright, and the moral was clear: when you help with kindness, good blossoms near.")

    world.facts["resolved"] = True
    world.facts["moral_value"] = "kindness"

    prompts = [
        f"Write a rhyming story about a child, a {thing.label}, and a kind solution.",
        f"Tell a gentle tale where {child.id} helps fix a problem with a {thing.label}.",
        f"Write a short story for a young child about problem solving and kindness in {setting.place}.",
    ]

    story_qa = [
        QAItem(
            question=f"What problem did {child.id} notice in {setting.place}?",
            answer=(
                f"{child.id} noticed {thing.phrase} had a {PROBLEMS[params.problem]}. "
                f"The problem made the room feel worried, so {child.id} looked for a fix."
            ),
        ),
        QAItem(
            question=f"How did {child.id} solve the problem with {thing.label}?",
            answer=(
                f"{child.id} asked for help, worked gently, and used a kind fix. "
                f"That calm problem solving helped the {thing.label} get better."
            ),
        ),
        QAItem(
            question=f"What moral value did the story show?",
            answer=(
                f"The story showed kindness. {child.id} cared about someone else's trouble, "
                f"and that caring helped solve the problem."
            ),
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a loom for?",
            answer="A loom is a tool used for weaving cloth or thread into fabric.",
        ),
        QAItem(
            question="What is a spine?",
            answer="A spine is the line of bones in the back that helps a body stand and bend.",
        ),
        QAItem(
            question="Why is kindness helpful when a problem comes up?",
            answer="Kindness helps because calm, caring people can work together instead of fighting, and that makes fixing the problem easier.",
        ),
    ]

    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa,
        world_qa=world_qa,
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
        meters = {k: v for k, v in getattr(e, "meters", {}).items() if v}
        memes = {k: v for k, v in getattr(e, "memes", {}).items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if getattr(e, "label", ""):
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({getattr(e, 'type', 'thing'):7}) {' '.join(bits)}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting in SETTINGS:
        for item in ITEMS:
            for problem in PROBLEMS:
                if item == "loom" and problem == "tangle":
                    out.append((setting, item, problem))
                if item != "loom" and problem == "ache":
                    out.append((setting, item, problem))
    return out


def explain_rejection(item: str, problem: str) -> str:
    if item == "loom" and problem != "tangle":
        return "(No story: a loom tale needs tangled threads so the problem can be fixed."
    if item != "loom" and problem != "ache":
        return "(No story: the spine tale needs an aching spine so the kindness matters.)"
    return "(No story: that combination is not a reasonable fit.)"


def build_from_args(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if args.item and args.problem:
        if (args.item == "loom" and args.problem != "tangle") or (args.item != "loom" and args.problem != "ache"):
            raise StoryError(explain_rejection(args.item, args.problem))
    combos = valid_combos()
    if args.setting:
        combos = [c for c in combos if c[0] == args.setting]
    if args.item:
        combos = [c for c in combos if c[1] == args.item]
    if args.problem:
        combos = [c for c in combos if c[2] == args.problem]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    setting, item, problem = rng.choice(combos)
    return StoryParams(
        setting=setting,
        child=args.child or rng.choice(CHILDREN),
        elder=args.elder or rng.choice(ELDERS),
        item=item,
        problem=problem,
        helper=args.helper or rng.choice(HELPERS),
    )


def asp_verify_parity() -> int:
    import asp
    model = asp.one_model(asp_program())
    happy = any(sym.name == "happy_end" for sym in model)
    if happy:
        print("OK: ASP derived the intended moral ending.")
        return 0
    print("MISMATCH: ASP did not derive the intended moral ending.")
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program())
        return
    if args.verify:
        sys.exit(asp_verify_parity())
    if args.asp:
        import asp
        model = asp.one_model(asp_program())
        atoms = sorted((sym.name, len(sym.arguments)) for sym in model)
        print("ASP model:", atoms)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(setting="attic", child="Mina", elder="Grandma", item="loom", problem="tangle", helper="friend"),
            StoryParams(setting="sunroom", child="Toby", elder="Auntie", item="spine_wrap", problem="ache", helper="sibling"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 50, 50):
            try:
                params = build_from_args(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
        header = ""
        if args.all:
            p = sample.params
            header = f"### {p.child}: {p.item} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
