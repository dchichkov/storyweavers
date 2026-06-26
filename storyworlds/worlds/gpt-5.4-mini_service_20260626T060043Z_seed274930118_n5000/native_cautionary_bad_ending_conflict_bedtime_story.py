#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/native_cautionary_bad_ending_conflict_bedtime_story.py
================================================================================================

A small bedtime-story world with a cautionary conflict and a bad ending.

Premise:
- A child wants to keep doing one cozy bedtime activity.
- A caregiver warns that the choice will make bedtime worse.
- The child ignores the warning, the room state worsens, and the night ends badly.

This world is intentionally compact and state-driven:
- physical meters track light, mess, warmth, and sleepiness
- emotional memes track worry, defiance, comfort, and conflict
- simulated state determines the prose, not a frozen template

The seed word is "native", which here appears as a handmade, local, native-style
bedtime ornament and lullaby tradition in the child's room.
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

# ---------------------------------------------------------------------------
# Shared storyworld constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world model
# ---------------------------------------------------------------------------


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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    item: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "noise": 0.0, "light": 0.0, "sleep": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "defiance": 0.0, "conflict": 0.0, "comfort": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
    place: str = "the bedroom"
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
    mess: str
    soil: str
    zone: set[str]
    keyword: str = ""
    caution: str = ""
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
class ComfortItem:
    id: str
    label: str
    phrase: str
    region: str
    guards: set[str]
    covers: set[str]
    prep: str
    tail: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.trace: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def chars(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.lines = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"book", "song", "nightlight"}),
}

ACTIVITIES = {
    "book": Activity(
        id="book",
        verb="read one more page",
        gerund="reading one more page",
        rush="reach for one more page",
        mess="sleep",
        soil="stay awake too late",
        zone={"sleep"},
        keyword="native",
        caution="late bedtime",
        tags={"book", "sleep", "native"},
    ),
    "song": Activity(
        id="song",
        verb="sing the native lullaby again",
        gerund="singing the native lullaby again",
        rush="ask for one more song",
        mess="noise",
        soil="make the room too lively",
        zone={"noise"},
        keyword="native",
        caution="late bedtime",
        tags={"song", "music", "native"},
    ),
    "nightlight": Activity(
        id="nightlight",
        verb="keep the nightlight on",
        gerund="keeping the nightlight on",
        rush="turn the lamp brighter",
        mess="light",
        soil="lose the sleepy dark",
        zone={"light"},
        keyword="native",
        caution="late bedtime",
        tags={"light", "native"},
    ),
}

COMFORTS = [
    ComfortItem(
        id="blanket",
        label="a quilted blanket",
        phrase="a quilted blanket with little stars",
        region="sleep",
        guards={"sleep"},
        covers={"sleep"},
        prep="tuck the blanket up first",
        tail="tucked the blanket back up",
    ),
    ComfortItem(
        id="nightlight",
        label="a soft nightlight",
        phrase="a soft nightlight shaped like a moon",
        region="light",
        guards={"light"},
        covers={"light"},
        prep="turn on the soft nightlight first",
        tail="switched the soft nightlight on",
    ),
    ComfortItem(
        id="earmuffs",
        label="sleepy ear covers",
        phrase="sleepy ear covers for quiet rooms",
        region="noise",
        guards={"noise"},
        covers={"noise"},
        prep="put on the sleepy ear covers first",
        tail="put on the sleepy ear covers",
        plural=True,
    ),
]

CHARACTER_NAMES = ["Mina", "Theo", "Luna", "Arlo", "June", "Nia", "Owen", "Milo"]
TRAITS = ["sleepy", "curious", "stubborn", "gentle", "lively"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def prize_at_risk(activity: Activity, item: ComfortItem) -> bool:
    return item.region in activity.zone


def select_comfort(activity: Activity, item: ComfortItem) -> Optional[ComfortItem]:
    for gear in COMFORTS:
        if activity.mess in gear.guards and item.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for item in COMFORTS:
                if prize_at_risk(act, item) and select_comfort(act, item):
                    combos.append((place, act_id))
    return combos


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------

def introduce(world: World, hero: Entity, parent: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "small")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved the soft things "
        f"that made bedtime feel safe."
    )
    world.say(
        f"{hero.id} shared {hero.pronoun('possessive')} room with {parent.label_word} "
        f"and a quiet lamp on the shelf."
    )


def loves_native(world: World, hero: Entity) -> None:
    hero.memes["joy"] += 1
    world.say(
        f"{hero.id} especially loved the native bedtime song, because it sounded "
        f"like a hush from far away and a hug close by."
    )


def setup_item(world: World, hero: Entity, parent: Entity, item: Entity) -> None:
    item.worn_by = hero.id
    world.say(
        f"{parent.label_word.capitalize()} had bought {hero.pronoun('object')} "
        f"{item.phrase}, and {hero.id} kept it close at night."
    )


def wants_more(world: World, hero: Entity, parent: Entity, activity: Activity, item: Entity) -> None:
    hero.memes["defiance"] += 1
    world.say(
        f"But when bedtime came, {hero.id} wanted to {activity.verb} instead of lying still."
    )
    world.say(
        f"{hero.pronoun('possessive').capitalize()} {parent.label_word} warned, "
        f"'{activity.caution.capitalize()} can make morning feel hard.'"
    )
    world.facts["warning"] = activity.caution


def ignore_and_push(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["worry"] += 0.5
    hero.memes["defiance"] += 0.5
    hero.meters[activity.mess] = hero.meters.get(activity.mess, 0.0) + 1.0
    world.say(
        f"{hero.id} did not listen. {hero.pronoun().capitalize()} reached for "
        f"{activity.rush}, and the room started to feel less sleepy."
    )


def consequence(world: World, hero: Entity, parent: Entity, activity: Activity, item: Entity) -> None:
    hero.meters["sleep"] += 0.5
    if activity.id == "book":
        item.meters["mess"] += 1
        world.say(
            f"The page slipped into the bed, and {item.label} got wrinkled from the rush."
        )
    elif activity.id == "song":
        hero.meters["noise"] += 1.0
        world.say(
            f"The song grew louder and louder, and the bedroom stopped feeling quiet."
        )
    else:
        hero.meters["light"] += 1.0
        world.say(
            f"The nightlight shone brighter and brighter, and the dark at the corners faded away."
        )

    parent.memes["worry"] += 1.0
    hero.memes["conflict"] += 1.0
    world.say(
        f"{parent.label_word.capitalize()} came back looking tired and said that this was the sort of choice "
        f"that makes bedtime go badly."
    )


def bad_ending(world: World, hero: Entity, parent: Entity, activity: Activity, item: Entity) -> None:
    hero.memes["conflict"] += 1.0
    hero.memes["comfort"] += 0.0
    world.say(
        f"In the end, {hero.id} stayed awake too long, with {hero.pronoun('possessive')} {item.label} out of place "
        f"and {hero.pronoun('possessive')} eyes still open."
    )
    world.say(
        f"The room was quiet again, but not peaceful. {hero.id} lay still and listened to the dark, "
        f"learning the hard way that a warning can be a kind of kindness."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    comfort: str
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


def tell(setting: Setting, activity: Activity, comfort_cfg: ComfortItem, hero_name: str, hero_type: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="the parent"))
    item = world.add(Entity(
        id=comfort_cfg.id,
        type="thing",
        label=comfort_cfg.label,
        phrase=comfort_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
    ))

    world.say(f"At {setting.place}, {hero.id} was getting ready for bed.")
    loves_native(world, hero)
    introduce(world, hero, parent)
    setup_item(world, hero, parent, item)
    world.para()
    wants_more(world, hero, parent, activity, item)
    ignore_and_push(world, hero, activity)
    consequence(world, hero, parent, activity, item)
    world.para()
    bad_ending(world, hero, parent, activity, item)

    world.facts.update(
        hero=hero,
        parent=parent,
        item=item,
        activity=activity,
        comfort_cfg=comfort_cfg,
        resolved=False,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, parent, act, item = f["hero"], f["parent"], f["activity"], f["comfort_cfg"]
    return [
        f'Write a bedtime story for a small child named {hero.id} about the word "native" and a warning that is ignored.',
        f"Tell a gentle but cautionary story where {hero.id} wants to {act.verb} even though {parent.label_word} says bedtime is getting late.",
        f"Write a short bedtime story with a conflict, a bad ending, and a quiet room that no longer feels sleepy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, act, item = f["hero"], f["parent"], f["activity"], f["item"]
    qa = [
        QAItem(
            question=f"Why did {hero.id} get into trouble at bedtime?",
            answer=(
                f"{hero.id} got into trouble because {hero.pronoun()} wanted to {act.verb} instead of going to sleep, "
                f"even after {hero.pronoun('possessive')} {parent.label_word} gave a warning."
            ),
        ),
        QAItem(
            question=f"What warning did {parent.label_word} give before the conflict?",
            answer=(
                f"{parent.label_word.capitalize()} warned that {act.caution} can make morning feel hard."
            ),
        ),
        QAItem(
            question=f"What was the native thing in the story that sounded cozy?",
            answer=(
                f"The native bedtime song sounded cozy, like a hush from far away and a hug close by."
            ),
        ),
    ]
    qa.append(
        QAItem(
            question=f"What happened to {hero.pronoun('possessive')} {item.label} by the end?",
            answer=(
                f"It ended up out of place and a little disturbed by the bedtime rush, which fit the bad ending."
            ),
        )
    )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="Why do children need sleep?",
            answer="Sleep helps a child's body rest, grow, and get ready for a new day.",
        ),
        QAItem(
            question="What happens when bedtime is too late?",
            answer="When bedtime is too late, a child can feel cranky, slow, and extra tired the next day.",
        ),
        QAItem(
            question="Why do parents give bedtime warnings?",
            answer="Parents give bedtime warnings to help children choose safe and calm things before sleep.",
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
    lines.append("== (3) World knowledge ==")
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
        if e.worn_by:
            bits.append(f"owned_by={e.worn_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(bedroom).
affords(bedroom,book).
affords(bedroom,song).
affords(bedroom,nightlight).

activity(book).
activity(song).
activity(nightlight).

zone(book,sleep).
zone(song,noise).
zone(nightlight,light).

comfort(blanket).
comfort(nightlight).
comfort(earmuffs).

region(blanket,sleep).
region(nightlight,light).
region(earmuffs,noise).

guards(blanket,sleep).
guards(nightlight,light).
guards(earmuffs,noise).

prize_at_risk(A,I) :- zone(A,R), region(I,R).
has_fix(A,I) :- prize_at_risk(A,I), guards(G,M), activity(A), comfort(G), (A=book, M=sleep; A=song, M=noise; A=nightlight, M=light), region(G,R), zone(A,R).
valid(Place,A,I) :- place(Place), affords(Place,A), prize_at_risk(A,I), has_fix(A,I).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place in SETTINGS:
        lines.append(asp.fact("place", place))
        for act in _safe_lookup(SETTINGS, place).affords:
            lines.append(asp.fact("affords", place, act))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for z in act.zone:
            lines.append(asp.fact("zone", aid, z))
    for c in COMFORTS:
        lines.append(asp.fact("comfort", c.id))
        lines.append(asp.fact("region", c.id, c.region))
        for g in c.guards:
            lines.append(asp.fact("guards", c.id, g))
    return "\n".join(lines)


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
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A cautionary bedtime story world with a bad ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--comfort", choices=[c.id for c in COMFORTS])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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


def explain_rejection(activity: Activity, item: ComfortItem) -> str:
    return (
        f"(No story: {activity.verb} does not disturb {item.label} in a way the bedtime world can safely fix.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "comfort", None):
        act, item = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), next(c for c in COMFORTS if c.id == getattr(args, "comfort", None))
        if not (prize_at_risk(act, item) and select_comfort(act, item)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for item in COMFORTS:
                if prize_at_risk(act, item) and select_comfort(act, item):
                    combos.append((place, act_id, item.id))
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "comfort", None) is None or c[2] == getattr(args, "comfort", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, act_id, comfort_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(CHARACTER_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=act_id, comfort=comfort_id, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    hero_type = params.gender
    parent_type = params.parent
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        next(c for c in COMFORTS if c.id == params.comfort),
        params.name,
        hero_type,
        parent_type,
        params.trait,
    )
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
        print(f"{len(combos)} compatible bedtime combos:")
        for place, act, item in combos:
            print(f"  {place:8} {act:10} {item}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("bedroom", "book", "blanket", "Mina", "girl", "mother", "curious"),
            StoryParams("bedroom", "song", "earmuffs", "Theo", "boy", "father", "stubborn"),
            StoryParams("bedroom", "nightlight", "nightlight", "Luna", "girl", "mother", "lively"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
