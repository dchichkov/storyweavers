#!/usr/bin/env python3
"""
storyworlds/worlds/banjo_tile_problem_solving_adventure.py
===========================================================

A small adventure storyworld about a child explorer, a tricky tile, and a
clever problem-solving turn with a banjo.

The seed idea:
- A traveler reaches an old place with a loose tile hiding trouble or a clue.
- The hero must pause, notice, and solve the problem with a practical plan.
- The banjo matters not as decoration, but as a useful tool for sound, string,
  rhythm, and courage.

The stories are short, child-facing, and state-driven:
setup -> obstacle -> careful thinking -> solved route forward.
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
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    problem: object | None = None
    tool: object | None = None
    def __post_init__(self):
        for k in ("strain", "dust", "care", "progress", "risk", "joy", "worry", "focus", "courage"):
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
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
    id: str
    label: str
    indoor: bool
    features: set[str] = field(default_factory=set)
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
class Problem:
    id: str
    label: str
    symptom: str
    danger: str
    fix_hint: str
    zone: set[str]
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
    covers: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, place: Place, problem: Problem) -> None:
        self.place = place
        self.problem = problem
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
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

    def copy(self) -> "World":
        import copy
        w = World(self.place, self.problem)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        return w


def _r_dust(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    if hero.memes["focus"] < THRESHOLD:
        return out
    if hero.meters["strain"] >= THRESHOLD and ("dust", hero.id) not in world.fired:
        world.fired.add(("dust", hero.id))
        hero.meters["dust"] += 1
        out.append(f"A little dust puffed up around {hero.id}'s boots.")
    return out


def _r_progress(world: World) -> list[str]:
    out = []
    hero = world.get("hero")
    problem = world.get("problem")
    tool = world.entities.get("tool")
    if not tool:
        return out
    if tool.meters["used"] < THRESHOLD:
        return out
    if problem.meters["risk"] < THRESHOLD:
        return out
    if ("progress", hero.id) in world.fired:
        return out
    world.fired.add(("progress", hero.id))
    hero.meters["progress"] += 1
    hero.memes["joy"] += 1
    hero.memes["worry"] = 0
    out.append("The careful fix made the path safe again.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_dust, _r_progress):
            lines = rule(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_solve(problem: Problem, tool: Tool) -> bool:
    return problem.id in tool.helps


def valid_story(place: Place, problem: Problem, tool: Tool) -> bool:
    return problem.id in place.features and can_solve(problem, tool)


PLACES = {
    "ruined_hall": Place("ruined_hall", "the ruined hall", indoor=True, features={"loose_tile", "echo"}),
    "old_bridge": Place("old_bridge", "the old bridge", indoor=False, features={"loose_tile", "wind"}),
    "stone_gallery": Place("stone_gallery", "the stone gallery", indoor=True, features={"loose_tile", "mosaic"}),
}

PROBLEMS = {
    "loose_tile": Problem(
        "loose_tile",
        "a loose tile",
        symptom="one tile wobbled underfoot",
        danger="it could trip the traveler and hide a secret below",
        fix_hint="it needed a careful lift and a steady wedge",
        zone={"feet"},
        tags={"tile", "adventure"},
    ),
    "stuck_tile": Problem(
        "stuck_tile",
        "a stuck tile",
        symptom="one tile would not budge",
        danger="it blocked the hidden latch under it",
        fix_hint="it needed a gentle tap and a slim pry",
        zone={"hands"},
        tags={"tile", "adventure"},
    ),
}

TOOLS = {
    "banjo": Tool(
        "banjo",
        "a banjo",
        "their banjo",
        helps={"loose_tile", "stuck_tile"},
        covers=set(),
    ),
    "wedge": Tool(
        "wedge",
        "a little wooden wedge",
        "the little wooden wedge",
        helps={"loose_tile"},
    ),
    "spoon": Tool(
        "spoon",
        "a metal spoon",
        "the metal spoon",
        helps={"stuck_tile"},
    ),
}

HERO_NAMES = ["Mina", "Toby", "Nora", "Leo", "Pip", "Iris"]
TRAITS = ["brave", "curious", "careful", "lively", "steady"]


@dataclass
class StoryParams:
    place: str
    problem: str
    tool: str
    name: str
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
    ap = argparse.ArgumentParser(description="Adventure storyworld: banjo, tile, and a clever fix.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--problem", choices=PROBLEMS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
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
    combos = [(pl.id, pr.id, tl.id) for pl in PLACES.values() for pr in PROBLEMS.values() for tl in TOOLS.values() if valid_story(pl, pr, tl)]
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "problem", None):
        combos = [c for c in combos if c[1] == getattr(args, "problem", None)]
    if getattr(args, "tool", None):
        combos = [c for c in combos if c[2] == getattr(args, "tool", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, problem, tool = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, problem=problem, tool=tool, name=name, trait=trait)


def setup_world(params: StoryParams) -> World:
    world = World(_safe_lookup(PLACES, params.place), _safe_lookup(PROBLEMS, params.problem))
    hero = world.add(Entity("hero", kind="character", type="child", label=params.name))
    hero.memes["courage"] = 1
    hero.memes["focus"] = 1
    tool_def = _safe_lookup(TOOLS, params.tool)
    tool = world.add(Entity("tool", type="tool", label=tool_def.label, phrase=tool_def.phrase, plural=tool_def.plural))
    tool.worn_by = hero.id
    problem = world.add(Entity("problem", type="problem", label=world.problem.label))
    problem.meters["risk"] = 1
    world.facts.update(hero=hero, tool=tool, problem=problem, place=world.place, params=params)
    return world


def predict(world: World) -> dict:
    sim = world.copy()
    hero = sim.get("hero")
    hero.meters["strain"] += 1
    tool = sim.get("tool")
    tool.meters["used"] += 1
    propagate(sim, narrate=False)
    return {"safe": sim.get("problem").meters["risk"] >= THRESHOLD, "progress": sim.get("hero").meters["progress"]}


def tell_story(world: World) -> None:
    hero = world.get("hero")
    tool = world.get("tool")
    problem = world.get("problem")
    params = _safe_fact(world, world.facts, "params")

    world.say(f"{hero.label} was a {params.trait} little explorer who loved {tool.label} and wide-open paths.")
    world.say(f"One day, {hero.label} reached {world.place.label}, where {problem.label} showed its trouble: {problem.symptom}.")
    world.para()
    world.say(f"{problem.danger.capitalize()}, so {hero.label} stopped instead of rushing on.")
    world.say(f"{hero.label} listened, looked, and thought hard. The {problem.label} needed {problem.fix_hint}.")
    hero.memes["worry"] += 1
    hero.memes["focus"] += 1
    hero.meters["strain"] += 1

    if params.tool == "banjo":
        world.say(f"{hero.label} plucked the banjo and heard the hollow sound around the tile.")
        world.say(f"That clue told {hero.label} exactly where the tile was loose.")
    elif params.tool == "wedge":
        world.say(f"{hero.label} used the little wooden wedge to lift one edge of the tile.")
    else:
        world.say(f"{hero.label} tapped the tile carefully with the metal spoon until it shifted.")

    tool.meters["used"] += 1
    propagate(world, narrate=True)
    world.para()
    world.say(f"Then {hero.label} slid the {tool.label} into place and fixed the problem.")
    world.say(f"The tile stopped wobbling, the path was safe, and {hero.label} moved on with a grin.")
    hero.memes["joy"] += 2
    hero.memes["worry"] = 0


def generation_prompts(world: World) -> list[str]:
    p = _safe_fact(world, world.facts, "params")
    return [
        f'Write a short adventure story for a child named {p.name} who uses a banjo to solve a tile problem.',
        f"Tell a brave, child-friendly story where a {p.trait} explorer notices a tile that is not safe and fixes it with a clever plan.",
        f'Write an adventure tale that includes the words "banjo" and "tile" and ends with the path safe again.',
    ]


def story_qa(world: World) -> list[QAItem]:
    p = _safe_fact(world, world.facts, "params")
    hero = _safe_fact(world, world.facts, "hero")
    place = world.place.label
    problem = world.problem.label
    tool = _safe_fact(world, world.facts, "tool").label
    return [
        QAItem(
            question=f"What kind of problem did {hero.label} find at {place}?",
            answer=f"{hero.label} found {problem}, and it made the path unsafe until it was fixed.",
        ),
        QAItem(
            question=f"How did {hero.label} use the banjo in the story?",
            answer=f"{hero.label} plucked the banjo to listen for the hollow place around the tile and figure out where to work.",
        ),
        QAItem(
            question=f"What changed after {hero.label} solved the problem?",
            answer=f"The tile stopped wobbling, the danger went away, and {hero.label} could go on with the adventure.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a banjo?",
            answer="A banjo is a stringed instrument you can pluck to make bright, cheerful music.",
        ),
        QAItem(
            question="What is a tile?",
            answer="A tile is a flat piece of hard material used on floors, walls, or roofs.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        lines.append(f"{e.id}: {e.label or e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


ASP_RULES = r"""
safe_story(P,Pr,T) :- place(P), problem(Pr), tool(T), needs(Pr,Pr), helps(T,Pr), available(P,Pr).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        for f in sorted(p.features):
            lines.append(asp.fact("available", pid, f))
    for prid, pr in PROBLEMS.items():
        lines.append(asp.fact("problem", prid))
        for z in sorted(pr.zone):
            lines.append(asp.fact("needs", prid, z))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool", tid))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> set[tuple]:
    import asp
    model = asp.one_model(asp_program("#show safe_story/3."))
    return set(asp.atoms(model, "safe_story"))


def python_valid() -> set[tuple]:
    return {(p.id, pr.id, t.id) for p in PLACES.values() for pr in PROBLEMS.values() for t in TOOLS.values() if valid_story(p, pr, t)}


def asp_verify() -> int:
    a = asp_valid()
    p = python_valid()
    if a == p:
        print(f"OK: clingo gate matches python valid stories ({len(a)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    print("only in clingo:", sorted(a - p))
    print("only in python:", sorted(p - a))
    return 1


CURATED = [
    StoryParams("ruined_hall", "loose_tile", "banjo", "Mina", "curious"),
    StoryParams("old_bridge", "loose_tile", "wedge", "Leo", "brave"),
    StoryParams("stone_gallery", "stuck_tile", "banjo", "Nora", "steady"),
]


def generate(params: StoryParams) -> StorySample:
    world = setup_world(params)
    tell_story(world)
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
        print(asp_program("#show safe_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show safe_story/3."))
        combos = sorted(set(asp.atoms(model, "safe_story")))
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print("  ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name}: {p.problem} with {p.tool} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
