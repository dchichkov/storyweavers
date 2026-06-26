#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/carve_gerund_flashback_moral_value_mystery.py
===============================================================================================================

A compact mystery-flavored story world about carving with a flashback and a
moral-value turn.

Premise:
- A child wants to carve a festival pumpkin.
- A small mystery appears: the pattern card and scoop are missing.
- A flashback recalls an earlier mistake and points to the hiding place.
- The child tells the truth, shares the work, and the finished lantern proves
  the change.

This world models physical meters and emotional memes, and emits a declarative
ASP twin for the reasonableness gate.
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


THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wore_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            if self.type in {"girl", "mother", "woman"}:
                return {"subject": "she", "object": "her", "possessive": "her"}[case]
            if self.type in {"boy", "father", "man"}:
                return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Place:
    name: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    helps: str  # mess kind or task kind


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str


@dataclass
class StoryParams:
    place: str
    name: str
    gender: str
    parent: str
    prize: str
    tool: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.flashback_used = False

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
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.flashback_used = self.flashback_used
        return clone


PLACES = {
    "kitchen": Place("the kitchen", indoors=True, affords={"carve"}),
    "porch": Place("the porch", indoors=False, affords={"carve"}),
    "table": Place("the table by the window", indoors=True, affords={"carve"}),
}

TOOLS = {
    "scoop": Tool("scoop", "pumpkin scoop", "a pumpkin scoop with a curved spoon", "soft_flesh"),
    "marker": Tool("marker", "marker", "a thick orange marker", "pattern"),
    "knife": Tool("knife", "small carving knife", "a small carving knife with a dull handle", "cut"),
}

PRIZES = {
    "pumpkin": Prize("pumpkin", "pumpkin", "a round orange pumpkin", "torso"),
}


@dataclass
class Gate:
    place: str
    prize: str
    tool: str


VALID_GATES = [
    Gate("kitchen", "pumpkin", "scoop"),
    Gate("porch", "pumpkin", "scoop"),
    Gate("table", "pumpkin", "scoop"),
]


TRAITS = ["careful", "curious", "gentle", "brave", "patient"]
GIRL_NAMES = ["Mia", "Lila", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Ben", "Theo", "Max", "Finn", "Leo"]


def child_pronoun(gender: str) -> str:
    return "she" if gender == "girl" else "he"


def poss(gender: str) -> str:
    return "her" if gender == "girl" else "his"


def select_tool(tool_id: str) -> Tool:
    return TOOLS[tool_id]


def select_prize(prize_id: str) -> Prize:
    return PRIZES[prize_id]


def can_story(place: Place, prize: Prize, tool: Tool) -> bool:
    return "carve" in place.affords and prize.id == "pumpkin" and tool.helps in {"soft_flesh", "pattern"}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for g in VALID_GATES:
        if can_story(PLACES[g.place], PRIZES[g.prize], TOOLS[g.tool]):
            out.append((g.place, g.prize, g.tool))
    return out


def choose_flashback(world: World, child: Entity, parent: Entity) -> None:
    world.flashback_used = True
    world.say(
        f"As {child.pronoun()} frowned, a little flashback came back to {child.pronoun('possessive')} mind: "
        f"last year, {child.id} had hidden the tools under a tea towel and forgotten."
    )
    world.say(
        f"{parent.label.capitalize()} had laughed then and said, \"If you put things back, the next mystery gets easier.\""
    )


def do_carving(world: World, child: Entity, parent: Entity, prize: Entity, tool: Entity) -> None:
    child.meters["hope"] = child.meters.get("hope", 0) + 1
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    world.say(
        f"{child.id} wanted to carve the {prize.label} right away, but the {tool.label} was missing."
    )
    world.say(
        f"{child.id} looked behind bowls, under napkins, and beside the sink, but the table stayed strangely empty."
    )


def resolve_mystery(world: World, child: Entity, parent: Entity, prize: Entity, tool: Entity) -> None:
    world.say(
        f"Then {child.id} noticed a small lump under a folded towel. There it was: the {tool.label}, tucked away where no one could see."
    )
    world.say(
        f"{child.id} told {parent.label} the truth about forgetting it there before. That made the room feel lighter."
    )
    child.memes["honesty"] = child.memes.get("honesty", 0) + 1
    parent.memes["trust"] = parent.memes.get("trust", 0) + 1
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    world.say(
        f"Together they carved the {prize.label} with care, and the bright face in the pumpkin glowed on the table like a tiny moon."
    )


def tell(place: Place, tool: Tool, prize: Prize, child_name: str, gender: str, parent_type: str) -> World:
    world = World(place)
    child = world.add(Entity(id=child_name, kind="character", type=gender, label=child_name))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="mom" if parent_type == "mother" else "dad"))
    pumpkin = world.add(Entity(id="pumpkin", type="pumpkin", label="pumpkin", phrase=prize.phrase, owner=child.id, caretaker=parent.id))
    cutter = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, owner=child.id))

    world.say(
        f"{child.id} was a {random.choice(TRAITS)} {gender} who loved making lanterns from pumpkins."
    )
    world.say(
        f"On a cool evening, {child.id} and {parent.label} sat at {place.name} with {pumpkin.phrase} waiting in the middle."
    )
    do_carving(world, child, parent, pumpkin, cutter)
    world.para()
    choose_flashback(world, child, parent)
    world.say(
        f"The old memory pointed to the towel, and the missing tool stopped being a mystery."
    )
    world.para()
    resolve_mystery(world, child, parent, pumpkin, cutter)
    world.facts.update(child=child, parent=parent, pumpkin=pumpkin, tool=cutter, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    tool = f["tool"]
    return [
        f'Write a short mystery story for a small child about {child.id} carving a pumpkin and finding a missing {tool.label}.',
        f'Create a gentle story with a flashback, where {child.id} remembers what happened to the {tool.label} and learns a moral value about telling the truth.',
        f'Write a child-friendly mystery that ends with a glowing pumpkin and a lesson about putting things back.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    tool = f["tool"]
    pumpkin = f["pumpkin"]
    place = f["place"]
    return [
        QAItem(
            question=f"What was {child.id} trying to make at {place.name}?",
            answer=f"{child.id} was trying to carve a {pumpkin.label} into a lantern.",
        ),
        QAItem(
            question=f"What was missing before the carving could begin?",
            answer=f"The {tool.label} was missing, so {child.id} had to solve the mystery first.",
        ),
        QAItem(
            question=f"What did the flashback help {child.id} remember?",
            answer=f"The flashback helped {child.id} remember that the {tool.label} had been hidden under a towel last year.",
        ),
        QAItem(
            question=f"What moral choice did {child.id} make near the end?",
            answer=f"{child.id} told {parent.label} the truth about forgetting the tool, and that honesty helped them finish together.",
        ),
    ]


WORLD_QA = [
    QAItem(
        question="What is a flashback in a story?",
        answer="A flashback is a moment when the story briefly shows something that happened earlier, so the reader understands the present better.",
    ),
    QAItem(
        question="What does it mean to tell the truth?",
        answer="To tell the truth means to say what really happened instead of making up a false story.",
    ),
]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_QA


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- trace ---"]
    for e in world.entities.values():
        out.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    out.append(f"flashback_used={world.flashback_used}")
    return "\n".join(out)


ASP_RULES = r"""
place(kitchen). place(porch). place(table).
affords(kitchen,carve). affords(porch,carve). affords(table,carve).
prize(pumpkin). worn_on(pumpkin,torso).
tool(scoop). helps(scoop,soft_flesh).
tool(marker). helps(marker,pattern).
tool(knife). helps(knife,cut).

valid(Place,Prize,Tool) :- affords(Place,carve), prize(Prize), tool(Tool), helps(Tool,soft_flesh), Prize = pumpkin.
"""


def asp_facts() -> str:
    import asp

    lines = []
    for pname, place in PLACES.items():
        lines.append(asp.fact("place", pname))
        if place.indoors:
            lines.append(asp.fact("indoors", pname))
        for act in sorted(place.affords):
            lines.append(asp.fact("affords", pname, act))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("helps", tid, tool.helps))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(place: Place, prize: Prize, tool: Tool) -> str:
    return (
        f"(No story: {place.name} can host carving, but the {tool.label} does not fit this mystery cleanly. "
        f"Try the pumpkin scoop, which can solve the missing-tool problem honestly.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mystery-flavored carving story world with flashback and moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    place = args.place or rng.choice(list(PLACES))
    prize = args.prize or "pumpkin"
    tool = args.tool or "scoop"
    if not can_story(PLACES[place], PRIZES[prize], TOOLS[tool]):
        raise StoryError(explain_rejection(PLACES[place], PRIZES[prize], TOOLS[tool]))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, name=name, gender=gender, parent=parent, prize=prize, tool=tool)


def generate(params: StoryParams) -> StorySample:
    world = tell(PLACES[params.place], TOOLS[params.tool], PRIZES[params.prize], params.name, params.gender, params.parent)
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
    StoryParams(place="kitchen", name="Mia", gender="girl", parent="mother", prize="pumpkin", tool="scoop"),
    StoryParams(place="porch", name="Leo", gender="boy", parent="father", prize="pumpkin", tool="scoop"),
    StoryParams(place="table", name="Ava", gender="girl", parent="mother", prize="pumpkin", tool="scoop"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print(asp_valid_combos())
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(50, args.n * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError as e:
                print(e)
                return
            params.seed = base_seed + i
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
