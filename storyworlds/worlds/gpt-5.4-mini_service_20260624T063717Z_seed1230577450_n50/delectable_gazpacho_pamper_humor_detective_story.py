#!/usr/bin/env python3
"""
storyworlds/worlds/delectable_gazpacho_pamper_humor_detective_story.py
=======================================================================

A small detective-style storyworld about a careful sleuth, a delectable bowl of
gazpacho, and a pampering plan that turns a cold complaint into a warm joke.

The seed words shape the premise:
- delectable: the gazpacho is impressively tasty
- gazpacho: the central dish, chilled and fragile
- pamper: the resolution is an attentive, gentle fix
- Humor: the ending should feel light, playful, and child-facing
- Detective Story: the world uses clues, suspicion, and a reveal

This is a self-contained storyworld script with:
- typed entities carrying physical meters and emotional memes
- a causal world model that drives the prose
- a Python reasonableness gate plus an inline ASP twin
- CLI support for generation, JSON, QA, trace, ASP, and verification
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

THEMES = {"humor", "detective", "food"}


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]


@dataclass
class Setting:
    place: str
    indoor: bool = True
    has_table: bool = True
    has_fridge: bool = True


@dataclass
class Dish:
    id: str
    label: str
    phrase: str
    temperature: str
    delight: str
    clue: str
    garnish: str


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    use: str
    tidy: bool = True


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
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class StoryParams:
    place: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    sidekick_type: str
    dish: str
    tool: str
    seed: Optional[int] = None


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, has_table=True, has_fridge=True),
    "cafe": Setting(place="the tiny cafe", indoor=True, has_table=True, has_fridge=False),
    "dining_room": Setting(place="the dining room", indoor=True, has_table=True, has_fridge=True),
}

DISHES = {
    "gazpacho": Dish(
        id="gazpacho",
        label="gazpacho",
        phrase="a bowl of delectable gazpacho",
        temperature="cold",
        delight="the cool tomato taste",
        clue="a tiny basil leaf",
        garnish="cucumber bits",
    ),
    "soup": Dish(
        id="soup",
        label="soup",
        phrase="a bowl of vegetable soup",
        temperature="warm",
        delight="the cozy broth",
        clue="a carrot coin",
        garnish="parsley",
    ),
}

TOOLS = {
    "spoon": Tool(id="spoon", label="spoon", phrase="a silver spoon", use="stir the bowl"),
    "napkin": Tool(id="napkin", label="napkin", phrase="a soft napkin", use="wipe the table"),
    "tray": Tool(id="tray", label="tray", phrase="a neat tray", use="carry the snack"),
}

HERO_NAMES = ["Mina", "Leo", "Ruby", "Toby", "Nora", "Ivy"]
SIDEKICK_NAMES = ["Pip", "Moe", "Zed", "Dot", "Pia", "Cal"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.dish not in DISHES:
        raise StoryError("Unknown dish.")
    if params.tool not in TOOLS:
        raise StoryError("Unknown tool.")
    if params.hero_name == params.sidekick_name:
        raise StoryError("The detective and sidekick must be different characters.")
    if params.place not in SETTINGS:
        raise StoryError("Unknown place.")


def allow_combo(place: str, dish: Dish, tool: Tool) -> bool:
    if dish.id == "gazpacho" and place == "cafe":
        return tool.id in {"napkin", "tray", "spoon"}
    if dish.id == "gazpacho":
        return tool.id in {"napkin", "tray"}
    return tool.id in {"spoon", "napkin", "tray"}


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place in SETTINGS:
        for dish in DISHES.values():
            for tool in TOOLS.values():
                if allow_combo(place, dish, tool):
                    out.append((place, dish.id, tool.id))
    return out


ASP_RULES = r"""
valid(Place,Dish,Tool) :- place(Place), dish(Dish), tool(Tool),
                         allowed(Place,Dish,Tool).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
    for dish in DISHES.values():
        lines.append(asp.fact("dish", dish.id))
        lines.append(asp.fact("allowed", "kitchen", dish.id, "napkin")) if dish.id == "gazpacho" else None
        lines.append(asp.fact("allowed", "kitchen", dish.id, "tray"))
        lines.append(asp.fact("allowed", "kitchen", dish.id, "spoon"))
        lines.append(asp.fact("allowed", "dining_room", dish.id, "napkin"))
        lines.append(asp.fact("allowed", "dining_room", dish.id, "tray"))
        lines.append(asp.fact("allowed", "dining_room", dish.id, "spoon"))
        lines.append(asp.fact("allowed", "cafe", dish.id, "napkin"))
        lines.append(asp.fact("allowed", "cafe", dish.id, "tray"))
        lines.append(asp.fact("allowed", "cafe", dish.id, "spoon"))
    for tool in TOOLS.values():
        lines.append(asp.fact("tool", tool.id))
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
    print("MISMATCH between clingo and Python gate.")
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Detective-style humor storyworld about gazpacho and pampering.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--dish", choices=DISHES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--sidekick")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.dish:
        combos = [c for c in combos if c[1] == args.dish]
    if args.tool:
        combos = [c for c in combos if c[2] == args.tool]
    if not combos:
        raise StoryError("No valid combination matches the given options.")
    place, dish, tool = rng.choice(sorted(combos))
    hero_name = args.name or rng.choice(HERO_NAMES)
    sidekick_name = args.sidekick or rng.choice([n for n in SIDEKICK_NAMES if n != hero_name])
    return StoryParams(place=place, hero_name=hero_name, hero_type="detective", sidekick_name=sidekick_name, sidekick_type="helper", dish=dish, tool=tool)


def _tell(params: StoryParams) -> World:
    setting = SETTINGS[params.place]
    dish = DISHES[params.dish]
    tool = TOOLS[params.tool]
    w = World(setting)
    hero = w.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    side = w.add(Entity(id=params.sidekick_name, kind="character", type=params.sidekick_type))
    bowl = w.add(Entity(id="bowl", type="bowl", label=dish.label, phrase=dish.phrase, owner=hero.id, caretaker=side.id))
    clue = w.add(Entity(id="clue", type="clue", label=dish.clue, phrase=dish.clue))
    hero.memes["curiosity"] = 1
    bowl.meters["cold"] = 1 if dish.temperature == "cold" else 0
    w.say(f"{hero.id} was a detective who could spot a clue in a teacup.")
    w.say(f"One evening at {setting.place}, {hero.id} found {dish.phrase}, and it looked so {dish.delight} that even {side.id} grinned.")
    w.para()
    w.say(f"Then the mystery began. The spoon was missing, and {hero.id} asked, 'Who borrowed the {dish.label} spoon?'")
    w.say(f"{side.id} pointed at the table. There was {dish.clue}, and that made the case feel funnier than serious.")
    w.para()
    if tool.id == "napkin":
        w.say(f"{hero.id} put {tool.phrase} under the bowl and gently used it to {tool.use}.")
    elif tool.id == "tray":
        w.say(f"{hero.id} slid the bowl onto {tool.phrase} so it would not wobble while they searched.")
    else:
        w.say(f"{hero.id} used {tool.phrase} to {tool.use}, which solved one tiny problem and made another funny one.")
    w.say(f"At last, the culprit was simple: a chilly breeze had nudged the bowl, not a thief at all.")
    w.say(f"So {side.id} got to pamper the snack with extra {dish.garnish}, and {hero.id} laughed at the very dramatic clue.")
    w.say(f"By the end, the delectable {dish.label} was safe, the mystery was solved, and the whole room felt like a cheerful joke.")
    w.facts.update(hero=hero, sidekick=side, dish=dish, tool=tool, setting=setting)
    return w


def generate(params: StoryParams) -> StorySample:
    w = _tell(params)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=[
            f"Write a funny detective story for young children featuring delectable {params.dish}.",
            f"Tell a story where {params.hero_name} solves a small kitchen mystery and someone gets to pamper the snack.",
        ],
        story_qa=[
            QAItem(question=f"What did {params.hero_name} find?", answer=f"{params.hero_name} found {DISHES[params.dish].phrase}."),
            QAItem(question="What turned out to be the cause of the trouble?", answer="It was just a chilly breeze nudging the bowl, not a thief."),
        ],
        world_qa=[
            QAItem(question="What is gazpacho?", answer="Gazpacho is a cold soup, often made with tomatoes and served chilled."),
            QAItem(question="What does it mean to pamper something?", answer="To pamper something means to care for it gently and make it feel special."),
        ],
        world=w,
    )


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, e.type, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(place="kitchen", hero_name="Mina", hero_type="detective", sidekick_name="Pip", sidekick_type="helper", dish="gazpacho", tool="napkin"),
    StoryParams(place="dining_room", hero_name="Leo", hero_type="detective", sidekick_name="Dot", sidekick_type="helper", dish="gazpacho", tool="tray"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/3."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos")
        for c in combos:
            print(c)
        return
    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if args.all else []
    if not samples:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1
    if args.json:
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=args.trace, qa=args.qa, header=f"### variant {i+1}" if len(samples) > 1 else "")
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
