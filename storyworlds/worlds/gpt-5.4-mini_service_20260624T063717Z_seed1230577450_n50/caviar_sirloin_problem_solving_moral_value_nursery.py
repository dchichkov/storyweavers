#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T063717Z_seed1230577450_n50/caviar_sirloin_problem_solving_moral_value_nursery.py
===============================================================================================================================

A standalone storyworld about a little nursery-rhyme problem:
a child wants a fancy snack, a plate goes wrong, and kindness plus clever
problem-solving turn the night into a warm, moral ending.

Seed words: caviar, sirloin
Style: Nursery Rhyme
Features: Problem Solving, Moral Value
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
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str = "the little kitchen"
    indoors: bool = True


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    delight: str
    value: str
    kind: str
    expensive: bool = False


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    cost: str = ""
    humble: bool = True


@dataclass
class StoryParams:
    place: str
    delicacy: str
    protein: str
    name: str
    child_type: str
    helper: str
    trait: str
    seed: Optional[int] = None


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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


def _children_names(kind: str) -> list[str]:
    return ["Mina", "Ned", "Toby", "Luna", "Poppy", "Finn"] if kind == "girl" else ["Tom", "Ben", "Theo", "Bram", "Kit", "Jules"]


SETTINGS = {
    "kitchen": Setting(place="the little kitchen", indoors=True),
    "pantry": Setting(place="the pantry nook", indoors=True),
    "table": Setting(place="the cozy table", indoors=True),
}

FOODS = {
    "caviar": Food(
        id="caviar",
        label="caviar",
        phrase="a silver spoon of caviar",
        delight="sparkling and fancy",
        value="special",
        kind="tiny pearls",
        expensive=True,
    ),
    "sirloin": Food(
        id="sirloin",
        label="sirloin",
        phrase="a warm plate of sirloin",
        delight="toasty and hearty",
        value="big",
        kind="a tender steak",
        expensive=False,
    ),
    "both": Food(
        id="both",
        label="caviar and sirloin",
        phrase="a tiny dish of caviar beside a small slice of sirloin",
        delight="splashy and filling",
        value="mixed",
        kind="a pair of treats",
        expensive=True,
    ),
}

TOOLS = {
    "tiny_spoon": Tool(
        id="tiny_spoon",
        label="a tiny spoon",
        phrase="a tiny spoon",
        helps={"caviar"},
        cost="gently",
        humble=True,
    ),
    "sharing_plate": Tool(
        id="sharing_plate",
        label="a sharing plate",
        phrase="a sharing plate with two neat spaces",
        helps={"caviar", "sirloin", "both"},
        cost="kindly",
        humble=True,
    ),
    "napkin_ring": Tool(
        id="napkin_ring",
        label="a napkin ring",
        phrase="a napkin ring and a folded cloth",
        helps={"sirloin"},
        cost="carefully",
        humble=True,
    ),
}


class Reason:
    @staticmethod
    def can_problem_solve(food: Food, tool: Tool) -> bool:
        return food.id in tool.helps

    @staticmethod
    def moral_turn(child: Entity, helper: Entity) -> bool:
        return child.memes.get("greed", 0) > 0 and helper.memes.get("kindness", 0) > 0


ASP_RULES = r"""
food(caviar;sirloin;both).
tool(tiny_spoon;sharing_plate;napkin_ring).
helps(tiny_spoon,caviar).
helps(sharing_plate,caviar).
helps(sharing_plate,sirloin).
helps(sharing_plate,both).
helps(napkin_ring,sirloin).

can_solve(F,T) :- food(F), tool(T), helps(T,F).
show_solution(F,T) :- can_solve(F,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for fid, food in FOODS.items():
        lines.append(asp.fact("food", fid))
        if food.expensive:
            lines.append(asp.fact("expensive", fid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for f in sorted(tool.helps):
            lines.append(asp.fact("helps", tid, f))
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def resolve_problem(food: Food, tool: Tool) -> bool:
    return Reason.can_problem_solve(food, tool)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about caviar, sirloin, and kind problem solving.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--delicacy", choices=FOODS)
    ap.add_argument("--protein", choices=FOODS)
    ap.add_argument("--name")
    ap.add_argument("--child-type", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "aunt", "uncle"])
    ap.add_argument("--trait", choices=["patient", "kind", "brave", "gentle", "curious"])
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for delicacy in FOODS:
            for protein in FOODS:
                if delicacy == protein:
                    continue
                if {delicacy, protein} <= {"caviar", "sirloin"}:
                    combos.append((place, delicacy, protein))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.delicacy:
        combos = [c for c in combos if c[1] == args.delicacy]
    if args.protein:
        combos = [c for c in combos if c[2] == args.protein]
    if not combos:
        raise StoryError("No valid story matches those choices.")
    place, delicacy, protein = rng.choice(sorted(combos))
    child_type = args.child_type or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(_children_names(child_type))
    helper = args.helper or rng.choice(["mother", "father", "aunt"])
    trait = args.trait or rng.choice(["patient", "kind", "brave", "gentle", "curious"])
    return StoryParams(place=place, delicacy=delicacy, protein=protein, name=name, child_type=child_type, helper=helper, trait=trait)


def tell(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    child = world.add(Entity(id=params.name, kind="character", type=params.child_type))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper, label=f"the {params.helper}"))
    delicacy = world.add(Entity(id="delicacy", type=params.delicacy, label=FOODS[params.delicacy].label, phrase=FOODS[params.delicacy].phrase, owner=child.id, caretaker=helper.id))
    protein = world.add(Entity(id="protein", type=params.protein, label=FOODS[params.protein].label, phrase=FOODS[params.protein].phrase, owner=child.id, caretaker=helper.id))

    child.memes["want"] = 1
    child.memes["greed"] = 1 if params.delicacy == "caviar" else 0
    helper.memes["kindness"] = 1

    world.say(f"Little {params.trait} {params.name} sat by {world.setting.place} and hummed a nursery tune.")
    world.say(f"{params.name} loved {FOODS[params.delicacy].label}, for it was {FOODS[params.delicacy].delight}, and also loved {FOODS[params.protein].label}, for it was {FOODS[params.protein].delight}.")
    world.say(f"The {params.helper} brought {delicacy.phrase} and {protein.phrase}, and the table looked bright as a moonbeam.")
    world.para()
    world.say(f"Then trouble came in a tiny trundle: the spoon was too small for the sirloin, and the caviar dish was too wide for careful hands.")
    world.say(f"{params.name} frowned, then thought and thought, for good children use their minds as well as their mouths.")
    if params.delicacy == "caviar" and params.protein == "sirloin":
        tool = TOOLS["sharing_plate"]
    elif params.delicacy == "caviar":
        tool = TOOLS["tiny_spoon"]
    else:
        tool = TOOLS["napkin_ring"]
    if resolve_problem(FOODS[params.delicacy], tool) and resolve_problem(FOODS[params.protein], TOOLS["sharing_plate"]):
        child.memes["pride"] = 1
        helper.memes["kindness"] = 1
        world.say(f"With {tool.label}, {params.name} made a neat little fix: {tool.phrase}.")
        world.say(f"The {params.helper} smiled, and together they placed the caviar on one side and the sirloin on the other, so neither would spill nor smudge.")
        world.para()
        world.say(f"{params.name} shared first and saved a bite for later, which was the kinder choice and the wiser choice too.")
        world.say(f"And so the meal went merry and mild, with caviar sparkling like dew and sirloin warm as a hearth, while every heart stayed light.")
    else:
        raise StoryError("This story needs a real fix, not a pretend one.")
    world.facts.update(child=child, helper=helper, delicacy=delicacy, protein=protein, tool=tool, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    return [
        f"Write a short nursery-rhyme story about {p.name} who likes caviar and sirloin and learns to solve a small mealtime problem kindly.",
        f"Tell a gentle rhyme where {p.name} uses clever thinking to share caviar and sirloin without fuss.",
        f"Write a child-friendly story with caviar, sirloin, and a moral about using a kind fix when things get tricky.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = world.facts["params"]
    return [
        QAItem(
            question=f"What did {p.name} do when the caviar and sirloin caused a tiny problem?",
            answer=f"{p.name} thought carefully, used a simple helper tool, and made a neat plan so the caviar and sirloin could be served safely.",
        ),
        QAItem(
            question=f"Why was the ending a moral one?",
            answer=f"It was moral because {p.name} chose kindness and sharing instead of grabbing everything at once.",
        ),
        QAItem(
            question=f"Who helped {p.name} at the table?",
            answer=f"The {p.helper} helped {p.name} by bringing the food and smiling at the clever fix.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is caviar?",
            answer="Caviar is tiny fish eggs that people sometimes eat as a fancy food.",
        ),
        QAItem(
            question="What is sirloin?",
            answer="Sirloin is a kind of beef steak, and it is often tender and tasty.",
        ),
        QAItem(
            question="What does it mean to solve a problem?",
            answer="To solve a problem means to find a good way to make a hard thing easier or to fix what went wrong.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is an idea like kindness, honesty, or sharing that helps people choose the good way to act.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:10} ({e.type:8}) meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="kitchen", delicacy="caviar", protein="sirloin", name="Luna", child_type="girl", helper="mother", trait="gentle"),
    StoryParams(place="table", delicacy="sirloin", protein="caviar", name="Tom", child_type="boy", helper="father", trait="kind"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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


def asp_verify() -> int:
    import asp
    program = asp_program("#show can_solve/2.")
    model = asp.one_model(program)
    atoms = sorted(set(asp.atoms(model, "can_solve")))
    py = sorted((f, t) for f in FOODS for t in TOOLS if resolve_problem(FOODS[f], TOOLS[t]))
    if atoms == py:
        print(f"OK: ASP matches Python ({len(py)} solutions).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("ASP:", atoms)
    print("PY :", py)
    return 1


def asp_solutions() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show can_solve/2."))
    return sorted(set(asp.atoms(model, "can_solve")))


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show can_solve/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        sols = asp_solutions()
        print(f"{len(sols)} solutions:")
        for f, t in sols:
            print(f"  {f} -> {t}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

    if args.json:
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(s, trace=args.trace, qa=args.qa, header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
