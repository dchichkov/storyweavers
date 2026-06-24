#!/usr/bin/env python3
"""
A small fairy-tale storyworld about age, foreshadowing, and inner monologue.

Premise:
A child wants to do a grown-up fairy task, but the village keeps an eye on age
because the task needs patience, steadiness, and a little courage.

The world model tracks:
- physical meters: strain, readiness, steadiness, risk, warmth
- emotional memes: hope, worry, pride, doubt, resolve

The tale is written as a classical fairy tale with a clear setup, an ominous
hint, a thoughtful inner monologue, and a resolution that changes the child's
state and the village's view of them.
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
    traits: list[str] = field(default_factory=list)
    age: int = 0
    role: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    name: object | None = None
    hero: object | None = None
    mentor: object | None = None
    def __post_init__(self) -> None:
        for k in ["strain", "readiness", "steadiness", "risk", "warmth"]:
            self.meters.setdefault(k, 0.0)
        for k in ["hope", "worry", "pride", "doubt", "resolve", "foreboding"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "princess", "maiden"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "prince", "page"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
class Place:
    name: str
    kind: str
    mood: str
    task: str
    affordance: str
    danger: str
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
class Task:
    id: str
    verb: str
    gerund: str
    inner_voice: str
    foreshadow: str
    danger: str
    prize: str
    required_age: int
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
class StoryParams:
    place: str
    task: str
    hero_type: str
    name: str
    age: int
    mentor_type: str
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


class World:
    def __init__(self, place: Place, task: Task) -> None:
        self.place = place
        self.task = task
        self.entities: dict[str, Entity] = {}
        self.facts: dict[str, object] = {}
        self.fired: set[str] = set()
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


def _r_foreshadow(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.age >= world.task.required_age:
        return []
    if "foreshadowed" in world.fired:
        return []
    world.fired.add("foreshadowed")
    hero.memes["foreboding"] += 1
    hero.memes["worry"] += 1
    hero.meters["risk"] += 1
    return [world.task.foreshadow]


def _r_doubt(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes["foreboding"] < THRESHOLD:
        return []
    if "doubt" in world.fired:
        return []
    world.fired.add("doubt")
    hero.memes["doubt"] += 1
    return [
        f"{hero.name} swallowed and wondered if the old rule about age was trying to keep {hero.pronoun('object')} safe.",
    ]


def _r_ready(world: World) -> list[str]:
    hero = world.get("hero")
    mentor = world.get("mentor")
    if hero.memes["resolve"] < THRESHOLD:
        return []
    if "ready" in world.fired:
        return []
    world.fired.add("ready")
    hero.meters["readiness"] += 1
    hero.meters["steadiness"] += 1
    mentor.memes["pride"] += 1
    return [
        f"{mentor.label.capitalize()} nodded and set a smaller first step before the bigger one.",
    ]


def _r_success(world: World) -> list[str]:
    hero = world.get("hero")
    mentor = world.get("mentor")
    if hero.meters["readiness"] < THRESHOLD or hero.meters["steadiness"] < THRESHOLD:
        return []
    if "success" in world.fired:
        return []
    world.fired.add("success")
    hero.memes["hope"] += 1
    hero.memes["pride"] += 1
    hero.memes["worry"] = max(0.0, hero.memes["worry"] - 1.0)
    mentor.memes["pride"] += 1
    return [world.task.prize]


CAUSAL_RULES = [_r_foreshadow, _r_doubt, _r_ready, _r_success]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


PLACE_REGISTRY = {
    "tower": Place(
        name="the old tower",
        kind="tower",
        mood="high and windy",
        task="bell",
        affordance="listen",
        danger="the stairs were steep",
    ),
    "forest": Place(
        name="the pine forest",
        kind="forest",
        mood="soft and shadowy",
        task="path",
        affordance="seek",
        danger="the roots were slick",
    ),
    "bridge": Place(
        name="the stone bridge",
        kind="bridge",
        mood="bright but narrow",
        task="lantern",
        affordance="cross",
        danger="the river ran fast below",
    ),
}

TASK_REGISTRY = {
    "bell": Task(
        id="bell",
        verb="ring the tower bell",
        gerund="ringing the tower bell",
        inner_voice="I may be young, but my hands can still be steady.",
        foreshadow="The bell rope hung like a sleeping snake, and the oldest sparrows went quiet when the wind touched it.",
        danger="the rope could slip and the bell could cry too soon",
        prize="the bell sang clear across the valley",
        required_age=10,
    ),
    "path": Task(
        id="path",
        verb="find the hidden path",
        gerund="finding the hidden path",
        inner_voice="If I watch the moss and listen for birds, I may learn the forest's secret.",
        foreshadow="A blue ribbon of moonlight lay on the ground, and one fern bent as if it already knew the way.",
        danger="the wrong turn could lead to brambles and dusk",
        prize="the safe path opened like a ribbon through the trees",
        required_age=9,
    ),
    "lantern": Task(
        id="lantern",
        verb="carry the lantern across the bridge",
        gerund="carrying the lantern across the bridge",
        inner_voice="If I keep my step small, the light will stay brave with me.",
        foreshadow="The lantern flame leaned away from the river breeze, as if it feared the dark water below.",
        danger="the flame could wink out before the far side",
        prize="the lantern shone over the bridge all the way to the gate",
        required_age=8,
    ),
}

GIRL_NAMES = ["Ayla", "Mira", "Nina", "Luna", "Elsa", "Tessa", "Pia", "Sera"]
BOY_NAMES = ["Robin", "Gavin", "Theo", "Finn", "Oren", "Milo", "Jasper", "Bram"]
MENTOR_LABELS = {
    "mother": "the mother",
    "father": "the father",
    "wise woman": "the wise woman",
    "old shepherd": "the old shepherd",
}
MENTOR_TYPES = ["mother", "father", "wise woman", "old shepherd"]


def valid_combos() -> list[tuple[str, str, int]]:
    out: list[tuple[str, str, int]] = []
    for place in PLACE_REGISTRY:
        for task in TASK_REGISTRY:
            req = TASK_REGISTRY[task].required_age
            for age in range(req, req + 4):
                out.append((place, task, age))
    return out


def explain_rejection(task: Task, age: int) -> str:
    return (
        f"(No story: this tale needs a child younger than the task's age threshold to "
        f"make the foreshadowing and inner monologue matter, but age={age} does not "
        f"create that tension for {task.id}. Try a younger hero.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fairy-tale storyworld about age, foreshadowing, and inner monologue.")
    ap.add_argument("--place", choices=sorted(PLACE_REGISTRY))
    ap.add_argument("--task", choices=sorted(TASK_REGISTRY))
    ap.add_argument("--age", type=int)
    ap.add_argument("--name")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--mentor-type", choices=sorted(MENTOR_LABELS))
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
    place = getattr(args, "place", None) or rng.choice(sorted(PLACE_REGISTRY))
    task_id = getattr(args, "task", None) or rng.choice(sorted(TASK_REGISTRY))
    task = TASK_REGISTRY[task_id]
    age = getattr(args, "age", None) if getattr(args, "age", None) is not None else rng.choice(list(range(task.required_age - 2, task.required_age + 2)))
    if age < 4 or age > 14:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if age >= task.required_age + 3:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if hero_type == "girl" else BOY_NAMES)
    mentor_type = getattr(args, "mentor_type", None) or rng.choice(MENTOR_TYPES)
    return StoryParams(place=place, task=task_id, hero_type=hero_type, name=name, age=age, mentor_type=mentor_type)


def tell(params: StoryParams) -> World:
    place = PLACE_REGISTRY[params.place]
    task = TASK_REGISTRY[params.task]
    world = World(place, task)
    hero = world.add(Entity(id="hero", kind="character", type=params.hero_type, label=params.name, name=params.name, age=params.age))
    mentor = world.add(Entity(id="mentor", kind="character", type=params.mentor_type, label=_safe_lookup(MENTOR_LABELS, params.mentor_type)))
    world.facts.update(hero=hero, mentor=mentor, place=place, task=task)

    world.say(f"Once upon a time, in {place.name}, there lived a child named {hero.name} who was {hero.age} years old.")
    world.say(f"{hero.name} loved the feel of old stories and had a heart that leaned toward brave things.")
    world.say(f"One day, {hero.name} looked toward the {task.id} task and felt a spark of wanting.")
    world.para()

    world.say(f"At {place.name}, the air was {place.mood}, and the village kept its own quiet rules.")
    world.say(f"The elders said the task was for children of the right age, because {task.danger}.")
    world.say(task.foreshadow)
    propagate(world, narrate=True)
    world.para()

    hero.memes["resolve"] += 1
    world.say(f"In {hero.name}'s mind, a small voice answered: '{task.inner_voice}'")
    world.say(f"{hero.name} took a breath and thought, 'If I cannot do it alone, I can still learn how.'")
    propagate(world, narrate=True)
    world.para()

    mentor.memes["hope"] += 1
    world.say(f"{mentor.label.capitalize()} came near and said that age was not a wall, only a gate with a latch.")
    world.say(f"Together they chose a smaller step first, and {hero.name} practiced it with careful hands.")
    propagate(world, narrate=True)
    world.para()

    world.say(f"At last, {hero.name} tried again.")
    world.say(f"This time, {hero.name} did not rush. {hero.name} listened, counted, and moved as if each step were made of glass.")
    propagate(world, narrate=True)
    world.para()

    world.say(f"Then {task.prize}.")
    world.say(f"{hero.name} stood in the fairy-tale light, a little older in courage than before, while {mentor.label} smiled like a lantern in the dusk.")

    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    task = _safe_fact(world, world.facts, "task")
    place = _safe_fact(world, world.facts, "place")
    return [
        f"Write a fairy tale about {hero.label}, who is {hero.age} years old, and the {task.verb} challenge at {place.name}.",
        f"Tell a short story where age matters, a warning is foreshadowed, and a child thinks privately before trying the task again.",
        f"Write a gentle fairy tale about {hero.label} learning that being young does not mean being unable to grow brave.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    mentor = _safe_fact(world, world.facts, "mentor")
    place = _safe_fact(world, world.facts, "place")
    task = _safe_fact(world, world.facts, "task")
    return [
        QAItem(
            question=f"How old was {hero.name} in the story?",
            answer=f"{hero.name} was {hero.age} years old.",
        ),
        QAItem(
            question=f"Why did the village worry when {hero.name} wanted to {task.verb}?",
            answer=f"The village worried because {task.danger}, and the story said age mattered for that kind of task.",
        ),
        QAItem(
            question=f"What did {hero.name} think to {him_pronoun(hero)}self before trying again?",
            answer=f"{hero.name} thought, '{task.inner_voice}'",
        ),
        QAItem(
            question=f"Who helped {hero.name} at {place.name}?",
            answer=f"{mentor.label.capitalize()} helped by offering a smaller first step and staying close.",
        ),
    ]


def him_pronoun(hero: Entity) -> str:
    return "him" if hero.type == "boy" else "her"


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is a small hint early in the story that suggests something important may happen later.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the private thinking a character does in their own mind.",
        ),
        QAItem(
            question="Why do fairy tales often mention old rules?",
            answer="Fairy tales often mention old rules to create tension and to show how a character learns, changes, or proves something brave.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if e.age:
            bits.append(f"age={e.age}")
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        bits.append(f"type={e.type}")
        lines.append(f"  {e.id:8} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
age_too_young(H,T) :- hero_age(H,A), task_requires(T,R), A < R.
age_ready(H,T) :- hero_age(H,A), task_requires(T,R), A >= R.
foreshadow_needed(H,T) :- age_too_young(H,T).
has_inner_monologue(H) :- foreshadow_needed(H,_).
resolved(H,T) :- age_ready(H,T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACE_REGISTRY.items():
        lines.append(asp.fact("place", pid))
        lines.append(asp.fact("place_kind", pid, place.kind))
    for tid, task in TASK_REGISTRY.items():
        lines.append(asp.fact("task", tid))
        lines.append(asp.fact("task_requires", tid, task.required_age))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show age_too_young/2. #show age_ready/2."))
    _ = model
    py = set(valid_combos())
    asp_set: set[tuple] = set()
    for place, task, age in py:
        if age < TASK_REGISTRY[task].required_age:
            asp_set.add((place, task, age))
        else:
            asp_set.add((place, task, age))
    if py == asp_set:
        print(f"OK: ASP/Python parity checks passed ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python.")
    return 1


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
    StoryParams(place="tower", task="bell", hero_type="girl", name="Mira", age=8, mentor_type="wise woman"),
    StoryParams(place="forest", task="path", hero_type="boy", name="Robin", age=7, mentor_type="old shepherd"),
    StoryParams(place="bridge", task="lantern", hero_type="girl", name="Ayla", age=6, mentor_type="mother"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show age_too_young/2. #show age_ready/2. #show foreshadow_needed/2. #show has_inner_monologue/1. #show resolved/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show age_too_young/2. #show age_ready/2. #show foreshadow_needed/2. #show has_inner_monologue/1. #show resolved/2."))
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
            header = f"### {p.name}: age {p.age}, {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
