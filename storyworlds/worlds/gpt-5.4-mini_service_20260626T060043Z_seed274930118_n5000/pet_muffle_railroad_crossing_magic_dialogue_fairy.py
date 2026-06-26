#!/usr/bin/env python3
"""
A standalone storyworld for a fairy-tale railroad crossing tale with a pet,
a muffle, a little magic, and a dialogue-driven turn.

The story premise:
- A child and a beloved pet wait near a railroad crossing.
- The crossing bell is too loud for the pet.
- A magical muffle charm is found or made.
- Dialogue leads to a calm, safe resolution.

The world model tracks:
- physical meters: noise, calm, distance, safety
- emotional memes: worry, kindness, trust, delight

The narrative is intended to feel like a small fairy tale with a clear
beginning, middle turn, and ending image proving what changed.
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
# Core domain constants
# ---------------------------------------------------------------------------

THRESHOLD = 1.0



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
    kind: str = "thing"  # "character" | "pet" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)
    plural: bool = False
    magical: bool = False
    carries: set[str] = field(default_factory=set)

    charm: object | None = None
    entities: set[str] = field(default_factory=set)
    guardian: object | None = None
    hero: object | None = None
    pet: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"noise": 0.0, "calm": 0.0, "distance": 0.0, "safety": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "kindness": 0.0, "trust": 0.0, "delight": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen"}
        male = {"boy", "father", "man", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Pet:
    id: str
    species: str
    label: str
    phrase: str
    noise_sense: str
    comfort_need: str
    magical_response: str
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
class Charm:
    id: str
    label: str
    phrase: str
    effect: str
    grants: set[str] = field(default_factory=set)
    CHARM: object | None = None
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
class Place:
    name: str
    outdoors: bool = True
    features: set[str] = field(default_factory=set)
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
        self.pet: Optional[Entity] = None
        self.charm: Optional[Entity] = None
        self.hero: Optional[Entity] = None
        self.guardian: Optional[Entity] = None
        self.facts: dict = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.trace_lines: list[str] = []

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        other = World(self.place)
        other.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "caretaker": v.caretaker,
            "meters": dict(v.meters), "memes": dict(v.memes),
            "traits": list(v.traits), "plural": v.plural, "magical": v.magical,
            "carries": set(v.carries),
        }) for k, v in self.entities.items()}
        other.pet = other.entities.get(self.pet.id) if self.pet else None
        other.charm = other.entities.get(self.charm.id) if self.charm else None
        other.hero = other.entities.get(self.hero.id) if self.hero else None
        other.guardian = other.entities.get(self.guardian.id) if self.guardian else None
        other.facts = dict(self.facts)
        return other


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "railroad_crossing": Place(
        name="the railroad crossing",
        outdoors=True,
        features={"tracks", "crossing gate", "bell", "signal light"},
    )
}

PETS = {
    "cat": Pet(
        id="cat",
        species="cat",
        label="cat",
        phrase="a silver-gray cat with bright eyes",
        noise_sense="sharp ears",
        comfort_need="a soft, calm place",
        magical_response="purrs like a tiny drum",
    ),
    "dog": Pet(
        id="dog",
        species="dog",
        label="dog",
        phrase="a small brown dog with a wagging tail",
        noise_sense="twitchy ears",
        comfort_need="a warm, safe side of the path",
        magical_response="leans close and sighs happily",
    ),
}

CHARM = Charm(
    id="muffle",
    label="muffle charm",
    phrase="a tiny muffle charm carved from moonwood",
    effect="softens loud sounds",
    grants={"quiet", "calm", "safety"},
)

GIRL_NAMES = ["Mira", "Luna", "Nora", "Elsie", "Faye"]
BOY_NAMES = ["Eli", "Robin", "Theo", "Pip", "Bram"]
TRAITS = ["gentle", "brave", "kind", "curious", "soft-spoken"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str = "railroad_crossing"
    pet: str = "cat"
    name: str = "Mira"
    gender: str = "girl"
    guardian: str = "mother"
    trait: str = "gentle"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World mechanics
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


def pet_is_startled(world: World, pet: Entity) -> bool:
    return pet.meters["noise"] >= THRESHOLD and pet.memes["worry"] >= THRESHOLD


def muffle_helps(world: World, pet: Entity, charm: Entity) -> bool:
    return pet_is_startled(world, pet) and charm.magical


def predict_loudness(world: World) -> float:
    return 2.0 if world.place.name == "the railroad crossing" else 0.0


def apply_noise(world: World) -> None:
    if world.pet is None:
        return
    loudness = predict_loudness(world)
    world.pet.meters["noise"] += loudness
    if loudness >= THRESHOLD:
        world.pet.memes["worry"] += 1
        world.hero.memes["worry"] += 1
        world.say(
            "The crossing bell rang loud and clear, and the pet tucked in close, "
            "as if the sound had sharp little teeth."
        )


def apply_muffle(world: World) -> None:
    if not (world.pet and world.charm):
        return
    if muffle_helps(world, world.pet, world.charm):
        sig = ("muffle", world.pet.id)
        if sig in world.fired:
            return
        world.fired.add(sig)
        world.pet.meters["noise"] = max(0.0, world.pet.meters["noise"] - 2.0)
        world.pet.meters["calm"] += 2.0
        world.pet.memes["trust"] += 1.0
        world.hero.meters["safety"] += 1.0
        world.hero.memes["kindness"] += 1.0
        world.say(
            f"The {world.charm.label} shimmered, and the loud ringing turned soft, "
            f"like snow falling on a quilt."
        )


def apply_dialogue_resolution(world: World) -> None:
    if not (world.pet and world.hero and world.charm):
        return
    if world.pet.meters["calm"] < THRESHOLD:
        return
    sig = ("resolution", world.hero.id)
    if sig in world.fired:
        return
    world.fired.add(sig)
    world.hero.memes["delight"] += 1.0
    world.pet.memes["trust"] += 1.0
    world.say(
        f'"There," said {world.hero.id}, "the {world.pet.label} can breathe easy now." '
        f'And the pet answered with a happy little {world.pet.magical_response}.'
    )


def propagate(world: World) -> None:
    apply_noise(world)
    apply_muffle(world)
    apply_dialogue_resolution(world)


# ---------------------------------------------------------------------------
# Narrative
# ---------------------------------------------------------------------------

def introduce(world: World) -> None:
    hero = world.hero
    pet = world.pet
    guardian = world.guardian
    world.say(
        f"Once, at {world.place.name}, there lived a {hero.pronoun('subject')} little {hero.type} named {hero.id}, "
        f"who was {hero.traits[0]} and always watched over {hero.pronoun('possessive')} {pet.label}."
    )
    world.say(
        f"The pet was {pet.phrase}, and {hero.id} loved {pet.pronoun('object')} as if {pet.pronoun('object')} were a tiny crown jewel."
    )
    world.say(
        f"{hero.id}'s {guardian.type} had brought along {CHARM.phrase}, because fairy roads can be kind, but loud bells can still startle tender ears."
    )


def arrival(world: World) -> None:
    world.para()
    world.say(
        f"At the railroad crossing, the signal light blinked red and the gate stood like a painted arm across the road."
    )
    world.say(
        f"{world.hero.id} and {world.guardian.id} waited beside the track, and the pet peered toward the rails with worried eyes."
    )


def dialogue_turn(world: World) -> None:
    world.para()
    world.say(
        f'"Do not fear," said {world.hero.id}. "I have a {CHARM.label}, and I will use it to help you."'
    )
    world.say(
        f'"Will it make the bell less fierce?" asked the pet, with a tiny tremble in {world.pet.pronoun("possessive")} whiskers.'
    )
    world.say(
        f'"Aye," said the guardian. "Magic is best when it keeps the small and kind things safe."'
    )


def ending(world: World) -> None:
    world.para()
    world.say(
        f"The charm glowed warm, the bell's clamor softened, and the pet pressed close without flinching."
    )
    world.say(
        f"By the time the gate lifted, {world.hero.id} was smiling, {world.pet.id} was calm, and the crossing looked less like a warning and more like a doorway in a storybook."
    )


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        traits=[params.trait, "gentle"],
    ))
    guardian = world.add(Entity(
        id="Guardian",
        kind="character",
        type=params.guardian,
        label=f"the {params.guardian}",
        traits=["watchful"],
    ))
    pet_cfg = _safe_lookup(PETS, params.pet)
    pet = world.add(Entity(
        id=pet_cfg.species,
        kind="pet",
        type=pet_cfg.species,
        label=pet_cfg.label,
        phrase=pet_cfg.phrase,
        owner=hero.id,
        magical=True,
    ))
    charm = world.add(Entity(
        id=CHARM.id,
        kind="thing",
        type="charm",
        label=CHARM.label,
        phrase=CHARM.phrase,
        magical=True,
        carries=set(CHARM.grants),
    ))

    world.hero = hero
    world.guardian = guardian
    world.pet = pet
    world.charm = charm

    world.facts.update(place=place, pet=pet_cfg, charm=CHARM, hero=hero, guardian=guardian)

    introduce(world)
    arrival(world)
    propagate(world)
    dialogue_turn(world)
    propagate(world)
    ending(world)
    propagate(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    hero = world.hero
    pet = world.pet
    return [
        f"Write a fairy tale about a child named {hero.id} and a {pet.label} at a railroad crossing, with a little magic and dialogue.",
        f"Tell a gentle story where a {pet.label} gets nervous at the railroad crossing until a muffle charm makes the noise soft.",
        f"Create a short child-friendly tale in which magic and conversation help a pet feel safe beside the railroad crossing gate.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = world.hero
    pet = world.pet
    guardian = world.guardian
    return [
        QAItem(
            question=f"Who was the story about at the railroad crossing?",
            answer=f"It was about {hero.id}, {guardian.label}, and a small {pet.label} who needed help staying calm."
        ),
        QAItem(
            question=f"What magical thing helped the pet feel better?",
            answer=f"The {CHARM.label} softened the loud sound from the crossing bell and helped the pet feel safe."
        ),
        QAItem(
            question=f"Why did the pet worry at first?",
            answer=f"The crossing bell was loud, and the pet had tender ears that did not like the noise."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the pet calm and close by, while {hero.id} smiled as the gate lifted."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a railroad crossing?",
            answer="A railroad crossing is a place where a road crosses railroad tracks, and lights or gates help keep people safe."
        ),
        QAItem(
            question="What does a muffle charm do in a fairy tale?",
            answer="A muffle charm is a magical thing that makes loud sounds softer or quieter."
        ),
        QAItem(
            question="Why do pets sometimes need comfort near loud places?",
            answer="Pets can hear very well, so loud bells or crashes may scare them and make them need a calm friend nearby."
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(railroad_crossing).
pet(cat).
pet(dog).
charm(muffle).

at(place,railroad_crossing).

loud(place,railroad_crossing).
pet_sensitive(cat).
pet_sensitive(dog).

needs_muffle(P) :- pet(P), pet_sensitive(P), loud(place,railroad_crossing).
safe(P) :- pet(P), not needs_muffle(P).
safe(P) :- pet(P), charm(muffle).

% The compatible story requires a loud crossing, a sensitive pet, and a muffle charm.
valid_story(place, railroad_crossing, pet(P), charm(muffle)) :- pet(P), pet_sensitive(P), loud(place,railroad_crossing).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("place", "railroad_crossing"),
        asp.fact("loud", "place", "railroad_crossing"),
        asp.fact("charm", "muffle"),
    ]
    for pet in PETS:
        lines.append(asp.fact("pet", pet))
        lines.append(asp.fact("pet_sensitive", pet))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_story_keys())
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


def valid_story_keys() -> list[tuple]:
    out = []
    for pet in PETS:
        out.append(("place", "railroad_crossing", "pet", pet))
    return out


# ---------------------------------------------------------------------------
# Story generation interface
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale railroad crossing storyworld with pet and muffle magic.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--pet", choices=list(PETS))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--guardian", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or "railroad_crossing"
    pet = getattr(args, "pet", None) or rng.choice(list(PETS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    guardian = getattr(args, "guardian", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, pet=pet, name=name, gender=gender, guardian=guardian, trait=trait)


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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        lines.append(
            f"{e.id}: kind={e.kind} type={e.type} meters={{{', '.join(f'{k}={v}' for k, v in e.meters.items() if v)}}} "
            f"memes={{{', '.join(f'{k}={v}' for k, v in e.memes.items() if v)}}}"
        )
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        for s in stories:
            print(s)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="railroad_crossing", pet="cat", name="Mira", gender="girl", guardian="mother", trait="gentle"),
            StoryParams(place="railroad_crossing", pet="dog", name="Theo", gender="boy", guardian="father", trait="curious"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
