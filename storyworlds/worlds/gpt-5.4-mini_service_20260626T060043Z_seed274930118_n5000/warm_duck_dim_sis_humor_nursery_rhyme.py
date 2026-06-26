#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a warm little room, a duck-dim light,
and a sisterly fix that turns grumps into giggles.

Seed premise:
A little child and their sis want to enjoy a cozy warm treat, but the duck-dim
corner is too dark and a tiny mishap makes the mood wobble. A gentle joke and a
simple fix help them finish happy.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    prize: object | None = None
    sibling: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "sister", "woman", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "brother", "man", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"
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


@dataclass
class Setting:
    place: str = "the snug nook"
    warmth: str = "warm"
    dimness: str = "duck-dim"
    affords: set[str] = field(default_factory=lambda: {"tea", "story", "duckgame"})
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
class Activity:
    id: str
    verb: str
    gerund: str
    stumble: str
    mess: str
    tag: str
    humidity: str = ""
    humor: str = ""
    zone: set[str] = field(default_factory=set)
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
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class Comfort:
    id: str
    label: str
    prep: str
    tail: str
    helps: set[str]
    covers: set[str] = field(default_factory=set)
    plural: bool = False
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "nook": Setting(place="the snug nook", warmth="warm", dimness="duck-dim", affords={"tea", "story", "duckgame"}),
    "porch": Setting(place="the front porch", warmth="warm", dimness="duck-dim", affords={"tea", "story"}),
    "kitchen": Setting(place="the little kitchen", warmth="warm", dimness="duck-dim", affords={"tea", "story", "biscuit"}),
}

ACTIVITIES = {
    "tea": Activity(
        id="tea",
        verb="sip warm tea",
        gerund="sipping warm tea",
        stumble="slurp too loud",
        mess="spill",
        tag="tea",
        humor="the spoon did a tiny wobble-walk",
        zone={"table"},
    ),
    "story": Activity(
        id="story",
        verb="tell a funny story",
        gerund="telling a funny story",
        stumble="mix up the rhyme",
        mess="giggle",
        tag="story",
        humor="the rhyme went hop-hop like a little frog",
        zone={"heart"},
    ),
    "duckgame": Activity(
        id="duckgame",
        verb="play duck-duck games",
        gerund="playing duck-duck games",
        stumble="quack at the wrong time",
        mess="splash",
        tag="duck",
        humor="the duck made a wobble and a quack",
        zone={"floor"},
    ),
    "biscuit": Activity(
        id="biscuit",
        verb="bake a biscuit",
        gerund="baking a biscuit",
        stumble="drop the sugar",
        mess="crumb",
        tag="biscuit",
        humor="the flour puffed up like a sleepy cloud",
        zone={"hands", "table"},
    ),
}

PRIZES = {
    "mug": Prize(label="mug", phrase="a bright blue mug", type="mug", region="table"),
    "blanket": Prize(label="blanket", phrase="a soft striped blanket", type="blanket", region="body"),
    "book": Prize(label="book", phrase="a new rhyme book", type="book", region="hands"),
    "ducktoy": Prize(label="duck toy", phrase="a tiny duck toy", type="ducktoy", region="hands"),
}

COMFORTS = [
    Comfort(
        id="lamp",
        label="a little lamp",
        prep="light a little lamp first",
        tail="lit the little lamp and peeped at the page",
        helps={"duck-dim"},
        covers={"dark"},
    ),
    Comfort(
        id="blanket",
        label="the blanket",
        prep="wrap the blanket around their knees",
        tail="wrapped the blanket around their knees",
        helps={"warm"},
        covers={"cold"},
        plural=False,
    ),
    Comfort(
        id="joke",
        label="a tickly joke",
        prep="tell a tickly joke first",
        tail="told a tickly joke and the grumps went poof",
        helps={"mood"},
        covers=set(),
    ),
]

NAMES = ["Mina", "Lulu", "Ned", "Pip", "Ada", "Ollie", "Tess", "June"]
TRAITS = ["cheery", "tiny", "brave", "spry", "curious"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
    sibling: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Helpers
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


def reason_ok(act: Activity, prize: Prize) -> bool:
    return True


def select_comfort(setting: Setting, act: Activity, prize: Prize) -> Optional[Comfort]:
    if act.id == "story":
        for c in COMFORTS:
            if c.id == "joke":
                return c
    if setting.dimness == "duck-dim":
        for c in COMFORTS:
            if c.id == "lamp":
                return c
    return _safe_lookup(COMFORTS, 0) if COMFORTS else None


def rhyme_opening(hero: Entity, sibling: Entity, setting: Setting) -> str:
    return (
        f"{hero.id} and {sibling.id} went toddle-tap into {setting.place}, "
        f"where the air felt {setting.warmth} and the light was {setting.dimness}."
    )


def build_story(world: World, hero: Entity, sibling: Entity, act: Activity, prize: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a {hero.meters.get('smile', 0) or 'ready'} smile, "
        f"and {sibling.id}, the {sibling.label}, was never far from {hero.pronoun('possessive')} side."
    )
    world.say(
        f"They loved {act.gerund}, because {act.humor}."
    )
    world.say(
        f"One day {sibling.id} brought {hero.pronoun('object')} {prize.phrase}, and {hero.id} loved {prize.it()} at once."
    )

    world.para()
    world.say(rhyme_opening(hero, sibling, world.setting))
    world.say(
        f"{hero.id} wanted to {act.verb}, but there was a tiny problem: {act.stumble}, and that could make a mess."
    )
    world.say(
        f"{hero.id} frowned a bit, because {prize.label} was close by and nobody wanted a silly spill or splash."
    )

    world.para()
    world.say(
        f"{sibling.id} gave a wink and said, \"No storm in a spoon! We can fix this with a little tune.\""
    )
    comfort = select_comfort(world.setting, act, prize)
    if comfort is None:
        pass
    world.say(
        f"So they chose {comfort.label}: {comfort.prep}."
    )
    world.say(
        f"That made the duck-dim corner seem brighter and the grumpy wobble shrink small."
    )
    world.say(
        f"Then {hero.id} could {act.verb}, and {sibling.id} laughed at the funny bit where {act.humor}."
    )
    world.say(
        f"At the end, {comfort.tail}, and {prize.label} stayed neat as a pin."
    )

    world.facts.update(
        hero=hero,
        sibling=sibling,
        activity=act,
        prize=prize,
        comfort=comfort,
        resolved=True,
        dimness=world.setting.dimness,
        warmth=world.setting.warmth,
    )


# ---------------------------------------------------------------------------
# QA generation
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sibling = _safe_fact(world, f, "sibling")
    act = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short nursery-rhyme story about {hero.id} and {sibling.id} in a {world.setting.warmth}, {world.setting.dimness} place.',
        f"Tell a gentle humorous story where {hero.id} wants to {act.verb} but worries about {prize.phrase}, then finds a small fix with {sibling.id}.",
        f'Write a rhyming-feeling child story with a cozy mood, a tiny mishap, and a happy ending that includes "{act.tag}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    sibling = _safe_fact(world, f, "sibling")
    act = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")
    comfort = _safe_fact(world, f, "comfort")
    return [
        QAItem(
            question=f"Who wanted to {act.verb} in the story?",
            answer=f"{hero.id} wanted to {act.verb}, and {sibling.id} stayed close to help.",
        ),
        QAItem(
            question=f"What little problem made {hero.id} pause?",
            answer=f"{act.stumble.capitalize()} was the little problem, so {hero.id} worried about making a mess near {prize.label}.",
        ),
        QAItem(
            question=f"How did the children solve the problem?",
            answer=f"They used {comfort.label} and a cheerful joke, which made the duck-dim corner feel safer and brighter.",
        ),
        QAItem(
            question=f"What stayed neat at the end?",
            answer=f"{prize.label.capitalize()} stayed neat at the end, even after all the warm, funny play.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "tea": [
        QAItem(question="What is tea?", answer="Tea is a warm drink that people sip from cups or mugs."),
    ],
    "story": [
        QAItem(question="What is a rhyme book?", answer="A rhyme book is a book with short, bouncy lines that sound playful when read aloud."),
    ],
    "duck": [
        QAItem(question="Why do ducks look funny when they waddle?", answer="Ducks waddle because their bodies and feet make a side-to-side walk that looks bouncy and funny."),
    ],
    "biscuit": [
        QAItem(question="What is a biscuit?", answer="A biscuit is a small baked snack, often soft inside and warm from the oven."),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tag = _safe_fact(world, world.facts, "activity").tag
    return list(WORLD_KNOWLEDGE.get(tag, [])) + WORLD_KNOWLEDGE["story"][:1]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for qa in sample.story_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    out.append("")
    out.append("== (3) World knowledge ==")
    for qa in sample.world_qa:
        out.append(f"Q: {qa.question}")
        out.append(f"A: {qa.answer}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place_ok(P) :- setting(P).
activity_ok(A) :- activity(A).
prize_ok(R) :- prize(R).

compatible(P, A, R) :- place_ok(P), activity_ok(A), prize_ok(R).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for key in SETTINGS:
        lines.append(asp.fact("setting", key))
    for key in ACTIVITIES:
        lines.append(asp.fact("activity", key))
    for key in PRIZES:
        lines.append(asp.fact("prize", key))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_compatible() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show compatible/3."))
    return sorted(set(asp.atoms(model, "compatible")))


def asp_verify() -> int:
    py = {(p, a, r) for p in SETTINGS for a in ACTIVITIES for r in PRIZES if reason_ok(_safe_lookup(ACTIVITIES, a), _safe_lookup(PRIZES, r))}
    cl = set(asp_compatible())
    if py == cl:
        print(f"OK: clingo gate matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python.")
    if py - cl:
        print("Only in Python:", sorted(py - cl))
    if cl - py:
        print("Only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    return [(p, a, r) for p in SETTINGS for a in ACTIVITIES for r in PRIZES if reason_ok(_safe_lookup(ACTIVITIES, a), _safe_lookup(PRIZES, r))]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None)) and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    sibling = getattr(args, "sibling", None) or ("sis" if gender == "girl" else "bro")
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, sibling=sibling, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    act = _safe_lookup(ACTIVITIES, params.activity)
    prize_cfg = _safe_lookup(PRIZES, params.prize)
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type="child"))
    sibling = world.add(Entity(id=params.sibling, kind="character", type="sister" if params.gender == "girl" else "brother", label=params.sibling))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, plural=prize_cfg.plural, owner=hero.id))

    hero.meters["smile"] = 1
    build_story(world, hero, sibling, act, prize)
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
    if qa:
        print()
        print(format_qa(sample))
    if trace and sample.world is not None:
        print("\n--- world trace ---")
        for e in sample.world.entities.values():
            print(f"{e.id}: kind={e.kind} type={e.type} label={e.label}")


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="nook", activity="tea", prize="mug", name="Mina", gender="girl", sibling="sis", trait="cheery"),
    StoryParams(place="kitchen", activity="story", prize="book", name="Pip", gender="boy", sibling="sis", trait="curious"),
    StoryParams(place="porch", activity="duckgame", prize="ducktoy", name="Tess", gender="girl", sibling="sis", trait="spry"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld with a warm, duck-dim, sisterly humor.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--sibling")
    ap.add_argument("--trait")
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show compatible/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_compatible()
        print(f"{len(combos)} compatible combos:")
        for p, a, r in combos:
            print(f"  {p:8} {a:10} {r:8}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 30):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        else:
            header = ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
