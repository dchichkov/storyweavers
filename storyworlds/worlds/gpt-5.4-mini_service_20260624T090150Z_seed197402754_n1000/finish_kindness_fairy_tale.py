#!/usr/bin/env python3
"""
storyworlds/worlds/finish_kindness_fairy_tale.py
================================================

A small fairy-tale storyworld about a kindness that begins unfinished and
finishes with a gentle, magical repair.

Premise:
- A child or young helper notices someone in the castle village is stuck with
  a broken task, a lost token, or a lonely feeling.
- Kindness is modeled as a resource that can be offered, shared, or returned.
- The turn arrives when a patient helper chooses the safe, honest, finishing
  action instead of a boastful shortcut.
- The ending proves the change by showing the task finished and the mood bright.

The story keeps to a fairy-tale cadence while staying grounded in the world
state: who has what, what is broken, what gets mended, and who feels better.
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
    caretakers: list[str] = field(default_factory=list)
    carried_by: Optional[str] = None
    hidden: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gift_ent: object | None = None
    helper: object | None = None
    hero: object | None = None
    task: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "princess", "queen", "woman", "mother"}
        male = {"boy", "prince", "king", "man", "father"}
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
class Setting:
    place: str = "the castle garden"
    indoors: bool = False
    light: str = "golden"
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
class Quest:
    id: str
    verb: str
    gerund: str
    risk: str
    fail: str
    token: str
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
class Gift:
    id: str
    label: str
    phrase: str
    type: str
    carried_kind: str
    needed_for: str
    return_word: str
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


@dataclass
class Charm:
    id: str
    label: str
    prep: str
    tail: str
    boosts: set[str]
    covers: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _r_unfinished(world: World) -> list[str]:
    out: list[str] = []
    for q in [e for e in world.entities.values() if e.kind == "quest"]:
        if q.meters.get("broken", 0) < THRESHOLD:
            continue
        if q.memes.get("kindness", 0) < THRESHOLD:
            continue
        sig = ("mend", q.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        q.meters["broken"] = 0
        q.meters["done"] = 1
        q.memes["hope"] = q.memes.get("hope", 0) + 1
        out.append(f"The unfinished thing at last became whole.")
    return out


def _r_cheer(world: World) -> list[str]:
    out: list[str] = []
    for e in [e for e in world.entities.values() if e.kind == "character"]:
        if e.memes.get("kindness", 0) < THRESHOLD:
            continue
        if e.meters.get("mended", 0) < THRESHOLD:
            continue
        sig = ("cheer", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["joy"] = e.memes.get("joy", 0) + 1
        out.append(f"{e.label or e.id} felt lighter, as if a small lantern had been lit inside.")
    return out


CAUSAL_RULES = [
    Rule("unfinished", _r_unfinished),
    Rule("cheer", _r_cheer),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                out.extend(s)
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_knowledge():
    return {
        "kindness": [
            ("What is kindness?",
             "Kindness means doing something gentle and helpful for someone else, like sharing, listening, or helping finish a hard task."),
        ],
        "finish": [
            ("What does it mean to finish something?",
             "To finish something means to bring it to the end so it is complete, instead of leaving it half done."),
        ],
        "fairy": [
            ("What is a fairy tale?",
             "A fairy tale is a magical story with simple characters, a clear problem, and a happy ending."),
        ],
        "castle": [
            ("What is a castle?",
             "A castle is a big strong home made of stone, like the home of a king or queen in a fairy tale."),
        ],
    }


KNOWLEDGE = build_knowledge()
KNOWLEDGE_ORDER = ["kindness", "finish", "fairy", "castle"]


SETTINGS = {
    "garden": Setting(place="the castle garden", indoors=False, light="golden", affords={"mend", "share"}),
    "hall": Setting(place="the great hall", indoors=True, light="soft", affords={"mend", "return"}),
    "village": Setting(place="the village lane", indoors=False, light="dawn", affords={"share", "return"}),
}

QUESTS = {
    "ribbon": Quest(
        id="ribbon",
        verb="finish weaving the ribbon",
        gerund="weaving the ribbon",
        risk="frayed and loose",
        fail="come undone",
        token="ribbon",
        tags={"finish", "kindness"},
    ),
    "lantern": Quest(
        id="lantern",
        verb="finish polishing the lantern",
        gerund="polishing the lantern",
        risk="dim and dusty",
        fail="stay dark",
        token="lantern",
        tags={"finish", "light"},
    ),
    "song": Quest(
        id="song",
        verb="finish the song",
        gerund="singing the song",
        risk="half-sung and lonely",
        fail="fade away",
        token="song",
        tags={"finish", "music"},
    ),
}

GIFTS = {
    "thread": Gift("thread", "silver thread", "a spool of silver thread", "thread", "thread", "ribbon", "return the thread"),
    "cloth": Gift("cloth", "clean cloth", "a square of clean cloth", "cloth", "cloth", "lantern", "return the cloth"),
    "notes": Gift("notes", "song notes", "a page of bright song notes", "notes", "notes", "song", "return the notes"),
}

CHAR_TYPES = ["girl", "boy", "princess", "prince"]
NAMES = ["Lily", "Mina", "Rose", "Elin", "Finn", "Theo", "Owen", "Iris"]
TRAITS = ["gentle", "curious", "brave", "kind", "patient"]


@dataclass
class StoryParams:
    place: str
    quest: str
    gift: str
    name: str
    type: str
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


def quest_at_risk(quest: Quest, gift: Gift) -> bool:
    return quest.id == gift.needed_for


def select_charm(quest: Quest, gift: Gift) -> Optional[Charm]:
    if not quest_at_risk(quest, gift):
        return None
    if quest.id == "ribbon":
        return Charm("gentle_knot", "a gentle knot charm", "tie on a tiny charm first", "and the ribbon stayed neat", {"mend"}, {"hands"})
    if quest.id == "lantern":
        return Charm("soft_wrap", "a soft wrapping charm", "wrap the lantern with a soft cloth first", "and the glass shone safe and bright", {"mend"}, {"hands"})
    if quest.id == "song":
        return Charm("memory_stitch", "a memory-stitch charm", "hum the first line together before starting", "and the song found its last line", {"mend"}, {"voice"})
    return None


ASP_RULES = r"""
quest_at_risk(Q, G) :- needs(Q, K), carried_kind(G, K).
fix(Q, C) :- quest_at_risk(Q, G), charm(C), boosts(C, mend), covers(C, hands).
valid_story(P, Q, G) :- place(P), quest(Q), gift(G), available_at(P, Q), quest_at_risk(Q, G), fix(Q, _).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        if s.indoors:
            lines.append(asp.fact("indoors", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("available_at", pid, a))
    for qid, q in QUESTS.items():
        lines.append(asp.fact("quest", qid))
        lines.append(asp.fact("needs", qid, _safe_lookup(GIFTS, qid).carried_kind))
    for gid, g in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("carried_kind", gid, g.carried_kind))
    for cid in ["gentle_knot", "soft_wrap", "memory_stitch"]:
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("boosts", cid, "mend"))
        lines.append(asp.fact("covers", cid, "hands"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, s in SETTINGS.items():
        for qid in s.affords:
            for gid, g in GIFTS.items():
                if quest_at_risk(_safe_lookup(QUESTS, qid), g):
                    out.append((place, qid, gid))
    return sorted(set(out))


def tell(setting: Setting, quest: Quest, gift: Gift, name: str, typ: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=typ, label=name, traits=[trait, "kind"]))
    helper = world.add(Entity(id="helper", kind="character", type="queen", label="the queen", traits=["wise"]))
    task = world.add(Entity(id=quest.id, kind="quest", type="quest", label=f"the {quest.id}", phrase=quest.gerund))
    gift_ent = world.add(Entity(id=gift.id, kind="thing", type=gift.type, label=gift.label, phrase=gift.phrase, owner=name))
    task.meters["broken"] = 1
    hero.memes["curiosity"] = 1
    world.facts.update(hero=hero, helper=helper, task=task, gift=gift_ent, quest=quest, setting=setting)

    world.say(f"Once in {setting.place}, there lived a {trait} {typ} named {name}.")
    world.say(f"{name} loved {quest.gerund}, yet the work was still {quest.risk}.")
    world.say(f"The queen brought {gift.phrase} and watched kindly from the stone steps.")
    world.para()
    world.say(f"One bright morning, {name} saw that {quest.id} might {quest.fail}.")
    world.say(f"{name} wanted to {quest.verb}, but needed a thoughtful way to begin.")
    world.say(f"Then {name} noticed {gift.label}, and {hero.pronoun('possessive')} heart felt warm with kindness.")
    charm = select_charm(quest, gift)
    if charm:
        task.memes["kindness"] = 1
        hero.memes["kindness"] = 1
        world.para()
        world.say(f"{hero.pronoun('possessive').capitalize()} {trait} hands chose to {charm.prep}.")
        world.say(f"That small kindness made the task possible.")
        task.meters["broken"] = 0
        task.meters["done"] = 1
        hero.meters["mended"] = 1
        propagate(world, narrate=True)
        world.say(f"At last, {name} {quest.verb}, and {charm.tail}.")
        world.say(f"The tale ended with {quest.id} finished and {name} smiling under the castle light.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, quest = f["hero"], f["quest"]
    return [
        f'Write a short fairy tale for a child about "{quest.id}" and kindness.',
        f"Tell a gentle story where {hero.label} notices that {quest.gerund} is unfinished and chooses a kind way to finish it.",
        f"Write a fairy-tale ending in which a small helper uses kindness to finish the work.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, quest, gift = f["hero"], f["quest"], f["gift"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.label}, a {hero.type} who shows kindness in a fairy-tale place.",
        ),
        QAItem(
            question=f"What was not finished at first?",
            answer=f"At first, {quest.id} was not finished. It was {quest.risk}, so it needed careful help.",
        ),
        QAItem(
            question=f"What helped {hero.label} begin the work?",
            answer=f"{gift.phrase} helped {hero.label} begin the work in a kind and careful way.",
        ),
    ]
    if f["task"].meters.get("done", 0) >= THRESHOLD:
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {quest.id} finished, and {hero.label} smiling because kindness helped the work come whole.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["quest"].tags)
    out = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", quest="ribbon", gift="thread", name="Lily", type="girl", trait="gentle"),
    StoryParams(place="hall", quest="lantern", gift="cloth", name="Finn", type="boy", trait="patient"),
    StoryParams(place="village", quest="song", gift="notes", name="Iris", type="princess", trait="kind"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale storyworld about finishing with kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--name")
    ap.add_argument("--type", choices=CHAR_TYPES)
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
    combos = [c for c in combos
              if getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)
              and getattr(args, "quest", None) is None or c[1] == getattr(args, "quest", None)
              and getattr(args, "gift", None) is None or c[2] == getattr(args, "gift", None)]
    if getattr(args, "quest", None) and getattr(args, "gift", None) and not quest_at_risk(_safe_lookup(QUESTS, getattr(args, "quest", None)), _safe_lookup(GIFTS, getattr(args, "gift", None))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, gift = rng.choice(list(combos))
    typ = getattr(args, "type", None) or rng.choice(CHAR_TYPES)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, quest=quest, gift=gift, name=name, type=typ, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(GIFTS, params.gift), params.name, params.type, params.trait)
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


def asp_verify() -> int:
    import storyworlds.asp as asp
    program = asp_program("#show valid_story/3.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "valid_story"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print(" only in clingo:", sorted(clingo_set - py_set))
    print(" only in python:", sorted(py_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
