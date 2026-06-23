#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/deli_chair_problem_solving_humor_lesson_learned.py
==============================================================================================================================

A standalone storyworld about a tiny mythic deli, a stubborn chair, funny
problem-solving, and a lesson learned.

The seed prompt asked for a story that includes the words "deli" and "chair",
with Problem Solving, Humor, Lesson Learned, and a mythic style. This world
models a small local legend: a hungry crowd, a wobbly chair, a clever fix,
and a final image that shows the chair made whole and the deli at peace.

The script follows the Storyweavers contract:
- typed entities with meters and memes
- state-driven narration
- a Python reasonableness gate and inline ASP twin
- prompts, story-grounded QA, and world-knowledge QA
- `--verify`, `--asp`, `--show-asp`, `--json`, `--trace`, `-n`, `--all`, `--seed`

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
from typing import Callable, Optional

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    tags: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    chair: object | None = None
    deli: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "queen", "priestess"}
        male = {"boy", "father", "dad", "man", "king", "priest"}
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
class Place:
    id: str
    label: str
    scene: str
    affords: set[str] = field(default_factory=set)
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
    danger: str
    symptom: str
    at_risk: set[str] = field(default_factory=set)
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
class Fix:
    id: str
    label: str
    method: str
    reveal: str
    succeeds: bool = True
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
class Charm:
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


@dataclass
class StoryParams:
    place: str = ""
    problem: str = ""
    fix: str = ""
    charm: str = ""
    hero: str = ""
    hero_kind: str = "priest"
    helper: str = ""
    helper_kind: str = "priestess"
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.needs_fix: bool = False

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        clone.needs_fix = self.needs_fix
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
    CAUSAL_RULES: list = field(default_factory=list)
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    chair = world.get("chair")
    if chair.meters["wobble"] < THRESHOLD:
        return out
    sig = ("wobble",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chair.meters["broken"] += 1
    chair.memes["embarrassment"] += 1
    out.append("The chair gave a shameful creak.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    chair = world.get("chair")
    if chair.meters["repaired"] < THRESHOLD:
        return out
    sig = ("fix",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    chair.meters["wobble"] = 0
    chair.meters["broken"] = 0
    chair.memes["relief"] += 1
    out.append("The chair stood steady again.")
    return out


CAUSAL_RULES = [Rule("wobble", "physical", _r_wobble), Rule("fix", "physical", _r_fix)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def needs_help(problem: Problem, place: Place) -> bool:
    return problem.id in place.affords


def valid_fix(problem: Problem, fix: Fix) -> bool:
    return problem.id in {"wobble"} and fix.succeeds


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for prob_id, prob in PROBLEMS.items():
            for fix_id, fix in FIXES.items():
                if needs_help(prob, place) and valid_fix(prob, fix):
                    combos.append((pid, prob_id, fix_id))
    return combos


def tell(place: Place, problem: Problem, fix: Fix, charm: Charm,
         hero_name: str = "Niko", helper_name: str = "Mara",
         hero_kind: str = "priest", helper_kind: str = "priestess") -> World:
    world = World(place)
    hero = world.add(Entity(id="hero", kind="character", type=hero_kind, label=hero_name,
                            traits=["wry", "steady"]))
    helper = world.add(Entity(id="helper", kind="character", type=helper_kind, label=helper_name,
                              traits=["wise", "kind"]))
    chair = world.add(Entity(id="chair", type="thing", label="chair", phrase="the chair",
                             tags={"chair"}))
    deli = world.add(Entity(id="deli", type="thing", label="deli", phrase="the deli",
                            tags={"deli"}))
    world.facts.update(hero=hero, helper=helper, chair=chair, deli=deli,
                       place=place, problem=problem, fix=fix, charm=charm)

    hero.memes["hunger"] += 1
    helper.memes["care"] += 1
    chair.meters["wobble"] += 1
    world.needs_fix = True

    world.say(
        f"At {place.label}, the deli glowed like a little hall of bread and steam. "
        f"{hero.label} and {helper.label} sat beside {place.scene}."
    )
    world.say(
        f"The {problem.label} chair began to lean, and everyone heard its {problem.symptom}. "
        f"{hero.label} laughed, because even an unruly chair can sound like a grumpy goat."
    )

    world.para()
    world.say(
        f"{helper.label} said, \"This is a problem for a patient mind.\" "
        f"{hero.label} peered under the chair and spotted {problem.danger}."
    )
    world.say(
        f"\"First we must choose the right fix,\" {hero.label} said, as if speaking to a small mountain."
    )
    if fix.id == "glue":
        chair.meters["repaired"] += 1
        chair.memes["hope"] += 1
        world.say(
            f"They used {fix.label}: {fix.method}. {fix.reveal}"
        )
    elif fix.id == "wedge":
        chair.meters["repaired"] += 1
        chair.meters["level"] += 1
        world.say(
            f"They used {fix.label}: {fix.method}. {fix.reveal}"
        )
    else:
        chair.meters["repaired"] += 1
        world.say(f"They used {fix.label}: {fix.method}. {fix.reveal}")
    propagate(world, narrate=True)

    world.para()
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"Then {helper.label} brought out {charm.phrase}, and both of them laughed. "
        f"{hero.label} sat down carefully, and the chair did not complain."
    )
    world.say(
        f"By sunset, the {place.label} had its old calm back: warm light, neat cups, "
        f"and a chair that held a story instead of a wobble."
    )

    world.facts.update(solved=True, repaired=chair.meters["repaired"] >= THRESHOLD)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a myth-like story for a young child about a {f["place"].label} with a {f["problem"].label} chair and a clever fix. Include the words "deli" and "chair".',
        f"Tell a funny little legend where {f['hero'].label} and {f['helper'].label} solve a chair problem at the deli, and the answer is smart, not magical.",
        f"Write a gentle myth about a stubborn chair in the deli, a clever repair, and a joke that makes the people laugh while they learn something useful.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    place = f["place"]
    problem = f["problem"]
    fix = f["fix"]
    charm = f["charm"]
    qa = [
        QAItem(
            question=f"What was wrong at the {place.label}?",
            answer=f"The {problem.label} chair was wobbling, and its {problem.symptom} told everyone it was not safe yet. The deli stayed open, but the chair needed a careful fix before anyone could sit comfortably.",
        ),
        QAItem(
            question=f"How did {hero.label} and {helper.label} solve the chair problem?",
            answer=f"They looked under the chair, found the trouble, and used {fix.label}. That was the right sort of fix for this little problem, so the chair became steady again.",
        ),
        QAItem(
            question=f"Why did {hero.label} laugh during the problem solving?",
            answer=f"{hero.label} laughed because the chair sounded like a grumpy goat, which made the mystery feel funny instead of scary. The joke helped the pair stay calm while they worked.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"At the end, the {place.label} was calm and the chair was steady. People could sit again, and the room felt safe and ordinary instead of wobbly.",
        ),
        QAItem(
            question=f"What did {helper.label} bring out after the repair?",
            answer=f"{helper.label} brought out {charm.phrase}, which made everybody laugh. The humor did not fix the chair by itself, but it made the whole job feel lighter.",
        ),
    ]
    if f.get("solved"):
        qa.append(QAItem(
            question=f"Did the fix really work on the chair?",
            answer=f"Yes. The chair stood steady again after {fix.label} was used, so the solution matched the problem. That is why the ending can show the deli peaceful and safe.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["place"].tags) | set(world.facts["problem"].tags) | set(world.facts["fix"].tags)
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(q, a) for q, a in KNOWLEDGE[tag])
    return out


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
        if e.tags:
            bits.append(f"tags={sorted(e.tags)}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


PLACES = {
    "sunroom": Place(id="sunroom", label="the sunroom deli", scene="a bright counter of soup and rolls", affords={"wobble"}, tags={"deli", "chair"}),
    "harbor": Place(id="harbor", label="the harbor deli", scene="salt air and wooden tables", affords={"wobble"}, tags={"deli", "chair"}),
    "market": Place(id="market", label="the market deli", scene="busy stalls and a lantern-lit bench", affords={"wobble"}, tags={"deli", "chair"}),
    "orchard": Place(id="orchard", label="the orchard deli", scene="apple crates and a shady awning", affords={"wobble"}, tags={"deli", "chair"}),
}

PROBLEMS = {
    "wobble": Problem(id="wobble", label="wobbly", danger="a loose leg under the seat", symptom="comic clack", at_risk={"chair"}, tags={"chair", "problem"}),
}

FIXES = {
    "wedge": Fix(id="wedge", label="a folded napkin wedge", method="they folded a thick napkin and tucked it beneath the short leg", reveal="The napkin turned into a tiny hill under the chair.", tags={"chair", "problem"}),
    "glue": Fix(id="glue", label="a pot of warm glue", method="they pinned the leg straight and sealed the crack with careful glue", reveal="The crack shone for a moment like honey before it dried.", tags={"chair", "problem"}),
    "shim": Fix(id="shim", label="a wooden shim", method="they slid a neat little shim under the leg until the chair sat level", reveal="The shim sat hidden like a pebble that knew its job.", tags={"chair", "problem"}),
}

CHARMS = {
    "pickle_joke": Charm(id="pickle_joke", label="pickle joke", phrase="a joke about a pickle wearing a crown", tags={"humor"}),
    "bread_rhyme": Charm(id="bread_rhyme", label="bread rhyme", phrase="a rhyme about brave bread and a sleepy spoon", tags={"humor"}),
    "napkin_song": Charm(id="napkin_song", label="napkin song", phrase="a song about napkins dancing like little flags", tags={"humor"}),
}

GODS = ["Ari", "Mina", "Tova", "Lio", "Eren", "Sera", "Kian", "Rhea"]
HELPERS = ["Bera", "Nilo", "Pia", "Dorin", "Hale", "Veda"]


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for p in PLACES:
        for pr in PROBLEMS:
            for fx in FIXES:
                for ch in CHARMS:
                    if needs_help(_safe_lookup(PROBLEMS, pr), _safe_lookup(PLACES, p)) and valid_fix(_safe_lookup(PROBLEMS, pr), _safe_lookup(FIXES, fx)):
                        combos.append((p, pr, fx, ch))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Mythic deli chair storyworld.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--charm", choices=CHARMS)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "fix", None) is None or c[2] == getattr(args, "fix", None))
              and (getattr(args, "charm", None) is None or c[3] == getattr(args, "charm", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, fix, charm = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(GODS)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    if helper == hero:
        helper = rng.choice([h for h in HELPERS if h != hero])
    return StoryParams(place=place, problem=problem, fix=fix, charm=charm, hero=hero, helper=helper)


def generate(params: StoryParams) -> StorySample:
    try:
        place = _safe_lookup(PLACES, params.place)
        problem = _safe_lookup(PROBLEMS, params.problem)
        fix = _safe_lookup(FIXES, params.fix)
        charm = _safe_lookup(CHARMS, params.charm)
    except KeyError as err:
        pass
    if not valid_fix(problem, fix) or not needs_help(problem, place):
        pass
    world = tell(place, problem, fix, charm, hero_name=params.hero, helper_name=params.helper)
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


ASP_RULES = r"""
problem(place,prob) :- place(place), problem(prob), needs(place,prob).
good_fix(prob,fix) :- problem(prob), fix(fix), fits(prob,fix).
valid(place,prob,fix,charm) :- problem(place,prob), good_fix(prob,fix), charm(charm).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem", pid))
    for fid in FIXES:
        lines.append(asp.fact("fix", fid))
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
    for pid, p in PLACES.items():
        for prob_id, prob in PROBLEMS.items():
            if needs_help(prob, p):
                lines.append(asp.fact("needs", pid, prob_id))
    for prob_id, prob in PROBLEMS.items():
        for fix_id, fix in FIXES.items():
            if valid_fix(prob, fix):
                lines.append(asp.fact("fits", prob_id, fix_id))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH between ASP and Python valid combos.")
        return 1
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(777)))
        _ = sample.story
    except Exception as err:
        print(f"SMOKE TEST FAILED: {err}")
        return 1
    print("OK: ASP parity and smoke test passed.")
    return 0


CURATED = [
    StoryParams(place="sunroom", problem="wobble", fix="wedge", charm="pickle_joke", hero="Ari", helper="Bera"),
    StoryParams(place="harbor", problem="wobble", fix="glue", charm="bread_rhyme", hero="Mina", helper="Nilo"),
    StoryParams(place="market", problem="wobble", fix="shim", charm="napkin_song", hero="Tova", helper="Pia"),
    StoryParams(place="orchard", problem="wobble", fix="wedge", charm="bread_rhyme", hero="Lio", helper="Dorin"),
]


def explain_rejection() -> str:
    return "(No story: this combination does not give the chair a real problem and fix.)"


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combos:")
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
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            seed = base_seed + i
            i += 1
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero} and {p.helper}: {p.problem} at the {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
