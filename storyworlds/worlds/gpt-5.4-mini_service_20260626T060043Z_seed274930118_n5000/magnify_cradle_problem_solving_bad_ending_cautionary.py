#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/magnify_cradle_problem_solving_bad_ending_cautionary.py
===============================================================================================================

A small folk-tale storyworld about a child, a cradle, and a magnifying glass.

Seed image:
A curious child finds an old cradle with a tiny crack in it. With a magnifying
glass, they try to solve the problem by finding the crack and fixing it before
a baby uses the cradle. But the trouble is bigger than it looks: the glass
magnifies the sunlight, the repair goes wrong, and the cradle ends up ruined.
The tale closes as a cautionary lesson about careful tools, patience, and
knowing when a broken thing needs a grown-up's help.

This world intentionally supports a problem-solving shape with a cautionary
bad ending.
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

    child: object | None = None
    cradle: object | None = None
    glass: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.kind == "character" and self.type in {"boy", "man", "father", "grandfather"}:
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
class Setting:
    place: str
    indoors: bool = False
    light: str = "sunny"
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
    kind: str
    use: str
    power: str
    risk: str
    apt: str
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
class Problem:
    id: str
    label: str
    phrase: str
    danger: str
    location: str
    vulnerable: str
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
class StoryParams:
    setting: str
    tool: str
    problem: str
    name: str
    gender: str
    helper: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


def _fixup(world: World) -> list[str]:
    out: list[str] = []
    child = next(e for e in world.entities.values() if e.kind == "character" and e.id == world.facts["child"].id)
    cradle = world.get("cradle")
    if child.meters.get("scratched", 0) >= THRESHOLD and cradle.meters.get("cracked", 0) >= THRESHOLD:
        sig = ("bad_ending",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] = child.memes.get("worry", 0) + 1
            cradle.meters["safe"] = 0
            out.append("__bad_ending__")
    return out


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for sent in _fixup(world):
            if sent:
                changed = True
                if sent != "__bad_ending__":
                    produced.append(sent)
    if narrate:
        for s in produced:
            world.say(s)


SETTINGS = {
    "cottage": Setting(place="the cottage hearth", indoors=True, light="lamplight"),
    "barn": Setting(place="the old barn", indoors=True, light="sunbeams"),
    "garden": Setting(place="the garden gate", indoors=False, light="sunny"),
}

TOOLS = {
    "magnify": Tool(
        id="magnify",
        label="magnifying glass",
        kind="glass",
        use="look closely at the crack",
        power="makes tiny things look larger",
        risk="can focus sunlight into a hot bright spot",
        apt="magnifies",
    ),
    "awl": Tool(
        id="awl",
        label="awl",
        kind="pointed tool",
        use="poke at the broken join",
        power="helps find loose wood",
        risk="can split dry wood",
        apt="pries",
    ),
}

PROBLEMS = {
    "cradle": Problem(
        id="cradle",
        label="cradle",
        phrase="a little wooden cradle with a hairline crack",
        danger="the crack could spread and make the cradle unsafe",
        location="the side rail",
        vulnerable="baby sleep",
    )
}

GIRL_NAMES = ["Mina", "Tara", "Elsa", "Nina", "Ada", "Lina"]
BOY_NAMES = ["Pip", "Tomas", "Ivo", "Marek", "Jory", "Ned"]
TRAITS = ["curious", "careful", "brave", "stubborn", "gentle"]


def folk_opening(hero: Entity, setting: Setting, problem: Problem) -> str:
    return (
        f"Long ago, in a small {setting.place}, there lived a {hero.pronoun('possessive')} "
        f"little helper who noticed {problem.phrase}."
    )


def answerable_setting(setting: Setting) -> str:
    return "inside the cottage" if setting.indoors else "outside in the open air"


def inspect(world: World, child: Entity, tool: Tool, problem: Problem) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0) + 1
    world.say(
        f"{child.id} picked up {tool.label} and tried to {tool.use}; "
        f"{tool.power}, so the crack seemed to grow long as a twig."
    )


def warn(world: World, helper: Entity, child: Entity, tool: Tool, problem: Problem) -> None:
    world.say(
        f"Then {helper.id} warned, \"Take care with that {tool.label}; "
        f"{tool.risk}, and the cradle is already tired.\""
    )


def act(world: World, child: Entity, tool: Tool, problem: Problem) -> None:
    child.memes["determination"] = child.memes.get("determination", 0) + 1
    world.say(
        f"But {child.id} wanted to solve the trouble at once. "
        f"{child.pronoun().capitalize()} leaned closer to the cradle and kept working."
    )


def fail(world: World, child: Entity, tool: Tool, problem: Problem) -> None:
    child.meters["scratched"] = child.meters.get("scratched", 0) + 1
    cradle = world.get("cradle")
    cradle.meters["cracked"] = cradle.meters.get("cracked", 0) + 1
    cradle.meters["safe"] = 0
    world.say(
        f"The bright glass caught the sun, and the hot spot kissed the wood. "
        f"The crack widened instead of mending, and a rough splinter sprang up."
    )


def end_bad(world: World, child: Entity, helper: Entity, problem: Problem) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(
        f"In the end, the {problem.label} could not be saved by hurried hands. "
        f"{helper.id} wrapped the broken cradle in cloth and carried it away, "
        f"while {child.id} sat very still, learning that some repairs need patience and grown-up help."
    )
    world.say(
        f"By dusk, the cradle was no more than splintered boards beside the hearth, "
        f"and the lesson stayed in the room like a quiet shadow."
    )


def tell(setting: Setting, tool: Tool, problem: Problem, hero_name: str, hero_gender: str, helper_kind: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    helper = world.add(Entity(id="helper", kind="character", type=helper_kind))
    cradle = world.add(Entity(id="cradle", kind="thing", type="cradle", label="cradle", phrase=problem.phrase))
    glass = world.add(Entity(id=tool.id, kind="thing", type=tool.kind, label=tool.label, phrase=tool.label))

    world.facts.update(child=child, helper=helper, cradle=cradle, tool=glass, problem=problem, setting=setting)

    world.say(folk_opening(child, setting, problem))
    world.say(
        f"{child.id} was a {trait} little {hero_gender} who loved to solve small troubles by looking closely."
    )
    world.say(
        f"One day, {child.id} found {problem.phrase} waiting by {setting.place}."
    )
    world.para()
    world.say(
        f"{child.id} thought {glass.label} would help, because it {tool.power}."
    )
    inspect(world, child, tool, problem)
    warn(world, helper, child, tool, problem)
    act(world, child, tool, problem)
    fail(world, child, tool, problem)
    propagate(world, narrate=False)
    world.para()
    end_bad(world, child, helper, problem)
    return world


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TOOLS:
            for p in PROBLEMS:
                if t == "magnify" and p == "cradle":
                    combos.append((s, t, p))
                if t == "awl" and p == "cradle":
                    combos.append((s, t, p))
    return combos


def explain_rejection(tool: Tool, problem: Problem) -> str:
    return (
        f"(No story: the chosen tool and problem do not make a believable folk-tale caution. "
        f"Try the magnifying glass with the cradle problem, where close looking can make the trouble worse.)"
    )


@dataclass
class StorySampleWrapper:
    pass
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


KNOWLEDGE = {
    "magnify": [
        QAItem(
            question="What does a magnifying glass do?",
            answer="A magnifying glass makes small things look bigger, so it helps people see tiny cracks, lines, and bugs more clearly."
        ),
        QAItem(
            question="Why can a magnifying glass be dangerous in bright sun?",
            answer="In bright sun, a magnifying glass can gather light into one hot spot, and that spot can burn wood, paper, or leaves."
        ),
    ],
    "cradle": [
        QAItem(
            question="What is a cradle for?",
            answer="A cradle is a little bed for a baby. It rocks gently so a baby can sleep."
        ),
        QAItem(
            question="Why must a cradle be safe?",
            answer="A cradle must be safe because a baby sleeps in it, and broken wood or loose parts can hurt the baby."
        ),
    ],
}


@dataclass
class StoryParamsFull:
    setting: str
    tool: str
    problem: str
    name: str
    gender: str
    helper: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk tale for a young child about "{(f.get("tool") or next(iter(TOOLS.values()))).label}" and a "{f["problem"].label}".',
        f"Tell a cautionary story where {f['child'].id} tries to solve a cradle problem by looking very closely, but the fix goes wrong.",
        f'Write a short story that includes a magnifying glass, a cradle, and a lesson about careful repairs.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    problem = _safe_fact(world, f, "problem")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What did {child.id} try to use to solve the {problem.label} trouble?",
            answer=f"{child.id} tried to use {tool.label} to look closely and fix the {problem.label}.",
        ),
        QAItem(
            question=f"Why did {helper.id} warn {child.id} about {tool.label}?",
            answer=f"{helper.id} warned {child.id} because {tool.risk}, and the {problem.label} was already fragile.",
        ),
        QAItem(
            question=f"What happened when {child.id} kept working on the {problem.label} anyway?",
            answer=f"The bright glass made the problem worse, the wood splintered, and the cradle became unsafe.",
        ),
        QAItem(
            question=f"What lesson did {child.id} learn at the end?",
            answer="The lesson was that some broken things need patience, careful tools, and help from a grown-up.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["magnify"])
    out.extend(KNOWLEDGE["cradle"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.kind}/{e.type} {' '.join(parts)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld about a magnifying glass and a cradle.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParamsFull:
    combos = valid_combos()
    if getattr(args, "tool", None) and getattr(args, "problem", None) and (getattr(args, "tool", None), getattr(args, "problem", None)) not in {(t, p) for _, t, p in combos}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos2 = [c for c in combos if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None)) and (getattr(args, "tool", None) is None or c[1] == getattr(args, "tool", None)) and (getattr(args, "problem", None) is None or c[2] == getattr(args, "problem", None))]
    if not combos2:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, tool, problem = rng.choice(sorted(combos2))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(list({"mother", "father", "grandmother", "grandfather"}))
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParamsFull(setting=setting, tool=tool, problem=problem, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParamsFull) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(TOOLS, params.tool), _safe_lookup(PROBLEMS, params.problem), params.name, params.gender, params.helper, params.trait)
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


ASP_RULES = r"""
tool(magnify).
tool(awl).
problem(cradle).
setting(cottage).
setting(barn).
setting(garden).

compatible(S, magnify, cradle) :- setting(S).
compatible(S, awl, cradle) :- setting(S).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    clingo_set = set(asp.atoms(model, "compatible"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in clingo:", sorted(clingo_set - python_set))
    print("only in python:", sorted(python_set - clingo_set))
    return 1


CURATED = [
    StoryParamsFull(setting="cottage", tool="magnify", problem="cradle", name="Mina", gender="girl", helper="grandmother", trait="curious"),
    StoryParamsFull(setting="barn", tool="magnify", problem="cradle", name="Pip", gender="boy", helper="father", trait="careful"),
    StoryParamsFull(setting="garden", tool="magnify", problem="cradle", name="Tara", gender="girl", helper="mother", trait="stubborn"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show compatible/3."))
        combos = sorted(set(asp.atoms(model, "compatible")))
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
