#!/usr/bin/env python3
"""
A small standalone story world: a detective story in a reading nook, with rhyme
as the special feature and "pinch" / "way" as seed words.

Premise:
- A young detective in a reading nook notices a tiny problem.
- A missing rhyme clue causes a little tension.
- By following sound, shelf order, and a clever pinch of observation, the case is solved.

This script follows the Storyweavers contract: it defines a world model, a
reasonableness gate, inline ASP rules, generation, QA, trace, and CLI modes.
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    card: object | None = None
    detective: object | None = None
    helper: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    place: str = "the reading nook"
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    clue: str
    weather: str = ""
    keyword: str = ""
    tags: set[str] = field(default_factory=set)
    ACTIVITY: object | None = None
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
    PRIZE: object | None = None
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
class Tool:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str] = field(default_factory=set)
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.current_activity: Optional[Activity] = None

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
        clone.facts = dict(self.facts)
        clone.current_activity = self.current_activity
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_misplaced_clue(world: World) -> list[str]:
    out: list[str] = []
    act = world.current_activity
    if not act:
        return out
    for ent in list(world.entities.values()):
        if ent.kind != "thing":
            continue
        if ent.label != "rhyme card":
            continue
        if ent.meters["missing"] < THRESHOLD:
            continue
        sig = ("missing_clue", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append("A clue had gone missing from the shelf, and that made the nook feel oddly quiet.")
    return out


def _r_pinched_thought(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("Detective")
    if detective.memes["curiosity"] < THRESHOLD or detective.memes["puzzle"] < THRESHOLD:
        return out
    sig = ("pinch_thought", detective.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.memes["focus"] += 1
    out.append("The detective gave the problem a tiny pinch of thought and noticed the rhyme of the words.")
    return out


def _r_find_way(world: World) -> list[str]:
    out: list[str] = []
    detective = world.get("Detective")
    card = world.get("RhymeCard")
    if detective.meters["solved"] >= THRESHOLD:
        return out
    if detective.memes["focus"] < THRESHOLD:
        return out
    sig = ("found_way", detective.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    detective.meters["solved"] += 1
    card.meters["found"] += 1
    out.append("By listening to the rhyming way the books were stacked, the detective found the card behind a taller book.")
    return out


CAUSAL_RULES = [
    Rule("misplaced_clue", _r_misplaced_clue),
    Rule("pinched_thought", _r_pinched_thought),
    Rule("find_way", _r_find_way),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_found(world: World) -> bool:
    sim = world.copy()
    propagate(sim, narrate=False)
    return sim.get("Detective").meters["solved"] >= THRESHOLD


SETTING = Setting(place="the reading nook", affords={"rhyme", "reading"})
ACTIVITY = Activity(
    id="rhyme",
    verb="follow the rhyme",
    gerund="following the rhyme",
    rush="hurry down the way of the words",
    mess="missing clue",
    clue="rhyme",
    weather="",
    keyword="rhyme",
    tags={"rhyme", "detective", "reading"},
)
PRIZE = Prize(
    label="rhyme card",
    phrase="a bright rhyme card with a tiny clue",
    type="card",
    region="shelf",
)
TOOLS = {
    "magnifier": Tool(
        id="magnifier",
        label="a magnifying glass",
        prep="pick up the magnifying glass",
        tail="looked closely at the shelf",
        helps={"rhyme", "reading"},
    ),
    "bookmark": Tool(
        id="bookmark",
        label="a ribbon bookmark",
        prep="slide in a ribbon bookmark",
        tail="used the bookmark to mark the right page",
        helps={"reading"},
    ),
}


@dataclass
class StoryParams:
    activity: str
    place: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A detective story world in a reading nook.")
    ap.add_argument("--place", choices=["reading_nook"], default="reading_nook")
    ap.add_argument("--activity", choices=["rhyme"], default="rhyme")
    ap.add_argument("--tool", choices=TOOLS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["cat", "owl", "mouse"])
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
    lines = [
        asp.fact("setting", "reading_nook"),
        asp.fact("affords", "reading_nook", "rhyme"),
        asp.fact("affords", "reading_nook", "reading"),
        asp.fact("activity", "rhyme"),
        asp.fact("keyword", "rhyme", "rhyme"),
        asp.fact("problem", "missing_clue"),
        asp.fact("prize", "rhyme_card"),
        asp.fact("tool", "magnifier"),
        asp.fact("tool", "bookmark"),
        asp.fact("helps", "magnifier", "rhyme"),
        asp.fact("helps", "magnifier", "reading"),
        asp.fact("helps", "bookmark", "reading"),
    ]
    return "\n".join(lines)


ASP_RULES = r"""
valid_tool(T) :- tool(T), helps(T, rhyme).
valid_story(P, A, T) :- setting(P), affords(P, A), valid_tool(T).
#show valid_story/3.
#show valid_tool/1.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_tools() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_tool/1."))
    return sorted(set(asp.atoms(model, "valid_tool")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {("magnifier",)}
    cl = set(asp_valid_tools())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} tool).")
        return 0
    print("MISMATCH between clingo and Python gate.")
    print("python:", sorted(py))
    print("clingo:", sorted(cl))
    return 1


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS.keys()))
    name = getattr(args, "name", None) or rng.choice(["Mina", "Ivy", "Nia", "Leo", "Noah", "Eli"])
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper = getattr(args, "helper", None) or rng.choice(["cat", "owl", "mouse"])
    if tool not in TOOLS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(
        activity="rhyme",
        place="reading_nook",
        tool=tool,
        name=name,
        gender=gender,
        helper=helper,
    )


def tell(params: StoryParams) -> World:
    world = World(SETTING)
    detective = world.add(Entity(
        id="Detective",
        kind="character",
        type=params.gender,
        label=params.name,
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type=params.helper,
        label=f"the {params.helper}",
    ))
    card = world.add(Entity(
        id="RhymeCard",
        type="card",
        label="rhyme card",
        phrase="a bright rhyme card with a tiny clue",
    ))
    tool = world.add(Entity(
        id=params.tool,
        type="tool",
        label=_safe_lookup(TOOLS, params.tool).label,
        phrase=_safe_lookup(TOOLS, params.tool).label,
        owner=detective.id,
    ))

    world.current_activity = ACTIVITY
    detective.memes["curiosity"] += 1
    detective.memes["puzzle"] += 1
    detective.meters["solved"] += 0

    world.say(
        f"{params.name} was a little detective in {world.setting.place}, where the books sat in neat rows."
    )
    world.say(
        f"{detective.pronoun().capitalize()} loved rhyme because the words made a gentle way through each mystery."
    )
    world.say(
        f"One afternoon, {helper.label} nudged the shelf and a rhyme card slipped from sight."
    )

    world.para()
    world.say(
        f"{params.name} noticed the missing card and picked up {_safe_lookup(TOOLS, params.tool).label}."
    )
    world.say(
        f"{detective.pronoun().capitalize()} gave the problem a careful look, as if the answer might be hiding in a small pinch of words."
    )
    world.say(
        f'The detective whispered, "If there is a rhyme, there is a way."'
    )
    card.meters["missing"] += 1
    propagate(world, narrate=True)

    if predict_found(world):
        world.para()
        world.say(
            f"{detective.pronoun().capitalize()} followed the way the rhymes leaned from one book to the next."
        )
        world.say(
            f"At last, {detective.pronoun('subject')} found the rhyme card behind a taller book, safe and bright."
        )
        world.say(
            f"{helper.label} blinked happily, and the whole reading nook felt quiet again."
        )

    world.facts = {
        "detective": detective,
        "helper": helper,
        "card": card,
        "tool": tool,
        "params": params,
        "activity": ACTIVITY,
        "setting": SETTING,
    }
    return world


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        'Write a short detective story for a young child set in a reading nook, using the word "rhyme".',
        f"Tell a cozy mystery where {p.name} follows a rhyming way to find a missing card in the reading nook.",
        "Write a small story about a detective, a clue, and a gentle solution, with a tiny pinch of suspense.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    detective = _safe_fact(world, world.facts, "detective")
    helper = _safe_fact(world, world.facts, "helper")
    card = _safe_fact(world, world.facts, "card")
    tool = _safe_fact(world, world.facts, "tool")
    return [
        QAItem(
            question=f"Where does {p.name} solve the mystery?",
            answer="The mystery is solved in the reading nook, among the shelves and quiet books.",
        ),
        QAItem(
            question=f"What was missing from the shelf when {helper.label} moved the books?",
            answer=f"A rhyme card was missing from the shelf, so the detective had to look carefully.",
        ),
        QAItem(
            question=f"What tool did {p.name} pick up to look for the clue?",
            answer=f"{p.name} picked up {tool.label} to help with the search.",
        ),
        QAItem(
            question=f"Why did {p.name} say there was a way through the mystery?",
            answer="Because the rhyme in the words gave a clue, and the detective followed that pattern to find the card.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like cat and hat.",
        ),
        QAItem(
            question="What does a magnifying glass help you do?",
            answer="A magnifying glass helps you look closely at small details.",
        ),
        QAItem(
            question="What is a reading nook?",
            answer="A reading nook is a cozy little place made for sitting and reading books.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
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


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def valid_tools() -> list[tuple[str]]:
    return [("magnifier",)]


CURATED = [
    StoryParams(activity="rhyme", place="reading_nook", tool="magnifier", name="Mina", gender="girl", helper="owl"),
    StoryParams(activity="rhyme", place="reading_nook", tool="magnifier", name="Leo", gender="boy", helper="cat"),
]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "tool", None) and getattr(args, "tool", None) not in TOOLS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    tool = getattr(args, "tool", None) or "magnifier"
    name = getattr(args, "name", None) or rng.choice(["Mina", "Ivy", "Nia", "Leo", "Noah", "Eli"])
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper = getattr(args, "helper", None) or rng.choice(["cat", "owl", "mouse"])
    return StoryParams(
        activity="rhyme",
        place="reading_nook",
        tool=tool,
        name=name,
        gender=gender,
        helper=helper,
    )


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for s in stories:
            print("  ", s)
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
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
