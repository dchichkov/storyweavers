#!/usr/bin/env python3
"""
storyworlds/worlds/barricade_mark_gerund_misunderstanding_happy_ending_nursery.py
=================================================================================

A tiny nursery-rhyme-style storyworld about a child, a misunderstanding, a
barricade, and a happy ending.

Premise:
A little child wants to mark a wall with a special gerund-like task phrase
(such as "painting" or "sticking"), but a grown-up thinks the child is making a
mess. A playful barricade and a simple explanation turn the scene into a happy
ending.

The world simulates:
- one child
- one grown-up helper
- one marking action
- one object that can be misunderstood
- one soft barricade used to keep the scene tidy

The story is state-driven, not a frozen paragraph. We model physical meters
(e.g. tidiness, blockedness, markedness) and emotional memes (e.g. confusion,
worry, relief, joy).
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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    barricade: object | None = None
    child: object | None = None
    thing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return self.label or self.id
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
class Place:
    name: str = "the nursery"
    indoor: bool = True
    afford_marking: bool = True
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


@dataclass
class Action:
    id: str
    gerund: str
    verb: str
    mark: str
    mess: str
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
class ObjectThing:
    id: str
    label: str
    phrase: str
    on_wall: bool = False
    coverable: bool = True
    tags: set[str] = field(default_factory=set)
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
class Barricade:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
    tags: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.lines: list[list[str]] = [[]]

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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.lines = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    action: str
    object_id: str
    barricade: str
    child_name: str
    child_type: str
    adult_name: str
    adult_type: str
    seed: Optional[int] = None
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


PLACES = {
    "nursery": Place(name="the nursery", indoor=True, afford_marking=True),
}

ACTIONS = {
    "painting": Action(
        id="painting",
        gerund="painting",
        verb="paint",
        mark="marking",
        mess="painted",
        keyword="painting",
        tags={"paint", "mark-gerund"},
    ),
    "sticking": Action(
        id="sticking",
        gerund="sticking",
        verb="stick",
        mark="marking",
        mess="stuck",
        keyword="sticking",
        tags={"stick", "mark-gerund"},
    ),
}

OBJECTS = {
    "star": ObjectThing(
        id="star",
        label="star sticker",
        phrase="a bright star sticker",
        on_wall=True,
        tags={"sticker"},
    ),
    "heart": ObjectThing(
        id="heart",
        label="heart stamp",
        phrase="a soft heart stamp",
        on_wall=True,
        tags={"stamp"},
    ),
}

BARRICADES = {
    "pillow": Barricade(
        id="pillow",
        label="pillow barricade",
        phrase="a fluffy pillow barricade",
        protects={"wall", "floor", "sheets"},
        tags={"barricade"},
    ),
    "blanket": Barricade(
        id="blanket",
        label="blanket barricade",
        phrase="a gentle blanket barricade",
        protects={"wall", "floor"},
        tags={"barricade"},
    ),
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Ruby", "Ivy"]
BOY_NAMES = ["Ben", "Theo", "Finn", "Noah", "Eli"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    return [(p, a, o, b) for p in PLACES for a in ACTIONS for o in OBJECTS for b in BARRICADES]


def explain_rejection(place: str, action: str, obj: str, barricade: str) -> str:
    return (
        f"(No story: the nursery setup must be about marking with a gentle object "
        f"and a soft barricade. Got place={place}, action={action}, object={obj}, "
        f"barricade={barricade}.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld about a barricade and a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--barricade", choices=BARRICADES)
    ap.add_argument("--name")
    ap.add_argument("--adult")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "object_id", None) is None or c[2] == getattr(args, "object_id", None))
              and (getattr(args, "barricade", None) is None or c[3] == getattr(args, "barricade", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, action, obj, barricade = rng.choice(list(combos))
    child_type = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    adult_type = rng.choice(["mother", "father"])
    child_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if child_type == "girl" else BOY_NAMES)
    adult_name = getattr(args, "adult", None) or rng.choice(["Mama", "Papa", "Mimi", "Dada"])
    return StoryParams(
        place=place,
        action=action,
        object_id=obj,
        barricade=barricade,
        child_name=child_name,
        child_type=child_type,
        adult_name=adult_name,
        adult_type=adult_type,
    )


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    child = world.add(Entity(id="child", kind="character", type=params.child_type, label=params.child_name))
    adult = world.add(Entity(id="adult", kind="character", type=params.adult_type, label=params.adult_name))
    thing = world.add(Entity(id="thing", kind="thing", type="thing", label=_safe_lookup(OBJECTS, params.object_id).label))
    barricade = world.add(Entity(id="barricade", kind="thing", type="thing", label=_safe_lookup(BARRICADES, params.barricade).label))
    child.meters = {"markedness": 0.0, "tidy": 1.0}
    child.memes = {"joy": 0.0, "confusion": 0.0, "relief": 0.0}
    adult.meters = {"tidy": 1.0}
    adult.memes = {"worry": 0.0, "relief": 0.0, "joy": 0.0}
    thing.meters = {"markedness": 0.0}
    barricade.meters = {"blockedness": 1.0}
    world.facts["child"] = child
    world.facts["adult"] = adult
    world.facts["thing"] = thing
    world.facts["barricade"] = barricade
    return world


def warn_and_misunderstand(world: World, params: StoryParams) -> None:
    child = world.facts["child"]
    adult = world.facts["adult"]
    thing = world.facts["thing"]
    act = _safe_lookup(ACTIONS, params.action)
    child.memes["joy"] += 1
    world.say(
        f"In the {world.place.name}, little {child.label} began to {act.gerund} with {thing.label_word}."
    )
    world.say(
        f"{child.label} made a small {act.mark} on the wall, and {thing.label_word} looked bright and neat."
    )
    world.para()
    adult.memes["worry"] += 1
    child.memes["confusion"] += 1
    world.say(
        f"Then {adult.label} peeped in and frowned, for {adult.pronoun()} thought the {act.mark} meant a mess."
    )
    world.say(
        f'"Oh dear," said {adult.label}, "that looks like trouble, and I do not mean to be cross."'
    )


def fix_with_barricade(world: World, params: StoryParams) -> None:
    child = world.facts["child"]
    adult = world.facts["adult"]
    thing = world.facts["thing"]
    barricade = world.facts["barricade"]
    act = _safe_lookup(ACTIONS, params.action)
    child.memes["confusion"] += 1
    world.para()
    world.say(
        f"But {child.label} pointed to the {barricade.label}, a soft little wall that kept the play in order."
    )
    world.say(
        f"'{act.mark} means I am making a mark on purpose,' said {child.label}, 'not making a muddle on the floor.'"
    )
    thing.meters["markedness"] += 1
    child.meters["markedness"] += 1
    adult.memes["worry"] = 0.0
    adult.memes["relief"] += 1
    child.memes["relief"] += 1
    child.memes["joy"] += 1
    adult.memes["joy"] += 1
    world.say(
        f"{adult.label} blinked, then smiled. {adult.pronoun().capitalize()} saw the tidy {barricade.label} and the happy little mark."
    )
    world.say(
        f'"Why, so you are," said {adult.label}. "You were {act.gerund}, and the {thing.label_word} stayed exactly where it should."'
    )
    world.say(
        f"And so the nursery held its breath for a tick, then all was well: {child.label} kept {act.gerund}, {adult.label} laughed, and the little wall of pillows kept the room snug and neat."
    )


def tell(params: StoryParams) -> World:
    world = setup_world(params)
    warn_and_misunderstand(world, params)
    fix_with_barricade(world, params)
    world.facts["params"] = params
    return world


def generation_prompts(world: World) -> list[str]:
    p = world.facts["params"]
    act = _safe_lookup(ACTIONS, p.action)
    return [
        f'Write a nursery-rhyme-style story about a child named {p.child_name} who is {act.gerund} in the nursery and meets a misunderstanding.',
        f"Tell a gentle story where a grown-up mistakes a small {act.mark} for a mess, but a barricade and a kind explanation lead to a happy ending.",
        f'Write a short rhyming-feeling story that includes the words "{act.keyword}" and "barricade".',
    ]


def story_qa(world: World) -> list[QAItem]:
    p: StoryParams = world.facts["params"]
    act = _safe_lookup(ACTIONS, p.action)
    child: Entity = world.facts["child"]
    adult: Entity = world.facts["adult"]
    thing: Entity = world.facts["thing"]
    barricade: Entity = world.facts["barricade"]
    return [
        QAItem(
            question=f"Who was {act.gerund} in the nursery?",
            answer=f"{child.label} was. {child.label} was happily {act.gerund} with {thing.label_word}.",
        ),
        QAItem(
            question=f"Why did {adult.label} misunderstand the little mark?",
            answer=f"{adult.label} thought the small {act.mark} meant a messy accident, not a tidy mark made on purpose.",
        ),
        QAItem(
            question=f"What helped the story reach a happy ending?",
            answer=f"The soft {barricade.label} helped, because it kept the play area tidy while {child.label} explained the marking.",
        ),
        QAItem(
            question=f"What did {child.label} say the word '{act.mark}' meant?",
            answer=f"{child.label} said it meant making a mark on purpose, not making a muddle.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a barricade?",
            answer="A barricade is something set up to block or guide movement. In a nursery, it can help keep play neat and safe.",
        ),
        QAItem(
            question="What does it mean to make a mark?",
            answer="To make a mark means to leave a shape, line, or spot on something. It can be done on purpose with crayons, stickers, or stamps.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="nursery",
        action="painting",
        object_id="star",
        barricade="pillow",
        child_name="Mia",
        child_type="girl",
        adult_name="Mama",
        adult_type="mother",
    ),
    StoryParams(
        place="nursery",
        action="sticking",
        object_id="heart",
        barricade="blanket",
        child_name="Ben",
        child_type="boy",
        adult_name="Papa",
        adult_type="father",
    ),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.action not in ACTIONS or params.object_id not in OBJECTS or params.barricade not in BARRICADES:
        pass
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


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = [asp.fact("place", "nursery")]
    for a in ACTIONS:
        lines.append(asp.fact("action", a))
    for o in OBJECTS:
        lines.append(asp.fact("object", o))
    for b in BARRICADES:
        lines.append(asp.fact("barricade", b))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,A,O,B) :- place(P), action(A), object(O), barricade(B).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a = set(asp_valid_combos())
    b = set(valid_combos())
    if a != b:
        print("MISMATCH between ASP and Python valid_combos()")
        return 1
    sample = generate(CURATED[0])
    if not sample.story:
        print("Smoke test failed: empty story.")
        return 1
    print(f"OK: ASP parity and smoke test passed ({len(a)} combos).")
    return 0


def build_variant_samples(args: argparse.Namespace) -> list[StorySample]:
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    out: list[StorySample] = []
    if getattr(args, "all", None):
        return [generate(p) for p in CURATED]
    seen: set[str] = set()
    i = 0
    while len(out) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
        seed = base_seed + i
        i += 1
        params = resolve_params(args, random.Random(seed))
        params.seed = seed
        sample = generate(params)
        if sample.story in seen:
            continue
        seen.add(sample.story)
        out.append(sample)
    return out


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "asp", None):
        print(asp_program("#show valid/4."))
        return
    samples = build_variant_samples(args)
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
