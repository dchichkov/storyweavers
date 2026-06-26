#!/usr/bin/env python3
"""
storyworlds/worlds/harm_charge_kindergarten_foreshadowing_flashback_comedy.py
==============================================================================

A small kindergarten storyworld about a child, a charge, a possible harm,
and a comic safe fix.

The seed tale behind this world:
A child in kindergarten wants to charge a small toy robot so it can play.
A teacher notices a puddle of juice nearby and worries the toy could be harmed.
The teacher remembers a messy moment from yesterday, gives a warning, and then
helps the child move the charger to a dry tray. The robot gets charged safely,
everyone laughs, and the robot zips around happily.

This script models that as a tiny stateful simulation with:
- physical meters: charge, wet, tidy, harm
- emotional memes: joy, worry, surprise, comedy
- foreshadowing and flashback as narrative instruments
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)
    plural: bool = False

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "teacher"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the kindergarten classroom"
    affords: set[str] = field(default_factory=set)


@dataclass
class Toy:
    id: str
    label: str
    phrase: str
    kind: str
    battery_low: bool = True


@dataclass
class Fix:
    id: str
    label: str
    phrase: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _splash_risk(world: World) -> list[str]:
    out: list[str] = []
    for toy in world.entities.values():
        if toy.type != "toy":
            continue
        if toy.meters.get("charge", 0.0) < THRESHOLD:
            continue
        if toy.meters.get("wet", 0.0) < THRESHOLD:
            continue
        sig = ("harm", toy.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        toy.meters["harm"] = toy.meters.get("harm", 0.0) + 1
        out.append(f"The little toy could get harmed if it charged on the wet table.")
    return out


CAUSAL_RULES = [_splash_risk]


def propagate(world: World, narrate: bool = True) -> list[str]:
    all_lines: list[str] = []
    changed = True
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                all_lines.extend(lines)
    if narrate:
        for line in all_lines:
            world.say(line)
    return all_lines


def predict_harm(world: World, toy_id: str) -> bool:
    sim = world.copy()
    sim.get(toy_id).meters["charge"] = 1.0
    propagate(sim, narrate=False)
    return sim.get(toy_id).meters.get("harm", 0.0) >= THRESHOLD


def safe_fix_for(toy: Entity) -> Optional[Fix]:
    return FIXES_BY_TOY.get(toy.type)


def toy_desire(toy: Entity) -> str:
    return {
        "robot": "zip and beep",
        "dinosaur": "stomp and roar",
        "truck": "roll and honk",
    }.get(toy.type, "play")


def setup_line(setting: Setting) -> str:
    return f"{setting.place.capitalize()} was bright and noisy in the nice way only kindergarten can be."


def foreshadow_line() -> str:
    return "The teacher had already noticed a little juice puddle by the art shelf, which was a clue that the floor wanted attention."


def flashback_line() -> str:
    return "Yesterday, a crayon basket had tipped over on the same cart, and everyone had laughed after cleaning it up with tiny sponges."


def intro(world: World, child: Entity, teacher: Entity, toy: Entity) -> None:
    world.say(setup_line(world.setting))
    world.say(
        f"{child.id} was a cheerful {child.type} who loved a toy named {toy.id}. "
        f"{toy.id} liked to {toy_desire(toy)}."
    )
    world.say(
        f"{teacher.id} kept an eye on the room and tried to make sure nothing got harmed."
    )


def want_charge(world: World, child: Entity, toy: Entity) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 0.5
    toy.meters["charge"] = toy.meters.get("charge", 0.0) + 0.2
    world.say(
        f"{child.id} wanted to charge {toy.id} right away so it could {toy_desire(toy)} all afternoon."
    )


def warn(world: World, teacher: Entity, toy: Entity) -> None:
    if predict_harm(world, toy.id):
        teacher.memes["worry"] = teacher.memes.get("worry", 0.0) + 1
        world.facts["foreshadow"] = True
        world.say(
            f'{teacher.id} pointed to the juice and said, '
            f'"If we charge {toy.id} there, it could get harmed."'
        )
        world.say(foreshadow_line())


def flashback(world: World, teacher: Entity) -> None:
    teacher.memes["surprise"] = teacher.memes.get("surprise", 0.0) + 0.2
    world.say(flashback_line())


def choose_fix(world: World, teacher: Entity, child: Entity, toy: Entity) -> Optional[Fix]:
    fix = safe_fix_for(toy)
    if fix is None:
        return None
    world.say(
        f'{teacher.id} smiled and said, "Let us move it to {fix.prep}."'
    )
    return fix


def apply_fix(world: World, child: Entity, toy: Entity, fix: Fix) -> None:
    toy.meters["wet"] = 0.0
    toy.meters["charge"] = 1.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    child.memes["surprise"] = child.memes.get("surprise", 0.0) + 0.5
    world.say(
        f"{child.id} helped move the charger to the dry tray. Then {toy.id} got its charge safely, "
        f"and the room stayed calm and silly instead of harmful."
    )
    world.say(
        f"They {fix.tail}. Soon {toy.id} was ready to {toy_desire(toy)}, and everybody giggled when it beeped twice."
    )


def tell(setting: Setting, child_name: str = "Mia", child_type: str = "girl", teacher_name: str = "Ms. Pine") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, meters={}, memes={}))
    teacher = world.add(Entity(id=teacher_name, kind="character", type="teacher", meters={}, memes={}))
    toy = world.add(Entity(
        id="Pip",
        kind="thing",
        type="robot",
        label="toy robot",
        phrase="a shiny toy robot",
        meters={"charge": 0.0, "wet": 1.0},
        memes={},
    ))
    world.add(Entity(
        id="juice",
        kind="thing",
        type="spill",
        label="juice puddle",
        phrase="a sticky juice puddle",
        meters={"wet": 1.0},
        memes={},
    ))

    intro(world, child, teacher, toy)

    world.para()
    want_charge(world, child, toy)
    warn(world, teacher, toy)
    flashback(world, teacher)

    world.para()
    fix = choose_fix(world, teacher, child, toy)
    if fix:
        apply_fix(world, child, toy, fix)
    propagate(world)

    world.facts.update(
        child=child,
        teacher=teacher,
        toy=toy,
        fix=fix,
    )
    return world


SETTINGS = {
    "kindergarten": Setting(place="the kindergarten classroom", affords={"charge"}),
}

TOYS = {
    "robot": Toy(id="robot", label="toy robot", phrase="a shiny toy robot", kind="robot", battery_low=True),
    "truck": Toy(id="truck", label="toy truck", phrase="a chubby toy truck", kind="truck", battery_low=True),
}

FIXES = [
    Fix(
        id="dry_tray",
        label="a dry tray",
        phrase="a dry tray",
        prep="the dry tray by the window",
        tail="parked the charger on the dry tray by the window",
        guards={"wet"},
        covers={"table"},
    ),
]

FIXES_BY_TOY = {
    "robot": FIXES[0],
    "truck": FIXES[0],
}


@dataclass
class StoryParams:
    place: str
    toy: str
    name: str
    gender: str
    teacher: str
    seed: Optional[int] = None


CURATED = [
    StoryParams(place="kindergarten", toy="robot", name="Mia", gender="girl", teacher="Ms. Pine"),
    StoryParams(place="kindergarten", toy="truck", name="Noah", gender="boy", teacher="Mr. Reed"),
]


def valid_combos() -> list[tuple[str, str]]:
    return [("kindergarten", toy_id) for toy_id in TOYS]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Kindergarten comedy about charge, harm, and a safe fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--toy", choices=TOYS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--teacher")
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
    if args.place and args.place != "kindergarten":
        raise StoryError("This world only takes place in kindergarten.")
    toy = args.toy or rng.choice(list(TOYS))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(["Mia", "Noah", "Ava", "Eli", "Lena", "Theo"])
    teacher = args.teacher or rng.choice(["Ms. Pine", "Mr. Reed", "Ms. Blue"])
    return StoryParams(place="kindergarten", toy=toy, name=name, gender=gender, teacher=teacher)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    toy = f["toy"]
    child = f["child"]
    teacher = f["teacher"]
    return [
        "Write a short kindergarten comedy about a child trying to charge a toy while a teacher worries about harm.",
        f"Tell a gentle story where {child.id} wants to charge {toy.id}, {teacher.id} notices a possible harm, and they find a safe fix.",
        "Write a playful story with a foreshadowing clue, a flashback, and a happy ending in kindergarten.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    teacher = f["teacher"]
    toy = f["toy"]
    fix = f["fix"]
    return [
        QAItem(
            question=f"Who wanted to charge {toy.id} in kindergarten?",
            answer=f"{child.id} wanted to charge {toy.id} so it could {toy_desire(toy)}.",
        ),
        QAItem(
            question=f"Why did {teacher.id} worry about harm?",
            answer=f"{teacher.id} worried because there was a wet juice puddle nearby, and charging {toy.id} there could have harmed it.",
        ),
        QAItem(
            question="What helped the story end safely?",
            answer=f"They moved the charger to {fix.label}, so {toy.id} got its charge without getting harmed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does charge mean for a toy?",
            answer="For a toy, charge means giving its battery energy so it can move, beep, or light up again.",
        ),
        QAItem(
            question="What is harm?",
            answer="Harm means damage or injury that can hurt a person or a thing.",
        ),
        QAItem(
            question="Why is a dry place helpful for charging?",
            answer="A dry place helps because water can make charging unsafe and can damage the toy.",
        ),
    ]


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


ASP_RULES = r"""
% A toy is at risk of harm if it has charge and there is wetness nearby.
at_risk(T) :- toy(T), has(T, charge), has(T, wet).

% A fix is safe if it guards wetness.
safe_fix(F, T) :- fix(F), toy(T), protects(F, wet), at_risk(T).

valid_story(kindergarten, T) :- toy(T), safe_fix(_, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    lines.append(asp.fact("setting", "kindergarten"))
    lines.append(asp.fact("affords", "kindergarten", "charge"))
    for toy_id, toy in TOYS.items():
        lines.append(asp.fact("toy", toy_id))
        lines.append(asp.fact("has", toy_id, "charge"))
        lines.append(asp.fact("has", toy_id, "wet"))
    for fix in FIXES:
        lines.append(asp.fact("fix", fix.id))
        for g in sorted(fix.guards):
            lines.append(asp.fact("protects", fix.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = {("kindergarten", toy) for toy in TOYS}
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], child_name=params.name, child_type=params.gender, teacher_name=params.teacher)
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


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid_story/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_stories())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(50, args.n * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
