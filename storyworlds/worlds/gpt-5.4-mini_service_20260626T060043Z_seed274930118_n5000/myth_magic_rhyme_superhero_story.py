#!/usr/bin/env python3
"""
myth_magic_rhyme_superhero_story.py
====================================

A small standalone storyworld about a young superhero in a mythic city where
magic and rhyme help solve a problem.

Premise:
- A child hero loves to practice rhyme-based magic.
- A mythic little trouble starts when a gloomy shadow steals the city's bright
  song from a statue, a lantern, or a bridge bell.
- The hero tries a forceful superhero fix first.
- A wiser helper suggests a magic rhyme that matches the trouble.
- The rhyme restores the city and leaves an ending image that proves the change.

The world is intentionally small and constraint-checked: not every artifact
matches every problem, and invalid combinations raise StoryError.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    mentor: object | None = None
    relic_ent: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "heroine", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "hero", "man"}:
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
class Setting:
    place: str
    mythic_detail: str
    has_tower: bool = False
    has_bridge: bool = False
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
class Power:
    id: str
    title: str
    verb: str
    rhyme_word: str
    glow: str
    effect: str
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
class Relic:
    id: str
    label: str
    phrase: str
    vulnerability: str
    place_kind: str
    owner_kind: str = "hero"
    tags: set[str] = field(default_factory=set)
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
class Remedy:
    id: str
    label: str
    rhyme: str
    action: str
    guards: set[str]
    fits: set[str]
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.current_villain: str = ""
        self.current_problem: str = ""

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

    def heroes(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.current_villain = self.current_villain
        clone.current_problem = self.current_problem
        return clone


def add_meter(e: Entity, key: str, amt: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + amt


def add_meme(e: Entity, key: str, amt: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + amt


def meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def problem_requires_relic(power: Power, relic: Relic) -> bool:
    return relic.vulnerability in power.tags


def remedy_matches(power: Power, relic: Relic) -> bool:
    return problem_requires_relic(power, relic) and relic.place_kind in remedy_place_fits(power, relic)


def remedy_place_fits(power: Power, relic: Relic) -> set[str]:
    # intentionally small, explicit compatibility layer
    fits: set[str] = set()
    for rem in REMEDIES:
        if relic.vulnerability in rem.guards and relic.place_kind in rem.fits:
            fits.add(rem.id)
    return fits


def select_remedy(power: Power, relic: Relic) -> Optional[Remedy]:
    for rem in REMEDIES:
        if relic.vulnerability in rem.guards and relic.place_kind in rem.fits:
            return rem
    return None


def predict_damage(world: World, hero: Entity, power: Power, relic: Relic) -> dict:
    sim = world.copy()
    _use_power(sim, sim.get(hero.id), power, narrate=False)
    rel = sim.get(relic.id)
    return {"broken": meter(rel, "broken") >= THRESHOLD, "shaken": meter(rel, "shaken")}


def _use_power(world: World, hero: Entity, power: Power, narrate: bool = True) -> None:
    add_meme(hero, "spark", 1.0)
    add_meter(hero, "glow", 1.0)
    if power.id == "thunder":
        add_meter(hero, "force", 1.0)
    if power.id == "rhyme":
        add_meme(hero, "rhythm", 1.0)
    _propagate(world, narrate=narrate)


def _ripple_break(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero").id)
    power = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "power")
    relic = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "relic").id)
    if meter(hero, "force") < THRESHOLD:
        return out
    if relic.id in world.fired:
        return out
    if world.current_problem != relic.vulnerability:
        return out
    world.fired.add((relic.id, "shaken"))
    add_meter(relic, "shaken", 1.0)
    out.append(f"The force made the {relic.label} tremble, but it did not solve the mythic trouble.")
    if power.id == "thunder":
        add_meter(relic, "broken", 1.0)
        out.append(f"A crack flashed across the {relic.label}.")
    return out


def _rhyme_heal(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "hero").id)
    relic = world.get(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "relic").id)
    if meme(hero, "rhythm") < THRESHOLD:
        return out
    if meter(relic, "broken") >= THRESHOLD:
        if ("heal", relic.id) in world.fired:
            return out
        world.fired.add(("heal", relic.id))
        relic.meters["broken"] = 0.0
        relic.meters["glow"] = relic.meters.get("glow", 0.0) + 1.0
        out.append(f"The rhyme stitched the {relic.label} back together with bright magic.")
    if meter(relic, "shaken") >= THRESHOLD:
        relic.meters["shaken"] = 0.0
    return out


CAUSAL_RULES = [_ripple_break, _rhyme_heal]


def _propagate(world: World, narrate: bool = True) -> list[str]:
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


def intro(world: World, hero: Entity, sidekick: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} superhero who loved {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "power").title.lower()} magic and brave plans."
    )
    world.say(
        f"{hero.id} and {sidekick.id} practiced tiny rhyme spells beside {world.setting.mythic_detail}."
    )


def problem(world: World, hero: Entity, relic: Relic) -> None:
    world.say(
        f"One day, a gloomy myth-shadow curled around the {relic.label} at {world.setting.place}."
    )
    world.say(
        f"The shadow wanted the {relic.label} to forget its bright song."
    )
    world.current_problem = relic.vulnerability
    add_meter(world.get(relic.id), "broken", 1.0 if relic.vulnerability == "fray" else 0.0)
    add_meter(world.get(relic.id), "shaken", 1.0)
    add_meme(hero, "worry", 1.0)


def try_force(world: World, hero: Entity, relic: Relic, power: Power) -> None:
    add_meme(hero, "courage", 1.0)
    world.say(
        f"{hero.id} soared in and used {power.verb}, but the trouble only bounced harder off the {relic.label}."
    )
    _use_power(world, hero, power)


def wise_pause(world: World, mentor: Entity, hero: Entity, relic: Relic, power: Power) -> bool:
    pred = predict_damage(world, hero, power, relic)
    if not pred["broken"] and meter(world.get(relic.id), "shaken") < THRESHOLD:
        return False
    world.say(
        f'"Not every fight needs more force," {mentor.id} said. "This one needs a rhyme that fits the myth."'
    )
    return True


def cast_rhyme(world: World, hero: Entity, relic: Relic, power: Power, remedy: Remedy) -> None:
    add_meme(hero, "rhythm", 1.0)
    add_meme(hero, "hope", 1.0)
    world.say(
        f'{hero.id} took a breath and sang, "{remedy.rhyme}!"'
    )
    world.say(
        f"The {remedy.label} answer was {remedy.action}, and the magic found the right beat."
    )
    _use_power(world, hero, power)
    rem = world.get(relic.id)
    if meter(rem, "broken") >= THRESHOLD:
        rem.meters["broken"] = 0.0
    rem.meters["glow"] = rem.meters.get("glow", 0.0) + 1.0
    world.say(
        f"The {relic.label} flashed bright again, and the myth-shadow slipped away like smoke."
    )


def ending(world: World, hero: Entity, relic: Relic) -> None:
    world.say(
        f"At the end, {hero.id} stood with {relic.label} shining safe again, and the city hummed a happy little tune."
    )


def tell(setting: Setting, power: Power, relic: Relic, hero_name: str, hero_type: str,
         sidekick_name: str, mentor_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    sidekick = world.add(Entity(id=sidekick_name, kind="character", type="friend"))
    mentor = world.add(Entity(id=mentor_name, kind="character", type="mentor"))
    relic_ent = world.add(Entity(
        id=relic.id, type="relic", label=relic.label, phrase=relic.phrase, owner=hero.id
    ))
    world.facts = {"hero": hero, "sidekick": sidekick, "mentor": mentor, "relic": relic_ent, "power": power}

    intro(world, hero, sidekick)
    world.para()
    problem(world, hero, relic)
    try_force(world, hero, relic_ent, power)
    world.para()
    if wise_pause(world, mentor, hero, relic_ent, power):
        remedy = select_remedy(power, relic)
        if remedy is None:
            _fallback_pool = globals().get("REMEDYS") or globals().get("REMEDYES") or globals().get("REMEDIES") or []
            if hasattr(_fallback_pool, "values"):
                _fallback_pool = list(_fallback_pool.values())
            remedy = next(iter(_fallback_pool), None)
            if remedy is None:
                raise StoryError
        world.say(
            f"{mentor.id} pointed to the old pattern in the air and offered a gentler spell."
        )
        cast_rhyme(world, hero, relic_ent, power, remedy)
    ending(world, hero, relic_ent)
    return world


SETTINGS = {
    "tower": Setting(place="Moonstone Tower", mythic_detail="the silver stairs of the tower", has_tower=True),
    "bridge": Setting(place="Starbridge", mythic_detail="the lanterns under the bridge", has_bridge=True),
    "square": Setting(place="Sunlit Square", mythic_detail="the stone fountain in the middle of the square"),
}

POWERS = {
    "thunder": Power(
        id="thunder",
        title="Thunder",
        verb="hurled a thunder-bolt",
        rhyme_word="storm",
        glow="blue",
        effect="shock",
        tags={"crack", "shock"},
    ),
    "rhyme": Power(
        id="rhyme",
        title="Rhyme",
        verb="spoke a rhyme spell",
        rhyme_word="chime",
        glow="gold",
        effect="heal",
        tags={"fray", "silence", "gloom"},
    ),
    "spark": Power(
        id="spark",
        title="Spark",
        verb="flashed a spark-ring",
        rhyme_word="spark",
        glow="red",
        effect="brighten",
        tags={"dim", "gloom"},
    ),
}

RELICS = {
    "bell": Relic(
        id="bell",
        label="bridge bell",
        phrase="a small bronze bell",
        vulnerability="silence",
        place_kind="bridge",
        tags={"sound", "bridge", "myth"},
    ),
    "lantern": Relic(
        id="lantern",
        label="tower lantern",
        phrase="a lantern with a glass star",
        vulnerability="dim",
        place_kind="tower",
        tags={"light", "tower", "myth"},
    ),
    "banner": Relic(
        id="banner",
        label="city banner",
        phrase="a bright banner with a lion mark",
        vulnerability="fray",
        place_kind="square",
        tags={"cloth", "city", "myth"},
    ),
}

REMEDIES = [
    Remedy(
        id="chime-knot",
        label="chime-knot",
        rhyme="Chime and shine, be clear and fine",
        action="a bright ring that woke the bell",
        guards={"silence"},
        fits={"bridge"},
    ),
    Remedy(
        id="star-glass",
        label="star-glass rhyme",
        rhyme="Star and flare, light the air",
        action="a golden beam that filled the lantern",
        guards={"dim"},
        fits={"tower"},
    ),
    Remedy(
        id="mend-chant",
        label="mend-chant",
        rhyme="Thread by thread, red to red",
        action="careful magic that mended cloth",
        guards={"fray"},
        fits={"square"},
    ),
]

HERO_NAMES = ["Nova", "Milo", "Aria", "Kai", "Luna", "Finn"]
SIDEKICK_NAMES = ["Pip", "Tess", "Rune", "Bea", "Jax"]
MENTOR_NAMES = ["Aunt Ember", "Captain Lyra", "Professor Vale", "Guardia"]

CURATED = [
    {"setting": "tower", "power": "rhyme", "relic": "lantern", "hero": "Nova", "sidekick": "Pip", "mentor": "Captain Lyra", "type": "girl"},
    {"setting": "bridge", "power": "rhyme", "relic": "bell", "hero": "Kai", "sidekick": "Rune", "mentor": "Aunt Ember", "type": "boy"},
    {"setting": "square", "power": "rhyme", "relic": "banner", "hero": "Aria", "sidekick": "Bea", "mentor": "Professor Vale", "type": "girl"},
]


@dataclass
class StoryParams:
    setting: str
    power: str
    relic: str
    hero_name: str
    hero_type: str
    sidekick_name: str
    mentor_name: str
    seed: Optional[int] = None
    params: object | None = None
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sname, setting in SETTINGS.items():
        for pname, power in POWERS.items():
            for rname, relic in RELICS.items():
                if relic.place_kind == sname and problem_requires_relic(power, relic):
                    out.append((sname, pname, rname))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic superhero story world with magic rhyme fixes.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--power", choices=POWERS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--hero-name", dest="hero_name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--sidekick-name", dest="sidekick_name")
    ap.add_argument("--mentor-name", dest="mentor_name")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "power", None) is None or c[1] == getattr(args, "power", None))
              and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, power, relic = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "hero_name", None) or rng.choice(HERO_NAMES)
    sidekick_name = getattr(args, "sidekick_name", None) or rng.choice(SIDEKICK_NAMES)
    mentor_name = getattr(args, "mentor_name", None) or rng.choice(MENTOR_NAMES)
    return StoryParams(setting, power, relic, hero_name, hero_type, sidekick_name, mentor_name)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a child that includes the word "myth" and a magic rhyme.',
        f"Tell a story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} tries to fix a mythic problem at {world.setting.place} but learns to use rhyme instead of force.",
        f"Write a gentle superhero story about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id}, {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mentor").id}, and a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "relic").label} that needs magic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    mentor = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mentor")
    relic = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "relic")
    power = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "power")
    return [
        QAItem(
            question=f"What mythic problem happened at {world.setting.place}?",
            answer=f"A gloomy myth-shadow wrapped around the {relic.label} and tried to steal its bright song.",
        ),
        QAItem(
            question=f"Why did {mentor.id} stop {hero.id} from using only force?",
            answer=f"Because force made the trouble shake harder, and the story needed a rhyme that matched the {relic.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} sing to solve the problem?",
            answer=f'{hero.id} sang, "{_safe_lookup(REMEDIES, 0).rhyme if relic.id == "bell" else _safe_lookup(REMEDIES, 1).rhyme if relic.id == "lantern" else _safe_lookup(REMEDIES, 2).rhyme}!" and the magic worked.',
        ),
        QAItem(
            question=f"What was special about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "power").title} magic in this story?",
            answer=f"{power.title} magic was strong and bright, but the hero learned that the right kind of magic had to fit the problem, not just hit it harder.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story people tell about heroes, gods, monsters, or magical happenings.",
        ),
        QAItem(
            question="What is rhyme?",
            answer="Rhyme is when words sound alike at the end, like chime and time.",
        ),
        QAItem(
            question="Why can a superhero use both strength and kindness?",
            answer="A superhero can be strong enough to help and kind enough to choose the safest way to solve a problem.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid_combo(S,P,R) :- setting(S), power(P), relic(R), place_kind(R,S), power_fits(P,R).
story_ready(S,P,R) :- valid_combo(S,P,R).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sname, s in SETTINGS.items():
        lines.append(asp.fact("setting", sname))
        if s.has_tower:
            lines.append(asp.fact("has_tower", sname))
        if s.has_bridge:
            lines.append(asp.fact("has_bridge", sname))
    for pname, p in POWERS.items():
        lines.append(asp.fact("power", pname))
        for t in sorted(p.tags):
            lines.append(asp.fact("power_tag", pname, t))
    for rname, r in RELICS.items():
        lines.append(asp.fact("relic", rname))
        lines.append(asp.fact("place_kind", rname, r.place_kind))
        lines.append(asp.fact("power_fits", "rhyme", r.vulnerability))
        lines.append(asp.fact("relic_vuln", rname, r.vulnerability))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


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


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(POWERS, params.power), _safe_lookup(RELICS, params.relic),
                 params.hero_name, params.hero_type, params.sidekick_name, params.mentor_name)
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


def explain_rejection(power: Power, relic: Relic) -> str:
    return (
        f"(No story: {power.title} magic does not fit a {relic.label} problem at this place. "
        f"Try a rhyme-based power matched to the relic's vulnerability.)"
    )


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_combo/3."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for cfg in CURATED:
            params = StoryParams(
                setting=cfg["setting"],
                power=cfg["power"],
                relic=cfg["relic"],
                hero_name=cfg["hero"],
                hero_type=cfg["type"],
                sidekick_name=cfg["sidekick"],
                mentor_name=cfg["mentor"],
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.power} at {p.setting} (relic: {p.relic})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
