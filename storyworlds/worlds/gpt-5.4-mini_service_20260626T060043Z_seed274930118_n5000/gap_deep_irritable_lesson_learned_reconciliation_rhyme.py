#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gap_deep_irritable_lesson_learned_reconciliation_rhyme.py
=================================================================================================

A small mystery-flavored storyworld about a child, a deep gap, an irritable
clue-keeper, a learned lesson, and a rhyming reconciliation.

The seed tale behind this world imagines a child who finds a deep gap in a
garden path, gets irritable when the answer is not obvious, follows a rhyme as a
clue, and ends by learning not to accuse too fast. The story world turns those
beats into a compact simulation:

* physical meters:
  - distance to the answer
  - gap depth / bridge safety / clue clarity
  - object state such as missing / found / returned

* emotional memes:
  - curiosity, worry, irritability, trust, relief, harmony, pride

The mystery style comes from:
* a hidden cause that must be inferred from clues
* a cautious reveal instead of an instant fix
* a final lesson learned, plus reconciliation with the misunderstood helper
* a short rhyme that helps solve the puzzle

The domain stays intentionally small so each story feels like a complete little
case: beginning, suspicion, clue, turn, resolution.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import re
import sys
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0

NAMES = ["Mina", "Toby", "Lena", "Arlo", "Nia", "Pip", "Sora", "Juno"]
HELPER_NAMES = ["Moss", "Aunt Bea", "Mr. Wren", "Kite", "Nell"]
PLACES = ["the old garden", "the quiet lane", "the stone bridge", "the back yard"]
OBJECTS = ["silver key", "blue bead", "tiny bell", "red ribbon", "little lantern"]
MOODS = ["curious", "irritable", "patient", "careful", "brave"]
LESSONS = [
    "look twice before blaming someone",
    "follow the clue before you leap",
    "ask a kind question before you decide",
]
RHYMES = [
    "When the gap looks wide and deep, listen close and clues will keep.",
    "If a mystery feels quite stark, follow rhyme and find the spark.",
    "When the path is split in two, a careful song can guide you through.",
]



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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    keeper: Optional[str] = None
    hidden_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    helper: object | None = None
    hero: object | None = None
    hint: object | None = None
    missing: object | None = None
    solves: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "uncle"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Setting:
    place: str
    gap_name: str
    deep: bool = True
    affords: set[str] = field(default_factory=set)
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
class Clue:
    label: str
    phrase: str
    kind: str
    hint: str
    solves: str
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
    name: str = ""
    helper: str = ""
    object: str = ""
    mood: str = ""
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


class World:
    def __init__(self, setting: Setting):
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
            self.trace.append(text)

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
        return clone


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def rhyme_clue(text: str) -> str:
    return text.rstrip(".") + "."


def mystery_introduction(world: World, hero: Entity, helper: Entity, missing: Entity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} child who lived near {world.setting.place}."
    )
    world.say(
        f"One morning, something was wrong: {missing.phrase} was gone, and a deep gap "
        f"cut the path beside {world.setting.gap_name}."
    )
    world.say(
        f"{hero.id} felt irritable because the answer did not show itself right away."
    )
    world.say(
        f"{helper.id} watched quietly, as if they knew the garden wanted a careful eye."
    )


def suspicion_turn(world: World, hero: Entity, helper: Entity, missing: Entity, clue: Entity) -> None:
    hero.memes["irritable"] += 1
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} spotted {clue.phrase} and guessed, perhaps too fast, that {helper.id} "
        f"must have hidden {(getattr(missing, 'it')() if callable(getattr(missing, 'it', None)) else getattr(missing, 'it', 'it'))}."
    )
    helper.memes["hurt"] += 1
    helper.memes["trust"] += 0.5
    world.say(
        f"{helper.id} looked hurt, and the air between them felt tight and gray."
    )


def follow_clue(world: World, hero: Entity, clue: Entity, bridge_ok: bool) -> None:
    world.say(
        f"Then {hero.id} remembered a short rhyme: \"{clue.phrase}\""
    )
    if bridge_ok:
        world.say(
            f"The rhyme pointed toward the narrow plank across the deep gap, where {clue.hint}."
        )
    else:
        world.say(
            f"The rhyme pointed toward the gap, but the path still looked too risky to cross."
        )


def reveal(world: World, hero: Entity, helper: Entity, missing: Entity, clue: Entity) -> None:
    helper.memes["hurt"] -= 0.5
    helper.memes["trust"] += 1
    hero.memes["curiosity"] += 0.5
    world.say(
        f"At last, {hero.id} saw the truth: {clue.hint}, and {missing.phrase} was not stolen at all."
    )
    world.say(
        f"It had slipped beside the deep gap and waited where only a careful search could find it."
    )


def reconciliation(world: World, hero: Entity, helper: Entity, missing: Entity) -> None:
    hero.memes["irritable"] = 0.0
    hero.memes["trust"] += 1
    hero.memes["relief"] += 1
    helper.memes["harmony"] += 1
    world.say(
        f"{hero.id} turned red with shame, then said, \"I was wrong to blame you.\""
    )
    world.say(
        f"{helper.id} smiled and helped lift {(getattr(missing, 'it')() if callable(getattr(missing, 'it', None)) else getattr(missing, 'it', 'it'))} back into safe hands."
    )
    world.say(
        f"After that, the garden felt softer, and the deep gap seemed less scary."
    )


def lesson_learned(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} learned to {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "lesson")}."
    )
    world.say(
        f"From then on, {hero.id} listened first, and the mystery felt smaller when it came back."
    )


def tell(setting: Setting, params: StoryParams) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.name in {"Mina", "Lena", "Nia", "Juno"} else "boy",
        traits=[params.mood, "careful"],
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="aunt" if params.helper == "Aunt Bea" else "man" if params.helper == "Mr. Wren" else "person",
        traits=["quiet", "patient"],
    ))
    missing = world.add(Entity(
        id="missing",
        type="thing",
        label=params.object,
        phrase=f"the {params.object}",
        owner=hero.id,
        keeper=helper.id,
        meters={"lost": 1.0},
    ))
    clue = world.add(Entity(
        id="clue",
        type="thing",
        label="rhyming note",
        phrase=random.choice(RHYMES),
        kind="rhyme",
        hint=f"a little scratch of mud on the plank and a faint clink below",
        solves=missing.id,
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        missing=missing,
        clue=clue,
        lesson=random.choice(LESSONS),
        bridge_safe=True,
    )

    mystery_introduction(world, hero, helper, missing)
    world.para()
    suspicion_turn(world, hero, helper, missing, clue)
    world.para()
    follow_clue(world, hero, clue, True)
    reveal(world, hero, helper, missing, clue)
    world.para()
    reconciliation(world, hero, helper, missing)
    lesson_learned(world, hero, helper)
    return world


SETTINGS = {
    "garden": Setting(place="the old garden", gap_name="the stone border gap", deep=True, affords={"rhyme", "lesson", "reconciliation"}),
    "lane": Setting(place="the quiet lane", gap_name="the drainage gap", deep=True, affords={"rhyme", "lesson", "reconciliation"}),
    "bridge": Setting(place="the stone bridge", gap_name="the cracked span gap", deep=True, affords={"rhyme", "lesson", "reconciliation"}),
}

PRIZES = OBJECTS[:]
HELPERS = HELPER_NAMES[:]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for prize in PRIZES:
            combos.append((place, "mystery", prize))
    return combos


@dataclass
class StoryParams:
    place: str = ""
    name: str = ""
    helper: str = ""
    object: str = ""
    mood: str = ""
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Mystery storyworld about a deep gap, an irritable moment, a rhyme clue, and reconciliation."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--object", dest="object_name", choices=PRIZES)
    ap.add_argument("--mood", choices=MOODS)
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    obj = getattr(args, "object_name", None) or rng.choice(PRIZES)
    mood = getattr(args, "mood", None) or rng.choice(MOODS)
    if helper == name:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, name=name, helper=helper, object=obj, mood=mood)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a child-friendly mystery about a deep gap, an irritable mistake, and a rhyming clue in {world.setting.place}.",
        f"Tell a short story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} blames {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper").id} for losing {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "missing").phrase}, then learns the truth.",
        "Write a small mystery that ends with reconciliation and a lesson learned.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, missing = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper"), _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "missing")
    return [
        QAItem(
            question=f"What was {hero.id} feeling at the start of the story?",
            answer=f"{hero.id} felt curious but also irritable because the answer was not obvious.",
        ),
        QAItem(
            question=f"What did {hero.id} think at first about {helper.id}?",
            answer=f"At first, {hero.id} wrongly thought {helper.id} had hidden {missing.phrase}.",
        ),
        QAItem(
            question="What helped solve the mystery?",
            answer=f"A short rhyme helped {hero.id} follow the clue and find where {missing.phrase} had slipped.",
        ),
        QAItem(
            question="What changed at the end?",
            answer=f"{hero.id} apologized, {helper.id} forgave them, and they reconciled after the truth came out.",
        ),
        QAItem(
            question="What lesson was learned?",
            answer=f"{hero.id} learned to {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "lesson")}.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a gap?",
            answer="A gap is an opening or missing space between two things.",
        ),
        QAItem(
            question="What does irritable mean?",
            answer="Irritable means easily annoyed or quick to feel upset.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a pattern of words that sound alike at the end, like song lines or a little chant.",
        ),
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people stop being upset and become friendly again.",
        ),
        QAItem(
            question="What is a lesson learned?",
            answer="A lesson learned is the useful idea someone understands after something goes wrong.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = []
    for title, items in [
        ("(1) Generation prompts", sample.prompts),
        ("(2) Story questions", sample.story_qa),
        ("(3) World questions", sample.world_qa),
    ]:
        lines.append(f"== {title} ==")
        for i, item in enumerate(items, 1):
            if isinstance(item, str):
                lines.append(f"{i}. {item}")
            else:
                lines.append(f"Q: {item.question}")
                lines.append(f"A: {item.answer}")
        lines.append("")
    return "\n".join(lines).rstrip()


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if setting.deep:
            lines.append(asp.fact("deep", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for obj in PRIZES:
        lines.append(asp.fact("object", obj))
    for name in NAMES:
        lines.append(asp.fact("name", name))
    for helper in HELPERS:
        lines.append(asp.fact("helper", helper))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,O) :- place(P), object(O).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    py = set((p, o) for p, _, o in valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    world = tell(setting, params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(place="garden", name="Mina", helper="Moss", object="silver key", mood="curious"),
    StoryParams(place="lane", name="Toby", helper="Aunt Bea", object="tiny bell", mood="irritable"),
    StoryParams(place="bridge", name="Lena", helper="Mr. Wren", object="blue bead", mood="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        for c in combos:
            print(c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(100, getattr(args, "n", None) * 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
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
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False, default=str))
        return

    for i, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name} at {p.place} with {p.helper} ({p.object})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
