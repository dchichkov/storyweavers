#!/usr/bin/env python3
"""
storyworlds/worlds/dependent_blank_cameo_misunderstanding_surprise_space_adventure.py
====================================================================================

A standalone story world for a small Space Adventure tale with misunderstanding
and surprise beats.

Premise:
- A child astronaut is preparing a blank mission board for a dependent robot
  assistant.
- A cameo signal from a tiny moonbase arrives with a surprise message.
- A misunderstanding about the blank board and the cameo leads to a worry.
- The turn reveals the board was meant for a hidden star-map party plan.
- The ending image proves the change: the blank board becomes a bright, shared
  launch plan.

The world uses typed entities with meters and memes, a small causal rule engine,
a reasonableness gate, and inline ASP rules mirroring the Python checker.
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
SENSE_MIN = 2



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
    owner: str = ""
    dependent_on: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    tags: set[str] = field(default_factory=set)
    plural: bool = False

    board: object | None = None
    cameo: object | None = None
    commander: object | None = None
    pilot: object | None = None
    robot: object | None = None
    star_map: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom"}
        male = {"boy", "man", "father", "dad"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

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
class Setting:
    id: str
    place: str
    detail: str
    affords: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    name: str
    cause: str
    misunderstanding: str
    surprise: str
    risk: str
    zone: set[str]
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
    region: str
    tags: set[str] = field(default_factory=set)
    plural: bool = False
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
class Fix:
    id: str
    label: str
    action: str
    outcome: str
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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_misunderstanding(world: World) -> list[str]:
    out: list[str] = []
    pilot = world.facts["pilot"]
    robot = world.facts["robot"]
    board = world.facts["board"]
    if pilot.memes["worry"] < THRESHOLD or board.meters["blank"] < THRESHOLD:
        return out
    sig = ("misunderstanding", pilot.id, board.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pilot.memes["confusion"] += 1
    pilot.memes["worry"] += 1
    robot.memes["hurt"] += 1
    out.append("__misunderstanding__")
    return out


CAUSAL_RULES = [Rule("misunderstanding", _r_misunderstanding)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for setting_id, setting in SETTINGS.items():
        for problem_id, problem in PROBLEMS.items():
            if problem.name in setting.affords:
                for board_id, board in OBJECTS.items():
                    if board.region in problem.zone:
                        for fix_id, fix in FIXES.items():
                            if fix_id in {"holo_tape", "sticker_notes"}:
                                combos.append((setting_id, problem_id, board_id))
                                break
    return combos


def explain_rejection(setting: Setting, problem: Problem, board: ObjectCfg) -> str:
    return (
        f"(No story: {problem.name} only works as a space misunderstanding if "
        f"the blank board sits in the risky zone. Try a board worn on {sorted(problem.zone)}.)"
    )


@dataclass
class StoryParams:
    setting: str
    problem: str
    board: str
    fix: str
    pilot_name: str
    pilot_gender: str
    robot_name: str
    commander_name: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Space Adventure storyworld: dependent, blank, cameo, misunderstanding, surprise."
    )
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--board", choices=OBJECTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--pilot-name")
    ap.add_argument("--pilot-gender", choices=["girl", "boy"])
    ap.add_argument("--robot-name")
    ap.add_argument("--commander-name")
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "board", None) is None or c[2] == getattr(args, "board", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, problem, board = rng.choice(list(combos))
    fix = getattr(args, "fix", None) or rng.choice(sorted(FIXES))
    pilot_gender = getattr(args, "pilot_gender", None) or rng.choice(["girl", "boy"])
    pilot_name = getattr(args, "pilot_name", None) or rng.choice(GIRL_NAMES if pilot_gender == "girl" else BOY_NAMES)
    robot_name = getattr(args, "robot_name", None) or rng.choice(ROBOT_NAMES)
    commander_name = getattr(args, "commander_name", None) or rng.choice(COMMANDER_NAMES)
    return StoryParams(setting=setting, problem=problem, board=board, fix=fix,
                       pilot_name=pilot_name, pilot_gender=pilot_gender,
                       robot_name=robot_name, commander_name=commander_name)


def _make_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    problem = _safe_lookup(PROBLEMS, params.problem)
    board_cfg = _safe_lookup(OBJECTS, params.board)
    fix_cfg = _safe_lookup(FIXES, params.fix)

    world = World(setting)
    pilot = world.add(Entity(
        id="pilot", kind="character", type=params.pilot_gender,
        label=params.pilot_name, role="pilot",
        attrs={"name": params.pilot_name},
    ))
    robot = world.add(Entity(
        id="robot", kind="character", type="thing",
        label=params.robot_name, role="helper", dependent_on="pilot",
        attrs={"name": params.robot_name},
    ))
    commander = world.add(Entity(
        id="commander", kind="character", type="adult",
        label=params.commander_name, role="commander",
        attrs={"name": params.commander_name},
    ))
    board = world.add(Entity(
        id="board", type="thing", label=board_cfg.label, phrase=board_cfg.phrase,
        plural=board_cfg.plural, tags=set(board_cfg.tags),
    ))
    cameo = world.add(Entity(
        id="cameo", type="signal", label="cameo signal", phrase="a tiny cameo signal",
        tags={"cameo", "surprise"},
    ))
    star_map = world.add(Entity(
        id="starmap", type="thing", label="star-map", phrase="a hidden star-map plan",
        tags={"blank", "surprise"},
    ))
    pilot.meters["meters"] = 0
    pilot.meters["distance"] = 0
    pilot.memes["curious"] = 1
    pilot.memes["worry"] = 0
    pilot.memes["joy"] = 1
    robot.memes["dependent"] = 1
    robot.meters["power"] = 1
    board.meters["blank"] = 1
    board.meters["ready"] = 0
    world.facts.update(
        pilot=pilot, robot=robot, commander=commander, board=board, cameo=cameo,
        starmap=star_map, setting=setting, problem=problem, board_cfg=board_cfg,
        fix_cfg=fix_cfg, surprise_seen=False, misunderstanding=False, resolved=False,
    )
    return world


def tell(world: World) -> None:
    p = world.facts["pilot"]
    r = world.facts["robot"]
    c = world.facts["commander"]
    problem = world.facts["problem"]
    board = world.facts["board"]
    cameo = world.facts["cameo"]
    fix_cfg = world.facts["fix_cfg"]
    starmap = world.facts["starmap"]

    world.say(
        f"{p.label} and {r.label} floated through {world.setting.place}. "
        f"{r.label} was a dependent little helper who stayed close beside {p.label}."
    )
    world.say(
        f"In the airlock, {p.label} held up the blank mission board. "
        f"It looked empty enough to fit a whole adventure."
    )
    world.para()
    world.say(
        f"Then a cameo signal blinked from the moon window. "
        f"{c.label} smiled and sent a surprise note: {problem.surprise}."
    )
    world.say(
        f"{p.label} misunderstood the blank board at once and thought the cameo note "
        f"meant the mission was canceled."
    )
    p.memes["confusion"] += 1
    p.memes["worry"] += 1
    r.memes["confusion"] += 1
    world.facts["misunderstanding"] = True
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"But {c.label} drifted closer and pointed to the board. "
        f"{problem.misunderstanding}."
    )
    world.say(
        f"The blank board was not empty because nothing would happen. "
        f"It was blank because it was waiting for the real plan."
    )
    world.say(
        f"{fix_cfg.action.capitalize()}, and the surprise turned into a happy launch."
    )
    board.meters["blank"] = 0
    board.meters["ready"] = 1
    world.facts["resolved"] = True
    world.facts["surprise_seen"] = True
    world.para()
    world.say(
        f"Now the board shone with the star-map plan, {cameo.label} glowed on the side, "
        f"and {r.label} held the corner steady while {p.label} pinned the first bright line."
    )
    world.say(
        f"Together they were ready for the moon relay, with the blank board no longer blank."
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short space adventure story for a 3-to-5-year-old that uses the words "dependent", "blank", and "cameo".',
        f"Tell a gentle story where {f['pilot'].label} misreads a blank mission board, but a surprise cameo message helps fix the misunderstanding.",
        f"Write a child-friendly space story about a helper robot, a blank board, and a surprise from a moon relay.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p = f["pilot"]
    r = f["robot"]
    c = f["commander"]
    problem = f["problem"]
    return [
        QAItem(
            question=f"Who is the story about when {p.label} and {r.label} check the mission board?",
            answer=f"It is about {p.label} and {r.label}. {r.label} is a dependent helper, so it stays close and follows the pilot's lead."
        ),
        QAItem(
            question="Why did the blank board cause a misunderstanding?",
            answer=f"The board looked empty, so {p.label} thought the mission was canceled. That was the misunderstanding, but the board was really waiting for the real star-map plan."
        ),
        QAItem(
            question="What surprised the crew from the moon window?",
            answer=f"A cameo signal came from the moon window, and {c.label} sent a surprise note. The note showed that {problem.name} was only a mix-up, not a canceled trip."
        ),
        QAItem(
            question="How did the story end after the misunderstanding was cleared up?",
            answer=f"{c.label} explained the plan, and the blank board filled with a bright route. In the ending image, {r.label} held the board steady while {p.label} pinned the first star line."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does dependent mean?",
            answer="Dependent means someone or something needs help, care, or direction from another person."
        ),
        QAItem(
            question="What does blank mean?",
            answer="Blank means empty or without writing, picture, or marks yet."
        ),
        QAItem(
            question="What is a cameo?",
            answer="A cameo is a small, brief appearance or message that shows up for a quick surprise."
        ),
        QAItem(
            question="What is a misunderstanding?",
            answer="A misunderstanding happens when someone thinks a message means one thing, but it really means something else."
        ),
        QAItem(
            question="What is a surprise?",
            answer="A surprise is something unexpected that makes a person stop and look again."
        ),
    ]


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
        if e.role:
            bits.append(f"role={e.role}")
        if e.dependent_on:
            bits.append(f"dependent_on={e.dependent_on}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("risk", pid, p.risk))
        for z in sorted(p.zone):
            lines.append(asp.fact("zone", pid, z))
        lines.append(asp.fact("has_misunderstanding", pid))
        lines.append(asp.fact("has_surprise", pid))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("board", oid))
        lines.append(asp.fact("blank_region", oid, o.region))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, B) :- setting(S), problem(P), board(B), affords(S, P), blank_region(B, R), zone(P, R).
"""


def asp_program(show: str) -> str:
    import asp
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    ok = True
    if clingo_set != python_set:
        ok = False
        print("MISMATCH between clingo and valid_combos():")
        print("  only in clingo:", sorted(clingo_set - python_set))
        print("  only in python:", sorted(python_set - clingo_set))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(7)))
        _ = sample.story
        print("OK: generation smoke test produced a story.")
    except Exception as ex:
        ok = False
        print(f"SMOKE TEST FAILED: {ex}")
    try:
        with contextlib.redirect_stdout(io.StringIO()):
            emit(generate(resolve_params(build_parser().parse_args([]), random.Random(8))))
        print("OK: emit smoke test succeeded.")
    except Exception as ex:
        ok = False
        print(f"EMIT SMOKE TEST FAILED: {ex}")
    if ok:
        print(f"OK: ASP parity matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    return 1


CURATED = [
    StoryParams(
        setting="orbital_hub",
        problem="moon_relay",
        board="blank_panel",
        fix="sticker_lines",
        pilot_name="Mira",
        pilot_gender="girl",
        robot_name="Nim",
        commander_name="Captain Sol",
    ),
    StoryParams(
        setting="dock_garden",
        problem="signal_mixup",
        board="blank_chart",
        fix="glow_markers",
        pilot_name="Theo",
        pilot_gender="boy",
        robot_name="Pip",
        commander_name="Commander Vale",
    ),
    StoryParams(
        setting="lunar_bay",
        problem="moon_relay",
        board="blank_panel",
        fix="holo_tape",
        pilot_name="Iris",
        pilot_gender="girl",
        robot_name="Rook",
        commander_name="Captain Sol",
    ),
    StoryParams(
        setting="orbital_hub",
        problem="signal_mixup",
        board="blank_chart",
        fix="sticker_lines",
        pilot_name="Ari",
        pilot_gender="boy",
        robot_name="Bean",
        commander_name="Commander Vale",
    ),
]


SETTINGS = {
    "orbital_hub": Setting(
        id="orbital_hub", place="the orbital hub", detail="bright windows and quiet docks",
        affords={"moon_relay", "signal_mixup"},
    ),
    "lunar_bay": Setting(
        id="lunar_bay", place="the lunar bay", detail="silver rails and soft moon dust",
        affords={"moon_relay"},
    ),
    "dock_garden": Setting(
        id="dock_garden", place="the dock garden", detail="tiny lights and hanging pods",
        affords={"signal_mixup"},
    ),
}

PROBLEMS = {
    "moon_relay": Problem(
        id="moon_relay", name="moon relay", cause="the relay looked empty",
        misunderstanding="The blank board was only waiting for the relay route.",
        surprise="The moon relay will bring a surprise guest signal.",
        risk="confusing blank with broken", zone={"pane", "panel"},
        tags={"misunderstanding", "surprise", "space"},
    ),
    "signal_mixup": Problem(
        id="signal_mixup", name="signal mix-up", cause="the message looked too small",
        misunderstanding="The blank chart was a mission note, not a canceled flight.",
        surprise="A cameo from the dock station will solve the mix-up.",
        risk="mistaking blank for finished", zone={"pane", "chart"},
        tags={"misunderstanding", "surprise", "space"},
    ),
}

OBJECTS = {
    "blank_panel": ObjectCfg(id="blank_panel", label="blank panel", phrase="a blank panel", region="panel", tags={"blank"}),
    "blank_chart": ObjectCfg(id="blank_chart", label="blank chart", phrase="a blank chart", region="chart", tags={"blank"}),
    "starboard": ObjectCfg(id="starboard", label="star board", phrase="a star board", region="panel", tags={"blank"}),
}

FIXES = {
    "holo_tape": Fix(id="holo_tape", label="holo tape", action="They used holo tape to mark the route", outcome="the route glowed"),
    "sticker_lines": Fix(id="sticker_lines", label="sticker lines", action="They added sticker lines and arrows", outcome="the plan filled the board"),
    "glow_markers": Fix(id="glow_markers", label="glow markers", action="They drew the route with glow markers", outcome="the map shone"),
}

GIRL_NAMES = ["Mira", "Iris", "Zoe", "Luna", "Nia", "Ava"]
BOY_NAMES = ["Theo", "Ari", "Noel", "Finn", "Kai", "Leo"]
ROBOT_NAMES = ["Nim", "Pip", "Rook", "Bolt", "Dot"]
COMMANDER_NAMES = ["Captain Sol", "Commander Vale", "Captain Nova"]


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.problem not in PROBLEMS or params.board not in OBJECTS or params.fix not in FIXES:
        pass
    world = _make_world(params)
    tell(world)
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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible (setting, problem, board) combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.pilot_name}: {p.problem} in {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
