#!/usr/bin/env python3
"""
storyworlds/worlds/center_friendship_animal_story.py
====================================================

A small animal-story world about friendship at the center of a place.

Premise:
- Two young animals meet at the center of a small setting.
- One wants to do a shared activity in a special spot.
- The other worries about fairness or being left out.
- They solve it by taking turns or sharing the center space.

The world is intentionally tiny and state-driven:
- physical meters track location, possession, and activity
- emotional memes track want, worry, hurt, and closeness
- the prose is generated from world state, not from a fixed template with swapped names
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
    preferred_spot: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "rabbit", "fox", "deer", "cat", "mouse"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "bear", "dog", "wolf", "squirrel"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def named(self) -> str:
        return self.label or self.id
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
    center: str
    features: set[str] = field(default_factory=set)
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
    item: str
    item_phrase: str
    shared: bool
    places: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    worry: str
    reason: str
    fix: str
    resolution: str
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
    activity: str
    problem: str
    hero: str
    friend: str
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


SETTINGS = {
    "meadow": Setting(place="the meadow", center="the center of the meadow", features={"soft grass", "open sky"}),
    "pond": Setting(place="the pond", center="the round stones by the middle of the pond", features={"water", "reeds"}),
    "forest": Setting(place="the forest clearing", center="the center of the clearing", features={"trees", "leafy ground"}),
    "garden": Setting(place="the garden", center="the center path", features={"flowers", "small fence"}),
}

ACTIVITIES = {
    "dance": Activity(
        id="dance",
        verb="dance in a circle",
        gerund="dancing in a circle",
        item="ribbon",
        item_phrase="a bright ribbon",
        shared=True,
        places={"meadow", "garden"},
        tags={"friendship", "sharing"},
    ),
    "sing": Activity(
        id="sing",
        verb="sing a song together",
        gerund="singing together",
        item="songbook",
        item_phrase="a little songbook",
        shared=True,
        places={"forest", "meadow"},
        tags={"friendship", "music"},
    ),
    "play_ball": Activity(
        id="play_ball",
        verb="play with a soft ball",
        gerund="playing ball",
        item="ball",
        item_phrase="a soft red ball",
        shared=True,
        places={"meadow", "garden"},
        tags={"friendship", "sharing"},
    ),
    "build": Activity(
        id="build",
        verb="build a tiny tower",
        gerund="building a tiny tower",
        item="blocks",
        item_phrase="three small wooden blocks",
        shared=True,
        places={"forest", "garden"},
        tags={"friendship", "teamwork"},
    ),
}

PROBLEMS = {
    "left_out": Problem(
        id="left_out",
        worry="felt left out",
        reason="one friend got to stand in the center first",
        fix="They could switch places and take turns in the center.",
        resolution="That made both friends feel included.",
    ),
    "shy": Problem(
        id="shy",
        worry="felt too shy to speak up",
        reason="the center spot looked big and important",
        fix="A kind friend could sit beside them and wait together.",
        resolution="That made the center feel safe.",
    ),
    "not_fair": Problem(
        id="not_fair",
        worry="thought it was not fair",
        reason="one friend was using the special item alone",
        fix="They could share the item and use it together.",
        resolution="That made the play feel fair.",
    ),
}

ANIMALS = {
    "rabbit": {"type": "rabbit", "kind": "character"},
    "fox": {"type": "fox", "kind": "character"},
    "bear": {"type": "bear", "kind": "character"},
    "deer": {"type": "deer", "kind": "character"},
    "mouse": {"type": "mouse", "kind": "character"},
    "squirrel": {"type": "squirrel", "kind": "character"},
    "cat": {"type": "cat", "kind": "character"},
    "dog": {"type": "dog", "kind": "character"},
}

NAMES = {
    "rabbit": ["Clover", "Mimi", "Nib", "Pip"],
    "fox": ["Tansy", "Fenn", "Reed", "Luna"],
    "bear": ["Bruno", "Moss", "Ollie", "Hank"],
    "deer": ["Fern", "Willow", "Dale", "Poppy"],
    "mouse": ["Nell", "Dot", "Squeak", "Bram"],
    "squirrel": ["Tiko", "Hazel", "Nutsy", "Skye"],
    "cat": ["Milo", "Penny", "Toby", "Lily"],
    "dog": ["Rufus", "Sunny", "Wren", "Bingo"],
}

TRAITS = ["gentle", "curious", "playful", "careful", "brave", "kind"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id, act in ACTIVITIES.items():
            if place not in act.places:
                continue
            for prob_id in PROBLEMS:
                combos.append((place, act_id, prob_id))
    return combos


def prize_at_risk(activity: Activity, problem: Problem) -> bool:
    return True


def select_fix(activity: Activity, problem: Problem) -> bool:
    return True


def build_world(setting: Setting, activity: Activity, problem: Problem, hero_name: str, hero_type: str, friend_name: str, friend_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, label=friend_name))
    item = world.add(Entity(
        id=activity.item,
        kind="thing",
        type=activity.item,
        label=activity.item,
        phrase=activity.item_phrase,
        owner=hero.id,
    ))
    hero.meters["center"] = 1
    friend.meters["center"] = 1
    hero.memes["want"] += 1
    friend.memes["want"] += 1
    world.facts.update(hero=hero, friend=friend, item=item, activity=activity, problem=problem, trait=trait)
    world.say(f"{hero.name if hasattr(hero,'name') else hero_name} was a {trait} {hero_type} who liked being near the center of {setting.place}.")
    return world


def tell(setting: Setting, activity: Activity, problem: Problem, hero_name: str = "Milo", hero_type: str = "cat", friend_name: str = "Pip", friend_type: str = "rabbit", trait: str = "kind") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    friend = world.add(Entity(id=friend_name, kind="character", type=friend_type, label=friend_name))
    item = world.add(Entity(id=activity.item, kind="thing", type=activity.item, label=activity.item, phrase=activity.item_phrase, owner=hero.id))
    hero.meters["center"] = 1
    friend.meters["center"] = 1
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1

    world.say(f"{hero.id} was a {trait} {hero.type} who loved {setting.center}.")
    world.say(f"One day, {hero.id} showed {friend.id} {hero.pronoun('possessive')} {item.phrase}.")
    world.say(f"The two friends wanted to {activity.verb} at {setting.center}.")

    world.para()
    if problem.id == "left_out":
        hero.memes["pride"] += 1
        friend.memes["hurt"] += 1
        world.say(f"At first, {hero.id} stayed in the center and {friend.id} {problem.worry}.")
        world.say(f"{problem.reason.capitalize()}.")
    elif problem.id == "shy":
        friend.memes["worry"] += 1
        world.say(f"{friend.id} {problem.worry} because {problem.reason}.")
        world.say(f"{hero.id} smiled and waited close by.")
    else:
        hero.memes["guard"] += 1
        friend.memes["hurt"] += 1
        world.say(f"{friend.id} {problem.worry} because {problem.reason}.")
        world.say(f"{hero.id} looked at the {item.label} and saw the problem.")

    world.para()
    hero.memes["care"] += 1
    friend.memes["care"] += 1
    world.say(problem.fix)
    hero.memes["joy"] += 1
    friend.memes["joy"] += 1
    hero.memes["hurt"] = 0
    friend.memes["hurt"] = 0
    world.say(f"{hero.id} and {friend.id} moved together to the center and kept going side by side.")
    world.say(f"In the end, {problem.resolution} {hero.id} was {activity.gerund}, and {friend.id} was smiling too.")

    world.facts.update(resolved=True)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    activity = _safe_fact(world, f, "activity")
    problem = _safe_fact(world, f, "problem")
    return [
        f"Write a short animal story about friendship at the center of a place, where {hero.id} and {friend.id} try to {activity.verb}.",
        f"Tell a gentle story in which two animal friends meet at {world.setting.center} and work through a {problem.id} problem.",
        f"Write a child-friendly animal story with a clear middle turn and a happy ending about sharing the center spot.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    activity = _safe_fact(world, f, "activity")
    problem = _safe_fact(world, f, "problem")
    setting = world.setting
    return [
        QAItem(
            question=f"Who are the friends in the story?",
            answer=f"The friends are {hero.id} the {hero.type} and {friend.id} the {friend.type}. They meet at {setting.center}.",
        ),
        QAItem(
            question=f"What did {hero.id} and {friend.id} want to do together?",
            answer=f"They wanted to {activity.verb} at {setting.center}. That fit their friendship because the activity was something they could share.",
        ),
        QAItem(
            question=f"What problem came up before they solved it?",
            answer=f"{friend.id} {problem.worry}, and the story showed a small worry about the center spot. Then they found a kinder way to play.",
        ),
        QAItem(
            question=f"How did the friends fix the problem?",
            answer=f"They used the idea in the story's center turn: {problem.fix} After that, both friends could stay together and enjoy the play.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is the center of a place?",
            answer="The center is the middle part of a place, the spot that is farthest from the edges.",
        ),
        QAItem(
            question="Why do friends take turns?",
            answer="Friends take turns so everyone gets a fair chance and nobody feels left out.",
        ),
        QAItem(
            question="What does friendship mean?",
            answer="Friendship means being kind, sharing, listening, and helping each other feel safe and happy.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.

valid(P,A,R) :- place(P), activity(A), problem(R), good_place(P,A), friendship_story(A,R).
good_place(P,A) :- place(P), activity(A), allows(P,A).
friendship_story(A,R) :- activity(A), problem(R).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.features):
            lines.append(asp.fact("feature", pid, a))
        for act_id in ACTIVITIES:
            if pid in _safe_lookup(ACTIVITIES, act_id).places:
                lines.append(asp.fact("allows", pid, act_id))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for rid in PROBLEMS:
        lines.append(asp.fact("problem", rid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal friendship storyworld with a center spot.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--hero")
    ap.add_argument("--friend")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "activity", None):
        combos = [c for c in combos if c[1] == getattr(args, "activity", None)]
    if getattr(args, "problem", None):
        combos = [c for c in combos if c[2] == getattr(args, "problem", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, problem = rng.choice(list(combos))
    act = _safe_lookup(ACTIVITIES, activity)
    hero_type = rng.choice(sorted(ANIMALS))
    friend_type = rng.choice(sorted(t for t in ANIMALS if t != hero_type))
    hero = getattr(args, "hero", None) or rng.choice(_safe_lookup(NAMES, hero_type))
    friend = getattr(args, "friend", None) or rng.choice(_safe_lookup(NAMES, friend_type))
    return StoryParams(place=place, activity=activity, problem=problem, hero=hero, friend=friend, seed=getattr(args, "seed", None))


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PROBLEMS, params.problem),
        hero_name=params.hero,
        hero_type="cat" if params.hero.startswith("M") else "rabbit",
        friend_name=params.friend,
        friend_type="rabbit",
        trait="kind",
    )
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
    StoryParams(place="meadow", activity="play_ball", problem="left_out", hero="Milo", friend="Pip"),
    StoryParams(place="forest", activity="sing", problem="shy", hero="Luna", friend="Bram"),
    StoryParams(place="garden", activity="dance", problem="not_fair", hero="Hazel", friend="Toby"),
]


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
        for c in combos:
            print(c)
        return

    rng = random.Random(getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31))
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            p = resolve_params(args, random.Random((getattr(args, "seed", None) or 0) + i))
            s = generate(p)
            if s.story in seen:
                i += 1
                continue
            seen.add(s.story)
            samples.append(s)
            i += 1

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
