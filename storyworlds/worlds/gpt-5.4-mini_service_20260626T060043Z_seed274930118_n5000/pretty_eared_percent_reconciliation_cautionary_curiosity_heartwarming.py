#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pretty_eared_percent_reconciliation_cautionary_curiosity_heartwarming.py
======================================================================================

A tiny, self-contained storyworld about a crafty afternoon: two children make a
pretty eared bunny mask, learn a cautionary lesson about careful tools, and
reconcile after a hurt feeling. The seed words appear as part of the world's
core objects and narration: pretty, eared, percent.

The simulation is intentionally small:
- a child wants to finish a craft
- a shared mask gets damaged
- curiosity about "how much is left" is measured in percent
- a cautionary reminder about scissors and glue helps them fix the problem
- reconciliation ends the story on a warm image

The world model tracks physical meters and emotional memes, and the prose is
driven by state changes rather than a frozen template.
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

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0



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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    project: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "grandmother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "grandfather", "man"}:
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
class Setting:
    place: str
    indoors: bool = True
    affords: set[str] = field(default_factory=set)
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
        return None


@dataclass
class Project:
    id: str
    label: str
    phrase: str
    completion_noun: str
    risk: str
    mess: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
    fix_label: str
    caution: str
    helps: set[str] = field(default_factory=set)
    safe: bool = True
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
class StoryParams:
    setting: str
    project: str
    tool: str
    name: str
    helper: str
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


SETTINGS = {
    "sunroom": Setting(place="the sunroom", indoors=True, affords={"craft"}),
    "kitchen": Setting(place="the kitchen table", indoors=True, affords={"craft"}),
    "playroom": Setting(place="the playroom", indoors=True, affords={"craft"}),
}

PROJECTS = {
    "bunny_mask": Project(
        id="bunny_mask",
        label="bunny mask",
        phrase="a pretty eared bunny mask",
        completion_noun="percent",
        risk="crinkled",
        mess="torn",
        keyword="eared",
        tags={"pretty", "eared", "percent", "mask"},
    ),
    "sticker_chart": Project(
        id="sticker_chart",
        label="sticker chart",
        phrase="a pretty chart with eared bunny stickers",
        completion_noun="percent",
        risk="scuffed",
        mess="creased",
        keyword="percent",
        tags={"pretty", "eared", "percent", "chart"},
    ),
}

TOOLS = {
    "tape": Tool(
        id="tape",
        label="a roll of tape",
        fix_label="tape",
        caution="be careful with the scissors before you peel the tape",
        helps={"torn", "creased"},
        safe=True,
    ),
    "glue": Tool(
        id="glue",
        label="a glue stick",
        fix_label="glue",
        caution="use just a little glue so the paper will not wrinkle",
        helps={"torn", "creased"},
        safe=True,
    ),
    "scissors": Tool(
        id="scissors",
        label="child-safe scissors",
        fix_label="scissors",
        caution="keep the scissors pointed down when walking",
        helps=set(),
        safe=False,
    ),
}

GIRL_NAMES = ["Maya", "Lina", "Nora", "Ella", "Zoey", "Ruby"]
BOY_NAMES = ["Theo", "Owen", "Finn", "Eli", "Milo", "Noah"]
HELPER_NAMES = ["Mom", "Dad", "Auntie", "Grandma"]


def project_needs_fix(project: Project) -> bool:
    return project.mess in {"torn", "creased", "crinkled", "scuffed"}


def select_tool(project: Project) -> Optional[Tool]:
    for tool in TOOLS.values():
        if project.mess in tool.helps:
            return tool
    return None


ASP_RULES = r"""
project_needs_fix(P) :- project(P), messy(P).
tool_helps(T, P) :- tool(T), project(P), messy(P), fixes(T, messy(P)).
compatible(P, T) :- project_needs_fix(P), tool_helps(T, P).
valid_story(S, P, T) :- setting(S), project(P), tool(T), compatible(P, T), affords(S, craft).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for act in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, act))
    for pid, proj in PROJECTS.items():
        lines.append(asp.fact("project", pid))
        lines.append(asp.fact("messy", pid, proj.mess))
        for tag in sorted(proj.tags):
            lines.append(asp.fact("tag", pid, tag))
    for tid, tool in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for m in sorted(tool.helps):
            lines.append(asp.fact("fixes", tid, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROJECTS:
            for t in TOOLS:
                if project_needs_fix(_safe_lookup(PROJECTS, p)) and _safe_lookup(PROJECTS, p).mess in _safe_lookup(TOOLS, t).helps:
                    combos.append((s, p, t))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A heartwarming craft storyworld with reconciliation, caution, and curiosity.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPER_NAMES)
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
    combos = valid_combos()
    if getattr(args, "setting", None) and getattr(args, "project", None) and getattr(args, "tool", None):
        if (getattr(args, "setting", None), getattr(args, "project", None), getattr(args, "tool", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    valid = [c for c in combos
             if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
             and (getattr(args, "project", None) is None or c[1] == getattr(args, "project", None))
             and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not valid:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, project, tool = rng.choice(sorted(valid))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES + BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    return StoryParams(setting=setting, project=project, tool=tool, name=name, helper=helper)


def _setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.setting))
    hero_type = "girl" if params.name in GIRL_NAMES else "boy"
    hero = world.add(Entity(id=params.name, kind="character", type=hero_type, label=params.name))
    helper_type = "mother" if params.helper == "Mom" else "father" if params.helper == "Dad" else "grandmother"
    helper = world.add(Entity(id=params.helper, kind="character", type=helper_type, label=params.helper))
    project = world.add(Entity(
        id="project",
        type="craft",
        label=_safe_lookup(PROJECTS, params.project).label,
        phrase=_safe_lookup(PROJECTS, params.project).phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))
    tool = world.add(Entity(
        id="tool",
        type="tool",
        label=_safe_lookup(TOOLS, params.tool).label,
        owner=helper.id,
    ))
    world.facts.update(hero=hero, helper=helper, project=project, tool=tool, params=params)
    return world


def _measure_percent(project: Entity) -> int:
    clean = max(0.0, 100.0 - project.meters.get("mess", 0.0) * 50.0 - project.meters.get("torn", 0.0) * 50.0)
    return int(max(0, min(100, clean)))


def _narrate_begin(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    project: Entity = _safe_fact(world, f, "project")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    world.say(
        f"{hero.id} was making {project.phrase} at {world.setting.place}. "
        f"It looked pretty, with little eared shapes that made the mask feel friendly."
    )
    world.say(
        f"{hero.id} loved it so much that {hero.pronoun('possessive')} hands kept smoothing the paper, "
        f"counting each piece like a tiny percent of a big happy picture."
    )
    world.say(
        f"{helper.id} sat nearby with {tool.label}, ready to help if the craft needed fixing."
    )


def _narrate_turn(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    project: Entity = _safe_fact(world, f, "project")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    project.meters["mess"] += 1
    hero.memes["curiosity"] += 1
    project.meters["torn"] += 1
    world.say(
        f"Then {hero.id} leaned too close, and one eared corner of the pretty mask tore."
    )
    world.say(
        f"{hero.id} stared at the rip and asked, \"What percent is left if one ear is torn?\""
    )
    world.say(
        f"{helper.id} answered gently that curious questions are good, but sharp tools and quick hands need caution."
    )
    world.say(
        f"Together they counted the pieces and found that most of the mask was still okay."
    )


def _narrate_reconciliation(world: World) -> None:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    project: Entity = _safe_fact(world, f, "project")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    hero.memes["hurt"] = max(hero.memes.get("hurt", 0.0), 1.0)
    helper.memes["worry"] = max(helper.memes.get("worry", 0.0), 1.0)
    if project.meters.get("torn", 0.0) >= THRESHOLD:
        project.meters["torn"] = 0.0
        project.meters["fixed"] = 1.0
        hero.memes["forgive"] = 1.0
        helper.memes["forgive"] = 1.0
        world.say(
            f"{helper.id} got the tape and said, \"We can fix it together.\""
        )
        world.say(
            f"{hero.id} nodded, and the little worry in {hero.pronoun('possessive')} chest softened."
        )
        world.say(
            f"They pressed the tear flat, careful and slow, until the pretty eared mask looked brave again."
        )
        world.say(
            f"By the end, {hero.id} and {helper.id} were smiling side by side, proud of the repair and kinder to each other."
        )


def tell(params: StoryParams) -> World:
    world = _setup_world(params)
    _narrate_begin(world)
    world.para()
    _narrate_turn(world)
    world.para()
    _narrate_reconciliation(world)
    world.facts["percent"] = _measure_percent(world.facts["project"])
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    project: Entity = _safe_fact(world, f, "project")
    return [
        f"Write a heartwarming story about {hero.id} making a pretty eared {project.label} and learning to be careful.",
        f"Tell a gentle children's story where {hero.id} asks what percent of the craft is left after a mishap.",
        f"Write a small reconciliation story in which {helper.id} helps {hero.id} fix a torn paper mask.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    project: Entity = _safe_fact(world, f, "project")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    percent = f.get("percent", 0)
    return [
        QAItem(
            question=f"What was {hero.id} making at {world.setting.place}?",
            answer=f"{hero.id} was making {project.phrase}, which looked pretty and had eared shapes.",
        ),
        QAItem(
            question=f"Why did {hero.id} ask about percent after the craft got torn?",
            answer=f"{hero.id} was curious about how much of the pretty eared mask was still usable after the tear.",
        ),
        QAItem(
            question=f"How did {helper.id} help {hero.id} fix the problem?",
            answer=f"{helper.id} helped with {tool.label} and careful hands, so they could repair the mask together.",
        ),
        QAItem(
            question=f"What happened after they repaired the craft?",
            answer=f"They reconciled, felt happier, and the mask was almost all the way done again, about {percent} percent whole.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    project: Entity = _safe_fact(world, f, "project")
    tool: Entity = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question="What does percent mean?",
            answer="Percent means how many parts out of 100 something has, like how much of a craft is finished.",
        ),
        QAItem(
            question="Why should children be careful with scissors?",
            answer="Scissors can cut paper and also fingers, so they should be used slowly and with adult help.",
        ),
        QAItem(
            question="Why is it nice to fix something together?",
            answer="Working together can turn a problem into a shared success and help people feel close again.",
        ),
    ] + [
        QAItem(
            question=f"What kind of thing is {project.label}?",
            answer=f"It is a craft project that can be decorated, torn, and repaired.",
        ),
        QAItem(
            question=f"What is {tool.label} for?",
            answer=f"It is for sticking paper together when a small tear needs a gentle fix.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts -- asks that would produce this story =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions -- answerable from the story text ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions -- child level, no story needed ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


CURATED = [
    StoryParams(setting="sunroom", project="bunny_mask", tool="tape", name="Maya", helper="Mom"),
    StoryParams(setting="kitchen", project="bunny_mask", tool="glue", name="Theo", helper="Dad"),
    StoryParams(setting="playroom", project="sticker_chart", tool="tape", name="Lina", helper="Grandma"),
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


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        stories = asp_valid_combos()
        print(f"{len(stories)} compatible stories:\n")
        for s in stories:
            print("  ", s)
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.project} with {p.tool} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
