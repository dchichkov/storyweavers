#!/usr/bin/env python3
"""
A small storyworld: a fairy-tale surprise in space.

A young fairy wants to visit the moon garden and shine her lantern stars, but a
quiet surprise waits there: a lost moon kitten is hiding inside a silver pod.
The fairy must choose whether to rush ahead or listen to the whispering guide.
The turn comes when she opens the pod and finds a friend, not a problem.

The world model tracks:
- physical meters: sparkles, tiredness, fuel, glow, dirt
- emotional memes: wonder, worry, kindness, surprise, joy
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


# ---------------------------------------------------------------------------
# Entities / world model
# ---------------------------------------------------------------------------

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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    parent: object | None = None
    token: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "fairy"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy"}:
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
    magical: bool
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
class Action:
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
class Gift:
    id: str
    label: str
    phrase: str
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
class Helper:
    id: str
    label: str
    offer: str
    tail: str
    guards: set[str]
    covers: set[str]
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
        self.zone: set[str] = set()

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "moon_garden": Place(name="the moon garden", magical=True, affords={"gather_starlight", "follow_comet"}),
    "starlit_hill": Place(name="the starlit hill", magical=True, affords={"follow_comet"}),
    "castle_roof": Place(name="the castle roof", magical=True, affords={"gather_starlight"}),
}

ACTIONS = {
    "gather_starlight": Action(
        id="gather_starlight",
        verb="gather starlight",
        gerund="gathering starlight",
        rush="run to the shining flowers",
        mess="sparkles",
        soil="all glittery",
        zone={"hands", "torso"},
        keyword="space",
        tags={"space", "stars"},
    ),
    "follow_comet": Action(
        id="follow_comet",
        verb="follow the comet",
        gerund="following the comet",
        rush="dash after the bright tail",
        mess="dust",
        soil="dusty from the stars",
        zone={"feet", "torso"},
        keyword="space",
        tags={"space", "comet"},
    ),
}

GIFTS = {
    "lantern": Gift(
        id="lantern",
        label="lantern",
        phrase="a little silver lantern of starglass",
        region="hands",
    ),
    "cloak": Gift(
        id="cloak",
        label="cloak",
        phrase="a soft blue cloak with moon-thread",
        region="torso",
    ),
}

HELPERS = [
    Helper(
        id="moon_cat",
        label="moon cat",
        offer="open the silver pod carefully",
        tail="opened the pod together",
        guards={"sparkles", "dust"},
        covers={"hands", "torso"},
    ),
    Helper(
        id="star_moth",
        label="star moth",
        offer="look behind the glowing fern",
        tail="peeked behind the glowing fern",
        guards={"sparkles"},
        covers={"hands"},
    ),
]

FAIRY_NAMES = ["Luna", "Mira", "Faye", "Elara", "Tilly", "Nina"]
GUIDE_NAMES = ["Aunt Willow", "Queen Rose", "Old Elm", "Dawnkeeper"]
TRAITS = ["brave", "curious", "gentle", "bright", "cheerful"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
at_risk(A,G) :- action(A), gift(G), action_zone(A,R), gift_region(G,R).

compatible(H,A,G) :- helper(H), at_risk(A,G), action_mess(A,M), guards(H,M), covers(H,R), gift_region(G,R).

valid(Place,A,G) :- place(Place), affords(Place,A), at_risk(A,G), compatible(_,A,G).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.magical:
            lines.append(asp.fact("magical", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("action_mess", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("action_zone", aid, r))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("gift_region", gid, g.region))
        if g.plural:
            lines.append(asp.fact("gift_plural", gid))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for m in sorted(h.guards):
            lines.append(asp.fact("guards", h.id, m))
        for r in sorted(h.covers):
            lines.append(asp.fact("covers", h.id, r))
    return "\n".join(lines)

def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"

def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def at_risk(action: Action, gift: Gift) -> bool:
    return gift.region in action.zone

def select_helper(action: Action, gift: Gift) -> Optional[Helper]:
    for h in HELPERS:
        if gift.region in h.covers and action.mess in h.guards:
            return h
    return None

def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for aid, action in ACTIONS.items():
            if aid not in place.affords:
                continue
            for gid, gift in GIFTS.items():
                if at_risk(action, gift) and select_helper(action, gift):
                    out.append((pid, aid, gid))
    return out


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    action: str
    gift: str
    name: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story generation
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


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    action = _safe_lookup(ACTIONS, params.action)
    gift = _safe_lookup(GIFTS, params.gift)
    world = World(place)

    hero = world.add(Entity(id=params.name, kind="character", type="fairy", meters={}, memes={}))
    parent = world.add(Entity(id="guide", kind="character", type="mother", label=params.parent))
    token = world.add(Entity(
        id="gift", type=gift.id, label=gift.label, phrase=gift.phrase,
        owner=hero.id, caretaker=parent.id, worn_by=hero.id
    ))

    helper = select_helper(action, gift)
    if helper is None:
        pass

    hero.memes["wonder"] = 1
    hero.memes["love"] = 1
    token.meters["shine"] = 1

    world.say(f"{hero.id} was a {params.trait} little fairy who lived by {place.name}.")
    world.say(f"{hero.id} loved {action.gerund} and carried {token.phrase} wherever {hero.pronoun()} went.")
    world.say(f"One evening, {hero.id} and {params.parent} went to {place.name} under a silver sky.")
    world.say(f"{hero.id} wanted to {action.verb} at once, but {params.parent} held up a gentle hand.")

    hero.memes["worry"] += 1
    world.say(f'"You will get {token.label} {action.soil}," {params.parent} said, "and I would have to clean it."')

    world.para()
    hero.memes["surprise"] += 1
    world.say(f"{hero.id} followed {params.parent} toward a glowing pod behind the comet fern.")
    world.say(f"Then the pod opened, and a moon cat blinked out like a tiny star.")
    world.say(f'"It was hiding there all along," said {params.parent}, smiling. "Now we can {helper.offer}."')

    hero.memes["joy"] += 2
    hero.memes["kindness"] += 1
    hero.memes["worry"] = 0
    token.meters["shine"] = 0
    world.para()
    world.say(f"{hero.id} smiled and helped the moon cat climb out.")
    world.say(f"Together they {helper.tail}, and {hero.id} still got to {action.gerund} in the moon garden.")
    world.say(f"The little {token.label} stayed safe, and the moon cat curled up beside {hero.pronoun('object')} like a warm pearl.")

    world.facts = {
        "hero": hero,
        "parent": parent,
        "gift": token,
        "action": action,
        "helper": helper,
        "place": place,
    }
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    action = _safe_fact(world, f, "action")
    gift = _safe_fact(world, f, "gift")
    return [
        f'Write a fairy tale set in space where {hero.id} wants to {action.verb} but there is a surprise to discover.',
        f"Tell a gentle story about a little fairy, a silver {gift.label}, and a happy surprise in {world.place.name}.",
        f'Write a child-friendly story that includes the word "space" and ends with kindness after a surprise.',
    ]

def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    action = _safe_fact(world, f, "action")
    gift = _safe_fact(world, f, "gift")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"Who is the fairy tale about?",
            answer=f"It is about {hero.id}, a little fairy, and {parent.label}, who guides {hero.pronoun('object')} through the moon garden.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at first?",
            answer=f"{hero.id} wanted to {action.verb} right away because {hero.pronoun()} loved the bright space garden.",
        ),
        QAItem(
            question=f"Why did {parent.label} warn {hero.id} about the {gift.label}?",
            answer=f"{parent.label} warned {hero.id} because {gift.label} could get {action.soil} if {hero.id} rushed into {action.gerund}.",
        ),
        QAItem(
            question="What was the surprise in the story?",
            answer=f"The surprise was a moon cat hiding in a silver pod behind the comet fern.",
        ),
        QAItem(
            question=f"How did the helper make things better?",
            answer=f"The {helper.label} helped by making it safe to handle the surprise, so {hero.id} could still enjoy {action.gerund}.",
        ),
    ]

def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is space?",
            answer="Space is the huge area beyond Earth where there are stars, moons, planets, and lots of dark sky.",
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that appears or happens when you were not ready for it.",
        ),
        QAItem(
            question="What is a fairy tale?",
            answer="A fairy tale is a made-up story that often has magic, kind helpers, and a happy ending.",
        ),
    ]


# ---------------------------------------------------------------------------
# Plumbing
# ---------------------------------------------------------------------------
def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
    out = ["--- trace ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        out.append(f"{e.id}: {e.type} {' '.join(parts)}")
    out.append(f"fired={sorted(world.fired)}")
    return "\n".join(out)

def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fairy-tale storyworld in space.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name", choices=FAIRY_NAMES)
    ap.add_argument("--parent", choices=GUIDE_NAMES)
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "place", None) or getattr(args, "action", None) or getattr(args, "gift", None):
        combos = [
            c for c in combos
            if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
            and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
            and (getattr(args, "gift", None) is None or c[2] == getattr(args, "gift", None))
        ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, gift = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(FAIRY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(GUIDE_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, action=action, gift=gift, name=name, parent=parent, trait=trait)

def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        combos = asp_valid()
        print(f"{len(combos)} valid combinations:")
        for row in combos:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(place="moon_garden", action="gather_starlight", gift="lantern", name="Luna", parent="Queen Rose", trait="brave"),
        StoryParams(place="starlit_hill", action="follow_comet", gift="cloak", name="Mira", parent="Aunt Willow", trait="curious"),
    ]

    if getattr(args, "all", None):
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        for i in range(max(getattr(args, "n", None), 1) * 50):
            if len(samples) >= getattr(args, "n", None):
                break
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
            header = f"### {p.name} / {p.place} / {p.action}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
