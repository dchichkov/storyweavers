#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/funnel_conservative_kindness_humor_foreshadowing_fairy_tale.py
====================================================================================================

A fairy-tale story world about a careful child, a conservative guardian, a
small spill risk, and a kindly compromise involving a funnel.

The seed image:
---
A little apprentice in a cozy kingdom wants to pour golden syrup into tiny jars.
The guardian worries because the jars have narrow mouths and the syrup is sticky.
The child notices a bright funnel, makes a joke about "feeding the jars," and
the guardian agrees that being careful is wiser than being stubborn. They use
the funnel, pour without a mess, and the finished jars gleam like treasure.

This world models:
- physical meters: spill, stickiness, worry, neatness, delight
- emotional memes: caution, kindness, humor, trust, pride

It supports:
- story generation
- Q&A
- JSON
- trace
- ASP parity verification
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    guardian: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "mother", "woman", "princess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "father", "man", "prince"}:
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
class Setting:
    place: str
    indoors: bool
    narrow_mouths: bool = True
    cozy: bool = True
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
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    risk: str
    consequence: str
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
class Prize:
    id: str
    label: str
    phrase: str
    type: str
    mouth: str
    plural: bool = False
    tags: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    fits: set[str]
    prep: str
    finish: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


TASKS = {
    "syrup": Task(
        id="syrup",
        verb="pour the golden syrup into the little jars",
        gerund="pouring golden syrup into little jars",
        rush="rush to pour the syrup",
        risk="it could spill over the rims",
        consequence="the table would get sticky",
        tags={"syrup", "sticky", "pour"},
    ),
    "milk": Task(
        id="milk",
        verb="pour the milk into the cups",
        gerund="pouring milk into cups",
        rush="tip the jug too quickly",
        risk="it could splash the cups",
        consequence="the cloth would get damp",
        tags={"milk", "spill", "pour"},
    ),
    "glitter": Task(
        id="glitter",
        verb="shake glitter into the little pouch",
        gerund="shaking glitter into the pouch",
        rush="shake the jar hard",
        risk="it could puff everywhere",
        consequence="the room would sparkle too much",
        tags={"glitter", "mess"},
    ),
}

PRIZES = {
    "jars": Prize(
        id="jars",
        label="jars",
        phrase="tiny glass jars",
        type="jars",
        mouth="narrow",
        plural=True,
        tags={"jar", "glass"},
    ),
    "cups": Prize(
        id="cups",
        label="cups",
        phrase="small cups",
        type="cups",
        mouth="wide",
        plural=True,
        tags={"cup"},
    ),
    "pouch": Prize(
        id="pouch",
        label="pouch",
        phrase="a little cloth pouch",
        type="pouch",
        mouth="narrow",
        plural=False,
        tags={"pouch"},
    ),
}

TOOLS = [
    Tool(
        id="funnel",
        label="a bright funnel",
        phrase="a bright little funnel",
        helps={"syrup", "milk", "glitter"},
        fits={"narrow"},
        prep="set the funnel in the jar mouths first",
        finish="lifted the funnel away and saw every drop had gone where it should",
    ),
    Tool(
        id="ladle",
        label="a ladle",
        phrase="a small wooden ladle",
        helps={"milk"},
        fits={"wide"},
        prep="use a ladle for the cups",
        finish="set the ladle aside and smiled at the neat little cups",
    ),
]

SETTINGS = {
    "kitchen": Setting(place="the castle kitchen", indoors=True, narrow_mouths=True),
    "pantry": Setting(place="the pantry", indoors=True, narrow_mouths=True),
    "garden": Setting(place="the herb garden", indoors=False, narrow_mouths=False),
}

NAMES = {
    "girl": ["Mira", "Elsa", "Lina", "Nia", "Tessa"],
    "boy": ["Rowan", "Finn", "Otto", "Pippin", "Galen"],
}

TRAITS = ["gentle", "curious", "cheerful", "brave", "quiet"]


def need_funnel(task: Task, prize: Prize) -> bool:
    return task.id in {"syrup", "glitter"} and prize.mouth == "narrow"


def choose_tool(task: Task, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if task.id in tool.helps and prize.mouth in tool.fits:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TASKS:
            for p in PRIZES:
                task = _safe_lookup(TASKS, t)
                prize = _safe_lookup(PRIZES, p)
                if need_funnel(task, prize) and choose_tool(task, prize):
                    combos.append((s, t, p))
    return combos


def _do_task(world: World, actor: Entity, task: Task, prize: Prize, tool: Optional[Tool], narrate: bool = True) -> None:
    if tool is None:
        actor.meters["spill"] += 1
        actor.meters["mess"] += 1
        prize.meters["mess"] += 1
        if narrate:
            world.say(f"When {actor.id} tried to {task.verb}, the {task.risk}; {task.consequence}.")
        return

    actor.meters["neatness"] += 1
    actor.memes["trust"] += 1
    prize.meters["clean"] += 1
    if narrate:
        world.say(f"{actor.id} used {tool.label} and {tool.prep}, so {task.verb} went smoothly.")


def foresee(world: World, actor: Entity, task: Task, prize: Prize) -> bool:
    sim = world.copy()
    _do_task(sim, sim.get(actor.id), task, prize, None, narrate=False)
    return sim.entities[prize.id].meters.get("mess", 0) >= THRESHOLD


def setup(world: World, hero: Entity, guardian: Entity, prize: Entity, task: Task) -> None:
    hero.memes["kindness"] += 1
    world.say(
        f"In {world.setting.place}, {hero.id} was a {hero.pronoun('subject')} little {hero.type} who loved careful work."
    )
    world.say(
        f"{hero.pronoun('subject').capitalize()} wanted to {task.verb}, and {guardian.id} kept a watchful eye on the {prize.label}."
    )


def foreshadow(world: World, hero: Entity, guardian: Entity, task: Task, prize: Entity) -> bool:
    if not foresee(world, hero, task, prize):
        return False
    guardian.memes["caution"] += 1
    world.facts["risk_line"] = f"{prize.phrase} could get messy"
    world.say(
        f"{guardian.id} peered at the {prize.label} and said, \"Careful now; {task.risk}.\""
    )
    return True


def humor(world: World, hero: Entity, task: Task) -> None:
    hero.memes["humor"] += 1
    world.say(
        f"{hero.id} grinned and said the jars were so tiny they looked hungry for supper."
    )
    world.say(
        f"That made {hero.id}'s {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "guardian").label} chuckle despite the worried look."
    )


def kindness_turn(world: World, hero: Entity, guardian: Entity, task: Task, prize: Entity) -> Optional[Tool]:
    tool = choose_tool(task, prize)
    if tool is None:
        return None
    if not need_funnel(task, prize):
        return tool
    world.say(
        f"{hero.id} held up {tool.label} and said, \"We can be kind to the jars and pour slowly.\""
    )
    guardian.memes["kindness"] += 1
    guardian.memes["trust"] += 1
    return tool


def resolution(world: World, hero: Entity, guardian: Entity, task: Task, prize: Entity, tool: Tool) -> None:
    _do_task(world, hero, task, prize, tool, narrate=True)
    world.say(
        f"Then {tool.finish}, and {prize.phrase} stayed clean and shining."
    )
    hero.memes["pride"] += 1
    guardian.memes["relief"] += 1
    world.say(
        f"{guardian.id} smiled because careful hands had saved the day, and {hero.id} was proud of the neat result."
    )


def tell(
    setting: Setting,
    task: Task,
    prize_cfg: Prize,
    hero_name: str = "Mira",
    hero_type: str = "girl",
    guardian_type: str = "queen",
    trait: str = "gentle",
) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    guardian = world.add(Entity(id="Guardian", kind="character", type=guardian_type, label="the guardian"))
    prize = world.add(Entity(id=prize_cfg.id, type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase))
    world.facts.update(hero=hero, guardian=guardian, prize=prize, task=task, setting=setting, trait=trait)

    setup(world, hero, guardian, prize, task)
    world.para()
    foreshadow(world, hero, guardian, task, prize)
    humor(world, hero, task)
    world.para()
    tool = kindness_turn(world, hero, guardian, task, prize)
    if tool is None:
        _fallback_pool = globals().get("TOOLS") or globals().get("TOOLES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        tool = next(iter(_fallback_pool), None)
        if tool is None:
            raise StoryError
    resolution(world, hero, guardian, task, prize, tool)
    world.facts["tool"] = tool
    return world


@dataclass
class StoryParams:
    setting: str
    task: str
    prize: str
    name: str
    gender: str
    guardian: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fairy tale about {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id}, a child who wants to {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "task").verb}, and a cautious guardian.',
        f"Tell a gentle story where a {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").type} named {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} uses a funnel to keep {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize").phrase} clean.",
        f"Create a short fairy tale with kindness, humor, and foreshadowing about careful pouring in {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting").place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    guardian = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "guardian")
    prize = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "prize")
    task = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "task")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What did {hero.id} want to do in the castle story?",
            answer=f"{hero.id} wanted to {task.verb}.",
        ),
        QAItem(
            question=f"Why did {guardian.id} worry about the {prize.label}?",
            answer=f"{guardian.id} worried because {task.risk}, so {prize.phrase} might get messy.",
        ),
        QAItem(
            question=f"What tool helped {hero.id} do the job carefully?",
            answer=f"{tool.label} helped because it guided the flow into the narrow opening.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {prize.phrase} staying clean and {hero.id} feeling proud of the careful pouring.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a funnel do?",
            answer="A funnel helps liquid or tiny bits go into a small opening without spilling everywhere.",
        ),
        QAItem(
            question="Why is it wise to be careful with sticky syrup?",
            answer="Sticky syrup can drip and make a mess, so careful pouring keeps the table clean.",
        ),
        QAItem(
            question="What is a conservative choice in a careful task?",
            answer="A conservative choice is the safer, more careful choice that avoids waste or mess.",
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


CURATED = [
    StoryParams(setting="kitchen", task="syrup", prize="jars", name="Mira", gender="girl", guardian="queen", trait="gentle"),
    StoryParams(setting="pantry", task="syrup", prize="jars", name="Rowan", gender="boy", guardian="king", trait="curious"),
    StoryParams(setting="kitchen", task="milk", prize="cups", name="Nia", gender="girl", guardian="mother", trait="cheerful"),
]


def valid_gender(gender: str, prize_id: str) -> bool:
    return True


def explain_rejection(task: Task, prize: Prize) -> str:
    return (
        f"(No story: {task.gerund} and {prize.phrase} do not make a meaningful dilemma here. "
        f"Try the narrow {prize.mouth} prize with a task that can spill.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "setting", None):
        combos = [c for c in combos if c[0] == getattr(args, "setting", None)]
    if getattr(args, "task", None):
        combos = [c for c in combos if c[1] == getattr(args, "task", None)]
    if getattr(args, "prize", None):
        combos = [c for c in combos if c[2] == getattr(args, "prize", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting, task, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    guardian = getattr(args, "guardian", None) or rng.choice(["queen", "king", "mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, task=task, prize=prize, name=name, gender=gender, guardian=guardian, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(TASKS, params.task),
        _safe_lookup(PRIZES, params.prize),
        hero_name=params.name,
        hero_type=params.gender,
        guardian_type=params.guardian,
        trait=params.trait,
    )
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale story world about a funnel, carefulness, and a kind compromise.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["queen", "king", "mother", "father"])
    ap.add_argument("--name")
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


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("task_tag", tid, tag))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("mouth", pid, p.mouth))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for h in sorted(tool.helps):
            lines.append(asp.fact("helps", tool.id, h))
        for f in sorted(tool.fits):
            lines.append(asp.fact("fits", tool.id, f))
    return "\n".join(lines)


ASP_RULES = r"""
need_funnel(T,P) :- task(T), prize(P), mouth(P,narrow), task_tag(T,syrup).
need_funnel(T,P) :- task(T), prize(P), mouth(P,narrow), task_tag(T,glitter).
compatible(T,P,Tool) :- need_funnel(T,P), tool(Tool), helps(Tool,T), fits(Tool,narrow).
valid(S,T,P) :- setting(S), task(T), prize(P), compatible(T,P,_).
#show valid/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.task} in {p.setting} with {p.prize}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
