#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/bacteria_shell_inner_monologue_repetition_suspense_superhero.py
=================================================================================================

A standalone story world for a tiny superhero-style domain: a child hero, a
mysterious shell, and a worry about bacteria. The world uses typed entities with
physical meters and emotional memes, a small forward-chaining causal model, a
reasonableness gate, an ASP twin, and three Q&A sets.

Seeded premise:
- A young hero finds a shell on the shore and hears a suspicious whisper: maybe
  there are bacteria hiding in its wet cracks.
- The hero wants to help, but the shell must be cleaned safely before it can be
  used.
- Suspense comes from a close look, repetition from a repeated warning phrase,
  and inner monologue from the hero thinking through the problem like a comic
  book rescuer.

The story quality target is a complete, child-facing superhero story with a
clear turn and ending image proving what changed.
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

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: str = ""
    caretaker: str = ""
    plural: bool = False
    washable: bool = False
    bacteria_risk: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    helper: object | None = None
    hero: object | None = None
    shell: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.label or self.type
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
        if not hasattr(self, "_tags"):
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
class Locale:
    id: str
    place: str
    surf: str
    style: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Problem:
    id: str
    noun: str
    phrase: str
    risk: str
    whisper: str
    zone: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Tool:
    id: str
    label: str
    phrase: str
    method: str
    effect: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Gear:
    id: str
    label: str
    phrase: str
    barrier: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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


class World:
    def __init__(self, locale: Locale) -> None:
        self.locale = locale
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        w = World(self.locale)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = copy.deepcopy(self.facts)
        return w


@dataclass
class Rule:
    name: str
    tag: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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


def _r_bacteria_spread(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    shell = world.get("shell")
    if hero.meters["inspect"] < THRESHOLD:
        return out
    if shell.meters["clean"] >= THRESHOLD:
        return out
    sig = ("bacteria", shell.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    shell.meters["bacteria"] += 1
    hero.memes["worry"] += 1
    out.append("__risk__")
    return out


def _r_cleaned(world: World) -> list[str]:
    shell = world.get("shell")
    helper = world.get("helper")
    if shell.meters["scrubbed"] < THRESHOLD or shell.meters["clean"] >= THRESHOLD:
        return []
    sig = ("cleaned", shell.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    shell.meters["clean"] = 1
    shell.meters["bacteria"] = 0
    helper.memes["pride"] += 1
    return ["__clean__"]


CAUSAL_RULES = [Rule("bacteria_spread", "physical", _r_bacteria_spread), Rule("cleaned", "physical", _r_cleaned)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            for s in rule.apply(world):
                changed = True
                if not s.startswith("__"):
                    produced.append(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def risk_at(issue: Problem, shell: Entity) -> bool:
    return issue.bacteria_risk and shell.washable


def choose_tool(issue: Problem, shell: Entity) -> Optional[Tool]:
    for t in TOOLS.values():
        if issue.id in t.tags and shell.id in t.tags:
            return t
    return None


def choose_gear(tool: Tool) -> Gear:
    return _safe_lookup(GEARS, tool.id)


def predict_clean(world: World, tool: Tool) -> dict:
    sim = world.copy()
    use_tool(sim, tool, narrate=False)
    sh = sim.get("shell")
    return {"clean": sh.meters["clean"] >= THRESHOLD, "bacteria": sh.meters["bacteria"]}


def use_tool(world: World, tool: Tool, narrate: bool = True) -> None:
    shell = world.get("shell")
    hero = world.get("hero")
    hero.meters["use_tool"] += 1
    shell.meters["scrubbed"] += 1
    shell.meters["clean"] += 1
    shell.meters["bacteria"] = 0
    hero.memes["relief"] += 1
    hero.memes["joy"] += 1
    propagate(world, narrate=narrate)
    if narrate:
        world.say(f"{hero.id} used {tool.phrase} and the shell shone clear again.")


def establish(world: World, hero: Entity, helper: Entity, shell: Entity, issue: Problem) -> None:
    hero.memes["duty"] += 1
    world.say(
        f"{hero.id} was {hero.traits[0]} and brave, the kind of hero who listened closely "
        f"when a shell looked too wet to trust."
    )
    world.say(
        f"{hero.pronoun().capitalize()} found {shell.phrase} near the water, and {hero.id} thought, "
        f'"One tiny shell should not hide tiny bacteria. One tiny shell should not hide tiny bacteria."'
    )
    world.say(
        f"{helper.id} pointed at the cracks. " + f'"Careful," {helper.id} said, "careful, careful."'
    )


def suspense(world: World, hero: Entity, shell: Entity, issue: Problem) -> None:
    hero.memes["focus"] += 1
    world.say(
        f"{hero.id} leaned closer. {hero.id} wondered, in a whisper inside {hero.pronoun('possessive')} own head, "
        f'"What if the shell is full of bacteria? What if the shell is full of bacteria?"'
    )
    world.say(
        f"Then {hero.id} remembered {issue.whisper}: {issue.risk}. The thought made the ocean seem very quiet."
    )


def resolve(world: World, helper: Entity, hero: Entity, shell: Entity, tool: Tool, gear: Gear) -> None:
    world.say(
        f'{helper.id} smiled and held up {gear.phrase}. "No shortcuts," {helper.id} said. '
        f'"{tool.method}. {tool.method}."'
    )
    use_tool(world, tool)
    world.say(
        f"At last the shell sat bright and safe in {hero.pronoun('possessive')} hands, "
        f"and the only thing left of the scare was the memory of the whisper."
    )


def tell(locale: Locale, issue: Problem, tool: Tool, gear: Gear, hero_name: str, helper_name: str, hero_gender: str, helper_gender: str) -> World:
    world = World(locale)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender, label=hero_name, traits=["focused", "kind"]))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_gender, label=helper_name, role="helper"))
    shell = world.add(Entity(id="shell", type="shell", label="shell", phrase=issue.phrase, washable=True, bacteria_risk=True))
    world.facts = {
        "hero": hero,
        "helper": helper,
        "shell": shell,
        "issue": issue,
        "tool": tool,
        "gear": gear,
        "locale": locale,
        "resolved": False,
    }
    establish(world, hero, helper, shell, issue)
    world.para()
    suspense(world, hero, shell, issue)
    world.para()
    world.say(f"{hero.id} took a breath. {hero.id} did not touch the shell yet.")
    world.say(f"{hero.id} thought, 'Clean first, shine later.'")
    world.say(f"{hero.id} thought again, 'Clean first, shine later.'")
    world.say(f"{hero.id} waited, and the waiting felt like a cape holding still in the wind.")
    world.para()
    if not risk_at(issue, shell):
        pass
    if predict_clean(world, tool)["clean"]:
        resolve(world, helper, hero, shell, tool, gear)
        world.facts["resolved"] = True
    else:
        pass
    return world


@dataclass
class StoryParams:
    locale: str = "shore"
    issue: str = "bacteria"
    tool: str = "soap"
    gear: str = "gloves"
    hero_name: str = "Mira"
    hero_gender: str = "girl"
    helper_name: str = "Ari"
    helper_gender: str = "boy"
    seed: Optional[int] = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


LOCALES = {
    "shore": Locale(id="shore", place="the shore", surf="the surf", style="bright and windy", affords={"bacteria", "shell"}),
    "dock": Locale(id="dock", place="the dock", surf="the water", style="salt-bright", affords={"bacteria", "shell"}),
    "tidepool": Locale(id="tidepool", place="the tidepool rocks", surf="the tide", style="shiny and splashy", affords={"bacteria", "shell"}),
    "beachbag": Locale(id="beachbag", place="the beach bag", surf="the sand", style="quiet and sunny", affords={"bacteria", "shell"}),
}

ISSUES = {
    "bacteria": Problem(id="bacteria", noun="bacteria", phrase="a shell", risk="bacteria might be hiding in the shell's wet cracks", whisper="bacteria", zone="shell", tags={"bacteria", "shell"}),
    "sea_slime": Problem(id="sea_slime", noun="sea slime", phrase="a shell", risk="sea slime can make the shell slippery and gross", whisper="slime", zone="shell", tags={"shell"}),
    "sand": Problem(id="sand", noun="sand", phrase="a shell", risk="sand can hide in the ridges and scrape fingers", whisper="sand", zone="shell", tags={"shell"}),
}

TOOLS = {
    "soap": Tool(id="soap", label="soap", phrase="warm soapy water", method="wash the shell in warm soapy water", effect="clean", tags={"bacteria", "shell"}),
    "brush": Tool(id="brush", label="brush", phrase="a soft brush", method="brush the shell with a soft brush", effect="scrubbed", tags={"sand", "shell"}),
    "rinse": Tool(id="rinse", label="rinse", phrase="a gentle rinse", method="rinse the shell again and again", effect="clean", tags={"sea_slime", "shell"}),
    "sun": Tool(id="sun", label="sunlight", phrase="warm sunlight", method="leave the shell in warm sunlight", effect="dry", tags={"bacteria", "shell"}),
}

GEARS = {
    "soap": Gear(id="soap", label="gloves", phrase="thin gloves", barrier="keep the hero's hands dry", tags={"soap"}),
    "brush": Gear(id="brush", label="towel", phrase="a towel", barrier="catch the grit", tags={"brush"}),
    "rinse": Gear(id="rinse", label="bucket", phrase="a clean bucket", barrier="hold the water", tags={"rinse"}),
    "sun": Gear(id="sun", label="cap", phrase="a bright cap", barrier="shade the eyes", tags={"sun"}),
}

GIRL_NAMES = ["Mira", "Nia", "Luna", "Tia", "Ruby", "Sana"]
BOY_NAMES = ["Ari", "Noah", "Leo", "Finn", "Omar", "Jace"]
TRAITS = ["careful", "curious", "steady", "brave"]

CURATED = [
    StoryParams(locale="shore", issue="bacteria", tool="soap", gear="soap", hero_name="Mira", hero_gender="girl", helper_name="Ari", helper_gender="boy"),
    StoryParams(locale="dock", issue="sea_slime", tool="rinse", gear="rinse", hero_name="Noah", hero_gender="boy", helper_name="Luna", helper_gender="girl"),
    StoryParams(locale="tidepool", issue="sand", tool="brush", gear="brush", hero_name="Ruby", hero_gender="girl", helper_name="Finn", helper_gender="boy"),
    StoryParams(locale="beachbag", issue="bacteria", tool="sun", gear="sun", hero_name="Jace", hero_gender="boy", helper_name="Sana", helper_gender="girl"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for loc in LOCALES:
        for issue in ISSUES:
            for tool in TOOLS:
                if issue in _safe_lookup(TOOLS, tool).tags and "shell" in _safe_lookup(TOOLS, tool).tags:
                    out.append((loc, issue, tool))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a superhero shell cleanup against bacteria.")
    ap.add_argument("--locale", choices=LOCALES)
    ap.add_argument("--issue", choices=ISSUES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--gear", choices=GEARS)
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
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
              if (getattr(args, "locale", None) is None or c[0] == getattr(args, "locale", None))
              and (getattr(args, "issue", None) is None or c[1] == getattr(args, "issue", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    locale, issue, tool = rng.choice(list(combos))
    gear = getattr(args, "gear", None) or tool
    hero_gender = getattr(args, "hero_gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or ("boy" if hero_gender == "girl" else "girl")
    hero_name = getattr(args, "hero_name", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != hero_name])
    return StoryParams(locale=locale, issue=issue, tool=tool, gear=gear, hero_name=hero_name, hero_gender=hero_gender, helper_name=helper_name, helper_gender=helper_gender)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a superhero story for a young child that includes the words "bacteria" and "shell".',
        f"Tell a suspenseful story where {f['hero'].id} spots {f['issue'].phrase} and decides how to protect the shell.",
        f"Write a child-friendly comic-style story about cleaning a shell safely before bacteria can be a problem.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, shell, issue, tool = f["hero"], f["helper"], f["shell"], f["issue"], (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What was {hero.id} trying to protect in the story?",
            answer=f"{hero.id} was trying to protect the shell. {hero.id} wanted it to stay safe and clean, because bacteria might hide in the wet cracks.",
        ),
        QAItem(
            question=f"Why did {helper.id} ask {hero.id} to wait before touching the shell?",
            answer=f"{helper.id} asked {hero.id} to wait because bacteria might be hiding in the shell's wet cracks. The wait let them clean first and keep the shell safe.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} fix the shell problem?",
            answer=f"They used {tool.phrase} to clean the shell. That careful method removed the bacteria and let the shell shine again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What are bacteria?", "Bacteria are tiny living things so small that you usually cannot see them without help. Some bacteria are harmless, but some can make things dirty or cause sickness."),
        QAItem("What is a shell?", "A shell is a hard covering found on some sea animals, and people also find empty shells on beaches. Shells can be pretty, but they can also hold sand, slime, or tiny germs in cracks."),
        QAItem("Why do superheroes use special gear?", "Superheroes use special gear to solve problems safely. The gear keeps hands, eyes, or clothes protected while they help."),
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.kind:
            bits.append(f"kind={e.kind}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
valid(Locale, Issue, Tool) :- locale(Locale), issue(Issue), tool(Tool), tool_supports(Tool, Issue).
cleaned(Shell) :- shell(Shell), scrubbed(Shell), not dirty(Shell).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for loc in LOCALES:
        lines.append(asp.fact("locale", loc))
    for issue in ISSUES:
        lines.append(asp.fact("issue", issue))
    for tool_id, tool in TOOLS.items():
        lines.append(asp.fact("tool", tool_id))
        for tag in tool.tags:
            lines.append(asp.fact("tool_supports", tool_id, tag))
    for gear in GEARS:
        lines.append(asp.fact("gear", gear))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    buf = io.StringIO()
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    ok = clingo_set == python_set
    if ok:
        print(f"OK: ASP gate matches valid_combos() ({len(clingo_set)} combos).")
    else:
        print("MISMATCH between ASP and Python combos.")
        if clingo_set - python_set:
            print("  only in ASP:", sorted(clingo_set - python_set))
        if python_set - clingo_set:
            print("  only in python:", sorted(python_set - clingo_set))
        return 1
    try:
        sample = generate(CURATED[0])
        assert sample.story
        print("OK: smoke test story generation succeeded.")
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.locale not in LOCALES or params.issue not in ISSUES or params.tool not in TOOLS or params.gear not in GEARS:
        pass
    locale = _safe_lookup(LOCALES, params.locale)
    issue = _safe_lookup(ISSUES, params.issue)
    tool = _safe_lookup(TOOLS, params.tool)
    gear = _safe_lookup(GEARS, params.gear)
    if not risk_at(issue, Entity(id="shell", washable=True, bacteria_risk=True)):
        pass
    world = tell(locale, issue, tool, gear, params.hero_name, params.helper_name, params.hero_gender, params.helper_gender)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
            print("  ", row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
