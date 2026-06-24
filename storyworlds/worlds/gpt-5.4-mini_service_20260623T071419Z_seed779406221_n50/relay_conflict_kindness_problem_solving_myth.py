#!/usr/bin/env python3
"""
relay_conflict_kindness_problem_solving_myth.py
===============================================

A small myth-style storyworld about a relay through a sacred path, where a
conflict blocks the way, kindness repairs trust, and problem solving restores
the relay.

The seed image:
---
A river spirit promised a village that its lantern would carry light from the
spring shrine to the hill shrine each night. Three helpers took turns in a relay
along the path. When one helper argued with another and dropped the lantern,
the village feared the light would fail. Then a kinder helper spoke gently,
found a safer way to pass the lantern around the broken stone, and the relay
reached the hill before moonrise.

This world models:
- a relay passed between typed entities
- conflict as an emotional meter that can block the relay
- kindness as an emotional meter that lowers conflict and helps cooperation
- problem solving as a physical/cognitive action that clears the path
- a mythic, child-facing voice with concrete ending imagery

Contract notes:
- standalone stdlib script
- imports storyworlds/results eagerly
- imports storyworlds/asp lazily inside helpers
- includes Python reasonableness gate plus inline ASP twin
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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
    title: str = ""
    role: str = ""
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    rival: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister", "queen", "priestess"}
        male = {"boy", "father", "man", "brother", "king", "priest"}
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
class Path:
    id: str
    label: str
    place: str
    length: int
    hazard: str = ""
    kind: str = "path"
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
class RelayItem:
    id: str
    label: str
    phrase: str
    bright: str
    fragile: bool = True
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
    issue: str
    fix_hint: str
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
class KindAction:
    id: str
    label: str
    phrase: str
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
    def __init__(self, setting: str) -> None:
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
        return c


@dataclass
class StoryParams:
    setting: str
    hero: str
    helper: str
    rival: str
    item: str
    path: str
    problem: str
    kindness: str
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
    "river_shrine": "the river shrine",
    "hill_shrine": "the hill shrine",
    "sun_bridge": "the sun bridge",
}

PATHS = {
    "river_road": Path(
        id="river_road",
        label="stone road",
        place="the river shrine",
        length=4,
        hazard="a broken stone step",
        tags={"river", "stone", "relay"},
    ),
    "hill_steps": Path(
        id="hill_steps",
        label="hill steps",
        place="the hill shrine",
        length=5,
        hazard="a fallen branch",
        tags={"hill", "steps", "relay"},
    ),
    "sun_bridge": Path(
        id="sun_bridge",
        label="bridge path",
        place="the sun bridge",
        length=3,
        hazard="a narrow crack",
        tags={"bridge", "relay"},
    ),
}

ITEMS = {
    "lantern": RelayItem(
        id="lantern",
        label="lantern",
        phrase="a bronze lantern",
        bright="glowed like a small star",
        tags={"lantern", "light", "relay"},
    ),
    "torch": RelayItem(
        id="torch",
        label="torch",
        phrase="a reed torch",
        bright="burned warm and gold",
        tags={"torch", "light", "relay"},
    ),
}

PROBLEMS = {
    "broken_step": Problem(
        id="broken_step",
        label="broken step",
        issue="the path had a broken step",
        fix_hint="build a safe line around it",
        tags={"problem", "problem_solving"},
    ),
    "river_wind": Problem(
        id="river_wind",
        label="river wind",
        issue="the wind kept bending the flame",
        fix_hint="cup the lantern and pass it low",
        tags={"problem", "problem_solving"},
    ),
    "fog_gate": Problem(
        id="fog_gate",
        label="fog gate",
        issue="fog hid the next marker stone",
        fix_hint="listen for the bell and count steps",
        tags={"problem", "problem_solving"},
    ),
}

KINDNESS = {
    "gentle_words": KindAction(
        id="gentle_words",
        label="gentle words",
        phrase="spoke gently and listened",
        tags={"kindness"},
    ),
    "shared_turn": KindAction(
        id="shared_turn",
        label="shared turn",
        phrase="shared the next turn without complaint",
        tags={"kindness"},
    ),
    "steady_hand": KindAction(
        id="steady_hand",
        label="steady hand",
        phrase="offered a steady hand",
        tags={"kindness"},
    ),
}

GIVEN_NAMES = ["Ari", "Mara", "Niko", "Lena", "Suri", "Tavi", "Ivo", "Kira"]
TITLES = ["runner", "keeper", "watcher", "guide", "messenger"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for setting in SETTINGS:
        for path in PATHS:
            for item in ITEMS:
                for problem in PROBLEMS:
                    if path == "river_road" and problem in {"broken_step", "river_wind"}:
                        combos.append((setting, path, item, problem))
                    elif path == "hill_steps" and problem in {"broken_step", "fog_gate"}:
                        combos.append((setting, path, item, problem))
                    elif path == "sun_bridge" and problem in {"river_wind", "fog_gate"}:
                        combos.append((setting, path, item, problem))
    return combos


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid, p in PATHS.items():
        lines.append(asp.fact("path", pid))
        lines.append(asp.fact("hazard", pid, p.hazard or "none"))
    for iid in ITEMS:
        lines.append(asp.fact("item", iid))
    for prob in PROBLEMS:
        lines.append(asp.fact("problem", prob))
    for kid in KINDNESS:
        lines.append(asp.fact("kindness", kid))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S, P, I, R) :- setting(S), path(P), item(I), problem(R), compatible(P, R).
compatible(river_road, broken_step).
compatible(river_road, river_wind).
compatible(hill_steps, broken_step).
compatible(hill_steps, fog_gate).
compatible(sun_bridge, river_wind).
compatible(sun_bridge, fog_gate).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic relay storyworld with conflict, kindness, and problem solving.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--path", choices=PATHS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--kindness", choices=KINDNESS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--rival")
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
              and (getattr(args, "path", None) is None or c[1] == getattr(args, "path", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))
              and (getattr(args, "problem", None) is None or c[3] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, path, item, problem = rng.choice(list(combos))
    kindness = getattr(args, "kindness", None) or rng.choice(sorted(KINDNESS))
    hero = getattr(args, "hero", None) or rng.choice(GIVEN_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in GIVEN_NAMES if n != hero])
    rival = getattr(args, "rival", None) or rng.choice([n for n in GIVEN_NAMES if n not in {hero, helper}])
    return StoryParams(setting=setting, hero=hero, helper=helper, rival=rival, item=item, path=path, problem=problem, kindness=kindness)


def reasonableness_gate(params: StoryParams) -> None:
    if params.problem not in PROBLEMS:
        pass
    if params.path not in PATHS:
        pass
    if params.path == "river_road" and params.problem not in {"broken_step", "river_wind"}:
        pass
    if params.path == "hill_steps" and params.problem not in {"broken_step", "fog_gate"}:
        pass
    if params.path == "sun_bridge" and params.problem not in {"river_wind", "fog_gate"}:
        pass


def tell(params: StoryParams) -> World:
    reasonableness_gate(params)
    world = World(params.setting)
    hero = world.add(Entity(id=params.hero, kind="character", type="runner", label=params.hero, title="runner", role="hero"))
    helper = world.add(Entity(id=params.helper, kind="character", type="guide", label=params.helper, title="guide", role="helper"))
    rival = world.add(Entity(id=params.rival, kind="character", type="rival", label=params.rival, title="rival", role="rival"))
    item = world.add(Entity(id=params.item, kind="thing", type="item", label=_safe_lookup(ITEMS, params.item).label, attrs={"phrase": _safe_lookup(ITEMS, params.item).phrase}))
    path = _safe_lookup(PATHS, params.path)
    problem = _safe_lookup(PROBLEMS, params.problem)
    kind = _safe_lookup(KINDNESS, params.kindness)

    for ent in (hero, helper, rival, item):
        ent.meters.setdefault("path_progress", 0.0)
        ent.meters.setdefault("damage", 0.0)
        ent.memes.setdefault("joy", 0.0)
        ent.memes.setdefault("conflict", 0.0)
        ent.memes.setdefault("kindness", 0.0)
        ent.memes.setdefault("resolve", 0.0)
    world.facts["path"] = path
    world.facts["problem"] = problem
    world.facts["kind"] = kind

    world.say(f"At {_safe_lookup(SETTINGS, params.setting)}, {hero.id} and {helper.id} were sworn to carry {item.attrs['phrase']} along the relay.")
    world.say(f"Their task was old as song: pass the light from hand to hand until it reached the last shrine.")
    world.para()
    hero.meters["path_progress"] += 1
    helper.meters["kindness"] += 1
    world.say(f"But {problem.issue}, and {rival.id} spoke sharply, making a conflict rise like smoke.")
    hero.memes["conflict"] += 1
    helper.memes["conflict"] += 1
    rival.memes["conflict"] += 1

    world.para()
    helper.memes["kindness"] += 1
    helper.memes["resolve"] += 1
    world.say(f"Then {helper.id} {kind.phrase}, because kindness can cool a quarrel faster than a winter spring.")
    world.say(f"{helper.id} saw {problem.fix_hint}.")

    if params.problem == "broken_step":
        hero.meters["path_progress"] += 1
        helper.meters["path_progress"] += 1
    elif params.problem == "river_wind":
        item.meters["shielded"] = 1
    else:
        helper.meters["path_progress"] += 1
        hero.meters["path_progress"] += 1

    hero.memes["conflict"] = max(0.0, hero.memes["conflict"] - 1)
    helper.memes["conflict"] = max(0.0, helper.memes["conflict"] - 1)
    rival.memes["conflict"] = max(0.0, rival.memes["conflict"] - 1)
    hero.memes["kindness"] += 1
    helper.memes["kindness"] += 1

    world.para()
    world.say(f"They solved it together: the relay bent around the trouble instead of striking it head-on.")
    world.say(f"The {item.label} went from {hero.id} to {helper.id} to {rival.id}, bright and steady.")
    world.say(f"By moonrise, the light reached the shrine, and the people knew the path had been mended by kindness and clear thinking.")

    world.facts.update(hero=hero, helper=helper, rival=rival, item=item, params=params, path=path, problem=problem)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p: StoryParams = f["params"]
    return [
        f'Write a short myth for a child about a relay at {_safe_lookup(SETTINGS, p.setting)} where {p.hero}, {p.helper}, and {p.rival} must carry {_safe_lookup(ITEMS, p.item).phrase} through {_safe_lookup(PROBLEMS, p.problem).issue}.',
        f'Write a mythic story where kindness changes a conflict during a relay, and the helpers find a way around {_safe_lookup(PROBLEMS, p.problem).label}.',
        f'Write a simple legend about {p.hero} and friends solving a relay problem with gentle words and good ideas.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    p: StoryParams = f["params"]
    path: Path = f["path"]
    problem: Problem = f["problem"]
    kind: KindAction = f["kind"]
    return [
        QAItem(
            question=f"Who carried the relay in the story?",
            answer=f"{p.hero}, {p.helper}, and {p.rival} carried it together, passing {_safe_lookup(ITEMS, p.item).label} along the sacred path.",
        ),
        QAItem(
            question=f"What problem blocked the relay?",
            answer=f"{problem.issue}. That trouble made the path hard until they thought carefully about a better way.",
        ),
        QAItem(
            question=f"How did kindness help?",
            answer=f"{p.helper} {kind.phrase}, and that calmed the conflict so the group could work together instead of arguing.",
        ),
        QAItem(
            question=f"What did they do to solve the problem?",
            answer=f"They used {problem.fix_hint} and kept the relay moving around the danger. That is how the journey stayed on course.",
        ),
        QAItem(
            question=f"Where did the relay end?",
            answer=f"It ended at {path.place}, where the light reached the shrine before moonrise.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a relay?",
            answer="A relay is a shared task where one helper passes something to the next helper so the journey can continue.",
        ),
        QAItem(
            question="What does kindness do in a quarrel?",
            answer="Kindness softens angry feelings, helps people listen, and makes it easier to solve a hard problem together.",
        ),
        QAItem(
            question="What is problem solving?",
            answer="Problem solving means noticing what is in the way and finding a smart, safe way around it.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions -- answerable from the story text ==")
    for qa in sample.story_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for qa in sample.world_qa:
        lines.append(f"Q: {qa.question}")
        lines.append(f"A: {qa.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"  {e.id}: meters={dict(e.meters)} memes={dict(e.memes)} attrs={dict(e.attrs)}")
    return "\n".join(out)


CURATED = [
    StoryParams(setting="river_shrine", hero="Ari", helper="Mara", rival="Niko", item="lantern", path="river_road", problem="broken_step", kindness="gentle_words"),
    StoryParams(setting="hill_shrine", hero="Lena", helper="Tavi", rival="Ivo", item="torch", path="hill_steps", problem="fog_gate", kindness="steady_hand"),
    StoryParams(setting="sun_bridge", hero="Kira", helper="Niko", rival="Suri", item="lantern", path="sun_bridge", problem="river_wind", kindness="shared_turn"),
]


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between Python and ASP gates.")
        print("python only:", sorted(py - cl))
        print("asp only:", sorted(cl - py))
        return 1
    smoke = generate(resolve_params(argparse.Namespace(setting=None, path=None, item=None, problem=None, kindness=None, hero=None, helper=None, rival=None), random.Random(7)))
    if not smoke.story.strip():
        print("Smoke test failed: empty story.")
        return 1
    print(f"OK: gate parity matches {len(py)} combos and smoke story generated.")
    return 0


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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "path", None) is None or c[1] == getattr(args, "path", None))
              and (getattr(args, "item", None) is None or c[2] == getattr(args, "item", None))
              and (getattr(args, "problem", None) is None or c[3] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, path, item, problem = rng.choice(list(combos))
    kindness = getattr(args, "kindness", None) or rng.choice(sorted(KINDNESS))
    hero = getattr(args, "hero", None) or rng.choice(GIVEN_NAMES)
    helper = getattr(args, "helper", None) or rng.choice([n for n in GIVEN_NAMES if n != hero])
    rival = getattr(args, "rival", None) or rng.choice([n for n in GIVEN_NAMES if n not in {hero, helper}])
    return StoryParams(setting=setting, hero=hero, helper=helper, rival=rival, item=item, path=path, problem=problem, kindness=kindness)


def valid_story_combo_count() -> int:
    return len(valid_combos())


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, path, item, problem) combos:\n")
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
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as e:
                print(e)
                return
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
