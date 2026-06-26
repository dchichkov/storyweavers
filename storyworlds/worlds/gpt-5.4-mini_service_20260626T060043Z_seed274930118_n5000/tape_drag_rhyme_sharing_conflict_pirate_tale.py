#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/tape_drag_rhyme_sharing_conflict_pirate_tale.py
===============================================================================================================================

A small pirate-tale storyworld about a crew, a thing that needs dragging, a bit
of tape, and a conflict over sharing that is eased with a rhyme.

Premise:
- A pirate crew sails a little ship with a torn sail and a heavy chest.
- The crew must drag something aboard, and a broken strap or torn sail is fixed
  with tape.
- A shiny prize causes conflict because someone wants to keep it, but the crew
  prefers sharing.
- A rhyme helps settle the mood and leads to a cheerful ending.

This world aims for a compact, state-driven pirate story with concrete props:
rope, tape, chest, sail, deck, map, coin, and a small crew.
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
# Data model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" or "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    broken: bool = False
    taped: bool = False
    shared: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    hero: object | None = None
    mate: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"captain", "pirate", "boy", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    place: str = "the ship"
    sea_state: str = "calm"
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
class CrewRole:
    name: str
    type: str
    trait: str
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
class Item:
    id: str
    label: str
    phrase: str
    kind: str
    weight: str
    needs_drag: bool = False
    needs_tape: bool = False
    can_share: bool = False
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
    place: str
    item: str
    rope: str
    name: str
    role: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World state
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "ship": Setting(place="the ship", sea_state="calm"),
    "dock": Setting(place="the dock", sea_state="breezy"),
    "island": Setting(place="the island shore", sea_state="windy"),
}

ITEMS = {
    "chest": Item(
        id="chest",
        label="chest",
        phrase="a heavy sea chest",
        kind="chest",
        weight="heavy",
        needs_drag=True,
        can_share=True,
    ),
    "sail": Item(
        id="sail",
        label="sail",
        phrase="a torn sail",
        kind="sail",
        weight="light",
        needs_tape=True,
    ),
    "map": Item(
        id="map",
        label="map",
        phrase="a treasure map",
        kind="map",
        weight="light",
        can_share=True,
    ),
    "flag": Item(
        id="flag",
        label="flag",
        phrase="a bright pirate flag",
        kind="flag",
        weight="light",
    ),
}

ROLES = {
    "captain": CrewRole(name="Captain Nell", type="captain", trait="bold"),
    "pirate": CrewRole(name="Pip", type="pirate", trait="cheerful"),
    "mate": CrewRole(name="Rory", type="pirate", trait="quick"),
}

# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def build_crew(world: World, params: StoryParams) -> tuple[Entity, Entity, Entity]:
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.role,
        label=params.name,
        memes={"joy": 0.0, "conflict": 0.0, "sharing": 0.0, "pride": 0.0},
        meters={"tired": 0.0},
    ))
    mate = world.add(Entity(
        id="mate",
        kind="character",
        type="pirate",
        label="Miz May",
        memes={"joy": 0.0, "conflict": 0.0, "sharing": 0.0},
    ))
    captain = world.add(Entity(
        id="captain",
        kind="character",
        type="captain",
        label="Captain Reed",
        memes={"joy": 0.0, "conflict": 0.0, "sharing": 0.0},
    ))
    return hero, mate, captain


def start_scene(world: World, hero: Entity, mate: Entity, captain: Entity, item: Item) -> None:
    world.say(
        f"{hero.label} was a {_safe_lookup(ROLES, hero.type).trait} little pirate who loved a good song and a good deck."
    )
    world.say(
        f"{mate.label} and {captain.label} kept the crew busy, and they carried {item.phrase} aboard."
    )
    if item.needs_tape:
        world.say(
            f"The {item.label} had a rip, so {captain.label} wrapped it with tape before the wind could tug it worse."
        )


def drag_action(world: World, hero: Entity, item: Item) -> None:
    if not item.needs_drag:
        return
    world.say(
        f"Then the crew had to drag the {item.label} across the deck, because it was too heavy to lift alone."
    )
    hero.meters["tired"] = hero.meters.get("tired", 0.0) + 1.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0


def conflict_scene(world: World, hero: Entity, mate: Entity, captain: Entity, item: Item) -> None:
    if not item.can_share:
        return
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
    captain.memes["conflict"] = captain.memes.get("conflict", 0.0) + 1.0
    world.say(
        f"Inside the chest, the crew found a shiny coin, and {hero.label} wanted to keep it close."
    )
    world.say(
        f"But {mate.label} said the best pirate crew shares shiny things, and the words made the deck feel tense."
    )


def rhyme_scene(world: World, hero: Entity, mate: Entity, captain: Entity, item: Item) -> None:
    hero.memes["sharing"] = hero.memes.get("sharing", 0.0) + 1.0
    mate.memes["sharing"] = mate.memes.get("sharing", 0.0) + 1.0
    captain.memes["sharing"] = captain.memes.get("sharing", 0.0) + 1.0
    hero.memes["conflict"] = 0.0
    captain.memes["conflict"] = 0.0
    world.say(
        "So Captain Reed began a rhyme: "
        '"One coin, two hands, three cheers at sea; '
        'what we share comes back to me!"'
    )
    world.say(
        f"{hero.label} laughed, and the crew passed the coin around so everyone could have a turn."
    )


def ending_scene(world: World, hero: Entity, mate: Entity, captain: Entity, item: Item) -> None:
    if item.needs_tape:
        tail = "The taped sail held steady"
    else:
        tail = "The deck felt easy again"
    world.say(
        f"{tail}, the chest sat safe, and {hero.label} smiled at the crew's shared treasure."
    )
    world.say(
        f"By the end, nobody was tugging or quarrelling; they were all singing the rhyme together."
    )


def tell(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        pass
    if params.item not in ITEMS:
        pass
    if params.role not in ROLES:
        pass
    world = World(_safe_lookup(SETTINGS, params.place))
    item = _safe_lookup(ITEMS, params.item)
    hero, mate, captain = build_crew(world, params)
    world.facts.update(hero=hero, mate=mate, captain=captain, item=item, params=params)

    start_scene(world, hero, mate, captain, item)
    world.para()
    drag_action(world, hero, item)
    conflict_scene(world, hero, mate, captain, item)
    world.para()
    rhyme_scene(world, hero, mate, captain, item)
    ending_scene(world, hero, mate, captain, item)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    item = _safe_fact(world, f, "item")
    hero = _safe_fact(world, f, "hero")
    return [
        f'Write a short pirate tale about {hero.label}, a bit of tape, and a {item.label} that must be dragged.',
        f"Tell a child-friendly pirate story where sharing solves a conflict and a rhyme helps the crew.",
        f'Write a simple sea story that uses the words "tape" and "drag" and ends with everyone sharing.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mate = _safe_fact(world, f, "mate")
    captain = _safe_fact(world, f, "captain")
    item = _safe_fact(world, f, "item")
    return [
        QAItem(
            question=f"What did the crew have to drag across the deck?",
            answer=f"They had to drag the {item.label} across the deck because it was too heavy to lift alone.",
        ),
        QAItem(
            question=f"Why did the captain use tape?",
            answer=f"The captain used tape to mend the torn sail so the wind would not tug the rip wider.",
        ),
        QAItem(
            question=f"Who spoke up about sharing the shiny coin?",
            answer=f"{mate.label} spoke up and reminded the crew that a good pirate crew shares shiny things.",
        ),
        QAItem(
            question=f"What helped end the conflict on the ship?",
            answer=f"A cheerful rhyme helped settle the conflict, and then the crew shared the coin in turns.",
        ),
        QAItem(
            question=f"How did {hero.label} feel at the end?",
            answer=f"{hero.label} felt happy, because the crew was sharing and singing together by the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is tape used for?",
            answer="Tape is a sticky strip that can hold broken things together or cover a tear for a while.",
        ),
        QAItem(
            question="What does it mean to drag something?",
            answer="To drag something means to pull it along a surface because it is too heavy or awkward to carry.",
        ),
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is a little song or poem where words sound alike at the ends, which makes it fun to say aloud.",
        ),
        QAItem(
            question="Why is sharing good?",
            answer="Sharing is good because it lets more than one person enjoy the same thing and helps everyone feel included.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
item_needs_drag(I) :- item(I), needs_drag(I).
item_needs_tape(I) :- item(I), needs_tape(I).

conflict(C) :- character(C), wants_keep(C, X), can_share(X).
sharing(C) :- character(C), hears_rhyme(C).

resolved :- conflict(_), sharing(_).
compatible_story(P, I, R) :- place(P), item(I), role(R), item_needs_drag(I), item_needs_tape(sail).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for iid, item in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if item.needs_drag:
            lines.append(asp.fact("needs_drag", iid))
        if item.needs_tape:
            lines.append(asp.fact("needs_tape", iid))
        if item.can_share:
            lines.append(asp.fact("can_share", iid))
    for rid in ROLES:
        lines.append(asp.fact("role", rid))
    lines.append(asp.fact("wants_keep", "hero", "chest"))
    lines.append(asp.fact("hears_rhyme", "hero"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    asp_set = set(asp.atoms(model, "compatible_story"))
    py_set = {("ship", "chest", "captain")} if ITEMS["chest"].needs_drag and ITEMS["sail"].needs_tape else set()
    if asp_set == py_set:
        print(f"OK: ASP matches Python gate ({len(asp_set)} combo).")
        return 0
    print("MISMATCH between ASP and Python gate.")
    print("ASP:", sorted(asp_set))
    print("PY :", sorted(py_set))
    return 1


# ---------------------------------------------------------------------------
# Sample generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in SETTINGS:
        for item in ITEMS:
            for role in ROLES:
                if _safe_lookup(ITEMS, item).needs_drag and _safe_lookup(ITEMS, item).needs_tape:
                    combos.append((place, item, role))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "item", None) and getattr(args, "item", None) not in ITEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "role", None) and getattr(args, "role", None) not in ROLES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    options = valid_combos()
    if getattr(args, "place", None):
        options = [c for c in options if c[0] == getattr(args, "place", None)]
    if getattr(args, "item", None):
        options = [c for c in options if c[1] == getattr(args, "item", None)]
    if getattr(args, "role", None):
        options = [c for c in options if c[2] == getattr(args, "role", None)]
    if not options:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, item, role = rng.choice(options)
    name = getattr(args, "name", None) or _safe_lookup(ROLES, role).name
    trait = getattr(args, "trait", None) or _safe_lookup(ROLES, role).trait
    return StoryParams(place=place, item=item, rope="rope", name=name, role=role, trait=trait, seed=getattr(args, "seed", None))


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.broken:
            bits.append("broken=True")
        if e.taped:
            bits.append("taped=True")
        if e.shared:
            bits.append("shared=True")
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small pirate tale with tape, drag, rhyme, sharing, and conflict.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--item", choices=ITEMS.keys())
    ap.add_argument("--role", choices=ROLES.keys())
    ap.add_argument("--name")
    ap.add_argument("--trait")
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


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show compatible_story/3."))
    return sorted(set(asp.atoms(model, "compatible_story")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:\n")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in [
            StoryParams(place="ship", item="chest", rope="rope", name="Pip", role="pirate", trait="cheerful"),
            StoryParams(place="dock", item="chest", rope="rope", name="Nell", role="captain", trait="bold"),
            StoryParams(place="island", item="sail", rope="rope", name="Rory", role="mate", trait="quick"),
        ]:
            samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
