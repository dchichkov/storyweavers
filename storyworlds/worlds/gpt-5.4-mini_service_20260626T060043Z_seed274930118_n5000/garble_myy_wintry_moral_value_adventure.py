#!/usr/bin/env python3
"""
storyworlds/worlds/garble_myy_wintry_moral_value_adventure.py
=============================================================

A small adventure story world about a wintry trek, a garbled map, and a moral
value test.

Premise:
- A child adventurer sets out across a wintry trail with a guide and a satchel
  of useful things.
- The trail matters because someone far away needs help before dusk.

Tension:
- The map and the trail-signs become garbled by snow and wind.
- The traveler must choose whether to hurry through the dark or help a small
  "myy" sound in the snow.

Turn:
- The traveler shows a moral value: patience, kindness, or honesty.
- That choice reveals the true path.

Resolution:
- The helper is safe, the route is clear, and the traveler reaches the goal
  with a warmer heart and a better plan.

The world is intentionally compact:
- typed entities with meters and memes
- a stateful simulation
- an inline ASP twin for the reasonableness gate
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
# Core world model
# ---------------------------------------------------------------------------
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    guide: object | None = None
    hero: object | None = None
    item: object | None = None
    obstacle: object | None = None
    small: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") or self.label.endswith("s") else "it"
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
    indoors: bool = False
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
class Quest:
    id: str
    verb: str
    gerund: str
    risk: str
    clue: str
    weather: str
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
class Tool:
    id: str
    label: str
    covers: set[str] = field(default_factory=set)
    helps: set[str] = field(default_factory=set)
    use_line: str = ""
    result_line: str = ""
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
class StoryParams:
    place: str
    quest: str
    value: str
    name: str
    gender: str
    guide: str
    trait: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.lines: list[str] = []
        self.facts: dict = {}
        self.weather: str = ""

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "trail": Place("the wintry trail", indoors=False, tags={"wintry", "adventure"}),
    "cabin": Place("the cabin porch", indoors=False, tags={"wintry", "safe"}),
    "ridge": Place("the snowy ridge", indoors=False, tags={"wintry", "adventure"}),
}

QUESTS = {
    "signal": Quest(
        id="signal",
        verb="fix the lantern signal",
        gerund="fixing the lantern signal",
        risk="the signal would stay garbled",
        clue="a flicker near the ice path",
        weather="snowy",
        tags={"lantern", "light", "garble"},
    ),
    "deliver": Quest(
        id="deliver",
        verb="deliver the warm parcel",
        gerund="delivering the warm parcel",
        risk="the parcel would get cold",
        clue="a narrow path behind the fir trees",
        weather="wintry",
        tags={"parcel", "help", "kind"},
    ),
    "rescue": Quest(
        id="rescue",
        verb="follow the myy sound",
        gerund="following the myy sound",
        risk="the little caller might freeze",
        clue="a soft sound under the snowbank",
        weather="wintry",
        tags={"myy", "help", "kind"},
    ),
}

VALUES = {
    "kindness": "kindness",
    "honesty": "honesty",
    "patience": "patience",
}

TOOLS = [
    Tool(
        id="lantern",
        label="a brass lantern",
        covers={"light"},
        helps={"garble"},
        use_line="held the lantern high and waited for the wind to pass",
        result_line="the path signs became easier to read",
    ),
    Tool(
        id="map",
        label="a waxed map",
        covers={"paper"},
        helps={"garble"},
        use_line="smoothed the map flat and traced the turns carefully",
        result_line="the messy lines started to make sense",
    ),
    Tool(
        id="blanket",
        label="a wool blanket",
        covers={"warmth"},
        helps={"myy"},
        use_line="wrapped the blanket around the shivering shape",
        result_line="the small caller warmed up at once",
    ),
    Tool(
        id="bell",
        label="a little silver bell",
        covers={"sound"},
        helps={"myy"},
        use_line="rang the bell so the lost one could answer",
        result_line="the soft myy sound came back from the snow",
    ),
]

GIRL_NAMES = ["Mira", "Nora", "Lina", "Ivy", "Zia", "Tara"]
BOY_NAMES = ["Eli", "Tobin", "Milo", "Arin", "Jace", "Oren"]
TRAITS = ["brave", "gentle", "curious", "careful", "bright", "steady"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A quest is reasonable when the place and the quest share a compatible theme,
% and there is at least one tool that helps the main risk.
compatible(Place, Quest) :- place(Place), quest(Quest),
                            place_tag(Place, wintry), quest_tag(Quest, wintry).
compatible(Place, Quest) :- place(Place), quest(Quest),
                            quest_tag(Quest, garble), place_tag(Place, adventure).
compatible(Place, Quest) :- place(Place), quest(Quest),
                            quest_tag(Quest, help), place_tag(Place, adventure).

fixable(Quest) :- quest(Quest), helps(Tool, garble).
fixable(Quest) :- quest(Quest), helps(Tool, myy).

valid(Place, Quest, Value) :- compatible(Place, Quest), fixable(Quest), moral_value(Value).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
        for t in sorted(p.tags):
            lines.append(asp.fact("place_tag", pid, t))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for t in sorted(q.tags):
            lines.append(asp.fact("quest_tag", qid, t))
    for v in VALUES:
        lines.append(asp.fact("moral_value", v))
    for tool in TOOLS:
        for k in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def python_valid() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for quest_id, quest in QUESTS.items():
            if "wintry" not in place.tags and "adventure" not in place.tags:
                continue
            if not ({"garble", "help"} & quest.tags):
                continue
            for value in VALUES:
                out.append((place_id, quest_id, value))
    return out


def asp_verify() -> int:
    a = set(asp_valid())
    p = set(python_valid())
    if a == p:
        print(f"OK: clingo gate matches python gate ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    if a - p:
        print("  only in clingo:", sorted(a - p))
    if p - a:
        print("  only in python:", sorted(p - a))
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def quest_at_risk(quest: Quest) -> bool:
    return quest.id in {"signal", "deliver", "rescue"}


def tool_for(quest: Quest) -> Optional[Tool]:
    for t in TOOLS:
        if quest.id == "signal" and "garble" in t.helps:
            return t
        if quest.id == "rescue" and "myy" in t.helps:
            return t
        if quest.id == "deliver" and "myy" in t.helps:
            return t
    return None


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    quest = _safe_lookup(QUESTS, params.quest)
    world = World(place)
    world.weather = quest.weather

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=[params.trait, "sturdy"],
        memes={"moral_value": 0.0, "worry": 0.0, "trust": 0.0, "joy": 0.0},
        meters={"cold": 0.0, "tired": 0.0},
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type=params.guide,
        label=f"the {params.guide}",
        traits=["old", "wise"],
        memes={"worry": 0.0, "trust": 1.0},
    ))
    item = world.add(Entity(
        id="QuestItem",
        type="thing",
        label="the mission",
        phrase=quest.verb,
        owner=hero.id,
        caretaker=guide.id,
        memes={"importance": 1.0},
    ))
    obstacle = world.add(Entity(
        id="Obstacle",
        type="thing",
        label="the garbled signs",
        phrase="snow-streaked trail signs",
        memes={"garble": 1.0 if quest.id == "signal" else 0.0, "lonely": 0.5},
    ))
    small = world.add(Entity(
        id="Myy",
        type="creature",
        label="the little myy",
        phrase="a small caller in the snow",
        memes={"fear": 1.0 if quest.id == "rescue" else 0.0, "hope": 0.0},
        meters={"cold": 1.0 if quest.id == "rescue" else 0.0},
    ))

    world.facts.update(hero=hero, guide=guide, item=item, quest=quest, obstacle=obstacle, small=small)
    return world


def narrate_setup(world: World) -> None:
    h: Entity = _safe_fact(world, world.facts, "hero")
    g: Entity = _safe_fact(world, world.facts, "guide")
    q: Quest = _safe_fact(world, world.facts, "quest")
    world.say(
        f"{h.id} was a {h.traits[0]} adventurer who liked narrow paths and bright plans."
    )
    world.say(
        f"On the wintry day, {h.id} and {g.label} set out because someone needed {q.verb}."
    )
    world.say(
        f"The air was sharp, and the mission mattered: if they were late, {q.risk}."
    )


def narrate_turn(world: World) -> None:
    h: Entity = _safe_fact(world, world.facts, "hero")
    g: Entity = _safe_fact(world, world.facts, "guide")
    q: Quest = _safe_fact(world, world.facts, "quest")
    tool = tool_for(q)
    if q.id == "signal":
        h.memes["worry"] += 1
        world.say(
            f"Then the snow blew hard, and the trail sign turned into garble."
        )
        world.say(
            f"{h.id} wanted to dash ahead, but {g.label} lifted {tool.label if tool else 'a lantern'} and asked for patience."
        )
    elif q.id == "rescue":
        h.memes["worry"] += 1
        world.say(
            f"From somewhere under the snow came a tiny myy sound, thin and shivery."
        )
        world.say(
            f"{h.id} had to choose: hurry past the sound, or stop and help."
        )
    else:
        h.memes["worry"] += 1
        world.say(
            f"The wind made the parcel straps flap, and the path looked longer than before."
        )
        world.say(
            f"{h.id} could rush on, but {g.label} said a careful step would be the kinder one."
        )


def narrate_choice(world: World) -> None:
    h: Entity = _safe_fact(world, world.facts, "hero")
    q: Quest = _safe_fact(world, world.facts, "quest")
    v = _safe_fact(world, world.facts, "value")
    tool = tool_for(q)
    h.memes["moral_value"] += 1
    if v == "patience":
        world.say(
            f"{h.id} chose patience, stood still, and let the wind finish its shouting."
        )
    elif v == "honesty":
        world.say(
            f"{h.id} chose honesty and admitted that the map line looked wrong."
        )
    else:
        world.say(
            f"{h.id} chose kindness first, because helping the small one felt right."
        )
    if tool:
        world.say(f"{h.id} used {tool.label}; {tool.use_line}.")
    if q.id == "signal":
        world.say("The garble cleared enough to show the right bend in the path.")
    elif q.id == "rescue":
        world.say("The blanket made the shivering myy warm, and the little caller blinked up gratefully.")
    else:
        world.say("The careful pace kept the parcel safe, warm, and snug.")


def narrate_resolution(world: World) -> None:
    h: Entity = _safe_fact(world, world.facts, "hero")
    g: Entity = _safe_fact(world, world.facts, "guide")
    q: Quest = _safe_fact(world, world.facts, "quest")
    v = _safe_fact(world, world.facts, "value")
    h.memes["joy"] += 1
    h.memes["trust"] += 1
    world.say(
        f"In the end, {h.id} reached the goal with the mission still safe."
    )
    if q.id == "rescue":
        world.say(
            f"The little myy curled up beside {g.label}, no longer shivering."
        )
    elif q.id == "signal":
        world.say(
            f"The lantern signal shone cleanly again, and the trail felt friendly instead of confusing."
        )
    else:
        world.say(
            f"The warm parcel arrived on time, and the waiting hands were happy."
        )
    world.say(
        f"{h.id} learned that {v} was not a small thing at all; it was the best compass in the snow."
    )


def tell_story(world: World) -> None:
    narrate_setup(world)
    narrate_turn(world)
    narrate_choice(world)
    narrate_resolution(world)


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    h: Entity = _safe_fact(world, world.facts, "hero")
    q: Quest = _safe_fact(world, world.facts, "quest")
    return [
        "Write a short adventure story for a young child about a wintry path, a garbled clue, and a moral choice.",
        f"Tell a gentle story where {h.id} must {q.verb} and learns that a moral value matters more than rushing.",
        "Write a child-facing winter adventure story that includes the words garble, myy, and wintry.",
    ]


def story_qa(world: World) -> list[QAItem]:
    h: Entity = _safe_fact(world, world.facts, "hero")
    g: Entity = _safe_fact(world, world.facts, "guide")
    q: Quest = _safe_fact(world, world.facts, "quest")
    v = _safe_fact(world, world.facts, "value")
    return [
        QAItem(
            question=f"Who went on the wintry adventure?",
            answer=f"{h.id} went with {g.label} on the wintry trail.",
        ),
        QAItem(
            question=f"What problem made the trip hard?",
            answer=f"The problem was that the trail turned garbled and {q.risk}.",
        ),
        QAItem(
            question=f"What moral value did {h.id} show?",
            answer=f"{h.id} showed {v}, and that choice helped the adventure end well.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the mission complete, the path clear, and {h.id} wiser in the snow.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does garble mean?",
            answer="Garble means mixed-up or hard-to-read, like when words or signs get scrambled.",
        ),
        QAItem(
            question="What does myy sound like in a story?",
            answer="Myy sounds like a tiny, soft call from something small, shy, or lost.",
        ),
        QAItem(
            question="What does wintry mean?",
            answer="Wintry means cold, snowy, or like winter weather.",
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good choice people try to follow, like kindness, honesty, or patience.",
        ),
    ]


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.traits:
            bits.append(f"traits={e.traits}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small wintry adventure about garble, myy, and moral value.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guide", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES:
        for q in QUESTS:
            for v in VALUES:
                combos.append((p, q, v))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "quest", None):
        combos = [c for c in combos if c[1] == getattr(args, "quest", None)]
    if getattr(args, "value", None):
        combos = [c for c in combos if c[2] == getattr(args, "value", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, quest, value = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = getattr(args, "guide", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, value=value, name=name, gender=gender, guide=guide, trait=trait)


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


# ---------------------------------------------------------------------------
# ASP / CLI
# ---------------------------------------------------------------------------
def asp_program_text(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_show() -> None:
    print(asp_program_text("#show valid/3."))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        asp_show()
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program_text("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid combinations:")
        for p, q, v in vals:
            print(f"  {p:8} {q:8} {v}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for i, combo in enumerate(valid_combos()):
            params = StoryParams(
                place=combo[0],
                quest=combo[1],
                value=combo[2],
                name=_safe_lookup(GIRL_NAMES, i % len(GIRL_NAMES)),
                gender="girl" if i % 2 == 0 else "boy",
                guide="mother" if i % 2 == 0 else "father",
                trait=_safe_lookup(TRAITS, i % len(TRAITS)),
                seed=base_seed + i,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
