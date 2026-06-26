#!/usr/bin/env python3
"""
storyworlds/worlds/rumpus_surprise_humor_cautionary_ghost_story.py
===================================================================

A small ghost-story world with a surprising, humorous, cautionary rumpus.

Premise:
A child hears strange bumping and whispering at night, follows the sounds,
and discovers that the "ghost" is not a monster at all but a sleepy troublemaker
causing a rumpus in the wrong place. The warning is that spooky things are not
always dangerous, but carelessness at night can still cause a mess, a scare, or
a broken rule.

The simulated world tracks:
- physical state: meters for noise, clutter, dimness, and soot
- emotional state: memes for fear, curiosity, relief, and laughter

The story logic:
- A quiet place becomes noisy.
- The hero investigates with caution.
- A surprise reveals the source of the rumpus.
- Humor softens the fear.
- The ending shows the rumpus was calmed and the lesson was learned.
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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    location: str = ""

    clue: object | None = None
    hero: object | None = None
    noise: object | None = None
    source: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    dim: str
    spooky: bool = False
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
class Trigger:
    id: str
    source: str
    clue: str
    surprise: str
    joke: str
    caution: str
    risk: str
    mess: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.night: bool = True

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
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        w.night = self.night
        return w


PLACES = {
    "attic": Place(id="attic", label="the attic", dim="dusty", spooky=True, affords={"listening", "hiding"}),
    "hall": Place(id="hall", label="the hallway", dim="dim", spooky=True, affords={"listening", "hiding"}),
    "kitchen": Place(id="kitchen", label="the kitchen", dim="warm", spooky=False, affords={"snacking", "listening"}),
    "garden": Place(id="garden", label="the garden", dim="moonlit", spooky=True, affords={"listening", "hiding"}),
    "basement": Place(id="basement", label="the basement", dim="dark", spooky=True, affords={"listening", "hiding"}),
}

TRIGGERS = {
    "cat": Trigger(
        id="cat",
        source="a cat",
        clue="tiny paw taps",
        surprise="the 'ghost' was only a cat knocking over a tin spoon",
        joke="it had been trying to steal a fish cracker all along",
        caution="quiet footsteps matter in a dark house",
        risk="a startled tumble",
        mess="a clattering rumpus",
    ),
    "curtain": Trigger(
        id="curtain",
        source="a curtain",
        clue="soft fluttering",
        surprise="the 'ghost' was only a curtain flapping in the window breeze",
        joke="it kept bowing like a shy dancer",
        caution="shadows can look scary when the room is dim",
        risk="a frightened dash",
        mess="a flapping rumpus",
    ),
    "grandpa": Trigger(
        id="grandpa",
        source="grandpa",
        clue="gentle humming",
        surprise="the 'ghost' was only grandpa in a sheet, sneezing behind the door",
        joke="the sheet kept slipping over his glasses like a silly mask",
        caution="pranks can backfire in the dark",
        risk="a silly scare",
        mess="a sheet-shaking rumpus",
    ),
    "toy": Trigger(
        id="toy",
        source="a toy",
        clue="clicking wheels",
        surprise="the 'ghost' was only a windup toy bumping the wall",
        joke="it rolled in circles like it wanted to dance",
        caution="winding toys can wake everyone up at night",
        risk="a noisy wake-up",
        mess="a rattling rumpus",
    ),
}

HERO_NAMES = ["Mia", "Leo", "Nora", "Ben", "Ava", "Finn", "Luna", "Owen"]
TRAITS = ["curious", "careful", "brave", "sleepy", "small", "serious"]


@dataclass
class StoryParams:
    place: str
    trigger: str
    name: str
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


ASP_RULES = r"""
place_dim(attic,dusty).
place_dim(hall,dim).
place_dim(kitchen,warm).
place_dim(garden,moonlit).
place_dim(basement,dark).

trigger(cat).
trigger(curtain).
trigger(grandpa).
trigger(toy).

spooky_place(P) :- place_dim(P,dusty).
spooky_place(P) :- place_dim(P,dim).
spooky_place(P) :- place_dim(P,moonlit).
spooky_place(P) :- place_dim(P,dark).

safe_story(P,T) :- trigger(T), place_dim(P,_).
valid(P,T) :- trigger(T), place_dim(P,_).
#show valid/2.
#show spooky_place/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_dim", pid, p.dim))
        if p.spooky:
            lines.append(asp.fact("spooky_place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for tid in TRIGGERS:
        lines.append(asp.fact("trigger", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return sorted((pid, tid) for pid in PLACES for tid in TRIGGERS)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and python:")
    print("only in python:", sorted(py - cl))
    print("only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost story world with a rumpus, surprise, humor, and caution.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--trigger", choices=TRIGGERS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "trigger", None) is None or c[1] == getattr(args, "trigger", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, trigger = rng.choice(combos)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, trigger=trigger, name=name, trait=trait)


def make_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    trig = _safe_lookup(TRIGGERS, params.trigger)
    w = World(place)
    hero = w.add(Entity(id=params.name, kind="character", type="child", traits=[params.trait, "little"]))
    noise = w.add(Entity(id="noise", meters={"noise": 0.0, "clutter": 0.0, "dimness": 0.0}, memes={"fear": 0.0, "curiosity": 0.0, "relief": 0.0, "laughter": 0.0}))
    clue = w.add(Entity(id="clue", label=trig.clue, location=place.id))
    source = w.add(Entity(id="source", label=trig.source, location=place.id))
    w.facts = {"hero": hero, "noise": noise, "clue": clue, "source": source, "trigger": trig, "place": place}
    return w


def tell_story(w: World) -> None:
    f = w.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    trig: Trigger = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trigger")
    place: Place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")

    w.say(f"On a quiet night, {hero.id} crept into {place.label}.")
    w.say(f"{hero.pronoun().capitalize()} had a {hero.traits[0]} nose for strange sounds, and the house was full of hush.")
    w.para()
    w.say(f"Then came {trig.clue}, and the hush turned into a little rumpus.")
    hero.memes["curiosity"] += 1
    _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "noise").meters["noise"] += 1
    if place.spooky:
        hero.memes["fear"] += 1
        w.say(f"{hero.id} swallowed hard because {trig.caution}.")
    w.say(f"But {hero.id} did not run away; {hero.pronoun().capitalize()} followed the sound one careful step at a time.")
    w.para()
    w.say(f"At the corner, the surprise was not a ghost at all.")
    hero.memes["fear"] = max(0.0, hero.memes["fear"] - 1)
    hero.memes["laughter"] += 1
    w.say(f"It was {trig.surprise}, and that was funny enough to make {hero.id} giggle.")
    w.say(f"The silly sight made the spooky room feel smaller, and even the shadow seemed to grin.")
    w.para()
    w.say(f"{hero.id} helped calm the rumpus before it woke the whole house.")
    _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "noise").meters["noise"] = 0.0
    _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "noise").meters["clutter"] += 1
    hero.memes["relief"] += 1
    w.say(f"In the end, the house was quiet again, the lesson stayed bright, and {hero.id} knew that a scary sound can hide a harmless cause.")


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    trig: Trigger = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trigger")
    place: Place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    return [
        QAItem(
            question=f"Where did {hero.id} go when the rumpus started?",
            answer=f"{hero.id} went to {place.label} after hearing the strange noises there.",
        ),
        QAItem(
            question=f"What first made the night feel spooky for {hero.id}?",
            answer=f"The first spooky thing was {trig.clue}, which turned the quiet into a rumpus.",
        ),
        QAItem(
            question=f"What was the surprise at the end of the story?",
            answer=trig.surprise.capitalize() + ".",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} calming the rumpus and learning that a scary sound can have a harmless cause.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rumpus?",
            answer="A rumpus is a noisy, lively disturbance where things get loud and a bit out of control.",
        ),
        QAItem(
            question="Why can shadows seem scary at night?",
            answer="Shadows can seem scary at night because the room is dim and our minds may imagine bigger troubles than are really there.",
        ),
        QAItem(
            question="Why should children be cautious when investigating strange sounds?",
            answer="Children should be cautious because nighttime noises can lead to a fall, a fright, or waking everyone up.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    trig: Trigger = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trigger")
    place: Place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    return [
        f"Write a short ghost story for young children about {hero.id} in {place.label} and a strange rumpus.",
        f"Tell a funny but cautionary story where {hero.id} hears {trig.clue} and discovers a surprising source.",
        f"Write a gentle spooky tale that starts with a hush, includes a rumpus, and ends with relief.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = make_world(params)
    tell_story(world)
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
    StoryParams(place="attic", trigger="cat", name="Mia", trait="curious"),
    StoryParams(place="hall", trigger="curtain", name="Leo", trait="careful"),
    StoryParams(place="basement", trigger="toy", name="Nora", trait="brave"),
    StoryParams(place="garden", trigger="grandpa", name="Ben", trait="sleepy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, trigger) combos:\n")
        for place, trig in combos:
            print(f"  {place:9} {trig}")
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
            header = f"### {p.name}: {p.trigger} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
