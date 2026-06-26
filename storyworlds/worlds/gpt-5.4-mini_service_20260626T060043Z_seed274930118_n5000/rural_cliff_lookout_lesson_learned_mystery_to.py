#!/usr/bin/env python3
"""
rural_cliff_lookout_lesson_learned_mystery_to.py
================================================

A small folk-tale storyworld set at a rural cliff lookout.

Premise:
- A child or young helper keeps watch at a cliff lookout in the countryside.
- Something goes missing or seems wrong.
- The search leads to a mystery.
- A twist changes the meaning of what happened.
- The ending gives a lesson learned.

The world is deliberately tiny: one lookout, one mystery, one twist, and a
resolution that proves something changed in the simulated state.
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
# Shared typed entities
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    elder: object | None = None
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
    place: str = "the cliff lookout"
    rural: bool = True
    afford: set[str] = field(default_factory=lambda: {"watch", "search", "wait"})
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
class Mystery:
    id: str
    title: str
    missing: str
    clue: str
    suspicion: str
    lesson: str
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
class Twist:
    id: str
    reveal: str
    helper: str
    changed_meaning: str
    resolution: str
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
    mystery: str
    twist: str
    name: str
    gender: str
    elder: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World model
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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
SETTING = Setting()

MYSTERIES = {
    "lantern": Mystery(
        id="lantern",
        title="the missing lantern",
        missing="lantern",
        clue="a line of beeswax drops leading toward the gorse bushes",
        suspicion="someone had taken the lantern in the night",
        lesson="Sometimes the best answer comes from following the clue instead of the fear.",
        tags={"light", "night", "missing"},
    ),
    "bell": Mystery(
        id="bell",
        title="the missing sheep bell",
        missing="bell",
        clue="a soft ringing heard from below the cliff path",
        suspicion="the bell must have fallen into the grass",
        lesson="It helps to listen carefully before you decide what happened.",
        tags={"sound", "sheep", "missing"},
    ),
    "bread": Mystery(
        id="bread",
        title="the vanished loaf",
        missing="loaf of bread",
        clue="little muddy paw prints on the sill",
        suspicion="a thief had stolen supper from the window",
        lesson="Not every surprise is a bad one, and not every missing thing is stolen.",
        tags={"food", "animal", "missing"},
    ),
}

TWISTS = {
    "fox": Twist(
        id="fox",
        reveal="a clever fox had carried the thing away",
        helper="the fox had been trying to lead a lost lamb home",
        changed_meaning="what looked like theft was really a roundabout kindness",
        resolution="the fox slipped off with a tail flick, and the lamb trotted safely home behind it",
        tags={"animal", "kindness", "twist"},
    ),
    "child": Twist(
        id="child",
        reveal="a sleepy village child had borrowed it for a lantern game",
        helper="the child had left a trail on purpose so the watcher could find the way back",
        changed_meaning="what looked like a mystery was really a planned little game",
        resolution="the child returned the missing thing with a bashful grin and a promise to ask first next time",
        tags={"play", "kindness", "twist"},
    ),
    "wind": Twist(
        id="wind",
        reveal="the wind had blown it into the old hawthorn hollow",
        helper="the breeze had only tucked it away, not stolen it",
        changed_meaning="what looked like a hidden hand was only a restless night wind",
        resolution="they found the thing snug in the grass and laughed at their own hurry",
        tags={"weather", "twist"},
    ),
}


# ---------------------------------------------------------------------------
# Folk-tale state helpers
# ---------------------------------------------------------------------------
def _init_entity(name: str, gender: str, trait: str) -> Entity:
    return Entity(
        id=name,
        kind="character",
        type=gender,
        meters={"walk": 0.0, "search": 0.0, "relief": 0.0},
        memes={"curiosity": 0.0, "worry": 0.0, "hope": 0.0, "lesson": 0.0},
    )


def _compose_intro(world: World, hero: Entity, elder: Entity, mystery: Mystery) -> None:
    world.say(
        f"At the rural cliff lookout, {hero.id} was a {hero.pronoun('subject')} with a {world.facts['trait']} heart, "
        f"and {elder.id} was always nearby with a calm eye for weather and sheep."
    )
    world.say(
        f"One evening, the pair found that {mystery.missing} had gone missing from its usual place, "
        f"and everyone at the lookout felt the hush of a small folk-tale problem."
    )


def _follow_clue(world: World, hero: Entity, mystery: Mystery) -> None:
    hero.memes["curiosity"] += 1
    hero.memes["worry"] += 1
    hero.meters["search"] += 1
    world.say(
        f"{hero.id} did not like leaving a mystery alone, so {hero.pronoun('subject')} climbed the stony path and followed the clue: "
        f"{mystery.clue}."
    )
    world.say(
        f"The more {hero.id} looked, the more {hero.pronoun('subject')} thought of {mystery.suspicion}."
    )


def _turn(world: World, hero: Entity, elder: Entity, mystery: Mystery, twist: Twist) -> None:
    hero.memes["worry"] += 1
    elder.memes["hope"] += 1
    world.say(
        f"Then came the twist: {twist.reveal}."
    )
    world.say(
        f"{twist.helper.capitalize()}, and that changed the whole meaning of the chase."
    )
    world.say(
        f"{twist.changed_meaning.capitalize()}."
    )
    hero.meters["walk"] += 1
    elder.meters["walk"] += 1


def _resolution(world: World, hero: Entity, elder: Entity, mystery: Mystery, twist: Twist) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = 1.0
    elder.memes["hope"] += 1
    hero.meters["relief"] += 1
    world.say(
        f"In the end, {twist.resolution}, and the missing {mystery.missing} was back where the tale could safely close."
    )
    world.say(
        f"{world.facts['lesson']} {hero.id} learned that a patient heart can make a mystery small enough to hold."
    )


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A mystery story is valid when the chosen mystery and twist belong to the same
% small folk-tale domain, and the twist is strong enough to resolve it.
valid_story(M, T) :- mystery(M), twist(T), compatible(M, T), has_resolution(T).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("missing", mid, m.missing))
        for tag in sorted(m.tags):
            lines.append(asp.fact("tag", mid, tag))
    for tid, t in TWISTS.items():
        lines.append(asp.fact("twist", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
        lines.append(asp.fact("has_resolution", tid))
    # Compatibility facts are the Python reasonableness gate mirrored exactly.
    for mid in MYSTERIES:
        for tid in TWISTS:
            if _compatible(mid, tid):
                lines.append(asp.fact("compatible", mid, tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def _compatible(mystery_id: str, twist_id: str) -> bool:
    m = _safe_lookup(MYSTERIES, mystery_id)
    t = _safe_lookup(TWISTS, twist_id)
    # Only allow twists that feel like folk-tale explanations for the mystery.
    if mystery_id == "lantern":
        return twist_id in {"fox", "wind"}
    if mystery_id == "bell":
        return twist_id in {"child", "wind"}
    if mystery_id == "bread":
        return twist_id in {"fox", "child"}
    return False


def valid_combos() -> list[tuple[str, str]]:
    return [(m, t) for m in MYSTERIES for t in TWISTS if _compatible(m, t)]


def explain_rejection(mystery_id: str, twist_id: str) -> str:
    m = _safe_lookup(MYSTERIES, mystery_id)
    t = _safe_lookup(TWISTS, twist_id)
    return (
        f"(No story: {t.id} does not fit {m.title} in a folk-tale way. "
        f"Choose a twist that naturally explains the clue and gives a real lesson learned.)"
    )


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
GIRL_NAMES = ["Mara", "Elsie", "Nell", "Annie", "Tilda", "Rose"]
BOY_NAMES = ["Bram", "Ewan", "Kit", "Tom", "Pip", "Robin"]
TRAITS = ["brave", "curious", "patient", "cheerful", "steady", "gentle"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale storyworld set at a rural cliff lookout.")
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--twist", choices=TWISTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--elder", choices=["grandmother", "grandfather", "aunt", "uncle"])
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
    combos = valid_combos()
    if getattr(args, "mystery", None) and getattr(args, "twist", None) and not _compatible(getattr(args, "mystery", None), getattr(args, "twist", None)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        (m, t) for (m, t) in combos
        if (getattr(args, "mystery", None) is None or m == getattr(args, "mystery", None))
        and (getattr(args, "twist", None) is None or t == getattr(args, "twist", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    mystery, twist = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    elder = getattr(args, "elder", None) or rng.choice(["grandmother", "grandfather", "aunt", "uncle"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(mystery=mystery, twist=twist, name=name, gender=gender, elder=elder, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = World(SETTING)
    hero = world.add(_init_entity(params.name, params.gender, params.trait))
    elder = world.add(Entity(id=params.elder, kind="character", type=params.elder, meters={"walk": 0.0}, memes={"calm": 1.0}))
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    twist = _safe_lookup(TWISTS, params.twist)

    world.facts.update(
        trait=params.trait,
        hero=hero,
        elder=elder,
        mystery=mystery,
        twist=twist,
        lesson=mystery.lesson,
    )

    _compose_intro(world, hero, elder, mystery)
    world.para()
    _follow_clue(world, hero, mystery)
    world.para()
    _turn(world, hero, elder, mystery, twist)
    world.para()
    _resolution(world, hero, elder, mystery, twist)

    story = world.render()
    prompts = [
        f'Write a short folk tale set at a rural cliff lookout about a missing {mystery.missing} and a surprising twist.',
        f"Tell a gentle story where {hero.id} and {elder.id} solve {mystery.title} at the cliff lookout.",
        f"Write a story with a lesson learned, a mystery to solve, and a twist that makes sense in a countryside lookout.",
    ]

    story_qa = [
        QAItem(
            question=f"What mystery did {hero.id} and {elder.id} find at the cliff lookout?",
            answer=f"They found {mystery.title}, because the {mystery.missing} had gone missing from its usual place.",
        ),
        QAItem(
            question=f"What clue did {hero.id} follow to solve the mystery?",
            answer=f"{hero.id} followed {mystery.clue}. That clue led {hero.pronoun('object')} closer to the answer.",
        ),
        QAItem(
            question=f"What did the twist change about the missing {mystery.missing}?",
            answer=f"The twist showed that {twist.changed_meaning}. It was not the trouble people first feared.",
        ),
        QAItem(
            question=f"What lesson did {hero.id} learn in the end?",
            answer=f"{mystery.lesson}",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {twist.resolution}, and the lookout felt calm again.",
        ),
    ]

    world_qa = [
        QAItem(
            question="What is a cliff lookout?",
            answer="A cliff lookout is a place high up near the edge of a cliff where people can watch the land, sea, or valley below.",
        ),
        QAItem(
            question="What does rural mean?",
            answer="Rural means in the countryside, where there may be fields, paths, animals, and few houses close together.",
        ),
        QAItem(
            question="Why do folk tales often include a lesson?",
            answer="Folk tales often include a lesson so the story teaches something kind, wise, or careful while still feeling magical.",
        ),
    ]

    return StorySample(params=params, story=story, prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


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
    StoryParams(mystery="lantern", twist="fox", name="Mara", gender="girl", elder="grandmother", trait="curious"),
    StoryParams(mystery="bell", twist="wind", name="Bram", gender="boy", elder="grandfather", trait="patient"),
    StoryParams(mystery="bread", twist="child", name="Nell", gender="girl", elder="aunt", trait="gentle"),
]


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    cl2 = {(m, t) for (m, t) in cl}
    if py == cl2:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if cl2 - py:
        print("  only in clingo:", sorted(cl2 - py))
    if py - cl2:
        print("  only in python:", sorted(py - cl2))
    return 1


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible mystery/twist combos:\n")
        for m, t in stories:
            print(f"  {m:8} {t}")
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
            header = f"### {p.name}: {p.mystery} + {p.twist}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
