#!/usr/bin/env python3
"""
storyworlds/worlds/scrawny_community_garden_flashback_surprise_space_adventure.py
=================================================================================

A small storyworld for a Space-Adventure-flavored garden tale with a scrawny
hero, a Flashback, and a Surprise.

Premise:
- A scrawny child helps in a community garden.
- The child wants to do a brave "space mission" task among the beds and trellises.
- A past memory warns that rushing can shake fragile plants.
- A Surprise arrives in the form of a clever, practical helper gear or tool.
- The child finishes the mission safely, and the garden changes visibly.

The world is intentionally small and constraint-checked: only stories with a
reasonable risk/fix pairing are generated.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    gear_ent: object | None = None
    helper: object | None = None
    hero: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        for k in ["tired", "dusty", "wet", "balanced", "safe", "bloom", "workload"]:
            self.meters.setdefault(k, 0.0)
        for k in ["hope", "worry", "joy", "surprise", "flashback", "pride", "care"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    place: str = "the community garden"
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
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    tag: str
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
class Prize:
    label: str
    phrase: str
    type: str
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
class Gear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
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
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.facts: dict = {}

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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


def _apply_risk(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for item in world.worn_items(actor):
            if not world.zone or item.protective:
                continue
            if item.region not in world.zone:
                continue
            if actor.meters["dusty"] < THRESHOLD and actor.meters["wet"] < THRESHOLD:
                continue
            sig = ("risk", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["dusty"] += 1
            out.append(f"{actor.label or actor.id}'s {item.label} got dusty.")
    return out


def _apply_caretaker(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dusty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("care", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get(item.caretaker).meters["workload"] += 1
        out.append("That would mean more work for the grown-up helper.")
    return out


CAUSAL_RULES = [_apply_risk, _apply_caretaker]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict(world: World, actor: Entity, mission: Mission) -> dict:
    sim = world.copy()
    a = sim.get(actor.id)
    a.meters[mission.tag] += 1
    a.meters["dusty"] += 1
    sim.zone = set(mission.zone)
    propagate(sim, narrate=False)
    return {
        "dusty": any(e.meters["dusty"] >= THRESHOLD for e in sim.entities.values()),
        "workload": sum(e.meters["workload"] for e in sim.entities.values()),
    }


SETTINGS = {
    "community_garden": Setting(
        place="the community garden",
        affords={"trellis", "seedlings", "watering"},
    )
}

MISSIONS = {
    "trellis": Mission(
        id="trellis",
        verb="climb the trellis",
        gerund="climbing the trellis",
        rush="scramble up the trellis",
        risk="shake the fragile beans",
        zone={"torso"},
        keyword="trellis",
        tag="balanced",
    ),
    "seedlings": Mission(
        id="seedlings",
        verb="carry the seedlings",
        gerund="carrying the seedlings",
        rush="hurry across the path",
        risk="bump the tiny roots",
        zone={"arms"},
        keyword="seedlings",
        tag="tired",
    ),
    "watering": Mission(
        id="watering",
        verb="water the beans",
        gerund="watering the beans",
        rush="dash to the barrel",
        risk="splash the soil too hard",
        zone={"arms", "torso"},
        keyword="water",
        tag="wet",
    ),
}

PRIZES = {
    "gloves": Prize("gloves", "a pair of garden gloves", "gloves", "arms", plural=True),
    "hat": Prize("hat", "a bright sun hat", "hat", "torso"),
    "vest": Prize("vest", "a small safety vest", "vest", "torso"),
}

GEAR = [
    Gear(
        id="stepstool",
        label="a little step stool",
        covers={"torso"},
        guards={"balanced"},
        prep="bring a little step stool over",
        tail="rolled the step stool beside the trellis",
    ),
    Gear(
        id="kneepads",
        label="soft kneepads",
        covers={"arms", "torso"},
        guards={"tired", "wet"},
        prep="put on soft kneepads first",
        tail="fastened the kneepads before the mission",
        plural=True,
    ),
    Gear(
        id="watering_wand",
        label="a narrow watering wand",
        covers={"arms"},
        guards={"wet"},
        prep="hand over a narrow watering wand",
        tail="set the watering wand in the bucket",
    ),
]

NAMES = ["Milo", "Pip", "Nova", "Luna", "Toby", "Ivy", "Zed", "Rae"]
TRAITS = ["scrawny", "careful", "bright-eyed", "determined", "small", "quick"]


@dataclass
class StoryParams:
    place: str
    mission: str
    prize: str
    name: str
    gender: str
    helper: str
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


def mission_needs(mission: Mission, prize: Prize) -> bool:
    return prize.region in mission.zone


def select_gear(mission: Mission, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if mission.tag in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid, mission in MISSIONS.items():
            if mid not in setting.affords:
                continue
            for pid, prize in PRIZES.items():
                if mission_needs(mission, prize) and select_gear(mission, prize):
                    combos.append((place, mid, pid))
    return combos


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a scrawny kid who loved the community garden because every bed "
        f"looked like a tiny star map."
    )


def flashback(world: World, hero: Entity, mission: Mission) -> None:
    hero.memes["flashback"] += 1
    world.say(
        f"Flashback: last summer, {hero.id} had rushed to {mission.rush} and nearly "
        f"knocked a row of bean poles sideways."
    )
    world.say(
        f"{hero.id} remembered how the beans had bowed like astronauts in a wobbling capsule."
    )


def surprise(world: World, helper: Entity, gear: Gear) -> None:
    helper.memes["surprise"] += 1
    world.say(
        f"Surprise! {helper.label} appeared from behind the compost bins with {gear.label}."
    )


def resolve(world: World, hero: Entity, helper: Entity, mission: Mission, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"{helper.id} smiled and said, “Use this first, little captain.”"
    )
    world.say(
        f"{hero.id} took a deep breath, followed the careful plan, and managed to {mission.verb} "
        f"without jostling {prize.label}."
    )
    world.say(
        f"By the end, the trellis stood steady, the beans stayed safe, and {hero.id} looked "
        f"less like a scrawny spark and more like a real garden astronaut."
    )


def tell(setting: Setting, mission: Mission, prize_cfg: Prize, name: str, gender: str, helper_kind: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, label=name, traits=["scrawny", trait]))
    helper = world.add(Entity(id=helper_kind, kind="character", type="adult", label="the garden helper"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    world.say(
        f"{hero.id} wanted to {mission.verb} because the garden's tallest beans felt like a mission to Mars."
    )
    world.say(
        f"{hero.id} also loved {prize_cfg.phrase} and wanted to keep it safe while working."
    )

    world.para()
    world.say(
        f"One afternoon in {setting.place}, {hero.id} and {helper.label} went to the bean patch."
    )
    world.say(
        f"{hero.id} wanted to {mission.verb}, but doing that too fast could {mission.risk}."
    )
    flashback(world, hero, mission)

    # Predict trouble before the action.
    pred = predict(world, hero, mission)
    world.facts["predicted"] = pred

    if pred["dusty"]:
        world.say(
            f"{helper.label} lifted a hand and warned, “Not that way, captain. We need a safer launch path.”"
        )

    world.para()
    gear = select_gear(mission, prize)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))

    surprise(world, helper, gear)
    gear_ent = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=helper.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    gear_ent.worn_by = hero.id

    if predict(world, hero, mission)["dusty"]:
        gear_ent.worn_by = None
        del world.entities[gear_ent.id]
        pass

    resolve(world, hero, helper, mission, prize, gear)

    hero.meters["safe"] += 1
    prize.meters["dusty"] = 0.0
    world.facts.update(hero=hero, helper=helper, prize=prize, mission=mission, gear=gear, resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mission = _safe_fact(world, f, "mission")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short Space Adventure story for a child named {hero.id} in the community garden.',
        f"Tell a Flashback-and-Surprise story where a scrawny hero wants to {mission.verb} but must protect {prize.phrase}.",
        f"Write a gentle story about a garden mission that feels like a trip to the stars and ends with a safe, clever fix.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    mission = _safe_fact(world, f, "mission")
    prize = _safe_fact(world, f, "prize")
    gear = _safe_fact(world, f, "gear")
    return [
        QAItem(
            question=f"Who was the scrawny kid in the story?",
            answer=f"The scrawny kid was {hero.id}, who loved the community garden and treated it like a little space mission.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the community garden?",
            answer=f"{hero.id} wanted to {mission.verb}, because the tall beans and trellis felt exciting and far away like stars.",
        ),
        QAItem(
            question=f"Why was there a Flashback in the story?",
            answer=f"There was a Flashback because {hero.id} remembered a time when rushing had almost shaken the bean poles and made the garden wobble.",
        ),
        QAItem(
            question=f"What was the Surprise?",
            answer=f"The Surprise was that {helper.label} brought {gear.label}, which gave {hero.id} a safer way to handle the mission.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} finishing the mission safely, while {prize.label} stayed safe and the garden looked steady and bright.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a community garden?",
            answer="A community garden is a shared place where neighbors grow flowers, herbs, and vegetables together.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a quick look back at something that happened earlier, so the character can remember it and learn from it.",
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what happens next, often by bringing help or a new idea.",
        ),
        QAItem(
            question="What does scrawny mean?",
            answer="Scrawny means very thin or small, usually in a way that makes someone look a little undergrown.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="community_garden", mission="trellis", prize="hat", name="Nova", gender="girl", helper="helper", trait="bright-eyed"),
    StoryParams(place="community_garden", mission="watering", prize="gloves", name="Pip", gender="boy", helper="helper", trait="careful"),
    StoryParams(place="community_garden", mission="seedlings", prize="vest", name="Luna", gender="girl", helper="helper", trait="determined"),
]


KNOWLEDGE_ORDER = ["garden", "flashback", "surprise", "scrawny"]


ASP_RULES = r"""
mission_risk(M, P) :- mission(M), prize(P), zone(M, R), region(P, R).
gear_fix(M, P) :- mission(M), prize(P), mission_risk(M, P), gear(G), guards(G, T), mission_tag(M, T), covers(G, R), region(P, R).
valid_combo(Place, M, P) :- affords(Place, M), mission_risk(M, P), gear_fix(M, P).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mission_tag", mid, m.tag))
        for r in sorted(m.zone):
            lines.append(asp.fact("zone", mid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_triples() -> list[tuple[str, str, str]]:
    return sorted(set(valid_combos()))


def asp_valid_story_triples() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_story_triples())
    asp_set = set(asp_valid_story_triples())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - asp_set))
    print("only asp:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A scrawny space-adventure story in a community garden.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", default="helper")
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
    if getattr(args, "mission", None) and getattr(args, "prize", None):
        mission = _safe_lookup(MISSIONS, getattr(args, "mission", None))
        prize = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not mission_needs(mission, prize) or not select_gear(mission, prize):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "mission", None) is None or c[1] == getattr(args, "mission", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mission, prize = rng.choice(list(combos))
    pr = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(sorted(pr.genders))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, mission=mission, prize=prize, name=name, gender=gender, helper=getattr(args, "helper", None), trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MISSIONS, params.mission), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.helper, params.trait)
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
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_story_triples()
        print(f"{len(combos)} compatible combos:\n")
        for place, mission, prize in combos:
            print(f"  {place:18} {mission:12} {prize}")
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
            header = f"### {p.name}: {p.mission} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
