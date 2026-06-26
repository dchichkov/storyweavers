#!/usr/bin/env python3
"""
A standalone storyworld for an adventure about a small quest, a stipend, a
careful plan, and a dipper that can help or ruin the day.

Seed premise:
A young helper wants to earn a stipend by delivering supplies on a little
adventure. They must formulate a safe plan, but a greedy shortcut and a tricky
dipper can turn the trip into a bad ending unless the helper listens to their
inner monologue and chooses the moral value of honesty.

World model:
- physical meters: tiredness, danger, mud, trust, stipend_gain, repair_need
- emotional memes: hope, doubt, greed, courage, guilt, pride

This script follows the Storyweavers contract:
- build_parser, resolve_params, generate, emit, main
- QAItem, StoryError, StorySample imported eagerly
- ASP twin with inline rules and a Python reasonableness gate
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
# Data model
# ---------------------------------------------------------------------------

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
    carried_by: Optional[str] = None
    sturdy: bool = False
    useful: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    mentor: object | None = None
    tool_ent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind != "character":
            return {"subject": "it", "object": "it", "possessive": "its"}[case]
        if self.type in {"girl", "woman", "sister", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "brother", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    id: str
    label: str
    dangerous: bool = False
    muddy: bool = False
    affords: set[str] = field(default_factory=set)
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
class Quest:
    id: str
    verb: str
    gerund: str
    risk: str
    danger: str
    keyword: str
    needs_moral_value: bool = True
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
    helps_against: set[str] = field(default_factory=set)
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.inner_monologue: list[str] = []

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
        import copy as _copy

        w = World(self.place)
        w.entities = _copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.paragraphs = [[]]
        w.facts = dict(self.facts)
        w.inner_monologue = list(self.inner_monologue)
        return w


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
PLACES = {
    "harbor": Place(id="harbor", label="the harbor", dangerous=True, affords={"cross", "deliver"}),
    "forest": Place(id="forest", label="the forest trail", dangerous=True, muddy=True, affords={"cross", "deliver"}),
    "market": Place(id="market", label="the market road", dangerous=False, affords={"deliver"}),
    "hill": Place(id="hill", label="the hill path", dangerous=True, affords={"cross", "deliver"}),
}

QUESTS = {
    "deliver_scroll": Quest(
        id="deliver_scroll",
        verb="deliver the scroll",
        gerund="delivering the scroll",
        risk="the scroll could get soaked or lost",
        danger="the wind might tear it loose",
        keyword="scroll",
    ),
    "carry_water": Quest(
        id="carry_water",
        verb="carry the water",
        gerund="carrying the water",
        risk="the water could spill",
        danger="the path might shake the bucket",
        keyword="water",
    ),
    "bring_supplies": Quest(
        id="bring_supplies",
        verb="bring the supplies",
        gerund="bringing the supplies",
        risk="the supplies could fall into the mud",
        danger="the trail might turn slippery",
        keyword="supplies",
    ),
}

TOOLS = {
    "dipper": Tool(
        id="dipper",
        label="a little dipper",
        phrase="a little dipper with a long handle",
        helps_against={"spill", "mud", "soaked"},
        covers={"hands", "bucket"},
    ),
    "satchel": Tool(
        id="satchel",
        label="a sturdy satchel",
        phrase="a sturdy satchel with a clasp",
        helps_against={"lost", "wind"},
        covers={"scroll", "supplies"},
    ),
    "cloak": Tool(
        id="cloak",
        label="a rain cloak",
        phrase="a rain cloak that snapped in the wind",
        helps_against={"soaked"},
        covers={"body"},
    ),
}

NAMES = ["Nina", "Milo", "Tara", "Pip", "Ari", "Jun", "Lina", "Rowan"]
TYPES = ["girl", "boy"]
TRAITS = ["brave", "curious", "careful", "stubborn", "kind", "restless"]


# ---------------------------------------------------------------------------
# Story world rules
# ---------------------------------------------------------------------------
def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("Hero")
    tool = world.entities.get("dipper")
    quest: Quest = _safe_fact(world, world.facts, "quest")
    if hero.meters.get("risk", 0) < 1:
        return out
    if not tool or tool.carried_by != hero.id:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["mud"] = hero.meters.get("mud", 0) + 1
    hero.memes["guilt"] = hero.memes.get("guilt", 0) + 1
    out.append(f"The little dipper tipped at the worst moment, and {hero.id} almost lost {quest.keyword}.")
    return out


def _r_repair(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("Hero")
    if hero.meters.get("mud", 0) < 1:
        return out
    sig = ("repair",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["repair_need"] = hero.meters.get("repair_need", 0) + 1
    out.append("That meant more fixing later.")
    return out


def _r_trust(world: World) -> list[str]:
    out: list[str] = []
    hero = world.get("Hero")
    if hero.memes.get("honesty", 0) < 1:
        return out
    sig = ("trust",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    hero.meters["trust"] = hero.meters.get("trust", 0) + 1
    out.append(f"{hero.id}'s honest choice made the path feel steadier.")
    return out


RULES = [_r_spill, _r_repair, _r_trust]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------
def quest_is_reasonable(place: Place, quest: Quest, tool: Tool) -> bool:
    if place.id == "market" and quest.id == "carry_water":
        return tool.id == "dipper"
    if quest.id == "deliver_scroll":
        return tool.id in {"satchel", "cloak"}
    if quest.id == "bring_supplies":
        return tool.id in {"satchel", "dipper"}
    return True


def explain_rejection(place: Place, quest: Quest, tool: Tool) -> str:
    return (
        f"(No story: at {place.label}, {quest.gerund} with {tool.label} would not be a sensible adventure. "
        f"The plan needs a tool that actually helps with {quest.risk}.)"
    )


# ---------------------------------------------------------------------------
# Narrative pieces
# ---------------------------------------------------------------------------
def inner_monologue(world: World, hero: Entity, quest: Quest) -> None:
    lines = [
        f"{hero.id} thought, 'If I rush now, I might make a bad ending.'",
        f"{hero.id} also thought, 'My moral value is to be honest, even when a shortcut looks easy.'",
        f"{hero.id} wondered whether to formulate a careful plan instead of pretending the danger was small.",
    ]
    world.inner_monologue.extend(lines)
    for line in lines:
        world.say(line)


def open_story(world: World, hero: Entity, mentor: Entity, quest: Quest, tool: Tool) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a brave heart who wanted to {quest.verb} and earn a small stipend."
    )
    world.say(
        f"{hero.id}'s {mentor.pronoun('possessive')} mentor handed over {tool.label} and said it could help on the road."
    )
    world.say(
        f"{hero.id} loved the idea of adventure, but the path ahead looked tricky enough to make anyone think twice."
    )


def formulate_plan(world: World, hero: Entity, quest: Quest, tool: Tool) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    hero.memes["courage"] = hero.memes.get("courage", 0) + 1
    world.say(
        f"{hero.id} tried to formulate a safe plan: carry the load slowly, keep the {tool.label} ready, and finish the job cleanly."
    )
    world.say(
        f"The plan sounded simple, but the trail could still turn slippery and the dipper could still betray a careless hand."
    )


def choose_shortcut(world: World, hero: Entity, quest: Quest, tool: Tool) -> None:
    hero.memes["greed"] = hero.memes.get("greed", 0) + 1
    hero.memes["doubt"] = hero.memes.get("doubt", 0) + 1
    hero.meters["risk"] = hero.meters.get("risk", 0) + 1
    world.say(
        f"Then {hero.id} saw a faster way and felt tempted to skip the careful steps."
    )
    world.say(
        f"{hero.id} whispered, 'Maybe I can finish sooner and still collect the stipend.'"
    )
    inner_monologue(world, hero, quest)


def bad_turn(world: World, hero: Entity, quest: Quest, tool: Tool) -> None:
    hero.meters["mud"] = hero.meters.get("mud", 0) + 1
    hero.memes["guilt"] = hero.memes.get("guilt", 0) + 1
    world.say(
        f"But the shortcut stumbled into trouble, and the little dipper tipped as the path shivered under {hero.id}'s feet."
    )
    propagate(world, narrate=True)
    world.say(
        f"{hero.id} froze, because the story was now leaning toward a bad ending."
    )


def honest_turn(world: World, hero: Entity, mentor: Entity, quest: Quest, tool: Tool) -> None:
    hero.memes["honesty"] = hero.memes.get("honesty", 0) + 1
    hero.memes["pride"] = hero.memes.get("pride", 0) + 1
    hero.meters["trust"] = hero.meters.get("trust", 0) + 1
    world.say(
        f"{hero.id} took a breath and chose the moral value of honesty instead of hiding the mistake."
    )
    world.say(
        f"{hero.id} told the mentor about the spill, then used the {tool.label} properly to steady the load."
    )
    propagate(world, narrate=True)
    world.say(
        f"That honest choice made the road feel lighter, even if the shoes were still a little muddy."
    )


def end_story(world: World, hero: Entity, mentor: Entity, quest: Quest) -> None:
    hero.memes["hope"] = hero.memes.get("hope", 0) + 1
    if hero.meters.get("mud", 0) >= 1 and hero.memes.get("honesty", 0) >= 1:
        world.say(
            f"In the end, {hero.id} still earned the stipend, and the day became a better adventure because the truth came first."
        )
    else:
        world.say(
            f"In the end, {hero.id} reached the goal, but the trail left a warning behind it."
        )
    world.say(
        f"{hero.id} looked back at the road and knew that a careful plan and a honest heart were worth more than a shortcut."
    )


def tell(place: Place, quest: Quest, tool: Tool, hero_name: str, hero_type: str, trait: str, mentor_type: str) -> World:
    world = World(place)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        meters={"risk": 0, "mud": 0, "trust": 0},
        memes={"hope": 0, "doubt": 0, "greed": 0, "courage": 0, "guilt": 0, "pride": 0, "honesty": 0},
    ))
    mentor = world.add(Entity(
        id="Mentor",
        kind="character",
        type=mentor_type,
        label="the mentor",
        meters={"trust": 0},
        memes={"patience": 0},
    ))
    tool_ent = world.add(Entity(
        id=tool.id,
        type="tool",
        label=tool.label,
        phrase=tool.phrase,
        carried_by=hero.id,
        useful=True,
        sturdy=True,
    ))
    world.facts["quest"] = quest
    world.facts["tool"] = tool
    world.facts["hero"] = hero
    world.facts["mentor"] = mentor
    world.facts["trait"] = trait

    open_story(world, hero, mentor, quest, tool_ent)
    world.para()
    formulate_plan(world, hero, quest, tool_ent)
    choose_shortcut(world, hero, quest, tool_ent)
    world.para()
    bad_turn(world, hero, quest, tool_ent)
    world.para()
    honest_turn(world, hero, mentor, quest, tool_ent)
    end_story(world, hero, mentor, quest)
    return world


# ---------------------------------------------------------------------------
# Prompting and QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    quest: Quest = _safe_fact(world, f, "quest")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))
    return [
        f'Write an adventure story for a young child that includes the word "{quest.keyword}" and the idea of a stipend.',
        f"Tell a story where {hero.id} must formulate a plan, but a little {tool.label} nearly causes a bad ending.",
        f"Write a short adventure with an inner monologue, a moral value, and a careful ending after a tricky mistake.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    mentor = _safe_fact(world, f, "mentor")
    quest: Quest = _safe_fact(world, f, "quest")
    tool: Tool = (f.get("tool") or next(iter(TOOLS.values())))

    qa = [
        QAItem(
            question=f"What did {hero.id} want to do in the adventure?",
            answer=f"{hero.id} wanted to {quest.verb} and earn a small stipend.",
        ),
        QAItem(
            question=f"What did {hero.id} try to do before the trouble started?",
            answer=f"{hero.id} tried to formulate a careful plan, because rushing could lead to a bad ending.",
        ),
        QAItem(
            question=f"What tool did {mentor.id} give {hero.id}?",
            answer=f"{mentor.id} gave {hero.id} {tool.label}, which could help steady the trip.",
        ),
        QAItem(
            question=f"Why did the story almost become a bad ending?",
            answer=f"The story almost became a bad ending because {hero.id} took a shortcut and the little dipper tipped at the wrong time.",
        ),
        QAItem(
            question=f"What moral value helped {hero.id} finish the day well?",
            answer="Honesty helped, because telling the truth made it possible to fix the mistake and keep going.",
        ),
    ]
    return qa


WORLD_KNOWLEDGE = {
    "stipend": [
        QAItem(
            question="What is a stipend?",
            answer="A stipend is a small amount of money or support given for helping with a job, practice, or project.",
        )
    ],
    "formulate": [
        QAItem(
            question="What does it mean to formulate a plan?",
            answer="To formulate a plan means to think carefully and make a plan step by step.",
        )
    ],
    "dipper": [
        QAItem(
            question="What is a dipper used for?",
            answer="A dipper is a tool used to scoop, pour, or carry a little liquid.",
        )
    ],
    "moral value": [
        QAItem(
            question="What is a moral value?",
            answer="A moral value is an important idea about how to treat people and make good choices, such as honesty or kindness.",
        )
    ],
    "inner monologue": [
        QAItem(
            question="What is inner monologue?",
            answer="Inner monologue is the quiet voice of a character's own thoughts inside their head.",
        )
    ],
    "bad ending": [
        QAItem(
            question="What is a bad ending in a story?",
            answer="A bad ending is when things go wrong at the end of a story instead of turning out safely or happily.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        *WORLD_KNOWLEDGE["stipend"],
        *WORLD_KNOWLEDGE["formulate"],
        *WORLD_KNOWLEDGE["dipper"],
        *WORLD_KNOWLEDGE["moral value"],
        *WORLD_KNOWLEDGE["inner monologue"],
        *WORLD_KNOWLEDGE["bad ending"],
    ]


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.carried_by:
            parts.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.kind:9}) {' '.join(parts)}")
    if world.inner_monologue:
        lines.append("  inner_monologue:")
        for line in world.inner_monologue:
            lines.append(f"    - {line}")
    lines.append(f"  fired rules: {sorted(world.fired)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
place(harbor).
place(forest).
place(market).
place(hill).

quest(deliver_scroll).
quest(carry_water).
quest(bring_supplies).

tool(dipper).
tool(satchel).
tool(cloak).

affords(harbor,cross).
affords(harbor,deliver).
affords(forest,cross).
affords(forest,deliver).
affords(market,deliver).
affords(hill,cross).
affords(hill,deliver).

helps(dipper,spill).
helps(dipper,mud).
helps(dipper,soaked).
helps(satchel,lost).
helps(satchel,wind).
helps(cloak,soaked).

reasonable(P,Q,T) :- place(P), quest(Q), tool(T), valid_combo(P,Q,T).

valid_combo(market,carry_water,dipper).
valid_combo(harbor,deliver_scroll,satchel).
valid_combo(harbor,deliver_scroll,cloak).
valid_combo(forest,deliver_scroll,satchel).
valid_combo(forest,deliver_scroll,cloak).
valid_combo(forest,bring_supplies,satchel).
valid_combo(forest,bring_supplies,dipper).
valid_combo(hill,deliver_scroll,satchel).
valid_combo(hill,deliver_scroll,cloak).
valid_combo(hill,bring_supplies,satchel).
valid_combo(hill,bring_supplies,dipper).
valid_combo(market,deliver_scroll,satchel).
valid_combo(market,deliver_scroll,cloak).
valid_combo(market,bring_supplies,satchel).
valid_combo(market,bring_supplies,dipper).

#show valid_combo/3.
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for pid in PLACES:
        lines.append(asp.fact("place", pid))
    for qid in QUESTS:
        lines.append(asp.fact("quest", qid))
    for tid in TOOLS:
        lines.append(asp.fact("tool", tid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place in PLACES.values():
        for quest in QUESTS.values():
            for tool in TOOLS.values():
                if quest_is_reasonable(place, quest, tool):
                    combos.append((place.id, quest.id, tool.id))
    return sorted(set(combos))


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid_combo/3."))
    return sorted(set(asp.atoms(model, "valid_combo")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Params / generation
# ---------------------------------------------------------------------------
@dataclass
class StoryParams:
    place: str
    quest: str
    tool: str
    name: str
    gender: str
    mentor_type: str
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
    ap = argparse.ArgumentParser(description="Adventure story world with a stipend, a plan, and a dipper.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--quest", choices=QUESTS)
    ap.add_argument("--tool", choices=TOOLS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--mentor-type", choices=["woman", "man"])
    ap.add_argument("--trait", choices=TRAITS)
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "quest", None):
        combos = [c for c in combos if c[1] == getattr(args, "quest", None)]
    if getattr(args, "tool", None):
        combos = [c for c in combos if c[2] == getattr(args, "tool", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, quest, tool = (list(rng.choice(combos)) + [None, None, None])[:3]
    gender = getattr(args, "gender", None) or rng.choice(TYPES)
    name = getattr(args, "name", None) or rng.choice(NAMES)
    mentor_type = getattr(args, "mentor_type", None) or ("woman" if gender == "boy" else "man")
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)

    if getattr(args, "quest", None) and getattr(args, "tool", None) and not quest_is_reasonable(_safe_lookup(PLACES, place), _safe_lookup(QUESTS, quest), _safe_lookup(TOOLS, tool)):
        return _fallback_storyparams(args, rng, StoryParams, globals())

    return StoryParams(place=place, quest=quest, tool=tool, name=name, gender=gender, mentor_type=mentor_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(PLACES, params.place), _safe_lookup(QUESTS, params.quest), _safe_lookup(TOOLS, params.tool), params.name, params.gender, params.trait, params.mentor_type)
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
        print(asp_program("#show valid_combo/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp

        combos = asp_valid_combos()
        print(f"{len(combos)} compatible place/quest/tool combos:\n")
        for p, q, t in combos:
            print(f"  {p:8} {q:16} {t}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="market", quest="carry_water", tool="dipper", name="Nina", gender="girl", mentor_type="woman", trait="careful"),
            StoryParams(place="forest", quest="bring_supplies", tool="satchel", name="Milo", gender="boy", mentor_type="man", trait="brave"),
            StoryParams(place="hill", quest="deliver_scroll", tool="cloak", name="Tara", gender="girl", mentor_type="woman", trait="curious"),
            StoryParams(place="harbor", quest="deliver_scroll", tool="satchel", name="Jun", gender="boy", mentor_type="man", trait="stubborn"),
        ]
        samples = [generate(p) for p in curated]
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
            header = f"### {p.name}: {p.quest} at {p.place} (tool: {p.tool})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
