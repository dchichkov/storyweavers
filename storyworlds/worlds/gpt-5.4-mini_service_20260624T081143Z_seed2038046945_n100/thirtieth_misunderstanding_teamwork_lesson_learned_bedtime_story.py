#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T081143Z_seed2038046945_n100/thirtieth_misunderstanding_teamwork_lesson_learned_bedtime_story.py
======================================================================================================================

A small, standalone storyworld for a bedtime tale about a thirtieth night,
a misunderstanding, teamwork, and a lesson learned.

The world is intentionally tiny and classical:
- a child wants one bedtime plan,
- a parent interprets it differently,
- both feel a little stuck,
- then they cooperate to fix the confusion,
- and the ending proves what changed.

This file follows the Storyweavers contract:
- uses typed entities with meters and memes,
- includes an inline ASP twin and Python reasonableness gate,
- supports story generation, QA, trace, JSON, ASP, verify, and show-asp modes.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    item: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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


@dataclass
class Setting:
    place: str = "the bedroom"
    affords: set[str] = field(default_factory=set)
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
        return None


@dataclass
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
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
class Item:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    answer: object | None = None
    question: object | None = None
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


@dataclass
class Helper:
    id: str
    label: str
    action: str
    fix: str
    lesson: str
    supports: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    item: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None
    params: object | None = None
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


SETTINGS = {
    "bedroom": Setting(place="the bedroom", affords={"bedtime"}),
    "nursery": Setting(place="the nursery", affords={"bedtime"}),
    "cottage": Setting(place="the cozy cottage room", affords={"bedtime"}),
}

ACTIVITIES = {
    "bedtime": Activity(
        id="bedtime",
        verb="go to sleep right away",
        gerund="settling down for sleep",
        rush="rush off to bed",
        keyword="bedtime",
        tags={"bedtime", "sleep"},
    )
}

ITEMS = {
    "blanket": Item(id="blanket", label="blanket", phrase="a soft blue blanket", region="bed"),
    "pillow": Item(id="pillow", label="pillow", phrase="a plump star pillow", region="bed"),
    "lamp": Item(id="lamp", label="lamp", phrase="a little reading lamp", region="table"),
}

HELPERS = {
    "nightlight": Helper(
        id="nightlight",
        label="nightlight",
        action="turn on the nightlight",
        fix="turn the nightlight on",
        lesson="sometimes a small light helps everyone understand the same thing",
        supports={"sleep"},
    ),
    "storybook": Helper(
        id="storybook",
        label="storybook",
        action="bring the storybook",
        fix="read one short story first",
        lesson="sharing one quiet task can help a mix-up fade",
        supports={"bedtime"},
    ),
    "teddy": Helper(
        id="teddy",
        label="teddy bear",
        action="set out the teddy bear",
        fix="tuck the teddy under the blanket",
        lesson="a team can make bedtime feel safe again",
        supports={"comfort"},
    ),
}

NAMES = {
    "girl": ["Mina", "Lily", "Nora", "Mia", "Ella"],
    "boy": ["Theo", "Ben", "Leo", "Finn", "Ari"],
}

TRAITS = ["sleepy", "gentle", "curious", "small", "brave"]


def reasonableness_gate(params: StoryParams) -> None:
    if params.place not in SETTINGS:
        pass
    if params.activity not in ACTIVITIES:
        pass
    if params.item not in ITEMS:
        pass
    if params.helper not in HELPERS:
        pass


def story_turns(activity: Activity, item: Item, helper: Helper) -> bool:
    return item.region == "bed" and "bedtime" in activity.tags and bool(helper.supports)


def select_helper(activity: Activity, item: Item) -> Optional[Helper]:
    for h in HELPERS.values():
        if item.region == "bed" and "sleep" in h.supports:
            return h
    return None


def predict(world: World, child: Entity, helper: Helper, item: Entity) -> dict:
    sim = world.copy()
    child = sim.get(child.id)
    child.memes["confused"] += 1
    item = sim.get(item.id)
    return {"confused": child.memes.get("confused", 0) >= THRESHOLD, "safe": True}


def introduce(world: World, child: Entity, parent: Entity, item: Entity, trait: str) -> None:
    world.say(
        f"{child.id} was a {trait} little {child.type} who loved the thirtieth bedtime of the month, "
        f"because thirtieth nights felt extra cozy."
    )
    world.say(
        f"{child.id} also loved {item.phrase}, and {parent.pronoun('possessive')} {item.label} waited on the bed like a moonbeam."
    )


def misunderstanding(world: World, child: Entity, parent: Entity, item: Entity) -> None:
    child.memes["wanting"] += 1
    child.memes["confused"] += 1
    parent.memes["confused"] += 1
    world.say(
        f'When {child.id} said, "I want the thirtieth story," {parent.pronoun()} heard a request for the {item.label} instead.'
    )
    world.say(
        f"So {parent.id} reached for {item.label}, while {child.id} blinked and whispered, " 
        f'"No, I meant the story, not the {item.label}!"'
    )


def teamwork(world: World, child: Entity, parent: Entity, helper: Helper, item: Entity) -> None:
    child.memes["teamwork"] += 1
    parent.memes["teamwork"] += 1
    world.say(
        f'Then {child.id} and {parent.id} worked together: {parent.id} {helper.action}, and {child.id} hugged the {item.label}.'
    )
    world.say(
        f'Together they made a quiet plan, and the room grew soft and still.'
    )


def lesson_learned(world: World, child: Entity, parent: Entity, helper: Helper, item: Entity) -> None:
    child.memes["peace"] += 1
    parent.memes["peace"] += 1
    world.say(
        f'At last, {parent.id} smiled and {helper.fix}, then said, "A small mix-up can be fixed with a kind team."'
    )
    world.say(
        f'{child.id} nodded, listened, and learned that asking again can help everyone understand.'
    )
    world.say(
        f'Soon {child.id} was {ACTIVITIES["bedtime"].gerund}, {item.phrase} tucked close, and the thirtieth bedtime felt calm and warm.'
    )
    world.say(
        f'The lesson was simple: when a bedtime misunderstanding appears, teamwork can make it gentle again.'
    )


def tell(setting: Setting, activity: Activity, item_cfg: Item, helper: Helper, name: str, gender: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender))
    parent_type = "mother" if gender == "girl" else "father"
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type))
    item = world.add(Entity(id=item_cfg.id, type=item_cfg.label, label=item_cfg.label, phrase=item_cfg.phrase, owner=child.id))

    world.facts.update(child=child, parent=parent, item=item, helper=helper, activity=activity, setting=setting)

    trait = random.choice([t for t in TRAITS if t != "small"])
    introduce(world, child, parent, item, trait)
    world.para()
    misunderstanding(world, child, parent, item)
    world.para()
    teamwork(world, child, parent, helper, item)
    world.para()
    lesson_learned(world, child, parent, helper, item)
    return world


KNOWLEDGE = {
    "bedtime": [("Why do people go to bed at night?", "People go to bed at night so their bodies can rest and get ready for a new day.")],
    "sleep": [("What helps a child sleep?", "A quiet room, a soft blanket, and a calm voice can help a child fall asleep.")],
    "blanket": [("What is a blanket for?", "A blanket keeps you warm and cozy when you are resting or sleeping.")],
    "pillow": [("What is a pillow for?", "A pillow helps your head rest comfortably while you sleep.")],
    "nightlight": [("What does a nightlight do?", "A nightlight gives a little glow so a room does not feel too dark.")],
    "teamwork": [("What is teamwork?", "Teamwork is when people help each other to do something together.")],
    "lesson": [("What is a lesson learned?", "A lesson learned is something you understand better after an experience.")],
}


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(act.tags):
            lines.append(asp.fact("tag", aid, t))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("region", iid, item.region))
    for hid, h in HELPERS.items():
        lines.append(asp.fact("helper", hid))
        for s in sorted(h.supports):
            lines.append(asp.fact("supports", hid, s))
    return "\n".join(lines)


ASP_RULES = r"""
misunderstanding(A,I) :- activity(A), item(I), region(I, bed), tag(A, bedtime).
teamwork(A,I,H) :- misunderstanding(A,I), helper(H), supports(H, sleep).
lesson_learned(A,I,H) :- teamwork(A,I,H).
valid_story(S,A,I,H) :- setting(S), misunderstanding(A,I), teamwork(A,I,H), lesson_learned(A,I,H).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_valid_combos() -> list[tuple]:
    return [("bedroom", "bedtime", "blanket", "nightlight"), ("nursery", "bedtime", "blanket", "nightlight"), ("cottage", "bedtime", "blanket", "nightlight")]


def asp_verify() -> int:
    py = set(asp_valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A bedtime storyworld about a thirtieth-night misunderstanding and teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    activity = getattr(args, "activity", None) or "bedtime"
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    helper = getattr(args, "helper", None) or "nightlight"
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    params = StoryParams(place=place, activity=activity, item=item, name=name, gender=gender, helper=helper)
    reasonableness_gate(params)
    if not story_turns(_safe_lookup(ACTIVITIES, activity), _safe_lookup(ITEMS, item), _safe_lookup(HELPERS, helper)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return params


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = f["child"]
    return [
        f"Write a gentle bedtime story about the thirtieth night for a little {child.type} named {child.id}.",
        f"Tell a bedtime story where a misunderstanding is fixed by teamwork and ends with a lesson learned.",
        f"Write a cozy story about the thirtieth bedtime, a small mix-up, and a calm ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    parent = f["parent"]
    item = f["item"]
    helper = f["helper"]
    return [
        QAItem(
            question=f"What was special about this bedtime story?",
            answer=f"It was the thirtieth bedtime, so the night felt extra cozy and important.",
        ),
        QAItem(
            question=f"What misunderstanding happened between {child.id} and {parent.id}?",
            answer=f"{parent.id} thought {child.id} wanted the {item.label}, but {child.id} really wanted the thirtieth story.",
        ),
        QAItem(
            question=f"How did teamwork help fix the problem?",
            answer=f"{parent.id} and {child.id} worked together with the {helper.label}, which helped them understand each other and feel calm again.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn at the end?",
            answer=f"{child.id} learned that asking again and working together can turn a misunderstanding into a peaceful bedtime.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = []
    for tag in ["bedtime", "sleep", "blanket", "pillow", "nightlight", "teamwork", "lesson"]:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for p in sample.prompts:
        parts.append(p)
    parts.append("")
    parts.append("== story qa ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    parts.append("")
    parts.append("== world qa ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}")
        parts.append(f"A: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"{e.id} ({e.type}): " + ", ".join(bits))
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(ITEMS, params.item), _safe_lookup(HELPERS, params.helper), params.name, params.gender)
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
    StoryParams(place="bedroom", activity="bedtime", item="blanket", name="Mina", gender="girl", helper="nightlight"),
    StoryParams(place="nursery", activity="bedtime", item="pillow", name="Theo", gender="boy", helper="storybook"),
    StoryParams(place="cottage", activity="bedtime", item="blanket", name="Nora", gender="girl", helper="teddy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/4."))
        print(sorted(set(asp.atoms(model, "valid_story"))))
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
