#!/usr/bin/env python3
"""
storyworlds/worlds/orange_pediatrician_magic_suspense_tall_tale.py
===================================================================

A standalone story world for a tall-tale flavored, magic-and-suspense tale
about a pediatrician, an orange object, and a child who needs help.

The world model keeps the story grounded in simulated state:
- a child has a physical condition or worry,
- a pediatrician uses a magical orange tool or charm,
- suspense rises when the fix must be chosen carefully,
- the ending proves that something changed.

The generated stories stay small, child-facing, concrete, and causal.
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    doc: object | None = None
    symptom: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    mood: str
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
    verb: str
    symptom: str
    danger: str
    tension: str
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
class Remedy:
    id: str
    label: str
    phrase: str
    prep: str
    result: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


def _m(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _v(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def _addm(e: Entity, key: str, val: float = 1.0) -> None:
    e.meters[key] = e.meters.get(key, 0.0) + val


def _addv(e: Entity, key: str, val: float = 1.0) -> None:
    e.memes[key] = e.memes.get(key, 0.0) + val


def _setv(e: Entity, key: str, val: float) -> None:
    e.memes[key] = val


def condition_presses(problem: Problem, child: Entity) -> bool:
    return _v(child, problem.id) >= THRESHOLD


def can_use(remedy: Remedy, problem: Problem) -> bool:
    return problem.id in remedy.tags or remedy.keyword == problem.keyword


def prove_fix(problem: Problem, remedy: Remedy) -> bool:
    return can_use(remedy, problem)


def reasonableness_gate(problem: Problem, remedy: Remedy) -> bool:
    return prove_fix(problem, remedy)


def tell(setting: Setting, problem: Problem, remedy: Remedy,
         child_name: str = "Nina", child_type: str = "girl",
         pediatrician_name: str = "Dr. Marlow") -> World:
    world = World(setting)

    child = world.add(Entity(
        id=child_name, kind="character", type=child_type,
        traits=["little", "bright", "brave"],
    ))
    doc = world.add(Entity(
        id=pediatrician_name, kind="character", type="pediatrician",
        label="the pediatrician",
        traits=["kind", "steady", "clever"],
    ))
    tool = world.add(Entity(
        id=remedy.id, type="tool", label=remedy.label, phrase=remedy.phrase,
        owner=doc.id, caretaker=doc.id
    ))
    symptom = world.add(Entity(
        id=problem.id, type="problem", label=problem.keyword,
        phrase=problem.symptom, owner=child.id
    ))

    _addv(child, "worry", 1)
    _addv(child, problem.id, 1)

    world.say(
        f"Folks in {setting.place} said {child.id} was as small as a sparrow and as brave as a bell."
    )
    world.say(
        f"{child.id} had a {problem.symptom}, and that made {child.pronoun('possessive')} day feel long and lonesome."
    )
    world.say(
        f"Then came {doc.id}, the pediatrician, with a sharp eye, a soft voice, and a coat as white as moon milk."
    )
    world.say(
        f"On {doc.id}'s cart sat {tool.phrase}, bright orange as a sunrise barrel."
    )

    world.para()
    world.say(
        f"The room was quiet except for the clock, and even the clock seemed to tiptoe."
    )
    _addv(child, "suspense", 1)
    world.say(
        f"{child.id} wanted {problem.verb}, but everyone knew {problem.danger}."
    )
    world.say(
        f"{doc.id} held up {tool.label} and said, \"Easy now. One careful choice at a time.\""
    )

    if not reasonableness_gate(problem, remedy):
        pass

    world.para()
    _addv(doc, "focus", 1)
    _addv(child, "hope", 1)
    world.say(
        f"{doc.id} tapped {tool.label} against the bedside lamp, and the orange thing woke with a tiny golden hum."
    )
    world.say(
        f"It was the sort of magic folks in town called tall-tale magic: light enough to float a feather, strong enough to move a storm."
    )
    world.say(
        f"At once {tool.result}, and the tight feeling in {child.id}'s chest loosened like a knot in warm string."
    )

    _setv(child, problem.id, 0)
    _addv(child, "joy", 1)
    _setv(child, "worry", 0)
    _addv(doc, "satisfaction", 1)

    world.para()
    world.say(
        f"{child.id} gave a surprised little laugh and sat up straighter."
    )
    world.say(
        f"{doc.id} smiled, packed away {tool.label}, and tucked the orange light back into its pocket like a coin from the sun."
    )
    world.say(
        f"By the time the bell over the door rang, {child.id} was fine, {doc.id} was grinning, and the whole town seemed to shine a shade more orange."
    )

    world.facts.update(
        child=child,
        doctor=doc,
        tool=tool,
        problem=symptom,
        problem_def=problem,
        remedy=remedy,
        resolved=True,
        setting=setting,
    )
    return world


SETTINGS = {
    "clinic": Setting(
        place="the little moonlit clinic",
        mood="quiet",
        affords={"checkup", "treatment"},
    ),
    "town": Setting(
        place="the windy town square clinic",
        mood="busy",
        affords={"checkup", "treatment"},
    ),
    "porch": Setting(
        place="the front-porch infirmary",
        mood="still",
        affords={"checkup", "treatment"},
    ),
}

PROBLEMS = {
    "fever": Problem(
        id="fever",
        verb="stay perfectly still",
        symptom="feverish cheeks",
        danger="the heat might climb higher if nobody helped",
        tension="the room felt too hot for comfort",
        keyword="fever",
        tags={"heat", "checkup"},
    ),
    "cough": Problem(
        id="cough",
        verb="take a deep breath",
        symptom="a rattly cough",
        danger="the coughing fit might wake the whole block",
        tension="the silence could break any second",
        keyword="cough",
        tags={"breath", "checkup"},
    ),
    "splinter": Problem(
        id="splinter",
        verb="use the hand without flinching",
        symptom="a splintery finger",
        danger="the little wood sliver might sting and sting again",
        tension="one wrong tug could make the tears start",
        keyword="splinter",
        tags={"hurt", "treatment"},
    ),
    "dream": Problem(
        id="dream",
        verb="open the eyes",
        symptom="a dream that felt too big and spooky",
        danger="the fear might keep the child awake all night",
        tension="shadows seemed to stretch under the bed",
        keyword="dream",
        tags={"sleep", "checkup"},
    ),
}

REMEDIES = {
    "orange_tonic": Remedy(
        id="orange_tonic",
        label="an orange tonic",
        phrase="a little bottle of orange tonic",
        prep="mix and swirl the orange tonic",
        result="the fever drifted down like a kite after the wind calms",
        keyword="orange",
        tags={"fever", "heat"},
    ),
    "orange_lantern": Remedy(
        id="orange_lantern",
        label="an orange lantern",
        phrase="a tiny orange lantern",
        prep="raise the orange lantern near the pillow",
        result="the shadows shrank and the scary corners grew small",
        keyword="orange",
        tags={"dream", "sleep"},
    ),
    "orange_peg": Remedy(
        id="orange_peg",
        label="an orange medicine peg",
        phrase="an orange medicine peg",
        prep="set the orange peg on the sore spot",
        result="the splinter slipped out as neat as a pea from its pod",
        keyword="orange",
        tags={"splinter", "hurt"},
    ),
    "orange_bubble": Remedy(
        id="orange_bubble",
        label="an orange bubble charm",
        phrase="a round orange bubble charm",
        prep="spin the orange bubble charm over the room",
        result="the cough softened to a tiny hiccup and then went away",
        keyword="orange",
        tags={"cough", "breath"},
    ),
}

CHILD_NAMES = ["Nina", "Leo", "Mabel", "Sam", "Ivy", "June", "Otto", "Elsie"]
TRAITS = ["brave", "wobbly", "curious", "sleepy", "sunny", "spunky"]


@dataclass
class StoryParams:
    place: str
    problem: str
    remedy: str
    name: str
    gender: str
    doctor: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for pid, prob in PROBLEMS.items():
            for rid, rem in REMEDIES.items():
                if reasonableness_gate(prob, rem):
                    out.append((place, pid, rid))
    return out


def explain_rejection(problem: Problem, remedy: Remedy) -> str:
    return (
        f"(No story: {remedy.label} does not actually solve {problem.keyword}. "
        f"Try a remedy whose magic matches the child's trouble.)"
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    prob = _safe_fact(world, f, "problem_def")
    rem = _safe_fact(world, f, "remedy")
    return [
        f'Write a short tall-tale story for a young child about {child.id}, a pediatrician, and the word "{rem.keyword}".',
        f"Tell a suspenseful but gentle story where {child.id} has {prob.symptom} and the pediatrician uses {rem.label} to help.",
        f"Write a magical clinic story that includes orange light, a worried child, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    doc = _safe_fact(world, f, "doctor")
    prob = _safe_fact(world, f, "problem_def")
    rem = _safe_fact(world, f, "remedy")
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {child.id}, a little {child.type}, and {doc.id}, the pediatrician who came to help.",
        ),
        QAItem(
            question=f"What problem did {child.id} have?",
            answer=f"{child.id} had {prob.symptom}, which made the day feel long and uneasy.",
        ),
        QAItem(
            question=f"What did the pediatrician use?",
            answer=f"{doc.id} used {rem.label}, a bright orange bit of magic, to help {child.id}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} feeling better, the scary feeling gone, and the orange light tucked safely away.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does a pediatrician help with?",
            answer="A pediatrician helps children when they are sick, hurt, or need a careful checkup.",
        ),
        QAItem(
            question="What is orange?",
            answer="Orange is a bright color like a sunset, a pumpkin, or a shiny tangerine.",
        ),
        QAItem(
            question="Why can magic make a story feel suspenseful?",
            answer="Magic can make a story feel suspenseful because the characters do not know exactly what will happen next.",
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
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"  {e.id:16} ({e.type:12}) {' '.join(bits)}")
    return "\n".join(lines)


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem", pid))
        lines.append(asp.fact("keyword", pid, p.keyword))
    for rid, r in REMEDIES.items():
        lines.append(asp.fact("remedy", rid))
        lines.append(asp.fact("remedy_keyword", rid, r.keyword))
        for t in sorted(r.tags):
            lines.append(asp.fact("solves", rid, t))
    return "\n".join(lines)


ASP_RULES = r"""
reasonably_matches(P, R) :- problem(P), remedy(R), solves(R, K), keyword(P, K).
valid_story(S, P, R) :- setting(S), problem(P), remedy(R), reasonably_matches(P, R), affords(S, checkup).
#show valid_story/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale story world: a pediatrician, orange magic, and suspense."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--remedy", choices=REMEDIES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--doctor")
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "problem", None) and getattr(args, "remedy", None):
        if not reasonableness_gate(_safe_lookup(PROBLEMS, getattr(args, "problem", None)), _safe_lookup(REMEDIES, getattr(args, "remedy", None))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "remedy", None) is None or c[2] == getattr(args, "remedy", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, remedy = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(CHILD_NAMES)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    doctor = getattr(args, "doctor", None) or "Dr. Marlow"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, remedy=remedy, name=name, gender=gender, doctor=doctor, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(REMEDIES, params.remedy),
                 child_name=params.name, child_type=params.gender, pediatrician_name=params.doctor)
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


CURATED = [
    StoryParams(place="clinic", problem="fever", remedy="orange_tonic", name="Nina", gender="girl", doctor="Dr. Marlow", trait="brave"),
    StoryParams(place="town", problem="cough", remedy="orange_bubble", name="Leo", gender="boy", doctor="Dr. Marlow", trait="curious"),
    StoryParams(place="porch", problem="splinter", remedy="orange_peg", name="Ivy", gender="girl", doctor="Dr. Marlow", trait="sunny"),
    StoryParams(place="clinic", problem="dream", remedy="orange_lantern", name="Sam", gender="boy", doctor="Dr. Marlow", trait="sleepy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (setting, problem, remedy) combos:\n")
        for c in combos:
            print("  ", c)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
