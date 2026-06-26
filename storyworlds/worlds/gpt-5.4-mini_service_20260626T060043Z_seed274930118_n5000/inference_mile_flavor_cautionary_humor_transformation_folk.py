#!/usr/bin/env python3
"""
A small folk-tale storyworld about a traveler, a long mile, and a clue found in flavor.

The tale premise:
- A young traveler and a village cook have to cross a long mile to reach a lantern fair.
- The traveler is hungry and impatient, but the cook notices a strange flavor in the stew.
- From the flavor, the cook makes an inference: the bridge ahead has washed out.
- A cautionary detour leads to a humorous, transformative ending where a humble meal
  becomes the key to safe passage and a better way of traveling.

The story is designed as a compact simulated world with meters and memes, plus
an inline ASP twin for parity checking of the story-logic gate.
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

# Emotional / physical dimensions used in the world simulation.
METER_KEYS = ("hunger", "tiredness", "distance", "safety", "luck")
MEME_KEYS = ("curiosity", "worry", "humor", "trust", "pride", "relief", "caution")

# ---------------------------------------------------------------------------
# Entities
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    buddy: object | None = None
    elder: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for k in METER_KEYS:
            self.meters.setdefault(k, 0.0)
        for k in MEME_KEYS:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
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
    id: str
    label: str
    road_name: str
    miles_to_next: int
    has_bridge: bool = False
    has_kitchen: bool = False
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
class Food:
    id: str
    label: str
    phrase: str
    flavor: str
    clue: str
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
class Companionship:
    id: str
    label: str
    help_text: str
    transformation: str


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "hillroad": Place("hillroad", "the hill road", "Old Lantern Road", 3, has_bridge=True),
    "riverbend": Place("riverbend", "the river bend", "Mossy Ford Road", 2, has_bridge=True),
    "orchard": Place("orchard", "the orchard path", "Apple Row", 1, has_bridge=False),
}

FOODS = {
    "stew": Food("stew", "stew", "a steaming bowl of stew", "smoky", "the soup tasted smoky where the bridge should have been"),
    "porridge": Food("porridge", "porridge", "a warm bowl of porridge", "sweet", "the porridge had a honey note, as if the village bees had been busy"),
    "broth": Food("broth", "broth", "a little cup of broth", "salty", "the broth tasted salty, like road tears in a storm"),
}

COMPANIONS = {
    "goat": Companionship("goat", "goat", "the goat could carry sacks and make a comic clatter", "the traveler learned patience from the goat's steady steps"),
    "mule": Companionship("mule", "mule", "the mule could carry a lantern and keep a calm pace", "the traveler learned that slow feet still reach the fair"),
    "cat": Companionship("cat", "cat", "the cat could sniff the pot and make everyone laugh", "the traveler learned to trust a small clue and a smaller cat"),
}

NAMES = ["Mina", "Jory", "Pavel", "Tessa", "Anya", "Borin", "Lina", "Niko"]
TYPES = {"girl", "boy"}
TRAITS = ["curious", "careful", "cheerful", "stubborn", "quick-eyed", "kind"]

# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------


@dataclass
class StoryParams:
    place: str
    food: str
    companion: str
    name: str
    gender: str
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


def valid_combo(place: Place, food: Food, companion: Companionship) -> bool:
    # The food flavor must offer a plausible inference clue.
    if place.has_bridge and food.clue and companion.id in {"goat", "mule", "cat"}:
        return True
    return False


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pid, place in PLACES.items():
        for fid, food in FOODS.items():
            for cid, comp in COMPANIONS.items():
                if valid_combo(place, food, comp):
                    out.append((pid, fid, cid))
    return out


def explain_rejection(place: Place, food: Food, companion: Companionship) -> str:
    return (
        f"(No story: the chosen ingredients do not make a believable folk-tale inference. "
        f"Try a place with a bridge and a food whose flavor can point to trouble.)"
    )


# ---------------------------------------------------------------------------
# Narrative simulation
# ---------------------------------------------------------------------------


def _narrate_setup(world: World, hero: Entity, elder: Entity, food: Food) -> None:
    world.say(
        f"Long ago, in {world.place.label}, there lived a {hero.pronoun('subject')} "
        f"named {hero.id} who was as {world.facts['trait']} as a candle in wind."
    )
    world.say(
        f"Each evening, {hero.id} walked the {world.place.road_name} with {elder.label} "
        f"and dreamed of the fair on the far side of the mile."
    )
    world.say(
        f"At supper, {elder.label} served {food.phrase}, and {hero.id} was so hungry "
        f"that {hero.pronoun('subject')} nearly forgot to breathe."
    )


def _infer_danger(world: World, hero: Entity, elder: Entity, food: Food) -> None:
    hero.memes["curiosity"] += 1
    elder.memes["caution"] += 1
    world.say(
        f"But when {elder.label} tasted the {food.label}, {elder.pronoun('subject')} paused. "
        f'"This flavor feels wrong," {elder.label} said. "It tastes like the river has been near."'
    )
    world.say(
        f"{hero.id} listened, and {hero.pronoun('subject')} made a quick inference: "
        f"if the water had touched the road, then the bridge on the mile ahead might be unsafe."
    )
    world.facts["inference"] = True
    world.facts["danger_reason"] = "the bridge may have washed out"


def _take_detour(world: World, hero: Entity, companion: Entity) -> None:
    hero.meters["distance"] += world.place.miles_to_next
    hero.memes["worry"] += 1
    world.say(
        f"So they did not march straight on. Instead, {hero.id}, {companion.label}, and {world.facts['elder_name']} "
        f"took the windy sheep track, one careful step at a time."
    )
    world.say(
        f"The road was longer, but the long mile was kinder than a broken bridge."
    )


def _comic_turn(world: World, hero: Entity, companion: Entity, food: Food) -> None:
    hero.memes["humor"] += 1
    companion.memes["humor"] += 1
    world.say(
        f"Halfway along, the {companion.label} snorted at a thorn bush and looked so serious "
        f"that {hero.id} laughed out loud."
    )
    world.say(
        f"Then the {food.label} pot tipped, not onto the path, but onto the goat's tail, "
        f"which made the whole party smell like a soup shop on market day."
    )
    world.say(
        f"Nobody liked the spill, but everybody laughed, because even a cautionary tale may wear a funny hat."
    )


def _transform(world: World, hero: Entity, elder: Entity, companion: Entity, food: Food) -> None:
    hero.memes["trust"] += 1
    elder.memes["relief"] += 1
    hero.memes["pride"] += 1
    hero.meters["safety"] += 1
    world.say(
        f"When they reached the hill, they found the bridge sagging under stormwater, just as {elder.label} had guessed."
    )
    world.say(
        f"Because they trusted the flavor clue, they were safe. Because they were safe, they could share the last of the {food.label} "
        f"with a ferryman who had lost his lunch."
    )
    world.say(
        f"The ferryman gave them lantern oil in return, and by the time the fair bells rang, "
        f"{hero.id} had learned that a small flavor can hide a big warning."
    )
    world.say(
        f"From then on, the village said that {hero.id} had grown from a hasty child into a thoughtful traveler."
    )
    world.facts["resolved"] = True
    world.facts["transformation"] = companion.transformation


def tell(place: Place, food: Food, companion: Companionship, name: str = "Mina",
         gender: str = "girl", trait: str = "curious") -> World:
    world = World(place)
    hero = world.add(Entity(name, kind="character", type=gender, label=name))
    elder = world.add(Entity("Elder", kind="character", type="elder", label="the village cook"))
    buddy = world.add(Entity(companion.id, kind="character", type="animal", label=f"the {companion.label}", plural=False))

    world.facts["trait"] = trait
    world.facts["elder_name"] = elder.label
    world.facts["food"] = food
    world.facts["companion"] = companion
    world.facts["place"] = place

    _narrate_setup(world, hero, elder, food)
    world.para()
    _infer_danger(world, hero, elder, food)
    _take_detour(world, hero, buddy)
    world.para()
    _comic_turn(world, hero, buddy, food)
    _transform(world, hero, elder, buddy, food)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "name") if "name" in f else "a child"
    food: Food = _safe_fact(world, f, "food")  # type: ignore[assignment]
    place: Place = _safe_fact(world, f, "place")  # type: ignore[assignment]
    return [
        f'Write a folk tale for a young child about {hero}, a long mile, and a clue hidden in the flavor of {food.label}.',
        f"Tell a cautionary but funny story set at {place.label} where someone makes an inference from a strange taste.",
        f'Write a short transformation tale in which {hero} learns to trust a flavor clue before crossing the road.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    food: Food = _safe_fact(world, f, "food")  # type: ignore[assignment]
    companion: Companionship = _safe_fact(world, f, "companion")  # type: ignore[assignment]
    place: Place = _safe_fact(world, f, "place")  # type: ignore[assignment]
    hero_name = _safe_fact(world, f, "name") if "name" in f else "the child"
    trait = _safe_fact(world, f, "trait")
    return [
        QAItem(
            question=f"What made {hero_name} and the village cook worry about the road?",
            answer=(
                f"They tasted {food.phrase}, and the strange flavor made the cook infer that the bridge on {place.road_name} might have washed out."
            ),
        ),
        QAItem(
            question=f"Why did they take the long way instead of crossing the bridge right away?",
            answer=(
                f"They took the long way because the flavor clue suggested danger, and caution was wiser than rushing across a possibly broken bridge."
            ),
        ),
        QAItem(
            question=f"What funny thing happened with the {companion.label} on the way?",
            answer=(
                f"The {companion.label} made everyone laugh when the food pot spilled and left the party smelling like a soup shop."
            ),
        ),
        QAItem(
            question=f"How did {hero_name} change by the end of the story?",
            answer=(
                f"At the end, {hero_name} became more thoughtful and trusting. The child learned that a small clue can protect everyone on a long mile."
            ),
        ),
        QAItem(
            question=f"What was the helpful inference in the story?",
            answer=(
                f"The helpful inference was that a strange flavor could mean the river had reached the road, so the bridge might be unsafe."
            ),
        ),
        QAItem(
            question=f"What did the story prove at the end?",
            answer=(
                f"It proved that careful listening, even to a flavor, can lead to safety, humor, and a wise transformation."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is an inference?",
            answer="An inference is a smart guess you make from clues, like noticing smoke and guessing there may be a fire."
        ),
        QAItem(
            question="What does flavor mean?",
            answer="Flavor is the taste and feeling of food in your mouth, such as sweet, salty, sour, or smoky."
        ),
        QAItem(
            question="Why should people be careful near a washed-out bridge?",
            answer="A washed-out bridge can be dangerous because water may have weakened it or carried parts away."
        ),
        QAItem(
            question="Why do folk tales often use simple clues?",
            answer="Folk tales often use simple clues so listeners can follow the warning, the joke, and the lesson easily."
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A story is valid when the place has a bridge and the food yields a useful clue.
bridge_place(P) :- place(P), has_bridge(P).
useful_clue(F) :- food(F), clue(F).

valid_story(P, F, C) :- bridge_place(P), useful_clue(F), companion(C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.has_bridge:
            lines.append(asp.fact("has_bridge", pid))
    for fid, f in FOODS.items():
        lines.append(asp.fact("food", fid))
        if f.clue:
            lines.append(asp.fact("clue", fid))
    for cid in COMPANIONS:
        lines.append(asp.fact("companion", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple[str, str, str]]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


# ---------------------------------------------------------------------------
# Parameter selection
# ---------------------------------------------------------------------------


def explain_gender(gender: str) -> str:
    return f"(No story: this world only supports {gender} as a story choice here.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = list(valid_combos())
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "food", None) is None or c[1] == getattr(args, "food", None))
        and (getattr(args, "companion", None) is None or c[2] == getattr(args, "companion", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place_id, food_id, companion_id = rng.choice(list(filtered))
    place = _safe_lookup(PLACES, place_id)
    food = _safe_lookup(FOODS, food_id)
    comp = _safe_lookup(COMPANIONS, companion_id)

    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    if getattr(args, "gender", None) and gender not in TYPES:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place_id,
        food=food_id,
        companion=companion_id,
        name=name,
        gender=gender,
        trait=trait,
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(PLACES, params.place),
        _safe_lookup(FOODS, params.food),
        _safe_lookup(COMPANIONS, params.companion),
        name=params.name,
        gender=params.gender,
        trait=params.trait,
    )
    world.facts["name"] = params.name
    prompts = generation_prompts(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=prompts,
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# CLI / output
# ---------------------------------------------------------------------------


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if abs(v) > 1e-9}
        memes = {k: round(v, 2) for k, v in e.memes.items() if abs(v) > 1e-9}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  facts: {world.facts}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Story world: a folk tale about inference, a mile, and flavor."
    )
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--food", choices=FOODS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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


CURATED = [
    StoryParams(place="hillroad", food="stew", companion="goat", name="Mina", gender="girl", trait="curious"),
    StoryParams(place="riverbend", food="broth", companion="mule", name="Jory", gender="boy", trait="careful"),
    StoryParams(place="hillroad", food="porridge", companion="cat", name="Tessa", gender="girl", trait="quick-eyed"),
]


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible story combos:\n")
        for t in combos:
            print("  ", t)
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
            header = f"### {p.name}: {p.food} at {p.place} with {p.companion}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
