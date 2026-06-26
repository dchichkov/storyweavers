#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/conscience_stellar_scissor_moral_value_fable.py
====================================================================================================

A small fable-world about conscience, a stellar pair of scissors, and the
moral value of choosing the right use for a tempting tool.

The tale shape is classical and child-facing:
- setup: a young creature finds or wants a bright thing
- tension: conscience warns that the bright thing should not be used selfishly
- turn: the hero chooses a fairer path
- ending: the world proves the choice changed something real

This script is self-contained and uses only the stdlib plus the shared
storyworld result containers. ASP support is inline and mirrors the Python
reasonableness gate.
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
    worn_by: Optional[str] = None
    meter: dict[str, float] = field(default_factory=dict)
    meme: dict[str, float] = field(default_factory=dict)

    region: object | None = None
    conscience: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "hen"}
        male = {"boy", "father", "dad", "man", "fox", "wolf"}
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
class Setting:
    place: str
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    harm: str
    zone: set[str]
    keyword: str
    moral_value: str
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
class Prize:
    label: str
    phrase: str
    region: str
    value: str
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
    covers: set[str]
    helps: set[str]
    prep: str
    tail: str
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _said(world: World, key: tuple) -> bool:
    if key in world.fired:
        return True
    world.fired.add(key)
    return False


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for ent in list(world.entities.values()):
            if ent.meme.get("sting", 0.0) >= THRESHOLD and not _said(world, ("sting", ent.id)):
                ent.meme["conscience"] = ent.meme.get("conscience", 0.0) + 1.0
                out.append(f"{ent.id} felt a little pinch in conscience.")
                changed = True
            if ent.meme.get("greed", 0.0) >= THRESHOLD and ent.meme.get("conscience", 0.0) >= THRESHOLD:
                if not _said(world, ("waver", ent.id)):
                    ent.meme["waver"] = 1.0
                    out.append(f"{ent.id} paused, because conscience would not stay quiet.")
                    changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def reason_gate(activity: Activity, prize: Prize, tool: Tool) -> bool:
    return prize.region in activity.zone and prize.region in tool.covers and activity.keyword in tool.helps


def explain_rejection(activity: Activity, prize: Prize, tool: Tool) -> str:
    return (
        f"(No story: {tool.label} does not fairly solve {activity.gerund} for a {prize.label} "
        f"on the {prize.region}. The tool must truly cover the at-risk part.)"
    )


def predict(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"ruined": prize.meter.get("torn", 0.0) >= THRESHOLD}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    actor.meter[activity.keyword] = actor.meter.get(activity.keyword, 0.0) + 1.0
    if narrate:
        world.say(f"{actor.id} did not resist and began {activity.gerund}.")
    for ent in list(world.entities.values()):
        if ent.owner == actor.id and ent.label == "banner" and prize_risk(activity, ent):
            ent.meter["torn"] = ent.meter.get("torn", 0.0) + 1.0
            if narrate:
                world.say(f"The {ent.label} got torn by the sharp motion.")


def prize_risk(activity: Activity, prize: Entity) -> bool:
    return prize.region in activity.zone


def select_tool(activity: Activity, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if reason_gate(activity, prize, tool):
            return tool
    return None


def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str, hero_type: str, moral_value: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type,
                            traits=["little", "bright"], meme={"greed": 0.0, "conscience": 0.0}))
    conscience = world.add(Entity(id="Conscience", kind="character", type="owl", label="conscience"))
    prize = world.add(Entity(id="banner", type="banner", label="banner", phrase=prize_cfg.phrase,
                             owner=hero.id, region=prize_cfg.region))
    hero.meme["greed"] = 1.0
    world.say(f"{hero.id} was a little {hero.type} who loved shiny things and tried to look stellar.")
    world.say(f"Near the shed lay a bright pair of stellar scissors, and {hero.id} wanted to use them at once.")
    world.para()
    world.say(f"In the {world.setting.place}, {hero.id} saw the {prize_cfg.phrase} and wished to snip a bit from it.")
    world.say(f"But conscience nudged {hero.id} and whispered that a tool should not be used for a selfish cut.")
    hero.meme["sting"] = 1.0
    propagate(world)
    world.say(f"{hero.id} hesitated, because {conscience.id.lower()} was right.")
    world.para()
    tool = select_tool(activity, prize_cfg)
    if tool is None:
        return world
    world.say(f"Then {hero.id} chose a fairer plan: {tool.prep}.")
    do_activity(world, hero, activity, narrate=True)
    hero.meme["greed"] = 0.0
    hero.meme["kindness"] = 1.0
    world.say(f"{hero.id} used the stellar scissors only where they were meant to help, not to take what was not theirs.")
    world.say(f"{tool.tail}, and the {prize.label} stayed whole.")
    world.say(f"The moral value of {moral_value} shone brighter than the shiny metal.")
    world.facts.update(hero=hero, conscience=conscience, prize=prize, tool=tool,
                       activity=activity, setting=setting, moral_value=moral_value)
    return world


SETTINGS = {
    "shed": Setting(place="the garden shed", affords={"trim"}),
    "meadow": Setting(place="the meadow", affords={"trim"}),
    "workbench": Setting(place="the workbench by the window", affords={"trim"}),
}

ACTIVITIES = {
    "trim": Activity(
        id="trim",
        verb="trim a loose ribbon",
        gerund="trimming",
        rush="snip at the banner",
        harm="torn",
        zone={"torso"},
        keyword="trim",
        moral_value="care",
    ),
}

PRIZES = {
    "banner": Prize(
        label="banner",
        phrase="a star banner",
        region="torso",
        value="care",
    ),
    "cloak": Prize(
        label="cloak",
        phrase="a velvet cloak",
        region="torso",
        value="truth",
    ),
}

TOOLS = [
    Tool(
        id="stellar_scissors",
        label="stellar scissors",
        covers={"torso"},
        helps={"trim"},
        prep="first ask permission and cut only the loose ribbon",
        tail="The ribbon was shortened neatly",
    ),
]

NAMES = ["Pip", "Mira", "Jun", "Tala", "Rin", "Pico"]
TYPES = ["mouse", "rabbit", "sparrow", "squirrel", "hedgehog"]
MORAL_VALUES = ["care", "honesty", "kindness", "fairness"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    kind: str
    moral_value: str
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


KNOWLEDGE = {
    "scissor": [("What are scissors for?",
                 "Scissors are tools for cutting paper, cloth, string, and other things carefully.")],
    "stellar": [("What does stellar mean?",
                 "Stellar means very bright, excellent, or like the stars.")],
    "conscience": [("What is conscience?",
                    "Conscience is the quiet inner feeling that helps you know what is right and wrong.")],
    "care": [("Why is care important?",
              "Care helps you protect things, avoid harm, and treat people kindly.")],
    "honesty": [("What does honesty mean?",
                 "Honesty means telling the truth and not pretending something wrong is right.")],
    "fairness": [("What is fairness?",
                  "Fairness means giving things a proper share and not taking more than your part.")],
    "kindness": [("What is kindness?",
                  "Kindness means helping, sharing, and being gentle with others.")],
}


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("moral", aid, a.moral_value))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        lines.append(asp.fact("value", pid, p.value))
    for t in TOOLS:
        lines.append(asp.fact("tool", t.id))
        for c in sorted(t.covers):
            lines.append(asp.fact("covers", t.id, c))
        for h in sorted(t.helps):
            lines.append(asp.fact("helps", t.id, h))
    return "\n".join(lines)


ASP_RULES = r"""
reasonably_valid(P,A,T) :- affords(P,A), prize(Pi), worn_on(Pi,R), zone(A,R),
                           tool(T), covers(T,R), helps(T,A).
#show reasonably_valid/3.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program(""))
    return sorted(set(asp.atoms(model, "reasonably_valid")))


def valid_combos() -> list[tuple[str, str, str]]:
    out: list[tuple[str, str, str]] = []
    for place in SETTINGS:
        for act_id in ACTIVITIES:
            for prize_id, prize in PRIZES.items():
                if reason_gate(_safe_lookup(ACTIVITIES, act_id), prize, _safe_lookup(TOOLS, 0)):
                    out.append((place, act_id, prize_id))
    return out


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Fable world: conscience, stellar scissors, and moral value.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--kind", choices=TYPES)
    ap.add_argument("--moral-value", choices=MORAL_VALUES)
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
    combo = (getattr(args, "place", None) or "shed", getattr(args, "activity", None) or "trim", getattr(args, "prize", None) or "banner")
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        if not reason_gate(_safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None)), _safe_lookup(TOOLS, 0)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "moral_value", None) and getattr(args, "prize", None) and getattr(args, "moral_value", None) != _safe_lookup(PRIZES, getattr(args, "prize", None)).value:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, act, prize = combo
    return StoryParams(
        place=place,
        activity=act,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        kind=getattr(args, "kind", None) or rng.choice(TYPES),
        moral_value=getattr(args, "moral_value", None) or _safe_lookup(PRIZES, prize).value,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short fable for children about conscience and {f['moral_value']}.",
        f"Tell a story where {f['hero'].id} finds stellar scissors but chooses a fair use for them.",
        f"Make a gentle moral tale in which a bright tool, a warning conscience, and a careful choice lead to a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    prize = _safe_fact(world, f, "prize")
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"What did {hero.id} want to do with the stellar scissors at first?",
            answer=f"At first {hero.id} wanted to use the stellar scissors too quickly, even though the {prize.label} was not theirs to cut.",
        ),
        QAItem(
            question="Why did conscience speak up?",
            answer=f"Conscience spoke up because using the stellar scissors selfishly would have harmed the {prize.label}, and the right choice was to be careful.",
        ),
        QAItem(
            question=f"What did {hero.id} choose instead of taking from the {prize.label}?",
            answer=f"{hero.id} chose the fairer plan and used {tool.label} only for the loose ribbon, so the {prize.label} stayed whole.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    for key in ["scissor", "stellar", "conscience", world.facts["moral_value"]]:
        for q, a in KNOWLEDGE.get(key, []):
            out.append(QAItem(question=q, answer=a))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i+1}. {p}" for i, p in enumerate(sample.prompts)], "",
             "== (2) Story questions =="]
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
        bits = []
        if e.traits:
            bits.append(f"traits={e.traits}")
        if e.meter:
            bits.append(f"meters={e.meter}")
        if e.meme:
            bits.append(f"memes={e.meme}")
        lines.append(f"  {e.id:12} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="shed", activity="trim", prize="banner", name="Pip", kind="mouse", moral_value="care"),
    StoryParams(place="workbench", activity="trim", prize="cloak", name="Mira", kind="rabbit", moral_value="honesty"),
]


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize),
                 params.name, params.kind, params.moral_value)
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


def valid_story_combos() -> list[tuple]:
    return [(p, a, pr) for (p, a, pr) in valid_combos()]


def asp_verify() -> int:
    import asp
    py = set(valid_story_combos())
    cl = set(asp_valid())
    if py == cl:
        print(f"OK: clingo gate matches python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only python:", sorted(py - cl))
    print("only clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show reasonably_valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        vals = asp_valid()
        print(f"{len(vals)} valid combos")
        for t in vals:
            print(t)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            rng = random.Random(base_seed + i)
            i += 1
            try:
                params = resolve_params(args, rng)
            except StoryError:
                continue
            params.seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} in {p.place} ({p.moral_value})"
        elif len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
