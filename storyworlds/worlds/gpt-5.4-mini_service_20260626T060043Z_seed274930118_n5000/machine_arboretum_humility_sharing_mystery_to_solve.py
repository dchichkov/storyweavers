#!/usr/bin/env python3
"""
storyworlds/worlds/machine_arboretum_humility_sharing_mystery_to_solve.py
=========================================================================

A small heartwarming story world about a child, a shared machine, and a
gentle mystery at an arboretum.

Premise:
- A child visits an arboretum where a little machine helps care for young trees.
- Something is not working right, and everyone wonders why.

Tension:
- The child is eager to fix it alone, but the machine needs careful sharing and
  humble listening to others.
- A hidden, ordinary cause explains the mystery.

Turn:
- The child admits what they tried, asks for help, and shares the machine.

Resolution:
- Together, they solve the mystery, the machine works again, and the arboretum
  feels calm and cared for.

This world models:
- physical meters: water level, dust, jam, repair
- emotional memes: curiosity, humility, worry, relief, pride, warmth
- sharing as a cooperative action
- mystery-to-solve as an unknown cause that becomes clear through clues
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
    helper: object | None = None
    machine: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "mother", "girl-child"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "boy-child"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    place: str = "the arboretum"
    indoor: bool = False
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
class Machine:
    id: str
    label: str
    phrase: str
    purpose: str
    clue: str
    fix: str
    requires: set[str] = field(default_factory=set)
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
class Mystery:
    id: str
    question: str
    cause: str
    revealed_by: str
    solved_text: str
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
class StoryParams:
    place: str
    machine: str
    mystery: str
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c


def _m(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mm(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _setm(e: Entity, key: str, val: float) -> None:
    e.meters[key] = val


def _addm(e: Entity, key: str, delta: float) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + delta


def _addmem(e: Entity, key: str, delta: float) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + delta


def _solve_clue(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    machine = world.get("machine")
    helper = world.get("helper")
    if _m(machine, "jam") >= THRESHOLD and _m(machine, "dust") >= THRESHOLD and ("clue", "hose") not in world.fired:
        world.fired.add(("clue", "hose"))
        _addmem(child, "curiosity", 1)
        out.append("They noticed a small clue: one hose end had slipped behind a pot stand.")
    if _m(machine, "jam") >= THRESHOLD and _mm(child, "humility") >= THRESHOLD and ("fix", "share") not in world.fired:
        world.fired.add(("fix", "share"))
        _addm(machine, "repair", 1)
        _addmem(helper, "warmth", 1)
        out.append("The child shared the crank and listened to the helper's careful idea.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    out = _solve_clue(world)
    if narrate:
        for s in out:
            world.say(s)
    return out


SETTINGS = {
    "arboretum": Setting(place="the arboretum", affords={"sprinkle", "sort"}),
}

MACHINES = {
    "sprinkler": Machine(
        id="sprinkler",
        label="watering machine",
        phrase="a small watering machine with a hand crank",
        purpose="sprinkle water onto the young trees",
        clue="a hose slipped loose",
        fix="put the hose back and share the crank",
        requires={"water", "hands"},
    ),
    "sorter": Machine(
        id="sorter",
        label="seed sorter",
        phrase="a little seed-sorting machine with bright buttons",
        purpose="sort seeds into neat trays",
        clue="a tray was upside down",
        fix="turn the tray right-side up and share the buttons",
        requires={"hands"},
    ),
}

MYSTERIES = {
    "dry_seedlings": Mystery(
        id="dry_seedlings",
        question="why the baby trees looked thirsty",
        cause="a hose slipped loose behind a pot stand",
        revealed_by="a hose end behind a pot stand",
        solved_text="the water reached the roots again",
    ),
    "missing_click": Mystery(
        id="missing_click",
        question="why the machine stopped clicking",
        cause="a tray was upside down",
        revealed_by="an upside-down tray",
        solved_text="the sorter clicked happily again",
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Sofia", "Nora", "Iris"]
BOY_NAMES = ["Eli", "Noah", "Theo", "Owen", "Finn"]
HELPERS = ["caretaker", "gardener"]
TRAITS = ["gentle", "curious", "shy", "kind", "thoughtful"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for mid, machine in MACHINES.items():
            if "sort" in setting.affords and mid == "sorter":
                for mys in MYSTERIES:
                    out.append((place, mid, mys))
            if "sprinkle" in setting.affords and mid == "sprinkler":
                for mys in MYSTERIES:
                    out.append((place, mid, mys))
    return out


def settings_detail(setting: Setting, machine: Machine) -> str:
    if machine.id == "sprinkler":
        return "The arboretum path smelled like wet bark and fresh leaves."
    return "The arboretum benches sat under a cool canopy of green."


def introduce(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {child.memes.get('trait_word', 'kind')} child who loved quiet places with trees.")


def describe_machine(world: World, machine: Entity) -> None:
    world.say(f"In the arboretum stood {machine.phrase}, built to {machine.phrase and world.facts['machine_cfg'].purpose}.")


def want_to_help(world: World, child: Entity, machine: Entity, mystery: Mystery) -> None:
    _addmem(child, "curiosity", 1)
    world.say(f"{child.id} wanted to help the arboretum solve {mystery.question}, so {child.pronoun()} walked closer to the machine.")


def attempt_alone(world: World, child: Entity, machine: Entity) -> None:
    _addmem(child, "pride", 1)
    _addm(machine, "jam", 1)
    _addm(machine, "dust", 1)
    _addmem(child, "worry", 1)
    world.say(f"{child.id} tried to fix it alone, but the crank only squeaked and stopped.")


def warn_and_share(world: World, helper: Entity, child: Entity, machine: Entity) -> None:
    _addmem(child, "humility", 1)
    _addmem(helper, "trust", 1)
    world.say(f"The {helper.label} smiled and said it was okay to ask for help and share the work.")
    world.say(f"{child.id} nodded, set aside the brave act, and handed over the crank so they could work together.")


def reveal(world: World, child: Entity, machine: Entity, mystery: Mystery) -> None:
    world.say(f"Then they found the answer: {mystery.revealed_by}.")
    world.say(f"Once it was moved, {mystery.solved_text}.")


def end(world: World, child: Entity, helper: Entity, machine: Entity, mystery: Mystery) -> None:
    _setm(machine, "repair", 2)
    _addmem(child, "relief", 1)
    _addmem(child, "warmth", 1)
    world.say(f"{child.id} felt small in a good way, because being humble helped everyone solve the mystery.")
    world.say(f"By the end, {machine.label} worked again, and the arboretum felt calm and cared for.")


def tell(setting: Setting, machine_cfg: Machine, mystery_cfg: Mystery, name: str, gender: str, helper_role: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, memes={"trait_word": trait}))
    helper = world.add(Entity(id="helper", kind="character", type="adult", label=f"the {helper_role}"))
    machine = world.add(Entity(id="machine", type="machine", label=machine_cfg.label, phrase=machine_cfg.phrase))
    world.facts = {"machine_cfg": machine_cfg, "mystery_cfg": mystery_cfg, "child": child, "helper": helper, "machine": machine}
    introduce(world, child)
    world.say(f"At {setting.place}, there was {machine_cfg.phrase}.")
    describe_machine(world, machine)
    world.para()
    world.say(settings_detail(setting, machine_cfg))
    want_to_help(world, child, machine, mystery_cfg)
    attempt_alone(world, child, machine)
    propagate(world)
    world.para()
    warn_and_share(world, helper, child, machine)
    reveal(world, child, machine, mystery_cfg)
    end(world, child, helper, machine, mystery_cfg)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    c: Entity = _safe_fact(world, f, "child")
    m: Machine = _safe_fact(world, f, "machine_cfg")
    mys: Mystery = _safe_fact(world, f, "mystery_cfg")
    return [
        f"Write a heartwarming story for a young child about {c.id} at the arboretum, a shared machine, and {mys.question}.",
        f"Tell a gentle mystery story where {c.id} learns humility and shares the work to fix {m.label}.",
        f"Create a short story about sharing, an arboretum, and a machine that starts working again after a clue is found.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    helper: Entity = _safe_fact(world, f, "helper")
    machine: Machine = _safe_fact(world, f, "machine_cfg")
    mystery: Mystery = _safe_fact(world, f, "mystery_cfg")
    return [
        QAItem(
            question=f"Where did {child.id} go in the story?",
            answer=f"{child.id} went to the arboretum, where there were trees and a machine that needed help.",
        ),
        QAItem(
            question=f"What did {child.id} want to do with {machine.label}?",
            answer=f"{child.id} wanted to help fix {machine.label} and solve {mystery.question}.",
        ),
        QAItem(
            question=f"How did {child.id} act after the machine did not work?",
            answer=f"{child.id} first tried to handle it alone, then showed humility, shared the work, and asked the helper for help.",
        ),
        QAItem(
            question=f"What clue solved the mystery?",
            answer=f"The clue was {mystery.revealed_by}, which showed what had gone wrong.",
        ),
        QAItem(
            question=f"Who helped {child.id} finish the job?",
            answer=f"The {helper.label} helped {child.id}, and together they got the machine working again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an arboretum?",
            answer="An arboretum is a place where many kinds of trees are grown and cared for.",
        ),
        QAItem(
            question="What does humility mean?",
            answer="Humility means not acting too proud and being willing to learn from other people.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use something, or doing a task together.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is something that is not understood at first and needs clues to solve.",
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


ASP_RULES = r"""
place(arboretum).
machine(sprinkler).
machine(sorter).
mystery(dry_seedlings).
mystery(missing_click).

affords(arboretum,sprinkle).
affords(arboretum,sort).

compatible(arboretum,sprinkler,dry_seedlings) :- place(arboretum), machine(sprinkler), mystery(dry_seedlings), affords(arboretum,sprinkle).
compatible(arboretum,sprinkler,missing_click) :- place(arboretum), machine(sprinkler), mystery(missing_click), affords(arboretum,sprinkle).
compatible(arboretum,sorter,dry_seedlings) :- place(arboretum), machine(sorter), mystery(dry_seedlings), affords(arboretum,sort).
compatible(arboretum,sorter,missing_click) :- place(arboretum), machine(sorter), mystery(missing_click), affords(arboretum,sort).

#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
        for a in sorted(_safe_lookup(SETTINGS, pid).affords):
            lines.append(asp.fact("affords", pid, a))
    for mid in MACHINES:
        lines.append(asp.fact("machine", mid))
    for myid in MYSTERIES:
        lines.append(asp.fact("mystery", myid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def valid_story_combos() -> list[tuple[str, str, str]]:
    return valid_combos()


def asp_verify() -> int:
    py = set(valid_story_combos())
    asps = set(asp_compatible())
    if py == asps:
        print(f"OK: ASP matches Python ({len(py)} combinations).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - asps:
        print("  only in python:", sorted(py - asps))
    if asps - py:
        print("  only in ASP:", sorted(asps - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming arboretum mystery story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--machine", choices=MACHINES)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "machine", None):
        combos = [c for c in combos if c[1] == getattr(args, "machine", None)]
    if getattr(args, "mystery", None):
        combos = [c for c in combos if c[2] == getattr(args, "mystery", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, machine, mystery = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, machine=machine, mystery=mystery, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(MACHINES, params.machine), _safe_lookup(MYSTERIES, params.mystery), params.name, params.gender, params.helper, params.trait)
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
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


CURATED = [
    StoryParams(place="arboretum", machine="sprinkler", mystery="dry_seedlings", name="Maya", gender="girl", helper="caretaker", trait="curious"),
    StoryParams(place="arboretum", machine="sorter", mystery="missing_click", name="Eli", gender="boy", helper="gardener", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_compatible())} compatible combinations:")
        for row in asp_compatible():
            print(" ", row)
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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
