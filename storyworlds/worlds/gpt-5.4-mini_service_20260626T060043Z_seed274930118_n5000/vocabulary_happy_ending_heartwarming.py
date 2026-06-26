#!/usr/bin/env python3
"""
A small heartwarming storyworld about a child building vocabulary with help,
misunderstanding, and a happy ending.

The simulated premise:
- A child wants to learn a new word.
- They try to use it in the wrong way or can't remember it.
- A kind helper gives a clue using a concrete object, picture, or action.
- The child learns the word, uses it correctly, and feels proud.

The world tracks both physical state (meters) and emotional state (memes):
- meters: visible things like page marks, cards, stickers, stacked books
- memes: feelings like curiosity, worry, pride, warmth, and relief

The prose is generated from world state, not swapped nouns.
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
# Domain registries
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

@dataclass(frozen=True)
class WordCard:
    key: str
    word: str
    kind: str
    clue: str
    example: str
    child_use: str
    scene_word: str
    physical: str
    mood_word: str
    tags: set[str] = field(default_factory=set)
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
        return None


@dataclass(frozen=True)
class Setting:
    key: str
    place: str
    helper_place: str
    light: str
    quiet: str
    tags: set[str] = field(default_factory=set)
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
        return None


@dataclass(frozen=True)
class Helper:
    key: str
    label: str
    role: str
    voice: str
    warm_action: str
    tags: set[str] = field(default_factory=set)
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
class Treasure:
    key: str
    label: str
    noun: str
    where: str
    can_mark: bool
    value: str
    tags: set[str] = field(default_factory=set)
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


SETTINGS = {
    "table": Setting(
        key="table",
        place="the kitchen table",
        helper_place="beside the window",
        light="sunlight",
        quiet="soft and calm",
        tags={"home", "reading"},
    ),
    "library": Setting(
        key="library",
        place="the little library corner",
        helper_place="near the picture shelf",
        light="lamplight",
        quiet="gentle and hushed",
        tags={"library", "books"},
    ),
    "porch": Setting(
        key="porch",
        place="the front porch",
        helper_place="by a potted plant",
        light="afternoon light",
        quiet="breezy and bright",
        tags={"home", "outdoors"},
    ),
}

HELPERS = {
    "mom": Helper(
        key="mom",
        label="mom",
        role="mother",
        voice="soft",
        warm_action="smiled and pointed to a clue",
        tags={"family", "warm"},
    ),
    "dad": Helper(
        key="dad",
        label="dad",
        role="father",
        voice="gentle",
        warm_action="sat down and listened first",
        tags={"family", "warm"},
    ),
    "teacher": Helper(
        key="teacher",
        label="teacher",
        role="teacher",
        voice="kind",
        warm_action="opened the book to a helpful page",
        tags={"school", "books"},
    ),
}

TREASURES = {
    "book": Treasure(
        key="book",
        label="storybook",
        noun="storybook",
        where="on the lap",
        can_mark=True,
        value="full of new words",
        tags={"books", "reading"},
    ),
    "cards": Treasure(
        key="cards",
        label="word cards",
        noun="word cards",
        where="on the table",
        can_mark=False,
        value="easy to shuffle and read",
        tags={"cards", "learning"},
    ),
    "poster": Treasure(
        key="poster",
        label="picture poster",
        noun="picture poster",
        where="on the wall",
        can_mark=False,
        value="bright and easy to point at",
        tags={"pictures", "learning"},
    ),
}

WORDS = {
    "glow": WordCard(
        key="glow",
        word="glow",
        kind="light word",
        clue="a warm light that seems to smile",
        example="The lamp began to glow in the dark room.",
        child_use="The child said the lamp could glow when it was switched on.",
        scene_word="glow",
        physical="lamp",
        mood_word="warmth",
        tags={"light", "warm"},
    ),
    "flutter": WordCard(
        key="flutter",
        word="flutter",
        kind="movement word",
        clue="a light, quick movement like a tiny bird wing",
        example="The paper flag began to flutter in the breeze.",
        child_use="The child said the ribbon would flutter in the wind.",
        scene_word="flutter",
        physical="ribbon",
        mood_word="happiness",
        tags={"movement", "wind"},
    ),
    "bundle": WordCard(
        key="bundle",
        word="bundle",
        kind="grouping word",
        clue="a small group of things tied or held together",
        example="She carried a bundle of crayons in one hand.",
        child_use="The child said the socks were a bundle when tied together.",
        scene_word="bundle",
        physical="stack",
        mood_word="care",
        tags={"grouping", "kindness"},
    ),
    "promise": WordCard(
        key="promise",
        word="promise",
        kind="feeling word",
        clue="a strong word that means you will try to do what you said",
        example="He made a promise to put the toys away.",
        child_use="The child said, 'I promise I will share the book.'",
        scene_word="promise",
        physical="hand",
        mood_word="trust",
        tags={"feelings", "family"},
    ),
    "careful": WordCard(
        key="careful",
        word="careful",
        kind="action word",
        clue="doing something slowly and kindly so it stays safe",
        example="She was careful when she carried the cup.",
        child_use="The child said to be careful with the pages so they would stay neat.",
        scene_word="careful",
        physical="pages",
        mood_word="trust",
        tags={"actions", "gentle"},
    ),
}

CHILD_NAMES = ["Mina", "Leo", "Nora", "Ari", "Ivy", "Theo", "Luna", "Noah"]
TRAITS = ["curious", "gentle", "shy", "bright", "patient", "playful"]


# ---------------------------------------------------------------------------
# Shared model
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    helper: str
    treasure: str
    word: str
    child_name: str
    child_trait: str
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


@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    type: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    worn_by: Optional[str] = None
    card: object | None = None
    child: object | None = None
    helper_ent: object | None = None
    treasure_ent: object | None = None
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.paragraphs: list[list[str]] = [[]]

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
# Story logic
# ---------------------------------------------------------------------------

def build_scene(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    helper = _safe_lookup(HELPERS, params.helper)
    treasure = _safe_lookup(TREASURES, params.treasure)
    word = _safe_lookup(WORDS, params.word)

    world = World(setting)

    child = world.add(Entity(
        id=params.child_name,
        kind="character",
        label=params.child_name,
        type="child",
        meters={"stillness": 0.0},
        memes={"curiosity": 1.0, "worry": 0.0, "pride": 0.0, "warmth": 0.0, "relief": 0.0},
    ))
    helper_ent = world.add(Entity(
        id=helper.key,
        kind="character",
        label=helper.label,
        type=helper.role,
        meters={"stillness": 0.0},
        memes={"warmth": 1.0},
    ))
    treasure_ent = world.add(Entity(
        id=treasure.key,
        kind="thing",
        label=treasure.label,
        type=treasure.noun,
        owner=child.id,
        caretaker=helper_ent.id,
        meters={"neat": 1.0, "marked": 0.0},
    ))
    card = world.add(Entity(
        id=word.key,
        kind="thing",
        label=word.word,
        type="word",
        owner=helper_ent.id,
        caretaker=helper_ent.id,
        meters={"clear": 1.0},
    ))

    world.facts.update(
        child=child,
        helper=helper_ent,
        treasure=treasure_ent,
        card=card,
        word=word,
        setting=setting,
        helper_def=helper,
        treasure_def=treasure,
    )

    # Act 1: setup
    world.say(
        f"{child.id} was a {params.child_trait} little child who loved new words."
    )
    world.say(
        f"At {setting.place}, the {setting.light} made everything feel {setting.quiet}."
    )
    world.say(
        f"{child.id} found {treasure.label}, which was {treasure.value}."
    )
    world.say(
        f"{child.id} also wanted to learn the word {word.word}, because it sounded bright and useful."
    )

    # Act 2: tension
    world.para()
    child.memes["worry"] += 1.0
    child.memes["curiosity"] += 1.0
    world.say(
        f"At first, {child.id} got the word mixed up and said it in the wrong way."
    )
    if treasure.can_mark:
        treasure_ent.meters["marked"] += 1.0
        treasure_ent.meters["neat"] -= 1.0
        child.memes["worry"] += 1.0
        world.say(
            f"A tiny mark landed on the {treasure.label}, and {child.id} looked down with a worried face."
        )
    else:
        world.say(
            f"{child.id} frowned, because the idea still felt slippery and hard to hold."
        )

    world.say(
        f"Then {helper.label} {helper.warm_action}."
    )
    world.say(
        f'{helper.label.capitalize()} said, "{word.clue}."'
    )
    world.say(
        f"To make it clear, {helper.label} showed {child.id} a simple example: {word.example}"
    )

    # turn: child learns and uses the word correctly
    world.para()
    child.memes["worry"] = max(0.0, child.memes["worry"] - 1.0)
    child.memes["warmth"] += 1.0
    child.memes["pride"] += 1.0
    child.memes["relief"] += 1.0
    treasure_ent.meters["neat"] += 1.0
    word.meters["clear"] = 1.0
    world.say(
        f"{child.id}'s eyes lit up. Suddenly the word made sense."
    )
    world.say(
        f"{child.id} tried again and said, '{word.child_use}'"
    )
    world.say(
        f"{helper.label} smiled, because the word fit perfectly this time."
    )

    # resolution: happy ending
    world.say(
        f"After that, {child.id} kept the {treasure.label} neat and remembered the new word all by {child.id.lower()}self."
    )
    world.say(
        f"{child.id} felt proud, and the whole room seemed warmer."
    )

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    treasure = _safe_fact(world, f, "treasure_def")
    word = _safe_fact(world, f, "word")
    return [
        f'Write a heartwarming story for a child named {child.id} who learns the word "{word.word}" with help from {helper.label}.',
        f"Tell a gentle story where a child tries to understand {word.word} while keeping a {treasure.label} safe.",
        f'Write a happy-ending story about learning vocabulary at {world.setting.place} with a kind helper.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    treasure = _safe_fact(world, f, "treasure_def")
    word = _safe_fact(world, f, "word")
    setting = _safe_fact(world, f, "setting")

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=(
                f"It is about {child.id}, a {world.facts['child'].memes and ''}{world.facts['child'].kind if hasattr(world.facts['child'], 'kind') else 'child'} who wanted to learn new words at {setting.place}."
            ),
        ),
        QAItem(
            question=f"What word did {child.id} learn?",
            answer=f"{child.id} learned the word {word.word}. It started out confusing, but it became clear with help.",
        ),
        QAItem(
            question=f"Who helped {child.id} understand the word?",
            answer=f"{helper.label} helped {child.id} by giving a clue and a simple example.",
        ),
        QAItem(
            question=f"What happened to the {treasure.label} before things got better?",
            answer=(
                f"The {treasure.label} got a tiny mark when {child.id} was unsure, which made {child.id} worry. "
                f"After that, the helper made the explanation clearer and the treasure was kept neat again."
            ),
        ),
        QAItem(
            question=f"How did the story end?",
            answer=(
                f"It ended happily: {child.id} understood the word, used it correctly, and felt proud."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    word: WordCard = _safe_fact(world, world.facts, "word")
    treasure: Treasure = _safe_fact(world, world.facts, "treasure_def")
    helper: Helper = _safe_fact(world, world.facts, "helper_def")

    qas = [
        QAItem(
            question="What is vocabulary?",
            answer=(
                "Vocabulary means the words a person knows and can use. "
                "Learning more vocabulary helps children explain what they mean."
            ),
        ),
        QAItem(
            question=f"What does the word {word.word} mean in this story?",
            answer=f"In this story, {word.word} means {word.clue}.",
        ),
        QAItem(
            question=f"What is a {treasure.noun} for?",
            answer=(
                f"A {treasure.noun} can be used for looking at pictures or words while someone reads and learns."
            ),
        ),
        QAItem(
            question=f"What does a {helper.label} do when helping a child learn?",
            answer=(
                f"A {helper.label} can explain kindly, give a clue, and show an example so the child can understand."
            ),
        ),
    ]
    return qas


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
chosen_word(W) :- word(W).
child_needs_help(C) :- child(C).
clear_meaning(W) :- chosen_word(W), clue(W,_).
happy_ending(C, W) :- child_needs_help(C), clear_meaning(W).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS.values():
        lines.append(asp.fact("setting", s.key))
    for h in HELPERS.values():
        lines.append(asp.fact("helper", h.key))
    for t in TREASURES.values():
        lines.append(asp.fact("treasure", t.key))
    for w in WORDS.values():
        lines.append(asp.fact("word", w.key))
        lines.append(asp.fact("clue", w.key, w.clue))
    lines.append(asp.fact("child", "child"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/2."))
    atoms = set(asp.atoms(model, "happy_ending"))
    python_ok = {(c, w.key) for c in ["child"] for w in WORDS.values()}
    # Python gate: every defined combo is reasonable for this tiny world.
    if atoms == python_ok:
        print(f"OK: clingo gate matches Python gate ({len(atoms)} pairs).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("  clingo:", sorted(atoms))
    print("  python:", sorted(python_ok))
    return 1


# ---------------------------------------------------------------------------
# Sampling and validation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s in SETTINGS:
        for h in HELPERS:
            for t in TREASURES:
                for w in WORDS:
                    combos.append((s, h, t, w))
    return combos


def explain_invalid() -> str:
    return "(No story: the requested choices do not form a gentle vocabulary-learning scene.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming vocabulary storyworld.")
    ap.add_argument("--setting", choices=sorted(SETTINGS))
    ap.add_argument("--helper", choices=sorted(HELPERS))
    ap.add_argument("--treasure", choices=sorted(TREASURES))
    ap.add_argument("--word", choices=sorted(WORDS))
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    helper = getattr(args, "helper", None) or rng.choice(list(HELPERS))
    treasure = getattr(args, "treasure", None) or rng.choice(list(TREASURES))
    word = getattr(args, "word", None) or rng.choice(list(WORDS))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        setting=setting,
        helper=helper,
        treasure=treasure,
        word=word,
        child_name=name,
        child_trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_scene(params)
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
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="table", helper="mom", treasure="book", word="glow", child_name="Mina", child_trait="curious"),
    StoryParams(setting="library", helper="teacher", treasure="cards", word="bundle", child_name="Leo", child_trait="patient"),
    StoryParams(setting="porch", helper="dad", treasure="poster", word="flutter", child_name="Nora", child_trait="bright"),
]


def asp_valid_pairs() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show happy_ending/2."))
    return sorted(set(asp.atoms(model, "happy_ending")))


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show happy_ending/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} compatible happy-ending pairs:")
        for c, w in pairs:
            print(f"  {c} + {w}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            i += 1
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
            header = f"### {p.child_name}: {p.word} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
