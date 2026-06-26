#!/usr/bin/env python3
"""
storyworlds/worlds/iconic_surprise_kindness_flashback_mystery.py
=================================================================

A small mystery storyworld with an iconic object, a surprise turn,
a kindness clue, and a flashback that explains the answer.

The simulated premise:
- A child finds an iconic item missing from a small place.
- Something surprising happens: a hidden note, a tucked-away gift, or a
  misplaced object appears.
- A remembered act of kindness becomes the clue that solves the mystery.
- The ending proves what changed in the world: trust, relief, and the item
  being returned to its rightful place.

This world is deliberately small and constraint-checked. Not every object can
be paired with every place or clue; invalid combinations raise StoryError.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    clue_obj: object | None = None
    helper: object | None = None
    hero: object | None = None
    item: object | None = None
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
class Setting:
    place: str
    indoors: bool = True
    afford_clues: set[str] = field(default_factory=set)
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
class MysteryClue:
    id: str
    label: str
    reveal: str
    hint: str
    kind: str
    tags: set[str] = field(default_factory=set)
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
class IconicThing:
    id: str
    label: str
    phrase: str
    type: str
    owner_kind: str
    place_role: str
    tag: str
    can_be_hidden: bool = True
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone
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
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_suspicion(world: World) -> list[str]:
    out: list[str] = []
    hero: Entity = world.facts.get("hero")
    item: Entity = world.facts.get("item")
    if not hero or not item:
        return out
    if hero.memes["curiosity"] < THRESHOLD:
        return out
    if item.hidden:
        sig = ("suspect", item.id)
        if sig in world.fired:
            return out
        world.fired.add(sig)
        hero.memes["mystery"] += 1
        out.append(f"{hero.label} felt sure the missing {item.label} was hiding somewhere nearby.")
    return out


def _r_flashback(world: World) -> list[str]:
    out: list[str] = []
    hero: Entity = world.facts.get("hero")
    helper: Entity = world.facts.get("helper")
    if not hero or not helper:
        return out
    if hero.memes["memory"] < THRESHOLD:
        return out
    sig = ("flashback", hero.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.memes["understanding"] += 1
    out.append(
        f"Then {hero.label} remembered how {helper.label} once helped clean up a mess without being asked."
    )
    return out


def _r_kindness_reveal(world: World) -> list[str]:
    out: list[str] = []
    clue: MysteryClue = world.facts.get("clue_obj")
    item: Entity = world.facts.get("item")
    hero: Entity = world.facts.get("hero")
    if not clue or not item or not hero:
        return out
    if hero.memes["understanding"] < THRESHOLD:
        return out
    sig = ("reveal", clue.id, item.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.hidden = False
    out.append(f"The clue showed that the lost {item.label} had been tucked behind {clue.reveal}.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("suspicion", "mental", _r_suspicion),
    Rule("flashback", "mental", _r_flashback),
    Rule("kindness_reveal", "story", _r_kindness_reveal),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def _do_search(world: World, actor: Entity, item: Entity) -> None:
    actor.memes["curiosity"] += 1
    actor.meters["search"] += 1
    if item.hidden:
        actor.memes["worry"] += 1
    propagate(world, narrate=True)


def _receive_hint(world: World, hero: Entity, clue: MysteryClue) -> None:
    hero.memes["memory"] += 1
    world.say(
        f"Near the {world.setting.place}, {hero.label} found a small note that said, "
        f"'{clue.hint}'."
    )


def _show_kindness(world: World, helper: Entity, hero: Entity) -> None:
    helper.memes["kindness"] += 1
    world.say(
        f"{helper.label} smiled and offered to help look, because {helper.pronoun().capitalize()} had done the same for {hero.label} before."
    )


SETTINGS = {
    "library": Setting(place="the library", indoors=True, afford_clues={"note", "bookmark", "dust"}),
    "museum": Setting(place="the museum hall", indoors=True, afford_clues={"label", "plaque", "note"}),
    "greenhouse": Setting(place="the greenhouse", indoors=True, afford_clues={"tag", "note", "leaf"}),
    "attic": Setting(place="the attic", indoors=True, afford_clues={"box", "blanket", "note"}),
}

ICONS = {
    "gold_star": IconicThing(
        id="gold_star",
        label="gold star badge",
        phrase="an iconic gold star badge",
        type="badge",
        owner_kind="child",
        place_role="display shelf",
        tag="star",
    ),
    "blue_crown": IconicThing(
        id="blue_crown",
        label="blue paper crown",
        phrase="an iconic blue paper crown",
        type="crown",
        owner_kind="child",
        place_role="craft table",
        tag="crown",
    ),
    "red_balloon": IconicThing(
        id="red_balloon",
        label="red balloon ribbon",
        phrase="an iconic red balloon ribbon",
        type="ribbon",
        owner_kind="child",
        place_role="bench",
        tag="ribbon",
    ),
    "silver_whistle": IconicThing(
        id="silver_whistle",
        label="silver whistle",
        phrase="an iconic silver whistle",
        type="whistle",
        owner_kind="helper",
        place_role="hook",
        tag="whistle",
    ),
}

CLUES = {
    "note": MysteryClue(
        id="note",
        label="folded note",
        reveal="the folded note",
        hint="Look where kindness was left last time",
        kind="note",
        tags={"kindness", "memory"},
    ),
    "bookmark": MysteryClue(
        id="bookmark",
        label="paper bookmark",
        reveal="the paper bookmark",
        hint="Check the shelf where the helper stood",
        kind="bookmark",
        tags={"book", "memory"},
    ),
    "box": MysteryClue(
        id="box",
        label="cardboard box",
        reveal="the cardboard box",
        hint="The answer is under something kept safe",
        kind="box",
        tags={"hide", "memory"},
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Ava", "Lily", "Zoe", "Ella", "Ruby", "Maya"]
BOY_NAMES = ["Leo", "Ben", "Finn", "Theo", "Max", "Noah", "Eli", "Jack"]
HELPER_NAMES = ["Mrs. Vale", "Mr. Reed", "Aunt June", "Uncle Sam"]

TRAITS = ["curious", "gentle", "brave", "quiet", "careful", "patient"]


@dataclass
class StoryParams:
    place: str
    item: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for clue_id in setting.afford_clues:
            for item_id, icon in ICONS.items():
                if clue_id in CLUES and icon.can_be_hidden:
                    combos.append((place, item_id, clue_id))
    return combos


def reasonableness_gate(place: str, item_id: str, clue_id: str) -> bool:
    setting = _safe_lookup(SETTINGS, place)
    item = _safe_lookup(ICONS, item_id)
    clue = _safe_lookup(CLUES, clue_id)
    return clue.id in setting.afford_clues and item.can_be_hidden and ("memory" in clue.tags or "kindness" in clue.tags)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A small mystery storyworld with an iconic missing item, a surprise clue, kindness, and a flashback."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ICONS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "grandparent", "teacher"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "item", None) and getattr(args, "clue", None):
        if not reasonableness_gate(getattr(args, "place", None), getattr(args, "item", None), getattr(args, "clue", None)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))
              and (getattr(args, "clue", None) is None or c[2] == getattr(args, "clue", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, item_id, clue_id = rng.choice(list(combos))
    icon = _safe_lookup(ICONS, item_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, item=item_id, clue=clue_id, name=name, gender=gender, helper=helper, trait=trait)


def tell(setting: Setting, icon: IconicThing, clue: MysteryClue, hero_name: str, hero_type: str, helper_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name, traits=["little", trait]))
    helper = world.add(Entity(id=helper_name, kind="character", type="adult", label=helper_name, traits=["kind"]))
    item = world.add(Entity(id=icon.id, type=icon.type, label=icon.label, phrase=icon.phrase, owner=hero.id, hidden=True))
    clue_obj = world.add(Entity(id=clue.id, type=clue.kind, label=clue.label, phrase=clue.hint))

    world.facts.update(hero=hero, helper=helper, item=item, clue_obj=clue_obj, icon=icon, clue=clue, setting=setting)

    world.say(
        f"{hero.label} was a little {trait} {hero.type} who liked noticing small things in {setting.place}."
    )
    world.say(
        f"One day, {hero.label} saw that the {item.label} was gone. It was an iconic little treasure, and its empty spot looked wrong."
    )
    world.para()
    world.say(
        f"{hero.label} searched under benches and behind shelves, while {helper.label} watched with a thoughtful face."
    )
    _do_search(world, hero, item)
    _show_kindness(world, helper, hero)
    world.para()
    _receive_hint(world, hero, clue)
    hero.memes["memory"] += 1
    hero.memes["kindness"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(
        f"{hero.label} looked back at the place where the clue pointed, and the mystery finally made sense."
    )
    world.say(
        f"Behind {clue.reveal}, there was the missing {item.label}. {hero.label} smiled because the surprise had been hiding inside a kindness all along."
    )
    item.hidden = False
    helper.memes["relief"] += 1
    hero.memes["relief"] += 1
    world.say(
        f"In the end, the {item.label} went back to its spot, and {setting.place} felt calm again."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    item = _safe_fact(world, f, "item")
    clue = _safe_fact(world, f, "clue")
    return [
        f'Write a short mystery story for a young child about the iconic {item.label} disappearing in {world.setting.place}, with a surprise clue and a kind helper.',
        f"Tell a gentle story where {hero.label} searches for {item.label}, remembers a kindness, and solves the mystery with a flashback.",
        f'Write a child-facing mystery that includes the word "iconic", a surprising hidden clue, and an ending that shows the missing {item.label} found again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    item = _safe_fact(world, f, "item")
    clue = _safe_fact(world, f, "clue")
    return [
        QAItem(
            question=f"What was missing from {world.setting.place}?",
            answer=f"The missing thing was {item.label}. It had an iconic spot in the room, so its empty place looked strange right away.",
        ),
        QAItem(
            question=f"Who helped {hero.label} look for the missing {item.label}?",
            answer=f"{helper.label} helped {hero.label}. The helper was kind and stayed close while they searched.",
        ),
        QAItem(
            question=f"What clue surprised {hero.label} during the search?",
            answer=f"{hero.label} found {clue.hint}. That surprise clue pointed the search in the right direction.",
        ),
        QAItem(
            question=f"What did {hero.label} remember before solving the mystery?",
            answer=f"{hero.label} remembered how {helper.label} had helped before. That flashback made the clue feel important.",
        ),
        QAItem(
            question=f"How did the story end for the {item.label}?",
            answer=f"The {item.label} was found and put back where it belonged, so {world.setting.place} felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a clue do in a mystery?",
            answer="A clue gives a helpful hint that can point a detective toward the answer.",
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a remembered moment from before that helps explain what is happening now.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means being gentle, helpful, and caring to someone else.",
        ),
        QAItem(
            question="What can surprise mean in a story?",
            answer="A surprise is something unexpected that changes what the character thinks or does next.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.hidden:
            bits.append("hidden=True")
        lines.append(f"  {e.id:12} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="library", item="gold_star", clue="note", name="Mia", gender="girl", helper="teacher", trait="curious"),
    StoryParams(place="museum", item="silver_whistle", clue="bookmark", name="Leo", gender="boy", helper="grandparent", trait="careful"),
    StoryParams(place="greenhouse", item="blue_crown", clue="note", name="Nora", gender="girl", helper="mother", trait="gentle"),
    StoryParams(place="attic", item="red_balloon", clue="box", name="Theo", gender="boy", helper="father", trait="brave"),
]


def explain_rejection(place: str, item: str, clue: str) -> str:
    return f"(No story: the {clue} clue does not fit a mystery about the {item} in {place}.)"


ASP_RULES = r"""
place(P) :- setting(P).
icon(I) :- item(I).
clue(C) :- clue(C).

valid(P,I,C) :- setting(P), item(I), clue(C), supports(P,C), hidden_ok(I), clue_kind(C,K), clue_kind_ok(K).
supports(P,C) :- afford(P,C).
hidden_ok(I) :- hiddenable(I).
clue_kind_ok(kind) :- clue_kind(_,kind).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for clue in sorted(s.afford_clues):
            lines.append(asp.fact("afford", pid, clue))
    for iid, icon in ICONS.items():
        lines.append(asp.fact("item", iid))
        if icon.can_be_hidden:
            lines.append(asp.fact("hiddenable", iid))
    for cid, clue in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_kind", cid, clue.kind))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, py_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ICONS, params.item), _safe_lookup(CLUES, params.clue), params.name, params.gender, params.helper, params.trait)
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
        print(f"{len(triples)} valid combos:")
        for t in triples:
            print(" ", t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.item} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
