#!/usr/bin/env python3
"""
storyworlds/worlds/pensive_problem_solving_quest_twist_whodunit.py
===================================================================

A small, child-facing whodunit story world: a curious sleuth notices a problem,
follows a quest of clues, and lands on a gentle twist that solves the mystery.

Premise:
- Something small goes missing in a cozy place.
- The main character is pensive, meaning they pause, think, and look carefully.
- Each story becomes a short mystery with clues, suspects, and a satisfying reveal.

The simulated world keeps track of:
- physical meters: where items are, whether drawers are open, whether clues are
  found, whether a hidden place is damp/dusty/etc.
- emotional memes: worry, curiosity, relief, suspicion, pride, gratitude.

Narrative shape:
1. A problem appears.
2. The sleuth forms a quest and checks clues.
3. A twist changes what seemed true.
4. The ending proves the change with a concrete recovered item or corrected guess.
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

# ---------------------------------------------------------------------------
# Core knobs
# ---------------------------------------------------------------------------

THRESHOLD = 1.0

PLACES = {
    "kitchen": {
        "label": "the kitchen",
        "hiding_spots": ["the cookie jar", "under the tea towel", "behind the fruit bowl"],
        "homey": True,
    },
    "library": {
        "label": "the library",
        "hiding_spots": ["between picture books", "under a cushion", "behind the lamp"],
        "homey": True,
    },
    "playroom": {
        "label": "the playroom",
        "hiding_spots": ["inside the toy box", "under the rug", "behind the blocks"],
        "homey": True,
    },
    "garden_shed": {
        "label": "the garden shed",
        "hiding_spots": ["on a shelf", "inside a bucket", "behind a watering can"],
        "homey": True,
    },
}

MYSTERIES = {
    "cookie": {
        "thing": "cookie",
        "plural": False,
        "value": "a warm cookie",
        "missing_phrase": "missing",
        "clue_kind": "crumb",
        "clue_text": "tiny crumbs",
        "twist": "a helpful squirrel had carried it to a safer spot",
        "suspects": ["the cat", "the wind", "the helper squirrel"],
        "solution": "the helper squirrel",
    },
    "ribbon": {
        "thing": "ribbon",
        "plural": False,
        "value": "a shiny ribbon",
        "missing_phrase": "gone",
        "clue_kind": "shine",
        "clue_text": "a thin shiny thread",
        "twist": "the ribbon had slipped behind something bright and had not been stolen at all",
        "suspects": ["the cat", "the breeze", "a bright hook"],
        "solution": "a bright hook",
    },
    "key": {
        "thing": "key",
        "plural": False,
        "value": "a small brass key",
        "missing_phrase": "lost",
        "clue_kind": "scratch",
        "clue_text": "little scratch marks",
        "twist": "the key had been tucked into a pocket by mistake",
        "suspects": ["the drawer", "the coat pocket", "the table"],
        "solution": "the coat pocket",
    },
    "marble": {
        "thing": "marble",
        "plural": False,
        "value": "a blue marble",
        "missing_phrase": "gone",
        "clue_kind": "glint",
        "clue_text": "a blue glint",
        "twist": "the marble had rolled into a toy and was hiding in plain sight",
        "suspects": ["the rug", "the toy truck", "the box"],
        "solution": "the toy truck",
    },
}

TOOLS = {
    "magnifier": {
        "label": "a little magnifying glass",
        "verb": "look closely",
        "helps": {"crumb", "shine", "scratch", "glint"},
    },
    "notebook": {
        "label": "a small notebook",
        "verb": "write clues down",
        "helps": {"crumb", "shine", "scratch", "glint"},
    },
    "lamp": {
        "label": "a bright lamp",
        "verb": "see into dark corners",
        "helps": {"shine", "glint", "scratch"},
    },
    "ladder": {
        "label": "a short step stool",
        "verb": "reach high places",
        "helps": {"shine", "crumb"},
    },
}

NAMES = ["Mina", "Arlo", "June", "Theo", "Nina", "Owen", "Ivy", "Luca"]
SIDEKICKS = ["grandma", "grandpa", "a parent", "an older sister", "an older brother", "a neighbor"]
TRAITS = ["pensive", "careful", "quiet", "curious", "gentle", "patient"]



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
    owner: Optional[str] = None
    location: str = ""
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clue: object | None = None
    helper: object | None = None
    missing: object | None = None
    sleuth: object | None = None
    suspect: object | None = None
    tool_ent: object | None = None
    twist: object | None = None
    def __post_init__(self):
        for k in ["open", "searched", "found", "recovered", "dusty", "shiny", "moved"]:
            self.meters.setdefault(k, 0.0)
        for k in ["worry", "curiosity", "suspicion", "relief", "pride", "calm"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "sister", "grandma", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "brother", "grandpa", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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
class Scene:
    place: str = "kitchen"
    mystery: str = "cookie"
    seed_word: str = "pensive"
    scene: object | None = None
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
    def __init__(self, scene: Scene):
        self.scene = scene
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
        import copy
        w = World(self.scene)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


# ---------------------------------------------------------------------------
# Story helpers
# ---------------------------------------------------------------------------

def clue_word(mystery: dict) -> str:
    return mystery["clue_kind"]


def missing_noun(mystery: dict) -> str:
    return mystery["thing"]


def article_name(name: str) -> str:
    return name


def suspense_line(mystery: dict) -> str:
    return f"Something felt odd because {mystery['value']} was {mystery['missing_phrase']}."


def location_label(place: str) -> str:
    return _safe_lookup(PLACES, place)["label"]


def suspect_sentence(suspects: list[str]) -> str:
    if len(suspects) == 1:
        return suspects[0]
    return ", ".join(suspects[:-1]) + ", and " + suspects[-1]


def trace_item(ent: Entity) -> str:
    meters = {k: v for k, v in ent.meters.items() if v}
    memes = {k: v for k, v in ent.memes.items() if v}
    bits = []
    if meters:
        bits.append(f"meters={meters}")
    if memes:
        bits.append(f"memes={memes}")
    if ent.location:
        bits.append(f"location={ent.location}")
    return f"{ent.id} ({ent.type}) " + " ".join(bits)


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

@dataclass
class Rule:
    name: str
    apply: callable
    RULES: list = field(default_factory=list)
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


def _r_search(world: World) -> list[str]:
    out = []
    sleuth = world.get("sleuth")
    mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "mystery")
    if sleuth.memes["curiosity"] < THRESHOLD:
        return out
    if world.get("clue").meters["found"] >= THRESHOLD:
        return out
    sig = ("search",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    clue = world.get("clue")
    clue.meters["found"] = 1
    clue.hidden = False
    out.append(f"The sleuth found {mystery['clue_text']} near the first place they checked.")
    return out


def _r_twist(world: World) -> list[str]:
    out = []
    sleuth = world.get("sleuth")
    clue = world.get("clue")
    if clue.meters["found"] < THRESHOLD:
        return out
    if world.get("twist").meters["revealed"] >= THRESHOLD:
        return out
    if sleuth.memes["curiosity"] < 1:
        return out
    sig = ("twist",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("twist").meters["revealed"] = 1
    out.append("The clue did not point to a thief at all.")
    return out


def _r_resolution(world: World) -> list[str]:
    out = []
    mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "mystery")
    twist = world.get("twist")
    item = world.get("missing")
    if twist.meters["revealed"] < THRESHOLD:
        return out
    if item.meters["recovered"] >= THRESHOLD:
        return out
    sig = ("resolve",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    item.meters["recovered"] = 1
    world.get(mystery["solution"]).meters["helped"] = 1
    out.append(f"The missing {mystery['thing']} was recovered from the place nobody expected.")
    return out


RULES = [Rule("search", _r_search), Rule("twist", _r_twist), Rule("resolve", _r_resolution)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            got = rule.apply(world)
            if got:
                changed = True
                lines.extend(got)
    if narrate:
        for line in lines:
            world.say(line)
    return lines


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------

def is_reasonable(place: str, mystery: str, tool: str) -> bool:
    return place in PLACES and mystery in MYSTERIES and tool in TOOLS


def explain_rejection(place: str, mystery: str, tool: str) -> str:
    return f"(No story: the combination of {place}, {mystery}, and {tool} does not make a sensible mystery.)"


# ---------------------------------------------------------------------------
# Screenplay
# ---------------------------------------------------------------------------

def tell(scene: Scene, hero_name: str, sidekick: str, tool: str, trait: str) -> World:
    mystery = _safe_lookup(MYSTERIES, scene.mystery)
    world = World(scene)

    sleuth = world.add(Entity(id="sleuth", kind="character", type="child", label=hero_name))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=sidekick))
    missing = world.add(Entity(id="missing", type=mystery["thing"], label=mystery["value"], owner=helper.id, hidden=True))
    clue = world.add(Entity(id="clue", type="clue", label=mystery["clue_text"], hidden=True))
    twist = world.add(Entity(id="twist", type="twist", label=mystery["twist"], hidden=True))
    suspect = world.add(Entity(id="suspect", type="suspect", label=mystery["solution"], hidden=True))
    tool_ent = world.add(Entity(id="tool", type="tool", label=_safe_lookup(TOOLS, tool)["label"], owner=sleuth.id))

    world.facts = {
        "scene": scene,
        "mystery": mystery,
        "hero": sleuth,
        "helper": helper,
        "missing": missing,
        "clue": clue,
        "twist": twist,
        "suspect": suspect,
        "tool": tool_ent,
        "trait": trait,
    }

    # Act 1
    world.say(f"{hero_name} was a {trait} child who liked to pause and think before speaking.")
    world.say(f"One day, in {location_label(scene.place)}, {missing.label} was nowhere to be seen.")
    world.say(f"{helper.label.capitalize()} looked worried, and {hero_name} felt the mystery begin.")
    world.para()

    # Act 2
    sleuth.memes["worry"] += 1
    sleuth.memes["curiosity"] += 1
    world.say(f"{hero_name} picked up {tool_ent.label} and decided to {_safe_lookup(TOOLS, tool)['verb']}.")
    world.say(f"With a pensive face, {hero_name} searched the room one careful corner at a time.")
    world.say(f"There were a few suspects at first: {suspect_sentence(mystery['suspects'])}.")
    clue.meters["found"] = 0
    propagate(world, narrate=True)
    world.para()

    # Act 3
    world.say("Then came the twist.")
    world.say(mystery["twist"].capitalize() + ".")
    twist.meters["revealed"] = 1
    missing.meters["recovered"] = 1
    world.say(f"{hero_name} smiled, and the room felt calm again.")
    world.say(f"In the end, {missing.label} was back where it belonged, and the mystery was solved.")
    sleuth.memes["relief"] += 1
    sleuth.memes["pride"] += 1
    helper.memes["gratitude"] += 1
    return world


# ---------------------------------------------------------------------------
# Registries and params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    mystery: str
    tool: str
    name: str
    sidekick: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for mystery in MYSTERIES:
            for tool in TOOLS:
                combos.append((place, mystery, tool))
    return combos


CURATED = [
    StoryParams(place="kitchen", mystery="cookie", tool="magnifier", name="Mina", sidekick="grandma", trait="pensive"),
    StoryParams(place="library", mystery="key", tool="notebook", name="Theo", sidekick="a parent", trait="curious"),
    StoryParams(place="playroom", mystery="marble", tool="lamp", name="Ivy", sidekick="older sister", trait="careful"),
    StoryParams(place="garden_shed", mystery="ribbon", tool="ladder", name="Arlo", sidekick="grandpa", trait="quiet"),
]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short whodunit story for children where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").label} is {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trait")} and uses {(f.get("tool") or next(iter(TOOLS.values()))).label}.',
        f"Tell a mystery about a missing {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery")['thing']} in {location_label(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "scene").place)} with a twist at the end.",
        f"Write a story where a child solves a small problem by noticing a clue and changing their guess.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").label
    helper = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper").label
    mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery")
    place = location_label(_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "scene").place)
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero}, a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "trait")} child who stayed pensive and solved the mystery.",
        ),
        QAItem(
            question=f"What was missing in {place}?",
            answer=f"{mystery['value'].capitalize()} was missing from {place}.",
        ),
        QAItem(
            question=f"What clue helped the sleuth think harder?",
            answer=f"The clue was {mystery['clue_text']}, which made the problem clearer.",
        ),
        QAItem(
            question=f"Who worried at the start of the story?",
            answer=f"{(getattr(helper, 'capitalize')() if callable(getattr(helper, 'capitalize', None)) else str(helper).capitalize())} worried when the {mystery['thing']} could not be found.",
        ),
        QAItem(
            question=f"What was the twist in the mystery?",
            answer=f"The twist was that {mystery['twist']}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the missing {mystery['thing']} recovered and everyone feeling calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    mystery = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "mystery")
    tool = (f.get("tool") or next(iter(TOOLS.values()))).label
    base = [
        QAItem(
            question="What does it mean to be pensive?",
            answer="Being pensive means pausing to think carefully before acting or speaking.",
        ),
        QAItem(
            question=f"What is {tool} for?",
            answer=f"{(getattr(tool, 'capitalize')() if callable(getattr(tool, 'capitalize', None)) else str(tool).capitalize())} helps a person search carefully, depending on what kind of clue they need to notice.",
        ),
        QAItem(
            question=f"What is a clue in a mystery?",
            answer="A clue is a small piece of information that helps someone figure out what happened.",
        ),
    ]
    if mystery["thing"] == "cookie":
        base.append(QAItem(question="Why are crumbs useful in a mystery?", answer="Crumbs can show where a cookie was carried or dropped."))
    return base


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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(kitchen). place(library). place(playroom). place(garden_shed).
mystery(cookie). mystery(ribbon). mystery(key). mystery(marble).
tool(magnifier). tool(notebook). tool(lamp). tool(ladder).

reasonably_compatible(P, M, T) :- place(P), mystery(M), tool(T).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery", m))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show reasonably_compatible/3."))
    return sorted(set(asp.atoms(model, "reasonably_compatible")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pensive child-friendly whodunit story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--sidekick", choices=SIDEKICKS)
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
    combos = valid_combos()
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))
        and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery, tool = rng.choice(filtered)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    trait = getattr(args, "trait", None) or "pensive"
    return StoryParams(place=place, mystery=mystery, tool=tool, name=name, sidekick=sidekick, trait=trait)


def generate(params: StoryParams) -> StorySample:
    scene = Scene(place=params.place, mystery=params.mystery, seed_word="pensive")
    world = tell(scene, params.name, params.sidekick, params.tool, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append("  " + trace_item(e))
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


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
        print(asp_program("#show reasonably_compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print("  ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.mystery} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
