#!/usr/bin/env python3
"""
A small rhyming storyworld about a brave, curious child, a long little climb,
and a promised respite with zwieback at the top of Hel.

The seed words shape the world:
- respite: the turn toward a needed rest
- zwieback: the snack that makes the pause sweet
- hel: the hill-top place where the wind hushes

This script follows the storyworld contract with a compact simulation,
grounded prose, QA, and an ASP twin for the reasonableness gate.
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
# World model
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
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    traits: list = field(default_factory=list)
    guide: object | None = None
    hero: object | None = None
    snack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    kind: str
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
    gerund: str
    rush: str
    strain: str
    place_tag: str
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
class Snack:
    id: str
    label: str
    phrase: str
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
class Guide:
    id: str
    label: str
    phrase: str
    gentleness: str
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
    activity: str
    snack: str
    hero_name: str
    hero_gender: str
    guide_type: str
    trait: str
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
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "trail": Place(id="trail", label="the winding trail to Hel", kind="outdoor", affords={"climb", "look", "rest"}),
    "ridge": Place(id="ridge", label="the bright ridge by Hel", kind="outdoor", affords={"climb", "look", "rest"}),
    "garden": Place(id="garden", label="the garden path", kind="outdoor", affords={"look", "rest"}),
}

ACTIVITIES = {
    "climb": Activity(
        id="climb",
        verb="climb up toward Hel",
        gerund="climbing up toward Hel",
        rush="dash uphill",
        strain="tired and breathy",
        place_tag="hel",
        keyword="hel",
        tags={"hel", "bravery", "curiosity"},
    ),
    "explore": Activity(
        id="explore",
        verb="explore the little trail",
        gerund="exploring the little trail",
        rush="run to peek around the bend",
        strain="tired but keen",
        place_tag="curiosity",
        keyword="curiosity",
        tags={"curiosity", "bravery"},
    ),
    "rest": Activity(
        id="rest",
        verb="take a rest by the stone",
        gerund="resting by the stone",
        rush="plop down at once",
        strain="calm and still",
        place_tag="respite",
        keyword="respite",
        tags={"respite"},
    ),
}

SNACKS = {
    "zwieback": Snack(id="zwieback", label="zwieback", phrase="a little tin of zwieback"),
    "berries": Snack(id="berries", label="berries", phrase="a small bowl of berries"),
}

GUIDES = {
    "sibling": Guide(id="sibling", label="big sibling", phrase="a patient big sibling", gentleness="soft"),
    "grandma": Guide(id="grandma", label="grandma", phrase="a smiling grandma", gentleness="warm"),
}

GIRL_NAMES = ["Mina", "Lina", "Tessa", "Nora", "Lily"]
BOY_NAMES = ["Milo", "Theo", "Finn", "Arlo", "Pip"]
TRAITS = ["brave", "curious", "bright", "gentle"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
risk(P,A) :- place(P), activity(A), needs_rest(A), affords(P,rest).
reason(P,A,S) :- risk(P,A), snack(S), sweet(S).
valid(P,A,S) :- risk(P,A), reason(P,A,S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        if a.id == "rest":
            lines.append(asp.fact("needs_rest", aid))
    for sid in SNACKS:
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("sweet", sid))
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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def is_reasonable(place: Place, activity: Activity, snack: Snack) -> bool:
    return "rest" in place.affords and activity.id in {"climb", "explore"} and snack.id == "zwieback"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for aid, act in ACTIVITIES.items():
            for sid, snack in SNACKS.items():
                if is_reasonable(place, act, snack):
                    combos.append((pid, aid, sid))
    return combos


def setup_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_gender,
        label=params.hero_name,
        traits=[],
    ))
    guide = world.add(Entity(
        id="Guide",
        kind="character",
        type=params.guide_type,
        label=_safe_lookup(GUIDES, params.guide_type).label,
    ))
    snack = world.add(Entity(
        id=params.snack,
        type="snack",
        label=_safe_lookup(SNACKS, params.snack).label,
        phrase=_safe_lookup(SNACKS, params.snack).phrase,
        plural=_safe_lookup(SNACKS, params.snack).plural,
        owner=guide.id,
        carried_by=guide.id,
    ))
    world.facts.update(hero=hero, guide=guide, snack=snack, activity=_safe_lookup(ACTIVITIES, params.activity), params=params)
    return world


def narrate_setup(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    guide: Entity = _safe_fact(world, f, "guide")
    snack: Entity = _safe_fact(world, f, "snack")
    act: Activity = _safe_fact(world, f, "activity")
    trait = _safe_fact(world, f, "params").trait

    world.say(
        f"{hero.id} was a {trait} child with a curious spark, "
        f"and {hero.pronoun('possessive')} feet loved a path to chart."
    )
    world.say(
        f"{hero.id} liked to {act.gerund}; {hero.pronoun().capitalize()} liked to see "
        f"what each little turn might start."
    )
    world.say(
        f"{guide.label.capitalize()} carried {snack.phrase}, for a snack can make a steep day sweet, "
        f"and a tiny taste of zwieback is a cheerful treat."
    )


def narrate_turn(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    guide: Entity = _safe_fact(world, f, "guide")
    act: Activity = _safe_fact(world, f, "activity")
    snack: Entity = _safe_fact(world, f, "snack")

    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["bravery"] = hero.memes.get("bravery", 0) + 1
    hero.meters["tired"] = hero.meters.get("tired", 0) + 1

    world.para()
    world.say(
        f"One bright day, {hero.id} and {guide.label} went to {world.place.label}."
    )
    world.say(
        f"The path rose high toward Hel, and {hero.id} wanted to {act.verb} "
        f"just to see what waited there."
    )
    world.say(
        f"Halfway up, {hero.id} grew {act.strain}, but {hero.pronoun()} did not turn away."
    )


def narrate_respite(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    guide: Entity = _safe_fact(world, f, "guide")
    snack: Entity = _safe_fact(world, f, "snack")
    act: Activity = _safe_fact(world, f, "activity")

    hero.meters["tired"] = 0
    hero.memes["calm"] = hero.memes.get("calm", 0) + 1

    world.para()
    world.say(
        f"At last they reached a flat little nook, a quiet respite by the stones."
    )
    world.say(
        f"{guide.label.capitalize()} smiled and opened {snack.phrase}; the zwieback crunched "
        f"like a kind, neat rhyme."
    )
    world.say(
        f"{hero.id} munched one piece, looked over Hel, and felt brave and curious all at the same time."
    )
    world.say(
        f"So {hero.id} {act.gerund}, then paused for respite, with a happy heart and a snack in time."
    )


def tell_story(params: StoryParams) -> World:
    world = setup_world(params)
    narrate_setup(world)
    narrate_turn(world)
    narrate_respite(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    act: Activity = _safe_fact(world, world.facts, "activity")
    return [
        f'Write a short rhyming story for a child about {p.hero_name}, '
        f'who feels brave and curious while {act.gerund}.',
        f"Tell a gentle story that includes Hel, respite, and zwieback.",
        f"Write a tiny rhyming adventure where a child climbs, tires, rests, and shares zwieback.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    guide: Entity = _safe_fact(world, f, "guide")
    snack: Entity = _safe_fact(world, f, "snack")
    act: Activity = _safe_fact(world, f, "activity")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a brave and curious child who went with {guide.label}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do on the way to Hel?",
            answer=f"{hero.id} wanted to {act.verb}, because curiosity kept tugging at {hero.pronoun('possessive')} heart.",
        ),
        QAItem(
            question=f"What helped make the ending feel peaceful?",
            answer=f"A quiet respite and {snack.phrase} helped {hero.id} slow down and feel happy at the top.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even when it feels a little hard or scary.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the wish to look, learn, and ask what might be around the next corner.",
        ),
        QAItem(
            question="What is respite?",
            answer="Respite means a short rest or a peaceful pause after work or travel.",
        ),
        QAItem(
            question="What is zwieback?",
            answer="Zwieback is a crisp, lightly baked snack that can be broken into small pieces.",
        ),
        QAItem(
            question="What is Hel in this story?",
            answer="Hel is the hill-top place the child reached after the climb.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(f"- {p}")
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small rhyming storyworld about bravery, curiosity, respite, and zwieback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--snack", choices=SNACKS)
    ap.add_argument("--gender", dest="hero_gender", choices=["girl", "boy"])
    ap.add_argument("--name", dest="hero_name")
    ap.add_argument("--guide", dest="guide_type", choices=GUIDES)
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
    if getattr(args, "place", None) and getattr(args, "activity", None) and getattr(args, "snack", None):
        if not is_reasonable(_safe_lookup(PLACES, getattr(args, "place", None)), _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(SNACKS, getattr(args, "snack", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "snack", None) is None or c[2] == getattr(args, "snack", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, snack = rng.choice(list(combos))
    gender = getattr(args, "hero_gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "hero_name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guide = getattr(args, "guide_type", None) or rng.choice(list(GUIDES))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, snack=snack, hero_name=name, hero_gender=gender, guide_type=guide, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


def asp_verify_cmd() -> int:
    return asp_verify()


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_cmd())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        triples = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="trail", activity="climb", snack="zwieback", hero_name="Mina", hero_gender="girl", guide_type="sibling", trait="brave"),
            StoryParams(place="ridge", activity="explore", snack="zwieback", hero_name="Theo", hero_gender="boy", guide_type="grandma", trait="curious"),
            StoryParams(place="trail", activity="rest", snack="zwieback", hero_name="Lina", hero_gender="girl", guide_type="grandma", trait="gentle"),
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
