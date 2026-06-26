#!/usr/bin/env python3
"""
storyworlds/worlds/cauliflower_infant_bravery_friendship_ghost_story.py
========================================================================

A small child-friendly ghost-story world about an infant, a spooky feeling,
and the brave little turn that grows into friendship.

The seed words are "cauliflower" and "infant". This world turns them into a
gentle, classical story: a tiny infant hears a ghostly rustle near a
cauliflower patch, feels frightened, finds courage with a friend, and learns
that the ghost was lonely rather than mean.

World model notes:
- Physical meters: chill, rustle, nibbled, glow
- Emotional memes: fear, bravery, trust, friendship, relief
- State changes are narrated, not just swapped into a frozen paragraph
- The ending proves what changed: fear settles, friendship rises, and the
  cauliflower is safe and shared

This file follows the shared Storyworld contract and includes an ASP twin for
reasonableness parity.
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
# Registries
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

@dataclass(frozen=True)
class Setting:
    key: str
    place: str
    light: str
    mood: str
    has_patch: bool = True
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


@dataclass(frozen=True)
class Companion:
    key: str
    name: str
    type: str
    role: str
    brave: bool = False
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


@dataclass(frozen=True)
class GhostKind:
    key: str
    label: str
    sound: str
    motive: str
    is_kind: bool = True
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


@dataclass(frozen=True)
class Prize:
    key: str
    label: str
    phrase: str
    location: str
    edible: bool = True
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


SETTINGS = {
    "moonlit_garden": Setting(
        key="moonlit_garden",
        place="the moonlit garden",
        light="moonlight",
        mood="still and silver",
        has_patch=True,
    ),
    "quiet_pantry": Setting(
        key="quiet_pantry",
        place="the quiet pantry",
        light="a little lamp glow",
        mood="small and hush-soft",
        has_patch=False,
    ),
    "backyard_patch": Setting(
        key="backyard_patch",
        place="the backyard patch",
        light="pale porch light",
        mood="damp and sleepy",
        has_patch=True,
    ),
}

COMPANIONS = {
    "mara": Companion(key="mara", name="Mara", type="girl", role="friend", brave=True),
    "noah": Companion(key="noah", name="Noah", type="boy", role="friend", brave=True),
    "nib": Companion(key="nib", name="Nib", type="rabbit", role="helper", brave=False),
    "syl": Companion(key="syl", name="Syl", type="girl", role="neighbor", brave=False),
}

GHOSTS = {
    "shy_ghost": GhostKind(
        key="shy_ghost",
        label="a shy little ghost",
        sound="whooo",
        motive="wanted company near the garden patch",
        is_kind=True,
    ),
    "windy_ghost": GhostKind(
        key="windy_ghost",
        label="a windy ghost",
        sound="whoosh",
        motive="kept spinning the leaves around",
        is_kind=True,
    ),
}

PRIZES = {
    "cauliflower": Prize(
        key="cauliflower",
        label="cauliflower",
        phrase="a white cauliflower with tight little florets",
        location="the patch",
        edible=True,
    ),
}


# ---------------------------------------------------------------------------
# Entities / world
# ---------------------------------------------------------------------------
@dataclass
class Entity:
    id: str
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    companion: object | None = None
    ghost: object | None = None
    infant: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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


# ---------------------------------------------------------------------------
# Story mechanics
# ---------------------------------------------------------------------------
def introduce(world: World, infant: Entity, setting: Setting) -> None:
    world.say(
        f"{infant.id} was a little infant who liked soft blankets, warm hands, "
        f"and the hush of {setting.place} at night."
    )


def show_cauliflower(world: World, prize: Entity) -> None:
    prize.meters["glow"] += 1
    world.say(
        f"Near the edge of the patch stood {prize.phrase}, pale as a tiny moon."
    )


def hearing_spooky_sound(world: World, infant: Entity, ghost: Entity, setting: Setting) -> None:
    infant.memes["fear"] += 1
    ghost.meters["rustle"] += 1
    world.say(
        f"Then the dark made a small sound: \"{ghost.label} said {ghost.meter_sound if hasattr(ghost, 'meter_sound') else 'whooo'}.\" "
        f"The sound drifted through {setting.place} and made {infant.id} cling close to the path."
    )


def brave_step(world: World, infant: Entity, companion: Entity) -> None:
    infant.memes["bravery"] += 1
    companion.memes["bravery"] += 1
    world.say(
        f"But {companion.name} squeezed {infant.pronoun('possessive')} hand and smiled. "
        f"\"We can look,\" {companion.pronoun()} said. So {infant.id} took one brave little step."
    )


def discover_kind_ghost(world: World, infant: Entity, companion: Entity, ghost: Entity, prize: Entity) -> None:
    infant.memes["fear"] = max(0.0, infant.memes["fear"] - 1.0)
    infant.memes["trust"] += 1
    infant.memes["friendship"] += 1
    companion.memes["trust"] += 1
    companion.memes["friendship"] += 1
    ghost.memes["trust"] += 1
    ghost.memes["friendship"] += 1
    world.say(
        f"Behind the leaves, {ghost.label} was not mean at all. It was only lonely, "
        f"and the ghost kept pointing at the {prize.label} with a worried little wave."
    )
    world.say(
        f"{companion.name} whispered that the ghost must have been guarding dinner, "
        f"not trying to frighten anyone."
    )


def share_cauliflower(world: World, infant: Entity, companion: Entity, ghost: Entity, prize: Entity) -> None:
    prize.meters["nibbled"] += 1
    ghost.meters["glow"] += 1
    infant.memes["relief"] += 1
    infant.memes["friendship"] += 1
    companion.memes["friendship"] += 1
    world.say(
        f"Together, they broke off a little piece of {prize.label} and offered it to {ghost.label}. "
        f"The ghost brightened like a lantern, and the three of them shared the crisp bites under the moonlight."
    )


def ending_image(world: World, infant: Entity, companion: Entity, ghost: Entity, prize: Entity) -> None:
    world.say(
        f"By the end, {infant.id} was no longer hiding. {infant.pronoun().capitalize()} was standing beside "
        f"{companion.name}, waving at {ghost.label}, while the {prize.label} patch stayed safe and silver."
    )


# ---------------------------------------------------------------------------
# Story construction
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    setting: str
    companion: str
    ghost: str
    infant_name: str
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


def tell(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    companion_cfg = _safe_lookup(COMPANIONS, params.companion)
    ghost_cfg = _safe_lookup(GHOSTS, params.ghost)
    prize_cfg = PRIZES["cauliflower"]

    world = World(setting)
    infant = world.add(Entity(id=params.infant_name, kind="character", type="infant"))
    companion = world.add(Entity(id=companion_cfg.name, kind="character", type=companion_cfg.type))
    ghost = world.add(Entity(id=ghost_cfg.label, kind="character", type="ghost"))
    prize = world.add(Entity(id=prize_cfg.label, kind="thing", type="cauliflower", label="cauliflower", phrase=prize_cfg.phrase))

    world.facts.update(
        setting=setting,
        companion=companion_cfg,
        ghost=ghost_cfg,
        prize=prize_cfg,
        infant=infant,
    )

    introduce(world, infant, setting)
    show_cauliflower(world, prize)

    world.para()
    world.say(
        f"That night, {params.infant_name} and {companion_cfg.name} went out to {setting.place}, "
        f"where the air felt {setting.mood}."
    )
    hearing_spooky_sound(world, infant, ghost, setting)

    world.say(
        f"{params.infant_name} wanted to turn back, but {companion_cfg.name} stayed close."
    )
    brave_step(world, infant, companion)

    world.para()
    discover_kind_ghost(world, infant, companion, ghost, prize)
    share_cauliflower(world, infant, companion, ghost, prize)
    ending_image(world, infant, companion, ghost, prize)

    world.facts.update(
        resolved=True,
        fear=infant.memes["fear"],
        bravery=infant.memes["bravery"],
        friendship=infant.memes["friendship"],
        trust=ghost.memes["trust"],
    )
    return world


# ---------------------------------------------------------------------------
# Registries / selection
# ---------------------------------------------------------------------------
INFANT_NAMES = ["Milo", "Nia", "Ivy", "Ari", "Lulu", "Oli"]
DEFAULT_COMBOS = [
    ("moonlit_garden", "mara", "shy_ghost"),
    ("backyard_patch", "noah", "windy_ghost"),
    ("quiet_pantry", "syl", "shy_ghost"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_key, setting in SETTINGS.items():
        for companion_key in COMPANIONS:
            for ghost_key in GHOSTS:
                if setting_key == "quiet_pantry" and ghost_key == "windy_ghost":
                    continue
                if setting.has_patch:
                    combos.append((setting_key, companion_key, ghost_key))
                elif setting_key == "quiet_pantry" and companion_key in {"mara", "syl"}:
                    combos.append((setting_key, companion_key, ghost_key))
    return combos


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    companion: Companion = _safe_fact(world, f, "companion")  # type: ignore[assignment]
    ghost: GhostKind = _safe_fact(world, f, "ghost")  # type: ignore[assignment]
    return [
        f'Write a gentle ghost story for a very young child in {setting.place} that includes a cauliflower patch and a brave friend.',
        f"Tell a tiny story where an infant named {f['infant'].id} feels scared, then learns courage with {companion.name} when a ghost appears.",
        f'Create a child-sized spooky story that uses the word "cauliflower" and ends in friendship instead of fear.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    infant: Entity = _safe_fact(world, f, "infant")  # type: ignore[assignment]
    companion: Companion = _safe_fact(world, f, "companion")  # type: ignore[assignment]
    setting: Setting = _safe_fact(world, f, "setting")  # type: ignore[assignment]
    ghost: GhostKind = _safe_fact(world, f, "ghost")  # type: ignore[assignment]
    prize: Prize = _safe_fact(world, f, "prize")  # type: ignore[assignment]

    return [
        QAItem(
            question=f"Who was the infant in the story?",
            answer=f"The infant was {infant.id}, who went into {setting.place} with {companion.name}.",
        ),
        QAItem(
            question=f"What made {infant.id} feel scared at first?",
            answer=f"The small spooky sound from {ghost.label} made {infant.id} feel frightened before {companion.name} helped.",
        ),
        QAItem(
            question=f"What was the white thing in the patch?",
            answer=f"It was {prize.phrase}, a cauliflower standing bright in the garden.",
        ),
        QAItem(
            question=f"How did {infant.id} become brave?",
            answer=f"{companion.name} held {infant.pronoun('possessive')} hand, and {infant.id} took a brave little step instead of running away.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"Fear went down, bravery and friendship went up, and {ghost.label} was welcomed as a friend.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is cauliflower?",
            answer="Cauliflower is a vegetable with a pale, bumpy flower head that can look like a little white tree.",
        ),
        QAItem(
            question="What does bravery mean?",
            answer="Bravery means doing something scary or hard even when you feel nervous.",
        ),
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, help each other, and like being together.",
        ),
    ]


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
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:24} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Reasonableness / ASP twin
# ---------------------------------------------------------------------------
def is_reasonable(setting: Setting, companion: Companion, ghost: GhostKind) -> bool:
    if setting.key == "quiet_pantry" and ghost.key == "windy_ghost":
        return False
    if setting.has_patch:
        return True
    return companion.key in {"mara", "syl"}


ASP_RULES = r"""
setting(moonlit_garden).
setting(quiet_pantry).
setting(backyard_patch).

has_patch(moonlit_garden).
has_patch(backyard_patch).

companion(mara).
companion(noah).
companion(nib).
companion(syl).

ghost(shy_ghost).
ghost(windy_ghost).

reasonable(S,C,G) :- has_patch(S), companion(C), ghost(G).
reasonable(quiet_pantry,C,shy_ghost) :- companion(C), C = mara; C = syl.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for s in SETTINGS.values():
        lines.append(asp.fact("setting", s.key))
        if s.has_patch:
            lines.append(asp.fact("has_patch", s.key))
    for c in COMPANIONS.values():
        lines.append(asp.fact("companion", c.key))
    for g in GHOSTS.values():
        lines.append(asp.fact("ghost", g.key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show reasonable/3."))
    return sorted(set(asp.atoms(model, "reasonable")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="A child-friendly ghost story about cauliflower, bravery, and friendship."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--ghost", choices=GHOSTS)
    ap.add_argument("--name", help="infant name")
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
    filtered = [
        c for c in combos
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "companion", None) is None or c[1] == getattr(args, "companion", None))
        and (getattr(args, "ghost", None) is None or c[2] == getattr(args, "ghost", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting_key, companion_key, ghost_key = rng.choice(list(filtered))
    infant_name = getattr(args, "name", None) or rng.choice(INFANT_NAMES)
    return StoryParams(setting=setting_key, companion=companion_key, ghost=ghost_key, infant_name=infant_name)


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
        print(asp_program("#show reasonable/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} reasonable combos:\n")
        for s, c, g in triples:
            print(f"  {s:16} {c:8} {g}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(setting="moonlit_garden", companion="mara", ghost="shy_ghost", infant_name="Milo"),
            StoryParams(setting="backyard_patch", companion="noah", ghost="windy_ghost", infant_name="Nia"),
            StoryParams(setting="quiet_pantry", companion="syl", ghost="shy_ghost", infant_name="Ivy"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.infant_name}: {p.setting} with {p.companion} and {p.ghost}"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
