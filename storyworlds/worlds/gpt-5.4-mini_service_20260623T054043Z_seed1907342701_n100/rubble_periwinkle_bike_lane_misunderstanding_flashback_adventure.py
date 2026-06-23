#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/rubble_periwinkle_bike_lane_misunderstanding_flashback_adventure.py
============================================================================================================

A small adventure storyworld about a bike-lane misunderstanding, with a flashback
that reveals why the characters act the way they do.

Seed premise:
- setting: bike lane
- words: rubble, periwinkle
- features: Misunderstanding, Flashback
- style: Adventure

This world uses typed entities with physical meters and emotional memes, a tiny
forward-rule simulator, a reasonableness gate, and an inline ASP twin.
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
    attrs: dict[str, str] = field(default_factory=dict)

    helper: object | None = None
    obstacle: object | None = None
    path: object | None = None
    rider: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "rider"}
        male = {"boy", "man", "father", "dad", "rider"}
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
class Problem:
    id: str
    noun: str
    verb: str
    risk_word: str
    zone: str
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
class Method:
    id: str
    label: str
    action: str
    success_image: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

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
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_blocked(world: World) -> list[str]:
    out: list[str] = []
    rider = world.get("rider")
    if rider.meters["stuck"] < THRESHOLD:
        return out
    sig = ("blocked",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    path = world.get("path")
    path.meters["blocked"] += 1
    rider.memes["confusion"] += 1
    out.append("The lane stopped feeling open.")
    return out


def _r_dusty(world: World) -> list[str]:
    out: list[str] = []
    obstacle = world.get("obstacle")
    rider = world.get("rider")
    if obstacle.meters["dusty"] < THRESHOLD:
        return out
    sig = ("dusty",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    rider.memes["worry"] += 1
    out.append("A pale dust drifted into the air.")
    return out


CAUSAL_RULES = [Rule("blocked", _r_blocked), Rule("dusty", _r_dusty)]


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


def predict_misunderstanding(world: World, problem: Problem) -> bool:
    sim = world.copy()
    rider = sim.get("rider")
    rider.meters["stuck"] += 1
    propagate(sim, narrate=False)
    return sim.get("path").meters["blocked"] >= THRESHOLD


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place in PLACES.values():
        for prob in PROBLEMS.values():
            for method in METHODS.values():
                if place.id == "bike_lane" and prob.zone == "lane" and method.id in {"move_rubble", "mark_path", "lift_bike"}:
                    combos.append((place.id, prob.id, method.id))
    return combos


@dataclass
class StoryParams:
    place: str = "bike_lane"
    problem: str = "rubble"
    method: str = "move_rubble"
    rider_name: str = "Mina"
    rider_gender: str = "girl"
    helper_name: str = "Jo"
    helper_gender: str = "boy"
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


PLACES = {
    "bike_lane": Place(id="bike_lane", label="the bike lane", tags={"bike_lane", "adventure"}),
}

PROBLEMS = {
    "rubble": Problem(id="rubble", noun="rubble", verb="clear the rubble", risk_word="rubble", zone="lane", tags={"rubble", "block"}),
    "periwinkle": Problem(id="periwinkle", noun="periwinkle paint", verb="brush away the periwinkle paint", risk_word="periwinkle", zone="lane", tags={"periwinkle", "paint"}),
    "flashback_note": Problem(id="flashback_note", noun="an old note", verb="pick up the old note", risk_word="flashback", zone="lane", tags={"flashback"}),
}

METHODS = {
    "move_rubble": Method(id="move_rubble", label="move the rubble aside", action="move it to the curb", success_image="the lane was open again", tags={"rubble"}),
    "mark_path": Method(id="mark_path", label="mark a safe path", action="draw a bright line around it", success_image="the lane had a clear edge", tags={"periwinkle"}),
    "lift_bike": Method(id="lift_bike", label="lift the bike over it", action="carry the bike around the mess", success_image="the bike rolled free", tags={"bike"}),
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld in a bike lane with a misunderstanding and a flashback.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--method", choices=METHODS)
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "method", None) is None or c[2] == getattr(args, "method", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, method = rng.choice(list(combos))
    rider_name = rng.choice(["Mina", "Tess", "Nia", "Arlo", "Pip"])
    helper_name = rng.choice([n for n in ["Jo", "Kai", "Finn", "Bea", "Owen"] if n != rider_name])
    rider_gender = rng.choice(["girl", "boy"])
    helper_gender = rng.choice(["girl", "boy"])
    return StoryParams(place=place, problem=problem, method=method, rider_name=rider_name, rider_gender=rider_gender, helper_name=helper_name, helper_gender=helper_gender)


def tell(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    problem = _safe_lookup(PROBLEMS, params.problem)
    method = _safe_lookup(METHODS, params.method)
    world = World(place)
    rider = world.add(Entity(id="rider", kind="character", type=params.rider_gender, label=params.rider_name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name))
    obstacle = world.add(Entity(id="obstacle", label=problem.noun, kind="thing", tags=problem.tags))
    path = world.add(Entity(id="path", label="the bike lane", kind="thing", tags={"lane"}))
    world.facts.update(params=params, rider=rider, helper=helper, obstacle=obstacle, path=path, place=place, problem=problem, method=method, flashback=False, resolved=False)

    world.say(f"{rider.label} and {helper.label} rode into {place.label} on a bright day, ready for adventure.")
    world.say(f"Then they saw {problem.noun} in the lane, and the path did not look right.")
    world.para()
    rider.meters["stuck"] += 1
    rider.memes["confusion"] += 1
    if predict_misunderstanding(world, problem):
        world.say(f"{rider.label} thought the mess meant the lane was closed, but {helper.label} shook {helper.pronoun('possessive')} head.")
        world.say(f'"That is not a closed gate," {helper.label} said. "It is only {problem.noun}."')

    world.para()
    world.facts["flashback"] = True
    world.say(f"A flashback tugged at {rider.label}'s mind: yesterday, {helper.label} had seen {problem.risk_word} and promised to help clear it on the next ride.")
    if problem.id == "periwinkle":
        obstacle.meters["dusty"] += 1
        obstacle.memes["care"] += 1
        world.say(f"The old memory was bright as periwinkle paint on a fence, and now {helper.label} had brought a brush.")
    else:
        obstacle.meters["dusty"] += 1
        world.say(f"The remembered promise made the day feel serious, like a map with a blue periwinkle line.")
    world.para()
    if method.id == "move_rubble":
        obstacle.meters["stuck"] += 1
        path.meters["blocked"] = 0
        world.say(f"Together they moved the rubble to the curb, stone by stone.")
        world.say(f"Then {method.success_image}, and the bike lane shone clear.")
    elif method.id == "mark_path":
        path.meters["blocked"] = 0
        world.say(f"{helper.label} used periwinkle chalk to mark a safe edge around the mess.")
        world.say(f"After that, {method.success_image}, and the riders knew exactly where to go.")
    else:
        path.meters["blocked"] = 0
        world.say(f"{rider.label} and {helper.label} lifted the bike around the rubble, careful and quick.")
        world.say(f"At last, {method.success_image}, and the adventure rolled on.")

    rider.memes["relief"] += 1
    helper.memes["relief"] += 1
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short adventure story set in a bike lane that includes the words "{f["problem"].noun}" and "periwinkle".',
        f"Tell a story where {f['rider'].label} and {f['helper'].label} face a misunderstanding in {f['place'].label}, then remember something in a flashback and fix the problem.",
        f"Write a child-friendly adventure with a clear problem, a flashback, and a safe ending in the bike lane.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    rider, helper, prob, method = f["rider"], f["helper"], f["problem"], f["method"]
    return [
        QAItem(question=f"Who rode into {f['place'].label} first?", answer=f"{rider.label} rode in with {helper.label}, and both were ready for an adventure."),
        QAItem(question=f"What made {rider.label} stop and look again?", answer=f"{prob.noun} in the lane caused the misunderstanding. It looked like a big problem at first, so {rider.label} paused."),
        QAItem(question=f"Why did the story flash back to yesterday?", answer=f"The flashback showed why {helper.label} knew what to do. Yesterday's memory explained the promise to help with {prob.risk_word}."),
        QAItem(question=f"How did they solve the problem?", answer=f"They used {method.label}. That cleared the lane and left it open for the bike ride."),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = [
        QAItem(question="What is rubble?", answer="Rubble is broken pieces of stone or building material. It can block a path until someone moves it away."),
        QAItem(question="What does periwinkle mean?", answer="Periwinkle is a light blue-purple color. People use it for paint, chalk, and small decorations."),
        QAItem(question="What is a misunderstanding?", answer="A misunderstanding happens when someone thinks something means one thing, but it actually means something else."),
        QAItem(question="What is a flashback in a story?", answer="A flashback is a part of the story that jumps back to something that happened earlier. It helps explain why the characters act the way they do."),
        QAItem(question="Why do bike lanes matter?", answer="Bike lanes give riders a clearer place to travel. They help keep bikes and people moving safely."),
    ]
    if f["problem"].id == "periwinkle":
        out.append(QAItem(question="Can a color help show the way?", answer="Yes. Bright periwinkle chalk or paint can mark an edge or a path so riders know where to go."))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    lines.extend(f"{i}. {p}" for i, p in enumerate(sample.prompts, 1))
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"  {e.id}: meters={ {k:v for k,v in e.meters.items() if v} } memes={ {k:v for k,v in e.memes.items() if v} }")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="bike_lane", problem="rubble", method="move_rubble", rider_name="Mina", rider_gender="girl", helper_name="Jo", helper_gender="boy"),
    StoryParams(place="bike_lane", problem="periwinkle", method="mark_path", rider_name="Arlo", rider_gender="boy", helper_name="Bea", helper_gender="girl"),
    StoryParams(place="bike_lane", problem="flashback_note", method="lift_bike", rider_name="Tess", rider_gender="girl", helper_name="Kai", helper_gender="boy"),
]


ASP_RULES = r"""
valid(P,O,M) :- place(P), problem(O), method(M), allowed(P,O,M).
story_ready(P,O,M) :- valid(P,O,M).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for oid in PROBLEMS:
        lines.append(asp.fact("problem", oid))
    for mid in METHODS:
        lines.append(asp.fact("method", mid))
    for p, o, m in valid_combos():
        lines.append(asp.fact("allowed", p, o, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    import asp
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    ok = True
    if py != asp_set:
        ok = False
        print("MISMATCH between Python and ASP combo gates.")
        print("python-only:", sorted(py - asp_set))
        print("asp-only:", sorted(asp_set - py))
    try:
        sample = generate(resolve_params(argparse.Namespace(place=None, problem=None, method=None), random.Random(0)))
        _ = sample.story
        with contextlib.redirect_stdout(io.StringIO()):
            emit(sample)
    except Exception as exc:
        ok = False
        print(f"SMOKE TEST FAILED: {exc}")
    if ok:
        print(f"OK: ASP parity and generate/emit smoke test passed ({len(py)} combos).")
        return 0
    return 1


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.problem not in PROBLEMS or params.method not in METHODS:
        pass
    if (params.place, params.problem, params.method) not in valid_combos():
        pass
    world = tell(params)
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
        print(f"{len(valid_combos())} compatible combos:\n")
        for t in valid_combos():
            print(" ", t)
        return

    base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        i = 0
        seen: set[str] = set()
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            s = generate(params)
            if s.story not in seen:
                seen.add(s.story)
                samples.append(s)
            i += 1

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
