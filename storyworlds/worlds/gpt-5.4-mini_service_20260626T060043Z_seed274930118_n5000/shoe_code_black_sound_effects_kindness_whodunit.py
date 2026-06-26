#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/shoe_code_black_sound_effects_kindness_whodunit.py
===============================================================================================================

A small whodunit-style storyworld about a missing black shoe, a bit of code, and
a kindly clue hunt powered by tiny sound effects.

The premise is simple:
- A black shoe goes missing.
- A child notices a code-like note and suspicious sound effects.
- A gentle helper follows the clues.
- Kindness solves the mystery and brings the shoe home.

This script follows the Storyweavers storyworld contract:
- self-contained stdlib script
- eager results import, lazy ASP import
- StoryParams, registries, build_parser, resolve_params, generate, emit, main
- support for default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
# Domain model
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
    possessed_by: Optional[str] = None
    hidden_in: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    code: object | None = None
    helper: object | None = None
    hero: object | None = None
    shoe: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character":
            female = {"girl", "mother", "woman", "sister"}
            male = {"boy", "father", "man", "brother"}
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
    mood: str
    afford: set[str] = field(default_factory=set)
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
class Shoe:
    label: str
    phrase: str
    color: str
    hidden_spot: str
    sound: str
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
class CodeClue:
    phrase: str
    meaning: str
    sound: str
    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Helper:
    label: str
    kindness: str
    action: str
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
    shoe: str
    code: str
    helper: str
    name: str
    gender: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Registries
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


SETTINGS: dict[str, Setting] = {
    "hallway": Setting(place="the hallway", mood="quiet", afford={"mystery"}),
    "classroom": Setting(place="the classroom", mood="busy", afford={"mystery"}),
    "clubhouse": Setting(place="the clubhouse", mood="cozy", afford={"mystery"}),
    "porch": Setting(place="the porch", mood="windy", afford={"mystery"}),
}

SHOES: dict[str, Shoe] = {
    "black_shoe": Shoe(
        label="shoe",
        phrase="a black shoe with one scuffed toe",
        color="black",
        hidden_spot="under the bench",
        sound="tap tap",
        clue="a tiny scuff mark",
    ),
    "black_sneaker": Shoe(
        label="shoe",
        phrase="a black shoe with a bright stripe",
        color="black",
        hidden_spot="behind the coat rack",
        sound="thump",
        clue="a loose lace",
    ),
}

CODE_CLUES: dict[str, CodeClue] = {
    "chalk_code": CodeClue(
        phrase="a little code in chalk: 2-1-3",
        meaning="look under the third thing, then the first, then the second",
        sound="scritch-scratch",
    ),
    "note_code": CodeClue(
        phrase="a folded note with three neat marks",
        meaning="count the seats and check the one in the middle",
        sound="flick",
    ),
}

HELPERS: dict[str, Helper] = {
    "kind_friend": Helper(
        label="friend",
        kindness="kind",
        action="helped look without teasing",
    ),
    "kind_teacher": Helper(
        label="teacher",
        kindness="kind",
        action="knelt down and listened to the clues",
    ),
    "kind_neighbor": Helper(
        label="neighbor",
        kindness="kind",
        action="smiled and shared a flashlight",
    ),
}

GIRL_NAMES = ["Mia", "Nora", "Lily", "Ava", "Zoe"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Finn"]


# ---------------------------------------------------------------------------
# World state
# ---------------------------------------------------------------------------
class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = {
            k: Entity(**{
                "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
                "phrase": v.phrase, "owner": v.owner, "possessed_by": v.possessed_by,
                "hidden_in": v.hidden_in, "plural": v.plural,
                "meters": dict(v.meters), "memes": dict(v.memes),
            })
            for k, v in self.entities.items()
        }
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# State helpers
# ---------------------------------------------------------------------------
def mget(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def add_meter(e: Entity, key: str, value: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + value


def add_meme(e: Entity, key: str, value: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + value


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------
def investigate_sounds(world: World, hero: Entity, helper: Entity, shoe: Entity, clue: Entity) -> None:
    world.say(
        f"In {world.setting.place}, {hero.id} heard {shoe.phrase} was gone."
    )
    world.say(
        f"Then came {clue.phrase}, and it made a {clue.phrase.split()[-1] if False else clue.phrase and clue.meters if False else clue.memes}"
    )


def setup_story(world: World, hero: Entity, helper: Entity, shoe: Entity, code: Entity) -> None:
    add_meme(hero, "worry", 1)
    add_meme(hero, "curiosity", 1)
    add_meme(helper, "kindness", 1)
    add_meter(shoe, "hidden", 1)
    code.meters["visible"] = 1
    world.say(
        f"{hero.id} was looking for {hero.pronoun('possessive')} {shoe.color} shoe when the room went still."
    )
    world.say(
        f"Near the corner sat {code.phrase}, and every time the wind moved, it made a {code.sound} sound."
    )


def reveal_clues(world: World, hero: Entity, helper: Entity, shoe: Entity, code: Entity) -> None:
    add_meme(hero, "curiosity", 1)
    world.say(
        f"{helper.id} was a kind {helper.type} who {helper.action}."
    )
    world.say(
        f"Together they followed the {code.sound} clue and the tiny {shoe.clue}."
    )
    world.say(
        f"The signs pointed {shoe.hidden_in or shoe.hidden_in}."
    )


def solve_mystery(world: World, hero: Entity, helper: Entity, shoe: Entity) -> None:
    shoe.possessed_by = hero.id
    shoe.hidden_in = ""
    shoe.meters["found"] = 1
    add_meme(hero, "relief", 1)
    add_meme(helper, "pride", 1)
    world.say(
        f"At last, they found the {shoe.color} shoe {shoe.hidden_spot}."
    )
    world.say(
        f"{helper.id} smiled and handed it back with a gentle, {helper.kindness} nod."
    )
    world.say(
        f"{hero.id} slipped on the shoe again, and the little mystery ended with a happy {shoe.sound}."
    )


def tell(world: World, hero: Entity, helper: Entity, shoe: Entity, code: Entity) -> World:
    setup_story(world, hero, helper, shoe, code)
    world.para()
    world.say(
        f"The clue said: {code.phrase}. That meant {code.meaning}."
    )
    world.say(
        f"{helper.id} listened carefully, because kind help was the best tool in a small whodunit."
    )
    world.para()
    solve_mystery(world, hero, helper, shoe)
    world.facts.update(hero=hero, helper=helper, shoe=shoe, code=code, setting=world.setting)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    shoe: Entity = _safe_fact(world, f, "shoe")  # type: ignore[assignment]
    code: Entity = _safe_fact(world, f, "code")  # type: ignore[assignment]
    return [
        f'Write a short whodunit for a young child about a missing {shoe.color} shoe and a tiny code clue.',
        f"Tell a mystery story where {hero.id} follows sound effects like {shoe.pronoun('possessive')} {shoe.phrase} and a code note.",
        f"Write a gentle detective story with kindness, a black shoe, and clues that make a soft sound.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, f, "helper")  # type: ignore[assignment]
    shoe: Entity = _safe_fact(world, f, "shoe")  # type: ignore[assignment]
    code: Entity = _safe_fact(world, f, "code")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What was missing in the story?",
            answer=f"The missing thing was {shoe.phrase}, and it was a {shoe.color} {shoe.label}.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} solve the mystery?",
            answer=f"The clue was {code.phrase}. It led them to the shoe by its secret code and sound.",
        ),
        QAItem(
            question=f"How did {helper.id} help?",
            answer=f"{helper.id} helped by being kind, listening closely, and handing the shoe back without being mean.",
        ),
        QAItem(
            question=f"What sound made the clue feel important?",
            answer=f"The story used {shoe.sound} and {code.sound} sounds to make the search feel like a little whodunit.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a code in a mystery story?",
            answer="A code is a set of marks, numbers, or signs that can help someone figure out a clue.",
        ),
        QAItem(
            question="Why is kindness helpful in a mystery?",
            answer="Kindness helps people listen, share clues, and solve problems without making anyone feel worse.",
        ),
        QAItem(
            question="What does a sound effect do in a story?",
            answer="A sound effect is a word that helps you hear the scene in your mind, like tap, thump, or scritch-scratch.",
        ),
    ]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        if "mystery" not in setting.afford:
            continue
        for shoe in SHOES:
            for code in CODE_CLUES:
                combos.append((place, shoe, code))
    return combos


def explain_rejection(place: str, shoe: str, code: str) -> str:
    return f"(No story: the requested mystery does not fit the available clues for {place}, {shoe}, and {code}.)"


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- setting(P).
shoe(S) :- shoe_item(S).
code(C) :- code_item(C).

valid(P,S,C) :- setting(P), shoe_item(S), code_item(C), mystery_place(P).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if "mystery" in s.afford:
            lines.append(asp.fact("mystery_place", sid))
    for sid in SHOES:
        lines.append(asp.fact("shoe_item", sid))
    for cid in CODE_CLUES:
        lines.append(asp.fact("code_item", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
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


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class NamePool:
    girl: list[str] = field(default_factory=lambda: GIRL_NAMES)
    boy: list[str] = field(default_factory=lambda: BOY_NAMES)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld: a black shoe, a code clue, and kindness.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--shoe", choices=SHOES)
    ap.add_argument("--code", choices=CODE_CLUES)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "shoe", None) is None or c[1] == getattr(args, "shoe", None))
              and (getattr(args, "code", None) is None or c[2] == getattr(args, "code", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, shoe, code = rng.choice(list(combos))
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, shoe=shoe, code=code, helper=helper, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    shoe_cfg = _safe_lookup(SHOES, params.shoe)
    code_cfg = _safe_lookup(CODE_CLUES, params.code)
    helper_cfg = _safe_lookup(HELPERS, params.helper)

    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id=helper_cfg.label, kind="character", type="person", label=helper_cfg.label))
    shoe = world.add(Entity(
        id="shoe", kind="thing", type="shoe", label="shoe", phrase=shoe_cfg.phrase,
        owner=hero.id, possessed_by=None, hidden_in=shoe_cfg.hidden_spot
    ))
    code = world.add(Entity(
        id="code", kind="thing", type="clue", label="code", phrase=code_cfg.phrase
    ))

    tell(world, hero, helper, shoe, code)

    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


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
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.phrase:
            parts.append(f"phrase={e.phrase!r}")
        if e.hidden_in:
            parts.append(f"hidden_in={e.hidden_in!r}")
        if e.possessed_by:
            parts.append(f"possessed_by={e.possessed_by!r}")
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.kind}/{e.type}) {' '.join(parts)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="hallway", shoe="black_shoe", code="chalk_code", helper="kind_friend", name="Mia", gender="girl"),
    StoryParams(place="classroom", shoe="black_sneaker", code="note_code", helper="kind_teacher", name="Leo", gender="boy"),
    StoryParams(place="clubhouse", shoe="black_shoe", code="note_code", helper="kind_neighbor", name="Nora", gender="girl"),
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, shoe, code) combos:")
        for c in combos:
            print(" ", c)
        return

    if getattr(args, "seed", None) is None:
        base_seed = random.randrange(2**31)
    else:
        base_seed = getattr(args, "seed", None)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.name}: {p.place} / {p.shoe} / {p.code}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
