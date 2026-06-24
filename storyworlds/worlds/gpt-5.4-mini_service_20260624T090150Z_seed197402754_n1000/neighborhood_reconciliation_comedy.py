#!/usr/bin/env python3
"""
neighborhood_reconciliation_comedy.py
=====================================

A small storyworld about neighborhood mix-ups, comic misunderstandings, and
reconciliation.

Premise:
- A person wants to do a cheerful neighborhood activity.
- Another neighbor worries about a small but real nuisance.
- The misunderstanding escalates in a funny, concrete way.
- A practical compromise makes room for both people.
- The ending proves the relationship is repaired.

This script keeps the simulation state-driven: meters track physical effects,
memes track social feelings, and the story is rendered from what actually
happened in the world model.
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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    issue: object | None = None
    neighbor: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandma", "aunt"}
        male = {"boy", "man", "father", "grandpa", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def are(self) -> str:
        return "are" if self.kind == "group" else "is"

    def verb(self, base: str) -> str:
        if self.kind == "group":
            return base
        if self.type in {"girl", "boy", "woman", "man", "mother", "father", "grandma", "grandpa", "aunt", "uncle"}:
            return {"play": "plays", "ring": "rings", "watch": "watches", "clean": "cleans"}.get(base, base + "s")
        return base + "s"
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    nuisance: str
    consequence: str
    zone: str
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
class Setting:
    place: str
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
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str] = field(default_factory=set)
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


@dataclass
class StoryParams:
    place: str
    activity: str
    issue: str
    fixer: str
    name: str
    neighbor: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone

    def neighbors(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id and e.kind == "thing"]


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_nuisance(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.neighbors():
        if actor.meters.get("noise", 0) < THRESHOLD:
            continue
        for other in world.neighbors():
            if other.id == actor.id:
                continue
            if other.memes.get("annoyed", 0) >= THRESHOLD:
                continue
            sig = ("annoy", actor.id, other.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            other.memes["annoyed"] = other.memes.get("annoyed", 0) + 1
            out.append(f"{other.id} heard the racket and frowned.")
    return out


def _r_conflict(world: World) -> list[str]:
    for e in world.neighbors():
        if e.memes.get("annoyed", 0) < THRESHOLD or e.memes.get("defiance", 0) < THRESHOLD:
            continue
        sig = ("conflict", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["conflict"] = e.memes.get("conflict", 0) + 1
        return ["__conflict__"]
    return []


CAUSAL_RULES = [
    Rule("nuisance", _r_nuisance),
    Rule("conflict", _r_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend([x for x in out if x != "__conflict__"])
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def activity_risk(activity: Activity, issue: str) -> bool:
    return issue in activity.tags


def select_fix(activity: Activity, issue: str) -> Optional[Fix]:
    for fix in FIXES:
        if issue in fix.guards and activity.keyword in fix.guards:
            return fix
    return None


def predict_problem(world: World, actor: Entity, activity: Activity, issue: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    return {
        "annoyed": sum(e.memes.get("annoyed", 0) for e in sim.neighbors()),
        "conflict": any(e.memes.get("conflict", 0) >= THRESHOLD for e in sim.neighbors()),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    actor.meters["noise"] = actor.meters.get("noise", 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    world.say(f"{actor.id} started to {activity.verb}.")
    world.say(f"It was the kind of {activity.gerund} that sounded cheerful to {actor.pronoun()}, but not to everyone else.")
    propagate(world, narrate=narrate)


def build_story(world: World, hero: Entity, neighbor: Entity, activity: Activity, issue: Entity, fix: Optional[Fix]) -> None:
    world.say(f"{hero.id} lived in a friendly neighborhood where every porch had a plant and every window had an opinion.")
    world.say(f"One afternoon, {hero.id} loved to {activity.verb} in the street, because it made the whole block feel lively.")
    world.say(f"{issue.label.capitalize()} was the thing {neighbor.id} cared about most, so when {hero.id} got ready, {neighbor.id} looked over the fence and said, \"Please not that today.\"")
    world.para()
    world.say(f"{hero.id} tried anyway, and the {activity.keyword} made a comic little commotion.")
    _do_activity(world, hero, activity, narrate=True)
    world.say(f"{neighbor.id} muttered that {issue.label} and {activity.keyword} were a silly mix, which only made the whole scene feel more dramatic.")
    hero.memes["defiance"] = hero.memes.get("defiance", 0) + 1
    propagate(world, narrate=True)
    if world.entities[hero.id].memes.get("conflict", 0) >= THRESHOLD:
        world.para()
        world.say(f"{hero.id} paused, looked at the face across the fence, and realized nobody was having fun anymore.")
        if fix:
            world.say(f"Then {neighbor.id} had a clever idea: {fix.prep}.")
            world.say(f"{hero.id} nodded, because the idea was simple enough to fit in a pocket and kind enough to fit in a neighborhood.")
            world.say(f"They {fix.tail}.")
            hero.memes["joy"] = hero.memes.get("joy", 0) + 1
            hero.memes["conflict"] = 0
            neighbor.memes["annoyed"] = 0
            neighbor.memes["conflict"] = 0
            world.say(f"After that, {hero.id} could keep the fun, {neighbor.id} could keep the peace, and the street sounded much better.")
    world.para()
    world.say(f"By evening, {hero.id} was {activity.gerund} again, and {neighbor.id} was laughing at how serious a tiny squabble had looked from a porch chair.")
    world.say(f"The neighborhood felt warmer because both of them had chosen a kinder ending.")


SETTINGS = {
    "street": Setting(place="the street", affords={"musical", "game", "delivery"}),
    "courtyard": Setting(place="the courtyard", affords={"musical", "game"}),
    "sidewalk": Setting(place="the sidewalk", affords={"game", "delivery"}),
    "lane": Setting(place="the lane", affords={"musical", "game"}),
}

ACTIVITIES = {
    "musical": Activity(
        id="musical",
        verb="play a trumpet on the porch",
        gerund="trumpet-blowing",
        rush="blast another loud note",
        nuisance="noise",
        consequence="too much noise",
        zone="ears",
        keyword="trumpet",
        tags={"noise", "music"},
    ),
    "game": Activity(
        id="game",
        verb="bounce a ball in the street",
        gerund="bouncing a ball",
        rush="chase the ball",
        nuisance="noise",
        consequence="bouncy racket",
        zone="windows",
        keyword="ball",
        tags={"noise", "ball"},
    ),
    "delivery": Activity(
        id="delivery",
        verb="roll a squeaky cart of lemons",
        gerund="rolling a squeaky cart",
        rush="push the cart faster",
        nuisance="noise",
        consequence="squeaky clatter",
        zone="doors",
        keyword="cart",
        tags={"noise", "cart"},
    ),
}

ISSUES = {
    "nap": Entity(id="nap", type="thing", label="the baby nap", phrase="a baby nap"),
    "cat": Entity(id="cat", type="thing", label="the sleepy cat", phrase="a sleepy cat"),
    "flowers": Entity(id="flowers", type="thing", label="the flowers", phrase="the flowers in the front yard"),
}

FIXES = [
    Fix(id="cookie_pause", label="a cookie break", prep="take a cookie break and move the game to the park bench", tail="took a cookie break and moved the fun to the park bench", guards={"noise", "ball"}),
    Fix(id="soft_notes", label="soft notes", prep="switch to soft notes and play with the mute on", tail="switched to soft notes and played with the mute on", guards={"noise", "music"}),
    Fix(id="wheels", label="rubber wheels", prep="put rubber wheels on the cart", tail="put rubber wheels on the cart and rolled it more quietly", guards={"noise", "cart"}),
]

NAMES = ["Maya", "Owen", "Pia", "Noah", "Lina", "Eli", "June", "Theo"]
NEIGHBORS = ["Mrs. Reed", "Mr. Bell", "Auntie Jo", "Mr. Kim", "Ms. Patel"]
TRAITS = ["cheerful", "busy", "curious", "silly", "gentle"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = _safe_lookup(ACTIVITIES, aid)
            for issue_id in ISSUES:
                if activity_risk(act, issue_id) and select_fix(act, issue_id):
                    out.append((place, aid, issue_id))
    return out


@dataclass
class StoryParams:
    place: str
    activity: str
    issue: str
    fixer: str
    name: str
    neighbor: str
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


def aspiration() -> str:
    return "A small neighborhood wants to stay cheerful, even when someone gets grumpy about the noise."


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type="child"))
    neighbor = world.add(Entity(id=params.neighbor, kind="character", type="adult"))
    issue = world.add(Entity(id=params.issue, kind="thing", label=_safe_lookup(ISSUES, params.issue).label))
    act = _safe_lookup(ACTIVITIES, params.activity)
    fix = next((f for f in FIXES if f.id == params.fixer), None)

    build_story(world, hero, neighbor, act, issue, fix)
    world.facts.update(hero=hero, neighbor=neighbor, activity=act, issue=issue, fix=fix, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a funny story for a young child about a {f["hero"].id} in a neighborhood who wants to {f["activity"].verb}.',
        f"Tell a gentle comedy where {f['neighbor'].id} gets upset about {f['issue'].label} and the neighbors find a peaceful fix.",
        f'Write a short neighborhood story that ends with everyone feeling better after a noisy problem is solved.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    neighbor = _safe_fact(world, f, "neighbor")
    act = _safe_fact(world, f, "activity")
    issue = _safe_fact(world, f, "issue")
    fix = _safe_fact(world, f, "fix")
    qa = [
        QAItem(
            question=f"Who was the story mostly about?",
            answer=f"The story was mostly about {hero.id}, who lived in the neighborhood and wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Why did {neighbor.id} get upset?",
            answer=f"{neighbor.id} got upset because {issue.label} was bothered by the noise from {act.keyword}, and the block became too loud.",
        ),
        QAItem(
            question=f"What did they do to make things better?",
            answer=f"They used {fix.label} so {hero.id} could keep playing while the neighborhood became quieter and calmer.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} and {neighbor.id} laughing again, which showed they had reconciled and the neighborhood felt friendly once more.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a neighborhood?",
            answer="A neighborhood is a place where people live near each other, and they often see one another on the street, sidewalk, or porch.",
        ),
        QAItem(
            question="What does reconcile mean?",
            answer="To reconcile means to make peace after a disagreement so people can be friendly again.",
        ),
        QAItem(
            question="Why can loud noise bother people?",
            answer="Loud noise can bother people because it makes it hard to relax, sleep, or think clearly.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="street", activity="musical", issue="nap", fixer="soft_notes", name="Maya", neighbor="Mrs. Reed"),
    StoryParams(place="sidewalk", activity="game", issue="flowers", fixer="cookie_pause", name="Owen", neighbor="Ms. Patel"),
    StoryParams(place="lane", activity="delivery", issue="cat", fixer="wheels", name="Pia", neighbor="Mr. Kim"),
]


def explain_rejection(activity: Activity, issue: str) -> str:
    return f"(No story: {activity.keyword} would not really bother {issue} in a way this world can fix kindly.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("keyword", aid, act.keyword))
        for t in sorted(act.tags):
            lines.append(asp.fact("tag", aid, t))
    for iid in ISSUES:
        lines.append(asp.fact("issue", iid))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for g in sorted(fx.guards):
            lines.append(asp.fact("guards", fx.id, g))
    return "\n".join(lines)


ASP_RULES = r"""
risk(A, I) :- tag(A, I).
compatible(A, I, F) :- risk(A, I), fix(F), guards(F, I), keyword(A, K), guards(F, K).
valid(P, A, I) :- affords(P, A), compatible(A, I, _).
#show valid/3.
"""


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
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Neighborhood reconciliation comedy storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--issue", choices=ISSUES)
    ap.add_argument("--name")
    ap.add_argument("--neighbor", choices=NEIGHBORS)
    ap.add_argument("--fixer", choices=[f.id for f in FIXES])
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
    combos = valid_combos()
    if getattr(args, "place", None) or getattr(args, "activity", None) or getattr(args, "issue", None):
        combos = [
            c for c in combos
            if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
            and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
            and (getattr(args, "issue", None) is None or c[2] == getattr(args, "issue", None))
        ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, issue = rng.choice(list(combos))
    fixer = getattr(args, "fixer", None) or next(f.id for f in FIXES if f.id == (select_fix(_safe_lookup(ACTIVITIES, activity), issue).id))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    neighbor = getattr(args, "neighbor", None) or rng.choice(NEIGHBORS)
    return StoryParams(place=place, activity=activity, issue=issue, fixer=fixer, name=name, neighbor=neighbor)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combos:")
        for t in triples:
            print(" ", t)
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
