#!/usr/bin/env python3
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "maid"}
        male = {"boy", "man", "father", "lord", "chef", "page"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str
    indoors: bool
    affords: set[str] = field(default_factory=set)


@dataclass
class Dish:
    id: str
    label: str
    phrase: str
    taste: str
    risk: str
    keyword: str
    tags: set[str] = field(default_factory=set)


@dataclass
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    dish: str
    fix: str
    name: str
    role: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def say(self, text: str) -> None:
        self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


SETTINGS = {
    "kitchen": Setting("the kitchen", True, {"serve"}),
    "hall": Setting("the dining hall", True, {"serve"}),
    "garden": Setting("the garden table", False, {"serve"}),
}

DISHES = {
    "loin": Dish(
        id="loin",
        label="loin",
        phrase="a simple roast loin",
        taste="savory",
        risk="burned",
        keyword="loin",
        tags={"moral", "food"},
    ),
    "stew": Dish(
        id="stew",
        label="stew",
        phrase="a warm stew",
        taste="soft and hearty",
        risk="scorched",
        keyword="stew",
        tags={"food"},
    ),
    "pie": Dish(
        id="pie",
        label="pie",
        phrase="a berry pie",
        taste="sweet",
        risk="soggy",
        keyword="pie",
        tags={"food"},
    ),
}

FIXES = {
    "adapt": Fix(
        id="adapt",
        label="an easier plan",
        prep="adapt the meal and slice the char off",
        tail="served the smaller slices with a calm smile",
        helps={"burned", "scorched"},
    ),
    "cool": Fix(
        id="cool",
        label="a cooler shelf",
        prep="move the dish to the cool shelf",
        tail="let the steam settle before serving",
        helps={"soggy"},
    ),
    "share": Fix(
        id="share",
        label="a shared table",
        prep="share the work and bring extra bread",
        tail="sat down together and ate slowly",
        helps={"burned", "scorched", "soggy"},
    ),
}

NAMES = ["Mina", "Toby", "June", "Pia", "Rowan", "Nico", "Lena", "Owen"]
ROLES = ["page", "maid", "boy", "girl"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for dish_id, dish in DISHES.items():
            for fix_id, fix in FIXES.items():
                if setting.affords and dish.risk in fix.helps:
                    combos.append((place, dish_id, fix_id))
    return combos


def reason_invalid(setting: Setting, dish: Dish, fix: Fix) -> str:
    return (
        f"(No story: at {setting.place}, the {dish.label} would be {dish.risk}, "
        f"but {fix.label} does not give a believable way to fix that.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world about a small household, a misunderstanding, and a brave adaptation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
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
    combos = [c for c in valid_combos()
              if (args.place is None or c[0] == args.place)
              and (args.dish is None or c[1] == args.dish)
              and (args.fix is None or c[2] == args.fix)]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, dish, fix = rng.choice(sorted(combos))
    name = args.name or rng.choice(NAMES)
    role = args.role or rng.choice(ROLES)
    return StoryParams(place=place, dish=dish, fix=fix, name=name, role=role)


def _speak(world: World, text: str) -> None:
    world.say(text)


def tell(setting: Setting, dish: Dish, fix: Fix, name: str, role: str) -> World:
    world = World(setting)
    lord = world.add(Entity(id="Lord", kind="character", type="lord", label="the lord"))
    child = world.add(Entity(id=name, kind="character", type=role, label=name))
    cook = world.add(Entity(id="Cook", kind="character", type="maid", label="the cook"))
    plate = world.add(Entity(id="dish", type=dish.id, label=dish.label, phrase=dish.phrase, caretaker=cook.id))

    world.facts.update(lord=lord, child=child, cook=cook, dish=plate, dish_cfg=dish, fix_cfg=fix)

    _speak(world, f"{name} was a small {role} who helped in {setting.place}.")
    _speak(world, f"{name} liked to adapt quickly when the day changed, and that made work feel lighter.")
    _speak(world, f"One evening, the cook made {dish.phrase} for the lord, because the meal was meant to stay simple.")
    _speak(world, f"The lord wanted a quiet supper, but a note on the tray caused a misunderstanding.")
    _speak(world, f"Someone read the word '{dish.keyword}' too quickly and worried the meal would become a grand feast instead of an honest one.")

    world.para()
    if dish.risk == "burned":
        _speak(world, f"When the oven door opened, the edges of the {dish.label} looked a little too dark.")
    elif dish.risk == "scorched":
        _speak(world, f"When the pot lid lifted, a little scorch mark clung to the top of the {dish.label}.")
    else:
        _speak(world, f"After the rain, the crust of the {dish.label} looked soft in the wrong way.")

    _speak(world, f"{name} felt brave enough to say the truth: the meal needed help, not pretending.")
    _speak(world, f"Their small bravery showed a good moral value, because kindness and honesty fit together.")
    _speak(world, f"Then the cook chose to {fix.prep}, and the lord nodded at once.")

    world.para()
    _speak(world, f"That was the right way to adapt the supper.")
    _speak(world, f"{name} helped carry plates, the cook {fix.tail}, and the misunderstanding melted away.")
    _speak(world, f"In the end, the lord ate the simple {dish.label}, and the table felt warm, calm, and friendly again.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    dish = f["dish_cfg"]
    return [
        f"Write a short slice-of-life story about {child.id}, a small {child.type}, who helps a lord with a {dish.keyword}.",
        f"Tell a gentle story that includes a misunderstanding, bravery, and a moral choice around {dish.phrase}.",
        f"Write a child-friendly story where people adapt to a small dinner problem without making a fuss.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    dish = f["dish_cfg"]
    fix = f["fix_cfg"]
    lord = f["lord"]
    cook = f["cook"]
    return [
        QAItem(
            question=f"Who was brave enough to speak up when the {dish.label} needed help?",
            answer=f"{child.id} was brave enough to speak up, and that helped the household solve the problem kindly.",
        ),
        QAItem(
            question=f"What was the misunderstanding about at supper?",
            answer=f"The misunderstanding was about the word '{dish.keyword}', which was read too quickly and made the meal sound grander than it was.",
        ),
        QAItem(
            question=f"How did they adapt the meal?",
            answer=f"They adapted by letting {cook.label} {fix.prep}, so the supper could still be served in a calm way for {lord.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing the right thing even when you feel shy, worried, or unsure.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good rule for how to treat others, like honesty, kindness, or fairness.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when people do not understand each other correctly at first.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        lines.append(f"{e.id}: type={e.type} label={e.label}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", dish="loin", fix="adapt", name="Mina", role="page"),
    StoryParams(place="hall", dish="stew", fix="share", name="Toby", role="boy"),
    StoryParams(place="garden", dish="pie", fix="cool", name="June", role="girl"),
]


ASP_RULES = r"""
valid(Place,Dish,Fix) :- setting(Place), dish(Dish), fix(Fix), affords(Place,serve), risk(Dish,R), helps(Fix,R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.indoors:
            lines.append(asp.fact("indoors", place))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", place, act))
    for dish_id, dish in DISHES.items():
        lines.append(asp.fact("dish", dish_id))
        lines.append(asp.fact("risk", dish_id, dish.risk))
    for fix_id, fix in FIXES.items():
        lines.append(asp.fact("fix", fix_id))
        for r in sorted(fix.helps):
            lines.append(asp.fact("helps", fix_id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTINGS[params.place], DISHES[params.dish], FIXES[params.fix], params.name, params.role)
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
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(sorted(set(asp.atoms(model, "valid"))))
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 40, 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
