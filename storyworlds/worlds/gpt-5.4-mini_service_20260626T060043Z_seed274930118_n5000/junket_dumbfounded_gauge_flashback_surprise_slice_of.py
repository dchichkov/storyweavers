#!/usr/bin/env python3
"""
Story world: a small slice-of-life tale about a planned junket, a surprising
flashback, and a gauge that helps a child and adult make a sensible choice.

Premise:
- A child is excited about a little junket to the waterfront market.
- They carry a family gauge from the kitchen, because it once belonged to a
  grandparent and helps measure how full jars and cups are.
- The child wants to use the gauge in a playful way, but the adult worries it
  could get damaged or lost during the outing.
- A flashback reminds the adult of how the gauge was used kindly at home.
- A surprise solution lets the child take a safer version of the fun: they
  help measure ingredients before the junket, then bring the gauge along only
  as a careful keepsake.

This world keeps the action small, grounded, and emotionally clear: a child
wants something, an adult notices a risk, a memory changes how they see the
moment, and they find a gentle compromise.
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
# Core vocabulary and simple world state
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    keepsake: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guardian: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    indoor: bool = True
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
class Activity:
    id: str
    verb: str
    gerund: str
    risk: str
    spoil: str
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
class Item:
    id: str
    label: str
    phrase: str
    portable: bool = True
    fragile: bool = False
    special: bool = False
    used_for: str = ""
    tags: set[str] = field(default_factory=set)
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
    item: str
    name: str
    gender: str
    guardian: str
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "kitchen": Place(name="the kitchen", indoor=True, affords={"bake", "measure"}),
    "porch": Place(name="the porch", indoor=False, affords={"junket", "measure"}),
    "market": Place(name="the waterfront market", indoor=False, affords={"junket", "walk"}),
    "library": Place(name="the library steps", indoor=False, affords={"junket", "walk"}),
}

ACTIONS = {
    "junket": Activity(
        id="junket",
        verb="go on the junket",
        gerund="going on the junket",
        risk="getting jostled",
        spoil="scratched or dropped",
        keyword="junket",
        tags={"junket", "outing"},
    ),
    "walk": Activity(
        id="walk",
        verb="take a walk",
        gerund="walking slowly",
        risk="being bumped",
        spoil="lost",
        keyword="walk",
        tags={"outing"},
    ),
    "measure": Activity(
        id="measure",
        verb="measure ingredients",
        gerund="measuring ingredients",
        risk="being splashed",
        spoil="wet",
        keyword="gauge",
        tags={"gauge", "home"},
    ),
    "bake": Activity(
        id="bake",
        verb="bake cookies",
        gerund="baking cookies",
        risk="getting dusty",
        spoil="sticky",
        keyword="cookies",
        tags={"home"},
    ),
}

ITEMS = {
    "gauge": Item(
        id="gauge",
        label="gauge",
        phrase="an old brass gauge with a tiny needle",
        fragile=True,
        special=True,
        used_for="measuring how full a jar was",
        tags={"gauge"},
    ),
    "snackbox": Item(
        id="snackbox",
        label="snack box",
        phrase="a little red snack box",
        fragile=False,
        special=False,
        used_for="carrying crackers",
        tags={"outing"},
    ),
    "recipecard": Item(
        id="recipecard",
        label="recipe card",
        phrase="a recipe card with neat handwriting",
        fragile=False,
        special=False,
        used_for="remembering a family recipe",
        tags={"home"},
    ),
    "sunhat": Item(
        id="sunhat",
        label="sun hat",
        phrase="a wide straw sun hat",
        fragile=False,
        special=False,
        used_for="keeping the sun out of eyes",
        tags={"outing"},
    ),
}

NAMES = {
    "girl": ["Mina", "Ruby", "Nora", "Lila", "June", "Ivy"],
    "boy": ["Owen", "Eli", "Finn", "Theo", "Max", "Sam"],
}
GUARDIANS = ["mother", "father", "grandma", "grandpa"]
TRAITS = ["curious", "cheerful", "careful", "spirited", "gentle"]


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def is_at_risk(action: Activity, item: Item) -> bool:
    return item.special and action.id == "junket"


def select_compromise(action: Activity, item: Item) -> Optional[str]:
    if action.id == "junket" and item.id == "gauge":
        return "measure first, then bring it only as a keepsake"
    if action.id == "measure" and item.id == "gauge":
        return "use the gauge at home where it belongs"
    return None


def flashback_text(hero: Entity, guardian: Entity, item: Entity) -> str:
    return (
        f"That brought a flashback to {hero.pronoun('possessive')} {guardian.type}: "
        f"the way {guardian.id} had once held the {item.label} by the rim and helped "
        f"{hero.pronoun('object')} pour water into a jar, one careful cup at a time."
    )


def surprise_text(hero: Entity, guardian: Entity, item: Entity) -> str:
    return (
        f"Then came a surprise: {guardian.id} remembered a tiny cloth pouch in the drawer. "
        f"They could tuck the {item.label} inside and let it come along safely."
    )


def tell(place: Place, action: Activity, item_cfg: Item,
         name: str = "Mina", gender: str = "girl", guardian_type: str = "mother") -> World:
    world = World(place)
    hero = world.add(Entity(
        id=name, kind="character", type=gender,
        meters={"joy": 0.0}, memes={"want": 0.0, "doubt": 0.0, "dumbfounded": 0.0}
    ))
    guardian = world.add(Entity(
        id=guardian_type, kind="character", type=guardian_type,
        meters={"care": 0.0}, memes={"concern": 0.0}
    ))
    item = world.add(Entity(
        id=item_cfg.id, kind="thing", type="thing", label=item_cfg.label,
        phrase=item_cfg.phrase, owner=hero.id, caretaker=guardian.id,
        keepsake=item_cfg.special
    ))

    # Act 1
    world.say(
        f"{hero.id} was a {random.choice(TRAITS)} little {gender} who loved family errands "
        f"almost as much as stories."
    )
    world.say(
        f"One morning, {hero.id} got excited about a little junket to {place.name}."
    )
    world.say(
        f"{hero.id} also found {hero.pronoun('possessive')} {item.label}, and "
        f"the tiny needle on it still pointed with a serious face."
    )

    # Act 2
    world.para()
    world.say(
        f"{hero.id} wanted to {action.verb}, but {guardian.id} looked at the {item.label} and worried "
        f"it could get {action.spoil} during the trip."
    )
    if is_at_risk(action, item_cfg):
        hero.memes["dumbfounded"] += 1
        world.say(
            f"{hero.id} was dumbfounded for a moment, because the {item.label} had always felt safe at home."
        )

    world.para()
    world.say(flashback_text(hero, guardian, item))
    world.say(
        f"That memory made the room feel quieter, as if everyone could hear how the {item.label} had helped before."
    )

    # Act 3
    world.para()
    compromise = select_compromise(action, item_cfg)
    if compromise:
        world.say(surprise_text(hero, guardian, item))
        hero.memes["joy"] += 1
        guardian.meters["care"] += 1
        world.say(
            f"So they chose a careful plan: {compromise}. {hero.id} packed the {item.label} in a pouch, "
            f"and the little junket could still happen."
        )
        world.say(
            f"At the waterfront market, {hero.id} walked beside {guardian.id}, holding the pouch like it was a treasure."
        )
        world.say(
            f"By the end, the {item.label} was still safe, and {hero.id} was smiling at the shiny stalls and the breeze."
        )
    else:
        world.say(
            f"They found a quieter plan instead, because the {item.label} was better left at home."
        )
        world.say(
            f"{hero.id} still felt proud helping with {action.gerund}, and the day ended with a calm little walk."
        )

    world.facts.update(
        hero=hero,
        guardian=guardian,
        item=item,
        place=place,
        action=action,
        item_cfg=item_cfg,
        compromise=compromise,
        risk=is_at_risk(action, item_cfg),
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    guardian: Entity = _safe_fact(world, f, "guardian")
    action: Activity = _safe_fact(world, f, "action")
    item: Item = _safe_fact(world, f, "item_cfg")
    return [
        f"Write a slice-of-life story about {hero.id}, a child who wants to {action.verb}, but a family {item.label} needs careful handling.",
        f"Tell a gentle story with a flashback and a surprise that helps {hero.id} and {guardian.id} make a safe plan for the {item.label}.",
        f"Write a short child-friendly story that includes the words junket, dumbfounded, and gauge.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    guardian: Entity = _safe_fact(world, f, "guardian")
    item: Item = _safe_fact(world, f, "item_cfg")
    action: Activity = _safe_fact(world, f, "action")
    place: Place = _safe_fact(world, f, "place")

    return [
        QAItem(
            question=f"What did {hero.id} want to do on the junket?",
            answer=f"{hero.id} wanted to {action.verb} at {place.name}, but needed to be careful about the {item.label}.",
        ),
        QAItem(
            question=f"Why was {guardian.id} worried about the {item.label}?",
            answer=f"{guardian.id} worried it could get {action.spoil} during the outing, so they wanted a safer plan.",
        ),
        QAItem(
            question="What did the flashback remind everyone of?",
            answer=f"It reminded them how {guardian.id} had helped {hero.id} use the {item.label} gently at home, one careful step at a time.",
        ),
        QAItem(
            question="How did the surprise help at the end?",
            answer=f"The surprise pouch let the {item.label} come along safely, so the junket could happen without damage.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gauge?",
            answer="A gauge is a tool that helps measure something, like how full a jar or container is.",
        ),
        QAItem(
            question="What does dumbfounded mean?",
            answer="Dumbfounded means so surprised that someone does not know what to say right away.",
        ),
        QAItem(
            question="What is a junket?",
            answer="A junket is a small trip or outing, often taken for fun or to visit a place.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story QA =="]
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A junket is valid when the chosen item is a gauge and the place supports outings.
valid_story(Place, Action, Item) :- place(Place), action(Action), item(Item),
                                    action_id(Action,junket), item_id(Item,gauge),
                                    affords(Place,junket).

% If the item is special and the action is a junket, it is at risk.
at_risk(Action, Item) :- action_id(Action,junket), item_special(Item).

% A compromise exists when the story can keep the gauge safe.
has_fix(Action, Item) :- at_risk(Action, Item), action_id(Action,junket), item_id(Item,gauge).

% Show the final compatibility set.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("action_id", aid, act.id))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        lines.append(asp.fact("item_id", iid, item.id))
        if item.special:
            lines.append(asp.fact("item_special", iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("market", "junket", "gauge"), ("porch", "junket", "gauge")}
    asp_set = set(asp_valid_stories())
    if asp_set == py:
        print(f"OK: ASP matches Python ({len(py)} valid stories).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP-only:", sorted(asp_set - py))
    print("Python-only:", sorted(py - asp_set))
    return 1


# ---------------------------------------------------------------------------
# CLI and generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for act_id in place.affords:
            for item_id, item in ITEMS.items():
                if act_id == "junket" and item_id == "gauge":
                    combos.append((place_id, act_id, item_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world with a junket, a flashback, and a surprising gauge.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--activity", choices=ACTIONS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=GUARDIANS)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if getattr(args, "item", None):
        combos = [c for c in combos if c[2] == getattr(args, "item", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, item = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    guardian = getattr(args, "guardian", None) or rng.choice(GUARDIANS)
    return StoryParams(place=place, activity=activity, item=item, name=name, gender=gender, guardian=guardian)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(ACTIONS, params.activity),
        _safe_lookup(ITEMS, params.item),
        name=params.name,
        gender=params.gender,
        guardian_type=params.guardian,
    )
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.keepsake:
            bits.append("keepsake=True")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="market", activity="junket", item="gauge", name="Mina", gender="girl", guardian="mother"),
    StoryParams(place="porch", activity="junket", item="gauge", name="Owen", gender="boy", guardian="grandpa"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for triple in asp_valid_stories():
            print(" ".join(triple))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 20, 20):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
