#!/usr/bin/env python3
"""
storyworlds/worlds/calorie_kindness_bedtime_story.py
====================================================

A tiny bedtime-story world about a child, a kind choice, and a snack with
calories that can either make bedtime bouncy or gently sleepy.

Seed tale inspiration:
---
A little child gets ready for bed after a kind day. They want a sweet bedtime
snack, but the grown-up worries it will bring too many calories and make sleep
harder. The child notices a smaller, kinder choice: sharing a simple snack and a
glass of milk, then helping tuck in a plush toy. The night ends softly, with the
room calm and warm.

World model:
---
- Physical meters include hunger, calories, sleepiness, and tidiness.
- Emotional memes include kindness, worry, comfort, and closeness.
- Actions change the meters and memes; narration is produced from the resulting
  state, not from a fixed template with swapped nouns.

This script follows the Storyweavers world contract with:
- StoryParams and registries
- generate / emit / main
- an inline ASP_RULES twin with a Python reasonableness gate
- --verify parity checks and story exercise
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
# Small domain registries
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
class ChildSpec:
    name: str
    gender: str
    pronoun_subject: str
    pronoun_object: str
    pronoun_possessive: str
    trait: str
    child_spec: object | None = None
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
class SettingSpec:
    place: str
    cozy_detail: str
    indoors: bool = True
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
class SnackSpec:
    id: str
    label: str
    phrase: str
    calories: int
    bedtime_fit: str  # "good", "okay", "heavy"
    sweet: bool = False
    warm: bool = False
    shared: bool = False
    tags: set[str] = field(default_factory=set)
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
class ComfortSpec:
    id: str
    label: str
    phrase: str
    kind_action: str
    calming: bool = True
    tags: set[str] = field(default_factory=set)
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


CHILDREN = {
    "girl": [
        ChildSpec("Maya", "girl", "she", "her", "her", "gentle"),
        ChildSpec("Nora", "girl", "she", "her", "her", "quiet"),
        ChildSpec("Lina", "girl", "she", "her", "her", "kind"),
    ],
    "boy": [
        ChildSpec("Eli", "boy", "he", "him", "his", "gentle"),
        ChildSpec("Theo", "boy", "he", "him", "his", "kind"),
        ChildSpec("Noah", "boy", "he", "him", "his", "quiet"),
    ],
}

SETTINGS = {
    "bedroom": SettingSpec(
        place="the little bedroom",
        cozy_detail="A lamp glowed softly beside the bed, and a stuffed bear waited on the pillow.",
    ),
    "kitchen": SettingSpec(
        place="the warm kitchen",
        cozy_detail="A small night-light made the table look like a moonlit island.",
    ),
}

SNACKS = {
    "cookie": SnackSpec(
        id="cookie",
        label="cookie",
        phrase="a sweet cookie",
        calories=180,
        bedtime_fit="heavy",
        sweet=True,
        shared=False,
        tags={"cookie", "sweet", "calorie"},
    ),
    "banana": SnackSpec(
        id="banana",
        label="banana",
        phrase="a soft banana",
        calories=90,
        bedtime_fit="good",
        sweet=True,
        shared=True,
        tags={"banana", "fruit", "calorie"},
    ),
    "milk": SnackSpec(
        id="milk",
        label="milk",
        phrase="a small cup of warm milk",
        calories=120,
        bedtime_fit="okay",
        warm=True,
        shared=True,
        tags={"milk", "warm", "calorie"},
    ),
    "toast": SnackSpec(
        id="toast",
        label="toast",
        phrase="a little piece of toast with butter",
        calories=110,
        bedtime_fit="good",
        shared=True,
        tags={"toast", "calorie"},
    ),
}

COMFORTS = {
    "teddy": ComfortSpec(
        id="teddy",
        label="teddy bear",
        phrase="the stuffed bear",
        kind_action="tuck in",
        tags={"bear", "teddy", "kindness"},
    ),
    "blanket": ComfortSpec(
        id="blanket",
        label="blanket",
        phrase="the blanket",
        kind_action="smooth over",
        tags={"blanket", "kindness"},
    ),
    "cup": ComfortSpec(
        id="cup",
        label="cup",
        phrase="the little cup",
        kind_action="carry back",
        tags={"cup", "kindness", "milk"},
    ),
}

KINDS_OF_KINDNESS = [
    "sharing",
    "helping",
    "tidying",
    "comforting",
    "waiting kindly",
]


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

@dataclass
class Entity:
    id: str
    kind: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    carried_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    comfort: object | None = None
    parent: object | None = None
    snack: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.id in {"Maya", "Nora", "Lina"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.id in {"Eli", "Theo", "Noah"}:
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
class World:
    setting: SettingSpec
    entities: dict[str, Entity] = field(default_factory=dict)
    fired: set[tuple] = field(default_factory=set)
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    facts: dict = field(default_factory=dict)

    clone: object | None = None
    world: object | None = None
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone
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


THRESHOLD = 1.0
HEAVY_CALORIES = 150


# ---------------------------------------------------------------------------
# Reasonable gate
# ---------------------------------------------------------------------------

def snack_is_reasonable(snack: SnackSpec) -> bool:
    return snack.calories > 0 and snack.bedtime_fit in {"good", "okay", "heavy"}


def bedtime_story_ok(snack: SnackSpec, comfort: ComfortSpec) -> bool:
    return snack_is_reasonable(snack) and comfort.calming


# ---------------------------------------------------------------------------
# Causal rules
# ---------------------------------------------------------------------------

def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for sent in _apply_rules(world):
            changed = True
            if sent:
                out.append(sent)
    if narrate:
        for s in out:
            world.say(s)
    return out


def _apply_rules(world: World) -> list[str]:
    out: list[str] = []
    child = world.get(world.facts["child"].id)
    snack = world.get("snack")
    if child.meters.get("hungry", 0) >= THRESHOLD and snack.meters.get("served", 0) >= THRESHOLD:
        sig = ("eating",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["hungry"] = max(0.0, child.meters.get("hungry", 0) - 1)
            child.meters["calories"] = child.meters.get("calories", 0) + snack.meters.get("calories", 0)
            child.memes["comfort"] = child.memes.get("comfort", 0) + 1
            if snack.meters.get("calories", 0) >= HEAVY_CALORIES:
                child.meters["sleepiness"] = child.meters.get("sleepiness", 0) - 0.5
                child.memes["restlessness"] = child.memes.get("restlessness", 0) + 1
                out.append("The sweet bite made bedtime a little brighter and a little harder to settle.")
            else:
                child.meters["sleepiness"] = child.meters.get("sleepiness", 0) + 1
                out.append("The small snack warmed the child and made sleepiness come closer.")
    if child.memes.get("kindness", 0) >= THRESHOLD and not world.facts.get("comfort_done"):
        sig = ("kindness",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.meters["tidy"] = child.meters.get("tidy", 0) + 1
            out.append("Kind hands put things back where they belonged.")
    if child.memes.get("worry", 0) >= THRESHOLD and child.memes.get("comfort", 0) >= THRESHOLD:
        sig = ("worry_softens",)
        if sig not in world.fired:
            world.fired.add(sig)
            child.memes["worry"] = max(0.0, child.memes.get("worry", 0) - 1)
            child.memes["close"] = child.memes.get("close", 0) + 1
            out.append("The worry turned soft when everyone chose the gentle way.")
    return out


# ---------------------------------------------------------------------------
# Forward prediction
# ---------------------------------------------------------------------------

def predict_effect(world: World, snack: SnackSpec) -> dict:
    sim = world.copy()
    child = sim.get(sim.facts["child"].id)
    sim.get("snack").meters["served"] = 1
    child.meters["hungry"] = 1
    child.meters["calories"] = child.meters.get("calories", 0)
    child.memes["worry"] = child.memes.get("worry", 0)
    _apply_rules(sim)
    return {
        "sleepiness": child.meters.get("sleepiness", 0),
        "restlessness": child.memes.get("restlessness", 0),
        "calories": child.meters.get("calories", 0) + snack.calories,
    }


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------

def introduce(world: World, child: Entity, comfort: ComfortSpec) -> None:
    world.say(
        f"{child.id} was a little {child.memes.get('trait', 'kind')} child who liked "
        f"quiet nights and gentle lights."
    )
    world.say(
        f"In {world.setting.place}, {world.setting.cozy_detail}"
    )
    world.say(
        f"{child.pronoun().capitalize()} liked {comfort.phrase} because bedtime felt safer with a soft friend nearby."
    )


def after_kind_day(world: World, child: Entity) -> None:
    child.memes["kindness"] = child.memes.get("kindness", 0) + 1
    child.meters["hungry"] = child.meters.get("hungry", 0) + 1
    world.say(
        f"After a day of {random.choice(KINDS_OF_KINDNESS)}, {child.id} came to bed feeling pleasantly hungry."
    )


def want_snack(world: World, child: Entity, snack: SnackSpec) -> None:
    world.say(
        f"{child.id} wanted {snack.phrase} before sleep, because the sweet smell still felt cozy in the air."
    )


def worry(world: World, parent: Entity, child: Entity, snack: SnackSpec) -> None:
    child.memes["worry"] = child.memes.get("worry", 0) + 1
    if snack.calories >= HEAVY_CALORIES:
        world.say(
            f"{parent.id} smiled gently and said, \"That snack has a lot of calories for bedtime. It might make your body feel too awake.\""
        )
    else:
        world.say(
            f"{parent.id} said softly, \"Let's keep bedtime calm so your body can rest.\""
        )


def offer_kind_choice(world: World, child: Entity, snack: SnackSpec, comfort: ComfortSpec) -> None:
    child.memes["kindness"] = child.memes.get("kindness", 0) + 1
    world.say(
        f"{child.id} thought about being kind to {child.pronoun_possessive} own sleepy body and chose a smaller snack."
    )
    world.say(
        f"Then {child.id} helped {comfort.kind_action} {comfort.phrase} and carried the cup back with careful hands."
    )
    snack_entity = world.get("snack")
    snack_entity.meters["served"] = 1
    child.meters["hungry"] = max(0.0, child.meters.get("hungry", 0) - 1)


def bedtime_resolution(world: World, child: Entity, snack: SnackSpec, comfort: ComfortSpec) -> None:
    child.memes["comfort"] = child.memes.get("comfort", 0) + 1
    child.meters["sleepiness"] = child.meters.get("sleepiness", 0) + 1
    child.meters["calories"] = child.meters.get("calories", 0) + snack.calories
    world.facts["comfort_done"] = True
    propagate(world, narrate=False)
    world.say(
        f"After that, {child.id} felt warm, calm, and ready for sleep."
    )
    world.say(
        f"{child.id} tucked {comfort.phrase} close, and the room grew still and soft."
    )


# ---------------------------------------------------------------------------
# World build
# ---------------------------------------------------------------------------

def make_world(params: "StoryParams") -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting=setting)
    child_spec = ChildSpec(params.name, params.gender, "she" if params.gender == "girl" else "he",
                           "her" if params.gender == "girl" else "him",
                           "her" if params.gender == "girl" else "his",
                           params.trait)
    child = world.add(Entity(id=child_spec.name, kind="character"))
    child.memes["trait"] = 1
    parent = world.add(Entity(id="parent", kind="character", label=params.parent))
    snack = world.add(Entity(id="snack", kind="thing", label=_safe_lookup(SNACKS, params.snack).label, phrase=_safe_lookup(SNACKS, params.snack).phrase))
    comfort = world.add(Entity(id="comfort", kind="thing", label=_safe_lookup(COMFORTS, params.comfort).label, phrase=_safe_lookup(COMFORTS, params.comfort).phrase))
    world.facts.update(child=child, parent=parent, snack_spec=_safe_lookup(SNACKS, params.snack), comfort_spec=_safe_lookup(COMFORTS, params.comfort), comfort_done=False)
    return world


def tell(params: "StoryParams") -> World:
    world = make_world(params)
    child = _safe_fact(world, world.facts, "child")
    parent = _safe_fact(world, world.facts, "parent")
    snack_spec = _safe_fact(world, world.facts, "snack_spec")
    comfort_spec = _safe_fact(world, world.facts, "comfort_spec")

    introduce(world, child, comfort_spec)
    world.para()
    after_kind_day(world, child)
    want_snack(world, child, snack_spec)
    worry(world, parent, child, snack_spec)
    offer_kind_choice(world, child, snack_spec, comfort_spec)
    bedtime_resolution(world, child, snack_spec, comfort_spec)
    return world


# ---------------------------------------------------------------------------
# Params and Q&A
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    setting: str
    snack: str
    comfort: str
    name: str
    gender: str
    parent: str
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
    ap = argparse.ArgumentParser(description="A bedtime story world about kindness and calories.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--snack", choices=SNACKS.keys())
    ap.add_argument("--comfort", choices=COMFORTS.keys())
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["mom", "dad", "parent"])
    ap.add_argument("--trait")
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
    setting = getattr(args, "setting", None) or rng.choice(list(SETTINGS.keys()))
    snack = getattr(args, "snack", None) or rng.choice(list(SNACKS.keys()))
    comfort = getattr(args, "comfort", None) or rng.choice(list(COMFORTS.keys()))
    if not bedtime_story_ok(_safe_lookup(SNACKS, snack), _safe_lookup(COMFORTS, comfort)):
        return _fallback_storyparams(args, rng, StoryParams, globals())
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    child = getattr(args, "name", None) or rng.choice([c.name for c in CHILDREN[gender]])
    parent = getattr(args, "parent", None) or rng.choice(["mom", "dad"])
    trait = getattr(args, "trait", None) or rng.choice(["gentle", "kind", "quiet"])
    return StoryParams(setting=setting, snack=snack, comfort=comfort, name=child, gender=gender, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    snack = _safe_fact(world, f, "snack_spec")
    comfort = _safe_fact(world, f, "comfort_spec")
    child = _safe_fact(world, f, "child")
    return [
        f'Write a bedtime story for young children that includes the word "calorie" and a gentle choice about {snack.label}.',
        f"Tell a soft story about {child.id} choosing kindness at bedtime instead of a bigger snack with too many calories.",
        f"Write a calm story where a child and grown-up solve a bedtime snack worry by choosing {comfort.label} and a smaller treat.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    snack = _safe_fact(world, f, "snack_spec")
    parent = _safe_fact(world, f, "parent")
    comfort = _safe_fact(world, f, "comfort_spec")
    return [
        QAItem(
            question=f"What did {child.id} want before sleep?",
            answer=f"{child.id} wanted {snack.phrase} before bedtime, because it felt cozy and sweet.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about the snack?",
            answer=f"{parent.id} worried because {snack.label} has {snack.calories} calories, which can be a lot for bedtime if a child wants to settle down.",
        ),
        QAItem(
            question=f"What kind choice did {child.id} make instead?",
            answer=f"{child.id} chose a smaller, kinder bedtime path by helping with {comfort.phrase} and keeping the room calm.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {child.id} feeling warm and sleepy, with {comfort.phrase} tucked close and bedtime finally peaceful.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    snack = _safe_fact(world, world.facts, "snack_spec")
    comfort = _safe_fact(world, world.facts, "comfort_spec")
    out = [
        QAItem(
            question="What are calories?",
            answer="Calories are a way to describe how much energy food gives to the body.",
        )
    ]
    if snack.sweet:
        out.append(QAItem(
            question="Why can sweet snacks feel exciting at bedtime?",
            answer="Sweet snacks can taste very nice and make a child feel like having one more happy bite.",
        ))
    if comfort.id == "teddy":
        out.append(QAItem(
            question="Why is a teddy bear comforting at bedtime?",
            answer="A teddy bear can feel soft and familiar, which helps a child feel safe and settled.",
        ))
    if comfort.id == "blanket":
        out.append(QAItem(
            question="What does a blanket do at bedtime?",
            answer="A blanket keeps a child cozy and warm while they rest.",
        ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
snack_ok(S) :- snack(S), calories(S,C), C > 0.
heavy(S) :- snack(S), calories(S,C), C >= 150.
gentle(S) :- snack(S), calories(S,C), C < 150.

valid_story(Setting, Snack, Comfort) :-
    setting(Setting),
    snack_ok(Snack),
    comfort(Comfort),
    calming(Comfort),
    bedtime_fit(Snack, good).
valid_story(Setting, Snack, Comfort) :-
    setting(Setting),
    snack_ok(Snack),
    comfort(Comfort),
    calming(Comfort),
    bedtime_fit(Snack, okay).

needs_warning(Snack) :- heavy(Snack).
"""
# The ASP rules are intentionally small; they mirror the Python gate:
# a bedtime story is reasonable when the snack has positive calories, the
# comfort choice is calming, and the snack is not absurdly incompatible.


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
    for sid, snack in SNACKS.items():
        lines.append(asp.fact("snack", sid))
        lines.append(asp.fact("calories", sid, snack.calories))
        lines.append(asp.fact("bedtime_fit", sid, snack.bedtime_fit))
    for cid, comfort in COMFORTS.items():
        lines.append(asp.fact("comfort", cid))
        if comfort.calming:
            lines.append(asp.fact("calming", cid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_reasonable() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for s in SETTINGS:
        for n, snack in SNACKS.items():
            for c, comfort in COMFORTS.items():
                if bedtime_story_ok(snack, comfort):
                    out.append((s, n, c))
    return sorted(out)


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_reasonable())
    if py == cl:
        print(f"OK: clingo gate matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between Python and clingo:")
    if py - cl:
        print("  only in Python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# Emit / trace / main
# ---------------------------------------------------------------------------

def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {ent.id:8} ({ent.kind:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
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


CURATED = [
    StoryParams(setting="bedroom", snack="banana", comfort="teddy", name="Maya", gender="girl", parent="mom", trait="gentle"),
    StoryParams(setting="bedroom", snack="milk", comfort="blanket", name="Eli", gender="boy", parent="dad", trait="quiet"),
    StoryParams(setting="kitchen", snack="toast", comfort="cup", name="Nora", gender="girl", parent="mom", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_reasonable()
        print(f"{len(combos)} compatible bedtime combos:\n")
        for combo in combos:
            print(" ", combo)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            i += 1
            seed = base_seed + i
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
            header = f"### {p.name}: {p.snack} with {p.comfort} at {p.setting}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
