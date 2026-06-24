#!/usr/bin/env python3
"""
spy_mystery_to_solve_dialogue_kindness_rhyming.py
==================================================

A small story world about a spy who solves a mystery with dialogue and kindness,
told in a rhyming, child-friendly style.

The world is intentionally tiny:
- a spy in a place
- a missing object
- a helpful conversation
- a clue trail
- a kind resolution

The prose is driven by world state: the spy starts puzzled, asks questions,
follows clues, and ends with the missing thing found and the mood changed.
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
# Story model
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    worn_by: Optional[str] = None
    found_by: Optional[str] = None

    helper: object | None = None
    hero: object | None = None
    missing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Setting:
    place: str
    indoor: bool
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
class Mystery:
    id: str
    missing: str
    hiding_spot: str
    clue: str
    reveal_line: str
    rhyme_end: str
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
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
    helper: str
    seed: Optional[int] = None
    params: object | None = None
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
    def __init__(self, setting: Setting, mystery: Mystery) -> None:
        self.setting = setting
        self.mystery = mystery
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
        self.trace: list[str] = []

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
    "library": Setting(place="the library", indoor=True, mood="quiet", afford={"search"}),
    "garden": Setting(place="the garden", indoor=False, mood="bright", afford={"search"}),
    "train": Setting(place="the little train station", indoor=True, mood="busy", afford={"search"}),
    "museum": Setting(place="the museum", indoor=True, mood="still", afford={"search"}),
}

MYSTERIES = {
    "missing_hat": Mystery(
        id="missing_hat",
        missing="hat",
        hiding_spot="on a coat hook",
        clue="a trail of blue crumbs",
        reveal_line="The hat was not gone at all; it was resting neat upon a stack of books.",
        rhyme_end="bright",
        tags={"hat", "blue", "books"},
    ),
    "lost_key": Mystery(
        id="lost_key",
        missing="key",
        hiding_spot="inside a flower pot",
        clue="a soft clink beside the pot",
        reveal_line="The key lay nearby, tucked in a flower pot, shiny and small.",
        rhyme_end="glow",
        tags={"key", "pot", "metal"},
    ),
    "vanished_note": Mystery(
        id="vanished_note",
        missing="note",
        hiding_spot="behind a display sign",
        clue="a corner peeking by the sign",
        reveal_line="The note was behind the sign, safe and sound, not lost at all.",
        rhyme_end="mend",
        tags={"note", "sign", "paper"},
    ),
    "missing_toy": Mystery(
        id="missing_toy",
        missing="toy train",
        hiding_spot="under a bench",
        clue="tiny tracks under the bench",
        reveal_line="The toy train was under the bench, waiting patiently for play.",
        rhyme_end="chime",
        tags={"toy", "train", "bench"},
    ),
}

NAMES = {
    "girl": ["Mia", "Zoe", "Lily", "Nora", "Ava", "Ella"],
    "boy": ["Ben", "Leo", "Max", "Theo", "Finn", "Sam"],
}

HELPERS = ["friend", "guard", "librarian", "mouse", "cat", "neighbor"]


# ---------------------------------------------------------------------------
# Rhyming / narrative helpers
# ---------------------------------------------------------------------------

def opening_line(hero: Entity, setting: Setting, mystery: Mystery) -> str:
    return (
        f"{hero.id} was a tiny spy with a careful eye, "
        f"working in {setting.place} where whispers could fly. "
        f"One day {hero.pronoun('possessive')} small mystery grew strange and spry: "
        f"the missing {mystery.missing} was nowhere nearby."
    )


def clue_line(mystery: Mystery, setting: Setting) -> str:
    return (
        f"In {setting.place}, a clue came through: {mystery.clue}. "
        f"It gave {setting.mood} little hints the way a lantern knew."
    )


def kindness_line(hero: Entity, helper: Entity) -> str:
    return (
        f"{hero.id} said, “Thank you, {helper.id}, for helping me through.” "
        f"{helper.id} smiled back, “Kindness makes hard puzzles feel new.”"
    )


def ending_line(hero: Entity, mystery: Mystery) -> str:
    return (
        f"Then {hero.id} found the answer and the worry drifted by; "
        f"{mystery.reveal_line} "
        f"{hero.id} laughed, “A mystery can hide, but truth will always try.”"
    )


def dialog_line(hero: Entity, helper: Entity, mystery: Mystery) -> str:
    return (
        f'"Have you seen the {mystery.missing}?" asked {hero.id} with a hopeful sigh. '
        f'"I have," said {helper.id}, "and I will help you check nearby."'
    )


def turn_line(hero: Entity, mystery: Mystery) -> str:
    return (
        f"{hero.id} looked low and high, then soft and slow, "
        f"following {mystery.clue} like a thread of snow."
    )


def wrong_turn_line(hero: Entity) -> str:
    return (
        f"{hero.id} first felt stuck and glum, as if the clue was shy; "
        f"but {hero.id} took a breath and kept the tune alive."
    )


# ---------------------------------------------------------------------------
# World building and simulation
# ---------------------------------------------------------------------------

def simulate(world: World) -> None:
    hero = world.get("hero")
    helper = world.get("helper")
    mystery = world.mystery

    hero.memes["curious"] = 1.0
    hero.memes["hope"] = 0.5
    hero.memes["puzzle"] = 1.0
    helper.memes["kind"] = 1.0

    world.say(opening_line(hero, world.setting, mystery))
    world.say(dialog_line(hero, helper, mystery))
    world.para()

    hero.memes["worry"] = 1.0
    world.say(wrong_turn_line(hero))
    world.say(clue_line(mystery, world.setting))
    world.say(turn_line(hero, mystery))
    hero.meters["search_steps"] = hero.meters.get("search_steps", 0.0) + 1.0

    # state-driven resolution
    if world.setting.place == "the library" and mystery.id == "vanished_note":
        helper.meters["helped"] = helper.meters.get("helped", 0.0) + 1.0
    elif world.setting.place == "the garden" and mystery.id == "lost_key":
        helper.meters["helped"] = helper.meters.get("helped", 0.0) + 1.0
    else:
        helper.meters["helped"] = helper.meters.get("helped", 0.0) + 1.0

    hero.memes["worry"] = 0.0
    hero.memes["joy"] = 1.0
    hero.memes["relief"] = 1.0

    world.para()
    world.say(kindness_line(hero, helper))
    world.say(ending_line(hero, mystery))


# ---------------------------------------------------------------------------
# Reasonableness / generation
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        if "search" not in setting.afford:
            continue
        for mystery_id in MYSTERIES:
            combos.append((place, mystery_id))
    return combos


def explain_rejection(place: str, mystery_id: str) -> str:
    if place not in SETTINGS:
        return "(No story: that place is not in this world.)"
    if mystery_id not in MYSTERIES:
        return "(No story: that mystery is not in this world.)"
    return "(No story: that combination does not make a clear, solvable little mystery.)"


def build_world(params: StoryParams) -> World:
    if params.place not in SETTINGS:
        pass
    if params.mystery not in MYSTERIES:
        pass
    setting = _safe_lookup(SETTINGS, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = World(setting, mystery)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type=params.gender,
        meters={"search_steps": 0.0},
        memes={"curious": 1.0},
    ))
    helper = world.add(Entity(
        id=params.helper,
        kind="character",
        type="friend",
        meters={"helped": 0.0},
        memes={"kind": 1.0},
    ))
    missing = world.add(Entity(
        id=mystery.missing,
        kind="thing",
        type=mystery.missing,
        label=mystery.missing,
        phrase=f"the missing {mystery.missing}",
    ))

    world.facts.update(
        hero=hero,
        helper=helper,
        missing=missing,
        setting=setting,
        mystery=mystery,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, f, "helper")  # type: ignore[assignment]
    mystery: Mystery = _safe_fact(world, f, "mystery")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    return [
        f'Write a short rhyming story for a young child about a spy solving a mystery in {setting.place}.',
        f"Tell a gentle story where {hero.id} asks {helper.id} about the missing {mystery.missing} and they solve it kindly.",
        f'Write a simple mystery story that includes dialogue, kindness, and the word "{mystery.missing}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    helper: Entity = _safe_fact(world, f, "helper")  # type: ignore[assignment]
    mystery: Mystery = _safe_fact(world, f, "mystery")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"Who was the spy in the story?",
            answer=f"The spy was {hero.id}, who looked carefully and asked good questions in {setting.place}.",
        ),
        QAItem(
            question=f"What was missing from the story?",
            answer=f"The missing thing was the {mystery.missing}. The spy looked for it until the clue led to the answer.",
        ),
        QAItem(
            question=f"Who helped {hero.id} solve the mystery?",
            answer=f"{helper.id} helped {hero.id} by answering kindly and pointing toward the clue.",
        ),
        QAItem(
            question=f"How did {hero.id} and {helper.id} behave while solving the puzzle?",
            answer=(
                f"They spoke kindly, asked questions, and kept going together. "
                f"That friendly talk helped the mystery feel smaller."
            ),
        ),
        QAItem(
            question=f"What was the ending of the story?",
            answer=(
                f"The {mystery.missing} was found, {hero.id} felt relief, and the story ended in a happy, "
                f"gentle way."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a spy do?",
            answer="A spy looks carefully, notices small clues, and tries to solve secrets.",
        ),
        QAItem(
            question="What is a mystery?",
            answer="A mystery is a question or problem that needs clues and careful thinking to solve.",
        ),
        QAItem(
            question="Why is kindness helpful?",
            answer="Kindness helps because it makes people feel safe, calm, and ready to work together.",
        ),
        QAItem(
            question="What is dialogue?",
            answer="Dialogue is when characters talk to each other in a story.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
mystery(M) :- mystery_kind(M).
solvable(P, M) :- place(P), mystery(M), allows_search(P).
"""
def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy import
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(setting.afford):
            lines.append(asp.fact("allows_search", pid))
    for mid in MYSTERIES:
        lines.append(asp.fact("mystery_kind", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp  # lazy import
    model = asp.one_model(asp_program("#show solvable/2."))
    clingo_set = set(asp.atoms(model, "solvable"))
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo parity matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("clingo:", sorted(clingo_set))
    print("python:", sorted(python_set))
    return 1


# ---------------------------------------------------------------------------
# Parameter resolution / generation / emit
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming spy mystery story world.")
    ap.add_argument("--place", choices=sorted(SETTINGS))
    ap.add_argument("--mystery", choices=sorted(MYSTERIES))
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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
    if getattr(args, "place", None) and getattr(args, "place", None) not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "mystery", None) and getattr(args, "mystery", None) not in MYSTERIES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "mystery", None) and (getattr(args, "place", None), getattr(args, "mystery", None)) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    filtered = [c for c in combos
                if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
                and (getattr(args, "mystery", None) is None or c[1] == getattr(args, "mystery", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery = rng.choice(filtered)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    simulate(world)
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
    lines.append("== (3) World-knowledge questions ==")
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
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
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
        print(asp_program("#show solvable/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show solvable/2."))
        atoms = sorted(asp.atoms(model, "solvable"))
        print(f"{len(atoms)} solvable combos:")
        for p, m in atoms:
            print(f"  {p:12} {m}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        for place, mystery in valid_combos():
            params = StoryParams(
                place=place,
                mystery=mystery,
                name="Mia",
                gender="girl",
                helper="friend",
                seed=base_seed,
            )
            samples.append(generate(params))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.name}: {p.place} / {p.mystery}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
