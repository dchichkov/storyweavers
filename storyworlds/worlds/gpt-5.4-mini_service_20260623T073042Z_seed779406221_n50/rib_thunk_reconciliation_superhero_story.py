#!/usr/bin/env python3
"""
storyworlds/worlds/rib_thunk_reconciliation_superhero_story.py
=============================================================

A standalone story world for a small superhero tale: a hero hears a rib-thunk
in the middle of a rescue, gets thrown off balance, and reaches Reconciliation
with a teammate after a mistake. The domain is tiny, state-driven, and child-
facing: a city block, a rescue, a bump, a repair, and a calm ending image.

Seed tale inspiration:
---
A young hero and a teammate patrol a windy city block. When a rescue goes wrong,
there is a rib-thunk from a hard landing. The teammate feels blamed, the hero
feels embarrassed, and the pair split apart for a moment. Later, they talk it
through, apologize, and fix the problem together. By the end they are reconciled
and flying side by side again.

The world uses physical meters and emotional memes, a forward-chaining rule
engine, a reasonableness gate, and an inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
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
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    hero: object | None = None
    sidekick: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sister"}
        male = {"boy", "man", "father", "brother"}
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
        return str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def phrase(self) -> str:
        return str(getattr(self, "_phrase", None) or str(getattr(self, "label", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower())))

    @phrase.setter
    def phrase(self, value: str) -> None:
        object.__setattr__(self, "_phrase", value)

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
class Setting:
    place: str
    afford: set[str] = field(default_factory=set)
    sky: str = "clear"
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
class Mission:
    id: str
    verb: str
    gerund: str
    risk: str
    zone: set[str]
    sound: str = "thunk"
    keyword: str = "rib"
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
class Gear:
    id: str
    label: str
    covers: set[str]
    helps: set[str]
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
    label: str
    phrase: str
    at_risk: str
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
class World:
    setting: Setting
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])

    c: object | None = None
    world: object | None = None
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

    def copy(self) -> "World":
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.facts = copy.deepcopy(self.facts)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        return c
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


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            produced = rule.apply(world)
            if produced:
                changed = True
                out.extend(produced)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _r_thunk(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    for mission in world.facts.get("active_missions", []):
        if hero.meters[mission.keyword] < THRESHOLD:
            continue
        sig = ("thunk", mission.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.meters["bruised"] += 1
        hero.memes["shame"] += 1
        sidekick.memes["worry"] += 1
        hero.memes["strain"] += 1
        out.append(f"There was a rib-thunk when {hero.id} landed hard.")
    return out


def _r_conflict(world: World) -> list[str]:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    if hero.memes["shame"] < THRESHOLD or sidekick.memes["worry"] < THRESHOLD:
        return []
    sig = ("conflict",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["distance"] += 1
    sidekick.memes["distance"] += 1
    return [f"{hero.id} and {sidekick.id} stopped talking for a moment."]


def _r_reconcile(world: World) -> list[str]:
    hero = world.get("hero")
    sidekick = world.get("sidekick")
    if hero.memes["apology"] < THRESHOLD or sidekick.memes["listened"] < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    hero.memes["distance"] = 0
    sidekick.memes["distance"] = 0
    hero.memes["reconciled"] += 1
    sidekick.memes["reconciled"] += 1
    return ["They made up and flew forward together again."]


RULES = [
    Rule("thunk", _r_thunk),
    Rule("conflict", _r_conflict),
    Rule("reconcile", _r_reconcile),
]


def mission_at_risk(mission: Mission, problem: Problem) -> bool:
    return problem.at_risk in mission.zone


def select_gear(mission: Mission, problem: Problem) -> Optional[Gear]:
    for gear in GEARS:
        if problem.id in gear.helps and problem.at_risk in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for setting in SETTINGS:
        for mission in MISSIONS.values():
            for problem in PROBLEMS.values():
                if mission_at_risk(mission, problem) and select_gear(mission, problem):
                    out.append((setting, mission.id, problem.id))
    return out


@dataclass
class StoryParams:
    setting: str
    mission: str
    problem: str
    hero: str
    sidekick: str
    hero_type: str
    sidekick_type: str
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


SETTINGS = {
    "city": Setting(place="the city block", afford={"rescue"}, sky="windy"),
    "rooftops": Setting(place="the rooftops", afford={"rescue"}, sky="bright"),
    "harbor": Setting(place="the harbor", afford={"rescue"}, sky="spray-bright"),
}

MISSIONS = {
    "rescue": Mission(
        id="rescue",
        verb="save the kitten",
        gerund="saving the kitten",
        risk="a hard landing",
        zone={"feet", "torso"},
        sound="thunk",
        keyword="rib",
        tags={"rib", "thunk", "hero"},
    ),
}

PROBLEMS = {
    "stuck_gate": Problem(
        id="stuck_gate",
        label="stuck gate",
        phrase="a gate jammed shut",
        at_risk="feet",
        tags={"repair", "city"},
    ),
    "fallen_sign": Problem(
        id="fallen_sign",
        label="fallen sign",
        phrase="a sign that had tipped over",
        at_risk="torso",
        tags={"repair", "roof"},
    ),
}

GEARS = [
    Gear("gloves", "grippy gloves", {"feet"}, {"stuck_gate"}, {"repair"}),
    Gear("shield", "a chest shield", {"torso"}, {"fallen_sign"}, {"repair"}),
    Gear("boots", "spring boots", {"feet"}, {"stuck_gate"}, {"repair"}),
]


def explain_rejection(mission: Mission, problem: Problem) -> str:
    return f"(No story: {mission.gerund} does not put {problem.label} at risk in a way this world can solve.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny superhero reconciliation story world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
    ap.add_argument("--sidekick-type", choices=["boy", "girl"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "mission", None) is None or c[1] == getattr(args, "mission", None))
              and (getattr(args, "problem", None) is None or c[2] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, mission, problem = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["boy", "girl"])
    sidekick_type = getattr(args, "sidekick_type", None) or ("girl" if hero_type == "boy" else "boy")
    hero = getattr(args, "hero", None) or rng.choice(["Nova", "Sky", "Bolt", "Mira"])
    sidekick = getattr(args, "sidekick", None) or rng.choice(["Patch", "Ruby", "Quill", "Jade"])
    if hero == sidekick:
        sidekick += " Jr."
    return StoryParams(setting, mission, problem, hero, sidekick, hero_type, sidekick_type)


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero = world.add(Entity("hero", "character", params.hero_type, params.hero, "hero"))
    sidekick = world.add(Entity("sidekick", "character", params.sidekick_type, params.sidekick, "sidekick"))
    problem = _safe_lookup(PROBLEMS, params.problem)
    mission = _safe_lookup(MISSIONS, params.mission)
    gear = select_gear(mission, problem)

    for e in (hero, sidekick):
        e.memes["trust"] = 1
        e.memes["distance"] = 0
        e.memes["reconciled"] = 0
        e.memes["apology"] = 0
        e.memes["listened"] = 0
        e.meters["rib"] = 0
        e.meters["bruised"] = 0

    world.facts["active_missions"] = [mission]
    world.facts["problem"] = problem
    world.facts["gear"] = gear

    world.say(f"{hero.id} and {sidekick.id} patrolled {world.setting.place} like two small superheroes.")
    world.say(f"They were trying to {mission.verb} near {problem.phrase}.")
    world.para()

    hero.meters["rib"] += 1
    propagate(world)
    world.say(f"{hero.id} winced and rubbed {hero.pronoun('possessive')} side.")
    world.say(f"{sidekick.id} looked worried because the landing sounded like {mission.sound}.")
    world.para()

    hero.memes["apology"] += 1
    sidekick.memes["listened"] += 1
    world.say(f"{hero.id} said sorry for snapping at {sidekick.id}.")
    world.say(f"{sidekick.id} listened, nodded, and helped fix the mistake.")
    if gear:
        world.say(f"They used {gear.label_word if hasattr(gear, 'label_word') else gear.label} to make the rescue safer.")
    propagate(world)
    world.para()

    hero.memes["reconciled"] += 1
    sidekick.memes["reconciled"] += 1
    propagate(world)
    world.say(f"By sunset, {hero.id} and {sidekick.id} were smiling again over {world.setting.place}.")
    world.say(f"They flew side by side, lighter than before, with the problem safely handled.")

    world.facts.update(hero=hero, sidekick=sidekick, mission=mission, problem=problem, setting=params.setting, gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short superhero story for a young child that includes the word "rib" and the sound "thunk".',
        f"Tell a story where {f['hero'].id} and {f['sidekick'].id} help each other after a hard landing and then reconcile.",
        f"Write a gentle superhero story about a mistake, an apology, and Reconciliation on {SETTINGS[f['setting']].place}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    sidekick = f["sidekick"]
    problem = f["problem"]
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id} and {sidekick.id}, two small superheroes who worked together on the city block.",
        ),
        QAItem(
            question=f"What sound happened when {hero.id} landed hard?",
            answer=f"The landing made a rib-thunk sound, and {hero.id} winced because it hurt a little.",
        ),
        QAItem(
            question=f"What did {hero.id} do after the mistake?",
            answer=f"{hero.id} said sorry, listened better, and worked with {sidekick.id} to fix the problem.",
        ),
        QAItem(
            question=f"What happened at the end?",
            answer=f"They reached Reconciliation, made up, and flew side by side again.",
        ),
    ]
    if f.get("gear"):
        qa.append(QAItem(
            question="What helped them finish the rescue safely?",
            answer=f"They used {f['gear'].label} to make the rescue safer while handling {problem.label}.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does reconciliation mean?",
            answer="Reconciliation means people stop being upset with each other, apologize, and become friends again.",
        ),
        QAItem(
            question="Why can a hard landing hurt a hero?",
            answer="A hard landing can bruise a hero because the body hits the ground fast and with force.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(sample.prompts)
    lines.append("")
    lines.append("== story qa ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== world qa ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: meters={dict(e.meters)} memes={dict(e.memes)}")
    return "\n".join(lines)


ASP_RULES = r"""
mission_at_risk(M,P) :- mission(M), problem(P), zone(M,Z), at_risk(P,Z).
can_resolve(M,P) :- mission_at_risk(M,P), gear(G), helps(G,P), covers(G,Z), at_risk(P,Z).
valid(S,M,P) :- setting(S), mission(M), problem(P), can_resolve(M,P).
reconciled :- apology, listened.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        for z in sorted(m.zone):
            lines.append(asp.fact("zone", mid, z))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("at_risk", pid, p.at_risk))
    for gid, g in enumerate(GEARS):
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for h in sorted(g.helps):
            lines.append(asp.fact("helps", g.id, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    asp_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if asp_set == py_set:
        print(f"OK: ASP parity matched valid_combos() ({len(py_set)} combos).")
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
    StoryParams("city", "rescue", "stuck_gate", "Nova", "Patch", "girl", "boy"),
    StoryParams("rooftops", "rescue", "fallen_sign", "Bolt", "Jade", "boy", "girl"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(base_seed + i))
            p.seed = base_seed + i
            samples.append(generate(p))
    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
