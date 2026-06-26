#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/accountant_priority_moral_value_animal_story.py
================================================================================

A tiny standalone storyworld with animal characters, an accountant's priority,
and a gentle moral-value turn.

This world is inspired by classic Animal Story pacing:
- a hardworking animal has a job to do,
- a small urgent problem changes the priority,
- the right moral choice creates the happy ending.

The world is state-driven: animals have physical meters and emotional memes,
and the story is generated from a short simulated sequence rather than from a
fixed paragraph with swapped nouns.
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
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    ledger: object | None = None
    note: object | None = None
    pal: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"fox", "wolf", "dog", "rabbit", "bear", "cat", "deer", "mouse"}:
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
    place: str
    detail: str
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
class Task:
    id: str
    verb: str
    gerund: str
    rush: str
    difficulty: str
    keyword: str
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
class Priority:
    id: str
    label: str
    phrase: str
    moral_value: str
    region: str = "heart"
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
class HelperAction:
    id: str
    offer: str
    ending: str
    reward_moral: str
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        return clone


def _clamp01(x: float) -> float:
    return max(0.0, min(1.0, x))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal storyworld with an accountant, a priority, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--priority", choices=PRIORITIES)
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--friend", choices=ANIMALS)
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


@dataclass
class StoryParams:
    place: str
    task: str
    priority: str
    animal: str
    friend: str
    name: str
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> "StoryParams":
    if getattr(args, "task", None) and getattr(args, "priority", None):
        task = _safe_lookup(TASKS, getattr(args, "task", None))
        pri = _safe_lookup(PRIORITIES, getattr(args, "priority", None))
        if not compatible(task, pri):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        (place, task_id, pri_id)
        for place in SETTINGS
        for task_id in _safe_lookup(SETTINGS, place).affords
        for pri_id in PRIORITIES
        if (getattr(args, "place", None) is None or place == getattr(args, "place", None))
        and (getattr(args, "task", None) is None or task_id == getattr(args, "task", None))
        and (getattr(args, "priority", None) is None or pri_id == getattr(args, "priority", None))
        and compatible(_safe_lookup(TASKS, task_id), _safe_lookup(PRIORITIES, pri_id))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, task_id, pri_id = rng.choice(list(combos))
    animal = getattr(args, "animal", None) or rng.choice(sorted(ANIMALS))
    friend = getattr(args, "friend", None) or rng.choice(sorted(a for a in ANIMALS if a != animal))
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, animal))
    return StoryParams(place=place, task=task_id, priority=pri_id, animal=animal, friend=friend, name=name)


SETTINGS = {
    "office": Setting(place="the riverbank office", detail="The office windows looked out over a slow silver river.", affords={"counting", "sorting"}),
    "market": Setting(place="the market square", detail="The market square was bright, busy, and full of cheerful footsteps.", affords={"counting", "sorting", "delivering"}),
    "treehouse": Setting(place="the treehouse desk", detail="The treehouse desk sat under warm leaves and smelled like wood and apples.", affords={"sorting", "counting"}),
}

TASKS = {
    "counting": Task(
        id="counting",
        verb="count the coins",
        gerund="counting coins",
        rush="hurry back to the ledger",
        difficulty="busy",
        keyword="accountant",
        tags={"accountant", "work"},
    ),
    "sorting": Task(
        id="sorting",
        verb="sort the receipts",
        gerund="sorting receipts",
        rush="rush to finish the papers",
        difficulty="careful",
        keyword="priority",
        tags={"priority", "work"},
    ),
    "delivering": Task(
        id="delivering",
        verb="deliver the payment note",
        gerund="delivering notes",
        rush="dart to the gate",
        difficulty="urgent",
        keyword="priority",
        tags={"priority", "help"},
    ),
}

PRIORITIES = {
    "ledger": Priority(id="ledger", label="the ledger", phrase="the ledger page", moral_value="careful work"),
    "friend": Priority(id="friend", label="the frightened friend", phrase="the friend in need", moral_value="kind help"),
    "truth": Priority(id="truth", label="the honest answer", phrase="the honest answer", moral_value="truth"),
}

HELPER_ACTIONS = {
    "share_work": HelperAction(id="share_work", offer="help count the coins", ending="worked side by side", reward_moral="kindness"),
    "carry_note": HelperAction(id="carry_note", offer="carry the note together", ending="walked together to the gate", reward_moral="helpfulness"),
    "read_aloud": HelperAction(id="read_aloud", offer="read the numbers aloud", ending="read the page together", reward_moral="care"),
}

ANIMALS = ["fox", "rabbit", "bear", "deer", "cat", "dog", "mouse", "otter"]
NAMES = {
    "fox": ["Finn", "Fable", "Rory"],
    "rabbit": ["Mina", "Pip", "Holly"],
    "bear": ["Bruno", "Toby", "Milo"],
    "deer": ["Daisy", "June", "Nora"],
    "cat": ["Cleo", "Luna", "Mika"],
    "dog": ["Perry", "Sunny", "Otis"],
    "mouse": ["Milo", "Nim", "Tessa"],
    "otter": ["Ollie", "Rina", "Sage"],
}


def compatible(task: Task, pri: Priority) -> bool:
    return bool(task.tags & set(pri.id for pri in PRIORITIES.values()))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for task_id in setting.affords:
            for pri_id in PRIORITIES:
                if compatible(_safe_lookup(TASKS, task_id), _safe_lookup(PRIORITIES, pri_id)):
                    out.append((place, task_id, pri_id))
    return out


ASP_RULES = r"""
priority_fit(T, P) :- task(T), priority(P), tag(T, X), label(P, X).
valid(Place, T, P) :- affords(Place, T), priority_fit(T, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", sid, t))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for pid, p in PRIORITIES.items():
        lines.append(asp.fact("priority", pid))
        lines.append(asp.fact("label", pid, p.id if p.id != "truth" else "truth"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    a, b = set(asp_valid_combos()), set(valid_combos())
    if a == b:
        print(f"OK: clingo gate matches valid_combos() ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if a - b:
        print("  only in clingo:", sorted(a - b))
    if b - a:
        print("  only in python:", sorted(b - a))
    return 1


def reasonableness(task: Task, priority: Priority) -> bool:
    return compatible(task, priority)


def tell(setting: Setting, task: Task, priority: Priority, animal: str, friend: str, name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=animal, traits=["little", "careful"]))
    pal = world.add(Entity(id=friend.title(), kind="character", type=friend, traits=["small", "kind"]))
    ledger = world.add(Entity(id="Ledger", type="thing", label="ledger", phrase="a heavy ledger page", owner=hero.id))
    note = world.add(Entity(id="Note", type="thing", label="note", phrase="a folded payment note", owner=pal.id))

    hero.memes["duty"] = 1.0
    hero.meters["workload"] = 1.0
    world.say(f"{hero.id} was a little {animal} who worked as an accountant at {setting.place}.")
    world.say(f"{hero.id} loved {task.gerund}, because {hero.pronoun('possessive')} job kept the numbers neat and safe.")
    world.say(f"Every day {hero.id} watched the coins, the papers, and the page with a careful eye.")

    world.para()
    world.say(setting.detail)
    world.say(f"One morning, {hero.id} was ready to {task.verb}, but {hero.pronoun('possessive')} mind kept noticing {priority.phrase}.")
    if priority.id == "ledger":
        world.say(f"The ledger page needed tidy numbers first, and that was {hero.pronoun('possessive')} priority.")
    elif priority.id == "friend":
        world.say(f"A small friend needed help first, and that tugged at {hero.pronoun('possessive')} heart.")
        world.get(pal.id).memes["fear"] = 1.0
    else:
        world.say(f"An honest answer mattered more than a quick answer, so {hero.id} paused before speaking.")
    world.facts["priority"] = priority
    world.facts["task"] = task
    world.facts["hero"] = hero
    world.facts["friend"] = pal
    world.facts["ledger"] = ledger
    world.facts["note"] = note

    world.para()
    if priority.id == "friend":
        world.say(f"Then {pal.id} wobbled in, holding {pal.pronoun('possessive')} paws out. {pal.id} had dropped {note.phrase}.")
        world.say(f"{hero.id} looked at the ledger, then at {pal.id}, and chose the kinder priority.")
        world.say(f'"Let me help first," {hero.id} said, and {hero.id} set aside the numbers for a moment.')
        world.say(f"{hero.id} helped {pal.id} carry the note, and the two friends crossed the square together.")
        hero.memes["care"] = 1.0
        hero.memes["joy"] = 1.0
        hero.memes["moral_value"] = 1.0
    elif priority.id == "ledger":
        world.say(f"{hero.id} kept the page neat, but then a gust tipped the papers into a little heap.")
        world.say(f"{pal.id} rushed in with a smile and said, 'I can help.'")
        world.say(f"{hero.id} accepted the help and learned that a priority can be shared without being lost.")
        hero.memes["gratitude"] = 1.0
        hero.memes["moral_value"] = 1.0
    else:
        world.say(f"{pal.id} asked a hard question, and {hero.id} chose the honest answer instead of a quick one.")
        world.say(f"That made the day calmer, because truth fit the work better than a hurried guess.")
        hero.memes["truth"] = 1.0
        hero.memes["moral_value"] = 1.0

    world.para()
    world.say(f"After that, {hero.id} returned to {task.gerund}, and the work felt lighter because the right priority had been chosen.")
    world.say(f"By evening, {hero.id} was smiling at the neat page, and {priority.moral_value} shone in the little office like a warm lamp.")
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    task = _safe_fact(world, f, "task")
    priority = _safe_fact(world, f, "priority")
    return [
        f'Write a short animal story for a young child about an accountant named {hero.id} who must choose a priority.',
        f"Tell a gentle story where {hero.id} wants to {task.verb} but learns that {priority.label} matters more for a moment.",
        f'Write a small animal story that includes the words "accountant" and "priority" and ends with a moral choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    task = _safe_fact(world, f, "task")
    priority = _safe_fact(world, f, "priority")
    friend = _safe_fact(world, f, "friend")
    return [
        QAItem(
            question=f"What kind of job did {hero.id} have?",
            answer=f"{hero.id} was an accountant. {hero.id} worked with numbers, coins, and papers in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do first?",
            answer=f"{hero.id} wanted to {task.verb} first, because that was the usual work for the day.",
        ),
        QAItem(
            question=f"What was the priority in the story?",
            answer=f"The priority was {priority.phrase}. That meant {priority.moral_value} mattered most at that moment.",
        ),
        QAItem(
            question=f"Who needed help in the story?",
            answer=f"{friend.id} needed help, so {hero.id} chose kindness before finishing the numbers.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} returning to {task.gerund} after choosing the right priority, and the day felt calmer and warmer.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does an accountant do?",
            answer="An accountant helps keep track of numbers, coins, and records so things stay neat and correct.",
        ),
        QAItem(
            question="What is a priority?",
            answer="A priority is the thing that should be handled first because it matters the most right then.",
        ),
        QAItem(
            question="What is moral value?",
            answer="Moral value means the good choice, like being kind, honest, or helpful when it matters.",
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
        meters = {k: round(v, 3) for k, v in e.meters.items() if v}
        memes = {k: round(v, 3) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(task: Task, priority: Priority) -> str:
    return f"(No story: {task.verb} does not match the priority {priority.label} in a reasonable way.)"


CURATED = [
    StoryParams(place="market", task="delivering", priority="friend", animal="fox", friend="rabbit", name="Fable"),
    StoryParams(place="office", task="counting", priority="ledger", animal="bear", friend="otter", name="Bruno"),
    StoryParams(place="treehouse", task="sorting", priority="truth", animal="mouse", friend="cat", name="Nim"),
]


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_facts_stub() -> str:
    return asp_facts()


def asp_program_full(show: str) -> str:
    return asp_program(show)


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
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(PRIORITIES, params.priority), params.animal, params.friend, params.name)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, task, priority) combos:\n")
        for place, task, pri in triples:
            print(f"  {place:10} {task:10} {pri}")
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
            header = f"### {p.name}: {p.task} at {p.place} (priority: {p.priority})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
