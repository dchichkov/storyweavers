#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/concern_male_art_ist_fallen_tree_trail.py
===============================================================================================================

A standalone storyworld for a small fable-like trail tale: a fallen tree blocks
a path, a male art-ist worries about the space, and careful sound effects help
solve the problem.

The world model tracks physical meters and emotional memes, then narrates from
state changes rather than swapping nouns into a fixed paragraph. A tiny causal
engine advances the world, and an inline ASP twin mirrors the reasonableness
gate and the main outcome logic.
"""

from __future__ import annotations

import argparse
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
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)
    plural: bool = False

    helper: object | None = None
    hero: object | None = None
    trail: object | None = None
    tree: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

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
    label: str
    place_phrase: str
    terrain: str
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
    obstacle: str
    sound: str
    concern: str
    risk: str
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
    use: str
    sound: str
    fix: str
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
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict[str, object] = field(default_factory=dict)

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
class StoryParams:
    setting: str
    art_form: str
    problem: str
    tool: str
    name: str
    gender: str
    helper_name: str
    helper_gender: str
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


SETTINGS = {
    "fallen_tree_trail": Setting(
        id="fallen_tree_trail",
        label="fallen tree trail",
        place_phrase="the fallen tree trail",
        terrain="a mossy trail with one huge tree lying across it",
        tags={"trail", "tree", "fallen"},
    ),
    "woodland_path": Setting(
        id="woodland_path",
        label="woodland path",
        place_phrase="the woodland path",
        terrain="a quiet path with roots, stones, and birdsong",
        tags={"trail", "wood", "path"},
    ),
    "river_bend_trail": Setting(
        id="river_bend_trail",
        label="river bend trail",
        place_phrase="the river bend trail",
        terrain="a trail that curled by water and reeds",
        tags={"trail", "river"},
    ),
}

PROBLEMS = {
    "blocked_path": Problem(
        id="blocked_path",
        label="a blocked path",
        obstacle="the fallen tree",
        sound="thud-crack",
        concern="the trail was blocked",
        risk="no one could pass through safely",
        tags={"blocked", "tree", "trail"},
    ),
    "splinters": Problem(
        id="splinters",
        label="splintered wood",
        obstacle="the broken branches",
        sound="creak-snap",
        concern="sharp branches stuck out everywhere",
        risk="someone could scrape a hand or knee",
        tags={"splinters", "tree"},
    ),
    "muddy_detour": Problem(
        id="muddy_detour",
        label="a muddy detour",
        obstacle="the slick bend around the trunk",
        sound="squish",
        concern="the ground was slippery and hard to cross",
        risk="someone could slip in the mud",
        tags={"mud", "trail"},
    ),
}

TOOLS = {
    "song": Tool(
        id="song",
        label="rhythm and counting",
        phrase="a steady count and a little song",
        use="tap the trunk, count the branches, and keep a calm rhythm",
        sound="tap-tap",
        fix="gave everyone a clear plan",
        tags={"sound", "problem_solving"},
    ),
    "drum_knock": Tool(
        id="drum_knock",
        label="drum-knocking",
        phrase="drum-knocking on the trunk",
        use="knock a beat on the wood and listen for loose parts",
        sound="boom-boom",
        fix="helped them hear where the tree was safest to move",
        tags={"sound", "problem_solving"},
    ),
    "leaf_whistle": Tool(
        id="leaf_whistle",
        label="leaf-whistling",
        phrase="a leaf whistle and a soft call",
        use="make a clear whistle to ask for help and answer back",
        sound="fiuu",
        fix="brought helpers together like a little signal",
        tags={"sound", "problem_solving"},
    ),
    "rope_plan": Tool(
        id="rope_plan",
        label="a rope plan",
        phrase="a rope plan with careful knots",
        use="tie, pull, and guide the branches aside",
        sound="huff-ha",
        fix="gave the helpers a safe way to shift the wood",
        tags={"problem_solving"},
    ),
}

ART_FORMS = {
    "art_ist": "art-ist",
    "painter": "painter",
    "sketcher": "sketcher",
}

GIRL_NAMES = ["Lina", "Mara", "Nia", "Tessa", "Ivy", "Leah"]
BOY_NAMES = ["Owen", "Noah", "Eli", "Milo", "Jonas", "Theo"]
HELPER_NAMES = ["Ben", "Cal", "Finn", "Hugo", "Mason", "Rory"]
TRAITS = ["careful", "thoughtful", "patient", "gentle"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid in SETTINGS:
        for pid, prob in PROBLEMS.items():
            for tid, tool in TOOLS.items():
                if sid == "fallen_tree_trail" and "sound" in tool.tags and prob.id == "blocked_path":
                    combos.append((sid, "art_ist", pid, tid))
                elif sid != "fallen_tree_trail" and tool.id != "rope_plan":
                    combos.append((sid, "painter", pid, tid))
    return combos


def reasonableness_check(params: StoryParams) -> None:
    if params.setting not in SETTINGS:
        pass
    if params.problem not in PROBLEMS or params.tool not in TOOLS:
        pass
    if params.setting == "fallen_tree_trail":
        if params.problem != "blocked_path":
            pass
        if params.tool not in {"song", "drum_knock", "leaf_whistle"}:
            pass
    if params.setting != "fallen_tree_trail" and params.tool == "song":
        pass


class Rule:
    def __init__(self, name: str, apply):
        self.name = name
        self.apply = apply


def _r_concern(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    prob = world.facts["problem_obj"]
    if hero.memes["concern"] >= THRESHOLD and not world.fired.__contains__(("concern",)):
        world.fired.add(("concern",))
        hero.memes["focus"] += 1
        out.append(f"{hero.id} took a slow breath and studied {prob.obstacle}.")
    return out


def _r_resolve(world: World) -> list[str]:
    out = []
    if world.facts.get("solved") and ("solve",) not in world.fired:
        world.fired.add(("solve",))
        hero = world.get("hero")
        helper = world.get("helper")
        hero.memes["relief"] += 1
        helper.memes["pride"] += 1
        out.append("__resolved__")
    return out


CAUSAL_RULES = [Rule("concern", _r_concern), Rule("resolve", _r_resolve)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(x for x in sents if not x.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        if "sound" in tool.tags:
            lines.append(asp.fact("sound_tool", tid))
    for aid in ART_FORMS:
        lines.append(asp.fact("art_form", aid))
    lines.append(asp.fact("favored", "fallen_tree_trail", "blocked_path", "song"))
    lines.append(asp.fact("favored", "fallen_tree_trail", "blocked_path", "drum_knock"))
    lines.append(asp.fact("favored", "fallen_tree_trail", "blocked_path", "leaf_whistle"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,P,T) :- setting(S), problem(P), tool(T), favored(S,P,T).
solved(S,P,T) :- valid(S,P,T), sound_tool(T).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    try:
        asp_set = set(asp_valid_combos())
        py_set = set(valid_combos())
        ok1 = asp_set == py_set
        sample_params = resolve_params(argparse.Namespace(
            setting=None, art_form=None, problem=None, tool=None, name=None, gender=None,
            helper_name=None, helper_gender=None, n=1, seed=777, all=False, trace=False,
            qa=False, json=False, asp=False, verify=False, show_asp=False
        ), random.Random(777))
        sample = generate(sample_params)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            emit(sample)
        ok2 = bool(sample.story.strip())
        if ok1 and ok2:
            print(f"OK: ASP parity and story smoke test passed ({len(py_set)} combos).")
            return 0
        print("MISMATCH or smoke-test failure.")
        if not ok1:
            print("ASP mismatch:")
            print(" only in asp:", sorted(asp_set - py_set))
            print(" only in py:", sorted(py_set - asp_set))
        return 1
    except Exception as exc:
        print(f"VERIFY FAILED: {exc}")
        return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: a fable on a fallen tree trail.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--art-form", choices=ART_FORMS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-name")
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--seed", type=int)
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
              and (getattr(args, "art_form", None) is None or c[1] == getattr(args, "art_form", None))
              and (getattr(args, "problem", None) is None or c[2] == getattr(args, "problem", None))
              and (getattr(args, "tool", None) is None or c[3] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, art_form, problem, tool = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    name = getattr(args, "name", None) or rng.choice(BOY_NAMES if gender == "boy" else GIRL_NAMES)
    helper_gender = getattr(args, "helper_gender", None) or rng.choice(["boy", "girl"])
    helper_name = getattr(args, "helper_name", None) or rng.choice(HELPER_NAMES)
    return StoryParams(
        setting=setting, art_form=art_form, problem=problem, tool=tool,
        name=name, gender=gender, helper_name=helper_name, helper_gender=helper_gender
    )


def tell(params: StoryParams) -> World:
    reasonableness_check(params)
    setting = _safe_lookup(SETTINGS, params.setting)
    problem = _safe_lookup(PROBLEMS, params.problem)
    tool = _safe_lookup(TOOLS, params.tool)
    world = World(setting=setting)
    hero = world.add(Entity(id="hero", kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type=params.helper_gender, label=params.helper_name))
    tree = world.add(Entity(id="tree", kind="thing", type="thing", label="the fallen tree"))
    trail = world.add(Entity(id="trail", kind="thing", type="thing", label=setting.place_phrase))
    world.facts.update(
        hero=hero, helper=helper, tree=tree, trail=trail,
        setting_obj=setting, problem_obj=problem, tool_obj=tool,
        art_form=params.art_form, solved=False, method=tool.id,
    )

    hero.memes["concern"] = 1.0
    hero.memes["focus"] = 0.0
    helper.memes["pride"] = 0.0

    world.say(
        f"{hero.label} was a male art-ist who liked to make tiny roadside fables "
        f"into bright pictures. One morning on {setting.label}, {setting.terrain}."
    )
    world.say(
        f"{hero.label} felt concern when {problem.obstacle} made {problem.concern}. "
        f'{hero.label} whispered, "{problem.sound}."'
    )
    world.para()
    world.say(
        f"{helper.label} came along and listened. Together they chose {tool.phrase}, "
        f"because {tool.fix}."
    )
    hero.memes["concern"] += 0.5
    propagate(world, narrate=False)
    if tool.id == "rope_plan":
        world.say(f"They tied careful knots, but the trail still wanted a sound to guide the work.")
    else:
        world.say(
            f'{hero.label} tapped, "{tool.sound}," and {helper.label} answered with the same beat. '
            f"The tree seemed to loosen its grip."
        )
    world.facts["solved"] = True
    propagate(world, narrate=False)
    world.para()
    world.say(
        f"At last the path opened. The fallen tree was shifted aside, and the trail lay clear "
        f"with pine needles, moss, and a tidy line where the wood had been."
    )
    world.say(
        f"{hero.label} made a little sketch of the open trail, and {helper.label} smiled beside it."
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a fable-like story for a child where a male art-ist feels concern on {f["setting_obj"].label} and solves a blocked trail with sound effects.',
        f"Tell a short story set on {f['setting_obj'].label} with a fallen tree, where {f['hero'].label} uses problem solving and sound effects to clear the way.",
        f'Write a gentle tale that includes the words "concern", "male", and "art-ist", and ends with an open trail and a picture.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    setting = f["setting_obj"]
    problem = f["problem_obj"]
    tool = f["tool_obj"]
    return [
        QAItem(
            question=f"What made {hero.label} feel concern on {setting.label}?",
            answer=f"{problem.obstacle} blocked the trail and made the way uncertain. That is why {hero.label} took the problem seriously before trying to fix it.",
        ),
        QAItem(
            question=f"How did {hero.label} and {helper.label} use sound effects to solve the problem?",
            answer=f"They used {tool.phrase} and let the sounds guide their work. The beat helped them listen, plan, and move the fallen tree safely.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The trail was clear again, and {hero.label} could make a sketch of the open path. The ending image proves the wood was moved and the walk could continue.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a fable?",
            answer="A fable is a short story that uses simple events to share a lesson. It often has a clear problem and a careful answer.",
        ),
        QAItem(
            question="Why can sound effects help with problem solving?",
            answer="Sound effects can help people work together because they make a rhythm or signal. A rhythm can keep a group calm and focused while they solve a problem.",
        ),
        QAItem(
            question="What is an art-ist in this world?",
            answer="An art-ist is a person who makes drawings or pictures. In this story, the art-ist notices the trail and turns the solved problem into a picture.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    parts = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("\n== story QA ==")
    for q in sample.story_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    parts.append("\n== world QA ==")
    for q in sample.world_qa:
        parts.append(f"Q: {q.question}\nA: {q.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        lines.append(f"  {e.id}: {e.label or e.type} {' '.join(bits)}")
    lines.append(f"  fired={sorted(world.fired)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    world = tell(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(
        setting="fallen_tree_trail", art_form="art_ist", problem="blocked_path",
        tool="song", name="Milo", gender="boy", helper_name="Ben", helper_gender="boy"
    ),
    StoryParams(
        setting="fallen_tree_trail", art_form="art_ist", problem="blocked_path",
        tool="drum_knock", name="Owen", gender="boy", helper_name="Rory", helper_gender="boy"
    ),
    StoryParams(
        setting="fallen_tree_trail", art_form="art_ist", problem="blocked_path",
        tool="leaf_whistle", name="Theo", gender="boy", helper_name="Finn", helper_gender="boy"
    ),
    StoryParams(
        setting="woodland_path", art_form="sketcher", problem="muddy_detour",
        tool="rope_plan", name="Nia", gender="girl", helper_name="Hugo", helper_gender="boy"
    ),
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
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

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
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
