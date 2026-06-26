#!/usr/bin/env python3
"""
A tiny storyworld for a chemist in a nursery-rhyme style.

Premise:
A cheerful chemist in a small lab wants to make a fizzy, glowing potion.
The potion almost turns into a silly mess, but a careful helper and a gentle
fix turn the day into a bright, rhyming ending.

This world uses a small simulation with physical meters and emotional memes,
plus a Python reasonableness gate and an inline ASP twin.
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
# Domain registries
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
class Room:
    name: str
    mood: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Potion:
    name: str
    base: str
    effect: str
    mess: str
    rhyme: str
    requires: set[str] = field(default_factory=set)
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


@dataclass
class Tool:
    name: str
    protects_from: set[str] = field(default_factory=set)
    helps_with: set[str] = field(default_factory=set)
    is_protective: bool = False
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


ROOMS = {
    "lab": Room(name="the little lab", mood="bright", affords={"mix", "boil", "glow"}),
    "kitchen": Room(name="the kitchen nook", mood="cozy", affords={"mix", "boil"}),
    "garden_shed": Room(name="the garden shed", mood="plain", affords={"mix", "glow"}),
}

POTIONS = {
    "fizzy": Potion(
        name="fizzy potion",
        base="bubbly liquid",
        effect="sparkle",
        mess="foamy",
        rhyme="bubble-trubble",
        requires={"stir", "heat"},
    ),
    "glow": Potion(
        name="glow potion",
        base="moon-sweet syrup",
        effect="glow",
        mess="sticky",
        rhyme="glow-show",
        requires={"stir", "light"},
    ),
    "color": Potion(
        name="color potion",
        base="rainbow tea",
        effect="paint",
        mess="splashed",
        rhyme="splash-catch",
        requires={"stir"},
    ),
}

TOOLS = {
    "goggles": Tool(
        name="goggles",
        protects_from={"foam", "splash", "spark"},
        helps_with={"mix"},
        is_protective=True,
    ),
    "apron": Tool(
        name="an apron",
        protects_from={"foam", "sticky", "splashed"},
        helps_with={"mix", "boil"},
        is_protective=True,
    ),
    "ladle": Tool(
        name="a ladle",
        helps_with={"stir"},
        is_protective=False,
    ),
    "lantern": Tool(
        name="a lantern",
        helps_with={"glow"},
        is_protective=False,
    ),
}

HERO_NAMES = ["Milo", "Pip", "Nia", "Luna", "Toby", "Mina", "Jules", "Poppy"]
HELPER_NAMES = ["Bee", "Dot", "Tess", "Roo", "Kit", "Ned", "Moss", "Wren"]
TRAITS = ["cheerful", "curious", "clever", "spry", "gentle", "bouncy"]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    worn_by: Optional[str] = None
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    room: str = ""
    protective: bool = False
    guards: set[str] = field(default_factory=set)
    helps_with: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    jar: object | None = None
    tool_ent: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "pride": 0.0, "humor": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"chemist", "girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "he", "object": "him", "possessive": "his"}[case]

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
class World:
    room: Room
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    sim: object | None = None
    world: object | None = None
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
        return None


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Reasoning and simulation
# ---------------------------------------------------------------------------

def is_reasonable(room: Room, potion: Potion, tool: Optional[Tool]) -> bool:
    if potion.name not in {"fizzy potion", "glow potion", "color potion"}:
        return False
    if room.name not in {"the little lab", "the kitchen nook", "the garden shed"}:
        return False
    if "mix" not in room.affords:
        return False
    if tool is None:
        return False
    if not (potion.mess in tool.protects_from or potion.effect in tool.helps_with):
        return False
    return True


def predict_mess(world: World, hero: Entity, potion: Potion, tool: Optional[Tool]) -> dict:
    sim = World(world.room)
    sim.entities = {
        k: Entity(**{**v.__dict__, "meters": dict(v.meters), "memes": dict(v.memes), "guards": set(v.guards), "helps_with": set(v.helps_with)})
        for k, v in world.entities.items()
    }
    if tool and tool.name in sim.entities:
        sim.get(tool.name).worn_by = hero.id
    _mix(sim, hero, potion, narrate=False)
    jar = sim.entities.get("jar")
    return {"messy": bool(jar and jar.meters["mess"] >= THRESHOLD)}


def _mix(world: World, hero: Entity, potion: Potion, narrate: bool = True) -> None:
    world.facts["potion"] = potion
    world.facts["hero"] = hero
    hero.memes["joy"] += 1
    if potion.mess == "foamy":
        world.facts["bubbling"] = True
    world.get("jar").meters["mess"] += 1
    if any(e.worn_by == hero.id and e.protective and potion.mess in e.guards for e in world.entities.values()):
        world.get("jar").meters["mess"] -= 1
        hero.memes["worry"] = max(0, hero.memes["worry"] - 1)
    else:
        hero.memes["worry"] += 1
    if narrate:
        if potion.name == "fizzy potion":
            world.say("The potion went pop and fizz, with bubbles doing a little jig.")
        elif potion.name == "glow potion":
            world.say("The potion gave a glow-and-show, like a lantern in a bow.")
        else:
            world.say("The potion made a splashy dash, and the table blinked in hash.")


def _helper_fix(world: World, hero: Entity, helper: Entity, tool: Tool, potion: Potion) -> None:
    helper.memes["humor"] += 1
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.get("jar").meters["mess"] = 0
    world.get("jar").meters["clean"] += 1
    world.say(
        f"{helper.id} laughed, 'No more blob and wobble!' "
        f"Then {helper.pronoun('subject')} brought {tool.name} and made the trouble double-fold into a tidy little bubble."
    )
    world.say(
        f"Together they tried again, and this time the {potion.name} shone bright and neat, "
        f"as cheerful as a tap-dancing beet."
    )


# ---------------------------------------------------------------------------
# Story screenplay
# ---------------------------------------------------------------------------

def tell(room: Room, potion: Potion, tool: Tool, hero_name: str, helper_name: str, trait: str) -> World:
    world = World(room=room)
    hero = world.add(Entity(id=hero_name, kind="character", type="chemist", label="chemist"))
    helper = world.add(Entity(id=helper_name, kind="character", type="assistant", label="helper"))
    jar = world.add(Entity(id="jar", kind="thing", type="jar", label="glass jar", caretaker=hero.id))
    tool_ent = world.add(Entity(
        id=tool.name,
        kind="thing",
        type="tool",
        label=tool.name,
        owner=hero.id,
        protective=tool.is_protective,
        guards=set(tool.protects_from),
        helps_with=set(tool.helps_with),
    ))
    tool_ent.worn_by = hero.id

    hero.memes["joy"] += 1
    hero.memes["humor"] += 1

    world.say(
        f"{hero.id} was a {trait} chemist in {room.name}, with a grin as wide as a spoon."
    )
    world.say(
        f"{hero.id} liked to make bright brews that rhymed with moon and spoon."
    )
    world.say(
        f"One day {hero.id} had {potion.name}, a {potion.base} meant to {potion.effect} by noon."
    )
    world.para()
    world.say(
        f"{hero.id} set the jar on the table and said, 'I'll mix it with care and a little bit of cheer.'"
    )
    _mix(world, hero, potion, narrate=True)

    if world.get("jar").meters["mess"] >= THRESHOLD:
        world.say(
            f"{helper.id} peered in and giggled, 'That is a jolly mess! It looks like a goose wore glitter for a dress.'"
        )
        world.say(
            f"{hero.id} blushed, then laughed too, because even a serious face can turn to a smile in a tiny space."
        )
        world.para()
        world.say(
            f"Then {hero.id} wore {tool.name}, and {helper.id} helped hold the spoon so the bubbles would behave."
        )
        _helper_fix(world, hero, helper, tool, potion)
    else:
        world.say(
            f"The brew stayed neat as a sheep in a sheet, and {hero.id} gave a happy, science-y beat."
        )

    world.say(
        f"At the end, the little lab was tidy and bright, and the jar shone like a star on a nursery-rhyme night."
    )
    world.facts.update(
        hero=hero,
        helper=helper,
        jar=jar,
        tool=tool_ent,
        potion=potion,
        room=room,
        trait=trait,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Params and generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    room: str
    potion: str
    tool: str
    hero: str
    helper: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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
        return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for rn, room in ROOMS.items():
        for pn, potion in POTIONS.items():
            for tn, tool in TOOLS.items():
                if is_reasonable(room, potion, tool):
                    combos.append((rn, pn, tn))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short nursery-rhyme style story about a chemist named {f["hero"].id} and a {f["potion"].name}.',
        f"Tell a funny, rhyming story where {f['hero'].id} mixes a potion in {f['room'].name} and needs {(f.get('tool') or next(iter(TOOLS.values()))).name}.",
        f"Make a gentle rhyme about a chemist, a helper, and a tiny mishap that ends in a clean, cheerful success.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    potion = _safe_fact(world, f, "potion")
    room = _safe_fact(world, f, "room")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a {f['trait']} chemist in {room.name}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to make?",
            answer=f"{hero.id} wanted to make a {potion.name} that could {potion.effect}.",
        ),
        QAItem(
            question=f"Why did {helper.id} laugh?",
            answer=f"{helper.id} laughed because the first try made a silly mess, and the whole scene felt funny instead of scary.",
        ),
        QAItem(
            question=f"How did {hero.id} fix the problem?",
            answer=f"{hero.id} put on {tool.name} and worked with {helper.id} to make the brew tidy again.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer="At the end, the jar was clean, the lab was bright, and the chemist felt happy and proud.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a chemist do?",
            answer="A chemist is a person who studies and mixes different substances to learn what they do and to make new things.",
        ),
        QAItem(
            question="Why do goggles help in a lab?",
            answer="Goggles help protect eyes from splashes, bubbles, and tiny flying bits while mixing things.",
        ),
        QAItem(
            question="What is a potion?",
            answer="A potion is a special drink or liquid mix in stories, often made for a magic or science surprise.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
room_ok(R) :- room(R).
potion_ok(P) :- potion(P).
tool_ok(T) :- tool(T).

reasonable(R,P,T) :- room_ok(R), potion_ok(P), tool_ok(T),
                     affords(R, mix),
                     potion_mess(P, M), tool_protects(T, M).
"""

def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for rid, room in ROOMS.items():
        lines.append(asp.fact("room", rid))
        for a in sorted(room.affords):
            lines.append(asp.fact("affords", rid, a))
    for pid, potion in POTIONS.items():
        lines.append(asp.fact("potion", pid))
        lines.append(asp.fact("potion_mess", pid, potion.mess))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for m in sorted(tool.protects_from):
            lines.append(asp.fact("tool_protects", tid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A nursery-rhyme chemistry storyworld.")
    ap.add_argument("--room", choices=ROOMS)
    ap.add_argument("--potion", choices=POTIONS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "room", None):
        combos = [c for c in combos if c[0] == getattr(args, "room", None)]
    if getattr(args, "potion", None):
        combos = [c for c in combos if c[1] == getattr(args, "potion", None)]
    if getattr(args, "tool", None):
        combos = [c for c in combos if c[2] == getattr(args, "tool", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    room, potion, tool = rng.choice(list(combos))
    return StoryParams(
        room=room,
        potion=potion,
        tool=tool,
        hero=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        helper=getattr(args, "helper", None) or rng.choice(HELPER_NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(ROOMS, params.room),
        _safe_lookup(POTIONS, params.potion),
        _safe_lookup(TOOLS, params.tool),
        params.hero,
        params.helper,
        params.trait,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={e.meters}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"guards={sorted(e.guards)}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
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


def asp_list() -> None:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    combos = sorted(set(asp.atoms(model, "reasonable")))
    print(f"{len(combos)} compatible combos:")
    for r, p, t in combos:
        print(f"  {r:12} {p:12} {t}")


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonable/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        asp_list()
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for room, potion, tool in sorted(valid_combos()):
            params = StoryParams(
                room=room,
                potion=potion,
                tool=tool,
                hero=_safe_lookup(HERO_NAMES, 0),
                helper=_safe_lookup(HELPER_NAMES, 0),
                trait=_safe_lookup(TRAITS, 0),
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError:
                continue
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
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
