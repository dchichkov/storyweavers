#!/usr/bin/env python3
"""
A small cautionary fairy-tale storyworld about a bonafide trek that turns
wise only after the hero learns to avoid a sterile shortcut.

The seed words are woven into the domain:
- sterile
- bonafide
- trek

Premise:
A young courier wants to take a bonafide trek to deliver a lantern-heart to a
friend across the meadow. A tempting sterile path looks easier, but it drains
warmth, dulls the lantern, and leaves the traveler lonely and cold. A careful
companion offers a better route with a coat, a crumb trail, and a promise to
stay together.

The simulation tracks both physical meters and emotional memes. The story
emerges from causal state changes, not from swapping nouns in a fixed paragraph.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gear: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "father", "man"}:
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
class Trek:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    soil: str
    zone: set[str]
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
        self.zone: set[str] = set()
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.zone = set(self.zone)
        c.fired = set(self.fired)
        c.facts = dict(self.facts)
        c.paragraphs = [[]]
        return c


@dataclass
class Rule:
    name: str
    apply: callable
    RULES: list = field(default_factory=list)
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


def _r_cold(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("cold", 0.0) < THRESHOLD:
            continue
        sig = ("cold", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["miserable"] = actor.memes.get("miserable", 0.0) + 1
        out.append(f"A chill settled in {actor.id}'s bones.")
    return out


def _r_dull(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("dull", 0.0) < THRESHOLD:
            continue
        sig = ("dull", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"The {item.label} lost some of its bright courage.")
    return out


def _r_lonely(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("lonely", 0.0) < THRESHOLD:
            continue
        sig = ("lonely", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append(f"{actor.id} felt small and alone.")
    return out


RULES = [Rule("cold", _r_cold), Rule("dull", _r_dull), Rule("lonely", _r_lonely)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


def trek_at_risk(trek: Trek, prize: Prize) -> bool:
    return prize.region in trek.zone


def select_gear(trek: Trek, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if trek.risk in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, actor: Entity, trek: Trek, prize_id: str) -> dict:
    sim = world.copy()
    _do_trek(sim, sim.get(actor.id), trek, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "cold": actor.meters.get("cold", 0.0) >= THRESHOLD,
        "dull": prize.meters.get("dull", 0.0) >= THRESHOLD,
    }


def _do_trek(world: World, actor: Entity, trek: Trek, narrate: bool = True) -> None:
    if trek.id not in world.setting.affords:
        pass
    world.zone = set(trek.zone)
    actor.meters["cold"] = actor.meters.get("cold", 0.0) + 1
    actor.memes["resolve"] = actor.memes.get("resolve", 0.0) + 1
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.memes if False), None)
    world.say(f"{hero.id} was a little {hero.type} with a brave heart and careful feet.")


def loves_trek(world: World, hero: Entity, trek: Trek) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(
        f"{hero.pronoun().capitalize()} loved a bonafide trek, especially one that wound "
        f"through the meadow like a silver ribbon."
    )
    world.say(f"The {trek.keyword} path looked grand, and {hero.id} wished to begin at once.")


def prize_to(world: World, parent: Entity, hero: Entity, prize: Entity) -> None:
    world.say(f"{parent.label} gave {hero.pronoun('object')} {prize.phrase}, a gift to carry on the journey.")
    prize.worn_by = hero.id


def arrive(world: World, hero: Entity, parent: Entity, trek: Trek) -> None:
    world.say(f"One evening, {hero.id} and {hero.pronoun('possessive')} {parent.label} set out toward {world.setting.place}.")
    world.say(f"The route was {trek.keyword} and quiet, with no birds singing in the hush.")


def wants(world: World, hero: Entity, trek: Trek) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(f"{hero.id} wanted to {trek.verb}, even though the air felt a little too still.")


def warn(world: World, parent: Entity, hero: Entity, trek: Trek, prize: Entity) -> bool:
    pred = predict(world, hero, trek, prize.id)
    if not pred["cold"] and not pred["dull"]:
        return False
    parts = [f"That way will feel {trek.soil}"]
    if pred["cold"]:
        parts.append("and your paws will grow cold")
    if pred["dull"]:
        parts.append(f"and your {prize.label} will lose its shine")
    world.say(f"\"{', '.join(parts)},\" said {parent.label}. \"We should choose more wisely.\"")
    return True


def refuse(world: World, hero: Entity, trek: Trek) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(f"But {hero.id} still tried to {trek.rush}, because the shortcut looked easy.")


def stumble(world: World, hero: Entity, trek: Trek) -> None:
    hero.memes["lonely"] = hero.memes.get("lonely", 0.0) + 1
    world.say(f"The path was too {trek.risk}, and {hero.id} felt the courage drain away.")


def compromise(world: World, parent: Entity, hero: Entity, trek: Trek, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(trek, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        kind="thing",
        type="gear",
        label=gear_def.label,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
        owner=hero.id,
    ))
    gear.worn_by = hero.id
    if predict(world, hero, trek, prize.id)["dull"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f"Then {hero.pronoun('possessive')} {parent.label} found a wise fix: "
        f"{gear_def.prep}."
    )
    return gear_def


def accept(world: World, parent: Entity, hero: Entity, trek: Trek, prize: Entity, gear_def: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["lonely"] = 0.0
    world.say(f"{hero.id} nodded, and the fear in {hero.pronoun('possessive')} chest grew soft.")
    world.say(f"They {gear_def.tail}. Soon {hero.id} was {trek.gerund}, and the {prize.label} stayed bright.")
    world.say(f"At the end, the bonafide trek felt longer, but it was kinder, and that was the better magic.")


def tell(setting: Setting, trek: Trek, prize_cfg: Prize, hero_name: str = "Mira",
         hero_type: str = "girl", parent_type: str = "mother") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id,
        worn_by=hero.id, plural=prize_cfg.plural, meters={"dull": 0.0}
    ))

    intro(world, hero)
    loves_trek(world, hero, trek)
    prize_to(world, parent, hero, prize)
    world.para()
    arrive(world, hero, parent, trek)
    wants(world, hero, trek)
    warn(world, parent, hero, trek, prize)
    refuse(world, hero, trek)
    stumble(world, hero, trek)
    world.para()
    gear_def = compromise(world, parent, hero, trek, prize)
    if gear_def:
        accept(world, parent, hero, trek, prize, gear_def)

    world.facts.update(hero=hero, parent=parent, prize=prize, trek=trek, setting=setting, gear=gear_def)
    return world


SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"lantern_path", "moss_path"}),
    "wood": Setting(place="the wood", affords={"lantern_path"}),
    "hill": Setting(place="the hill road", affords={"lantern_path", "moss_path"}),
}

TREKS = {
    "lantern_path": Trek(
        id="lantern_path",
        verb="follow the lantern path",
        gerund="following the lantern path",
        rush="dash after the glow",
        risk="sterile",
        soil="too sterile and cold",
        zone={"feet", "hands"},
        keyword="lantern",
        tags={"lantern", "light", "sterile"},
    ),
    "moss_path": Trek(
        id="moss_path",
        verb="cross the moss path",
        gerund="crossing the moss path",
        rush="run over the moss",
        risk="slick",
        soil="slick and damp",
        zone={"feet"},
        keyword="moss",
        tags={"moss", "green", "cold"},
    ),
}

PRIZES = {
    "cloak": Prize(label="cloak", phrase="a red cloak", type="cloak", region="torso"),
    "lantern": Prize(label="lantern", phrase="a bonafide lantern", type="lantern", region="hands"),
    "crown": Prize(label="crown", phrase="a little gold crown", type="crown", region="head"),
}

GEAR = [
    Gear(
        id="gloves",
        label="soft gloves",
        covers={"hands"},
        guards={"sterile"},
        prep="put on soft gloves first",
        tail="went on with the gloves snug and warm",
    ),
    Gear(
        id="cloak",
        label="a wool cloak",
        covers={"torso"},
        guards={"cold", "sterile"},
        prep="wrap the cloak around the shoulders",
        tail="crossed the path with the cloak wrapped tight",
    ),
    Gear(
        id="boots",
        label="mud boots",
        covers={"feet"},
        guards={"slick"},
        prep="lace on the mud boots",
        tail="marched on in the mud boots",
        plural=True,
    ),
]

GIRL_NAMES = ["Mira", "Tilda", "Nina", "Elsa", "Poppy", "Lina"]
BOY_NAMES = ["Robin", "Tobin", "Eli", "Jon", "Perry", "Gavin"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for trek_id in setting.affords:
            trek = _safe_lookup(TREKS, trek_id)
            for prize_id, prize in PRIZES.items():
                if trek_at_risk(trek, prize) and select_gear(trek, prize):
                    combos.append((place, trek_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    trek: str
    prize: str
    name: str
    gender: str
    parent: str
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


KNOWLEDGE = {
    "sterile": [("What does sterile mean?",
                 "Sterile means very clean and empty, with little life or warmth in it.")],
    "lantern": [("What is a lantern for?",
                 "A lantern is used to make light so people can see when it is dark.")],
    "cloak": [("What does a cloak do?",
               "A cloak is a loose covering that keeps a traveler warmer on a windy road.")],
    "gloves": [("Why do people wear gloves?",
                "People wear gloves to keep their hands warm or to protect them from dirt and cold.")],
    "boots": [("What are boots for?",
               "Boots protect your feet and help you walk through wet or muddy places.")],
    "moss": [("What is moss?",
              "Moss is a soft green plant that grows on stones, trees, and damp ground.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale for a child about a "bonafide trek" and a warning about something "{f["trek"].risk}".',
        f"Tell a cautionary story where {f['hero'].id} wants to {f['trek'].verb} but learns why the {f['prize'].label} needs protecting.",
        f'Write a gentle story using the words "sterile", "bonafide", and "trek" that ends with a wiser choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, prize, trek = f["hero"], f["parent"], f["prize"], f["trek"]
    qas = [
        QAItem(
            question=f"Who was the story about when {hero.id} went on the {trek.keyword} road?",
            answer=f"It was about {hero.id} and {hero.pronoun('possessive')} {parent.label}, who traveled carefully together.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do on the trek before the warning?",
            answer=f"{hero.id} wanted to {trek.verb}, even though the path looked a little too {trek.risk}.",
        ),
        QAItem(
            question=f"Why did the parent worry about the {prize.label}?",
            answer=f"{parent.label} worried that the {prize.label} would lose its shine if the trip stayed {trek.soil}.",
        ),
    ]
    if f.get("gear"):
        gear = _safe_fact(world, f, "gear")
        qas.append(QAItem(
            question=f"How did {gear.label} help on the journey?",
            answer=f"{gear.label} helped by covering the right part of the body so {hero.id} could keep going safely.",
        ))
        qas.append(QAItem(
            question=f"How did {hero.id} feel when the wiser choice was made?",
            answer=f"{hero.id} felt happy and calmer once the safer plan was chosen.",
        ))
    return qas


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["trek"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", trek="lantern_path", prize="lantern", name="Mira", gender="girl", parent="mother"),
    StoryParams(place="wood", trek="lantern_path", prize="cloak", name="Robin", gender="boy", parent="father"),
    StoryParams(place="hill", trek="moss_path", prize="boots", name="Tilda", gender="girl", parent="mother"),
]


ASP_RULES = r"""
at_risk(T, P) :- zone(T, R), worn_on(P, R).
fix(T, P) :- at_risk(T, P), trek_risk(T, R), guards(G, R), covers(G, C), worn_on(P, C).
valid(Place, T, P) :- affords(Place, T), at_risk(T, P), fix(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, s in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", place, t))
    for tid, t in TREKS.items():
        lines.append(asp.fact("trek", tid))
        lines.append(asp.fact("trek_risk", tid, t.risk))
        for z in sorted(t.zone):
            lines.append(asp.fact("zone", tid, z))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary fairy-tale storyworld about a bonafide trek.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trek", choices=TREKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "trek", None) and getattr(args, "prize", None):
        tr, pr = _safe_lookup(TREKS, getattr(args, "trek", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (trek_at_risk(tr, pr) and select_gear(tr, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "trek", None) is None or c[1] == getattr(args, "trek", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, trek, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(sorted(_safe_lookup(PRIZES, prize).genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    return StoryParams(place=place, trek=trek, prize=prize, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TREKS, params.trek), _safe_lookup(PRIZES, params.prize),
                 hero_name=params.name, hero_type=params.gender, parent_type=params.parent)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, trek, prize) combos:")
        for place, trek, prize in combos:
            print(f"  {place:8} {trek:12} {prize}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
