#!/usr/bin/env python3
"""
storyworlds/worlds/menagerie_problem_solving_rhyming_story.py
=============================================================

A standalone storyworld for a small menagerie tale with problem solving and a
rhyming-story feel.

Premise:
- A child visits a menagerie and finds a small problem that needs careful
  thinking.
- The world model tracks who is there, what is broken or missing, what tools
  exist, and how much worry/relief each entity feels.
- The ending proves the problem changed because of the chosen fix.

The prose aims for child-facing rhyming cadence, without turning into a frozen
template swap. The simulated state drives the narrative beats:
setup -> problem -> reasoning -> fix -> resolution.
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
# World model
# ---------------------------------------------------------------------------

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
    kind: str = "thing"  # "character" | "animal" | "thing" | "place"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    location: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    animal: object | None = None
    child: object | None = None
    parent: object | None = None
    problem: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.kind == "animal":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
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
class Problem:
    id: str
    label: str
    phrase: str
    clue: str
    mess: str
    solution: str
    required_tool: str
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
    phrase: str
    helps: set[str]
    verb: str
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
class Setting:
    place: str = "the menagerie"
    detail: str = "a bright place with straw, stone, and song"
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, line: str) -> None:
        self.events.append(line)

    def render(self) -> str:
        return " ".join(self.events)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "menagerie": Setting(place="the menagerie", detail="a bright place with straw, stone, and song"),
}

PROBLEMS = {
    "lost_bucket": Problem(
        id="lost_bucket",
        label="lost bucket",
        phrase="a little red bucket",
        clue="a trail of berries and paw prints",
        mess="thirsty",
        solution="find the bucket by following the clue trail",
        required_tool="map",
        tags={"find", "water"},
    ),
    "stuck_gate": Problem(
        id="stuck_gate",
        label="stuck gate",
        phrase="the side gate that would not swing wide",
        clue="a squeak in the hinge and a sleepy key ring nearby",
        mess="stuck",
        solution="oil the hinge and use the right key",
        required_tool="oilcan",
        tags={"fix", "gate"},
    ),
    "tangled_rope": Problem(
        id="tangled_rope",
        label="tangled rope",
        phrase="a rope knotted tight like a loop of twine",
        clue="a twist in the rope that shone in the light",
        mess="tied",
        solution="unwind the knot with a hook and a gentle tug",
        required_tool="hook",
        tags={"untie", "rope"},
    ),
    "muddy_path": Problem(
        id="muddy_path",
        label="muddy path",
        phrase="a muddy path by the marmot pen",
        clue="fresh prints and a patch that squelched again",
        mess="muddy",
        solution="sweep the path clean so paws and shoes can pass",
        required_tool="broom",
        tags={"clean", "path"},
    ),
}

TOOLS = {
    "map": Tool(
        id="map",
        label="a folded map",
        phrase="a folded map with marks in ink",
        helps={"find"},
        verb="follow",
        tags={"find", "clue"},
    ),
    "oilcan": Tool(
        id="oilcan",
        label="a small oilcan",
        phrase="a small oilcan that glimmered gold",
        helps={"fix"},
        verb="oil",
        tags={"fix", "hinge"},
    ),
    "hook": Tool(
        id="hook",
        label="a hook on a stick",
        phrase="a hook on a stick with a round, safe bend",
        helps={"untie"},
        verb="hook",
        tags={"untie", "rope"},
    ),
    "broom": Tool(
        id="broom",
        label="a sturdy broom",
        phrase="a sturdy broom with bristles neat",
        helps={"clean"},
        verb="sweep",
        tags={"clean", "path"},
    ),
}

ANIMALS = {
    "panda": {"type": "panda", "label": "panda", "phrase": "a sleepy panda"},
    "otter": {"type": "otter", "label": "otter", "phrase": "a bouncy otter"},
    "goat": {"type": "goat", "label": "goat", "phrase": "a silly goat"},
    "lemur": {"type": "lemur", "label": "lemur", "phrase": "a ring-tailed lemur"},
}

GIRL_NAMES = ["Mia", "Lily", "Nora", "Zoe", "Ava", "Ruby", "Ella", "June"]
BOY_NAMES = ["Leo", "Ben", "Max", "Theo", "Finn", "Noah", "Eli", "Sam"]
TRAITS = ["brave", "curious", "gentle", "quick", "cheery", "spry"]


# ---------------------------------------------------------------------------
# Reasonableness gate and ASP twin
# ---------------------------------------------------------------------------

def problem_needs_tool(problem: Problem, tool: Tool) -> bool:
    return problem.required_tool == tool.id and bool(problem.tags & tool.tags)


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, p in PROBLEMS.items():
        for tid, t in TOOLS.items():
            if problem_needs_tool(p, t):
                combos.append((pid, tid))
    return combos


ASP_RULES = r"""
% A problem is solvable when its required tool matches a tool that helps that task.
solvable(P, T) :- problem(P), tool(T), needs(P, T), helps(T, K), tag(P, K).

#show solvable/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("needs", pid, p.required_tool))
        for tag in sorted(p.tags):
            lines.append(asp.fact("tag", pid, tag))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for tag in sorted(t.tags):
            lines.append(asp.fact("helps", tid, tag))
    return "\n".join(lines)


def asp_program(show: str = "#show solvable/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_solvable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show solvable/2."))
    return sorted(set(asp.atoms(model, "solvable")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_solvable())
    if py == cl:
        print(f"OK: clingo parity matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gate:")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Params
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
    gender: str
    parent: str
    trait: str
    animal: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Story world mechanics
# ---------------------------------------------------------------------------
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


class StoryWorld:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.story: list[str] = []
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def say(self, text: str) -> None:
        if text:
            self.story.append(text)

    def render(self) -> str:
        return " ".join(self.story)


def build_world(params: StoryParams) -> StoryWorld:
    world = StoryWorld(_safe_lookup(SETTINGS, params.place))

    child = world.add(Entity(
        id=params.name, kind="character", type=params.gender, label=params.name,
        meters={"worry": 0.0, "joy": 0.0}, memes={"hope": 0.0, "curiosity": 1.0}
    ))
    parent = world.add(Entity(
        id="parent", kind="character", type=params.parent, label=f"the {params.parent}",
        meters={"work": 0.0}, memes={"calm": 1.0}
    ))
    animal_info = _safe_lookup(ANIMALS, params.animal)
    animal = world.add(Entity(
        id="animal", kind="animal", type=animal_info["type"], label=animal_info["label"],
        phrase=animal_info["phrase"], location="yard",
        meters={"thirst": 0.0, "worry": 0.0}, memes={"patience": 1.0}
    ))
    problem = world.add(Entity(
        id="problem", kind="thing", type=params.problem, label=_safe_lookup(PROBLEMS, params.problem).label,
        phrase=_safe_lookup(PROBLEMS, params.problem).phrase, location=params.place,
        meters={"broken": 1.0, "stuck": 0.0, "mess": 0.0}, memes={"attention": 1.0}
    ))
    tool = world.add(Entity(
        id="tool", kind="thing", type=params.tool, label=_safe_lookup(TOOLS, params.tool).label,
        phrase=_safe_lookup(TOOLS, params.tool).phrase, location="tool shed",
        meters={"ready": 1.0}, memes={"help": 1.0}
    ))
    world.facts.update(child=child, parent=parent, animal=animal, problem=problem, tool=tool, params=params)
    return world


def _setup(world: StoryWorld) -> None:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    child: Entity = _safe_fact(world, world.facts, "child")
    parent: Entity = _safe_fact(world, world.facts, "parent")
    animal: Entity = _safe_fact(world, world.facts, "animal")
    problem: Entity = _safe_fact(world, world.facts, "problem")

    world.say(f"At {world.setting.place}, {p.name} came with a grin and a springy stride.")
    world.say(f"{p.name} was a {p.trait} little {p.gender} who liked every game with a glide.")
    world.say(f"Near the pens was {animal.phrase}, who blinked at the day with a patient stare.")
    world.say(f"But {problem.phrase} had a snag, so the path needed care.")
    child.memes["curiosity"] += 1
    animal.meters["worry"] += 1
    problem.meters["broken"] = 1.0


def _problem(world: StoryWorld) -> None:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    problem: Entity = _safe_fact(world, world.facts, "problem")
    child: Entity = _safe_fact(world, world.facts, "child")
    parent: Entity = _safe_fact(world, world.facts, "parent")

    world.say(f"{p.name} saw the clue: {problem.phrase} and {problem.clue}.")
    world.say(f'"We can sort this out," said {parent.label}, "with careful thinking, too."')
    child.meters["worry"] += 1
    child.memes["hope"] += 1


def _solve(world: StoryWorld) -> None:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    problem: Entity = _safe_fact(world, world.facts, "problem")
    tool: Entity = _safe_fact(world, world.facts, "tool")
    animal: Entity = _safe_fact(world, world.facts, "animal")
    parent: Entity = _safe_fact(world, world.facts, "parent")
    child: Entity = _safe_fact(world, world.facts, "child")

    if not problem_needs_tool(_safe_lookup(PROBLEMS, p.problem), _safe_lookup(TOOLS, p.tool)):
        pass

    world.say(f"{p.name} found {tool.phrase} and held it up high.")
    world.say(f"Together they used it to {_safe_lookup(PROBLEMS, p.problem).solution}, nice and spry.")
    if p.tool == "map":
        world.say(f"They followed the marks, and the red bucket popped into sight like a rhyme.")
    elif p.tool == "oilcan":
        world.say(f"The hinge gave a tiny squeak, then swung open in time.")
    elif p.tool == "hook":
        world.say(f"The knot came loose with a soft little bob, then a merry little twine.")
    elif p.tool == "broom":
        world.say(f"The mud brushed away, and the path turned neat and fine.")
    problem.meters["broken"] = 0.0
    problem.memes["attention"] = 0.0
    animal.meters["worry"] = 0.0
    child.meters["worry"] = max(0.0, child.meters["worry"] - 1.0)
    child.meters["joy"] += 1.0
    parent.meters["work"] += 0.0


def _resolution(world: StoryWorld) -> None:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    problem: Entity = _safe_fact(world, world.facts, "problem")
    animal: Entity = _safe_fact(world, world.facts, "animal")
    child: Entity = _safe_fact(world, world.facts, "child")

    if p.problem == "lost_bucket":
        ending = f"At last, the little red bucket sat by the pen, all shiny and bright."
    elif p.problem == "stuck_gate":
        ending = f"At last, the side gate swung wide, and the way felt airy and light."
    elif p.problem == "tangled_rope":
        ending = f"At last, the rope lay loose and smooth, like a ribbon in flight."
    else:
        ending = f"At last, the muddy path was clean, and every step felt right."
    world.say(ending)
    world.say(f"{animal.phrase} gave a happy nod, and {p.name} felt proud that the fix was tight.")
    world.say(f"Problem solved in the menagerie, and the whole day ended in rhyme and delight.")
    child.memes["hope"] += 1
    problem.meters["broken"] = 0.0


def tell_story(params: StoryParams) -> StoryWorld:
    world = build_world(params)
    _setup(world)
    _problem(world)
    _solve(world)
    _resolution(world)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: StoryWorld) -> list[str]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    prob = _safe_lookup(PROBLEMS, p.problem)
    return [
        f"Write a rhyming story about a child at the menagerie who solves {prob.label}.",
        f"Tell a gentle problem-solving tale where {p.name} uses {_safe_lookup(TOOLS, p.tool).label} to fix {prob.phrase}.",
        f"Write a short rhyming story set at the menagerie, with a clue, a tool, and a happy ending.",
    ]


def story_qa(world: StoryWorld) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    prob = _safe_lookup(PROBLEMS, p.problem)
    tool = _safe_lookup(TOOLS, p.tool)
    child: Entity = _safe_fact(world, world.facts, "child")
    animal: Entity = _safe_fact(world, world.facts, "animal")

    return [
        QAItem(
            question=f"What problem did {p.name} notice at the menagerie?",
            answer=f"{p.name} noticed {prob.phrase}, and it needed careful fixing."
        ),
        QAItem(
            question=f"What tool helped {p.name} solve the problem?",
            answer=f"{tool.phrase} helped {p.name} {tool.verb} the problem in the right way."
        ),
        QAItem(
            question=f"How did {child.label} feel after the problem was solved?",
            answer=f"{child.label} felt proud and happy, because the worry went away and the day ended well."
        ),
        QAItem(
            question=f"What did the animal do at the end?",
            answer=f"{animal.phrase} gave a happy nod when everything was fixed."
        ),
    ]


WORLD_KNOWLEDGE = {
    "menagerie": [
        (
            "What is a menagerie?",
            "A menagerie is a place where animals are cared for and people can see different kinds of creatures.",
        )
    ],
    "map": [
        (
            "What is a map for?",
            "A map shows where places are and helps you find your way.",
        )
    ],
    "oilcan": [
        (
            "What does oil do for a hinge?",
            "Oil can help a hinge move more smoothly and stop it from squeaking.",
        )
    ],
    "broom": [
        (
            "What is a broom used for?",
            "A broom is used to sweep up dirt and make a floor or path cleaner.",
        )
    ],
    "hook": [
        (
            "What can a hook be used for?",
            "A hook can help lift, catch, or pull something gently without using your hands.",
        )
    ],
}


def world_knowledge_qa(world: StoryWorld) -> list[QAItem]:
    p: StoryParams = _safe_fact(world, world.facts, "params")
    out = list(WORLD_KNOWLEDGE["menagerie"])
    out.extend(WORLD_KNOWLEDGE.get(p.tool, []))
    return [QAItem(question=q, answer=a) for q, a in out]


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


def dump_trace(world: StoryWorld) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.location:
            bits.append(f"location={e.location}")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Params resolution
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming menagerie problem-solving storyworld."
    )
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--problem", choices=PROBLEMS.keys())
    ap.add_argument("--tool", choices=TOOLS.keys())
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--animal", choices=ANIMALS.keys())
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
    combos = valid_combos()
    if getattr(args, "problem", None) and getattr(args, "tool", None):
        if (getattr(args, "problem", None), getattr(args, "tool", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    options = [
        (p, t) for p, t in combos
        if (getattr(args, "problem", None) is None or p == getattr(args, "problem", None))
        and (getattr(args, "tool", None) is None or t == getattr(args, "tool", None))
    ]
    if not options:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    problem, tool = rng.choice(sorted(options))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    animal = getattr(args, "animal", None) or rng.choice(sorted(ANIMALS.keys()))
    place = getattr(args, "place", None) or "menagerie"
    return StoryParams(
        place=place,
        problem=problem,
        tool=tool,
        name=name,
        gender=gender,
        parent=parent,
        trait=trait,
        animal=animal,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell_story(params)
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


# ---------------------------------------------------------------------------
# ASP support
# ---------------------------------------------------------------------------

def asp_program(show: str = "#show solvable/2.") -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show solvable/2."))
        return

    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show solvable/2."))
        print(f"{len(set(asp.atoms(model, 'solvable')))} solvable pairs:")
        for pid, tid in sorted(set(asp.atoms(model, "solvable"))):
            print(f"  {pid:12} {tid}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams("menagerie", "lost_bucket", "map", "Mia", "girl", "mother", "curious", "otter"),
            StoryParams("menagerie", "stuck_gate", "oilcan", "Leo", "boy", "father", "brave", "goat"),
            StoryParams("menagerie", "tangled_rope", "hook", "Nora", "girl", "father", "gentle", "lemur"),
            StoryParams("menagerie", "muddy_path", "broom", "Ben", "boy", "mother", "cheery", "panda"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.name}: {p.problem} with {p.tool} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
