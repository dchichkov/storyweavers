#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/smarten_professional_week_humor_foreshadowing_inner_monologue.py
===============================================================================================================================

A tall-tale storyworld about a dusty small-town fellow trying to smarten up
for Professional Week without losing his humor, his nerve, or his socks.

Premise:
- A character in a tiny town wants to look professional for a week-long event.
- His usual gear is too rough, too muddy, or too silly for the occasion.
- A wary helper sees the trouble coming and offers a smarter compromise.

Narrative instruments:
- Humor: the hero thinks and speaks in a comic, oversized way.
- Foreshadowing: small details hint at the later fix.
- Inner monologue: the hero's private thoughts appear in the story.

Style:
- Tall tale, but grounded in state changes and causal turns.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    traits: list = field(default_factory=list)
    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        male = {"boy", "man", "father", "dad", "uncle", "grandfather"}
        female = {"girl", "woman", "mother", "mom", "aunt", "grandmother"}
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    name: str
    indoor: bool = False
    affords: set[str] = field(default_factory=set)
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
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
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
    genders: set[str] = field(default_factory=lambda: {"boy", "girl"})
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.zone: set[str] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.weather: str = ""

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    task: str
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


SETTINGS = {
    "townhall": Place("the town hall", indoor=True, affords={"week"}),
    "barber": Place("the barber shop", indoor=True, affords={"week"}),
    "porch": Place("the front porch", indoor=False, affords={"week"}),
}

TASKS = {
    "week": Task(
        id="week",
        verb="get ready for Professional Week",
        gerund="getting ready for Professional Week",
        rush="dash off half-dressed to the hall",
        mess="rumpled",
        soil="all rumpled",
        zone={"torso", "hair", "feet"},
        keyword="professional",
        tags={"professional", "week", "humor", "foreshadowing"},
    )
}

PRIZES = {
    "coat": Prize("coat", "a clean little coat", "coat", "torso"),
    "tie": Prize("tie", "a bright necktie", "tie", "torso"),
    "shoes": Prize("shoes", "polished shoes", "shoes", "feet", plural=True),
}

GEAR = [
    Gear(
        id="comb",
        label="a fine comb",
        covers={"hair"},
        guards={"rumpled"},
        prep="comb down your hair first",
        tail="came back with the comb tucked in a vest pocket",
    ),
    Gear(
        id="vest",
        label="a tidy vest",
        covers={"torso"},
        guards={"rumpled"},
        prep="put on a tidy vest over that shirt",
        tail="went to fetch the tidy vest",
    ),
    Gear(
        id="polish",
        label="shoe polish",
        covers={"feet"},
        guards={"rumpled"},
        prep="shine those shoes till they could wink at a moonbeam",
        tail="came back with the shoes shining like little black mirrors",
    ),
]

NAMES = ["Milo", "Jeb", "Cal", "Otis", "Ned", "Eli", "Bo"]
TRAITS = ["spirited", "cheerful", "stubborn", "lively", "curious"]


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            for prize_id in PRIZES:
                if prize_at_risk(_safe_lookup(TASKS, task_id), _safe_lookup(PRIZES, prize_id)):
                    out.append((place, task_id, prize_id))
    return out


def prize_at_risk(task: Task, prize: Prize) -> bool:
    return prize.region in task.zone


def select_gear(task: Task, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if prize.region in gear.covers and task.mess in gear.guards:
            return gear
    return None


def predict_mess(world: World, hero: Entity, task: Task, prize_id: str) -> dict:
    sim = world.copy()
    _do_task(sim, sim.get(hero.id), task, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": bool(prize.meters["dirty"] >= THRESHOLD)}


def _do_task(world: World, actor: Entity, task: Task, narrate: bool = True) -> None:
    world.zone = set(task.zone)
    actor.meters[task.mess] += 1
    actor.memes["joy"] += 1
    for item in world.worn_items(actor):
        if item.protective:
            continue
        if item.region in world.zone and not world.covered(actor, item.region):
            sig = ("soak", item.id, task.id)
            if sig not in world.fired:
                world.fired.add(sig)
                item.meters["dirty"] += 1
                item.meters[task.mess] += 1
                if narrate:
                    world.say(f"{actor.pronoun('possessive').capitalize()} {item.label} got rumpled.")
    if narrate:
        world.say(f"{actor.pronoun().capitalize()} made a little trouble for tidy clothes.")


def tell(place: Place, task: Task, prize_cfg: Prize, hero_name: str, hero_gender: str, helper_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name, traits=[trait]))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label=f"the {helper_type}"))
    prize = world.add(Entity(
        id=prize_cfg.label,
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    prize.worn_by = hero.id

    world.say(f"{hero.id} was a {trait} youngster who liked to look as sharp as a whistle on Sunday morning.")
    world.say(f"For all that, {hero.id} still had a soft spot for {task.keyword}, because Professional Week had come to town like a brass band on skates.")
    world.say(f"{hero.id} wore {prize.phrase} and wondered if that would be professional enough.")

    world.para()
    world.say(f"On the eve of the week, {hero.id} stood near {place.name} and looked at {prize.phrase}.")
    world.say(f"In {hero.pronoun('possessive')} head, a little thought whispered: \"If I show up looking like a barn owl in Sunday shoes, everybody will know it.\"")
    world.say(f"Then {helper_type} {helper.id.lower()} noticed the shine of {prize.label} and the worry in {hero.id}'s eyes, which was the sort of clue that can wag its tail before the dog even barks.")

    world.para()
    hero.memes["desire"] += 1
    world.say(f"{hero.id} wanted to {task.verb}, but {hero.pronoun('possessive')} {helper_type} held up a hand.")
    world.say(f"\"You can be fancy and still be yourself,\" {helper.id.lower()} said, \"but not with that outfit half-wrestling a mud puddle.\"")
    world.say(f"{hero.id} thought, \"Well, that's a fair crack of the whip. I did leave a streak of last week on my collar.\"")

    if predict_mess(world, hero, task, prize.id)["soiled"]:
        world.say(f"\"{hero.id}, you'll get {prize.label} all {task.soil},\" said {helper.id.lower()}.")
        hero.memes["defiance"] += 1
        world.say(f"{hero.id} nearly objected, but then the foreshadowing came home: a crooked comb on the shelf, a vest on the hook, and a shoe brush under the bench, each one waiting like a quiet little prophecy.")
        gear = select_gear(task, prize)
        if gear is None:
            gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
        item = world.add(Entity(
            id=gear.id,
            type="gear",
            label=gear.label,
            owner=hero.id,
            caretaker=helper.id,
            protective=True,
            covers=set(gear.covers),
            plural=gear.plural,
        ))
        item.worn_by = hero.id
        world.say(f"{helper.id.lower()} smiled and offered a compromise: {gear.prep}.")
        world.say(f"{hero.id} felt the laugh coming before the grin did, because the plan was so sensible it could have taught manners to a barn cat.")
        hero.memes["joy"] += 1
        hero.memes["conflict"] = 0
        world.say(f"{hero.id} agreed, and {gear.tail}.")
        world.say(f"At last, {hero.id} was {task.gerund}, looking neat as a pin and twice as bright, while {prize.phrase} stayed clean as a whistle.")
    else:
        world.say(f"To everybody's surprise, the clothes were safe already, but that never stopped a tall tale from taking a bow.")

    world.facts.update(hero=hero, helper=helper, prize=prize, task=task, gear=gear if 'gear' in locals() else None, place=place)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, task, prize = f["hero"], f["task"], f["prize"]
    return [
        f'Write a tall-tale story for children about {hero.id} trying to {task.verb} during Professional Week.',
        f'Write a funny story where {hero.id} worries about looking professional while wearing {prize.phrase}.',
        f"Tell a story with humor, foreshadowing, and inner monologue about a child who wants to be smartened up for a week-long town event.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, prize, task = f["hero"], f["helper"], f["prize"], f["task"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do for Professional Week?",
            answer=f"{hero.id} wanted to {task.verb}, but {hero.pronoun('possessive')} clothes needed some smartening first.",
        ),
        QAItem(
            question=f"Why was {helper.label} worried about {prize.label}?",
            answer=f"{helper.label.capitalize()} worried that {prize.phrase} would get {task.soil} if {hero.id} rushed off in the wrong outfit.",
        ),
        QAItem(
            question=f"What did {hero.id} think to himself before the compromise?",
            answer=f"{hero.id} thought that if he went out looking like a barn owl in Sunday shoes, everybody would notice. That inner monologue made him slow down and listen.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did {gear.label} help {hero.id}?",
                answer=f"{gear.label.capitalize()} helped by covering the right part of the outfit so {hero.id} could {task.verb} without ruining {prize.label}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to look professional?",
            answer="Looking professional means your clothes and manners seem neat, careful, and ready for an important event.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when the story gives little hints about what will happen later.",
        ),
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the private talking a character does inside their own head.",
        ),
        QAItem(
            question="Why can humor help in a story?",
            answer="Humor can make a story feel friendly and lively, even when the character is worried.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="townhall", task="week", prize="coat", name="Milo", gender="boy", helper="aunt", trait="spirited"),
    StoryParams(place="barber", task="week", prize="tie", name="Jeb", gender="boy", helper="uncle", trait="cheerful"),
    StoryParams(place="porch", task="week", prize="shoes", name="Ivy", gender="girl", helper="aunt", trait="curious"),
]


def explain_rejection(task: Task, prize: Prize) -> str:
    if not prize_at_risk(task, prize):
        return f"(No story: {prize.label} would not be in danger during {task.gerund}.)"
    return f"(No story: this domain expects a neat fix for a {prize.label} at risk during Professional Week.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: a {_safe_lookup(PRIZES, prize_id).label} is not typically paired with {gender} here; try {ok}.)"


ASP_RULES = r"""
prize_at_risk(T, P) :- task(T), splashes(T, R), worn_on(P, R).
protects(G, T, P) :- gear(G), prize_at_risk(T, P), covers(G, R), worn_on(P, R), guards(G, M), mess_of(T, M).
has_fix(T, P) :- protects(_, T, P).
valid(Place, T, P) :- affords(Place, T), prize_at_risk(T, P), has_fix(T, P).
valid_story(Place, T, P, Gender) :- valid(Place, T, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if place.indoor:
            lines.append(asp.fact("indoor", pid))
        for t in sorted(place.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, task in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("mess_of", tid, task.mess))
        for r in sorted(task.zone):
            lines.append(asp.fact("splashes", tid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
        for g in sorted(prize.genders):
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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
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
    ap = argparse.ArgumentParser(description="Tall-tale storyworld: smarten up for Professional Week.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["boy", "girl"])
    ap.add_argument("--helper", choices=["aunt", "uncle"])
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
    if getattr(args, "task", None) and getattr(args, "prize", None):
        t, p = _safe_lookup(TASKS, getattr(args, "task", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not prize_at_risk(t, p):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.genders))
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in prize.genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        task=task,
        prize=prize_id,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        gender=gender,
        helper=getattr(args, "helper", None) or rng.choice(["aunt", "uncle"]),
        trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.helper, params.trait)
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
        for place, task, prize in triples:
            genders = sorted(g for (pl, ta, pr, g) in stories if (pl, ta, pr) == (place, task, prize))
            print(f"  {place:10} {task:6} {prize:8}  [{', '.join(genders)}]")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.task} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
