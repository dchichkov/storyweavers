#!/usr/bin/env python3
"""
storyworlds/worlds/return_community_garden_repetition_reconciliation_adventure.py
==================================================================================

A small story world about a child returning to a community garden, where a
repeated mistake creates trouble and a reconciliation turns the day into an
adventure again.

The seed premise:
- A child returns to a community garden.
- Something keeps happening again and again.
- A disagreement grows, then is repaired.
- The ending should feel like a completed adventure, not just a report.

This world models:
- physical meters: distance, carry, mess, repair, growth, rest
- emotional memes: joy, worry, stubbornness, hurt, trust, relief, apology, welcome

The compatible story shape is:
1) return to the garden
2) repetition of one small problem
3) a disagreement or missed handoff
4) reconciliation through apology and shared work
5) a concrete ending image proving things changed
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    tags: set[str] = field(default_factory=set)

    child: object | None = None
    helper: object | None = None
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
    place: str = "the community garden"
    home: str = "the front gate"
    allows: set[str] = field(default_factory=set)
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
class Task:
    id: str
    verb: str
    gerund: str
    repeated_action: str
    snag: str
    fix: str
    risk: str
    tag: str
    mess: str = "tired"
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
    phrase: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
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
class StoryParams:
    place: str
    task: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()

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
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy as _copy
        w = World(self.setting)
        w.entities = _copy.deepcopy(self.entities)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        w.fired = set(self.fired)
        return w

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.owner == actor.id and e.kind == "tool"]


THRESHOLD = 1.0


def _advance_repetition(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.kind != "character":
            continue
        if e.meters.get("repetition", 0) < THRESHOLD:
            continue
        sig = ("repeat", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["frustration"] = e.memes.get("frustration", 0) + 1
        out.append(f"Again and again, the same little problem kept coming back.")
    return out


def _advance_broken_trust(world: World) -> list[str]:
    out: list[str] = []
    for e in list(world.entities.values()):
        if e.kind != "character":
            continue
        if e.memes.get("hurt", 0) < THRESHOLD or e.memes.get("apology", 0) < THRESHOLD:
            continue
        sig = ("reconcile", e.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        e.memes["trust"] = e.memes.get("trust", 0) + 1
        e.memes["hurt"] = 0
        out.append(f"The hurt softened into trust.")
    return out


CAUSAL_RULES = [_advance_repetition, _advance_broken_trust]


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


SETTINGS = {
    "community_garden": Setting(
        place="the community garden",
        home="the front gate",
        allows={"water", "weed", "harvest"},
    )
}

TASKS = {
    "water": Task(
        id="water",
        verb="water the seedlings",
        gerund="watering the seedlings",
        repeated_action="kept spilling the little bucket again",
        snag="the water kept sloshing onto the path",
        fix="pour from the low blue cup with two hands",
        risk="the path would get muddy and the seedlings might miss their water",
        tag="water",
    ),
    "weed": Task(
        id="weed",
        verb="pull the weeds",
        gerund="pulling weeds",
        repeated_action="kept tugging at the wrong stems again",
        snag="the same tiny weeds kept hiding among the beans",
        fix="follow the yellow string row by row",
        risk="the good plants might get pulled by mistake",
        tag="garden",
    ),
    "harvest": Task(
        id="harvest",
        verb="pick ripe tomatoes",
        gerund="picking ripe tomatoes",
        repeated_action="kept choosing the red ones again and again",
        snag="the basket filled too fast and one branch bent low",
        fix="share the basket and count together",
        risk="the branch might bend and the smaller children might be left out",
        tag="fruit",
    ),
}

TOOLS = [
    Tool(
        id="cup",
        label="a low blue cup",
        phrase="a low blue cup with a wide rim",
        covers={"hands"},
        guards={"water"},
        prep="slow down and use the low blue cup",
        tail="carried the cup carefully back to the beds",
    ),
    Tool(
        id="string",
        label="a yellow string guide",
        phrase="a yellow string guide stretched beside the bean row",
        covers={"eyes"},
        guards={"weed"},
        prep="follow the yellow string together",
        tail="walked the row from the first bean to the last",
    ),
    Tool(
        id="basket",
        label="the shared basket",
        phrase="the shared basket with two handles",
        covers={"hands"},
        guards={"fruit"},
        prep="share the basket and take turns",
        tail="went back and forth until the basket was full",
        plural=False,
    ),
]

GIRL_NAMES = ["Maya", "Lena", "Iris", "Nora", "Ava", "Zoe", "Lily"]
BOY_NAMES = ["Noah", "Eli", "Finn", "Theo", "Leo", "Jack", "Sam"]
TRAITS = ["brave", "curious", "gentle", "spirited", "patient", "hopeful"]


def choose_tool(task: Task) -> Optional[Tool]:
    for tool in TOOLS:
        if task.id in tool.guards:
            return tool
    return None


def valid_combos() -> list[tuple[str, str]]:
    return [("community_garden", t) for t in TASKS if choose_tool(_safe_lookup(TASKS, t)) is not None]


def setting_detail(setting: Setting, task: Task) -> str:
    return f"{setting.place.capitalize()} smelled like soil and mint, and the rows stood neat and bright."


def intro(world: World, child: Entity) -> None:
    trait = next((t for t in child.tags if t != "little"), "curious")
    world.say(f"{child.id} was a little {trait} {child.type} who loved the path back to the garden.")
    world.say("The beans climbed their poles, and the tomatoes shone like small red lanterns.")


def return_to_garden(world: World, child: Entity, helper: Entity, task: Task) -> None:
    world.say(
        f"One afternoon, {child.id} returned to {world.setting.place} with {child.pronoun('possessive')} {helper.label}."
    )
    world.say(setting_detail(world.setting, task))


def repeated_problem(world: World, child: Entity, task: Task) -> None:
    child.meters["repetition"] = child.meters.get("repetition", 0) + 1
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    world.say(f"{child.id} tried to {task.verb}, but {task.repeated_action}.")
    propagate(world, narrate=True)


def warning(world: World, helper: Entity, child: Entity, task: Task) -> None:
    child.memes["stubbornness"] = child.memes.get("stubbornness", 0) + 1
    child.memes["hurt"] = child.memes.get("hurt", 0) + 1
    world.say(
        f'"If it keeps happening like that," {helper.id} said, "we will have to stop and try a safer way."'
    )
    world.say(f"{child.id} frowned, because {task.risk}.")


def split_apart(world: World, child: Entity) -> None:
    world.say(f"{child.id} turned away, then looked back at the garden path in silence.")
    world.say(f"The same trouble felt even bigger after the second try.")


def apology_and_fix(world: World, child: Entity, helper: Entity, task: Task, tool: Tool) -> None:
    child.memes["apology"] = child.memes.get("apology", 0) + 1
    helper.memes["hurt"] = 0
    world.say(
        f"{child.id} took a breath and said sorry for not listening. {helper.id} nodded, then smiled."
    )
    world.say(
        f'"How about we {tool.prep}?" {helper.id} asked.'
    )
    world.say(
        f"So they {tool.tail}, and the work became calm and steady instead of rushed."
    )
    child.memes["joy"] = child.memes.get("joy", 0) + 1
    child.memes["relief"] = child.memes.get("relief", 0) + 1
    helper.memes["trust"] = helper.memes.get("trust", 0) + 1
    propagate(world, narrate=True)


def ending(world: World, child: Entity, helper: Entity, task: Task) -> None:
    if task.id == "water":
        world.say(
            f"By the end, the seedlings sparkled, the path stayed dry, and {child.id} carried the little cup home like treasure."
        )
    elif task.id == "weed":
        world.say(
            f"By the end, the bean row was clear, the yellow string stayed straight, and {child.id} could point to each plant with pride."
        )
    else:
        world.say(
            f"By the end, the basket was full, the tomatoes were safe, and {child.id} and {helper.id} left the garden laughing together."
        )


def tell(setting: Setting, task: Task, tool: Tool, name: str, gender: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, tags={"little", trait}))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the gardener"))
    world.add(Entity(id="Tool", kind="tool", label=tool.label, phrase=tool.phrase, plural=tool.plural, owner=child.id))

    intro(world, child)
    world.para()
    return_to_garden(world, child, helper, task)
    repeated_problem(world, child, task)
    warning(world, helper, child, task)
    split_apart(world, child)
    world.para()
    apology_and_fix(world, child, helper, task, tool)
    ending(world, child, helper, task)

    world.facts.update(
        child=child,
        helper=helper,
        task=task,
        tool=tool,
        setting=setting,
        reconciled=child.memes.get("apology", 0) >= THRESHOLD,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    task = _safe_fact(world, f, "task")
    return [
        f'Write a short adventure story about {child.id} returning to a community garden and repeating a small mistake while {task.gerund}.',
        f"Tell a gentle tale where a little {child.type} named {child.id} goes back to the community garden, has trouble again, and then makes up with the gardener.",
        f'Write a child-friendly adventure about the community garden, with repetition, apology, and a happy return to the work.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    task = _safe_fact(world, f, "task")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Where did {child.id} return at the start of the story?",
            answer=f"{child.id} returned to {world.setting.place}, where the beans, tomatoes, and paths were waiting.",
        ),
        QAItem(
            question=f"What problem kept happening again while {child.id} tried to {task.verb}?",
            answer=f"The problem was that {task.repeated_action}, so the same trouble came back more than once.",
        ),
        QAItem(
            question=f"What did the gardener suggest after {child.id} felt stuck?",
            answer=f"{helper.id} suggested using {tool.label} and doing the job in a calmer, safer way.",
        ),
        QAItem(
            question=f"How did {child.id} and the gardener fix the disagreement?",
            answer=f"{child.id} apologized, {helper.id} accepted it, and they worked together with {tool.label} until the task felt easy again.",
        ),
        QAItem(
            question=f"What changed at the end of the story?",
            answer=f"The garden work got finished, the hurt feelings turned into trust again, and {child.id} left with a happy, steady feeling.",
        ),
    ]


WORLD_KNOWLEDGE = {
    "garden": [
        QAItem(
            question="What is a community garden?",
            answer="A community garden is a shared place where people grow flowers, vegetables, and herbs together.",
        ),
        QAItem(
            question="Why do gardens need water?",
            answer="Gardens need water so seeds and plants can grow strong and stay healthy.",
        ),
    ],
    "repetition": [
        QAItem(
            question="What does repetition mean?",
            answer="Repetition means doing the same thing again and again.",
        )
    ],
    "reconciliation": [
        QAItem(
            question="What is reconciliation?",
            answer="Reconciliation is when people repair a hurt feeling and become friendly again.",
        )
    ],
    "adventure": [
        QAItem(
            question="What makes a day feel like an adventure?",
            answer="A day can feel like an adventure when there is a goal to reach, a problem to solve, and brave teamwork.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return WORLD_KNOWLEDGE["garden"] + WORLD_KNOWLEDGE["repetition"] + WORLD_KNOWLEDGE["reconciliation"] + WORLD_KNOWLEDGE["adventure"]


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for q in sample.story_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    lines.append("")
    lines.append("== (3) World knowledge questions ==")
    for q in sample.world_qa:
        lines.append(f"Q: {q.question}")
        lines.append(f"A: {q.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.label:
            bits.append(f"label={e.label}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: " + " ".join(bits))
    return "\n".join(lines)


CURATED = [
    StoryParams(place="community_garden", task="water", tool="cup", name="Maya", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="community_garden", task="weed", tool="string", name="Noah", gender="boy", helper="father", trait="patient"),
    StoryParams(place="community_garden", task="harvest", tool="basket", name="Lily", gender="girl", helper="mother", trait="brave"),
]


def prize_at_risk(task: Task, tool: Tool) -> bool:
    return task.id in tool.guards


def valid_story_combo(task: Task) -> bool:
    return choose_tool(task) is not None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place in SETTINGS:
        for task_id, task in TASKS.items():
            if place == "community_garden" and valid_story_combo(task):
                out.append((place, task_id))
    return out


def explain_rejection(task: Task) -> str:
    return f"(No story: there is no reasonable tool that fits the repeated {task.id} problem in the community garden.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child returns to a community garden, repeats a mistake, and reconciles through teamwork.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--task", choices=TASKS)
    ap.add_argument("--tool", choices=[t.id for t in TOOLS])
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "gardener"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if getattr(args, "task", None) and getattr(args, "tool", None):
        task = _safe_lookup(TASKS, getattr(args, "task", None))
        tool = next(t for t in TOOLS if t.id == getattr(args, "tool", None))
        if not prize_at_risk(task, tool):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "task", None):
        combos = [c for c in combos if c[1] == getattr(args, "task", None)]
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, task_id = rng.choice(list(combos))
    task = _safe_lookup(TASKS, task_id)
    tool = choose_tool(task)
    if getattr(args, "tool", None):
        tool = next(t for t in TOOLS if t.id == getattr(args, "tool", None))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "gardener"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, task=task_id, tool=tool.id, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(TASKS, params.task),
        next(t for t in TOOLS if t.id == params.tool),
        params.name,
        params.gender,
        params.helper,
        params.trait,
    )
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
place(community_garden).
task(water). task(weed). task(harvest).
tool(cup). tool(string). tool(basket).

guards(cup, water).
guards(string, weed).
guards(basket, fruit).

valid(Place, Task) :- place(Place), task(Task), tool(T), guards(T, Task).
#show valid/2.
"""


def asp_facts() -> str:
    import asp
    lines = [asp.fact("place", "community_garden")]
    for t in TASKS:
        lines.append(asp.fact("task", t))
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for g in sorted(tool.guards):
            lines.append(asp.fact("guards", tool.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

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
            header = f"### {p.name}: {p.task} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
