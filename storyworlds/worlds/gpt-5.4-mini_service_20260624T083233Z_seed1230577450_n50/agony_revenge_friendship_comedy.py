#!/usr/bin/env python3
"""
storyworlds/worlds/agony_revenge_friendship_comedy.py
======================================================

A tiny comedy story world about friendship, a hurt feeling, a silly revenge
idea, and a warm repair.

The source tale behind this world is the kind where two friends have a big
squabble over a shared game, one feels dramatic "agony", imagines a revenge
plan, and then discovers that the funniest ending is to apologize, swap turns,
and laugh together again.

The world model tracks:
- who is friends with whom,
- what small thing caused the hurt feeling,
- whether a prankish revenge plan is brewing,
- and how a kind repair changes the mood.

This is a standalone storyworld script.
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

# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "person"
    type: str = "friend"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    friends: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    def __post_init__(self) -> None:
        for key in ["hunger", "tired", "mess", "work", "noise"]:
            self.meters.setdefault(key, 0.0)
        for key in ["joy", "hurt", "agony", "revenge", "friendship", "sorry", "laugh", "pride"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
    @property
    def label_word(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "label", None) or getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)
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


@dataclass
class Activity:
    id: str
    name: str
    verb: str
    trigger: str
    mess: str = ""
    tension: str = ""
    repair: str = ""
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
class ObjectThing:
    id: str
    label: str
    type: str
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    broken: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    def __post_init__(self) -> None:
        self.meters.setdefault("scuffed", 0.0)
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity | ObjectThing] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}

    def add(self, ent):
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str):
        return self.entities[eid]

    def people(self) -> list[Entity]:
        return [e for e in self.entities.values() if isinstance(e, Entity)]

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

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
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "playroom": Setting("the playroom", {"games", "noise", "friends"}),
    "backyard": Setting("the backyard", {"games", "noise", "friends"}),
    "classroom": Setting("the classroom", {"games", "friends", "quiet"}),
    "park": Setting("the park", {"games", "friends", "noise"}),
}

ACTIVITIES = {
    "blocks": Activity(
        id="blocks",
        name="block tower",
        verb="build a tower",
        trigger="wanted the tallest tower",
        mess="blocks",
        tension="one tower toppling into the other",
        repair="make a new tower together",
        tags={"game", "friendship", "comedy"},
    ),
    "ball": Activity(
        id="ball",
        name="ball game",
        verb="kick the ball",
        trigger="wanted the ball all to themselves",
        mess="dust",
        tension="the ball rolling under the bench",
        repair="share turns and count to three",
        tags={"game", "friendship", "comedy"},
    ),
    "drawing": Activity(
        id="drawing",
        name="drawing contest",
        verb="draw a silly monster",
        trigger="wanted the best picture",
        mess="crayon",
        tension="a crayon snapping in half",
        repair="trade colors and finish the page",
        tags={"art", "friendship", "comedy"},
    ),
    "cookies": Activity(
        id="cookies",
        name="cookie break",
        verb="decorate cookies",
        trigger="wanted the biggest cookie",
        mess="crumbs",
        tension="sprinkles everywhere",
        repair="split the sprinkles and laugh",
        tags={"food", "friendship", "comedy"},
    ),
}

OBJECTS = {
    "tower": ObjectThing(id="tower", label="block tower", type="toy"),
    "ball": ObjectThing(id="ball", label="bouncy ball", type="toy"),
    "page": ObjectThing(id="page", label="drawing page", type="paper"),
    "cookies": ObjectThing(id="cookies", label="cookie plate", type="snack"),
}

NAMES = ["Mina", "Toby", "Zuri", "Owen", "Lia", "Niko", "June", "Pippa"]
TRAITS = ["playful", "curious", "silly", "spirited", "cheerful", "bouncy"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
friend_pair(A, B) :- friends(A, B).
friend_pair(A, B) :- friends(B, A).

hurt(A) :- aggrieved(A).
revenge_thought(A) :- hurt(A), not repaired(A).
repair_possible(A, B) :- friend_pair(A, B), shared_game(A, B).

good_story(A, B, Place, Act) :- friend_pair(A, B), at_place(A, Place), at_place(B, Place),
                                activity(Act), repair_possible(A, B).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("place", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("afford", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for t in sorted(a.tags):
            lines.append(asp.fact("tag", aid, t))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show good_story/4."))
    return sorted(set(asp.atoms(model, "good_story")))


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


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_combos() -> list[tuple[str, str]]:
    combos: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id, act in ACTIVITIES.items():
            if "friends" in setting.afford and "game" in act.tags:
                combos.append((place, act_id))
    return combos


def explain_rejection(place: Optional[str], act: Optional[str]) -> str:
    return (
        "(No story: this world only works when friends are in a place that supports a "
        "small shared game. Try a setting like the playroom or park, and an activity "
        "like blocks, ball, drawing, or cookies.)"
    )


# ---------------------------------------------------------------------------
# Story generation helpers
# ---------------------------------------------------------------------------

def shared_game(world: World, a: Entity, b: Entity) -> bool:
    return b.id in a.friends


def introduce(world: World, hero: Entity, friend: Entity, setting: Setting, activity: Activity) -> None:
    world.say(
        f"{hero.id} was a {hero.traits[0]} little friend who loved {activity.name}s "
        f"with {friend.id}."
    )
    world.say(
        f"They both liked going to {setting.place} because it was a good place to play together."
    )


def start_game(world: World, hero: Entity, friend: Entity, activity: Activity, thing: ObjectThing) -> None:
    hero.memes["friendship"] += 1
    friend.memes["friendship"] += 1
    world.say(
        f"One day, {hero.id} and {friend.id} got ready to {activity.verb} with the {thing.label}."
    )


def trigger_agony(world: World, hero: Entity, friend: Entity, activity: Activity, thing: ObjectThing) -> None:
    hero.memes["hurt"] += 1
    hero.memes["agony"] += 1
    hero.memes["pride"] += 1
    world.say(
        f"Then {activity.tension} made {hero.id} feel a tiny bit of comedy-sized agony."
    )
    world.say(
        f"{hero.id} frowned and thought, \"I should get revenge for that!\""
    )


def prank_plan(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    hero.memes["revenge"] += 1
    world.say(
        f"{hero.id} made a very silly revenge plan that sounded dramatic but looked more like a wiggle than a scare."
    )
    world.say(
        f"{friend.id} noticed the face and asked what was wrong."
    )


def repair(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    hero.memes["sorry"] += 1
    hero.memes["agony"] = 0.0
    hero.memes["revenge"] = 0.0
    hero.memes["hurt"] = 0.0
    hero.memes["joy"] += 1
    hero.memes["laugh"] += 1
    friend.memes["joy"] += 1
    friend.memes["laugh"] += 1
    world.say(
        f"{hero.id} took a breath, admitted the feelings, and stopped the revenge idea."
    )
    world.say(
        f"Then {hero.id} and {friend.id} chose to {activity.repair}, and that was funnier than any prank."
    )


def ending(world: World, hero: Entity, friend: Entity, activity: Activity) -> None:
    world.say(
        f"By the end, {hero.id} and {friend.id} were laughing so hard that the whole {world.setting.place} felt brighter."
    )
    world.say(
        f"Their friendship stayed in one piece, and the day ended with a shared grin instead of a grudge."
    )


def build_world(setting: Setting, activity: Activity, hero_name: str, friend_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="person", type="friend", traits=[trait, "small"]))
    friend = world.add(Entity(id=friend_name, kind="person", type="friend", traits=["friendly", "small"]))
    hero.friends.add(friend.id)
    friend.friends.add(hero.id)
    thing = world.add(copy.deepcopy(_safe_lookup(OBJECTS, activity.id)))
    thing.owner = hero.id

    introduce(world, hero, friend, setting, activity)
    world.para()
    start_game(world, hero, friend, activity, thing)
    trigger_agony(world, hero, friend, activity, thing)
    prank_plan(world, hero, friend, activity)
    world.para()
    repair(world, hero, friend, activity)
    ending(world, hero, friend, activity)

    world.facts.update(
        hero=hero,
        friend=friend,
        activity=activity,
        thing=thing,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, friend, activity, setting = f["hero"], f["friend"], f["activity"], f["setting"]
    return [
        f'Write a funny story for a young child about two friends at {setting.place} who start with a tiny bit of "agony" and end by laughing together.',
        f"Tell a comedy story where {hero.id} wants to {activity.verb}, feels upset, imagines revenge, and then fixes the friendship with {friend.id}.",
        f'Write a short, child-friendly story that uses the words "agony" and "revenge" but ends with a kind apology and a shared laugh.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, friend, activity, setting = f["hero"], f["friend"], f["activity"], f["setting"]
    return [
        QAItem(
            question=f"Who were the two friends in the story at {setting.place}?",
            answer=f"The story was about {hero.id} and {friend.id}, who were friends and played together.",
        ),
        QAItem(
            question=f"What made {hero.id} feel a tiny bit of agony?",
            answer=f"{activity.tension.capitalize()} made {hero.id} feel upset and dramatic for a moment.",
        ),
        QAItem(
            question=f"What silly idea did {hero.id} think about after feeling hurt?",
            answer=f"{hero.id} thought about revenge, but it was more of a funny idea than a real plan.",
        ),
        QAItem(
            question=f"How did the friends fix things in the end?",
            answer=f"They calmed down, talked it out, and chose to {activity.repair}. That repaired the friendship and made them laugh.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is when people care about each other, share time together, and try to be kind after a problem.",
        ),
        QAItem(
            question="What does an apology do?",
            answer="An apology helps after a mistake by showing you are sorry and want to make things better.",
        ),
        QAItem(
            question="Why can revenge be a bad idea?",
            answer="Revenge usually keeps a problem going instead of fixing it, so it makes everyone feel worse.",
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
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params and sampling
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    name: str
    friend: str
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


CURATED = [
    StoryParams(place="playroom", activity="blocks", name="Mina", friend="Toby", trait="playful"),
    StoryParams(place="park", activity="ball", name="Zuri", friend="Owen", trait="curious"),
    StoryParams(place="classroom", activity="drawing", name="Lia", friend="Niko", trait="silly"),
    StoryParams(place="backyard", activity="cookies", name="June", friend="Pippa", trait="cheerful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: agony, revenge, friendship, comedy.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--name")
    ap.add_argument("--friend")
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
    combos = [c for c in valid_combos() if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    friend = getattr(args, "friend", None) or rng.choice([n for n in NAMES if n != name])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, name=name, friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = build_world(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), params.name, params.friend, params.trait)
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        if isinstance(e, Entity):
            bits = []
            mems = {k: v for k, v in e.memes.items() if v}
            if mems:
                bits.append(f"memes={dict(mems)}")
            if e.friends:
                bits.append(f"friends={sorted(e.friends)}")
            lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
        else:
            lines.append(f"  {e.id:8} ({e.type:7}) owner={e.owner} scuffed={e.meters.get('scuffed', 0)}")
    return "\n".join(lines)


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show good_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for row in combos:
            print("  ", row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
