#!/usr/bin/env python3
"""
storyworlds/worlds/wok_lesson_learned_dialogue_animal_story.py
==============================================================

A small animal-story world about a wok, a little mistake, and a lesson
learned through dialogue.

The seed tale behind this world:
A hungry young animal wants to cook with a shiny wok. The animal gets too
excited, makes a smoky mess, and worries the others. A friend explains a
safer way to cook, and the animal learns to listen, take turns, and use the
wok carefully.

This world keeps the simulation small:
- one animal cook
- one helper friend
- one wok
- one snack being prepared
- a single kitchen-like setting

The turn is state-driven:
- heat and impatience can create smoke or a spill
- smoke raises worry
- a dialogue offer can lower worry and restore trust
- the learned lesson is narrated at the end
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
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    cook: object | None = None
    food: object | None = None
    friend: object | None = None
    helper: object | None = None
    wok: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen", "owl", "cat", "fox"}
        male = {"boy", "father", "dad", "man", "bear", "dog", "rabbit", "rat", "mouse"}
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
    place: str = "the little kitchen"
    affords: set[str] = field(default_factory=set)
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
class Snack:
    id: str
    label: str
    phrase: str
    cook_verb: str
    smell: str
    danger: str
    messy_if_rushed: bool = True
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
class Tool:
    id: str
    label: str
    phrase: str
    safe_when: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
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

    def copy(self) -> "World":
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    animal: str
    helper: str
    snack: str
    name: str
    friend_name: str
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


SETTINGS = {
    "kitchen": Setting(place="the little kitchen", affords={"stir-fry", "toast", "noodle"}),
}

ANIMALS = {
    "fox": {"girl", "boy"},
    "bear": {"boy"},
    "rabbit": {"girl", "boy"},
    "owl": {"girl", "boy"},
    "cat": {"girl", "boy"},
}

ANIMAL_NAMES = {
    "fox": ["Fiona", "Finn"],
    "bear": ["Benny", "Bella"],
    "rabbit": ["Rory", "Ruby"],
    "owl": ["Ollie", "Opal"],
    "cat": ["Cleo", "Coco"],
}

FRIEND_NAMES = ["Milo", "Mina", "Pip", "Poppy", "Teddy", "Tia"]
TRAITS = ["curious", "eager", "brave", "bouncy", "gentle", "restless"]

SNACKS = {
    "noodle": Snack(
        id="noodle",
        label="noodles",
        phrase="a bowl of noodles",
        cook_verb="stir-fry noodles",
        smell="savory",
        danger="too smoky",
    ),
    "toast": Snack(
        id="toast",
        label="toast",
        phrase="slices of toast",
        cook_verb="toast bread",
        smell="toasty",
        danger="too dark",
    ),
    "stir-fry": Snack(
        id="stir-fry",
        label="stir-fry",
        phrase="a bright stir-fry",
        cook_verb="stir-fry vegetables",
        smell="warm and tasty",
        danger="too hot",
    ),
}

TOOLS = {
    "wok": Tool(
        id="wok",
        label="wok",
        phrase="a shiny wok",
        safe_when={"stir-fry", "noodle"},
    ),
}


class Mood:
    def __init__(self) -> None:
        self.values = {"joy": 0.0, "worry": 0.0, "trust": 0.0, "lesson": 0.0, "rush": 0.0}


def _m(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mm(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _say(world: World, text: str) -> None:
    world.say(text)


def predict_problem(world: World, cook: Entity, snack: Snack) -> dict:
    sim = world.copy()
    c = sim.get(cook.id)
    c.memes["rush"] = c.memes.get("rush", 0.0) + 1
    c.meters["heat"] = c.meters.get("heat", 0.0) + 1
    c.meters["mess"] = c.meters.get("mess", 0.0) + (1 if snack.messy_if_rushed else 0)
    smoke = c.meters.get("smoke", 0.0) + (1 if c.meters["heat"] >= THRESHOLD and c.meters["mess"] >= THRESHOLD else 0)
    return {"smoke": smoke >= THRESHOLD, "mess": c.meters["mess"] >= THRESHOLD}


def tell(setting: Setting, snack: Snack, hero_name: str, friend_name: str, hero_type: str, friend_type: str, trait: str) -> World:
    world = World(setting)
    cook = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, traits=["kind", "careful"]))
    wok = world.add(Entity(id="wok", type="wok", label="wok", phrase="a shiny wok", owner=cook.id))
    food = world.add(Entity(id="snack", type=snack.id, label=snack.label, phrase=snack.phrase, caretaker=cook.id))
    helper = world.add(Entity(id="helper", type=friend_type, label=friend_name))
    world.facts.update(cook=cook, friend=friend, wok=wok, food=food, snack=snack, helper=helper)

    _say(world, f"{cook.id} was a little {trait} {cook.type} who loved to cook.")
    _say(world, f"{cook.id} liked {snack.cook_verb} in {setting.place} because the wok made the food sizzle.")
    _say(world, f"One day, {cook.id} found {wok.phrase} and wanted to use it right away.")

    world.para()
    _say(world, f"{cook.id} asked, \"Can I cook now?\"")
    _say(world, f"{friend.id} said, \"Only if you go slowly and keep your paws steady.\"")
    cook.memes["rush"] = 1
    cook.memes["joy"] = 1
    cook.meters["heat"] = 1
    world.facts["predicted"] = predict_problem(world, cook, snack)

    if world.facts["predicted"]["smoke"]:
        _say(world, f"{cook.id} tried to hurry anyway, and the wok got too hot.")
        cook.meters["mess"] = cook.meters.get("mess", 0.0) + 1
        cook.meters["smoke"] = cook.meters.get("smoke", 0.0) + 1
        friend.memes["worry"] = friend.memes.get("worry", 0.0) + 1
        _say(world, f"A puff of smoke rose up. \"Oh no,\" said {friend.id}, \"that can make everyone cough.\"")
        _say(world, f"{cook.id} looked down and whispered, \"I was too fast.\"")
    else:
        _say(world, f"{cook.id} moved carefully, and the wok stayed calm.")

    world.para()
    if _mm(cook, "rush") >= THRESHOLD:
        _say(world, f"{friend.id} smiled and said, \"A wok works best when the cook listens to the food.\"")
        _say(world, f"\"If the pan starts to hiss too hard, take a breath and lower the heat,\" said {friend.id}.")
        cook.memes["lesson"] = 1
        cook.memes["trust"] = 1
        cook.memes["rush"] = 0
        cook.meters["heat"] = 0
        cook.meters["smoke"] = 0
        _say(world, f"{cook.id} nodded. \"I learned it,\" {cook.id} said. \"Slow paws make safer soup.\"")
        _say(world, f"So {cook.id} stirred gently, and the snack finished cooking without more smoke.")
        _say(world, f"In the end, {cook.id} shared {snack.phrase} with {friend.id}, and the wok stayed shiny.")
    else:
        _say(world, f"{cook.id} whispered, \"I can do it slowly,\" and {friend.id} nodded.")
        _say(world, f"Together they finished {snack.phrase}, and the kitchen smelled warm and good.")
        cook.memes["lesson"] = 1
        cook.memes["trust"] = 1

    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    cook = _safe_fact(world, f, "cook")
    snack = _safe_fact(world, f, "snack")
    friend = _safe_fact(world, f, "friend")
    return [
        f'Write an animal story for a young child that includes a wok, dialogue, and the lesson "{cook.id} should slow down."',
        f"Tell a gentle story where {cook.id} tries to cook {snack.phrase} with a wok and {friend.id} helps with advice.",
        f'Write a simple animal story about a wok where a fast animal learns a safer way to cook.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cook = _safe_fact(world, f, "cook")
    friend = _safe_fact(world, f, "friend")
    snack = _safe_fact(world, f, "snack")
    out = [
        QAItem(
            question=f"Who wanted to use the wok in the story?",
            answer=f"{cook.id}, the little {cook.type}, wanted to use the wok to cook {snack.phrase}.",
        ),
        QAItem(
            question=f"What did {friend.id} tell {cook.id} to do?",
            answer=f"{friend.id} told {cook.id} to go slowly, keep steady paws, and lower the heat if the wok got too hot.",
        ),
        QAItem(
            question=f"What lesson did {cook.id} learn?",
            answer=f"{cook.id} learned that slow paws and careful cooking make a safer, better meal.",
        ),
    ]
    if f["predicted"]["smoke"]:
        out.append(
            QAItem(
                question=f"Why did the friend worry when {cook.id} rushed?",
                answer=f"The wok got too hot and a puff of smoke rose up, so {friend.id} worried the animal friends might cough.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a wok?",
            answer="A wok is a round, deep pan used for cooking food quickly with stirring.",
        ),
        QAItem(
            question="Why should a cook be careful around hot pans?",
            answer="Hot pans can burn paws or hands and can make smoke if food is left too long.",
        ),
        QAItem(
            question="What does it mean to learn a lesson?",
            answer="It means understanding a better way to do something after making a mistake or hearing good advice.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story Q&A ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_invalid(snack: Snack) -> str:
    return f"(No story: this snack cannot be taught with the wok in a reasonable way.)"


CURATED = [
    StoryParams(animal="fox", helper="rabbit", snack="noodle", name="Fiona", friend_name="Rory", trait="curious"),
    StoryParams(animal="bear", helper="owl", snack="stir-fry", name="Benny", friend_name="Opal", trait="eager"),
    StoryParams(animal="cat", helper="fox", snack="toast", name="Cleo", friend_name="Finn", trait="restless"),
]


ASP_RULES = r"""
% Facts represent the tiny cooking world.
% A cook can have a problem if rushing + heat create smoke.
problem(C,S) :- cook(C), snack(S), rush(C), heat(C), messy(S).
lesson_learned(C) :- problem(C,_), advice(_).
safe_finish(C,S) :- cook(C), snack(S), lesson_learned(C), wok_ok(S).
valid_story(C,S) :- safe_finish(C,S).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for sid, s in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("messy", sid) if s.messy_if_rushed else asp.fact("calm", sid))
        lines.append(asp.fact("wok_ok", sid) if "stir-fry" in s.cook_verb or sid in {"noodle", "stir-fry"} else asp.fact("wok_ok", sid))
    for aid in ANIMALS:
        lines.append(asp.fact("cook", aid))
    lines.append(asp.fact("advice", "friend"))
    lines.append(asp.fact("rush", "fox"))
    lines.append(asp.fact("heat", "fox"))
    lines.append(asp.fact("wok", "wok"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    prog = asp_program("#show valid_story/2.")
    model = asp.one_model(prog)
    atoms = set(asp.atoms(model, "valid_story"))
    py = {(p.animal, p.snack) for p in valid_combos()}
    if atoms == py:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    print("clingo only:", sorted(atoms - py))
    print("python only:", sorted(py - atoms))
    return 1


def valid_combos() -> list[StoryParams]:
    combos: list[StoryParams] = []
    for animal, genders in ANIMALS.items():
        for snack in SNACKS:
            if snack in {"noodle", "stir-fry"}:
                combos.append(StoryParams(animal=animal, helper="owl", snack=snack, name="", friend_name="", trait="curious"))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with a wok, dialogue, and a lesson learned.")
    ap.add_argument("--animal", choices=sorted(ANIMALS))
    ap.add_argument("--snack", choices=sorted(SNACKS))
    ap.add_argument("--name")
    ap.add_argument("--friend-name")
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
    animal = getattr(args, "animal", None) or rng.choice(sorted(ANIMALS))
    snack = getattr(args, "snack", None) or rng.choice(sorted(SNACKS))
    if snack not in {"noodle", "stir-fry"}:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(ANIMAL_NAMES, animal))
    friend_name = getattr(args, "friend_name", None) or rng.choice(FRIEND_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    helper = "owl"
    return StoryParams(animal=animal, helper=helper, snack=snack, name=name, friend_name=friend_name, trait=trait)


def generate(params: StoryParams) -> StorySample:
    snack = _safe_lookup(SNACKS, params.snack)
    world = tell(SETTINGS["kitchen"], snack, params.name, params.friend_name, params.animal, params.helper, params.trait)
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
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/2."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(combos)} valid stories:")
        for a, s in combos:
            print(f"  {a} + {s}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in CURATED:
            samples.append(generate(p))
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
            header = f"### {p.name}: {p.animal} cooks {p.snack}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
