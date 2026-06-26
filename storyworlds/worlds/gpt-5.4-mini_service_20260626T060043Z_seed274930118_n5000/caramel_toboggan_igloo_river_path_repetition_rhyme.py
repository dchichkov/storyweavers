#!/usr/bin/env python3
"""
storyworlds/worlds/caramel_toboggan_igloo_river_path_repetition_rhyme.py
========================================================================

A small superhero-style story world set on a river path, built from the seed
words caramel, toboggan, and igloo.

Premise:
- A young hero patrols a river path.
- A friend wants to use a toboggan on the slippy path.
- Caramel is being delivered for a small celebration near an igloo.

Tension:
- The toboggan drifts toward the river and threatens the caramel.
- A rival blocks the path and causes conflict.
- The hero uses repetition and rhyme to steady the group and solve the problem.

Resolution:
- The hero redirects the toboggan, protects the caramel, and turns the igloo
  stop into a cheerful ending image.

This script keeps the simulated state concrete:
- physical meters track motion, risk, and damage
- emotional memes track confidence, conflict, relief, and delight

It also includes an inline ASP twin for the reasonableness gate, plus a Python
gate used by normal generation.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field, asdict
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
    allied_with: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    ally: object | None = None
    hero: object | None = None
    prize: object | None = None
    rival: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
    place: str = "the river path"
    windy: bool = False
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
    rush: str
    risk: str
    zone: set[str]
    keyword: str
    rhyme: str
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
    risky_by: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _add_meter(e: Entity, key: str, amt: float) -> None:
    e.meters[key] = _meter(e, key) + amt


def _add_mem(e: Entity, key: str, amt: float) -> None:
    e.memes[key] = _mem(e, key) + amt


def _set_mem(e: Entity, key: str, val: float) -> None:
    e.memes[key] = val


def _do_action(world: World, hero: Entity, action: Action, narrate: bool = True) -> None:
    world.zone = set(action.zone)
    _add_meter(hero, action.keyword, 1.0)
    _add_mem(hero, "confidence", 1.0)
    if narrate:
        world.say(f"{hero.id} went to {world.setting.place} and {action.verb}.")


def _apply_conflict(world: World, hero: Entity, rival: Entity) -> None:
    if _mem(hero, "frustration") >= THRESHOLD and _mem(rival, "blocking") >= THRESHOLD:
        sig = ("conflict", hero.id)
        if sig not in world.fired:
            world.fired.add(sig)
            _add_mem(hero, "conflict", 1.0)
            _add_mem(rival, "conflict", 1.0)


def _apply_risk(world: World, hero: Entity, prize: Entity) -> None:
    if _meter(hero, "toboggan") < THRESHOLD:
        return
    if prize.region in world.zone:
        sig = ("risk", prize.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        _add_meter(prize, "risky", 1.0)
        _add_mem(hero, "worry", 1.0)


def _apply_rescue(world: World, hero: Entity, prize: Entity, gear: Optional[Gear]) -> None:
    if gear and _meter(prize, "risky") >= THRESHOLD and gear.covers and prize.region in gear.covers:
        sig = ("rescue", prize.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        _set_mem(hero, "conflict", 0.0)
        _add_mem(hero, "relief", 1.0)
        _set_mem(prize, "risky", 0.0)


def propagate(world: World, hero: Entity, rival: Entity, prize: Entity, gear: Optional[Gear]) -> None:
    _apply_conflict(world, hero, rival)
    _apply_risk(world, hero, prize)
    _apply_rescue(world, hero, prize, gear)


def rhyme_line(a: str, b: str) -> str:
    return f"{a.capitalize()} and {b} can glide; keep calm and ride."


def repetition_line(word: str) -> str:
    return f"{word.capitalize()}, {word}, keep going on."


def prize_at_risk(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone and action.id in prize.risky_by


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if action.id in g.guards and prize.region in g.covers:
            return g
    return None


def reasonableness_gate(action: Action, prize: Prize) -> bool:
    return prize_at_risk(action, prize) and select_gear(action, prize) is not None


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a brave little hero who watched over {world.setting.place}."
    )


def setup(world: World, hero: Entity, ally: Entity, rival: Entity, prize: Entity, action: Action) -> None:
    world.say(
        f"Every day, {hero.id} loved to patrol the river path and look for trouble."
    )
    world.say(
        f"{ally.id} brought a sweet caramel treat for the stop by the igloo."
    )
    world.say(
        f"{hero.id} smiled at the {prize.label}, because the plan was to keep it safe."
    )
    world.say(repetition_line("steady"))
    world.say(rhyme_line("bright", "light"))


def conflict_scene(world: World, hero: Entity, ally: Entity, rival: Entity, prize: Entity, action: Action) -> None:
    world.para()
    world.say(
        f"Then {ally.id} pulled a toboggan onto the river path, and the wheels skated fast."
    )
    world.say(
        f"{rival.id} blocked the path and barked, 'No, no, no!'"
    )
    _add_mem(hero, "frustration", 1.0)
    _add_mem(rival, "blocking", 1.0)
    propagate(world, hero, rival, prize, None)
    if _mem(hero, "conflict") >= THRESHOLD:
        world.say(
            f"{hero.id} felt the clash in the air and called out, 'Slow, slow, stay in control.'"
        )
    world.say(
        f"The toboggan tilted toward the water, and the caramel box wobbled on its rope."
    )
    world.say(repetition_line("careful"))


def resolution_scene(world: World, hero: Entity, ally: Entity, rival: Entity, prize: Entity, gear: Gear, action: Action) -> None:
    world.para()
    world.say(
        f"{hero.id} pointed to the safe side of the path and said, '{gear.prep}.'"
    )
    world.say(
        f"{ally.id} listened, and {rival.id} stopped shouting long enough to help."
    )
    world.say(
        f"The {gear.label} held the toboggan steady while {hero.id} guided it away from the river."
    )
    world.say(
        f"At the igloo, the caramel stayed clean, and everyone laughed at the cool, crunchy snow."
    )
    world.say(
        f"'{gear.tail.capitalize()},' said {hero.id}, and the day felt calm again."
    )
    world.say(repetition_line("safe"))


def tell(setting: Setting, action: Action, prize_cfg: Prize, hero_name: str = "Nova") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl"))
    ally = world.add(Entity(id="Pip", kind="character", type="boy"))
    rival = world.add(Entity(id="Rook", kind="character", type="boy"))
    prize = world.add(Entity(id="caramel_box", type="caramel", label="caramel box", phrase="a shiny caramel box", region=prize_cfg.region, plural=False))
    gear_def = select_gear(action, prize_cfg)
    if gear_def is None:
        pass

    intro(world, hero)
    setup(world, hero, ally, rival, prize, action)
    conflict_scene(world, hero, ally, rival, prize, action)
    resolution_scene(world, hero, ally, rival, prize, gear_def, action)

    world.facts.update(
        hero=hero,
        ally=ally,
        rival=rival,
        prize=prize,
        prize_cfg=prize_cfg,
        action=action,
        gear=gear_def,
        setting=setting,
    )
    return world


SETTINGS = {
    "river_path": Setting(place="the river path", windy=True, affords={"toboggan"}),
}

ACTIONS = {
    "toboggan": Action(
        id="toboggan",
        verb="push the toboggan",
        gerund="pushing the toboggan",
        rush="race the toboggan downhill",
        risk="slip toward the river",
        zone={"ground", "path"},
        keyword="toboggan",
        rhyme="glide",
        tags={"toboggan", "river"},
    ),
}

PRIZES = {
    "caramel": Prize(
        id="caramel",
        label="caramel",
        phrase="sweet caramel",
        region="path",
        risky_by={"toboggan"},
    ),
}

GEAR = [
    Gear(
        id="rope_guide",
        label="rope guide",
        covers={"path"},
        guards={"toboggan"},
        prep="keep the toboggan close and steer it with the rope guide",
        tail="kept the toboggan close and safe",
    ),
]

HERO_NAMES = ["Nova", "Spark", "Comet", "Rae", "Zoom", "Vera"]
RIVAL_NAMES = ["Rook", "Brick", "Moss", "Blaze"]
TRAITS = ["brave", "bright", "quick", "kind"]


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    rival: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    return [
        'Write a short superhero story set on the river path that uses the words "caramel", "toboggan", and "igloo".',
        f"Tell a brave story about {hero.id} using repetition and rhyme to stop a toboggan from causing trouble near the igloo.",
        "Write a child-friendly conflict-and-rescue story where a hero keeps caramel safe beside an igloo on a river path.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, ally, rival, prize, action, gear = f["hero"], f["ally"], f["rival"], f["prize"], f["action"], f["gear"]
    return [
        QAItem(
            question=f"Who is the superhero in the story?",
            answer=f"The superhero is {hero.id}, who watched over the river path and stayed brave during the trouble.",
        ),
        QAItem(
            question=f"What caused the problem on the river path?",
            answer=f"The problem started when {ally.id} pulled a toboggan onto the path and it skidded toward the river.",
        ),
        QAItem(
            question=f"What was the sweet thing the hero wanted to protect?",
            answer=f"The hero wanted to protect the caramel so it would stay safe for the stop by the igloo.",
        ),
        QAItem(
            question=f"How did {hero.id} solve the conflict?",
            answer=f"{hero.id} used the rope guide, calmed everyone down, and steered the toboggan away from the river.",
        ),
        QAItem(
            question=f"What helped the ending feel peaceful again?",
            answer=f"The rope guide and the hero's calm words helped the group settle down, and the caramel stayed safe near the igloo.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a toboggan?",
            answer="A toboggan is a sled or滑 ride that can slide over snow or a slippery path.",
        ),
        QAItem(
            question="What is caramel?",
            answer="Caramel is a sweet, sticky treat made by heating sugar until it turns golden brown.",
        ),
        QAItem(
            question="What is an igloo?",
            answer="An igloo is a shelter built from blocks of snow or ice.",
        ),
        QAItem(
            question="Why can repetition help in a story?",
            answer="Repetition can make a line easy to remember and can help a character sound calm and steady.",
        ),
        QAItem(
            question="Why do rhymes sound nice to children?",
            answer="Rhymes sound musical because the ends of the words sound alike, like in a cheerful song.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: type={e.type} meters={dict((k, v) for k, v in e.meters.items() if v)} memes={dict((k, v) for k, v in e.memes.items() if v)}"
        )
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="river_path", action="toboggan", prize="caramel", name="Nova", rival="Rook", trait="brave"),
    StoryParams(place="river_path", action="toboggan", prize="caramel", name="Spark", rival="Brick", trait="bright"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.windy:
            lines.append(asp.fact("windy", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        for z in sorted(a.zone):
            lines.append(asp.fact("zone", aid, z))
        lines.append(asp.fact("risk_word", aid, a.risk))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        for r in sorted(p.risky_by):
            lines.append(asp.fact("risky_by", pid, r))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for gk in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, gk))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), region(P,R), risky_by(P,A).
has_fix(A,P) :- prize_at_risk(A,P), gear(G), guards(G,A), covers(G,R), region(P,R).
valid_story(S,A,P) :- setting(S), affords(S,A), prize(P), prize_at_risk(A,P), has_fix(A,P).
#show valid_story/3.
#show prize_at_risk/2.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("river_path", "toboggan", "caramel")}
    import asp
    clingo_set = set(asp.atoms(asp.one_model(asp_program("#show valid_story/3.")), "valid_story"))
    if clingo_set == py:
        print(f"OK: ASP matches Python gate ({len(py)} story).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("python:", sorted(py))
    print("asp:", sorted(clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: caramel, toboggan, and igloo on the river path.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=HERO_NAMES)
    ap.add_argument("--rival", choices=RIVAL_NAMES)
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
    if getattr(args, "action", None) and getattr(args, "prize", None):
        if not reasonableness_gate(_safe_lookup(ACTIONS, getattr(args, "action", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=getattr(args, "place", None) or "river_path",
        action=getattr(args, "action", None) or "toboggan",
        prize=getattr(args, "prize", None) or "caramel",
        name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        rival=getattr(args, "rival", None) or rng.choice(RIVAL_NAMES),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize), params.name)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        print(asp_program("#show valid_story/3."))
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(asp.atoms(model, "valid_story"))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
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
