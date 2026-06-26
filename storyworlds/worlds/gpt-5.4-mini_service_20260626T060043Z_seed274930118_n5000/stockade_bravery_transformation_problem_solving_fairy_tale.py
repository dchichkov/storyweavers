#!/usr/bin/env python3
"""
storyworlds/worlds/stockade_bravery_transformation_problem_solving_fairy_tale.py
=================================================================================

A tiny fairy-tale storyworld about a stockade, a brave choice, and a problem
that changes into a better shape once someone thinks carefully.

Premise:
- A small kingdom keeps a stockade to protect a village.
- A timid child, page, or young helper wants to help.
- A harmless but tricky problem appears near the stockade gate.
- Bravery is not loud here; it is stepping forward anyway.
- Transformation happens when the hero solves the problem and becomes more
  certain of themselves.

The story is generated from a simple world model with meters and memes:
- meters track physical state like fear, safety, damage, and repairedness
- memes track emotional state like bravery, worry, hope, and relief

The domain is intentionally small and constraint-checked:
- the stockade can be cracked, closed, or opened
- the problem can be a loose beam, a stuck gate, a lost key, or a frightened
  guard
- the resolution is always a concrete problem-solving action that creates a
  visible ending image

This script follows the shared Storyworld contract and includes an ASP twin for
the reasonableness gate.
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


# ---------------------------------------------------------------------------
# World model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    role: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    tool: object | None = None
    def __post_init__(self) -> None:
        for k in ["fear", "bravery", "worry", "hope", "relief", "damage", "repaired", "safety", "confusion"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "woman"}
        male = {"boy", "king", "prince", "man", "guard", "knight", "page"}
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
    name: str = "the stockade"
    setting_line: str = "The stockade stood around the village like a wooden necklace."
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
    label: str
    phrase: str
    danger_line: str
    fix: str
    helper_tool: str
    requires: str
    turn_line: str
    outcome_line: str
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
class HeroProfile:
    type: str
    name: str
    role_word: str
    traits: list[str] = field(default_factory=list)
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.problem_zone: str = ""
        self.problem_resolved: bool = False
        self.problem_active: bool = False

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def copy(self) -> "World":
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.fired = set(self.fired)
        clone.problem_zone = self.problem_zone
        clone.problem_resolved = self.problem_resolved
        clone.problem_active = self.problem_active
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "stockade_village": Place(
        name="the stockade",
        setting_line="The stockade stood around the village like a wooden necklace, keeping the little homes safe.",
        affords={"gate", "repair", "listen"},
    )
}

PROBLEMS = {
    "stuck_gate": Problem(
        id="stuck_gate",
        label="stuck gate",
        phrase="a gate that would not swing open",
        danger_line="The gate groaned and stayed shut, even when the wind pushed at it.",
        fix="free the hinge with the iron oil can",
        helper_tool="iron oil can",
        requires="gate",
        turn_line="The oil slipped into the hinge, and the gate gave one sigh and moved.",
        outcome_line="The gate finally opened wide, and the stockade felt friendly again.",
        tags={"gate", "metal", "repair"},
    ),
    "loose_beam": Problem(
        id="loose_beam",
        label="loose beam",
        phrase="a loose beam in the stockade wall",
        danger_line="One beam had shifted, making a small gap that fluttered in the breeze.",
        fix="tie the beam tight with a rope",
        helper_tool="rope",
        requires="wall",
        turn_line="The rope pulled the beam back into place, snug as a tucked blanket.",
        outcome_line="The wall stood straight once more, and not a single board wobbled.",
        tags={"wall", "rope", "repair"},
    ),
    "lost_key": Problem(
        id="lost_key",
        label="lost key",
        phrase="the missing key for the stockade lock",
        danger_line="The lock waited on the gate, but the key had vanished into the hay.",
        fix="search carefully under the hay and find the key",
        helper_tool="hay scoop",
        requires="key",
        turn_line="Under the hay, the key glinted like a tiny star, and the lock clicked awake.",
        outcome_line="The stockade gate clicked shut safely, and the missing key was no longer missing.",
        tags={"key", "search", "find"},
    ),
    "frightened_guard": Problem(
        id="frightened_guard",
        label="frightened guard",
        phrase="a guard who was too frightened to call for help",
        danger_line="The guard held the lantern close and trembled when the dark got loud.",
        fix="speak kindly and show the guard the safer path",
        helper_tool="lantern",
        requires="guard",
        turn_line="The hero's calm words steadied the guard, like a candle steadies a room.",
        outcome_line="The guard lifted the lantern high, and the stockade path shone clear and warm.",
        tags={"guard", "kindness", "light"},
    ),
}

HEROES = {
    "page": HeroProfile(type="page", name="Nora", role_word="young page", traits=["gentle", "curious"]),
    "boy": HeroProfile(type="boy", name="Theo", role_word="young boy", traits=["careful", "kind"]),
    "girl": HeroProfile(type="girl", name="Mina", role_word="young girl", traits=["bright", "steadfast"]),
}

TOOLS = {
    "iron oil can": {"kind": "tool", "label": "iron oil can", "phrase": "an iron oil can", "protects": {"gate"}},
    "rope": {"kind": "tool", "label": "rope", "phrase": "a sturdy rope", "protects": {"wall"}},
    "hay scoop": {"kind": "tool", "label": "hay scoop", "phrase": "a small hay scoop", "protects": {"search"}},
    "lantern": {"kind": "tool", "label": "lantern", "phrase": "a shining lantern", "protects": {"light"}},
}

TRAITS = ["brave", "thoughtful", "gentle", "curious", "steadfast", "patient"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    problem: str
    hero: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def problem_at_risk(problem: Problem) -> bool:
    return True


def select_solution(problem: Problem) -> Optional[str]:
    if problem.id == "stuck_gate":
        return "iron oil can"
    if problem.id == "loose_beam":
        return "rope"
    if problem.id == "lost_key":
        return "hay scoop"
    if problem.id == "frightened_guard":
        return "lantern"
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for prob_id, prob in PROBLEMS.items():
            for hero_id in HEROES:
                if problem_at_risk(prob) and select_solution(prob):
                    combos.append((place_id, prob_id, hero_id))
    return combos


def explain_rejection(problem: Problem) -> str:
    return f"(No story: there is no good problem-solving path for {problem.label}.)"


# ---------------------------------------------------------------------------
# Causal simulation
# ---------------------------------------------------------------------------
def _raise_bravery(world: World, hero: Entity, amount: float = 1.0) -> None:
    hero.meters["bravery"] += amount
    hero.memes["bravery"] += amount
    hero.meters["fear"] = max(0.0, hero.meters["fear"] - amount)


def _raise_worry(world: World, hero: Entity, amount: float = 1.0) -> None:
    hero.memes["worry"] += amount
    hero.meters["fear"] += amount


def _resolve_problem(world: World, hero: Entity, prob: Problem, tool: Entity) -> None:
    hero.memes["hope"] += 1
    world.problem_resolved = True
    hero.meters["repaired"] += 1
    hero.memes["relief"] += 1


def propagate(world: World) -> None:
    if world.problem_active and not world.problem_resolved:
        hero = next(e for e in world.characters() if e.kind == "character")
        hero.meters["confusion"] += 0.5
        hero.memes["worry"] += 0.5
        hero.meters["bravery"] += 0.5


# ---------------------------------------------------------------------------
# Narrative helpers
# ---------------------------------------------------------------------------
def intro(world: World, hero: Entity, prob: Problem) -> None:
    world.say(world.place.setting_line)
    world.say(
        f"{hero.name} was a {hero.type} with a {hero.memes.get('trait', 0) and ''}".strip()
    )
    world.say(
        f"{hero.name} was a little {world.facts['trait']} {hero.type} who wanted to help near the stockade."
    )
    world.say(
        f"{hero.pronoun().capitalize()} had heard that a good heart should be brave, even when the boards creaked."
    )
    world.say(f"Then {prob.danger_line}")


def scene_problem(world: World, hero: Entity, prob: Problem) -> None:
    _raise_worry(world, hero, 1.0)
    world.problem_active = True
    world.say(
        f"{hero.name} looked at {prob.phrase} and felt small for a moment."
    )
    world.say(
        f"But {hero.pronoun()} took one careful breath and decided to try."
    )


def scene_bravery(world: World, hero: Entity, prob: Problem) -> None:
    _raise_bravery(world, hero, 1.5)
    world.say(
        f"{hero.pronoun().capitalize()} stepped closer to the stockade gate anyway, even though the wind tugged at {hero.pronoun('possessive')} sleeve."
    )
    world.say(
        f"That choice was bravery: not a roar, but a steady step."
    )


def scene_problem_solving(world: World, hero: Entity, prob: Problem, tool: Entity) -> None:
    world.say(
        f"{hero.name} found {tool.phrase} and used it to {prob.fix}."
    )
    world.say(prob.turn_line)
    _resolve_problem(world, hero, prob, tool)


def scene_transformation(world: World, hero: Entity, prob: Problem) -> None:
    hero.meters["safety"] += 1
    hero.memes["relief"] += 1
    hero.memes["hope"] += 1
    world.say(
        f"After that, {hero.name} did not feel like the same {hero.type} who had first looked at the gate."
    )
    world.say(
        f"{hero.pronoun().capitalize()} felt taller inside, as if courage had grown a small bright feather in {hero.pronoun('possessive')} chest."
    )
    world.say(prob.outcome_line)


def tell(place: Place, prob: Problem, hero_profile: HeroProfile) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_profile.name,
        kind="character",
        type=hero_profile.type,
        label=hero_profile.name,
        phrase=f"little {hero_profile.role_word}",
    ))
    tool_info = _safe_lookup(TOOLS, select_solution(prob))
    tool = world.add(Entity(
        id=tool_info["label"].replace(" ", "_"),
        kind="thing",
        type="tool",
        label=tool_info["label"],
        phrase=tool_info["phrase"],
        owner=hero.id,
    ))
    world.facts["trait"] = random.choice(hero_profile.traits + TRAITS)
    world.facts["problem"] = prob
    world.facts["hero"] = hero
    world.facts["tool"] = tool
    world.facts["place"] = place

    intro(world, hero, prob)
    world.para()
    scene_problem(world, hero, prob)
    scene_bravery(world, hero, prob)
    scene_problem_solving(world, hero, prob, tool)
    world.para()
    scene_transformation(world, hero, prob)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    prob = _safe_fact(world, world.facts, "problem")
    return [
        f'Write a fairy tale for a young child about {hero.name} and a {prob.label} at a stockade.',
        f'Tell a short story where a {hero.type} becomes brave by solving a problem near the stockade.',
        f'Write a gentle fairy tale that includes a stockade, courage, and a clever fix.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    prob = _safe_fact(world, world.facts, "problem")
    tool = _safe_fact(world, world.facts, "tool")
    place = _safe_fact(world, world.facts, "place")
    return [
        QAItem(
            question=f"What problem did {hero.name} find at the stockade?",
            answer=f"{hero.name} found {prob.phrase} at {place.name}.",
        ),
        QAItem(
            question=f"What did {hero.name} use to solve the problem?",
            answer=f"{hero.name} used {tool.phrase} to solve it.",
        ),
        QAItem(
            question=f"How did {hero.name} change by the end?",
            answer=f"{hero.name} became braver and more confident after solving the problem.",
        ),
        QAItem(
            question=f"What happened to the stockade at the end?",
            answer=f"The stockade became safer and felt calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a stockade?",
            answer="A stockade is a strong fence or wall made of upright wooden posts that helps protect a place.",
        ),
        QAItem(
            question="What does bravery mean in a fairy tale?",
            answer="Bravery means doing the right thing even when you feel scared.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means thinking carefully about a trouble and choosing a helpful way to fix it.",
        ),
        QAItem(
            question="What is transformation?",
            answer="Transformation means something changes into a new form or a person changes in an important way.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


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
        lines.append(f"  {e.id:12} ({e.type}) {' '.join(bits)}")
    lines.append(f"  resolved={world.problem_resolved} active={world.problem_active}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(stockade_village).
problem(stuck_gate).
problem(loose_beam).
problem(lost_key).
problem(frightened_guard).

solution(stuck_gate,iron_oil_can).
solution(loose_beam,rope).
solution(lost_key,hay_scoop).
solution(frightened_guard,lantern).

valid(Place,Prob,Hero) :- place(Place), problem(Prob), hero(Hero), solution(Prob,_).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for prob_id in PROBLEMS:
        lines.append(asp.fact("problem", prob_id))
    for hero_id in HEROES:
        lines.append(asp.fact("hero", hero_id))
    for prob_id, prob in PROBLEMS.items():
        sol = select_solution(prob)
        if sol:
            lines.append(asp.fact("solution", prob_id, sol.replace(" ", "_")))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
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
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Fairy-tale storyworld about stockade bravery, transformation, and problem solving."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero", choices=HEROES)
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
    if getattr(args, "problem", None) and getattr(args, "problem", None) not in PROBLEMS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "problem", None) and select_solution(_safe_lookup(PROBLEMS, getattr(args, "problem", None))) is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
        and (getattr(args, "hero", None) is None or c[2] == getattr(args, "hero", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prob, hero = rng.choice(list(filtered))
    return StoryParams(place=place, problem=prob, hero=hero)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(HEROES, params.hero))
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


CURATED = [
    StoryParams(place="stockade_village", problem="stuck_gate", hero="page"),
    StoryParams(place="stockade_village", problem="loose_beam", hero="girl"),
    StoryParams(place="stockade_village", problem="lost_key", hero="boy"),
    StoryParams(place="stockade_village", problem="frightened_guard", hero="page"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid/3."))
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
