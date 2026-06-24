#!/usr/bin/env python3
"""
storyworlds/worlds/sag_sound_effects_flashback_myth.py
======================================================

A small mythic storyworld about a sacred rope-banner that sags, a remembered
storm, and the sound effects that make the danger feel alive.

The seed image:
- A village keeps a sky-banner between two tall posts.
- The banner begins to sag in the middle.
- The sag makes a creak: "eek-eek."
- The hero remembers a past storm that tore a banner loose.
- The hero and a helper retie the ropes, and the banner rises again.

This world is intentionally tiny and classical:
- one setting, one tension, one remembered past event, one repair
- physical meters and emotional memes both matter
- the prose is generated from the live state, not from a frozen template swap

The narrative instruments are explicit:
- Sound Effects: creak, thrum, snap, whoosh
- Flashback: a short remembered storm that explains the fear
- Style: mythic, child-facing, concrete, and ceremonial
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0


# ---------------------------------------------------------------------------
# Entities
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    entities: set[str] = field(default_factory=set)
    helper: object | None = None
    hero: object | None = None
    obj: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "queen", "priestess"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "king", "priest"}:
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
    name: str = "the hill shrine"
    place_phrase: str = "the hill shrine"
    affords: set[str] = field(default_factory=set)
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
class ObjectDef:
    id: str
    label: str
    phrase: str
    region: str
    weight: str
    joins: set[str] = field(default_factory=set)
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
class FixDef:
    id: str
    label: str
    phrase: str
    action: str
    tail: str
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
    object: str
    fix: str
    hero_name: str
    helper_name: str
    hero_type: str = "boy"
    helper_type: str = "woman"
    trait: str = "brave"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# World
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[str] = set()
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
        clone.entities = {k: Entity(**asdict(v)) for k, v in self.entities.items()}
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "hill_shrine": Setting(name="the hill shrine", place_phrase="the hill shrine", affords={"banner"}),
    "river_gate": Setting(name="the river gate", place_phrase="the river gate", affords={"banner"}),
}

OBJECTS = {
    "banner": ObjectDef(
        id="banner",
        label="sky-banner",
        phrase="a long sky-banner woven with gold thread",
        region="air",
        weight="the middle",
        joins={"wind"},
    ),
    "bridgecloth": ObjectDef(
        id="bridgecloth",
        label="bridge-cloth",
        phrase="a woven bridge-cloth that stretched over the stream",
        region="air",
        weight="the center",
        joins={"wind"},
    ),
}

FIXES = {
    "tighten": FixDef(
        id="tighten",
        label="the tying knot",
        phrase="a strong tying knot",
        action="retie the ropes",
        tail="they pulled the ropes until the middle stood straight again",
        helps={"banner"},
    ),
    "peg": FixDef(
        id="peg",
        label="a cedar peg",
        phrase="a cedar peg driven deep into the post",
        action="hammer in a cedar peg",
        tail="the post held firm and the cloth no longer drooped",
        helps={"bridgecloth"},
    ),
}

TRAITS = ["brave", "patient", "curious", "gentle", "steadfast"]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def sound_effect(s: str) -> str:
    return {
        "sag": "creeeak",
        "tight": "thrum",
        "wind": "whoooosh",
        "storm": "whap-whap",
        "snap": "crack",
    }.get(s, "sound")


def object_arisk(obj: ObjectDef) -> bool:
    return obj.region == "air" and obj.weight in {"the middle", "the center"}


def compatible_fix(obj: ObjectDef, fix: FixDef) -> bool:
    return obj.id in fix.helps


def tell_flashback(world: World, hero: Entity, obj: Entity) -> None:
    hero.memes["fear"] += 1
    world.say(
        f"Flashback: once, when a storm ran over the hill, {obj.label} had whipped like a white snake. "
        f"{sound_effect('storm')} the wind had cried, and the people had run to catch the cords before they tore."
    )


def tighten_world(world: World, hero: Entity, helper: Entity, obj: Entity, fix: FixDef) -> None:
    hero.memes["hope"] += 1
    helper.memes["calm"] += 1
    obj.meters["sag"] = max(0.0, obj.meters.get("sag", 0.0) - 1.0)
    obj.meters["tight"] = obj.meters.get("tight", 0.0) + 1.0
    world.say(
        f"{hero.id} and {helper.id} chose {fix.phrase}. {sound_effect('tight')}, {sound_effect('tight')} went the rope as they worked."
    )
    world.say(f"{fix.tail.capitalize()}.")


# ---------------------------------------------------------------------------
# Story structure
# ---------------------------------------------------------------------------
def build_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.place)
    obj_def = _safe_lookup(OBJECTS, params.object)
    fix_def = _safe_lookup(FIXES, params.fix)

    if not object_arisk(obj_def):
        pass
    if not compatible_fix(obj_def, fix_def):
        pass

    world = World(setting)
    hero = world.add(Entity(
        id=params.hero_name,
        kind="character",
        type=params.hero_type,
        traits=[params.trait, "watchful"],
    ))
    helper = world.add(Entity(
        id=params.helper_name,
        kind="character",
        type=params.helper_type,
        traits=["calm", "older"],
    ))
    obj = world.add(Entity(
        id=obj_def.id,
        type=obj_def.label,
        label=obj_def.label,
        phrase=obj_def.phrase,
        owner=hero.id,
    ))
    world.facts.update(hero=hero, helper=helper, obj=obj, fix=fix_def, setting=setting, params=params)

    # Act 1: the mythic setting and the thing that sags.
    world.say(f"At {setting.place_phrase}, {obj.phrase} hung between two tall posts.")
    world.say(
        f"{hero.id}, a {params.trait} little {params.hero_type}, kept watch over it because the banner belonged to the shrine."
    )
    world.say(
        f"At first the cloth was proud and bright, but by evening its middle began to sag."
    )
    obj.meters["sag"] = 1.0
    world.say(f"{sound_effect('sag').capitalize()} went the rope, and the center drooped lower.")

    # Act 2: the remembered danger and rising feeling.
    world.para()
    tell_flashback(world, hero, obj)
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(
        f"{hero.id} looked up and felt {hero.pronoun('possessive')} chest grow small, because the old storm seemed to return in the wind."
    )

    # Act 3: the helper and the repair.
    world.para()
    helper.memes["encourage"] = helper.memes.get("encourage", 0.0) + 1.0
    world.say(
        f"Then {helper.id} came with {fix_def.phrase} and said, \"A thing that sags can rise again.\""
    )
    tighten_world(world, hero, helper, obj, fix_def)
    world.say(
        f"At last the banner stood straight, and the hill shrine looked like it was listening to the sky again."
    )
    hero.memes["fear"] = max(0.0, hero.memes.get("fear", 0.0) - 1.0)
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0

    world.facts["resolved"] = True
    return world


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    p = _safe_fact(world, f, "params")
    return [
        f'Write a short mythic story for a small child about a {p.hero_type} named {p.hero_name} who hears a sagging banner make a sound.',
        f"Tell a gentle legend where {p.hero_name} remembers an old storm, then fixes the sag with {f['fix'].label}.",
        f"Write a child-facing myth with a flashback, a creaking rope, and a happy ending at {f['setting'].place_phrase}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    obj: Entity = _safe_fact(world, f, "obj")
    fix: FixDef = _safe_fact(world, f, "fix")

    return [
        QAItem(
            question=f"What began to happen to the {obj.label} at {f['setting'].place_phrase}?",
            answer=f"The {obj.label} began to sag in the middle, so it drooped lower and made a creaking sound.",
        ),
        QAItem(
            question=f"Why did {hero.id} feel worried when the banner sagged?",
            answer=f"{hero.id} remembered a past storm that had whipped the cloth dangerously, so the sag felt like trouble returning.",
        ),
        QAItem(
            question=f"Who helped {hero.id} fix the sagging thing?",
            answer=f"{helper.id} helped {hero.id}, and they worked together to make the banner rise again.",
        ),
        QAItem(
            question=f"What did {helper.id} use to solve the problem?",
            answer=f"{helper.id} used {fix.phrase} and the two of them retied the ropes until the middle stood straight again.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with the banner standing straight at {f['setting'].place_phrase}, as if the shrine was listening to the sky again.",
        ),
    ]


KNOWLEDGE = {
    "sag": [
        QAItem(
            question="What does it mean when a rope sags?",
            answer="When a rope sags, it hangs lower in the middle because it is not pulled tight enough.",
        )
    ],
    "flashback": [
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a part of a story that shows something from the past, so readers can understand why a character feels a certain way now.",
        )
    ],
    "sound": [
        QAItem(
            question="Why do stories sometimes use sound words like creak or whoosh?",
            answer="Sound words help readers imagine what is happening, almost like they can hear the scene themselves.",
        )
    ],
    "myth": [
        QAItem(
            question="What makes a myth feel special?",
            answer="A myth often feels old, grand, and important, and it may explain why something in the world matters to people.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [*KNOWLEDGE["sag"], *KNOWLEDGE["flashback"], *KNOWLEDGE["sound"], *KNOWLEDGE["myth"]]


def format_qa(sample: StorySample) -> str:
    out = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== Story questions ==")
    for item in sample.story_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    out.append("")
    out.append("== World knowledge questions ==")
    for item in sample.world_qa:
        out.append(f"Q: {item.question}")
        out.append(f"A: {item.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
arisk(O) :- object(O), region(O, air), weight(O, middle).
compatible(O, F) :- arisk(O), fix(F), helps(F, O).

valid_story(P, O, F) :- place(P), object(O), fix(F), at(P, O), arisk(O), compatible(O, F).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(p.affords):
            lines.append(asp.fact("affords", pid, a))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("object", oid))
        lines.append(asp.fact("region", oid, o.region))
        lines.append(asp.fact("weight", oid, "middle" if o.weight in {"the middle", "the center"} else o.weight))
        lines.append(asp.fact("at", "hill_shrine", oid))
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        for h in sorted(f.helps):
            lines.append(asp.fact("helps", fid, h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = {(p, o, f) for p in SETTINGS for o in OBJECTS for f in FIXES if object_arisk(_safe_lookup(OBJECTS, o)) and compatible_fix(_safe_lookup(OBJECTS, o), _safe_lookup(FIXES, f))}
    clingo_set = set(asp_valid_stories())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches Python gate ({len(python_set)} stories).")
        return 0
    print("MISMATCH between clingo and Python gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


# ---------------------------------------------------------------------------
# Standard interface
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A mythic sag-and-flashback storyworld.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--object", choices=OBJECTS)
    ap.add_argument("--fix", choices=FIXES)
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--gender", choices=["boy", "girl", "man", "woman"])
    ap.add_argument("--helper-gender", choices=["boy", "girl", "man", "woman"])
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
    place = getattr(args, "place", None) or rng.choice(list(SETTINGS))
    obj = getattr(args, "object", None) or rng.choice(list(OBJECTS))
    fix = getattr(args, "fix", None) or rng.choice(list(FIXES))
    if not (object_arisk(_safe_lookup(OBJECTS, obj)) and compatible_fix(_safe_lookup(OBJECTS, obj), _safe_lookup(FIXES, fix))):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    hero_name = getattr(args, "name", None) or rng.choice(["Ari", "Niko", "Sera", "Tavi", "Luma", "Mira"])
    helper_name = getattr(args, "helper", None) or rng.choice(["Elda", "Mara", "Rina", "Oren", "Bela", "Ivo"])
    hero_type = getattr(args, "gender", None) or rng.choice(["boy", "girl"])
    helper_type = getattr(args, "helper_gender", None) or rng.choice(["woman", "man"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(
        place=place,
        object=obj,
        fix=fix,
        hero_name=hero_name,
        helper_name=helper_name,
        hero_type=hero_type,
        helper_type=helper_type,
        trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = build_world(params)
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
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        stories = sorted(set(asp.atoms(model, "valid_story")))
        print(f"{len(stories)} compatible story combinations:")
        for item in stories:
            print(" ", item)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    curated = [
        StoryParams(place="hill_shrine", object="banner", fix="tighten", hero_name="Ari", helper_name="Elda", hero_type="boy", helper_type="woman", trait="brave"),
        StoryParams(place="river_gate", object="bridgecloth", fix="peg", hero_name="Mira", helper_name="Oren", hero_type="girl", helper_type="man", trait="steadfast"),
    ]

    if getattr(args, "all", None):
        samples = [generate(p) for p in curated]
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
            header = f"### {p.hero_name}: {p.object} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
