#!/usr/bin/env python3
"""
storyworlds/worlds/burr_biz_mould_friendship_space_adventure.py
===============================================================

A small space-adventure storyworld about friendship, a tricky little problem,
and a kind fix that keeps the ship's biz moving.

Seed tale used to shape the world:
---
On a bright ship drifting past the moon, two best friends ran a tiny cargo biz.
One day a prickly burr rolled out of a crate and a damp patch of mould spread
under the cooling vent. Their ship smelled weird, and the customers' parcels
might get ruined.

The friends wanted to fix it fast. One friend gathered the burr with sticky
tape. The other wiped the mould with a scrub cloth and opened the vent wider.
They worked together, laughed, and got the cargo bay ready for the next stop.

World idea:
- The ship has physical meters like burrs, mould, mess, and cargo_safety.
- Friendship adds emotional memes like trust, teamwork, and worry.
- The narrative turns when the friends notice the mess, coordinate, and repair it.
- The ending proves the change: the bay is clean, the biz is safe, and the
  friends feel closer than before.
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
    carrying: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    a: object | None = None
    b: object | None = None
    cargo: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Place:
    name: str
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
class Problem:
    burr_kind: str = "burr"
    mould_kind: str = "mould"
    mess_kind: str = "space-mess"
    danger: str = "slippery"
    keyword: str = "burr"
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
class Tool:
    id: str
    label: str
    label_phrase: str
    fixes: set[str]
    offer: str
    closing: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
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


@dataclass
class StoryParams:
    place: str
    problem: str
    name1: str
    name2: str
    role1: str
    role2: str
    seed: Optional[int] = None
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


PLACES = {
    "cargo_bay": Place("the cargo bay", {"ship", "biz", "cargo"}),
    "moon_market": Place("the moon market", {"ship", "biz", "market"}),
    "orbital_kitchen": Place("the orbital kitchen", {"ship", "mould", "food"}),
    "starglass_hall": Place("the starglass hall", {"ship", "friendship"}),
}

PROBLEMS = {
    "cargo_bay": Problem(keyword="burr", burr_kind="burr", mould_kind="mould",
                         mess_kind="space-dust", danger="scratchy"),
    "moon_market": Problem(keyword="biz", burr_kind="burr", mould_kind="mould",
                           mess_kind="space-spill", danger="awkward"),
    "orbital_kitchen": Problem(keyword="mould", burr_kind="burr", mould_kind="mould",
                               mess_kind="damp", danger="sour"),
    "starglass_hall": Problem(keyword="friendship", burr_kind="burr", mould_kind="mould",
                              mess_kind="echo", danger="lonely"),
}

TOOLS = [
    Tool("tape", "sticky tape", "sticky tape", {"burr"}, "wrap the burr", "they peeled the burr away"),
    Tool("cloth", "scrub cloth", "a scrub cloth", {"mould"}, "wipe the mould", "they scrubbed the mould clean"),
    Tool("fan", "vent fan", "the vent fan", {"mould"}, "open the vent wider", "fresh air pushed the mould away"),
    Tool("bin", "sealed bin", "a sealed bin", {"burr"}, "drop the burr into a sealed bin", "the burr stayed trapped"),
]

NAMES = ["Nova", "Pip", "Milo", "Rin", "Tala", "Jett", "Iris", "Zed"]
ROLES = ["pilot", "mechanic", "navigator", "helper", "captain", "runner"]


def _meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _mem(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def valid_combos() -> list[tuple[str, str]]:
    return [(place, prob) for place in PLACES for prob in PROBLEMS]


def _problem_at_risk(place: Place, problem: Problem) -> bool:
    return True


def select_tool(problem: Problem) -> Optional[Tool]:
    if problem.keyword == "friendship":
        return None
    for tool in TOOLS:
        if problem.burr_kind in tool.fixes or problem.mould_kind in tool.fixes:
            return tool
    return None


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    problem = _safe_lookup(PROBLEMS, params.problem)
    world = World(place)

    a = world.add(Entity(id=params.name1, kind="character", type="girl", label=params.role1))
    b = world.add(Entity(id=params.name2, kind="character", type="boy", label=params.role2))
    cargo = world.add(Entity(id="cargo", type="thing", label="cargo crates", plural=True, caretaker=a.id))

    a.memes.update({"friendship": 2.0, "trust": 1.0, "curiosity": 1.0})
    b.memes.update({"friendship": 2.0, "trust": 1.0, "curiosity": 1.0})
    cargo.meters.update({"safe": 1.0})

    # Setup.
    world.say(
        f"In {place.name}, {a.id} and {b.id} ran a little biz moving cargo between bright stations."
    )
    world.say(
        f"{a.id} was the {params.role1} and {b.id} was the {params.role2}, and they liked working as a team."
    )
    world.say(
        f"One day, a prickly {problem.burr_kind} rolled under a crate, and a damp patch of {problem.mould_kind} spread near the vent."
    )

    # Conflict.
    world.para()
    a.memes["worry"] += 1.0
    b.memes["worry"] += 1.0
    cargo.meters["safe"] -= 1.0
    world.say(
        f"The cargo bay felt wrong. The {problem.burr_kind} could scratch the parcels, and the {problem.mould_kind} made the air smell old."
    )
    world.say(
        f"{a.id} said the biz needed help fast, and {b.id} nodded because friendship meant fixing hard things together."
    )

    # Turn.
    world.para()
    tool = select_tool(problem)
    if tool is None:
        # Direct friendship-focused fix, no tool.
        a.memes["trust"] += 1.0
        b.memes["trust"] += 1.0
        a.memes["teamwork"] += 1.0
        b.memes["teamwork"] += 1.0
        world.say(
            f"So they split the work. {a.id} chased the {problem.burr_kind} into a sealed bin while {b.id} opened the vent wide."
        )
        world.say(
            f"Then they wiped the damp spot together until the {problem.mould_kind} was gone."
        )
        world.say(
            f"That careful teamwork saved the little biz and made the ship feel friendly again."
        )
    else:
        if "burr" in tool.fixes:
            a.memes["teamwork"] += 1.0
            world.say(
                f"{a.id} used {tool.offer}, and {b.id} held the crate still."
            )
        if "mould" in tool.fixes:
            b.memes["teamwork"] += 1.0
            world.say(
                f"{b.id} used {tool.offer}, and fresh air helped the wet patch dry."
            )
        world.say(
            f"At last, {tool.closing}, and the cargo bay looked ready for the next stop."
        )
        a.memes["joy"] += 1.0
        b.memes["joy"] += 1.0
        a.memes["trust"] += 1.0
        b.memes["trust"] += 1.0

    cargo.meters["safe"] = 2.0
    world.facts.update(
        place=place,
        problem=problem,
        hero=a,
        friend=b,
        cargo=cargo,
        tool=tool,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    problem = _safe_fact(world, f, "problem").keyword
    return [
        f'Write a short space adventure for a child about friendship and a {problem} problem in a tiny biz.',
        f"Tell a gentle story where {f['hero'].id} and {f['friend'].id} fix a {f['problem'].burr_kind} and {f['problem'].mould_kind} problem together.",
        f"Write a child-facing story set on a ship where friends keep the cargo safe and the biz keeps going.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    friend: Entity = _safe_fact(world, f, "friend")
    problem: Problem = _safe_fact(world, f, "problem")
    place: Place = _safe_fact(world, f, "place")
    return [
        QAItem(
            question=f"Who were the two friends in {place.name}?",
            answer=f"They were {hero.id} and {friend.id}, and they worked together in a tiny cargo biz."
        ),
        QAItem(
            question=f"What problem appeared in the ship?",
            answer=f"A prickly {problem.burr_kind} and a damp patch of {problem.mould_kind} caused trouble in the cargo bay."
        ),
        QAItem(
            question=f"How did the friends solve it?",
            answer=(
                f"They shared the work. One friend handled the {problem.burr_kind}, the other cleaned the {problem.mould_kind}, "
                f"and their friendship helped the biz stay safe."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is friendship?",
            answer="Friendship is a kind bond between people who care about each other, share, and help when things are hard."
        ),
        QAItem(
            question="What is a burr?",
            answer="A burr is a tiny prickly bit that can stick to cloth or scratch things if you do not take it away."
        ),
        QAItem(
            question="What is mould?",
            answer="Mould is a fuzzy growth that likes damp places and can make food or rooms smell stale."
        ),
        QAItem(
            question="What is a biz?",
            answer="A biz is a small business or job that people run to make and deliver things."
        ),
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.kind:9}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place(P) :- fact_place(P).
problem(X) :- fact_problem(X).
valid(P, X) :- place(P), problem(X).

% A valid story should contain friendship, burr, and mould.
needs_friendship(P, X) :- valid(P, X), fact_theme(friendship).
needs_burr(P, X) :- valid(P, X), fact_keyword(burr).
needs_mould(P, X) :- valid(P, X), fact_keyword(mould).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for p in PLACES:
        lines.append(asp.fact("fact_place", p))
    for x in PROBLEMS:
        lines.append(asp.fact("fact_problem", x))
    lines.append(asp.fact("fact_theme", "friendship"))
    lines.append(asp.fact("fact_keyword", "burr"))
    lines.append(asp.fact("fact_keyword", "mould"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    clingo_set = set(asp.atoms(model, "valid"))
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(py_set)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("  only in clingo:", sorted(clingo_set - py_set))
    print("  only in python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Space-adventure friendship storyworld with burr and mould.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--name1")
    ap.add_argument("--name2")
    ap.add_argument("--role1", choices=ROLES)
    ap.add_argument("--role2", choices=ROLES)
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
    if getattr(args, "place", None) and getattr(args, "problem", None):
        if (getattr(args, "place", None), getattr(args, "problem", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    name1 = getattr(args, "name1", None) or rng.choice(NAMES)
    name2 = getattr(args, "name2", None) or rng.choice([n for n in NAMES if n != name1])
    role1 = getattr(args, "role1", None) or rng.choice(ROLES)
    role2 = getattr(args, "role2", None) or rng.choice([r for r in ROLES if r != role1])
    return StoryParams(place=place, problem=problem, name1=name1, name2=name2, role1=role1, role2=role2)


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/2."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams("cargo_bay", "cargo_bay", "Nova", "Pip", "pilot", "mechanic"),
            StoryParams("moon_market", "moon_market", "Rin", "Tala", "navigator", "helper"),
            StoryParams("orbital_kitchen", "orbital_kitchen", "Milo", "Jett", "captain", "runner"),
            StoryParams("starglass_hall", "starglass_hall", "Iris", "Zed", "pilot", "helper"),
        ]
        samples = [generate(p) for p in curated]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 40, 40):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
            header = f"### {p.name1} and {p.name2} at {p.place} ({p.problem})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
