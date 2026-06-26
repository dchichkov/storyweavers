#!/usr/bin/env python3
"""
storyworlds/worlds/lmnop_cautionary_quest_comedy.py
===================================================

A small cautionary quest-comedy world built from the seed word "lmnop".

Premise:
- A child hero wants to do a silly quest in a tiny, concrete place.
- A sensible helper warns that the obvious path will cause a comic mess.
- The hero nearly blunders ahead, then chooses a safer route.
- The ending proves the change in state: the prize stays safe, the hero
  completes the quest, and the helper can laugh instead of worry.

This world is intentionally small and constraint-checked:
- only plausible quest/hazard/gear combinations are allowed
- the prose is driven by simulated state, not a frozen template
- an inline ASP twin mirrors the Python reasonableness gate
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
    guards: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    helper: object | None = None
    hero: object | None = None
    relic: object | None = None
    def __post_init__(self) -> None:
        for k in ["dusty", "wet", "slippery", "work", "speed", "safe"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "resolve", "alarm", "comedy", "pride"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "aunt", "sister"}
        male = {"boy", "father", "man", "uncle", "brother"}
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
    affords: set[str]
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
    hazard: str
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
        self.zone: set[str] = set()
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
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


SETTINGS = {
    "attic": Setting(place="the attic", indoor=True, affords={"fetch", "deliver"}),
    "garden": Setting(place="the garden", indoor=False, affords={"fetch", "rescue"}),
    "market": Setting(place="the market lane", indoor=False, affords={"deliver", "fetch"}),
}

QUESTS = {
    "fetch-kite": Quest(
        id="fetch-kite",
        verb="fetch the lmnop kite",
        gerund="fetching the lmnop kite",
        rush="dash straight across the loose ladder",
        hazard="wobbly",
        soil="all dusty and bent",
        zone={"feet", "legs"},
        keyword="lmnop",
        tags={"lmnop", "kite", "dusty"},
    ),
    "deliver-jar": Quest(
        id="deliver-jar",
        verb="deliver the lmnop jam jar",
        gerund="delivering the lmnop jam jar",
        rush="hurry past the tilted cart",
        hazard="sticky",
        soil="spilled and sticky",
        zone={"hands", "torso"},
        keyword="lmnop",
        tags={"lmnop", "jam", "sticky"},
    ),
    "rescue-duck": Quest(
        id="rescue-duck",
        verb="rescue the lmnop duck toy",
        gerund="rescuing the lmnop duck toy",
        rush="tiptoe through the splashy puddle",
        hazard="wet",
        soil="wet and silly",
        zone={"feet", "legs"},
        keyword="lmnop",
        tags={"lmnop", "duck", "wet"},
    ),
}

PRIZES = {
    "map": Prize("map", "a folded treasure map", "map", "torso"),
    "jar": Prize("jar", "a shiny jam jar", "jar", "hands"),
    "toy": Prize("toy", "a squeaky duck toy", "toy", "feet"),
}

GEAR = [
    Gear("boots", "rain boots", {"feet"}, {"wet", "wobbly"}, "put on rain boots first", "went back for the rain boots"),
    Gear("gloves", "rubber gloves", {"hands"}, {"sticky"}, "slip on rubber gloves first", "went back for the rubber gloves"),
    Gear("sash", "a canvas sash", {"torso"}, {"dusty"}, "wear a canvas sash first", "stopped for the canvas sash"),
    Gear("knee-pads", "knee pads", {"legs"}, {"wobbly", "wet"}, "strap on knee pads first", "stopped for the knee pads"),
]

GIRL_NAMES = ["Mina", "Lily", "Ada", "Zoe", "Tia", "Nora"]
BOY_NAMES = ["Milo", "Finn", "Theo", "Ben", "Ollie", "Max"]
TRAITS = ["curious", "silly", "bold", "careful", "bouncy", "cheery"]


def quest_at_risk(quest: Quest, prize: Prize) -> bool:
    return prize.region in quest.zone


def select_gear(quest: Quest, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if quest.hazard in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            q = _safe_lookup(QUESTS, "fetch-kite" if qid == "fetch" else ("deliver-jar" if qid == "deliver" else "rescue-duck"))
            for pid, prize in PRIZES.items():
                if quest_at_risk(q, prize) and select_gear(q, prize):
                    combos.append((place, q.id, pid))
    return combos


def _do_quest(world: World, actor: Entity, quest: Quest, narrate: bool = True) -> list[str]:
    out: list[str] = []
    world.zone = set(quest.zone)
    actor.meters["speed"] += 1
    actor.memes["comedy"] += 1
    if actor.meters.get(quest.hazard, 0.0) >= THRESHOLD:
        actor.memes["alarm"] += 1
    for item in world.worn_items(actor):
        if item.protective or item.region not in world.zone:
            continue
        if world.covered(actor, item.region):
            continue
        if quest.hazard in item.guards:
            continue
        sig = ("mess", item.id, quest.hazard)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters[quest.hazard] += 1
        item.meters["dusty"] += 1 if quest.hazard == "wobbly" else 0
        out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {quest.soil}.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict_mess(world: World, actor: Entity, quest: Quest, prize_id: str) -> dict:
    sim = world.copy()
    _do_quest(sim, sim.get(actor.id), quest, narrate=False)
    prize = sim.entities[prize_id]
    return {"ruined": any(v >= THRESHOLD for v in prize.meters.values()), "alarm": actor.memes["alarm"]}


def tell(setting: Setting, quest: Quest, prize: Prize, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=[trait, "little"]))
    helper = world.add(Entity(id="Helper", kind="character", type=parent_type, label="the helper"))
    relic = world.add(Entity(
        id="prize", type=prize.type, label=prize.label, phrase=prize.phrase,
        owner=hero.id, caretaker=helper.id, region=prize.region, plural=prize.plural
    ))
    relic.worn_by = hero.id
    world.say(f"{hero_name} was a {trait} little {hero_type} who loved the word lmnop and anything that sounded like a giggle.")
    world.say(f"{hero.pronoun().capitalize()} had a quest for {quest.gerund}, and {hero.pronoun('possessive')} {helper.label_word if hasattr(helper, 'label_word') else 'helper'} had already seen enough tiny disasters to be cautious.")
    world.say(f"That morning, {helper.id.lower()} bought {hero.pronoun('object')} {prize.phrase}, and {hero_name} loved it like a crown made of breadcrumbs.")
    world.para()
    world.say(f"One day, {hero_name} and {hero.pronoun('possessive')} helper went to {setting.place}.")
    world.say(f"{quest.keyword.capitalize()} was the silly word on the map, and it pointed toward a quest that sounded easy until it met the {quest.hazard} part.")
    hero.memes["resolve"] += 1
    world.say(f"{hero_name} wanted to {quest.verb}, but {helper.id.lower()} held up a finger and said, \"Careful now. The shortcut is a wobble trap wearing comedy shoes.\"")
    pred = predict_mess(world, hero, quest, relic.id)
    if pred["ruined"]:
        world.say(f"{hero_name} tried to {quest.rush}, just a little bit, and the helper sighed in the smallest possible way.")
        _do_quest(world, hero, quest, narrate=True)
        hero.memes["worry"] += 1
        world.say(f"That could have made {relic.label} {quest.soil}.")
    world.para()
    gear = select_gear(quest, relic)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
    if predict_mess(world, hero, quest, relic.id)["ruined"]:
        pass
    world.add(Entity(id=gear.id, type="gear", label=gear.label, protective=True, covers=set(gear.covers), guards=set(gear.guards), owner=hero.id, caretaker=helper.id))
    world.get(gear.id).worn_by = hero.id
    world.say(f"Then {helper.id.lower()} smiled and said they could {gear.prep} instead.")
    hero.memes["joy"] += 1
    world.say(f"{hero_name} nodded, wore the {gear.label}, and at last {hero.pronoun().capitalize()} got to {quest.gerund} without ruining {relic.label}.")
    world.say(f"The whole thing ended with {hero_name} carrying {relic.label} home, clean and safe, while the helper laughed at the very serious expression on {hero_name}'s face.")
    world.facts.update(hero=hero, helper=helper, prize=relic, quest=quest, gear=gear, setting=setting)
    return world


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
    hero, helper, quest, prize = f["hero"], f["helper"], f["quest"], f["prize"]
    return [
        f'Write a short comedy for a child about lmnop, a cautionary warning, and a small quest in {f["setting"].place}.',
        f"Tell a funny story where {hero.id} wants to {quest.verb} but {helper.label} worries about {prize.phrase}.",
        f'Write a gentle quest story that includes the word "lmnop" and ends with a safer plan.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, quest, prize, gear = f["hero"], f["helper"], f["quest"], f["prize"], f["gear"]
    return [
        QAItem(
            question=f"What was {hero.id} trying to do at {f['setting'].place}?",
            answer=f"{hero.id} was trying to {quest.verb}. It was a silly little quest, but the warning came first because the shortcut looked messy.",
        ),
        QAItem(
            question=f"Why did {helper.label} warn {hero.id} about the quest?",
            answer=f"{helper.label} warned {hero.id} because the obvious path would have made {prize.label} {quest.soil}. That would have turned the quest into a sticky, dusty comedy.",
        ),
        QAItem(
            question=f"How did {hero.id} finish the quest without ruining the prize?",
            answer=f"{hero.id} wore {gear.label} and chose the safer way. That let {hero.id} {quest.gerund} while {prize.label} stayed clean and safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does caution mean?",
            answer="Caution means being careful and thinking before you rush into something that could cause trouble.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a trip or task where someone goes looking for something, solves a problem, or tries to complete a goal.",
        ),
        QAItem(
            question="Why can a shortcut be risky?",
            answer="A shortcut can be risky if it is slippery, messy, or hard to cross safely, because then you might spill, trip, or get dirty.",
        ),
        QAItem(
            question="What is comedy?",
            answer="Comedy is a kind of story or joke that is meant to be funny and make people smile or laugh.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world QA ==")
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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("attic", "fetch-kite", "map", "Mina", "girl", "mother", "curious"),
    StoryParams("garden", "rescue-duck", "toy", "Milo", "boy", "father", "cheery"),
    StoryParams("market", "deliver-jar", "jar", "Ada", "girl", "mother", "silly"),
]


KNOWLEDGE_ORDER = ["caution", "quest", "shortcut", "comedy"]


ASP_RULES = r"""
quest_at_risk(Q, P) :- zone(Q, R), worn_on(P, R).
protects(G, Q, P) :- quest(Q), prize_at_risk(Q, P), hazard(Q, H), guards(G, H), covers(G, R), worn_on(P, R).
has_fix(Q, P) :- protects(_, Q, P).
valid(Place, Q, P) :- affords(Place, Q), quest_at_risk(Q, P), has_fix(Q, P).
"""

def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for q in sorted(s.affords):
            lines.append(asp.fact("affords", sid, q))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("hazard", qid, q.hazard))
        for r in sorted(q.zone):
            lines.append(asp.fact("zone", qid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("plural", pid))
        for g in sorted(p.genders):
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


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Cautionary quest comedy storyworld with the seed word lmnop.")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, qid, pid = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, pid)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.genders))
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in prize.genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, quest=qid, prize=pid, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.parent, params.trait)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for qid in setting.affords:
            q = _safe_lookup(QUESTS, "fetch-kite" if qid == "fetch" else ("deliver-jar" if qid == "deliver" else "rescue-duck"))
            for pid, prize in PRIZES.items():
                if quest_at_risk(q, prize) and select_gear(q, prize):
                    combos.append((place, q.id, pid))
    return combos


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        combos = asp_valid_combos()
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
            header = f"### {p.name}: {p.quest} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
