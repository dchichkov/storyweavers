#!/usr/bin/env python3
"""
storyworlds/worlds/wall_humor_problem_solving_transformation_comedy.py
======================================================================

A small comedy storyworld about a wall that turns a simple problem into a funny
bit of problem solving and transformation.

Premise:
- A child wants to get something on the other side of a wall.
- The wall is not evil; it is just a stubborn obstacle.
- A helper and a silly plan lead to a transformation that changes the scene.

The story is driven by a lightweight world model:
- physical meters: stuckness, reach, wobble, height, tidy, funny
- emotional memes: worry, confidence, delight, pride, surprise

The generated stories stay concrete and child-facing while keeping the tone
comic, with a real setup, a turn, and a changed ending image.
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
    plural: bool = False
    owner: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    goal: object | None = None
    helper: object | None = None
    hero: object | None = None
    wall: object | None = None
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
    place: str = "the yard"
    has_wall: bool = True
    wall_kind: str = "brick wall"
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
class Goal:
    label: str
    phrase: str
    reason: str
    kind: str = "thing"
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
    label: str
    phrase: str
    action: str
    transform: str
    helps: set[str] = field(default_factory=set)
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
class StoryParams:
    place: str
    goal: str
    tool: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

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

    def copy(self) -> "World":
        import copy as _copy

        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        return w


@dataclass
class Rule:
    name: str
    apply: callable
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


def _r_boast(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.memes.get("confidence", 0.0) >= THRESHOLD and ("boast", e.id) not in world.fired:
            world.fired.add(("boast", e.id))
            out.append(f"{e.id} puffed up and said they could handle the wall problem.")
    return out


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    for e in world.characters():
        if e.meters.get("wobble", 0.0) >= THRESHOLD and ("wobble", e.id) not in world.fired:
            world.fired.add(("wobble", e.id))
            e.memes["surprise"] = e.memes.get("surprise", 0.0) + 1
            out.append(f"That made {e.id} wobble like a spoon on a saucer.")
    return out


CAUSAL_RULES = [Rule("boast", _r_boast), Rule("wobble", _r_wobble)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                out.extend(sents)
    if narrate:
        for s in out:
            world.say(s)
    return out


def reasonableness_gate(goal: Goal, tool: Tool) -> bool:
    return goal.kind in tool.helps


def tool_for_goal(goal: Goal) -> Optional[Tool]:
    for t in TOOLS:
        if reasonableness_gate(goal, t):
            return t
    return None


def predicted_result(world: World, hero: Entity, goal: Goal, tool: Tool) -> dict:
    sim = world.copy()
    do_attempt(sim, sim.get(hero.id), goal, tool, narrate=False)
    target = sim.entities.get("goal")
    return {
        "solved": bool(target and target.meters.get("reachable", 0.0) >= THRESHOLD),
        "funny": hero.memes.get("delight", 0.0) + hero.meters.get("funny", 0.0),
    }


def do_attempt(world: World, hero: Entity, goal: Goal, tool: Tool, narrate: bool = True) -> None:
    if ("attempt", hero.id) in world.fired:
        return
    world.fired.add(("attempt", hero.id))
    hero.meters["stuckness"] = max(0.0, hero.meters.get("stuckness", 0.0) - 0.25)
    hero.memes["worry"] = max(0.0, hero.memes.get("worry", 0.0) - 0.25)
    hero.memes["confidence"] = hero.memes.get("confidence", 0.0) + 0.5
    if narrate:
        world.say(f"{hero.id} tried the {tool.label} idea, because the wall still would not budge.")


def hero_intro(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.meters.get("traits", []) if t), "")
    if trait:
        world.say(f"{hero.id} was a little {trait} {hero.type} who loved solving tiny problems.")
    else:
        world.say(f"{hero.id} was a little {hero.type} who loved solving tiny problems.")


def setup_story(world: World, hero: Entity, helper: Entity, goal: Entity, wall: Entity, goal_cfg: Goal) -> None:
    hero_intro(world, hero)
    world.say(
        f"One day, {hero.id} wanted {goal_cfg.phrase}, but a {wall.label} stood in the way."
    )
    world.say(
        f"{helper.id} said the wall looked serious, but probably only because it was pretending."
    )
    hero.memes["worry"] = 1.0
    goal.meters["reachable"] = 0.0
    wall.meters["height"] = 2.0
    wall.meters["funny"] = 0.0


def problem_turn(world: World, hero: Entity, helper: Entity, goal: Entity, wall: Entity, goal_cfg: Goal) -> None:
    world.para()
    world.say(
        f"{hero.id} stretched, tiptoed, and reached only air."
    )
    hero.meters["stuckness"] = 1.0
    hero.memes["surprise"] = 1.0
    world.say(
        f"The wall did not laugh, but it did look annoyingly tall."
    )
    world.say(
        f"{helper.id} pointed at the wall and said, \"If you can't go over it, let's ask the wall to become less wall.\""
    )


def transform_solution(world: World, hero: Entity, helper: Entity, goal: Entity, wall: Entity, tool: Tool) -> None:
    world.para()
    if tool.id == "stepstool":
        world.say(
            f"They brought out {tool.phrase}. It was not magic, just very determined furniture."
        )
    elif tool.id == "pancake_ladder":
        world.say(
            f"They unfolded {tool.phrase}, which had the shape of a ladder and the confidence of a pancake."
        )
    else:
        world.say(
            f"They used {tool.phrase}, which turned out to be excellent at pretending to be a solution."
        )
    do_attempt(world, hero, Goal(goal.label, goal.phrase, goal.reason, goal.kind), tool)
    hero.memes["delight"] = hero.memes.get("delight", 0.0) + 1.0
    goal.meters["reachable"] = 1.0
    wall.meters["funny"] = wall.meters.get("funny", 0.0) + 1.0
    wall.label = "friendly wall"
    wall.phrase = "a friendly wall that now seemed shorter after the plan worked"
    world.say(
        f"{hero.id} went up, down, and then exactly where {goal.id} was waiting."
    )
    world.say(
        f"Even the wall seemed to transform into part of the joke."
    )


def ending_image(world: World, hero: Entity, helper: Entity, goal: Entity) -> None:
    world.para()
    world.say(
        f"In the end, {hero.id} stood on the other side with {goal.phrase}, grinning at {helper.id}."
    )
    world.say(
        f"The wall was still there, but now it felt less like a problem and more like the punch line."
    )


SETTINGS = {
    "yard": Setting(place="the yard", has_wall=True, wall_kind="brick wall"),
    "garden": Setting(place="the garden", has_wall=True, wall_kind="stone wall"),
    "playground": Setting(place="the playground", has_wall=True, wall_kind="low wall"),
}

GOALS = {
    "ball": Goal(label="ball", phrase="the red ball", reason="it rolled behind the wall", kind="round"),
    "kite": Goal(label="kite", phrase="the bright kite", reason="it blew onto the ledge", kind="light"),
    "cookie": Goal(label="cookie", phrase="the last cookie", reason="it got set on the other side", kind="small"),
}

TOOLS = [
    Tool(label="stepstool", phrase="a tiny stepstool", action="step up", transform="make the hero taller", helps={"round", "light", "small"}),
    Tool(label="pancake ladder", phrase="a silly pancake ladder", action="climb carefully", transform="turn the wall into a stage", helps={"round", "light"}),
    Tool(label="stack of boxes", phrase="a stack of wobbling boxes", action="climb up", transform="raise the hero high enough", helps={"small", "round"}),
]

HELPERS = ["mom", "dad", "grandma", "big sister", "neighbor"]
GIRL_NAMES = ["Mia", "Lily", "Ava", "Zoe", "Nora"]
BOY_NAMES = ["Ben", "Leo", "Max", "Finn", "Noah"]
TRAITS = ["curious", "cheerful", "silly", "brave", "bouncy"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for goal_id, goal in GOALS.items():
        for tool in TOOLS:
            if reasonableness_gate(goal, tool):
                combos.append((goal_id, tool.label))
    return combos


def select_tool(goal: Goal) -> Optional[Tool]:
    return tool_for_goal(goal)


def explain_rejection(goal: Goal) -> str:
    return f"(No story: none of the tools can reasonably solve the {goal.label} problem.)"


def explain_gender(_: str, __: str) -> str:
    return "(No story: this world does not use a gender restriction for this goal.)"


def tell(setting: Setting, goal_cfg: Goal, tool: Tool, hero_name: str, hero_type: str, helper_label: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, meters={"stuckness": 0.0, "funny": 0.0}, memes={"worry": 0.0, "confidence": 0.0, "delight": 0.0, "surprise": 0.0}))
    helper = world.add(Entity(id=helper_label, kind="character", type="adult", meters={}, memes={}))
    wall = world.add(Entity(id="wall", type="wall", label=setting.wall_kind, phrase=f"a {setting.wall_kind}"))
    goal = world.add(Entity(id="goal", type=goal_cfg.kind, label=goal_cfg.label, phrase=goal_cfg.phrase, owner=hero.id, meters={"reachable": 0.0}, memes={}))
    hero.meters["traits"] = [trait]

    setup_story(world, hero, helper, goal, wall, goal_cfg)
    problem_turn(world, hero, helper, goal, wall, goal_cfg)
    transform_solution(world, hero, helper, goal, wall, tool)
    ending_image(world, hero, helper, goal)

    world.facts.update(hero=hero, helper=helper, goal=goal, wall=wall, goal_cfg=goal_cfg, tool=tool, setting=setting)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    goal = _safe_fact(world, f, "goal_cfg")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write a funny short story for a child about {hero.id} and a wall, using the word "wall".',
        f"Tell a comedy story where a {hero.type} named {hero.id} wants {goal.phrase} but needs {tool.phrase} to solve the problem.",
        f"Write a playful story about a wall, a small problem, and a surprising transformation at the end.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    goal = _safe_fact(world, f, "goal_cfg")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    wall = _safe_fact(world, f, "wall")
    return [
        QAItem(
            question=f"What problem did {hero.id} have in the story?",
            answer=f"{hero.id} wanted {goal.phrase}, but {wall.label} blocked the way.",
        ),
        QAItem(
            question=f"Who helped {hero.id} with the wall problem?",
            answer=f"{helper.id} helped {hero.id} think of a funny plan instead of giving up.",
        ),
        QAItem(
            question=f"What tool helped {hero.id} solve the problem?",
            answer=f"{tool.phrase} helped by making it possible to reach {goal.phrase}.",
        ),
        QAItem(
            question=f"How did the wall change by the end?",
            answer="It became part of the joke, and the story treated it like a friendly obstacle instead of a big problem.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a wall?",
            answer="A wall is a hard structure that can divide spaces or block the way from one side to another.",
        ),
        QAItem(
            question="Why do people use a stepstool?",
            answer="People use a stepstool to reach something a little too high to reach by standing on the floor.",
        ),
        QAItem(
            question="What does it mean when something transforms?",
            answer="It means it changes into a different form or seems very different from before.",
        ),
    ]
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:10} ({e.type}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


ASP_RULES = r"""
goal_problem(H) :- hero(H), blocked_by_wall(H).
good_tool(T,G) :- tool(T), helps(T,G).
solves(H,G) :- goal_kind(H,G), good_tool(T,G), uses(H,T).
transformed(W) :- wall(W), solved_problem.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        lines.append(asp.fact("wall_kind", pid, s.wall_kind))
    for gid, g in GOALS.items():
        lines.append(asp.fact("goal", gid))
        lines.append(asp.fact("goal_kind", gid, g.kind))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.label))
        for k in sorted(t.helps):
            lines.append(asp.fact("helps", t.label, k))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    program = asp_program("#show good_tool/2.")
    model = asp.one_model(program)
    clingo_set = set(asp.atoms(model, "good_tool"))
    py_set = set((t.label, g.kind) for g in GOALS.values() for t in TOOLS if reasonableness_gate(g, t))
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld about a wall, problem solving, and transformation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--goal", choices=GOALS)
    ap.add_argument("--tool")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=HELPERS)
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
    goal_id = getattr(args, "goal", None) or rng.choice(list(GOALS))
    goal = _safe_lookup(GOALS, goal_id)
    tool = next((t for t in TOOLS if t.label == getattr(args, "tool", None)), None) if getattr(args, "tool", None) else select_tool(goal)
    if tool is None:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "tool", None) and tool.label != getattr(args, "tool", None):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, goal=goal_id, tool=tool.label, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    goal = _safe_lookup(GOALS, params.goal)
    tool = next(t for t in TOOLS if t.label == params.tool)
    hero_type = params.gender
    world = tell(setting, goal, tool, params.name, hero_type, params.helper, params.trait)
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
    StoryParams(place="yard", goal="ball", tool="stepstool", name="Mia", gender="girl", helper="mom", trait="silly"),
    StoryParams(place="garden", goal="kite", tool="pancake ladder", name="Ben", gender="boy", helper="dad", trait="curious"),
    StoryParams(place="playground", goal="cookie", tool="stack of boxes", name="Nora", gender="girl", helper="big sister", trait="bouncy"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show good_tool/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show good_tool/2."))
        combos = sorted(set(asp.atoms(model, "good_tool")))
        print(f"{len(combos)} compatible tool/goal pairs:\n")
        for tool, kind in combos:
            print(f"  {tool:16} -> {kind}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
            header = f"### {p.name}: {p.goal} in {p.place} with {p.tool}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
