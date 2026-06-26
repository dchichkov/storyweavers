#!/usr/bin/env python3
"""
storyworlds/worlds/mafia_paddy_count_problem_solving_space_adventure.py
=======================================================================

A tiny space-adventure storyworld about a counted cargo mystery, a clever
problem-solving crew, and a troublesome "mafia" of smugglers who try to steal
parts from a moon station.

The seed words are treated as a premise:
- mafia: a sneaky gang of space smugglers
- paddy: the crew's helper mechanic
- count: a careful counting problem that must be solved

The story stays close to a classic space-adventure shape:
1) setup on a station or ship,
2) a problem appears,
3) the crew counts, compares, and tests a plan,
4) the solution restores order.

This world models both physical meters and emotional memes, and it includes an
ASP twin for the reasonableness gate plus parity verification.
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
# Core model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    ally: object | None = None
    device: object | None = None
    hero: object | None = None
    issue: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        female = {"girl", "woman", "mother", "captain"}
        male = {"boy", "man", "father", "pilot", "mechanic", "scout"}
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
    sky: str
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
class Problem:
    id: str
    title: str
    verb: str
    gerund: str
    mess: str
    soil: str
    zone: set[str]
    clue: str
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
    solves: set[str]
    prep: str
    tail: str
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


@dataclass
class StoryParams:
    setting: str
    problem: str
    tool: str
    name: str
    role: str
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        return clone


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "moon_station": Setting(place="the moon station", sky="silver-black sky", affords={"counting"}),
    "asteroid_dock": Setting(place="the asteroid dock", sky="deep star-dark", affords={"counting"}),
    "cargo_ship": Setting(place="the cargo ship", sky="blue-black space", affords={"counting"}),
}

PROBLEMS = {
    "missing_bolts": Problem(
        id="missing_bolts",
        title="missing bolts",
        verb="find the missing bolts",
        gerund="counting bolts",
        mess="missing",
        soil="not enough to build the panel",
        zone={"cargo"},
        clue="three crates had the wrong number written on them",
        tags={"count", "cargo"},
    ),
    "mixed_crates": Problem(
        id="mixed_crates",
        title="mixed crates",
        verb="sort the mixed crates",
        gerund="sorting crates",
        mess="mixed",
        soil="out of order",
        zone={"cargo", "hands"},
        clue="the red crates and blue crates were all in one pile",
        tags={"count", "cargo"},
    ),
    "too_many_lights": Problem(
        id="too_many_lights",
        title="too many lights",
        verb="count the blinking lights",
        gerund="counting lights",
        mess="confused",
        soil="too confusing to read",
        zone={"eyes", "dash"},
        clue="the dashboard lights blinked in a pattern that was easy to lose",
        tags={"count", "dash"},
    ),
}

TOOLS = {
    "counting_grid": Tool(
        id="counting_grid",
        label="a counting grid",
        phrase="a square counting grid",
        covers={"cargo", "hands"},
        solves={"missing", "mixed"},
        prep="set up a counting grid",
        tail="used the grid to line everything up",
    ),
    "flash_card": Tool(
        id="flash_card",
        label="flash cards",
        phrase="bright flash cards",
        covers={"eyes"},
        solves={"confused"},
        prep="make flash cards",
        tail="held up the flash cards one by one",
    ),
    "sticker_tags": Tool(
        id="sticker_tags",
        label="sticker tags",
        phrase="neat sticker tags",
        covers={"cargo"},
        solves={"mixed", "missing"},
        prep="put sticker tags on each crate",
        tail="tagged each crate before counting again",
    ),
}

CREW_NAMES = ["Paddy", "Mara", "Juno", "Tess", "Rin", "Nova", "Lio", "Kip"]
ROLES = ["captain", "pilot", "mechanic", "scout"]
HELPERS = ["mechanic", "navigator", "helper", "mate"]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
% A problem is a good fit when the tool solves its mess and covers the zone
% where the problem matters.
fits(P, T) :- problem(P), tool(T),
              problem_mess(P, M), solves(T, M),
              problem_zone(P, Z), covers(T, Z).

valid_story(S, P, T) :- setting(S), problem(P), tool(T), affords(S, counting), fits(P, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("problem_mess", pid, p.mess))
        for z in sorted(p.zone):
            lines.append(asp.fact("problem_zone", pid, z))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for m in sorted(t.solves):
            lines.append(asp.fact("solves", tid, m))
        for z in sorted(t.covers):
            lines.append(asp.fact("covers", tid, z))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    a = set(valid_stories())
    b = set(asp_valid_stories())
    if a == b:
        print(f"OK: clingo gate matches valid_stories() ({len(a)} stories).")
        return 0
    print("MISMATCH between clingo and valid_stories():")
    if a - b:
        print("  only in python:", sorted(a - b))
    if b - a:
        print("  only in clingo:", sorted(b - a))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def problem_matches_tool(problem: Problem, tool: Tool) -> bool:
    return problem.mess in tool.solves and any(z in tool.covers for z in problem.zone)


def valid_stories() -> list[tuple[str, str, str]]:
    out = []
    for sid, s in SETTINGS.items():
        for pid, p in PROBLEMS.items():
            for tid, t in TOOLS.items():
                if s.affords and "counting" in s.affords and problem_matches_tool(p, t):
                    out.append((sid, pid, tid))
    return out


# ---------------------------------------------------------------------------
# Story engine
# ---------------------------------------------------------------------------

def pick_name(rng: random.Random) -> str:
    return rng.choice(CREW_NAMES)


def build_story(setting: Setting, problem: Problem, tool: Tool, name: str, role: str, helper: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=role, label=name))
    ally = world.add(Entity(id="Paddy", kind="character", type=helper, label="Paddy"))
    issue = world.add(Entity(id=problem.id, type="problem", label=problem.title, phrase=problem.title))
    device = world.add(Entity(id=tool.id, type="tool", label=tool.label, phrase=tool.phrase, owner=hero.id))

    # setup
    world.say(f"{hero.id} worked on {world.setting.place}, where the {world.setting.sky} hung over the hull.")
    world.say(f"Near the loading bay, {ally.id} found a small space problem: {problem.clue}.")
    world.say(f"That meant the crew had to {problem.verb}, and the answer had to come from careful counting.")

    world.para()

    # tension
    hero.memes["worry"] += 1
    ally.memes["focus"] += 1
    world.say(f"{hero.id} looked at the crates and frowned. {hero.pronoun().capitalize()} could not trust a quick guess.")
    world.say(f"{ally.id} said, \"Let's count it slowly, one by one.\"")
    world.say(f"They set out {tool.phrase} so each piece had a place.")

    # problem solving
    world.para()
    hero.memes["confidence"] += 1
    world.zone = set(problem.zone)
    world.say(f"{hero.id} used {tool.label} to line the cargo up again.")
    world.say(f"{problem.clue.capitalize()}, so {ally.id} checked each crate aloud.")
    world.say(f"When the last piece was counted, the mistake was plain: {problem.soil}.")

    # resolution
    world.para()
    hero.memes["joy"] += 1
    ally.memes["relief"] += 1
    world.say(f"Together they fixed it with {tool.label}, and the crew could finally move the supplies.")
    world.say(f"{hero.id} smiled as the station lights blinked clean and steady again.")
    world.say(f"Even the little space mafia that had tried to hide the parts could not beat a good count.")

    world.facts.update(
        hero=hero,
        ally=ally,
        problem=issue,
        problem_cfg=problem,
        tool=device,
        tool_cfg=tool,
        setting=setting,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    problem = _safe_fact(world, f, "problem_cfg")
    tool = _safe_fact(world, f, "tool_cfg")
    return [
        f"Write a short space-adventure story about {hero.id}, Paddy, and a counting problem on {world.setting.place}.",
        f"Tell a child-friendly story where a tiny space mafia causes trouble, but the crew solves it by counting carefully with {tool.label}.",
        f"Write a simple story that includes the words mafia, Paddy, and count, and ends with a solved problem on a spaceship.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    ally = _safe_fact(world, f, "ally")
    problem = _safe_fact(world, f, "problem_cfg")
    tool = _safe_fact(world, f, "tool_cfg")
    return [
        QAItem(
            question=f"Who helped {hero.id} solve the counting problem?",
            answer=f"Paddy helped {hero.id}, and they worked together on the problem step by step.",
        ),
        QAItem(
            question=f"What did {hero.id} use to fix the mistake?",
            answer=f"{hero.id} used {tool.label} to line up the cargo and count it again.",
        ),
        QAItem(
            question=f"Why was the space mafia not a match for the crew?",
            answer="Because the crew did not rush. They counted carefully, checked the pieces, and found the mistake.",
        ),
        QAItem(
            question=f"What kind of problem was it?",
            answer=f"It was a problem about {problem.title}, so the crew had to solve it by counting carefully.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a count mean?",
            answer="A count is how many things there are when you say each one in order.",
        ),
        QAItem(
            question="Why can counting help solve a problem?",
            answer="Counting helps because it shows whether something is missing, extra, or in the wrong place.",
        ),
        QAItem(
            question="What is a spacecraft?",
            answer="A spacecraft is a vehicle built to travel in space.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({x[0] for x in world.fired})}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny space adventure about mafia, Paddy, and count.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--role", choices=ROLES)
    ap.add_argument("--helper", choices=HELPERS)
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
    choices = list(valid_stories())
    if getattr(args, "setting", None):
        choices = [c for c in choices if c[0] == getattr(args, "setting", None)]
    if getattr(args, "problem", None):
        choices = [c for c in choices if c[1] == getattr(args, "problem", None)]
    if getattr(args, "tool", None):
        choices = [c for c in choices if c[2] == getattr(args, "tool", None)]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, problem, tool = rng.choice(sorted(choices))
    name = getattr(args, "name", None) or pick_name(rng)
    role = getattr(args, "role", None) or rng.choice(["captain", "pilot", "scout"])
    helper = getattr(args, "helper", None) or "mechanic"
    return StoryParams(setting=setting, problem=problem, tool=tool, name=name, role=role, helper=helper)


def generate(params: StoryParams) -> StorySample:
    world = build_story(_safe_lookup(SETTINGS, params.setting), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(TOOLS, params.tool), params.name, params.role, params.helper)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        stories = asp_valid_stories()
        print(f"{len(stories)} compatible stories:\n")
        for s, p, t in stories:
            print(f"  {s:14} {p:16} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("moon_station", "missing_bolts", "counting_grid", "Paddy", "captain", "mechanic"),
            StoryParams("asteroid_dock", "mixed_crates", "sticker_tags", "Mara", "pilot", "mechanic"),
            StoryParams("cargo_ship", "too_many_lights", "flash_card", "Juno", "scout", "mechanic"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
            header = f"### {p.name}: {p.problem} on {p.setting} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
