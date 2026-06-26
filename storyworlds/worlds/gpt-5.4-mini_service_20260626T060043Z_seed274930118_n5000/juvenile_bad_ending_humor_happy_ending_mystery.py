#!/usr/bin/env python3
"""
storyworlds/worlds/juvenile_bad_ending_humor_happy_ending_mystery.py
=====================================================================

A small mystery storyworld for a juvenile, child-facing domain.

Core premise:
- A child notices something missing.
- A funny false clue causes a brief bad turn.
- The real clue is found.
- The mystery ends in a happy reveal.

The prose stays close to mystery style: noticing, suspecting, testing,
and finally solving.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    hidden_in: Optional[str] = None
    found_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    false_clue: object | None = None
    helper: object | None = None
    hero: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman", "sister"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man", "brother"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
    indoors: bool
    hides: set[str]
    mood: str
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
class MysteryThing:
    id: str
    label: str
    phrase: str
    size: str
    kind: str
    can_hide_in: set[str]
    funny_fit: str
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
class Clue:
    id: str
    label: str
    phrase: str
    points_to: str
    is_false: bool = False
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
class StoryParams:
    place: str
    object: str
    clue: str
    name: str
    gender: str
    helper: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
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


def _n(arr: list[str], rng: random.Random) -> str:
    return rng.choice(arr)


PLACES = {
    "kitchen": Place("kitchen", "the kitchen", True, {"cupboard", "table", "fridge", "sink"}, "bright"),
    "bedroom": Place("bedroom", "the bedroom", True, {"bed", "drawer", "closet", "rug"}, "quiet"),
    "backyard": Place("backyard", "the backyard", False, {"shed", "bucket", "tree", "bench"}, "splashy"),
    "classroom": Place("classroom", "the classroom", True, {"desk", "box", "shelf", "coat rack"}, "busy"),
}

THINGS = {
    "marble": MysteryThing("marble", "a blue marble", "tiny blue marble", "small", "toy", {"drawer", "cupboard", "desk", "box"}, "it looked like a candy"),
    "badge": MysteryThing("badge", "a shiny badge", "shiny badge", "small", "prize", {"drawer", "coat rack", "desk", "shelf"}, "it winked like a tiny moon"),
    "cookie": MysteryThing("cookie", "a special cookie", "special cookie", "small", "snack", {"cupboard", "table", "box"}, "it could hide under a napkin"),
    "key": MysteryThing("key", "a little key", "little key", "small", "tool", {"drawer", "fridge", "bench"}, "it could disappear in a palm"),
}

CLUES = {
    "crumbs": Clue("crumbs", "crumbs", "a trail of crumbs", "cookie", is_false=True),
    "mud": Clue("mud", "muddy prints", "muddy prints", "backyard", is_false=True),
    "rattle": Clue("rattle", "a rattle", "a tiny rattle under the floorboards", "drawer", is_false=True),
    "note": Clue("note", "a note", "a note with a wobbly arrow", "true", is_false=False),
    "glint": Clue("glint", "a glint", "a little glint of light", "true", is_false=False),
}

NAMES = ["Mia", "Leo", "Zoe", "Ben", "Nora", "Ava", "Theo", "Lily"]
TRAITS = ["curious", "brave", "busy", "careful", "silly", "cheerful"]
HELPERS = ["mother", "father", "grandma", "older sister", "older brother"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Juvenile mystery storyworld with a funny false lead and a happy solve.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=THINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for thing_id, thing in THINGS.items():
            if place_id in thing.can_hide_in:
                for clue_id, clue in CLUES.items():
                    combos.append((place_id, thing_id, clue_id))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "object", None) is None or c[1] == getattr(args, "object", None))
              and (getattr(args, "clue", None) is None or c[2] == getattr(args, "clue", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, obj, clue = rng.choice(list(combos))
    thing = _safe_lookup(THINGS, obj)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, object=obj, clue=clue, name=name, gender=gender, helper=helper, trait=trait)


def _hero_pronoun(gender: str, case: str = "subject") -> str:
    return {"girl": {"subject": "she", "object": "her", "possessive": "her"},
            "boy": {"subject": "he", "object": "him", "possessive": "his"}}[gender][case]


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    thing = _safe_lookup(THINGS, params.object)
    clue = _safe_lookup(CLUES, params.clue)
    world = World(place)
    hero = world.add(Entity(params.name, kind="character", type=params.gender, label=params.name, traits=[params.trait, "juvenile"]))
    helper = world.add(Entity(params.helper, kind="character", type=params.helper if params.helper in {"mother", "father", "grandma"} else "person", label=params.helper))
    obj = world.add(Entity("object", type=thing.kind, label=thing.label, phrase=thing.phrase, owner=hero.id))
    false_clue = world.add(Entity("false_clue", type="clue", label=clue.label, phrase=clue.phrase))
    world.facts.update(hero=hero, helper=helper, obj=obj, thing=thing, clue=clue, false_clue=false_clue, place=place)

    hero.memes["curiosity"] = 1
    hero.memes["worry"] = 1
    world.say(f"{hero.id} was a {params.trait} little detective who liked noticing tiny things.")
    world.say(f"{_hero_pronoun(params.gender).capitalize()} loved {thing.label} and kept it close because it felt like a lucky secret.")

    world.para()
    world.say(f"One day, {thing.label} was gone.")
    world.say(f"{hero.id} looked under the bed, inside the drawers, and behind the little doors in {place.label}.")
    world.say(f"Then {hero.id} found {clue.phrase}, which looked important enough to be a clue.")

    if clue.is_false:
        hero.memes["confusion"] = 1
        hero.memes["embarrassment"] = 1
        world.say(f"{hero.id} followed the clue and made a very serious face.")
        if clue.id == "crumbs":
            world.say(f"It led to the cupboard, where a cookie tin sat smugly and smelled like a joke.")
        elif clue.id == "mud":
            world.say(f"It led outside, where the muddy prints belonged to a dog wearing a leaf on its nose.")
        elif clue.id == "rattle":
            world.say(f"It led to the floorboards, but the rattle was only a loose spoon tapping when the floor shook.")
        world.say("That was a bad turn for the mystery, because the clue was funny and completely wrong.")
        hero.memes["confusion"] = 0
        hero.memes["worry"] = 2

    world.para()
    real_hint = "glint" if clue.is_false else clue.id
    if clue.is_false:
        world.say(f"After the silly mistake, {helper.id} knelt down and said, \"Try looking where the light bounces.\"")
        world.say(f"{hero.id} looked again and spotted a tiny glint near a hidden space in {place.label}.")
    else:
        world.say(f"{helper.id} pointed at the clue and said, \"That one is telling the truth.\"")
        world.say(f"{hero.id} followed the sign carefully and spotted a tiny opening in {place.label}.")

    hide_spot = None
    for spot in sorted(place.hides):
        if spot in thing.can_hide_in:
            hide_spot = spot
            break
    if hide_spot is None:
        pass
    obj.hidden_in = hide_spot
    obj.found_by = hero.id
    hero.memes["relief"] = 2
    hero.memes["joy"] = 2
    world.say(f"There it was: {thing.label}, tucked in the {hide_spot} {thing.funny_fit}.")
    world.say(f"{hero.id} laughed at the sneaky hiding spot, and {helper.id} laughed too.")
    world.say(f"It was a happy ending for the little mystery, because the missing thing was safe at last.")
    world.facts["resolved"] = True
    world.facts["hide_spot"] = hide_spot
    world.facts["false_turn"] = clue.is_false
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    thing = _safe_fact(world, f, "thing")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a short juvenile mystery story about {hero.id} looking for {thing.label} in {place.label}.',
        f'Tell a child-friendly mystery with a funny false clue, a brief bad turn, and a happy ending.',
        f'Write a playful detective story where a small missing object is found in a surprising place.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    thing = _safe_fact(world, f, "thing")
    place = _safe_fact(world, f, "place")
    hide_spot = _safe_fact(world, f, "hide_spot")
    clue = _safe_fact(world, f, "clue")
    qa = [
        QAItem(
            question=f"What was {hero.id} trying to find?",
            answer=f"{hero.id} was trying to find {thing.label}, the small thing that went missing in {place.label}.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the mystery?",
            answer=f"{helper.id} helped by giving a calmer hint after the funny wrong clue caused trouble.",
        ),
        QAItem(
            question=f"Where was {thing.label} hiding at the end?",
            answer=f"It was tucked in the {hide_spot} in {place.label}, where it could hide in plain sight.",
        ),
    ]
    if clue.is_false:
        qa.append(QAItem(
            question=f"Why was the first clue a bad turn?",
            answer="It was a bad turn because the clue looked important, but it led to the wrong place and made the search feel silly before the real answer appeared.",
        ))
    qa.append(QAItem(
        question=f"How did the story end?",
        answer=f"It ended happily when the missing {thing.label} was found and everyone laughed about the sneaky hiding spot.",
    ))
    return qa


WORLD_KNOWLEDGE = {
    "juvenile": [
        ("What does juvenile mean?", "Juvenile means young or childlike."),
    ],
    "mystery": [
        ("What is a mystery?", "A mystery is a puzzle or problem that needs to be solved."),
    ],
    "clue": [
        ("What is a clue?", "A clue is a small hint that helps someone solve a mystery."),
    ],
    "happy": [
        ("What does a happy ending mean?", "A happy ending is when the problem gets solved in a good way."),
    ],
    "humor": [
        ("What is humor?", "Humor is something funny that makes people laugh."),
    ],
    "bed": [
        ("Why do people look under the bed when searching?", "People often look under the bed because small things can roll there and hide."),
    ],
    "drawer": [
        ("Why do drawers hide things well?", "Drawers can hide things because they are small boxes that close up and keep things out of sight."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"juvenile", "mystery", "clue", "happy", "humor"}
    out: list[QAItem] = []
    for tag in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[tag])
    return out


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
        bits = []
        if e.hidden_in:
            bits.append(f"hidden_in={e.hidden_in}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  place: {world.place.id}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bedroom", object="marble", clue="crumbs", name="Mia", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="kitchen", object="cookie", clue="glint", name="Leo", gender="boy", helper="father", trait="silly"),
    StoryParams(place="classroom", object="badge", clue="rattle", name="Nora", gender="girl", helper="older sister", trait="careful"),
    StoryParams(place="backyard", object="key", clue="mud", name="Theo", gender="boy", helper="grandma", trait="brave"),
]


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


ASP_RULES = r"""
place(kitchen; bedroom; backyard; classroom).
object(marble; badge; cookie; key).
clue(crumbs; mud; rattle; note; glint).

hides_in(kitchen,cupboard; kitchen,table; kitchen,fridge; bedroom,bed; bedroom,drawer; bedroom,closet; backyard,shed; backyard,bucket; classroom,desk; classroom,box; classroom,shelf; classroom,coat_rack).
can_hide(object(marble), bedroom,drawer).
can_hide(object(marble), classroom,desk).
can_hide(object(marble), classroom,box).
can_hide(object(badge), bedroom,drawer).
can_hide(object(badge), classroom,desk).
can_hide(object(badge), classroom,shelf).
can_hide(object(cookie), kitchen,cupboard).
can_hide(object(cookie), kitchen,table).
can_hide(object(cookie), classroom,box).
can_hide(object(key), backyard,bench).
can_hide(object(key), bedroom,drawer).
can_hide(object(key), kitchen,fridge).

valid_story(P,O,C) :- place(P), object(O), clue(C), can_hide(object(O), P, _).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid in THINGS:
        lines.append(asp.fact("object", oid))
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for pid, place in PLACES.items():
        for spot in sorted(place.hides):
            lines.append(asp.fact("hides_in", pid, spot))
    for oid, thing in THINGS.items():
        for pid in sorted(thing.can_hide_in):
            for spot in sorted(_safe_lookup(PLACES, pid).hides):
                lines.append(asp.fact("can_hide", oid, pid, spot))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, o, c) for p, o, c in valid_combos()}
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    return build_parser.__wrapped__()  # type: ignore[attr-defined]


def _build_parser_impl() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Juvenile mystery storyworld with humor, a bad turn, and a happy ending.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--object", choices=THINGS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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


build_parser.__wrapped__ = _build_parser_impl  # type: ignore[attr-defined]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.object} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
