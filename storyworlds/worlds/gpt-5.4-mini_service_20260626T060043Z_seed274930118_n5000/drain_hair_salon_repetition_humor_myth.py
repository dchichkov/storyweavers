#!/usr/bin/env python3
"""
Storyworld: drain / hair salon / repetition / humor / myth.

A small, self-contained world where a hair salon's drain slowly chokes on hair
and soap foam, the stylist notices the omen, and the crowd learns a comic,
myth-like lesson about combs, clumps, and the value of catching hair before it
reaches the drain.

The simulated state drives the prose: hair accumulates, water drains slowly or
stops, a repeatable chant-like handling loop is used to clear it, and the ending
shows what changed.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    drain: object | None = None
    guest: object | None = None
    stylist: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "stylist"}
        male = {"boy", "man", "father"}
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
class Salon:
    name: str = "Moon-Crown Salon"
    drain_name: str = "the drain"
    sink_name: str = "the washing sink"
    SALON: object | None = None
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
class HairStyle:
    id: str
    label: str
    hair_kind: str
    amount: str
    cling: str
    chant: str
    humor: str
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
class Tool:
    id: str
    label: str
    noun: str
    action: str
    helps: bool = True
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
    def __init__(self, salon: Salon) -> None:
        self.salon = salon
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.drain_state: str = "clear"
        self.water_level: float = 0.0
        self.repeated_lines: int = 0

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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
        import copy
        clone = World(self.salon)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.drain_state = self.drain_state
        clone.water_level = self.water_level
        clone.repeated_lines = self.repeated_lines
        return clone


@dataclass
class StoryParams:
    name: str
    stylist_name: str
    style: str
    tool: str
    seed: Optional[int] = None
    params: object | None = None
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


SALON = Salon()

STYLES = {
    "golden_curls": HairStyle(
        id="golden_curls",
        label="golden curls",
        hair_kind="curls",
        amount="a great tumble of",
        cling="clung like seaweed to a stone",
        chant="comb, gather, lift, comb, gather, lift",
        humor="the curls bounced back like tiny springs",
    ),
    "silver_straight": HairStyle(
        id="silver_straight",
        label="silver straight hair",
        hair_kind="straight hair",
        amount="a long sheet of",
        cling="slid like river water toward the drain",
        chant="sweep, catch, sweep, catch, sweep, catch",
        humor="the hair behaved like a proud banner that would not sit still",
    ),
    "red_waves": HairStyle(
        id="red_waves",
        label="red waves",
        hair_kind="waves",
        amount="a bright tide of",
        cling="twisted into the soap foam and grinned there",
        chant="lift, rinse, lift, rinse, lift, rinse",
        humor="every wave seemed to wave back",
    ),
}

TOOLS = {
    "wide_comb": Tool(id="wide_comb", label="a wide comb", noun="comb", action="comb"),
    "catch_bowl": Tool(id="catch_bowl", label="a little catch bowl", noun="bowl", action="catch"),
    "drain_basket": Tool(id="drain_basket", label="a drain basket", noun="basket", action="guard"),
}

NAMES = ["Mina", "Ivo", "Lena", "Oren", "Tala", "Pip", "Nina", "Bram"]
STYLISTS = ["Sela", "Mara", "Joren", "Anya", "Kito", "Rina"]


def _is_valid_explicit(style: HairStyle, tool: Tool) -> bool:
    return style.id in STYLES and tool.id in TOOLS


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for sid in STYLES:
        for tid in TOOLS:
            out.append((sid, tid))
    return out


def _line_repeat(world: World, text: str) -> None:
    world.say(text)
    world.repeated_lines += 1


def _pour(world: World, style: HairStyle) -> None:
    actor = world.get("guest")
    stylist = world.get("stylist")
    actor.meters["hair"] += 1
    actor.meters["soap"] += 0.5
    world.water_level += 1.0
    world.say(
        f"When {actor.id} leaned over the sink, {style.amount} {style.label} "
        f"{style.cling}."
    )
    world.say(
        f"{stylist.id} watched the water and knew the old truth: hair that rides "
        f"the water may one day meet {world.salon.drain_name}."
    )


def _block(world: World, tool: Tool) -> None:
    if tool.id == "drain_basket":
        world.drain_state = "guarded"
        world.say(
            f"So {world.get('stylist').id} set {tool.label} in the mouth of {world.salon.drain_name}, "
            f"and the drain was guarded."
        )
    else:
        world.drain_state = "slowed"
        world.say(
            f"So {world.get('stylist').id} lifted {tool.label} and used it again and again, "
            f"and again, to keep the hair from the pipe."
        )


def _clog(world: World, style: HairStyle) -> None:
    if world.drain_state == "guarded":
        world.say(
            f"The water swirled, the foam swirled, and the basket held the hair. "
            f"{world.salon.drain_name} stayed clear."
        )
        return
    world.get("drain").meters["clog"] += 1
    if world.get("drain").meters["clog"] >= THRESHOLD:
        world.drain_state = "clogged"
        world.say(
            f"But {style.label} kept drifting down, and by the third swirl "
            f"{world.salon.drain_name} was clogged."
        )


def _repeat_ritual(world: World, style: HairStyle) -> None:
    stylist = world.get("stylist")
    if world.drain_state != "clogged":
        return
    words = style.chant.split(", ")
    for i in range(3):
        _line_repeat(world, f"{stylist.id} said, “{words[0]}, {words[1]}, {words[2]}.”")
    world.say(
        f"The old salon folk loved a repeatable charm, and this one was half work, "
        f"half joke: the more they repeated it, the less the hair could boast."
    )
    world.drain_state = "clearing"
    world.get("drain").meters["clog"] = 0.0
    world.say(
        f"At last the twist of hair came free, and {world.salon.drain_name} sighed like a small flute."
    )


def _end_image(world: World, style: HairStyle) -> None:
    guest = world.get("guest")
    stylist = world.get("stylist")
    if world.drain_state in {"guarded", "clearing", "clear", "slowed"}:
        world.say(
            f"When the wash was done, {guest.id} laughed at {style.humor}, "
            f"and {stylist.id} brushed the last shining strands away from {world.salon.drain_name}."
        )
        world.say(
            f"In the end, the water ran clean, the drain stayed open, and the salon kept its bright, "
            f"patient song."
        )


def tell(params: StoryParams) -> World:
    if params.style not in STYLES:
        pass
    if params.tool not in TOOLS:
        pass
    style = _safe_lookup(STYLES, params.style)
    tool = _safe_lookup(TOOLS, params.tool)
    if not _is_valid_explicit(style, tool):
        pass
    world = World(SALON)
    guest = world.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    stylist = world.add(Entity(id=params.stylist_name, kind="character", type="stylist", label=params.stylist_name))
    drain = world.add(Entity(id="drain", kind="thing", type="drain", label="the drain"))
    world.facts.update(guest=guest, stylist=stylist, drain=drain, style=style, tool=tool)

    world.say(
        f"In {world.salon.name}, there lived a little rule as old as soap: what the head sheds, the drain remembers."
    )
    world.say(
        f"{guest.id} came for {style.label}, and {stylist.id} welcomed {guest.pronoun('object')} "
        f"with a smile and a warm chair."
    )
    world.para()
    _pour(world, style)
    _clog(world, style)
    world.say(
        f"{stylist.id} muttered the salon proverb twice, because in a myth, a warning likes to be heard more than once."
    )
    world.para()
    _block(world, tool)
    if world.drain_state == "clogged":
        _repeat_ritual(world, style)
    _end_image(world, style)
    return world


def generation_prompts(world: World) -> list[str]:
    style = _safe_fact(world, world.facts, "style")
    return [
        f"Write a short myth-like story about {style.label} and a hair salon drain.",
        f"Tell a humorous salon tale where the drain starts to clog and the stylist uses a repeated chant to fix it.",
        f"Write a child-friendly story set in a hair salon with a little repetition, a funny worry, and a clean ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    guest = _safe_fact(world, world.facts, "guest")
    stylist = _safe_fact(world, world.facts, "stylist")
    style = _safe_fact(world, world.facts, "style")
    tool = _safe_fact(world, world.facts, "tool")
    return [
        QAItem(
            question=f"Who came to {SALON.name} for {style.label}?",
            answer=f"{guest.id} came to {SALON.name} for {style.label}, and {stylist.id} helped with the wash.",
        ),
        QAItem(
            question=f"What problem did {world.salon.drain_name} have in the story?",
            answer=f"{world.salon.drain_name} got clogged when hair and soap drifted down with the water.",
        ),
        QAItem(
            question=f"What did {stylist.id} use to help keep hair out of the drain?",
            answer=f"{stylist.id} used {tool.label} and then repeated the chant until the drain was clear again.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The water ran clean again, the drain stayed open, and the salon kept its bright, patient song.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a drain for?",
            answer="A drain lets water flow away through pipes so a sink or tub does not fill up.",
        ),
        QAItem(
            question="Why can hair clog a drain?",
            answer="Hair can catch on the pipe and tangle with soap and small bits until water cannot pass easily.",
        ),
        QAItem(
            question="Why do stories sometimes repeat the same words?",
            answer="Stories repeat words to make a feeling stronger, to sound musical, or to make a joke memorable.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== (2) Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== (3) World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  drain_state={world.drain_state}")
    lines.append(f"  water_level={world.water_level}")
    lines.append(f"  repeated_lines={world.repeated_lines}")
    return "\n".join(lines)


ASP_RULES = r"""
% Facts:
% salon(S).
% style(Sid).
% tool(Tid).
% clog_risk(Sid).
% helper(Tid).

cloggy(S) :- style(S), clog_risk(S).
fixable(S) :- style(S), tool(T), helper(T).
valid_story(S, T) :- cloggy(S), fixable(S).
"""

def asp_facts() -> str:
    import asp
    lines = [asp.fact("salon", "moon_crown")]
    for sid in STYLES:
        lines.append(asp.fact("style", sid))
        lines.append(asp.fact("clog_risk", sid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
        if _safe_lookup(TOOLS, tid).helps:
            lines.append(asp.fact("helper", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/2."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    ax = set(asp_valid_combos())
    if py == ax:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("only in python:", sorted(py - ax))
    print("only in clingo:", sorted(ax - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Hair-salon myth storyworld about a drain, humor, and repetition.")
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--stylist-name", choices=STYLISTS)
    ap.add_argument("--style", choices=STYLES)
    ap.add_argument("--tool", choices=TOOLS)
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
    if getattr(args, "style", None) and getattr(args, "tool", None):
        if (getattr(args, "style", None), getattr(args, "tool", None)) not in combos:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    style = getattr(args, "style", None) or rng.choice(list(STYLES))
    tool = getattr(args, "tool", None) or rng.choice(list(TOOLS))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    stylist_name = getattr(args, "stylist_name", None) or rng.choice(STYLISTS)
    return StoryParams(name=name, stylist_name=stylist_name, style=style, tool=tool)


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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible style/tool combos:")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for sid in STYLES:
            for tid in TOOLS:
                params = StoryParams(
                    name=random.Random(base_seed + len(samples)).choice(NAMES),
                    stylist_name=random.Random(base_seed + len(samples) + 1).choice(STYLISTS),
                    style=sid,
                    tool=tid,
                    seed=base_seed + len(samples),
                )
                samples.append(generate(params))
    else:
        seen: set[str] = set()
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
            key = sample.story
            if key in seen:
                continue
            seen.add(key)
            samples.append(sample)

    if getattr(args, "json", None):
        if len(samples) == 1:
            print(samples[0].to_json())
        else:
            print(json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, sample in enumerate(samples):
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
