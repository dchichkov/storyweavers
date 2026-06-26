#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/reptile_inner_monologue_misunderstanding_moral_value_rhyming.py
==============================================================================================================================

A small classical storyworld about a reptile, an inner monologue, a misunderstanding,
and a moral-value turn, told in a rhyming, child-facing style.

Seed tale:
---
A little gecko named Pip found a shiny blue pebble on a garden path. Pip thought it
must be a special prize and decided to keep it. But while Pip was hiding it away,
a tiny bird named Bea came looking for a lost marble from her nest game. Pip worried
inside, listened to the small voice in the head, and realized the pebble might not
be a treasure to keep. Pip returned it, learned about honesty and kindness, and felt
brightly proud.

World premise:
- A reptile protagonist finds an item and misunderstands who it belongs to.
- The protagonist has an inner monologue that pushes toward a selfish choice.
- A gentle correction reveals the moral value: honesty and returning what is not yours.
- The ending proves the change through a concrete return and a happy image.

This script follows the Storyweavers world contract:
- stdlib only
- StoryParams and registries
- build_parser / resolve_params / generate / emit / main
- eager results import; lazy asp import
- inline ASP_RULES twin and asp_facts()
- --verify parity checks
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
# Entities and world state
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    keeper: Optional[str] = None
    carried_by: Optional[str] = None
    secreted: bool = False
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    friend: object | None = None
    hero: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        rept = {"subject": "it", "object": "it", "possessive": "its"}
        bird = {"subject": "she", "object": "her", "possessive": "her"}
        frog = {"subject": "he", "object": "him", "possessive": "his"}
        if self.type in {"bird", "girl", "hen"}:
            return bird[case]
        if self.type in {"boy", "frog", "boy-reptile"}:
            return frog[case]
        return rept[case]

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
    place: str = "the garden path"
    indoors: bool = False
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
class ObjectKind:
    id: str
    label: str
    phrase: str
    moral_value: str  # honesty, kindness, sharing
    belongs_to: str
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
class Action:
    id: str
    verb: str
    gerund: str
    worry: str
    rhyme_noun: str
    keyword: str
    tags: set[str] = field(default_factory=set)
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
        self.trace: list[str] = []

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
            self.trace.append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)

    def copy(self) -> "World":
        import copy

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "garden": Setting(place="the garden path", indoors=False, affords={"find", "return"}),
    "pond": Setting(place="the pond bank", indoors=False, affords={"find", "return"}),
    "nest": Setting(place="the nest nook", indoors=False, affords={"find", "return"}),
}

ACTIVITIES = {
    "find": Action(
        id="find",
        verb="find a shiny pebble",
        gerund="finding a shiny pebble",
        worry="take the pebble home",
        rhyme_noun="pebble",
        keyword="pebble",
        tags={"shiny", "find", "moral"},
    ),
    "marble": Action(
        id="marble",
        verb="find a bright marble",
        gerund="finding a bright marble",
        worry="keep the marble",
        rhyme_noun="marble",
        keyword="marble",
        tags={"shiny", "find", "moral"},
    ),
    "shell": Action(
        id="shell",
        verb="find a tiny shell",
        gerund="finding a tiny shell",
        worry="hide the shell",
        rhyme_noun="shell",
        keyword="shell",
        tags={"find", "moral"},
    ),
}

OBJECTS = {
    "pebble": ObjectKind(
        id="pebble",
        label="pebble",
        phrase="a shiny blue pebble",
        moral_value="honesty",
        belongs_to="bird",
    ),
    "marble": ObjectKind(
        id="marble",
        label="marble",
        phrase="a bright green marble",
        moral_value="kindness",
        belongs_to="bird",
    ),
    "shell": ObjectKind(
        id="shell",
        label="shell",
        phrase="a tiny shell with a spiral glow",
        moral_value="sharing",
        belongs_to="turtle",
    ),
}

REPTILES = ["Pip", "Rex", "Sly", "Milo", "Nori", "Tiko"]
BIRDS = ["Bea", "Lula", "Tia", "Mimi", "Cleo"]
TRAITS = ["small", "brave", "curious", "gentle", "prickly", "bright"]


@dataclass
class StoryParams:
    place: str
    activity: str
    object_kind: str
    reptile_name: str
    reptile_type: str
    bird_name: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Rhyming narration helpers
# ---------------------------------------------------------------------------
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


def rhyme_line(a: str, b: str) -> str:
    return f"{a} {b}"


def intro(world: World, hero: Entity, friend: Entity, obj: Entity, action: Action) -> None:
    world.say(
        f"{hero.id} the little reptile liked warm sun and steady play, "
        f"and {friend.id} liked songs that floated softly through the day."
    )
    world.say(
        f"On {world.setting.place}, {hero.id} saw {obj.phrase} shine, "
        f"and thought, \"That looks like mine, all mine, all mine.\""
    )


def inner_monologue(world: World, hero: Entity, obj: Entity) -> None:
    hero.memes["want"] = hero.memes.get("want", 0.0) + 1
    hero.memes["greedy"] = hero.memes.get("greedy", 0.0) + 1
    world.say(
        f"Inside {hero.id}'s head, a tiny voice would sing: "
        f"\"Keep the glow, don't let it go; hide it fast and crawl away.\""
    )
    world.say(
        f"But another small thought came tapping like a pebble in a drum: "
        f"\"If it is not yours, be fair and pure; the kindest choice is the truest one.\""
    )


def misunderstanding(world: World, hero: Entity, friend: Entity, obj: Entity) -> None:
    hero.memes["confusion"] = hero.memes.get("confusion", 0.0) + 1
    world.say(
        f"{hero.id} tucked the treasure near a stone, then heard a worried little call, "
        f"\"My marble's missing from the mossy wall!\""
    )
    world.say(
        f"{hero.id} blinked and thought, \"Oh dear, oh no, did I find a thing that wasn't so?\""
    )


def reveal(world: World, hero: Entity, friend: Entity, obj: Entity) -> None:
    hero.memes["empathy"] = hero.memes.get("empathy", 0.0) + 1
    world.say(
        f"{friend.id} smiled and said, \"That shiny round thing fits my game; "
        f"I came to look for it, and call its name.\""
    )
    world.say(
        f"{hero.id} felt a warm, brave spark inside, "
        f"and knew the honest path was better than the hide-and-hide."
    )


def return_item(world: World, hero: Entity, friend: Entity, obj: Entity) -> None:
    hero.memes["honesty"] = hero.memes.get("honesty", 0.0) + 1
    obj.carried_by = friend.id
    obj.secreted = False
    world.say(
        f"{hero.id} brought the pebble back with care, "
        f"and laid it in {friend.id}'s paws, so bright and fair."
    )
    world.say(
        f"\"It wasn't mine,\" {hero.id} said with a tiny grin, "
        f"\"The honest heart feels light within.\""
    )


def ending(world: World, hero: Entity, friend: Entity, obj: Entity) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    world.say(
        f"{friend.id} cheered, and both of them danced in a sunny ring; "
        f"the pebble stayed with its true owner, and the garden seemed to sing."
    )
    world.say(
        f"{hero.id} went home with a lighter chest, "
        f"for telling the truth had made the day the best."
    )


# ---------------------------------------------------------------------------
# World simulation
# ---------------------------------------------------------------------------
def tell(setting: Setting, action: Action, obj_kind: ObjectKind, reptile_name: str, reptile_type: str,
         bird_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=reptile_name, kind="character", type=reptile_type))
    friend = world.add(Entity(id=bird_name, kind="character", type="bird"))
    obj = world.add(Entity(
        id=obj_kind.id,
        kind="thing",
        type=obj_kind.id,
        label=obj_kind.label,
        phrase=obj_kind.phrase,
        owner=friend.id,
        keeper=friend.id,
        secreted=True,
    ))
    hero.meters["warmth"] = 1.0
    friend.meters["worry"] = 1.0

    intro(world, hero, friend, obj, action)
    world.para()
    inner_monologue(world, hero, obj)
    misunderstanding(world, hero, friend, obj)
    world.para()
    reveal(world, hero, friend, obj)
    return_item(world, hero, friend, obj)
    ending(world, hero, friend, obj)

    world.facts.update(
        hero=hero,
        friend=friend,
        obj=obj,
        action=action,
        obj_kind=obj_kind,
        setting=setting,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    action = _safe_fact(world, f, "action")
    obj_kind = _safe_fact(world, f, "obj_kind")
    return [
        f'Write a short rhyming story for a young child about {hero.id}, a reptile, who gets confused about {obj_kind.label}.',
        f"Tell a gentle rhyme where {hero.id} hears an inner voice, makes a mistake about {friend.id}'s {obj_kind.label}, and chooses the honest thing.",
        f'Create a tiny moral-value story with a reptile, a lost {obj_kind.label}, and a happy return at {world.setting.place}.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    friend = _safe_fact(world, f, "friend")
    obj = _safe_fact(world, f, "obj")
    action = _safe_fact(world, f, "action")
    obj_kind = _safe_fact(world, f, "obj_kind")
    return [
        QAItem(
            question=f"Who found the {obj_kind.label} on the path?",
            answer=f"{hero.id}, the little reptile, found the {obj_kind.label} on {world.setting.place}.",
        ),
        QAItem(
            question=f"What was {hero.id} thinking inside at first?",
            answer=f"{hero.id} first thought about keeping the {obj_kind.label}, but the inner voice reminded {hero.pronoun('object')} to be fair and honest.",
        ),
        QAItem(
            question=f"Why did {friend.id} look worried?",
            answer=f"{friend.id} was looking for a lost {obj_kind.label}, so {friend.pronoun('subject')} felt worried until {hero.id} listened and helped.",
        ),
        QAItem(
            question=f"What did {hero.id} do at the end?",
            answer=f"{hero.id} returned the {obj_kind.label} to {friend.id}, which showed honesty and kindness.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a reptile?",
            answer="A reptile is a cold-blooded animal, like a lizard, snake, or turtle, that often has scales.",
        ),
        QAItem(
            question="What does honesty mean?",
            answer="Honesty means telling the truth and giving things back when they are not yours.",
        ),
        QAItem(
            question="Why is it kind to return a lost thing?",
            answer="It is kind to return a lost thing because it helps the owner feel safe and happy again.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Story generation
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for action_id in setting.affords:
            for obj_id in OBJECTS:
                combos.append((place, action_id, obj_id))
    return combos


def explain_rejection(setting: Setting, action: Action, obj: ObjectKind) -> str:
    return (
        f"(No story: this setup does not create a clear misunderstanding with a moral-value turn. "
        f"Try the garden path with a shining object and a bird owner.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Rhyming reptile storyworld with inner monologue, misunderstanding, and moral value."
    )
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--object-kind", dest="object_kind", choices=OBJECTS)
    ap.add_argument("--name")
    ap.add_argument("--friend")
    ap.add_argument("--reptile-type", dest="reptile_type", default="lizard")
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
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "object_kind", None) is None or c[2] == getattr(args, "object_kind", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, obj = rng.choice(list(combos))
    reptile_name = getattr(args, "name", None) or rng.choice(REPTILES)
    bird_name = getattr(args, "friend", None) or rng.choice(BIRDS)
    return StoryParams(
        place=place,
        activity=activity,
        object_kind=obj,
        reptile_name=reptile_name,
        reptile_type=getattr(args, "reptile_type", None),
        bird_name=bird_name,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(OBJECTS, params.object_kind),
        params.reptile_name,
        params.reptile_type,
        params.bird_name,
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.kind:
            bits.append(f"kind={e.kind}")
        if e.type:
            bits.append(f"type={e.type}")
        if e.owner:
            bits.append(f"owner={e.owner}")
        if e.keeper:
            bits.append(f"keeper={e.keeper}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        if e.secreted:
            bits.append("secreted=True")
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"  {e.id}: " + ", ".join(bits))
    return "\n".join(lines)


CURATED = [
    StoryParams(place="garden", activity="find", object_kind="pebble", reptile_name="Pip", reptile_type="gecko", bird_name="Bea"),
    StoryParams(place="pond", activity="find", object_kind="marble", reptile_name="Rex", reptile_type="lizard", bird_name="Lula"),
    StoryParams(place="nest", activity="find", object_kind="shell", reptile_name="Nori", reptile_type="newt", bird_name="Mimi"),
]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
% A valid story needs a place where the finding can happen.
valid_story(Place, Act, Obj) :- setting(Place), activity(Act), object(Obj),
                                affords(Place, Act), can_misunderstand(Obj), can_return(Obj).

% The moral-value turn is possible when the object belongs to another creature.
can_misunderstand(O) :- belongs_to(O, bird).
can_return(O) :- belongs_to(O, bird).

% Human-readable summarizing predicate for parity checks.
valid(Place, Act, Obj) :- valid_story(Place, Act, Obj).
"""


def asp_facts() -> str:
    import asp

    lines: list[str] = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
        for act in sorted(_safe_lookup(SETTINGS, sid).affords):
            lines.append(asp.fact("affords", sid, act))
    for aid in ACTIVITIES:
        lines.append(asp.fact("activity", aid))
    for oid, obj in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("belongs_to", oid, obj.belongs_to))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
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
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible stories:\n")
        for place, act, obj in triples:
            print(f"  {place:10} {act:6} {obj:8}")
        return

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
            header = f"### {p.reptile_name}: {p.activity} at {p.place} (object: {p.object_kind})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
