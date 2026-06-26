#!/usr/bin/env python3
"""
storyworlds/worlds/skeletal_challenge_teamwork_slice_of_life.py
===============================================================

A small slice-of-life storyworld about a modest challenge, a skeletal
half-finished thing, and the teamwork that helps it become whole.

The seed image is simple:
---
A child and a helper arrive at a quiet place with a skeletal project that is
almost, but not quite, ready. The project is light, fragile, and awkward. By
working together carefully, they steady it, fix the trouble, and end the day
with a useful thing that stands up straight.

This world keeps the action small and concrete:
- a place for the everyday scene
- a skeletal object made of a bare frame
- a challenge that creates a specific problem
- a teamwork solution that uses a shared tool or steady hands
- a final image proving the change
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    held_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    project: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoors: bool
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
class Challenge:
    id: str
    name: str
    verb: str
    difficulty: str
    wobble: str
    fix: str
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
class Project:
    id: str
    label: str
    phrase: str
    region: str
    fragile: bool = True
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


@dataclass
class Tool:
    id: str
    label: str
    use: str
    helps: set[str]
    holds: set[str]
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.problem: str = ""

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.problem = self.problem
        return clone


def _r_unsteady(world: World) -> list[str]:
    out: list[str] = []
    for project in [e for e in world.entities.values() if e.type == "project"]:
        if project.meters.get("steady", 0.0) >= THRESHOLD:
            continue
        for char in world.characters():
            if char.memes.get("focus", 0.0) < THRESHOLD:
                continue
            sig = ("unsteady", project.id, char.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            project.meters["wobble"] = project.meters.get("wobble", 0.0) + 1
            out.append(f"The {project.label} wobbled in {char.pronoun('possessive')} hands.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    chars = world.characters()
    if len(chars) < 2:
        return out
    if not any(c.memes.get("help", 0.0) >= THRESHOLD for c in chars):
        return out
    project = next((e for e in world.entities.values() if e.type == "project"), None)
    if not project:
        return out
    sig = ("teamwork", project.id)
    if sig in world.fired:
        return out
    if project.meters.get("wobble", 0.0) < THRESHOLD:
        return out
    world.fired.add(sig)
    project.meters["steady"] = 1.0
    project.meters["wobble"] = 0.0
    out.append("Together, they steadied it.")
    return out


CAUSAL_RULES = [_r_unsteady, _r_teamwork]


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


def predict_outcome(world: World, hero: Entity, helper: Entity, challenge: Challenge, project_id: str) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["focus"] = 1.0
    sim.get(helper.id).memes["help"] = 1.0
    sim.problem = challenge.id
    do_challenge(sim, sim.get(hero.id), sim.get(helper.id), narrate=False)
    project = sim.get(project_id)
    return {
        "steady": project.meters.get("steady", 0.0) >= THRESHOLD,
        "wobble": project.meters.get("wobble", 0.0),
    }


def do_challenge(world: World, hero: Entity, helper: Entity, narrate: bool = True) -> None:
    challenge: Challenge = _safe_fact(world, world.facts, "challenge")
    project: Entity = _safe_fact(world, world.facts, "project")
    world.problem = challenge.id
    hero.memes["focus"] = hero.memes.get("focus", 0.0) + 1
    helper.memes["help"] = helper.memes.get("help", 0.0) + 1
    project.meters["wobble"] = project.meters.get("wobble", 0.0) + 1
    if narrate:
        world.say(
            f"At {world.setting.place}, {hero.id} and {helper.id} tried to {challenge.verb} "
            f"the {project.label}, but the frame felt {challenge.difficulty} and {challenge.wobble}."
        )
    propagate(world, narrate=narrate)


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "careful")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who liked quiet projects."
    )
    world.say(
        f"{helper.id} was the kind of helper who noticed when small things needed a hand."
    )


def setup(world: World, hero: Entity, helper: Entity, project: Entity) -> None:
    world.say(
        f"On the table sat {project.phrase}, a skeletal little frame that was almost ready."
    )
    world.say(
        f"{hero.id} wanted to finish it, but the last pieces kept leaning the wrong way."
    )


def worry(world: World, hero: Entity, helper: Entity, challenge: Challenge, project: Entity) -> None:
    prediction = predict_outcome(world, hero, helper, challenge, project.id)
    if prediction["steady"]:
        world.facts["predicted"] = "steady"
    else:
        world.facts["predicted"] = "wobble"
    world.say(
        f"{helper.id} looked at the challenge and said it needed patient hands, not fast ones."
    )
    world.say(
        f"So they slowed down, lined up the edges, and got ready to try again."
    )


def resolve(world: World, hero: Entity, helper: Entity, project: Entity, tool: Tool) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    helper.memes["joy"] = helper.memes.get("joy", 0.0) + 1
    project.meters["steady"] = 1.0
    world.say(
        f"{hero.id} held one side while {helper.id} used {tool.label} to {tool.use}."
    )
    world.say(
        f"With both of them working together, the {project.label} stood up straight at last."
    )
    world.say(
        f"By the end, the skeletal frame was no longer a problem. It was a finished little thing for an ordinary day."
    )


SETTINGS = {
    "kitchen": Setting(place="the kitchen table", indoors=True, affords={"assemble"}),
    "porch": Setting(place="the porch", indoors=False, affords={"assemble"}),
    "workshop": Setting(place="the tiny workshop", indoors=True, affords={"assemble"}),
}

CHALLENGES = {
    "assemble": Challenge(
        id="assemble",
        name="assembly challenge",
        verb="assemble",
        difficulty="careful",
        wobble="a little shaky",
        fix="steady it together",
        keyword="challenge",
        tags={"challenge", "teamwork"},
    ),
}

PROJECTS = {
    "frame": Project(
        id="frame",
        label="skeletal frame",
        phrase="a skeletal frame with a few loose joints",
        region="hands",
    ),
    "rack": Project(
        id="rack",
        label="skeletal rack",
        phrase="a skeletal rack made of thin slats",
        region="hands",
    ),
}

TOOLS = {
    "tape": Tool(
        id="tape",
        label="masking tape",
        use="hold the corners in place",
        helps={"assemble"},
        holds={"frame", "rack"},
    ),
    "clamp": Tool(
        id="clamp",
        label="a small clamp",
        use="pin the pieces together",
        helps={"assemble"},
        holds={"frame", "rack"},
    ),
}

GIRL_NAMES = ["Mia", "Luna", "Tess", "Nora", "Ivy", "June"]
BOY_NAMES = ["Eli", "Noah", "Sam", "Theo", "Max", "Finn"]
HELPER_NAMES = ["Aunt May", "Uncle Ray", "Mr. Park", "Ms. Green", "Ben"]
TRAITS = ["patient", "curious", "quiet", "cheerful", "steady"]


@dataclass
class StoryParams:
    place: str
    challenge: str
    project: str
    name: str
    gender: str
    helper: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld: skeletal challenge teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--challenge", choices=CHALLENGES)
    ap.add_argument("--project", choices=PROJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    challenge = getattr(args, "challenge", None) or "assemble"
    project = getattr(args, "project", None) or rng.choice(list(PROJECTS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPER_NAMES)
    trait = rng.choice(TRAITS)
    if place not in SETTINGS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if challenge not in CHALLENGES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if project not in PROJECTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(place=place, challenge=challenge, project=project, name=name, gender=gender, helper=helper, trait=trait)


def introduce_world(world: World, hero: Entity, helper: Entity, project: Entity) -> None:
    introduce(world, hero, helper)
    world.para()
    setup(world, hero, helper, project)


def tell_story(params: StoryParams) -> StorySample:
    world = World(_safe_lookup(SETTINGS, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, traits=["little", params.trait]))
    helper = world.add(Entity(id="Helper", kind="character", type="person", label=params.helper))
    project = world.add(Entity(
        id="project",
        kind="thing",
        type="project",
        label=_safe_lookup(PROJECTS, params.project).label,
        phrase=_safe_lookup(PROJECTS, params.project).phrase,
    ))
    tool = world.add(Entity(id="tool", kind="thing", type="tool", label="masking tape"))

    world.facts.update(
        hero=hero,
        helper=helper,
        project=project,
        challenge=_safe_lookup(CHALLENGES, params.challenge),
        tool=TOOL_BY_PROJECT[params.project],
    )

    introduce_world(world, hero, helper, project)
    world.para()
    worry(world, hero, helper, _safe_lookup(CHALLENGES, params.challenge), project)
    world.para()
    resolve(world, hero, helper, project, TOOL_BY_PROJECT[params.project])
    return world


TOOL_BY_PROJECT = {
    "frame": TOOLS["tape"],
    "rack": TOOLS["clamp"],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    challenge = _safe_fact(world, f, "challenge")
    project = _safe_fact(world, f, "project")
    return [
        f'Write a short slice-of-life story about a "{challenge.keyword}" and a skeletal project at {world.setting.place}.',
        f"Tell a gentle story where {hero.id} and {helper.label} work together to {challenge.verb} the {project.label}.",
        f"Write a simple story that includes the word \"skeletal\" and ends with teamwork making the project stand up straight.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    project = _safe_fact(world, f, "project")
    challenge = _safe_fact(world, f, "challenge")
    place = world.setting.place
    return [
        QAItem(
            question=f"What did {hero.id} and {helper.label} try to do at {place}?",
            answer=f"They tried to {challenge.verb} the {project.label} at {place}.",
        ),
        QAItem(
            question=f"Why was the {project.label} hard to finish?",
            answer=f"It was still skeletal and a little shaky, so it needed careful teamwork to stay steady.",
        ),
        QAItem(
            question=f"What helped the {project.label} become finished?",
            answer=f"{hero.id} and {helper.label} worked together and used masking tape to hold the pieces in place.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does teamwork mean?",
            answer="Teamwork means people help one another and use their different strengths to do something together.",
        ),
        QAItem(
            question="What does skeletal mean here?",
            answer="Skeletal means something is bare or frame-like, with only the thin main pieces in place.",
        ),
        QAItem(
            question="Why can tape help with a small project?",
            answer="Tape can hold pieces together for a while so they do not slide apart while you finish the work.",
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
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: {e.type} {' '.join(parts)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid_story/5.

valid_story(Place, Challenge, Project, Gender, Tool) :-
    place(Place), challenge(Challenge), project(Project), gender(Gender), tool(Tool),
    affords(Place, Challenge),
    solves(Tool, Project, Challenge).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for cid, c in CHALLENGES.items():
        lines.append(asp.fact("challenge", cid))
    for pid, p in PROJECTS.items():
        lines.append(asp.fact("project", pid))
    for gid in ["girl", "boy"]:
        lines.append(asp.fact("gender", gid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.holds):
            lines.append(asp.fact("solves", tid, h, "assemble"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program("#show valid_story/5."))
    atoms = sorted(set(asp.atoms(model, "valid_story")))
    py = sorted(
        (place, "assemble", project, gender, tool)
        for place in SETTINGS
        for project in PROJECTS
        for gender in ["girl", "boy"]
        for tool in TOOLS
        if place in SETTINGS and "assemble" in _safe_lookup(SETTINGS, place).affords
    )
    if atoms == py:
        print(f"OK: ASP matches Python gate ({len(atoms)} combinations).")
        return 0
    print("Mismatch between ASP and Python.")
    print("ASP:", atoms)
    print("PY :", py)
    return 1


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
    world = tell_story(params)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


CURATED = [
    StoryParams(place="kitchen", challenge="assemble", project="frame", name="Mia", gender="girl", helper="Aunt May", trait="patient"),
    StoryParams(place="porch", challenge="assemble", project="rack", name="Eli", gender="boy", helper="Mr. Park", trait="quiet"),
    StoryParams(place="workshop", challenge="assemble", project="frame", name="Nora", gender="girl", helper="Ms. Green", trait="curious"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/5."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import storyworlds.asp as asp
        model = asp.one_model(asp_program("#show valid_story/5."))
        combos = sorted(set(asp.atoms(model, "valid_story")))
        for combo in combos:
            print(combo)
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
            header = f"### {p.name}: {p.project} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
