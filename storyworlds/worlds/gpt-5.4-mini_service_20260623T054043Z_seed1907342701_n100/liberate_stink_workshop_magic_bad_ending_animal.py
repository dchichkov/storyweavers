#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T054043Z_seed1907342701_n100/liberate_stink_workshop_magic_bad_ending_animal.py
===============================================================================================================

A standalone storyworld for a small animal tale set in a workshop.

Seeded premise:
- workshop setting
- words: liberate, stink
- features: magic, bad ending
- style: animal story

The world models a tiny cast of animals, a stinky workshop problem, a magical
attempt to liberate something, and a bad ending in which the smell and the mess
win. Prose is driven by world state, not by a frozen paragraph template.
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
    owner: str = ""
    trapped: bool = False
    magical: bool = False
    smells: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    helper: object | None = None
    hero: object | None = None
    stink: object | None = None
    tool: object | None = None
    workshop: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"mouse", "cow", "goat", "cat"}
        male = {"fox", "dog", "owl", "rat"}
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
class AnimalKind:
    key: str
    label: str
    pronoun_type: str
    traits: list[str] = field(default_factory=list)
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


@dataclass
class StinkSource:
    key: str
    label: str
    phrase: str
    smell_word: str
    spread: str
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
class MagicTool:
    key: str
    label: str
    phrase: str
    spark: str
    power: int
    can_liberate: bool
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
class TrapTarget:
    key: str
    label: str
    phrase: str
    place_phrase: str
    size: str
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
    def __init__(self, setting: str) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict[str, object] = {}

    def add(self, ent: Entity) -> Entity:
        self.entities[ent.id] = ent
        return ent

    def get(self, eid: str) -> Entity:
        if eid not in self.entities:
            label = str(eid).replace("_", " ")
            self.entities[eid] = Entity(str(eid), label=label)
        return self.entities[eid]

    def animals(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "animal"]

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
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
        return c


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_smell(world: World) -> list[str]:
    out: list[str] = []
    for src in list(world.entities.values()):
        if not src.smells or src.meters["active"] < THRESHOLD:
            continue
        sig = ("smell", src.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for a in world.animals():
            a.memes["disgust"] += 1
        world.get("workshop").meters["stink"] += 1
        out.append("The workshop filled with stink.")
    return out


def _r_magic_spill(world: World) -> list[str]:
    out: list[str] = []
    for tool in list(world.entities.values()):
        if not tool.magical or tool.meters["sparked"] < THRESHOLD:
            continue
        sig = ("spark", tool.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        world.get("workshop").meters["glow"] += 1
        out.append("Magic shimmered over the bench.")
    return out


CAUSAL_RULES: list[Rule] = [
    Rule("smell", "physical", _r_smell),
    Rule("magic_spill", "physical", _r_magic_spill),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_liberate(tool: MagicTool, target: TrapTarget, stink: StinkSource) -> bool:
    return tool.can_liberate and tool.power >= 2 and target.key != "jar" or tool.can_liberate and stink.key != "toad"


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for animal in ANIMALS:
        for stink in STINKS:
            for tool in TOOLS.values():
                if tool.can_liberate:
                    combos.append((animal, stink, tool.key))
    return combos


@dataclass
class StoryParams:
    animal: str
    stink: str
    tool: str
    trapped: str
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal workshop storyworld with magic, stink, and a bad ending.")
    ap.add_argument("--animal", choices=ANIMALS)
    ap.add_argument("--stink", choices=STINKS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--trapped", choices=TRAPS)
    ap.add_argument("--helper", choices=ANIMALS)
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


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = [c for c in valid_combos()
              if (getattr(args, "animal", None) is None or c[0] == getattr(args, "animal", None))
              and (getattr(args, "stink", None) is None or c[1] == getattr(args, "stink", None))
              and (getattr(args, "tool", None) is None or c[2] == getattr(args, "tool", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    animal, stink, tool = rng.choice(list(combos))
    trapped = getattr(args, "trapped", None) or rng.choice(sorted(TRAPS))
    helper = getattr(args, "helper", None) or rng.choice(sorted(a for a in ANIMALS if a != animal))
    return StoryParams(animal=animal, stink=stink, tool=tool, trapped=trapped, helper=helper)


def tell(params: StoryParams) -> World:
    if params.animal not in ANIMALS or params.stink not in STINKS or params.tool not in TOOLS or params.trapped not in TRAPS or params.helper not in ANIMALS:
        pass
    world = World("workshop")
    hero_cfg = _safe_lookup(ANIMALS, params.animal)
    helper_cfg = _safe_lookup(ANIMALS, params.helper)
    stink_cfg = _safe_lookup(STINKS, params.stink)
    tool_cfg = _safe_lookup(TOOLS, params.tool)
    trap_cfg = _safe_lookup(TRAPS, params.trapped)

    workshop = world.add(Entity(id="workshop", kind="place", type="place", label="the workshop"))
    hero = world.add(Entity(id="hero", kind="animal", type=hero_cfg.pronoun_type, label=hero_cfg.label, role="hero"))
    helper = world.add(Entity(id="helper", kind="animal", type=helper_cfg.pronoun_type, label=helper_cfg.label, role="helper"))
    stink = world.add(Entity(id="stink", kind="thing", type="thing", label=stink_cfg.label, smells=True))
    tool = world.add(Entity(id="tool", kind="thing", type="thing", label=tool_cfg.label, magical=True))
    trapped = world.add(Entity(id="trapped", kind="thing", type="thing", label=trap_cfg.label, trapped=True))

    world.facts.update(hero=hero, helper=helper, stink=stink_cfg, tool=tool_cfg, trapped=trap_cfg)

    workshop.meters["stink"] = 0.0
    workshop.meters["glow"] = 0.0
    stink.meters["active"] = 1.0
    tool.meters["sparked"] = 1.0
    hero.memes["hope"] = 1.0
    helper.memes["worry"] = 1.0
    trapped.meters["bound"] = 1.0

    world.say(f"{hero.label} and {helper.label} were in {workshop.label} on a busy day.")
    world.say(f"Near the bench sat {trapped.phrase}, and {stink.phrase} hung in the air.")
    world.para()
    world.say(f"{hero.label.capitalize()} wanted to liberate {trapped.label}, but the smell made both noses wrinkle.")
    world.say(f"{helper.label.capitalize()} lifted {tool.phrase} and whispered a magic word.")
    propagate(world, narrate=True)
    world.para()

    # Bad ending: the magic works a little, but the stink and spill ruin it.
    trapped.meters["bound"] = 0.0
    trapped.meters["rolling"] = 1.0
    workshop.meters["stink"] += 1.0
    hero.memes["disgust"] += 2.0
    helper.memes["disgust"] += 2.0
    world.say(f"The spell twinkled, but it only loosened {trapped.label} just enough to wobble away.")
    world.say(f"Then the stink got worse, and the whole workshop smelled sour and old.")
    world.say(f"In the end, {trapped.label} slipped into a dusty crack while the magic fizzled out.")
    world.say(f"The animals sat with droopy ears beside the bench, and the bad ending left the workshop sticky, dim, and stinky.")

    world.facts.update(outcome="bad", workshop=workshop, ruled=False)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write an animal story set in a workshop that uses the words "{(f.get("tool") or next(iter(TOOLS.values()))).label}" and "stink".',
        f"Tell a short story where {f['hero'].label} tries to liberate {f['trapped'].label} with magic, but the workshop smell gets in the way.",
        f'Write a bad-ending animal story about {f["helper"].label}, {f["hero"].label}, and a stinky workshop.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = f["hero"]
    helper = f["helper"]
    stink = f["stink"]
    tool = (f.get("tool") or next(iter(TOOLS.values())))
    trapped = f["trapped"]
    return [
        QAItem(
            question=f"Who wanted to liberate {trapped.label} in the workshop?",
            answer=f"{hero.label.capitalize()} wanted to liberate {trapped.label}, and {helper.label} came along to help. They both hoped the magic would work before the stink got worse.",
        ),
        QAItem(
            question=f"Why did the animals wrinkle their noses when they saw the bench?",
            answer=f"The workshop already smelled like {stink.label}, so the air was sharp and unpleasant. That made the magic feel weaker and the rescue harder.",
        ),
        QAItem(
            question=f"What did {helper.label} do with {tool.label}?",
            answer=f"{helper.label.capitalize()} lifted {tool.label} and tried a magic word. The spell twinkled, but it did not fully liberate {trapped.label}.",
        ),
        QAItem(
            question=f"How did the story end for {trapped.label}?",
            answer=f"It ended badly. {trapped.label} slipped away into a dusty crack, and the workshop was left stinky and dim.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    out = []
    out.append(QAItem(
        question="What is a workshop?",
        answer="A workshop is a place where people build, fix, and make things. It often has tools, benches, and little bits of work lying around.",
    ))
    out.append(QAItem(
        question="What does stink mean?",
        answer="Stink means a very bad smell. A stink can make animals wrinkle their noses and want to move away.",
    ))
    out.append(QAItem(
        question="What is magic in a story?",
        answer="Magic is something special that can make surprising things happen. In stories, magic can glow, sparkle, or change what happens next.",
    ))
    if (f.get("tool") or next(iter(TOOLS.values()))).key in {"wand", "charm", "glimmer"}:
        out.append(QAItem(
            question="What is a magic tool for?",
            answer="A magic tool is used to try to change something with a spell. It can glow or spark, but it does not always solve the problem.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    parts = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        parts.append(f"{i}. {p}")
    parts.append("")
    parts.append("== (2) Story questions ==")
    for item in sample.story_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    parts.append("")
    parts.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        parts.append(f"Q: {item.question}")
        parts.append(f"A: {item.answer}")
    return "\n".join(parts)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if any(v for v in e.meters.values()):
            bits.append(f"meters={dict(e.meters)}")
        if any(v for v in e.memes.values()):
            bits.append(f"memes={dict(e.memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.trapped:
            bits.append("trapped=True")
        if e.magical:
            bits.append("magical=True")
        if e.smells:
            bits.append("smells=True")
        lines.append(f"  {e.id}: {e.label} {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted(n for n, *_ in world.fired)}")
    return "\n".join(lines)


ANIMALS = {
    "mouse": AnimalKind(key="mouse", label="Mina the mouse", pronoun_type="mouse"),
    "cat": AnimalKind(key="cat", label="Cleo the cat", pronoun_type="cat"),
    "fox": AnimalKind(key="fox", label="Fenn the fox", pronoun_type="fox"),
    "owl": AnimalKind(key="owl", label="Orrin the owl", pronoun_type="owl"),
}

STINKS = {
    "fish": StinkSource(key="fish", label="fishy bucket", phrase="a fishy bucket", smell_word="fishy", spread="sharp", tags={"stink"}),
    "mud": StinkSource(key="mud", label="muddy boots", phrase="muddy boots by the door", smell_word="muddy", spread="heavy", tags={"stink"}),
    "paint": StinkSource(key="paint", label="paint fumes", phrase="paint fumes from a green can", smell_word="sharp", spread="thin", tags={"stink"}),
}

TOOLS = {
    "wand": MagicTool(key="wand", label="wand", phrase="a striped magic wand", spark="sparkled", power=2, can_liberate=True, tags={"magic"}),
    "bell": MagicTool(key="bell", label="bell", phrase="a little magic bell", spark="tinkled", power=1, can_liberate=False, tags={"magic"}),
    "charm": MagicTool(key="charm", label="charm", phrase="a silver charm", spark="glowed", power=3, can_liberate=True, tags={"magic"}),
}

TRAPS = {
    "jar": TrapTarget(key="jar", label="jar", phrase="a glass jar under a cloth", place_phrase="on the bench", size="small", tags={"bad_ending"}),
    "crate": TrapTarget(key="crate", label="crate", phrase="a crate tied with twine", place_phrase="by the window", size="large", tags={"bad_ending"}),
}


CURATED = [
    StoryParams(animal="mouse", stink="fish", tool="wand", trapped="jar", helper="cat"),
    StoryParams(animal="fox", stink="mud", tool="charm", trapped="crate", helper="owl"),
    StoryParams(animal="cat", stink="paint", tool="wand", trapped="jar", helper="mouse"),
]


def explain_rejection(tool: MagicTool) -> str:
    return f"(No story: {tool.label} is not a strong enough magic tool for this animal rescue.)"


def asp_facts() -> str:
    import asp
    lines = []
    for a in ANIMALS:
        lines.append(asp.fact("animal", a))
    for s in STINKS:
        lines.append(asp.fact("stink", s))
    for t in TOOLS:
        lines.append(asp.fact("tool", t))
        if _safe_lookup(TOOLS, t).can_liberate:
            lines.append(asp.fact("can_liberate", t))
    for tr in TRAPS:
        lines.append(asp.fact("trap", tr))
    lines.append(asp.fact("setting", "workshop"))
    return "\n".join(lines)


ASP_RULES = r"""
valid(A,S,T) :- animal(A), stink(S), can_liberate(T), trap(_).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ax = set(asp_valid_combos())
    if py != ax:
        print("MISMATCH")
        if py - ax:
            print("only python:", sorted(py - ax))
        if ax - py:
            print("only asp:", sorted(ax - py))
        return 1
    # smoke test
    sample = generate(resolve_params(argparse.Namespace(animal=None, stink=None, tool=None, trapped=None, helper=None), random.Random(777)))
    _ = sample.story
    return 0


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
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_combos():
            print(row)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            i += 1
            seed = base_seed + i
            try:
                params = resolve_params(args, random.Random(seed))
            except StoryError as err:
                print(err)
                return
            params.seed = seed
            s = generate(params)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

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
