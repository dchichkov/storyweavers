#!/usr/bin/env python3
"""
storyworlds/worlds/assed_decibel_heir_humor_curiosity_whodunit.py
==================================================================

A small whodunit-style story world about an heir, a curious clue hunt, and a
very loud decibel mystery.

The seed words are woven into the world as:
- assed: the odd family note clue, "assed" as a nonsense word in a scribbled
  message that becomes part of the puzzle
- decibel: the measuring tool that turns a hunch into evidence
- heir: the child who inherits the house and the mystery

The domain is child-facing, humorous, and clue-driven: the story begins with a
quiet inheritance, turns on a noisy interruption, and ends with a reveal that
proves who, or what, made the racket.
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
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    adult: object | None = None
    heir: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    label: str
    type: str
    clue: str
    sound: str
    reveal: str
    target: str
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
class Suspect:
    id: str
    label: str
    type: str
    behavior: str
    hint: str
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
class Gear:
    id: str
    label: str
    purpose: str
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


SETTINGS = {
    "manor": Setting(place="the old manor", afford={"search", "listen", "measure"}),
    "library": Setting(place="the quiet library", afford={"search", "listen", "measure"}),
    "attic": Setting(place="the dusty attic", afford={"search", "listen", "measure"}),
}

MYSTERIES = {
    "bell": Mystery(
        id="bell",
        label="the silver bell",
        type="bell",
        clue="a scribbled note with the word assed on it",
        sound="a sharp ding",
        reveal="the bell was tied to a rolling tray",
        target="tray",
        tags={"assed", "decibel", "heir", "sound"},
    ),
    "jar": Mystery(
        id="jar",
        label="the cookie jar",
        type="jar",
        clue="crumbs shaped like tiny footsteps",
        sound="a clink and a thump",
        reveal="the jar lid was stuck under a stack of books",
        target="books",
        tags={"decibel", "curiosity", "heir", "crumbs"},
    ),
    "cymbal": Mystery(
        id="cymbal",
        label="the brass cymbal",
        type="cymbal",
        clue="a shiny scratch on the floor",
        sound="a crashy boom",
        reveal="a toy wagon bumped it in the hall",
        target="wagon",
        tags={"decibel", "humor", "heir", "noise"},
    ),
}

SUSPECTS = {
    "butler": Suspect(
        id="butler",
        label="the butler",
        type="man",
        behavior="walked like a whisper",
        hint="his shoes were too soft for a noisy prank",
        tags={"quiet", "humor"},
    ),
    "aunt": Suspect(
        id="aunt",
        label="the aunt",
        type="aunt",
        behavior="carried a teacup and a smile",
        hint="she had flour on her sleeve from baking",
        tags={"baking", "curiosity"},
    ),
    "cousin": Suspect(
        id="cousin",
        label="the cousin",
        type="boy",
        behavior="kept peeking around corners",
        hint="he knew where the toy wagon was hidden",
        tags={"toy", "humor"},
    ),
    "cat": Suspect(
        id="cat",
        label="the cat",
        type="thing",
        behavior="sat with a guilty tail flick",
        hint="its whiskers were dusted with cookie crumbs",
        tags={"crumbs", "funny"},
    ),
}

GEAR = {
    "meter": Gear(id="meter", label="a decibel meter", purpose="measure loud sounds", tags={"decibel"}),
    "lamp": Gear(id="lamp", label="a little lamp", purpose="shine into dark corners", tags={"curiosity"}),
    "notebook": Gear(id="notebook", label="a pocket notebook", purpose="write down clues", tags={"curiosity", "assed"}),
}

GUILTY_MAP = {
    "bell": "cousin",
    "jar": "cat",
    "cymbal": "wagon",
}

WAGONS = {
    "tray": "a rolling silver tray",
    "books": "a stack of old books",
    "wagon": "a toy wagon with one wobbly wheel",
}

NAMES = ["Mina", "Toby", "Iris", "Noah", "Pia", "Eli", "Ada", "Finn"]
TRAITS = ["curious", "bright", "cheerful", "careful", "thoughtful", "brave"]


@dataclass
class StoryParams:
    place: str
    mystery: str
    name: str
    gender: str
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


def suspicion_level(world: World, mystery: Mystery, suspect: Suspect) -> float:
    score = 0.0
    if suspect.id == GUILTY_MAP[mystery.id]:
        score += 2.0
    if mystery.id == "bell" and suspect.id == "butler":
        score -= 1.0
    if mystery.id == "jar" and suspect.id == "cat":
        score += 1.0
    if mystery.id == "cymbal" and suspect.id == "cousin":
        score += 1.0
    return score


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for mid, mystery in MYSTERIES.items():
            if "measure" not in setting.afford:
                continue
            combos.append((place, mid, GUILTY_MAP[mid]))
    return combos


def explain_rejection(mystery_id: str, suspect_id: str) -> str:
    mystery = _safe_lookup(MYSTERIES, mystery_id)
    suspect = _safe_lookup(SUSPECTS, suspect_id)
    return (
        f"(No story: {suspect.label} is too weak a match for {mystery.label}. "
        f"The clues would not point there honestly.)"
    )


def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    world = World(setting)
    heir = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    adult = world.add(Entity(id="guardian", kind="character", type="aunt", label="the guardian"))
    for sid, s in SUSPECTS.items():
        world.add(Entity(id=sid, kind="character", type=s.type, label=s.label))
    for gid, g in GEAR.items():
        world.add(Entity(id=gid, type="thing", label=g.label))
    world.facts.update(heir=heir, guardian=adult, mystery=mystery, place=setting.place)
    return world


def tell(world: World, params: StoryParams) -> None:
    heir = world.get(params.name)
    guardian = world.get("guardian")
    mystery = _safe_lookup(MYSTERIES, params.mystery)
    culprit = GUILTY_MAP[mystery.id]
    suspect = world.get(culprit)

    world.say(
        f"{heir.id} was the new heir of {world.setting.place}, and {heir.pronoun('possessive')} "
        f"guardian handed over the key with a grin."
    )
    world.say(
        f"There was one odd rule: if anything made a noise louder than a whisper, {heir.id} had to "
        f"check it with a decibel meter."
    )

    world.para()
    world.say(
        f"That afternoon, a noise rang out: {mystery.sound}. {heir.id} blinked. "
        f"{heir.pronoun().capitalize()} loved mysteries, and this one sounded almost rude."
    )
    world.say(
        f"Near the noise sat {mystery.clue}. It looked funny enough to make {heir.id} frown and smile at the same time."
    )
    world.say(
        f"'{mystery.clue.split(' ')[0].capitalize()}?' {heir.id} said. 'That is not a normal clue.'"
    )

    world.para()
    world.say(f"{heir.id} grabbed a {GEAR['meter'].label} and a pocket notebook.")
    world.say(
        f"{heir.id} measured the sound, then followed the trail of tiny marks. "
        f"Each clue seemed to tip the answer a little more."
    )
    world.say(
        f"The first suspect was {world.get('butler').label}, because he {world.get('butler').behavior}. "
        f"But his own hint was {world.get('butler').hint}."
    )
    world.say(
        f"Then {heir.id} checked {world.get('aunt').label}, who {world.get('aunt').behavior}. "
        f"Yet she was only carrying flour and a spoon."
    )
    world.say(
        f"At last {heir.id} found {suspect.label}, who {suspect.behavior}. "
        f"Under one paw or pocket or shoe was the missing trick."
    )

    world.para()
    world.say(
        f"The clue led to {_safe_lookup(WAGONS, mystery.target)}. {mystery.reveal}."
    )
    world.say(
        f"{heir.id} laughed so hard that {heir.pronoun('possessive')} notebook shook. "
        f"'So that was the whole fuss! No villain at all, just a noisy accident.'"
    )
    world.say(
        f"{heir.id} wrote the answer down anyway, because an heir who is curious never wastes a good mystery."
    )

    world.facts.update(culprit=culprit, mystery_id=mystery.id, clue=mystery.clue)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    heir = _safe_fact(world, f, "heir")
    mystery = _safe_fact(world, f, "mystery")
    return [
        f'Write a humorous whodunit for a child named {heir.id} about {mystery.label} and a strange clue.',
        f"Tell a curiosity-driven mystery where an heir uses a decibel meter to figure out who made a loud noise.",
        f'Write a short whodunit that includes the odd clue "{mystery.clue}" and ends with a funny reveal.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    heir = _safe_fact(world, f, "heir")
    mystery = _safe_fact(world, f, "mystery")
    culprit = _safe_fact(world, f, "culprit")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {heir.id}, the curious heir of {world.setting.place}.",
        ),
        QAItem(
            question=f"What noisy thing started the mystery?",
            answer=f"The mystery started with {mystery.sound}.",
        ),
        QAItem(
            question=f"What clue looked odd enough to make {heir.id} laugh and think?",
            answer=f"The clue was {mystery.clue}.",
        ),
        QAItem(
            question=f"Who turned out to be behind the problem?",
            answer=f"It turned out to be {_safe_lookup(SUSPECTS, culprit).label}, not a scary villain.",
        ),
        QAItem(
            question=f"What tool did {heir.id} use to check the sound?",
            answer=f"{heir.id} used a decibel meter to measure the noise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a decibel meter do?",
            answer="A decibel meter measures how loud a sound is.",
        ),
        QAItem(
            question="What is an heir?",
            answer="An heir is a person who will receive something from a family, like a house, a title, or a special treasure.",
        ),
        QAItem(
            question="Why do curious people ask questions?",
            answer="Curious people ask questions because they want to understand what is happening.",
        ),
    ]


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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
% A mystery is valid when the setting allows careful measuring and the clue points
% to a single plausible culprit.
valid(Place, Mystery, Culprit) :- setting(Place), afford(Place, measure),
                                 mystery(Mystery), culprit_for(Mystery, Culprit).

% The clue is a good fit when it belongs to the mystery and the suspect matches
% the intended reveal.
matches(Mystery, Culprit) :- mystery(Mystery), culprit_for(Mystery, Culprit).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.afford):
            lines.append(asp.fact("afford", pid, a))
    for mid, m in MYSTERIES.items():
        lines.append(asp.fact("mystery", mid))
        lines.append(asp.fact("culprit_for", mid, GUILTY_MAP[mid]))
        for t in sorted(m.tags):
            lines.append(asp.fact("tagged", mid, t))
    for sid, s in SUSPECTS.items():
        lines.append(asp.fact("suspect", sid))
        for t in sorted(s.tags):
            lines.append(asp.fact("suspect_tag", sid, t))
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous whodunit about an heir, a decibel clue, and curiosity.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mystery", choices=MYSTERIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "mystery", None):
        combos = [c for c in combos if c[1] == getattr(args, "mystery", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mystery, _ = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, mystery=mystery, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
    tell(world, params)
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
    StoryParams(place="manor", mystery="bell", name="Mina", gender="girl", trait="curious"),
    StoryParams(place="library", mystery="jar", name="Toby", gender="boy", trait="bright"),
    StoryParams(place="attic", mystery="cymbal", name="Iris", gender="girl", trait="careful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} compatible (place, mystery, culprit) combos:\n")
        for t in vals:
            print("  ", t)
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
            header = f"### {p.name}: {p.mystery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
