#!/usr/bin/env python3
"""
storyworlds/worlds/alight_enthusiasm_hare_foreshadowing_fable.py
===============================================================

A small fable-style story world about a hare, enthusiasm, and something alight.

Seed tale used to build the world model:
---
At dusk, a young hare saw a lantern alight beside the path. He felt a great rush
of enthusiasm and decided he could dash home faster than the wind. An older crow
noticed the dry grass, the leaning lantern, and the sharp little sparks at the
wick. "Careful," she warned, "a bright start can still end in ash if you run
without looking."

The hare laughed and sprang forward anyway. Soon the breeze tugged at the flame,
the lantern wobbled, and the path ahead grew dark. At last the hare slowed, took
the lantern carefully in both paws, and followed the crow's steady advice. He
reached the burrow safely and learned that enthusiasm is useful when it listens
to foresight.

World model:
---
The world tracks:
- a hare's enthusiasm and caution as memes
- an alight lantern's brightness and smoke as meters
- wind, dry grass, and path safety as physical conditions
- foreshadowing cues that let a wise witness predict trouble before it happens

Narrative shape:
---
setup -> foreshadowing -> mistake -> repair -> moral ending
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
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    crow: object | None = None
    hare: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man", "hare", "crow", "fox"}
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
    id: str
    label: str
    dusk: bool = True
    windy: bool = False
    dry: bool = False
    narrow: bool = False
    affords: set[str] = field(default_factory=set)
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
class Activity:
    id: str
    verb: str
    rush: str
    gerund: str
    risk: str
    foreshadow: str
    outcome_bad: str
    outcome_good: str
    keyword: str = "enthusiasm"
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
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    carried: bool = True
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
class HelpItem:
    id: str
    label: str
    phrase: str
    helps: set[str]
    effect: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.trace_notes: list[str] = []

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


SETTINGS = {
    "meadow": Place(id="meadow", label="the meadow", windy=True, dry=True, affords={"dash", "watch"}),
    "lane": Place(id="lane", label="the lane", windy=True, narrow=True, dry=True, affords={"dash", "watch"}),
    "burrow-yard": Place(id="burrow-yard", label="the burrow yard", windy=False, dry=False, affords={"watch", "rest"}),
}

ACTIVITIES = {
    "dash": Activity(
        id="dash",
        verb="dash home",
        rush="spring ahead without looking",
        gerund="dashing home",
        risk="the flame could sputter in the wind",
        foreshadow="the wick was already short, and the breeze kept teasing the flame",
        outcome_bad="the lantern would go dim",
        outcome_good="the lantern stayed bright",
    ),
    "watch": Activity(
        id="watch",
        verb="keep watch",
        rush="stare only at the flame",
        gerund="watching carefully",
        risk="he might miss the warning signs",
        foreshadow="the dry grass crackled beside the path, as if it wanted to whisper first",
        outcome_bad="the warning would come too late",
        outcome_good="the warning arrived in time",
    ),
}

PRIZES = {
    "lantern": Prize(id="lantern", label="lantern", phrase="a small lantern alight", type="lantern"),
    "bundle": Prize(id="bundle", label="bundle", phrase="a dry bundle of reeds", type="bundle", plural=False),
}

HELP = {
    "shade": HelpItem(
        id="shade",
        label="lantern shade",
        phrase="a clear lantern shade",
        helps={"dash"},
        effect="kept the flame sheltered from the wind",
    ),
    "path": HelpItem(
        id="path",
        label="stone path",
        phrase="the stone path",
        helps={"watch"},
        effect="gave the hare a safer way to move",
    ),
}

GIRL_NAMES = ["Mina", "Luna", "Nia"]
BOY_NAMES = ["Pip", "Toby", "Finn"]
HARE_NAMES = ["Hopper", "Brindle", "Pounce"]
TRAITS = ["quick", "young", "bright-eyed", "restless"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about a hare, enthusiasm, and what was alight.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
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


def reasonableness_gate(place: Place, activity: Activity, prize: Prize) -> bool:
    if activity.id not in place.affords:
        return False
    if prize.id == "bundle" and activity.id == "dash":
        return False
    return True


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
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


def resolve_params(args: argparse.Namespace, rng: random.Random):
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    activity = getattr(args, "activity", None) or rng.choice(sorted(_safe_lookup(SETTINGS, place).affords))
    prize = getattr(args, "prize", None) or "lantern"
    if place not in SETTINGS or activity not in ACTIVITIES or prize not in PRIZES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    p = _safe_lookup(SETTINGS, place)
    a = _safe_lookup(ACTIVITIES, activity)
    pr = _safe_lookup(PRIZES, prize)
    if getattr(args, "place", None) and getattr(args, "activity", None) and not reasonableness_gate(p, a, pr):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    name = getattr(args, "name", None) or rng.choice(HARE_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, trait=trait)


def _do_activity(world: World, hare: Entity, activity: Activity, prize: Entity, narrate: bool = True) -> None:
    hare.memes["enthusiasm"] = hare.memes.get("enthusiasm", 0.0) + 1
    hare.memes["caution"] = hare.memes.get("caution", 0.0) - 0.25
    if activity.id == "dash":
        world.trace_notes.append("hare rushed toward the dark lane")
        prize.meters["brightness"] = prize.meters.get("brightness", 1.0) - 0.5
        prize.meters["smoke"] = prize.meters.get("smoke", 0.0) + 0.25
    else:
        world.trace_notes.append("hare paused to look for signs")
    if narrate:
        world.say(f"{hare.pronoun().capitalize()} felt a rush of enthusiasm and wanted to {activity.verb}.")


def predict(world: World, hare: Entity, activity: Activity, prize: Entity) -> dict:
    sim = World(world.place)
    sim.entities = {
        k: Entity(**{
            "id": e.id, "kind": e.kind, "type": e.type, "label": e.label, "phrase": e.phrase,
            "owner": e.owner, "caretaker": e.caretaker, "carried_by": e.carried_by,
            "plural": e.plural, "meters": dict(e.meters), "memes": dict(e.memes), "traits": list(e.traits)
        }) for k, e in world.entities.items()
    }
    _do_activity(sim, sim.get(hare.id), activity, sim.get(prize.id), narrate=False)
    lamp = sim.get(prize.id)
    return {
        "dim": lamp.meters.get("brightness", 1.0) < 0.6,
        "smoke": lamp.meters.get("smoke", 0.0),
    }


def introduce(world: World, hare: Entity) -> None:
    world.say(
        f"In {world.place.label}, there lived a {hare.traits[0]} hare named {hare.id}, "
        f"and {hare.pronoun('possessive')} heart was full of enthusiasm."
    )


def foreshadow(world: World, activity: Activity, prize: Entity) -> None:
    world.say(
        f"At dusk, {activity.foreshadow}, and the {prize.label} glowed a little unevenly."
    )


def warning(world: World, crow: Entity, hare: Entity, activity: Activity, prize: Entity) -> None:
    world.say(
        f"{crow.id} peered at the path and said, \"{activity.risk.capitalize()}. "
        f"Even something {prize.phrase.split()[-1]} can fail if it is rushed.\""
    )


def mistake(world: World, hare: Entity, activity: Activity) -> None:
    hare.memes["pride"] = hare.memes.get("pride", 0.0) + 1
    world.say(
        f"{hare.id} laughed, sprang ahead, and tried to {activity.rush}."
    )


def turn(world: World, hare: Entity, prize: Entity) -> None:
    prize.meters["brightness"] = max(0.0, prize.meters.get("brightness", 1.0) - 0.4)
    prize.meters["smoke"] = prize.meters.get("smoke", 0.0) + 0.4
    hare.memes["worry"] = hare.memes.get("worry", 0.0) + 1
    world.say(
        f"The breeze tugged at the flame, and the {prize.label} began to dim."
    )


def repair(world: World, hare: Entity, crow: Entity, prize: Entity, help_item: HelpItem) -> None:
    hare.memes["caution"] = hare.memes.get("caution", 0.0) + 1
    world.say(
        f"Then {hare.id} slowed down, listened to {crow.id}, and used {help_item.phrase}."
    )
    world.say(
        f"It {help_item.effect}, and soon the {prize.label} was steady again."
    )


def ending(world: World, hare: Entity, crow: Entity, prize: Entity) -> None:
    hare.memes["enthusiasm"] = hare.memes.get("enthusiasm", 0.0) + 0.5
    hare.memes["caution"] = hare.memes.get("caution", 0.0) + 0.5
    world.say(
        f"So {hare.id} reached the burrow safely with {prize.phrase}, and {crow.id} smiled."
    )
    world.say(
        "The little fable ended with a simple truth: enthusiasm is a fine light, "
        "but foresight keeps it from blowing out."
    )


def tell(world: World, params: StoryParams) -> World:
    hare = world.add(Entity(id=params.name, kind="character", type="hare", traits=[params.trait, "hare"]))
    crow = world.add(Entity(id="Crow", kind="character", type="crow", traits=["old", "wise"]))
    prize = world.add(Entity(id=params.prize, type=params.prize, label=_safe_lookup(PRIZES, params.prize).label, phrase=_safe_lookup(PRIZES, params.prize).phrase))
    world.facts.update(hare=hare, crow=crow, prize=prize, activity=_safe_lookup(ACTIVITIES, params.activity), place=_safe_lookup(SETTINGS, params.place), help=HELP["shade"])

    introduce(world, hare)
    world.para()
    foreshadow(world, _safe_lookup(ACTIVITIES, params.activity), prize)
    warning(world, crow, hare, _safe_lookup(ACTIVITIES, params.activity), prize)
    world.para()
    _do_activity(world, hare, _safe_lookup(ACTIVITIES, params.activity), prize)
    mistake(world, hare, _safe_lookup(ACTIVITIES, params.activity))
    turn(world, hare, prize)
    world.para()
    repair(world, hare, crow, prize, HELP["shade"])
    ending(world, hare, crow, prize)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hare = _safe_fact(world, f, "hare")
    act = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short fable for a child about a hare named {hare.id} whose enthusiasm nearly ruins a {prize.label}.',
        f"Tell a gentle story with foreshadowing about {hare.id}, a {hare.traits[0]} hare, and a lantern alight at dusk.",
        f'Write a fable-style tale where "enthusiasm" must learn from a warning before the end.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hare = _safe_fact(world, f, "hare")
    crow = _safe_fact(world, f, "crow")
    prize = _safe_fact(world, f, "prize")
    act = _safe_fact(world, f, "activity")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about a hare named {hare.id}, who began with a lot of enthusiasm and learned to slow down.",
        ),
        QAItem(
            question=f"What warning did {crow.id} give before the hare ran ahead?",
            answer=f"{crow.id} warned that {act.risk}. She noticed the dry signs before the problem grew bigger.",
        ),
        QAItem(
            question=f"What happened to the {prize.label} when the hare rushed forward?",
            answer=f"The {prize.label} wobbled, lost some brightness, and began to smoke a little before the hare made it steady again.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The hare reached safety by listening to the wise warning, and the fable ended by praising foresight as well as enthusiasm.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a lantern do?",
            answer="A lantern holds a light so people or animals can see better in the dark.",
        ),
        QAItem(
            question="What is enthusiasm?",
            answer="Enthusiasm is a strong, happy eagerness to do something.",
        ),
        QAItem(
            question="Why can wind be a problem for a flame?",
            answer="Wind can make a flame flicker, dim, or go out if it is not protected.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.extend(f"  note: {n}" for n in world.trace_notes)
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for pr in PRIZES:
        lines.append(asp.fact("prize", pr))
    lines.append(asp.fact("reasonably", "meadow", "dash", "lantern"))
    lines.append(asp.fact("reasonably", "lane", "dash", "lantern"))
    lines.append(asp.fact("reasonably", "meadow", "watch", "lantern"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,R) :- affords(P,A), place(P), activity(A), prize(R), reasonably(P,A,R).
#show valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = sorted({(p, a, r) for p in SETTINGS for a in _safe_lookup(SETTINGS, p).affords for r in PRIZES if reasonableness_gate(_safe_lookup(SETTINGS, p), _safe_lookup(ACTIVITIES, a), _safe_lookup(PRIZES, r))})
    cl = set(asp_valid())
    py_set = set(py)
    if cl == py_set:
        print(f"OK: clingo gate matches Python gate ({len(cl)} combos).")
        return 0
    print("MISMATCH:")
    print("  only in clingo:", sorted(cl - py_set))
    print("  only in python:", sorted(py_set - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(World(_safe_lookup(SETTINGS, params.place)), params)
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
    StoryParams(place="meadow", activity="dash", prize="lantern", name="Hopper", trait="restless"),
    StoryParams(place="lane", activity="watch", prize="lantern", name="Brindle", trait="bright-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "asp", None):
        for row in asp_valid():
            print(row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
        hdr = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=hdr)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
