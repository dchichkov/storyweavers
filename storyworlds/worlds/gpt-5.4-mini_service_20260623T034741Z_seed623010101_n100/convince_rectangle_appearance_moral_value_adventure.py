#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/convince_rectangle_appearance_moral_value_adventure.py
===============================================================================================================

A small adventure storyworld about a child, a careful choice, and the difference
between flashy appearance and real moral value.

Seed tale:
---
On a windy morning, Mira and her cousin Jory hiked toward the old stone bridge
at the edge of the green valley. They hoped to cross to the hill ruin where a
tiny bell was said to wait inside a cracked tower.

At the bridge, they found a wooden crate shaped like a neat rectangle, painted
bright red. Jory smiled at its fine appearance and wanted to use it as a stage
so everyone would think they were brave explorers. But the crate was meant to
hold stones for the broken bridge, and the valley workers needed it.

Mira tried to convince Jory that the box's appearance was less important than
doing the right thing. Together they carried the crate to the bridge, returned
the stones, and helped repair the path. When the little bell rang at last, Jory
understood that real adventure meant helping, not showing off.

World model:
---
- physical meters: carried, damaged, neat, repaired, worn, noticed
- emotional memes: desire, pride, trust, fairness, gratitude, shame, resolve

Causal beats:
---
- flashy temptation raises pride and desire
- an object with strong appearance can still be morally wrong to misuse
- carrying the right load increases repair and gratitude
- choosing help over show raises fairness/resolve and quiets shame
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
    role: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    load: str = ""
    pretty: bool = False
    hollow: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    c1: object | None = None
    c2: object | None = None
    helper_ent: object | None = None
    obj: object | None = None
    sign: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman"}
        male = {"boy", "father", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
class Setting:
    place: str
    route: str
    vista: str
    trail: str
    affordances: set[str] = field(default_factory=set)
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


@dataclass
class Temptation:
    id: str
    label: str
    phrase: str
    use: str
    show: str
    risk: str
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
class Load:
    id: str
    label: str
    phrase: str
    moral: str
    weight: str
    carries: str
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
class Help:
    id: str
    label: str
    phrase: str
    action: str
    result: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.route_open = False

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.route_open = self.route_open
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


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


def _r_notice(world: World) -> list[str]:
    out: list[str] = []
    if world.get("load").meters["noticed"] >= THRESHOLD and ("notice",) not in world.fired:
        world.fired.add(("notice",))
        world.get("child2").memes["resolve"] += 1
        out.append("The route was noticed.")
    return out


def _r_use_wrong(world: World) -> list[str]:
    out: list[str] = []
    temptation = world.facts["temptation"]
    load = world.get("load")
    if load.carried_by == world.get("child1").id and world.get("child1").memes["showoff"] >= THRESHOLD:
        sig = ("wrong_use",)
        if sig not in world.fired:
            world.fired.add(sig)
            load.meters["misused"] += 1
            world.get("child1").memes["shame"] += 1
            out.append("The pretty thing was being used for the wrong purpose.")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    if world.get("load").carried_by == world.get("child2").id and world.get("load").meters["repaired"] >= THRESHOLD:
        sig = ("repair",)
        if sig not in world.fired:
            world.fired.add(sig)
            world.route_open = True
            world.get("child2").memes["gratitude"] += 1
            world.get("child1").memes["fairness"] += 1
            out.append("The route grew safe again.")
    return out


CAUSAL_RULES = [Rule("notice", "social", _r_notice), Rule("wrong_use", "moral", _r_use_wrong), Rule("repair", "physical", _r_repair)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            s = rule.apply(world)
            if s:
                changed = True
                produced.extend(s)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_choice(temptation: Temptation, load: Load) -> bool:
    return temptation.id in {"rectangle_sign"} and load.id in {"bridge_crate"}


def valid_combos() -> list[tuple[str, str]]:
    return [(s, l) for s in SETTINGS for l in LOADS if valid_choice(TEMPTATIONS["rectangle_sign"], _safe_lookup(LOADS, l))]


@dataclass
class StoryParams:
    setting: str
    temptation: str
    load: str
    child1: str
    child1_gender: str
    child2: str
    child2_gender: str
    helper: str
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


SETTINGS = {
    "valley": Setting(place="the green valley", route="the old stone bridge", vista="a cracked tower", trail="the hill ruin path", affordances={"carry", "repair"}),
}
TEMPTATIONS = {
    "rectangle_sign": Temptation(
        id="rectangle_sign",
        label="the bright rectangle sign",
        phrase="a bright red rectangle sign",
        use="stand on it to look brave",
        show="fine appearance",
        risk="the right way to keep the path safe",
        tags={"rectangle", "appearance"},
    ),
}
LOADS = {
    "bridge_crate": Load(
        id="bridge_crate",
        label="the bridge crate",
        phrase="a crate of repair stones",
        moral="real help matters more than fancy appearance",
        weight="heavy enough to need two careful hands",
        carries="stones for the broken bridge",
        tags={"help", "moral"},
    ),
}
HELPS = {
    "repair": Help(
        id="repair",
        label="repair the bridge",
        phrase="put the stones back where they belonged",
        action="carry the crate to the bridge",
        result="make the path safe again",
        tags={"repair"},
    )
}

GIRL_NAMES = ["Mira", "Nina", "Tia", "Lena", "Ava", "Rosa"]
BOY_NAMES = ["Jory", "Ben", "Milo", "Keen", "Otis", "Rowan"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an adventure story for a young child that uses the words "convince", "rectangle", and "appearance".',
        f"Tell a moral adventure where {f['child1'].id} tries to convince {f['child2'].id} that a rectangle's appearance matters less than doing the right thing.",
        f"Write a small bridge adventure about helpers, a rectangle-shaped object, and a choice that shows real moral value.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    c1, c2, tem, load = f["child1"], f["child2"], f["temptation"], f["load"]
    return [
        QAItem(
            question=f"Why did {c1.id} try to convince {c2.id} about the rectangle?",
            answer=f"{c1.id} wanted {c2.id} to care more about doing the right thing than about the rectangle's appearance. The shiny look was tempting, but it did not help the bridge.",
        ),
        QAItem(
            question=f"What did the rectangle's appearance make {c2.id} want to do first?",
            answer=f"It made {c2.id} want to use it for showing off instead of helping. That choice would have ignored the real need at {world.setting.route}.",
        ),
        QAItem(
            question=f"What changed after they carried the crate together?",
            answer=f"They used the crate to repair the bridge, so the route became safe again. After that, {c2.id} felt grateful and {c1.id} felt fairness and pride in helping.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem("What is a rectangle?", "A rectangle is a shape with four straight sides and four corners. Many signs, doors, and boxes have a rectangle shape."),
        QAItem("What does appearance mean?", "Appearance means how something looks on the outside. Something can look fancy, plain, or even misleading."),
        QAItem("What is moral value?", "Moral value means whether a choice is right, fair, and helpful. A good-looking thing is not always the best choice."),
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
    out.append("== (3) World knowledge ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def tell(setting: Setting, temptation: Temptation, load: Load, child1: str, child1_gender: str, child2: str, child2_gender: str, helper: str) -> World:
    world = World(setting)
    c1 = world.add(Entity(id=child1, kind="character", type=child1_gender, role="convincer", traits=["bold"]))
    c2 = world.add(Entity(id=child2, kind="character", type=child2_gender, role="listener", traits=["careful"]))
    helper_ent = world.add(Entity(id="helper", kind="character", type=helper, role="helper", label="the helper"))
    obj = world.add(Entity(id="load", kind="thing", type="thing", label=load.label, phrase=load.phrase, carried_by=c2.id))
    sign = world.add(Entity(id="sign", kind="thing", type="thing", label=temptation.label, phrase=temptation.phrase, pretty=True))
    world.facts.update(child1=c1, child2=c2, helper=helper_ent, temptation=temptation, load=obj)

    world.say(f"{c1.id} and {c2.id} set out across {setting.place}, hoping to reach {setting.vista}.")
    world.say(f"Near {setting.route}, they found {temptation.phrase} with a striking appearance.")
    world.para()
    c1.memes["desire"] += 1
    c1.memes["showoff"] += 1
    c2.memes["trust"] += 1
    world.say(f"{c1.id} wanted to use the rectangle to seem brave, and {c1.id} tried to convince {c2.id} to agree.")
    world.say(f'But {c2.id} looked at the bridge crate and said, "The appearance is not the important part. We should help the bridge first."')
    c2.memes["fairness"] += 1
    c1.memes["moral_attention"] += 1
    world.para()
    obj.meters["noticed"] += 1
    obj.carried_by = c2.id
    obj.meters["repaired"] += 1
    world.say(f"Together they carried {load.phrase} onto {setting.route} and put the stones back where they belonged.")
    propagate(world, narrate=False)
    world.say(f"The bridge stood firm again, and the path to {setting.vista} opened for a true adventure.")
    world.say(f"At the end, {c1.id} learned that moral value mattered more than a flashy appearance.")
    world.facts.update(setting=setting, load=obj, sign=sign, route_open=world.route_open)
    return world


CURATED = [
    StoryParams(setting="valley", temptation="rectangle_sign", load="bridge_crate", child1="Mira", child1_gender="girl", child2="Jory", child2_gender="boy", helper="father"),
    StoryParams(setting="valley", temptation="rectangle_sign", load="bridge_crate", child1="Nina", child1_gender="girl", child2="Milo", child2_gender="boy", helper="mother"),
    StoryParams(setting="valley", temptation="rectangle_sign", load="bridge_crate", child1="Rowan", child1_gender="boy", child2="Ava", child2_gender="girl", helper="mother"),
]


ASP_RULES = r"""
valid(S,T,L) :- setting(S), temptation(T), load(L), rectangle(T), appearance(T), moral(L).
good_choice(C1,C2) :- convince(C1,C2), moral_value.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for tid, t in TEMPTATIONS.items():
        lines.append(asp.fact("temptation", tid))
        lines.append(asp.fact("rectangle", tid))
        lines.append(asp.fact("appearance", tid))
    for lid, l in LOADS.items():
        lines.append(asp.fact("load", lid))
        lines.append(asp.fact("moral", lid))
        lines.append(asp.fact("moral_value", lid))
    lines.append(asp.fact("convince", "story"))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import io
    import contextlib
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    ok = True
    if py != cl:
        ok = False
        print("MISMATCH between ASP and Python:", sorted(py ^ cl))
    try:
        sample = generate(resolve_params(build_parser().parse_args([]), random.Random(0)))
        assert sample.story
    except Exception as e:
        ok = False
        print(f"SMOKE TEST FAILED: {e}")
    print("OK" if ok else "FAIL")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Adventure storyworld about convincing, rectangles, and moral value.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--load", choices=LOADS)
    ap.add_argument("--child1")
    ap.add_argument("--child2")
    ap.add_argument("--child1-gender", choices=["girl", "boy"])
    ap.add_argument("--child2-gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father"])
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
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "temptation", None) is None or c[1] == getattr(args, "temptation", None))
              and (getattr(args, "load", None) is None or c[2] == getattr(args, "load", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, temptation, load = (list(rng.choice(combos)) + [None, None, None])[:3]
    c1g = getattr(args, "child1_gender", None) or rng.choice(["girl", "boy"])
    c2g = getattr(args, "child2_gender", None) or ("boy" if c1g == "girl" else "girl")
    c1 = getattr(args, "child1", None) or rng.choice(GIRL_NAMES if c1g == "girl" else BOY_NAMES)
    c2pool = [n for n in (GIRL_NAMES if c2g == "girl" else BOY_NAMES) if n != c1]
    c2 = getattr(args, "child2", None) or rng.choice(c2pool)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father"])
    return StoryParams(setting=setting, temptation=temptation, load=load, child1=c1, child1_gender=c1g, child2=c2, child2_gender=c2g, helper=helper)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.temptation not in TEMPTATIONS or params.load not in LOADS:
        pass
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(TEMPTATIONS, params.temptation), _safe_lookup(LOADS, params.load), params.child1, params.child1_gender, params.child2, params.child2_gender, params.helper)
    return StorySample(params=params, story=world.render(), prompts=generation_prompts(world), story_qa=story_qa(world), world_qa=world_knowledge_qa(world), world=world)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print("--- trace ---")
        for e in sample.world.entities.values():
            print(e.id, dict(e.meters), dict(e.memes))
    if qa:
        print()
        print(format_qa(sample))


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_combos():
            print(row)
        return
    base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            p = resolve_params(args, random.Random(base + i))
            p.seed = base + i
            samples.append(generate(p))
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, s in enumerate(samples):
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i + 1 < len(samples):
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
