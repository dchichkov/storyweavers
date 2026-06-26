#!/usr/bin/env python3
"""
A standalone story world for a small superhero mystery:
- digital clues
- a procedure to follow
- dialogue-driven problem solving
- a bright, child-facing superhero style
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    clue: object | None = None
    gadget: object | None = None
    hero: object | None = None
    missing: object | None = None
    sidekick: object | None = None
    solves: object | None = None
    villain: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "heroine"}
        male = {"boy", "man", "father", "hero"}
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


@dataclass
class Place:
    name: str
    indoors: bool = True
    supports: set[str] = field(default_factory=set)
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
class Procedure:
    id: str
    name: str
    steps: list[str]
    clue_kind: str
    risk_kind: str
    clue_place: str
    dialogue_prompt: str
    resolution: str
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
class Mystery:
    id: str
    missing: str
    culprit: str
    clue: str
    hidden_where: str
    exposed_by: str
    label: str
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
class Tool:
    id: str
    label: str
    helps: set[str]
    solves: set[str]
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.scene: str = "setup"

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "tower": Place("the bright tower", indoors=True, supports={"scan", "talk", "map"}),
    "lab": Place("the hero lab", indoors=True, supports={"scan", "talk", "repair"}),
    "cityhall": Place("city hall", indoors=True, supports={"scan", "talk", "procedure"}),
}

PROCEDURES = {
    "scan_talk_fix": Procedure(
        id="scan_talk_fix",
        name="scan, talk, and fix",
        steps=["scan the clue", "ask careful questions", "repair the device"],
        clue_kind="digital",
        risk_kind="signal",
        clue_place="screen",
        dialogue_prompt="What did the screen show?",
        resolution="The team followed the procedure step by step.",
    ),
    "map_trace_alert": Procedure(
        id="map_trace_alert",
        name="map, trace, and alert",
        steps=["map the path", "trace the signal", "alert the team"],
        clue_kind="digital",
        risk_kind="glitch",
        clue_place="tablet",
        dialogue_prompt="Where did the signal lead?",
        resolution="The heroes traced the mystery to the right room.",
    ),
}

MYSTERIES = {
    "missing_keycard": Mystery(
        id="missing_keycard",
        missing="the mayor's keycard",
        culprit="a sneaky robot",
        clue="a blinking digital trail",
        hidden_where="behind the printer",
        exposed_by="a careful scan",
        label="keycard",
    ),
    "silent_alarm": Mystery(
        id="silent_alarm",
        missing="the alarm code",
        culprit="a scrambled message",
        clue="tiny blue numbers",
        hidden_where="inside the console",
        exposed_by="a calm question",
        label="code",
    ),
    "lost_map": Mystery(
        id="lost_map",
        missing="the rescue map",
        culprit="a loop of static",
        clue="glowing arrows",
        hidden_where="under the chair",
        exposed_by="a screen check",
        label="map",
    ),
}

TOOLS = {
    "scanner": Tool("scanner", "a pocket scanner", helps={"digital"}, solves={"glitch", "signal"}),
    "decoder": Tool("decoder", "a code decoder", helps={"digital"}, solves={"code"}),
    "patchkit": Tool("patchkit", "a repair patch kit", helps={"repair"}, solves={"signal", "glitch"}),
}

HERO_NAMES = ["Nova", "Spark", "Orbit", "Blaze", "Comet", "Aura"]
SIDEKICK_NAMES = ["Milo", "Tess", "Rin", "Pip", "Zuri", "Jax"]
VILLAINS = ["Captain Creak", "Dr. Static", "The Sneak Coil", "Byte Bandit"]
TRAITS = ["brave", "kind", "quick", "curious", "steady"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    procedure: str
    mystery: str
    hero: str
    sidekick: str
    villain: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
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


ASP_RULES = r"""
place(tower).
place(lab).
place(cityhall).

procedure(scan_talk_fix).
procedure(map_trace_alert).

mystery(missing_keycard).
mystery(silent_alarm).
mystery(lost_map).

supports(tower,scan). supports(tower,talk). supports(tower,map).
supports(lab,scan). supports(lab,talk). supports(lab,repair).
supports(cityhall,scan). supports(cityhall,talk). supports(cityhall,procedure).

mystery_kind(missing_keycard,digital).
mystery_kind(silent_alarm,digital).
mystery_kind(lost_map,digital).

procedure_fit(scan_talk_fix,digital).
procedure_fit(map_trace_alert,digital).

valid_story(P,Proc,M) :- place(P), procedure(Proc), mystery(M),
                         mystery_kind(M,digital), procedure_fit(Proc,digital),
                         supports(P,scan), supports(P,talk).
#show valid_story/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
        for s in sorted(_safe_lookup(PLACES, p).supports):
            lines.append(asp.fact("supports", p, s))
    for proc in PROCEDURES.values():
        lines.append(asp.fact("procedure", proc.id))
        lines.append(asp.fact("procedure_fit", proc.id, proc.clue_kind))
    for m in MYSTERIES.values():
        lines.append(asp.fact("mystery", m.id))
        lines.append(asp.fact("mystery_kind", m.id, "digital"))
    return "\n".join(lines)


def asp_program(show: str = "#show valid_story/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    print("only in python:", sorted(py - asp_set))
    print("only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for proc in PROCEDURES:
            for mystery in MYSTERIES:
                if place in {"tower", "lab", "cityhall"} and _safe_lookup(PROCEDURES, proc).clue_kind == "digital":
                    combos.append((place, proc, mystery))
    return combos


def explain_rejection(place: str, proc: str, mystery: str) -> str:
    return (
        f"(No story: the procedure '{proc}' and the mystery '{mystery}' do not make a "
        f"good superhero solve at {place}. Try a digital mystery with a careful step-by-step fix.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------

def seed_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    hero = world.add(Entity(id=params.hero, kind="character", type="hero", traits=[params.trait, "heroic"]))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="friend", traits=["helpful"]))
    villain = world.add(Entity(id=params.villain, kind="character", type="villain", traits=["sneaky"]))
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    tool = TOOLS["scanner" if params.procedure == "scan_talk_fix" else "decoder"]

    clue = world.add(Entity(id="clue", type="thing", label=mystery.clue, phrase=mystery.clue, owner=villain.id))
    missing = world.add(Entity(id="missing", type="thing", label=mystery.label, phrase=mystery.missing, caretaker=hero.id))
    gadget = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.label, owner=hero.id, protective=True, solves=set(tool.solves)))

    hero.memes["curiosity"] = 1
    sidekick.memes["trust"] = 1
    villain.memes["trick"] = 1
    world.facts.update(
        hero=hero, sidekick=sidekick, villain=villain,
        mystery=mystery, tool=gadget, clue=clue, missing=missing,
        procedure=_safe_lookup(PROCEDURES, params.procedure), place=world.place,
        params=params,
    )
    return world


def narrate_setup(world: World) -> None:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sidekick = _safe_fact(world, f, "sidekick")
    villain = _safe_fact(world, f, "villain")
    mystery = _safe_fact(world, f, "mystery")
    world.say(
        f"{hero.id} was a {world.facts['params'].trait} superhero who watched the city with bright eyes."
    )
    world.say(
        f"{sidekick.id} stayed close, because {hero.id} liked solving puzzles with a friend."
    )
    world.say(
        f"One day, {villain.id} caused a mystery: {mystery.missing} was gone, and only {mystery.clue} was left behind."
    )


def narrate_middle(world: World) -> None:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sidekick = _safe_fact(world, f, "sidekick")
    villain = _safe_fact(world, f, "villain")
    mystery = _safe_fact(world, f, "mystery")
    proc = _safe_fact(world, f, "procedure")

    world.para()
    world.say(
        f"{hero.id} and {sidekick.id} hurried to {world.place.name}. "
        f'"Let\'s use the {proc.name} procedure," {hero.id} said.'
    )
    world.say(
        f'"Good idea," {sidekick.id} said. "We should {proc.steps[0]}, then {proc.steps[1]}."'
    )
    world.say(
        f"They found {mystery.clue} near the {mystery.hidden_where}, which looked like a clue on a glowing screen."
    )
    world.say(
        f'"Who could have done this?" {hero.id} asked. "I left a trace," {villain.id} laughed from the shadows.'
    )


def narrate_resolution(world: World) -> None:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sidekick = _safe_fact(world, f, "sidekick")
    villain = _safe_fact(world, f, "villain")
    mystery = _safe_fact(world, f, "mystery")
    proc = _safe_fact(world, f, "procedure")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    missing = _safe_fact(world, f, "missing")

    world.para()
    world.say(
        f'"Step one: scan the digital clue," {hero.id} said, holding up {tool.label}. '
        f'"Step two: ask careful questions."'
    )
    world.say(
        f'"Was the {mystery.label} hidden there?" {sidekick.id} asked.'
    )
    world.say(
        f'"Yes," {villain.id} muttered, "but {mystery.exposed_by} found it right away."'
    )
    world.say(
        f"After the procedure, the team uncovered {missing.phrase} and stopped the trick."
    )
    world.say(
        f"{hero.id} smiled. {sidekick.id} smiled too. The city was safe again, and the screen was quiet."
    )


def generate_world(params: StoryParams) -> World:
    world = seed_world(params)
    narrate_setup(world)
    narrate_middle(world)
    narrate_resolution(world)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    proc = _safe_fact(world, world.facts, "procedure")
    mystery = _safe_fact(world, world.facts, "mystery")
    return [
        f'Write a superhero story about a {p.trait} hero who must solve a digital mystery with dialogue.',
        f'Create a child-friendly mystery story where the heroes follow the "{proc.name}" procedure to find {mystery.missing}.',
        f'Write a bright superhero tale set at {world.place.name} with a clue on a screen and a calm team conversation.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sidekick = _safe_fact(world, f, "sidekick")
    villain = _safe_fact(world, f, "villain")
    mystery = _safe_fact(world, f, "mystery")
    proc = _safe_fact(world, f, "procedure")
    params = _safe_fact(world, f, "params")
    return [
        QAItem(
            question=f"Who solved the mystery in the story?",
            answer=f"{hero.id} solved it with help from {sidekick.id}, using the {proc.name} procedure.",
        ),
        QAItem(
            question=f"What was missing in the story?",
            answer=f"{mystery.missing} was missing, and the clue was {mystery.clue}.",
        ),
        QAItem(
            question=f"Where did the heroes look for clues?",
            answer=f"They looked at {world.place.name}, where the digital clue was hidden near the {mystery.hidden_where}.",
        ),
        QAItem(
            question=f"How did the heroes work together?",
            answer=f"They used dialogue, asked careful questions, and followed the procedure step by step.",
        ),
        QAItem(
            question=f"Why was the villain part of the mystery?",
            answer=f"{villain.id} was the one who caused the trouble, but the team's calm procedure exposed the trick.",
        ),
        QAItem(
            question=f"What kind of story was this?",
            answer=f"It was a superhero mystery story with a digital clue and a procedure for solving it.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does digital mean?",
            answer="Digital means made with numbers or electronic devices like screens, tablets, or computers.",
        ),
        QAItem(
            question="What is a procedure?",
            answer="A procedure is a set of steps that you follow in order to do a job carefully.",
        ),
        QAItem(
            question="Why do superheroes talk to each other when solving mysteries?",
            answer="They talk to share clues, check ideas, and make a smart plan together.",
        ),
    ]


# ---------------------------------------------------------------------------
# Params and CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero digital-procedure mystery storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--procedure", choices=PROCEDURES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--villain")
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
    if getattr(args, "place", None) and getattr(args, "procedure", None) and getattr(args, "mystery", None):
        if (getattr(args, "place", None), getattr(args, "procedure", None), getattr(args, "mystery", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "procedure", None) is None or c[1] == getattr(args, "procedure", None))
              and (getattr(args, "mystery", None) is None or c[2] == getattr(args, "mystery", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, procedure, mystery = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICK_NAMES)
    villain = getattr(args, "villain", None) or rng.choice(VILLAINS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place, procedure, mystery, hero, sidekick, villain, trait)


def generate(params: StoryParams) -> StorySample:
    world = generate_world(params)
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label!r}")
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("\n== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("\n== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
    StoryParams("tower", "scan_talk_fix", "missing_keycard", "Nova", "Milo", "Captain Creak", "brave"),
    StoryParams("lab", "map_trace_alert", "silent_alarm", "Spark", "Tess", "Dr. Static", "curious"),
    StoryParams("cityhall", "scan_talk_fix", "lost_map", "Orbit", "Rin", "Byte Bandit", "steady"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible story combos:")
        for item in stories:
            print(" ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
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
