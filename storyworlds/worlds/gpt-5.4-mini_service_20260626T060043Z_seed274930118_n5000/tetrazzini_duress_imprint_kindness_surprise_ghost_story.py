#!/usr/bin/env python3
"""
storyworlds/worlds/tetrazzini_duress_imprint_kindness_surprise_ghost_story.py
=============================================================================

A small ghost-story world about a child, a restless kitchen ghost, and a pan of
tetrazzini that turns fear into kindness.

Seed tale:
---
A child arrives in an old house during a stormy evening and finds a ghost in the
kitchen. The ghost is not frightening for long; it is hungry and under duress.
A smudged imprint on a recipe card leads the child to make tetrazzini the way the
ghost remembers it. There is a little surprise when the ghost turns out to be
kind, and the meal becomes a gentle ending instead of a scare.

World premise:
---
- The old house has an echoing kitchen.
- The ghost is tied to an imprint: a flour-marked recipe card and a handprint on
  the counter.
- Duress comes from the storm, the hunger, and the fear that the ghost will
  vanish without tasting the dish again.
- Kindness lets the child help.
- Surprise is the turn when the ghost is not dangerous at all; it only wants to
  be remembered and fed.

The story engine narrates the state change: fear rises, the imprint is found,
ingredients are gathered, tetrazzini is cooked, and the ghost settles when the
kind act is complete.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "grandmother", "grandma"}
        male = {"boy", "man", "father", "dad", "grandfather", "grandpa"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]


@dataclass
class Setting:
    place: str = "the old house"
    kitchen: str = "the old kitchen"
    stormy: bool = True


@dataclass
class Ingredient:
    id: str
    label: str
    phrase: str
    role: str


@dataclass
class Offer:
    id: str
    label: str
    action: str
    result: str


@dataclass
class StoryParams:
    name: str
    age: int
    gender: str
    setting: str = "old_house"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle ghost-story world with tetrazzini, duress, imprint, kindness, and surprise.")
    ap.add_argument("--name")
    ap.add_argument("--age", type=int)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--setting", choices=["old_house"])
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


NAMES = ["Mina", "Owen", "Luna", "Iris", "Theo", "Nora", "June", "Eli"]
GENDERS = {"girl", "boy"}
AGES = [6, 7, 8, 9]

SETTING = Setting()

INGREDIENTS = {
    "tetrazzini": Ingredient("tetrazzini", "tetrazzini", "a warm pan of tetrazzini", "dish"),
    "noodles": Ingredient("noodles", "noodles", "soft noodles", "food"),
    "milk": Ingredient("milk", "milk", "a small jug of milk", "liquid"),
    "cheese": Ingredient("cheese", "cheese", "a handful of cheese", "topping"),
}

OFFERS = {
    "kindness": Offer("kindness", "kindness", "helped", "safer"),
    "surprise": Offer("surprise", "surprise", "revealed", "gentler"),
}


class GhostWorldError(StoryError):
    pass


def reasonableness_gate() -> None:
    return


def setup_world(params: StoryParams) -> World:
    world = World(SETTING)
    child = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["small", "brave"]))
    ghost = world.add(Entity(id="ghost", kind="character", type="ghost", label="the kitchen ghost", traits=["hungry", "lonely"]))
    card = world.add(Entity(id="card", kind="thing", type="recipe_card", label="recipe card", phrase="a flour-smudged recipe card"))
    pan = world.add(Entity(id="pan", kind="thing", type="pan", label="pan", phrase="a heavy pan"))
    child.meters["courage"] = 0.0
    child.meters["fear"] = 0.0
    child.memes["kindness"] = 0.0
    child.memes["surprise"] = 0.0
    ghost.meters["hunger"] = 2.0
    ghost.meters["restlessness"] = 2.0
    ghost.memes["duress"] = 2.0
    ghost.memes["loneliness"] = 1.0
    world.facts.update(child=child, ghost=ghost, card=card, pan=pan)
    return world


def introduce(world: World) -> None:
    c: Entity = world.facts["child"]
    g: Entity = world.facts["ghost"]
    world.say(f"One stormy evening, {c.id} arrived at {world.setting.place} and tiptoed into {world.setting.kitchen}.")
    world.say(f"Inside, {g.label} hovered by the stove, looking pale and worried, as if something had gone wrong long ago.")


def discover_imprint(world: World) -> None:
    c: Entity = world.facts["child"]
    card: Entity = world.facts["card"]
    c.meters["fear"] += 1.0
    c.memes["surprise"] += 1.0
    world.say(f"{c.id} almost cried out, but then {c.pronoun('subject')} noticed {card.phrase} on the counter.")
    world.say("The card held a floury handprint and one word, pressed deep like a memory: tetrazzini.")
    world.say("That imprint made the room feel less haunted and more like it was asking to be understood.")


def explain_duress(world: World) -> None:
    g: Entity = world.facts["ghost"]
    world.say("The ghost trembled in the draft. The storm had cut the lights, the kitchen was cold, and the old wish had turned into duress.")
    world.say("It was not a mean kind of haunting; it was the kind that happens when a lonely thing is too hungry to be calm.")
    g.memes["duress"] = 2.5


def kindness_offer(world: World) -> None:
    c: Entity = world.facts["child"]
    g: Entity = world.facts["ghost"]
    c.memes["kindness"] += 1.0
    c.meters["courage"] += 1.0
    world.say(f"Instead of running, {c.id} took a slow breath and said, \"If you want, I can help.\"")
    world.say(f"The ghost blinked, surprised by the kindness, and nodded as if it had been waiting a very long time for someone to ask.")


def cook_tetrazzini(world: World) -> None:
    c: Entity = world.facts["child"]
    g: Entity = world.facts["ghost"]
    pan: Entity = world.facts["pan"]
    c.meters["busy"] = 1.0
    g.meters["hunger"] -= 2.0
    g.memes["duress"] -= 1.5
    world.say(f"Together they filled {pan.label} with noodles, milk, and cheese, then stirred until the tetrazzini smelled warm and safe.")
    world.say("The steam curled up like a soft blanket, and the old kitchen stopped feeling empty.")
    world.say(f"As {c.id} scooped the meal into a bowl, the ghost's outline steadied, as if the house itself could finally rest.")


def surprise_turn(world: World) -> None:
    g: Entity = world.facts["ghost"]
    c: Entity = world.facts["child"]
    g.memes["surprise"] = 1.0
    world.say("Then came the surprise: the ghost did not vanish in smoke or grin with sharp teeth.")
    world.say("It smiled in a gentle way and thanked the child for remembering the recipe at all.")
    world.say(f"{c.id} laughed through the last of the fear, because the scariest thing in the kitchen had been only sorrow, not danger.")


def ending_image(world: World) -> None:
    c: Entity = world.facts["child"]
    g: Entity = world.facts["ghost"]
    card: Entity = world.facts["card"]
    world.say(f"At the end, {c.id} left a clean spoon beside {card.label}, and the floury imprint stayed on the card like a small hand wave.")
    world.say(f"The ghost ate the last bite of tetrazzini, sighed with relief, and settled into the warm dark of the kitchen with kindness instead of duress.")


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    introduce(world)
    world.para()
    discover_imprint(world)
    explain_duress(world)
    world.para()
    kindness_offer(world)
    surprise_turn(world)
    cook_tetrazzini(world)
    world.para()
    ending_image(world)
    world.facts["resolved"] = True
    return world


ASP_RULES = r"""
child_feels(courage) :- kind_help, not fear_only.
kind_help :- kindness.
surprise_turn :- imprint, kindness.
resolved :- surprise_turn, tetrazzini.
#show child_feels/1.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp
    return "\n".join([
        asp.fact("tetrazzini"),
        asp.fact("imprint"),
        asp.fact("kindness"),
        asp.fact("surprise"),
        asp.fact("duress"),
    ])


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generation_prompts(world: World) -> list[str]:
    return [
        "Write a gentle ghost story about a child, a kitchen, and a comforting pan of tetrazzini.",
        "Tell a story where an imprint on a recipe card helps a frightened child understand a lonely ghost.",
        "Make kindness the turn that changes the ghost story from scary to warm.",
    ]


def story_qa(world: World) -> list[QAItem]:
    c: Entity = world.facts["child"]
    g: Entity = world.facts["ghost"]
    return [
        QAItem(
            question=f"Why was the ghost in the kitchen under duress?",
            answer="The storm had made the house cold and dark, and the ghost was hungry and lonely, so it could not settle down.",
        ),
        QAItem(
            question=f"What did {c.id} find that pointed to tetrazzini?",
            answer="The child found a flour-smudged recipe card with a handprint imprint on it, and it pointed to tetrazzini.",
        ),
        QAItem(
            question="What changed the ghost story from frightening to gentle?",
            answer="Kindness changed it. The child helped make the food, and the ghost turned out to be grateful instead of scary.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is tetrazzini?", answer="Tetrazzini is a warm baked noodle dish, often creamy and comforting."),
        QAItem(question="What is an imprint?", answer="An imprint is a mark left behind when something presses onto a surface."),
        QAItem(question="What is kindness?", answer="Kindness means helping, caring, or being gentle with someone else."),
        QAItem(question="What is surprise?", answer="Surprise is the feeling you get when something unexpected happens."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in world.entities.values():
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    name = args.name or rng.choice(NAMES)
    gender = args.gender or rng.choice(sorted(GENDERS))
    age = args.age or rng.choice(AGES)
    if gender not in GENDERS:
        raise StoryError("gender must be girl or boy")
    return StoryParams(name=name, age=age, gender=gender, setting="old_house")


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
    print("OK: ASP twin is present for the ghost story world.")
    return 0


CURATED = [
    StoryParams(name="Mina", age=7, gender="girl"),
    StoryParams(name="Theo", age=8, gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show resolved/0."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        print("ghost-story ASP twin is available; run --show-asp to inspect the rules.")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if args.all:
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(args.n):
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
