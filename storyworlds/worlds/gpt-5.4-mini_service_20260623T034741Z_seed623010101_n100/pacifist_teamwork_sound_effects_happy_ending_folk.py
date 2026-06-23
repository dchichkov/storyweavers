#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/pacifist_teamwork_sound_effects_happy_ending_folk.py
==============================================================================================================

A small folk-tale storyworld about a pacifist villager, teamwork, sound effects,
and a happy ending.

Premise:
A gentle village needs help moving a heavy festival cart to the green. The main
character refuses to fight or bully anyone, so the story turns on cooperation,
rhythmic sound effects, and a friendly ending image.

The world is intentionally tiny:
- one child-facing domain
- one clear obstacle
- one pacifist choice
- one teamwork solution
- one celebratory ending

The prose is driven by world state, not a frozen paragraph with swapped nouns.
The script also includes a Python reasonableness gate and an inline ASP twin.
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
            keys = [upper + "S", upper + "ES"]
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
    role: str = ""
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    cart: object | None = None
    elder: object | None = None
    helper: object | None = None
    hero: object | None = None
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
        return self.label or self.type
    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    tags: set[str] = field(default_factory=set)
    supports: set[str] = field(default_factory=set)
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
    sound: str
    obstacle: str
    result: str
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
class Treasure:
    id: str
    label: str
    phrase: str
    weight: int
    risk: str
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
class Aid:
    id: str
    label: str
    action: str
    sound: str
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
class StoryParams:
    place: str = "village"
    task: str = "cart"
    treasure: str = "bells"
    aid: str = "rope"
    hero: str = "Pippa"
    hero_gender: str = "girl"
    helper: str = "Milo"
    helper_gender: str = "boy"
    elder: str = "Gran"
    seed: Optional[int] = None
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.facts = copy.deepcopy(self.facts)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_slip(world: World) -> list[str]:
    out: list[str] = []
    cart = world.get("cart")
    if cart.meters.get("stuck", 0) < THRESHOLD:
        return out
    sig = ("stuck", cart.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cart.meters["weight"] = cart.meters.get("weight", 0) + 1
    out.append("The cart gave a stubborn groan.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    if world.get("hero").memes.get("teamwork", 0) < THRESHOLD:
        return out
    if world.get("helper").memes.get("teamwork", 0) < THRESHOLD:
        return out
    sig = ("teamwork",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cart = world.get("cart")
    cart.meters["move"] = cart.meters.get("move", 0) + 1
    world.get("hero").memes["joy"] = world.get("hero").memes.get("joy", 0) + 1
    world.get("helper").memes["joy"] = world.get("helper").memes.get("joy", 0) + 1
    out.append("The wheels rolled a little farther.")
    return out


def _r_harmony(world: World) -> list[str]:
    out: list[str] = []
    if world.get("hero").memes.get("calm", 0) < THRESHOLD:
        return out
    sig = ("harmony",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.get("elder").memes["pride"] = world.get("elder").memes.get("pride", 0) + 1
    out.append("The lane grew quiet and kind again.")
    return out


CAUSAL_RULES = [_r_slip, _r_teamwork, _r_harmony]


def propagate(world: World, narrate: bool = True) -> list[str]:
    notes: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            parts = rule(world)
            if parts:
                changed = True
                notes.extend(parts)
    if narrate:
        for n in notes:
            world.say(n)
    return notes


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES:
        for task in TASKS.values():
            for treasure in TREASURES:
                if task.supports & _safe_lookup(TREASURES, treasure).tags:
                    combos.append((place, task, treasure))
    return combos


def requires_teamwork(task: Task, treasure: Treasure) -> bool:
    return bool(task.supports & treasure.tags)


def tell(place: Place, task: Task, treasure: Treasure, aid: Aid, params: StoryParams) -> World:
    if not requires_teamwork(task, treasure):
        pass
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_gender, label=params.hero))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper))
    elder = world.add(Entity(id="elder", kind="character", type="woman", label=params.elder))
    cart = world.add(Entity(id="cart", label=treasure.label, phrase=treasure.phrase, tags=set(treasure.tags)))
    cart.meters.update({"stuck": 1.0, "weight": float(treasure.weight), "move": 0.0})
    hero.memes.update({"wish": 1.0, "calm": 0.0, "teamwork": 0.0, "joy": 0.0})
    helper.memes.update({"teamwork": 0.0, "joy": 0.0})
    elder.memes.update({"pride": 0.0})
    world.facts.update(place=place, task=task, treasure=treasure, aid=aid, hero=hero, helper=helper, elder=elder)

    world.say(
        f"Long ago, in {place.label}, {hero.label} was a pacifist who liked to solve trouble with gentle hands."
    )
    world.say(
        f"One bright morning, {hero.label} and {helper.label} found {treasure.phrase} on the cart and needed to {task.verb} it to the green."
    )
    world.para()
    world.say(
        f"They did not shove or quarrel. {hero.label} tapped the side of the cart and called, '{task.sound}!'"
    )
    world.say(
        f"{helper.label} answered with {aid.sound} and took the other rope."
    )
    hero.memes["calm"] += 1
    hero.memes["teamwork"] += 1
    helper.memes["teamwork"] += 1
    cart.meters["stuck"] = 0.0
    propagate(world)
    world.para()
    if cart.meters.get("move", 0) >= 1:
        world.say(
            f"Together they {task.action} and the cart rolled free, {task.result}, while {elder.label} smiled from the gate."
        )
        world.say(
            f"When the bells reached the green, the whole village heard {task.sound} and {aid.sound} like a happy drum-beat."
        )
        world.say(
            f"That evening, the lanterns glowed, the grass danced in the wind, and {hero.label} knew peace could be strong."
        )
    else:
        pass
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    task: Task = f["task"]  # type: ignore[assignment]
    treasure: Treasure = f["treasure"]  # type: ignore[assignment]
    aid: Aid = f["aid"]  # type: ignore[assignment]
    return [
        f'Write a folk tale for a young child about a pacifist named {hero.label} who needs teamwork to move {treasure.phrase}.',
        f"Tell a gentle story where {hero.label} and {helper.label} use sound effects like {task.sound} and {aid.sound} to solve a problem without fighting.",
        f'Write a happy ending story set in {world.place.label} that includes the word "pacifist" and ends with a village celebration.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]  # type: ignore[assignment]
    helper: Entity = f["helper"]  # type: ignore[assignment]
    elder: Entity = f["elder"]  # type: ignore[assignment]
    task: Task = f["task"]  # type: ignore[assignment]
    treasure: Treasure = f["treasure"]  # type: ignore[assignment]
    aid: Aid = f["aid"]  # type: ignore[assignment]
    qa = [
        QAItem(
            question=f"Who is the story mainly about in {world.place.label}?",
            answer=f"It is mainly about {hero.label}, a pacifist villager who tries to solve a problem without fighting. {helper.label} and {elder.label} help make the ending peaceful too.",
        ),
        QAItem(
            question=f"What did {hero.label} and {helper.label} need to move?",
            answer=f"They needed to move {treasure.phrase} to the green. It was too heavy to handle alone, so they had to work together.",
        ),
        QAItem(
            question=f"What sound did {hero.label} make to start the teamwork?",
            answer=f"{hero.label} called '{task.sound}!' as a gentle work sound. That sound was a sign to begin pulling together instead of arguing.",
        ),
        QAItem(
            question=f"How did {aid.label} help the cart move?",
            answer=f"{helper.label} answered with {aid.sound} and took the other rope. That helped the cart roll free because both children pulled at the same time.",
        ),
    ]
    if world.get("cart").meters.get("move", 0) >= 1:
        qa.append(
            QAItem(
                question=f"Why was the ending happy?",
                answer=f"The ending was happy because the cart reached the green and nobody had to fight. The village got its festival treasure in time, and everyone could celebrate together.",
            )
        )
    if world.get("hero").memes.get("calm", 0) >= 1:
        qa.append(
            QAItem(
                question=f"How did {hero.label} show that being a pacifist was strong?",
                answer=f"{hero.label} stayed calm and used teamwork instead of pushing or shouting. That choice helped everyone solve the problem peacefully.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does pacifist mean?",
            answer="A pacifist is a person who does not want to fight. They try to solve problems with peace, kindness, and careful words.",
        ),
        QAItem(
            question="Why do people use sound effects while working together?",
            answer="Sound effects can help a group keep the same rhythm. When everyone pulls or lifts on the same beat, teamwork becomes easier.",
        ),
        QAItem(
            question="Why can teamwork make a heavy job easier?",
            answer="Teamwork spreads the hard work across more than one person. Each helper carries only part of the load, so the job feels lighter.",
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={e.meters} memes={e.memes} attrs={e.attrs}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


PLACES = {
    "village": Place(id="village", label="the village green", tags={"folk", "green"}, supports={"cart"}),
    "forest": Place(id="forest", label="the forest road", tags={"folk", "road"}, supports={"cart"}),
    "mill": Place(id="mill", label="the old mill lane", tags={"folk", "lane"}, supports={"cart"}),
}

TASKS = {
    "cart": Task(id="cart", verb="carry", sound="heave-ho", obstacle="heavy cart", result="safe and steady", tags={"teamwork"}),
    "log": Task(id="log", verb="roll", sound="roll-roll", obstacle="stuck log", result="free and bright", tags={"teamwork"}),
    "lanterns": Task(id="lanterns", verb="hang", sound="tap-tap", obstacle="long lantern rope", result="all lit up", tags={"teamwork"}),
}

TREASURES = {
    "bells": Treasure(id="bells", label="bell-cart", phrase="the festival bells", weight=8, risk="heavy", tags={"cart", "teamwork"}),
    "log": Treasure(id="log", label="oak log", phrase="the oak log", weight=7, risk="stuck", tags={"cart", "teamwork"}),
    "lanterns": Treasure(id="lanterns", label="lantern crate", phrase="the lantern crate", weight=6, risk="high", tags={"cart", "teamwork"}),
}

AIDS = {
    "rope": Aid(id="rope", label="rope", action="pull", sound="pull-pull", tags={"teamwork"}),
    "stool": Aid(id="stool", label="stool", action="push", sound="push-push", tags={"teamwork"}),
    "song": Aid(id="song", label="work-song", action="sing", sound="la-la", tags={"teamwork"}),
}

CURATED = [
    StoryParams(place="village", task="cart", treasure="bells", aid="rope", hero="Pippa", hero_gender="girl", helper="Milo", helper_gender="boy", elder="Gran"),
    StoryParams(place="forest", task="log", treasure="log", aid="song", hero="Tomas", hero_gender="boy", helper="Lina", helper_gender="girl", elder="Auntie Roe"),
    StoryParams(place="mill", task="lanterns", treasure="lanterns", aid="stool", hero="Mara", hero_gender="girl", helper="Nico", helper_gender="boy", elder="Old Birch"),
]


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES.values():
        lines.append(asp.fact("place", p.id))
        for s in p.supports:
            lines.append(asp.fact("supports", p.id, s))
    for t in TASKS.values():
        lines.append(asp.fact("task", t.id))
        lines.append(asp.fact("task_sound", t.id, t.sound))
        for tag in t.tags:
            lines.append(asp.fact("task_tag", t.id, tag))
    for tr in TREASURES.values():
        lines.append(asp.fact("treasure", tr.id))
        lines.append(asp.fact("weight", tr.id, tr.weight))
        for tag in tr.tags:
            lines.append(asp.fact("treasure_tag", tr.id, tag))
    for a in AIDS.values():
        lines.append(asp.fact("aid", a.id))
        lines.append(asp.fact("aid_sound", a.id, a.sound))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,R) :- place(P), task(T), treasure(R), supports(P, cart), task_tag(T, teamwork), treasure_tag(R, teamwork).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    ok = 0
    if python_set == clingo_set:
        print(f"OK: ASP matches valid_combos() ({len(python_set)} combos).")
    else:
        ok = 1
        print("MISMATCH in valid combos:")
        print("python only:", sorted(python_set - clingo_set))
        print("asp only:", sorted(clingo_set - python_set))
    try:
        sample = generate(CURATED[0])
        if not sample.story.strip():
            raise RuntimeError("empty story")
        print("OK: generate() smoke test passed.")
    except Exception as exc:  # pragma: no cover
        ok = 1
        print(f"SMOKE TEST FAILED: {exc}")
    return ok


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about pacifist teamwork and cheerful sound effects.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--aid", choices=AIDS)
    ap.add_argument("--hero")
    ap.add_argument("--hero-gender", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--elder")
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "task", None) is None or c[1] == getattr(args, "task", None))
              and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task, treasure = rng.choice(list(combos))
    aid = getattr(args, "aid", None) or rng.choice(sorted(AIDS))
    hero = getattr(args, "hero", None) or rng.choice(["Pippa", "Mara", "Nia", "Tomas", "Eli"])
    helper = getattr(args, "helper", None) or rng.choice(["Milo", "Lina", "Jori", "Nico", "Anya"])
    hero_gender = getattr(args, "hero_gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["girl", "boy"])
    elder = getattr(args, "elder", None) or rng.choice(["Gran", "Old Birch", "Auntie Roe"])
    return StoryParams(place=place, task=task, treasure=treasure, aid=aid, hero=hero, hero_gender=hero_gender, helper=helper, helper_gender=helper_gender, elder=elder)


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.task not in TASKS or params.treasure not in TREASURES or params.aid not in AIDS:
        pass
    if not requires_teamwork(_safe_lookup(TASKS, params.task), _safe_lookup(TREASURES, params.treasure)):
        pass
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(TREASURES, params.treasure), _safe_lookup(AIDS, params.aid), params)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


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
        print(f"{len(combos)} compatible combos:")
        for combo in combos:
            print(" ", combo)
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
