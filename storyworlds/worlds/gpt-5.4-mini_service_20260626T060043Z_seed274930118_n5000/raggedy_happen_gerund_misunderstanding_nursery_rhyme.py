#!/usr/bin/env python3
"""
A small nursery-rhyme story world about a raggedy little misunderstanding.

Premise:
- A child hears a strange phrase and thinks a plan means something else.
- The world carries both physical state (meters) and emotional state (memes).
- A gentle correction turns confusion into a tidy, happy ending.

This world is intentionally small and constraint-driven.
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
# World model
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
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hero: object | None = None
    obj: object | None = None
    parent: object | None = None
    def __post_init__(self) -> None:
        for k in ("torn", "dirty", "lost", "fixed"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "confusion", "relief"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoor: bool
    afford: set[str] = field(default_factory=set)
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
class ObjectCfg:
    id: str
    label: str
    phrase: str
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
class EventCfg:
    id: str
    gerund: str
    verb: str
    misunderstanding: str
    true_meaning: str
    clue: str
    risk: str
    place_word: str
    weather: str = ""
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
class FixCfg:
    id: str
    label: str
    action: str
    benefit: str
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
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()

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
            self.lines.append(text)

    def para(self) -> None:
        if self.lines and self.lines[-1] != "":
            self.lines.append("")

    def render(self) -> str:
        out: list[str] = []
        para: list[str] = []
        for line in self.lines:
            if line == "":
                if para:
                    out.append(" ".join(para))
                    para = []
            else:
                para.append(line)
        if para:
            out.append(" ".join(para))
        return "\n\n".join(out)

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "nursery": Setting(place="the nursery", indoor=True, afford={"tune", "mend", "mix"}),
    "garden": Setting(place="the garden", indoor=False, afford={"tune", "mend"}),
    "meadow": Setting(place="the meadow", indoor=False, afford={"tune", "mix"}),
}

EVENTS = {
    "tune": EventCfg(
        id="tune",
        gerund="tuning the little bell",
        verb="ring the little bell",
        misunderstanding="going on a big stormy spree",
        true_meaning="making a bright little song",
        clue="the bell only made a tiny tinkle",
        risk="it might startle the kitten",
        place_word="toy shelf",
        weather="",
    ),
    "mend": EventCfg(
        id="mend",
        gerund="mending the raggedy kite",
        verb="mend the raggedy kite",
        misunderstanding="throwing the kite away",
        true_meaning="stitching it up so it can fly",
        clue="the thread and needle sat beside the torn edge",
        risk="the breeze might tug the torn ribbon loose",
        place_word="work basket",
        weather="windy",
    ),
    "mix": EventCfg(
        id="mix",
        gerund="mixing the mooncake batter",
        verb="mix the mooncake batter",
        misunderstanding="making a muddy mess",
        true_meaning="stirring the sweet batter for supper",
        clue="the spoon was all sugar, not mud",
        risk="it could spill onto the little apron",
        place_word="kitchen table",
        weather="",
    ),
}

OBJECTS = {
    "kite": ObjectCfg(
        id="kite",
        label="kite",
        phrase="a raggedy kite with a bright red tail",
        region="hands",
    ),
    "apron": ObjectCfg(
        id="apron",
        label="apron",
        phrase="a clean apron with blue trim",
        region="torso",
    ),
    "bell": ObjectCfg(
        id="bell",
        label="bell",
        phrase="a tiny silver bell",
        region="hands",
    ),
}

FIXES = {
    "thread": FixCfg(
        id="thread",
        label="needle and thread",
        action="stitch the tear",
        benefit="mend the raggedy thing",
    ),
    "song": FixCfg(
        id="song",
        label="a little song",
        action="sing softly",
        benefit="settle the worry",
    ),
    "cloth": FixCfg(
        id="cloth",
        label="a clean cloth",
        action="wipe the spill",
        benefit="keep the apron neat",
    ),
}

NAMES = ["Mina", "Lily", "Poppy", "Nora", "Ruby", "Elsie", "Mabel", "June"]
PARENTS = [("mother", "mom"), ("father", "dad")]
TRAITS = ["cheery", "curious", "sprightly", "gentle", "bouncy"]


# ---------------------------------------------------------------------------
# Story parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    event: str
    object: str
    name: str
    gender: str
    parent: str
    trait: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for event_id in setting.afford:
            for obj_id in OBJECTS:
                if event_id == "mend" and obj_id == "kite":
                    combos.append((place, event_id, obj_id))
                elif event_id == "mix" and obj_id == "apron":
                    combos.append((place, event_id, obj_id))
                elif event_id == "tune" and obj_id == "bell":
                    combos.append((place, event_id, obj_id))
    return combos


def explain_rejection(event: EventCfg, obj: ObjectCfg) -> str:
    return (
        f"(No story: {event.gerund} does not fit {obj.label}. "
        f"This world needs a clear misunderstanding that can be gently fixed.)"
    )


# ---------------------------------------------------------------------------
# Prose helpers
# ---------------------------------------------------------------------------

def article(word: str) -> str:
    return "an" if word[:1].lower() in "aeiou" else "a"


def opening_rhyme(hero: Entity, parent: Entity, obj: Entity, event: EventCfg) -> str:
    return (
        f"Little {hero.id} in the soft-lit lane loved {event.gerund} every day, "
        f"and {hero.pronoun('possessive')} {obj.label} seemed to hum and sway."
    )


def mismatch_line(hero: Entity, parent: Entity, event: EventCfg) -> str:
    return (
        f"When {hero.id} heard {hero.pronoun('possessive')} {parent.id} say, "
        f'"Let us {event.verb}," {hero.id} thought it meant {event.misunderstanding}.'
    )


def clue_line(event: EventCfg) -> str:
    return (
        f"But the {event.clue}, and that showed the truth: it was really {event.true_meaning}."
    )


def resolve_line(hero: Entity, parent: Entity, fix: FixCfg, event: EventCfg, obj: Entity) -> str:
    return (
        f"Then {hero.id} and {hero.pronoun('possessive')} {parent.id} took {fix.label}, "
        f"{fix.action}, and smiled at the tidy little scene; the raggedy day turned bright and keen."
    )


# ---------------------------------------------------------------------------
# Story simulation
# ---------------------------------------------------------------------------

def simulate(world: World, hero: Entity, parent: Entity, obj: Entity, event: EventCfg) -> None:
    hero.memes["joy"] += 1
    hero.memes["confusion"] += 1
    obj.worn_by = hero.id if obj.region == "hands" else None

    world.say(opening_rhyme(hero, parent, obj, event))
    world.para()

    world.say(
        f"One day at {world.setting.place}, {hero.id} wanted to {event.verb}, "
        f"but {hero.pronoun('possessive')} {parent.id} frowned with care."
    )
    world.say(mismatch_line(hero, parent, event))
    world.say(
        f"{hero.id} looked raggedy and puzzled, because the words sounded like a warning in the air."
    )

    hero.memes["worry"] += 1
    parent.memes["worry"] += 1
    world.facts["misunderstanding"] = event.misunderstanding
    world.facts["true_meaning"] = event.true_meaning
    world.facts["risk"] = event.risk

    world.para()
    world.say(clue_line(event))
    world.say(
        f"{hero.id} blinked and saw the clue, then laughed a little at the mix-up too."
    )

    fix = choose_fix(event)
    hero.memes["confusion"] = 0.0
    hero.memes["relief"] += 1
    parent.memes["relief"] += 1

    if event.id == "mend":
        obj.meters["torn"] += 1
        obj.meters["fixed"] += 1
    elif event.id == "mix":
        obj.meters["dirty"] += 1
        obj.meters["fixed"] += 1
    else:
        obj.meters["fixed"] += 1

    world.para()
    world.say(resolve_line(hero, parent, fix, event, obj))
    world.say(
        f"In the end, {hero.id} was glad to know the words meant something kinder than first believed."
    )
    world.facts["fix"] = fix
    world.facts["hero"] = hero
    world.facts["parent"] = parent
    world.facts["object"] = obj
    world.facts["event"] = event


def choose_fix(event: EventCfg) -> FixCfg:
    if event.id == "mend":
        return FIXES["thread"]
    if event.id == "mix":
        return FIXES["cloth"]
    return FIXES["song"]


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    event: EventCfg = _safe_fact(world, f, "event")  # type: ignore[assignment]
    obj: Entity = _safe_fact(world, f, "object")  # type: ignore[assignment]
    return [
        f'Write a short nursery-rhyme story about a raggedy misunderstanding with "{event.gerund}".',
        f"Tell a gentle story where {hero.id} thinks {event.misunderstanding} but learns it really means {event.true_meaning}.",
        f'Create a child-friendly rhyme that includes "{obj.label}" and ends with a happy correction.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")  # type: ignore[assignment]
    parent: Entity = _safe_fact(world, f, "parent")  # type: ignore[assignment]
    obj: Entity = _safe_fact(world, f, "object")  # type: ignore[assignment]
    event: EventCfg = _safe_fact(world, f, "event")  # type: ignore[assignment]
    fix: FixCfg = _safe_fact(world, f, "fix")  # type: ignore[assignment]
    return [
        QAItem(
            question=f"What did {hero.id} think {hero.pronoun('possessive')} {parent.id} meant?",
            answer=f"{hero.id} thought it meant {event.misunderstanding}.",
        ),
        QAItem(
            question=f"What did the words really mean in the story?",
            answer=f"They really meant {event.true_meaning}.",
        ),
        QAItem(
            question=f"What helped after the misunderstanding with the {obj.label}?",
            answer=f"{fix.label} helped because it let the family {fix.action}.",
        ),
        QAItem(
            question=f"How did {hero.id} feel at the end?",
            answer=f"{hero.id} felt relieved and happy once the misunderstanding was cleared up.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a misunderstanding?",
            answer=(
                "A misunderstanding happens when someone hears or thinks the wrong thing, "
                "so they need a kind explanation to understand."
            ),
        ),
        QAItem(
            question="What does raggedy mean?",
            answer=(
                "Raggedy means a little worn, torn, or scruffy, like something that has been used a lot."
            ),
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story QA ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World QA ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
place(P) :- setting(P).
event(E) :- action(E).
object(O) :- thing(O).

valid(P, E, O) :- affords(P, E), fits(E, O).

misunderstanding(E, M) :- action(E), confusing(E, M).
resolution(E, F) :- fix(F), solves(F, E).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.afford):
            lines.append(asp.fact("affords", sid, a))
    for eid, e in EVENTS.items():
        lines.append(asp.fact("action", eid))
        lines.append(asp.fact("confusing", eid, e.misunderstanding))
        lines.append(asp.fact("meaning", eid, e.true_meaning))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("thing", oid))
        lines.append(asp.fact("fits", "mend", oid) if oid == "kite" else "")
        lines.append(asp.fact("fits", "mix", oid) if oid == "apron" else "")
        lines.append(asp.fact("fits", "tune", oid) if oid == "bell" else "")
    for fid, f in FIXES.items():
        lines.append(asp.fact("fix", fid))
        lines.append(asp.fact("solves", fid, "mend") if fid == "thread" else "")
        lines.append(asp.fact("solves", fid, "mix") if fid == "cloth" else "")
        lines.append(asp.fact("solves", fid, "tune") if fid == "song" else "")
    return "\n".join(x for x in lines if x)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - ac:
        print("  only in Python:", sorted(py - ac))
    if ac - py:
        print("  only in ASP:", sorted(ac - py))
    return 1


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A raggedy nursery-rhyme misunderstanding world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--event", choices=EVENTS)
    ap.add_argument("--object", dest="object_", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
    ap.add_argument("--name")
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
    if getattr(args, "event", None) and getattr(args, "object_", None):
        ev = _safe_lookup(EVENTS, getattr(args, "event", None))
        obj = _safe_lookup(OBJECTS, getattr(args, "object_", None))
        ok = (getattr(args, "event", None) == "mend" and getattr(args, "object_", None) == "kite") or (
            getattr(args, "event", None) == "mix" and getattr(args, "object_", None) == "apron"
        ) or (getattr(args, "event", None) == "tune" and getattr(args, "object_", None) == "bell")
        if not ok:
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = valid_combos()
    combos = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "event", None) is None or c[1] == getattr(args, "event", None))
        and (getattr(args, "object_", None) is None or c[2] == getattr(args, "object_", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, event, obj = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, event=event, object=obj, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    event = _safe_lookup(EVENTS, params.event)
    obj_cfg = _safe_lookup(OBJECTS, params.object)
    world = World(setting)

    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent_id = "Mom" if params.parent == "mother" else "Dad"
    parent = world.add(Entity(id=parent_id, kind="character", type=params.parent))
    obj = world.add(Entity(
        id=obj_cfg.id,
        type=obj_cfg.id,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        owner=hero.id,
        caretaker=parent.id,
        plural=obj_cfg.plural,
    ))

    world.say(f"Little {hero.id} was {params.trait} and bright.")
    world.say(
        f"{hero.id} loved {event.gerund}, and {hero.pronoun('possessive')} {obj.label} was {obj_cfg.phrase}."
    )
    world.para()

    simulate(world, hero, parent, obj, event)

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
        print()
        print("--- world trace ---")
        for e in sample.world.entities.values():
            m = {k: v for k, v in e.meters.items() if v}
            s = {k: v for k, v in e.memes.items() if v}
            bits = []
            if m:
                bits.append(f"meters={m}")
            if s:
                bits.append(f"memes={s}")
            print(f"{e.id}: {e.type} {' '.join(bits)}")
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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        vals = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(vals)} valid combinations:")
        for x in vals:
            print(x)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        curated = [
            StoryParams(place="nursery", event="tune", object="bell", name="Mina", gender="girl", parent="mother", trait="curious"),
            StoryParams(place="garden", event="mend", object="kite", name="Poppy", gender="girl", parent="father", trait="sprightly"),
            StoryParams(place="nursery", event="mix", object="apron", name="Nora", gender="girl", parent="mother", trait="gentle"),
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
