#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/effect_transformation_repetition_inner_monologue_nursery_rhyme.py
==============================================================================================================

A standalone story world for a tiny nursery-rhyme-like domain about a child,
a wish for a magical effect, a transformation, repeated tries, and an inner
monologue that helps the turn toward a gentle resolution.

The seed-word is "effect". The stories are kept small, concrete, and causal:
a child wants a playful effect, tries a repeated rhyme, worries aloud in their
head, and then the world changes in a way that makes the ending image different
from the beginning.

This world intentionally keeps the premise compact so the generated stories feel
like little rhymes with a clear beginning, a turn, and an ending image.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    target: object | None = None
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
        return {"mother": "mom", "father": "dad", "grandmother": "grandma", "grandfather": "grandpa"}.get(self.type, self.type)
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
class Spell:
    id: str
    verb: str
    gerund: str
    repeat_line: str
    effect: str
    change: str
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
class Charm:
    id: str
    label: str
    prep: str
    tail: str
    works_on: str
    causes: str
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
        self.facts: dict = {}
        self.cycle: int = 0

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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.cycle = self.cycle
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_repeat(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("chanting", 0.0) < THRESHOLD:
            continue
        key = ("repeat", actor.id, world.cycle)
        if key in world.fired:
            continue
        world.fired.add(key)
        actor.meters["chants"] = actor.meters.get("chants", 0.0) + 1
        actor.memes["hope"] = actor.memes.get("hope", 0.0) + 1
        out.append(f"{actor.id} said the little line again and again.")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("hope", 0.0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.owner != actor.id:
                continue
            if item.meters.get("spark", 0.0) < THRESHOLD:
                continue
            key = ("transform", actor.id, item.id)
            if key in world.fired:
                continue
            world.fired.add(key)
            item.meters["changed"] = 1.0
            item.label = item.label + " with a bright new glow"
            out.append(f"The {item.type} changed at last.")
    return out


def _r_settle(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("chants", 0.0) < 2:
            continue
        key = ("settle", actor.id)
        if key in world.fired:
            continue
        world.fired.add(key)
        actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1
        out.append(f"{actor.id} took a slow breath and listened to the hush.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("repeat", "social", _r_repeat),
    Rule("transformation", "physical", _r_transformation),
    Rule("settle", "social", _r_settle),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        world.cycle += 1
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def setting_detail(setting: Setting) -> str:
    if setting.indoor:
        return f"Inside {setting.place}, the air was still and soft."
    return f"{setting.place.capitalize()} was bright and small, with room for a tiny tune."


def prefix_by_day(setting: Setting) -> str:
    return "One day, " if not setting.indoor else "One afternoon, "


def inner_monologue(hero: Entity, charm: Charm, target: Prize) -> str:
    return (
        f'In {hero.pronoun("possessive")} head, {hero.pronoun("subject")} thought, '
        f'"One more try, one more rhyme. Maybe the {charm.label} will help the '
        f'{target.label} change this time."'
    )


def attempt(world: World, hero: Entity, spell: Spell, charm: Charm, target: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    hero.memes["chanting"] = hero.memes.get("chanting", 0.0) + 1
    target.meters["spark"] = target.meters.get("spark", 0.0) + 1
    world.say(
        f"{hero.id} wanted the {spell.keyword} effect right away, "
        f"so {hero.pronoun('subject')} tapped the {charm.label} and said, "
        f'"{spell.repeat_line}"'
    )
    world.say(inner_monologue(hero, charm, target))
    propagate(world, narrate=True)


def worry(world: World, parent: Entity, hero: Entity, spell: Spell, target: Entity) -> None:
    parent.memes["care"] = parent.memes.get("care", 0.0) + 1
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} watched the little spark and said, "
        f'"Careful now. Some effects are small, and some effects run away."'
    )


def resolve(world: World, hero: Entity, spell: Spell, charm: Charm, target: Entity) -> None:
    hero.memes["calm"] = hero.memes.get("calm", 0.0) + 1
    world.say(
        f"Then {hero.id} whispered the rhyme a last time, and the air grew kind."
    )
    target.label = target.label + " turned merry"
    world.say(
        f"The {target.type} did not stay plain. It became {target.phrase}, "
        f"and {hero.id} smiled at the new little shine."
    )


def tell(setting: Setting, spell: Spell, target_cfg: Prize, charm: Charm,
         hero_name: str = "Mina", hero_type: str = "girl",
         parent_type: str = "mother", hero_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"spark": 0.0, "chants": 0.0},
        memes={"want": 1.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=parent_type,
        label="the parent",
        memes={"care": 0.0},
    ))
    target = world.add(Entity(
        id="target",
        type=target_cfg.type,
        label=target_cfg.label,
        phrase=target_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        region=target_cfg.region,
        plural=target_cfg.plural,
        meters={"spark": 0.0, "changed": 0.0},
    ))
    world.say(f"{prefix_by_day(setting)}{hero.id} was a little {hero_type} with a head full of song.")
    world.say(f"{hero.id} loved the {spell.keyword} effect and the {spell.gerund}.")
    world.say(f"{hero.id} had a {target.phrase} that waited on the table.")
    world.para()
    world.say(setting_detail(setting))
    worry(world, parent, hero, spell, target)
    attempt(world, hero, spell, charm, target)
    world.para()
    resolve(world, hero, spell, charm, target)
    world.facts.update(hero=hero, parent=parent, target=target, spell=spell, charm=charm, setting=setting)
    return world


SETTINGS = {
    "nursery": Setting(place="the nursery", indoor=True, affords={"chant"}),
    "garden": Setting(place="the garden", indoor=False, affords={"chant"}),
    "attic": Setting(place="the attic", indoor=True, affords={"chant"}),
    "meadow": Setting(place="the meadow", indoor=False, affords={"chant"}),
}

SPELLS = {
    "glow": Spell(
        id="glow",
        verb="make it glow",
        gerund="making glow-songs",
        repeat_line="Glow, glow, little row",
        effect="glow",
        change="bright and warm",
        keyword="glow",
        tags={"light", "change"},
    ),
    "bounce": Spell(
        id="bounce",
        verb="make it bounce",
        gerund="bouncing in a circle",
        repeat_line="Bounce, bounce, up it goes",
        effect="bounce",
        change="high and funny",
        keyword="bounce",
        tags={"move", "change"},
    ),
    "turn": Spell(
        id="turn",
        verb="turn it round",
        gerund="turning and twirling",
        repeat_line="Turn, turn, little fern",
        effect="turn",
        change="round and new",
        keyword="turn",
        tags={"spin", "change"},
    ),
}

PRIZES = {
    "star": Prize(label="star card", phrase="a tiny star card", type="card", region="hands"),
    "block": Prize(label="block", phrase="a plain wooden block", type="block", region="hands"),
    "cup": Prize(label="cup", phrase="a little tin cup", type="cup", region="hands"),
    "bell": Prize(label="bell", phrase="a small brass bell", type="bell", region="hands"),
}

CHARMS = {
    "rattle": Charm(id="rattle", label="a rattle", prep="tap", tail="tapped again", works_on="chant", causes="spark"),
    "wand": Charm(id="wand", label="a wand", prep="wave", tail="waved again", works_on="chant", causes="spark"),
    "spoon": Charm(id="spoon", label="a spoon", prep="tap", tail="tapped again", works_on="chant", causes="spark"),
}

GIRL_NAMES = ["Mina", "Lila", "Nina", "Poppy", "Ruby", "Ivy"]
BOY_NAMES = ["Noah", "Owen", "Finn", "Theo", "Ben", "Leo"]


@dataclass
class StoryParams:
    place: str
    spell: str
    prize: str
    charm: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for spell in setting.affords:
            for prize in PRIZES:
                combos.append((place, spell, prize))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, spell, target, charm = f["hero"], f["spell"], f["target"], f["charm"]
    return [
        f'Write a short nursery-rhyme story with the word "effect" in it about {hero.id}, '
        f'a {spell.keyword} effect, and a little transformation.',
        f"Tell a gentle rhyming story where {hero.id} repeats a tiny line, wonders "
        f"inwardly, and helps {target.phrase} change.",
        f'Write a child-friendly story with repetition and an inner monologue, ending '
        f'with the {target.type} becoming different because of a magical effect.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, target, spell, charm = f["hero"], f["parent"], f["target"], f["spell"], f["charm"]
    qa = [
        QAItem(
            question=f"What did {hero.id} want to happen with the {target.label}?",
            answer=f"{hero.id} wanted the {spell.keyword} effect to help the {target.label} change into something brighter and nicer.",
        ),
        QAItem(
            question=f"What little line did {hero.id} repeat over and over?",
            answer=f"{hero.id} repeated, \"{spell.repeat_line}\" while tapping the {charm.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} think in {hero.pronoun('possessive')} head before the last try?",
            answer=f"{hero.id} thought that one more rhyme might help the {target.label} change this time.",
        ),
        QAItem(
            question=f"Why did {parent.label_word} speak up?",
            answer=f"{parent.label_word} worried that the effect might be too wild, so {parent.label_word} reminded {hero.id} to be careful.",
        ),
        QAItem(
            question=f"What was different at the end?",
            answer=f"At the end, the {target.type} was no longer plain; it had become {target.phrase} and looked merry and bright.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an effect?",
            answer="An effect is something that happens because of a cause, like a light turning on when you press a switch.",
        ),
        QAItem(
            question="What does repeating a rhyme do in a story?",
            answer="Repeating a rhyme can make a story sound musical and can also show that a character is trying again and again.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking a character does in their own head.",
        ),
        QAItem(
            question="What is a transformation?",
            answer="A transformation is a change from one form or state into another.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="nursery", spell="glow", prize="star", charm="rattle", name="Mina", gender="girl", parent="mother"),
    StoryParams(place="garden", spell="bounce", prize="block", charm="wand", name="Noah", gender="boy", parent="father"),
    StoryParams(place="attic", spell="turn", prize="cup", charm="spoon", name="Lila", gender="girl", parent="mother"),
]


ASP_RULES = r"""
spell_effect(S,E) :- spell(S), effect_of(S,E).
repeats(S) :- spell(S), line(S,_).
transforms(T) :- target(T), spark(T), hope(hero).
valid_story(P,S,T) :- place(P), spell(S), target(T), affords(P,S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, s in SPELLS.items():
        lines.append(asp.fact("spell", sid))
        lines.append(asp.fact("effect_of", sid, s.effect))
        lines.append(asp.fact("line", sid, s.repeat_line))
    for tid, t in PRIZES.items():
        lines.append(asp.fact("target", tid))
    for cid, c in CHARMS.items():
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("causes", cid, c.causes))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    clingo_set = set(asp.atoms(model, "valid_story"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme story world about effect, repetition, inner monologue, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--spell", choices=SPELLS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father", "grandmother", "grandfather"])
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
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "spell", None) is None or c[1] == getattr(args, "spell", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, spell, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    charm = getattr(args, "charm", None) or rng.choice(list(CHARMS))
    return StoryParams(place=place, spell=spell, prize=prize, charm=charm, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(SPELLS, params.spell), _safe_lookup(PRIZES, params.prize), _safe_lookup(CHARMS, params.charm), params.name, params.gender, params.parent)
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
        model = asp.one_model(asp_program("#show valid_story/3."))
        triples = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(triples)} compatible (place, spell, prize) combos:\n")
        for t in triples:
            print("  ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

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
            header = f"### {p.name}: {p.spell} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
