#!/usr/bin/env python3
"""
storyworlds/worlds/wreath_senator_bachelor_flashback_fairy_tale.py
===================================================================

A small fairy-tale storyworld about a bachelor senator, a wreath, and a
flashback that changes how a lonely evening ends.

Premise:
- The senator is proud and busy, but a wreath from the old garden stirs a
  memory.
- A wind-heavy road threatens the wreath on the way to the feast.
- A flashback reveals why the wreath matters, and the senator chooses a wiser
  way to carry it.

The world tracks both physical meters and emotional memes:
- wreath.freshness, wreath.dryness, wreath.safeness
- senator.pride, senator.loneliness, senator.kindness, senator.memory
- helper.gentleness, helper.workload

The story is deliberately tiny and classical: setup, flashback turn, and a
resolution image that proves what changed.
"""

from __future__ import annotations

import argparse
import copy
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

# ---------------------------------------------------------------------------
# Core domain model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    bachelor: object | None = None
    gear: object | None = None
    helper: object | None = None
    senator: object | None = None
    wreath: object | None = None
    def __post_init__(self) -> None:
        if not self.label:
            self.label = self.type
        if not self.phrase:
            self.phrase = self.label

    def pronoun(self, case: str = "subject") -> str:
        female = {"queen", "girl", "woman", "mother"}
        male = {"senator", "bachelor", "boy", "man", "father"}
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
    outdoor: bool
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    weather: str
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
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.weather: str = ""
        self.windy: bool = False

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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        clone.windy = self.windy
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "garden_gate": Setting(place="the garden gate", outdoor=True, affords={"walk", "ride"}),
    "castle_road": Setting(place="the castle road", outdoor=True, affords={"walk", "ride"}),
    "feast_hall": Setting(place="the feast hall", outdoor=False, affords={"carry"}),
}

ACTIVITIES = {
    "walk": Activity(
        id="walk",
        verb="walk to the feast",
        gerund="walking to the feast",
        rush="hurry down the road",
        risk="the wind could ruffle the wreath and shake its ribbon loose",
        weather="windy",
        keyword="flashback",
        tags={"wreath", "wind", "flashback"},
    ),
    "ride": Activity(
        id="ride",
        verb="ride to the feast",
        gerund="riding to the feast",
        rush="climb into the cart",
        risk="the bumps could jostle the wreath and bend its flowers",
        weather="windy",
        keyword="flashback",
        tags={"wreath", "wind", "flashback"},
    ),
    "carry": Activity(
        id="carry",
        verb="carry the wreath inside",
        gerund="carrying the wreath inside",
        rush="lift the wreath high",
        risk="the hall is safe, so the wreath stays fresh",
        weather="calm",
        keyword="flashback",
        tags={"wreath", "flashback"},
    ),
}

PRIZES = {
    "wreath": Prize(
        label="wreath",
        phrase="a green wreath braided with white flowers",
        type="wreath",
        region="hands",
    ),
}

GEAR = [
    Gear(
        id="wicker_box",
        label="a wicker box",
        prep="place the wreath in a wicker box first",
        tail="set the wicker box softly on the cart",
        guards={"windy", "bumpy"},
        covers={"hands"},
    ),
    Gear(
        id="silk_wrap",
        label="a silk wrap",
        prep="wrap the wreath in silk first",
        tail="tuck the silk wrap around the wreath",
        guards={"windy"},
        covers={"hands"},
    ),
]

NAMES = ["Alaric", "Bram", "Cedric", "Dorian", "Edwin", "Falk", "Gavin"]
HELPERS = ["mason", "baker", "gardener", "page"]
TRAITS = ["quiet", "proud", "gentle", "lonely", "fair", "patient"]


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------

def wreath_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region == "hands" and activity.id in {"walk", "ride"}


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.keyword in gear.guards or activity.weather in gear.guards or "windy" in gear.guards:
            if prize.region in gear.covers:
                return gear
    return None


def predict_damage(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict[str, bool]:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"damaged": bool(prize.meters.get("bent", 0) >= THRESHOLD or prize.meters.get("damp", 0) >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    world.windy = activity.weather == "windy"
    actor.memes["resolve"] = actor.memes.get("resolve", 0) + 1
    if activity.id in {"walk", "ride"}:
        for ent in list(world.entities.values()):
            if ent.id == "wreath":
                if world.windy and not any(g.id in world.entities and world.entities[g.id].carried_by == actor.id for g in GEAR):
                    ent.meters["bent"] = ent.meters.get("bent", 0) + 1
                    ent.meters["damp"] = ent.meters.get("damp", 0) + 1
                    ent.memes["worry"] = ent.memes.get("worry", 0) + 1
    if narrate:
        world.say(f"They began {activity.gerund}.")


def flashback(world: World, senator: Entity, wreath: Entity) -> None:
    senator.memes["memory"] = senator.memes.get("memory", 0) + 1
    senator.memes["kindness"] = senator.memes.get("kindness", 0) + 1
    world.say(
        f"As he held the wreath, {senator.id} had a flashback: when he was a small boy, "
        f"his grandmother said, 'A wreath is a circle because welcome should not have a sharp end.'"
    )
    world.say(
        f"He remembered how the old garden smelled after rain, and how the flowers had looked like a tiny crown for anyone lonely enough to need one."
    )


def offer_help(world: World, helper: Entity, senator: Entity, prize: Entity, gear: Gear) -> None:
    helper.memes["gentleness"] = helper.memes.get("gentleness", 0) + 1
    world.say(
        f"A kind {helper.type} stepped forward and said, 'We can {gear.prep}.'"
    )


def accept_help(world: World, senator: Entity, prize: Entity, gear: Gear) -> None:
    senator.memes["pride"] = max(0.0, senator.memes.get("pride", 0) - 1)
    senator.memes["loneliness"] = max(0.0, senator.memes.get("loneliness", 0) - 1)
    prize.meters["safe"] = prize.meters.get("safe", 0) + 1
    world.say(
        f"{senator.id} nodded at once. He chose the careful way, because the wreath was not only a pretty ring of leaves; it was a memory he meant to keep whole."
    )
    world.say(
        f"They {gear.tail}, and the road forgot its roughness before the flowers could lose a petal."
    )


def ending(world: World, senator: Entity, prize: Entity) -> None:
    world.say(
        f"By the time they reached the hall, the wreath was still fresh, {senator.id}'s heart was less lonely, and the feast felt warmer for everyone who entered."
    )


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------

def tell(setting: Setting, activity: Activity, prize_cfg: Prize, helper_name: str = "Tobin") -> World:
    world = World(setting)
    world.weather = activity.weather

    senator = world.add(Entity(
        id="Senator",
        kind="character",
        type="senator",
        label="the senator",
        traits=["bachelor", "proud", "quiet"],
    ))
    bachelor = world.add(Entity(
        id="Bachelor",
        kind="character",
        type="bachelor",
        label="the bachelor",
        traits=["lonely", "gentle"],
    ))
    helper = world.add(Entity(
        id=helper_name,
        kind="character",
        type=random.choice(HELPERS),
        label=f"the {random.choice(HELPERS)}",
    ))
    wreath = world.add(Entity(
        id="wreath",
        type="wreath",
        label="wreath",
        phrase=prize_cfg.phrase,
        owner=senator.id,
        caretaker=helper.id,
        meters={"fresh": 1.0},
        memes={"hope": 1.0},
    ))
    gear = world.add(Entity(
        id="wicker_box",
        type="gear",
        label="a wicker box",
        phrase="a wicker box",
        carried_by=helper.id,
    ))

    # Act 1: setup
    world.say(
        f"In a small fair kingdom, there lived a bachelor senator named {senator.id}. He was proud enough to sit straight, but lonely enough to notice when the moon rose early."
    )
    world.say(
        f"One morning, the {bachelor.type} brought him {prize_cfg.phrase}. The wreath smelled of leaves, and it made the senator think of a door opened kindly."
    )
    world.para()

    # Act 2: tension and flashback
    world.say(
        f"That evening, the senator had to {activity.verb} to the feast hall, and the road was windy."
    )
    world.say(
        f"'{activity.risk},' said the helper, glancing at the sky."
    )
    flashback(world, senator, wreath)
    world.say(
        f"The memory softened his face. He no longer wanted to rush the wreath through the dark."
    )
    world.para()

    # Act 3: resolution
    offer_help(world, helper, senator, wreath, gear)
    accept_help(world, senator, wreath, gear)
    ending(world, senator, wreath)

    world.facts.update(
        senator=senator,
        bachelor=bachelor,
        helper=helper,
        wreath=wreath,
        activity=activity,
        setting=setting,
        gear=gear,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    activity: Activity = _safe_fact(world, f, "activity")
    return [
        f"Write a gentle fairy tale about a bachelor senator, a wreath, and a flashback that helps him make a wise choice.",
        f"Tell a short story where someone named the senator wants to {activity.verb} but remembers something from the past.",
        f"Write a child-friendly fairy tale that includes the word 'flashback' and ends with a wreath staying fresh.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    senator: Entity = _safe_fact(world, f, "senator")
    bachelor: Entity = _safe_fact(world, f, "bachelor")
    helper: Entity = _safe_fact(world, f, "helper")
    wreath: Entity = _safe_fact(world, f, "wreath")
    activity: Activity = _safe_fact(world, f, "activity")
    setting: Setting = _safe_fact(world, f, "setting")

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {senator.label}, a bachelor senator who learns to protect a special wreath.",
        ),
        QAItem(
            question=f"What did the senator remember in the flashback?",
            answer=f"He remembered his grandmother's gentle words about wreaths meaning welcome, so he became more careful.",
        ),
        QAItem(
            question=f"Why was the road a problem when he tried to {activity.verb}?",
            answer=f"The road was windy, and the wind could shake the wreath and spoil its flowers.",
        ),
        QAItem(
            question=f"How did the helper solve the problem?",
            answer=f"The helper offered a wicker box, so the wreath could travel safely to {setting.place}.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"The wreath stayed fresh, and the senator felt less lonely and more kind by the time the feast began.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wreath?",
            answer="A wreath is a круг? No, a wreath is a ring of leaves, flowers, or branches often used for decoration or welcome.",
        ),
        QAItem(
            question="What is a senator?",
            answer="A senator is a person who helps make decisions for a kingdom or a country.",
        ),
        QAItem(
            question="What is a bachelor?",
            answer="A bachelor is a grown-up man who is not married.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly tells about something that happened before the present moment.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", ""]
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
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        out.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting(garden_gate).
setting(castle_road).
setting(feast_hall).
outdoor(garden_gate).
outdoor(castle_road).
affords(garden_gate,walk).
affords(garden_gate,ride).
affords(castle_road,walk).
affords(castle_road,ride).
affords(feast_hall,carry).

activity(walk).
activity(ride).
activity(carry).
weather(walk,windy).
weather(ride,windy).
weather(carry,calm).
splashes(walk,hands).
splashes(ride,hands).

prize(wreath).
worn_on(wreath,hands).

gear(wicker_box).
guards(wicker_box,windy).
covers(wicker_box,hands).
gear(silk_wrap).
guards(silk_wrap,windy).
covers(silk_wrap,hands).

wreath_at_risk(A,P) :- splashes(A,R), worn_on(P,R), activity(A).

has_fix(A,P) :- wreath_at_risk(A,P), gear(G), guards(G,windy), covers(G,hands).

valid_story(Place,A,P) :- affords(Place,A), wreath_at_risk(A,P), has_fix(A,P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if not setting.outdoor:
            lines.append(asp.fact("indoor", sid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("weather", aid, act.weather))
        for tag in sorted(act.tags):
            lines.append(asp.fact("tag", aid, tag))
        if aid in {"walk", "ride"}:
            lines.append(asp.fact("splashes", aid, "hands"))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, g))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            if not wreath_at_risk(act, PRIZES["wreath"]):
                continue
            if select_gear(act, PRIZES["wreath"]) is None:
                continue
            combos.append((place, act_id, "wreath"))
    return sorted(combos)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("only in Python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "castle_road"
    activity: str = "walk"
    prize: str = "wreath"
    seed: Optional[int] = None
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


CURATED = [
    StoryParams(place="castle_road", activity="walk", prize="wreath"),
    StoryParams(place="garden_gate", activity="ride", prize="wreath"),
    StoryParams(place="feast_hall", activity="carry", prize="wreath"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy tale storyworld: a bachelor senator, a wreath, and a flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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
    choices = [c for c in valid_combos()
               if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
               and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
               and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(choices)
    return StoryParams(place=place, activity=activity, prize=prize)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize))
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for place, act, prize in combos:
            print(f"  {place:12} {act:8} {prize}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
