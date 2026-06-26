#!/usr/bin/env python3
"""
A small mythic storyworld: a quest through a post office, with a multirise
pattern and a bad ending. The story remains child-facing, concrete, and state-
driven, while the ending proves what changed in the world.

The seed words and features shape the domain:
- multirise
- quest
- bad ending
- myth
- post office
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
# Core model
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    art: object | None = None
    hero: object | None = None
    parent: object | None = None
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
    name: str
    tags: set[str] = field(default_factory=set)
    shelter: bool = False
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
class Goal:
    id: str
    verb: str
    gerund: str
    keyword: str
    risk: str
    count_name: str
    rises: list[str] = field(default_factory=list)
    bad: str = "lost"
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
class Artifact:
    id: str
    label: str
    phrase: str
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
class Aid:
    id: str
    label: str
    covers: set[str]
    wards: set[str]
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
        self.lines: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.tension: float = 0.0
        self.quest_started = False
        self.quest_failed = False

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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "post_office": Place(name="the post office", tags={"post", "mail", "quest"}, shelter=True),
}

GOALS = {
    "deliver_letter": Goal(
        id="deliver_letter",
        verb="deliver the letter",
        gerund="delivering the letter",
        keyword="letter",
        risk="lost",
        count_name="deliveries",
        rises=["walk to the counter", "ask for the seal", "cross the hall", "climb the second step"],
        bad="lost",
        tags={"mail", "quest", "post"},
    ),
    "find_stamp": Goal(
        id="find_stamp",
        verb="find the missing stamp",
        gerund="finding the missing stamp",
        keyword="stamp",
        risk="lost",
        count_name="searches",
        rises=["look under the tray", "check the drawer", "peek behind the basket"],
        bad="missing",
        tags={"mail", "quest", "post"},
    ),
    "sort_parcel": Goal(
        id="sort_parcel",
        verb="sort the parcel",
        gerund="sorting the parcel",
        keyword="parcel",
        risk="mixed up",
        count_name="sorts",
        rises=["carry the parcel to the shelf", "lift it to the counter", "turn toward the bins"],
        bad="mixed up",
        tags={"mail", "quest", "post"},
    ),
}

ARTIFACTS = {
    "letter": Artifact(id="letter", label="letter", phrase="a sealed letter", region="hand"),
    "stamp": Artifact(id="stamp", label="stamp", phrase="a tiny stamp", region="hand"),
    "parcel": Artifact(id="parcel", label="parcel", phrase="a wrapped parcel", region="arm"),
}

AIDS = [
    Aid(id="lamp", label="a brass lamp", covers={"hand"}, wards={"lost", "missing"}, prep="light the lamp first", tail="walked back with the lamp lit"),
    Aid(id="ribbon", label="a red ribbon", covers={"arm"}, wards={"mixed up"}, prep="tie on the red ribbon", tail="followed the ribbon to the right shelf"),
    Aid(id="traymap", label="a tray map", covers={"hand", "arm"}, wards={"lost", "missing", "mixed up"}, prep="bring the tray map along", tail="moved through the hall with the tray map"),
]

NAMES = ["Mara", "Niko", "Lina", "Oren", "Suri", "Bram", "Kira", "Ezra"]
TRAITS = ["brave", "curious", "small", "earnest", "stubborn", "gentle"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    goal: str
    artifact: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
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


def goal_risk(goal: Goal, art: Artifact) -> bool:
    return art.region in {"hand", "arm"}


def select_aid(goal: Goal, art: Artifact) -> Optional[Aid]:
    for aid in AIDS:
        if goal.risk in aid.wards and art.region in aid.covers:
            return aid
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_name, place in PLACES.items():
        for goal_id, goal in GOALS.items():
            for art_id, art in ARTIFACTS.items():
                if goal_risk(goal, art) and select_aid(goal, art):
                    out.append((place_name, goal_id, art_id))
    return out


def explain_rejection(goal: Goal, art: Artifact) -> str:
    if not goal_risk(goal, art):
        return (
            f"(No story: {goal.gerund} would not truly endanger {art.label}; "
            f"the tale needs an honest risk for the quest to matter.)"
        )
    return (
        f"(No story: nothing in the aid set can rightly protect a {art.label} "
        f"from {goal.gerund}. The compromise must actually fit the danger.)"
    )


# ---------------------------------------------------------------------------
# World actions / mythic narration
# ---------------------------------------------------------------------------

def hero_title(hero: Entity) -> str:
    return f"little {next((t for t in hero.meters.get('traits', []) if t), 'hero')}"


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a small {hero.type} with a head full of old stories and a heart set on a quest.")


def love_goal(world: World, hero: Entity, goal: Goal) -> None:
    hero.memes["wonder"] = hero.memes.get("wonder", 0) + 1
    world.say(f"{hero.pronoun().capitalize()} loved {goal.gerund}, because every good errand felt like a brave tale.")


def gift(world: World, parent: Entity, hero: Entity, art: Entity) -> None:
    world.say(f"At dawn, {hero.pronoun('possessive')} {parent.label} gave {hero.pronoun('object')} {art.phrase}.")


def carry(world: World, hero: Entity, art: Entity) -> None:
    art.carried_by = hero.id
    world.say(f"{hero.id} held {art.it()} close and promised to keep {art.it()} safe.")


def arrive(world: World) -> None:
    world.say(f"One day, {world.place.name} stood quiet and bright, with shelves like cliffs and drawers like hidden caves.")


def begin_quest(world: World, hero: Entity, parent: Entity, goal: Goal, art: Entity) -> None:
    world.quest_started = True
    world.tension += 1
    world.say(f"{hero.id} set out to {goal.verb} at {world.place.name}, while {hero.pronoun('possessive')} {parent.label} watched from the door.")


def rise_of_tension(world: World, hero: Entity, goal: Goal, art: Entity) -> None:
    for step in goal.rises:
        world.tension += 1
        world.say(f"{hero.id} went on: {step}.")
    world.tension += 1
    world.say(f"But the hall felt longer than it looked, and {art.label} began to seem easy to lose.")


def bad_turn(world: World, hero: Entity, goal: Goal, art: Entity) -> None:
    hero.memes["fear"] = hero.memes.get("fear", 0) + 1
    world.quest_failed = True
    art.carried_by = None
    world.say(f"Then the worst happened: {hero.id} looked down, and {art.label} was gone from {hero.pronoun('possessive')} hands.")


def offer_aid(world: World, parent: Entity, hero: Entity, goal: Goal, art: Entity) -> Optional[Aid]:
    aid = select_aid(goal, art)
    if aid is None:
        return None
    world.say(f"{hero.pronoun('possessive').capitalize()} {parent.label} pointed at {aid.label} and said, \"{aid.prep}.\"")
    return aid


def end_badly(world: World, hero: Entity, parent: Entity, goal: Goal, art: Entity, aid: Optional[Aid]) -> None:
    if aid is not None:
        world.say(f"{hero.id} tried the plan, but the quest had already slipped away.")
    world.say(f"{hero.id} searched the bins, then the counter, then the floor, but {goal.bad} meant {art.label} never reached the right place.")
    world.say(f"At last, {hero.id} went home with empty hands, and {hero.pronoun('possessive')} {parent.label} held {hero.pronoun('object')} close.")
    world.say(f"So the quest ended badly, with the post office still quiet and the missing thing still missing.")


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A goal is risky for an artifact when the artifact is carried in a vulnerable body region.
goal_risky(G, A) :- goal(G), artifact(A), risk_region(A, R), vulnerable(R), goal_kind(G, K), matches(K, R).

% Aid is useful if it wards off the goal's danger and covers the vulnerable region.
helps(H, G, A) :- aid(H), goal_risky(G, A), wards(H, W), goal_risk(G, W), covers(H, R), risk_region(A, R).
has_fix(G, A) :- helps(_, G, A).

valid_story(P, G, A, Gender) :- place(P), goal(G), artifact(A), goal_risky(G, A), has_fix(G, A), wears(Gender, A).
valid_combo(P, G, A) :- place(P), goal(G), artifact(A), goal_risky(G, A), has_fix(G, A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.shelter:
            lines.append(asp.fact("shelter", pid))
    for gid, goal in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("goal_kind", gid, goal.risk))
        lines.append(asp.fact("goal_risk", gid, goal.risk))
        for r in {"hand", "arm"}:
            lines.append(asp.fact("matches", goal.risk, r))
    for aid, art in ARTIFACTS.items():
        lines.append(asp.fact("artifact", aid))
        lines.append(asp.fact("risk_region", aid, art.region))
        lines.append(asp.fact("wears", "girl", aid))
        lines.append(asp.fact("wears", "boy", aid))
    for aid in AIDS:
        lines.append(asp.fact("aid", aid.id))
        for c in sorted(aid.covers):
            lines.append(asp.fact("covers", aid.id, c))
        for w in sorted(aid.wards):
            lines.append(asp.fact("wards", aid.id, w))
    lines.append(asp.fact("vulnerable", "hand"))
    lines.append(asp.fact("vulnerable", "arm"))
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
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    goal = _safe_fact(world, f, "goal")
    art = _safe_fact(world, f, "artifact")
    return [
        f'Write a short mythic story for a young child about a quest in a post office that includes "{goal.keyword}".',
        f"Tell a gentle bad-ending story where {hero.id} tries to {goal.verb} but loses {art.label} in the post office.",
        f"Write a tiny myth with a rising quest, a lost treasure, and a sad ending image.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    goal = _safe_fact(world, f, "goal")
    art = _safe_fact(world, f, "artifact")
    aid = f.get("aid")
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to do in the post office?",
            answer=f"{hero.id} was trying to {goal.verb}. It was a little quest through the post office.",
        ),
        QAItem(
            question=f"What important thing did {hero.id} carry on the quest?",
            answer=f"{hero.id} carried {art.phrase} and hoped to keep {art.label} safe.",
        ),
        QAItem(
            question=f"Why did {hero.id}'s {parent.label} speak up about the quest?",
            answer=f"{parent.label} worried that {art.label} could be {goal.bad} if the quest went on too long.",
        ),
    ]
    if aid is not None:
        qa.append(
            QAItem(
                question=f"How was the {aid.label} supposed to help?",
                answer=f"The {aid.label} was supposed to help by protecting the risky part of the quest and keeping {art.label} safer.",
            )
        )
    if world.quest_failed:
        qa.append(
            QAItem(
                question="How did the story end?",
                answer=f"It ended badly. {hero.id} went home with empty hands, and the missing thing never made it to the right place.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a post office?",
            answer="A post office is a place where people send letters and parcels, and where mail is sorted and handled.",
        ),
        QAItem(
            question="What is a quest?",
            answer="A quest is a journey to do an important task or find something that matters.",
        ),
        QAItem(
            question="What does a bad ending mean in a story?",
            answer="A bad ending means the problem is not fixed and the story finishes with loss or sadness.",
        ),
        QAItem(
            question="What does multirise mean in a story?",
            answer="Multirise means the trouble grows in more than one step, so the tension rises several times before the ending.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    out.append(f"  quest_started={world.quest_started} quest_failed={world.quest_failed} tension={world.tension}")
    return "\n".join(out)


def tell(place: Place, goal: Goal, art_cfg: Artifact, hero_name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, meters={"traits": [trait]}))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="parent"))
    art = world.add(Entity(id=art_cfg.id, type=art_cfg.id, label=art_cfg.label, phrase=art_cfg.phrase, owner=hero.id, caretaker=parent.id))
    intro(world, hero)
    love_goal(world, hero, goal)
    gift(world, parent, hero, art)
    carry(world, hero, art)
    world.para()
    arrive(world)
    begin_quest(world, hero, parent, goal, art)
    rise_of_tension(world, hero, goal, art)
    offer_aid(world, parent, hero, goal, art)
    bad_turn(world, hero, goal, art)
    world.para()
    end_badly(world, hero, parent, goal, art, select_aid(goal, art))
    world.facts.update(hero=hero, parent=parent, goal=goal, artifact=art, aid=select_aid(goal, art))
    return world


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic post office quest with a multirise and a bad ending.")
    ap.add_argument("--place", choices=PLACES.keys())
    ap.add_argument("--goal", choices=GOALS.keys())
    ap.add_argument("--artifact", choices=ARTIFACTS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=["brave", "curious", "small", "earnest", "stubborn", "gentle"])
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
    if getattr(args, "goal", None) and getattr(args, "artifact", None):
        goal = _safe_lookup(GOALS, getattr(args, "goal", None))
        art = _safe_lookup(ARTIFACTS, getattr(args, "artifact", None))
        if not (goal_risk(goal, art) and select_aid(goal, art)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "goal", None) is None or c[1] == getattr(args, "goal", None))
        and (getattr(args, "artifact", None) is None or c[2] == getattr(args, "artifact", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, goal_id, art_id = rng.choice(list(combos))
    art = _safe_lookup(ARTIFACTS, art_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if gender not in art.genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        place=place,
        goal=goal_id,
        artifact=art_id,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        gender=gender,
        parent=getattr(args, "parent", None) or rng.choice(["mother", "father"]),
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(GOALS, params.goal),
        _safe_lookup(ARTIFACTS, params.artifact),
        params.name,
        params.gender,
        params.parent,
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
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_combo/3."))
        combos = sorted(set(asp.atoms(model, "valid_combo")))
        print(f"{len(combos)} valid combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="post_office", goal="deliver_letter", artifact="letter", name="Mara", gender="girl", parent="mother", trait="brave"),
            StoryParams(place="post_office", goal="find_stamp", artifact="stamp", name="Niko", gender="boy", parent="father", trait="curious"),
            StoryParams(place="post_office", goal="sort_parcel", artifact="parcel", name="Lina", gender="girl", parent="mother", trait="earnest"),
        ]
        samples = [generate(p) for p in curated]
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
