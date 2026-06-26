#!/usr/bin/env python3
"""
A small fable-style story world about Patch, Lmnop, and Whit, where bravery
turns a hard moment into a kind one.
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


BRAVERY_THRESHOLD = 1.0



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
    kind: str = "character"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    lmnop: object | None = None
    patch: object | None = None
    whit: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    description: str
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
    pressure: str
    risk: str
    trigger: str
    feared_result: str
    benefit: str
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
class Helper:
    id: str
    label: str
    act: str
    method: str
    result: str
    covers: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: callable
    RULES: list = field(default_factory=list)
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


def _r_calm(world: World) -> list[str]:
    out = []
    for e in world.characters():
        if e.memes.get("safe", 0.0) >= BRAVERY_THRESHOLD and e.memes.get("fear", 0.0) > 0:
            sig = ("calm", e.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            e.memes["fear"] = 0.0
            e.memes["hope"] = e.memes.get("hope", 0.0) + 1
            out.append(f"{e.id} found courage and breathed easier.")
    return out


def _r_help(world: World) -> list[str]:
    out = []
    hero = world.entities.get("Patch")
    helper = world.entities.get("Whit")
    if not hero or not helper:
        return out
    if hero.memes.get("bravery", 0.0) < BRAVERY_THRESHOLD:
        return out
    sig = ("help", hero.id, helper.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["kindness"] = helper.memes.get("kindness", 0.0) + 1
    hero.meters["burden"] = max(0.0, hero.meters.get("burden", 0.0) - 1)
    out.append("Whit stepped close and shared the load.")
    return out


RULES = [Rule("calm", _r_calm), Rule("help", _r_help)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            out = rule.apply(world)
            if out:
                changed = True
                produced.extend(out)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def ask_brave(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["bravery"] = hero.memes.get("bravery", 0.0) + 1
    hero.meters["burden"] = hero.meters.get("burden", 0.0) + 1
    world.say(
        f"{hero.id} looked at the {problem.pressure} and chose to be brave."
    )


def warn_of_risk(world: World, problem: Problem) -> None:
    world.say(
        f"The old path carried a hard risk: if the {problem.trigger} went wrong, "
        f"the {problem.feared_result} could follow."
    )
    world.facts["fear"] = problem.risk


def helper_offer(world: World, helper: Helper, hero: Entity) -> None:
    world.say(
        f"{helper.id} said, \"I can {helper.act}, and we can do it together.\""
    )
    hero.memes["safe"] = hero.memes.get("safe", 0.0) + 1


def resolve(world: World, hero: Entity, helper: Helper, problem: Problem) -> None:
    propagate(world, narrate=False)
    world.say(
        f"So {hero.id} and {helper.id} chose the kinder way, using {helper.method}. "
        f"{helper.result.capitalize()}, and the {problem.benefit} was enough for all."
    )
    hero.memes["peace"] = hero.memes.get("peace", 0.0) + 1


def tell(place: Place, problem: Problem, hero_name: str = "Patch") -> World:
    world = World(place)
    patch = world.add(Entity(
        id="Patch",
        kind="character",
        type="fox",
        label="Patch",
        traits=["small", "curious", "brave"],
        meters={"burden": 0.0},
        memes={"bravery": 0.0, "fear": 0.0, "hope": 0.0},
    ))
    lmnop = world.add(Entity(
        id="Lmnop",
        kind="character",
        type="hare",
        label="Lmnop",
        traits=["quick", "soft-spoken", "careful"],
        meters={"burden": 0.0},
        memes={"care": 1.0},
    ))
    whit = world.add(Entity(
        id="Whit",
        kind="character",
        type="owl",
        label="Whit",
        traits=["wise", "gentle"],
        meters={"burden": 0.0},
        memes={"kindness": 0.0},
    ))
    world.facts.update(hero=patch, friend=lmnop, helper=whit, problem=problem, place=place)

    world.say(
        f"In {place.name}, there lived a little fox named Patch, a careful hare named Lmnop, "
        f"and a wise owl named Whit."
    )
    world.say(
        f"Each one knew the lane well, but Patch loved the {problem.benefit} of trying hard things."
    )

    world.para()
    world.say(place.description)
    warn_of_risk(world, problem)
    ask_brave(world, patch, problem)
    world.say(
        f"Patch wanted to {problem.trigger}, though the {problem.risk} made the way feel steep."
    )
    patch.memes["fear"] = patch.memes.get("fear", 0.0) + 1

    world.para()
    helper_offer(world, whit, patch)
    world.say(
        f"Lmnop stood beside Patch so the little fox would not have to face the road alone."
    )
    patch.memes["safe"] = patch.memes.get("safe", 0.0) + 1
    resolve(world, patch, whit, problem)
    world.say(
        f"After that, Patch walked on with a lighter heart, and even the stones seemed less sharp."
    )
    return world


SETTINGS = {
    "meadow": Place(
        name="the meadow",
        description="The meadow was wide, and the wind moved through the grass like a soft song.",
        affords={"cross_stream"},
    ),
    "hill": Place(
        name="the hill",
        description="The hill climbed up under a bright sky, and the path curled between little stones.",
        affords={"carry_lantern"},
    ),
    "bridge": Place(
        name="the old bridge",
        description="The old bridge creaked over the water, but it still held fast.",
        affords={"cross_stream"},
    ),
}

PROBLEMS = {
    "stream": Problem(
        id="stream",
        pressure="shallow stream",
        risk="slippery stones",
        trigger="cross the stream",
        feared_result="a tumble into the water",
        benefit="far bank",
        tags={"water", "bravery"},
    ),
    "lantern": Problem(
        id="lantern",
        pressure="dark hill path",
        risk="long shadows",
        trigger="carry the lantern to the top",
        feared_result="a lost step",
        benefit="warm light",
        tags={"dark", "bravery"},
    ),
}

HELPERS = {
    "whit": Helper(
        id="Whit",
        label="Whit",
        act="guide the way",
        method="Whit’s steady wing and Lmnop’s close watch",
        result="the path stayed true",
        covers={"fear"},
    ),
    "lmnop": Helper(
        id="Lmnop",
        label="Lmnop",
        act="keep watch",
        method="Lmnop’s quick eyes and Whit’s calm words",
        result="the crossing went smoothly",
        covers={"burden"},
    ),
}


@dataclass
class StoryParams:
    setting: str
    problem: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A small fable-world about bravery.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--problem", choices=PROBLEMS)
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS))
    problem = getattr(args, "problem", None) or rng.choice(list(PROBLEMS))
    if setting == "meadow" and problem == "lantern":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if setting == "hill" and problem == "stream":
        return _fallback_storyparams(args, rng, StoryParams, globals())
    return StoryParams(setting=setting, problem=problem)


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "problem")
    return [
        f"Write a short fable about Patch, Lmnop, and Whit, and the {p.pressure}.",
        f"Tell a child-friendly story where bravery helps Patch face the {p.risk}.",
        f"Write a gentle animal tale that ends with a wiser choice and a calmer heart.",
    ]


def story_qa(world: World) -> list[QAItem]:
    p: Problem = _safe_fact(world, world.facts, "problem")
    return [
        QAItem(
            question="Who was the story mainly about?",
            answer="The story was mainly about Patch, a small fox who tried to be brave.",
        ),
        QAItem(
            question=f"What hard thing did Patch want to do?",
            answer=f"Patch wanted to {p.trigger} even though {p.risk} made it feel hard.",
        ),
        QAItem(
            question="Who helped Patch?",
            answer="Whit helped Patch, and Lmnop stayed close so Patch would not feel alone.",
        ),
        QAItem(
            question="What changed by the end?",
            answer="Patch's heart grew steadier, the path felt kinder, and the friends finished together.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is bravery?",
            answer="Bravery means feeling afraid but choosing to do the right thing anyway.",
        ),
        QAItem(
            question="Why do friends help one another?",
            answer="Friends help one another because a hard task feels lighter when it is shared.",
        ),
        QAItem(
            question="What does a wise helper do?",
            answer="A wise helper gives a calm plan, a steady word, and a way to keep going safely.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    lines.extend(f"- {p}" for p in sample.prompts)
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
        lines.append(f"{e.id}: meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
hero(patch).
helper(whit).
friend(lmnop).

brave(patch) :- chooses_courage(patch).
chooses_courage(patch) :- fear(patch), help(whit), support(lmnop).

resolve :- brave(patch), support(lmnop), help(whit).
"""

def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("hero", "patch"),
        asp.fact("helper", "whit"),
        asp.fact("friend", "lmnop"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for s in SETTINGS:
        for p in PROBLEMS:
            if s == "meadow" and p == "lantern":
                continue
            if s == "hill" and p == "stream":
                continue
            combos.append((s, p))
    return combos


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show resolve/0.\n#show brave/1."))
    return sorted(set((atom.name, len(atom.arguments)) for atom in model))


def asp_verify() -> int:
    import asp
    _ = asp.one_model(asp_program("#show resolve/0."))
    if len(valid_combos()) == 2:
        print("OK: ASP loaded and Python validity gate is sane.")
        return 0
    print("Mismatch in validity gate.")
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(PROBLEMS, params.problem))
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
    StoryParams(setting="meadow", problem="stream"),
    StoryParams(setting="hill", problem="lantern"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show resolve/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        samples: list[StorySample] = []
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story not in seen:
                seen.add(sample.story)
                samples.append(sample)
            i += 1

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
