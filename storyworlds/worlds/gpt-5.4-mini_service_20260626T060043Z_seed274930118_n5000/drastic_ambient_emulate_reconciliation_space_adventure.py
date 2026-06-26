#!/usr/bin/env python3
"""
Space-adventure storyworld with a reconciliation turn.

Seed premise:
- A small crew is aboard a ship drifting through a colorful nebula.
- One character wants a drastic course change to save an ambient-signal probe.
- Another character resists, worried the maneuver is too risky.
- They reconcile by emulating a careful pilot routine and sharing the work.

This script generates one tiny, classical story with:
setup -> tension -> turn -> reconciliation.
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
    worn_by: Optional[str] = None
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    pal: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "pilot", "captain"}
        female = {"girl", "woman", "mother", "mom"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    place: str = "the starship"
    backdrop: str = "a glowing nebula"
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
class Mission:
    id: str
    verb: str
    gerund: str
    danger: str
    risk: str
    mood: str
    tag: str
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
class Gear:
    id: str
    label: str
    helps: set[str]
    offers: str
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
        import copy
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "nebula": Setting(place="the starship", backdrop="a glowing nebula", affords={"drift", "scan", "dock"}),
    "orbit": Setting(place="the space station", backdrop="the planet below", affords={"scan", "dock"}),
    "moonbay": Setting(place="the moon bay", backdrop="a silver moon horizon", affords={"dock", "repair"}),
}

MISSIONS = {
    "drift": Mission(
        id="drift",
        verb="change course",
        gerund="changing course",
        danger="drastic",
        risk="too drastic",
        mood="urgent",
        tag="drastic",
        requires={"scan"},
    ),
    "scan": Mission(
        id="scan",
        verb="scan the ambient signal",
        gerund="scanning the ambient signal",
        danger="fragile",
        risk="too rough",
        mood="careful",
        tag="ambient",
        requires={"scan"},
    ),
    "dock": Mission(
        id="dock",
        verb="dock with the beacon",
        gerund="docking with the beacon",
        danger="tight",
        risk="too risky",
        mood="steady",
        tag="reconcile",
        requires={"dock"},
    ),
    "repair": Mission(
        id="repair",
        verb="repair the antenna",
        gerund="repairing the antenna",
        danger="delicate",
        risk="too shaky",
        mood="patient",
        tag="emulate",
        requires={"repair"},
    ),
}

GEAR = {
    "gloves": Gear(
        id="gloves",
        label="magnetic gloves",
        helps={"dock"},
        offers="put on magnetic gloves first",
        prep="put on magnetic gloves first",
        tail="slid into the gloves",
    ),
    "tablet": Gear(
        id="tablet",
        label="a pilot tablet",
        helps={"scan", "drift"},
        offers="use the pilot tablet to emulate the old flight routine",
        prep="use the pilot tablet to emulate the old flight routine",
        tail="held the pilot tablet together",
    ),
    "visor": Gear(
        id="visor",
        label="a light visor",
        helps={"scan"},
        offers="wear a light visor to read the ambient signal",
        prep="wear a light visor to read the ambient signal",
        tail="wore the visor side by side",
    ),
}

NAMES = ["Ari", "Mina", "Juno", "Kai", "Luz", "Nico", "Rhea", "Tari"]
TYPES = {"girl", "boy"}
TRAITS = ["curious", "brave", "careful", "stubborn", "gentle", "steady"]


# ---------------------------------------------------------------------------
# Contract dataclass
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    mission: str
    gear: str
    name: str
    friend: str
    gender: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
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


def mission_at_risk(mission: Mission, gear: Gear) -> bool:
    return mission.id in gear.helps


def select_gear(mission: Mission) -> Optional[Gear]:
    for g in GEAR.values():
        if mission.id in g.helps:
            return g
    return None


def validate_combo(setting: Setting, mission: Mission) -> bool:
    return mission.id in setting.affords and select_gear(mission) is not None


def _apply_drama(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    mission: Mission = _safe_fact(world, world.facts, "mission")
    if hero.memes.get("worry", 0) >= THRESHOLD and friend.memes.get("worry", 0) >= THRESHOLD:
        world.trace.append("tension: both crew members are worried")
    if mission.id == "drift" and hero.meters.get("speed", 0) >= THRESHOLD:
        world.trace.append("state: ship speed increases")


def predict(world: World, mission: Mission) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.memes["worry"] = 1.0
    hero.meters["speed"] = 1.0 if mission.id == "drift" else 0.0
    return {"risk": mission.danger, "drastic": mission.tag == "drastic"}


# ---------------------------------------------------------------------------
# Story beats
# ---------------------------------------------------------------------------

def opening(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    mission: Mission = _safe_fact(world, world.facts, "mission")
    setting = world.setting
    world.say(
        f"{hero.id} was a {world.facts['trait']} young pilot aboard {setting.place}, "
        f"watching {setting.backdrop} through the windows."
    )
    world.say(
        f"{hero.id} and {friend.id} had one job: {mission.gerund} without losing the tiny probe."
    )


def tension(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    mission: Mission = _safe_fact(world, world.facts, "mission")
    world.para()
    world.say(
        f"The signal flickered soft and ambient, but {hero.id} wanted a drastic move right away."
    )
    world.say(
        f"{friend.id} shook {friend.pronoun('possessive')} head and said the plan sounded too risky."
    )
    hero.memes["worry"] = 1.0
    friend.memes["worry"] = 1.0
    _apply_drama(world)


def turn_and_reconcile(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    mission: Mission = _safe_fact(world, world.facts, "mission")
    gear = _safe_fact(world, world.facts, "gear_obj")
    world.para()
    world.say(
        f"Then {hero.id} remembered how the old captain used to work: slow, steady, and clear."
    )
    world.say(
        f"{hero.id} and {friend.id} chose to emulate that routine together and use {gear.label}."
    )
    world.say(
        f"{hero.id} said, \"Let's do it my way only this time, and you can check the lights.\""
    )
    world.say(
        f"{friend.id} smiled, and the two of them started to reconcile while they worked."
    )
    hero.memes["worry"] = 0.0
    friend.memes["worry"] = 0.0
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    friend.memes["trust"] = friend.memes.get("trust", 0) + 1
    world.facts["reconciled"] = True


def ending(world: World) -> None:
    hero = world.get("hero")
    friend = world.get("friend")
    mission: Mission = _safe_fact(world, world.facts, "mission")
    gear = _safe_fact(world, world.facts, "gear_obj")
    world.para()
    world.say(
        f"At last they finished {mission.gerund}, and the probe blinked safe and bright."
    )
    world.say(
        f"{hero.id} and {friend.id} floated side by side, still wearing {gear.label}, "
        f"as the ship drifted calmly past the glowing nebula."
    )


def tell(setting: Setting, mission: Mission, gear: Gear, name: str, friend: str, gender: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    pal = world.add(Entity(id=friend, kind="character", type="boy" if gender == "girl" else "girl"))
    world.facts["trait"] = trait
    world.facts["mission"] = mission
    world.facts["gear"] = gear.id
    world.facts["gear_obj"] = gear
    world.facts["setting"] = setting.place

    opening(world)
    tension(world)
    turn_and_reconcile(world)
    ending(world)
    world.facts["hero"] = hero
    world.facts["friend_entity"] = pal
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def prompts(world: World) -> list[str]:
    mission: Mission = _safe_fact(world, world.facts, "mission")
    return [
        f'Write a short space story for a young child that includes the word "{mission.tag}" and a reconciliation.',
        f"Tell a gentle spaceship story where two friends disagree, then reconcile by emulating an old routine.",
        f"Write a TinyStories-style adventure about a {mission.gerund} mission and a careful compromise.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    friend = _safe_fact(world, world.facts, "friend_entity")
    mission: Mission = _safe_fact(world, world.facts, "mission")
    gear: Gear = _safe_fact(world, world.facts, "gear_obj")
    setting = _safe_fact(world, world.facts, "setting")
    return [
        QAItem(
            question=f"Who wanted the drastic change during the mission on {setting}?",
            answer=f"{hero.id} wanted the drastic move because the signal looked urgent and ambient.",
        ),
        QAItem(
            question=f"Why did {friend.id} worry about the plan?",
            answer=f"{friend.id} worried because the change felt too drastic and too risky for the tiny probe.",
        ),
        QAItem(
            question=f"How did the two friends fix the problem?",
            answer=f"They reconciled by emulating the old captain's routine and using {gear.label}.",
        ),
        QAItem(
            question=f"What was the ship doing at the end?",
            answer=f"The ship was calmly drifting past the nebula after {mission.gerund} was finished safely.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to reconcile?",
            answer="To reconcile means to make peace again after a disagreement and work together once more.",
        ),
        QAItem(
            question="What does ambient mean?",
            answer="Ambient means all around you, like a soft sound or light that fills the space nearby.",
        ),
        QAItem(
            question="What does emulate mean?",
            answer="To emulate means to copy a good example and try to do it the same careful way.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
mission_valid(S, M) :- setting(S), mission(M), affords(S, M), gear(G), helps(G, M).
reconcile(S, M) :- mission_valid(S, M), mission(M), tag(M, reconcile).
drastic(M) :- tag(M, drastic).
ambient(M) :- tag(M, ambient).
emulate(M) :- tag(M, emulate).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("tag", mid, m.tag))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for m in sorted(g.helps):
            lines.append(asp.fact("helps", gid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show mission_valid/2."))
    return sorted(set(asp.atoms(model, "mission_valid")))


def valid_pairs() -> list[tuple]:
    out = []
    for sid, setting in SETTINGS.items():
        for mid, mission in MISSIONS.items():
            if validate_combo(setting, mission):
                out.append((sid, mid))
    return sorted(out)


def asp_verify() -> int:
    a = set(asp_valid())
    b = set(valid_pairs())
    if a == b:
        print(f"OK: ASP gate matches Python gate ({len(a)} pairs).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    if a - b:
        print("  only in ASP:", sorted(a - b))
    if b - a:
        print("  only in Python:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    mission: str
    gear: str
    name: str
    friend: str
    gender: str
    trait: str
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
    ap = argparse.ArgumentParser(description="Space adventure storyworld with reconciliation.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    valid = valid_pairs()
    if getattr(args, "setting", None) and getattr(args, "mission", None):
        if (getattr(args, "setting", None), getattr(args, "mission", None)) not in valid:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [p for p in valid
              if (getattr(args, "setting", None) is None or p[0] == getattr(args, "setting", None))
              and (getattr(args, "mission", None) is None or p[1] == getattr(args, "mission", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, mission = rng.choice(combos)
    ms = _safe_lookup(MISSIONS, mission)
    gear = getattr(args, "gear", None) or select_gear(ms).id
    if gear not in GEAR or mission not in GEAR[gear].helps:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in NAMES if n != name])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, mission=mission, gear=gear, name=name, friend=friend, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    mission = _safe_lookup(MISSIONS, params.mission)
    gear = GEAR[params.gear]
    world = tell(setting, mission, gear, params.name, params.friend, params.gender, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    if world.trace:
        lines.append("  trace: " + "; ".join(world.trace))
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print("== prompts ==")
        for i, p in enumerate(sample.prompts, 1):
            print(f"{i}. {p}")
        print()
        print("== story qa ==")
        for item in sample.story_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")
        print()
        print("== world qa ==")
        for item in sample.world_qa:
            print(f"Q: {item.question}")
            print(f"A: {item.answer}")


CURATED = [
    StoryParams(setting="nebula", mission="drift", gear="tablet", name="Ari", friend="Mina", gender="boy", trait="curious"),
    StoryParams(setting="orbit", mission="scan", gear="visor", name="Luz", friend="Kai", gender="girl", trait="careful"),
    StoryParams(setting="moonbay", mission="dock", gear="gloves", name="Rhea", friend="Nico", gender="girl", trait="steady"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show mission_valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        pairs = asp_valid()
        print(f"{len(pairs)} compatible setting/mission pairs:")
        for s, m in pairs:
            print(f"  {s:8} {m}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
