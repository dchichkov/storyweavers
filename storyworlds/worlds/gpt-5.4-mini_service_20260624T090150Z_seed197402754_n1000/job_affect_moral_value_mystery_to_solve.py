#!/usr/bin/env python3
"""
storyworlds/worlds/job_affect_moral_value_mystery_to_solve.py
==============================================================

A small slice-of-life story world about a child's job, their changing affect,
a moral value to practice, and a tiny mystery to solve.

The seed idea is a gentle everyday tale: someone gets a simple job, notices
feelings shift while doing it, and solves a small mystery in a kind, honest way.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    used_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    entities: set[str] = field(default_factory=set)
    grownup: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "aunt"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man", "uncle"}:
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
    place: str = "the little community library"
    indoors: bool = True
    afford_job: set[str] = field(default_factory=set)
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
class Job:
    id: str
    label: str
    verb: str
    gerund: str
    task: str
    affect_start: str
    affect_turn: str
    affect_end: str
    clue_focus: str
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


@dataclass
class Mystery:
    id: str
    label: str
    missing: str
    clue: str
    reveal: str
    owner_role: str
    risk: str
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


@dataclass
class Value:
    id: str
    label: str
    action: str
    benefit: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_log: list[str] = []

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
        clone.entities = {k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "caretaker": v.caretaker,
            "used_by": v.used_by, "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in self.entities.items()}
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "library": Setting(place="the little community library", indoors=True, afford_job={"shelf", "desk"}),
    "cafe": Setting(place="the corner cafe", indoors=True, afford_job={"tray", "counter"}),
    "garden": Setting(place="the neighborhood garden shed", indoors=False, afford_job={"tools", "sorting"}),
}

JOBS = {
    "shelf_helper": Job(
        id="shelf_helper",
        label="shelf helper",
        verb="sort the returned books",
        gerund="sorting the returned books",
        task="put the books back in the right places",
        affect_start="proud",
        affect_turn="worried",
        affect_end="calm",
        clue_focus="a tiny paper star",
        tags={"job", "library", "sorting"},
    ),
    "tray_runner": Job(
        id="tray_runner",
        label="tray runner",
        verb="carry the cups",
        gerund="carrying cups",
        task="bring cups to the right tables",
        affect_start="excited",
        affect_turn="careful",
        affect_end="happy",
        clue_focus="a cup with blue stripes",
        tags={"job", "cafe", "serving"},
    ),
    "tool_sorter": Job(
        id="tool_sorter",
        label="tool sorter",
        verb="sort the garden tools",
        gerund="sorting the garden tools",
        task="place the tools where they belong",
        affect_start="curious",
        affect_turn="serious",
        affect_end="relieved",
        clue_focus="a small red ribbon",
        tags={"job", "garden", "sorting"},
    ),
}

MYSTERIES = {
    "missing_card": Mystery(
        id="missing_card",
        label="missing library card",
        missing="a library card with a cat sticker",
        clue="the card was tucked inside a returned picture book",
        reveal="it had slipped into the wrong book during the morning rush",
        owner_role="the librarian",
        risk="someone might think it was lost for good",
        tags={"library", "honesty"},
    ),
    "wrong_cups": Mystery(
        id="wrong_cups",
        label="mixed-up cups",
        missing="two cups that should have gone to different tables",
        clue="one cup had a blue stripe and the other had a tiny dent",
        reveal="the cups had been placed on the same tray by mistake",
        owner_role="the cafe owner",
        risk="a customer might wait for the wrong drink",
        tags={"cafe", "care"},
    ),
    "lost_ribbon": Mystery(
        id="lost_ribbon",
        label="lost ribbon",
        missing="a red ribbon tied around a seed packet",
        clue="the ribbon was caught on a rake handle",
        reveal="the ribbon had snagged when the tools were moved too fast",
        owner_role="the gardener",
        risk="a packet could be overlooked and left behind",
        tags={"garden", "attention"},
    ),
}

VALUES = {
    "honesty": Value(
        id="honesty",
        label="honesty",
        action="tell the truth right away",
        benefit="people can trust the helper and fix little mistakes quickly",
        tags={"truth", "library"},
    ),
    "care": Value(
        id="care",
        label="care",
        action="notice what belongs where",
        benefit="things end up in the right hands with less fuss",
        tags={"cafe", "kind"},
    ),
    "attention": Value(
        id="attention",
        label="attention",
        action="look closely before moving on",
        benefit="small signs are easier to spot before they turn into bigger problems",
        tags={"garden", "careful"},
    ),
}

GIRL_NAMES = ["Mina", "Lily", "Nora", "Ava", "June", "Tia"]
BOY_NAMES = ["Leo", "Ben", "Milo", "Ezra", "Owen", "Noah"]
TRAITS = ["gentle", "patient", "curious", "kind", "thoughtful", "quiet"]


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for job_id in setting.afford_job:
            for mystery_id, mystery in MYSTERIES.items():
                if place in mystery.tags:
                    combos.append((place, job_id, mystery_id))
    return combos


def explain_rejection(place: str, job_id: str, mystery_id: str) -> str:
    setting = _safe_lookup(SETTINGS, place)
    job = _safe_lookup(JOBS, job_id)
    mystery = _safe_lookup(MYSTERIES, mystery_id)
    return (
        f"(No story: {setting.place} fits {job.label}, but this mystery does not belong there. "
        f"The world needs a small, believable everyday puzzle, so this pairing is rejected.)"
    )


# ---------------------------------------------------------------------------
# Prose engine
# ---------------------------------------------------------------------------
def setup_story(world: World, hero: Entity, grownup: Entity, job: Job, mystery: Mystery, value: Value) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} who had a job as a {job.label} at {world.setting.place}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked the job because {job.gerund} made the room feel useful and neat."
    )
    world.say(
        f"But {hero.pronoun('possessive')} feelings were not the same all the time: in the morning {hero.pronoun()} felt {job.affect_start}, "
        f"and {job.task} gave {hero.pronoun('object')} a warm, busy feeling."
    )
    world.say(
        f"{grownup.label.capitalize()} had taught {hero.id} that {value.label} matters because to {value.action}, "
        f"and that way {value.benefit}."
    )


def raise_mystery(world: World, hero: Entity, grownup: Entity, job: Job, mystery: Mystery) -> None:
    hero.meters["job"] += 1
    hero.memes["affect"] = 1
    world.para()
    world.say(
        f"One afternoon, while {hero.id} was {job.gerund}, {hero.pronoun('possessive')} mood turned {job.affect_turn}."
    )
    world.say(
        f"{hero.pronoun().capitalize()} noticed {mystery.clue} and wondered who it belonged to."
    )
    world.say(
        f"It was a small mystery to solve, and it made {hero.id} slow down and look again instead of guessing."
    )


def solve_mystery(world: World, hero: Entity, grownup: Entity, job: Job, mystery: Mystery, value: Value) -> None:
    hero.memes["mystery"] = 1
    hero.memes["moral_value"] = 1
    world.para()
    world.say(
        f"{hero.id} remembered {value.label} and decided to {value.action}."
    )
    world.say(
        f"So {hero.pronoun()} asked {grownup.label} about the clue, and together they found that {mystery.reveal}."
    )
    world.say(
        f"{grownup.label.capitalize()} smiled because {hero.id} had used the job well: the mystery was solved without blame or fuss."
    )


def end_story(world: World, hero: Entity, job: Job, mystery: Mystery) -> None:
    hero.memes["affect"] = 2
    world.say(
        f"By the end, {hero.id} felt {job.affect_end}. {mystery.label.capitalize()} was no longer hanging over the room."
    )
    world.say(
        f"{hero.id} finished the job, and the little place felt calm again, as if a neat answer had been sitting there all along."
    )


def tell(setting: Setting, job: Job, mystery: Mystery, value: Value,
         hero_name: str = "Mina", hero_type: str = "girl") -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        label=hero_name,
        meters={"job": 0.0},
        memes={"affect": 0.0},
    ))
    grownup = world.add(Entity(
        id="Adult",
        kind="character",
        type="woman",
        label="the librarian" if setting.place == "the little community library" else (
            "the cafe owner" if setting.place == "the corner cafe" else "the gardener"
        ),
    ))

    setup_story(world, hero, grownup, job, mystery, value)
    raise_mystery(world, hero, grownup, job, mystery)
    solve_mystery(world, hero, grownup, job, mystery, value)
    end_story(world, hero, job, mystery)

    world.facts.update(
        hero=hero,
        grownup=grownup,
        job=job,
        mystery=mystery,
        value=value,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    job = _safe_fact(world, f, "job")
    mystery = _safe_fact(world, f, "mystery")
    value = _safe_fact(world, f, "value")
    return [
        f'Write a short slice-of-life story for a small child about a {job.label}, a mystery to solve, and the value of {value.label}.',
        f"Tell a gentle story where {hero.id} has a job, notices a clue, and learns that {value.action}.",
        f'Write a simple story that uses the words "job" and "mystery" and ends with a calm answer.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    grownup = _safe_fact(world, f, "grownup")
    job = _safe_fact(world, f, "job")
    mystery = _safe_fact(world, f, "mystery")
    value = _safe_fact(world, f, "value")
    return [
        QAItem(
            question=f"What job did {hero.id} have at {world.setting.place}?",
            answer=f"{hero.id} had a job as a {job.label}, and {hero.pronoun()} used it to help the room feel organized.",
        ),
        QAItem(
            question=f"How did {hero.id} feel before the mystery was solved?",
            answer=f"At first {hero.id} felt {job.affect_start}, then {job.affect_turn} when the clue appeared, and at the end {job.affect_end}.",
        ),
        QAItem(
            question=f"What small mystery did {hero.id} notice?",
            answer=f"{hero.id} noticed {mystery.clue}, which led to {mystery.label}.",
        ),
        QAItem(
            question=f"What moral value helped {hero.id} solve the problem?",
            answer=f"{value.label} helped {hero.id} because it was important to {value.action}.",
        ),
        QAItem(
            question=f"Why did the grownup smile at the end?",
            answer=f"{grownup.label.capitalize()} smiled because {hero.id} solved the mystery kindly, without blame, and the little mistake was fixed.",
        ),
    ]


KNOWLEDGE = {
    "job": [
        ("What is a job?", "A job is work that someone does to help other people or keep a place running well."),
    ],
    "mystery": [
        ("What is a mystery?", "A mystery is something that is not understood at first, so people look for clues."),
    ],
    "honesty": [
        ("What does honesty mean?", "Honesty means telling the truth and not pretending something different happened."),
    ],
    "care": [
        ("What does care mean?", "Care means paying attention and treating people and things gently."),
    ],
    "attention": [
        ("What is attention?", "Attention means looking and listening closely so you do not miss small details."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["job"].tags) | set(f["mystery"].tags) | set(f["value"].tags)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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


# ---------------------------------------------------------------------------
# Trace
# ---------------------------------------------------------------------------
def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={dict(e.meters)}")
        if e.memes:
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A valid story needs a place that affords the job and a mystery that belongs there.
valid(Place, Job, Mystery) :- setting(Place), job(Job), mystery(Mystery),
                               affords_job(Place, Job), mystery_in(Mystery, Place).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        if setting.indoors:
            lines.append(asp.fact("indoors", place))
        for job in sorted(setting.afford_job):
            lines.append(asp.fact("affords_job", place, job))
    for job_id in JOBS:
        lines.append(asp.fact("job", job_id))
    for mystery_id, mystery in MYSTERIES.items():
        lines.append(asp.fact("mystery", mystery_id))
        for tag in sorted(mystery.tags):
            lines.append(asp.fact("mystery_in", mystery_id, tag))
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
# Parameters and CLI
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    job: str
    mystery: str
    value: str
    name: str
    gender: str
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


CURATED = [
    StoryParams(place="library", job="shelf_helper", mystery="missing_card", value="honesty", name="Mina", gender="girl"),
    StoryParams(place="cafe", job="tray_runner", mystery="wrong_cups", value="care", name="Leo", gender="boy"),
    StoryParams(place="garden", job="tool_sorter", mystery="lost_ribbon", value="attention", name="Nora", gender="girl"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: a job, an affect change, and a mystery to solve.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--job", choices=JOBS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--value", choices=VALUES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    if getattr(args, "place", None) and getattr(args, "job", None) and getattr(args, "mystery", None) and (getattr(args, "place", None), getattr(args, "job", None), getattr(args, "mystery", None)) not in combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "job", None) is None or c[1] == getattr(args, "job", None))
        and (getattr(args, "mystery", None) is None or c[2] == getattr(args, "mystery", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, job, mystery = rng.choice(list(filtered))
    value = getattr(args, "value", None) or next(iter(_safe_lookup(MYSTERIES, mystery).tags & VALUES.keys()), None) or (
        "honesty" if place == "library" else "care" if place == "cafe" else "attention"
    )
    gender = getattr(args, "gender", None) or ("girl" if rng.random() < 0.5 else "boy")
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, job=job, mystery=mystery, value=value, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(JOBS, params.job),
        _safe_lookup(MYSTERIES, params.mystery),
        _safe_lookup(VALUES, params.value),
        hero_name=params.name,
        hero_type=params.gender,
    )
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, job, mystery) combos:\n")
        for place, job, mystery in combos:
            print(f"  {place:8} {job:14} {mystery}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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
            header = f"### {p.name}: {p.job} at {p.place} (mystery: {p.mystery})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
