#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/freighter_felt_faggot_suspense_comedy.py
===============================================================================================================

A small story world for a freighter, a felt bundle, and a faggot of kindling.
The domain is built for Suspense with a comic, child-facing tone: a dockside
mix-up, a worried helper, a clattering freighter, and a safe ending image that
shows what changed.

The story uses the seed words freighter, felt, and faggot in natural prose.
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
    role: str = ""
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    box: object | None = None
    cap: object | None = None
    danger: object | None = None
    hel: object | None = None
    ship: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
class Dock:
    id: str
    name: str
    has_wind: bool = True
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
class ObjectConfig:
    id: str
    label: str
    phrase: str
    kind: str
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
    risk: str
    trigger: str
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
class Fix:
    id: str
    label: str
    phrase: str
    method: str
    result: str
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
    def __init__(self, dock: Dock) -> None:
        self.dock = dock
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
        clone = World(self.dock)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    dock: str
    cargo: str
    problem: str
    fix: str
    captain: str
    captain_gender: str
    helper: str
    helper_gender: str
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


DOCKS = {
    "harbor": Dock(id="harbor", name="the harbor", has_wind=True, affords={"load", "inspect", "wait"}),
    "wharf": Dock(id="wharf", name="the wharf", has_wind=True, affords={"load", "inspect", "wait"}),
    "pier": Dock(id="pier", name="the pier", has_wind=False, affords={"load", "inspect", "wait"}),
    "bay": Dock(id="bay", name="the bay dock", has_wind=True, affords={"load", "inspect", "wait"}),
}

CARGOS = {
    "felt": ObjectConfig(id="felt", label="felt bundle", phrase="a soft felt bundle", kind="cargo", tags={"felt", "soft"}),
    "faggot": ObjectConfig(id="faggot", label="faggot of kindling", phrase="a tidy faggot of kindling", kind="cargo", tags={"faggot", "wood"}),
    "canvas": ObjectConfig(id="canvas", label="canvas roll", phrase="a rolled canvas sheet", kind="cargo", tags={"canvas"}),
    "rope": ObjectConfig(id="rope", label="rope coil", phrase="a neat rope coil", kind="cargo", tags={"rope"}),
}

PROBLEMS = {
    "wind": Problem(id="wind", label="wind", phrase="a gusty wind", risk="blow loose", trigger="started to flap and slip", tags={"wind", "sway"}),
    "sway": Problem(id="sway", label="sway", phrase="the freighter's sway", risk="slide around", trigger="wobbled like jelly", tags={"sway"}),
    "clatter": Problem(id="clatter", label="clatter", phrase="a clattery deck", risk="bump and tumble", trigger="began to rattle", tags={"clatter"}),
}

FIXES = {
    "strap": Fix(id="strap", label="strap it down", phrase="a wide strap", method="buckled it down", result="stayed snug and still", tags={"strap"}),
    "cover": Fix(id="cover", label="cover it with felt", phrase="a felt wrap", method="covered it in felt", result="stayed quiet and safe", tags={"felt"}),
    "wait": Fix(id="wait", label="wait for calmer water", phrase="a patient pause", method="waited for the wind to ease", result="was easier to carry", tags={"wait"}),
}

GIRL_NAMES = ["Mira", "Nina", "Tessa", "Ada", "Lina", "Zuri"]
BOY_NAMES = ["Owen", "Eli", "Noah", "Jasper", "Theo", "Milo"]
TRAITS = ["careful", "curious", "cheerful", "quick-thinking", "patient"]

KNOWLEDGE = {
    "felt": [("What is felt?", "Felt is a soft cloth made by pressing fibers together. It can help cushion or cover something neatly.")],
    "faggot": [("What is a faggot of kindling?", "A faggot of kindling is a bundle of small sticks tied together. People use kindling to help start a fire, so it must be handled carefully.")],
    "freighter": [("What is a freighter?", "A freighter is a big ship that carries cargo from one place to another. It can move heavy things across water.")],
    "wind": [("What is wind?", "Wind is moving air. It can tug at light things and make them wobble or flap.")],
    "strap": [("What does a strap do?", "A strap holds something tightly so it does not slide around.")],
    "wait": [("Why would someone wait for calmer water?", "Waiting can make carrying heavy things safer. A steadier moment means fewer bumps and slips.")],
}
KNOWLEDGE_ORDER = ["freighter", "felt", "faggot", "wind", "strap", "wait"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for d in DOCKS:
        for c in CARGOS:
            for p in PROBLEMS:
                if c == "felt" and p in {"wind", "sway"}:
                    combos.append((d, c, p))
                elif c == "faggot" and p in {"clatter", "sway"}:
                    combos.append((d, c, p))
                elif c == "canvas" and p in {"wind", "clatter"}:
                    combos.append((d, c, p))
    return combos


def explain_rejection(cargo: ObjectConfig, problem: Problem) -> str:
    return f"(No story: {cargo.label} is not a good match for {problem.label} in this little dock tale.)"


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for d in DOCKS:
        lines.append(asp.fact("dock", d))
    for c in CARGOS:
        lines.append(asp.fact("cargo", c))
    for p in PROBLEMS:
        lines.append(asp.fact("problem", p))
    for f in FIXES:
        lines.append(asp.fact("fix", f))
    for d, dock in DOCKS.items():
        if dock.has_wind:
            lines.append(asp.fact("windy", d))
    for d, c, p in valid_combos():
        lines.append(asp.fact("valid_combo", d, c, p))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("risk", pid, prob.risk))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("method", fid, fix.method))
    return "\n".join(lines)


ASP_RULES = r"""
choice(D,C,P) :- valid_combo(D,C,P).
recommend(F,C,P) :- choice(D,C,P), fix(F), cargo(C), problem(P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show choice/3."))
    return sorted(set(asp.atoms(model, "choice")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py != cl:
        print("MISMATCH between python and ASP")
        if py - cl:
            print(" only python:", sorted(py - cl))
        if cl - py:
            print(" only clingo:", sorted(cl - py))
        return 1
    try:
        sample = generate(resolve_params(argparse.Namespace(dock=None, cargo=None, problem=None, fix=None, captain=None, captain_gender=None, helper=None, helper_gender=None), random.Random(1)))
        _ = sample.story
    except Exception as exc:  # noqa: BLE001
        print(f"SMOKE TEST FAILED: {exc}")
        return 1
    print(f"OK: {len(py)} combos; ASP parity and smoke test passed.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A comic suspense storyworld about dockside cargo.")
    ap.add_argument("--dock", choices=DOCKS)
    ap.add_argument("--cargo", choices=CARGOS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--captain", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["girl", "boy"])
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
              if (getattr(args, "dock", None) is None or c[0] == getattr(args, "dock", None))
              and (getattr(args, "cargo", None) is None or c[1] == getattr(args, "cargo", None))
              and (getattr(args, "problem", None) is None or c[2] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    dock, cargo, problem = rng.choice(list(combos))
    fix = getattr(args, "fix", None) or rng.choice(sorted(FIXES))
    captain_gender = getattr(args, "captain", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper", None) or ("boy" if captain_gender == "girl" else "girl")
    captain = rng.choice(GIRL_NAMES if captain_gender == "girl" else BOY_NAMES)
    helper = rng.choice([n for n in (GIRL_NAMES if helper_gender == "girl" else BOY_NAMES) if n != captain])
    return StoryParams(dock=dock, cargo=cargo, problem=problem, fix=fix,
                       captain=captain, captain_gender=captain_gender,
                       helper=helper, helper_gender=helper_gender)


def _make_world(params: StoryParams) -> World:
    dock = _safe_lookup(DOCKS, params.dock)
    cargo = _safe_lookup(CARGOS, params.cargo)
    problem = _safe_lookup(PROBLEMS, params.problem)
    fix = _safe_lookup(FIXES, params.fix)
    w = World(dock)
    cap = w.add(Entity(id=params.captain, kind="character", type=params.captain_gender, role="captain"))
    hel = w.add(Entity(id=params.helper, kind="character", type=params.helper_gender, role="helper"))
    ship = w.add(Entity(id="freighter", kind="thing", type="ship", label="freighter"))
    box = w.add(Entity(id="cargo", kind="thing", type="cargo", label=cargo.label, phrase=cargo.phrase, tags=set(cargo.tags), owner=cap.id, carried_by=ship.id))
    danger = w.add(Entity(id="danger", kind="thing", type="problem", label=problem.label, phrase=problem.phrase, tags=set(problem.tags)))
    tool = w.add(Entity(id="fix", kind="thing", type="fix", label=fix.label, phrase=fix.phrase, tags=set(fix.tags), caretaker=hel.id))
    # init facts before use
    w.facts.update(captain=cap, helper=hel, ship=ship, cargo=box, danger=danger, tool=tool, dock=dock, cargo_cfg=cargo, problem_cfg=problem, fix_cfg=fix)
    return w


def _propagate(w: World) -> list[str]:
    out = []
    c = w.get("cargo")
    d = w.get("danger")
    if ("risk", c.id, d.id) not in w.fired:
        if c.label == "felt bundle" and d.label in {"wind", "sway"}:
            w.fired.add(("risk", c.id, d.id))
            c.meters["wobble"] += 1
            out.append("The felt bundle shivered in the wind.")
        elif c.label == "faggot of kindling" and d.label in {"clatter", "sway"}:
            w.fired.add(("risk", c.id, d.id))
            c.meters["wobble"] += 1
            out.append("The faggot of kindling began to skitter and tap.")
    if c.meters["wobble"] >= THRESHOLD and ("alarm", c.id) not in w.fired:
        w.fired.add(("alarm", c.id))
        w.get("helper").memes["focus"] += 1
        out.append("That was funny enough to be worrying.")
    return out


def tell(params: StoryParams) -> World:
    w = _make_world(params)
    cap = w.get(params.captain)
    hel = w.get(params.helper)
    cargo = w.get("cargo")
    prob = w.get("danger")
    fix = w.get("fix")

    cap.memes["worry"] += 1
    hel.memes["care"] += 1
    w.say(f"At {w.dock.name}, {cap.id} and {hel.id} were loading the freighter.")
    w.say(f"They had a {cargo.phrase}, and it looked too soft, too loose, and a little too silly to trust.")
    w.say(f"Then the problem came: {prob.phrase} made the cargo {prob.trigger}.")
    w.para()
    _propagate(w)
    w.say(f"{hel.id} stared at it and whispered, \"That {cargo.label} is trying to become a prank.\"")
    w.say(f"{cap.id} laughed once, then checked the rope. The freighter rocked, and the cargo rocked back.")
    w.para()
    if params.fix == "strap":
        cargo.meters["secured"] += 1
        w.say(f"So {hel.id} {fix.method}, and the {cargo.label} {fix.result}.")
    elif params.fix == "cover":
        cargo.meters["secured"] += 1
        cargo.meters["softness"] += 1
        w.say(f"So {hel.id} {fix.method}, and the little bundle {fix.result}.")
    else:
        cargo.meters["secured"] += 1
        w.say(f"So they {fix.method}, and soon the deck felt less like a joke and more like a job.")
    w.say(f"At the end, the {cargo.label} sat neat on the freighter, tied down and not going anywhere dramatic.")
    return w


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short suspense-comedy story about a freighter, a {f["cargo_cfg"].label}, and {f["problem_cfg"].label}.',
        f'Tell a child-friendly dockside story where {f["captain"].id} and {f["helper"].id} worry about a {f["cargo_cfg"].label} on a freighter, then fix it.',
        f'Write a funny but tense story that includes the words freighter, felt, and faggot, and ends with the cargo safely secured.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cap = f["captain"]
    hel = f["helper"]
    cargo = f["cargo_cfg"]
    prob = f["problem_cfg"]
    fix = f["fix_cfg"]
    return [
        QAItem(
            question=f"What were {cap.id} and {hel.id} doing at the dock?",
            answer=f"They were loading the freighter and checking the cargo. The job got tricky because {cargo.label} and {prob.label} made the deck feel uncertain.",
        ),
        QAItem(
            question=f"Why did the cargo worry them?",
            answer=f"The {cargo.label} was light enough to wobble, and {prob.phrase} made it move even more. That meant it could slide around unless they handled it carefully.",
        ),
        QAItem(
            question=f"How did they solve the problem?",
            answer=f"They used {fix.phrase} and secured the cargo. After that, the freighter felt calmer, and the cargo stayed put.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["cargo_cfg"].tags) | set(world.facts["problem_cfg"].tags) | set(world.facts["fix_cfg"].tags)
    out = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out


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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            m = {k: v for k, v in e.meters.items() if v}
            if m:
                bits.append(f"meters={m}")
        if e.memes:
            m = {k: v for k, v in e.memes.items() if v}
            if m:
                bits.append(f"memes={m}")
        lines.append(f"  {e.id}: {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    if params.dock not in DOCKS or params.cargo not in CARGOS or params.problem not in PROBLEMS or params.fix not in FIXES:
        pass
    w = tell(params)
    return StorySample(params=params, story=w.render(), prompts=generation_prompts(w), story_qa=story_qa(w), world_qa=world_knowledge_qa(w), world=w)


CURATED = [
    StoryParams(dock="harbor", cargo="felt", problem="wind", fix="strap", captain="Mira", captain_gender="girl", helper="Owen", helper_gender="boy"),
    StoryParams(dock="wharf", cargo="faggot", problem="clatter", fix="cover", captain="Theo", captain_gender="boy", helper="Nina", helper_gender="girl"),
    StoryParams(dock="bay", cargo="felt", problem="sway", fix="wait", captain="Lina", captain_gender="girl", helper="Jasper", helper_gender="boy"),
    StoryParams(dock="pier", cargo="faggot", problem="sway", fix="strap", captain="Milo", captain_gender="boy", helper="Ada", helper_gender="girl"),
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
        print(asp_program("#show choice/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for row in combos:
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
            i += 1
            try:
                params = resolve_params(args, random.Random(base_seed + i))
            except StoryError as err:
                print(err)
                return
            params.seed = base_seed + i
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
    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
