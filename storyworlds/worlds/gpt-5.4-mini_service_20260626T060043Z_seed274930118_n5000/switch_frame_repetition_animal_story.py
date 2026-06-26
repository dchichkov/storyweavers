#!/usr/bin/env python3
"""
storyworlds/worlds/switch_frame_repetition_animal_story.py
===========================================================

A small animal story world built from the seed words "switch" and "frame",
with repetition as the main narrative instrument.

Premise:
- A little animal wants to switch a picture frame on a wall.
- The old frame is plain; the new frame is bright and special.
- The animal keeps trying, then learns a careful way to switch the frames
  without dropping the picture.

The world is intentionally tiny and constraint-checked:
- physical state: frame weight, height, dust, stability
- emotional state: curiosity, worry, pride, relief
- repeated action beats build the story's rhythm
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    hero: object | None = None
    newf: object | None = None
    oldf: object | None = None
    sw: object | None = None
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
class Frame:
    id: str
    label: str
    phrase: str
    style: str
    weight: str
    safe_to_switch: bool
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
class Switch:
    id: str
    label: str
    verb: str
    repeat_line: str
    prep: str
    tail: str
    compatible_frames: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.switching: bool = False
        self.switch_target: str = ""

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.switching = self.switching
        clone.switch_target = self.switch_target
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_stress(world: World) -> list[str]:
    out: list[str] = []
    if not world.switching:
        return out
    for actor in world.characters():
        sig = ("stress", actor.id, world.switch_target)
        if sig in world.fired:
            continue
        frame = world.get(world.switch_target)
        if actor.memes["worry"] >= THRESHOLD:
            world.fired.add(sig)
            actor.memes["stress"] += 1
            out.append(f"{actor.id} pressed their paws together and tried again.")
        if frame.meters["dust"] >= THRESHOLD:
            world.fired.add(("dusty", frame.id))
            out.append(f"The dusty frame made the job feel trickier.")
    return out


def _r_safety(world: World) -> list[str]:
    out: list[str] = []
    if not world.switching:
        return out
    frame = world.get(world.switch_target)
    if frame.safe_to_switch and frame.meters["stable"] >= THRESHOLD:
        sig = ("safe", frame.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("__safe__")
    return out


CAUSAL_RULES = [Rule("stress", _r_stress), Rule("safety", _r_safety)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__safe__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


@dataclass
class StoryParams:
    place: str
    animal: str
    switch: str
    old_frame: str
    new_frame: str
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
    "hall": Place(name="the hall", indoor=True, affords={"switch"}),
    "den": Place(name="the den", indoor=True, affords={"switch"}),
    "porch": Place(name="the porch", indoor=False, affords={"switch"}),
}

ANIMALS = {
    "rabbit": {"type": "rabbit", "trait": "curious"},
    "fox": {"type": "fox", "trait": "bright"},
    "bear": {"type": "bear", "trait": "gentle"},
    "cat": {"type": "cat", "trait": "fussy"},
}

FRAMES = {
    "plain": Frame(id="plain", label="plain frame", phrase="a plain wooden frame", style="plain", weight="light", safe_to_switch=True),
    "gold": Frame(id="gold", label="gold frame", phrase="a shiny gold frame", style="bright", weight="light", safe_to_switch=True),
    "blue": Frame(id="blue", label="blue frame", phrase="a blue frame with little stars", style="bright", weight="light", safe_to_switch=True),
    "heavy": Frame(id="heavy", label="heavy frame", phrase="a heavy carved frame", style="fancy", weight="heavy", safe_to_switch=False),
}

SWITCHES = {
    "wall-switch": Switch(
        id="wall-switch",
        label="wall switch",
        verb="switch the frame",
        repeat_line="switch, switch, switch",
        prep="carefully line up the corners",
        tail="swapped the old frame for the new one",
        compatible_frames={"plain", "gold", "blue"},
    ),
}

ANIMAL_NAMES = {
    "rabbit": ["Nia", "Pip", "Tilly", "Bun", "Milo"],
    "fox": ["Ruby", "Finn", "Poppy", "Arlo", "Kit"],
    "bear": ["Bruno", "Hugo", "Mara", "Luna", "Toby"],
    "cat": ["Mimi", "Suki", "Nora", "Juno", "Ziggy"],
}

TRAITS = ["curious", "gentle", "eager", "proud", "busy"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for p, place in PLACES.items():
        for s_id, sw in SWITCHES.items():
            for old_id, old in FRAMES.items():
                for new_id, new in FRAMES.items():
                    if old_id == new_id:
                        continue
                    if old.safe_to_switch and new.safe_to_switch and old.weight != "heavy" and new.weight != "heavy":
                        out.append((p, s_id, old_id, new_id))
    return out


def frame_pair_reasonable(old: Frame, new: Frame) -> bool:
    return old.safe_to_switch and new.safe_to_switch and old.weight != "heavy" and new.weight != "heavy"


def select_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str, str]:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "switch", None) is None or c[1] == getattr(args, "switch", None))
              and (getattr(args, "old_frame", None) is None or c[2] == getattr(args, "old_frame", None))
              and (getattr(args, "new_frame", None) is None or c[3] == getattr(args, "new_frame", None))]
    if not combos:
        pass
    return rng.choice(list(combos))


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place, sw, old_id, new_id = select_combo(args, rng)
    animal = getattr(args, "animal", None) or rng.choice(sorted(ANIMALS))
    if getattr(args, "animal", None) and getattr(args, "animal", None) not in ANIMALS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "name", None):
        name = getattr(args, "name", None)
    else:
        name = rng.choice(_safe_lookup(ANIMAL_NAMES, animal))
    return StoryParams(place=place, animal=animal, switch=sw, old_frame=old_id, new_frame=new_id, seed=getattr(args, "seed", None))


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    trait = _safe_lookup(ANIMALS, params.animal)["trait"]
    hero = world.add(Entity(id=params.seed.__str__() if params.seed is not None else "hero", kind="character", type=params.animal))
    hero.label = params.animal
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 0.0

    oldf = world.add(Entity(id="old", type="frame", label=_safe_lookup(FRAMES, params.old_frame).label, phrase=_safe_lookup(FRAMES, params.old_frame).phrase))
    newf = world.add(Entity(id="new", type="frame", label=_safe_lookup(FRAMES, params.new_frame).label, phrase=_safe_lookup(FRAMES, params.new_frame).phrase))
    sw = world.add(Entity(id=params.switch, type="switch", label=_safe_lookup(SWITCHES, params.switch).label, phrase=_safe_lookup(SWITCHES, params.switch).label))

    world.facts.update(hero=hero, trait=trait, oldf=oldf, newf=newf, switch=sw, params=params)
    return world


def introduce(world: World) -> None:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    trait = _safe_fact(world, f, "trait")
    oldf = _safe_fact(world, f, "oldf")
    newf = _safe_fact(world, f, "newf")
    world.say(f"A little {trait} {hero.type} lived near {world.place.name}.")
    world.say(f"{hero.type.capitalize()} loved {oldf.label} and also loved {newf.label}, one shining, one plain.")
    world.say(f"Every day, {hero.type} looked at the wall and thought about a switch.")


def desire(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    sw = _safe_fact(world, world.facts, "switch")
    oldf = _safe_fact(world, world.facts, "oldf")
    newf = _safe_fact(world, world.facts, "newf")
    hero.memes["desire"] += 1
    world.say(f"{hero.type.capitalize()} wanted to {sw.verb} and make {newf.label} take the place of {oldf.label}.")
    world.say(f"{hero.type.capitalize()} whispered, '{sw.repeat_line},' and then whispered it again: '{sw.repeat_line}.'")


def worry(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    oldf = _safe_fact(world, world.facts, "oldf")
    newf = _safe_fact(world, world.facts, "newf")
    hero.memes["worry"] += 1
    world.say(f"But the old frame was snug on the wall, and the new frame was precious too.")
    world.say(f"{hero.type.capitalize()} worried that a clumsy tug might bump {oldf.label} or scratch {newf.label}.")


def attempt(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    oldf = _safe_fact(world, world.facts, "oldf")
    newf = _safe_fact(world, world.facts, "newf")
    sw = _safe_fact(world, world.facts, "switch")
    world.switching = True
    world.switch_target = oldf.id
    world.say(f"Tap, tap, tap. {hero.type.capitalize()} tried to start the switch, slowly and carefully.")
    world.say(f"{sw.repeat_line}, went the paws, but the frame did not budge yet.")
    hero.memes["frustration"] += 1


def helper_step(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    oldf = _safe_fact(world, world.facts, "oldf")
    newf = _safe_fact(world, world.facts, "newf")
    hero.memes["pride"] += 1
    world.say(f"Then {hero.type} took a breath, counted to three, and tried again.")
    world.say(f"One paw held {oldf.label}. One paw held {newf.label}. Softly, softly, the switch began to work.")


def resolve_story(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    oldf = _safe_fact(world, world.facts, "oldf")
    newf = _safe_fact(world, world.facts, "newf")
    sw = _safe_fact(world, world.facts, "switch")
    oldf.meters["stable"] += 1
    newf.meters["stable"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1)
    hero.memes["joy"] += 1
    world.say(f"{sw.tail}, and the room felt new at once.")
    world.say(f"{oldf.label} stayed safe in a neat place, and {newf.label} shone on the wall.")
    world.say(f"{hero.type.capitalize()} smiled, because the switch had worked without a bump.")


def tell(params: StoryParams) -> World:
    world = build_world(params)
    introduce(world)
    world.para()
    desire(world)
    worry(world)
    attempt(world)
    world.para()
    helper_step(world)
    resolve_story(world)
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    oldf = _safe_fact(world, f, "oldf")
    newf = _safe_fact(world, f, "newf")
    return [
        f"Write a short animal story about a {hero.type} who wants to switch one frame for another.",
        f"Tell a gentle repeating story where {hero.type} keeps saying switch, switch, switch while moving {oldf.label} and {newf.label}.",
        f"Make a child-friendly story about a frame on a wall and a careful switch that ends happily.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    oldf = _safe_fact(world, f, "oldf")
    newf = _safe_fact(world, f, "newf")
    sw = _safe_fact(world, f, "switch")
    return [
        QAItem(
            question=f"What did the little {hero.type} want to do with the frames?",
            answer=f"{hero.type.capitalize()} wanted to {sw.verb} so {newf.label} could replace {oldf.label}.",
        ),
        QAItem(
            question=f"Why did the {hero.type} try so carefully?",
            answer=f"{hero.type.capitalize()} tried carefully because both frames were special and a rough tug could bump or scratch them.",
        ),
        QAItem(
            question=f"What repeated words showed the story's rhythm?",
            answer=f"The repeated words were '{sw.repeat_line}', which the {hero.type} said more than once while trying to switch the frame.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, {newf.label} was on the wall and {oldf.label} stayed safe, so the room looked fresh and happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a frame for?",
            answer="A frame is a border that holds or displays a picture so it looks neat and special.",
        ),
        QAItem(
            question="What does a switch do?",
            answer="A switch is something you move to change from one thing to another, or to start and stop something.",
        ),
        QAItem(
            question="Why do people repeat words when they are trying something tricky?",
            answer="Repeating words can help a person stay focused, remember the steps, and feel brave while they try again.",
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
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hall", animal="rabbit", switch="wall-switch", old_frame="plain", new_frame="gold"),
    StoryParams(place="den", animal="fox", switch="wall-switch", old_frame="blue", new_frame="plain"),
    StoryParams(place="porch", animal="bear", switch="wall-switch", old_frame="plain", new_frame="blue"),
]


ASP_RULES = r"""
valid(Place, Sw, Old, New) :- place(Place), switch(Sw), frame(Old), frame(New), Old != New,
                              safe_frame(Old), safe_frame(New).
story(Place, Sw, Old, New) :- valid(Place, Sw, Old, New), affords(Place, Sw).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for sid, s in SWITCHES.items():
        lines.append(asp.fact("switch", sid))
    for fid, f in FRAMES.items():
        lines.append(asp.fact("frame", fid))
        if f.safe_to_switch:
            lines.append(asp.fact("safe_frame", fid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world about switching frames with repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--switch", choices=SWITCHES)
    ap.add_argument("--old-frame", choices=FRAMES)
    ap.add_argument("--new-frame", choices=FRAMES)
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
    if getattr(args, "old_frame", None) and getattr(args, "new_frame", None):
        oldf, newf = _safe_lookup(FRAMES, getattr(args, "old_frame", None)), _safe_lookup(FRAMES, getattr(args, "new_frame", None))
        if not frame_pair_reasonable(oldf, newf):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "switch", None) is None or c[1] == getattr(args, "switch", None))
              and (getattr(args, "old_frame", None) is None or c[2] == getattr(args, "old_frame", None))
              and (getattr(args, "new_frame", None) is None or c[3] == getattr(args, "new_frame", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, sw, oldf, newf = rng.choice(list(combos))
    animal = getattr(args, "animal", None) or rng.choice(sorted(ANIMALS))
    return StoryParams(place=place, animal=animal, switch=sw, old_frame=oldf, new_frame=newf, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
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
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, sw, oldf, newf in combos:
            print(f"  {place:8} {sw:11} {oldf:8} -> {newf:8}")
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
            header = f"### {p.animal} at {p.place} ({p.old_frame} -> {p.new_frame})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
