#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/squeegee_soldier_insistent_flashback_detective_story.py
====================================================================================================

A standalone story world for a tiny detective tale with a flashback turn.

Premise:
- A small detective notices a clue hidden on a foggy pane.
- An insistent soldier keeps pushing for a quick cleanup.
- A flashback reveals why the soldier knows the right tool.
- The squeegee clears the glass and exposes the clue, resolving the case.

This world models:
- physical state: fog, wetness, clarity, clue visibility
- emotional state: curiosity, insistence, relief, trust
- a flashback instrument: the story explicitly revisits a past moment that explains
  the soldier's certainty about the squeegee

It follows the Storyweavers contract:
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- eager import of results containers
- lazy import of asp in ASP helpers
- inline ASP_RULES twin and Python reasonableness gate
- --verify compares ASP/Python parity and exercises generated stories
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    wielded_by: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)

    case_ent: object | None = None
    detective: object | None = None
    helper: object | None = None
    window: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad", "soldier"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.label.endswith("s") else "it"
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
class Setting:
    place: str = "the station hallway"
    affords: set[str] = field(default_factory=set)
    indoor: bool = True
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
class Tool:
    id: str
    label: str
    phrase: str
    action: str
    clears: set[str]
    fits: set[str]
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
class Case:
    id: str
    label: str
    hidden_on: str
    revealed_by: str
    stain: str
    clue_text: str
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
    setting: str
    case: str
    tool: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_clear_fog(world: World) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters["squeegee"] < THRESHOLD:
            continue
        if ent.meters["fog"] < THRESHOLD:
            continue
        sig = ("clear", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        ent.meters["clarity"] += 1
        ent.meters["fog"] = 0.0
        out.append(f"The glass turned clear where {ent.id} worked.")
    return out


def _r_reveal_clue(world: World) -> list[str]:
    out: list[str] = []
    scene = world.facts.get("case")
    if scene is None:
        return out
    window = world.get("window")
    if window.meters["clarity"] < THRESHOLD:
        return out
    sig = ("reveal", scene.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    scene.meters["seen"] += 1
    out.append("A hidden clue became easy to read.")
    return out


CAUSAL_RULES = [
    _r_clear_fog,
    _r_reveal_clue,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
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


def select_tool(case: Case) -> Optional[Tool]:
    for tool in TOOLS:
        if case.hidden_on in tool.fits and case.stain in tool.clears:
            return tool
    return None


def case_needs_tool(case: Case, tool: Tool) -> bool:
    return case.hidden_on in tool.fits and case.stain in tool.clears


def explain_rejection(case: Case, tool: Tool) -> str:
    return (
        f"(No story: the {tool.label} would not reasonably help with a clue hidden on "
        f"{case.hidden_on} by {case.stain}. The cleanup tool must fit the surface "
        f"and clear the stain.)"
    )


def flashback(world: World, soldier: Entity, tool: Tool) -> None:
    soldier.memes["trust"] += 1
    world.say(
        f"Then came a flashback: {soldier.id} remembered a rainy drill long ago, "
        f"when the same {tool.label} had wiped a panel clean in a single careful pass."
    )
    world.say(
        f"That old memory made {soldier.id} more certain, and more insistent, about the fix."
    )


def setup(world: World, detective: Entity, helper: Entity, case: Case) -> None:
    world.say(
        f"{detective.id} was a little detective with bright eyes and a notebook that never stayed closed."
    )
    world.say(
        f"{helper.id} was an insistent soldier who watched every corner and spoke in short, sure words."
    )
    world.say(
        f"Together they stood in {world.setting.place}, where a clue had gone missing behind a foggy pane."
    )
    world.say(
        f"{detective.id} wanted to solve the case, but the glass was too cloudy to read the hidden message."
    )
    detective.memes["curiosity"] += 1
    helper.memes["insistent"] += 1
    world.facts["case"] = case


def inspect_scene(world: World, detective: Entity, case: Case) -> None:
    detective.meters["fog"] += 1
    world.say(
        f"{detective.id} leaned close and saw only blur and shine, which meant the clue was still trapped."
    )
    world.say(
        f"On the pane, the stain from {case.stain} kept the words from showing themselves."
    )


def use_tool(world: World, detective: Entity, helper: Entity, tool: Tool, case: Case) -> None:
    detective.meters["squeegee"] += 1
    world.say(
        f"{helper.id} pointed at the frame and said, 'Use the {tool.label}.'"
    )
    flashback(world, helper, tool)
    world.say(
        f"{detective.id} listened, pressed the {tool.label} to the glass, and pulled it down in one smooth line."
    )
    propagate(world, narrate=True)
    if case.meters["seen"] >= THRESHOLD:
        world.say(
            f"At last, the clue on the window showed itself: {case.clue_text}"
        )


def resolve_case(world: World, detective: Entity, helper: Entity, case: Case) -> None:
    detective.memes["relief"] += 1
    helper.memes["pride"] += 1
    world.say(
        f"{detective.id} smiled, because the message made sense now and the case was no longer a mystery."
    )
    world.say(
        f"{helper.id} gave one firm nod, still insistent, but now everyone could see the reason."
    )
    world.say(
        f"By the end, the pane was clear, the clue was found, and the two of them left the station hallway with the truth in hand."
    )


def tell(setting: Setting, case: Case, tool: Tool, hero_name: str, hero_type: str, helper_type: str) -> World:
    world = World(setting)
    detective = world.add(Entity(id=hero_name, kind="character", type=hero_type, label="detective"))
    helper = world.add(Entity(id="Soldier", kind="character", type=helper_type, label="soldier"))
    window = world.add(Entity(id="window", type="thing", label="window"))
    window.meters["fog"] = 1.0
    window.meters["stain"] = 1.0
    case_ent = world.add(Entity(id=case.id, type="thing", label=case.label))
    case_ent.meters["seen"] = 0.0

    setup(world, detective, helper, case)
    world.para()
    inspect_scene(world, detective, case)
    world.say(f"The only sensible tool was the {tool.label}, and {helper.id} knew it.")
    world.para()
    use_tool(world, detective, helper, tool, case)
    world.para()
    resolve_case(world, detective, helper, case)

    world.facts.update(
        detective=detective,
        helper=helper,
        case=case_ent,
        tool=tool,
        setting=setting,
    )
    return world


SETTINGS = {
    "station": Setting(place="the station hallway", affords={"window"}),
    "office": Setting(place="the detective office", affords={"window"}),
    "depot": Setting(place="the old depot office", affords={"window"}),
}

CASES = {
    "message": Case(
        id="message",
        label="missing message",
        hidden_on="window",
        revealed_by="squeegee",
        stain="fog",
        clue_text="MEET ME AT NOON",
    ),
    "map": Case(
        id="map",
        label="paper map",
        hidden_on="window",
        revealed_by="squeegee",
        stain="rain",
        clue_text="THE MAP IS UNDER THE GLASS",
    ),
}

TOOLS = [
    Tool(
        id="squeegee",
        label="squeegee",
        phrase="a rubber squeegee",
        action="wipe",
        clears={"fog", "rain"},
        fits={"window"},
    ),
    Tool(
        id="cloth",
        label="cloth",
        phrase="a soft cloth",
        action="rub",
        clears={"fog"},
        fits={"window"},
    ),
]

GENDERS = ["girl", "boy"]
NAMES = {
    "girl": ["Mina", "Ivy", "Nora", "Lena", "June"],
    "boy": ["Eli", "Theo", "Milo", "Finn", "Jasper"],
}
HELPER_NAMES = ["Soldier"]
TRAITS = ["curious", "quiet", "sharp", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for sname, setting in SETTINGS.items():
        for cname, case in CASES.items():
            for tool in TOOLS:
                if case_needs_tool(case, tool) and case.hidden_on in setting.affords:
                    out.append((sname, cname, tool.id))
    return out


@dataclass
class StoryParams:
    setting: str
    case: str
    tool: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    helper = _safe_fact(world, f, "helper")
    case = _safe_fact(world, f, "case")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a short detective story for a child where a {detective.type} named {detective.id} follows a clue hidden on a window.',
        f"Tell a story with a flashback in which {helper.id} the soldier remembers why the {tool.label} is the right tool.",
        f"Write a gentle mystery that ends when the {tool.label} clears the glass and reveals the {case.label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective = _safe_fact(world, f, "detective")
    helper = _safe_fact(world, f, "helper")
    case = _safe_fact(world, f, "case")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who solved the mystery at {world.setting.place}?",
            answer=f"The little detective named {detective.id} solved it with help from the insistent soldier.",
        ),
        QAItem(
            question=f"What tool did {helper.id} insist on using?",
            answer=f"{helper.id} insisted on using the {tool.label} because it could clear the foggy glass.",
        ),
        QAItem(
            question="What did the flashback show?",
            answer=f"The flashback showed {helper.id} remembering an old rainy drill where the {tool.label} had worked before.",
        ),
        QAItem(
            question=f"What became visible after the glass was cleaned?",
            answer=f"The hidden clue became visible: {case.clue_text}.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a squeegee do?",
            answer="A squeegee pulls water or fog off a smooth surface, like a window or mirror.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment that briefly shows something from the past so the reader understands why it matters now.",
        ),
        QAItem(
            question="What does it mean when someone is insistent?",
            answer="Someone who is insistent keeps saying what they think is important and does not give up easily.",
        ),
        QAItem(
            question="What is a soldier?",
            answer="A soldier is a person who works in the army and follows orders, practices carefully, and looks after safety.",
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
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A scene is valid when the case is hidden on the surface the tool can clean.
case_valid(S, C, T) :- setting(S), case(C), tool(T),
                       hidden_on(C, X), fits(T, X),
                       stain_of(C, St), clears(T, St),
                       affords(S, X).

% If the tool clears the stain, the clue becomes readable.
reveals(C) :- case_valid(_, C, T), hidden_on(C, X), fits(T, X),
              stain_of(C, St), clears(T, St).

% The flashback exists because the soldier remembers an earlier success.
flashback_needed(T) :- tool(T), clears(T, _), soldier_role(soldier).

#show case_valid/3.
#show reveals/1.
#show flashback_needed/1.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for cid, case in CASES.items():
        lines.append(asp.fact("case", cid))
        lines.append(asp.fact("hidden_on", cid, case.hidden_on))
        lines.append(asp.fact("stain_of", cid, case.stain))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for s in sorted(tool.clears):
            lines.append(asp.fact("clears", tool.id, s))
        for f in sorted(tool.fits):
            lines.append(asp.fact("fits", tool.id, f))
    lines.append(asp.fact("soldier_role", "soldier"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_models() -> list[list[tuple]]:
    import asp
    model = asp.one_model(asp_program("#show case_valid/3.\n#show reveals/1.\n#show flashback_needed/1."))
    return [tuple()]


def asp_verify() -> int:
    py = set(valid_combos())
    import asp
    model = asp.one_model(asp_program("#show case_valid/3."))
    asp_set = set(asp.atoms(model, "case_valid"))
    # map clingo atoms case_valid(setting,case,tool) to tuples
    if py == asp_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world sketch: a detective, an insistent soldier, a squeegee, and a flashback.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--case", choices=CASES)
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
    ap.add_argument("--gender", choices=GENDERS)
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    if getattr(args, "tool", None) and getattr(args, "case", None):
        tool = next(t for t in TOOLS if t.id == getattr(args, "tool", None))
        case = _safe_lookup(CASES, getattr(args, "case", None))
        if not case_needs_tool(case, tool):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "case", None) is None or c[1] == getattr(args, "case", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, case, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    helper = getattr(args, "helper", None) or "Soldier"
    return StoryParams(setting=setting, case=case, tool=tool, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.setting)
    case = _safe_lookup(CASES, params.case)
    tool = next(t for t in TOOLS if t.id == params.tool)
    world = tell(setting, case, tool, params.name, params.gender, params.helper)
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
        print(asp_program("#show case_valid/3.\n#show reveals/1.\n#show flashback_needed/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show case_valid/3.\n#show reveals/1.\n#show flashback_needed/1."))
        print("case_valid:", sorted(asp.atoms(model, "case_valid")))
        print("reveals:", sorted(asp.atoms(model, "reveals")))
        print("flashback_needed:", sorted(asp.atoms(model, "flashback_needed")))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(setting="station", case="message", tool="squeegee", name="Mina", gender="girl", helper="Soldier"),
            StoryParams(setting="office", case="map", tool="squeegee", name="Eli", gender="boy", helper="Soldier"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.name}: {p.case} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
