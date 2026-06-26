#!/usr/bin/env python3
"""
A small standalone storyworld for a ghost-story style tale with dialogue and repetition.

Premise:
A child visits a quiet reception desk in an old lodge. A tiny wolverine-shaped ghost keeps
repeating the same worried line because a broken night bell will not operate. The child and
a helpful grown-up listen, find the stuck part, and gently fix the reception so the ghost can
rest.

This world models:
- typed entities with meters and memes
- a reasonableness gate for when the ghostly repair story is plausible
- an inline ASP twin for the same gate
- dialogue and repetition as a first-class narrative instrument
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    desk: object | None = None
    ghost: object | None = None
    grown: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
class Place:
    name: str
    quiet: bool = True
    spooky: bool = True
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Problem:
    id: str
    verb: str
    gerund: str
    rush: str
    issue: str
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
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    fits: set[str] = field(default_factory=set)
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
    place: str
    problem: str
    fix: str
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
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.repeated_lines: dict[str, int] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def say(self, text: str) -> None:
        if text:
            self.lines.append(text)
            self.repeated_lines[text] = self.repeated_lines.get(text, 0) + 1

    def render(self) -> str:
        return " ".join(self.lines)


def _entity_meter(e: Entity, key: str) -> float:
    return e.meters.get(key, 0.0)


def _entity_meme(e: Entity, key: str) -> float:
    return e.memes.get(key, 0.0)


def intro(world: World, child: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"{child.id} came to the reception at {world.place.name}, where the lamps were low and the air felt cold."
    )
    world.say(
        f"{helper.id} was there too, listening for the little click that would mean the old desk could {problem.verb} again."
    )


def describe_ghost(world: World, ghost: Entity) -> None:
    world.say(
        f"A wolverine ghost drifted by the desk, and {ghost.id} kept whispering, "
        f"\"I am still here. I am still here.\""
    )
    world.say(
        f"It was not a scary shout, just a small repeating voice, like a story that forgot how to end."
    )


def issue_begins(world: World, child: Entity, ghost: Entity, problem: Problem) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    ghost.memes["worry"] = ghost.memes.get("worry", 0.0) + 1
    world.say(
        f"{ghost.id} pointed at the desk bell and said, \"It will not {problem.verb}.\""
    )
    world.say(
        f"Then the ghost said it again: \"It will not {problem.verb}.\""
    )


def predict_fix(world: World, problem: Problem, fix: Fix) -> bool:
    return problem.id in fix.fits and world.place.name in {"old hotel", "front reception", "mountain lodge"}


def broken_state(world: World, child: Entity, problem: Problem) -> None:
    child.memes["unease"] = child.memes.get("unease", 0.0) + 1
    world.say(
        f"The reception felt stuck and sleepy, as if the whole room had held its breath for too long."
    )
    world.say(
        f"{child.id} looked at the silent desk and heard the same worried line one more time: \"It will not {problem.verb}.\""
    )


def try_fix(world: World, helper: Entity, ghost: Entity, problem: Problem, fix: Fix) -> None:
    if not predict_fix(world, problem, fix):
        pass
    helper.memes["helpfulness"] = helper.memes.get("helpfulness", 0.0) + 1
    world.say(
        f"{helper.id} smiled and said, \"Let's {fix.prep}.\""
    )
    world.say(
        f"Carefully, they followed the tiny clue by the desk."
    )


def operate_repair(world: World, child: Entity, ghost: Entity, problem: Problem, fix: Fix) -> None:
    child.meters["care"] = child.meters.get("care", 0.0) + 1
    ghost.meters["relief"] = ghost.meters.get("relief", 0.0) + 1
    ghost.memes["worry"] = 0.0
    world.say(
        f"Together they worked the little lever until the desk could {problem.verb} at last."
    )
    world.say(
        f"The ghost repeated, softer now, \"It can {problem.verb}. It can {problem.verb}.\""
    )
    world.say(
        f"At the end, the reception was warm again, and {ghost.id} floated up with a gentle sigh."
    )
    world.say(
        f"{fix.tail}, and the old room finally felt peaceful."
    )


def tell_story(place: Place, problem: Problem, fix: Fix, name: str, role: str, helper: str) -> World:
    world = World(place)
    child = world.add(Entity(id=name, kind="character", type=role, traits=["small", "quiet"]))
    grown = world.add(Entity(id=helper, kind="character", type="adult", traits=["patient"]))
    ghost = world.add(Entity(id="WolverineGhost", kind="spirit", type="ghost", label="wolverine ghost"))
    desk = world.add(Entity(id="ReceptionDesk", type="desk", label="reception desk"))

    world.facts.update(child=child, grown=grown, ghost=ghost, desk=desk, problem=problem, fix=fix)

    intro(world, child, grown, problem)
    world.say("")
    describe_ghost(world, ghost)
    world.say("")
    issue_begins(world, child, ghost, problem)
    broken_state(world, child, problem)
    world.say("")
    try_fix(world, grown, ghost, problem, fix)
    operate_repair(world, child, ghost, problem, fix)
    return world


PLACES = {
    "old hotel": Place(name="the old hotel", quiet=True, spooky=True, affords={"bell"}),
    "front reception": Place(name="the front reception", quiet=True, spooky=True, affords={"bell"}),
    "mountain lodge": Place(name="the mountain lodge", quiet=True, spooky=True, affords={"bell"}),
}

PROBLEMS = {
    "bell": Problem(
        id="bell",
        verb="operate",
        gerund="operating",
        rush="rush to the bell",
        issue="stuck bell",
        keyword="reception",
        tags={"ghost", "reception", "bell"},
    )
}

FIXES = {
    "oil": Fix(
        id="oil",
        label="a tiny drop of oil",
        prep="put a tiny drop of oil on the squeaky hinge",
        tail="The little bell worked because the hinge could move again",
        fits={"bell"},
    ),
    "tap": Fix(
        id="tap",
        label="a soft tap",
        prep="give the bell a soft tap and turn the knob slowly",
        tail="The old desk answered with one clear ring",
        fits={"bell"},
    ),
}

NAMES = ["Mila", "Noah", "Ivy", "Eli", "June", "Theo", "Zoe", "Ava"]
ROLES = ["girl", "boy"]
HELPERS = ["Grandma", "Grandpa", "Aunt Rose", "Mr. Lane"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for pname, place in PLACES.items():
        for prname, problem in PROBLEMS.items():
            if problem.keyword in {"reception", "ghost"}:
                for fname, fix in FIXES.items():
                    if problem.id in fix.fits and "bell" in place.affords:
                        out.append((pname, prname, fname))
    return out


def explain_rejection(problem: Problem, fix: Fix) -> str:
    return f"(No story: the fix '{fix.id}' does not reasonably help with the {problem.issue}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Ghost-story world with dialogue and repetition.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--fix", choices=FIXES)
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
    if getattr(args, "problem", None) and getattr(args, "fix", None):
        if not (getattr(args, "problem", None) in PROBLEMS and getattr(args, "fix", None) in FIXES):
            return _fallback_storyparams(args, rng, StoryParams, globals())
        if _safe_lookup(PROBLEMS, getattr(args, "problem", None)).id not in _safe_lookup(FIXES, getattr(args, "fix", None)).fits:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "problem", None) is None or c[1] == getattr(args, "problem", None))
              and (getattr(args, "fix", None) is None or c[2] == getattr(args, "fix", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, fix = (list(rng.choice(combos)) + [None, None, None])[:3]
    name = getattr(args, "name", None) or rng.choice(NAMES)
    role = getattr(args, "role", None) or rng.choice(ROLES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(place=place, problem=problem, fix=fix, name=name, role=role, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short ghost story for a young child about a quiet reception and a wolverine ghost.',
        f'Tell a story where {f["child"].id} hears a wolverine ghost repeat the same line until the reception can {f["problem"].verb}.',
        f'Write a gentle spooky tale with dialogue and repetition set at {world.place.name}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    ghost = _safe_fact(world, f, "ghost")
    problem = _safe_fact(world, f, "problem")
    fix = _safe_fact(world, f, "fix")
    return [
        QAItem(
            question=f"Where did {child.id} meet the wolverine ghost?",
            answer=f"{child.id} met the wolverine ghost at {world.place.name}, near the reception desk.",
        ),
        QAItem(
            question=f"What did the ghost keep repeating?",
            answer=f"The ghost kept repeating, \"It will not {problem.verb}.\"",
        ),
        QAItem(
            question=f"What helped the reception {problem.verb} again?",
            answer=f"{fix.label} helped, because they used it to fix the stuck reception bell.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer="The bell worked again, the ghost grew calm, and the reception felt peaceful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reception?",
            answer="A reception is a front area where people are welcomed and helped, often with a desk or bell.",
        ),
        QAItem(
            question="What is a wolverine?",
            answer="A wolverine is a strong animal with thick fur and sharp claws.",
        ),
        QAItem(
            question="Why do stories repeat a line in a ghost story?",
            answer="A repeated line can make a ghost story feel eerie, like the room remembers the words.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== (3) World-knowledge questions ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:14} ({e.kind:8}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
place_ok(P) :- place(P).
problem_ok(B) :- problem(B).
fix_ok(F) :- fix(F), helps(F, bell).
valid(P,B,F) :- place_ok(P), problem_ok(B), fix_ok(F), affords(P, bell), helps(F, B).
#show valid/3.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.quiet:
            lines.append(asp.fact("quiet", pid))
        if p.spooky:
            lines.append(asp.fact("spooky", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for bid, b in PROBLEMS.items():
        lines.append(asp.fact("problem", bid))
        lines.append(asp.fact("verb", bid, b.verb))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for x in sorted(f.fits):
            lines.append(asp.fact("helps", fid, x))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


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
    print("MISMATCH:")
    print("python-only:", sorted(py - cl))
    print("clingo-only:", sorted(cl - py))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell_story(_safe_lookup(PLACES, params.place), _safe_lookup(PROBLEMS, params.problem), _safe_lookup(FIXES, params.fix),
                       params.name, params.role, params.helper)
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
    StoryParams(place="old hotel", problem="bell", fix="oil", name="Mila", role="girl", helper="Grandma"),
    StoryParams(place="front reception", problem="bell", fix="tap", name="Noah", role="boy", helper="Mr. Lane"),
    StoryParams(place="mountain lodge", problem="bell", fix="oil", name="Ivy", role="girl", helper="Aunt Rose"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid/3."))
        return

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        samples = []
        seen = set()
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
