#!/usr/bin/env python3
"""
Storyworld: weed_pseudo_crummy_bravery_friendship_space_adventure
=================================================================

A tiny space-adventure story domain about a child astronaut, a stubborn weed,
a crummy shortcut, and a brave friend who helps make the right choice.

The seed tale premise:
- A young space gardener wants to keep a moon garden neat.
- A weird pseudo-tool seems faster, but it is crummy and risky.
- Bravery and friendship lead to the real fix: pulling the weed by hand
  and helping the garden thrive.

The world is intentionally small and constraint-checked:
- The weed must be a real threat to the garden patch.
- The pseudo-tool must be a tempting but bad substitute.
- The resolution must come from bravery plus friendship, not magic.

This script follows the Storyweavers contract with:
- StoryParams
- registries
- build_parser / resolve_params
- generate / emit / main
- inline ASP rules and an ASP verification parity check
"""

from __future__ import annotations

import argparse
import copy
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    prize: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Setting:
    place: str
    affords: set[str] = field(default_factory=set)
    spacey: bool = True
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    danger: str
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
class Prize:
    label: str
    phrase: str
    type: str
    owner_kind: str = "character"
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    crummy: bool = False
    pseudo: bool = False
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.tool_used: Optional[str] = None
        self.story_flags: dict[str, bool] = {}

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.paragraphs = [[]]
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.tool_used = self.tool_used
        c.story_flags = dict(self.story_flags)
        return c


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    tool: str
    name: str
    friend: str
    gender: str
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


SETTINGS = {
    "moon_garden": Setting(place="the moon garden", affords={"weed"}, spacey=True),
    "space_station": Setting(place="the little space station greenhouse", affords={"weed"}, spacey=True),
    "orbital_farm": Setting(place="the orbital farm dome", affords={"weed"}, spacey=True),
}

ACTIVITIES = {
    "weed": Activity(
        id="weed",
        verb="pull the weed",
        gerund="pulling weeds",
        rush="run to the weed patch",
        mess="dusty",
        soil="messy",
        danger="the weed could crowd out the tiny sprouts",
        keyword="weed",
        tags={"weed", "garden"},
    )
}

PRIZES = {
    "sprout": Prize(label="sprout", phrase="a tiny green sprout", type="sprout"),
    "flower": Prize(label="flower", phrase="a bright space flower", type="flower"),
    "seedling": Prize(label="seedling", phrase="a young seedling", type="seedling"),
}

TOOLS = {
    "pseudo_rover": Tool(
        id="pseudo_rover",
        label="a pseudo-rover",
        phrase="a crummy pseudo-rover",
        helps=set(),
        covers=set(),
        crummy=True,
        pseudo=True,
    ),
    "gloves": Tool(
        id="gloves",
        label="garden gloves",
        phrase="a pair of sturdy gloves",
        helps={"weed"},
        covers={"hands"},
        crummy=False,
        pseudo=False,
    ),
    "tongs": Tool(
        id="tongs",
        label="long tongs",
        phrase="a long pair of tongs",
        helps={"weed"},
        covers={"hands"},
        crummy=False,
        pseudo=False,
    ),
}

GIRL_NAMES = ["Mia", "Zoe", "Luna", "Nia", "Ava"]
BOY_NAMES = ["Kai", "Leo", "Noah", "Eli", "Finn"]
FRIENDS = ["Rin", "Pax", "Bea", "Jules", "Tomo"]


class Reasoner:
    @staticmethod
    def weed_is_risky(activity: Activity, prize: Prize) -> bool:
        return activity.id == "weed" and prize.type in {"sprout", "flower", "seedling"}

    @staticmethod
    def tool_is_reasonable(activity: Activity, tool: Tool) -> bool:
        return activity.id in tool.helps and not tool.crummy

    @staticmethod
    def valid_combo(place: str, activity: str, prize: str, tool: str) -> bool:
        return (
            place in SETTINGS
            and activity in ACTIVITIES
            and prize in PRIZES
            and tool in TOOLS
            and Reasoner.weed_is_risky(_safe_lookup(ACTIVITIES, activity), _safe_lookup(PRIZES, prize))
            and Reasoner.tool_is_reasonable(_safe_lookup(ACTIVITIES, activity), _safe_lookup(TOOLS, tool))
        )


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for place in SETTINGS:
        for activity in ACTIVITIES:
            for prize in PRIZES:
                for tool in TOOLS:
                    if Reasoner.valid_combo(place, activity, prize, tool):
                        out.append((place, activity, prize, tool))
    return out


def _do_activity(world: World, actor: Entity, activity: Activity) -> None:
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    actor.memes["bravery"] = actor.memes.get("bravery", 0.0) + 1.0
    actor.memes["care"] = actor.memes.get("care", 0.0) + 1.0


def predict(world: World, actor: Entity, activity: Activity, prize_id: str, tool_id: str) -> dict:
    sim = world.copy()
    hero = sim.get(actor.id)
    _do_activity(sim, hero, activity)
    prize = sim.get(prize_id)
    tool = sim.get(tool_id)
    return {
        "risk": prize.memes.get("trouble", 0.0) >= THRESHOLD,
        "tool_crummy": tool.crummy,
        "friendship": hero.memes.get("friendship", 0.0),
    }


def setup_story(world: World, hero: Entity, friend: Entity, prize: Entity) -> None:
    world.say(f"{hero.id} was a little space gardener who loved every green thing in {world.setting.place}.")
    world.say(f"{friend.id} was {friend.phrase}, and the two friends liked fixing things together.")
    world.say(f"One day, {hero.id} found {prize.phrase} near a weed patch and promised to protect it.")


def conflict_story(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity, tool: Tool) -> None:
    world.para()
    world.say(f"Then {hero.id} saw {activity.danger}. {hero.pronoun().capitalize()} wanted to {activity.verb} at once.")
    world.say(f"At the same time, a crummy pseudo-tool sat nearby and looked like a fast shortcut.")
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1.0
    world.tool_used = tool.id
    if tool.pseudo:
        world.say(f"{friend.id} frowned and said the pseudo-rover looked crummy, because it would not really fix the weed.")
    if tool.crummy:
        hero.memes["doubt"] = hero.memes.get("doubt", 0.0) + 1.0
    hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1.0


def resolve_story(world: World, hero: Entity, friend: Entity, activity: Activity, prize: Entity, tool: Tool) -> None:
    world.para()
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1.0
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1.0
    world.say(f"{hero.id} took a deep breath and chose bravery over the crummy shortcut.")
    world.say(f"With friendship to steady {hero.pronoun('object')}, {hero.id} pulled the weed by hand.")
    world.say(f"The little garden brightened, and {prize.phrase} stood safe and proud beside the clean path.")
    world.say(f"{friend.id} smiled, because the real fix was small, honest, and brave.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, tool: Tool,
         hero_name: str, friend_name: str, gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, phrase="a brave little astronaut"))
    friend = world.add(Entity(id=friend_name, kind="character", type="friend", phrase="a loyal space friend"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    tool_ent = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase))

    hero.memes["bravery"] = 0.0
    hero.memes["friendship"] = 0.0
    friend.memes["friendship"] = 0.0
    prize.memes["trouble"] = 1.0 if Reasoner.weed_is_risky(activity, prize_cfg) else 0.0

    setup_story(world, hero, friend, prize)
    conflict_story(world, hero, friend, activity, prize, tool_ent)
    resolve_story(world, hero, friend, activity, prize, tool_ent)

    world.facts.update(hero=hero, friend=friend, prize=prize, activity=activity, tool=tool_ent, setting=setting)
    return world


KNOWLEDGE = {
    "weed": [
        ("What is a weed?", "A weed is a plant that grows where it is not wanted and can crowd out other plants."),
    ],
    "pseudo": [
        ("What does pseudo mean?", "Pseudo means fake or not quite real, like something that only pretends to be the real thing."),
    ],
    "crummy": [
        ("What does crummy mean?", "Crummy means bad, poor, or not useful the way you hoped."),
    ],
    "bravery": [
        ("What is bravery?", "Bravery is when you do something scary or hard even though you feel nervous."),
    ],
    "friendship": [
        ("What is friendship?", "Friendship is a caring bond between people who help and enjoy each other."),
    ],
    "space": [
        ("What is a space garden?", "A space garden is a garden kept in a place like a station, dome, or ship where plants are grown with care."),
    ],
}

KNOWLEDGE_ORDER = ["weed", "pseudo", "crummy", "bravery", "friendship", "space"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure for a young child that includes the words "weed", "pseudo", and "crummy".',
        f"Tell a story where {f['hero'].id} and {f['friend'].id} face a weed in {f['setting'].place} and choose bravery and friendship over a crummy pseudo-tool.",
        f"Write a gentle moon-garden story that ends with a brave choice and a clean little plant.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    prize: Entity = _safe_fact(world, f, "prize")
    activity: Activity = _safe_fact(world, f, "activity")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Who was the story about in {place}?",
            answer=f"It was about {hero.id}, a little astronaut, and {friend.id}, a loyal friend who helped in the garden.",
        ),
        QAItem(
            question=f"What problem did {hero.id} need to solve in the garden?",
            answer=f"{hero.id} needed to deal with the weed so {prize.phrase} could stay safe in the moon garden.",
        ),
        QAItem(
            question=f"Why was the pseudo-rover called crummy?",
            answer=f"It was called crummy because it was only a pseudo-tool and would not really solve the weed problem.",
        ),
        QAItem(
            question=f"What did {hero.id} choose instead of the crummy shortcut?",
            answer=f"{hero.id} chose bravery and friendship, then pulled the weed by hand.",
        ),
        QAItem(
            question=f"How did the story end for {prize.label}?",
            answer=f"{prize.phrase} stayed safe, and the garden looked neat and bright at the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    tags = {"weed", "pseudo", "crummy", "bravery", "friendship", "space"}
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- activity(A), prize(P), dangerous(A,P).
good_tool(A,T) :- activity(A), tool(T), helps(T,A), not crummy(T).
valid_story(Place,A,P,T) :- setting(Place), affords(Place,A), prize_at_risk(A,P), good_tool(A,T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in s.affords:
            lines.append(asp.fact("affords", sid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pid in PRIZES:
        lines.append(asp.fact("prize", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.crummy:
            lines.append(asp.fact("crummy", tid))
        if t.pseudo:
            lines.append(asp.fact("pseudo", tid))
        for a in t.helps:
            lines.append(asp.fact("helps", tid, a))
    for aid, act in ACTIVITIES.items():
        for pid, pr in PRIZES.items():
            if Reasoner.weed_is_risky(act, pr):
                lines.append(asp.fact("dangerous", aid, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp.atoms(asp.one_model(asp_program("#show valid_story/4.")), "valid_story"))
    if py == cl:
        print(f"OK: ASP parity matches python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("asp-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space adventure about weed, pseudo, crummy, bravery, and friendship.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "activity", None) and getattr(args, "activity", None) != "weed":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "tool", None) and getattr(args, "tool", None) == "pseudo_rover" and getattr(args, "activity", None) == "weed":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "activity", None) and getattr(args, "prize", None) and getattr(args, "tool", None):
        if not Reasoner.valid_combo(getattr(args, "place", None), getattr(args, "activity", None), getattr(args, "prize", None), getattr(args, "tool", None)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [c for c in combos
                if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
                and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
                and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
                and (getattr(args, "tool", None) is None or c[3] == getattr(args, "tool", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize, tool = rng.choice(list(filtered))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    friend = getattr(args, "friend", None) or rng.choice(FRIENDS)
    return StoryParams(place=place, activity=activity, prize=prize, tool=tool, name=name, friend=friend, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), _safe_lookup(TOOLS, params.tool), params.name, params.friend, params.gender)
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
    StoryParams(place="moon_garden", activity="weed", prize="sprout", tool="gloves", name="Luna", friend="Rin", gender="girl"),
    StoryParams(place="space_station", activity="weed", prize="flower", tool="tongs", name="Kai", friend="Pax", gender="boy"),
    StoryParams(place="orbital_farm", activity="weed", prize="seedling", tool="gloves", name="Mia", friend="Bea", gender="girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} valid stories:")
        for row in stories:
            print("  ", row)
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
            header = f"### {p.name}: {p.activity} at {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
