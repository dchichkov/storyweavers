#!/usr/bin/env python3
"""
storyworlds/worlds/tang_brown_misunderstanding_animal_story.py
==============================================================

A small animal story world about a friendly misunderstanding.

Seed story sketch:
---
Tang was a little brown tang fish who loved exploring the reef with his friend Pip,
a bright crab. One day Tang found a shiny shell and tucked it under a rock so he
could show it to Pip later. Pip only saw Tang hiding something and thought Tang
was hiding a snack.

Pip grew worried and called for the sea turtle, saying Tang had taken something
from the reef. Tang felt upset because he had only been saving the shell as a gift.
When the turtle asked questions, Tang explained, Pip listened, and the friends
laughed at the mix-up. Tang gave Pip the shell, and Pip tucked it into a safe
little cave for everyone to admire.

Causal state updates:
---
    finding treasure        -> hero.meters["excitement"] += 1
    hiding an object        -> observer.memes["suspicion"] += 1 if observer cannot see reason
    false guess             -> observer.memes["worry"] += 1, hero.memes["hurt"] += 1
    clear explanation       -> observer.memes["suspicion"] -> 0, hero.memes["hurt"] -> 0
    shared gift             -> hero.memes["warmth"] += 1, friend.memes["warmth"] += 1
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    hidden_in: Optional[str] = None
    visible: bool = True
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    helper: object | None = None
    hero: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "female_fish", "octopus"}
        male = {"boy", "father", "dad", "man", "male_fish", "crab"}
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Place:
    id: str
    label: str
    detail: str
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class ObjectSpec:
    id: str
    label: str
    phrase: str
    hide_spot: str
    treasure: bool = True
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class StoryParams:
    place: str = ""
    object: str = ""
    hero_name: str = ""
    hero_type: str = ""
    friend_name: str = ""
    friend_type: str = ""
    helper_name: str = ""
    helper_type: str = ""
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)
    def copy(self):
        clone = __import__("copy").deepcopy(self)
        return clone


PLACES = {
    "reef": Place(
        id="reef",
        label="the reef",
        detail="Bright coral made little hiding places between the rocks.",
        affords={"explore", "hide", "share"},
    ),
    "tidepool": Place(
        id="tidepool",
        label="the tide pool",
        detail="The water was shallow and clear, and every pebble looked shiny.",
        affords={"explore", "hide", "share"},
    ),
    "riverbank": Place(
        id="riverbank",
        label="the riverbank",
        detail="Tall reeds leaned over the water and made snug little nooks.",
        affords={"explore", "hide", "share"},
    ),
}

OBJECTS = {
    "shell": ObjectSpec(
        id="shell",
        label="shell",
        phrase="a shiny shell",
        hide_spot="under a rock",
    ),
    "pebble": ObjectSpec(
        id="pebble",
        label="pebble",
        phrase="a smooth pebble",
        hide_spot="in a little crevice",
    ),
    "tassel": ObjectSpec(
        id="tassel",
        label="tassel",
        phrase="a bright red tassel",
        hide_spot="inside a coral loop",
    ),
}

HERO_NAMES = ["Tang", "Milo", "Nia", "Bram", "Luna", "Kiko"]
FRIEND_NAMES = ["Pip", "Dot", "Marn", "Sera", "Tobi", "Rin"]
HELPER_NAMES = ["Turtle", "Aunt Fin", "Captain Shell", "Grandpa Wave"]
ANIMAL_TYPES = ["fish", "crab", "turtle", "otter", "bird"]
COLORS = ["brown", "golden", "striped", "speckled", "silver"]


def _article(phrase: str) -> str:
    return "an" if phrase[0].lower() in "aeiou" else "a"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        if "hide" not in place.affords:
            continue
        for obj_id in OBJECTS:
            combos.append((place_id, obj_id))
    return combos


def prize_at_risk(place: Place, obj: ObjectSpec) -> bool:
    return "hide" in place.affords and obj.hide_spot is not None


def explain_rejection(place: Place, obj: ObjectSpec) -> str:
    return f"(No story: {obj.phrase} doesn't fit this place's hiding-and-finding pattern.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about a misunderstanding.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--helper")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
              and (getattr(args, "object", None) is None or c[1] == getattr(args, "object", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, obj = rng.choice(list(combos))
    hero_name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    friend_name = getattr(args, "friend", None) or rng.choice([n for n in FRIEND_NAMES if n != hero_name])
    helper_name = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    return StoryParams(
        place=place,
        object=obj,
        hero_name=hero_name,
        hero_type="fish",
        friend_name=friend_name,
        friend_type="crab",
        helper_name=helper_name,
        helper_type="turtle",
    )


def _do_find(world: World, hero: Entity, obj: ObjectSpec) -> None:
    hero.meters["excitement"] = hero.meters.get("excitement", 0) + 1
    world.say(
        f"{hero.id} found {obj.phrase} near {world.place.label}."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} tucked {(getattr(hero, 'it')() if callable(getattr(hero, 'it', None)) else getattr(hero, 'it', 'it'))} {obj.hide_spot} so {hero.pronoun('object')} could keep it safe."
    )


def _misunderstand(world: World, friend: Entity, hero: Entity, obj: ObjectSpec) -> None:
    friend.memes["suspicion"] = friend.memes.get("suspicion", 0) + 1
    friend.memes["worry"] = friend.memes.get("worry", 0) + 1
    hero.memes["hurt"] = hero.memes.get("hurt", 0) + 1
    world.say(
        f"{friend.id} only saw {hero.id} hiding something and thought it was a snack."
    )
    world.say(
        f"{friend.pronoun('subject').capitalize()} got worried and called for help."
    )


def _explain(world: World, hero: Entity, friend: Entity, helper: Entity, obj: ObjectSpec) -> None:
    friend.memes["suspicion"] = 0
    friend.memes["worry"] = 0
    hero.memes["hurt"] = 0
    friend.memes["warmth"] = friend.memes.get("warmth", 0) + 1
    hero.memes["warmth"] = hero.memes.get("warmth", 0) + 1
    world.say(
        f"{helper.id} listened carefully while {hero.id} explained, \"I was saving {obj.phrase} as a gift.\""
    )
    world.say(
        f"{friend.id} blinked, then laughed. It had all been a misunderstanding."
    )
    world.say(
        f"{hero.id} shared {obj.phrase} with {friend.id}, and the friends placed it in a safe little nook for everyone to admire."
    )


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    obj = _safe_lookup(OBJECTS, params.object)
    world = World(place)
    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type, label=params.hero_name))
    friend = world.add(Entity(id=params.friend_name, kind="character", type=params.friend_type, label=params.friend_name))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, label=params.helper_name))
    treasure = world.add(Entity(
        id="treasure",
        kind="thing",
        type="object",
        label=obj.label,
        phrase=obj.phrase,
        owner=hero.id,
        hidden_in=obj.hide_spot,
    ))

    world.say(
        f"{hero.id} was a little brown tang who loved exploring {world.place.label}."
    )
    world.say(
        f"One day, {hero.id} spotted {obj.phrase}, and {hero.pronoun('subject')} felt very excited."
    )

    world.para()
    world.say(world.place.detail)
    _do_find(world, hero, obj)
    _misunderstand(world, friend, hero, obj)

    world.para()
    world.say(
        f"{helper.id} came over and asked gentle questions instead of guessing."
    )
    _explain(world, hero, friend, helper, obj)

    world.facts.update(
        hero=hero,
        friend=friend,
        helper=helper,
        treasure=treasure,
        obj=obj,
        place=place,
        misunderstood=True,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story for a young child about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id}, a brown tang, and a kind misunderstanding at {world.place.label}.',
        f"Tell a gentle story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend").id} thinks {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} is hiding a snack, but the hidden thing is {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "obj").phrase}.",
        f'Write a simple reef story that uses the words "tang" and "brown" and ends with friends laughing after a misunderstanding.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    friend = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "friend")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    obj = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "obj")
    place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    return [
        QAItem(
            question=f"Who was the little brown tang in the story?",
            answer=f"The little brown tang was {hero.id}, who loved exploring {world.place.label}.",
        ),
        QAItem(
            question=f"What did {friend.id} misunderstand about {hero.id}?",
            answer=f"{friend.id} thought {hero.id} was hiding a snack, but {hero.id} was really saving {obj.phrase} as a gift.",
        ),
        QAItem(
            question=f"Who helped clear up the misunderstanding?",
            answer=f"{helper.id} helped by listening carefully and asking gentle questions.",
        ),
        QAItem(
            question=f"What did the friends do at the end?",
            answer=f"They laughed at the mix-up and placed {obj.phrase} in a safe little nook at {place.label}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a tang?",
            answer="A tang is a kind of fish that can swim around coral reefs and eat tiny plants.",
        ),
        QAItem(
            question="What does brown mean?",
            answer="Brown is a warm color like tree bark, soil, or cocoa.",
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone gets the wrong idea about what another person meant.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.kind == "thing" and e.hidden_in:
            parts.append(f"hidden_in={e.hidden_in}")
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams("reef", "shell", "Tang", "fish", "Pip", "crab", "Turtle"),
    StoryParams("tidepool", "pebble", "Milo", "fish", "Dot", "crab", "Aunt Fin"),
    StoryParams("riverbank", "tassel", "Nia", "fish", "Rin", "crab", "Grandpa Wave"),
]


ASP_RULES = r"""
valid(Place, Obj) :- place(Place), object(Obj), hides(Obj), spot(Place).
misunderstanding(Place, Obj) :- valid(Place, Obj).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
        if "hide" in p.affords:
            lines.append(asp.fact("spot", pid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("hides", oid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_sample(params: StoryParams) -> StorySample:
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for place, obj in combos:
            print(f"  {place:10} {obj}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [build_sample(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError:
                continue
            params.seed = seed
            sample = build_sample(params)
            if sample.story in seen:
                continue
            seen.add(sample.story)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.object} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
