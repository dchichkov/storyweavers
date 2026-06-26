#!/usr/bin/env python3
"""
Story world: an icy sidewalk fable about problem solving, kindness, and magic.

A small, self-contained simulation in which a child notices a neighbor struggling
on an icy sidewalk, explains the danger, and uses a little magic plus kindness
to solve the problem.
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
    traits: list[str] = field(default_factory=list)
    plural: bool = False
    protective: bool = False

    child: object | None = None
    helper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "aunt"}
        male = {"boy", "father", "man", "brother", "uncle"}
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
class Place:
    name: str
    icy: bool = True
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
class Problem:
    id: str
    verb: str
    gerund: str
    danger: str
    reason: str
    zone: set[str]
    keyword: str = "explain"
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
class Magic:
    id: str
    label: str
    tool: str
    method: str
    effect: str
    helps: set[str] = field(default_factory=set)
    covers: set[str] = field(default_factory=set)
    plural: bool = False
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
class StoryParams:
    place: str
    problem: str
    magic: str
    name: str
    child_type: str
    helper_type: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.ice: float = 1.0

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def say(self, text: str) -> None:
        if text:
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.lines = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.ice = self.ice
        return clone


def explain_surface(world: World) -> None:
    world.say(
        f"It was an icy sidewalk, bright as glass under the pale morning light."
    )


def introduce(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "careful")
    world.say(
        f"{child.id} was a little {trait} {child.type} who liked to notice what others missed."
    )


def want_to_help(world: World, child: Entity) -> None:
    child.memes["kindness"] += 1
    world.say(
        f"{child.id} loved kindness, and {child.pronoun()} liked to help when someone was in trouble."
    )


def problem_seen(world: World, child: Entity, problem: Problem, helper: Entity) -> None:
    child.memes["concern"] += 1
    world.say(
        f"One cold day, {child.id} saw {helper.pronoun('object')} on the sidewalk, "
        f"sliding in a way that made {helper.pronoun('possessive')} arms flap."
    )
    world.say(
        f"{child.id} could see the problem right away: the {problem.keyword} on the sidewalk made every step risky."
    )


def explain_problem(world: World, child: Entity, problem: Problem, helper: Entity) -> None:
    child.memes["explain"] += 1
    world.say(
        f'"Please do not hurry," {child.id} said. "{problem.reason}."'
    )
    world.say(
        f"{child.id} explained it gently, because a clear reason can be kinder than a loud warning."
    )


def magical_fix(world: World, child: Entity, helper: Entity, magic: Magic, problem: Problem) -> None:
    child.memes["hope"] += 1
    child.meters["magic"] = child.meters.get("magic", 0.0) + 1.0
    world.say(
        f"Then {child.id} held up {child.pronoun('possessive')} {magic.label} and whispered a small spell."
    )
    world.say(
        f"The spell {magic.effect}, and the icy shine faded where {magic.method} touched the ground."
    )
    if "salt" in magic.helps or "sand" in magic.helps or "mat" in magic.helps:
        world.ice = 0.0


def solve_problem(world: World, child: Entity, helper: Entity, problem: Problem, magic: Magic) -> None:
    helper.meters["safe_steps"] = helper.meters.get("safe_steps", 0.0) + 1.0
    helper.memes["relief"] += 1
    world.say(
        f"{helper.id} steadied {helper.pronoun('object')} and followed the safer path {child.id} showed."
    )
    world.say(
        f"Together they used the {magic.tool} and the little trick worked like a lantern in fog."
    )


def ending(world: World, child: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"After that, the sidewalk was safer, and {child.id} smiled to see {helper.id} walking with careful steps."
    )
    world.say(
        f"{child.id} had solved the problem with kindness, explanation, and magic, and the cold morning felt bright."
    )


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    problem = _safe_lookup(PROBLEMS, params.problem)
    magic = _safe_lookup(MAGICS, params.magic)

    world = World(place)
    child = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.child_type,
        traits=["little", params.trait],
    ))
    helper = world.add(Entity(
        id="Neighbor",
        kind="character",
        type=params.helper_type,
        label="the neighbor",
        traits=["old", "gentle"],
    ))
    world.add(Entity(
        id="problem",
        type="problem",
        label=problem.id,
        phrase=problem.verb,
    ))
    world.add(Entity(
        id="magic",
        type="magic",
        label=magic.label,
        phrase=magic.tool,
    ))

    explain_surface(world)
    world.para()
    introduce(world, child)
    want_to_help(world, child)
    problem_seen(world, child, problem, helper)
    explain_problem(world, child, problem, helper)
    magical_fix(world, child, helper, magic, problem)
    solve_problem(world, child, helper, problem, magic)
    world.para()
    ending(world, child, helper, problem)

    world.facts.update(
        child=child,
        helper=helper,
        problem=problem,
        magic=magic,
        place=place,
        resolved=world.ice <= 0.0,
    )
    return world


PLACES = {
    "icy_sidewalk": Place(
        name="the icy sidewalk",
        icy=True,
        affords={"explain", "kindness", "magic", "problem_solving"},
    )
}

PROBLEMS = {
    "slip": Problem(
        id="slip",
        verb="slip",
        gerund="slipping",
        danger="the ice could make feet slide out from under a person",
        reason="The ice is slick, and a careful step is safer than a fast one.",
        zone={"feet"},
        keyword="ice",
        tags={"ice", "sidewalk"},
    )
}

MAGICS = {
    "warm_light": Magic(
        id="warm_light",
        label="warm light charm",
        tool="warm light charm",
        method="its golden glow",
        effect="melted the slickest patch and showed the safer stones underneath",
        helps={"salt", "sand", "lamp"},
        covers={"feet"},
    )
}

GIRL_NAMES = ["Mina", "Lila", "Nora", "Tessa", "Ayla", "Iris"]
BOY_NAMES = ["Owen", "Eli", "Jude", "Milo", "Finn", "Theo"]
TRAITS = ["brave", "gentle", "curious", "patient", "clever"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place_id, place in PLACES.items():
        for problem_id in place.affords:
            for magic_id in MAGICS:
                out.append((place_id, problem_id, magic_id))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    problem = _safe_fact(world, f, "problem")
    magic = _safe_fact(world, f, "magic")
    return [
        f'Write a short fable for a child that includes the word "explain" and takes place on an icy sidewalk.',
        f"Tell a gentle story where {child.id} sees {helper.pronoun('object')} in danger, explains the danger, and uses {magic.label} to help.",
        f"Write a fable about kindness and problem solving on {world.place.name} with a little magic and a clear explanation.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    problem = _safe_fact(world, f, "problem")
    magic = _safe_fact(world, f, "magic")
    return [
        QAItem(
            question=f"Where did {child.id} see the trouble happen?",
            answer=f"{child.id} saw it on {world.place.name}, where the ice made the sidewalk slippery.",
        ),
        QAItem(
            question=f"Why did {child.id} explain the problem instead of just rushing past?",
            answer=f"{child.id} explained it because the ice was slick and a fast step could make {helper.id} slip.",
        ),
        QAItem(
            question=f"What did {child.id} use to help solve the problem?",
            answer=f"{child.id} used {magic.label} and a kind explanation to help {helper.id} walk safely.",
        ),
        QAItem(
            question=f"How did the story end for {helper.id}?",
            answer=f"{helper.id} walked with careful steps, and the icy place felt safer by the end.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is ice?",
            answer="Ice is frozen water. It can be slippery and cold.",
        ),
        QAItem(
            question="Why should people walk carefully on an icy sidewalk?",
            answer="People should walk carefully because ice can make shoes slide and cause a fall.",
        ),
        QAItem(
            question="What does kindness mean?",
            answer="Kindness means caring about others and trying to help them in a gentle way.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means finding a good way to fix a hard situation.",
        ),
        QAItem(
            question="What is a magic charm in a fable?",
            answer="A magic charm is a story device that can help change something in a special, surprising way.",
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
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.plural:
            parts.append("plural=True")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(parts)}")
    lines.append(f"  icy surface remaining: {world.ice}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="icy_sidewalk", problem="slip", magic="warm_light", name="Mina", child_type="girl", helper_type="woman", trait="clever"),
    StoryParams(place="icy_sidewalk", problem="slip", magic="warm_light", name="Owen", child_type="boy", helper_type="man", trait="patient"),
    StoryParams(place="icy_sidewalk", problem="slip", magic="warm_light", name="Lila", child_type="girl", helper_type="woman", trait="gentle"),
]


ASP_RULES = r"""
place(icy_sidewalk).
problem(slip).
magic(warm_light).

affords(icy_sidewalk, explain).
affords(icy_sidewalk, kindness).
affords(icy_sidewalk, magic).
affords(icy_sidewalk, problem_solving).

safe_story(P,Pr,M) :- place(P), problem(Pr), magic(M), affords(P, explain), affords(P, kindness), affords(P, magic), affords(P, problem_solving).
#show safe_story/3.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", pid) for pid in PLACES]
    for pid, place in PLACES.items():
        for a in sorted(place.affords):
            lines.append(asp.fact("affords", pid, a))
    for pr in PROBLEMS:
        lines.append(asp.fact("problem", pr))
    for m in MAGICS:
        lines.append(asp.fact("magic", m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_story/3."))
    return sorted(set(asp.atoms(model, "safe_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fable about icy-sidwalk problem solving, kindness, and magic.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--magic", choices=MAGICS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["woman", "man"])
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
    if getattr(args, "place", None) and getattr(args, "place", None) not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "problem", None) and getattr(args, "problem", None) not in PROBLEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "magic", None) and getattr(args, "magic", None) not in MAGICS:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place = getattr(args, "place", None) or "icy_sidewalk"
    problem = getattr(args, "problem", None) or "slip"
    magic = getattr(args, "magic", None) or "warm_light"
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["woman", "man"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, magic=magic, name=name, child_type=gender, helper_type=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show safe_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_valid_combos())
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
