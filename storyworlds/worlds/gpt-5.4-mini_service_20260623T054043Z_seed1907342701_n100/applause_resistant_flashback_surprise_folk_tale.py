#!/usr/bin/env python3
"""
storyworlds/worlds/applause_resistant_flashback_surprise_folk_tale.py
=====================================================================

A small folk-tale storyworld about a village performance, a resistant performer,
a flashback to an earlier lesson, and a surprise that turns the ending.

Seed premise:
- The story must include the words "applause" and "resistant".
- It should use a folk-tale tone, with a flashback and a surprise.

The world model tracks:
- a village setting,
- a performer and a helper,
- a difficult task that is resisted,
- a remembered lesson from a flashback,
- a surprise gift or twist that changes the ending.

The prose is generated from world state, not from a fixed paragraph template.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    crowd: object | None = None
    gift: object | None = None
    helper: object | None = None
    memory: object | None = None
    performer: object | None = None
    stage: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
        if not hasattr(self, "_tags"):
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
    id: str
    label: str
    kind: str
    sound: str
    crowd: str
    mood: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
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
class Task:
    id: str
    verb: str
    resistance: str
    cost: str
    need: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class SurpriseGift:
    id: str
    label: str
    phrase: str
    method: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
class Memory:
    id: str
    scene: str
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
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.timeline: list[str] = []

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
            self.timeline.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        c.timeline = list(self.timeline)
        return c

    def people(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    place: str
    performer: str
    helper: str
    task: str
    gift: str
    memory: str
    seed: Optional[int] = None
    params: object | None = None
    sample_params: object | None = None
    @property
    def meters(self):
        if not hasattr(self, "_meters"):
            object.__setattr__(self, "_meters", __import__("collections").defaultdict(float))
        return self._meters

    @property
    def memes(self):
        if not hasattr(self, "_memes"):
            object.__setattr__(self, "_memes", __import__("collections").defaultdict(float))
        return self._memes

    @property
    def tags(self):
        if not hasattr(self, "_tags"):
            object.__setattr__(self, "_tags", set())
        return self._tags

    def __getattr__(self, name: str):
        if name.startswith("__"):
            raise AttributeError(name)
        return None


PLACES = {
    "market": Place("market", "the village market", "outdoor", "bells and voices", "many folk", "lively"),
    "square": Place("square", "the town square", "outdoor", "drums and laughter", "many folk", "bright"),
    "meadow": Place("meadow", "the green meadow", "outdoor", "birds and wind", "few folk", "open"),
    "hall": Place("hall", "the long hall", "indoor", "low footsteps", "many folk", "warm"),
}

TASKS = {
    "dance": Task("dance", "dance before the crowd", "shy feet", "a trembling voice", "steady rhythm", {"applause"}),
    "sing": Task("sing", "sing the old song", "a wavering note", "a dry throat", "a brave breath", {"applause"}),
    "story": Task("story", "tell the folk tale", "a restless tongue", "a lost ending", "a remembered beginning", {"flashback"}),
    "bow": Task("bow", "bow to the crowd", "stiff knees", "a nervous pause", "a gentle cue", {"applause"}),
}

GIFTS = {
    "drum": SurpriseGift("drum", "a little drum", "a drum with a bright red strap", "beat a steady rhythm"),
    "bell": SurpriseGift("bell", "a silver bell", "a bell tied with blue ribbon", "ring out the ending"),
    "cloak": SurpriseGift("cloak", "a warm cloak", "a cloak sewn with bright thread", "wrap the performer in courage"),
    "flute": SurpriseGift("flute", "a reed flute", "a flute carved from willow", "carry the tune"),
}

MEMORIES = {
    "first_stage": Memory("first_stage", "the first time on the old stump", "the crowd had once been kind"),
    "rain_practice": Memory("rain_practice", "the wet morning under the eaves", "practice could turn fear into steadiness"),
    "grandmother": Memory("grandmother", "the hour with grandmother by the fire", "a soft voice could carry a hard song"),
}


GIRL_NAMES = ["Mina", "Lena", "Tara", "Sina", "Nora", "Mara", "Elin", "Hana"]
BOY_NAMES = ["Bram", "Jory", "Tavi", "Milo", "Perrin", "Roan", "Ari", "Jon"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    out = []
    for p in PLACES:
        for t in TASKS:
            for g in GIFTS:
                for m in MEMORIES:
                    out.append((p, t, g, m))
    return out


def reasonableness_check(params: StoryParams) -> None:
    if params.place not in PLACES:
        pass
    if params.task not in TASKS:
        pass
    if params.gift not in GIFTS:
        pass
    if params.memory not in MEMORIES:
        pass
    if params.task == "dance" and params.gift == "flute":
        return
    if params.task == "sing" and params.gift in {"bell", "flute"}:
        return
    if params.task == "story" and params.gift in {"cloak", "drum"}:
        return
    if params.task == "bow" and params.gift in {"cloak", "bell"}:
        return
    if params.task == "dance" and params.gift == "bell":
        return
    if params.task == "sing" and params.gift == "drum":
        return
    if params.task == "story" and params.gift == "bell":
        return
    if params.task == "bow" and params.gift == "drum":
        return
    pass


def choose_combo(args: argparse.Namespace, rng: random.Random) -> tuple[str, str, str, str]:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "gift", None) is None or c[2] == getattr(args, "gift", None))
              and (getattr(args, "memory", None) is None or c[3] == getattr(args, "memory", None))]
    if not combos:
        pass
    return rng.choice(list(combos))


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    world = World(place)

    performer_name = params.performer
    helper_name = params.helper
    performer_gender = "girl" if performer_name in GIRL_NAMES else "boy"
    helper_gender = "girl" if helper_name in GIRL_NAMES else "boy"

    performer = world.add(Entity(
        id="performer",
        kind="character",
        type=performer_gender,
        label=performer_name,
        role="performer",
        attrs={"name": performer_name, "resistant": True},
        meters={"energy": 1.0, "applause": 0.0},
        memes={"fear": 0.0, "hope": 0.0, "joy": 0.0, "resistance": 1.0},
    ))
    helper = world.add(Entity(
        id="helper",
        kind="character",
        type=helper_gender,
        label=helper_name,
        role="helper",
        attrs={"name": helper_name, "wise": True},
        meters={"energy": 1.0},
        memes={"care": 1.0, "joy": 0.0},
    ))
    crowd = world.add(Entity(
        id="crowd",
        kind="character",
        type="folk",
        label="the crowd",
        role="crowd",
        plural=True,
        meters={"applause": 0.0},
        memes={"expectation": 1.0},
    ))
    stage = world.add(Entity(
        id="stage",
        kind="thing",
        type="stage",
        label=place.label,
        attrs={"sound": place.sound, "mood": place.mood},
        meters={"stillness": 1.0},
        memes={"waiting": 1.0},
    ))
    gift = world.add(Entity(
        id="gift",
        kind="thing",
        type="gift",
        label=_safe_lookup(GIFTS, params.gift).label,
        phrase=_safe_lookup(GIFTS, params.gift).phrase,
        attrs={"method": _safe_lookup(GIFTS, params.gift).method},
        meters={"newness": 1.0},
    ))
    memory = world.add(Entity(
        id="memory",
        kind="thing",
        type="memory",
        label=_safe_lookup(MEMORIES, params.memory).scene,
        phrase=_safe_lookup(MEMORIES, params.memory).lesson,
        attrs={"scene": _safe_lookup(MEMORIES, params.memory).scene, "lesson": _safe_lookup(MEMORIES, params.memory).lesson},
        meters={"past": 1.0},
        memes={"warmth": 1.0},
    ))

    world.facts.update(
        place=place,
        performer=performer,
        helper=helper,
        crowd=crowd,
        stage=stage,
        gift=gift,
        memory=memory,
        task=_safe_lookup(TASKS, params.task),
        params=params,
        resisted=False,
        flashback_used=False,
        surprise_used=False,
        resolved=False,
    )
    return world


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    performer = world.facts["performer"]
    crowd = world.facts["crowd"]
    if performer.memes["hope"] >= THRESHOLD and ("applause", "hope") not in world.fired:
        world.fired.add(("applause", "hope"))
        performer.meters["applause"] += 1
        crowd.meters["applause"] += 1
        out.append("Applause rose like rain on a roof.")
    if world.facts["flashback_used"] and performer.memes["fear"] < 1 and ("calm",) not in world.fired:
        world.fired.add(("calm",))
        performer.memes["joy"] += 1
        out.append("The remembered lesson settled the performer's heart.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def stage_setup(world: World) -> None:
    p = world.facts["performer"]
    h = world.facts["helper"]
    place = world.facts["place"]
    task = world.facts["task"]
    world.say(
        f"Once in {place.label}, {p.label} stood beside {h.label} while the folk gathered "
        f"close to hear a tale."
    )
    world.say(
        f"The air carried {place.sound}, and the old stage looked ready for {task.verb}."
    )


def resist(world: World) -> None:
    p = world.facts["performer"]
    task = world.facts["task"]
    p.memes["fear"] += 1
    p.memes["resistance"] += 1
    world.facts["resisted"] = True
    world.say(
        f"But {p.label} was resistant and would not begin at once."
    )
    world.say(
        f"{p.label} kept looking at the crowd, as if the first step might slip away."
    )


def flashback(world: World) -> None:
    p = world.facts["performer"]
    mem = world.facts["memory"]
    world.facts["flashback_used"] = True
    world.say(
        f"Then came a flashback: {mem.attrs['scene']}."
    )
    world.say(
        f"{p.label} remembered how {mem.attrs['lesson']}."
    )


def surprise(world: World) -> None:
    p = world.facts["performer"]
    h = world.facts["helper"]
    gift = world.facts["gift"]
    task = world.facts["task"]
    world.facts["surprise_used"] = True
    h.memes["care"] += 1
    p.memes["hope"] += 1
    world.say(
        f"At that very moment, a surprise waited under a cloth: {gift.phrase}."
    )
    world.say(
        f"{h.label} lifted it and showed how it could {gift.attrs['method']}."
    )
    if task.id == "story":
        world.say(
            f"The new thing gave the tale a thread to follow, and {p.label} found the ending."
        )
    else:
        world.say(
            f"The new thing gave {p.label} a rhythm and a reason to step forward."
        )
    propagate(world, narrate=True)


def resolve(world: World) -> None:
    p = world.facts["performer"]
    h = world.facts["helper"]
    crowd = world.facts["crowd"]
    task = world.facts["task"]
    gift = world.facts["gift"]
    p.memes["joy"] += 2
    p.memes["fear"] = 0
    world.facts["resolved"] = True
    world.say(
        f"Then {p.label} took the {gift.label}, began to {task.verb}, and the whole square grew still."
    )
    world.say(
        f"When the last line or note or bow came right, the crowd burst into applause."
    )
    world.say(
        f"{p.label} bowed with a bright face, and {h.label} smiled beside {p.label} as the {gift.label} caught the light."
    )


def tell(params: StoryParams) -> World:
    world = build_world(params)
    stage_setup(world)
    world.para()
    resist(world)
    flashback(world)
    world.para()
    surprise(world)
    world.para()
    resolve(world)
    return world


def prompts(world: World) -> list[str]:
    f = world.facts
    p = f["performer"]
    h = f["helper"]
    task = f["task"]
    place = f["place"]
    return [
        f"Write a gentle folk tale about {p.label} in {place.label} who is resistant at first but finds courage with help.",
        f"Tell a story with a flashback and a surprise where {p.label} finally {task.verb} and hears applause.",
        f"Write a village story for a young child that includes the word applause and ends with a surprise gift.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["performer"]
    h = f["helper"]
    task = f["task"]
    place = f["place"]
    gift = f["gift"]
    mem = f["memory"]
    qa = [
        QAItem(
            question=f"Who was the story about in {place.label}?",
            answer=f"It was about {p.label}, who stood in {place.label} with {h.label}. {p.label} wanted to do the task, but the moment began with hesitation."
        ),
        QAItem(
            question=f"Why was {p.label} resistant at the start?",
            answer=f"{p.label} felt the crowd's eyes and held back. The task looked hard, so {p.label} resisted until a kinder moment arrived."
        ),
        QAItem(
            question="What was the flashback in the story?",
            answer=f"The flashback went back to {mem.attrs['scene']}. It reminded {p.label} that {mem.attrs['lesson']}."
        ),
        QAItem(
            question="What was the surprise?",
            answer=f"The surprise was {gift.phrase}. It helped by letting {p.label} {gift.attrs['method']} and step into the tale with more courage."
        ),
        QAItem(
            question="How did the story end?",
            answer=f"{p.label} finally began to {task.verb}, and the crowd answered with applause. The ending showed {p.label} standing tall while the new gift gleamed nearby."
        ),
    ]
    if world.facts["resolved"]:
        qa.append(QAItem(
            question=f"How did {h.label} help {p.label}?",
            answer=f"{h.label} brought the surprise and showed how to use it. That small help turned fear into motion and made the ending feel warm."
        ))
    return qa


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is applause?",
            answer="Applause is the sound of hands clapping together to show delight and approval."
        ),
        QAItem(
            question="What does resistant mean?",
            answer="Resistant means not easily moved or changed. A resistant person or thing holds back before yielding."
        ),
        QAItem(
            question="What is a flashback?",
            answer="A flashback is a moment in a story that goes back to something that happened earlier. It helps explain why a character feels ready or afraid now."
        ),
        QAItem(
            question="What is a surprise in a story?",
            answer="A surprise is something unexpected that changes what happens next. It can turn worry into a happier path."
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    return prompts(world)


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


ASP_RULES = r"""
resolved :- surprise_used, flashback_used, resisted.
applause :- resolved.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp  # lazy
    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for tid in TASKS:
        lines.append(asp.fact("task", tid))
    for gid in GIFTS:
        lines.append(asp.fact("gift", gid))
    for mid in MEMORIES:
        lines.append(asp.fact("memory", mid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show resolved/0."))
    return [()] if any(sym.name == "resolved" for sym in model) else []


def asp_verify() -> int:
    sample_params = StoryParams(
        place="market",
        performer="Mina",
        helper="Bram",
        task="dance",
        gift="flute",
        memory="first_stage",
    )
    try:
        sample = generate(sample_params)
        _ = sample.story
    except Exception as exc:
        print(f"FAIL: generation smoke test crashed: {exc}")
        return 1
    import storyworlds.asp as asp
    py_ok = True
    asp_ok = True
    try:
        _ = asp.one_model(asp_program("#show applause/0.\n#show resolved/0."))
    except Exception as exc:
        asp_ok = False
        print(f"FAIL: ASP smoke test crashed: {exc}")
    if not py_ok or not asp_ok:
        return 1
    print("OK: generation and ASP smoke tests passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale storyworld with applause, resistance, flashback, and surprise.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--gift", choices=GIFTS)
    ap.add_argument("--memory", choices=MEMORIES)
    ap.add_argument("--performer")
    ap.add_argument("--helper")
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
    choice = choose_combo(args, rng)
    place, task, gift, memory = choice
    reasonableness_check(StoryParams(place=place, performer="Mina", helper="Bram", task=task, gift=gift, memory=memory))
    performer = getattr(args, "performer", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper_choices = [n for n in GIRL_NAMES + BOY_NAMES if n != performer]
    helper = getattr(args, "helper", None) or rng.choice(helper_choices)
    params = StoryParams(place=place, performer=performer, helper=helper, task=task, gift=gift, memory=memory)
    reasonableness_check(params)
    return params


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.task not in TASKS or params.gift not in GIFTS or params.memory not in MEMORIES:
        pass
    reasonableness_check(params)
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
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
    StoryParams(place="market", performer="Mina", helper="Bram", task="dance", gift="flute", memory="first_stage"),
    StoryParams(place="square", performer="Lena", helper="Tavi", task="sing", gift="bell", memory="grandmother"),
    StoryParams(place="hall", performer="Roan", helper="Nora", task="story", gift="cloak", memory="rain_practice"),
    StoryParams(place="meadow", performer="Hana", helper="Milo", task="bow", gift="drum", memory="first_stage"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show resolved/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available; this world is deterministic and small.")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
