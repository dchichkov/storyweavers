#!/usr/bin/env python3
"""
storyworlds/worlds/seminar_galore_surprise_twist_mystery.py
===========================================================

A small mystery-flavored story world about a lively seminar, a missing item,
and a gentle surprise twist.

The seed words for this world are "seminar" and "galore"; the narrative
instrumentation is surprise and twist, with a cozy mystery tone.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    guardian: object | None = None
    hero: object | None = None
    prize: object | None = None
    tool: object | None = None
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
class Mystery:
    id: str
    label: str
    verb: str
    clue: str
    surprise: str
    twist: str
    mess: str
    zone: set[str]
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
class Aid:
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


def _r_bump_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mist in MYSTERIES.values():
            if actor.meters.get(mist.mess, 0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.region not in world.zone:
                    continue
                if ("soil", item.id, mist.id) in world.fired:
                    continue
                world.fired.add(("soil", item.id, mist.id))
                item.meters[mist.mess] = item.meters.get(mist.mess, 0) + 1
                item.meters["dusty"] = item.meters.get("dusty", 0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got dusty.")
    return out


CAUSAL_RULES = []


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


def mystery_at_risk(mystery: Mystery, prize: Prize) -> bool:
    return prize.region in mystery.zone


def select_aid(mystery: Mystery, prize: Prize) -> Optional[Aid]:
    for aid in AIDS:
        if mystery.mess in aid.guards and prize.region in aid.covers:
            return aid
    return None


def predict(world: World, hero: Entity, mystery: Mystery, prize_id: str) -> dict:
    sim = world.copy()
    perform_mystery(sim, sim.get(hero.id), mystery, narrate=False)
    prize = sim.entities[prize_id]
    return {"dusty": prize.meters.get("dusty", 0) >= THRESHOLD}


def perform_mystery(world: World, hero: Entity, mystery: Mystery, narrate: bool = True) -> None:
    if mystery.id not in world.setting.affords:
        return
    world.zone = set(mystery.zone)
    hero.meters[mystery.mess] = hero.meters.get(mystery.mess, 0) + 1
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return f"The {setting.place} was quiet, but the tables were ready and the lights were warm."
    return f"{setting.place.capitalize()} looked bright and busy, like it was waiting for something big."


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved noticing tiny clues.")


def loves_seminar(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["interest"] = hero.memes.get("interest", 0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved the seminar because there were {mystery.label} galore, "
        f"and every table seemed to hide a clue."
    )


def arrive(world: World, hero: Entity, guardian: Entity, mystery: Mystery) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {guardian.label} went to {world.setting.place} "
        f"for the seminar."
    )
    world.say(setting_detail(world.setting))


def notice_missing(world: World, hero: Entity, prize: Entity, mystery: Mystery) -> None:
    world.say(
        f"{hero.id} noticed something odd: the {prize.label} was missing from the welcome table."
    )
    world.say(
        f"That made the room feel like a mystery, because everyone had expected {mystery.label} galore."
    )


def warn(world: World, guardian: Entity, hero: Entity, mystery: Mystery, prize: Entity) -> bool:
    pred = predict(world, hero, mystery, prize.id)
    if not pred["dusty"]:
        return False
    world.facts["predicted_dusty"] = True
    world.say(
        f'"If you rush into the {mystery.label}, your {prize.label} could get dusty," '
        f"{guardian.pronoun('possessive')} {guardian.label} said."
    )
    return True


def surprise_beats(world: World, hero: Entity, guardian: Entity, mystery: Mystery) -> None:
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"{hero.id} frowned, but {hero.pronoun()} kept looking at the clues."
    )
    world.say(
        f"Then came a surprise: the loudspeaker crackled, and a twist in the plan made everyone pause."
    )


def reveal_twist(world: World, hero: Entity, guardian: Entity, mystery: Mystery, prize: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    world.say(
        f"The twist was that the missing {prize.label} was tucked inside the stack of handouts all along."
    )
    world.say(
        f"{hero.id} giggled, because the mystery had been hiding in plain sight."
    )


def compromise(world: World, guardian: Entity, hero: Entity, mystery: Mystery, prize: Entity) -> Optional[Aid]:
    aid = select_aid(mystery, prize)
    if aid is None:
        return None
    tool = world.add(Entity(
        id=aid.id,
        type="thing",
        label=aid.label,
        owner=hero.id,
        caretaker=guardian.id,
        worn_by=hero.id,
        plural=aid.plural,
    ))
    if predict(world, hero, mystery, prize.id)["dusty"]:
        tool.worn_by = None
        del world.entities[tool.id]
        return None
    world.say(
        f"{guardian.id} smiled and said they could use {aid.prep}."
    )
    return aid


def accept(world: World, guardian: Entity, hero: Entity, mystery: Mystery, prize: Entity, aid: Aid) -> None:
    world.say(
        f"{hero.id} nodded, and soon they {aid.tail}."
    )
    world.say(
        f"With the {mystery.label} sorted out, the seminar began at last, and the room held {mystery.label} galore."
    )


def tell(setting: Setting, mystery: Mystery, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait, "curious"]))
    guardian = world.add(Entity(id="Guardian", kind="character", type=parent_type, label=parent_type))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=guardian.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero)
    loves_seminar(world, hero, mystery)
    arrive(world, hero, guardian, mystery)

    world.para()
    notice_missing(world, hero, prize, mystery)
    warn(world, guardian, hero, mystery, prize)
    surprise_beats(world, hero, guardian, mystery)
    reveal_twist(world, hero, guardian, mystery, prize)

    world.para()
    aid = compromise(world, guardian, hero, mystery, prize)
    if aid:
        accept(world, guardian, hero, mystery, prize, aid)

    world.facts.update(hero=hero, guardian=guardian, prize=prize, mystery=mystery, aid=aid, setting=setting)
    return world


SETTINGS = {
    "hall": Setting(place="the school hall", indoor=True, affords={"seminar"}),
    "library": Setting(place="the library", indoor=True, affords={"seminar"}),
    "community_center": Setting(place="the community center", indoor=True, affords={"seminar"}),
    "garden_tent": Setting(place="the garden tent", indoor=False, affords={"seminar"}),
}

MYSTERIES = {
    "seminar": Mystery(
        id="seminar",
        label="papers",
        verb="attend the seminar",
        clue="a note tucked under a cup",
        surprise="the microphone clicked on by itself",
        twist="the missing item was nearby all along",
        mess="dusty",
        zone={"torso"},
        tags={"seminar", "mystery"},
    )
}

PRIZES = {
    "badge": Prize(label="badge", phrase="a shiny name badge", type="badge", region="torso"),
    "glasses": Prize(label="glasses", phrase="a pair of reading glasses", type="glasses", region="torso", plural=True),
    "notebook": Prize(label="notebook", phrase="a neat notebook with a ribbon", type="notebook", region="torso"),
}

AIDS = [
    Aid(id="cover", label="a clear cover", covers={"torso"}, guards={"dusty"}, prep="put on a clear cover first", tail="slipped on the clear cover"),
    Aid(id="folder", label="a folder sleeve", covers={"torso"}, guards={"dusty"}, prep="slide the papers into a folder sleeve", tail="slid the papers into the folder sleeve"),
]

GIRL_NAMES = ["Mia", "Lina", "Nora", "Ruby", "Sana", "Ivy"]
BOY_NAMES = ["Noah", "Eli", "Theo", "Finn", "Owen", "Leo"]
TRAITS = ["careful", "curious", "brave", "gentle", "clever"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    prize: str
    name: str
    gender: str
    parent: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid in setting.affords:
            myst = _safe_lookup(MYSTERIES, mid)
            for prize_id, prize in PRIZES.items():
                if mystery_at_risk(myst, prize) and select_aid(myst, prize):
                    combos.append((place, mid, prize_id))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    myst = _safe_fact(world, f, "mystery")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a cozy mystery story for a small child about a seminar with "{myst.label}" galore and a gentle surprise twist.',
        f"Tell a short story where {hero.id} goes to {world.setting.place} for a seminar, notices a missing {prize.label}, and learns the surprise truth.",
        f'Write a child-friendly mystery using the word "seminar" and ending with the twist that the missing item was found nearby.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guardian, prize, myst = f["hero"], f["guardian"], f["prize"], f["mystery"]
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa = [
        QAItem(
            question=f"Who was the story about at the seminar?",
            answer=f"It was about {hero.id}, a little {trait} {hero.type}, and {guardian.label} who went with {hero.id} to the seminar.",
        ),
        QAItem(
            question=f"What made the room feel like a mystery?",
            answer=f"The room felt like a mystery because the {prize.label} was missing, and everyone expected {myst.label} galore.",
        ),
        QAItem(
            question=f"What was the surprise twist?",
            answer=f"The surprise twist was that the missing {prize.label} had been tucked inside the stack of handouts all along.",
        ),
    ]
    if f.get("aid"):
        aid = _safe_fact(world, f, "aid")
        qa.append(
            QAItem(
                question=f"How did {aid.label} help at the end?",
                answer=f"The {aid.label} helped keep the {prize.label} safe and clean, so the seminar could begin without making the item dusty.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a seminar?",
            answer="A seminar is a meeting where people come together to listen, learn, and talk about a topic.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small bit of information that helps someone figure something out.",
        ),
        QAItem(
            question="What does surprise mean?",
            answer="A surprise is something unexpected that makes people stop and notice.",
        ),
        QAItem(
            question="What does twist mean in a story?",
            answer="A twist is a new turn in the story that changes what people thought was happening.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(M, P) :- zone(M, R), region(P, R).
aid_fits(M, P) :- mystery(M), prize_at_risk(M, P), aid(A), guards(A, dusty), covers(A, R), region(P, R).
valid(Place, M, P) :- affords(Place, M), prize_at_risk(M, P), aid_fits(M, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        for r in sorted(m.zone):
            lines.append(asp.fact("zone", mid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
    for a in AIDS:
        lines.append(asp.fact("aid", a.id))
        for r in sorted(a.covers):
            lines.append(asp.fact("covers", a.id, r))
        for g in sorted(a.guards):
            lines.append(asp.fact("guards", a.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def explain_rejection(mystery: Mystery, prize: Prize) -> str:
    return f"(No story: the seminar mystery would not truly threaten a {prize.label}, so there is no honest mystery turn.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "mystery", None) and getattr(args, "prize", None):
        m, p = _safe_lookup(MYSTERIES, getattr(args, "mystery", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (mystery_at_risk(m, p) and select_aid(m, p)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(MYSTERIES, params.mystery),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.gender,
        params.parent,
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


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cozy seminar mystery with a surprise twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


CURATED = [
    StoryParams(place="hall", mystery="seminar", prize="badge", name="Mia", gender="girl", parent="mother", trait="curious"),
    StoryParams(place="library", mystery="seminar", prize="glasses", name="Eli", gender="boy", parent="father", trait="careful"),
    StoryParams(place="community_center", mystery="seminar", prize="notebook", name="Nora", gender="girl", parent="mother", trait="clever"),
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
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: seminar at {p.place} (mystery: {p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
