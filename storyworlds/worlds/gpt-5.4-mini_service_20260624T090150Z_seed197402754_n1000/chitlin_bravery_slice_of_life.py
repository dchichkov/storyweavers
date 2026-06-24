#!/usr/bin/env python3
"""
storyworlds/worlds/chitlin_bravery_slice_of_life.py
===================================================

A small slice-of-life storyworld about a child, a family meal, and the brave
little moment of trying something new.

Premise:
- A child is at home during an ordinary dinner.
- The child is curious about chitlins, a Southern dish served at the table.
- The child feels nervous because the smell and look are unfamiliar.
- A caring adult encourages a tiny act of bravery: try one bite.

The world model tracks:
- physical meters: amount eaten, steam, neatness, fullness
- emotional memes: nervousness, curiosity, bravery, pride, warmth

The story resolves when the child takes a bite, discovers they can be brave,
and the meal becomes a calm, happy family moment.
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
# World data
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=dict)
    memes: dict[str, float] = field(default_factory=dict)

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"


@dataclass
class Place:
    id: str
    label: str
    indoors: bool = True
    warmth: str = "cozy"
    table: str = "table"


@dataclass
class Food:
    id: str
    label: str
    phrase: str
    smell: str
    look: str
    taste: str
    bravery_need: str
    tags: set[str] = field(default_factory=set)


@dataclass
class StoryParams:
    place: str
    food: str
    hero_name: str
    hero_gender: str
    parent_type: str
    seed: Optional[int] = None


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "home_kitchen": Place(id="home_kitchen", label="the kitchen", indoors=True, warmth="cozy", table="dinner table"),
    "home_dining_room": Place(id="home_dining_room", label="the dining room", indoors=True, warmth="quiet", table="big table"),
}

FOODS = {
    "chitlin": Food(
        id="chitlin",
        label="chitlins",
        phrase="a small bowl of chitlins",
        smell="strong",
        look="shiny",
        taste="savory",
        bravery_need="take a brave bite",
        tags={"chitlin", "food", "meal", "bravery"},
    ),
    "greens": Food(
        id="greens",
        label="greens",
        phrase="a bowl of greens",
        smell="fresh",
        look="soft",
        taste="earthy",
        bravery_need="try a new bite",
        tags={"food", "meal"},
    ),
}

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ava", "Ivy", "Ruby"]
BOY_NAMES = ["Leo", "Eli", "Noah", "Finn", "Owen", "Sam"]


# ---------------------------------------------------------------------------
# Simulated world logic
# ---------------------------------------------------------------------------

def smell_is_unfamiliar(food: Food) -> bool:
    return food.id == "chitlin"


def do_dinner(world: World, hero: Entity, parent: Entity, food: Food) -> None:
    hero.memes["curiosity"] = 1.0
    hero.memes["nervousness"] = 1.0 if smell_is_unfamiliar(food) else 0.4
    hero.memes["bravery"] = 0.0
    hero.memes["pride"] = 0.0
    food_ent = world.add(Entity(
        id=food.id, type="food", label=food.label, phrase=food.phrase,
        meters={"served": 1.0, "steam": 1.0},
    ))
    world.facts["food_ent"] = food_ent
    world.say(f"{hero.id} sat at {world.place.label} with {hero.pronoun('possessive')} {parent.type} for dinner.")
    world.say(f"On the {world.place.table}, there was {food.phrase}, looking {food.look} and smelling {food.smell}.")
    if smell_is_unfamiliar(food):
        world.say(f"{hero.id} wrinkled {hero.pronoun('possessive')} nose a little.")
    else:
        world.say(f"{hero.id} leaned closer right away.")

def prompt_bravery(world: World, parent: Entity, hero: Entity, food: Food) -> None:
    hero.memes["nervousness"] += 0.5
    world.say(f"{parent.label.capitalize()} smiled and said, \"You do not have to love it, but you can be brave and try one small bite.\"")
    world.say(f"{hero.id} looked at the bowl and thought about {food.bravery_need}.")

def take_bite(world: World, hero: Entity, food: Food) -> None:
    hero.memes["bravery"] += 1.0
    hero.memes["nervousness"] = max(0.0, hero.memes["nervousness"] - 0.7)
    hero.meters["bites"] = hero.meters.get("bites", 0.0) + 1.0
    hero.meters["fullness"] = hero.meters.get("fullness", 0.0) + 0.5
    world.get(food.id).meters["eaten"] = world.get(food.id).meters.get("eaten", 0.0) + 1.0
    world.say(f"{hero.id} took one tiny bite.")
    if food.id == "chitlin":
        world.say(f"The taste was salty and warm, and it was not as scary as {hero.id} had imagined.")
    else:
        world.say(f"The flavor was simple, and {hero.id} realized trying something new could feel easy after all.")

def finish(world: World, hero: Entity, parent: Entity, food: Food) -> None:
    hero.memes["pride"] += 1.0
    hero.memes["warmth"] = 1.0
    world.say(f"{hero.id} smiled and took another bite.")
    world.say(f"{parent.label.capitalize()} laughed softly and said, \"That was brave.\"")
    world.say(f"By the end of dinner, {hero.id} was sitting happily at the table, feeling warm and proud.")


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combo(place_id: str, food_id: str) -> bool:
    return place_id in PLACES and food_id in FOODS


def valid_combos() -> list[tuple[str, str]]:
    return [(p, f) for p in PLACES for f in FOODS if valid_combo(p, f)]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
food(F) :- menu(F).

bravery_story(P, F) :- setting(P), menu(F), serves(P, F), interest(F), needs_bravery(F).
valid(P, F) :- bravery_story(P, F).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("serves", pid, "chitlin"))
        lines.append(asp.fact("serves", pid, "greens"))
    for fid, food in FOODS.items():
        lines.append(asp.fact("menu", fid))
        if food.id == "chitlin":
            lines.append(asp.fact("interest", fid))
            lines.append(asp.fact("needs_bravery", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def build_story(world: World, hero: Entity, parent: Entity, food: Food) -> None:
    do_dinner(world, hero, parent, food)
    world.para()
    prompt_bravery(world, parent, hero, food)
    take_bite(world, hero, food)
    finish(world, hero, parent, food)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    parent = f["parent"]
    food = f["food"]
    place = f["place"]
    return [
        f"Write a gentle slice-of-life story about {hero.id} at {place.label} trying {food.phrase} with help from {parent.label}.",
        f"Tell a short story for young children where a child feels nervous about {food.label} but finds bravery at dinner.",
        f"Write a homey story about family dinner, one small brave bite, and a child who feels proud afterward.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    parent: Entity = f["parent"]
    food: Food = f["food"]
    place: Place = f["place"]
    return [
        QAItem(
            question=f"Where was {hero.id} sitting when dinner started?",
            answer=f"{hero.id} was sitting at {place.label} with {parent.label.capitalize()} for dinner.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel nervous about {food.label}?",
            answer=f"{hero.id} felt nervous because {food.label} smelled {food.smell} and looked {food.look}, so it seemed unfamiliar at first.",
        ),
        QAItem(
            question=f"What did {parent.label.capitalize()} tell {hero.id} to do?",
            answer=f"{parent.label.capitalize()} told {hero.id} to be brave and try one small bite.",
        ),
        QAItem(
            question=f"What changed after {hero.id} took the bite?",
            answer=f"{hero.id} felt proud and calmer, and the dinner became a happy family moment.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when you feel a little scared.",
        ),
        QAItem(
            question="What is a family dinner?",
            answer="A family dinner is a meal where people sit together, talk, and eat at home.",
        ),
        QAItem(
            question="What is chitlins?",
            answer="Chitlins are a kind of food served as part of a meal, often with a strong smell and a savory taste.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
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


# ---------------------------------------------------------------------------
# CLI helpers
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about chitlins and bravery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if args.place:
        combos = [c for c in combos if c[0] == args.place]
    if args.food:
        combos = [c for c in combos if c[1] == args.food]
    if not combos:
        raise StoryError("(No valid combination matches the given options.)")
    place, food = rng.choice(sorted(combos))
    gender = args.gender or rng.choice(["girl", "boy"])
    name = args.name or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = args.parent or rng.choice(["mother", "father"])
    return StoryParams(place=place, food=food, hero_name=name, hero_gender=gender, parent_type=parent)


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    food = FOODS[params.food]
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=params.parent_type, label="parent"))
    world.facts.update(hero=hero, parent=parent, food=food, place=place)
    build_story(world, hero, parent, food)
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
    if set(asp_valid_combos()) == set(valid_combos()):
        print("OK: ASP parity matches Python valid_combos().")
        return 0
    print("MISMATCH between ASP and Python valid_combos().")
    print("Python:", sorted(valid_combos()))
    print("ASP:", sorted(asp_valid_combos()))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if args.show_asp:
        print(asp_program("#show valid/2."))
        return
    if args.verify:
        sys.exit(asp_verify())
    if args.asp:
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, food in combos:
            print(f"  {place}  {food}")
        return

    base_seed = args.seed if args.seed is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if args.all:
        for place in PLACES:
            for food in FOODS:
                p = StoryParams(place=place, food=food, hero_name="Mia", hero_gender="girl", parent_type="mother")
                samples.append(generate(p))
    else:
        seen = set()
        i = 0
        while len(samples) < args.n and i < max(args.n * 20, 20):
            i += 1
            seed = base_seed + i
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
