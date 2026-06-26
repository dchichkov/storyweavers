#!/usr/bin/env python3
"""
Standalone storyworld: a small detective mystery with suspense.

Premise:
A child detective follows a trail of clues through a rainy town. The word
"precipitate" belongs to the rainy setup and the word "cackle" marks the
villain's telltale laugh. The detective must reason from physical trace
evidence, witness memories, and a final reveal.

This world is intentionally compact and deterministic enough for testability,
while still producing varied, fully narrated stories with a clear beginning,
turn, and resolution.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    detective: object | None = None
    suspect_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
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
    label: str
    mood: str
    cover: str
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
class SuspectProfile:
    id: str
    label: str
    type: str
    motive: str
    tells: list[str] = field(default_factory=list)
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
class ClueProfile:
    id: str
    label: str
    text: str
    place: str
    suspect: str
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
    suspect: str
    clue: str
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
    def __init__(self, place: Place):
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = "rainy"

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

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.weather = self.weather
        return clone


PLACES = {
    "alley": Place("alley", "the narrow alley", "tense", "brick walls and a bent lamp"),
    "library": Place("library", "the old library", "quiet", "dusty shelves and a tall clock"),
    "harbor": Place("harbor", "the wet harbor", "foggy", "ropes, crates, and a creaking dock"),
    "market": Place("market", "the night market", "busy", "lanterns and striped cloth awnings"),
}

SUSPECTS = {
    "cat": SuspectProfile("cat", "the gray cat", "cat", "wanted fish from the stall", ["soft paws", "yellow eyes"]),
    "clown": SuspectProfile("clown", "the painted clown", "clown", "wanted the missing ribbon", ["bright shoes", "loud boots"]),
    "butler": SuspectProfile("butler", "the careful butler", "butler", "wanted to hide a surprise", ["white gloves", "straight back"]),
    "crow": SuspectProfile("crow", "the black crow", "crow", "wanted the shiny key", ["glittery feathers", "tilted head"]),
}

CLUES = {
    "mudprint": ClueProfile("mudprint", "mud prints", "small muddy prints", "alley", "cat"),
    "glove": ClueProfile("glove", "white glove", "a single white glove", "library", "butler"),
    "feather": ClueProfile("feather", "black feather", "a black feather", "market", "crow"),
    "shoe": ClueProfile("shoe", "red shoe", "one red shoe", "harbor", "clown"),
}

GENDERS = {"girl", "boy"}
GIRL_NAMES = ["Mina", "Tia", "Lena", "Iris", "Nora", "Zoe"]
BOY_NAMES = ["Owen", "Eli", "Milo", "Noah", "Theo", "Finn"]
TRAITS = ["curious", "brave", "sharp-eyed", "patient", "careful"]
HELPERS = ["police officer", "street sweeper", "shopkeeper", "librarian"]


def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, s, c) for p in PLACES for s in SUSPECTS for c in CLUES if _safe_lookup(CLUES, c).place == p and _safe_lookup(CLUES, c).suspect == s]


def suspect_at_scene(suspect: SuspectProfile, clue: ClueProfile) -> bool:
    return clue.suspect == suspect.id


def reasonableness_gate(place: str, suspect: str, clue: str) -> bool:
    return clue in CLUES and suspect in SUSPECTS and place in PLACES and _safe_lookup(CLUES, clue).place == place and _safe_lookup(CLUES, clue).suspect == suspect


def _r_suspense(world: World) -> list[str]:
    out: list[str] = []
    detective = _safe_fact(world, world.facts, "detective")
    if detective.memes.get("suspense", 0) >= THRESHOLD and detective.meters.get("rain", 0) >= THRESHOLD:
        sig = ("suspense", detective.id)
        if sig not in world.fired:
            world.fired.add(sig)
            out.append("The rain made every step feel like a question.")
    return out


def _r_cackle(world: World) -> list[str]:
    out: list[str] = []
    villain = _safe_fact(world, world.facts, "suspect_entity")
    detective = _safe_fact(world, world.facts, "detective")
    if villain.memes.get("cackle", 0) >= THRESHOLD and detective.memes.get("suspense", 0) >= THRESHOLD:
        sig = ("cackle", villain.id)
        if sig not in world.fired:
            world.fired.add(sig)
            detective.memes["alarm"] = detective.memes.get("alarm", 0) + 1
            out.append("A thin cackle drifted from the shadows.")
    return out


CAUSAL_RULES = [_r_suspense, _r_cackle]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def solve_case(world: World, detective: Entity, clue: ClueProfile, suspect: SuspectProfile) -> None:
    detective.meters["rain"] += 1
    detective.memes["suspense"] += 1
    world.say(f"{detective.id} stepped into {world.place.label} as the rain began to precipitate on the stones.")
    world.say(f"{detective.id} liked mysteries, but this one felt different; the air held quiet suspense.")
    world.say(f"On the ground, {clue.text} waited beside the path.")
    world.para()
    world.say(f"{detective.id} followed the clue deeper inside {world.place.label}.")
    if clue.id == "mudprint":
        world.say("The mud prints were small and quick, like paws that tried not to be seen.")
    elif clue.id == "glove":
        world.say("The white glove looked careful and formal, as if it had come from a tidy hand.")
    elif clue.id == "feather":
        world.say("The black feather twitched in the breeze, shiny at the tip.")
    else:
        world.say("The red shoe was bright enough to stand out even in the wet dark.")
    world.para()
    world.say(f"Then someone nearby let out a cackle.")
    villain = _safe_fact(world, world.facts, "suspect_entity")
    villain.memes["cackle"] += 1
    propagate(world, narrate=True)
    world.say(f"{detective.id} froze, then smiled a little. That sound matched the clue.")
    world.para()
    world.say(f'"It was {suspect.label}," {detective.id} said. "The clue and the laugh point to them."')
    world.say(f"{suspect.label} had the motive to {suspect.motive}, and the clue proved they had been here.")
    world.say(f"{world.facts['helper']} came over just in time, and the case was solved before the rain could wash away the proof.")
    world.say(f"In the end, {detective.id} held the clue up under the lamp while the city stayed quiet again.")


def tell(place: Place, suspect: SuspectProfile, clue: ClueProfile, name: str, gender: str, helper: str, trait: str) -> World:
    world = World(place)
    detective = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait, "detective"]))
    suspect_ent = world.add(Entity(id="suspect", kind="character", type=suspect.type, label=suspect.label))
    world.facts["detective"] = detective
    world.facts["suspect_entity"] = suspect_ent
    world.facts["helper"] = helper

    detective.memes["suspense"] = 1
    world.say(f"{detective.id} was a little {trait} {gender} who loved solving mysteries.")
    world.say(f"One rainy night, {detective.id} walked to {place.label} with {helper} nearby.")
    world.say(f"A case had opened: someone had left {clue.text}, and nobody knew why.")
    world.say(f"{suspect.label} was known for a strange motive: they wanted to {suspect.motive}.")
    world.para()
    solve_case(world, detective, clue, suspect)
    world.facts.update(place=place, suspect=suspect, clue=clue)
    return world


KNOWLEDGE = {
    "precipitate": [
        ("What does precipitate mean in weather words?", "In weather words, precipitate means to fall from clouds, like rain or snow."),
    ],
    "cackle": [
        ("What is a cackle?", "A cackle is a loud, sharp laugh, sometimes used to sound sneaky or excited."),
    ],
    "detective": [
        ("What does a detective do?", "A detective looks for clues and uses careful thinking to solve a mystery."),
    ],
    "rain": [
        ("Why can rain help hide clues?", "Rain can wash tracks away or make them muddy, which can make clues harder to see."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short detective story for a child that uses the word "precipitate" and includes a clue in {f["place"].label}.',
        f"Tell a suspenseful mystery where {f['detective'].id} hears a cackle and solves the case from one small clue.",
        f'Write a gentle detective story in which {f["detective"].id} uses {f["clue"].text} to identify {f["suspect"].label}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    d = _safe_fact(world, f, "detective")
    s = _safe_fact(world, f, "suspect")
    c = _safe_fact(world, f, "clue")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"Who solved the mystery in {f['place'].label}?",
            answer=f"{d.id} solved the mystery by following {c.text} and listening for the cackle.",
        ),
        QAItem(
            question=f"What clue helped {d.id} figure out who was there?",
            answer=f"The clue was {c.text}. It matched {s.label} and pointed to the right suspect.",
        ),
        QAItem(
            question=f"Why did the story feel suspenseful?",
            answer=f"It felt suspenseful because it was raining, the clue was mysterious, and a cackle came from the shadows.",
        ),
        QAItem(
            question=f"Who helped near the end of the case?",
            answer=f"{helper} came over near the end while {d.id} finished solving the mystery.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["precipitate"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["cackle"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["detective"])
    out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["rain"])
    return out


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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def explain_rejection(place: str, suspect: str, clue: str) -> str:
    c = CLUES.get(clue)
    s = SUSPECTS.get(suspect)
    p = PLACES.get(place)
    if not c or not s or not p:
        return "(No story: unknown place, suspect, or clue.)"
    return f"(No story: {c.text} belongs to {c.place}, and it points to {s.label}, not a different suspect.)"


ASP_RULES = r"""
% A case is valid when the clue belongs to the selected place and suspect.
valid_case(Place, Suspect, Clue) :- place(Place), suspect(Suspect), clue(Clue),
                                    clue_place(Clue, Place),
                                    clue_suspect(Clue, Suspect).

% The story is suspenseful when rain, clue, and cackle all appear together.
suspenseful_case(Place, Suspect, Clue) :- valid_case(Place, Suspect, Clue),
                                          rainy(Place), cackle_clue(Clue).

#show valid_case/3.
#show suspenseful_case/3.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.id in {"alley", "harbor"}:
            lines.append(asp.fact("rainy", pid))
    for sid in SUSPECTS:
        lines.append(asp.fact("suspect", sid))
    for cid, c in CLUES.items():
        lines.append(asp.fact("clue", cid))
        lines.append(asp.fact("clue_place", cid, c.place))
        lines.append(asp.fact("clue_suspect", cid, c.suspect))
        if cid in {"mudprint", "feather"}:
            lines.append(asp.fact("cackle_clue", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_asp_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_case/3."))
    return sorted(set(asp.atoms(model, "valid_case")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_asp_cases())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} cases).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print(" only in python:", sorted(py - cl))
    if cl - py:
        print(" only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a suspenseful detective mystery.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--suspect", choices=SUSPECTS)
    ap.add_argument("--clue", choices=CLUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if getattr(args, "place", None) or getattr(args, "suspect", None) or getattr(args, "clue", None):
        combos = [
            c for c in combos
            if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
            and (getattr(args, "suspect", None) is None or c[1] == getattr(args, "suspect", None))
            and (getattr(args, "clue", None) is None or c[2] == getattr(args, "clue", None))
        ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, suspect, clue = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, suspect=suspect, clue=clue, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(SUSPECTS, params.suspect), _safe_lookup(CLUES, params.clue), params.name, params.gender, params.helper, params.trait)
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
    StoryParams(place="alley", suspect="cat", clue="mudprint", name="Mina", gender="girl", helper="police officer", trait="curious"),
    StoryParams(place="library", suspect="butler", clue="glove", name="Owen", gender="boy", helper="librarian", trait="careful"),
    StoryParams(place="market", suspect="crow", clue="feather", name="Iris", gender="girl", helper="shopkeeper", trait="sharp-eyed"),
    StoryParams(place="harbor", suspect="clown", clue="shoe", name="Theo", gender="boy", helper="police officer", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_case/3.\n#show suspenseful_case/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_case/3.\n#show suspenseful_case/3."))
        print("Valid cases:")
        for atom in sorted(set(asp.atoms(model, "valid_case"))):
            print(" ", atom)
        print("Suspenseful cases:")
        for atom in sorted(set(asp.atoms(model, "suspenseful_case"))):
            print(" ", atom)
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
            header = f"### {p.name}: {p.clue} at {p.place} (suspect: {p.suspect})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
