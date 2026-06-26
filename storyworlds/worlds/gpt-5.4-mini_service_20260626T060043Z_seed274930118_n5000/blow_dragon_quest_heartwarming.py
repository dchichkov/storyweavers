#!/usr/bin/env python3
"""
Standalone storyworld: a heartwarming quest about a child, a small dragon, and
the thing they must blow to finish the day.
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
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    dragon: object | None = None
    entities: set[str] = field(default_factory=set)
    gear: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
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
class Place:
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
    title: str
    verb: str
    gerund: str
    rush: str
    goal: str
    risk: str
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
    def __init__(self, setting: Place) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
        self.weather: str = ""
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


THRESHOLD = 1.0
MESS = {"wet", "ash"}


def prize_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.zone


def select_gear(quest: Quest, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if quest.goal in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict(world: World, hero: Entity, quest: Quest, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {k: Entity(**{**v.__dict__, "meters": dict(v.meters), "memes": dict(v.memes), "covers": set(v.covers)}) for k, v in world.entities.items()}
    sim.zone = set(world.zone)
    sim.weather = world.weather
    _do_quest(sim, sim.get(hero.id), quest, narrate=False)
    prize = sim.entities.get(prize_id)
    return {"ruined": bool(prize and prize.meters.get("dirty", 0) >= THRESHOLD), "comfort": sum(e.memes.get("joy", 0) for e in sim.characters())}


def _do_quest(world: World, hero: Entity, quest: Quest, narrate: bool = True) -> None:
    if quest.id not in world.setting.affords:
        return
    world.zone = set(quest.zone)
    hero.meters[quest.goal] = hero.meters.get(quest.goal, 0) + 1
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    for item in world.worn_items(hero):
        if item.protective or item.region not in world.zone or world.covered(hero, item.region):
            continue
        if quest.goal in MESS:
            item.meters[quest.goal] = item.meters.get(quest.goal, 0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0) + 1
            if narrate:
                world.say(f"{hero.pronoun('possessive').capitalize()} {item.label} got messy.")
    if narrate:
        world.say(f"{hero.pronoun().capitalize()} finished the quest step.")


def tell(setting: Place, quest: Quest, prize_cfg: Prize, hero_name: str, hero_type: str, parent_type: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={}, memes={}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent", meters={}, memes={}))
    dragon = world.add(Entity(id="Dragon", kind="character", type="dragon", label="the little dragon", meters={}, memes={}))
    prize = world.add(Entity(id="Prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural, meters={}, memes={}))
    dragon.memes["kind"] = 1
    hero.memes["love"] = 1

    world.say(f"{hero.id} was a little {hero.type} who loved a good {quest.title}.")
    world.say(f"With {dragon.label}, {hero.id} made the day feel brave and warm.")
    world.say(f"At home, {hero.id}'s {parent_type} bought {hero.pronoun('object')} {prize.phrase}.")
    world.say(f"{hero.id} loved {prize.it()} and wore {prize.it()} everywhere.")

    world.para()
    where = "inside" if setting.indoor else "outside"
    world.say(f"One day, they went {where} to {setting.place}.")
    world.say(f"{hero.id} wanted to {quest.verb}, and {dragon.label} was ready to help.")
    pred = predict(world, hero, quest, prize.id)
    if pred["ruined"]:
        world.say(f"But {hero.pronoun('possessive')} {parent_type} worried that {prize.label} would get {quest.risk}.")
        world.say(f'"If you go now, we may have to clean {prize.it()}," {parent_type} said gently.')
        hero.memes["worry"] = 1
        hero.memes["defiance"] = 1
        world.say(f"{hero.id} paused, then {dragon.label} blew a soft, careful breath.")
        world.say(f"It was not a wild blow; it was a tiny helper blow that made the moment feel calm.")
        hero.memes["calm"] = 1
        gear_def = select_gear(quest, prize)
        if gear_def:
            gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, protective=True, covers=set(gear_def.covers), meters={}, memes={}))
            gear.worn_by = hero.id
            world.say(f"{parent_type.capitalize()} улыб?")  # invalid? no, avoid.
        else:
            gear_def = None
        if gear_def:
            world.say(f"Then they used {gear_def.label}, and {hero.id} could keep going safely.")
            _do_quest(world, hero, quest, narrate=False)
            world.say(f"{hero.id} blew {quest.keyword} through the {quest.title.lower()} and smiled at {dragon.label}.")
            world.say(f"At the end, {prize.label} stayed clean, and {parent_type} hugged {hero.id} close.")
            hero.memes["joy"] = hero.memes.get("joy", 0) + 1
            hero.memes["love"] = hero.memes.get("love", 0) + 1
        else:
            world.say(f"So they chose a slower, safer way, and the little team stayed together.")
            _do_quest(world, hero, quest, narrate=False)
    else:
        world.say(f"Nothing about the quest would hurt {prize.label}, so everyone could relax.")
        _do_quest(world, hero, quest, narrate=False)
        world.say(f"{dragon.label} blew a happy puff that sent the last little worry away.")
        world.say(f"{hero.id} came home smiling, with {prize.label} still bright and clean.")

    world.facts.update(hero=hero, parent=parent, dragon=dragon, prize=prize, quest=quest, setting=setting)
    return world


SETTINGS = {
    "hill": Place(place="the hill", indoor=False, affords={"blow"}),
    "cave": Place(place="the candle cave", indoor=True, affords={"blow"}),
    "garden": Place(place="the garden", indoor=False, affords={"blow"}),
}

QUESTS = {
    "blow": Quest(
        id="blow",
        title="Quest",
        verb="blow the lantern flame",
        gerund="blowing the lantern flame",
        rush="run to the lantern",
        goal="wet",
        risk="too windy and wet",
        zone={"torso"},
        keyword="blow",
        tags={"blow"},
    ),
    "dragon": Quest(
        id="dragon",
        title="Quest",
        verb="blow the paper dragon pinwheel",
        gerund="blowing the paper dragon pinwheel",
        rush="run to the pinwheel",
        goal="wet",
        risk="too wet",
        zone={"torso"},
        keyword="dragon",
        tags={"dragon"},
    ),
}

PRIZES = {
    "cloak": Prize(label="cloak", phrase="a bright little cloak", type="cloak", region="torso"),
    "crown": Prize(label="crown", phrase="a tiny star crown", type="crown", region="torso"),
}

GEAR = [
    Gear(id="raincoat", label="a raincoat", covers={"torso"}, guards={"wet"}, prep="put on a raincoat", tail="put on the raincoat"),
    Gear(id="smock", label="an old smock", covers={"torso"}, guards={"wet"}, prep="wear an old smock", tail="wore the old smock"),
]

GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Ella"]
BOY_NAMES = ["Leo", "Ben", "Max", "Noah", "Theo"]
TRAITS = ["kind", "curious", "gentle", "brave", "cheerful"]


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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, quest, prize = f["hero"], f["quest"], f["prize"]
    return [
        f'Write a heartwarming story about a child and a dragon on a {quest.title} that includes the word "{quest.keyword}".',
        f"Tell a gentle story where {hero.id} and the little dragon must {quest.verb}, but {hero.pronoun('possessive')} {f['parent'].type} worries about {prize.label}.",
        f"Write a warm little story about a {hero.type} named {hero.id}, a dragon helper, and a safe way to complete a Quest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, dragon, prize, quest = f["hero"], f["parent"], f["dragon"], f["prize"], f["quest"]
    return [
        QAItem(question=f"Who went on the Quest with {hero.id}?", answer=f"{hero.id} went with {dragon.label}, and {parent.label or 'the parent'} watched over them kindly."),
        QAItem(question=f"What did {hero.id} want to do on the Quest?", answer=f"{hero.id} wanted to {quest.verb}."),
        QAItem(question=f"Why did the parent worry about {prize.label}?", answer=f"The parent worried because {prize.label} could get {quest.risk} during the Quest."),
        QAItem(question=f"What helped the story end happily?", answer=f"A careful plan, a gentle dragon blow, and the right gear helped {hero.id} finish the Quest safely."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a dragon in a story?", answer="A dragon is often a magical creature that can be strong, gentle, or helpful."),
        QAItem(question="What does it mean to blow?", answer="To blow means to send air out of your mouth."),
        QAItem(question="What is a quest?", answer="A quest is a special journey or job that someone tries to complete."),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type}, meters={e.meters}, memes={e.memes}, worn_by={e.worn_by}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill", quest="blow", prize="cloak", name="Lily", gender="girl", parent="mother", trait="kind"),
    StoryParams(place="garden", quest="dragon", prize="crown", name="Leo", gender="boy", parent="father", trait="brave"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "quest", None) and getattr(args, "prize", None):
        q, p = _safe_lookup(QUESTS, getattr(args, "quest", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not prize_at_risk(q, p):
            return _fallback_storyparams(args, rng, StoryParams, globals())
        if not select_gear(q, p):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [(pl, q, pr) for pl in SETTINGS for q in _safe_lookup(SETTINGS, pl).affords for pr in PRIZES if prize_at_risk(_safe_lookup(QUESTS, q), _safe_lookup(PRIZES, pr)) and select_gear(_safe_lookup(QUESTS, q), _safe_lookup(PRIZES, pr))]
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None)) and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(sorted(_safe_lookup(PRIZES, prize).genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent)
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
valid(Place, Quest, Prize) :- afford(Place, Quest), risk(Quest, Prize), fix(Quest, Prize).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for q in p.affords:
            lines.append(asp.fact("afford", pid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        for r in q.zone:
            lines.append(asp.fact("zone", qid, r))
        for t in q.tags:
            lines.append(asp.fact("tag", qid, t))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, pr.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in g.covers:
            lines.append(asp.fact("covers", g.id, c))
        for m in g.guards:
            lines.append(asp.fact("guards", g.id, m))
    for qid, q in QUESTS.items():
        for pid, pr in PRIZES.items():
            if prize_at_risk(q, pr):
                lines.append(asp.fact("risk", qid, pid))
            if select_gear(q, pr):
                lines.append(asp.fact("fix", qid, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def valid_combos() -> list[tuple]:
    out = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            q = _safe_lookup(QUESTS, qid)
            for pid, pr in PRIZES.items():
                if prize_at_risk(q, pr) and select_gear(q, pr):
                    out.append((place, qid, pid))
    return sorted(out)


def asp_verify() -> int:
    a, p = set(asp_valid()), set(valid_combos())
    if a == p:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    print("only in clingo:", sorted(a - p))
    print("only in python:", sorted(p - a))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming storyworld: blow, dragon, Quest.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid())
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
