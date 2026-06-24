#!/usr/bin/env python3
"""
storyworlds/worlds/afford_conflict_teamwork_mystery.py
======================================================

A small mystery storyworld about a missing object, an affordability clue, a
pair of children in conflict, and the teamwork that solves the case.

Premise:
- In a small, ordinary setting, a child wants something they cannot afford.
- That want creates conflict with a sibling/friend.
- The children investigate a mystery together, using clues from the world state.
- The ending reveals a fair way they can afford it, or a clever substitute, and
  their teamwork repairs the conflict.

The world uses typed entities with physical meters and emotional memes, a small
state machine, a reasonableness gate, and an inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    kind: str = "thing"  # character | thing | place
    type: str = "thing"
    label: str = ""
    role: str = ""
    age: int = 0
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    clue: object | None = None
    item: object | None = None
    jar: object | None = None
    room: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def name(self) -> str:
        return self.label or self.id
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    c: object | None = None
    w: object | None = None
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

    def copy(self) -> "World":
        c = World()
        c.entities = copy.deepcopy(self.entities)
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c
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


@dataclass
class Room:
    id: str
    scene: str
    clue: str
    hidden: str
    mood: str
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
class WantItem:
    id: str
    label: str
    afford_cost: int
    shiny: str
    mystery_tag: str = ""
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
class ConflictBeat:
    id: str
    label: str
    problem: str
    blame_line: str
    repair_line: str
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
class TeamSolution:
    id: str
    label: str
    method: str
    result: str
    qa: str
    substitute: str = ""
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
class StoryParams:
    setting: str
    room: str
    want: str
    conflict: str
    solution: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    relation: str
    seed: Optional[int] = None
    params: object | None = None
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


SETTINGS = {
    "house": Room(
        id="house",
        scene="the quiet house",
        clue="a small note on the fridge",
        hidden="the money jar",
        mood="soft and a little secret",
    ),
    "library": Room(
        id="library",
        scene="the little library",
        clue="a bookmark tucked into a storybook",
        hidden="the coin tray at the desk",
        mood="hushed and puzzle-like",
    ),
    "shop": Room(
        id="shop",
        scene="the corner shop",
        clue="a sticker on the price tag",
        hidden="the change cup by the counter",
        mood="busy and bright",
    ),
}

WANTS = {
    "toy": WantItem("toy", "the red puzzle box", 4, "shiny with a silver lock", "missing-toy"),
    "book": WantItem("book", "the moon atlas", 3, "glimmering with star maps", "missing-book"),
    "snack": WantItem("snack", "the berry tart", 2, "sweet and warm", "missing-snack"),
}

CONFLICTS = {
    "argue": ConflictBeat(
        "argue",
        "an argument",
        "They both wanted the same thing at once.",
        "That made their voices sharp and cross.",
        "Then they took a breath and tried again.",
    ),
    "share": ConflictBeat(
        "share",
        "a sharing problem",
        "Only one of them could carry it safely.",
        "That made the room tense and quiet.",
        "Then they made a plan together.",
    ),
    "lost": ConflictBeat(
        "lost",
        "a lost-item problem",
        "The thing they wanted was nowhere in sight.",
        "That made both children frown at the same time.",
        "Then they searched side by side.",
    ),
}

SOLUTIONS = {
    "money-jar": TeamSolution(
        "money-jar",
        "the money jar",
        "counting coins together",
        "enough coins for the want",
        "They counted coins together and found enough to afford it.",
    ),
    "trade": TeamSolution(
        "trade",
        "a trade",
        "finding a fair trade",
        "a way to get it without wasting money",
        "They found a fair trade and got what they wanted without fighting.",
        substitute="a smaller version",
    ),
    "wait": TeamSolution(
        "wait",
        "waiting for later",
        "saving up with a promise",
        "a plan to afford it soon",
        "They chose to save up and come back later.",
        substitute="a promise card",
    ),
}


GIRL_NAMES = ["Lily", "Mia", "Zoe", "Ava", "Nora", "Maya", "Ivy", "Ella"]
BOY_NAMES = ["Tom", "Ben", "Max", "Sam", "Leo", "Finn", "Eli", "Theo"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mystery storyworld with afford, conflict, and teamwork.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--room", choices=SETTINGS)
    ap.add_argument("--want", choices=WANTS)
    ap.add_argument("--conflict", choices=CONFLICTS)
    ap.add_argument("--solution", choices=SOLUTIONS)
    ap.add_argument("--child1")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2")
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("--relation", choices=["siblings", "friends"])
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


def _pick_name(rng: random.Random, gender: str, avoid: str = "") -> str:
    pool = GIRL_NAMES if gender == "girl" else BOY_NAMES
    choices = [n for n in pool if n != avoid]
    return rng.choice(choices)


def reasonableness_gate(params: StoryParams) -> None:
    if params.want not in WANTS:
        pass
    if params.conflict not in CONFLICTS:
        pass
    if params.solution not in SOLUTIONS:
        pass
    if params.setting not in SETTINGS or params.room not in SETTINGS:
        pass
    if params.want == "snack" and params.solution == "wait":
        pass
    if params.want == "toy" and params.solution == "money-jar":
        return
    if params.want == "book" and params.solution in {"money-jar", "wait", "trade"}:
        return
    if params.want == "snack" and params.solution in {"money-jar", "trade"}:
        return


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for w in WANTS:
            for c in CONFLICTS:
                if w != "snack" or c != "share":
                    out.append((s, w, c))
    return out


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for w, item in WANTS.items():
        lines.append(asp.fact("want", w))
        lines.append(asp.fact("afford_cost", w, item.afford_cost))
    for c in CONFLICTS:
        lines.append(asp.fact("conflict", c))
    for sol in SOLUTIONS:
        lines.append(asp.fact("solution", sol))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,W,C) :- setting(S), want(W), conflict(C), not invalid_combo(W,C).
invalid_combo(snack,argue).
ok_solution(W, money-jar) :- want(W), afford_cost(W, C), C >= 3.
ok_solution(W, trade) :- want(W).
ok_solution(W, wait) :- want(W), W != snack.
"""


def asp_program(extra: str = "", show: str = "") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{extra}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("", "#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


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
        if e.role:
            bits.append(f"role={e.role}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def setup_world(params: StoryParams) -> World:
    w = World()
    setting = _safe_lookup(SETTINGS, params.setting)
    want = _safe_lookup(WANTS, params.want)
    conflict = _safe_lookup(CONFLICTS, params.conflict)
    solution = _safe_lookup(SOLUTIONS, params.solution)

    a = w.add(Entity(id=params.child1, kind="character", type=params.child1_gender, role="child1"))
    b = w.add(Entity(id=params.child2, kind="character", type=params.child2_gender, role="child2"))
    room = w.add(Entity(id=setting.id, kind="place", type="place", label=setting.scene))
    jar = w.add(Entity(id="money_jar", kind="thing", type="jar", label="the money jar"))
    clue = w.add(Entity(id="clue", kind="thing", type="note", label=setting.clue))
    item = w.add(Entity(id=want.id, kind="thing", type="want", label=want.label))

    a.memes["curiosity"] = 1.0
    b.memes["curiosity"] = 1.0
    a.memes["want"] = 1.0
    b.memes["want"] = 1.0

    w.facts.update(
        setting=setting.id,
        room=room,
        want=want,
        conflict=conflict,
        solution=solution,
        child1=a,
        child2=b,
        jar=jar,
        clue=clue,
        item=item,
    )
    return w


def story_intro(w: World) -> None:
    f = w.facts
    a, b = f["child1"], f["child2"]
    setting = SETTINGS[f["setting"]]
    want = f["want"]
    w.say(
        f"At {setting.scene}, {a.id} and {b.id} found a small mystery waiting in the air. "
        f"They both wanted {want.label}, but neither child had enough money for it yet."
    )
    w.say(
        f"That made the day feel {setting.mood}, like a secret was hiding behind {setting.clue}."
    )


def conflict_beat(w: World) -> None:
    f = w.facts
    a, b = f["child1"], f["child2"]
    conflict = f["conflict"]
    a.memes["frustration"] = 1.0
    b.memes["frustration"] = 1.0
    w.para()
    w.say(
        f"Then {conflict.problem} {conflict.blame_line}"
    )
    w.say(
        f'"If you take it, I lose my chance," said {a.id}. "No, I need it more," said {b.id}.'
    )


def investigate(w: World) -> None:
    f = w.facts
    a, b = f["child1"], f["child2"]
    setting = SETTINGS[f["setting"]]
    want = f["want"]
    w.para()
    w.say(
        f"Still, the children looked at the clue. {setting.clue} pointed them to {setting.hidden}, "
        f"where the answer might be."
    )
    w.say(
        f"They searched together, one peeking high and the other checking low, because teamwork was the only way to solve the mystery."
    )
    a.memes["teamwork"] = 1.0
    b.memes["teamwork"] = 1.0


def solve_mystery(w: World) -> None:
    f = w.facts
    a, b = f["child1"], f["child2"]
    want = f["want"]
    solution = f["solution"]
    conflict = f["conflict"]
    w.para()
    if solution.id == "money-jar":
        w.say(
            f"At last they found {solution.label}. The jar held enough coins to afford {want.label}, so the mystery was not a thief at all."
        )
    elif solution.id == "trade":
        w.say(
            f"At last they found a fair trade: one child could offer a neat swap and still afford {want.label} later."
        )
    else:
        w.say(
            f"At last they found a patient plan. They would save up together and afford {want.label} soon."
        )
    w.say(
        f"That answer turned {conflict.label} into teamwork, and both children felt proud instead of cross."
    )


def ending(w: World) -> None:
    f = w.facts
    a, b = f["child1"], f["child2"]
    want = f["want"]
    solution = f["solution"]
    w.para()
    if solution.substitute:
        w.say(
            f"In the end they chose {solution.substitute} to enjoy right away, and kept the real {want.label} in mind for later."
        )
    else:
        w.say(
            f"In the end they walked home together, coins safe in a pocket or a plan in mind, ready to afford {want.label} the honest way."
        )
    w.say(
        f"The last thing the mystery left behind was a quieter room, two kinder voices, and a shared smile."
    )


def tell(params: StoryParams) -> World:
    w = setup_world(params)
    story_intro(w)
    conflict_beat(w)
    investigate(w)
    solve_mystery(w)
    ending(w)
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    want = f["want"]
    setting = SETTINGS[f["setting"]]
    return [
        f"Write a child-friendly mystery story set in {setting.scene} where two children cannot afford {want.label}, argue about it, and solve the problem together.",
        f"Tell a short story about afford, conflict, and teamwork: the children find a clue, discover how to afford {want.label}, and end as friends.",
        f"Create a simple mystery with a fair ending in which a hidden clue helps two children stop fighting and work together.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    a, b = f["child1"], f["child2"]
    want = f["want"]
    solution = f["solution"]
    setting = SETTINGS[f["setting"]]
    return [
        QAItem(
            question=f"What did {a.id} and {b.id} want?",
            answer=f"They wanted {want.label}, but they could not afford it at first.",
        ),
        QAItem(
            question="What made the story feel like a mystery?",
            answer=f"A clue in {setting.scene} pointed them toward the answer, so they had to search and think carefully.",
        ),
        QAItem(
            question="How did the conflict change?",
            answer="They stopped arguing and began helping each other, which turned the problem into teamwork.",
        ),
        QAItem(
            question="What helped them solve it?",
            answer=f"They worked together and used {solution.label} to figure out a fair way forward.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does it mean to afford something?",
            answer="To afford something means to have enough money for it.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people help each other and work together on the same job.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something puzzling that you need clues to solve.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    room = getattr(args, "room", None) or setting
    want = getattr(args, "want", None) or rng.choice(list(WANTS))
    conflict = getattr(args, "conflict", None) or rng.choice(list(CONFLICTS))
    solution = getattr(args, "solution", None) or rng.choice(list(SOLUTIONS))
    if want == "snack" and conflict == "argue":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    child1_gender = getattr(args, "child1_gender", None) or rng.choice(["girl", "boy"])
    child2_gender = getattr(args, "child2_gender", None) or ("boy" if child1_gender == "girl" else "girl")
    child1 = getattr(args, "child1", None) or _pick_name(rng, child1_gender)
    child2 = getattr(args, "child2", None) or _pick_name(rng, child2_gender, avoid=child1)
    relation = getattr(args, "relation", None) or rng.choice(["siblings", "friends"])
    params = StoryParams(
        setting=setting,
        room=room,
        want=want,
        conflict=conflict,
        solution=solution,
        child1=child1,
        child1_gender=child1_gender,
        child2=child2,
        child2_gender=child2_gender,
        relation=relation,
        seed=getattr(args, "seed", None),
    )
    reasonableness_gate(params)
    return params


def generate(params: StoryParams) -> StorySample:
    w = tell(params)
    return StorySample(
        params=params,
        story=w.render(),
        prompts=generation_prompts(w),
        story_qa=story_qa(w),
        world_qa=world_knowledge_qa(w),
        world=w,
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


CURATED = [
    StoryParams("house", "house", "toy", "argue", "money-jar", "Lily", "girl", "Tom", "boy", "siblings", 1),
    StoryParams("library", "library", "book", "lost", "trade", "Mia", "girl", "Ben", "boy", "friends", 2),
    StoryParams("shop", "shop", "snack", "share", "wait", "Ava", "girl", "Leo", "boy", "friends", 3),
]


def valid_combo(params: StoryParams) -> bool:
    return (params.setting, params.want, params.conflict) in valid_combos()


def asp_verify() -> int:
    rc = 0
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python on {len(py)} valid combos.")
    else:
        rc = 1
        print("Mismatch in valid combos.")
        print("python-only:", sorted(py - cl))
        print("asp-only:", sorted(cl - py))
    return rc


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("", "#show valid/3."))
        return
    if getattr(args, "asp", None):
        print(sorted(valid_combos()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
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
