#!/usr/bin/env python3
"""
storyworlds/worlds/down_grown_gumbo_bravery_flashback_bedtime_story.py
======================================================================

A tiny bedtime-story world about a child, a little fear, a brave turn, and a
warm flashback that helps the night feel safe again.

Premise seed:
- down
- grown
- gumbo

Story shape:
- A child is tucked down for bed.
- A smell of gumbo or a small bedtime worry brings up a flashback.
- Bravery grows when the child remembers something kind and true.
- The ending image proves the child can settle and sleep.

This world is deliberately small and constraint-checked: one child, one parent,
one bedtime setting, one worry, one memory, and one comforting resolution.
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

# ---------------------------------------------------------------------------
# World constants
# ---------------------------------------------------------------------------

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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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


@dataclass(frozen=True)
class Setting:
    place: str
    detail: str
    affordances: set[str] = field(default_factory=set)
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


@dataclass(frozen=True)
class Memory:
    id: str
    label: str
    trigger: str
    warmth: str
    bravery_gain: float = 1.0
    fear_drop: float = 1.0
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


@dataclass(frozen=True)
class Comfort:
    id: str
    label: str
    helps_against: set[str]
    action: str
    ending: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        import copy as _copy

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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


SETTINGS = {
    "bedroom": Setting(
        place="the bedroom",
        detail="The lamp made a soft gold circle on the wall.",
        affordances={"bedtime", "sleep", "listen"},
    ),
    "hallway": Setting(
        place="the hallway",
        detail="The hallway was quiet, with sleepy shadows on the floor.",
        affordances={"bedtime", "listen"},
    ),
}

MEMORIES = {
    "gumbo_kitchen": Memory(
        id="gumbo_kitchen",
        label="the gumbo memory",
        trigger="gumbo",
        warmth="warm and safe",
        bravery_gain=1.0,
        fear_drop=1.0,
    ),
    "grown_voice": Memory(
        id="grown_voice",
        label="a grown-up voice",
        trigger="grown",
        warmth="steady and calm",
        bravery_gain=0.5,
        fear_drop=0.5,
    ),
    "down_steps": Memory(
        id="down_steps",
        label="the walk down the steps",
        trigger="down",
        warmth="careful and kind",
        bravery_gain=0.5,
        fear_drop=0.5,
    ),
}

COMFORTS = {
    "nightlight": Comfort(
        id="nightlight",
        label="a little nightlight",
        helps_against={"dark", "shadows"},
        action="switched on",
        ending="glowed like a tiny moon",
    ),
    "blanket": Comfort(
        id="blanket",
        label="the blue blanket",
        helps_against={"cold", "shivers"},
        action="pulled up",
        ending="sat tucked under the child’s chin",
    ),
    "handhold": Comfort(
        id="handhold",
        label="a warm hand to hold",
        helps_against={"thunder", "lonely"},
        action="held",
        ending="stayed close until the breathing slowed",
    ),
}

TRAITS = ["sleepy", "curious", "gentle", "small", "brave"]


@dataclass
class StoryParams:
    place: str = "bedroom"
    memory: str = "gumbo_kitchen"
    comfort: str = "nightlight"
    name: str = "Mia"
    gender: str = "girl"
    parent: str = "mother"
    trait: str = "sleepy"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
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


ASP_RULES = r"""
% A bedtime story is valid when the setting supports bedtime, the memory can
% be triggered, and the chosen comfort actually helps the child's worry.
valid_story(P, M, C) :-
    setting(P),
    memory(M),
    comfort(C),
    affords(P, bedtime),
    triggers(M, _),
    helps(C, Worry),
    worry(Worry).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(setting.affordances):
            lines.append(asp.fact("affords", sid, a))
    for mid, mem in MEMORIES.items():
        lines.append(asp.fact("memory", mid))
        lines.append(asp.fact("triggers", mid, mem.trigger))
    for cid, com in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        for w in sorted(com.helps_against):
            lines.append(asp.fact("helps", cid, w))
    for w in sorted({"dark", "shadows", "thunder", "lonely", "cold", "shivers"}):
        lines.append(asp.fact("worry", w))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_stories())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        if "bedtime" not in setting.affordances:
            continue
        for mem_id, mem in MEMORIES.items():
            for com_id, com in COMFORTS.items():
                worry = mem.trigger if mem.trigger in com.helps_against else None
                if mem_id == "gumbo_kitchen" and com_id == "nightlight":
                    worry = "dark"
                if worry:
                    combos.append((place, mem_id, com_id))
    return combos


def explain_rejection(place: str, memory: str, comfort: str) -> str:
    return (
        f"(No story: the chosen memory and comfort do not make a believable "
        f"bedtime turn in {_safe_lookup(SETTINGS, place).place}. Try a memory/comfort pair "
        f"that genuinely fits the worry and gives the child a brave ending.)"
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))

    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        label=params.name,
        owner=None,
        meters={"fear": 0.0},
        memes={"bravery": 0.0, "sleepiness": 0.0, "comfort": 0.0, "memory": 0.0},
    ))
    parent = world.add(Entity(
        id="Parent",
        kind="character",
        type=params.parent,
        label="the grown-up",
        meters={},
        memes={"patience": 0.0},
    ))
    comfort = _safe_lookup(COMFORTS, params.comfort)
    memory = _safe_lookup(MEMORIES, params.memory)

    world.facts.update(child=child, parent=parent, comfort=comfort, memory=memory)
    return world


def _trigger_memory(world: World, child: Entity, memory: Memory) -> None:
    sig = ("memory", memory.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["memory"] += 1
    child.memes["bravery"] += memory.bravery_gain
    child.meters["fear"] = max(0.0, child.meters["fear"] - memory.fear_drop)
    world.say(
        f"Then a flashback came: {memory.label}, when {memory.warmth}."
    )
    world.say(
        f"The thought made {child.pronoun('possessive')} chest feel a little steadier."
    )


def _use_comfort(world: World, child: Entity, comfort: Comfort) -> None:
    sig = ("comfort", comfort.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    child.memes["comfort"] += 1
    if comfort.id == "nightlight":
        child.meters["fear"] = max(0.0, child.meters["fear"] - 0.5)
    elif comfort.id == "blanket":
        child.meters["fear"] = max(0.0, child.meters["fear"] - 0.25)
    else:
        child.meters["fear"] = max(0.0, child.meters["fear"] - 0.75)
    world.say(
        f"{comfort.label.capitalize()} was {comfort.action}, and the room felt less big."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    child: Entity = world.get(params.name)
    parent: Entity = world.get("Parent")
    memory = _safe_lookup(MEMORIES, params.memory)
    comfort = _safe_lookup(COMFORTS, params.comfort)

    # Act 1
    world.say(
        f"{child.id} was a {params.trait} little {params.gender} getting ready for bed "
        f"down in {world.setting.place}."
    )
    world.say(world.setting.detail)
    world.say(
        f"The grown-up tucked {child.id} in and said it was time to listen to the quiet."
    )

    # Act 2
    world.para()
    child.meters["fear"] += 1
    world.say(
        f"But when the house creaked, {child.id} grew still. The dark felt too tall."
    )
    world.say(
        f"At the same time, the smell of {memory.trigger} drifted up from dinner, "
        f"and that brought a flashback."
    )
    _trigger_memory(world, child, memory)

    # Act 3
    world.para()
    _use_comfort(world, child, comfort)
    if child.meters["fear"] > 0:
        child.memes["bravery"] += 0.5
        world.say(
            f"{child.id} took one slow breath, then another, and held onto the brave thought."
        )
    world.say(
        f"By the end, {child.id} lay down with {comfort.ending}, "
        f"and {parent.pronoun('subject')} smiled because the room was calm again."
    )
    child.memes["sleepiness"] += 1
    child.meters["fear"] = 0.0

    world.facts.update(
        fear=child.meters["fear"],
        bravery=child.memes["bravery"],
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Story generation / QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    memory: Memory = _safe_fact(world, f, "memory")
    comfort: Comfort = _safe_fact(world, f, "comfort")
    return [
        f'Write a bedtime story for a young child where the word "{memory.trigger}" appears as a gentle flashback.',
        f"Tell a small bedtime story about {child.id} becoming brave with {comfort.label} after a worry in {world.setting.place}.",
        f'Write a cozy story that includes "{memory.trigger}", "down", and a calm ending image.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")
    memory: Memory = _safe_fact(world, f, "memory")
    comfort: Comfort = _safe_fact(world, f, "comfort")
    parent: Entity = _safe_fact(world, f, "parent")

    return [
        QAItem(
            question=f"Who was the bedtime story about?",
            answer=f"It was about {child.id}, a little {child.type} getting ready for bed down in {world.setting.place}.",
        ),
        QAItem(
            question=f"What brought the flashback into the story?",
            answer=f"The smell of {memory.trigger} brought a flashback about {memory.label}.",
        ),
        QAItem(
            question=f"What helped {child.id} feel brave again?",
            answer=f"{comfort.label.capitalize()} helped, because it was {comfort.action} and made the room feel safer.",
        ),
        QAItem(
            question=f"How did the grown-up help at the end?",
            answer=f"The grown-up stayed close, watched {child.id} settle down, and smiled when the room became calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gumbo?",
            answer="Gumbo is a warm, thick soup or stew that many people eat for dinner.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something even though you feel scared, because you know you can try.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when a story briefly remembers something that happened before.",
        ),
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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world: down, grown, gumbo, bravery, flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--comfort", choices=COMFORTS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    memory = getattr(args, "memory", None) or rng.choice(list(MEMORIES))
    comfort = getattr(args, "comfort", None) or rng.choice(list(COMFORTS))

    if (place, memory, comfort) not in valid_combos():
        return _fallback_storyparams(args, rng, StoryParams, globals())

    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    name = getattr(args, "name", None) or rng.choice(["Mia", "Noah", "Lila", "Eli", "Ava", "Theo"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        memory=memory,
        comfort=comfort,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
    )


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (place, memory, comfort) combos:\n")
        for place, mem, com in stories:
            print(f"  {place:9} {mem:14} {com}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for p in [
            StoryParams(place="bedroom", memory="gumbo_kitchen", comfort="nightlight", name="Mia", gender="girl", parent="mother", trait="sleepy"),
            StoryParams(place="bedroom", memory="grown_voice", comfort="blanket", name="Noah", gender="boy", parent="father", trait="curious"),
            StoryParams(place="hallway", memory="down_steps", comfort="handhold", name="Ava", gender="girl", parent="mother", trait="gentle"),
        ]:
            samples.append(generate(p))
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
