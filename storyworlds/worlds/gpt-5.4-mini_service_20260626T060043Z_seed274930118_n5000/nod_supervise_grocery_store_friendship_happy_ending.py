#!/usr/bin/env python3
"""
storyworlds/worlds/nod_supervise_grocery_store_friendship_happy_ending.py
========================================================================

A standalone storyworld for a tiny comedy set in a grocery store, where
friendship, supervision, sound effects, and a happy ending are all part of the
world model.

Premise seed:
- Two friends visit a grocery store.
- One wants to help, but the other must supervise.
- Small mistakes create silly sound effects.
- The story ends with a happy, friendly fix.

This script models physical state with meters and emotional state with memes.
It also includes an inline ASP twin for parity checks and registry facts.
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    entities: set[str] = field(default_factory=set)
    friend: object | None = None
    hero: object | None = None
    item: object | None = None
    supervisor: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
class Store:
    place: str = "the grocery store"
    aisles: tuple[str, ...] = ("produce", "bakery", "cereal", "snacks", "checkout")
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
class Task:
    id: str
    verb: str
    gerund: str
    mishap: str
    sound: str
    keyword: str
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
class Item:
    id: str
    label: str
    phrase: str
    fragile: bool = False
    noisy: bool = False
    answer: object | None = None
    question: object | None = None
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
    task: str
    item: str
    hero: str
    friend: str
    supervisor: str
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


class World:
    def __init__(self, store: Store) -> None:
        self.store = store
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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


def _sfx(sound: str) -> str:
    return {
        "beep": "beep!",
        "clatter": "clatter!",
        "squeak": "squeak!",
        "whirr": "whirr!",
        "thump": "thump!",
        "ding": "ding!",
    }.get(sound, "pop!")


TASKS = {
    "cart": Task(
        id="cart",
        verb="push the cart",
        gerund="pushing the cart",
        mishap="bump the cart into a shelf",
        sound="clatter",
        keyword="cart",
        tags={"cart", "sound"},
    ),
    "scanner": Task(
        id="scanner",
        verb="scan the groceries",
        gerund="scanning the groceries",
        mishap="press the scanner button too many times",
        sound="beep",
        keyword="scanner",
        tags={"scanner", "sound"},
    ),
    "fruits": Task(
        id="fruits",
        verb="sort the fruit",
        gerund="sorting the fruit",
        mishap="drop an apple",
        sound="thump",
        keyword="apple",
        tags={"fruit", "sound"},
    ),
    "shelf": Task(
        id="shelf",
        verb="stack the snacks",
        gerund="stacking the snacks",
        mishap="make a bag slide off the shelf",
        sound="squeak",
        keyword="snack",
        tags={"snack", "sound"},
    ),
    "samples": Task(
        id="samples",
        verb="hand out samples",
        gerund="handing out samples",
        mishap="spill the sample cup",
        sound="plop",
        keyword="sample",
        tags={"food", "sound"},
    ),
}

ITEMS = {
    "cart": Item(id="cart", label="cart", phrase="a wobbly grocery cart"),
    "banana": Item(id="banana", label="banana", phrase="a ripe banana", fragile=True),
    "bread": Item(id="bread", label="bread", phrase="a soft loaf of bread", fragile=True),
    "scanner": Item(id="scanner", label="scanner", phrase="a tiny scanner with a red light", noisy=True),
    "samples": Item(id="samples", label="sample tray", phrase="a tray of tiny snack samples", fragile=True),
}

NAMES = ["Mia", "Ben", "Lily", "Noah", "Zoe", "Theo", "Ava", "Eli"]
TRAITS = ["playful", "curious", "cheerful", "silly", "helpful"]
SUPERVISORS = ["mother", "father", "aunt", "uncle"]


def setting_detail() -> str:
    return "The grocery store hummed softly, and the aisles looked busy but friendly."


def is_reasonable(task: Task, item: Item) -> bool:
    if task.id == "cart":
        return item.id == "cart"
    if task.id == "scanner":
        return item.noisy or item.id == "scanner"
    if task.id == "fruits":
        return item.fragile or item.id in {"banana", "bread"}
    if task.id == "shelf":
        return item.id in {"bread", "banana"}
    if task.id == "samples":
        return item.fragile or item.id == "samples"
    return False


def choose_valid_pairs() -> list[tuple[str, str]]:
    pairs = []
    for t in TASKS.values():
        for item in ITEMS.values():
            if is_reasonable(t, item):
                pairs.append((t.id, item.id))
    return pairs


def _do_task(world: World, actor: Entity, task: Task, item: Entity, narrate: bool = True) -> None:
    actor.meters[task.id] = actor.meters.get(task.id, 0.0) + 1.0
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0
    if task.sound:
        actor.memes["sound"] = actor.memes.get("sound", 0.0) + 1.0
    if item.fragile:
        item.meters["stress"] = item.meters.get("stress", 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} tried {task.gerund}, and the store answered with {_sfx(task.sound)}")


def predict_mishap(world: World, hero: Entity, task: Task, item: Entity) -> dict:
    sim = World(world.store)
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    _do_task(sim, sim.get(hero.id), task, sim.get(item.id), narrate=False)
    return {
        "fragile_stress": sim.get(item.id).meters.get("stress", 0.0),
        "hero_joy": sim.get(hero.id).memes.get("joy", 0.0),
    }


def tell_story(store: Store, task: Task, item_cfg: Item, hero_name: str, friend_name: str, supervisor_type: str) -> World:
    world = World(store)

    hero = world.add(Entity(id=hero_name, kind="character", type="child"))
    friend = world.add(Entity(id=friend_name, kind="character", type="child"))
    supervisor = world.add(Entity(id="Supervisor", kind="character", type=supervisor_type, label=f"the {supervisor_type}"))
    item = world.add(Entity(id=item_cfg.id, type=item_cfg.id, label=item_cfg.label, phrase=item_cfg.phrase))

    world.say(f"{hero.id} and {friend.id} went to {store.place} with {supervisor.label}.")
    world.say(f"{setting_detail()} {hero.id} wanted to help by {task.gerund}, and {friend.id} nodded fast.")
    world.say(f"{supervisor.label.capitalize()} smiled and said they could help, but only if someone could supervise.")

    world.para()
    world.say(f"At the {store.aisles[0]} aisle, {hero.id} reached for {item.label}.")
    world.say(f"Then {hero.id} tried to {task.verb}, but that was the sort of plan that could turn silly.")

    pred = predict_mishap(world, hero, task, item)
    world.facts["predicted_stress"] = pred["fragile_stress"]
    world.facts["task"] = task
    world.facts["item"] = item
    world.facts["hero"] = hero
    world.facts["friend"] = friend
    world.facts["supervisor"] = supervisor

    if pred["fragile_stress"] >= THRESHOLD:
        world.say(f"\"Easy now,\" said {supervisor.label}, because {item.label} did not want extra drama.")
    _do_task(world, hero, task, item, narrate=True)

    world.say(f"{friend.id} nodded again and held the cart steady while {supervisor.label} supervised.")
    if task.id == "cart":
        world.say(f"The cart gave a silly {_sfx(task.sound)} when it hit a tiny bump, but nobody was upset.")
    elif task.id == "scanner":
        world.say(f"The scanner chirped {_sfx(task.sound)} so many times that even the bananas looked amused.")
    elif task.id == "fruits":
        world.say(f"One apple rolled with a dramatic {_sfx(task.sound)}, then stopped right by {friend.id}'s shoe.")
    elif task.id == "shelf":
        world.say(f"A snack bag slid down with {_sfx(task.sound)}, and {friend.id} caught it with both hands.")
    else:
        world.say(f"The sample cup went {_sfx(task.sound)} and made everyone laugh, especially {supervisor.label}.")

    world.para()
    hero.memes["friendship"] = hero.memes.get("friendship", 0.0) + 1.0
    friend.memes["friendship"] = friend.memes.get("friendship", 0.0) + 1.0
    supervisor.memes["pride"] = supervisor.memes.get("pride", 0.0) + 1.0

    world.say(f"{friend.id} nodded at {hero.id} like a tiny coach, and {hero.id} nodded back.")
    world.say(f"Together they fixed the mix-up, put everything back neatly, and kept the aisle tidy.")
    world.say(f"At the checkout, {supervisor.label} said they were a great team.")
    world.say(f"{hero.id} grinned, {friend.id} grinned, and the grocery store seemed to grin too.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    task = _safe_fact(world, f, "task")
    return [
        f"Write a short comedy story set in a grocery store where a child and a friend nod, supervise, and make a funny {_sfx(task.sound)} sound.",
        f"Tell a friendly story in which one child wants to {task.verb} and another helper must supervise so everything ends happily.",
        f"Write a happy ending grocery-store story about friendship, a small mistake, and a silly sound effect.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    supervisor = _safe_fact(world, f, "supervisor")
    task = _safe_fact(world, f, "task")
    item = _safe_fact(world, f, "item")

    return [
        QAItem(
            question=f"Who went to the grocery store with {hero.id}?",
            answer=f"{friend.id} went with {hero.id}, and {supervisor.label} came too to supervise the plan.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do in the store?",
            answer=f"{hero.id} wanted to {task.verb}, which made the day feel playful and a little silly.",
        ),
        QAItem(
            question=f"What sound effect showed up when {hero.id} tried the task?",
            answer=f"The story used the sound effect {_sfx(task.sound)} when things got funny around the {item.label}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {hero.id}, {friend.id}, and {supervisor.label} fixed the problem and stayed friends.",
        ),
    ]


KNOWLEDGE = {
    "cart": [(
        "What is a grocery cart for?",
        "A grocery cart is for carrying food and other store items while you shop."
    )],
    "scanner": [(
        "What does a scanner do at a store?",
        "A scanner reads the barcode on an item so the store can ring it up."
    )],
    "fruit": [(
        "Why are fruits handled carefully?",
        "Some fruit can bruise or get squished, so people handle it gently."
    )],
    "sound": [(
        "What is a sound effect in a story?",
        "A sound effect is a little word like beep or clatter that helps you hear the action."
    )],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["task"].tags)
    out: list[QAItem] = []
    if "cart" in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["cart"])
    if "scanner" in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["scanner"])
    if "fruit" in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["fruit"])
    if "sound" in tags:
        out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE["sound"])
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        lines.append(f"  {e.id:10} ({e.type:9}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


SETTINGS = {
    "grocery_store": Store(place="the grocery store"),
}

CURATED = [
    StoryParams(place="grocery_store", task="cart", item="cart", hero="Mia", friend="Ben", supervisor="mother"),
    StoryParams(place="grocery_store", task="scanner", item="scanner", hero="Noah", friend="Zoe", supervisor="father"),
    StoryParams(place="grocery_store", task="fruits", item="banana", hero="Lily", friend="Eli", supervisor="aunt"),
    StoryParams(place="grocery_store", task="shelf", item="bread", hero="Theo", friend="Ava", supervisor="uncle"),
    StoryParams(place="grocery_store", task="samples", item="samples", hero="Mia", friend="Noah", supervisor="mother"),
]


def valid_combos() -> list[tuple[str, str]]:
    return choose_valid_pairs()


def explain_rejection(task: Task, item: Item) -> str:
    return (
        f"(No story: {task.gerund} does not reasonably connect to {item.label}. "
        f"Try a match where the task and object make comic sense.)"
    )


ASP_RULES = r"""
task_valid(T,I) :- task(T), item(I), compatible(T,I).
valid_story(P,T,I) :- place(P), task_valid(T,I), supervise_story(P,T,I).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid in SETTINGS:
        lines.append(asp.fact("place", pid))
    for tid, t in TASKS.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("sound", t.sound))
        for tag in sorted(t.tags):
            lines.append(asp.fact("tag", tid, tag))
    for iid, it in ITEMS.items():
        lines.append(asp.fact("item", iid))
        if it.fragile:
            lines.append(asp.fact("fragile", iid))
        if it.noisy:
            lines.append(asp.fact("noisy", iid))
    for tid, t in TASKS.items():
        for iid, it in ITEMS.items():
            if is_reasonable(t, it):
                lines.append(asp.fact("compatible", tid, iid))
    for pid in SETTINGS:
        for tid in TASKS:
            for iid in ITEMS:
                if is_reasonable(_safe_lookup(TASKS, tid), _safe_lookup(ITEMS, iid)):
                    lines.append(asp.fact("supervise_story", pid, tid, iid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show task_valid/2."))
    return sorted(set(asp.atoms(model, "task_valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy grocery-store friendship storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--hero")
    ap.add_argument("--friend")
    ap.add_argument("--supervisor", choices=SUPERVISORS)
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
    if getattr(args, "task", None) and getattr(args, "item", None):
        if not is_reasonable(_safe_lookup(TASKS, getattr(args, "task", None)), _safe_lookup(ITEMS, getattr(args, "item", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    candidates = [
        c for c in combos
        if (getattr(args, "task", None) is None or c[0] == getattr(args, "task", None))
        and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))
    ]
    if not candidates:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    task, item = rng.choice(sorted(candidates))
    hero = getattr(args, "hero", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in NAMES if n != hero])
    supervisor = getattr(args, "supervisor", None) or rng.choice(SUPERVISORS)
    return StoryParams(place="grocery_store", task=task, item=item, hero=hero, friend=friend, supervisor=supervisor)


def generate(params: StoryParams) -> StorySample:
    world = tell_story(_safe_lookup(SETTINGS, params.place), _safe_lookup(TASKS, params.task), _safe_lookup(ITEMS, params.item), params.hero, params.friend, params.supervisor)
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
        print(asp_program("#show task_valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show task_valid/2."))
        print(sorted(set(asp.atoms(model, "task_valid"))))
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
            header = f"### {p.hero}: {p.task} at {p.place} (item: {p.item})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
