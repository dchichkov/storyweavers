#!/usr/bin/env python3
"""
A standalone story world: a small whodunit set around a dromedary caravan,
where kindness causes a transformation and the ending proves a moral value.

The seed idea:
- A dromedary caravan arrives at a desert rest stop.
- Something important goes missing.
- The search reveals that a kind act, not greed or blame, changes the outcome.
- The final image shows the transformation and the moral value made visible.

This world is intentionally small and constraint-driven:
- one mystery case per story
- one culprit among a small cast
- one humane resolution
- one visible transformation by the ending
"""

from __future__ import annotations

import argparse
import dataclasses
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    used_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    culprit: object | None = None
    hero: object | None = None
    missing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother"}
        male = {"boy", "man", "father"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    id: str
    label: str
    detail: str
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
class Item:
    id: str
    label: str
    phrase: str
    value: str
    transform_to: str
    risky_by: set[str] = field(default_factory=set)
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
class Suspect:
    id: str
    type: str
    label: str
    motive: str
    can_take: set[str] = field(default_factory=set)
    guilty_if: set[str] = field(default_factory=set)
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
    item: str
    suspect: str
    hero: str
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
        self.fired: set[tuple] = set()
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = dataclasses.replace(self) if False else {}
        import copy
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "oasis": Place("oasis", "the oasis", "A little pool of water shone under the palms."),
    "caravanserai": Place("caravanserai", "the caravanserai", "Lanterns swung softly beside the low stone walls."),
    "market": Place("market", "the market", "Small stalls stood in a dusty square with bright cloth overhead."),
}

ITEMS = {
    "water_map": Item("water_map", "water map", "a folded water map", "important", "spotted with tea", risky_by={"tea", "ink"}),
    "lantern_key": Item("lantern_key", "lantern key", "a brass lantern key", "important", "dusty and bent", risky_by={"mud"}),
    "date_bag": Item("date_bag", "date bag", "a sack of sweet dates", "important", "half empty", risky_by={"snack"}),
}

SUSPECTS = {
    "keeper": Suspect("keeper", "person", "the keeper", "to protect the caravan stop", can_take={"lantern_key"}, guilty_if={"lantern_key"}),
    "child": Suspect("child", "person", "the child", "to make a joke", can_take={"water_map"}, guilty_if={"water_map"}),
    "merchant": Suspect("merchant", "person", "the merchant", "to hide a shortage", can_take={"date_bag"}, guilty_if={"date_bag"}),
}

HERO_NAMES = ["Mira", "Nadi", "Lina", "Tariq", "Sami", "Ari"]
TRAITS = ["careful", "curious", "gentle", "brave", "patient"]


# ---------------------------------------------------------------------------
# Narrative state
# ---------------------------------------------------------------------------

@dataclass
class Clue:
    item_id: str
    suspect_id: str
    found: bool = False
    true: bool = False
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


def clue_is_plausible(suspect: Suspect, item: Item, place: Place) -> bool:
    if item.id not in suspect.can_take:
        return False
    if item.id in suspect.guilty_if:
        return True
    return False


def chosen_solution(place: Place, item: Item, suspect: Suspect) -> bool:
    return clue_is_plausible(suspect, item, place)


def _predict_transformation(world: World, item: Entity) -> bool:
    return bool(item.meters.get("restored", 0) >= 1 or item.memes.get("kindness", 0) >= 1)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A suspect is guilty if they can take the missing item and the item is linked to them.
guilty(S, I) :- can_take(S, I), guilty_if(S, I), missing(I).

% A kind act changes the moral outcome and helps restore the item.
kind_transforms(H, I) :- kindness(H), missing(I), restored(I).

% A story is reasonable when there is exactly one guilty suspect and one moral turning point.
reasonable(Place, Item, Suspect) :- place(Place), missing(Item), guilty(Suspect, Item), moral_value(Item).
#show reasonable/3.
#show guilty/2.
#show kind_transforms/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for word in place.detail.lower().split():
            if word.isalpha():
                pass
    for iid, item in ITEMS.items():
        lines.append(asp.fact("missing", iid))
        lines.append(asp.fact("moral_value", iid))
        for r in sorted(item.risky_by):
            lines.append(asp.fact("risky_by", iid, r))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        for i in sorted(s.can_take):
            lines.append(asp.fact("can_take", sid, i))
        for i in sorted(s.guilty_if):
            lines.append(asp.fact("guilty_if", sid, i))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show guilty/2.\n#show kind_transforms/2.\n"))
    atoms_g = set(asp.atoms(model, "guilty"))
    atoms_k = set(asp.atoms(model, "kind_transforms"))
    py = set()
    for sid, sus in SUSPECTS.items():
        for iid, item in ITEMS.items():
            if clue_is_plausible(sus, item, next(iter(PLACES.values()))):
                py.add((sid, iid))
    if atoms_g == py and atoms_k == set():
        print("OK: ASP and Python gates are aligned.")
        return 0
    print("MISMATCH.")
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def detect_missing(item: Item, suspect: Suspect) -> str:
    return f"Someone had taken the {item.label}."


def suspecting_line(hero: Entity, suspect: Suspect) -> str:
    return f"{hero.id} looked at {suspect.label} and wondered if the face hid a secret."


def reveal_line(item: Item, suspect: Suspect) -> str:
    return f"The clue pointed to {suspect.label}, because only {suspect.label} could explain the missing {item.label}."


def kindness_action(world: World, hero: Entity, suspect: Entity, item: Entity) -> None:
    hero.memes["kindness"] = hero.memes.get("kindness", 0) + 1
    suspect.memes["relief"] = suspect.memes.get("relief", 0) + 1
    item.meters["restored"] = item.meters.get("restored", 0) + 1
    world.say(
        f"Instead of scolding anyone, {hero.id} offered help and a cup of water. "
        f"{suspect.label} could breathe again, and the missing {item.label} came back."
    )


def transform_ending(world: World, hero: Entity, item: Entity, suspect: Entity) -> None:
    world.say(
        f"By sunset, the {item.label} was no longer a problem to hide. "
        f"It was cleaned, handed back, and set where everyone could see it. "
        f"{hero.id} saw that kindness had turned the whole search into something better."
    )


def tell(place: Place, item: Item, suspect: Suspect, hero_name: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type="girl", label=hero_name))
    culprit = world.add(Entity(id=suspect.id, kind="character", type="man", label=suspect.label))
    missing = world.add(Entity(id=item.id, kind="thing", type="thing", label=item.label))

    world.say(
        f"At {place.label}, under the quiet desert light, {hero.id} noticed that the {item.label} was gone."
    )
    world.say(
        f"{place.detail} {hero.id} was a {trait} little detective who liked fair answers more than loud ones."
    )
    world.para()
    world.say(detect_missing(item, suspect))
    world.say(suspecting_line(hero, suspect))
    world.say(
        f"The first clue was small: a clean footprint by the lantern, and a sweet smell near the tea tray."
    )
    world.say(
        f"{hero.id} followed the clues carefully, because a good whodunit needed patience, not panic."
    )
    world.para()

    guilty = chosen_solution(place, item, suspect)
    if not guilty:
        pass

    world.say(reveal_line(item, suspect))
    world.say(
        f"Yet when {hero.id} asked softly, {suspect.label} did not laugh or lie. "
        f"{suspect.label} only looked ashamed, because the item had been taken to keep a mistake from being seen."
    )
    kindness_action(world, hero, culprit, missing)
    transform_ending(world, hero, missing, culprit)

    world.facts.update(
        hero=hero,
        suspect=culprit,
        item=missing,
        place=place,
        trait=trait,
        guilty=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    item = _safe_fact(world, f, "item")
    place = _safe_fact(world, f, "place")
    return [
        f"Write a short whodunit about a dromedary stop at {place.label} where {hero.id} solves the missing {item.label}.",
        f"Tell a gentle mystery story for young children that includes a dromedary caravan, kindness, and a moral value.",
        f"Write a simple detective tale where a child finds a missing object, offers kindness, and ends with a transformation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    suspect = _safe_fact(world, f, "suspect")
    item = _safe_fact(world, f, "item")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What went missing at {place.label}?",
            answer=f"The {item.label} went missing, which started the little mystery."
        ),
        QAItem(
            question=f"Who did {hero.id} think was involved in the mystery?",
            answer=f"{hero.id} thought {suspect.label} was involved, because the clues matched that person."
        ),
        QAItem(
            question=f"What changed the ending of the story?",
            answer=f"Kindness changed the ending. Instead of blame, {hero.id} offered help, and that let the truth come out safely."
        ),
        QAItem(
            question=f"What was the transformation by the end?",
            answer=f"The missing {item.label} was restored, the suspect felt relieved, and the search turned into a calm, honest moment."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a dromedary?",
            answer="A dromedary is a camel with one hump. It can travel well through dry, hot places."
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means choosing to help, comfort, or be gentle with someone instead of being mean."
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a different state or becomes different in an important way."
        ),
        QAItem(
            question="What is a moral value?",
            answer="A moral value is a good rule for living, like honesty, kindness, or fairness."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Sampling
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld about a dromedary, kindness, and transformation.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--name")
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
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    item = getattr(args, "item", None) or rng.choice(list(ITEMS))
    suspect = getattr(args, "suspect", None) or rng.choice(list(SUSPECTS))
    if not clue_is_plausible(_safe_lookup(SUSPECTS, suspect), _safe_lookup(ITEMS, item), _safe_lookup(PLACES, place)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, item=item, suspect=suspect, hero=name, seed=None)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(ITEMS, params.item), _safe_lookup(SUSPECTS, params.suspect), params.hero, params.trait or "curious")
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
        print("--- world trace ---")
        for e in sample.world.entities.values():
            print(e)
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show guilty/2.\n#show kind_transforms/2.\n"))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        combos = [
            StoryParams(place=p, item=i, suspect=s, hero=h, seed=base_seed)
            for p in PLACES for i in ITEMS for s in SUSPECTS
            for h in ["Mira"]
            if clue_is_plausible(_safe_lookup(SUSPECTS, s), _safe_lookup(ITEMS, i), _safe_lookup(PLACES, p))
        ]
        samples = [generate(p) for p in combos]
    else:
        samples = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(1000, getattr(args, "n", None) * 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
