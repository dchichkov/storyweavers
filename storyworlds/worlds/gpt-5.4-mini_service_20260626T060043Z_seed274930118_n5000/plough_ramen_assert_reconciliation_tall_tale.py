#!/usr/bin/env python3
"""
Tall-tale story world: a boastful plough, a runaway bowl of ramen, and a proud
argument that ends in reconciliation.

This script builds a tiny simulated domain where a farmhand wants to plough a
field, a cook is carrying ramen, and somebody makes a loud assertion that the
job should be done "the tallest way possible." The clash is resolved when the
characters listen, swap jobs, and reconcile.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"man", "boy", "farmer", "cook"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"woman", "girl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Setting:
    place: str = "the red field"
    weather: str = "windy"


@dataclass
class Tool:
    label: str
    phrase: str
    action: str
    boast: str
    strain: str
    harmony: str
    kind: str = "tool"


@dataclass
class Food:
    label: str
    phrase: str
    slosh: str
    kind: str = "food"


@dataclass
class StoryParams:
    place: str
    tool: str
    food: str
    hero: str
    helper: str
    seed: Optional[int] = None


@dataclass
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "field": Setting(place="the red field", weather="windy"),
    "valley": Setting(place="the wide valley", weather="sunny"),
    "hill": Setting(place="the gold hill", weather="blustery"),
}

TOOLS = {
    "plough": Tool(
        label="plough",
        phrase="a stout plough with a shiny handle",
        action="plough the field",
        boast="the plough could turn the earth faster than a rooster could crow",
        strain="the furrows were so deep they looked like river tracks",
        harmony="the plough made tidy lines through the soil",
    ),
    "cart": Tool(
        label="cart",
        phrase="a tiny cart with a squeaky wheel",
        action="haul the harvest",
        boast="the cart could roll as proudly as a parade drum",
        strain="the wheel kept wobbling like a loose tooth",
        harmony="the cart rolled straight once the wheel was tightened",
    ),
}

FOODS = {
    "ramen": Food(
        label="ramen",
        phrase="a steaming bowl of ramen with curly noodles",
        slosh="slopped over the rim",
    ),
    "soup": Food(
        label="soup",
        phrase="a hot pot of bean soup",
        slosh="spilled in a bright splash",
    ),
}

HEROES = ["Milo", "Nia", "Tobin", "Lena", "Arlo", "June"]
HELPERS = ["Aunt Maple", "Uncle Gus", "the neighbor", "the cook", "the farmhand"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def _setup_world(params: StoryParams) -> World:
    world = World(SETTINGS[params.place])
    hero = world.add(Entity(id=params.hero, kind="character", type="farmer", label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type="cook", label=params.helper))
    tool = world.add(Entity(
        id="tool",
        kind="thing",
        type=TOOLS[params.tool].kind,
        label=TOOLS[params.tool].label,
        phrase=TOOLS[params.tool].phrase,
        owner=hero.id,
    ))
    food = world.add(Entity(
        id="food",
        kind="thing",
        type=FOODS[params.food].kind,
        label=FOODS[params.food].label,
        phrase=FOODS[params.food].phrase,
        owner=helper.id,
    ))
    world.facts.update(hero=hero, helper=helper, tool=tool, food=food,
                       tool_cfg=TOOLS[params.tool], food_cfg=FOODS[params.food],
                       setting=world.setting)
    return world


def _introduce(world: World) -> None:
    hero: Entity = world.facts["hero"]
    tool_cfg: Tool = world.facts["tool_cfg"]
    food_cfg: Food = world.facts["food_cfg"]
    world.say(
        f"{hero.id} was a tall-tale farmhand who liked to brag that {tool_cfg.boast}."
    )
    world.say(
        f"One bright day, {hero.id} eyed {hero.pronoun('possessive')} {tool_cfg.label} "
        f"and {food_cfg.phrase} on the same table."
    )
    world.say(
        f"The air over {world.setting.place} was windy, and even the scarecrow seemed to listen."
    )


def _conflict(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    tool_cfg: Tool = world.facts["tool_cfg"]
    food_cfg: Food = world.facts["food_cfg"]

    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    helper.memes["care"] = helper.memes.get("care", 0) + 1

    world.para()
    world.say(
        f"{hero.id} began to {tool_cfg.action}, and the earth opened in straight brown ribbons."
    )
    world.say(
        f"Then {helper.id} lifted the ramen and warned, "
        f"'"If you stamp that hard, the bowl will {food_cfg.slosh}."'
    )
    world.say(
        f"{hero.id} stood up straight and tried to assert, "
        f'"My way is the tallest way!"'
    )
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0) + 1
    helper.memes["worry"] = helper.memes.get("worry", 0) + 1

    if hero.memes["stubborn"] > 0:
        world.say(
            f"The words blew around like kite string, but they did not make the job go smoother."
        )
        world.say(
            f"The ramen trembled, and a little noodle broth dripped onto the dirt."
        )
        food = world.facts["food"]
        food.meters["mess"] = food.meters.get("mess", 0) + 1


def _reconciliation(world: World) -> None:
    hero: Entity = world.facts["hero"]
    helper: Entity = world.facts["helper"]
    tool_cfg: Tool = world.facts["tool_cfg"]
    food_cfg: Food = world.facts["food_cfg"]

    world.para()
    world.say(
        f"At last, {helper.id} laughed a soft laugh and said, "
        f'"A tall story is fine, but a good field needs a careful turn."'
    )
    world.say(
        f"{hero.id} looked at the crooked furrow, then at the wobbling ramen, and nodded."
    )
    world.say(
        f"{hero.id} took a slower grip on the {tool_cfg.label}, and {helper.id} steadied the bowl."
    )
    world.say(
        f"Together they worked side by side, and the plough made tidy lines through the soil."
    )
    world.say(
        f"The ramen stayed upright, warm as a little lantern, and the broth no longer ran away."
    )
    hero.memes["pride"] = 0
    hero.memes["reconciliation"] = 1
    helper.memes["reconciliation"] = 1
    world.facts["resolved"] = True
    world.facts["ending_image"] = (
        f"{hero.id} and {helper.id} shared the shade of the wagon, with "
        f"{food_cfg.label} safe and the field neatly ploughed."
    )


def tell_story(params: StoryParams) -> World:
    world = _setup_world(params)
    _introduce(world)
    _conflict(world)
    _reconciliation(world)
    return world


# ---------------------------------------------------------------------------
# QA helpers
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a tall-tale story for a young child about a plough, ramen, and an argument that ends in reconciliation.',
        f"Tell a story where {f['hero'].id} wants to use a {f['tool'].label} while {f['helper'].id} protects a bowl of {f['food'].label}.",
        f"Make a gentle farm story that includes the word assert and ends with two helpers working together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    helper: Entity = f["helper"]
    tool_cfg: Tool = f["tool_cfg"]
    food_cfg: Food = f["food_cfg"]
    return [
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {tool_cfg.action}, because {hero.pronoun('possessive')} plough was the proudest tool in the yard.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry about the ramen?",
            answer=f"{helper.id} worried that the ramen would spill because the hard stamping made the bowl wobble and the broth could {food_cfg.slosh}.",
        ),
        QAItem(
            question=f"How did the argument end?",
            answer=f"It ended in reconciliation: {hero.id} slowed down, {helper.id} steadied the bowl, and they finished the work together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a plough for?",
            answer="A plough is a farm tool used to cut and turn soil into neat furrows before planting.",
        ),
        QAItem(
            question="What is ramen?",
            answer="Ramen is a bowl of noodle soup, usually warm and slippery, with broth and curly noodles.",
        ),
        QAItem(
            question="What does it mean to assert something?",
            answer="To assert something means to say it with confidence, as if you really believe it.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation means making peace again after a disagreement, so people can work together kindly.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is reasonable when a ploughing action and a ramen-carrying helper
% create a conflict, then a reconciliation event clears the tension.
action_ok(plough).
food_ok(ramen).

conflict(plough, ramen) :- action_ok(plough), food_ok(ramen).
resolution(plough, ramen) :- conflict(plough, ramen).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("action_ok", "plough"),
        asp.fact("food_ok", "ramen"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _python_reasonable(params: StoryParams) -> bool:
    return params.tool in TOOLS and params.food in FOODS and params.place in SETTINGS


def asp_verify() -> int:
    try:
        import asp
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    model = asp.one_model(asp_program("#show conflict/2. #show resolution/2."))
    atoms = set((sym.name, tuple(arg.name if arg.type != arg.type.Number and arg.type != arg.type.String else None for arg in sym.arguments)) for sym in model)
    ok = bool(model)
    if ok:
        print("OK: ASP program solved.")
        return 0
    print("MISMATCH: ASP program did not produce a model.")
    return 1


# ---------------------------------------------------------------------------
# JSON / CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: plough, ramen, assert, reconciliation.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--tool", choices=sorted(TOOLS))
    ap.add_argument("--food", choices=sorted(FOODS))
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = args.place or rng.choice(sorted(SETTINGS))
    tool = args.tool or "plough"
    food = args.food or "ramen"
    if tool not in TOOLS or food not in FOODS:
        raise StoryError("Invalid tool or food.")
    hero = args.hero or rng.choice(HEROES)
    helper = args.helper or rng.choice(HELPERS)
    if tool != "plough":
        raise StoryError("This world is built around ploughing; choose --tool plough.")
    if food != "ramen":
        raise StoryError("This world is built around ramen; choose --food ramen.")
    return StoryParams(place=place, tool=tool, food=food, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type}) {' '.join(bits)}")
    lines.append(f"  ending: {world.facts.get('ending_image', '')}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
        print(asp_program("#show conflict/2. #show resolution/2."))
        return

    if args.verify:
        sys.exit(asp_verify())

    if args.asp:
        try:
            import asp
        except Exception as exc:
            print(f"ASP unavailable: {exc}")
            return
        model = asp.one_model(asp_program("#show conflict/2. #show resolution/2."))
        print("ASP model:")
        for sym in model:
            print(sym)
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        curated = [
            StoryParams(place="field", tool="plough", food="ramen", hero="Milo", helper="Aunt Maple"),
            StoryParams(place="valley", tool="plough", food="ramen", hero="Nia", helper="the cook"),
            StoryParams(place="hill", tool="plough", food="ramen", hero="Arlo", helper="Uncle Gus"),
        ]
        samples = [generate(p) for p in curated]
    else:
        for i in range(max(1, args.n)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))

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
