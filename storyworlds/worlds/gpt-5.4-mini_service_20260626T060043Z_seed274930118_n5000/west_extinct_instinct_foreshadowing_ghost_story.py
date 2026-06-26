#!/usr/bin/env python3
"""
Storyworld: west_extinct_instinct_foreshadowing_ghost_story
===========================================================

A small, self-contained story world in a ghost-story register.

Premise:
- A child ventures west of the village at dusk.
- They find signs of something extinct: a bird, a bell, a path, or a lantern from
  a life gone quiet.
- Their instinct tells them the place is not empty; a lonely ghost is present.
- Foreshadowing matters: small clues at the beginning explain the gentle turn
  at the end.
- The story resolves by helping the ghost rest, leaving the west place calm and
  changed.

The model uses typed entities with physical meters and emotional memes, and it
keeps the narration grounded in simulated state.
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
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing" | "spirit"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "spirit":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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


@dataclass
class Place:
    id: str
    name: str
    west: bool = False
    haunted: bool = False
    clues: list[str] = field(default_factory=list)
    hidden: list[str] = field(default_factory=list)
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
class Relic:
    id: str
    label: str
    phrase: str
    extinct_kind: str
    dust: str
    clue: str
    grief: str
    rests_with: str = "ghost"
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
class Ghost:
    id: str
    name: str
    old_name: str
    extinct_kind: str
    tether: str
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    resting: bool = False
    ghost: object | None = None
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    relic: Optional[Relic] = None
    ghost: Optional[Ghost] = None
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)

    clone: object | None = None
    world: object | None = None
    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

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

        clone = World(place=copy.deepcopy(self.place))
        clone.entities = copy.deepcopy(self.entities)
        clone.relic = copy.deepcopy(self.relic)
        clone.ghost = copy.deepcopy(self.ghost)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
    "west_hill": Place(
        id="west_hill",
        name="the west hill",
        west=True,
        haunted=True,
        clues=["a cold bell sound", "a bent lantern glow", "thin tracks in the dust"],
        hidden=["a stone marker", "a nest of feathers"],
    ),
    "west_gate": Place(
        id="west_gate",
        name="the west gate",
        west=True,
        haunted=True,
        clues=["a chain that hummed", "a lantern with no flame", "a hush in the grass"],
        hidden=["a cracked sign", "a trail of ash"],
    ),
    "old_fence": Place(
        id="old_fence",
        name="the old fence",
        west=True,
        haunted=False,
        clues=["a whistle in the boards", "a moth-gray ribbon", "a snagged feather"],
        hidden=["a broken latch", "a lost toy"],
    ),
}

RELICS = {
    "feather": Relic(
        id="feather",
        label="feather",
        phrase="a small gray feather",
        extinct_kind="bird",
        dust="soft dust",
        clue="It matched the shape of a bird that was extinct long ago.",
        grief="The place remembered a sky that no longer came.",
    ),
    "bell": Relic(
        id="bell",
        label="bell",
        phrase="a little bronze bell",
        extinct_kind="village-watch",
        dust="green dust",
        clue="Its sound was old enough to feel like a memory.",
        grief="It had once called people home before the road changed.",
    ),
    "lantern": Relic(
        id="lantern",
        label="lantern",
        phrase="a cracked lantern",
        extinct_kind="lamp-keeper",
        dust="white dust",
        clue="Its glass held a ghostly shine even without a flame.",
        grief="It had once glowed for travelers who no longer came.",
    ),
}

GHOSTS = {
    "owl": Ghost(
        id="owl",
        name="Oren",
        old_name="the west watcher",
        extinct_kind="owl",
        tether="the west hill",
    ),
    "lantern_keeper": Ghost(
        id="keeper",
        name="Mara",
        old_name="the lantern keeper",
        extinct_kind="lamp-keeper",
        tether="the west gate",
    ),
    "bird_child": Ghost(
        id="bird_child",
        name="Nell",
        old_name="the bird child",
        extinct_kind="bird",
        tether="the old fence",
    ),
}

CHILD_NAMES = ["Ava", "Milo", "June", "Eli", "Nora", "Iris", "Theo", "Mina"]
CHILD_TRAITS = ["quiet", "curious", "brave", "careful", "gentle", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    relic: str
    ghost: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
    params: object | None = None
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


ASP_RULES = r"""
% A place is a west place when it is marked west.
west_place(P) :- place(P), west(P).

% A relic is eerie when it points to an extinct thing and the place is haunted.
eerie(P, R) :- haunted(P), relic(R), extinct_kind(R, K), extinct(K).

% Foreshadowing: the place offers clues that hint at the relic and ghost.
foreshadow(P, R, G) :- clue(P, C), relic_clue(R, C), tether(G, P).

% A story is valid when the child can notice the west place, the eerie relic,
% and the ghost can rest by the end.
valid_story(P, R, G) :- west_place(P), eerie(P, R), ghost(G), tether(G, P).

#show valid_story/3.
#show west_place/1.
#show eerie/2.
#show foreshadow/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.west:
            lines.append(asp.fact("west", pid))
        if place.haunted:
            lines.append(asp.fact("haunted", pid))
        for clue in place.clues:
            lines.append(asp.fact("clue", pid, clue))
    for rid, relic in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("extinct_kind", rid, relic.extinct_kind))
        lines.append(asp.fact("relic_clue", rid, relic.clue))
    for gid, ghost in GHOSTS.items():
        lines.append(asp.fact("ghost", gid))
        lines.append(asp.fact("tether", gid, ghost.tether))
        lines.append(asp.fact("extinct", ghost.extinct_kind))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    valid = set(asp_valid_stories())
    python_valid = set(valid_combos())
    if valid == python_valid:
        print(f"OK: clingo gate matches python gate ({len(valid)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("only in clingo:", sorted(valid - python_valid))
    print("only in python:", sorted(python_valid - valid))
    return 1


# ---------------------------------------------------------------------------
# Logic helpers
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        if not place.west:
            continue
        for relic in RELICS.values():
            for ghost in GHOSTS.values():
                if ghost.tether == place.name:
                    combos.append((place.id, relic.id, ghost.id))
    return combos


def explain_rejection(place: str, relic: str, ghost: str) -> str:
    return (
        f"(No story: the chosen path does not fit the ghost tale. "
        f"Pick a west place with a tethered ghost and an eerie relic.)"
    )


def choose_name(rng: random.Random) -> str:
    return rng.choice(CHILD_NAMES)


def choose_trait(rng: random.Random) -> str:
    return rng.choice(CHILD_TRAITS)


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    relic = _safe_lookup(RELICS, params.relic)
    ghost_def = _safe_lookup(GHOSTS, params.ghost)

    world = World(place=place)
    child = world.add(
        Entity(
            id=params.name,
            kind="character",
            type="child",
            label=params.name,
            meters={"fear": 0.0, "wonder": 0.0, "care": 0.0},
            memes={"instinct": 0.0, "bravery": 0.0, "comfort": 0.0},
        )
    )
    ghost = Ghost(
        id=ghost_def.id,
        name=ghost_def.name,
        old_name=ghost_def.old_name,
        extinct_kind=ghost_def.extinct_kind,
        tether=ghost_def.tether,
        meters={"cold": 1.0, "glow": 0.2},
        memes={"lonely": 1.0, "hope": 0.0},
    )
    world.ghost = ghost
    world.relic = relic

    # Act 1: setup and foreshadowing.
    world.say(f"{child.id} lived on the east side of the village, but one dusk {child.id} wandered west.")
    world.say(f"The path led to {place.name}, where the air felt cool and old.")
    world.say(
        f"{child.id} noticed {place.clues[0]}. It was the kind of clue that made a child slow down."
    )
    child.meters["wonder"] += 1
    child.memes["instinct"] += 1

    world.para()

    # Act 2: the ghost-story turn.
    world.say(
        f"Near the grass, {child.id} found {relic.phrase}. {relic.clue}"
    )
    world.say(
        f"{relic.grief} {child.id}'s instinct said the west was not empty."
    )
    child.meters["fear"] += 1
    child.meters["wonder"] += 1
    if place.haunted:
        world.say(
            f"Then a small chill moved by the gate, and {ghost.name} appeared like breath on a window."
        )
        ghost.memes["lonely"] += 0.5

    world.para()

    # Turn: child chooses care over fear.
    child.memes["bravery"] += 1
    world.say(
        f"{child.id} did not run. Instead, {child.id} remembered the hint hidden in the bell of the night."
    )
    world.say(
        f"With a soft voice, {child.id} asked why {ghost.name} stayed near the west place."
    )
    ghost.memes["hope"] += 1
    world.say(
        f"{ghost.name} answered that something extinct had gone quiet here long ago, and the silence had never been kind."
    )

    # Resolution: making peace and resting.
    ghost.resting = True
    ghost.memes["lonely"] = 0.0
    ghost.meters["glow"] = 1.0
    child.meters["care"] += 1
    child.memes["comfort"] += 1

    world.say(
        f"{child.id} set the relic on a flat stone and listened until the west wind felt gentle."
    )
    world.say(
        f"The ghost bowed, lighter now, and the fading glow drifted into the dark like a star going home."
    )
    world.say(
        f"By the time {child.id} walked back east, {place.name} was still, but it no longer felt lonely."
    )

    world.facts.update(
        child=child,
        ghost=ghost,
        relic=relic,
        place=place,
        foreshadow=place.clues,
        extinct_word=relic.extinct_kind,
    )
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    relic = _safe_fact(world, f, "relic")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a ghost story for a young child that includes the words "west", "extinct", and "instinct".',
        f"Tell a gentle foreshadowing story about {child.id} walking west to {place.name} and finding {relic.phrase}.",
        f"Write a spooky-but-kind story where a child follows an instinct and helps a lonely ghost rest.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    ghost = _safe_fact(world, f, "ghost")
    relic = _safe_fact(world, f, "relic")
    place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Where did {child.id} go when the story turned toward the spooky part?",
            answer=f"{child.id} went west to {place.name}, where the air felt old and quiet.",
        ),
        QAItem(
            question=f"What did {child.id} find that hinted at something extinct?",
            answer=f"{child.id} found {relic.phrase}, and it suggested a creature or life that was extinct long ago.",
        ),
        QAItem(
            question=f"Why did {child.id} feel that the west place was not empty?",
            answer=(
                f"{child.id}'s instinct noticed the clues and then {ghost.name} appeared, so the place felt haunted rather than empty."
            ),
        ),
        QAItem(
            question=f"What changed for {ghost.name} by the end?",
            answer=f"{ghost.name} became calm and resting, and the lonely feeling faded away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives early clues that hint at what will matter later in the story.",
        ),
        QAItem(
            question="What is instinct?",
            answer="Instinct is a quick feeling that helps someone sense what to do without thinking about every step.",
        ),
        QAItem(
            question="What does extinct mean?",
            answer="Extinct means a kind of animal or plant no longer lives anywhere.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    lines.append(f"place: {world.place.name} west={world.place.west} haunted={world.place.haunted}")
    if world.relic:
        lines.append(f"relic: {world.relic.label} / {world.relic.extinct_kind}")
    if world.ghost:
        lines.append(
            f"ghost: {world.ghost.name} resting={world.ghost.resting} lonely={world.ghost.memes.get('lonely', 0)} hope={world.ghost.memes.get('hope', 0)}"
        )
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A gentle westward ghost story with foreshadowing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=CHILD_TRAITS)
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
    combos = valid_combos()
    if getattr(args, "place", None) or getattr(args, "relic", None) or getattr(args, "ghost", None):
        combos = [
            c for c in combos
            if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
            and (getattr(args, "relic", None) is None or c[1] == getattr(args, "relic", None))
            and (getattr(args, "ghost", None) is None or c[2] == getattr(args, "ghost", None))
        ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, relic, ghost = rng.choice(list(combos))
    return StoryParams(
        place=place,
        relic=relic,
        ghost=ghost,
        name=getattr(args, "name", None) or choose_name(rng),
        trait=getattr(args, "trait", None) or choose_trait(rng),
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place, relic, ghost in valid_combos():
            params = StoryParams(
                place=place,
                relic=relic,
                ghost=ghost,
                name="Ava",
                trait="curious",
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
            rng = random.Random(base_seed + i)
            i += 1
            params = resolve_params(args, rng)
            params.seed = base_seed + i - 1
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
        header = ""
        if len(samples) > 1:
            p = sample.params
            header = f"### variant {idx + 1}: {p.name} at {p.place} with {p.relic}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
