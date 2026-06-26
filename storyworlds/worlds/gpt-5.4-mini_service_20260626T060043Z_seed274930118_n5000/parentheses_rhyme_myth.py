#!/usr/bin/env python3
"""
A small mythic story world about a careful apprentice, a wise elder, and a
forbidden spell of parentheses and rhyme.

The seed image:
- In a temple archive, a young scribe finds a tablet marked with strange
  parentheses.
- The elder warns that the carved chant must be spoken in rhyme, or the seal
  will not hold.
- The apprentice tries, stumbles, then learns the shape of the line and saves
  the hidden light.

This file models that premise as a tiny simulation with physical meters and
emotional memes, a reasonableness gate, and an inline ASP twin.
"""

from __future__ import annotations

import argparse
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


# ---------------------------------------------------------------------------
# World entities
# ---------------------------------------------------------------------------

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
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    kept_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    elder: object | None = None
    hero: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "priestess", "elder", "mother"}
        male = {"boy", "man", "priest", "elder", "father"}
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
    id: str
    label: str
    tags: set[str] = field(default_factory=set)
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
class Relic:
    id: str
    label: str
    phrase: str
    risk: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Charm:
    id: str
    label: str
    rhyme_key: str
    protects: set[str]
    line: str
    ending: str
    plural: bool = False
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
        self.lines: list[list[str]] = [[]]
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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.lines = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "archive": Place("archive", "the moonlit archive", {"archive", "stone", "quiet"}, {"chant"}),
    "hall": Place("hall", "the echoing hall", {"hall", "stone"}, {"chant"}),
    "garden": Place("garden", "the temple garden", {"garden", "breeze"}, {"chant"}),
}

RITUALS = {
    "seal": {
        "verb": "speak the seal-chant",
        "gerund": "speaking the seal-chant",
        "rush": "speak the chant at once",
        "risk": "shaken",
        "soil": "shaken loose",
        "tags": {"seal", "light"},
        "rhyme": ("glow", "show"),
    },
    "wake": {
        "verb": "wake the sleeping lantern",
        "gerund": "waking the sleeping lantern",
        "rush": "call the lantern awake",
        "risk": "dimmed",
        "soil": "dimmed away",
        "tags": {"lantern", "light"},
        "rhyme": ("night", "light"),
    },
    "river": {
        "verb": "recite the river verse",
        "gerund": "reciting the river verse",
        "rush": "hurry the verse too fast",
        "risk": "slurred",
        "soil": "slurred into silence",
        "tags": {"river", "song"},
        "rhyme": ("flow", "glow"),
    },
}

RELICS = {
    "tablet": Relic("tablet", "tablet", "a carved stone tablet", "stone", "hands"),
    "lamp": Relic("lamp", "lamp", "a glass lamp with a bright wick", "light", "hands"),
    "scroll": Relic("scroll", "scroll", "a silk scroll", "ink", "hands"),
}

CHARMS = [
    Charm("rhyme_cord", "a rhyme cord", "seal", {"shaken"}, "tie the rhyme, line by line", "kept the seal from trembling"),
    Charm("lamp_cover", "a lantern cover", "wake", {"dimmed"}, "shade the flame, but let it stay awake", "kept the lantern bright"),
    Charm("ink_cap", "an ink cap", "river", {"slurred"}, "set the words in steady flow", "kept the verse from spilling"),
]


NAMES = {
    "girl": ["Nia", "Iris", "Mira", "Lina", "Sera"],
    "boy": ["Oren", "Tavi", "Milo", "Eren", "Pax"],
}
TRAITS = ["curious", "brave", "gentle", "earnest", "bright"]
ELDER_TITLES = ["elder", "priest", "priestess"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    ritual: str
    relic: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
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


def rhyme_ok(text: str) -> bool:
    words = re.findall(r"[A-Za-z']+", text.lower())
    if len(words) < 2:
        return False
    a, b = words[-2], words[-1]
    return a[-2:] == b[-2:] or a[-3:] == b[-3:]


class Rule:
    def __init__(self, name, apply):
        self.name = name
        self.apply = apply


def _r_shaken(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters.get("shaken", 0) < THRESHOLD:
            continue
        if ent.meters.get("sealed", 0) >= THRESHOLD:
            continue
        sig = ("shaken", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["unstable"] = ent.meters.get("unstable", 0) + 1
        out.append(f"The seal on the {ent.label} trembled.")
    return out


def _r_dimmed(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters.get("dimmed", 0) < THRESHOLD:
            continue
        if ent.meters.get("guarded", 0) >= THRESHOLD:
            continue
        sig = ("dimmed", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["fading"] = ent.meters.get("fading", 0) + 1
        out.append(f"The light in the {ent.label} began to fade.")
    return out


def _r_slurred(world: World) -> list[str]:
    out = []
    for ent in list(world.entities.values()):
        if ent.meters.get("slurred", 0) < THRESHOLD:
            continue
        if ent.meters.get("steady", 0) >= THRESHOLD:
            continue
        sig = ("slurred", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["lost"] = ent.meters.get("lost", 0) + 1
        out.append(f"The verse in the {ent.label} nearly vanished.")
    return out


CAUSAL_RULES = [Rule("shaken", _r_shaken), Rule("dimmed", _r_dimmed), Rule("slurred", _r_slurred)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def predict(world: World, hero: Entity, ritual: str, relic: Entity) -> dict:
    sim = world.copy()
    do_ritual(sim, sim.get(hero.id), ritual, narrate=False)
    target = sim.get(relic.id)
    return {
        "ruined": target.meters.get(_safe_lookup(RITUALS, ritual)["risk"], 0) >= THRESHOLD or target.meters.get("fading", 0) >= THRESHOLD or target.meters.get("lost", 0) >= THRESHOLD,
    }


def do_ritual(world: World, hero: Entity, ritual: str, narrate: bool = True) -> None:
    if ritual not in world.place.affords:
        pass
    if ritual == "chant":
        return
    hero.meters[ritual] = hero.meters.get(ritual, 0) + 1
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity) -> None:
    world.say(f"In {world.place.label}, a {hero.memes.get('trait', 'curious')} seeker named {hero.id} listened for old songs.")


def setup_story(world: World, hero: Entity, elder: Entity, ritual: str, relic: Entity) -> None:
    world.say(
        f"{hero.id} loved {_safe_lookup(RITUALS, ritual)['gerund']}, for the temple air rang like a bell in spring."
    )
    world.say(f"The {elder.type} kept {relic.phrase} beside a lamp and a stone wall, where dust lay thin as snow.")
    relic.carried_by = hero.id
    relic.kept_in = world.place.id
    hero.meters["care"] = hero.meters.get("care", 0) + 1


def arrival(world: World, hero: Entity, elder: Entity, ritual: str) -> None:
    world.say(
        f"One dusk, {hero.id} and {elder.id} came to {world.place.label}, "
        f"and the old stones waited to hear {hero.pronoun('possessive')} voice."
    )
    world.say(f"{hero.id} wanted to {_safe_lookup(RITUALS, ritual)['verb']}, but the elder lifted a hand and frowned.")
    hero.memes["want"] = hero.memes.get("want", 0) + 1


def warning(world: World, elder: Entity, hero: Entity, ritual: str, relic: Entity) -> bool:
    pred = predict(world, hero, ritual, relic)
    if not pred["ruined"]:
        return False
    world.facts["danger"] = _safe_lookup(RITUALS, ritual)["risk"]
    world.say(
        f'"If you {_safe_lookup(RITUALS, ritual)["rush"]}, your {relic.label} will go {_safe_lookup(RITUALS, ritual)["soil"]}," '
        f"{elder.id} said. \"A chant must land in rhyme, or the old seal will groan.\""
    )
    return True


def stumble(world: World, hero: Entity, ritual: str) -> None:
    hero.memes["fluster"] = hero.memes.get("fluster", 0) + 1
    world.say(f"{hero.id} tried to begin anyway, but the first line slipped like water from a cup.")


def offer_charm(world: World, elder: Entity, hero: Entity, ritual: str, relic: Entity) -> Optional[Charm]:
    for charm in CHARMS:
        if charm.rhyme_key == ritual and relic.risk in charm.protects:
            if predict_with_charm(world, hero, ritual, relic, charm):
                world.say(
                    f"{elder.id} smiled and brought out {charm.label}. "
                    f"\"{charm.line},\" {elder.id} said. \"Let the words fall paired as birds.\""
                )
                return charm
    return None


def predict_with_charm(world: World, hero: Entity, ritual: str, relic: Entity, charm: Charm) -> bool:
    sim = world.copy()
    relic_sim = sim.get(relic.id)
    relic_sim.meters["sealed"] = relic_sim.meters.get("sealed", 0) + 1
    if ritual == "seal":
        relic_sim.meters["shaken"] = 0
    elif ritual == "wake":
        relic_sim.meters["guarded"] = relic_sim.meters.get("guarded", 0) + 1
    else:
        relic_sim.meters["steady"] = relic_sim.meters.get("steady", 0) + 1
    do_ritual(sim, sim.get(hero.id), ritual, narrate=False)
    target = sim.get(relic.id)
    return not (
        target.meters.get("unstable", 0) >= THRESHOLD
        or target.meters.get("fading", 0) >= THRESHOLD
        or target.meters.get("lost", 0) >= THRESHOLD
    )


def accept(world: World, hero: Entity, elder: Entity, ritual: str, relic: Entity, charm: Charm) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    hero.memes["trust"] = hero.memes.get("trust", 0) + 1
    hero.memes["fluster"] = 0
    relic.meters["sealed"] = relic.meters.get("sealed", 0) + 1
    if ritual == "seal":
        relic.meters["shaken"] = 0
    elif ritual == "wake":
        relic.meters["guarded"] = relic.meters.get("guarded", 0) + 1
    else:
        relic.meters["steady"] = relic.meters.get("steady", 0) + 1
    world.say(f"{hero.id} breathed, found the beat, and answered in rhyme.")
    world.say(
        f'\"{charm.line.capitalize()},\" {hero.id} sang, and the old air brightened like dawn. '
        f"{charm.ending.capitalize()}; the {relic.label} stayed safe."
    )


def tell(place: Place, ritual: str, relic_cfg: Relic, name: str, gender: str, elder_type: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=name, kind="character", type=gender, memes={"trait": trait}))
    elder = world.add(Entity(id="Elder", kind="character", type=elder_type))
    relic = world.add(Entity(
        id=relic_cfg.id,
        type=relic_cfg.id,
        label=relic_cfg.label,
        phrase=relic_cfg.phrase,
        owner=hero.id,
        caretaker=elder.id,
    ))
    world.facts.update(hero=hero, elder=elder, relic=relic, ritual=ritual, place=place)

    introduce(world, hero)
    setup_story(world, hero, elder, ritual, relic)
    world.para()
    arrival(world, hero, elder, ritual)
    warning(world, elder, hero, ritual, relic)
    stumble(world, hero, ritual)
    charm = offer_charm(world, elder, hero, ritual, relic)
    world.para()
    if charm:
        accept(world, hero, elder, ritual, relic, charm)
        world.facts["resolved"] = True
        world.facts["charm"] = charm
    else:
        world.say(f"The air stayed tense, and the old line would not close.")
        world.facts["resolved"] = False
    return world


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for ritual in place.affords:
            for rid, relic in RELICS.items():
                if _safe_lookup(RITUALS, ritual)["risk"] in [relic.risk]:
                    for charm in CHARMS:
                        if charm.rhyme_key == ritual and relic.risk in charm.protects:
                            combos.append((pid, ritual, rid))
    return combos


# ---------------------------------------------------------------------------
# Params, QA, prose
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    ritual: str
    relic: str
    name: str
    gender: str
    elder: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic story world of parentheses and rhyme.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--ritual", choices=RITUALS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--elder", choices=ELDER_TITLES)
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


def explain_rejection(ritual: str, relic: str) -> str:
    return f"(No story: {ritual} cannot honestly endanger {relic} in a way the charm can fix.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "ritual", None) and getattr(args, "relic", None):
        if (getattr(args, "place", None) or "archive", getattr(args, "ritual", None), getattr(args, "relic", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "ritual", None) is None or c[1] == getattr(args, "ritual", None))
              and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, ritual, relic = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    elder = getattr(args, "elder", None) or rng.choice(ELDER_TITLES)
    trait = rng.choice(TRAITS)
    return StoryParams(place, ritual, relic, name, gender, elder, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for children that uses the word "parentheses" and ends in rhyme.',
        f"Tell a gentle temple story where {f['hero'].id} learns that {RITUALS[f['ritual']]['verb']} must rhyme.",
        f"Write a story about a young {f['hero'].type} in {f['place'].label} who saves the {f['relic'].label} by following a rhyming chant.",
    ]


def story_text(world: World) -> str:
    return world.render()


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, elder, relic, ritual = f["hero"], f["elder"], f["relic"], f["ritual"]
    return [
        QAItem(
            question=f"Who learned the rhyme in {f['place'].label}?",
            answer=f"{hero.id}, a {hero.memes.get('trait', 'curious')} {hero.type}, learned it with help from {elder.id}.",
        ),
        QAItem(
            question=f"Why did the elder warn {hero.id} about the {relic.label}?",
            answer=f"Because the elder knew that if the chant was rushed, the {relic.label} would go {_safe_lookup(RITUALS, ritual)['soil']}.",
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{hero.id} found the beat, spoke in rhyme, and the {relic.label} stayed safe.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What are parentheses for?", answer="Parentheses are curved marks that hold extra words together or tuck them into a line."),
        QAItem(question="What is rhyme?", answer="Rhyme happens when the ends of words sound alike, like glow and show."),
        QAItem(question="What is a myth?", answer="A myth is an old story that explains special people, gods, or wonders in a magical way."),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(R) :- relic(R), danger(R).
has_charm(R) :- relic(R), danger(R), charm_for(R).
valid_story(P, V, R) :- place(P), ritual(V), relic(R), affords(P, V), danger(R), has_charm(R).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for r in sorted(p.affords):
            lines.append(asp.fact("affords", pid, r))
    for rid, rel in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("danger", rid))  # every relic here is vulnerable to its matched ritual
    for v, cfg in RITUALS.items():
        lines.append(asp.fact("ritual", v))
    for c in CHARMS:
        lines.append(asp.fact("charm_for", c.rhyme_key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), params.ritual, _safe_lookup(RELICS, params.relic), params.name, params.gender, params.elder, params.trait)
    return StorySample(
        params=params,
        story=story_text(world),
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
    StoryParams("archive", "seal", "tablet", "Nia", "girl", "elder", "curious"),
    StoryParams("hall", "wake", "lamp", "Oren", "boy", "priest", "brave"),
    StoryParams("garden", "river", "scroll", "Mira", "girl", "priestess", "gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, ritual, relic) combos:")
        for x in combos:
            print(" ", x)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
