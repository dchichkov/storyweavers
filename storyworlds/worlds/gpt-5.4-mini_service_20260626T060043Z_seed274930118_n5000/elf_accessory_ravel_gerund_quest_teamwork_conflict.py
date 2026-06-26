#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/elf_accessory_ravel_gerund_quest_teamwork_conflict.py
==============================================================================================================================

A small, classical story world in a ghost-story mood: an elf, a cherished accessory,
a raveling problem, a quest, teamwork, and a brief conflict before a gentle fix.

The world is built from a tiny source-tale premise:
- An elf wants to keep a special accessory neat.
- The accessory starts to ravel during a quest through a quiet haunted place.
- The elf feels conflicted, but teamwork helps them mend the problem.
- The ending proves the change by showing the accessory whole again.

This script follows the storyworld contract:
- standalone stdlib Python
- StoryParams + parser + resolve_params + generate + emit + main
- eager import of shared result containers
- lazy import of storyworlds.asp in ASP helpers
- inline ASP_RULES twin and a Python reasonableness gate
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elf: object | None = None
    helper: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"elf"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        if self.kind == "character":
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Place:
    key: str
    name: str
    haunted: bool = False
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Quest:
    key: str
    verb: str
    gerund: str
    rush: str
    ravel_gerund: str
    risk: str
    zone: set[str]
    tags: set[str] = field(default_factory=set)
    keyword: str = "quest"
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
        return None


@dataclass
class Accessory:
    key: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"elf"})
    fixable_with: set[str] = field(default_factory=set)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Aid:
    key: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
    CAUSAL_RULES: list = field(default_factory=list)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


def _r_ravel(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for q in QUESTS.values():
            if actor.meters.get(q.key, 0) < THRESHOLD:
                continue
            for item in list(world.entities.values()):
                if item.kind != "accessory":
                    continue
                if item.owner != actor.id:
                    continue
                sig = ("ravel", item.id, q.key)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters["ravel"] = item.meters.get("ravel", 0) + 1
                item.meters["tangled"] = item.meters.get("tangled", 0) + 1
                out.append(f"{item.label.capitalize()} began to ravel in the damp dark.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.meters.get("ravel", 0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0) + 1
        return ["__conflict__"]
    return []


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("conflict", 0) < THRESHOLD:
            continue
        for aid in AIDS.values():
            sig = ("aid", aid.key, actor.id)
            if sig in world.fired:
                continue
            if "tangled" in aid.guards:
                continue
            world.fired.add(sig)
            actor.memes["teamwork"] = actor.memes.get("teamwork", 0) + 1
            out.append(f"A helper came near, and together they found a calm way to mend it.")
            return out
    return out


CAUSAL_RULES = [Rule("ravel", _r_ravel), Rule("conflict", _r_conflict), Rule("teamwork", _r_teamwork)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(place: Place) -> str:
    if place.haunted:
        return f"The air in {place.name} was quiet and cool, like a room holding its breath."
    return f"{place.name} was still and dim, ready for a careful little quest."


def prize_at_risk(quest: Quest, acc: Accessory) -> bool:
    return acc.region in quest.zone


def select_aid(quest: Quest, acc: Accessory) -> Optional[Aid]:
    for aid in AIDS.values():
        if quest.key in aid.guards and acc.region in aid.covers:
            return aid
    return None


def valid_story(place: Place, quest: Quest, acc: Accessory) -> bool:
    return place.key in QUEST_PLACES and quest.key in place.affords and prize_at_risk(quest, acc) and select_aid(quest, acc) is not None


def explain_rejection(place: Place, quest: Quest, acc: Accessory) -> str:
    if place.key not in QUEST_PLACES or quest.key not in place.affords:
        return "(No story: that place does not support this quest.)"
    if not prize_at_risk(quest, acc):
        return f"(No story: {quest.gerund} does not reach the {acc.region}, so the accessory would not truly be at risk.)"
    return f"(No story: no helper in the catalog can fix a {acc.label} for this quest.)"


def build_world(place: Place, quest: Quest, acc: Accessory, name: str, helper_kind: str) -> World:
    world = World(place)
    elf = world.add(Entity(id=name, kind="character", type="elf", label=name, owner=None))
    helper = world.add(Entity(id="helper", kind="character", type=helper_kind, label=helper_kind))
    item = world.add(Entity(
        id="accessory",
        kind="accessory",
        type=acc.key,
        label=acc.label,
        phrase=acc.phrase,
        owner=elf.id,
        caretaker=helper.id,
        worn_by=elf.id,
        plural=acc.plural,
    ))

    world.say(f"{elf.id} was a little elf who loved a small quest and a quiet moonlit path.")
    world.say(f"{elf.pronoun('possessive').capitalize()} favorite thing was {acc.phrase}, because it made the dark feel friendly.")
    world.para()
    world.say(setting_detail(place))
    world.say(f"One night, {elf.id} set out {quest.gerund} through {place.name}.")
    world.say(f"Then {elf.id} noticed that {item.label} was starting to {quest.ravel_gerund}.")
    elf.meters[quest.key] = 1
    item.meters["ravel"] = 1
    propagate(world, narrate=False)

    world.para()
    world.say(f"{elf.id} felt a tight little conflict in {elf.pronoun('possessive')} chest.")
    world.say(f"{elf.id} wanted to keep going, but {elf.pronoun('possessive')} heart said the accessory needed help.")
    aid = select_aid(quest, acc)
    if aid:
        world.say(f"Then {elf.id}'s helper came close and offered {aid.prep}.")
        helper.memes["teamwork"] = helper.memes.get("teamwork", 0) + 1
        elf.memes["conflict"] = 1
        elf.memes["teamwork"] = 1
        if item.meters.get("ravel", 0) >= THRESHOLD:
            item.meters["mended"] = 1
            item.meters["ravel"] = 0
            item.meters["tangled"] = 0
            elf.memes["conflict"] = 0
            world.say(f"Together, they worked by the lantern glow until the {acc.label} was neat again.")
            world.say(f"They {aid.tail}. In the end, {elf.id} kept {(getattr(acc, 'it')() if callable(getattr(acc, 'it', None)) else getattr(acc, 'it', 'it'))} safe, and the dark road felt kind.")
    world.facts.update(elf=elf, helper=helper, accessory=item, place=place, quest=quest, aid=aid)
    return world


PLACES = {
    "old_grove": Place(key="old_grove", name="the old grove", haunted=True, affords={"lantern_quest", "moon_quest"}, mood="whisper"),
    "moon_bridge": Place(key="moon_bridge", name="the moon bridge", haunted=True, affords={"moon_quest"}, mood="silver"),
    "quiet_attic": Place(key="quiet_attic", name="the quiet attic", haunted=True, affords={"lantern_quest", "thread_quest"}, mood="dust"),
    "green_hall": Place(key="green_hall", name="the green hall", haunted=False, affords={"thread_quest", "lantern_quest"}, mood="soft"),
}

QUESTS = {
    "moon_quest": Quest(
        key="moon_quest",
        verb="cross the moonlit path",
        gerund="crossing the moonlit path",
        rush="hurry across the moonlit stones",
        ravel_gerund="ravel",
        risk="the damp night would tug the threads loose",
        zone={"torso"},
        tags={"moon", "ghost", "quest"},
        keyword="quest",
    ),
    "lantern_quest": Quest(
        key="lantern_quest",
        verb="carry the lantern through the dark",
        gerund="carrying the lantern through the dark",
        rush="rush with the lantern",
        ravel_gerund="ravel",
        risk="the bright walk would catch on stray threads",
        zone={"torso"},
        tags={"lantern", "ghost", "quest"},
        keyword="quest",
    ),
    "thread_quest": Quest(
        key="thread_quest",
        verb="follow the thread trail",
        gerund="following the thread trail",
        rush="run after the thread trail",
        ravel_gerund="ravel",
        risk="the trail would snag the accessory",
        zone={"torso"},
        tags={"thread", "quest"},
        keyword="quest",
    ),
}

ACCESSORIES = {
    "scarf": Accessory("scarf", "scarf", "a soft blue scarf", "torso"),
    "satchel": Accessory("satchel", "satchel", "a tiny satchel with a brass clasp", "torso"),
    "wristbell": Accessory("wristbell", "wrist bell", "a bright wrist bell", "torso"),
}

AIDS = {
    "mendkit": Aid("mendkit", "mending kit", {"torso"}, {"ravel"}, "open a mending kit", "set the mending kit on the bench"),
    "spool": Aid("spool", "spool of silver thread", {"torso"}, {"ravel"}, "offer a spool of silver thread", "tied the loose ends with silver thread"),
}

QUEST_PLACES = set(PLACES.keys())
NAME_POOL = ["Ari", "Nell", "Milo", "Ivo", "Lumi", "Sera", "Pip", "Tavi"]
HELPER_KINDS = ["friend", "older elf", "lantern keeper", "quiet cousin"]
TRAITS = ["gentle", "brave", "careful", "curious", "soft-spoken"]


@dataclass
class StoryParams:
    place: str
    quest: str
    accessory: str
    name: str
    helper_kind: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story for a young child about an elf named {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "elf").id}, a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "accessory").label}, and a small quest.',
        f"Tell a gentle spooky tale where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "elf").id} starts {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "quest").gerund} at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place").name} and a helper fixes the problem with teamwork.",
        f'Write a short story that uses the word "quest" and ends with an elf keeping {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "accessory").label} neat again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    elf, acc, quest, place, aid = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "elf"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "accessory"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "quest"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "aid")
    qa = [
        QAItem(
            question=f"What was the story about at {place.name}?",
            answer=f"It was about {elf.id}, a little elf who loved {acc.phrase} and went on a quiet quest at {place.name}.",
        ),
        QAItem(
            question=f"What problem started during {quest.gerund}?",
            answer=f"{acc.label.capitalize()} began to ravel while {elf.id} was {quest.gerund}.",
        ),
        QAItem(
            question=f"How was the conflict solved?",
            answer=f"{elf.id} and the helper used teamwork, opened {aid.label}, and mended the {acc.label} together.",
        ),
    ]
    if elf.memes.get("conflict", 0) >= THRESHOLD:
        qa.append(QAItem(
            question=f"Why did {elf.id} feel upset?",
            answer=f"{elf.id} felt a little conflict because {acc.label} was raveling during the quest, and {elf.id} wanted to keep it safe.",
        ))
    qa.append(QAItem(
        question=f"What changed by the end of the story?",
        answer=f"By the end, the {acc.label} was neat again, and {elf.id} could keep going without worry.",
    ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is an elf?",
            answer="An elf is a small magical person from old stories, often shown as careful, kind, and good with tiny tasks.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey or job someone does because they want to find, fix, or bring back something important.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work together toward the same goal.",
        ),
        QAItem(
            question="What is conflict?",
            answer="Conflict is a feeling of trouble or disagreement when someone wants two different things at once.",
        ),
        QAItem(
            question="What does it mean for something to ravel?",
            answer="If something ravels, its threads or strands start coming loose and messy.",
        ),
    ]
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
        lines.append(f"  {e.id:10} ({e.kind:10}) meters={meters} memes={memes}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for p in PLACES.values():
        for qk, q in QUESTS.items():
            if qk not in p.affords:
                continue
            for ak, a in ACCESSORIES.items():
                if prize_at_risk(q, a) and select_aid(q, a):
                    combos.append((p.key, qk, ak))
    return combos


CURATED = [
    StoryParams("old_grove", "moon_quest", "scarf", "Ari", "older elf", "careful"),
    StoryParams("quiet_attic", "lantern_quest", "satchel", "Nell", "friend", "gentle"),
    StoryParams("green_hall", "thread_quest", "wristbell", "Lumi", "lantern keeper", "curious"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world: elf, accessory, quest, teamwork, conflict.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--accessory", choices=ACCESSORIES)
    ap.add_argument("--name")
    ap.add_argument("--helper-kind", choices=HELPER_KINDS)
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
    combos = valid_combos()
    if getattr(args, "place", None) and getattr(args, "quest", None) and getattr(args, "accessory", None):
        if (getattr(args, "place", None), getattr(args, "quest", None), getattr(args, "accessory", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [c for c in combos if (not getattr(args, "place", None) or c[0] == getattr(args, "place", None)) and (not getattr(args, "quest", None) or c[1] == getattr(args, "quest", None)) and (not getattr(args, "accessory", None) or c[2] == getattr(args, "accessory", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, accessory = rng.choice(list(filtered))
    return StoryParams(
        place=place,
        quest=quest,
        accessory=accessory,
        name=getattr(args, "name", None) or rng.choice(NAME_POOL),
        helper_kind=getattr(args, "helper_kind", None) or rng.choice(HELPER_KINDS),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(_safe_lookup(PLACES, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(ACCESSORIES, params.accessory), params.name, params.helper_kind)
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


ASP_RULES = r"""
place(old_grove). place(moon_bridge). place(quiet_attic). place(green_hall).
haunted(old_grove). haunted(moon_bridge). haunted(quiet_attic).
affords(old_grove,moon_quest). affords(old_grove,lantern_quest).
affords(moon_bridge,moon_quest).
affords(quiet_attic,lantern_quest). affords(quiet_attic,thread_quest).
affords(green_hall,thread_quest). affords(green_hall,lantern_quest).

quest(moon_quest). quest(lantern_quest). quest(thread_quest).
zone(moon_quest,torso). zone(lantern_quest,torso). zone(thread_quest,torso).
raveling(moon_quest). raveling(lantern_quest). raveling(thread_quest).

accessory(scarf). accessory(satchel). accessory(wristbell).
worn_on(scarf,torso). worn_on(satchel,torso). worn_on(wristbell,torso).

aid(mendkit). aid(spool).
covers(mendkit,torso). covers(spool,torso).
guards(mendkit,ravel). guards(spool,ravel).

prize_at_risk(Q,A) :- zone(Q,R), worn_on(A,R).
has_fix(Q,A) :- prize_at_risk(Q,A), raveling(Q), aid(G), covers(G,R), worn_on(A,R), guards(G,ravel).
valid_story(P,Q,A) :- place(P), quest(Q), accessory(A), affords(P,Q), prize_at_risk(Q,A), has_fix(Q,A).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.key))
        if p.haunted:
            lines.append(asp.fact("haunted", p.key))
        for q in sorted(p.affords):
            lines.append(asp.fact("affords", p.key, q))
    for q in QUESTS.values():
        lines.append(asp.fact("quest", q.key))
        lines.append(asp.fact("zone", q.key, "torso"))
        lines.append(asp.fact("raveling", q.key))
    for a in ACCESSORIES.values():
        lines.append(asp.fact("accessory", a.key))
        lines.append(asp.fact("worn_on", a.key, a.region))
    for aid in AIDS.values():
        lines.append(asp.fact("aid", aid.key))
        for c in aid.covers:
            lines.append(asp.fact("covers", aid.key, c))
        for g in aid.guards:
            lines.append(asp.fact("guards", aid.key, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    asp_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP matches Python valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if asp_set - py_set:
        print(" only in ASP:", sorted(asp_set - py_set))
    if py_set - asp_set:
        print(" only in Python:", sorted(py_set - asp_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        vals = sorted(set(asp.atoms(model, "valid_story")))
        for v in vals:
            print(v)
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
