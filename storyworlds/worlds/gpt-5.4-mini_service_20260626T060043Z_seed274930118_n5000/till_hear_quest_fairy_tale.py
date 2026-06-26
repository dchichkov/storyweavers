#!/usr/bin/env python3
"""
storyworlds/worlds/till_hear_quest_fairy_tale.py
=================================================

A small fairy-tale story world about a child who hears a quest, wants to dash
off at once, and learns to wait till the safer way is ready.

Seed tale shape:
- A young hero hears a quest from a kindly grown-up.
- The hero wants to rush ahead before hearing the whole warning.
- The grown-up explains the risk and offers a fitting magical fix.
- The hero waits till the fix is ready, then sets out happily.

This world keeps the prose child-facing and concrete, with a state-driven turn:
the quest is real, the risk is physical, and the ending proves what changed.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guide: object | None = None
    hero: object | None = None
    item: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"wet": 0.0, "muddy": 0.0, "dirty": 0.0, "sparkle": 0.0}
        if not self.memes:
            self.memes = {
                "joy": 0.0,
                "curiosity": 0.0,
                "patience": 0.0,
                "worry": 0.0,
                "defiance": 0.0,
                "conflict": 0.0,
                "love": 0.0,
                "heard": 0.0,
            }

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "witch", "princess", "woman"}
        male = {"boy", "father", "king", "wizard", "prince", "man"}
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
    place: str
    indoor: bool = False
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
class Quest:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str
    keyword: str = "quest"
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
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


SETTINGS = {
    "castle": Setting("the castle hall", True, {"quest"}),
    "forest": Setting("the moonlit forest", False, {"quest"}),
    "meadow": Setting("the bright meadow", False, {"quest"}),
    "river": Setting("the silver riverbank", False, {"quest"}),
}

QUESTS = {
    "brook": Quest(
        id="brook",
        verb="cross the brook",
        gerund="crossing the brook",
        rush="run straight to the brook",
        mess="wet",
        soil="soaked and muddy",
        zone={"feet", "legs"},
        weather="misty",
        keyword="quest",
        tags={"water", "quest", "brook"},
    ),
    "briar": Quest(
        id="briar",
        verb="sneak through the briars",
        gerund="slipping through briars",
        rush="dash into the briars",
        mess="muddy",
        soil="muddy and scratched",
        zone={"legs", "torso"},
        weather="misty",
        keyword="quest",
        tags={"briar", "quest"},
    ),
    "dew": Quest(
        id="dew",
        verb="gather moondew",
        gerund="gathering moondew",
        rush="hurry into the meadow",
        mess="wet",
        soil="damp and sparkly",
        zone={"feet"},
        weather="misty",
        keyword="quest",
        tags={"dew", "quest"},
    ),
}

PRIZES = {
    "shoes": Prize("shoes", "little golden shoes", "shoes", "feet", True),
    "cloak": Prize("cloak", "a silver cloak", "cloak", "torso"),
    "skirt": Prize("skirt", "a bright fair skirt", "skirt", "legs", True, {"girl"}),
    "boots": Prize("boots", "blue walking boots", "boots", "feet", True),
}

GEAR = [
    Gear("boots", "rain boots", {"feet"}, {"wet", "muddy"}, "put on rain boots first", "walked back for the rain boots", True),
    Gear("cloak", "a waterproof cloak", {"torso"}, {"wet"}, "tie on a waterproof cloak first", "went to fetch the waterproof cloak"),
    Gear("hushcloak", "a sturdy travel cloak", {"torso", "legs"}, {"muddy", "wet"}, "wear a sturdy travel cloak first", "came back for the sturdy travel cloak"),
]

NAMES = {
    "girl": ["Lina", "Mira", "Tess", "Nora", "Elin"],
    "boy": ["Owen", "Finn", "Theo", "Milo", "Robin"],
}
TRAITS = ["curious", "brave", "gentle", "cheerful", "stubborn"]


def prize_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.zone


def select_gear(quest: Quest, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if quest.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            q = _safe_lookup(QUESTS, qid)
            for pid, pr in PRIZES.items():
                if prize_at_risk(q, pr) and select_gear(q, pr):
                    out.append((place, qid, pid))
    return out


@dataclass
class StoryParams:
    place: str
    quest: str
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


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_soak(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for mess in ("wet", "muddy"):
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone or world.covered(actor, item.region):
                    continue
                sig = ("soak", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess} and dirty.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("defiance", 0.0) < THRESHOLD or actor.memes.get("heard", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] = actor.memes.get("conflict", 0.0) + 1
        return ["__conflict__"]
    return []


RULES = [Rule("soak", _r_soak), Rule("conflict", _r_conflict)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, quest: Quest, prize_id: str) -> dict:
    sim = world_copy(world)
    do_quest(sim, sim.get(actor.id), quest, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"soiled": bool(prize and prize.meters.get("dirty", 0.0) >= THRESHOLD)}


def world_copy(world: World) -> World:
    import copy

    clone = World(world.setting)
    clone.entities = copy.deepcopy(world.entities)
    clone.fired = set(world.fired)
    clone.zone = set(world.zone)
    clone.weather = world.weather
    clone.paragraphs = [[]]
    return clone


def do_quest(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> None:
    world.zone = set(quest.zone)
    actor.meters[quest.mess] = actor.meters.get(quest.mess, 0.0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    world.say(f"{hero.id} was a little {trait} {hero.type} who loved fairy tales and hidden paths.")


def hear_quest(world: World, hero: Entity, guide: Entity, quest: Quest) -> None:
    hero.memes["heard"] = hero.memes.get("heard", 0.0) + 1
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(f"One evening, {hero.id} heard a quest from {guide.label_word if hasattr(guide,'label_word') else guide.label}.")
    world.say(f'"There is a {quest.keyword} for you," said {guide.label}. "You must {quest.verb} till the moon is high."')


def setting_line(world: World, quest: Quest) -> None:
    if world.setting.indoor:
        world.say("The hall was warm, and the candles made the shadows dance.")
    elif quest.weather == "misty":
        world.say(f"The air at {world.setting.place} was silver and misty, as if the world were holding its breath.")
    else:
        world.say(f"{world.setting.place.capitalize()} looked bright and ready for an adventure.")


def want_now(world: World, hero: Entity, quest: Quest) -> None:
    hero.memes["defiance"] = hero.memes.get("defiance", 0.0) + 1
    world.say(f"{hero.id} wanted to {quest.rush} at once.")


def warn(world: World, guide: Entity, hero: Entity, quest: Quest, prize: Entity) -> bool:
    pred = predict_mess(world, hero, quest, prize.id)
    if not pred["soiled"]:
        return False
    world.say(f'"If you go now, your {prize.label} will get {quest.soil}," said {guide.label}.')
    world.say(f'"Please hear the whole quest till the end," {guide.label} told {hero.id}.')
    return True


def hesitate(world: World, hero: Entity, quest: Quest) -> None:
    world.say(f"{hero.id} stopped, but the wish to hurry still tugged at {hero.pronoun('possessive')} feet.")


def wait_till(world: World, hero: Entity, guide: Entity, quest: Quest, prize: Entity) -> Optional[Gear]:
    gear = select_gear(quest, prize)
    if gear is None:
        return None
    item = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=guide.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
    ))
    item.worn_by = hero.id
    if predict_mess(world, hero, quest, prize.id)["soiled"]:
        item.worn_by = None
        del world.entities[item.id]
        return None
    world.say(f'So {guide.label} smiled and said, "How about we {gear.prep} and then go together?"')
    return item


def accept(world: World, hero: Entity, guide: Entity, quest: Quest, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    hero.memes["conflict"] = 0.0
    world.say(f"{hero.id}'s face lit up, and {hero.id} hugged {hero.pronoun('possessive')} {guide.label}.")
    world.say(f'"Yes, let us wait till then!" {hero.id} said.')
    world.say(
        f"At last they {gear.tail}, and {hero.id} went {quest.gerund}, "
        f"while {prize.label} stayed clean and bright."
    )


def tell(setting: Setting, quest: Quest, prize_cfg: Prize, hero_name: str, hero_type: str, hero_traits: list[str], parent_type: str) -> World:
    world = World(setting)
    world.weather = quest.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little"] + hero_traits))
    guide = world.add(Entity(id="Guide", kind="character", type=parent_type, label="the queen" if parent_type == "queen" else "the guide"))
    if guide.type in {"queen", "king"}:
        guide.label = "the queen" if guide.type == "queen" else "the king"
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=guide.id, region=prize_cfg.region, plural=prize_cfg.plural))

    world.say(f"{hero.id} was a little {next((t for t in hero.traits if t != 'little'), hero.type)} {hero.type} who loved fairy tales and quests.")
    setting_line(world, quest)
    hear_quest(world, hero, guide, quest)
    world.say(f"{hero.id} wore {prize.phrase} and thought it looked like treasure.")
    world.para()
    want_now(world, hero, quest)
    warn(world, guide, hero, quest, prize)
    hesitate(world, hero, quest)
    world.para()
    gear = wait_till(world, hero, guide, quest, prize)
    if gear:
        accept(world, hero, guide, quest, prize, gear)

    world.facts.update(hero=hero, guide=guide, prize=prize, quest=quest, setting=setting, gear=gear, resolved=gear is not None)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, guide, quest, prize = f["hero"], f["guide"], f["quest"], f["prize"]
    return [
        f'Write a short fairy tale for a child about a {hero.type} named {hero.id} who hears a {quest.keyword} and must wait till the safe way is ready.',
        f'Tell a gentle story where {hero.id} wants to {quest.verb}, but {guide.label} warns about {prize.phrase}.',
        f'Write a simple fairy tale that includes the words "{quest.keyword}" and "till" and ends with a happy quest.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, guide, quest, prize = f["hero"], f["guide"], f["quest"], f["prize"]
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa = [
        QAItem(
            question=f"Who heard the quest in the story?",
            answer=f"{hero.id} heard the quest from {guide.label}, and {hero.id} was a little {trait} {hero.type}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do right away?",
            answer=f"{hero.id} wanted to {quest.rush}, but {guide.label} asked {hero.id} to wait till the safer way was ready.",
        ),
        QAItem(
            question=f"Why did {guide.label} worry about the {prize.label}?",
            answer=f"{guide.label} worried because if {hero.id} rushed into {quest.verb}, the {prize.label} would get {quest.soil}.",
        ),
    ]
    if f.get("gear") is not None:
        gear = _safe_fact(world, f, "gear")
        qa.append(QAItem(
            question=f"How did the {gear.label} help?",
            answer=f"The {gear.label} covered the right part of {hero.id}'s body, so {hero.id} could {quest.verb} without ruining the {prize.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to wait till something happens?",
            answer="To wait till something happens means to stay ready and not do the thing yet, until the right time comes.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a special journey or task in a story, often with a goal to find, fetch, or help.",
        ),
        QAItem(
            question="What does hearing mean?",
            answer="Hearing means noticing a sound with your ears, like a voice, a bell, or a song.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(quest: Quest, prize: Prize) -> str:
    if not prize_at_risk(quest, prize):
        return f"(No story: {quest.gerund} does not really threaten the {prize.label}.)"
    return f"(No story: nothing in the gear set safely protects the {prize.label} from {quest.verb}.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("mess_of", qid, q.mess))
        for r in sorted(q.zone):
            lines.append(asp.fact("splashes", qid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(Q, P) :- splashes(Q, R), worn_on(P, R).
protects(G, Q, P) :- gear(G), prize_at_risk(Q, P), mess_of(Q, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(Q, P) :- protects(_, Q, P).
valid(Place, Q, P) :- affords(Place, Q), prize_at_risk(Q, P), has_fix(Q, P).
"""


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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams("castle", "brook", "shoes", "Lina", "girl", "queen", "curious"),
    StoryParams("forest", "briar", "cloak", "Owen", "boy", "queen", "brave"),
    StoryParams("meadow", "dew", "skirt", "Mira", "girl", "queen", "cheerful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale story world about hearing a quest and waiting till the safe way is ready.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["queen", "king"])
    ap.add_argument("--name")
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
    if getattr(args, "quest", None) and getattr(args, "prize", None):
        q, p = _safe_lookup(QUESTS, getattr(args, "quest", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(q, p) and select_gear(q, p)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest_id, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.genders))
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["queen", "king"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest_id, prize=prize_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(PRIZES, params.prize), params.name, params.gender, [params.trait, "stubborn"], params.parent)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible story combos:")
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
            header = f"### {p.name}: {p.quest} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
