#!/usr/bin/env python3
"""
storyworlds/worlds/wrack_surprise_mystery.py
============================================

A small mystery storyworld about a wrack line on the shore, where a careful
search leads to a surprise.

Premise:
- A child loves exploring the wrack line at the beach.
- Something tiny and unexpected is hidden among the seaweed, shells, and driftwood.
- A gentle mystery unfolds: who put it there, and what is it?

The world model tracks:
- physical meters: curiosity, searched, found, hidden, surprise, worry
- emotional memes: excitement, wonder, trust, relief, suspense

The story is intentionally small and child-facing, with a clear beginning,
middle turn, and ending image.
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
# Core model
# ---------------------------------------------------------------------------

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
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    props: dict[str, str] = field(default_factory=dict)

    helper: object | None = None
    hero: object | None = None
    wrack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        gender = self.props.get("gender", "")
        if gender == "girl":
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if gender == "boy":
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class World:
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    w: object | None = None
    world: object | None = None
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
        import copy
        w = World()
        w.entities = copy.deepcopy(self.entities)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w
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
class Setting:
    place: str = "the wrack line"
    detail: str = "a narrow strip of seaweed, shells, and driftwood left by the tide"
    SETTING: object | None = None
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
class Clue:
    id: str
    label: str
    line: str
    hint: str
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
class Surprise:
    id: str
    label: str
    reveal: str
    joy: str
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
    name: str
    gender: str
    companion: str
    clue: str
    surprise: str
    seed: Optional[int] = None
    p: object | None = None
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


SETTING = Setting()

CLUES = {
    "blue_ribbon": Clue(
        id="blue_ribbon",
        label="a blue ribbon",
        line="a blue ribbon snagged on a piece of driftwood",
        hint="It looked like someone had tied it there on purpose.",
    ),
    "shell_mark": Clue(
        id="shell_mark",
        label="three little shells",
        line="three little shells set in a neat row",
        hint="The shells made a tiny trail like a message.",
    ),
    "footprint": Clue(
        id="footprint",
        label="a small footprint",
        line="a small footprint pressed in the damp sand beside the wrack",
        hint="Someone small had been there not long ago.",
    ),
    "bottle_note": Clue(
        id="bottle_note",
        label="a bottle note",
        line="a bottle with a rolled-up note tucked inside the wrack",
        hint="It was hidden where the tide could not easily reach it.",
    ),
}

SURPRISES = {
    "seashell_star": Surprise(
        id="seashell_star",
        label="a star-shaped shell",
        reveal="it was a star-shaped shell wrapped in soft blue cloth",
        joy="The child gasped because it was prettier than any ordinary shell.",
    ),
    "birthday_note": Surprise(
        id="birthday_note",
        label="a birthday note",
        reveal="it was a note that said, 'Surprise!' and showed a little birthday cake",
        joy="The child smiled because the mystery was really a birthday surprise.",
    ),
    "tiny_key": Surprise(
        id="tiny_key",
        label="a tiny brass key",
        reveal="it was a tiny brass key tied to a tag that said 'for the treasure box'",
        joy="The child felt a fizzy thrill because it hinted at another hidden treasure.",
    ),
}


GIRL_NAMES = ["Maya", "Luna", "Nora", "Ivy", "Zoe"]
BOY_NAMES = ["Eli", "Noah", "Finn", "Leo", "Theo"]
COMPANIONS = ["grandmother", "grandfather", "mother", "father", "older sister", "older brother"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A clue is suspicious if it appears at the wrack line.
suspicious(C) :- clue(C).

% A surprise is found when the search reaches the wrack and the hidden item is revealed.
found(S) :- surprise(S), hidden(S), searched(wrack).

% A valid story needs a clue and a surprise.
valid_story(C, S) :- clue(C), surprise(S).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("wrack", "wrack")]
    for cid in CLUES:
        lines.append(asp.fact("clue", cid))
    for sid in SURPRISES:
        lines.append(asp.fact("surprise", sid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    asp_pairs = sorted(set(asp.atoms(model, "valid_story")))
    py_pairs = sorted((c, s) for c in CLUES for s in SURPRISES)
    if asp_pairs == py_pairs:
        print(f"OK: clingo gate matches Python registry pairs ({len(py_pairs)}).")
        return 0
    print("MISMATCH between clingo and Python registries.")
    print("clingo:", asp_pairs)
    print("python:", py_pairs)
    return 1


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def build_world(params: StoryParams) -> World:
    if params.clue not in CLUES:
        pass
    if params.surprise not in SURPRISES:
        pass

    world = World()
    hero = world.add(Entity(
        id=params.name,
        kind="character",
        label=params.name,
        props={"gender": params.gender},
        meters={"curiosity": 0.0, "searched": 0.0},
        memes={"wonder": 0.0, "suspense": 0.0, "joy": 0.0, "relief": 0.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        label=params.companion,
        props={"gender": ""},
        meters={"searched": 0.0},
        memes={"trust": 0.0, "relief": 0.0},
    ))
    wrack = world.add(Entity(
        id="wrack",
        kind="place",
        label="the wrack line",
        phrase=SETTING.detail,
        meters={"hidden": 1.0},
    ))
    clue = _safe_lookup(CLUES, params.clue)
    surprise = _safe_lookup(SURPRISES, params.surprise)
    world.add(Entity(
        id=clue.id,
        kind="object",
        label=clue.label,
        phrase=clue.line,
        owner="wrack",
        meters={"hidden": 1.0},
        memes={"mystery": 1.0},
    ))
    world.add(Entity(
        id=surprise.id,
        kind="object",
        label=surprise.label,
        phrase=surprise.reveal,
        owner="wrack",
        meters={"hidden": 1.0, "surprise": 1.0},
        memes={"wonder": 1.0},
    ))
    world.facts.update(hero=hero, helper=helper, wrack=wrack, clue=clue, surprise=surprise)
    return world


def search(world: World) -> None:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    helper: Entity = _safe_fact(world, world.facts, "helper")
    clue: Clue = _safe_fact(world, world.facts, "clue")
    surprise: Surprise = _safe_fact(world, world.facts, "surprise")

    world.say(f"{hero.id} loved walking along {SETTING.place} because every tide left behind a new little puzzle.")
    world.say(f"One afternoon, {hero.id} and {helper.label} found {SETTING.detail}.")
    world.say(f"Near the wrack was {clue.line}. {clue.hint}")
    hero.meters["curiosity"] += 1
    hero.memes["suspense"] += 1
    helper.memes["trust"] += 1

    world.para()
    world.say(f"{hero.id} knelt down and searched the wrack more carefully.")
    hero.meters["searched"] += 1
    helper.meters["searched"] += 1
    hero.memes["wonder"] += 1
    world.say(f"The clues led {hero.id} to a small hidden pocket under the seaweed, where something waited quietly.")

    world.para()
    world.say(f"When {hero.id} lifted the last piece of wrack, the mystery turned into a surprise: {surprise.reveal}.")
    hero.meters["found"] += 1
    hero.meters["hidden"] += -1
    hero.memes["joy"] += 1
    hero.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.say(surprise.joy)
    world.say(f"{helper.label} smiled, and {hero.id} tucked the surprise safely in both hands while the tide whispered behind them.")


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    clue: Clue = _safe_fact(world, f, "clue")
    surprise: Surprise = _safe_fact(world, f, "surprise")
    return [
        f'Write a gentle mystery story for a young child about {hero.id} at the wrack line, with a clue like {clue.label}.',
        f"Tell a short suspenseful story where {hero.id} searches {SETTING.place} and discovers {surprise.label}.",
        f'Write a child-facing surprise mystery that includes the word "wrack" and ends with a happy reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    clue: Clue = _safe_fact(world, f, "clue")
    surprise: Surprise = _safe_fact(world, f, "surprise")

    return [
        QAItem(
            question=f"What did {hero.id} and {helper.label} find at {SETTING.place}?",
            answer=f"They found {SETTING.detail}, and that made the place feel like a mystery waiting to be solved.",
        ),
        QAItem(
            question=f"What clue helped {hero.id} start solving the mystery?",
            answer=f"The clue was {clue.line}. It looked unusual, so {hero.id} knew to look more closely.",
        ),
        QAItem(
            question=f"What was the surprise hidden in the wrack?",
            answer=f"The surprise was {surprise.reveal}. That is why the mystery ended with joy instead of worry.",
        ),
        QAItem(
            question=f"How did {hero.id} feel after the surprise was found?",
            answer=f"{hero.id} felt wonder, joy, and relief after the hidden thing was revealed.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is wrack on a beach?",
            answer="Wrack is the line of seaweed, shells, driftwood, and other things that the tide leaves behind on the shore.",
        ),
        QAItem(
            question="Why do mysteries make people curious?",
            answer="Mysteries make people curious because they want to know what happened and why something is hidden or unusual.",
        ),
        QAItem(
            question="What does surprise mean in a story?",
            answer="A surprise is something unexpected that makes the ending feel exciting or happy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== Prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== Story Q&A ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== World Q&A ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# Parameter handling
# ---------------------------------------------------------------------------

@dataclass
class Registry:
    setting: str = "wrack"
    clue: str = "blue_ribbon"
    surprise: str = "seashell_star"
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
    ap = argparse.ArgumentParser(description="A small wrack-line surprise mystery storyworld.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--clue", choices=sorted(CLUES))
    ap.add_argument("--surprise", choices=sorted(SURPRISES))
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
    clue = getattr(args, "clue", None) or rng.choice(sorted(CLUES))
    surprise = getattr(args, "surprise", None) or rng.choice(sorted(SURPRISES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    companion = getattr(args, "companion", None) or rng.choice(COMPANIONS)
    return StoryParams(name=name, gender=gender, companion=companion, clue=clue, surprise=surprise)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    search(world)
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
        print()
        print("--- trace ---")
        for e in sample.world.entities.values():
            meters = {k: v for k, v in e.meters.items() if v}
            memes = {k: v for k, v in e.memes.items() if v}
            print(f"{e.id}: kind={e.kind} meters={meters} memes={memes}")
    if qa:
        print()
        print(format_qa(sample))


# ---------------------------------------------------------------------------
# ASP helpers
# ---------------------------------------------------------------------------

def asp_valid_pairs() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        pairs = asp_valid_pairs()
        print(f"{len(pairs)} valid (clue, surprise) pairs:")
        for c, s in pairs:
            print(f"  {c}  {s}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for clue in sorted(CLUES):
            for surprise in sorted(SURPRISES):
                p = StoryParams(
                    name="Maya",
                    gender="girl",
                    companion="mother",
                    clue=clue,
                    surprise=surprise,
                )
                samples.append(generate(p))
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            s = generate(p)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
