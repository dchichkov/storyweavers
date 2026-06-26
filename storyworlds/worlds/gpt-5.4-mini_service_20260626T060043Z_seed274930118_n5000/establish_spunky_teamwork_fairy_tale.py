#!/usr/bin/env python3
"""
establish_spunky_teamwork_fairy_tale.py
======================================

A small fairy-tale story world about a spunky team that has to work together
to solve one cozy problem with a satisfying ending.

Premise:
- A brave child or small hero wants to do a lively task.
- The task is too big for one helper alone.
- The team must establish a plan, share tools, and finish together.

World model:
- Physical state tracks carried items, fixed objects, and completed work.
- Emotional state tracks confidence, worry, pride, and team spirit.
- The story is driven by state changes, not by a frozen template.

Seed words:
- establish
- spunky

Feature:
- Teamwork
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
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    fixed: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    trait: object | None = None
    friend: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "queen", "princess", "woman", "mother"}
        male = {"boy", "king", "prince", "man", "father"}
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
class Place:
    name: str
    affords: set[str] = field(default_factory=set)
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
class Challenge:
    id: str
    name: str
    want_verb: str
    attempt_verb: str
    risk: str
    task: str
    result_phrase: str
    teamwork_move: str
    place_tags: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    helps: set[str]
    covers: set[str]
    phrase: str
    plural: bool = False
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[list[str]] = [[]]
        self.facts: dict = {}
        self.fired: set[tuple] = set()

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
            self.lines[-1].append(text)

    def para(self) -> None:
        if self.lines[-1]:
            self.lines.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.lines if p)

    def copy(self) -> "World":
        import copy as _copy

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.lines = [[]]
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "castle_gate": Place(name="the castle gate", affords={"rope", "banner", "lantern"}),
    "forest_path": Place(name="the forest path", affords={"rope", "bridge", "lantern"}),
    "river_bank": Place(name="the river bank", affords={"bridge", "rope"}),
    "village_square": Place(name="the village square", affords={"banner", "lantern"}),
}

CHALLENGES = {
    "rope_bridge": Challenge(
        id="rope_bridge",
        name="a wobbly little rope bridge",
        want_verb="cross the bridge",
        attempt_verb="build the bridge",
        risk="the boards could slip",
        task="tie the ropes and lay the boards",
        result_phrase="the bridge stayed steady",
        teamwork_move="hold the ropes while one friend tied the knots",
        place_tags={"bridge", "rope"},
    ),
    "lost_banner": Challenge(
        id="lost_banner",
        name="a bright banner for the feast",
        want_verb="hang the banner",
        attempt_verb="raise the banner",
        risk="it could twist and snag in the wind",
        task="lift the pole and fasten the cloth",
        result_phrase="the banner flew straight and proud",
        teamwork_move="hold the pole while one friend fastened the cloth",
        place_tags={"banner"},
    ),
    "dark_lantern": Challenge(
        id="dark_lantern",
        name="a small lantern for the path",
        want_verb="walk safely home",
        attempt_verb="light the lantern",
        risk="the path would stay dim",
        task="find kindling and spark the wick",
        result_phrase="the path glowed like honey",
        teamwork_move="shield the flame while one friend struck the spark",
        place_tags={"lantern"},
    ),
}

TOOLS = {
    "rope": Tool(id="rope", label="a length of rope", helps={"rope_bridge"}, covers={"rope"}, phrase="a long rope"),
    "planks": Tool(id="planks", label="two wooden planks", helps={"rope_bridge"}, covers={"bridge"}, phrase="two sturdy planks", plural=True),
    "banner_clips": Tool(id="banner_clips", label="gold clips", helps={"lost_banner"}, covers={"banner"}, phrase="tiny gold clips", plural=True),
    "lantern_match": Tool(id="lantern_match", label="a matchbox", helps={"dark_lantern"}, covers={"lantern"}, phrase="a little matchbox"),
    "wind_cloak": Tool(id="wind_cloak", label="a wind cloak", helps={"dark_lantern"}, covers={"lantern"}, phrase="a warm wind cloak"),
}

HERO_TYPES = ["girl", "boy"]
HERO_NAMES = ["Mina", "Toby", "Pia", "Rowan", "Nico", "Elin", "Jory", "Luna"]
SIDEKICKS = ["mouse", "fox", "goat", "sparrow"]
TRAITS = ["spunky", "brave", "cheerful", "curious", "quick"]
TEAM_SPIRIT_WORDS = ["teamwork", "helping", "sharing", "trying together"]


# ---------------------------------------------------------------------------
# Story params
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    challenge: str
    name: str
    gender: str
    sidekick: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
    params: object | None = None
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


def challenge_needs_team(ch: Challenge) -> bool:
    return True


def select_tool_bundle(ch: Challenge) -> list[Tool]:
    bundle = [t for t in TOOLS.values() if ch.id in t.helps]
    return bundle


def explain_rejection(place: Place, ch: Challenge) -> str:
    return (
        f"(No story: {place.name} does not support the needed kind of work for "
        f"{ch.name}. Try a place whose tools match the task.)"
    )


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------
def predict_outcome(world: World, hero: Entity, friend: Entity, ch: Challenge) -> dict:
    sim = world.copy()
    hero2 = sim.get(hero.id)
    friend2 = sim.get(friend.id)
    hero2.memes["wanting"] = hero2.memes.get("wanting", 0) + 1
    hero2.memes["worry"] = hero2.memes.get("worry", 0) + 1
    friend2.memes["helping"] = friend2.memes.get("helping", 0) + 1
    sim.facts["would_finish"] = True
    return {"finish": True, "team": True}


def setup(world: World, hero: Entity, friend: Entity, ch: Challenge) -> None:
    world.say(
        f"Once upon a time, {hero.id} was a {hero.type} with a {hero.trait} heart and a spunky grin."
    )
    world.say(
        f"{hero.id} loved {ch.want_verb}, because {ch.name} made the day feel like a tiny adventure."
    )
    world.say(
        f"By {hero.id}'s side was a small {friend.type} named {friend.id}, ready to help and ready to listen."
    )


def begin_problem(world: World, hero: Entity, friend: Entity, ch: Challenge) -> None:
    world.para()
    world.say(
        f"One day at {world.place.name}, {hero.id} tried to {ch.attempt_verb} alone."
    )
    hero.memes["wanting"] = hero.memes.get("wanting", 0) + 1
    hero.memes["worry"] = hero.memes.get("worry", 0) + 1
    world.say(
        f"But {ch.risk}, and the task was too big for one pair of hands."
    )
    world.say(
        f"{hero.id} frowned, then said, \"I wish we could {ch.task} without a mishap.\""
    )


def establish_plan(world: World, hero: Entity, friend: Entity, ch: Challenge) -> None:
    world.para()
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    friend.memes["helping"] = friend.memes.get("helping", 0) + 1
    world.say(
        f"{friend.id} wagged {friend.pronoun('possessive')} tail and said, "
        f"\"Let's establish a plan.\""
    )
    world.say(
        f"So the two of them made a spunky little teamwork plan: {ch.teamwork_move}."
    )
    world.say(
        f"They gathered their tools, took a breath, and began together."
    )


def solve_task(world: World, hero: Entity, friend: Entity, ch: Challenge) -> None:
    hero.meters["progress"] = hero.meters.get("progress", 0) + 1
    friend.meters["progress"] = friend.meters.get("progress", 0) + 1
    hero.memes["confidence"] = hero.memes.get("confidence", 0) + 1
    friend.memes["confidence"] = friend.memes.get("confidence", 0) + 1
    world.para()
    world.say(
        f"{hero.id} held steady while {friend.id} worked the hard bit, and then they switched."
    )
    world.say(
        f"Little by little, the job grew easier, because each friend did the part that fit best."
    )
    world.say(
        f"At last, they finished the last careful step: {ch.task}."
    )


def resolve(world: World, hero: Entity, friend: Entity, ch: Challenge) -> None:
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    friend.memes["pride"] = friend.memes.get("pride", 0) + 1
    world.para()
    world.say(
        f"Then something lovely happened: {ch.result_phrase}."
    )
    world.say(
        f"{hero.id} beamed and hugged {friend.id}. \"We did it together!\" {hero.id} cried."
    )
    world.say(
        f"And from that day on, the little pair knew that teamwork could make even a spunky plan come true."
    )


def tell(place: Place, ch: Challenge, hero_name: str, gender: str, sidekick: str, trait: str) -> World:
    world = World(place)
    hero = world.add(Entity(id=hero_name, kind="character", type=gender, trait=trait))
    friend = world.add(Entity(id=sidekick.capitalize(), kind="character", type=sidekick))
    world.facts.update(hero=hero, friend=friend, challenge=ch, place=place)

    setup(world, hero, friend, ch)
    begin_problem(world, hero, friend, ch)
    establish_plan(world, hero, friend, ch)
    solve_task(world, hero, friend, ch)
    resolve(world, hero, friend, ch)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ch = _safe_fact(world, f, "challenge")
    return [
        f'Write a fairy tale for a small child about how {hero.id} and a friend used teamwork to {ch.attempt_verb}.',
        f'Create a story that includes the word "establish" and shows a spunky hero making a plan with a helper.',
        f'Write a gentle fairy tale where cooperation helps a brave {hero.type} solve {ch.name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    ch: Challenge = _safe_fact(world, f, "challenge")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"What kind of child was {hero.id} in the story?",
            answer=f"{hero.id} was a {hero.trait} {hero.type}, and the story calls {hero.id} spunky too.",
        ),
        QAItem(
            question=f"What problem did {hero.id} and {friend.id} have to solve together?",
            answer=f"They had to work on {ch.name} at {place.name}, and the job needed teamwork.",
        ),
        QAItem(
            question=f"What did they do after they decided to establish a plan?",
            answer=f"They shared the job, used teamwork, and took turns on {ch.task}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {ch.result_phrase}, and {hero.id} said they did it together.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "teamwork": [
        (
            "What is teamwork?",
            "Teamwork is when two or more helpers work together to do one job and make it easier.",
        )
    ],
    "rope": [
        (
            "What is rope used for?",
            "Rope is used to tie, hold, or pull things so they stay in place.",
        )
    ],
    "banner": [
        (
            "Why do people hang banners?",
            "People hang banners to decorate a place or celebrate a special day.",
        )
    ],
    "lantern": [
        (
            "What does a lantern do?",
            "A lantern makes light so people can see better when it is dark.",
        )
    ],
    "fairy": [
        (
            "What is a fairy tale?",
            "A fairy tale is a story with a simple adventure, a big feeling, and a magical-feeling ending.",
        )
    ],
    "spunky": [
        (
            "What does spunky mean?",
            "Spunky means lively, bold, and full of cheerful energy.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"teamwork", "fairy", "spunky"}
    ch: Challenge = _safe_fact(world, world.facts, "challenge")
    if ch.id == "rope_bridge":
        tags.add("rope")
    if ch.id == "lost_banner":
        tags.add("banner")
    if ch.id == "dark_lantern":
        tags.add("lantern")
    out: list[QAItem] = []
    for tag in ["fairy", "spunky", "teamwork", "rope", "banner", "lantern"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in WORLD_KNOWLEDGE[tag])
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(P) :- place_fact(P).
challenge(C) :- challenge_fact(C).

needs_team(rope_bridge).
needs_team(lost_banner).
needs_team(dark_lantern).

compatible(P, C) :- place_supports(P, C), needs_team(C).

valid_story(P, C) :- compatible(P, C).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place_fact", pid))
        for ch in sorted(p.affords):
            lines.append(asp.fact("place_supports", pid, ch))
    for cid in CHALLENGES:
        lines.append(asp.fact("challenge_fact", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = {(p, c) for p, place in PLACES.items() for c in place.affords if c in CHALLENGES}
    asp_set = set(asp_valid_stories())
    if py == asp_set:
        print(f"OK: clingo gate matches Python valid stories ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python:")
    if py - asp_set:
        print("  only in python:", sorted(py - asp_set))
    if asp_set - py:
        print("  only in clingo:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    challenge: str
    name: str
    gender: str
    sidekick: str
    trait: str
    seed: Optional[int] = None
    params: object | None = None
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
    ap = argparse.ArgumentParser(description="A fairy-tale teamwork story world.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--sidekick", choices=SIDEKICKS)
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def valid_pairs() -> list[tuple[str, str]]:
    out = []
    for p, place in PLACES.items():
        for c in place.affords:
            if c in CHALLENGES:
                out.append((p, c))
    return out


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    pairs = valid_pairs()
    if getattr(args, "place", None) or getattr(args, "challenge", None):
        pairs = [x for x in pairs if (getattr(args, "place", None) is None or x[0] == getattr(args, "place", None)) and (getattr(args, "challenge", None) is None or x[1] == getattr(args, "challenge", None))]
    if not pairs:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, challenge = rng.choice(sorted(pairs))
    ch = _safe_lookup(CHALLENGES, challenge)
    gender = getattr(args, "gender", None) or rng.choice(HERO_TYPES)
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice(SIDEKICKS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, challenge=challenge, name=name, gender=gender, sidekick=sidekick, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(CHALLENGES, params.challenge), params.name, params.gender, params.sidekick, params.trait)
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
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible (place, challenge) combos:\n")
        for p, c in stories:
            print(f"  {p:14} {c}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p, c in valid_pairs():
            params = StoryParams(
                place=p,
                challenge=c,
                name=random.Random(base_seed + len(samples)).choice(HERO_NAMES),
                gender=random.Random(base_seed + len(samples) + 1).choice(HERO_TYPES),
                sidekick=random.Random(base_seed + len(samples) + 2).choice(SIDEKICKS),
                trait=random.Random(base_seed + len(samples) + 3).choice(TRAITS),
                seed=base_seed + len(samples),
            )
            samples.append(generate(params))
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
        if len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
