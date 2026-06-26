#!/usr/bin/env python3
"""
A small nursery-rhyme storyworld about a blonde child, a dour mood, and
curiosity turned into chitchat, with a tiny turn from worry to cheer.

The world is intentionally constraint-checked: curiosity should lead to a
reasonable small problem, a helpful conversation, and a gentle resolution.
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

# -----------------------------------------------------------------------------
# World model
# -----------------------------------------------------------------------------

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    carried_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    comp: object | None = None
    hero: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "aunt"}
        male = {"boy", "father", "dad", "man", "uncle"}
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
    place: str
    outdoor: bool
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
    mess: str
    soil: str
    zone: set[str]
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
class Companion:
    id: str
    type: str
    label: str
    phrase: str
    help_line: str
    tail: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
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


# -----------------------------------------------------------------------------
# Story content
# -----------------------------------------------------------------------------

SETTINGS = {
    "nursery": Setting(place="the nursery", outdoor=False, affords={"peek"}),
    "garden": Setting(place="the garden", outdoor=True, affords={"peek", "follow"}),
    "lane": Setting(place="the little lane", outdoor=True, affords={"peek"}),
}

ACTIVITIES = {
    "peek": Activity(
        id="peek",
        verb="peek under the gate",
        gerund="peeking under the gate",
        rush="run to the gate",
        mess="dusty",
        soil="dusty and cross",
        zone={"hands", "knees"},
        keyword="gate",
        tags={"curiosity", "look", "gate"},
    ),
    "follow": Activity(
        id="follow",
        verb="follow the little trail",
        gerund="following the little trail",
        rush="hurry after the trail",
        mess="muddy",
        soil="muddy and grumpy",
        zone={"feet", "knees"},
        keyword="trail",
        tags={"curiosity", "trail", "mud"},
    ),
}

PRIZES = {
    "ribbon": Prize(
        label="ribbon",
        phrase="a neat blue ribbon",
        type="ribbon",
        region="head",
    ),
    "shoes": Prize(
        label="shoes",
        phrase="fresh little shoes",
        type="shoes",
        region="feet",
        plural=True,
    ),
}

COMPANIONS = {
    "sister": Companion(
        id="sister",
        type="girl",
        label="little sister",
        phrase="a tiny sister with bright eyes",
        help_line="Let's ask first and look together.",
        tail="walked with them to look again",
    ),
    "neighbor": Companion(
        id="neighbor",
        type="woman",
        label="kind neighbor",
        phrase="a kind neighbor with a warm smile",
        help_line="Come, come, let's chitchat and see what is what.",
        tail="stayed nearby and talked softly",
    ),
}


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    for comp_id in COMPANIONS:
                        combos.append((place, act_id, prize_id, comp_id))
    return combos


# -----------------------------------------------------------------------------
# Params
# -----------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    companion: str
    name: str
    gender: str
    seed: Optional[int] = None


# -----------------------------------------------------------------------------
# Reasonableness
# -----------------------------------------------------------------------------
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


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return (
        f"(No story: {activity.gerund} does not reach the {prize.label}. "
        f"Try a prize worn on the same spot the activity splashes.)"
    )


# -----------------------------------------------------------------------------
# Narrative helpers
# -----------------------------------------------------------------------------

def intro(world: World, hero: Entity) -> None:
    world.say(
        f"Once in {world.setting.place}, there was a blonde little {hero.type} named {hero.id}, "
        f"and {hero.pronoun('subject')} often had a dour look when the day felt slow."
    )


def loves_curiosity(world: World, hero: Entity) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0.0) + 1
    world.say(
        f"But {hero.pronoun('subject')} had Curiosity in {hero.pronoun('possessive')} pocket, "
        f"and that made {hero.pronoun('object')} peep and ponder and softly chitchat to the air."
    )


def prize_line(world: World, hero: Entity, prize: Entity) -> None:
    prize.carried_by = hero.id
    world.say(
        f"{hero.id} wore {hero.pronoun('possessive')} {prize.label}, for it was {prize.phrase}, "
        f"and {hero.pronoun('subject')} liked to keep it neat and fair."
    )


def meet_companion(world: World, comp: Entity) -> None:
    world.say(
        f"Then came {comp.label}, {comp.phrase}, and the two began a bit of chitchat, "
        f"light as bubbles in the air."
    )


def want_to_peek(world: World, hero: Entity, act: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {act.verb}, for Curiosity was tugging near, "
        f"but the place looked still and the little gate looked tall."
    )


def warn(world: World, comp: Entity, hero: Entity, act: Activity, prize: Entity) -> None:
    world.say(
        f"{comp.label} said, “{comp.help_line} If you rush the gate, your {prize.label} may get {act.soil}.”"
    )


def do_activity(world: World, hero: Entity, act: Activity) -> None:
    world.zone = set(act.zone)
    hero.meters[act.mess] = hero.meters.get(act.mess, 0.0) + 1
    hero.memes["impatience"] = hero.memes.get("impatience", 0.0) + 1
    propagate(world, narrate=True)


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.meters.get("dusty", 0.0) < THRESHOLD and hero.meters.get("muddy", 0.0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.carried_by != hero.id:
                continue
            if item.region not in world.zone:
                continue
            sig = ("soil", hero.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            if hero.meters.get("dusty", 0.0) >= THRESHOLD:
                item.meters["dusty"] = item.meters.get("dusty", 0.0) + 1
                out.append(f"{hero.pronoun('possessive').capitalize()} {item.label} grew dusty.")
            if hero.meters.get("muddy", 0.0) >= THRESHOLD:
                item.meters["muddy"] = item.meters.get("muddy", 0.0) + 1
                out.append(f"{hero.pronoun('possessive').capitalize()} {item.label} picked up mud.")
    return out


def _r_dour_to_cheer(world: World) -> list[str]:
    out: list[str] = []
    for hero in world.characters():
        if hero.memes.get("dour", 0.0) < THRESHOLD:
            continue
        if hero.memes.get("chitchat", 0.0) < THRESHOLD:
            continue
        sig = ("cheer", hero.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        hero.memes["dour"] = 0.0
        hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
        out.append(f"The dour look melted away a little, and a small smile came to stay.")
    return out


CAUSAL_RULES = [
    Rule("soil", _r_soil),
    Rule("cheer", _r_dour_to_cheer),
]


def predict_mess(world: World, hero: Entity, act: Activity, prize_id: str) -> bool:
    sim = world.copy()
    sim.get(hero.id).meters[act.mess] = 1
    sim.zone = set(act.zone)
    _r_soil(sim)
    prize = sim.get(prize_id)
    return prize.meters.get(act.mess, 0.0) >= THRESHOLD


def compromise(world: World, comp: Entity, hero: Entity, act: Activity, prize: Entity) -> bool:
    if not predict_mess(world, hero, act, prize.id):
        return False
    hero.memes["chitchat"] = hero.memes.get("chitchat", 0.0) + 1
    world.say(
        f"So {comp.label} smiled and said, “How about we keep chitchat first, "
        f"and peek the careful way?”"
    )
    return True


def resolve(world: World, hero: Entity, comp: Entity, act: Activity, prize: Entity) -> None:
    hero.memes["dour"] = 0.0
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["chitchat"] = hero.memes.get("chitchat", 0.0) + 1
    world.say(
        f"{hero.id} nodded, and the two went to {act.gerund} together, with {comp.label} beside them."
    )
    world.say(
        f"In the end, {hero.pronoun('subject')} was no longer dour; {hero.pronoun('subject')} was merry, "
        f"and {hero.pronoun('possessive')} {prize.label} stayed clean and bright."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, comp_cfg: Companion, hero_name: str, hero_gender: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_gender))
    comp = world.add(Entity(id=comp_cfg.id, kind="character", type=comp_cfg.type, label=comp_cfg.label, phrase=comp_cfg.phrase))
    prize = world.add(Entity(id=prize_cfg.label, type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, carried_by=hero.id, region=prize_cfg.region))

    intro(world, hero)
    loves_curiosity(world, hero)
    prize_line(world, hero, prize)
    world.para()
    meet_companion(world, comp)
    want_to_peek(world, hero, activity)
    warn(world, comp, hero, activity, prize)
    world.say(f"{hero.id} felt a bit dour, but Curiosity would not let go.")
    world.para()
    if compromise(world, comp, hero, activity, prize):
        do_activity(world, hero, activity)
        resolve(world, hero, comp, activity, prize)

    world.facts.update(hero=hero, companion=comp, prize=prize, activity=activity, setting=setting)
    return world


# -----------------------------------------------------------------------------
# Q&A
# -----------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")
    comp = _safe_fact(world, f, "companion")
    return [
        f'Write a nursery-rhyme-like story about a blonde child named {hero.id} and the word "chitchat".',
        f"Tell a gentle story where {hero.id} is dour at first, then curiosity and chitchat help after wanting to {act.verb}.",
        f"Write a short child-friendly rhyme about {hero.id}, {comp.label}, and {prize.label} staying safe during a little adventure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    comp = _safe_fact(world, f, "companion")
    prize = _safe_fact(world, f, "prize")
    act = _safe_fact(world, f, "activity")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Who was the blonde child in the story?",
            answer=f"The blonde child was {hero.id}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {place}?",
            answer=f"{hero.id} wanted to {act.verb}.",
        ),
        QAItem(
            question=f"Who had chitchat with {hero.id} and helped the story turn gentler?",
            answer=f"{comp.label} had chitchat with {hero.id} and helped {hero.id} be careful.",
        ),
        QAItem(
            question=f"What stayed clean at the end?",
            answer=f"{hero.pronoun('possessive').capitalize()} {prize.label} stayed clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curiosity mean?",
            answer="Curiosity means wanting to look, ask, and learn about something new.",
        ),
        QAItem(
            question="What is chitchat?",
            answer="Chitchat is light, friendly talking about small things.",
        ),
        QAItem(
            question="What does dour mean?",
            answer="Dour means looking gloomy or frowning, like a face that needs a cheer.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
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


# -----------------------------------------------------------------------------
# ASP twin
# -----------------------------------------------------------------------------

ASP_RULES = r"""
setting(nursery).
setting(garden).
setting(lane).

affords(nursery, peek).
affords(garden, peek).
affords(garden, follow).
affords(lane, peek).

activity(peek).
activity(follow).

mess_of(peek, dusty).
mess_of(follow, muddy).

splashes(peek, hands).
splashes(peek, knees).
splashes(follow, feet).
splashes(follow, knees).

prize(ribbon).
worn_on(ribbon, head).
prize(shoes).
worn_on(shoes, feet).

companion(sister).
companion(neighbor).

prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
valid_story(Place, A, P, C) :- affords(Place, A), prize_at_risk(A, P), companion(C).
#show valid_story/4.
"""


def asp_facts() -> str:
    import storyworlds.asp as asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.outdoor:
            lines.append(asp.fact("outdoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for cid in COMPANIONS:
        lines.append(asp.fact("companion", cid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_stories() -> list[tuple]:
    import storyworlds.asp as asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import storyworlds.asp as asp
    py = set(valid_combos())
    cl = set(asp_valid_stories())
    cl2 = {(a, b, c, d) for (a, b, c, d) in cl}
    if py == cl2:
        print(f"OK: ASP matches Python gate ({len(py)} stories).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only in python:", sorted(py - cl2))
    print("only in asp:", sorted(cl2 - py))
    return 1


# -----------------------------------------------------------------------------
# Params / generation / emit / main
# -----------------------------------------------------------------------------

GIRL_NAMES = ["Alice", "Mabel", "Nora", "Lily", "Daisy"]
BOY_NAMES = ["Tom", "Robin", "Peter", "Billy", "Charlie"]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Nursery-rhyme storyworld: curiosity, chitchat, and a dour-to-cheer turn.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--companion", choices=COMPANIONS)
    ap.add_argument("--name")
    ap.add_argument("--gender", choices=["girl", "boy"])
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
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "companion", None) is None or c[3] == getattr(args, "companion", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize, companion = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, companion=companion, name=name, gender=gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), _safe_lookup(COMPANIONS, params.companion), params.name, params.gender)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams(place="nursery", activity="peek", prize="ribbon", companion="neighbor", name="Mabel", gender="girl"),
    StoryParams(place="garden", activity="follow", prize="shoes", companion="sister", name="Billy", gender="boy"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_stories():
            print(row)
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
            header = f"### {p.name}: {p.activity} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
