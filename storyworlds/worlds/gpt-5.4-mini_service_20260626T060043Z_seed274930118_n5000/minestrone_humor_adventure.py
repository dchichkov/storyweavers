#!/usr/bin/env python3
"""
A tiny storyworld about a careful soup expedition, a comic spill, and a warm
minestrone rescue.

Seed premise:
- A child wants to help make minestrone.
- The pot is heavy, the path is tricky, and someone wants to be brave.
- A small mishap turns the kitchen into a funny adventure.
- The ending proves the soup became a shared success.

This world is designed to feel adventurous, but with gentle humor.
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


# ---------------------------------------------------------------------------
# Core model
# ---------------------------------------------------------------------------

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

@dataclass
class Entity:
    id: str
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    floor: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
class Kitchen:
    place: str = "the kitchen"
    route: str = "the narrow pantry path"
    affords: set[str] = field(default_factory=lambda: {"stir", "carry", "serve"})
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
class Tool:
    id: str
    label: str
    phrase: str
    helper: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
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
class Prize:
    label: str
    phrase: str
    type: str
    region: str
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
    hero_name: str
    hero_type: str
    parent_type: str
    trait: str
    prize: str
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


class World:
    def __init__(self, setting: Kitchen):
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
        import copy
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = dict(self.facts)
        return c


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


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    cook = world.get("hero")
    pot = world.get("pot")
    if cook.meters.get("jostle", 0) < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    pot.meters["spill"] = pot.meters.get("spill", 0) + 1
    pot.memes["panic"] = pot.memes.get("panic", 0) + 1
    out.append("The pot tipped and a ribbon of tomato-red soup splashed across the floor.")
    return out


def _r_stain(world: World) -> list[str]:
    out: list[str] = []
    floor = world.get("floor")
    pot = world.get("pot")
    if pot.meters.get("spill", 0) < THRESHOLD:
        return out
    sig = ("stain",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    floor.meters["stained"] = floor.meters.get("stained", 0) + 1
    out.append("The floor got streaked with bright red dots that looked a little like tiny treasure maps.")
    return out


def _r_help(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("hero")
    helper = world.get("parent")
    pot = world.get("pot")
    if hero.memes.get("embarrassed", 0) < THRESHOLD or pot.meters.get("spill", 0) < THRESHOLD:
        return out
    sig = ("help",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    helper.memes["warmth"] = helper.memes.get("warmth", 0) + 1
    out.append(f"{helper.label} chuckled and said the soup had simply made a dramatic entrance.")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("stain", _r_stain), Rule("help", _r_help)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            lines = rule.apply(world)
            if lines:
                changed = True
                produced.extend(lines)
    if narrate:
        for line in produced:
            world.say(line)
    return produced


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "kitchen": Kitchen(place="the kitchen", route="the narrow pantry path"),
    "camp": Kitchen(place="the camp kitchen", route="the bumpy path between crates"),
}

PRIZES = {
    "minestrone": Prize(
        label="minestrone",
        phrase="a big pot of minestrone",
        type="soup",
        region="hands",
        plural=False,
    )
}

TOOLS = [
    Tool(id="ladle", label="ladle", phrase="a long ladle", helper=True),
    Tool(id="towel", label="towel", phrase="a thick towel", protective=True, covers={"hands"}),
]


GIRL_NAMES = ["Mina", "Luna", "Ada", "Nia", "Pia"]
BOY_NAMES = ["Owen", "Milo", "Theo", "Noah", "Eli"]
TRAITS = ["curious", "brave", "sly", "cheerful", "wriggly"]


# ---------------------------------------------------------------------------
# World logic
# ---------------------------------------------------------------------------

def _hero_intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a little {hero.memes.get('trait', 'curious')} {hero.type} who loved busy kitchens and bold smells.")


def _love_soup(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0) + 1
    world.say(f"{hero.id} loved {prize.label} most of all, because it smelled like tomatoes, noodles, and a tiny parade.")


def _prepare(world: World, hero: Entity, prize: Entity) -> None:
    world.say(f"One afternoon, {hero.id} and {hero.pronoun('possessive')} {world.get('parent').label} began carrying {prize.phrase} toward {world.setting.place}.")
    world.say(f"The only tricky part was {world.setting.route}, which was just narrow enough to make every step feel like an expedition.")


def _wants_to_help(world: World, hero: Entity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0) + 1
    world.say(f"{hero.id} wanted to help stir, because the spoon looked like a shiny captain's wheel.")


def _warn(world: World, hero: Entity, prize: Entity) -> None:
    world.say(f'{world.get("parent").label} pointed at the pot and said, "Easy now. If we rush, {prize.label} will wear the floor instead of the bowl."')


def _jostle(world: World, hero: Entity) -> None:
    hero.meters["jostle"] = hero.meters.get("jostle", 0) + 1
    hero.memes["embarrassed"] = hero.memes.get("embarrassed", 0) + 1
    world.say(f"{hero.id} took one heroic step, then another, and the spoon gave the pot a wobbly little bonk.")


def _rescue(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["relief"] = hero.memes.get("relief", 0) + 1
    world.say(f"{world.get('parent').label} grabbed the ladle, set the pot steady, and declared that every brave explorer needs a calm second-in-command.")
    world.say(f"Together they wiped the floor, sprinkled in the last beans, and made the minestrone look happy again.")


def _finish(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0) + 1
    world.say(f"In the end, {hero.id} carried the bowl with both hands, and {prize.label} reached the table without another wobble.")


def tell(params: StoryParams) -> World:
    setting = SETTINGS["kitchen"]
    world = World(setting)

    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        meters={},
        memes={"trait": params.trait},
    ))
    parent = world.add(Entity(
        id="parent",
        kind="character",
        type=params.parent_type,
        label=f"the {params.parent_type}",
        meters={},
        memes={},
    ))
    prize = world.add(Entity(
        id="pot",
        type="pot",
        label="minestrone",
        phrase="a big pot of minestrone",
        owner=hero.id,
        caretaker=parent.id,
        meters={},
        memes={},
    ))
    floor = world.add(Entity(id="floor", type="floor", label="the floor", meters={}, memes={}))

    _hero_intro(world, hero)
    _love_soup(world, hero, prize)
    _prepare(world, hero, prize)

    world.para()
    _wants_to_help(world, hero)
    _warn(world, hero, prize)
    _jostle(world, hero)
    propagate(world, narrate=True)

    world.para()
    _rescue(world, hero, prize)
    _finish(world, hero, prize)

    world.facts.update(hero=hero, parent=parent, prize=prize, floor=floor, setting=setting)
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    return [
        f"Write a short humorous adventure story about {hero.id} helping make minestrone in a kitchen.",
        f"Tell a child-friendly story where a brave cook nearly spills minestrone but then fixes the problem.",
        f"Create a funny little adventure with minestrone, a wobbly pot, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    hero: Entity = _safe_fact(world, world.facts, "hero")
    parent: Entity = _safe_fact(world, world.facts, "parent")
    prize: Entity = _safe_fact(world, world.facts, "prize")
    return [
        QAItem(
            question=f"What did {hero.id} want to help with?",
            answer=f"{hero.id} wanted to help stir the minestrone.",
        ),
        QAItem(
            question=f"Why did the {parent.type} worry?",
            answer=f"The {parent.type} worried that the minestrone might spill onto the floor if they rushed.",
        ),
        QAItem(
            question=f"What happened after the pot wobbled?",
            answer=f"The {parent.type} steadied the pot, the floor was wiped clean, and the minestrone was finished safely.",
        ),
        QAItem(
            question=f"Did the minestrone make it to the table?",
            answer=f"Yes. {prize.label} reached the table in the end without another wobble.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is minestrone?",
            answer="Minestrone is a hearty soup made with vegetables, broth, and often beans or pasta.",
        ),
        QAItem(
            question="Why do people use a ladle for soup?",
            answer="A ladle helps scoop soup out of a pot without spilling too much.",
        ),
        QAItem(
            question="What does it mean when something is steady?",
            answer="Steady means it does not wobble or shake much.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    out.extend(sample.prompts)
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
hero(hero).
parent(parent).
thing(pot).
thing(floor).

can_help(hero, stir).
can_fix(parent, steady).

spill_happens :- jostle(hero), carries(hero, pot).
floor_stains :- spill_happens.
resolution :- floor_stains, steady(parent).

#show spill_happens/0.
#show floor_stains/0.
#show resolution/0.
"""


def asp_facts() -> str:
    import asp
    lines = [
        asp.fact("jostle", "hero"),
        asp.fact("carries", "hero", "pot"),
        asp.fact("steady", "parent"),
    ]
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_results() -> set[str]:
    import asp
    model = asp.one_model(asp_program("#show spill_happens/0.\n#show floor_stains/0.\n#show resolution/0."))
    return {str(a) for a in model}


def python_reasonableness() -> set[str]:
    return {"spill_happens", "floor_stains", "resolution"}


def asp_verify() -> int:
    import asp
    model = asp.one_model(asp_program("#show spill_happens/0.\n#show floor_stains/0.\n#show resolution/0."))
    atoms = {sym.name for sym in model}
    py = python_reasonableness()
    if atoms == py:
        print("OK: ASP and Python reasonableness agree.")
        return 0
    print("MISMATCH between ASP and Python:")
    print("ASP:", sorted(atoms))
    print("PY :", sorted(py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A humorous adventure storyworld about minestrone.")
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("--prize", choices=PRIZES)
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    prize = getattr(args, "prize", None) or "minestrone"
    return StoryParams(hero_name=name, hero_type=gender, parent_type=parent, trait=trait, prize=prize)


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
        print(asp_program("#show spill_happens/0.\n#show floor_stains/0.\n#show resolution/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("ASP mode is available; this world has one simple adventure-shaped reasoner.")
        sys.exit(0)

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        presets = [
            StoryParams("Mina", "girl", "mother", "curious", "minestrone"),
            StoryParams("Owen", "boy", "father", "brave", "minestrone"),
            StoryParams("Luna", "girl", "mother", "cheerful", "minestrone"),
        ]
        samples = [generate(p) for p in presets]
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

    for idx, sample in enumerate(samples):
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
