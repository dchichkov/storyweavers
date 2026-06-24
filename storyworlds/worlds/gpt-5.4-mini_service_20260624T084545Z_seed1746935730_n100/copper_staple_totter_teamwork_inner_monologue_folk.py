#!/usr/bin/env python3
"""
storyworlds/worlds/copper_staple_totter_teamwork_inner_monologue_folk.py
========================================================================

A small folk-tale storyworld about a wobbly totter, a missing copper staple,
and two friends who solve the trouble by working together.

Seed tale idea:
---
In a little village at the edge of a wood, a child finds that the old village
totter keeps wobbling when anyone steps on it. A loose board has come apart, and
the blacksmith has gone away for the day. The child worries in silence, then
hears a friend call from the lane. Together they fetch a copper staple, hold the
board steady, and mend the totter before sunset.

The world is built to support:
- Teamwork as the turning point.
- Inner monologue as the hero's quiet worry and decision.
- Folk-tale style with a village, a helper, a tool, and a modest repair.
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



def _safe_fact(world, facts, key):
    value = facts.get(key) if hasattr(facts, "get") else None
    if hasattr(value, "id") or hasattr(value, "label") or hasattr(value, "verb"):
        return value
    if isinstance(value, str) and hasattr(world, "get"):
        try:
            resolved = world.get(value)
            if resolved is not None:
                return resolved
        except Exception:
            pass
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

    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
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
class Place:
    name: str
    indoors: bool = False
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
class Problem:
    id: str
    verb: str
    gerund: str
    cause: str
    risk: str
    inner_thought: str
    zone: str = "bridge"
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
    task: str
    tail: str
    requires: set[str] = field(default_factory=set)
    ends_risk: bool = True
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.state: dict[str, float] = {"totter": 0.0, "repair": 0.0}
        self.thoughts: list[str] = []

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
        c = World(self.place)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.state = dict(self.state)
        c.thoughts = list(self.thoughts)
        c.facts = copy.deepcopy(self.facts)
        return c


def _r_totter(world: World) -> list[str]:
    out: list[str] = []
    if world.state["totter"] < THRESHOLD:
        return out
    sig = ("totter",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("The old totter shivered and gave a little wobble.")
    return out


def _r_risk(world: World) -> list[str]:
    out: list[str] = []
    if world.state["totter"] < THRESHOLD:
        return out
    sig = ("risk",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    out.append("Anyone who stepped on it felt the board dip underfoot.")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    if world.state["repair"] < THRESHOLD:
        return out
    sig = ("repair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    world.state["totter"] = 0.0
    out.append("The loose board held fast at last.")
    return out


CAUSAL_RULES = [_r_totter, _r_risk, _r_repair]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoors:
            lines.append(asp.fact("indoors", pid))
    for pid, prob in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        for t in sorted(prob.tags):
            lines.append(asp.fact("tagged", pid, t))
    for fid, fix in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for r in sorted(fix.requires):
            lines.append(asp.fact("requires", fid, r))
    for rid in sorted(ROLES):
        lines.append(asp.fact("role", rid))
    return "\n".join(lines)


ASP_RULES = r"""
% A problem is resolveable when the fix requires the same folk tools/tone.
eligible(P, F) :- problem(P), fix(F), problem_tag(P, teamwork), requires(F, teamwork).
eligible(P, F) :- problem(P), fix(F), problem_tag(P, copper), requires(F, copper).
eligible(P, F) :- problem(P), fix(F), problem_tag(P, staple), requires(F, staple).
eligible_story(Place, P, F, Role) :- place(Place), problem(P), fix(F), eligible(P, F), role(Role).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show eligible_story/4."))
    return sorted(set(asp.atoms(model, "eligible_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set((p, f) for _, p, f, _ in asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print(" only in python:", sorted(py - cl))
    print(" only in clingo:", sorted(cl - py))
    return 1


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place in PLACES:
        for prob in PROBLEMS:
            for fix in FIXES:
                if reason_ok(_safe_lookup(PROBLEMS, prob), _safe_lookup(FIXES, fix)):
                    combos.append((place, prob, fix))
    return combos


def reason_ok(problem: Problem, fix: Fix) -> bool:
    return problem.id in {"totter"} and fix.id in {"copper_staple"} and {"teamwork", "copper", "staple"} & (problem.tags | fix.requires)


@dataclass
class StoryParams:
    place: str
    problem: str
    fix: str
    hero: str
    helper: str
    hero_type: str
    helper_type: str
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
    "village_green": Place("the village green"),
    "mill_lane": Place("the mill lane"),
    "oak_lane": Place("the oak lane"),
}

PROBLEMS = {
    "totter": Problem(
        id="totter",
        verb="step onto the totter",
        gerund="stepping onto the totter",
        cause="a loose board had come apart",
        risk="the board might give way",
        inner_thought="What if I step on it and it breaks? What if everyone laughs?",
        tags={"teamwork", "copper", "staple"},
    ),
}

FIXES = {
    "copper_staple": Fix(
        id="copper_staple",
        label="a copper staple",
        phrase="a bright copper staple from the smith's box",
        task="hold the loose board steady",
        tail="worked together until the board was snug and still",
        requires={"copper", "staple", "teamwork"},
    ),
}

ROLES = {
    "girl", "boy", "mother", "father", "friend", "sibling"
}

NAMES = {
    "girl": ["Mira", "Lina", "Edda", "Nora", "Tilda"],
    "boy": ["Jon", "Bram", "Alfie", "Oren", "Pip"],
    "friend": ["Pip", "Moss", "Lark", "Wren", "Tavi"],
    "sibling": ["Pip", "Mira", "Lina", "Jon"],
    "mother": ["Mother Rowan", "Mother Elin"],
    "father": ["Father Alder", "Father Bram"],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short folk tale about {_safe_fact(world, f, "hero")} and {_safe_fact(world, f, "helper")} fixing a tottering village plaything with a copper staple.',
        f'Tell a gentle teamwork story where {_safe_fact(world, f, "hero")} worries in an inner monologue, then asks for help and mends the totter.',
        'Write a child-friendly village story that includes the words "copper", "staple", and "totter".',
    ]


def intro(world: World, hero: Entity) -> None:
    world.say(
        f"In {world.place.name}, {hero.id} was a little {hero.type} with quick feet and a careful heart."
    )


def set_scene(world: World, problem: Problem) -> None:
    world.say(
        f"By the green stood an old totter. {problem.cause.capitalize()}, so the board would wobble whenever anyone tried {problem.verb}."
    )


def inner_monologue(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["worry"] += 1
    world.thoughts.append(problem.inner_thought)
    world.say(
        f"{hero.id} looked at it and thought, \"{problem.inner_thought}\""
    )


def ask_for_help(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["resolve"] += 1
    helper.memes["kindness"] += 1
    world.say(
        f"Then {hero.id} saw {helper.id} coming down the lane, and {hero.id} called softly for help."
    )


def teamwork_fix(world: World, hero: Entity, helper: Entity, fix: Fix) -> None:
    world.state["repair"] += 1
    propagate(world, narrate=False)
    world.say(
        f"{hero.id} and {helper.id} fetched {fix.phrase}. {hero.id} held the board still while {helper.id} pressed the metal into place."
    )
    world.say(
        f"They {fix.tail}, and the totter stopped its shiver."
    )


def ending(world: World, hero: Entity, helper: Entity) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"At sunset, {hero.id} and {helper.id} stepped on it together, and it stayed steady. "
        f"The village folk smiled, for the little repair had become a fine shared deed."
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place))
    hero = world.add(Entity(id=params.hero, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper, kind="character", type=params.helper_type))
    problem = _safe_lookup(PROBLEMS, params.problem)
    fix = _safe_lookup(FIXES, params.fix)

    world.facts.update(hero=hero.id, helper=helper.id, problem=problem, fix=fix, place=world.place.name)

    intro(world, hero)
    world.para()
    set_scene(world, problem)
    inner_monologue(world, hero, problem)
    world.para()
    ask_for_help(world, hero, helper)
    teamwork_fix(world, hero, helper, fix)
    ending(world, hero, helper)
    return world


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    problem: Problem = _safe_fact(world, f, "problem")
    fix: Fix = _safe_fact(world, f, "fix")
    return [
        QAItem(
            question=f"Why did {hero} worry when looking at the totter?",
            answer=f"{hero} worried because {problem.cause}, so the board might not stay safe and steady.",
        ),
        QAItem(
            question=f"What did {hero} think before asking {helper} for help?",
            answer=f"{hero} thought, \"{problem.inner_thought}\" Then {hero} decided that two pairs of hands would be better than one.",
        ),
        QAItem(
            question=f"How did {hero} and {helper} fix the totter?",
            answer=f"They used {fix.label} to hold the loose board steady. {hero} kept it still while {helper} pressed the copper piece into place, and that teamwork made the repair hold.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is copper?",
            answer="Copper is a reddish-brown metal. People can shape it into tools, wire, or shiny little parts that help hold things together.",
        ),
        QAItem(
            question="What is a staple?",
            answer="A staple is a small metal piece that can fasten things together, like paper or a loose bit of wood in a simple repair.",
        ),
        QAItem(
            question="What does totter mean?",
            answer="To totter means to wobble or sway unsteadily, as if something might tip over if it is not supported.",
        ),
        QAItem(
            question="What is teamwork?",
            answer="Teamwork is when people help each other do a job. One may hold, one may fix, and together they can finish the work well.",
        ),
        QAItem(
            question="What is an inner monologue?",
            answer="An inner monologue is the quiet talking a person does in their own mind, when they think through a problem or plan.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    lines.append(f"  place: {world.place.name}")
    lines.append(f"  state: {world.state}")
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"  {e.id:12} ({e.type}) meters={meters} memes={memes}")
    if world.thoughts:
        lines.append(f"  thoughts: {world.thoughts}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="village_green",
        problem="totter",
        fix="copper_staple",
        hero="Mira",
        helper="Pip",
        hero_type="girl",
        helper_type="friend",
    ),
    StoryParams(
        place="mill_lane",
        problem="totter",
        fix="copper_staple",
        hero="Jon",
        helper="Wren",
        hero_type="boy",
        helper_type="friend",
    ),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A folk-tale story world about copper, a staple, and a totter.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper-type", choices=["friend", "sibling"])
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
    if getattr(args, "problem", None) and getattr(args, "fix", None):
        if not reason_ok(_safe_lookup(PROBLEMS, getattr(args, "problem", None)), _safe_lookup(FIXES, getattr(args, "fix", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "fix", None) is None or c[2] == getattr(args, "fix", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, fix = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(["girl", "boy"])
    helper_type = getattr(args, "helper_type", None) or "friend"
    hero = getattr(args, "hero", None) or rng.choice(_safe_lookup(NAMES, hero_type))
    helper = getattr(args, "helper", None) or rng.choice(_safe_lookup(NAMES, helper_type))
    return StoryParams(place=place, problem=problem, fix=fix, hero=hero, helper=helper, hero_type=hero_type, helper_type=helper_type)


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


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show eligible/2."))
    return sorted(set(asp.atoms(model, "eligible")))


def asp_verify_gate() -> int:
    cl = set(asp_valid_combos())
    py = set(valid_combos())
    if cl == py:
        print(f"OK: clingo gate matches valid_combos() ({len(cl)} combos).")
        return 0
    print("Mismatch between clingo and python.")
    print("Only in clingo:", sorted(cl - py))
    print("Only in python:", sorted(py - cl))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show eligible_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify_gate())
    if getattr(args, "asp", None):
        items = asp_valid_combos()
        print(f"{len(items)} eligible story combos:")
        for p, prob, fix in items:
            print(f"  {p:12} {prob:10} {fix}")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero} and {p.helper}: {p.problem} with {p.fix} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
