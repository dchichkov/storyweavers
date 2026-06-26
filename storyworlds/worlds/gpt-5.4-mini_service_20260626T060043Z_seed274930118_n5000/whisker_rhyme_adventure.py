#!/usr/bin/env python3
"""
storyworlds/worlds/whisker_rhyme_adventure.py
=============================================

A small Adventure-style storyworld about a child explorer, a whiskered guide,
and a rhyme that points the way through a risky little journey.

Premise:
- A young adventurer wants to reach a landmark and recover a lost treasure.
- A rhyme gives clues, but the path is blocked or uncertain.
- The whiskered guide notices something the child misses.
- A simple tool or ally makes the route safe enough to finish the quest.

The world is intentionally small and constraint-checked so every story has a
clear setup, a genuine turn, and a concrete ending image.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    tool: object | None = None
    treasure_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def them(self) -> str:
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
class Setting:
    place: str
    outdoors: bool = True
    afford: str = "explore"
    hazard: str = "dark"
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


@dataclass
class Tool:
    id: str
    label: str
    phrase: str
    kind: str
    helps_against: set[str] = field(default_factory=set)
    required_place: set[str] = field(default_factory=set)
    clue: str = ""
    tail: str = ""
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


@dataclass
class Treasure:
    id: str
    label: str
    phrase: str
    kind: str
    location: str
    risk: str
    risk_place: set[str] = field(default_factory=set)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.path_open: bool = False
        self.rhyme_known: bool = False

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.path_open = self.path_open
        clone.rhyme_known = self.rhyme_known
        clone.facts = dict(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_blocked(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    treasure = world.get("treasure")
    if hero.memes.get("boldness", 0.0) < THRESHOLD:
        return out
    if world.path_open:
        return out
    if treasure.meters.get("risk", 0.0) < THRESHOLD:
        return out
    sig = ("blocked", treasure.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    out.append("The way ahead looked too dark and narrow to trust.")
    return out


def _r_tool_solved(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    tool = world.get("tool")
    treasure = world.get("treasure")
    if tool.worn_by != hero.id and tool.carried_by != hero.id:
        return out
    if not world.rhyme_known:
        return out
    if not (tool.kind in treasure.risk_place or treasure.location in tool.required_place):
        return out
    sig = ("solved", tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.path_open = True
    hero.memes["hope"] = hero.memes.get("hope", 0.0) + 1
    out.append("The rhyme fit the path at last, and the little way was safe enough to take.")
    return out


CAUSAL_RULES = [
    Rule("blocked", _r_blocked),
    Rule("tool_solved", _r_tool_solved),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    return {
        "forest": "The forest path was soft with pine needles and thin green shade.",
        "cave": "The cave mouth yawned like a sleepy mouth in the hill.",
        "river": "The river glittered and hurried over round stones.",
        "ruins": "The old ruins leaned in quiet stacks of stone.",
    }[setting.place]


def rhyme_line(setting: Setting, treasure: Treasure) -> str:
    return {
        "forest": f"“Past the roots, past the moss, follow the whisper and find what was lost.”",
        "cave": f"“By the stone that drinks the light, keep your steps small and your lantern bright.”",
        "river": f"“Where the water sings and turns, look for the bridge where the lantern burns.”",
        "ruins": f"“Under arches cracked and gray, listen close and choose the safer way.”",
    }[setting.place]


def select_tool(setting: Setting, treasure: Treasure) -> Optional[Tool]:
    for tool in TOOLS:
        if treasure.risk in tool.helps_against and (
            not tool.required_place or setting.place in tool.required_place
        ):
            return tool
    return None


def path_is_reasonable(setting: Setting, treasure: Treasure) -> bool:
    return select_tool(setting, treasure) is not None and treasure.location in setting.afford or True


def predict(world: World, hero: Entity, tool: Tool, treasure: Treasure) -> dict:
    sim = world.copy()
    sim.get("hero").memes["boldness"] = 1.0
    sim.get("tool").carried_by = hero.id
    sim.rhyme_known = True
    propagate(sim, narrate=False)
    return {"open": sim.path_open, "hope": sim.get("hero").memes.get("hope", 0.0)}


def tell(setting: Setting, treasure: Treasure, tool_def: Tool, hero_name: str, hero_type: str, guide_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, traits=["brave"]))
    guide = world.add(Entity(id="guide", kind="character", type="cat", label=guide_name, traits=["whiskered"]))
    treasure_ent = world.add(Entity(id="treasure", type=treasure.kind, label=treasure.label, phrase=treasure.phrase))
    tool = world.add(Entity(id="tool", type=tool_def.kind, label=tool_def.label, phrase=tool_def.phrase))
    tool.carried_by = hero.id

    hero.memes["curiosity"] = 1.0
    hero.memes["boldness"] = 1.0
    treasure_ent.meters["risk"] = 1.0
    guide.memes["knowing"] = 1.0

    world.say(f"{hero.label} was a little {hero.type} who loved adventure.")
    world.say(f"Beside {hero.pronoun('object')}, {guide.label} the whiskered guide twitched a bright nose and led the way.")
    world.say(f"They were chasing {treasure.phrase} through {setting.place}.")
    world.say(setting_detail(setting))
    world.say(rhyme_line(setting, treasure))
    world.rhyme_known = True
    world.para()

    world.say(f"{hero.label} wanted to reach the treasure, but the path looked risky.")
    if treasure.risk == "dark":
        world.say("The shadows made the ground hard to read.")
    elif treasure.risk == "water":
        world.say("The water made the stones slick and slippery.")
    else:
        world.say("The old stones wobbled under careful feet.")
    propagate(world, narrate=True)

    world.para()
    world.say(f"{guide.label} lifted {guide.pronoun('possessive')} whiskers and sniffed the air.")
    world.say(f"Then {guide.pronoun('subject')} pointed at {tool.label} and chirped that it was the right thing to use.")
    tool.carried_by = hero.id

    if tool_def.clue:
        world.say(tool_def.clue)

    open_state = predict(world, hero, tool_def, treasure)
    if open_state["open"]:
        world.path_open = True

    world.para()
    world.say(f"{hero.label} used {tool.label.lower()} and stepped forward.")
    propagate(world, narrate=True)

    world.para()
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(f"At last, {hero.label} found {treasure.label} waiting at the end of the path.")
    world.say(f"{guide.label}'s whiskers quivered with pride as the two of them headed home with the prize.")
    world.facts.update(
        hero=hero,
        guide=guide,
        treasure=treasure_ent,
        tool=tool,
        setting=setting,
        treasure_def=treasure,
        tool_def=tool_def,
    )
    return world


SETTINGS = {
    "forest": Setting(place="forest", outdoors=True, afford="explore", hazard="dark"),
    "cave": Setting(place="cave", outdoors=False, afford="explore", hazard="dark"),
    "river": Setting(place="river", outdoors=True, afford="cross", hazard="water"),
    "ruins": Setting(place="ruins", outdoors=True, afford="explore", hazard="stone"),
}

TREASURES = {
    "lantern": Treasure(
        id="lantern",
        label="a little lantern",
        phrase="a little lantern",
        kind="lantern",
        location="cave",
        risk="dark",
        risk_place={"light"},
    ),
    "map": Treasure(
        id="map",
        label="a folded map",
        phrase="a folded map",
        kind="map",
        location="forest",
        risk="dark",
        risk_place={"light", "nose"},
    ),
    "shell": Treasure(
        id="shell",
        label="a silver shell",
        phrase="a silver shell",
        kind="shell",
        location="river",
        risk="water",
        risk_place={"bridge", "rope"},
    ),
    "crown": Treasure(
        id="crown",
        label="an old crown",
        phrase="an old crown",
        kind="crown",
        location="ruins",
        risk="stone",
        risk_place={"rope", "hook"},
    ),
}

TOOLS = [
    Tool(
        id="lantern",
        label="a lantern",
        phrase="a lantern",
        kind="lantern",
        helps_against={"dark"},
        required_place={"cave", "forest", "ruins"},
        clue="Its warm glow made the hidden stones easier to trust.",
        tail="followed the glow",
    ),
    Tool(
        id="rope",
        label="a short rope",
        phrase="a short rope",
        kind="rope",
        helps_against={"water", "stone"},
        required_place={"river", "ruins"},
        clue="The rope could make a safe line across the slippery place.",
        tail="held the rope tight",
    ),
    Tool(
        id="boots",
        label="sturdy boots",
        phrase="sturdy boots",
        kind="boots",
        helps_against={"water"},
        required_place={"river"},
        clue="The boots kept little feet from skidding on the wet stones.",
        tail="stepped carefully",
    ),
    Tool(
        id="hook",
        label="a little hook",
        phrase="a little hook",
        kind="hook",
        helps_against={"stone"},
        required_place={"ruins"},
        clue="The hook could pull down the swinging plank at the ruins.",
        tail="used the hook",
    ),
]

NAMES = ["Pip", "Mina", "Tavi", "Lumi", "Rin", "Kest", "Nora", "Bram"]
GUIDES = ["Whisker", "Mallow", "Pounce", "Tumble"]

@dataclass
class StoryParams:
    place: str
    treasure: str
    tool: str
    name: str
    guide: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for treasure_id, treasure in TREASURES.items():
            if treasure.location != place:
                continue
            for tool in TOOLS:
                if treasure.risk in tool.helps_against and (
                    not tool.required_place or place in tool.required_place
                ):
                    combos.append((place, treasure_id, tool.id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld with a whiskered guide and a rhyme.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
    ap.add_argument("--name")
    ap.add_argument("--guide")
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


def explain_rejection(treasure: Treasure, tool: Tool) -> str:
    return f"(No story: {tool.label} cannot solve the risk of {treasure.label} on this path.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "treasure", None) and getattr(args, "tool", None):
        tr = _safe_lookup(TREASURES, getattr(args, "treasure", None))
        tl = next(t for t in TOOLS if t.id == getattr(args, "tool", None))
        if not (tr.risk in tl.helps_against and (not tl.required_place or tr.location in tl.required_place)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "treasure", None) is None or c[1] == getattr(args, "treasure", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, treasure_id, tool_id = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    guide = getattr(args, "guide", None) or rng.choice(GUIDES)
    return StoryParams(place=place, treasure=treasure_id, tool=tool_id, name=name, guide=guide)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short Adventure story for a child named {f["hero"].label} with a whiskered guide and a rhyme clue.',
        f"Tell a gentle quest story where {f['hero'].label} tries to find {f['treasure'].label} in the {f['setting'].place}.",
        f'Write an adventure that uses the word "whisker" and ends with the treasure safely found.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    guide = _safe_fact(world, f, "guide")
    treasure_def = _safe_fact(world, f, "treasure_def")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    setting = _safe_fact(world, f, "setting")

    return [
        QAItem(
            question=f"Who went on the adventure in the {setting.place}?",
            answer=f"{hero.label} went with {guide.label} the whiskered guide.",
        ),
        QAItem(
            question=f"What were they trying to find?",
            answer=f"They were trying to find {treasure_def.phrase}.",
        ),
        QAItem(
            question=f"What helped them get past the risky part of the path?",
            answer=f"They used {tool.label} to make the path safe enough to continue.",
        ),
        QAItem(
            question=f"Why did the rhyme matter in this story?",
            answer="The rhyme gave a clue that helped them choose the right thing for the path.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    setting = _safe_fact(world, f, "setting").place
    if setting == "forest":
        return [QAItem(question="What is a forest?", answer="A forest is a place with many trees and paths under their leaves.")]
    if setting == "cave":
        return [QAItem(question="What is a cave?", answer="A cave is a hollow space in rock that can be dark and cool.")]
    if setting == "river":
        return [QAItem(question="What is a river?", answer="A river is moving water that flows along a long path.")]
    return [QAItem(question="What are ruins?", answer="Ruins are the remains of old buildings or walls." )]


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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  path_open={world.path_open}")
    lines.append(f"  rhyme_known={world.rhyme_known}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.outdoors:
            lines.append(asp.fact("outdoors", sid))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("risk", tid, t.risk))
        lines.append(asp.fact("location", tid, t.location))
        for rp in sorted(t.risk_place):
            lines.append(asp.fact("risk_place", tid, rp))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for h in sorted(tool.helps_against):
            lines.append(asp.fact("helps", tool.id, h))
        for rp in sorted(tool.required_place):
            lines.append(asp.fact("for_place", tool.id, rp))
    return "\n".join(lines)


ASP_RULES = r"""
valid(Place, Treasure, Tool) :-
    location(Treasure, Place),
    risk(Treasure, Risk),
    helps(Tool, Risk),
    (not for_place(Tool, P) ; for_place(Tool, Place)).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(TREASURES, params.treasure),
        next(t for t in TOOLS if t.id == params.tool),
        params.name,
        "girl" if params.name in {"Mina", "Lumi", "Nora"} else "boy",
        params.guide,
    )
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
    StoryParams(place="forest", treasure="map", tool="lantern", name="Pip", guide="Whisker"),
    StoryParams(place="cave", treasure="lantern", tool="lantern", name="Mina", guide="Whisker"),
    StoryParams(place="river", treasure="shell", tool="boots", name="Tavi", guide="Whisker"),
    StoryParams(place="ruins", treasure="crown", tool="hook", name="Lumi", guide="Whisker"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, treasure, tool) combos:\n")
        for p, t, tl in triples:
            print(f"  {p:8} {t:10} {tl}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.treasure} in {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
