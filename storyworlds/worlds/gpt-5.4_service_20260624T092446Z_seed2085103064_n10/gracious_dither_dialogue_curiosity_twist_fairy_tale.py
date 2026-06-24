#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    aid: object | None = None
    fairy: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "queen", "fairy"}
        male = {"boy", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
    id: str
    place: str
    affords: set[str] = field(default_factory=set)
    detail: str = ""
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
class Problem:
    id: str
    need: str
    label: str
    symptom: str
    ask: str
    solved_by: str
    result: str
    tags: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    aids: set[str] = field(default_factory=set)
    action: str = ""
    ending: str = ""
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


@dataclass
class Disguise:
    id: str
    label: str
    phrase: str
    move: str
    reveal: str
    voice: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        clone.paragraphs = [[]]
        return clone


def _r_use_tool(world: World) -> list[str]:
    out: list[str] = []
    problem: Problem = _safe_fact(world, world.facts, "problem")
    tool: Tool = _safe_fact(world, world.facts, "tool")
    fairy = world.get("fairy")
    if fairy.meters["need"] < THRESHOLD:
        return out
    if problem.need not in tool.aids:
        return out
    sig = ("solve", problem.id, tool.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    fairy.meters["need"] = 0.0
    fairy.memes["relief"] += 1
    world.setting_detail_glow = 1
    out.append(problem.result)
    return out


def _r_kindness_blooms(world: World) -> list[str]:
    hero = world.get("hero")
    fairy = world.get("fairy")
    if hero.memes["curiosity"] < THRESHOLD or hero.memes["trust"] < THRESHOLD:
        return []
    if fairy.memes["relief"] < THRESHOLD:
        return []
    sig = ("gratitude",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    fairy.memes["gratitude"] += 1
    return ["The little stranger's eyes shone with grateful light."]


def _r_reveal(world: World) -> list[str]:
    fairy = world.get("fairy")
    if fairy.memes["gratitude"] < THRESHOLD:
        return []
    sig = ("reveal",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    fairy.memes["revealed"] += 1
    return ["__reveal__"]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_use_tool, _r_kindness_blooms, _r_reveal):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            if s != "__reveal__":
                world.say(s)
    return produced


SETTINGS = {
    "brook": Setting(
        id="brook",
        place="the willow brook",
        affords={"float"},
        detail="Silver fish flicked beneath the water, and the reeds whispered at the edge.",
    ),
    "grove": Setting(
        id="grove",
        place="the moonlit grove",
        affords={"light"},
        detail="Tall trees held their leaves like green curtains, and the path grew dim beneath them.",
    ),
    "rosepath": Setting(
        id="rosepath",
        place="the rose path",
        affords={"cut"},
        detail="Hedges of roses leaned over the lane, sweet-smelling and full of thorns.",
    ),
    "oakyard": Setting(
        id="oakyard",
        place="the old oak yard",
        affords={"reach"},
        detail="An ancient oak spread its branches wide, as if it had been listening for a hundred years.",
    ),
}

PROBLEMS = {
    "satchel": Problem(
        id="satchel",
        need="float",
        label="a tiny satchel",
        symptom="a tiny satchel sat on one bank while the speaker waited on the other",
        ask="Would you help my satchel cross the brook?",
        solved_by="float",
        result="The satchel drifted safely across the brook instead of getting swallowed by the water.",
        tags={"brook", "water"},
    ),
    "lantern": Problem(
        id="lantern",
        need="light",
        label="a pearl lantern",
        symptom="a pearl lantern had gone dark under the trees",
        ask="Would you help me light my lantern again?",
        solved_by="light",
        result="The lantern woke with a soft gold glow, and the dark path opened like a kind smile.",
        tags={"light", "dark"},
    ),
    "cloak": Problem(
        id="cloak",
        need="cut",
        label="a silver cloak",
        symptom="a silver cloak was snared in thorny rose briars",
        ask="Would you help me free my cloak from these briars?",
        solved_by="cut",
        result="The briars let go at last, and the silver cloak slipped free without tearing.",
        tags={"thorn", "rose"},
    ),
    "key": Problem(
        id="key",
        need="reach",
        label="a small gold key",
        symptom="a small gold key hung high in an oak branch",
        ask="Would you help me reach my key?",
        solved_by="reach",
        result="The gold key came down from the high branch and rang like a tiny bell in the hero's hand.",
        tags={"tree", "key"},
    ),
}

TOOLS = {
    "leafboat": Tool(
        id="leafboat",
        label="a leaf boat",
        phrase="a neat leaf boat folded from a broad green leaf",
        aids={"float"},
        action="set the satchel inside the leaf boat and nudged it onto the water",
        ending="a leaf boat bobbed beside the bank",
        tags={"boat", "water"},
    ),
    "fireflylamp": Tool(
        id="fireflylamp",
        label="a firefly lamp",
        phrase="a little lamp where kind fireflies blinked behind clear glass",
        aids={"light"},
        action="held up the firefly lamp until its warm gleam kissed the dark lantern",
        ending="the firefly lamp winked among the ferns",
        tags={"lamp", "light"},
    ),
    "goldenshears": Tool(
        id="goldenshears",
        label="golden shears",
        phrase="a pair of golden shears with handles shaped like curling vines",
        aids={"cut"},
        action="snipped the thorny stems one by one with the golden shears",
        ending="the golden shears rested shut and shining",
        tags={"shears", "thorn"},
    ),
    "ashladder": Tool(
        id="ashladder",
        label="an ash ladder",
        phrase="an ash ladder with smooth rungs worn pale by many feet",
        aids={"reach"},
        action="leaned the ash ladder against the oak and climbed carefully",
        ending="the ash ladder stood by the trunk",
        tags={"ladder", "tree"},
    ),
}

DISGUISES = {
    "toad": Disguise(
        id="toad",
        label="a toad",
        phrase="a round-eyed toad in a velvet cap",
        move="blinked from a flat stone",
        reveal="a bright little fairy in a dew-silver gown",
        voice="a gracious voice no bigger than a spoon",
        tags={"toad", "fairy"},
    ),
    "cat": Disguise(
        id="cat",
        label="a cat",
        phrase="a soot-gray cat with a bell on its collar",
        move="sat with its tail tucked neatly around its paws",
        reveal="a bright little fairy in a moon-pale cloak",
        voice="a gracious purring voice",
        tags={"cat", "fairy"},
    ),
    "crow": Disguise(
        id="crow",
        label="a crow",
        phrase="a black crow with a single white feather",
        move="hopped along the path and bowed its head",
        reveal="a bright little fairy with feather-light sleeves",
        voice="a gracious crackling voice",
        tags={"crow", "fairy"},
    ),
    "mouse": Disguise(
        id="mouse",
        label="a mouse",
        phrase="a field mouse in a stitched red hood",
        move="peeped from beneath a fern",
        reveal="a bright little fairy with rose-petal slippers",
        voice="a gracious whispering voice",
        tags={"mouse", "fairy"},
    ),
}

GIRL_NAMES = ["Lina", "Mira", "Tessa", "Nora", "Elin", "Wren"]
BOY_NAMES = ["Oren", "Tobin", "Milo", "Perrin", "Rowan", "Finn"]
TRAITS = ["curious", "gentle", "careful", "bright-eyed", "thoughtful", "kind"]


def tool_for_problem(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS.values():
        if problem.need in tool.aids:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for prob_id, problem in PROBLEMS.items():
            if problem.need not in setting.affords:
                continue
            tool = tool_for_problem(problem)
            if tool is not None:
                out.append((place, prob_id, tool.id))
    return sorted(out)


def explain_rejection(setting: Setting, problem: Problem, tool: Optional[Tool]) -> str:
    if problem.need not in setting.affords:
        return (
            f"(No story: {setting.place} does not suit {problem.label}. "
            f"That place cannot honestly host a problem that needs {problem.need}.)"
        )
    if tool is None or problem.need not in tool.aids:
        return (
            f"(No story: {tool.label if tool else 'that tool'} would not solve {problem.label}. "
            f"The helping gift must truly fix the trouble.)"
        )
    return "(No story: the choices do not make a reasonable fairy-tale problem.)"


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    disguise: str
    name: str
    gender: str
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


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    world.say(
        f"Once, in a small valley where stories liked to wander, there lived a little {trait} "
        f"{hero.type} named {hero.id}."
    )
    hero.memes["curiosity"] += 1
    world.say(
        f"{hero.id} was the sort of child who noticed bright beetles, crooked doors in tree roots, "
        f"and every secret sound the wind carried."
    )


def arrive(world: World, hero: Entity) -> None:
    world.say(f"One morning, {hero.id} walked to {world.setting.place}.")
    world.say(world.setting.detail)


def encounter(world: World, hero: Entity, fairy: Entity, disguise: Disguise, problem: Problem) -> None:
    fairy.meters["need"] += 1
    world.say(
        f"There {hero.id} saw {disguise.phrase}. It {disguise.move}, and beside it {problem.symptom}."
    )
    world.say(
        f'"Good day," said {disguise.voice}. "I hope I am not troubling you. {problem.ask}"'
    )


def dither(world: World, hero: Entity, disguise: Disguise) -> None:
    hero.memes["caution"] += 1
    hero.memes["dither"] += 1
    world.say(
        f"{hero.id} stopped. A talking {disguise.label} was not an everyday thing, and for a moment "
        f"{hero.pronoun()} did dither."
    )


def ask_questions(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["curiosity"] += 1
    world.say(
        f'"Why do you need help?" {hero.id} asked. "{problem.label.capitalize()} seems very important."'
    )
    world.say(
        f'The small stranger answered politely, "It is, and I would be thankful for any kind help."'
    )


def choose_help(world: World, hero: Entity, tool: Tool) -> None:
    hero.memes["trust"] += 1
    world.say(
        f"{hero.id} looked into {hero.pronoun('possessive')} basket and found {tool.phrase}."
    )
    world.say(
        f'"I think this may help," {hero.pronoun()} said in a gracious voice.'
    )


def solve_problem(world: World, hero: Entity, tool: Tool) -> None:
    world.say(f"{hero.id} {tool.action}.")
    propagate(world, narrate=True)


def reveal_twist(world: World, disguise: Disguise) -> None:
    fairy = world.get("fairy")
    if fairy.memes["revealed"] < THRESHOLD:
        return
    world.say(
        f"Then came the twist: a ring of light circled the little stranger, and the {disguise.label} "
        f"was gone. In its place stood {disguise.reveal}."
    )


def blessing(world: World, hero: Entity, tool: Tool) -> None:
    fairy = world.get("fairy")
    hero.memes["joy"] += 1
    fairy.memes["fondness"] += 1
    world.say(
        f'"Your curious heart looked twice before it judged once," the fairy said. '
        f'"That is a rare and gracious kind of wisdom."'
    )
    world.say(
        f'The fairy touched the air with one shining finger, and all at once {world.setting.place} '
        f'grew warmer and brighter.'
    )
    world.say(
        f"When {hero.id} walked home, {tool.ending}, a gold sparkle trailed through the leaves, "
        f"and {hero.pronoun('possessive')} smile stayed bright all the way to the cottage door."
    )


def tell(
    setting: Setting,
    problem: Problem,
    tool: Tool,
    disguise: Disguise,
    hero_name: str,
    hero_type: str,
    trait: str,
) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=hero_name, traits=["little", trait]))
    fairy = world.add(Entity(id="fairy", kind="character", type="fairy", label="the stranger"))
    aid = world.add(Entity(id="tool", kind="thing", type="tool", label=tool.label, phrase=tool.phrase, owner=hero.id))

    introduce(world, hero)
    world.para()
    arrive(world, hero)
    encounter(world, hero, fairy, disguise, problem)
    dither(world, hero, disguise)
    ask_questions(world, hero, problem)
    world.para()
    choose_help(world, hero, tool)
    solve_problem(world, hero, tool)
    reveal_twist(world, disguise)
    blessing(world, hero, tool)

    world.facts.update(
        hero=hero,
        fairy=fairy,
        tool=tool,
        problem=problem,
        disguise=disguise,
        setting=setting,
        solved=fairy.meters["need"] < THRESHOLD,
        revealed=fairy.memes["revealed"] >= THRESHOLD,
        hero_name=hero_name,
    )
    return world


KNOWLEDGE = {
    "water": [
        (
            "Why can a small boat help something cross a brook?",
            "A small boat floats on top of the water, so it can carry a little thing across without letting it sink."
        )
    ],
    "light": [
        (
            "Why does a lantern help in a dark place?",
            "A lantern makes light, so it helps people see the path, roots, and stones around them."
        )
    ],
    "thorn": [
        (
            "Why are thorns tricky?",
            "Thorns are sharp parts of some plants. They can catch cloth and scratch skin if you are not careful."
        )
    ],
    "tree": [
        (
            "Why is a ladder useful for a high branch?",
            "A ladder gives you safe steps to climb, so you can reach something that is above your head."
        )
    ],
    "fairy": [
        (
            "What is a fairy in a fairy tale?",
            "A fairy is a tiny magical person who may hide in an ordinary shape and use magic to help or test others."
        )
    ],
    "boat": [
        (
            "What is a leaf boat?",
            "A leaf boat is a make-believe tiny boat made from a leaf. In stories, it can carry very small things on water."
        )
    ],
    "lamp": [
        (
            "What are fireflies?",
            "Fireflies are little insects that glow. Their bodies make a soft light that shines in the dark."
        )
    ],
    "shears": [
        (
            "What are shears?",
            "Shears are strong scissors used for cutting things like stems, cloth, or wool."
        )
    ],
    "ladder": [
        (
            "What does a ladder do?",
            "A ladder helps you go up and down safely because it has rungs to step on."
        )
    ],
}
KNOWLEDGE_ORDER = ["water", "light", "thorn", "tree", "boat", "lamp", "shears", "ladder", "fairy"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    problem = _safe_fact(world, f, "problem")
    disguise = _safe_fact(world, f, "disguise")
    setting = _safe_fact(world, f, "setting")
    return [
        f'Write a short fairy-tale story for a young child about a curious {hero.type} who meets {disguise.phrase} at {setting.place}.',
        f"Tell a gentle story with dialogue where a child first dithers, then helps solve the problem of {problem.label}.",
        f'Write a fairy tale with a twist: a gracious talking {disguise.label} asks for help, and the ending reveals a fairy.'
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    problem = _safe_fact(world, f, "problem")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    disguise = _safe_fact(world, f, "disguise")
    setting = _safe_fact(world, f, "setting")
    hero_name = _safe_fact(world, f, "hero_name")
    trait = next((t for t in hero.traits if t != "little"), hero.type)
    qa = [
        QAItem(
            question=f"Who is the story about in {setting.place}?",
            answer=f"The story is about a little {trait} {hero.type} named {hero_name}, who walks into {setting.place} and finds a strange new mystery there.",
        ),
        QAItem(
            question=f"What made {hero_name} stop and listen?",
            answer=f"{hero_name} saw {disguise.phrase} and heard it speak in a gracious voice. That surprise made {hero_name} stop and pay close attention.",
        ),
        QAItem(
            question=f"Why did {hero_name} dither at first?",
            answer=f"{hero_name} dithered because talking animals are unusual, and it felt wise to be careful before trusting a stranger. Curiosity still pulled {hero.pronoun('object')} closer, so {hero.pronoun()} asked questions instead of running away.",
        ),
        QAItem(
            question=f"What trouble needed to be fixed?",
            answer=f"The trouble was that {problem.symptom}. The little stranger asked for help because it could not solve that problem alone.",
        ),
        QAItem(
            question=f"How did {tool.label} help?",
            answer=f"{tool.label.capitalize()} helped because it matched the problem exactly. {hero_name} used it to fix the trouble, and that changed the whole moment from worry into relief.",
        ),
    ]
    if f["revealed"]:
        qa.append(
            QAItem(
                question="What was the twist at the end?",
                answer=f"The twist was that the talking {disguise.label} was not only an ordinary creature. After the problem was solved, it changed into {disguise.reveal}, so the stranger had been a fairy all along.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["problem"].tags) | set(world.facts["tool"].tags) | set(world.facts["disguise"].tags)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
problem_at_place(P,L) :- problem(P), need(P,N), affords(L,N).
tool_fits(T,P) :- tool(T), helps(T,N), need(P,N).
valid(L,P,T) :- place(L), problem_at_place(P,L), tool_fits(T,P).
valid_story(L,P,T,D) :- valid(L,P,T), disguise(D).

#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        for need in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, need))
    for pid, problem in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("need", pid, problem.need))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for need in sorted(tool.aids):
            lines.append(asp.fact("helps", tid, need))
    for did in DISGUISES:
        lines.append(asp.fact("disguise", did))
    return "\n".join(lines)


def asp_program(show: str = "#show valid/3.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


CURATED = [
    StoryParams(place="brook", problem="satchel", tool="leafboat", disguise="mouse", name="Lina", gender="girl", trait="curious"),
    StoryParams(place="grove", problem="lantern", tool="fireflylamp", disguise="cat", name="Milo", gender="boy", trait="careful"),
    StoryParams(place="rosepath", problem="cloak", tool="goldenshears", disguise="crow", name="Tessa", gender="girl", trait="gentle"),
    StoryParams(place="oakyard", problem="key", tool="ashladder", disguise="toad", name="Rowan", gender="boy", trait="thoughtful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld of curiosity, dialogue, and a gracious twist.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--disguise", choices=DISGUISES)
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "place", None) and getattr(args, "problem", None) and getattr(args, "tool", None):
        setting = _safe_lookup(SETTINGS, getattr(args, "place", None))
        problem = _safe_lookup(PROBLEMS, getattr(args, "problem", None))
        tool = _safe_lookup(TOOLS, getattr(args, "tool", None))
        if problem.need not in setting.affords or problem.need not in tool.aids:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
        and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, problem, tool = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    disguise = getattr(args, "disguise", None) or rng.choice(sorted(DISGUISES))
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place,
        problem=problem,
        tool=tool,
        disguise=disguise,
        name=name,
        gender=gender,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(PROBLEMS, params.problem),
        _safe_lookup(TOOLS, params.tool),
        _safe_lookup(DISGUISES, params.disguise),
        hero_name=params.name,
        hero_type=params.gender,
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


def verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py != asp_set:
        print("MISMATCH between Python and ASP:")
        if py - asp_set:
            print(" only in python:", sorted(py - asp_set))
        if asp_set - py:
            print(" only in asp:", sorted(asp_set - py))
        return 1
    for params in CURATED:
        sample = generate(params)
        if not sample.story.strip():
            print("Verification failed: empty story.")
            return 1
        if "Then came the twist" not in sample.story:
            print("Verification failed: missing twist line.")
            return 1
    print(f"OK: Python/ASP parity on {len(py)} combos, and curated stories render cleanly.")
    return 0


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} valid (place, problem, tool, disguise) tuples:\n")
        for place, problem, tool, disguise in stories:
            print(f"  {place:8} {problem:8} {tool:12} {disguise}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.problem} at {p.place} ({p.disguise})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
