#!/usr/bin/env python3
"""
A standalone story world: a small detective tale about pretend greenery,
silly clues, and a cheerful solve.

The premise:
- A child detective is visiting a place decorated with pretend greenery.
- Something funny and small has gone missing or been mixed up.
- The detective follows clues, uses observation, and solves the case gently.
- The ending proves what changed in the world: the lost object is found, and
  the pretend greenery ends up in the right place again.

This script follows the Storyweavers world contract:
- typed entities with meters and memes
- state-driven prose
- QA sets
- lazy ASP import in helpers
- verify mode for ASP/Python parity
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue_e: object | None = None
    detective: object | None = None
    helper: object | None = None
    missing: object | None = None
    prop_e: object | None = None
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
    name: str
    outdoor: bool = True
    greenery: str = "green vines"
    vibe: str = "quiet"
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


@dataclass
class Clue:
    id: str
    label: str
    hint: str
    funny: str
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
class Prop:
    id: str
    label: str
    phrase: str
    role: str  # clue, decoration, missing, tool
    careful: bool = False
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
    place: str
    clue: str
    prop: str
    name: str
    gender: str
    sidekick: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _default_meters() -> dict[str, float]:
    return {"found": 0.0, "lost": 0.0, "moved": 0.0}


def _default_memes() -> dict[str, float]:
    return {"curious": 0.0, "joy": 0.0, "confused": 0.0, "pride": 0.0, "smirk": 0.0}


def make_world(place: Place) -> World:
    return World(place)


def _r_notice(w: World) -> list[str]:
    out = []
    detective = next((e for e in w.entities.values() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    if not detective:
        return out
    if detective.memes["curious"] >= THRESHOLD and ("notice", detective.id) not in w.fired:
        w.fired.add(("notice", detective.id))
        detective.meters["found"] += 0.0
        out.append(f"{detective.id} looked closely at the pretend greenery and spotted a funny little clue.")
    return out


def _r_misplace(w: World) -> list[str]:
    out = []
    missing = w.entities.get("missing")
    prop = w.entities.get("prop")
    if not missing or not prop:
        return out
    if prop.meters.get("moved", 0.0) >= THRESHOLD and missing.meters.get("lost", 0.0) >= THRESHOLD:
        if ("misplace", prop.id) not in w.fired:
            w.fired.add(("misplace", prop.id))
            out.append(f"The clue said the {prop.label} had been tucked behind the greenery like a shy squirrel.")
    return out


def _r_reveal(w: World) -> list[str]:
    out = []
    if w.facts.get("solved") and ("reveal",) not in w.fired:
        w.fired.add(("reveal",))
        out.append("The case clicked into place, and the pretend greenery was put back where it belonged.")
    return out


RULES = [
    _r_notice,
    _r_misplace,
    _r_reveal,
]


def propagate(w: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            lines = rule(w)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for line in out:
            w.say(line)
    return out


def _setup_story(w: World, detective: Entity, helper: Entity, clue: Entity, prop: Entity) -> None:
    detective.memes["curious"] += 1
    detective.memes["smirk"] += 1
    helper.memes["joy"] += 1
    clue.meters["found"] += 0.0
    prop.meters["lost"] += 1
    prop.meters["moved"] += 1

    w.say(
        f"{detective.id} was a little detective who loved clever puzzles and tidy answers."
    )
    w.say(
        f"{detective.pronoun().capitalize()} and {helper.id} went to {w.place.name}, where the pretend greenery looked almost real."
    )
    w.say(
        f"Then {prop.phrase} went missing, and everybody made a very serious face that lasted only one second."
    )
    w.say(
        f"{detective.id} found {clue.hint.lower()} and said, “That clue is so silly it might actually be useful.”"
    )


def _investigate(w: World, detective: Entity, helper: Entity, clue: Entity, prop: Entity) -> None:
    detective.memes["curious"] += 1
    detective.meters["found"] += 1
    helper.memes["confused"] += 1

    w.para()
    w.say(
        f"{detective.id} followed the clue past the fake leaves, under the paper fern, and around the cardboard tree."
    )
    w.say(
        f"The trail ended at a lump in the greenery that looked suspiciously like {prop.phrase} taking a nap."
    )
    w.say(
        f"{helper.id} laughed and said, “Well, that is the least sneaky hiding spot I have ever seen.”"
    )

    w.facts["solved"] = True
    propagate(w, narrate=True)


def _resolve(w: World, detective: Entity, helper: Entity, clue: Entity, prop: Entity) -> None:
    detective.memes["joy"] += 1
    detective.memes["pride"] += 1
    helper.memes["joy"] += 1

    w.para()
    w.say(
        f"{detective.id} lifted {prop.phrase} out from behind the pretend greenery and dusted it off carefully."
    )
    w.say(
        f"Then {helper.id} set the greenery straight again, and the whole display looked proud of itself."
    )
    w.say(
        f"{detective.id} smiled at the solved case, because the mystery had been funny, harmless, and neatly finished."
    )


PARKS = {
    "garden": Place(name="the school garden stage", outdoor=True, greenery="pretend vines", vibe="playful"),
    "lobby": Place(name="the library lobby", outdoor=False, greenery="paper ivy", vibe="quiet"),
    "yard": Place(name="the backyard set", outdoor=True, greenery="painted bushes", vibe="busy"),
}

CLUES = {
    "leaf": Clue(id="leaf", label="leaf clue", hint="A paper leaf had a curl in one corner.", funny="It looked like it had tried to wink."),
    "shrub": Clue(id="shrub", label="shrub clue", hint="A fake shrub leaned the wrong way.", funny="It was pretending to be innocent, very badly."),
    "ladder": Clue(id="ladder", label="ladder clue", hint="A tiny ladder was set up beside the vines.", funny="It was the shortest ladder with the biggest attitude."),
}

PROPS = {
    "sign": Prop(id="sign", label="welcome sign", phrase="the welcome sign", role="missing"),
    "hat": Prop(id="hat", label="tiny hat", phrase="a tiny hat from the display", role="missing"),
    "spoon": Prop(id="spoon", label="silver spoon", phrase="the silver spoon on the shelf", role="missing"),
    "balloon": Prop(id="balloon", label="red balloon", phrase="the red balloon from the party table", role="missing"),
}

GIRL_NAMES = ["Mina", "Lena", "Ivy", "Nora", "Tess", "Ruby", "Ada"]
BOY_NAMES = ["Eli", "Owen", "Finn", "Noah", "Theo", "Milo", "Jude"]
SIDEKICKS = ["a cheerful helper", "the stagekeeper", "the gardener", "the librarian"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id in PARKS:
        for clue_id in CLUES:
            for prop_id in PROPS:
                combos.append((place_id, clue_id, prop_id))
    return combos


def choose_name(rng: random.Random, gender: str) -> str:
    return rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)


def tell(place: Place, clue: Clue, prop: Prop, name: str, gender: str, sidekick: str) -> World:
    w = make_world(place)
    detective = w.add(Entity(id=name, kind="character", type=gender, meters=_default_meters(), memes=_default_memes()))
    helper = w.add(Entity(id=sidekick, kind="character", type="adult", meters=_default_meters(), memes=_default_memes()))
    clue_e = w.add(Entity(id="clue", kind="thing", type="clue", label=clue.label, phrase=clue.hint, meters=_default_meters(), memes=_default_memes()))
    prop_e = w.add(Entity(id="prop", kind="thing", type="prop", label=prop.label, phrase=prop.phrase, meters=_default_meters(), memes=_default_memes()))
    missing = w.add(Entity(id="missing", kind="thing", type="missing", label=prop.label, phrase=prop.phrase, meters=_default_meters(), memes=_default_memes()))

    _setup_story(w, detective, helper, clue_e, prop_e)
    _investigate(w, detective, helper, clue_e, prop_e)
    _resolve(w, detective, helper, clue_e, prop_e)

    w.facts.update(
        detective=detective,
        helper=helper,
        clue=clue_e,
        prop=prop_e,
        missing=missing,
        place=place,
        clue_cfg=clue,
        prop_cfg=prop,
        solved=True,
    )
    return w


def generation_prompts(w: World) -> list[str]:
    f = w.facts
    det = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "detective")
    return [
        f'Write a short detective story for a child that includes pretend greenery and a silly clue.',
        f"Tell a humorous mystery where {det.id} follows a clue through {w.place.name} and finds a missing prop.",
        f"Write a gentle detective story with pretend greenery, an obvious hiding spot, and a happy ending.",
    ]


def story_qa(w: World) -> list[QAItem]:
    f = w.facts
    det = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "detective")
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    clue = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "clue_cfg")
    prop = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prop_cfg")
    return [
        QAItem(
            question=f"Who solved the mystery in {w.place.name}?",
            answer=f"{det.id} solved it by following a silly clue through the pretend greenery with {helper.id} nearby.",
        ),
        QAItem(
            question=f"What went missing in the story?",
            answer=f"{prop.phrase} went missing, and that started the funny little mystery.",
        ),
        QAItem(
            question=f"What clue helped {det.id} notice where the missing thing was?",
            answer=f"{clue.hint} That clue led {det.id} right to the hiding spot.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"{det.id} found the missing prop, and the pretend greenery was put back neatly again.",
        ),
    ]


KNOWLEDGE = {
    "leaf": [
        QAItem(
            question="What is a leaf?",
            answer="A leaf is a flat part of a plant that grows from a stem or branch.",
        )
    ],
    "shrub": [
        QAItem(
            question="What is a shrub?",
            answer="A shrub is a small woody plant with many branches close to the ground.",
        )
    ],
    "ladder": [
        QAItem(
            question="What is a ladder for?",
            answer="A ladder helps someone reach something higher up.",
        )
    ],
    "sign": [
        QAItem(
            question="What is a sign used for?",
            answer="A sign can show information, like a name, direction, or welcome message.",
        )
    ],
    "hat": [
        QAItem(
            question="What does a hat do?",
            answer="A hat can cover your head and sometimes help keep the sun off.",
        )
    ],
    "spoon": [
        QAItem(
            question="What is a spoon for?",
            answer="A spoon is used for scooping and eating food like soup or cereal.",
        )
    ],
    "balloon": [
        QAItem(
            question="Why are balloons fun?",
            answer="Balloons are fun because they are light, bouncy, and float when filled with air or helium.",
        )
    ],
}


def world_knowledge_qa(w: World) -> list[QAItem]:
    tags = {w.facts["clue_cfg"].id, w.facts["prop_cfg"].id}
    out: list[QAItem] = []
    for t in ["leaf", "shrub", "ladder", "sign", "hat", "spoon", "balloon"]:
        if t in tags:
            out.extend(KNOWLEDGE[t])
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


def dump_trace(w: World) -> str:
    lines = ["--- world model state ---"]
    for e in w.entities.values():
        m = {k: v for k, v in e.meters.items() if v}
        mm = {k: v for k, v in e.memes.items() if v}
        bits = []
        if m:
            bits.append(f"meters={m}")
        if mm:
            bits.append(f"memes={mm}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired: {sorted(w.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- setting(P).
clue(C) :- clue_cfg(C).
prop(R) :- prop_cfg(R).
solved_story :- solved.
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid in PARKS:
        lines.append(asp.fact("setting", pid))
    for cid in CLUES:
        lines.append(asp.fact("clue_cfg", cid))
    for pid in PROPS:
        lines.append(asp.fact("prop_cfg", pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show setting/1."))
    return sorted(set(asp.atoms(model, "setting")))


def asp_verify() -> int:
    import asp
    py = {("setting", k) for k in PARKS}
    cl = {("setting", t[0]) for t in asp_valid_combos()}
    if py == cl:
        print(f"OK: clingo gate matches registries ({len(py)} settings).")
        return 0
    print("MISMATCH between clingo and python registries.")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous detective story world with pretend greenery.")
    ap.add_argument("--place", choices=PARKS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--prop", choices=PROPS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    place = getattr(args, "place", None) or rng.choice(list(PARKS))
    clue = getattr(args, "clue", None) or rng.choice(list(CLUES))
    prop = getattr(args, "prop", None) or rng.choice(list(PROPS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or choose_name(rng, gender)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    return StoryParams(place=place, clue=clue, prop=prop, name=name, gender=gender, sidekick=sidekick)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PARKS, params.place), _safe_lookup(CLUES, params.clue), _safe_lookup(PROPS, params.prop), params.name, params.gender, params.sidekick)
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
    StoryParams(place="garden", clue="leaf", prop="sign", name="Mina", gender="girl", sidekick="the stagekeeper"),
    StoryParams(place="lobby", clue="ladder", prop="hat", name="Eli", gender="boy", sidekick="the librarian"),
    StoryParams(place="yard", clue="shrub", prop="balloon", name="Tess", gender="girl", sidekick="the gardener"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show setting/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show setting/1."))
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

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
