#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini/malapropism_accuracy_product_mystery_to_solve_conflict.py
=========================================================================================

A standalone storyworld for a small animal mystery quest about two friends,
a confusing malapropism, and a careful product test that solves a conflict.

The world is built around three seed words:
- malapropism
- accuracy
- product

and three narrative instruments:
- Mystery to Solve
- Conflict
- Quest

The story is intentionally small and classical: an animal protagonist notices a
mystery, makes a funny mistake, learns to check accuracy, and finishes the quest
with a clear change in the world state.
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
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
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

    tags: set[str] = field(default_factory=set)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "rooster"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.type



    @property
    def phrase(self) -> str:
        return getattr(self, "_phrase", None) or self.label or self.id.replace("_", " ")

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

@dataclass
class Place:
    id: str
    label: str
    mystery: str
    clue: str
    quest: str
    conflict: str
    product: str
    product_use: str
    resolution: str
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Animal:
    id: str
    type: str
    role: str
    label: str
    companion_word: str
    traits: list[str]
    relation: str

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


@dataclass
class Product:
    id: str
    label: str
    phrase: str
    use: str
    accurate: bool = True
    tags: set[str] = field(default_factory=set)

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
@dataclass
class StoryParams:
    place: str
    hero: str
    hero_type: str
    friend: str
    friend_type: str
    product: str
    seed: Optional[int] = None

    def __getattr__(self, name: str):
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name == "tags":
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word"}:
            return (getattr(self, "label", "") or getattr(self, "name", "") or getattr(self, "id", self.__class__.__name__.lower())).replace("_", " ")
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}[case]
        raise AttributeError(f"{self.__class__.__name__!r} object has no attribute {name!r}")


PLACES = {
    "barn": Place(
        "barn", "the old barn",
        mystery="a missing honey jar",
        clue="a tiny sticky trail on the floor",
        quest="search for the missing jar",
        conflict="the friends could not agree on what the sticky trail meant",
        product="map paste",
        product_use="stick labels onto the map",
        resolution="they checked the trail carefully and found the jar behind a hay bale",
        tags={"mystery", "quest", "conflict"},
    ),
    "garden": Place(
        "garden", "the garden path",
        mystery="a missing ribbon",
        clue="a pale thread caught on a rose bush",
        quest="follow the clue to the ribbon",
        conflict="one friend guessed too fast and the other wanted to look again",
        product="window polish",
        product_use="shine the clue marker",
        resolution="they followed the thread and found the ribbon in a bird nest",
        tags={"mystery", "quest", "conflict"},
    ),
    "pond": Place(
        "pond", "the pond bank",
        mystery="a missing bell",
        clue="small footprints in the mud",
        quest="track the footsteps to the bell",
        conflict="the first guess sounded fun, but it was not accurate",
        product="boat glue",
        product_use="mark the path on the quest chart",
        resolution="they followed the footprints and found the bell under a dock plank",
        tags={"mystery", "quest", "conflict"},
    ),
}

PRODUCTS = {
    "map paste": Product("map paste", "map paste", "a little jar of map paste", "stick labels onto the map", True, {"product"}),
    "window polish": Product("window polish", "window polish", "a bottle of window polish", "shine the clue marker", True, {"product"}),
    "boat glue": Product("boat glue", "boat glue", "a bottle of boat glue", "mark the quest chart", True, {"product"}),
}

ANIMALS = [
    ("Pip", "mouse", "scout", "little mouse", "partner"),
    ("Mimi", "cat", "leader", "curious cat", "partner"),
    ("Boo", "duck", "helper", "brave duck", "partner"),
    ("Tilly", "rabbit", "finder", "soft rabbit", "partner"),
    ("Wren", "fox", "checker", "clever fox", "partner"),
    ("Coco", "goat", "guide", "small goat", "partner"),
]


def _pick_names(rng: random.Random) -> tuple[tuple[str, str], tuple[str, str]]:
    hero = rng.choice(["Pip", "Mimi", "Boo", "Tilly", "Wren", "Coco"])
    friend = rng.choice([n for n in ["Pip", "Mimi", "Boo", "Tilly", "Wren", "Coco"] if n != hero])
    return (hero, rng.choice(["mouse", "cat", "duck", "rabbit", "fox", "goat"])), (
        friend, rng.choice(["mouse", "cat", "duck", "rabbit", "fox", "goat"])
    )


def _article(word: str) -> str:
    return "an" if word[0].lower() in "aeiou" else "a"


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in PLACES:
        for product in PRODUCTS:
            out.append((place, product))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal mystery quest storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--product", choices=PRODUCTS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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
              and (args.product is None or c[1] == args.product)]
    if not combos:
        raise StoryError("(No valid mystery quest matches the given options.)")
    place, product = rng.choice(sorted(combos))
    hero = args.hero or rng.choice(["Pip", "Mimi", "Boo", "Tilly", "Wren", "Coco"])
    friend = args.friend or rng.choice([n for n in ["Pip", "Mimi", "Boo", "Tilly", "Wren", "Coco"] if n != hero])
    return StoryParams(place=place, hero=hero, hero_type="animal", friend=friend, friend_type="animal", product=product)


def _render_story(world: World, params: StoryParams) -> None:
    place = world.place
    hero = world.get("hero")
    friend = world.get("friend")
    product = world.get("product")

    world.say(
        f"At {place.label}, {hero.id} and {friend.id} found a mystery to solve: {place.mystery}."
    )
    world.say(
        f"They began a quest to {place.quest}, following {place.clue} through the quiet paths."
    )
    world.para()
    world.say(
        f'{hero.id} pointed at the clue and said, "I know, this must be the '
        f"{place.product}."
    )
    world.say(
        f"{friend.id} blinked. \"That is a malapropism,\" {friend.id} said. "
        f"\"You mean the clue, not the product.\""
    )
    hero.memes["embarrassment"] += 1
    friend.memes["concern"] += 1
    world.say(
        f"{hero.id} frowned, because the first guess was not accurate."
    )
    world.para()
    world.say(
        f"The friends had a conflict for a moment: {place.conflict}."
    )
    world.say(
        f"Then they used {product.phrase} to {product.use}, and they checked the clue again."
    )
    hero.memes["determination"] += 1
    friend.memes["trust"] += 1
    world.say(
        f"This time they were careful and accurate. The clue led them to the right place."
    )
    world.para()
    world.say(
        f"In the end, {place.resolution}, and the mystery was solved."
    )
    world.say(
        f"{hero.id} and {friend.id} smiled, proud that the quest had taught them to look twice."
    )
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    world.facts.update(
        place=place, hero=hero, friend=friend, product=product,
        solved=True, malapropism=True, accuracy=True, conflict=True
    )


def generate(params: StoryParams) -> StorySample:
    place = PLACES[params.place]
    world = World(place)
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type, role="hero", label="the scout"))
    friend = world.add(Entity(id=params.friend, kind="character", type=params.friend_type, role="friend", label="the helper"))
    product = world.add(Entity(id="product", kind="thing", type="product", label=PRODUCTS[params.product].label))
    _render_story(world, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=[QAItem(q, a) for q, a in story_qa(world)],
        world_qa=[QAItem(q, a) for q, a in world_knowledge_qa(world)],
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    p = world.place
    return [
        f"Write an animal story with a mystery to solve at {p.label} that includes the word malapropism.",
        f"Tell a quest story where two animal friends argue, then use accuracy to solve the conflict.",
        f"Write a child-friendly story featuring the word product, a wrong guess, and a happy ending.",
    ]


def story_qa(world: World) -> list[tuple[str, str]]:
    p = world.place
    hero = world.get("hero")
    friend = world.get("friend")
    return [
        ("What kind of story is this?", "It is an animal story with a mystery, a conflict, and a quest. The friends work through a confusion and then solve it together."),
        ("What was the mystery?", f"The mystery was {p.mystery}. They followed a clue to find it."),
        ("What was the malapropism?", f"{hero.id} accidentally used the word {p.product} when talking about the clue. {friend.id} corrected the mistake so they could stay accurate."),
        ("How was the conflict solved?", f"They paused, checked the clue carefully, and used {p.product} to help with the quest. That accurate choice led them to the answer."),
    ]


def world_knowledge_qa(world: World) -> list[tuple[str, str]]:
    return [
        ("What is a malapropism?", "A malapropism is a funny mistake where someone uses the wrong word that sounds a little like the right one."),
        ("What does accuracy mean?", "Accuracy means being correct and careful, so your words or guesses match the truth."),
        ("What is a product?", "A product is something that is made or sold for people to use."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: kind={e.kind} type={e.type} role={e.role} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(P, R) :- place(P), product(R).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for r in PRODUCTS:
        lines.append(asp.fact("product", r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    ok = set(asp_valid_combos()) == set(valid_combos())
    sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
    crash_ok = bool(sample.story)
    if ok and crash_ok:
        print("OK: ASP parity and generation smoke test passed.")
        return 0
    print("MISMATCH or smoke test failure.")
    return 1


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
    StoryParams("barn", "Pip", "animal", "Mimi", "animal", "map paste"),
    StoryParams("garden", "Boo", "animal", "Wren", "animal", "window polish"),
    StoryParams("pond", "Tilly", "animal", "Coco", "animal", "boat glue"),
]


def main() -> None:
    args = build_parser().parse_args()
    if args.show_asp:
        print(asp_program("#show valid/2."))
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
        i = 0
        seen: set[str] = set()
        while len(samples) < args.n and i < max(args.n * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
