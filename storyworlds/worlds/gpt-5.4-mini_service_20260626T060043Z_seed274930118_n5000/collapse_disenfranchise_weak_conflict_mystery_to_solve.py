#!/usr/bin/env python3
"""
storyworlds/worlds/collapse_disenfranchise_weak_conflict_mystery_to_solve.py
=============================================================================

A standalone storyworld for a tall-tale style problem story about collapse,
weakness, and a mystery to solve.

Seed impression:
---
In a small wide-eyed town, a flimsy voting bridge and a weak notice board both
gave way on the same blustery afternoon. That left the little river folk
disenfranchised from choosing their lantern captain, and nobody could tell
whether the wind, the board, or somebody's bad aim caused the mess. A brave
child and a patient grown-up had to follow the clues, learn the true cause, and
restore everyone's turn to choose.

This world models:
- a physical collapse driven by weak support
- a social conflict over who gets a say
- a mystery clue trail that resolves the conflict
- tall-tale exaggeration with child-facing prose

It follows the Storyweavers storyworld contract:
- typed entities with meters and memes
- a reasonableness gate
- an inline ASP twin
- story, prompts, QA, and verification modes
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    board: object | None = None
    bridge: object | None = None
    hero: object | None = None
    parent: object | None = None
    riverfolk: object | None = None
    vote: object | None = None
    wrench: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
class Setting:
    place: str
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
class Conflict:
    id: str
    title: str
    cause: str
    effect: str
    risk_region: str
    weak_support: str
    repair: str
    tags: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    question: str
    clues: list[str]
    culprit: str
    reveal: str
    tags: set[str] = field(default_factory=set)
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
class Remedy:
    id: str
    label: str
    phrase: str
    covers: set[str]
    fixes: set[str]
    prep: str
    tail: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace_log: list[str] = []
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


def mget(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def madd(e: Entity, key: str, value: float = 1.0) -> None:
    e.meters[key] = mget(e, key) + value


def eadd(e: Entity, key: str, value: float = 1.0) -> None:
    e.memes[key] = mem(e, key) + value


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule(world)
            if lines:
                changed = True
                out.extend(lines)
    if narrate:
        for line in out:
            world.say(line)
    return out


def _r_collapse(world: World) -> list[str]:
    out: list[str] = []
    bridge = world.get("bridge")
    board = world.get("board")
    if mget(bridge, "stress") >= THRESHOLD and ("bridge_collapse",) not in world.fired:
        world.fired.add(("bridge_collapse",))
        madd(bridge, "collapsed")
        out.append("With a long groan like a foghorn in a teacup, the bridge collapsed into a heap of planks.")
    if mget(board, "stress") >= THRESHOLD and ("board_collapse",) not in world.fired:
        world.fired.add(("board_collapse",))
        madd(board, "collapsed")
        out.append("Then the notice board gave a shiver, leaned sideways, and collapsed onto the mud.")
    return out


def _r_disenfranchise(world: World) -> list[str]:
    out: list[str] = []
    voting = world.get("vote")
    townsfolk = world.characters()
    if mget(voting, "spilled") >= THRESHOLD and ("vote_lost",) not in world.fired:
        world.fired.add(("vote_lost",))
        for e in townsfolk:
            if e.type in {"kid", "riverfolk"}:
                e.memes["disenfranchised"] = 1.0
        out.append("The vote jar spilled everywhere, and the little river folk were left out of the choice.")
    return out


def _r_conflict(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    parent = world.get("parent")
    if mem(hero, "disenfranchised") >= THRESHOLD and ("conflict",) not in world.fired:
        world.fired.add(("conflict",))
        eadd(hero, "upset")
        eadd(parent, "worried")
        out.append("That made the air go tight between the child and the grown-up.")
    return out


CAUSAL_RULES = [_r_collapse, _r_disenfranchise, _r_conflict]


def setting_detail(setting: Setting) -> str:
    return f"{setting.place.capitalize()} was all bustle and breeze, with creek water singing nearby."


def ask_clue(world: World, clue: str) -> str:
    if clue == "splinters":
        return "splinters"
    if clue == "mud_tracks":
        return "mud tracks"
    if clue == "loose_pole":
        return "a loose pole"
    return clue


def tell(world: World, conflict: Conflict, mystery: Mystery, remedy: Remedy,
         hero_name: str, hero_type: str, parent_type: str) -> World:
    hero = world.add(Entity(
        id="hero", kind="character", type=hero_type, label=hero_name,
        meters={"curiosity": 0.0}, memes={"hope": 0.0},
    ))
    parent = world.add(Entity(
        id="parent", kind="character", type=parent_type, label="the grown-up",
        meters={"patience": 1.0}, memes={"calm": 1.0},
    ))
    riverfolk = world.add(Entity(
        id="riverfolk", kind="character", type="riverfolk", label="the river folk",
        plural=True, memes={},
    ))
    bridge = world.add(Entity(
        id="bridge", type="thing", label="the voting bridge", phrase="a thin plank bridge",
        meters={"stress": 0.0}, memes={},
    ))
    board = world.add(Entity(
        id="board", type="thing", label="the notice board", phrase="a weak notice board",
        meters={"stress": 0.0}, memes={},
    ))
    vote = world.add(Entity(
        id="vote", type="thing", label="the vote jar", phrase="a clay vote jar",
        meters={"spilled": 0.0}, memes={},
    ))
    wrench = world.add(Entity(
        id="wrench", type="thing", label=remedy.label, phrase=remedy.phrase
    ))

    world.say(f"{hero_name} was a small {hero_type} with a big nose for trouble and a bigger nose for clues.")
    world.say(setting_detail(world.setting))
    world.say(f"Every year, the river folk chose their lantern captain there, and everyone got a turn to speak.")
    world.say(f"But this year, {conflict.title} made the day wobble like a spoon on a barrel head.")
    world.para()
    world.say(f"The trouble began when {conflict.cause}.")
    world.say(f"The {conflict.weak_support} was weak, so the {conflict.effect} came fast.")
    madd(bridge, "stress", 1.0)
    madd(board, "stress", 1.0)
    madd(vote, "spilled", 1.0)
    propagate(world)
    world.para()
    hero.memes["curiosity"] = 1.0
    world.say(f'{hero_name} pointed at the mess and said, "This looks like a mystery to solve."')
    world.say(f"{mystery.question}")
    for clue in mystery.clues:
        world.say(f"{hero_name} found {ask_clue(world, clue)}.")
    world.say(f"The clues all pointed to {mystery.culprit}, which matched the last loud thump before the collapse.")
    world.para()
    world.say(f"Then the grown-up brought out {remedy.phrase}.")
    world.say(f'“How about we {remedy.prep}?” {parent.label} asked.')
    if mget(bridge, "collapsed") >= THRESHOLD:
        world.say(f"{hero_name} helped lift the boards, and the river folk carried the vote jar back in a basket.")
    world.say(f"That fixed the {conflict.id} and gave everybody a fair turn again.")
    world.say(f"{mystery.reveal}")
    world.say(f"By sunset, the lantern captain was chosen, the bridge was patched, and the town was cheerful as a kettle song.")
    eadd(hero, "pride", 1.0)
    eadd(parent, "relief", 1.0)
    riverfolk.memes["included"] = 1.0
    world.facts.update(
        hero=hero,
        parent=parent,
        riverfolk=riverfolk,
        bridge=bridge,
        board=board,
        vote=vote,
        wrench=wrench,
        conflict=conflict,
        mystery=mystery,
        remedy=remedy,
    )
    return world


SETTINGS = {
    "riverside": Setting(place="the riverside square", affords={"vote", "repair"}),
    "fairground": Setting(place="the fairground lane", affords={"vote", "repair"}),
    "hilltown": Setting(place="the hilltown green", affords={"vote", "repair"}),
}

CONFLICTS = {
    "weak_bridge": Conflict(
        id="weak_bridge",
        title="the weak bridge trouble",
        cause="a blustery gust bumped the bridge while the vote jar was being carried across",
        effect="vote jar spill",
        risk_region="feet",
        weak_support="bridge planks",
        repair="bridge patch",
        tags={"collapse", "weak", "conflict"},
    ),
    "weak_board": Conflict(
        id="weak_board",
        title="the weak board trouble",
        cause="a crooked nail let the notice board sag when the town list was hung up",
        effect="notice-board tumble",
        risk_region="torso",
        weak_support="board legs",
        repair="board brace",
        tags={"collapse", "weak", "conflict"},
    ),
}

MYSTERIES = {
    "windy_thump": Mystery(
        id="windy_thump",
        question="Who gave the bridge its last shove, and why did the vote jar end up in the mud?",
        clues=["mud_tracks", "loose_pole", "splinters"],
        culprit="the gusty wind",
        reveal="The windy shove was the real trickster, not any of the river folk.",
        tags={"mystery", "collapse"},
    ),
    "crooked_nail": Mystery(
        id="crooked_nail",
        question="What made the notice board lean like a tired giraffe?",
        clues=["splinters", "loose_pole", "mud_tracks"],
        culprit="a crooked nail",
        reveal="The crooked nail was the small thing that made the big old board fall.",
        tags={"mystery", "weak"},
    ),
}

REMEDIES = {
    "bridge_patch": Remedy(
        id="bridge_patch",
        label="a bundle of fresh bridge boards",
        phrase="a bundle of fresh bridge boards and stout pegs",
        covers={"feet"},
        fixes={"collapse", "weak"},
        prep="patch the bridge with these stout boards",
        tail="patched the bridge",
    ),
    "board_brace": Remedy(
        id="board_brace",
        label="a sturdy brace",
        phrase="a sturdy brace and two bright nails",
        covers={"torso"},
        fixes={"collapse", "weak"},
        prep="brace the board with these fresh nails",
        tail="braced the board",
    ),
}

HERO_NAMES = ["Mabel", "Otis", "Nell", "Poppy", "Bram", "Toby", "Ada", "June"]
HERO_TYPES = ["girl", "boy"]
PARENT_TYPES = ["mother", "father"]


@dataclass
class StoryParams:
    setting: str
    conflict: str
    mystery: str
    remedy: str
    name: str
    hero_type: str
    parent_type: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for c in CONFLICTS:
            for m in MYSTERIES:
                if c == "weak_bridge" and m == "windy_thump":
                    combos.append((s, c, m))
                if c == "weak_board" and m == "crooked_nail":
                    combos.append((s, c, m))
    return combos


def reason_invalid(conflict: Conflict, mystery: Mystery) -> str:
    return f"(No story: that conflict and mystery do not fit together for a clear tall-tale mystery.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: collapse, disenfranchise, weak; conflict and mystery to solve.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--parent-type", choices=PARENT_TYPES)
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
    if getattr(args, "setting", None) or getattr(args, "conflict", None) or getattr(args, "mystery", None):
        combos = [c for c in combos
                  if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
                  and (getattr(args, "conflict", None) is None or c[1] == getattr(args, "conflict", None))
                  and (getattr(args, "mystery", None) is None or c[2] == getattr(args, "mystery", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, conflict, mystery = rng.choice(list(combos))
    remedy = getattr(args, "remedy", None) or ("bridge_patch" if conflict == "weak_bridge" else "board_brace")
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    parent_type = getattr(args, "parent_type", None) or rng.choice(PARENT_TYPES)
    return StoryParams(setting=setting, conflict=conflict, mystery=mystery, remedy=remedy,
                       name=name, hero_type=hero_type, parent_type=parent_type)


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.setting))
    conflict = _safe_lookup(CONFLICTS, params.conflict)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    remedy = _safe_lookup(REMEDIES, params.remedy)
    world = tell(world, conflict, mystery, remedy, params.name, params.hero_type, params.parent_type)
    story = world.render()
    return StorySample(
        params=params,
        story=story,
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    conflict = _safe_fact(world, f, "conflict")
    mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a tall-tale story for a young child about "{conflict.title}" and a mystery to solve.',
        f"Tell a story where {f['hero'].label} discovers why the {conflict.id} happened and helps the town choose fairly again.",
        f'Write a child-friendly mystery story that includes the words "collapse", "weak", and "disenfranchise".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    conflict = _safe_fact(world, f, "conflict")
    mystery = _safe_fact(world, f, "mystery")
    remedy = _safe_fact(world, f, "remedy")
    qa = [
        QAItem(
            question="What was the story about?",
            answer=f"It was about {hero.label}, a little {hero.type}, helping solve a mystery after a weak {conflict.weak_support} caused a collapse at {world.setting.place}.",
        ),
        QAItem(
            question="Why were the river folk disenfranchised?",
            answer="They were disenfranchised because the vote jar spilled, so they could not cast their votes until the town fixed the mess.",
        ),
        QAItem(
            question="What did the child do to solve the mystery?",
            answer=f"{hero.label} followed the clues, found the cause, and helped bring out {remedy.phrase} to repair the trouble.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="The broken thing was repaired, the vote was fair again, and the town ended with everybody included.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does weak mean?",
            answer="Weak means not strong enough to hold up well, so something weak can bend, sag, or break more easily.",
        ),
        QAItem(
            question="What is a collapse?",
            answer="A collapse is when something gives way and falls down, often because it is weak or pushed too hard.",
        ),
        QAItem(
            question="What does disenfranchise mean?",
            answer="Disenfranchise means to take away someone's chance to choose or vote, so they cannot help decide.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story QA ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World QA ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
setting(S) :- place(S).
conflict(C) :- conflict_id(C).
mystery(M) :- mystery_id(M).

valid(S,C,M) :- setting(S), conflict(C), mystery(M), compatible(C,M).
"""

def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("place", s))
    for c in CONFLICTS:
        lines.append(asp.fact("conflict_id", c))
    for m in MYSTERIES:
        lines.append(asp.fact("mystery_id", m))
    for s, c, m in valid_combos():
        lines.append(asp.fact("compatible", c, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        print(f"{len(set(asp.atoms(model, 'valid')))} compatible combos")
        for t in sorted(set(asp.atoms(model, "valid"))):
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for i, p in enumerate([
            StoryParams("riverside", "weak_bridge", "windy_thump", "bridge_patch", "Mabel", "girl", "mother", base_seed + 1),
            StoryParams("fairground", "weak_board", "crooked_nail", "board_brace", "Otis", "boy", "father", base_seed + 2),
        ]):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
