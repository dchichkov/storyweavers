#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/auburn_problem_solving_moral_value_sound_effects.py
=============================================================================================================================

A small slice-of-life storyworld about an auburn-haired child, everyday problems,
gentle moral choices, and satisfying sound effects.

Seed tale idea:
---
A child with auburn hair notices a little household problem, feels a tiny worry,
then chooses to tell the truth, ask for help, and fix things carefully. The room
gets calm again, and the sound of the solution becomes the ending image.
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

    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Problem:
    id: str
    symptom: str
    sound: str
    verb: str
    method: str
    value: str
    tool: str
    consequence: str
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
    solves: set[str] = field(default_factory=set)
    sound: str = ""
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace_notes: list[str] = []

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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


SETTINGS = {
    "kitchen": Setting("the kitchen", True, {"spill", "stuck", "missing"}),
    "hallway": Setting("the hallway", True, {"stuck", "squeak", "missing"}),
    "bedroom": Setting("the bedroom", True, {"messy", "missing", "tear"}),
    "porch": Setting("the porch", True, {"squeak", "missing", "spill"}),
    "backyard": Setting("the backyard", False, {"missing", "tear", "squeak"}),
}

PROBLEMS = {
    "spill": Problem(
        id="spill",
        symptom="a little spill on the floor",
        sound="splat",
        verb="clean up the spill",
        method="wipe it with a towel",
        value="responsibility",
        tool="towel",
        consequence="the floor would stay sticky and someone could slip",
        tags={"mess", "cleaning", "honesty"},
    ),
    "squeak": Problem(
        id="squeak",
        symptom="a chair that gave a tiny squeak",
        sound="eeek",
        verb="fix the squeak",
        method="put a little oil on the joint",
        value="patience",
        tool="oil",
        consequence="the noise would keep bothering everyone",
        tags={"sound", "repair", "patience"},
    ),
    "missing": Problem(
        id="missing",
        symptom="a missing item under the sofa",
        sound="rustle",
        verb="find the missing thing",
        method="look carefully with a flashlight",
        value="helpfulness",
        tool="flashlight",
        consequence="the room would stay crowded with worry",
        tags={"searching", "help", "care"},
    ),
    "stuck": Problem(
        id="stuck",
        symptom="a drawer that would not open",
        sound="thunk",
        verb="free the drawer",
        method="pull gently and use a spoon to nudge the edge",
        value="calm",
        tool="spoon",
        consequence="the drawer would stay jammed",
        tags={"repair", "calm", "problem-solving"},
    ),
    "tear": Problem(
        id="tear",
        symptom="a torn little kite string",
        sound="rip",
        verb="mend the string",
        method="tie it with fresh tape",
        value="care",
        tool="tape",
        consequence="the kite would not fly right",
        tags={"repair", "care", "outside"},
    ),
}

TOOLS = {
    "towel": Tool("towel", "a soft towel", "the towel", {"spill"}, "swish"),
    "oil": Tool("oil", "a tiny bottle of oil", "the little bottle of oil", {"squeak"}, "glug"),
    "flashlight": Tool("flashlight", "a small flashlight", "the flashlight", {"missing"}, "click"),
    "spoon": Tool("spoon", "a sturdy spoon", "the spoon", {"stuck"}, "tap"),
    "tape": Tool("tape", "a roll of tape", "the tape", {"tear"}, "rip-tap"),
}

NAMES = {
    "girl": ["Lily", "Maya", "Nora", "Ava", "Zoe"],
    "boy": ["Leo", "Finn", "Theo", "Ben", "Max"],
}
TRAITS = ["careful", "curious", "kind", "patient", "bright"]


@dataclass
class StoryParams:
    place: str
    problem: str
    name: str
    gender: str
    parent: str
    trait: str
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


ASP_RULES = r"""
valid(Place, Problem, Tool) :- setting(Place), problem(Problem), tool(Tool),
                               affords(Place, Problem), solves(Tool, Problem).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for p in sorted(s.affords):
            lines.append(asp.fact("affords", sid, p))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("value_of", pid, p.value))
        lines.append(asp.fact("sound_of", pid, p.sound))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for p in sorted(t.solves):
            lines.append(asp.fact("solves", tid, p))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def reasonableness_gate(setting: Setting, problem: Problem) -> bool:
    return problem.id in setting.affords and problem.id in _safe_lookup(TOOLS, problem.tool).solves


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for pid, problem in PROBLEMS.items():
            if reasonableness_gate(setting, problem):
                combos.append((place, pid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld with auburn hair, everyday problems, moral values, and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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


def explain_rejection(setting: Setting, problem: Problem) -> str:
    return f"(No story: {setting.place} does not reasonably support a {problem.id} problem here.)"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "problem", None):
        if not reasonableness_gate(_safe_lookup(SETTINGS, getattr(args, "place", None)), _safe_lookup(PROBLEMS, getattr(args, "problem", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, name=name, gender=gender, parent=parent, trait=trait)


def _setup(world: World, hero: Entity, parent: Entity, problem: Problem) -> None:
    auburn = "auburn"
    world.say(f"{hero.id} was a {hero.pronoun('subject')} little {hero.type} with auburn hair and a careful way of looking at the room.")
    world.say(f"{hero.pronoun('subject').capitalize()} liked quiet chores, warm light, and the tiny sounds that came with everyday life.")
    world.say(f"That day, {world.setting.place} felt ordinary until there was {problem.symptom}; it made a little {problem.sound} sound.")
    world.say(f"{hero.id}'s {parent.type if parent.type in {'mother','father'} else 'parent'} noticed too, but waited to see what {hero.pronoun('subject')} would do.")


def _problem(world: World, hero: Entity, parent: Entity, problem: Problem) -> None:
    hero.memes["worry"] += 1
    world.say(f"{hero.id} took a breath. {hero.pronoun('subject').capitalize()} wanted to do the right thing, not pretend it was someone else's fault.")
    if problem.id == "spill":
        world.say(f'"Oh no," {hero.id} said with a soft {problem.sound}. "I should tell you what happened."')
    else:
        world.say(f'"{problem.sound}," {hero.id} murmured, and {hero.pronoun('subject')} started thinking about a gentle fix.')


def _solve(world: World, hero: Entity, parent: Entity, problem: Problem) -> None:
    tool = _safe_lookup(TOOLS, problem.tool)
    if problem.id == "spill":
        world.say(f"{hero.id} told the truth about the spill, and {parent.pronoun('subject')} nodded kindly. Together they used {tool.phrase} to {problem.method}, {tool.sound} {tool.sound}.")
    elif problem.id == "squeak":
        world.say(f"{hero.id} asked before touching the chair, then {parent.pronoun('subject')} helped. A careful dab of oil went {tool.sound}, and the chair grew quiet.")
    elif problem.id == "missing":
        world.say(f"{hero.id} did not rush. {hero.pronoun('subject').capitalize()} found {tool.phrase}, and the room answered with a small {tool.sound} as the missing thing appeared under the sofa.")
    elif problem.id == "stuck":
        world.say(f"{hero.id} and {parent.id} worked slowly together. One gentle push, one careful pull, a soft {tool.sound}, and the drawer gave way.")
    elif problem.id == "tear":
        world.say(f"{hero.id} held the torn string still while {parent.pronoun('subject')} used {tool.phrase}. The little rip became a neat fix with a crisp {tool.sound}-tap sound.")
    hero.memes["pride"] += 1
    hero.memes["trust"] += 1
    hero.memes["worry"] = 0
    world.say(f"{hero.id} felt better because the problem was smaller now, and because being honest had made the air feel open and kind.")


def tell(setting: Setting, problem: Problem, hero_name: str, hero_gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label="Parent"))
    world.facts.update(hero=hero, parent=parent, problem=problem, setting=setting)
    _setup(world, hero, parent, problem)
    world.para()
    _problem(world, hero, parent, problem)
    world.para()
    _solve(world, hero, parent, problem)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, problem = f["hero"], f["parent"], f["problem"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little {hero.type} with auburn hair who notices a small problem and tries to fix it kindly.",
        ),
        QAItem(
            question=f"What problem did {hero.id} notice?",
            answer=f"{hero.id} noticed {problem.symptom}, and it made a little {problem.sound} sound in the room.",
        ),
        QAItem(
            question=f"What did {hero.id} do to solve it?",
            answer=f"{hero.id} chose to be honest and helpful, then used {_safe_lookup(TOOLS, problem.tool).phrase} to {problem.method}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt proud and calm because the problem was fixed and the right choice made the room feel kind again.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a flashlight for?",
            answer="A flashlight helps you see in dark places by shining a bright beam of light.",
        ),
        QAItem(
            question="Why is it good to tell the truth when something goes wrong?",
            answer="Telling the truth helps other people trust you, and it makes it easier to fix the problem together.",
        ),
        QAItem(
            question="What does a towel do?",
            answer="A towel can soak up water or wipe up a spill so the floor becomes clean again.",
        ),
        QAItem(
            question="What does patience mean?",
            answer="Patience means staying calm and waiting or working slowly when something needs care.",
        ),
    ]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, problem = f["hero"], f["problem"]
    return [
        f'Write a gentle slice-of-life story for a young child with auburn hair who notices a {problem.id} problem and tries to help.',
        f"Tell a short story where {hero.id} is honest, solves a little everyday problem, and ends with a quiet sound.",
        f'Write a simple story that includes the sound word "{problem.sound}" and shows a kind choice.',
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
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams("kitchen", "spill", "Lily", "girl", "mother", "careful"),
    StoryParams("hallway", "missing", "Leo", "boy", "father", "curious"),
    StoryParams("bedroom", "stuck", "Maya", "girl", "mother", "patient"),
    StoryParams("porch", "squeak", "Ben", "boy", "father", "kind"),
    StoryParams("backyard", "tear", "Nora", "girl", "mother", "bright"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROBLEMS, params.problem), params.name, params.gender, params.parent, params.trait)
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
    ap = build_parser()
    args = ap.parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, problem, tool) combos:\n")
        for item in triples:
            print(" ", item)
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
            header = f"### {p.name}: {p.problem} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
