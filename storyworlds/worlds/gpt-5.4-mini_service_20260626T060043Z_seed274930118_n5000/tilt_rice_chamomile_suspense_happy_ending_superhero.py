#!/usr/bin/env python3
"""
Storyworld: Tilted Rice and Chamomile Rescue
============================================

A small superhero-style storyworld about a child hero, a careful kitchen job,
a suspenseful near-miss, and a happy ending.

Seed imagery:
- tilt
- rice
- chamomile

Premise:
A little superhero is helping make a comforting meal and tea for someone at
home. The work needs careful balance: rice must be rinsed, the pot must be
carried level, and chamomile tea must steep without spilling. A tiny mistake
creates suspense, but the hero uses focus, a helper tool, and a brave choice to
finish with a happy ending.

This script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven narration
- inline ASP twin plus Python reasonableness gate
- StorySample / QAItem / StoryError from storyworlds/results.py
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    placed_in: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    mentor: object | None = None
    rice: object | None = None
    shield: object | None = None
    sidekick: object | None = None
    tea: object | None = None
    tool_ent: object | None = None
    tray: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "sister"}
        male = {"boy", "father", "dad", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
    indoor: bool
    affords: set[str] = field(default_factory=set)
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
class Action:
    id: str
    verb: str
    gerund: str
    risk: str
    hazard: str
    weather: str
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
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
    helps: set[str]
    protects: set[str]
    plural: bool = False
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
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _default_meters() -> dict[str, float]:
    return {"steady": 0.0, "risk": 0.0, "spill": 0.0, "steam": 0.0, "mess": 0.0}


def _default_memes() -> dict[str, float]:
    return {"hope": 0.0, "fear": 0.0, "focus": 0.0, "joy": 0.0, "bravery": 0.0}


def is_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.tags


def select_tool(action: Action, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if action.id in tool.helps and prize.region in tool.protects:
            return tool
    return None


def predict_outcome(world: World, hero: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    perform_action(sim, sim.get(hero.id), action, narrate=False)
    prize = sim.get(prize_id)
    return {
        "ruined": prize.meters.get("spill", 0.0) >= THRESHOLD or prize.meters.get("mess", 0.0) >= THRESHOLD,
        "risk": hero.memes.get("fear", 0.0),
    }


def perform_action(world: World, hero: Entity, action: Action, narrate: bool = True) -> None:
    hero.meters[action.id] = hero.meters.get(action.id, 0.0) + 1.0
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1.0
    if action.id == "tilt":
        hero.memes["fear"] = hero.memes.get("fear", 0.0) + 1.0
        if narrate:
            world.say(
                f"{hero.id} had to tilt the tray just a little, and everyone held their breath."
            )
        for ent in list(world.entities.values()):
            if ent.kind == "thing" and ent.placed_in == "tray":
                ent.meters["risk"] = ent.meters.get("risk", 0.0) + 1.0
    elif action.id == "rice":
        hero.meters["rice"] = hero.meters.get("rice", 0.0) + 1.0
        if narrate:
            world.say(
                f"{hero.id} rinsed the rice until the water ran clear and the grains looked ready."
            )
    elif action.id == "chamomile":
        hero.meters["steam"] = hero.meters.get("steam", 0.0) + 1.0
        if narrate:
            world.say(
                f"{hero.id} watched the chamomile bloom in hot water, turning the room soft and calm."
            )
    if narrate:
        apply_consequences(world)


def apply_consequences(world: World) -> None:
    hero = world.get("hero")
    rice = world.get("rice_pot")
    tea = world.get("tea_cup")
    tray = world.get("tray")
    if hero.meters.get("tilt", 0.0) >= 1.0 and not hero.memes.get("steady_boost", 0.0):
        rice.meters["spill"] = rice.meters.get("spill", 0.0) + 1.0
        tea.meters["spill"] = tea.meters.get("spill", 0.0) + 1.0
        tray.meters["mess"] = tray.meters.get("mess", 0.0) + 1.0
        world.say("A wobble sent a few drops toward the tray, and the little kitchen grew tense.")
    if hero.memes.get("focus", 0.0) >= THRESHOLD and hero.memes.get("fear", 0.0) >= THRESHOLD:
        world.say("But the hero did not panic. The hero looked down, planted both feet, and breathed slowly.")
        hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1.0
        hero.memes["fear"] = 0.0
    if hero.meters.get("steady", 0.0) >= 1.0:
        rice.meters["spill"] = 0.0
        tea.meters["spill"] = 0.0
        tray.meters["mess"] = 0.0
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
        world.say("With a steady hand, the hero set everything level again, and nothing fell.")
    if tea.meters.get("steam", 0.0) >= 1.0 and rice.meters.get("spill", 0.0) < THRESHOLD:
        world.say("The chamomile smelled like a bedtime hug, and the rice stayed neatly piled beside it.")


def setup_world(setting: Setting) -> World:
    w = World(setting)
    hero = w.add(Entity("hero", kind="character", type="girl", label="Star Byte", meters=_default_meters(), memes=_default_memes()))
    sidekick = w.add(Entity("sidekick", kind="character", type="boy", label="Pip", meters=_default_meters(), memes=_default_memes()))
    mentor = w.add(Entity("mentor", kind="character", type="mother", label="Mom", meters=_default_meters(), memes=_default_memes()))
    rice = w.add(Entity("rice_pot", kind="thing", type="pot", label="pot of rice", phrase="a warm pot of rice", owner=hero.id, caretaker=mentor.id, meters=_default_meters(), memes=_default_memes()))
    tea = w.add(Entity("tea_cup", kind="thing", type="cup", label="cup of chamomile tea", phrase="a small cup of chamomile tea", owner=mentor.id, caretaker=mentor.id, meters=_default_meters(), memes=_default_memes()))
    tray = w.add(Entity("tray", kind="thing", type="tray", label="silver tray", phrase="a silver tray", meters=_default_meters(), memes=_default_memes()))
    shield = w.add(Entity("shield", kind="thing", type="tool", label="tilt shield", phrase="a little tilt shield", protective=True, covers={"tray", "rice_pot", "tea_cup"}, meters=_default_meters(), memes=_default_memes()))
    rice.placed_in = "tray"
    tea.placed_in = "tray"
    w.facts = {"hero": hero, "sidekick": sidekick, "mentor": mentor, "rice": rice, "tea": tea, "tray": tray, "shield": shield}
    return w


def tell_story(setting: Setting, action: Action, prize: Prize) -> World:
    w = setup_world(setting)
    hero = w.get("hero")
    sidekick = w.get("sidekick")
    mentor = w.get("mentor")
    rice = w.get("rice_pot")
    tea = w.get("tea_cup")
    tool = select_tool(action, prize)

    w.say(
        f"Star Byte was a little superhero who loved helping at home, especially when rice and chamomile were waiting."
    )
    w.say(
        f"Pip watched the counter while Mom lifted the tray and said that this job needed a careful {action.keyword}."
    )
    w.say(
        f"Star Byte wanted to {action.verb}, because the rice had to be ready and the chamomile had to stay warm."
    )

    if is_at_risk(action, prize):
        pred = predict_outcome(w, hero, action, prize.id)
        if pred["ruined"]:
            w.say(
                f"Then came the suspense: one tiny tilt could send the rice sliding, and even the chamomile cup might wobble."
            )
            hero.memes["fear"] += 1.0
            hero.memes["focus"] += 1.0
            w.say(
                f"Star Byte narrowed {hero.pronoun('possessive')} eyes, held still, and listened to Pip call, 'Easy now!'"
            )
            if tool is not None:
                tool_ent = w.add(Entity(tool.id, kind="thing", type="tool", label=tool.label, phrase=tool.phrase, protective=True, covers=set(tool.protects), meters=_default_meters(), memes=_default_memes()))
                w.say(
                    f"Mom placed the {tool_ent.label} under the tray, and that little shield kept the rice and tea from sliding."
                )
                hero.memes["steady_boost"] = 1.0
            hero.meters["steady"] = 1.0
            perform_action(w, hero, action, narrate=True)
            w.say(
                f"At last, the tray stayed level, the rice sat neatly in its pot, and the chamomile smelled sweet and safe."
            )
            w.say(
                f"Star Byte smiled at {mentor.label_word if hasattr(mentor, 'label_word') else mentor.label} and felt like a real hero."
            )
        else:
            hero.meters["steady"] = 1.0
            perform_action(w, hero, action, narrate=True)
    else:
        pass

    w.say("That night, everyone ate dinner, drank the chamomile tea, and laughed because the rescue had worked.")
    w.facts.update({"action": action, "prize": prize, "setting": setting, "tool": tool})
    return w


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"tilt", "rice", "chamomile"}),
    "sunroom": Setting(place="the sunroom", indoor=True, affords={"tilt", "rice", "chamomile"}),
}

ACTIONS = {
    "tilt": Action(
        id="tilt",
        verb="tilt the tray just enough to carry it",
        gerund="tilting the tray",
        risk="wobble",
        hazard="spill",
        weather="",
        keyword="tilt",
        tags={"tray", "rice", "tea"},
    ),
    "rice": Action(
        id="rice",
        verb="wash the rice",
        gerund="washing the rice",
        risk="slosh",
        hazard="spill",
        weather="",
        keyword="rice",
        tags={"rice"},
    ),
    "chamomile": Action(
        id="chamomile",
        verb="pour chamomile tea",
        gerund="pouring chamomile tea",
        risk="splash",
        hazard="spill",
        weather="",
        keyword="chamomile",
        tags={"tea"},
    ),
}

PRIZES = {
    "rice": Prize(id="rice", label="rice", phrase="a pot of rice", region="tray", plural=False),
    "chamomile": Prize(id="chamomile", label="chamomile tea", phrase="a cup of chamomile tea", region="tray", plural=False),
}

TOOLS = [
    Tool(id="shield", label="tilt shield", phrase="a little tilt shield", helps={"tilt"}, protects={"tray"}),
]

GIRL_NAMES = ["Star Byte", "Nova", "Mina", "Ruby", "Iris"]
BOY_NAMES = ["Pip", "Toby", "Finn", "Leo", "Max"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    sidekick_name: str = "Pip"
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero storyworld: tilt, rice, chamomile, suspense, happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--sidekick-name")
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
    for place, setting in SETTINGS.items():
        for action in setting.affords:
            for prize in PRIZES:
                if is_at_risk(_safe_lookup(ACTIONS, action), _safe_lookup(PRIZES, prize)) and select_tool(_safe_lookup(ACTIONS, action), _safe_lookup(PRIZES, prize)):
                    combos.append((place, action, prize))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    sidekick = getattr(args, "sidekick_name", None) or "Pip"
    return StoryParams(place=place, action=action, prize=prize, name=name, sidekick_name=sidekick)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    action: Action = _safe_fact(world, f, "action")  # type: ignore[assignment]
    prize: Prize = _safe_fact(world, f, "prize")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    return [
        f'Write a short superhero story for a young child that features "{action.keyword}", "{prize.label}", and "{setting.place}".',
        f"Tell a suspenseful but happy story about a hero who must {action.verb} without ruining {prize.phrase}.",
        f"Create a gentle superhero rescue story where chamomile, rice, and a careful tilt all matter.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    mentor: Entity = _safe_fact(world, f, "mentor")  # type: ignore[assignment]
    action: Action = _safe_fact(world, f, "action")  # type: ignore[assignment]
    prize: Prize = _safe_fact(world, f, "prize")  # type: ignore[assignment]
    tool = f.get("tool")
    return [
        QAItem(
            question=f"Who was the superhero in the story?",
            answer=f"The superhero was {hero.id}, a brave little hero who helped with {prize.label} and chamomile tea.",
        ),
        QAItem(
            question=f"What made the story suspenseful?",
            answer=f"The story was suspenseful because {hero.id} had to {action.verb} without spilling the rice or the chamomile tea.",
        ),
        QAItem(
            question=f"What helped the hero keep things safe?",
            answer=f"The tilt shield helped keep the tray level, so the rice and chamomile tea stayed safe.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: the tray stayed level, the rice stayed neat, and everyone shared the chamomile tea.",
        ),
        QAItem(
            question=f"Who watched the hero during the rescue?",
            answer=f"{mentor.label if mentor.label else 'Mom'} and Pip watched closely while {hero.id} handled the tray.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is chamomile?",
            answer="Chamomile is a plant often used to make a gentle tea with a soft, calming smell.",
        ),
        QAItem(
            question="Why does rice need careful handling?",
            answer="Rice can spill or scatter if it is tipped too fast, so careful hands help keep it in the bowl or pot.",
        ),
        QAItem(
            question="What does tilt mean?",
            answer="To tilt means to lean something a little to one side instead of keeping it flat.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(f"{ent.id}: kind={ent.kind} type={ent.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- action(A), prize(P), tag(A,R), region(P,R).
has_tool(A,P) :- prize_at_risk(A,P), tool(T), helps(T,A), protects(T,R), region(P,R).
valid_story(Place,A,P) :- setting(Place), affords(Place,A), prize_at_risk(A,P), has_tool(A,P).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    out = []
    for sid, setting in SETTINGS.items():
        out.append(asp.fact("setting", sid))
        if setting.indoor:
            out.append(asp.fact("indoor", sid))
        for a in sorted(setting.affords):
            out.append(asp.fact("affords", sid, a))
    for aid, action in ACTIONS.items():
        out.append(asp.fact("action", aid))
        for t in sorted(action.tags):
            out.append(asp.fact("tag", aid, t))
    for pid, prize in PRIZES.items():
        out.append(asp.fact("prize", pid))
        out.append(asp.fact("region", pid, prize.region))
    for tid, tool in TOOLS:
        pass
    for tool in TOOLS:
        out.append(asp.fact("tool", tool.id))
        for a in sorted(tool.helps):
            out.append(asp.fact("helps", tool.id, a))
        for r in sorted(tool.protects):
            out.append(asp.fact("protects", tool.id, r))
    return "\n".join(out)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("only in asp:", sorted(asp_set - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize))
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
    StoryParams(place="kitchen", action="tilt", prize="rice", name="Star Byte", sidekick_name="Pip"),
    StoryParams(place="sunroom", action="tilt", prize="chamomile", name="Nova", sidekick_name="Pip"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp

        model = asp.one_model(asp_program("#show valid_story/3."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
            rng = random.Random(seed)
            try:
                params = resolve_params(args, rng)
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
