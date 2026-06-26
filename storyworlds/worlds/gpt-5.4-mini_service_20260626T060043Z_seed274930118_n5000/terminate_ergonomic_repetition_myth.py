#!/usr/bin/env python3
"""
storyworlds/worlds/terminate_ergonomic_repetition_myth.py
==========================================================

A small mythic story world about a repeated sacred task that must be ended
without breaking the work. The turning point comes when the elder finds an
ergonomic tool that lets the hero terminate the repetition and finish the rite.
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

    ergonomic: object | None = None
    elder: object | None = None
    entities: set[str] = field(default_factory=set)
    hero: object | None = None
    sacred: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "queen", "priestess", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "king", "priest", "man"}:
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
class Place:
    id: str
    name: str
    mood: str
    affords: set[str] = field(default_factory=set)
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
class Rite:
    id: str
    title: str
    repeated_action: str
    ending_action: str
    strain: str
    success: str
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
class Tool:
    id: str
    label: str
    phrase: str
    helps: set[str]
    ergonomic: bool = False
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
class StoryParams:
    place: str
    rite: str
    tool: str
    hero_name: str
    hero_type: str
    elder_type: str
    trait: str
    seed: Optional[int] = None
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = {k: Entity(**vars(v)) for k, v in self.entities.items()}
        clone.facts = dict(self.facts)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        return clone


PLACES = {
    "temple": Place("temple", "the temple of dawn", "hushed", affords={"chant", "carry", "restore"}),
    "hill": Place("hill", "the wind-hill", "open", affords={"chant", "carry", "restore"}),
    "river": Place("river", "the river shrine", "cool", affords={"chant", "carry", "restore"}),
}

RITES = {
    "chant": Rite(
        id="chant",
        title="the night chant",
        repeated_action="repeat the chant",
        ending_action="end the chant",
        strain="hoarse and tired",
        success="the bells could ring at last",
        keyword="repetition",
        tags={"repeat", "myth", "voice"},
    ),
    "carry": Rite(
        id="carry",
        title="the stone carrying",
        repeated_action="lift the stone again",
        ending_action="set the stone down",
        strain="sore and trembling",
        success="the gate could open at last",
        keyword="repetition",
        tags={"repeat", "myth", "stone"},
    ),
    "restore": Rite(
        id="restore",
        title="the lantern restoration",
        repeated_action="polish the lantern again",
        ending_action="hang the lantern",
        strain="stiff-fingered",
        success="the road could glow at last",
        keyword="repetition",
        tags={"repeat", "myth", "light"},
    ),
}

TOOLS = {
    "staff": Tool("staff", "an ergonomic staff", "an ergonomic staff with a carved grip", {"chant", "carry"}, ergonomic=True),
    "bench": Tool("bench", "an ergonomic bench", "an ergonomic bench with a rounded edge", {"carry", "restore"}, ergonomic=True),
    "gloves": Tool("gloves", "soft gloves", "soft gloves that fit the hands well", {"restore", "chant"}),
}

HERO_NAMES = ["Ari", "Mira", "Taro", "Nisa", "Sorin", "Lena"]
TRAITS = ["brave", "patient", "gentle", "curious", "steadfast"]


def reasonableness_gate(place: Place, rite: Rite, tool: Tool) -> bool:
    return rite.id in place.affords and rite.id in tool.helps


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, p in PLACES.items():
        for rid, r in RITES.items():
            for tid, t in TOOLS.items():
                if reasonableness_gate(p, r, t):
                    out.append((pid, rid, tid))
    return out


def select_hero_name(rng: random.Random) -> str:
    return rng.choice(HERO_NAMES)


def select_gendered_type(rng: random.Random) -> str:
    return rng.choice(["girl", "boy"])


def make_story_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    rite = _safe_lookup(RITES, params.rite)
    tool = _safe_lookup(TOOLS, params.tool)
    world = World(place)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        label=params.hero_name,
        memes={"weariness": 0.0, "hope": 0.0, "joy": 0.0, "resolve": 0.0},
    ))
    elder = world.add(Entity(
        id="Elder",
        kind="character",
        type=params.elder_type,
        label="the elder",
        memes={"concern": 0.0, "wisdom": 1.0},
    ))
    sacred = world.add(Entity(
        id="Rite",
        type="thing",
        label=rite.title,
        phrase=f"the burden of {rite.title}",
        owner=hero.id,
        caretaker=elder.id,
        meters={"strain": 0.0},
        memes={"repetition": 0.0},
    ))
    tool_ent = world.add(Entity(
        id=tool.id,
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        owner=elder.id,
        ergonomic=tool.ergonomic,  # type: ignore[attr-defined]
        plural=tool.plural,
    ))

    world.facts.update(hero=hero, elder=elder, sacred=sacred, tool=tool_ent, rite=rite, tool_def=tool)

    world.say(f"In {place.name}, {hero.id} was a {params.trait} {hero.type} who served {rite.title}.")
    world.say(f"Each night {hero.id} had to {rite.repeated_action}, and the same motions returned again and again.")
    world.say(f"The work was old as rain, and it left {hero.id} {rite.strain}.")
    world.para()
    world.say(f"At {place.name}, the people waited while {hero.id} kept the rite alive.")
    world.say(f"{hero.id} wanted to finish, but the repetition would not end on its own.")
    hero.memes["weariness"] += 1
    sacred.memes["repetition"] += 2
    sacred.meters["strain"] += 1

    world.para()
    world.say(f"Then the elder watched the trembling hands and brought {tool.phrase}.")
    if tool.ergonomic:
        world.say(f'"This is ergonomic," said the elder, "so the body can endure what the spirit must complete."')
    if reasonableness_gate(place, rite, tool):
        world.say(f"With {tool.label}, {hero.id} could stop the wasteful strain and {rite.ending_action}.")
        hero.memes["resolve"] += 1
        hero.memes["hope"] += 1
        sacred.meters["strain"] = 0.0
        sacred.memes["repetition"] = 0.0
        world.say(f"At last, {rite.success}, and the old pattern was terminated.")
        world.say(f"{hero.id} stood calm beside the altar, while the dusk felt new.")
    else:
        pass
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    rite = _safe_fact(world, f, "rite")
    place = world.place.name
    return [
        f'Write a short myth about {hero.id} in {place} where repetition must be brought to an end.',
        f"Tell a child-friendly myth in which {hero.id} keeps doing {rite.repeated_action} until an ergonomic helper arrives.",
        f'Write a simple story that includes the words "terminate" and "ergonomic" and ends with the old task finally stopping.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    rite = _safe_fact(world, f, "rite")
    tool = _safe_fact(world, f, "tool_def")
    elder = _safe_fact(world, f, "elder")
    place = world.place.name
    return [
        QAItem(
            question=f"What did {hero.id} have to do again and again in {place}?",
            answer=f"{hero.id} had to {rite.repeated_action} again and again as part of {rite.title}.",
        ),
        QAItem(
            question=f"Who brought help when the repetition became too hard?",
            answer=f"The elder brought help, and the help was {tool.phrase}.",
        ),
        QAItem(
            question=f"How did the story end once the ergonomic tool arrived?",
            answer=f"{hero.id} could {rite.ending_action}, and the old repetition was terminated at last.",
        ),
        QAItem(
            question=f"Why was the tool useful to {hero.id}?",
            answer=f"It was useful because it was ergonomic, so {hero.id} could finish the rite without so much strain.",
        ),
        QAItem(
            question=f"What did the elder say the ergonomic tool would help with?",
            answer=f"The elder said it would help the body endure the work while the spirit completed the rite.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does ergonomic mean?",
            answer="Ergonomic means shaped or made to fit the body in a comfortable way, so a person can work with less strain.",
        ),
        QAItem(
            question="What does terminate mean?",
            answer="Terminate means to end something or make it stop.",
        ),
        QAItem(
            question="What is repetition?",
            answer="Repetition is doing the same thing over and over again.",
        ),
        QAItem(
            question="What is a myth?",
            answer="A myth is an old story that explains people, gods, heroes, or big events in a memorable way.",
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if getattr(e, "ergonomic", False):
            bits.append("ergonomic=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  place: {world.place.id}")
    return "\n".join(lines)


ASP_RULES = r"""
place_affords(P, R) :- affords(P, R).
tool_helps(T, R) :- helps(T, R).
valid(P, R, T) :- place_affords(P, R), tool_helps(T, R).
#show valid/3.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for r in sorted(p.affords):
            lines.append(asp.fact("affords", pid, r))
    for rid, r in RITES.items():
        lines.append(asp.fact("rite", rid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for r in sorted(t.helps):
            lines.append(asp.fact("helps", tid, r))
        if t.ergonomic:
            lines.append(asp.fact("ergonomic", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid/3."))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic repetition story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--rite", choices=RITES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["elder", "priest", "priestess", "king", "queen"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "rite", None) is None or c[1] == getattr(args, "rite", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, rite, tool = rng.choice(list(combos))
    return StoryParams(
        place=place,
        rite=rite,
        tool=tool,
        hero_name=getattr(args, "name", None) or select_hero_name(rng),
        hero_type=getattr(args, "gender", None) or select_gendered_type(rng),
        elder_type=getattr(args, "parent", None) or "elder",
        trait=getattr(args, "trait", None) or rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = make_story_world(params)
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, rite, tool) combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("temple", "chant", "staff", "Ari", "girl", "elder", "steadfast"),
            StoryParams("hill", "carry", "bench", "Mira", "boy", "king", "patient"),
            StoryParams("river", "restore", "gloves", "Nisa", "girl", "priestess", "gentle"),
        ]
        samples = [generate(p) for p in curated]
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero_name}: {p.rite} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
