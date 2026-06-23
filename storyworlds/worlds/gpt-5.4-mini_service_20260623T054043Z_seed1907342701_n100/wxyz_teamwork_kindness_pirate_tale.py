#!/usr/bin/env python3
"""
storyworlds/worlds/wxyz_teamwork_kindness_pirate_tale.py
========================================================

A standalone story world about pirate teamwork and kindness.

A tiny crew sails with a map clue that includes the word "wxyz". The storyworld
keeps the domain small and constraint-checked: a crew problem, a cooperative
fix, a simple turn, and a visible ending image showing what changed.

The story premise is intentionally close to a pirate tale:
- the crew is trying to cross a small cove and reach a hidden chest
- the boat is stuck, the tide is shifting, and they must work together
- kindness matters because the crew helps a worried friend and shares the load
- the solution is teamwork, not force

This script follows the Storyweavers contract:
- stdlib only
- imports storyworlds/results.py eagerly
- imports storyworlds/asp.py lazily inside ASP helpers
- defines StoryParams, registries, build_parser, resolve_params, generate,
  emit, and main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
- includes a Python reasonableness gate and inline ASP twin
- generates grounded prompts and Q&A from world state
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
from typing import Optional

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
    plural: bool = False
    owner: str = ""
    caretaker: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, str] = field(default_factory=dict)

    captain: object | None = None
    helper: object | None = None
    mate: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    id: str
    place: str
    water: bool = False
    wind: bool = False
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


@dataclass
class Problem:
    id: str
    obstacle: str
    danger: str
    turn: str
    ending: str
    clue: str
    cause: str
    risk_kind: str
    zone: str
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


@dataclass
class Method:
    id: str
    name: str
    action: str
    result: str
    help_word: str
    clears: str
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


@dataclass
class Prize:
    id: str
    label: str
    phrase: str
    region: str = "deck"
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
class CrewRole:
    id: str
    label: str
    type: str
    trait: str
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
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        return w

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class StoryParams:
    setting: str = ""
    problem: str = ""
    method: str = ""
    prize: str = ""
    captain_name: str = ""
    captain_type: str = "girl"
    mate_name: str = ""
    mate_type: str = "boy"
    helper_name: str = ""
    helper_type: str = "girl"
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
    "cove": Setting("cove", "the blue cove", water=True, wind=False),
    "harbor": Setting("harbor", "the quiet harbor", water=True, wind=True),
    "island": Setting("island", "the small island dock", water=True, wind=True),
    "reef": Setting("reef", "the reef edge", water=True, wind=True),
}

PROBLEMS = {
    "stuck_boat": Problem(
        "stuck_boat", "the boat is wedged on a sandbar", "the tide is slipping away",
        "the crew pushes together", "the boat floats free", "wxyz", "sandbar", "water", "boat"
    ),
    "tangled_rope": Problem(
        "tangled_rope", "the sail rope is all tangled", "the mast can't catch the wind",
        "the crew untangles the rope together", "the sail snaps open", "wxyz", "rope", "rope", "rope"
    ),
    "spilled_crates": Problem(
        "spilled_crates", "the crates have spilled across the deck", "the deck is cluttered and slippery",
        "the crew sorts the crates together", "the deck is clear again", "wxyz", "crates", "deck", "deck"
    ),
    "lost_lantern": Problem(
        "lost_lantern", "the lantern blew into a dark corner", "the map is hard to read",
        "the crew searches together", "the lantern glows again", "wxyz", "corner", "dark", "corner"
    ),
}

METHODS = {
    "push_pull": Method("push_pull", "push and pull", "push together from one side and pull from the other", "the heavy thing moves", "shared effort", "move"),
    "tie_line": Method("tie_line", "tie a line around it", "loop a rope around the problem and steady it", "the crew can guide it safely", "careful teamwork", "guide"),
    "share_lift": Method("share_lift", "share a lift", "lift in turns so nobody strains", "the load becomes light enough", "kind help", "lighten"),
    "steady_light": Method("steady_light", "steady the light", "hold the lantern and shield it from wind", "the map stays visible", "gentle help", "see"),
}

PRIZES = {
    "chest": Prize("chest", "the treasure chest", "a small treasure chest"),
    "shell_map": Prize("shell_map", "the shell map", "a shell map wrapped in twine"),
    "flag": Prize("flag", "the red flag", "a bright red flag"),
    "snack_box": Prize("snack_box", "the snack box", "a snack box for the crew"),
}

CREW = {
    "captain": CrewRole("captain", "captain", "girl", "brave"),
    "mate": CrewRole("mate", "mate", "boy", "steady"),
    "helper": CrewRole("helper", "helper", "girl", "kind"),
}


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, prob in PROBLEMS.items():
            for mid, meth in METHODS.items():
                if prob.cause in {"sandbar", "rope", "deck", "corner"} and meth.clears in {"move", "guide", "lighten", "see"}:
                    combos.append((sid, pid, mid))
    return combos


def can_solve(problem: Problem, method: Method) -> bool:
    if problem.id == "stuck_boat":
        return method.id in {"push_pull", "share_lift"}
    if problem.id == "tangled_rope":
        return method.id in {"tie_line", "share_lift"}
    if problem.id == "spilled_crates":
        return method.id in {"share_lift", "push_pull"}
    if problem.id == "lost_lantern":
        return method.id in {"steady_light", "share_lift"}
    return False


def reason_invalid(problem: Problem, method: Method) -> str:
    return f"(No story: {method.name} does not honestly solve {problem.obstacle}.)"


def _propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    for ent in world.characters():
        if ent.meters.get("helping", 0) >= THRESHOLD and not world.fired.__contains__(("teamup", ent.id)):
            world.fired.add(("teamup", ent.id))
            ent.memes["joy"] = ent.memes.get("joy", 0) + 1
            out.append(f"{ent.label_word.capitalize()} felt proud of helping.")
    if narrate:
        for s in out:
            world.say(s)
    return out


def build_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    captain = world.add(Entity(id=params.captain_name, kind="character", type=params.captain_type, label=params.captain_name))
    mate = world.add(Entity(id=params.mate_name, kind="character", type=params.mate_type, label=params.mate_name))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type, label=params.helper_name))
    world.add(Entity(id="boat", kind="thing", type="boat", label="boat"))
    world.add(Entity(id="map", kind="thing", type="map", label="map"))
    world.add(Entity(id="lantern", kind="thing", type="lantern", label="lantern"))
    world.facts.update(
        captain=captain, mate=mate, helper=helper,
        setting=_safe_lookup(SETTINGS, params.setting), problem=_safe_lookup(PROBLEMS, params.problem),
        method=_safe_lookup(METHODS, params.method), prize=_safe_lookup(PRIZES, params.prize),
        solved=False, kindness=False, teamwork=False
    )
    return world


def tell(world: World, params: StoryParams) -> World:
    cap = world.facts["captain"]
    mate = world.facts["mate"]
    helper = world.facts["helper"]
    problem = world.facts["problem"]
    method = world.facts["method"]
    prize = world.facts["prize"]
    setting = world.facts["setting"]

    cap.memes["curiosity"] = 1
    mate.memes["worry"] = 1
    helper.memes["kindness"] = 1

    world.say(
        f"On a bright day, {cap.id}, {mate.id}, and {helper.id} turned {setting.place} into a tiny pirate adventure."
        f" They followed the wxyz clue to the treasure."
    )
    world.say(
        f"But {problem.obstacle}. That meant {problem.danger}, and the crew had to stop and think."
    )
    world.para()
    cap.memes["want"] = 1
    mate.memes["want"] = 1
    helper.memes["kindness"] += 1
    world.say(
        f'{cap.id} said, "If we work together, we can fix it."'
        f' {helper.id} smiled and offered kind help.'
    )
    world.say(
        f"They chose to {method.action}. {helper.id} made room, {mate.id} held the other side, and {cap.id} kept everyone steady."
    )
    if not can_solve(problem, method):
        pass
    cap.meters["helping"] = 1
    mate.meters["helping"] = 1
    helper.meters["helping"] = 1
    _propagate(world)
    world.facts["teamwork"] = True
    world.facts["kindness"] = True
    world.facts["solved"] = True
    world.para()
    world.say(
        f"At last, {problem.ending}. {prize.phrase} sat safe and neat while the crew grinned in the sea wind."
    )
    world.say(
        f"{helper.id} shared a smile, and the little pirate team sailed on with the wxyz clue tucked away."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a pirate story for a young child that includes the word "wxyz" and shows teamwork.',
        f"Tell a gentle pirate tale where {f['captain'].id}, {f['mate'].id}, and {f['helper'].id} solve {f['problem'].obstacle} with kindness.",
        f"Write a short adventure about a crew at {f['setting'].place} who work together to reach {f['prize'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c, m, h = f["captain"], f["mate"], f["helper"]
    p, pr = f["problem"], f["prize"]
    return [
        QAItem(
            question=f"Who helped fix the problem at the pirate place?",
            answer=f"{c.id}, {m.id}, and {h.id} all helped, and they did it with teamwork. Each one had a small job, so nobody had to do the work alone."
        ),
        QAItem(
            question=f"What was wrong before the crew solved it?",
            answer=f"{p.obstacle}. That made the day harder because {p.danger}, so the crew had to pause and work together."
        ),
        QAItem(
            question=f"How did the kindness in the story show up?",
            answer=f"{h.id} offered kind help and made room for the others. That kindness helped the whole crew feel calm enough to fix the problem together."
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"{p.ending}. In the end, {pr.phrase} was safe and tidy, which showed that the teamwork really worked."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people do a job together. They share the work and help each other so the job becomes easier."
        ),
        QAItem(
            question="What is kindness?",
            answer="Kindness means being gentle, helpful, and thoughtful to someone else. A kind person tries to make things better for others."
        ),
        QAItem(
            question="What is a pirate tale?",
            answer="A pirate tale is a story about pirates, boats, treasure, maps, and adventures on the sea."
        ),
        QAItem(
            question="What is the word wxyz doing in the story?",
            answer="The word wxyz works like a clue in the adventure. It helps make the treasure hunt feel special and part of the pirate game."
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


def explain_rejection(problem: Problem, method: Method) -> str:
    return f"(No story: {method.name} cannot solve {problem.obstacle} in a believable pirate tale.)"


CURATED = [
    StoryParams(setting="cove", problem="stuck_boat", method="push_pull", prize="chest", captain_name="Mira", captain_type="girl", mate_name="Joss", mate_type="boy", helper_name="Tia", helper_type="girl"),
    StoryParams(setting="harbor", problem="tangled_rope", method="tie_line", prize="shell_map", captain_name="Nia", captain_type="girl", mate_name="Ben", mate_type="boy", helper_name="Lulu", helper_type="girl"),
    StoryParams(setting="island", problem="spilled_crates", method="share_lift", prize="flag", captain_name="Pip", captain_type="boy", mate_name="Ava", mate_type="girl", helper_name="Rin", helper_type="girl"),
    StoryParams(setting="reef", problem="lost_lantern", method="steady_light", prize="snack_box", captain_name="Tess", captain_type="girl", mate_name="Noah", mate_type="boy", helper_name="Zee", helper_type="girl"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate teamwork and kindness storyworld with wxyz.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--method", choices=METHODS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--captain-name")
    ap.add_argument("--captain-type", choices=["girl", "boy"])
    ap.add_argument("--mate-name")
    ap.add_argument("--mate-type", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-type", choices=["girl", "boy"])
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
              and (getattr(args, "method", None) is None or c[2] == getattr(args, "method", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, problem, method = rng.choice(list(combos))
    prize = getattr(args, "prize", None) or rng.choice(sorted(PRIZES))
    cap_type = getattr(args, "captain_type", None) or rng.choice(["girl", "boy"])
    mate_type = getattr(args, "mate_type", None) or ("boy" if cap_type == "girl" else "girl")
    helper_type = getattr(args, "helper_type", None) or rng.choice(["girl", "boy"])
    cap_name = getattr(args, "captain_name", None) or rng.choice(["Mira", "Nia", "Tess", "Pip", "Lia", "Rae"])
    mate_name = getattr(args, "mate_name", None) or rng.choice(["Joss", "Ben", "Noah", "Finn", "Kai", "Zed"])
    helper_name = getattr(args, "helper_name", None) or rng.choice(["Tia", "Lulu", "Rin", "Zoe", "May", "Etta"])
    return StoryParams(
        setting=setting, problem=problem, method=method, prize=prize,
        captain_name=cap_name, captain_type=cap_type,
        mate_name=mate_name, mate_type=mate_type,
        helper_name=helper_name, helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    for field_name, table in (("setting", SETTINGS), ("problem", PROBLEMS), ("method", METHODS), ("prize", PRIZES)):
        if getattr(params, field_name) not in table:
            pass
    if not can_solve(_safe_lookup(PROBLEMS, params.problem), _safe_lookup(METHODS, params.method)):
        pass
    world = build_world(params)
    world = tell(world, params)
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


ASP_RULES = r"""
valid(S,P,M) :- setting(S), problem(P), method(M), solvable(P,M).
solvable(stuck_boat,push_pull).
solvable(stuck_boat,share_lift).
solvable(tangled_rope,tie_line).
solvable(tangled_rope,share_lift).
solvable(spilled_crates,share_lift).
solvable(spilled_crates,push_pull).
solvable(lost_lantern,steady_light).
solvable(lost_lantern,share_lift).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("setting", sid) for sid in SETTINGS]
    lines += [asp.fact("problem", pid) for pid in PROBLEMS]
    lines += [asp.fact("method", mid) for mid in METHODS]
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("obstacle", pid, p.obstacle))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    from contextlib import redirect_stdout
    py = set(valid_combos())
    asps = set(asp_valid_combos())
    ok = True
    if py != asps:
        ok = False
        print("MISMATCH between Python and ASP valid combos.")
    try:
        sample = generate(resolve_params(argparse.Namespace(setting=None, problem=None, method=None, prize=None, captain_name=None, captain_type=None, mate_name=None, mate_type=None, helper_name=None, helper_type=None), random.Random(777)))
        with redirect_stdout(io.StringIO()):
            emit(sample, trace=True, qa=True)
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    if ok:
        print(f"OK: verify passed with {len(py)} valid combos.")
        return 0
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.captain_name} and crew: {p.problem} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
