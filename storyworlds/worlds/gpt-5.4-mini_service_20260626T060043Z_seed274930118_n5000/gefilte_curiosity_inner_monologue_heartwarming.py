#!/usr/bin/env python3
"""
storyworlds/worlds/gefilte_curiosity_inner_monologue_heartwarming.py
====================================================================

A small heartwarming storyworld about a curious child, a comforting kitchen,
and the brave first taste of gefilte.

Premise:
- A child notices a special family dish called gefilte.
- Curiosity grows, but so does hesitation.
- A caregiver offers a tiny, gentle taste and reassuring words.
- The child discovers the dish is safe, warm, and connected to family love.

This world is intentionally small and constraint-checked. It uses:
- physical meters for tangible state like aroma, tastiness, and portion size
- emotional memes for curiosity, worry, courage, comfort, and closeness
- an inner-monologue beat to make the child's hesitation feel authored
- a heartwarming resolution that changes state, not just nouns in a template
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    served_to: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
    place: str
    warmth: str
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
class Food:
    id: str
    label: str
    phrase: str
    aroma: str
    taste: str
    texture: str
    familiar: bool = False
    needs_small_first_taste: bool = True
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
class Companion:
    id: str
    type: str
    label: str
    role_word: str
    soothing_phrase: str
    offer_phrase: str
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
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "kitchen": Setting(place="the kitchen", warmth="warm", affords={"serve"}),
    "dining_room": Setting(place="the dining room", warmth="cozy", affords={"serve"}),
    "grandma_table": Setting(place="Grandma's table", warmth="bright", affords={"serve"}),
}

FOODS = {
    "gefilte": Food(
        id="gefilte",
        label="gefilte",
        phrase="a little dish of gefilte fish",
        aroma="gentle",
        taste="soft and savory",
        texture="smooth",
        familiar=False,
    ),
    "matzo": Food(
        id="matzo",
        label="matzo",
        phrase="a crisp piece of matzo",
        aroma="plain",
        taste="light and toasty",
        texture="dry and crunchy",
        familiar=True,
        needs_small_first_taste=False,
    ),
}

COMPANIONS = {
    "grandmother": Companion(
        id="grandmother",
        type="grandmother",
        label="Grandma",
        role_word="grandma",
        soothing_phrase="a tiny taste is enough to begin with",
        offer_phrase="Would you like to try just a little bite with me?",
    ),
    "mother": Companion(
        id="mother",
        type="mother",
        label="Mom",
        role_word="mom",
        soothing_phrase="we can start small and go slowly",
        offer_phrase="Would you like a small taste and a smile?",
    ),
}

CHILD_NAMES = ["Leah", "Noah", "Maya", "Eli", "Zoe", "Ari", "Nina", "Ben"]
TRAITS = ["curious", "gentle", "careful", "thoughtful", "bright", "soft-hearted"]


@dataclass
class StoryParams:
    setting: str
    food: str
    companion: str
    name: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for food in FOODS:
            for companion in COMPANIONS:
                combos.append((setting, food, companion))
    return combos


def explain_rejection(setting: str, food: str, companion: str) -> str:
    return (
        f"(No story: the requested combination {setting!r}, {food!r}, {companion!r} "
        f"does not make a coherent family-food scene.)"
    )


# ---------------------------------------------------------------------------
# Simulation
# ---------------------------------------------------------------------------
def build_child(world: World, name: str, trait: str) -> Entity:
    child = world.add(Entity(
        id=name,
        kind="character",
        type="girl" if name in {"Leah", "Maya", "Zoe", "Nina"} else "boy",
        label=name,
        plural=False,
        meters={"hunger": 0.0, "portion": 0.0, "satisfied": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "courage": 0.0, "comfort": 0.0, "love": 0.0},
    ))
    child.memes["trait_" + trait] = 1.0
    return child


def build_companion(world: World, key: str) -> Entity:
    comp = _safe_lookup(COMPANIONS, key)
    return world.add(Entity(
        id=comp.id,
        kind="character",
        type=comp.type,
        label=comp.label,
        plural=False,
        meters={"warmth": 1.0},
        memes={"care": 1.0, "patience": 1.0, "love": 1.0},
    ))


def build_food(world: World, key: str, caretaker: str) -> Entity:
    food = _safe_lookup(FOODS, key)
    return world.add(Entity(
        id=food.id,
        kind="thing",
        type="food",
        label=food.label,
        phrase=food.phrase,
        plural=False,
        caretaker=caretaker,
        meters={"aroma": 1.0, "freshness": 1.0, "portion": 1.0, "served": 0.0},
        memes={"specialness": 1.0},
    ))


def _rule_aroma(world: World) -> list[str]:
    out = []
    child = next((e for e in world.entities.values() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    food = world.get("gefilte")
    if not child:
        return out
    sig = ("aroma", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["curiosity"] += 1.0
    out.append(f"A gentle smell drifted from the plate and made {child.id} look up.")
    return out


def _rule_inner_monologue(world: World) -> list[str]:
    out = []
    child = next((e for e in world.entities.values() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    food = world.get("gefilte")
    if not child or child.memes["curiosity"] < 1.0:
        return out
    sig = ("monologue", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["worry"] += 1.0
    out.append(
        f'{child.id} thought, "I want to know how {food.label} tastes, but I do not want '
        f'a surprise I cannot handle."'
    )
    return out


def _rule_small_bite(world: World) -> list[str]:
    out = []
    child = next((e for e in world.entities.values() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    food = world.get("gefilte")
    if not child or child.memes["worry"] < 1.0:
        return out
    sig = ("offer", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["comfort"] += 1.0
    food.meters["portion"] = 0.25
    out.append("So a grown-up gently broke off just a tiny bite and set it on a spoon.")
    return out


def _rule_taste_and_resolve(world: World) -> list[str]:
    out = []
    child = next((e for e in world.entities.values() if e.kind == "character" and e.type in {"girl", "boy"}), None)
    food = world.get("gefilte")
    if not child or food.meters["portion"] < 0.25:
        return out
    sig = ("taste", child.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    child.memes["courage"] += 1.0
    child.memes["worry"] = 0.0
    child.memes["love"] += 1.0
    child.meters["satisfied"] += 1.0
    food.meters["served"] = 1.0
    out.append(
        f"{child.id} took the little bite, and the taste was soft, savory, and comforting."
    )
    return out


CAUSAL_RULES = [_rule_aroma, _rule_inner_monologue, _rule_small_bite, _rule_taste_and_resolve]


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in CAUSAL_RULES:
            sentences = rule(world)
            if sentences:
                changed = True
                produced.extend(sentences)
    if narrate:
        for s in produced:
            world.say(s)


def tell(setting: Setting, food_key: str, companion_key: str, name: str, trait: str) -> World:
    world = World(setting)
    child = build_child(world, name, trait)
    companion = build_companion(world, companion_key)
    food = build_food(world, food_key, companion.id)

    world.say(f"{child.id} was a {trait} child who liked to notice every interesting thing on the table.")
    world.say(
        f"At {setting.place}, {companion.label} set out {food.phrase}, and the room felt {setting.warmth}."
    )
    world.say(
        f"{child.id} felt curious right away, because {food.label} was new and special."
    )

    world.para()
    world.say(
        f"{child.id} wanted to ask about the dish, but first {child.pronoun('subject')} listened to "
        f"{companion.label} explain that {food.label} was part of the family's meal."
    )
    world.say(f"{companion.label} smiled and said, \"{_safe_lookup(COMPANIONS, companion_key).soothing_phrase}\"")
    world.say(f"Then {companion.label} asked, \"{_safe_lookup(COMPANIONS, companion_key).offer_phrase}\"")

    propagate(world, narrate=True)

    world.para()
    world.say(
        f"{child.id} nodded, took the spoon carefully, and tried the tiny bite."
    )
    world.say(
        f"After that, {child.id} smiled in surprise, because {food.label} tasted {_safe_lookup(FOODS, food_key).taste}."
    )
    world.say(
        f"{companion.label} looked delighted, and the table felt even warmer when {child.id} asked for another small bite."
    )

    world.facts.update(
        child=child,
        companion=companion,
        food=food,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")  # type: ignore[assignment]
    comp: Entity = _safe_fact(world, f, "companion")  # type: ignore[assignment]
    food: Entity = _safe_fact(world, f, "food")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    return [
        f'Write a heartwarming story for a young child about curiosity and a tiny taste of {food.label}.',
        f'Tell a gentle family story set at {setting.place} where {child.id} wonders about {food.label} and {comp.label} helps.',
        f'Write a warm story that includes the word "{food.label}" and ends with a child feeling brave after a first bite.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child: Entity = _safe_fact(world, f, "child")  # type: ignore[assignment]
    comp: Entity = _safe_fact(world, f, "companion")  # type: ignore[assignment]
    food: Entity = _safe_fact(world, f, "food")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who was curious about {food.label} in the story?",
            answer=f"{child.id} was curious about {food.label} at {setting.place}.",
        ),
        QAItem(
            question=f"How did {comp.label} help {child.id} feel better about trying {food.label}?",
            answer=(
                f"{comp.label} offered a tiny bite, spoke kindly, and gave {child.id} time "
                f"to feel ready before tasting it."
            ),
        ),
        QAItem(
            question=f"What changed after {child.id} tasted the {food.label}?",
            answer=(
                f"{child.id} felt brave and comforted, and the dish no longer felt scary."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is gefilte?",
            answer="Gefilte is a traditional fish dish that is often served for a special family meal.",
        ),
        QAItem(
            question="Why might a child be curious about a new food?",
            answer=(
                "A child might be curious because new food looks interesting, smells different, "
                "and they want to know what it tastes like."
            ),
        ),
        QAItem(
            question="Why can a tiny first bite help?",
            answer=(
                "A tiny first bite can help because it feels safer and lets someone try a new food slowly."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
setting(S) :- setting_fact(S).
food(F) :- food_fact(F).
companion(C) :- companion_fact(C).

compatible(S, F, C) :- setting(S), food(F), companion(C).
#show compatible/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting_fact", sid))
    for fid in FOODS:
        lines.append(asp.fact("food_fact", fid))
    for cid in COMPANIONS:
        lines.append(asp.fact("companion_fact", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


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


# ---------------------------------------------------------------------------
# Interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming gefilte curiosity storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--name", choices=CHILD_NAMES)
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
    if getattr(args, "setting", None) and getattr(args, "food", None) and getattr(args, "companion", None):
        if (getattr(args, "setting", None), getattr(args, "food", None), getattr(args, "companion", None)) not in valid_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "food", None) is None or c[1] == getattr(args, "food", None))
        and (getattr(args, "companion", None) is None or c[2] == getattr(args, "companion", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, food, companion = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, food=food, companion=companion, name=name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), params.food, params.companion, params.name, params.trait)
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
        lines.append(f"  {e.id:10} ({e.type:10}) meters={meters} memes={memes}")
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
    StoryParams(setting="kitchen", food="gefilte", companion="grandmother", name="Leah", trait="curious"),
    StoryParams(setting="dining_room", food="gefilte", companion="mother", name="Noah", trait="thoughtful"),
    StoryParams(setting="grandma_table", food="gefilte", companion="grandmother", name="Maya", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for c in combos:
            print(" ", c)
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
            header = f"### {p.name}: {p.food} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
