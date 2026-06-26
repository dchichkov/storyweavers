#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/inner_sharing_repetition_bad_ending_whodunit.py
===============================================================================================================

A small whodunit-style storyworld built from the seed word "inner".

Premise:
- A child in an inner room notices something missing.
- Characters share clues, but one clue gets repeated so many times that it turns into a problem.
- The mystery ends with a bad ending flavor: the wrong suspect is blamed at first, and the real answer arrives too late to make the situation fully cheerful.

The world keeps the story grounded in meters and memes:
- meters track physical things like clue copies, misplaced items, and mess.
- memes track suspicion, worry, relief, embarrassment, and trust.

This script follows the shared Storyweavers world contract:
- standalone stdlib script
- lazy ASP helper import
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- QA and trace support
- inline ASP twin and verification mode
"""

from __future__ import annotations

import argparse
import copy
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
    caretaker: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    helper: object | None = None
    missing: object | None = None
    suspect_ent: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def they(self) -> str:
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
    inner: bool = False
    echoes: bool = False
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
class Clue:
    id: str
    label: str
    phrase: str
    reveal: str
    kind: str
    loudness: str
    repeats: bool = False
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
    label: str
    type: str
    likely: set[str] = field(default_factory=set)
    innocent_reason: str = ""
    guilty_reason: str = ""
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
    clue: str
    suspect: str
    name: str
    gender: str
    helper: str
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
        self.events: list[str] = []
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]

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
        clone.entities = copy.deepcopy(self.entities)
        clone.events = list(self.events)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


PLACES = {
    "inner_room": Place(
        id="inner_room",
        label="the inner room",
        inner=True,
        echoes=True,
        affords={"search", "share", "whisper"},
    ),
    "hall": Place(
        id="hall",
        label="the hall",
        inner=False,
        echoes=False,
        affords={"search", "share", "whisper"},
    ),
    "attic": Place(
        id="attic",
        label="the inner attic",
        inner=True,
        echoes=False,
        affords={"search", "share", "whisper"},
    ),
}

CLUES = {
    "lantern": Clue(
        id="lantern",
        label="lantern",
        phrase="a small brass lantern",
        reveal="it had been set near the window",
        kind="light",
        loudness="bright",
        repeats=False,
    ),
    "button": Clue(
        id="button",
        label="button",
        phrase="a tiny blue button",
        reveal="it matched a coat in the corner",
        kind="fabric",
        loudness="tiny",
        repeats=True,
    ),
    "note": Clue(
        id="note",
        label="note",
        phrase="a folded note",
        reveal="it pointed to a shelf behind the curtain",
        kind="paper",
        loudness="soft",
        repeats=True,
    ),
    "crumb": Clue(
        id="crumb",
        label="crumb",
        phrase="a crumb trail",
        reveal="it led to the pantry door",
        kind="food",
        loudness="small",
        repeats=False,
    ),
}

SUSPECTS = {
    "cat": Suspect(
        id="cat",
        label="the cat",
        type="cat",
        likely={"crumb"},
        innocent_reason="the cat was sleeping in the basket when the clue was checked",
        guilty_reason="",
    ),
    "brother": Suspect(
        id="brother",
        label="the brother",
        type="boy",
        likely={"button", "note"},
        innocent_reason="he was helping in the inner room and never left with the missing thing",
        guilty_reason="",
    ),
    "aunt": Suspect(
        id="aunt",
        label="the aunt",
        type="woman",
        likely={"lantern", "note"},
        innocent_reason="she had already walked out before the search began",
        guilty_reason="",
    ),
}

HELPERS = {
    "friend": "a careful friend",
    "parent": "a patient parent",
    "teacher": "a quiet teacher",
}

GIRL_NAMES = ["Mina", "Nora", "Lina", "Ivy", "June", "Pia", "Tess"]
BOY_NAMES = ["Owen", "Miles", "Noah", "Ezra", "Levi", "Theo", "Finn"]
TRAITS = ["curious", "careful", "brave", "gentle", "serious", "quick"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place_id, place in PLACES.items():
        for clue_id, clue in CLUES.items():
            for suspect_id, suspect in SUSPECTS.items():
                if clue_id in suspect.likely and place.affords:
                    combos.append((place_id, clue_id, suspect_id))
    return combos


def invalid_reason(place: Place, clue: Clue, suspect: Suspect) -> str:
    return (
        f"(No story: {clue.label} does not fit a whodunit about {suspect.label} "
        f"in {place.label}. Try a clue that plausibly points to that suspect.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small inner-room whodunit with sharing and repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
              and (getattr(args, "suspect", None) is None or c[2] == getattr(args, "suspect", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place_id, clue_id, suspect_id = rng.choice(list(combos))
    place = _safe_lookup(PLACES, place_id)
    clue = _safe_lookup(CLUES, clue_id)
    suspect = _safe_lookup(SUSPECTS, suspect_id)

    if getattr(args, "gender", None):
        if getattr(args, "gender", None) == "girl":
            name = getattr(args, "name", None) or rng.choice(GIRL_NAMES)
        else:
            name = getattr(args, "name", None) or rng.choice(BOY_NAMES)
    else:
        gender = rng.choice(["girl", "boy"])
        name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)

    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    gender = getattr(args, "gender", None) or ("girl" if name in GIRL_NAMES else "boy")

    return StoryParams(
        place=place_id,
        clue=clue_id,
        suspect=suspect_id,
        name=name,
        gender=gender,
        helper=helper,
    )


def _share_clue(world: World, child: Entity, helper: Entity, clue: Clue) -> None:
    child.meters["clue_shares"] += 1
    helper.memes["trust"] += 1
    world.say(
        f"{child.id} shared the clue with {helper.label}, and {helper.label} listened closely."
    )


def _repeat_clue(world: World, child: Entity, clue: Clue) -> None:
    child.meters["repeats"] += 1
    child.memes["nervous"] += 1
    world.say(
        f"Then {child.id} repeated the same clue again and again, as if saying it one more time "
        f"could pin the answer down."
    )
    if clue.repeats:
        child.meters["echo_clue"] += 1
        world.say(
            f"Because the clue was so small, it got echoed around the inner room and seemed even more important."
        )
    else:
        child.memes["worry"] += 1


def _accuse(world: World, child: Entity, suspect: Entity, clue: Clue) -> None:
    child.memes["suspicion"] += 1
    suspect.memes["pressure"] += 1
    world.say(
        f"{child.id} pointed at {suspect.label} and thought the clue fit. "
        f"But the room felt too quiet for a sure answer."
    )


def _bad_ending(world: World, child: Entity, suspect: Entity, clue: Clue) -> None:
    world.say(
        f"By the time the truth arrived, the wrong guess had already spread through the house."
    )
    world.say(
        f"The missing thing was found in a place nobody had looked at first, and {child.id} felt a hot, "
        f"small sting of embarrassment."
    )
    child.memes["embarrassment"] += 1
    child.memes["relief"] += 0.5
    suspect.memes["innocence"] += 1
    world.say(
        f"{suspect.label} was innocent after all, but the day ended with a bad feeling lingering "
        f"like a shadow in the inner room."
    )


def tell_story(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    clue = _safe_lookup(CLUES, params.clue)
    suspect = _safe_lookup(SUSPECTS, params.suspect)
    world = World(place)

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type="girl" if params.gender == "girl" else "boy",
        traits=["little", random.choice(TRAITS)],
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="woman" if params.helper in {"parent", "teacher"} else "boy",
        label=_safe_lookup(HELPERS, params.helper),
    ))
    suspect_ent = world.add(Entity(
        id="Suspect",
        kind="character",
        type=suspect.type,
        label=suspect.label,
    ))
    missing = world.add(Entity(
        id="Missing",
        kind="thing",
        type=clue.kind,
        label=f"the missing {clue.label}",
        phrase=clue.phrase,
        owner=child.id,
        caretaker=helper.id,
    ))

    world.facts.update(child=child, helper=helper, suspect=suspect_ent, clue=clue, missing=missing, place=place)

    world.say(
        f"In {place.label}, {child.id} found a mystery waiting in the inner corner."
    )
    world.say(
        f"{child.id} noticed that {missing.label} was gone, and the only thing left behind was {clue.phrase}."
    )
    world.say(
        f"{clue.reveal.capitalize()}."
    )

    world.para()
    world.say(
        f"{child.id} and {helper.label} searched carefully, because the room had a hush that made every sound seem like a clue."
    )
    _share_clue(world, child, helper, clue)
    _repeat_clue(world, child, clue)
    _accuse(world, child, suspect_ent, clue)

    world.para()
    if place.echoes and clue.repeats:
        world.say(
            f"In the echoing inner room, the repeated clue bounced back and made the wrong idea feel bigger than it was."
        )
    elif place.inner:
        world.say(
            f"Inside the inner place, the same clue kept coming back to {child.id}'s mind."
        )
    else:
        world.say(
            f"The clue kept returning to the front of {child.id}'s thoughts."
        )
    _bad_ending(world, child, suspect_ent, clue)

    world.facts["resolved"] = False
    world.facts["bad_ending"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    clue = _safe_fact(world, f, "clue")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a short whodunit for a child named {child.id} in {place.label} with the clue "{clue.label}".',
        f"Tell a mystery story where the clue is shared, then repeated, and the first guess turns out wrong.",
        f"Write a gentle inner-room whodunit that ends badly enough to feel sad, but still makes sense.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    helper: Entity = _safe_fact(world, f, "helper")
    suspect: Entity = _safe_fact(world, f, "suspect")
    clue: Clue = _safe_fact(world, f, "clue")
    missing: Entity = _safe_fact(world, f, "missing")
    place: Place = _safe_fact(world, f, "place")

    return [
        QAItem(
            question=f"Who noticed that {missing.label} was missing in {place.label}?",
            answer=f"{child.id} noticed that {missing.label} was missing in {place.label}.",
        ),
        QAItem(
            question=f"What clue did {child.id} share with {helper.label}?",
            answer=f"{child.id} shared {clue.phrase} with {helper.label}.",
        ),
        QAItem(
            question=f"Who did {child.id} think the clue pointed to at first?",
            answer=f"At first, {child.id} thought the clue pointed to {suspect.label}.",
        ),
        QAItem(
            question=f"Why did the story have a bad ending?",
            answer=(
                f"The story had a bad ending because the wrong guess spread before the real answer was found, "
                f"and {child.id} felt embarrassed even after {missing.label} turned up."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    clue: Clue = _safe_fact(world, f, "clue")
    place: Place = _safe_fact(world, f, "place")
    out = [
        QAItem(
            question="What is a clue in a mystery story?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        )
    ]
    if place.inner:
        out.append(
            QAItem(
                question="What does inner mean?",
                answer="Inner means inside something or farther toward the middle.",
            )
        )
    if clue.repeats:
        out.append(
            QAItem(
                question="Why can repeating the same idea make it feel bigger?",
                answer="When you repeat an idea, people notice it more, so it can seem more important than it really is.",
            )
        )
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.label:
            parts.append(f"label={e.label}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A clue is relevant when it fits the suspect's likely trail.
relevant(C,S) :- clue(C), suspect(S), likely(C,S).

% Repetition is a physical/social buildup: repeated clues create pressure.
repeated(C) :- clue(C), repeatable(C).
pressure(C) :- repeated(C).

% A bad ending happens when the wrong suspect is accused before the truth is found.
bad_ending(P,C,S) :- place(P), clue(C), suspect(S), relevant(C,S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.inner:
            lines.append(asp.fact("inner", pid))
        if p.echoes:
            lines.append(asp.fact("echoes", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("kind", cid, c.kind))
        if c.repeats:
            lines.append(asp.fact("repeatable", cid))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        for c in sorted(s.likely):
            lines.append(asp.fact("likely", c, sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def _asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show relevant/2.\n#show bad_ending/3."))
    rel = set(asp.atoms(model, "relevant"))
    bad = set(asp.atoms(model, "bad_ending"))
    return sorted(rel | bad)


def asp_verify() -> int:
    python_set = set()
    for c in CLUES:
        for s in SUSPECTS:
            if c in _safe_lookup(SUSPECTS, s).likely:
                python_set.add(("relevant", c, s))
                python_set.add(("bad_ending", "inner_room", c, s))
    clingo_set = set(_asp_valid())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches Python reasoning ({len(clingo_set)} atoms).")
        return 0
    print("MISMATCH between clingo and Python reasoning:")
    print(" only in clingo:", sorted(clingo_set - python_set))
    print(" only in python:", sorted(python_set - clingo_set))
    return 1


def explain_rejection(place: Place, clue: Clue, suspect: Suspect) -> str:
    return invalid_reason(place, clue, suspect)


CURATED = [
    StoryParams(place="inner_room", clue="button", suspect="brother", name="Mina", gender="girl", helper="parent"),
    StoryParams(place="attic", clue="note", suspect="aunt", name="Theo", gender="boy", helper="teacher"),
    StoryParams(place="hall", clue="crumb", suspect="cat", name="Ivy", gender="girl", helper="parent"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "clue", None) is None or c[1] == getattr(args, "clue", None))
              and (getattr(args, "suspect", None) is None or c[2] == getattr(args, "suspect", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place_id, clue_id, suspect_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    return StoryParams(place=place_id, clue=clue_id, suspect=suspect_id, name=name, gender=gender, helper=helper)


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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show relevant/2.\n"))
    rel = asp.atoms(model, "relevant")
    return sorted(set(rel))


def build_asp_listing() -> str:
    lines = []
    for c in sorted(valid_combos()):
        lines.append(f"{c[0]} / {c[1]} / {c[2]}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show relevant/2.\n#show bad_ending/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(build_asp_listing())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.clue} in {p.place} (suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
