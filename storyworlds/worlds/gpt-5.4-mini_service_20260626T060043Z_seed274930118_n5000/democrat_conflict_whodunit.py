#!/usr/bin/env python3
"""
A small whodunit storyworld about a neighborhood conflict, a missing object, and
a careful democratic decision about who is telling the truth.

The world begins with an ordinary disagreement: a group is gathered for a vote,
a prize goes missing, and everyone has a reason to look suspicious. The story
turns on evidence, testimony, and a calm resolution that restores trust.
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
# Core entities
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    role: str = ""
    owner: Optional[str] = None
    held_by: Optional[str] = None
    hidden: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    chair: object | None = None
    democrat: object | None = None
    helper: object | None = None
    prize: object | None = None
    watcher: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "aunt"}
        male = {"boy", "man", "father", "uncle"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Place:
    name: str
    kind: str
    clues: list[str] = field(default_factory=list)
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


@dataclass
class Suspicion:
    suspect: str
    clue: str
    weight: int
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
class World:
    place: Place
    entities: dict[str, Entity] = field(default_factory=dict)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)
    fired: set[str] = field(default_factory=set)

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
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
class CastOption:
    name: str
    type: str
    role: str
    temperament: str
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


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    location: str
    owner_role: str
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
class StoryParams:
    place: str
    culprit: str
    prize: str
    investigator: str
    committee_member: str
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


PLACES = {
    "hall": Place(
        name="the community hall",
        kind="hall",
        clues=["a flipped chair", "a muddy footprint", "a torn note"],
    ),
    "library": Place(
        name="the little library",
        kind="library",
        clues=["a shelf gap", "a scrap of blue thread", "a quiet whisper"],
    ),
    "schoolroom": Place(
        name="the schoolroom",
        kind="schoolroom",
        clues=["chalk dust", "a dropped button", "a sticky jam stain"],
    ),
}

CAST = {
    "democrat": CastOption(
        name="Della",
        type="woman",
        role="democrat",
        temperament="calm",
    ),
    "chair": CastOption(
        name="Mayor Finn",
        type="man",
        role="chair",
        temperament="stern",
    ),
    "helper": CastOption(
        name="Mina",
        type="girl",
        role="helper",
        temperament="sharp-eyed",
    ),
    "watcher": CastOption(
        name="Owen",
        type="boy",
        role="watcher",
        temperament="nervous",
    ),
}

PRIZES = {
    "stamp": Prize(
        id="stamp",
        label="silver stamp",
        phrase="a tiny silver stamp",
        location="the vote box",
        owner_role="chair",
    ),
    "key": Prize(
        id="key",
        label="brass key",
        phrase="a small brass key",
        location="the drawer",
        owner_role="helper",
    ),
    "banner": Prize(
        id="banner",
        label="blue banner",
        phrase="a folded blue banner",
        location="the side table",
        owner_role="democrat",
    ),
}

CULPRITS = ["chair", "helper", "watcher"]
INVESTIGATORS = ["democrat", "helper"]
COMMITTEE = ["chair", "watcher"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def make_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place=place)

    democrat = world.add(Entity(
        id="democrat",
        kind="character",
        type=CAST["democrat"].type,
        label=CAST["democrat"].name,
        role="democrat",
        meters={"confidence": 1.0},
        memes={"duty": 1.0, "curiosity": 1.0},
    ))
    chair = world.add(Entity(
        id="chair",
        kind="character",
        type=CAST["chair"].type,
        label=CAST["chair"].name,
        role="chair",
        meters={"confidence": 1.0},
        memes={"authority": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=CAST["helper"].type,
        label=CAST["helper"].name,
        role="helper",
        meters={"confidence": 1.0},
        memes={"curiosity": 1.0},
    ))
    watcher = world.add(Entity(
        id="watcher",
        kind="character",
        type=CAST["watcher"].type,
        label=CAST["watcher"].name,
        role="watcher",
        meters={"confidence": 1.0},
        memes={"worry": 1.0},
    ))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type="thing",
        label=_safe_lookup(PRIZES, params.prize).label,
        phrase=_safe_lookup(PRIZES, params.prize).phrase,
        owner=_safe_lookup(PRIZES, params.prize).owner_role,
        hidden=True,
    ))

    culprit = world.get(params.culprit)
    investigator = world.get(params.investigator)
    committee_member = world.get(params.committee_member)

    # Clue state
    if params.prize == "stamp":
        prize.held_by = culprit.id
    elif params.prize == "key":
        prize.held_by = culprit.id
    else:
        prize.held_by = culprit.id

    world.facts.update(
        democrat=democrat,
        chair=chair,
        helper=helper,
        watcher=watcher,
        prize=prize,
        culprit=culprit,
        investigator=investigator,
        committee_member=committee_member,
        place=place,
    )
    return world


def deduce_suspicion(world: World) -> list[Suspicion]:
    culprit = _safe_fact(world, world.facts, "culprit")
    prize = _safe_fact(world, world.facts, "prize")
    place = world.place

    out = []
    for clue in place.clues:
        if culprit.id == "chair" and "chair" in clue or culprit.id == "helper" and "thread" in clue or culprit.id == "watcher" and "whisper" in clue:
            out.append(Suspicion(suspect=culprit.id, clue=clue, weight=2))
        else:
            out.append(Suspicion(suspect="chair", clue=clue, weight=1))
            out.append(Suspicion(suspect="helper", clue=clue, weight=1))
            out.append(Suspicion(suspect="watcher", clue=clue, weight=1))
    if prize.label == "silver stamp":
        out.append(Suspicion(suspect="chair", clue="the vote box was left open", weight=2))
    elif prize.label == "brass key":
        out.append(Suspicion(suspect="helper", clue="only the drawer was unlocked", weight=2))
    else:
        out.append(Suspicion(suspect="watcher", clue="the banner was dragged behind a curtain", weight=2))
    return out


def story_intro(world: World) -> None:
    d = _safe_fact(world, world.facts, "democrat")
    c = _safe_fact(world, world.facts, "chair")
    p = world.place.name
    world.say(
        f"In {p}, {d.label} was known as a careful democrat who liked fair turns and clear votes."
    )
    world.say(
        f"That afternoon, {c.label} called everyone together, because something important had gone missing."
    )


def story_conflict(world: World) -> None:
    prize = _safe_fact(world, world.facts, "prize")
    culprit = _safe_fact(world, world.facts, "culprit")
    inv = _safe_fact(world, world.facts, "investigator")
    com = _safe_fact(world, world.facts, "committee_member")
    d = _safe_fact(world, world.facts, "democrat")

    world.para()
    world.say(
        f"The {prize.label} had vanished from {prize.location}, and each person looked at the others with fresh worry."
    )
    world.say(
        f"{inv.label} started asking careful questions, while {com.label} crossed {com.pronoun('possessive')} arms and muttered that someone must have seen something."
    )
    world.say(
        f"{d.label} did not shout. {d.pronoun().capitalize()} listened to every answer and noticed which stories matched the clues."
    )
    world.say(
        f"Then {d.label} pointed to the odd clue left behind: it fit {culprit.label} better than anyone else."
    )


def story_turn(world: World) -> None:
    culprit = _safe_fact(world, world.facts, "culprit")
    prize = _safe_fact(world, world.facts, "prize")
    d = _safe_fact(world, world.facts, "democrat")
    c = _safe_fact(world, world.facts, "chair")

    world.para()
    world.say(
        f"{culprit.label} went quiet, because the clue made the room feel smaller and the conflict harder to hide."
    )
    world.say(
        f"But {d.label} said the aim was not to win an argument; it was to find the truth together."
    )
    world.say(
        f"{c.label} checked the drawer and the table again, and at last noticed the {prize.label} tucked where it had been dropped."
    )


def story_resolution(world: World) -> None:
    prize = _safe_fact(world, world.facts, "prize")
    culprit = _safe_fact(world, world.facts, "culprit")
    d = _safe_fact(world, world.facts, "democrat")
    world.para()
    world.say(
        f"The room grew calm when the {prize.label} was returned and the real reason became clear."
    )
    world.say(
        f"{culprit.label} had not meant to steal it; {culprit.pronoun()} had only hidden it during the conflict and then forgotten."
    )
    world.say(
        f"{d.label} helped everyone agree on a kinder rule for the next vote, and the hall felt fair again."
    )
    world.say(
        f"By the end, the missing thing was back in place, and the whole group could sit together without side-eye or blame."
    )


def generate_story(params: StoryParams) -> StorySample:
    world = make_world(params)
    story_intro(world)
    story_conflict(world)
    story_turn(world)
    story_resolution(world)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "prize")
    d = _safe_fact(world, world.facts, "democrat")
    return [
        f"Write a short whodunit for children about {d.label}, a missing {p.label}, and a fair way to settle a conflict.",
        f"Tell a simple mystery story where a democrat helps a group figure out who moved {p.phrase}.",
        f"Write a gentle detective story that ends with the lost item returned and the conflict cooled down.",
    ]


def story_qa(world: World) -> list[QAItem]:
    d = _safe_fact(world, world.facts, "democrat")
    culprit = _safe_fact(world, world.facts, "culprit")
    prize = _safe_fact(world, world.facts, "prize")
    place = world.place.name
    return [
        QAItem(
            question=f"Who helped solve the conflict in {place}?",
            answer=f"{d.label} helped solve it by listening carefully and using the clues instead of making a wild guess.",
        ),
        QAItem(
            question=f"What was missing from {prize.location}?",
            answer=f"The {prize.label} was missing, which made everyone worry and start looking for clues.",
        ),
        QAItem(
            question=f"Who was the real cause of the trouble?",
            answer=f"{culprit.label} was the one tied most closely to the missing {prize.label}, though it turned out to be a mistake rather than a mean trick.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The missing thing was found, the conflict cooled down, and the group agreed to act more fairly next time.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "democrat": QAItem(
        question="What is a democrat in this story world?",
        answer="A democrat is a person who cares about fair choices, listening to people, and letting everyone have a say.",
    ),
    "conflict": QAItem(
        question="What is a conflict?",
        answer="A conflict is a problem or disagreement that makes people upset until they talk it through and solve it.",
    ),
    "whodunit": QAItem(
        question="What is a whodunit?",
        answer="A whodunit is a mystery story where the fun is figuring out who did it by following clues.",
    ),
    "clue": QAItem(
        question="Why are clues useful in a mystery?",
        answer="Clues help people think carefully and discover what really happened instead of just guessing.",
    ),
}


def world_qa(world: World) -> list[QAItem]:
    return [WORLD_KNOWLEDGE["democrat"], WORLD_KNOWLEDGE["conflict"], WORLD_KNOWLEDGE["whodunit"], WORLD_KNOWLEDGE["clue"]]


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
        if e.label:
            bits.append(f"label={e.label!r}")
        if e.role:
            bits.append(f"role={e.role!r}")
        if e.owner:
            bits.append(f"owner={e.owner!r}")
        if e.hidden:
            bits.append("hidden=True")
        if e.held_by:
            bits.append(f"held_by={e.held_by!r}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  place: {world.place.name}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A suspect is plausible if they have any clue linked to them.
plausible(S) :- suspect(S), clue_for(S, _).

% The culprit is the one with the strongest clue.
strong(S) :- clue_for(S, C), clue_weight(C, W), W >= 2.
guilty(S) :- suspect(S), strong(S).

% A fair resolution exists when the missing prize is found and the conflict is settled.
resolved :- found(prize), not unresolved_conflict.

#show plausible/1.
#show guilty/1.
#show resolved/0.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        for clue in place.clues:
            lines.append(asp.fact("clue", clue))
    for sid in CAST:
        lines.append(asp.fact("suspect", sid))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("found", "prize"))  # the story resolves with the prize returned
    return "\n".join(lines)


def asp_program() -> str:
    return f"""{asp_facts()}

% derived from the current seed-world style
clue_for(chair, "a flipped chair").
clue_for(helper, "a scrap of blue thread").
clue_for(watcher, "a quiet whisper").
clue_weight("a flipped chair", 1).
clue_weight("a scrap of blue thread", 2).
clue_weight("a quiet whisper", 1).

unresolved_conflict :- suspect(_), not resolved.

{ASP_RULES}
"""


def asp_verify() -> int:
    import asp

    model = asp.one_model(asp_program())
    shown = set((sym.name, tuple(a.name if a.type != 4 else a.string for a in sym.arguments)) for sym in model)
    expected = {("resolved", ())}
    if shown & expected:
        print("OK: ASP program reaches a resolved state.")
        return 0
    print("MISMATCH: ASP program did not resolve as expected.")
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Whodunit storyworld with a democratic conflict and a fair resolution.")
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--culprit", choices=sorted(CULPRITS))
    ap.add_argument("--prize", choices=sorted(PRIZES))
    ap.add_argument("--investigator", choices=sorted(INVESTIGATORS))
    ap.add_argument("--committee-member", dest="committee_member", choices=sorted(COMMITTEE))
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


def valid_combos() -> list[tuple[str, str, str, str, str]]:
    combos = []
    for place in PLACES:
        for culprit in CULPRITS:
            for prize in PRIZES:
                for investigator in INVESTIGATORS:
                    for committee_member in COMMITTEE:
                        if culprit != investigator:
                            combos.append((place, culprit, prize, investigator, committee_member))
    return combos


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "culprit", None) is None or c[1] == getattr(args, "culprit", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
        and (getattr(args, "investigator", None) is None or c[3] == getattr(args, "investigator", None))
        and (getattr(args, "committee_member", None) is None or c[4] == getattr(args, "committee_member", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, culprit, prize, investigator, committee_member = rng.choice(list(combos))
    return StoryParams(
        place=place,
        culprit=culprit,
        prize=prize,
        investigator=investigator,
        committee_member=committee_member,
    )


def generate(params: StoryParams) -> StorySample:
    sample = generate_story(params)
    return sample


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
    StoryParams(place="hall", culprit="watcher", prize="stamp", investigator="democrat", committee_member="chair"),
    StoryParams(place="library", culprit="helper", prize="key", investigator="democrat", committee_member="watcher"),
    StoryParams(place="schoolroom", culprit="chair", prize="banner", investigator="helper", committee_member="watcher"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available for this world.")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
