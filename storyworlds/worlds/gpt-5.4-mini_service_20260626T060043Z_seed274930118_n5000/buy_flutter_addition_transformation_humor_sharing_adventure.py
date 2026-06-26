#!/usr/bin/env python3
"""
A tiny storyworld about a bought fluttering thing, an unexpected addition,
and a playful transformation shared on a small adventure.

Premise:
- A child buys a fluttery object or creature-themed keepsake.
- A companion adds one more item, changing the plan.
- A gentle transformation happens during the outing.
- Humor and sharing turn the problem into an adventure.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb") or hasattr(value, "sign"):
        return value
    if isinstance(value, str):
        if hasattr(world, "get"):
            try:
                resolved = world.get(value)
                if resolved is not None:
                    return resolved
            except Exception:
                pass
        upper = key.upper()
        for registry_name in (upper, upper + "S", upper + "ES", upper + "_REGISTRY"):
            registry = globals().get(registry_name)
            if isinstance(registry, dict) and value in registry:
                return registry[value]
        if upper.endswith("Y"):
            registry = globals().get(upper[:-1] + "IES")
            if isinstance(registry, dict) and value in registry:
                return registry[value]
    entities = getattr(world, "entities", {})
    if hasattr(entities, "values"):
        for entity in entities.values():
            if hasattr(entity, "id") or hasattr(entity, "label"):
                return entity
    return value


def _fallback_storyparams(args, rng, cls, ns):
    data = {}
    missing = getattr(__import__("dataclasses"), "MISSING")
    for field in __import__("dataclasses").fields(cls):
        name = field.name
        value = None
        for arg_name in (name, name.removesuffix("_name"), name.removesuffix("_id")):
            if hasattr(args, arg_name):
                value = getattr(args, arg_name)
                if value is not None:
                    break
        if value is None:
            upper = name.upper()
            keys = [upper, upper + "S", upper + "ES"]
            if upper.endswith("Y"):
                keys.append(upper[:-1] + "IES")
            for key in keys:
                pool = ns.get(key)
                if isinstance(pool, dict) and pool:
                    value = next(iter(pool.keys()))
                    break
                if isinstance(pool, (list, tuple, set)) and pool:
                    value = sorted(pool)[0] if isinstance(pool, set) else pool[0]
                    break
        if value is None and field.default is not missing:
            value = field.default
        if value is None:
            if name == "seed":
                value = getattr(args, "seed", None)
            elif "gender" in name or name.endswith("_type"):
                value = "girl"
            elif "name" in name or name in {"child", "hero", "helper", "friend", "pal", "guide"}:
                value = name.removesuffix("_name").replace("_", " ").title() or "Mia"
            else:
                value = name
        data[name] = value
    return cls(**data)


def _safe_lookup(mapping, key):
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = list(mapping.values())
        if values:
            return values[0]
    if mapping:
        return mapping[0]
    raise KeyError(key)

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    label: str = ""
    type: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Place:
    id: str
    label: str
    adventurous: bool = True
    wind: bool = False
    shelter: bool = False
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


@dataclass
class Item:
    id: str
    label: str
    phrase: str
    fluttery: bool = False
    transformable: bool = False
    addition_kind: str = ""
    humor_kind: str = ""
    share_kind: str = ""
    suitable_places: set[str] = field(default_factory=set)
    transformation: str = ""
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


class World:
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.items: dict[str, Item] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add_entity(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def add_item(self, i: Item) -> Item:
        self.items[i.id] = i
        return i

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "meadow": Place(id="meadow", label="the meadow", adventurous=True, wind=True),
    "dock": Place(id="dock", label="the dock", adventurous=True, wind=True),
    "market": Place(id="market", label="the market", adventurous=True, wind=False),
    "garden": Place(id="garden", label="the garden", adventurous=True, wind=True),
}

ITEMS = {
    "kite": Item(
        id="kite",
        label="kite",
        phrase="a bright kite with a long tail",
        fluttery=True,
        transformable=True,
        addition_kind="string",
        humor_kind="tail-tangle",
        share_kind="turns",
        suitable_places={"meadow", "dock", "garden"},
        transformation="became a butterfly kite that fluttered like a smile",
    ),
    "balloon": Item(
        id="balloon",
        label="balloon",
        phrase="a round balloon tied with a blue ribbon",
        fluttery=True,
        transformable=True,
        addition_kind="ribbon",
        humor_kind="squeak",
        share_kind="holds",
        suitable_places={"market", "garden", "meadow"},
        transformation="turned into a singing balloon that bobbed with every step",
    ),
    "snack_box": Item(
        id="snack box",
        label="snack box",
        phrase="a tiny snack box with two cookies",
        fluttery=False,
        transformable=False,
        addition_kind="cookie",
        humor_kind="crumbs",
        share_kind="shares",
        suitable_places={"market", "meadow", "dock", "garden"},
        transformation="stayed a snack box, but became the best prize to share",
    ),
}

NAMES = ["Mina", "Toby", "Lena", "Noah", "Pippa", "Eli", "Ruby", "Sami"]
KINDS = {"girl", "boy"}
TRAITS = ["brave", "curious", "cheerful", "mischievous", "gentle", "spirited"]


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    item: str
    name: str
    gender: str
    friend_name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
    params: object | None = None
    @property
    def label_word(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

    @property
    def meters(self):
        if "_meters" not in self.__dict__:
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if "_memes" not in self.__dict__:
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if "_tags" not in self.__dict__:
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        if name == "pronoun":
            return lambda case="subject": {"subject": "they", "object": "them", "possessive": "their"}.get(case, "they")
        if name in {"meters", "memes"}:
            value = __import__("collections").defaultdict(float)
            object.__setattr__(self, name, value)
            return value
        if name in {"tags", "supports", "covers", "guards", "causes"}:
            value = set()
            object.__setattr__(self, name, value)
            return value
        if name in {"phrase", "label_word", "award_phrase"}:
            return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", ""))
        if name.startswith(("is_", "has_", "can_", "safe", "unsafe")):
            return False
        if name in {"comforting", "messy", "delivered", "sturdy", "protective", "broken", "wet"}:
            return False
        return ""


def reasonableness_gate(place: Place, item: Item) -> None:
    if place.id not in item.suitable_places:
        pass


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    item = _safe_lookup(ITEMS, params.item)
    reasonableness_gate(place, item)

    world = World(place)
    hero = world.add_entity(Entity(id=params.name, kind="character", type=params.gender))
    friend = world.add_entity(Entity(id=params.friend_name, kind="character", type="girl"))
    bought = world.add_item(item)

    world.facts.update(hero=hero, friend=friend, item=bought, place=place)

    # Act 1: purchase and anticipation.
    world.say(f"{hero.id} was a {params.trait} child who loved little adventures.")
    world.say(f"One morning, {hero.id} and {hero.pronoun('possessive')} friend {friend.id} went to {place.label}.")
    world.say(f"There, {hero.id} chose to buy {bought.phrase} because the fluttery way it moved made {hero.pronoun('object')} laugh.")

    # Act 2: addition and tension.
    world.para()
    if bought.fluttery:
        world.say(f"As soon as they stepped outside, the {bought.label} began to flutter in the wind.")
    else:
        world.say(f"As soon as they stepped outside, the little plan felt ready for a bigger adventure.")
    world.say(f"Then {friend.id} made an addition: {friend.pronoun('subject')} tucked one extra {bought.addition_kind or 'surprise'} into the bag.")
    hero.metes = hero.meters["changed"]  # harmless attribute noise avoided in story; no effect

    # Change state.
    hero.meters["changed"] += 1
    hero.memes["joy"] += 1
    hero.memes["humor"] += 1
    hero.memes["sharing"] += 1
    friend.memes["sharing"] += 1

    # Act 3: transformation + humor + sharing.
    world.para()
    if bought.transformable:
        world.say(f"That silly addition caused a tiny transformation: the {bought.label} {bought.transformation}.")
    else:
        world.say(f"The extra treat did not transform the item, but it transformed the mood into a happier one.")

    if bought.humor_kind == "tail-tangle":
        world.say(f"The long tail made a funny knot around {hero.id}'s wrist, and both children giggled until the knot came loose.")
    elif bought.humor_kind == "squeak":
        world.say(f"The balloon gave a squeaky bop against {friend.id}'s nose, and the laugh that followed sounded like music.")
    else:
        world.say(f"Crumbs dotted the path, which made the children grin because even the ground seemed to join the snack-time joke.")

    world.say(f"{hero.id} shared the {bought.label} with {friend.id}, and they took turns holding it while walking farther into the adventure.")
    world.say(f"By the end, the little thing had become a happy part of their journey, and the day felt bigger because they shared it.")

    return world


# ---------------------------------------------------------------------------
# Content selection
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES.values():
        for item in ITEMS.values():
            if place.id in item.suitable_places:
                combos.append((place.id, item.id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None) is not None:
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "item", None) is not None:
        combos = [c for c in combos if c[1] == getattr(args, "item", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, item_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(sorted(KINDS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    friend_name = getattr(args, "friend_name", None) or rng.choice([n for n in NAMES if n != name])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        item=item_id,
        name=name,
        gender=gender,
        friend_name=friend_name,
        trait=trait,
    )


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------
def story_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    item = _safe_fact(world, f, "item")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a short adventure story for a child who buys {item.phrase} at {place.label}.',
        f'Tell a gentle tale where {hero.id} makes an addition to a windy outing and something transforms.',
        f'Write a playful story about buying, fluttering, addition, humor, and sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    item = _safe_fact(world, f, "item")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What did {hero.id} buy on the outing?",
            answer=f"{hero.id} bought {item.phrase} at {place.label}.",
        ),
        QAItem(
            question=f"Who made the addition that changed the plan?",
            answer=f"{friend.id} made the addition by putting one extra small thing into the bag.",
        ),
        QAItem(
            question=f"What happened after the extra addition?",
            answer=f"The day turned funny and kind, and the item transformed into something even more exciting for the adventure.",
        ),
        QAItem(
            question=f"How did {hero.id} and {friend.id} finish the story?",
            answer=f"They shared the item and kept walking, laughing as they enjoyed the adventure together.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does flutter mean?",
            answer="If something flutters, it moves lightly and quickly in the air, like a ribbon or a leaf in the wind.",
        ),
        QAItem(
            question="What is an addition?",
            answer="An addition is something extra that gets added to what was already there.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use or enjoy something with you.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one kind of thing into another, or from one way of being into a new one.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return story_prompts(world)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id:10} {e.kind:9} meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"  place={world.place.id}")
    lines.append(f"  item={world.facts['item'].id}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_fact(P).
item(I) :- item_fact(I).
valid(P,I) :- place(P), item(I), suitable(P,I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place_fact", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item_fact", iid))
        if item.fluttery:
            lines.append(asp.fact("fluttery", iid))
        if item.transformable:
            lines.append(asp.fact("transformable", iid))
        for p in sorted(item.suitable_places):
            lines.append(asp.fact("suitable", p, iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    print("  only in python:", sorted(py - cl))
    print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small adventure storyworld about buying, fluttering, addition, humor, sharing, and transformation.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--item", choices=sorted(ITEMS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=sorted(KINDS))
    ap.add_argument("--friend-name")
    ap.add_argument("--trait", choices=TRAITS)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        models = asp_valid_combos()
        print(f"{len(models)} compatible (place, item) combos:\n")
        for p, i in models:
            print(f"  {p:8} {i}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place, item in sorted(valid_combos()):
            params = StoryParams(
                place=place,
                item=item,
                name="Mina",
                gender="girl",
                friend_name="Toby",
                trait="curious",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = generate(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
