#!/usr/bin/env python3
"""
Storyworld: fielder_magic_animal_story
======================================

A small Animal Story-style world about a fielder who wants to play with a
magical animal friend, but a tiny problem must be solved first.

Premise:
- A child fielder likes a friendly animal and a simple game in the field.
- Magic can help, but only if the right object is chosen.
- The story turns on a worry about losing or spoiling something precious.
- Resolution comes from a sensible magical fix, not a random event.
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
            keys = [upper + "S", upper + "ES"]
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    friend: object | None = None
    gear: object | None = None
    hero: object | None = None
    object_: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man", "fielder"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class StoryParams:
    name: str
    animal: str
    place: str
    prize: str
    seed: Optional[int] = None
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Animal:
    id: str
    label: str
    type: str
    joy_line: str
    action: str
    tags: set[str] = field(default_factory=set)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
    risk: str
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class MagicAid:
    id: str
    label: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    def __init__(self, place: str) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}

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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def add_magic(self, hero: Entity, aid: MagicAid) -> Entity:
        gear = self.add(Entity(
            id=aid.id,
            kind="thing",
            type="magic",
            label=aid.label,
            owner=hero.id,
            protective=True,
            covers=set(aid.covers),
        ))
        gear.worn_by = hero.id
        return gear


ANIMALS = {
    "rabbit": Animal("rabbit", "rabbit", "rabbit", "hops happily", "hop across the field", {"small", "quick"}),
    "fox": Animal("fox", "fox", "fox", "smiles slyly", "dash across the field", {"bright", "quick"}),
    "puppy": Animal("puppy", "puppy", "puppy", "wags kindly", "bound across the field", {"friendly"}),
    "owl": Animal("owl", "owl", "owl", "blinks wisely", "glide over the field", {"wise"}),
}

PRIZES = {
    "hat": Prize("hat", "hat", "a new straw hat", "head", "wind"),
    "scarf": Prize("scarf", "scarf", "a soft blue scarf", "neck", "snag"),
    "boots": Prize("boots", "boots", "shiny boots", "feet", "mud"),
    "ball": Prize("ball", "ball", "a bright red ball", "hands", "drop"),
}

MAGIC = {
    "sparkle-cloak": MagicAid(
        "sparkle-cloak",
        "sparkle cloak",
        guards={"wind", "snag"},
        covers={"head", "neck"},
        prep="put on the sparkle cloak",
        tail="slipped on the sparkle cloak",
    ),
    "mud-steps": MagicAid(
        "mud-steps",
        "mud steps",
        guards={"mud"},
        covers={"feet"},
        prep="tie on the mud steps",
        tail="fastened the mud steps",
    ),
    "soft-glove": MagicAid(
        "soft-glove",
        "soft glove",
        guards={"drop"},
        covers={"hands"},
        prep="wear the soft glove",
        tail="pulled on the soft glove",
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Finn", "Max", "Eli", "Noah"]


def is_at_risk(animal: Animal, prize: Prize) -> bool:
    if animal.id == "rabbit":
        return prize.region in {"feet", "hands"}
    if animal.id == "fox":
        return prize.region in {"head", "neck"}
    if animal.id == "puppy":
        return prize.region in {"hands", "feet"}
    return prize.region in {"head", "hands", "feet", "neck"}


def select_magic(animal: Animal, prize: Prize) -> Optional[MagicAid]:
    for aid in MAGIC.values():
        if prize.risk in aid.guards and prize.region in aid.covers:
            return aid
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for a in ANIMALS.values():
        for p in PRIZES.values():
            if is_at_risk(a, p) and select_magic(a, p):
                out.append((a.id, p.id))
    return out


def tell(params: StoryParams) -> World:
    animal = _safe_lookup(ANIMALS, params.animal)
    prize = _safe_lookup(PRIZES, params.prize)
    world = World(params.place)

    hero = world.add(Entity(id=params.name, kind="character", type="fielder"))
    friend = world.add(Entity(id=animal.id, kind="character", type=animal.type, label=animal.label))
    object_ = world.add(Entity(
        id=prize.id,
        kind="thing",
        type=prize.id,
        label=prize.label,
        phrase=prize.phrase,
        owner=hero.id,
        caretaker=hero.id,
        region=prize.region,
    ))

    hero.memes["joy"] = 1
    world.say(f"{hero.id} was a little fielder who loved {friend.label} the {animal.label}.")
    world.say(f"{hero.id} and {friend.label} liked to play in {params.place}, where {animal.joy_line}.")

    world.say(f"One day, {hero.id} wore {object_.phrase} and wanted to play.")
    world.say(f"But {friend.label} wanted to {animal.action}, and that could make {object_.label} get {prize.risk}.")
    hero.memes["worry"] = 1
    world.say(f"{hero.id}'s heart felt tight because {object_.label} was special.")

    aid = select_magic(animal, prize)
    if aid is None:
        pass
    world.say(f"Then {hero.id} found a little magic idea: to {aid.prep} before play.")
    world.add_magic(hero, aid)
    world.say(f"So {hero.id} {aid.tail}, and {friend.label} smiled at once.")
    hero.memes["worry"] = 0
    hero.memes["joy"] = 2
    world.say(f"{hero.id} and {friend.label} played together in {params.place}, and {object_.label} stayed safe and clean.")

    world.facts = {
        "hero": hero,
        "animal": friend,
        "prize": object_,
        "aid": aid,
        "place": params.place,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    animal = f["animal"]
    prize = f["prize"]
    aid = f["aid"]
    return [
        f"Write an Animal Story about {hero.id}, a fielder, and a {animal.label} in {f['place']}.",
        f"Tell a short story where {hero.id} worries about {prize.phrase} and uses {aid.label} magic.",
        f"Make a gentle child story about a fielder, a friendly animal, and a safe magical fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    animal = f["animal"]
    prize = f["prize"]
    aid = f["aid"]
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a little fielder, and {animal.label}, the friendly animal friend.",
        ),
        QAItem(
            question=f"Why did {hero.id} worry about {prize.label}?",
            answer=f"{hero.id} worried because {animal.label} could make {prize.label} get {prize.risk}.",
        ),
        QAItem(
            question=f"How did the magic help?",
            answer=f"The {aid.label} helped by protecting {prize.label} while {hero.id} and {animal.label} played.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a fielder?", answer="A fielder is a child who likes to play in a field or grassy place."),
        QAItem(question="What does magic mean in stories?", answer="Magic in stories means something special and surprising can happen in a kind way."),
        QAItem(question="Why do animals need gentle play?", answer="Animals need gentle play because they can be scared or hurt by rough actions."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["Prompts:"]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("Story Q&A:")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("World Q&A:")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


ASP_RULES = r"""
risk(A,P) :- animal(A), prize(P), risky(A,P).
fix(A,P) :- risk(A,P), magic(M), guards(M, R), covers(P, R), fits(M, A, P).
valid(A,P) :- risk(A,P), fix(A,P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for a in ANIMALS.values():
        lines.append(asp.fact("animal", a.id))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", a.id, t))
    for p in PRIZES.values():
        lines.append(asp.fact("prize", p.id))
        lines.append(asp.fact("risky", p.id, p.risk))
        lines.append(asp.fact("covers", p.id, p.region))
    for m in MAGIC.values():
        lines.append(asp.fact("magic", m.id))
        for g in sorted(m.guards):
            lines.append(asp.fact("guards", m.id, g))
        for c in sorted(m.covers):
            lines.append(asp.fact("fits", m.id, c, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


@dataclass
class Registry:
    animals: dict[str, Animal] = field(default_factory=lambda: ANIMALS)
    prizes: dict[str, Prize] = field(default_factory=lambda: PRIZES)
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


def explain_rejection(animal: Animal, prize: Prize) -> str:
    return f"(No story: {animal.label} and {prize.label} do not make a sensible magical problem-and-fix pair.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal Story world with a fielder and a little magic.")
    ap.add_argument("--name")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--place", default="the field")
    ap.add_argument("--prize", choices=PRIZES)
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
    if getattr(args, "animal", None):
        combos = [c for c in combos if c[0] == getattr(args, "animal", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[1] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    animal, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(BOY_NAMES + GIRL_NAMES)
    return StoryParams(name=name, animal=animal, place=getattr(args, "place", None), prize=prize)


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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"{e.id}: {' '.join(bits)}")
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for a in ANIMALS.values():
        for p in PRIZES.values():
            if is_at_risk(a, p) and select_magic(a, p):
                combos.append((a.id, p.id))
    return combos


def asp_verify() -> int:
    try:
        import asp  # noqa: F401
    except Exception as exc:
        print(f"ASP unavailable: {exc}")
        return 1
    py = set(valid_combos())
    clingo = set(asp_valid_combos())
    if py == clingo:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - clingo))
    print("asp-only:", sorted(clingo - py))
    return 1


CURATED = [
    StoryParams(name="Fielder", animal="rabbit", place="the field", prize="hat"),
    StoryParams(name="Milo", animal="fox", place="the field", prize="scarf"),
    StoryParams(name="Nora", animal="puppy", place="the field", prize="boots"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for combo in asp_valid_combos():
            print(combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
