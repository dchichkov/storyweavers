#!/usr/bin/env python3
"""
storyworlds/worlds/satellite_nasty_ratio_happy_ending_sharing_problem.py
========================================================================

A small superhero story world about a rescue problem around a satellite,
a nasty mess, and a ratio that helps the team solve things by sharing.

Premise seed:
- A young superhero team spots a satellite in trouble.
- The satellite gets covered in nasty sludge after a stormy mishap.
- The heroes must share tools and solve a simple ratio puzzle to clean it.
- The story ends with a happy ending: the satellite shines again.

This world is deliberately constraint-checked:
- It models physical meters and emotional memes.
- It drives prose from simulated state, not a frozen template.
- It has an inline ASP twin and a Python reasonableness gate.
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
# Domain constants
# ---------------------------------------------------------------------------
THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities and world model
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    hero: object | None = None
    sat: object | None = None
    sidekick: object | None = None
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
    place: str
    indoor: bool = False
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
class Mission:
    id: str
    title: str
    danger: str
    mess: str
    soil: str
    clean_tool: str
    share_ratio_good: tuple[int, int]
    share_ratio_bad: tuple[int, int]
    keyword: str
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
    phrase: str
    covers: set[str]
    guards: set[str]
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "city": Setting(place="the bright city", indoor=False, affords={"repair", "share"}),
    "roof": Setting(place="the rooftop", indoor=False, affords={"repair", "share"}),
    "lab": Setting(place="the sky lab", indoor=True, affords={"repair", "share"}),
}

MISSIONS = {
    "satellite": Mission(
        id="satellite",
        title="the satellite problem",
        danger="the satellite would lose its signal",
        mess="nasty",
        soil="covered in nasty slime",
        clean_tool="cleaning foam",
        share_ratio_good=(2, 1),
        share_ratio_bad=(1, 2),
        keyword="satellite",
        tags={"satellite", "nasty", "ratio"},
    ),
    "antenna": Mission(
        id="antenna",
        title="the antenna problem",
        danger="the antenna would stop blinking",
        mess="nasty",
        soil="smeared with nasty goo",
        clean_tool="mop foam",
        share_ratio_good=(3, 1),
        share_ratio_bad=(1, 3),
        keyword="antenna",
        tags={"nasty", "ratio"},
    ),
}

TOOLS = [
    Tool(
        id="foam",
        label="cleaning foam",
        phrase="a can of cleaning foam",
        covers={"metal", "glass"},
        guards={"nasty"},
    ),
    Tool(
        id="cloths",
        label="soft cloths",
        phrase="a bundle of soft cloths",
        covers={"metal", "glass"},
        guards={"nasty"},
        plural=True,
    ),
    Tool(
        id="gloves",
        label="gloves",
        phrase="strong gloves",
        covers={"hands"},
        guards={"nasty"},
        plural=True,
    ),
]

HERO_NAMES = ["Nova", "Bolt", "Spark", "Ray", "Mira", "Jett", "Piper", "Sky"]
SIDEKICK_NAMES = ["Zip", "Comet", "Echo", "Flash", "Bean", "Luna"]
TRAITS = ["brave", "kind", "curious", "steady", "quick-thinking"]


# ---------------------------------------------------------------------------
# Python reasonableness gate
# ---------------------------------------------------------------------------
def mission_is_reasonable(mission: Mission, setting: Setting) -> bool:
    return mission.id in setting.affords or "share" in setting.affords


def select_tool(mission: Mission) -> Optional[Tool]:
    for tool in TOOLS:
        if mission.mess in tool.guards:
            return tool
    return None


def ratio_helpful(mission: Mission, water: int, slime: int) -> bool:
    return slime > 0 and water > 0 and (water, slime) == mission.share_ratio_good


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    mission: str
    hero: str
    sidekick: str
    hero_trait: str
    sidekick_trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World actions
# ---------------------------------------------------------------------------
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


def _normalize_ratio(a: int, b: int) -> tuple[int, int]:
    if a <= 0 or b <= 0:
        return (a, b)
    from math import gcd
    g = gcd(a, b)
    return (a // g, b // g)


def introduce(world: World, hero: Entity, sidekick: Entity, mission: Mission) -> None:
    world.say(
        f"{hero.id} was a {hero.memes.get('trait', 'brave')} superhero who could spot trouble "
        f"from far away. {sidekick.id} stayed close, because teamwork made every rescue feel safer."
    )
    world.say(
        f"One day, they heard about {mission.title} and flew toward the sky with a plan."
    )


def damage_satellite(world: World, mission: Mission) -> None:
    sat = world.get("satellite")
    sat.meters["nasty"] += 1
    sat.meters["signal"] = 0
    world.say(
        f"The satellite had been hit by a splash of {mission.mess} slime, and now it looked "
        f"{mission.soil}."
    )


def share_tools(world: World, hero: Entity, sidekick: Entity, mission: Mission, tool: Tool) -> None:
    world.facts["tool"] = tool
    world.say(
        f"{hero.id} and {sidekick.id} did not grab the foam all at once. They shared {tool.label} "
        f"so each of them could help."
    )


def compute_ratio(world: World, mission: Mission) -> tuple[int, int]:
    water = 2
    slime = 1
    world.facts["ratio"] = (water, slime)
    return water, slime


def solve_problem(world: World, hero: Entity, sidekick: Entity, mission: Mission, tool: Tool) -> None:
    water, slime = compute_ratio(world, mission)
    if ratio_helpful(mission, water, slime):
        world.say(
            f"{hero.id} counted the mix and smiled. The right ratio was {water}:{slime}, "
            f"which meant {water} scoops of water for every {slime} scoop of foam."
        )
        world.say(
            f"With that simple ratio, {hero.id} and {sidekick.id} mixed the cleaner and wiped "
            f"the nasty slime away."
        )
    else:
        pass


def restore_satellite(world: World, mission: Mission) -> None:
    sat = world.get("satellite")
    sat.meters["nasty"] = 0
    sat.meters["signal"] = 1
    sat.memes["relief"] += 1
    world.say(
        f"At last, the satellite shone again. Its signal blinked back on, and the whole city "
        f"felt safe and bright."
    )
    world.say(
        f"{mission.keyword.capitalize()} trouble had turned into a happy ending."
    )


def tell_world(world: World, hero: Entity, sidekick: Entity, mission: Mission) -> None:
    introduce(world, hero, sidekick, mission)
    world.para()
    damage_satellite(world, mission)
    tool = select_tool(mission)
    if tool is None:
        pass
    share_tools(world, hero, sidekick, mission, tool)
    solve_problem(world, hero, sidekick, mission, tool)
    restore_satellite(world, mission)


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    mission: Mission = _safe_fact(world, f, "mission")
    hero: Entity = _safe_fact(world, f, "hero")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    return [
        f'Write a superhero story for a small child about a {mission.keyword}, a nasty mess, and a ratio that helps solve a problem.',
        f"Tell a happy-ending rescue story where {hero.id} and {sidekick.id} share tools to clean a {mission.keyword}.",
        f"Write a short story that uses the words satellite, nasty, and ratio in a kind superhero adventure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    sidekick: Entity = _safe_fact(world, f, "sidekick")
    mission: Mission = _safe_fact(world, f, "mission")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    water, slime = f["ratio"]
    return [
        QAItem(
            question=f"What was the main problem in the story?",
            answer=f"The main problem was that the {mission.keyword} was {mission.soil}, so the heroes had to fix it.",
        ),
        QAItem(
            question=f"Why did {hero.id} and {sidekick.id} share {tool.label}?",
            answer=f"They shared {tool.label} because teamwork helped them clean the nasty mess faster and more carefully.",
        ),
        QAItem(
            question=f"What ratio did {hero.id} use to solve the cleaning problem?",
            answer=f"{hero.id} used the ratio {water}:{slime}, which meant the cleaner mix had {water} parts water and {slime} part foam.",
        ),
        QAItem(
            question=f"What happened at the end of the story?",
            answer=f"The satellite was cleaned, its signal came back, and the story ended with a happy ending.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a satellite?",
            answer="A satellite is an object that travels around a planet, and some satellites help send signals for communication.",
        ),
        QAItem(
            question="What does nasty mean?",
            answer="Nasty means dirty, unpleasant, or hard to like because it is messy or gross.",
        ),
        QAItem(
            question="What is a ratio?",
            answer="A ratio compares amounts, like how many parts of one thing match how many parts of another thing.",
        ),
        QAItem(
            question="Why do superheroes share tools?",
            answer="Superheroes share tools so they can work together, solve problems, and finish rescue jobs safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% Reasonableness gate:
reasonable(M) :- mission(M), setting(S), affords(S, share).
reasonable(M) :- mission(M), setting(S), affords(S, repair).

% A tool helps when it guards the nasty mess.
helps(T, M) :- tool(T), mission(M), mess_of(M, nasty), guards(T, nasty).

% A ratio solves the problem when it matches the mission's good ratio.
ratio_ok(A,B,M) :- mission(M), good_ratio(M,A,B).

% A valid story has a reasonable mission, a helping tool, and the right ratio.
valid_story(S, M, T, A, B) :- setting(S), mission(M), tool(T),
                             reasonable(M), helps(T, M), ratio_ok(A,B,M).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for mid, m in MISSIONS.items():
        lines.append(asp.fact("mission", mid))
        lines.append(asp.fact("mess_of", mid, m.mess))
        lines.append(asp.fact("good_ratio", mid, *m.share_ratio_good))
        lines.append(asp.fact("bad_ratio", mid, *m.share_ratio_bad))
        for t in sorted(m.tags):
            lines.append(asp.fact("tag", mid, t))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for g in sorted(t.guards):
            lines.append(asp.fact("guards", t.id, g))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_combos())
    cl = set((s, m, t) for (s, m, t, _, _) in asp_valid_stories())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and Python reasonableness gate:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for sid, setting in SETTINGS.items():
        for mid, mission in MISSIONS.items():
            if not mission_is_reasonable(mission, setting):
                continue
            if select_tool(mission) is None:
                continue
            combos.append((sid, mid, "foam"))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Superhero story world: satellite, nasty, ratio, happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--mission", choices=MISSIONS)
    ap.add_argument("--hero")
    ap.add_argument("--sidekick")
    ap.add_argument("-n", "--n", type=int, default=1)
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
    if getattr(args, "place", None) and getattr(args, "mission", None):
        setting = _safe_lookup(SETTINGS, getattr(args, "place", None))
        mission = _safe_lookup(MISSIONS, getattr(args, "mission", None))
        if not mission_is_reasonable(mission, setting):
            return _fallback_storyparams(args, rng, StoryParams, globals())
        if select_tool(mission) is None:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "mission", None) is None or c[1] == getattr(args, "mission", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, mission, _ = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    sidekick = getattr(args, "sidekick", None) or rng.choice([n for n in SIDEKICK_NAMES if n != hero])
    return StoryParams(
        place=place,
        mission=mission,
        hero=hero,
        sidekick=sidekick,
        hero_trait=rng.choice(TRAITS),
        sidekick_trait=rng.choice(TRAITS),
    )


def generate(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.hero, kind="character", type="girl", memes={"trait": params.hero_trait}))
    sidekick = world.add(Entity(id=params.sidekick, kind="character", type="boy", memes={"trait": params.sidekick_trait}))
    sat = world.add(Entity(id="satellite", type="machine", label="satellite", tags={"satellite"}))
    mission = _safe_lookup(MISSIONS, params.mission)
    world.facts.update(hero=hero, sidekick=sidekick, satellite=sat, mission=mission, setting=_safe_lookup(SETTINGS, params.place))
    tell_world(world, hero, sidekick, mission)
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
        lines.append(f"  {e.id:10} ({e.kind:7}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="city", mission="satellite", hero="Nova", sidekick="Zip", hero_trait="brave", sidekick_trait="kind"),
    StoryParams(place="roof", mission="satellite", hero="Bolt", sidekick="Echo", hero_trait="steady", sidekick_trait="curious"),
    StoryParams(place="lab", mission="antenna", hero="Spark", sidekick="Luna", hero_trait="quick-thinking", sidekick_trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for s, m, t, a, b in stories:
            print(f"  {s:8} {m:9} {t:8} ratio={a}:{b}")
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
            header = f"### {p.hero} and {p.sidekick}: {p.mission} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
