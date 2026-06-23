#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/clearance_natural_yearling_bad_ending_transformation_animal.py
===============================================================================================================

A standalone story world for a small animal tale with a bad ending and a
transformation beat.

Premise:
- A yearling animal loves a natural place to play.
- It finds something shiny during a clearance event.
- A warning tries to stop it.
- The animal chooses the wrong thing, and the world changes badly.
- The ending proves the transformation happened and could not be undone.

This world is intentionally compact and constraint-driven:
- 4 registries for ordinary generation variety
- typed entities with meters and memes
- a forward-chaining causal model
- a Python reasonableness gate plus inline ASP twin
- three QA sets grounded in the simulated world
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)

    guardian: object | None = None
    hero: object | None = None
    prop: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"doe", "ewe", "cow", "mare", "hen", "goat"}
        male = {"buck", "ram", "bull", "stallion", "rooster", "boar"}
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

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    id: str
    place: str
    mood: str
    has_clearance: bool
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class AnimalKind:
    id: str
    type: str
    young_label: str
    adult_label: str
    sound: str
    traits: list[str] = field(default_factory=list)
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class ObjectKind:
    id: str
    label: str
    phrase: str
    mess: str
    transforms_into: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Trigger:
    id: str
    label: str
    phrase: str
    effect: str
    risky_place: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_touch_transform(world: World) -> list[str]:
    out: list[str] = []
    for actor in list(world.entities.values()):
        if actor.kind != "character":
            continue
        if actor.meters.get("glow", 0.0) < THRESHOLD:
            continue
        for obj in list(world.entities.values()):
            if obj.kind != "thing" or obj.id == actor.id:
                continue
            if obj.id in world.fired:
                continue
        sig = ("transform", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.meters["changed"] += 1
        actor.meters["stuck"] += 1
        actor.memes["fear"] += 1
        actor.memes["loss"] += 1
        return ["__transformation__"]
    return out


CAUSAL_RULES = [Rule("touch_transform", "physical", _r_touch_transform)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule.apply(world)
            if bits:
                changed = True
                produced.extend(b for b in bits if not b.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def danger_at_risk(setting: Setting, trigger: Trigger, obj: ObjectKind) -> bool:
    return setting.id == trigger.risky_place and obj.id in {"frogstatue", "shell", "dewdrop"} or True


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for animal in ANIMALS:
            for obj in OBJECTS:
                for trig in TRIGGERS:
                    if setting.has_clearance and animal.id == "yearling" and trig.risky_place == setting.id:
                        combos.append((setting.id, animal.id, obj.id, trig.id))
    return combos


@dataclass
class StoryParams:
    setting: str
    animal: str
    object: str
    trigger: str
    name: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
    ap = argparse.ArgumentParser(description="Animal story world with a bad ending and a transformation.")
    ap.add_argument("--setting", choices=[s.id for s in SETTINGS])
    ap.add_argument("--animal", choices=[a.id for a in ANIMALS])
    ap.add_argument("--object", choices=[o.id for o in OBJECTS])
    ap.add_argument("--trigger", choices=[t.id for t in TRIGGERS])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "animal", None) is None or c[1] == getattr(args, "animal", None))
              and (getattr(args, "object", None) is None or c[2] == getattr(args, "object", None))
              and (getattr(args, "trigger", None) is None or c[3] == getattr(args, "trigger", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, animal, obj, trig = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(setting=setting, animal=animal, object=obj, trigger=trig, name=name)


def _introduce(world: World, hero: Entity, animal: AnimalKind, setting: Setting) -> None:
    world.say(
        f"{hero.id} was a yearling {animal.type} who loved the natural {setting.place}. "
        f"{hero.pronoun().capitalize()} knew every soft path and every cool patch of shade."
    )
    hero.memes["joy"] += 1


def _clearance(world: World, hero: Entity, trig: Trigger, obj: Entity) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f"Near a small clearance sign, {hero.id} found {obj.phrase}. "
        f"It looked bright and strange beside the moss."
    )
    world.say(
        f"{hero.id} wanted to touch {obj.label}, but an old otter called softly, "
        f"'{trig.effect} {trig.label}.'"
    )


def _warn(world: World, guardian: Entity, hero: Entity, trig: Trigger) -> None:
    guardian.memes["worry"] += 1
    world.say(
        f"{guardian.id} stepped closer and said, "
        f"'{trig.phrase} can change things you cannot get back.'"
    )


def _choose_wrong(world: World, hero: Entity, obj: Entity, trig: Trigger) -> None:
    hero.memes["want"] += 1
    hero.meters["glow"] += 1
    world.say(
        f"But {hero.id} did not listen. {hero.pronoun().capitalize()} pressed a hoof to {obj.label}, "
        f"and a soft glow climbed up {hero.pronoun('possessive')} legs."
    )


def _bad_ending(world: World, hero: Entity, obj: Entity, setting: Setting) -> None:
    hero.meters["changed"] = 1
    hero.meters["stuck"] = 1
    hero.memes["fear"] += 1
    world.say(
        f"When the glow faded, {hero.id} was no longer a yearling at all. "
        f"{hero.pronoun().capitalize()} had turned into {obj.phrase}, silent in the middle of the natural {setting.place}."
    )
    world.say(
        f"{hero.id}'s guardian searched the {setting.place}, but there was no undoing what had happened."
    )


SETTINGS = [
    Setting(id="meadow", place="meadow", mood="soft", has_clearance=True, tags={"natural", "clearance"}),
    Setting(id="grove", place="grove", mood="green", has_clearance=True, tags={"natural", "clearance"}),
    Setting(id="pond", place="pond edge", mood="still", has_clearance=True, tags={"natural", "clearance"}),
    Setting(id="hill", place="hill clearing", mood="open", has_clearance=True, tags={"natural", "clearance"}),
]

ANIMALS = [
    AnimalKind(id="yearling", type="deer", young_label="yearling", adult_label="doe", sound="bleat", traits=["young"], tags={"yearling"}),
    AnimalKind(id="yearling_foal", type="pony", young_label="yearling", adult_label="mare", sound="whinny", traits=["young"], tags={"yearling"}),
]

OBJECTS = [
    ObjectKind(id="mossorb", label="moss orb", phrase="a small moss orb", mess="glow", transforms_into="statue", tags={"natural"}),
    ObjectKind(id="dewseed", label="dew seed", phrase="a clear dew seed", mess="glow", transforms_into="stone", tags={"natural"}),
    ObjectKind(id="fernring", label="fern ring", phrase="a natural fern ring", mess="glow", transforms_into="shell", tags={"natural"}),
]

TRIGGERS = [
    Trigger(id="clearance_light", label="clearance light", phrase="A clearance light", effect="Do not touch", risky_place="meadow", tags={"clearance"}),
    Trigger(id="clearance_mist", label="clearance mist", phrase="A clearance mist", effect="Do not touch", risky_place="grove", tags={"clearance"}),
    Trigger(id="clearance_spark", label="clearance spark", phrase="A clearance spark", effect="Do not touch", risky_place="pond", tags={"clearance"}),
    Trigger(id="clearance_dust", label="clearance dust", phrase="A clearance dust", effect="Do not touch", risky_place="hill", tags={"clearance"}),
]

NAMES = ["Mina", "Pip", "Luna", "Bram", "Nell", "Otis", "Cleo", "Tavi"]


def tell(setting: Setting, animal: AnimalKind, obj: ObjectKind, trig: Trigger, name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=animal.type, label=name, meters={}, memes={}, tags={"yearling"}))
    guardian = world.add(Entity(id="guardian", kind="character", type="doe", label="the mother deer", meters={}, memes={}))
    prop = world.add(Entity(id=obj.id, kind="thing", type="thing", label=obj.label, phrase=obj.phrase, meters={}, memes={}, tags=obj.tags))
    world.facts = {"hero": hero, "guardian": guardian, "object": prop, "setting": setting, "animal": animal, "trigger": trig, "objcfg": obj}
    _introduce(world, hero, animal, setting)
    world.para()
    _clearance(world, hero, trig, prop)
    _warn(world, guardian, hero, trig)
    _choose_wrong(world, hero, prop, trig)
    propagate(world, narrate=False)
    world.para()
    _bad_ending(world, hero, prop, setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = f["hero"]
    obj = f["object"]
    setting = f["setting"]
    return [
        f'Write an animal story for a small child that uses the words "clearance", "natural", and "yearling".',
        f"Tell a short story about {hero.id}, a yearling animal, who finds {obj.phrase} during a clearance at the {setting.place} and ignores a warning.",
        f"Write a gentle story with a bad ending where a natural place and a clearance sign lead a yearling into a strange transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    guardian = f["guardian"]
    obj = f["object"]
    setting = f["setting"]
    return [
        QAItem(
            question=f"Who is the story about in the natural {setting.place}?",
            answer=f"It is about {hero.id}, a yearling animal who loved the natural {setting.place}. {hero.id} was the one who changed by the end.",
        ),
        QAItem(
            question=f"What did {hero.id} find during the clearance?",
            answer=f"{hero.id} found {obj.phrase} near the clearance sign. It looked bright, but it was the wrong thing to touch.",
        ),
        QAItem(
            question=f"Why did the mother deer warn {hero.id}?",
            answer=f"She warned {hero.id} because the clearance object could cause a transformation. She did not want the yearling to get stuck in a bad ending.",
        ),
        QAItem(
            question=f"What happened after {hero.id} touched {obj.label}?",
            answer=f"A glow climbed over {hero.id}, and then {hero.id} turned into {obj.phrase}. The guardian could only look on because the change could not be undone.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does clearance mean?",
            answer="Clearance means something is being sold off or cleared away. A clearance sign often means the thing is on a special shelf or being removed soon.",
        ),
        QAItem(
            question="What does natural mean?",
            answer="Natural means it comes from the world around us, not from a machine or a pretend trick. Trees, grass, water, and animals are natural.",
        ),
        QAItem(
            question="What does yearling mean?",
            answer="A yearling is a young animal that is about one year old. It is not a tiny baby anymore, but it is still young.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} tags={sorted(e.tags)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s.id))
        if s.has_clearance:
            lines.append(asp.fact("has_clearance", s.id))
    for a in ANIMALS:
        lines.append(asp.fact("animal", a.id))
        lines.append(asp.fact("young_label", a.id, a.young_label))
    for o in OBJECTS:
        lines.append(asp.fact("object", o.id))
        lines.append(asp.fact("transforms_into", o.id, o.transforms_into))
    for t in TRIGGERS:
        lines.append(asp.fact("trigger", t.id))
        lines.append(asp.fact("risky_place", t.id, t.risky_place))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,O,T) :- setting(S), animal(A), object(O), trigger(T), has_clearance(S).
bad_ending(S,A,O,T) :- valid(S,A,O,T), transforms_into(O,_), risky_place(T,S).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set != python_set:
        print("MISMATCH between ASP and Python gate.")
        if clingo_set - python_set:
            print("  only in clingo:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        return 1
    sample = generate(resolve_params(argparse.Namespace(setting=None, animal=None, object=None, trigger=None, name=None), random.Random(777)))
    if not sample.story.strip():
        print("Smoketest failed: empty story.")
        return 1
    print(f"OK: {len(clingo_set)} valid combos and a generation smoke test passed.")
    return 0


def generate(params: StoryParams) -> StorySample:
    setting = next(s for s in SETTINGS if s.id == params.setting)
    animal = next(a for a in ANIMALS if a.id == params.animal)
    obj = next(o for o in OBJECTS if o.id == params.object)
    trig = next(t for t in TRIGGERS if t.id == params.trigger)
    world = tell(setting, animal, obj, trig, params.name)
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
    StoryParams(setting="meadow", animal="yearling", object="mossorb", trigger="clearance_light", name="Mina"),
    StoryParams(setting="grove", animal="yearling_foal", object="dewseed", trigger="clearance_mist", name="Pip"),
    StoryParams(setting="pond", animal="yearling", object="fernring", trigger="clearance_spark", name="Luna"),
    StoryParams(setting="hill", animal="yearling_foal", object="mossorb", trigger="clearance_dust", name="Bram"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:\n")
        for row in combos:
            print("  " + " ".join(map(str, row)))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
