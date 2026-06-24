#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260624T090150Z_seed197402754_n1000/gown_addictive_result_grocery_store_magic_detective.py
================================================================================

A small detective-style story world set in a grocery store.

Seed tale idea:
A child detective notices that a fancy gown in a grocery store display is
acting strangely. It feels almost addictive to look at, and the odd magic in
the aisle has a clear result: shoppers keep drifting back to the dress rack
instead of finishing their errands. The detective follows clues, finds the
source of the spell, and fixes the problem before the store gets too chaotic.

The world keeps the prose state-driven:
- the gown can be enchanted or plain
- the magic can cause fascination and repeated visits
- the result of the spell changes shopper behavior and the detective's plan
- resolution comes from a concrete physical change in the store

This script follows the Storyweavers contract:
- standalone stdlib script
- eager results import for QAItem, StoryError, StorySample
- lazy asp import only inside ASP helpers
- build_parser, resolve_params, generate, emit, main
- supports default run, -n, --all, --seed, --trace, --qa, --json, --asp,
  --verify, and --show-asp
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

@dataclass
class Entity:
    id: str
    kind: str = "thing"                 # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    clerk: object | None = None
    detective: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "daughter"}
        male = {"boy", "man", "father", "dad", "son"}
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
    place: str = "the grocery store"
    affords: set[str] = field(default_factory=set)
    SETTING: object | None = None
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
class Case:
    id: str
    clue_word: str
    result_word: str
    magical_effect: str
    detective_action: str
    twist: str
    tag: str = "magic"
    CASE: object | None = None
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
    type: str
    location: str
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
    PRIZE: object | None = None
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
    action: str
    result: str
    neutralizes: set[str] = field(default_factory=set)
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
        return clone


SETTING = Setting(place="the grocery store", affords={"magic"})
CASE = Case(
    id="gown_case",
    clue_word="gown",
    result_word="addictive",
    magical_effect="addictive",
    detective_action="follow the magic trail",
    twist="the spell was hiding in a price tag",
    tag="magic",
)

PRIZE = Prize(
    label="gown",
    phrase="a blue satin gown",
    type="gown",
    location="dress aisle",
)

TOOLS = [
    Tool(
        id="salt",
        label="a little packet of salt",
        action="sprinkle salt around the hem",
        result="break the spell",
        neutralizes={"magic"},
    ),
    Tool(
        id="receipt",
        label="the torn receipt",
        action="match the torn receipt to the gown",
        result="find the hidden clue",
        neutralizes={"magic"},
    ),
]

GIRL_NAMES = ["Mina", "Nora", "Ivy", "Ella", "June", "Pia", "Luna"]
BOY_NAMES = ["Theo", "Finn", "Leo", "Max", "Owen", "Ben", "Eli"]
TRAITS = ["curious", "sharp-eyed", "patient", "brave", "clever"]


def prize_at_risk(case: Case, prize: Prize) -> bool:
    return case.clue_word == prize.type and case.result_word == "addictive"


def select_tool(case: Case, prize: Prize) -> Optional[Tool]:
    for tool in TOOLS:
        if case.tag in tool.neutralizes:
            return tool
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in {"grocery_store": SETTING}.items():
        for case in [CASE]:
            for prize in [PRIZE]:
                if prize_at_risk(case, prize) and select_tool(case, prize):
                    combos.append((place, case.id, prize.type))
    return combos


def _narrate_magic(world: World, detective: Entity, case: Case, prize: Entity) -> None:
    detective.memes["focus"] = detective.memes.get("focus", 0) + 1
    detective.memes["wonder"] = detective.memes.get("wonder", 0) + 1
    world.say(
        f"{detective.id} was a little detective who noticed strange things other people missed."
    )
    world.say(
        f"At {world.setting.place}, {detective.pronoun('subject').capitalize()} spotted "
        f"{prize.phrase} hanging in the {prize.location}."
    )
    world.say(
        f"The gown looked {case.result_word} in a way that made people stop and stare."
    )


def _narrate_clue(world: World, detective: Entity, clerk: Entity, prize: Entity) -> None:
    world.say(
        f"A clerk whispered that shoppers kept circling back to the gown, and no one knew why."
    )
    world.say(
        f"{detective.id} bent down, looked at the tag, and said the clue had to be small, not loud."
    )


def _narrate_investigation(world: World, detective: Entity, case: Case, prize: Entity) -> None:
    detective.memes["curiosity"] = detective.memes.get("curiosity", 0) + 1
    world.say(
        f"{detective.id} decided to {case.detective_action}."
    )
    world.say(
        f"{detective.pronoun('subject').capitalize()} followed the shine from the gown to the price tag, then to the shelf."
    )


def _narrate_warning(world: World, detective: Entity, clerk: Entity, prize: Entity, case: Case) -> None:
    world.say(
        f'"This gown is almost {case.result_word}," {detective.pronoun("possessive")} detective voice said. '
        f'"That kind of magic makes people come back again and again."'
    )
    world.say(
        f"The clerk frowned because the result was not a happy one: shoppers were forgetting their lists."
    )


def _narrate_fix(world: World, detective: Entity, clerk: Entity, prize: Entity, tool: Tool) -> None:
    world.say(
        f"{detective.id} held up {tool.label} and asked the clerk to help."
    )
    world.say(
        f"They used it to {tool.action}, and soon the magic began to fade."
    )


def _narrate_resolution(world: World, detective: Entity, clerk: Entity, prize: Entity) -> None:
    detective.memes["satisfaction"] = detective.memes.get("satisfaction", 0) + 1
    world.say(
        f"In the end, the gown was still pretty, but it no longer pulled people back like a magnet."
    )
    world.say(
        f"The result was better for everyone: shoppers finished their errands, and the store got quiet again."
    )


def tell(setting: Setting, case: Case, prize_cfg: Prize,
         name: str = "Mina", gender: str = "girl",
         trait: str = "curious") -> World:
    world = World(setting)
    detective = world.add(Entity(
        id=name,
        kind="character",
        type=gender,
        meters={"energy": 1.0},
        memes={"focus": 0.0, "wonder": 0.0, "curiosity": 0.0, "satisfaction": 0.0},
    ))
    clerk = world.add(Entity(
        id="Clerk",
        kind="character",
        type="woman",
        label="the clerk",
        meters={"busy": 1.0},
        memes={"worry": 0.0},
    ))
    prize = world.add(Entity(
        id="gown",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        caretaker=clerk.id,
        meters={"shine": 1.0},
    ))

    detective.traits = [trait]  # type: ignore[attr-defined]

    _narrate_magic(world, detective, case, prize)
    world.para()
    _narrate_clue(world, detective, clerk, prize)
    _narrate_investigation(world, detective, case, prize)

    world.para()
    if prize_at_risk(case, prize_cfg):
        world.say(
            f"That was the result of the spell: every time someone looked at the gown, they wanted one more glance."
        )
        _narrate_warning(world, detective, clerk, prize, case)
        tool = select_tool(case, prize_cfg)
        if tool is None:
            pass
        detective.memes["resolve"] = detective.memes.get("resolve", 0) + 1
        _narrate_fix(world, detective, clerk, prize, tool)
        _narrate_resolution(world, detective, clerk, prize)

    world.facts.update(
        detective=detective,
        clerk=clerk,
        prize=prize,
        case=case,
        tool=select_tool(case, prize_cfg),
        setting=setting,
        resolved=True,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    d = _safe_fact(world, f, "detective")
    c = _safe_fact(world, f, "case")
    return [
        f'Write a short detective story for a small child set in a grocery store, using the words "{c.clue_word}", "{c.result_word}", and "magic".',
        f"Tell a gentle mystery where {d.id} notices a {c.clue_word} in a grocery store and works out why the spell feels {c.result_word}.",
        f"Write a simple story about a detective who follows magic clues in a grocery store and fixes the result before shopping gets chaotic.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    detective: Entity = _safe_fact(world, f, "detective")
    clerk: Entity = _safe_fact(world, f, "clerk")
    prize: Entity = _safe_fact(world, f, "prize")
    case: Case = _safe_fact(world, f, "case")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        QAItem(
            question=f"Who solved the mystery in the grocery store?",
            answer=f"{detective.id} solved it by noticing the magic around the gown and following the clues carefully.",
        ),
        QAItem(
            question=f"What was strange about the gown?",
            answer=f"The gown felt {case.result_word}, which meant people kept noticing it and drifting back to look again.",
        ),
        QAItem(
            question=f"Why was the clerk worried?",
            answer=f"The clerk was worried because the spell's result made shoppers forget their lists and keep circling back to the gown.",
        ),
        QAItem(
            question=f"What did {detective.id} use to fix the problem?",
            answer=f"{detective.id} used {tool.label} to help break the magic and make the gown ordinary again.",
        ),
        QAItem(
            question=f"What changed at the end?",
            answer=f"The gown stayed pretty, but it stopped pulling people back, so the grocery store became calm again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a detective for?",
            answer="A detective looks for clues and tries to figure out what happened.",
        ),
        QAItem(
            question="What is a grocery store?",
            answer="A grocery store is a place where people buy food and other everyday things.",
        ),
        QAItem(
            question="What does magic mean in stories?",
            answer="Magic in stories is a special kind of impossible power that can make strange things happen.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for p in sample.prompts:
        lines.append(p)
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
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.label:
            bits.append(f"label={e.label}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(C, P) :- case(C), prize(P), clue(C, gown), result_word(C, addictive), prize_type(P, gown).
has_tool(C, T) :- case(C), tool(T), neutralizes(T, magic).
valid_story(place, C, P) :- setting(place), prize_at_risk(C, P), has_tool(C, _).
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("setting", "grocery_store"),
        asp.fact("case", CASE.id),
        asp.fact("clue", CASE.id, CASE.clue_word),
        asp.fact("result_word", CASE.id, CASE.result_word),
        asp.fact("tag", CASE.id, CASE.tag),
        asp.fact("prize", PRIZE.type),
        asp.fact("prize_type", PRIZE.type, PRIZE.type),
    ]
    for tool in TOOLS:
        lines.append(asp.fact("tool", tool.id))
        for n in sorted(tool.neutralizes):
            lines.append(asp.fact("neutralizes", tool.id, n))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


@dataclass
class StoryParams:
    place: str
    case: str
    prize: str
    name: str
    gender: str
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
    ap = argparse.ArgumentParser(
        description="Detective-style grocery store magic story with a gown and an odd result."
    )
    ap.add_argument("--place", choices=["grocery_store"])
    ap.add_argument("--case", choices=[CASE.id])
    ap.add_argument("--prize", choices=[PRIZE.type])
    ap.add_argument("--gender", choices=["girl", "boy"])
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
    if getattr(args, "gender", None) and getattr(args, "gender", None) not in PRIZE.genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "case", None) is None or c[1] == getattr(args, "case", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, case, prize = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(sorted(PRIZE.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, case=case, prize=prize, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(SETTING, CASE, PRIZE, params.name, params.gender, params.trait)
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
    StoryParams(place="grocery_store", case=CASE.id, prize=PRIZE.type, name="Mina", gender="girl", trait="curious"),
    StoryParams(place="grocery_store", case=CASE.id, prize=PRIZE.type, name="Theo", gender="boy", trait="sharp-eyed"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid_story/3."))
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: detective gown mystery"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
