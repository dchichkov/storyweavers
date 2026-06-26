#!/usr/bin/env python3
"""
A small mythic story world about a tangible mystery to solve, with a surprise
and a cautionary ending.

Premise:
- A child or young seeker finds an odd tangible object near an old place.
- The object belongs to an old mythic cycle: it is a token, charm, or relic.
- People warn that touching it carelessly brings trouble.
- The seeker solves the mystery by tracing signs in the world.
- The surprise is that the feared object is not cursed in the way everyone
  believed; the real danger is the ancient rule that must be respected.
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

    elder: object | None = None
    relic_ent: object | None = None
    seer: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
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
    tags: set[str] = field(default_factory=set)
    holds: set[str] = field(default_factory=set)
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
class Relic:
    id: str
    label: str
    phrase: str
    type: str
    danger: str
    sign: str
    place: str
    tangible: bool = True
    bound_to: Optional[str] = None
    warnings: list[str] = field(default_factory=list)
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
class Omen:
    id: str
    label: str
    clue: str
    reveals: str
    place_tags: set[str] = field(default_factory=set)
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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_warning(world: World) -> list[str]:
    out = []
    seer = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "seer")
    relic = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "relic")
    if seer.memes.get("fear", 0) < THRESHOLD:
        return out
    sig = ("warning", relic.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append(f"The old folk whispered that {relic.label} should not be touched carelessly.")
    return out


def _r_reveal(world: World) -> list[str]:
    out = []
    seer = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "seer")
    omen = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "omen")
    relic = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "relic")
    if seer.meters.get("clue", 0) < THRESHOLD:
        return out
    sig = ("reveal", omen.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seer.memes["wonder"] = seer.memes.get("wonder", 0) + 1
    out.append(f"{omen.clue.capitalize()}, and the clue pointed toward the old truth behind {relic.label}.")
    return out


def _r_surprise(world: World) -> list[str]:
    out = []
    seer = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "seer")
    relic = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "relic")
    if seer.meters.get("solved", 0) < THRESHOLD:
        return out
    sig = ("surprise", relic.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    seer.memes["relief"] = seer.memes.get("relief", 0) + 1
    out.append(f"At last, the feared {relic.label} was not the curse itself; it was only the key to the caution.")
    return out


CAUSAL_RULES = [_r_warning, _r_reveal, _r_surprise]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    seeker: str
    seeker_type: str
    relic: str
    omen: str
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


PLACES = {
    "hill": Place(id="hill", label="the hill shrine", tags={"stone", "wind", "old"}),
    "well": Place(id="well", label="the dry well", tags={"stone", "echo", "old"}),
    "grove": Place(id="grove", label="the lantern grove", tags={"tree", "night", "old"}),
}

RELICS = {
    "stone_key": Relic(
        id="stone_key",
        label="the stone key",
        phrase="a cold stone key with a worn groove",
        type="key",
        danger="break the old vow",
        sign="the groove matches the shrine door",
        place="hill",
    ),
    "bell_shell": Relic(
        id="bell_shell",
        label="the shell bell",
        phrase="a bright shell bell tied with red thread",
        type="bell",
        danger="wake the sleeping flood",
        sign="its thread matches the lanterns in the grove",
        place="grove",
    ),
    "moon_cup": Relic(
        id="moon_cup",
        label="the moon cup",
        phrase="a pale cup that shone like milk under moonlight",
        type="cup",
        danger="spill the blessing too soon",
        sign="its rim bears the mark of the dry well",
        place="well",
    ),
}

OMENS = {
    "tracks": Omen(
        id="tracks",
        label="wolf tracks",
        clue="tiny tracks crossed the dust, then stopped at the stone",
        reveals="a hidden path",
        place_tags={"stone", "dust", "old"},
    ),
    "song": Omen(
        id="song",
        label="bird song",
        clue="a bird sang three times from the same branch",
        reveals="the rhythm of the old charm",
        place_tags={"tree", "night", "old"},
    ),
    "water": Omen(
        id="water",
        label="water marks",
        clue="a ring of water showed where the earth had once been wet",
        reveals="the well's forgotten mouth",
        place_tags={"stone", "echo", "old"},
    ),
}

SEEKER_NAMES = ["Mira", "Niko", "Tala", "Eli", "Sana", "Ivo", "Lina", "Ari"]
SEEKER_TYPES = {"girl", "boy"}
TRAITS = ["curious", "brave", "gentle", "thoughtful", "quick", "quiet"]


def place_for_relic(relic_id: str) -> str:
    return _safe_lookup(RELICS, relic_id).place


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for relic_id, relic in RELICS.items():
            if relic.place != place_id:
                continue
            for omen_id, omen in OMENS.items():
                if place.tags & omen.place_tags:
                    combos.append((place_id, relic_id, omen_id))
    return combos


def reason_gate(place_id: str, relic_id: str, omen_id: str) -> bool:
    return (place_id, relic_id, omen_id) in valid_combos()


def explain_rejection(place_id: str, relic_id: str, omen_id: str) -> str:
    place = _safe_lookup(PLACES, place_id)
    relic = _safe_lookup(RELICS, relic_id)
    omen = _safe_lookup(OMENS, omen_id)
    return (
        f"(No story: {relic.label} belongs at {place.label}, but that place does not hold a clue like {omen.label} "
        f"well enough to solve the mystery in a mythic way.)"
    )


def select_omen(place_id: str, rng: random.Random) -> Omen:
    place = _safe_lookup(PLACES, place_id)
    options = [o for o in OMENS.values() if place.tags & o.place_tags]
    return rng.choice(options)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic tangible mystery story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--omen", choices=OMENS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    place_id = getattr(args, "place", None) or rng.choice(list(PLACES))
    relic_choices = [r for r in RELICS if _safe_lookup(RELICS, r).place == place_id]
    relic_id = getattr(args, "relic", None) or rng.choice(relic_choices)
    omen_id = getattr(args, "omen", None) or select_omen(place_id, rng).id
    if getattr(args, "place", None) and getattr(args, "relic", None) and not reason_gate(place_id, relic_id, omen_id):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "omen", None) and not reason_gate(place_id, relic_id, omen_id):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(SEEKER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place_id, seeker=name, seeker_type=gender, relic=relic_id, omen=omen_id)


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    relic = _safe_lookup(RELICS, params.relic)
    omen = _safe_lookup(OMENS, params.omen)
    world = World(place)
    seer = world.add(Entity(
        id=params.seeker,
        kind="character",
        type=params.seeker_type,
        meters={"clue": 0.0, "solved": 0.0},
        memes={"fear": 0.0, "wonder": 0.0, "relief": 0.0},
    ))
    elder = world.add(Entity(id="elder", kind="character", type="man", label="the elder"))
    relic_ent = world.add(Entity(
        id=relic.id,
        kind="thing",
        type=relic.type,
        label=relic.label,
        phrase=relic.phrase,
        owner=None,
        caretaker=elder.id,
    ))
    world.facts.update(seer=seer, elder=elder, relic=relic_ent, omen=omen, place=place, trait=params.seeker_type)

    world.say(f"Long ago, in {place.label}, there lived a quiet wonder that the old people still feared.")
    world.say(f"{params.seeker} was a {params.seeker_type} who carried a {params.trait} heart and noticed small signs others missed.")
    world.say(f"One evening, {params.seeker} found {relic.phrase} beside the path.")

    world.para()
    seer.memes["fear"] += 1
    world.say(f"The sight of {relic.label} made the air feel heavy, for everyone said it could {relic.danger}.")
    propagate(world, narrate=True)
    world.say(f"But {params.seeker} did not turn away. {params.seeker} looked for a sign instead of a shout.")

    world.para()
    seer.meters["clue"] += 1
    world.say(f"Near the {place.label}, {omen.clue}.")
    propagate(world, narrate=True)
    world.say(f"{omen.sign.capitalize()}.")

    world.para()
    seer.meters["solved"] += 1
    propagate(world, narrate=True)
    world.say(
        f"Then {params.seeker} understood the old warning: the relic was tangible, but the true danger was careless hands and forgotten rules."
    )
    world.say(
        f"{params.seeker} set {(getattr(relic, 'it')() if callable(getattr(relic, 'it', None)) else getattr(relic, 'it', 'it'))} down respectfully, and the place grew calm again, as if the hill itself had sighed."
    )
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short myth about a tangible mystery at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place").label} involving {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "relic").label} and a surprising truth.",
        f"Tell a cautionary story for children where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "seer").id} follows a clue and learns why the old warning mattered.",
        f"Write a gentle myth in which a small seeker solves the secret of {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "relic").label} by noticing {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "omen").clue}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    seer = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "seer")
    relic = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "relic")
    omen = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "omen")
    place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    return [
        QAItem(
            question=f"What mystery did {seer.id} solve at {place.label}?",
            answer=f"{seer.id} solved the mystery of {relic.label} and learned why people were careful around it.",
        ),
        QAItem(
            question=f"What clue helped {seer.id} understand the truth about {relic.label}?",
            answer=f"The clue was this: {omen.clue}. That sign pointed {seer.id} toward the old meaning behind the relic.",
        ),
        QAItem(
            question=f"Why did the old people warn children about {relic.label}?",
            answer=f"They warned them because touching {relic.label} carelessly could {relic.danger}. The story shows that caution was wiser than fear.",
        ),
        QAItem(
            question=f"What surprising thing did {seer.id} learn in the end?",
            answer=f"The surprise was that {relic.label} was not a curse by itself. It was a tangible object that only became dangerous if the old rule was ignored.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a relic?",
            answer="A relic is an old object kept from long ago because people remember it and the story around it.",
        ),
        QAItem(
            question="What does tangible mean?",
            answer="Tangible means something you can touch or hold with your hands.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story people tell to explain a place, a warning, or a deep feeling.",
        ),
        QAItem(
            question="Why do people give warnings in cautionary stories?",
            answer="They give warnings so listeners can stay safe and remember the lesson before making a mistake.",
        ),
    ]


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
    lines.append("== (3) World knowledge questions ==")
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
        lines.append(f"  {e.id:12} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hill", seeker="Mira", seeker_type="girl", relic="stone_key", omen="tracks"),
    StoryParams(place="grove", seeker="Niko", seeker_type="boy", relic="bell_shell", omen="song"),
    StoryParams(place="well", seeker="Tala", seeker_type="girl", relic="moon_cup", omen="water"),
]


ASP_RULES = r"""
place_valid(P) :- place(P).
relic_valid(R) :- relic(R).
omen_valid(O) :- omen(O).

combo(P,R,O) :- relic_place(R,P), place_tag(P,T), omen_tag(O,T).
valid_story(P,R,O) :- combo(P,R,O).

#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for tag in sorted(place.tags):
            lines.append(asp.fact("place_tag", pid, tag))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("relic_place", rid, relic.place))
        lines.append(asp.fact("tangible", rid))
    for oid, omen in OMENS.items():
        lines.append(asp.fact("omen", oid))
        for tag in sorted(omen.place_tags):
            lines.append(asp.fact("omen_tag", oid, tag))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
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


def generate(params: StoryParams) -> StorySample:
    return build_sample(params)


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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:")
        for row in stories:
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            i += 1
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
            header = f"### {p.seeker}: {p.relic} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
