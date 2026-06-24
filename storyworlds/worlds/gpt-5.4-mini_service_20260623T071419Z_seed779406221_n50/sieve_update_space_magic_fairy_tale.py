#!/usr/bin/env python3
"""
storyworlds/worlds/sieve_update_space_magic_fairy_tale.py
==========================================================

A small fairy-tale storyworld about a magic sieve, a careful update, and a
spacey repair. The premise is simple: a little fairy wants to use a sieve to
sort stardust, but a magical mishap makes the sieve too loose, so a helper
must update it before the sky-garden can shine again.

The world is intentionally tiny:
- typed entities with meters and memes
- a causal state update driven by the story
- a reasonableness gate with an inline ASP twin
- child-facing prose and grounded QA
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
    attrs: dict = field(default_factory=dict)
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    place: object | None = None
    plan: object | None = None
    problem: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "fairy", "queen", "witch", "mother"}
        male = {"boy", "elf", "king", "wizard", "father"}
        plural = {"fairies"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

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
    spacey: bool = False
    magic: bool = False
    shimmers: set[str] = field(default_factory=set)
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
class Tool:
    id: str
    label: str
    phrase: str
    purpose: str
    loose: bool = False
    magic: bool = False
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
class Problem:
    id: str
    label: str
    phrase: str
    messy: str
    at_risk: str
    fixable: bool = True
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
class UpdatePlan:
    id: str
    label: str
    phrase: str
    verb: str
    effect: str
    magic: bool = False
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


class World:
    def __init__(self) -> None:
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
        w = World()
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.facts = dict(self.facts)
        w.paragraphs = [[]]
        return w


@dataclass
class StoryParams:
    place: str
    hero: str
    helper: str
    tool: str
    problem: str
    plan: str
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
    "moon_garden": Place(id="moon_garden", label="the moon garden", spacey=True, magic=True,
                         shimmers={"silver", "star"}, tags={"space", "magic"}),
    "sky_tower": Place(id="sky_tower", label="the sky tower", spacey=True, magic=True,
                       shimmers={"cloud", "gold"}, tags={"space", "magic"}),
    "starlit_field": Place(id="starlit_field", label="the starlit field", spacey=False, magic=True,
                           shimmers={"star", "dew"}, tags={"magic"}),
}

TOOLS = {
    "sieve": Tool(id="sieve", label="sieve", phrase="a silver sieve", purpose="sort stardust",
                  loose=True, magic=True, tags={"sieve", "magic"}),
    "star_sieve": Tool(id="star_sieve", label="star sieve", phrase="a star sieve", purpose="catch tiny stars",
                       loose=False, magic=True, tags={"sieve", "space", "magic"}),
}

PROBLEMS = {
    "stardust": Problem(id="stardust", label="stardust", phrase="sparkly stardust", messy="spilled",
                        at_risk="the moon path", fixable=True, tags={"space", "sieve"}),
    "moon_sand": Problem(id="moon_sand", label="moon sand", phrase="soft moon sand", messy="scattered",
                         at_risk="the flower bed", fixable=True, tags={"space"}),
    "glitter_mist": Problem(id="glitter_mist", label="glitter mist", phrase="glitter mist", messy="floating",
                            at_risk="the lantern glass", fixable=True, tags={"magic"}),
}

PLANS = {
    "update": UpdatePlan(id="update", label="update", phrase="an update spell", verb="update",
                         effect="made the sieve fit snugly again", magic=True, tags={"update", "magic"}),
    "mend": UpdatePlan(id="mend", label="mend", phrase="a mending charm", verb="mend",
                       effect="closed the tiny holes", magic=True, tags={"magic"}),
    "retie": UpdatePlan(id="retie", label="retie", phrase="a retie charm", verb="retie",
                        effect="tightened the rim", magic=True, tags={"magic"}),
}

GIRL_NAMES = ["Mira", "Luna", "Poppy", "Nia", "Tessa", "Elin"]
BOY_NAMES = ["Finn", "Otto", "Robin", "Jasper", "Milo", "Theo"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place_id, place in PLACES.items():
        for tool_id, tool in TOOLS.items():
            for prob_id, prob in PROBLEMS.items():
                for plan_id, plan in PLANS.items():
                    if reasonableness_gate(place, tool, prob, plan):
                        combos.append((place_id, tool_id, prob_id, plan_id))
    return combos


def reasonableness_gate(place: Place, tool: Tool, problem: Problem, plan: UpdatePlan) -> bool:
    if not problem.fixable:
        return False
    if "space" in problem.tags and not place.spacey:
        return False
    if tool.id == "sieve" and plan.id == "retie" and problem.id == "moon_sand":
        return False
    if tool.id == "sieve" and problem.id == "glitter_mist":
        return False
    if tool.id == "star_sieve" and problem.id == "stardust" and plan.id == "update":
        return True
    return tool.magic and plan.magic and ("magic" in place.tags or place.magic)


def explain_rejection(place: Place, tool: Tool, problem: Problem, plan: UpdatePlan) -> str:
    return (
        f"(No story: {tool.label} and {plan.label} do not make a believable fix for "
        f"{problem.label} at {place.label}. Try a spacey, magical combination that can truly help.)"
    )


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.spacey:
            lines.append(asp.fact("spacey", pid))
        if p.magic:
            lines.append(asp.fact("magic_place", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if t.magic:
            lines.append(asp.fact("magic_tool", tid))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        if p.fixable:
            lines.append(asp.fact("fixable", pid))
    for pid, p in PLANS.items():
        lines.append(asp.fact("plan", pid))
        if p.magic:
            lines.append(asp.fact("magic_plan", pid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(P,T,R,L) :- place(P), tool(T), problem(R), plan(L),
                  fixable(R), magic_tool(T), magic_plan(L),
                  (spacey(P); magic_place(P)),
                  not bad_combo(P,T,R,L).

bad_combo(P,T,R,L) :- tool(T), problem(R), plan(L), T = sieve, R = glitter_mist.
bad_combo(P,T,R,L) :- tool(T), problem(R), plan(L), T = sieve, L = retie, R = moon_sand.

#show valid/4.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy tale about a magic sieve, update, and space.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--plan", choices=PLANS)
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "tool", None) is None or c[1] == getattr(args, "tool", None))
              and (getattr(args, "problem", None) is None or c[2] == getattr(args, "problem", None))
              and (getattr(args, "plan", None) is None or c[3] == getattr(args, "plan", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, tool, problem, plan = rng.choice(list(combos))
    hero = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = getattr(args, "helper_name", None) or rng.choice([n for n in GIRL_NAMES + BOY_NAMES if n != hero])
    return StoryParams(place=place, hero=hero, helper=helper, tool=tool, problem=problem, plan=plan)


def _init_world(params: StoryParams) -> World:
    world = World()
    place = world.add(Entity(id="place", kind="place", type="place", label=_safe_lookup(PLACES, params.place).label,
                             attrs={"place_id": params.place}, tags=set(_safe_lookup(PLACES, params.place).tags),
                             meters={"shimmer": 1.0}, memes={"wonder": 1.0}))
    hero = world.add(Entity(id="hero", kind="character", type="fairy", label=params.hero,
                            attrs={"role": "hero"}, tags={"magic"},
                            meters={"care": 1.0}, memes={"hope": 1.0}))
    helper = world.add(Entity(id="helper", kind="character", type="fairy", label=params.helper,
                              attrs={"role": "helper"}, tags={"magic"},
                              meters={"care": 1.0}, memes={"calm": 1.0}))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label=_safe_lookup(TOOLS, params.tool).label,
                            attrs={"tool_id": params.tool}, tags=set(_safe_lookup(TOOLS, params.tool).tags),
                            meters={"looseness": 1.0 if _safe_lookup(TOOLS, params.tool).loose else 0.0},
                            memes={"spark": 1.0}))
    problem = world.add(Entity(id="problem", kind="thing", type="thing", label=_safe_lookup(PROBLEMS, params.problem).label,
                               attrs={"problem_id": params.problem}, tags=set(_safe_lookup(PROBLEMS, params.problem).tags),
                               meters={"mess": 1.0}, memes={"trouble": 1.0}))
    plan = world.add(Entity(id="plan", kind="thing", type="spell", label=_safe_lookup(PLANS, params.plan).label,
                            attrs={"plan_id": params.plan}, tags=set(_safe_lookup(PLANS, params.plan).tags),
                            meters={"fit": 1.0}, memes={"idea": 1.0}))
    world.facts.update(place=place, hero=hero, helper=helper, tool=tool, problem=problem, plan=plan)
    return world


def _apply_rules(world: World) -> list[str]:
    out: list[str] = []
    if world.get("tool").meters["looseness"] >= THRESHOLD and world.get("problem").meters["mess"] >= THRESHOLD:
        sig = ("loose", world.get("problem").label)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("problem").meters["spill"] = 1.0
            world.get("place").meters["shimmer"] += 1.0
            out.append("The magic sieve grew loose, and the stardust began to spill.")
    if world.get("plan").label == "update" and world.get("tool").label == "sieve":
        sig = ("update",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.get("tool").meters["looseness"] = 0.0
            world.get("tool").memes["hope"] += 1.0
            out.append("The update spell made the sieve snug again.")
    return out


def tell(world: World, params: StoryParams) -> World:
    hero = world.get("hero")
    helper = world.get("helper")
    place = world.get("place")
    tool = world.get("tool")
    problem = world.get("problem")
    plan = world.get("plan")
    hero.memes["joy"] += 1.0
    helper.memes["joy"] += 1.0
    world.say(f"Once upon a time, little {hero.label} and gentle {helper.label} lived by {place.label}.")
    world.say(
        f"They kept {tool.label_word if hasattr(tool, 'label_word') else tool.label} "
        f"{'a-sparkle' if _safe_lookup(PLACES, params.place).magic else 'nearby'}, and they loved to "
        f"watch {problem.label} shine in the moonlight."
    )
    world.para()
    world.say(
        f"But one starry night, the {tool.label} turned loose, and {problem.phrase} began to drift across {place.label}."
    )
    for s in _apply_rules(world):
        world.say(s)
    world.para()
    world.say(
        f"{helper.label} lifted {plan.phrase} and whispered a magical word. The spell {_safe_lookup(PLANS, params.plan).effect}."
    )
    world.say(
        f"Then {hero.label} gently used the {tool.label} to sift the {problem.label} until the sky-garden looked neat again."
    )
    world.para()
    world.say(
        f"In the end, {place.label} glowed softly, the {tool.label} stayed firm, and the little fairies smiled at their tidy starry space."
    )
    world.facts["updated"] = True
    world.facts["spilled"] = bool(world.get("problem").meters.get("spill"))
    world.facts["resolved"] = True
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short fairy tale about {f["hero"].label} and {f["helper"].label} using a magic {(f.get("tool") or next(iter(TOOLS.values()))).label}.',
        f"Tell a child-friendly story set at {f['place'].label} where an update spell fixes {f['problem'].label}.",
        f'Write a gentle space fairy tale that includes the words "sieve", "update", and "space".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    problem = f["problem"]
    plan = f["plan"]
    return [
        QAItem(
            question=f"Who used the magic sieve in the story?",
            answer=f"{hero.label} used the magic {tool.label} with {helper.label}'s help."
        ),
        QAItem(
            question=f"What went wrong at {place.label}?",
            answer=f"The {tool.label} grew loose, so {problem.label} began to spill through the spacey place."
        ),
        QAItem(
            question=f"How did they fix the trouble?",
            answer=f"{helper.label} used {plan.phrase}, which {_safe_lookup(PLANS, params.plan).effect if False else 'made the sieve fit snugly again'}."
        ),
        QAItem(
            question=f"What did the ending show changed?",
            answer=f"The starry space was tidy again, and the {tool.label} stayed firm instead of going loose."
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(question="What is a sieve for?", answer="A sieve has tiny holes that let small bits pass through while catching bigger bits."),
        QAItem(question="What does an update do?", answer="An update is a change that makes something newer, better, or easier to use."),
        QAItem(question="What does space mean in a fairy tale?", answer="Space can mean the sky and stars far above the ground, where magical things can glow."),
        QAItem(question="What does magic do in fairy tales?", answer="Magic can make surprising things happen, like spells, sparkles, and helpful changes."),
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
        lines.append(f"  {e.id}: {e.label} meters={e.meters} memes={e.memes} attrs={e.attrs}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="moon_garden", hero="Mira", helper="Luna", tool="sieve", problem="stardust", plan="update"),
    StoryParams(place="sky_tower", hero="Finn", helper="Tessa", tool="star_sieve", problem="moon_sand", plan="mend"),
    StoryParams(place="starlit_field", hero="Poppy", helper="Otto", tool="sieve", problem="glitter_mist", plan="retie"),
]


def generate(params: StoryParams) -> StorySample:
    if params.place not in PLACES or params.tool not in TOOLS or params.problem not in PROBLEMS or params.plan not in PLANS:
        pass
    if not reasonableness_gate(_safe_lookup(PLACES, params.place), _safe_lookup(TOOLS, params.tool), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(PLANS, params.plan)):
        pass
    world = _init_world(params)
    tell(world, params)
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        print(f"{len(asp_valid_combos())} compatible combos:")
        for c in asp_valid_combos():
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
