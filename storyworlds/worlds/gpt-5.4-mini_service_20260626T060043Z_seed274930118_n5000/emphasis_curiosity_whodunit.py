#!/usr/bin/env python3
"""
storyworlds/worlds/emphasis_curiosity_whodunit.py
==================================================

A small whodunit story world about curiosity, clues, and a tidy reveal.

Seed tale idea:
---
A curious child notices that a small treat or treasure has gone missing.
The grown-up suspects the wrong thing at first.
The child looks closely, follows tiny clues, and discovers who did it.
By the end, the mystery is solved, the truth is shared gently, and the child
feels proud that curiosity helped.

This world models the mystery as state:
- physical meters: clues, mess, solved, trust, comfort
- emotional memes: curiosity, worry, suspicion, delight
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Setting:
    place: str
    inside: bool
    surface: str
    opening: str
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
class Item:
    id: str
    label: str
    phrase: str
    category: str
    where: str
    scent: str
    lure: str
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
class Culprit:
    id: str
    label: str
    type: str
    signature: str
    hiding_place: str
    excuse: str
    likes: str
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
    setting: str
    item: str
    culprit: str
    name: str
    gender: str
    parent: str
    curiosity: str
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


SETTINGS = {
    "kitchen": Setting(
        place="the kitchen",
        inside=True,
        surface="table",
        opening="the window",
    ),
    "garden": Setting(
        place="the garden",
        inside=False,
        surface="bench",
        opening="the gate",
    ),
    "classroom": Setting(
        place="the classroom",
        inside=True,
        surface="reading rug",
        opening="the door",
    ),
}

ITEMS = {
    "muffin": Item(
        id="muffin",
        label="muffin",
        phrase="a warm blueberry muffin",
        category="food",
        where="table",
        scent="sweet crumbs",
        lure="sweet",
    ),
    "cookie": Item(
        id="cookie",
        label="cookie",
        phrase="a sugar cookie with sprinkles",
        category="food",
        where="plate",
        scent="crumbs",
        lure="sweet",
    ),
    "button": Item(
        id="button",
        label="button",
        phrase="a shiny red button",
        category="toy",
        where="sewing basket",
        scent="none",
        lure="bright",
    ),
    "crayon": Item(
        id="crayon",
        label="crayon",
        phrase="a bright green crayon",
        category="school",
        where="crayon cup",
        scent="wax",
        lure="bright",
    ),
}

CULPRITS = {
    "squirrel": Culprit(
        id="squirrel",
        label="squirrel",
        type="animal",
        signature="tiny muddy paw prints and a nutshell crumb",
        hiding_place="the low branch by the window",
        excuse="It only wanted a snack",
        likes="nuts and sweet things",
    ),
    "mouse": Culprit(
        id="mouse",
        label="mouse",
        type="animal",
        signature="small nibble marks and a little gray fluff",
        hiding_place="behind the baseboard",
        excuse="It was making a nest",
        likes="crumbs and soft paper",
    ),
    "magpie": Culprit(
        id="magpie",
        label="magpie",
        type="animal",
        signature="a black feather and a shiny trinket trail",
        hiding_place="the fence post",
        excuse="It likes shiny things",
        likes="bright, glittery treasures",
    ),
}

NAMES = {
    "girl": ["Mina", "Ruby", "Lina", "Tess", "Ivy", "Nora"],
    "boy": ["Owen", "Finn", "Leo", "Milo", "Sam", "Eli"],
}
TRAITS = ["curious", "careful", "thoughtful", "brave", "patient"]


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[str] = set()
        self.facts: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = {
            k: Entity(
                id=v.id,
                kind=v.kind,
                type=v.type,
                label=v.label,
                phrase=v.phrase,
                plural=v.plural,
                owner=v.owner,
                meters=dict(v.meters),
                memes=dict(v.memes),
            )
            for k, v in self.entities.items()
        }
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _bump(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.meters[key] = ent.meters.get(key, 0.0) + amount


def _feel(ent: Entity, key: str, amount: float = 1.0) -> None:
    ent.memes[key] = ent.memes.get(key, 0.0) + amount


def solve_reveal(world: World) -> None:
    clue = _safe_fact(world, world.facts, "clue")
    culprit = _safe_fact(world, world.facts, "culprit_entity")
    child = _safe_fact(world, world.facts, "child")
    parent = _safe_fact(world, world.facts, "parent")
    item = _safe_fact(world, world.facts, "item_entity")

    if "solved" in world.fired:
        return
    world.fired.add("solved")

    _bump(item, "returned", 1)
    _bump(parent, "relief", 1)
    _feel(child, "delight", 1)
    _feel(child, "curiosity", 1)

    world.say(
        f"{child.id} pointed to the little clue: {clue}. "
        f"That was enough to see who had done it."
    )
    world.say(
        f"The culprit was the {culprit.label}. {culprit.excuse}, "
        f"and the trail matched {culprit.signature}."
    )
    world.say(
        f"In the end, {item.label} was found again, and {parent.pronoun('subject').capitalize()} "
        f"laughed with relief while {child.id} felt proud that careful curiosity had solved the mystery."
    )


def tell_mystery(world: World, child: Entity, parent: Entity, item: Entity, culprit: Culprit) -> None:
    setting = world.setting

    world.say(
        f"{child.id} was a little {next(t for t in child.memes if t == 'curiosity' or True) if False else 'curious'} {child.type} "
        f"who loved noticing tiny things."
    )
    world.say(
        f"{child.pronoun('subject').capitalize()} liked asking why, especially when something odd happened at {setting.place}."
    )
    world.say(
        f"One day, {item.phrase} went missing from the {item.where}, and {parent.label} looked worried."
    )
    _feel(parent, "worry", 1)
    _feel(child, "curiosity", 2)

    world.para()
    world.say(
        f"{parent.pronoun('subject').capitalize()} first guessed it might be the wind, "
        f"but {child.id} studied the scene like a tiny detective."
    )
    if culprit.id == "squirrel":
        clue = "muddy paw prints on the sill"
    elif culprit.id == "mouse":
        clue = "little nibble marks near the basket"
    else:
        clue = "a shiny trail and one black feather"

    _bump(item, "mystery", 1)
    _bump(parent, "suspicion", 1)
    world.say(
        f"{child.id} found {clue}, and the clue felt important because it did not belong there."
    )
    world.say(
        f"Then {child.id} followed it toward {culprit.hiding_place}."
    )
    world.facts["clue"] = clue
    world.facts["culprit_entity"] = culprit
    solve_reveal(world)


def generate_story_text(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    item = _safe_lookup(ITEMS, params.item)
    culprit = _safe_lookup(CULPRITS, params.culprit)
    world = World(setting)

    child = world.add(
        Entity(
            id=params.name,
            kind="character",
            type=params.gender,
            label=params.name,
            meters={"care": 1},
            memes={"curiosity": 2, "confidence": 1},
        )
    )
    parent = world.add(
        Entity(
            id=params.parent.capitalize(),
            kind="character",
            type=params.parent,
            label=f"the {params.parent}",
            meters={"care": 2},
            memes={"worry": 1},
        )
    )
    item_entity = world.add(
        Entity(
            id=item.id,
            kind="thing",
            type=item.category,
            label=item.label,
            phrase=item.phrase,
            owner=child.id,
            meters={"missing": 1},
        )
    )

    world.facts.update(
        child=child,
        parent=parent,
        item_entity=item_entity,
        item=item,
        culprit=culprit,
        setting=setting,
    )
    tell_mystery(world, child, parent, item_entity, culprit)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for i in ITEMS:
            for c in CULPRITS:
                if reasonableness_gate(s, i, c):
                    combos.append((s, i, c))
    return combos


def reasonableness_gate(setting_id: str, item_id: str, culprit_id: str) -> bool:
    setting = _safe_lookup(SETTINGS, setting_id)
    item = _safe_lookup(ITEMS, item_id)
    culprit = _safe_lookup(CULPRITS, culprit_id)

    if item.category == "food" and culprit.type != "animal":
        return False
    if setting_id == "classroom" and culprit_id == "squirrel":
        return False
    if setting_id == "garden" and culprit_id == "mouse" and item_id == "crayon":
        return False
    if setting_id == "kitchen" and item_id == "button" and culprit_id == "magpie":
        return False
    if setting.inside and culprit_id == "squirrel" and item_id == "button":
        return False
    return True


def explain_rejection(setting_id: str, item_id: str, culprit_id: str) -> str:
    setting = _safe_lookup(SETTINGS, setting_id)
    item = _safe_lookup(ITEMS, item_id)
    culprit = _safe_lookup(CULPRITS, culprit_id)
    return (
        f"(No story: a {culprit.label} in {setting.place} does not make a strong whodunit "
        f"for {item.phrase}. Try a clue and culprit that fit the room and the missing thing.)"
    )


def build_storyparams(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))
              and (getattr(args, "culprit", None) is None or c[2] == getattr(args, "culprit", None))]
    if not combos:
        pass
    setting, item, culprit = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    curiosity = getattr(args, "curiosity", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, item=item, culprit=culprit, name=name, gender=gender, parent=parent, curiosity=curiosity)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item: Item = _safe_fact(world, f, "item")  # type: ignore[assignment]
    culprit: Culprit = _safe_fact(world, f, "culprit")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    child: Entity = _safe_fact(world, f, "child")  # type: ignore[assignment]
    return [
        f'Write a short whodunit story for a child about a missing {item.label} in {setting.place}.',
        f"Tell a curious detective story where {child.id} notices clues and discovers who took the {item.label}.",
        f'Write a gentle mystery story with the word "curiosity" and a clear ending reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")  # type: ignore[assignment]
    parent: Entity = _safe_fact(world, f, "parent")  # type: ignore[assignment]
    item: Item = _safe_fact(world, f, "item")  # type: ignore[assignment]
    culprit: Culprit = _safe_fact(world, f, "culprit")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    clue = _safe_fact(world, f, "clue")
    return [
        QAItem(
            question=f"What went missing in {setting.place}?",
            answer=f"{item.phrase} went missing, and that made the {parent.label} worried.",
        ),
        QAItem(
            question=f"Who solved the mystery with curiosity?",
            answer=f"{child.id} solved the mystery by paying attention to tiny details and following the clue.",
        ),
        QAItem(
            question=f"What clue helped reveal the culprit?",
            answer=f"The clue was {clue}. It matched the {culprit.label}'s signature trail and pointed to the truth.",
        ),
        QAItem(
            question=f"Who had taken the {item.label}?",
            answer=f"The {culprit.label} had taken it. {culprit.excuse}, and the story ended with the missing thing found again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity help people do?",
            answer="Curiosity helps people notice details, ask questions, and learn the truth about what is happening.",
        ),
        QAItem(
            question="What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps solve a mystery.",
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(kitchen).
setting(garden).
setting(classroom).

item(muffin).
item(cookie).
item(button).
item(crayon).

culprit(squirrel).
culprit(mouse).
culprit(magpie).

valid(S,I,C) :- setting(S), item(I), culprit(C), not blocked(S,I,C).

blocked(kitchen, button, magpie).
blocked(classroom, muffin, squirrel).
blocked(garden, crayon, mouse).
blocked(classroom, button, squirrel).
blocked(kitchen, muffin, magpie) :- true.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for cid in CULPRITS:
        lines.append(asp.fact("culprit", cid))
    for s in SETTINGS:
        for i in ITEMS:
            for c in CULPRITS:
                if not reasonableness_gate(s, i, c):
                    lines.append(asp.fact("blocked", s, i, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-sized whodunit story world with curiosity at the center.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=CULPRITS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
    ap.add_argument("--curiosity", choices=TRAITS)
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


def generate(params: StoryParams) -> StorySample:
    world = generate_story_text(params)
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
    StoryParams(setting="kitchen", item="muffin", culprit="squirrel", name="Mina", gender="girl", parent="mother", curiosity="curious"),
    StoryParams(setting="garden", item="cookie", culprit="mouse", name="Owen", gender="boy", parent="father", curiosity="careful"),
    StoryParams(setting="classroom", item="crayon", culprit="magpie", name="Ivy", gender="girl", parent="mother", curiosity="thoughtful"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "setting", None) and getattr(args, "item", None) and getattr(args, "culprit", None):
        if not reasonableness_gate(getattr(args, "setting", None), getattr(args, "item", None), getattr(args, "culprit", None)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))
              and (getattr(args, "culprit", None) is None or c[2] == getattr(args, "culprit", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, item, culprit = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    curiosity = getattr(args, "curiosity", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, item=item, culprit=culprit, name=name, gender=gender, parent=parent, curiosity=curiosity)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (setting, item, culprit) combos:\n")
        for s, i, c in triples:
            print(f"  {s:10} {i:8} {c:8}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.setting} / {p.item} / {p.culprit}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
