#!/usr/bin/env python3
"""
A tall-tale story world about a child, a hedge, and a stubborn chime.

Premise:
- A child notices a small chime tangled high in a hedge.
- They want it for a cheerful sound, but the hedge is too scratchy and the chime is too stuck.

Turn:
- The child tries a few obvious tricks and learns they need a smarter plan.

Resolution:
- With a helper tool and a careful scooch, they free the chime and make the hedge look proud of it.

This world is intentionally small, state-driven, and child-facing.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    chime: object | None = None
    helper: object | None = None
    hero: object | None = None
    tool: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    name: str = "the hedge lane"
    tall: bool = True
    windy: bool = True
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
class StoryParams:
    name: str
    gender: str
    helper: str
    place: str
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


@dataclass
class Tool:
    id: str
    label: str
    helps_with: set[str]
    reach: str
    verb: str
    carries: str
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
    verb: str
    snag: str
    risk: str
    zone: str
    needs: set[str]
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.trace_bits: list[str] = []

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
        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


GIRL_NAMES = ["Mina", "Luna", "Ada", "Nora", "Penny", "Ruby", "Ivy", "June"]
BOY_NAMES = ["Otis", "Bram", "Toby", "Milo", "Finn", "Arlo", "Jasper", "Theo"]
HELPERS = ["grandfather", "mother", "neighbor", "sister", "uncle"]
PLACES = {
    "lane": Place(name="the hedge lane", tall=True, windy=True),
    "yard": Place(name="the yard beside the hedge", tall=True, windy=False),
    "garden": Place(name="the garden path", tall=True, windy=True),
}

TOOLS = {
    "ladder": Tool(
        id="ladder",
        label="a little ladder",
        helps_with={"reach"},
        reach="high",
        verb="climb up",
        carries="climbed up",
    ),
    "hook": Tool(
        id="hook",
        label="a hooked stick",
        helps_with={"pull"},
        reach="long",
        verb="reach over",
        carries="reached over",
    ),
    "cloth": Tool(
        id="cloth",
        label="a soft cloth",
        helps_with={"grip"},
        reach="close",
        verb="wrap around",
        carries="wrapped around",
    ),
}

PROBLEMS = {
    "chime_in_hedge": Problem(
        id="chime_in_hedge",
        label="a tin chime",
        verb="ring",
        snag="caught on a thorn",
        risk="might bend or go silent",
        zone="top",
        needs={"reach", "pull"},
    ),
}

ASP_RULES = r"""
problem(P) :- problem_id(P).
tool(T) :- tool_id(T).
can_help(T,P) :- tool(T), problem(P), tool_helps(T,reach), tool_helps(T,pull).
valid_story(Place, P, T) :- place(Place), problem(P), can_help(T,P).
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", pid) for pid in PLACES]
    for pid, p in PROBLEMS.items():
        lines.append(asp.fact("problem_id", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_id", tid))
        for h in sorted(t.helps_with):
            lines.append(asp.fact("tool_helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def is_reasonable(problem: Problem, tool: Tool) -> bool:
    return problem.needs.issubset(tool.helps_with)


def select_tool(problem: Problem) -> Optional[Tool]:
    for tool in TOOLS.values():
        if is_reasonable(problem, tool):
            return tool
    return None


def validate_params(args: argparse.Namespace) -> None:
    if getattr(args, "place", None) and getattr(args, "place", None) not in PLACES:
        pass
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in {"girl", "boy"}:
        pass
    if getattr(args, "name", None) and not getattr(args, "name", None).strip():
        pass


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    validate_params(args)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    return StoryParams(name=name, gender=gender, helper=helper, place=place)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale story world: scooch, chime, hedge, problem solving.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=HELPERS)
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


def _r_doubt(world: World) -> list[str]:
    hero = world.get("hero")
    if hero.memes.get("puzzled", 0) >= THRESHOLD and ("doubt", hero.id) not in world.fired:
        world.fired.add(("doubt", hero.id))
        hero.memes["resolve"] = hero.memes.get("resolve", 0) + 1
        return [f"{hero.id} paused and looked twice, because a problem worth fixing needed a better idea."]
    return []


def _r_free_chime(world: World) -> list[str]:
    chime = world.get("chime")
    hero = world.get("hero")
    tool = world.get("tool")
    if hero.meters.get("scooch", 0) < THRESHOLD:
        return []
    if tool.id != "hook":
        return []
    sig = ("free", chime.id)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    chime.meters["free"] = 1
    chime.memes["happy"] = chime.memes.get("happy", 0) + 1
    world.trace_bits.append("chime-freed")
    return [f"The hooked stick did the trick, and the chime came loose with a bright little twinkle."]


CAUSAL_RULES = [_r_doubt, _r_free_chime]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def intro(world: World, hero: Entity, helper: Entity, problem: Problem) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a big heart and a bigger eye for trouble."
        f" One breezy day, {hero.id} noticed {problem.label} stuck in the hedge like a shy star in a green sky."
    )
    world.say(
        f"{hero.id} wanted {problem.label} to {problem.verb}, but it was {problem.snag}, and the hedge kept its secret tight."
    )
    helper.memes["care"] = helper.memes.get("care", 0) + 1
    world.say(
        f"Then {hero.pronoun('possessive')} {helper.type} came along and said, "
        f"\"Let's not wrestle the hedge; let's outthink it.\""
    )


def attempt_one(world: World, hero: Entity, problem: Problem) -> None:
    hero.memes["puzzled"] = hero.memes.get("puzzled", 0) + 1
    world.say(
        f"{hero.id} tried to yank the chime free with both hands, but the hedge only rustled and held on harder."
    )


def attempt_two(world: World, hero: Entity, problem: Problem) -> None:
    hero.meters["scooch"] = hero.meters.get("scooch", 0) + 1
    world.say(
        f"So {hero.id} gave a careful scooch along the hedge line, side-stepping the prickles and peeking for a loose branch."
    )
    propagate(world, narrate=True)


def solve_problem(world: World, hero: Entity, helper: Entity, tool: Entity, problem: Problem) -> None:
    world.say(
        f"{helper.id} held up {tool.label} and laughed, \"Reach high, then pull gentle—that is the whole lantern-load of it!\""
    )
    world.say(
        f"{hero.id} set the hook just so, gave one tidy scooch, and the chime slipped free with a bright little ching-chang-chime."
    )
    world.say(
        f"The hedge shivered once, then stood proud and neat, as if it had been waiting all along to wear a song."
    )
    world.say(
        f"By the end, {hero.id} carried {problem.label} home, and the whole lane seemed to smile in the wind."
    )


def tell(params: StoryParams) -> World:
    rng = random.Random(params.seed)
    world = World(_safe_lookup(PLACES, params.place))
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender, label=params.name))
    helper = world.add(Entity(id="helper", kind="character", type="helper", label=params.helper))
    chime = world.add(Entity(id="chime", type="chime", label="the tin chime", owner=hero.id))
    tool = world.add(Entity(id="tool", type="tool", label=TOOLS["hook"].label, owner=helper.id))
    problem = PROBLEMS["chime_in_hedge"]

    hero.memes["curious"] = 1
    intro(world, hero, helper, problem)
    world.para()
    attempt_one(world, hero, problem)
    world.para()
    attempt_two(world, hero, problem)
    world.para()
    solve_problem(world, hero, helper, tool, problem)

    world.facts.update(hero=hero, helper=helper, chime=chime, tool=tool, problem=problem, params=params)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    return [
        f'Write a tall-tale style story about {hero.id}, a hedge, and a chime, using the word "scooch".',
        f"Tell a problem-solving story where {hero.id} and {helper.id} figure out how to free a chime from a hedge.",
        f'Write a short child-friendly tale that includes "chime" and ends with a clever fix instead of a tug-of-war.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    return [
        QAItem(
            question=f"What was stuck in the hedge?",
            answer=f"A tin chime was stuck in the hedge, caught up high where the wind could not shake it loose.",
        ),
        QAItem(
            question=f"How did {hero.id} try to solve the problem first?",
            answer=f"{hero.id} tried to pull the chime free by hand first, but that only made the hedge hold on tighter.",
        ),
        QAItem(
            question=f"What smart move finally helped?",
            answer=f"{helper.id} brought a hooked stick, and {hero.id} used a careful scooch to free the chime without hurting the hedge.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a hedge?",
            answer="A hedge is a row of bushes or shrubs that grows together like a living green fence.",
        ),
        QAItem(
            question="What is a chime?",
            answer="A chime is something that rings and makes a light, musical sound when it moves or is struck.",
        ),
        QAItem(
            question="What does scooch mean?",
            answer="To scooch means to move a little way by shuffling or sliding carefully.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
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
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        lines.append(f"{e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    lines.append(f"fired={sorted(world.fired)}")
    lines.append(f"notes={world.trace_bits}")
    return "\n".join(lines)


def valid_combos() -> list[tuple[str, str, str]]:
    return [(place, "chime_in_hedge", "hook") for place in PLACES]


ASP_RULES = r"""
valid(Place, Problem, Tool) :- place(Place), problem_id(Problem), tool_id(Tool), tool_helps(Tool, reach), tool_helps(Tool, pull).
"""


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("Mismatch between ASP and Python.")
    if py - cl:
        print("only in python:", sorted(py - cl))
    if cl - py:
        print("only in asp:", sorted(cl - py))
    return 1


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


def asp_facts() -> str:
    import asp
    lines = []
    for p in PLACES:
        lines.append(asp.fact("place", p))
    for pid in PROBLEMS:
        lines.append(asp.fact("problem_id", pid))
    for tid, t in TOOLS.items():
        lines.append(asp.fact("tool_id", tid))
        for h in sorted(t.helps_with):
            lines.append(asp.fact("tool_helps", tid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "place", None) and getattr(args, "place", None) not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    return StoryParams(name=name, gender=gender, helper=helper, place=place)


def build_curated() -> list[StoryParams]:
    return [
        StoryParams(name="Mina", gender="girl", helper="grandfather", place="lane"),
        StoryParams(name="Otis", gender="boy", helper="neighbor", place="yard"),
        StoryParams(name="Nora", gender="girl", helper="sister", place="garden"),
    ]


def main() -> None:
    ap = build_parser()
    args = ap.parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} valid combinations:")
        for c in combos:
            print(c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in build_curated()]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 20):
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
