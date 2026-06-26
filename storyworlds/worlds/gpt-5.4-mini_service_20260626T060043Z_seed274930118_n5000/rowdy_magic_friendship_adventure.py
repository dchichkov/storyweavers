#!/usr/bin/env python3
"""
rowdy_magic_friendship_adventure.py
===================================

A small story world about a rowdy adventure where magic and friendship turn
trouble into a shared win.

The seed image:
---
A rowdy child and a close friend set out on a little adventure with a magic
tool. The rowdiness makes the magic wobble and the path gets confusing, but the
friend notices, helps steady the magic, and they finish the trip together with
new courage.

World model:
---
- physical meters: excitement, spark, lost, tired, glow, dust
- emotional memes: joy, worry, trust, frustration, courage, closeness

Story shape:
---
setup -> adventure begins -> rowdy trouble -> friendship-based fix -> bright ending

This script is standalone and uses only stdlib plus the shared Storyweavers
result containers. ASP is imported lazily only in ASP helpers.
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

THRESHOLD = 1.0



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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    touched_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    tool: object | None = None
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
    name: str
    kind: str
    affords: set[str] = field(default_factory=set)
    mood: str = ""
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
    id: str
    label: str
    kind: str
    helps_with: set[str]
    purpose: str
    fix: str
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
class Adventure:
    id: str
    verb: str
    gerund: str
    rush: str
    challenge: str
    risk: str
    region: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
    place: str
    adventure: str
    tool: str
    hero_name: str
    hero_type: str
    friend_name: str
    friend_type: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.current_adventure: Optional[Adventure] = None

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy as _copy
        c = World(self.place)
        c.entities = _copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        c.fired = set(self.fired)
        c.current_adventure = self.current_adventure
        return c


SETTINGS = {
    "forest": Place("the forest", "outdoor", {"map", "lantern", "gloworb"}, "mysterious"),
    "cave": Place("the cave", "outdoor", {"lantern", "gloworb"}, "echoing"),
    "garden": Place("the garden", "outdoor", {"map", "gloworb"}, "bright"),
    "treehouse": Place("the treehouse", "outdoor", {"map", "lantern"}, "playful"),
}

ADVENTURES = {
    "forest_path": Adventure(
        id="forest_path",
        verb="follow the hidden path",
        gerund="following the hidden path",
        rush="dash down the path",
        challenge="the path keeps bending under the trees",
        risk="the magic map gets confused by too much bouncing around",
        region="path",
        keyword="path",
        tags={"forest", "map", "adventure"},
    ),
    "cave_echo": Adventure(
        id="cave_echo",
        verb="search for the glowing stone",
        gerund="searching for the glowing stone",
        rush="run deeper into the cave",
        challenge="the echoes make every clue sound mixed up",
        risk="the lantern wobbles and the sparkle in the dark fades",
        region="dark",
        keyword="glow",
        tags={"cave", "lantern", "magic"},
    ),
    "garden_bridge": Adventure(
        id="garden_bridge",
        verb="cross the little bridge",
        gerund="crossing the little bridge",
        rush="skip too fast over the bridge",
        challenge="the bridge sways when feet land too hard",
        risk="the gloworb slips and rolls away into the flowers",
        region="bridge",
        keyword="bridge",
        tags={"garden", "gloworb", "friendship"},
    ),
}

TOOLS = {
    "map": Tool(
        id="map",
        label="a magic map",
        kind="map",
        helps_with={"lost"},
        purpose="shows the way when the path twists",
        fix="held it still and let the map point north",
    ),
    "lantern": Tool(
        id="lantern",
        label="a small lantern",
        kind="lantern",
        helps_with={"dark"},
        purpose="spreads a warm circle of light",
        fix="covered the flame with two careful hands",
    ),
    "gloworb": Tool(
        id="gloworb",
        label="a gloworb",
        kind="orb",
        helps_with={"lost", "dark"},
        purpose="shines like a soft star in a pocket",
        fix="cupped it so the glow would stay steady",
    ),
}

GIRL_NAMES = ["Mina", "Lia", "Nora", "Ari", "Sia", "Tess", "Maya", "Eve"]
BOY_NAMES = ["Robin", "Finn", "Theo", "Jude", "Leo", "Owen", "Pip", "Kai"]
TRAITS = ["curious", "brave", "playful", "spunky", "cheerful", "bold"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in SETTINGS.items():
        for adv_id, adv in ADVENTURES.items():
            for tool_id, tool in TOOLS.items():
                if tool.kind in adv.tags or tool.helps_with.intersection({"lost", "dark"}):
                    combos.append((place_id, adv_id, tool_id))
    return combos


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(SETTINGS, params.place)
    adv = _safe_lookup(ADVENTURES, params.adventure)
    tool_def = _safe_lookup(TOOLS, params.tool)
    world = World(place)
    world.current_adventure = adv

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={"excitement": 0.0, "spark": 0.0, "lost": 0.0, "tired": 0.0},
        memes={"joy": 0.0, "trust": 0.0, "frustration": 0.0, "courage": 0.0, "closeness": 0.0},
    ))
    friend = world.add(Entity(
        id=params.friend_name,
        kind="character",
        type=params.friend_type,
        meters={"excitement": 0.0, "spark": 0.0, "lost": 0.0, "tired": 0.0},
        memes={"joy": 0.0, "trust": 0.0, "frustration": 0.0, "courage": 0.0, "closeness": 0.0},
    ))
    tool = world.add(Entity(
        id=tool_def.id,
        kind="thing",
        type=tool_def.kind,
        label=tool_def.label,
        phrase=tool_def.label,
        owner=hero.id,
        carried_by=hero.id,
        meters={"glow": 1.0},
    ))
    world.facts.update(hero=hero, friend=friend, tool=tool, tool_def=tool_def, adventure=adv)
    return world


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    adv = world.current_adventure
    if adv is None:
        return out

    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    tool = _safe_fact(world, world.facts, "tool")

    if hero.meters.get("spark", 0.0) >= THRESHOLD and tool.carried_by == hero.id:
        sig = ("spark_tool", tool.id)
        if sig not in world.fired:
            world.fired.add(sig)
            tool.meters["glow"] = 1.5
            out.append(f"The {tool.label} glowed brighter in {hero.pronoun('possessive')} hands.")

    if hero.memes["frustration"] >= THRESHOLD and friend.memes["trust"] >= THRESHOLD:
        sig = ("friend_help", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["lost"] = max(0.0, hero.meters.get("lost", 0.0) - 1.0)
            hero.memes["courage"] += 1.0
            friend.memes["closeness"] += 1.0
            out.append("Their friendship made the tricky part feel smaller.")

    if tool.kind == "map" and tool.carried_by == hero.id and hero.meters.get("lost", 0.0) >= THRESHOLD:
        sig = ("map_help", tool.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["lost"] = 0.0
            out.append("The magic map settled and pointed toward the right way.")

    if tool.kind == "lantern" and tool.carried_by == friend.id and hero.meters.get("lost", 0.0) >= THRESHOLD:
        sig = ("lantern_help", tool.id)
        if sig not in world.fired:
            world.fired.add(sig)
            hero.meters["lost"] = max(0.0, hero.meters["lost"] - 1.0)
            out.append("The lantern's light made the dark look less scary.")

    if narrate:
        for line in out:
            world.say(line)
    return out


def intro(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    adv = _safe_fact(world, world.facts, "adventure")
    world.say(
        f"{hero.id} was a little {hero.type} with a rowdy laugh, and {friend.id} was the kind of friend who never backed away from a little adventure."
    )
    world.say(
        f"Together they loved {adv.gerund}, because every bend in the trail could hide a surprise."
    )


def setup_tool(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    tool = _safe_fact(world, world.facts, "tool")
    tool_def = _safe_fact(world, world.facts, "tool_def")
    world.say(
        f"{hero.id} carried {tool.label}, and everyone knew it was no ordinary thing: it {tool_def.purpose}."
    )


def begin_adventure(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    adv = _safe_fact(world, world.facts, "adventure")
    world.para()
    world.say(
        f"One day, they set out for {world.place.name}."
    )
    world.say(
        f"{hero.id} wanted to {adv.verb}, and {friend.id} stayed close, grinning at the windy, exciting path."
    )
    hero.meters["excitement"] += 1.0
    friend.meters["excitement"] += 1.0
    hero.memes["joy"] += 1.0
    friend.memes["joy"] += 1.0


def rowdy_problem(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    adv = _safe_fact(world, world.facts, "adventure")
    tool = _safe_fact(world, world.facts, "tool")

    world.para()
    world.say(f"But {hero.id} got rowdy.")
    world.say(f"{hero.pronoun().capitalize()} started to {adv.rush}, which made {adv.challenge}.")
    hero.meters["spark"] += 1.0
    hero.meters["lost"] += 1.0
    hero.memes["frustration"] += 1.0
    friend.memes["worry"] = friend.memes.get("worry", 0.0) + 1.0
    world.say(f"{adv.risk.capitalize()}, and even {tool.label} began to wobble in the hand.")
    propagate(world)


def friendship_fix(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    tool = _safe_fact(world, world.facts, "tool")
    tool_def = _safe_fact(world, world.facts, "tool_def")

    world.para()
    world.say(f"{friend.id} did not scold. {friend.pronoun().capitalize()} just stepped beside {hero.id}.")
    world.say(f'"Let me help," {friend.id} said, and the two of them {tool_def.fix}.')
    friend.memes["trust"] += 1.0
    hero.memes["trust"] += 1.0
    hero.memes["courage"] += 1.0
    friend.memes["closeness"] += 1.0
    if tool.kind == "map":
        hero.meters["lost"] = 0.0
    elif tool.kind == "lantern":
        hero.meters["lost"] = max(0.0, hero.meters["lost"] - 1.0)
    else:
        hero.meters["lost"] = max(0.0, hero.meters["lost"] - 0.5)
    tool.meters["glow"] = 1.5
    propagate(world)


def ending(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend")
    adv = _safe_fact(world, world.facts, "adventure")
    tool = _safe_fact(world, world.facts, "tool")
    world.para()
    if hero.meters.get("lost", 0.0) < THRESHOLD:
        world.say(
            f"In the end, the path opened up, the magic worked again, and {hero.id} and {friend.id} reached the bright place they had been looking for."
        )
        world.say(
            f"{hero.id} was still rowdy, but now it was happy rowdy, the kind that comes from winning an adventure together."
        )
    else:
        world.say(
            f"In the end, {friend.id}'s steady help kept the adventure from going wrong, and the two friends went home with {tool.label} glowing softly between them."
        )
    world.say(
        f"They had gone from a noisy start to a brave finish, and the little adventure ended with laughter under {world.place.name}."
    )


def tell_story(world: World) -> World:
    intro(world)
    setup_tool(world)
    begin_adventure(world)
    rowdy_problem(world)
    friendship_fix(world)
    ending(world)
    world.facts["resolved"] = world.facts["hero"].meters.get("lost", 0.0) < THRESHOLD
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    adv = _safe_fact(world, f, "adventure")
    tool_def = _safe_fact(world, f, "tool_def")
    return [
        f'Write a short adventure story for a child about a rowdy {hero.type} named {hero.id} and {friend.id} using {tool_def.label}.',
        f"Tell a magic friendship adventure where {hero.id} wants to {adv.verb} but gets rowdy, and {friend.id} helps.",
        f'Write a gentle, exciting story that includes the word "rowdy" and ends with {tool_def.label} helping two friends finish their quest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    adv = _safe_fact(world, f, "adventure")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    tool_def = _safe_fact(world, f, "tool_def")
    qa = [
        QAItem(
            question=f"Who went on the adventure in {world.place.name}?",
            answer=f"{hero.id} and {friend.id} went together, and they traveled with {tool.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at the start?",
            answer=f"{hero.id} wanted to {adv.verb}, because the whole trip was meant to be a fun adventure.",
        ),
        QAItem(
            question=f"Why did the trouble start?",
            answer=f"The trouble started because {hero.id} got rowdy and rushed ahead, which made the magic wobble and the path hard to read.",
        ),
        QAItem(
            question=f"How did {friend.id} help?",
            answer=f"{friend.id} stayed calm, helped steady {tool.label}, and made the friendship stronger so the way forward was easier to see.",
        ),
        QAItem(
            question=f"What was special about {tool.label}?",
            answer=f"{tool.label} was special because it was {tool_def.purpose}.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does rowdy mean?",
            answer="Rowdy means noisy, wild, and hard to control, like when someone gets too bouncy or rough for the moment.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and stay kind even when something goes wrong.",
        ),
        QAItem(
            question="What is magic in a story?",
            answer="Magic in a story is something unusual and wonderful that can do special things, like glow, guide, or help a problem feel smaller.",
        ),
    ]
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({a for a, *_ in world.fired})}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="forest", adventure="forest_path", tool="map", hero_name="Mina", hero_type="girl",
                friend_name="Pip", friend_type="boy"),
    StoryParams(place="cave", adventure="cave_echo", tool="lantern", hero_name="Theo", hero_type="boy",
                friend_name="Lia", friend_type="girl"),
    StoryParams(place="garden", adventure="garden_bridge", tool="gloworb", hero_name="Ari", hero_type="girl",
                friend_name="Robin", friend_type="boy"),
]


ASP_RULES = r"""
% A tool fits an adventure when it can help with the adventure's danger.
fits(T, A) :- tool(T), adventure(A), tool_kind(T, K), adventure_tag(A, K).
fits(T, A) :- tool(T), adventure(A), helps(T, lost).
fits(T, A) :- tool(T), adventure(A), helps(T, dark).

% A valid story requires a place, adventure, and fitting tool.
valid_story(P, A, T) :- place(P), adventure(A), allows(P, A), fits(T, A).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("allows", pid, a))
    for aid, a in ADVENTURES.items():
        lines.append(asp.fact("adventure", aid))
        lines.append(asp.fact("adventure_tag", aid, aid.split("_")[0] if "_" in aid else aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("adventure_tag", aid, t))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        lines.append(asp.fact("tool_kind", tid, t.kind))
        for h in sorted(t.helps_with):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Rowdy magic friendship adventure story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--adventure", choices=ADVENTURES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--friend-gender", choices=["girl", "boy"])
    ap.add_argument("-n", "--n", type=int, default=1)
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
    combos = [c for c in combos
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "adventure", None) is None or c[1] == getattr(args, "adventure", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, adventure, tool = rng.choice(list(combos))
    hero_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    friend_gender = getattr(args, "friend_gender", None) or ("boy" if hero_gender == "girl" else "girl")
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    friend_name = getattr(args, "friend", None) or rng.choice(GIRL_NAMES if friend_gender == "girl" else BOY_NAMES)
    return StoryParams(
        place=place,
        adventure=adventure,
        tool=tool,
        hero_name=hero_name,
        hero_type=hero_gender,
        friend_name=friend_name,
        friend_type=friend_gender,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell_story(world)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, adventure, tool) combos:\n")
        for place, adventure, tool in combos:
            print(f"  {place:10} {adventure:14} {tool}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.adventure} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
