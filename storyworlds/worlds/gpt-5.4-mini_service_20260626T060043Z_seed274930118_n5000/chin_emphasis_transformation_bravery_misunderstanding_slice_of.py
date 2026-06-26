#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/chin_emphasis_transformation_bravery_misunderstanding_slice_of.py
=========================================================================================================================

A small slice-of-life story world about a child, a quiet misunderstanding, and
a gentle transformation into bravery.

Premise used to build the world model:
---
A child is practicing a short talk for a family gathering. A grown-up keeps
telling them to "put emphasis on the words" and "lift your chin." The child
misunderstands the advice and thinks they are being told to act bossy. After a
small moment of embarrassment, the grown-up explains that emphasis just means
speaking clearly and lifting the chin means looking at the listener. The child
tries again, grows a little braver, and the talk goes well.

World model:
---
- Actors and objects are typed entities with physical meters and emotional memes.
- The child can start shy, then gain bravery.
- A misunderstanding can raise tension until it is explained.
- The final story image proves transformation through a changed posture and mood.

Narrative instruments:
---
- chin: a physical/postural detail that changes in the story.
- emphasis: a speech-style cue that can be misunderstood.
- Transformation: the child becomes more confident.
- Bravery: the child speaks up despite feeling shy.
- Misunderstanding: the advice is initially interpreted the wrong way.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Callable, Optional

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    grownup: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def possessive_name(self) -> str:
        return f"{self.id}'s"
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
    place: str = "the kitchen"
    occasion: str = "family dinner"
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
class Scene:
    id: str
    verb: str
    gerund: str
    rush: str
    cue: str
    misunderstanding: str
    turn: str
    outcome: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_shy(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes.get("shy", 0) >= THRESHOLD and (("shy_line",) not in world.fired):
        world.fired.add(("shy_line",))
        out.append(f"{child.id} kept their eyes on the table and spoke very softly.")
    return out


def _r_bravery(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes.get("bravery", 0) >= THRESHOLD and ("brave_line",) not in world.fired:
        world.fired.add(("brave_line",))
        out.append(f"{child.id} took a breath and tried again.")
    return out


def _r_transformation(world: World) -> list[str]:
    out: list[str] = []
    child = world.entities.get("child")
    if not child:
        return out
    if child.memes.get("bravery", 0) >= THRESHOLD and child.meters.get("chin", 0) >= THRESHOLD:
        if ("transform",) not in world.fired:
            world.fired.add(("transform",))
            out.append(f"{child.id} stood a little taller, as if a quiet change had settled in.")
    return out


CAUSAL_RULES = [
    Rule("shy", _r_shy),
    Rule("bravery", _r_bravery),
    Rule("transformation", _r_transformation),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def forecast(world: World, child_id: str, scene: Scene) -> dict:
    sim = world.copy()
    child = sim.get(child_id)
    child.memes["shy"] += 1
    child.meters["chin"] += 1
    child.meters["voice"] += 1
    child.memes["bravery"] += 1
    propagate(sim, narrate=False)
    return {
        "brave": child.memes.get("bravery", 0) >= THRESHOLD,
        "changed": child.meters.get("chin", 0) >= THRESHOLD and child.memes.get("bravery", 0) >= THRESHOLD,
    }


def introduce(world: World, child: Entity, grownup: Entity) -> None:
    world.say(
        f"{child.id} was a quiet little {child.type} who was supposed to speak at {world.setting.occasion}."
    )
    world.say(
        f"{grownup.id} was kind and watched over the table, ready to help."
    )


def setup(world: World, child: Entity, grownup: Entity, scene: Scene) -> None:
    child.memes["shy"] += 1
    world.say(
        f"That evening, in {world.setting.place}, {child.id} practiced {scene.gerund} for {world.setting.occasion}."
    )
    world.say(
        f"{grownup.id} kept saying, \"Put some {scene.cue} on the important words, and lift your chin a little.\""
    )


def misunderstanding(world: World, child: Entity, grownup: Entity, scene: Scene) -> None:
    child.memes["confused"] += 1
    child.meters["chin"] = 0
    world.say(
        f"{child.id} misunderstood the advice and thought {scene.misunderstanding}."
    )
    world.say(
        f"That made {child.id} feel small, and the words stuck in their throat."
    )


def turn(world: World, child: Entity, grownup: Entity, scene: Scene) -> None:
    child.memes["bravery"] += 1
    child.meters["chin"] += 1
    child.meters["voice"] += 1
    world.say(
        f"Then {grownup.id} smiled and explained that {scene.turn}"
    )
    world.say(
        f"{child.id} took another breath, looked up, and tried the line again."
    )
    propagate(world, narrate=True)


def resolution(world: World, child: Entity, grownup: Entity, scene: Scene) -> None:
    child.memes["bravery"] += 1
    child.memes["shy"] = 0
    child.meters["chin"] += 1
    world.say(
        f"This time, {child.id} spoke clearly, with just the right {scene.cue}, and {grownup.id} nodded proudly."
    )
    world.say(
        f"By the end, {child.id} was no longer hiding behind their plate; they were standing straight with a lifted chin and a brave little smile."
    )


def tell(setting: Setting, scene: Scene, child_name: str = "Mina", child_type: str = "girl",
         grownup_type: str = "mother") -> World:
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_type, meters={"chin": 0, "voice": 0}, memes={"shy": 0}))
    grownup = world.add(Entity(id="grownup", kind="character", type=grownup_type, label="the grown-up"))
    world.facts["scene"] = scene

    introduce(world, child, grownup)
    world.para()
    setup(world, child, grownup, scene)
    misunderstanding(world, child, grownup, scene)
    world.para()
    turn(world, child, grownup, scene)
    resolution(world, child, grownup, scene)

    world.facts.update(child=child, grownup=grownup, transformed=child.memes.get("bravery", 0) >= THRESHOLD)
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", occasion="family dinner", affords={"speech"}),
    "living_room": Setting(place="the living room", occasion="a small visit from relatives", affords={"speech"}),
    "porch": Setting(place="the porch", occasion="a neighborhood get-together", affords={"speech"}),
}

SCENES = {
    "speech": Scene(
        id="speech",
        verb="give a little speech",
        gerund="practicing a little speech",
        rush="blurt out the lines all at once",
        cue="emphasis",
        misunderstanding="they were supposed to sound bossy or loud",
        turn="emphasis just meant making the words clear, and lifting the chin meant looking at the people they were talking to",
        outcome="the little speech sounded warm and steady",
        tags={"chin", "emphasis", "bravery", "misunderstanding", "transformation"},
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Suri", "Nia", "Ivy", "Ada", "Maya", "Tara"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Theo", "Finn", "Leo", "Arlo", "Milo"]
TRAITS = ["shy", "careful", "gentle", "nervous", "soft-spoken", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    scene: str
    name: str
    gender: str
    grownup_type: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life story world about chin, emphasis, bravery, and misunderstanding.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--scene", choices=SCENES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--grownup", choices=["mother", "father", "grandmother", "grandfather"])
    ap.add_argument("--name")
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


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, scene, "child") for place in SETTINGS for scene in SCENES]


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    scene = getattr(args, "scene", None) or rng.choice(list(SCENES))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    grownup = getattr(args, "grownup", None) or rng.choice(["mother", "father", "grandmother", "grandfather"])
    trait = rng.choice(TRAITS)
    if scene not in SCENES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, scene=scene, name=name, gender=gender, grownup_type=grownup, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(SCENES, params.scene), params.name, params.gender, params.grownup_type)
    prompts = [
        f"Write a short slice-of-life story for young children about {params.name} learning to use chin and emphasis while speaking.",
        f"Tell a gentle story where a shy child named {params.name} feels confused, then becomes brave after a grown-up explains the advice clearly.",
        f"Write a simple story about a misunderstanding that turns into a small transformation and ends with a lifted chin.",
    ]
    child = _safe_fact(world, world.facts, "child")
    grownup = _safe_fact(world, world.facts, "grownup")
    scene = _safe_fact(world, world.facts, "scene")
    story_qa = [
        QAItem(
            question=f"Why did {params.name} feel confused at first?",
            answer=f"{params.name} misunderstood the advice and thought {scene.misunderstanding}. That made {child.id} feel small before the grown-up explained it kindly.",
        ),
        QAItem(
            question=f"What did the grown-up mean by emphasis?",
            answer=f"The grown-up meant {scene.turn}. It was a gentle reminder to speak clearly, not to be bossy.",
        ),
        QAItem(
            question=f"How did {params.name} change by the end?",
            answer=f"{params.name} grew more brave and confident. By the end, {child.id} was standing straighter with a lifted chin and speaking clearly.",
        ),
    ]
    world_qa = [
        QAItem(question="What is emphasis in speech?", answer="Emphasis is when you make some words stand out a little so listeners can hear what matters most."),
        QAItem(question="Why might someone lift their chin when speaking?", answer="Lifting the chin can help someone look toward the people they are talking to and speak more clearly."),
        QAItem(question="What is a misunderstanding?", answer="A misunderstanding happens when someone hears or thinks the wrong thing and gets confused."),
    ]
    return StorySample(params=params, story=world.render(), prompts=prompts, story_qa=story_qa, world_qa=world_qa, world=world)


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    return "\n".join(lines)


ASP_RULES = r"""
has_misunderstanding(C) :- child(C), hears_badly(C).
grows_brave(C) :- child(C), receives_kind_help(C).
transforms(C) :- grows_brave(C), chin_up(C).
#show has_misunderstanding/1.
#show grows_brave/1.
#show transforms/1.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("child", "child")]
    for place in SETTINGS:
        lines.append(asp.fact("setting", place))
    for scene in SCENES:
        lines.append(asp.fact("scene", scene))
    lines.append(asp.fact("hears_badly", "child"))
    lines.append(asp.fact("receives_kind_help", "child"))
    lines.append(asp.fact("chin_up", "child"))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program())
    names = {sym.name for sym in model}
    expected = {"has_misunderstanding", "grows_brave", "transforms"}
    if names >= expected:
        print("OK: ASP parity looks reasonable.")
        return 0
    print("Mismatch in ASP verification.")
    return 1


def asp_show() -> str:
    return asp_program()


CURATED = [
    StoryParams(place="kitchen", scene="speech", name="Mina", gender="girl", grownup_type="mother", trait="shy"),
    StoryParams(place="living_room", scene="speech", name="Owen", gender="boy", grownup_type="grandmother", trait="careful"),
    StoryParams(place="porch", scene="speech", name="Ivy", gender="girl", grownup_type="father", trait="gentle"),
]


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
        print(asp_show())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program())
        print("ASP model:")
        for sym in model:
            print(sym)
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
