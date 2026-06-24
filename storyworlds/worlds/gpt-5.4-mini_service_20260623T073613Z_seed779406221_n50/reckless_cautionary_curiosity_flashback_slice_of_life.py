#!/usr/bin/env python3
"""
storyworlds/worlds/reckless_cautionary_curiosity_flashback_slice_of_life.py
===========================================================================

A small slice-of-life storyworld about a curious child, a reckless choice, a
cautionary warning, a flashback to a previous wobble, and a safer ending.

Premise:
- A child notices something interesting on a high shelf.
- Curiosity pushes them toward a reckless way to reach it.
- A caregiver remembers a past mishap and warns them.
- The child remembers the wobble too.
- They choose a safer helper item and the moment ends peacefully.

The domain is intentionally small: one household scene, one tempting object, one
possible risky method, and one safer method. Every story is built from world
state, not from a frozen paragraph with swapped names.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field, asdict
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    height: str = ""
    stable: bool = True
    helpful: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    caregiver: object | None = None
    child: object | None = None
    helper_ent: object | None = None
    jar: object | None = None
    shelf: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "they", "object": "them", "possessive": "their"}[case]

    @property
    def label_word(self) -> str:
        return {"mother": "mom", "father": "dad"}.get(self.type, self.type)
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
class Setting:
    place: str
    mood: str
    affords: set[str] = field(default_factory=set)
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


@dataclass
class Temptation:
    id: str
    label: str
    phrase: str
    verb: str
    reason: str
    danger: str
    zone: str
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
class Helper:
    id: str
    label: str
    phrase: str
    use: str
    stable: bool = True
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
    def __init__(self, setting: Setting) -> None:
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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


@dataclass
class Rule:
    name: str
    apply: Callable[[World], list[str]]
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


def _r_wobble(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    shelf = world.get("shelf")
    if child.meters["climb"] >= THRESHOLD and not shelf.stable:
        sig = ("wobble",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        child.meters["wobble"] += 1
        child.memes["startle"] += 1
        out.append("The chair wobbled under the child's weight.")
    return out


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    child = world.get("child")
    jar = world.get("jar")
    if child.meters["reach"] >= THRESHOLD and child.meters["wobble"] >= THRESHOLD:
        sig = ("spill",)
        if sig in world.fired:
            return []
        world.fired.add(sig)
        jar.meters["spilled"] += 1
        jar.meters["mess"] += 1
        out.append("The jar tipped and the little pieces spilled across the floor.")
    return out


CAUSAL_RULES = [Rule("wobble", _r_wobble), Rule("spill", _r_spill)]


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


def predict_mess(world: World) -> bool:
    sim = world.copy()
    child = sim.get("child")
    child.meters["climb"] += 1
    child.meters["reach"] += 1
    propagate(sim, narrate=False)
    return sim.get("jar").meters["mess"] >= THRESHOLD


def valid_pair(temptation: Temptation, helper: Helper) -> bool:
    return temptation.zone in helper.tags and helper.stable


def choose_helper(temptation: Temptation) -> Optional[Helper]:
    for h in HELPERS.values():
        if valid_pair(temptation, h):
            return h
    return None


def setup(world: World, child: Entity, caregiver: Entity, temptation: Temptation, jar: Entity) -> None:
    child.memes["curiosity"] += 1
    child.memes["reckless"] += 1
    world.say(
        f"{child.id} was a lively child who noticed every small thing in {world.setting.place}."
    )
    world.say(
        f"{child.pronoun().capitalize()} loved the quiet rhythm of the day, and today "
        f"{temptation.label} seemed especially interesting."
    )
    world.say(
        f"On the shelf sat {jar.phrase}, and {jar.label} looked just far enough away to be tempting."
    )
    caregiver.memes["care"] += 1


def flashback(world: World, child: Entity, caregiver: Entity) -> None:
    child.memes["remember"] += 1
    caregiver.memes["remember"] += 1
    world.say(
        f"{caregiver.id} paused and looked at the chair. That brought back a flashback "
        f"of the last time it had rocked side to side."
    )
    world.say(
        f"{child.id} remembered it too: a tiny wobble, a held breath, and a quick step back."
    )


def warn(world: World, caregiver: Entity, child: Entity, temptation: Temptation, jar: Entity) -> None:
    if predict_mess(world):
        world.say(
            f'"If you climb like that," {caregiver.id} said, "you might make {jar.label} spill."'
        )
        world.say(
            f'"Let’s not be reckless. We can reach {jar.label} another way," {caregiver.id} added.'
        )


def try_risky(world: World, child: Entity, temptation: Temptation) -> None:
    child.meters["climb"] += 1
    child.meters["reach"] += 1
    child.memes["reckless"] += 1
    world.say(
        f"{child.id} still wanted to {temptation.verb}, so {child.pronoun()} dragged over the chair."
    )
    world.say(
        f"{child.pronoun().capitalize()} stretched up with a too-brave grin, trying to act like the height was no big deal."
    )
    propagate(world, narrate=True)


def choose_safely(world: World, caregiver: Entity, child: Entity, helper: Helper, jar: Entity, temptation: Temptation) -> None:
    child.memes["curiosity"] += 1
    child.memes["calm"] += 1
    child.memes["reckless"] = 0
    world.say(
        f"Then {caregiver.id} brought over {helper.phrase}, and {child.id} changed plans."
    )
    world.say(
        f"Together they used {helper.label} to {helper.use}, and {jar.label} stayed safely on the shelf."
    )
    world.say(
        f"{child.id} smiled at the tidy room and the easy answer, pleased that curiosity could wait for a safer moment."
    )


def tell(setting: Setting, temptation: Temptation, helper: Helper, name: str, gender: str, caregiver_type: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, label=name, stable=True))
    caregiver = world.add(Entity(id="Caregiver", kind="character", type=caregiver_type, label="the caregiver"))
    shelf = world.add(Entity(id="shelf", type="thing", label="the chair", stable=False))
    jar = world.add(Entity(
        id="jar",
        type="thing",
        label=temptation.label,
        phrase=temptation.phrase,
        caretaker=caregiver.id,
        stable=True,
    ))
    helper_ent = world.add(Entity(id=helper.id, type="thing", label=helper.label, phrase=helper.phrase, helpful=True, stable=True))

    setup(world, child, caregiver, temptation, jar)
    world.para()
    flashback(world, child, caregiver)
    warn(world, caregiver, child, temptation, jar)
    world.para()
    try_risky(world, child, temptation)
    world.para()
    choose_safely(world, caregiver, child, helper, jar, temptation)

    world.facts.update(
        child=child,
        caregiver=caregiver,
        shelf=shelf,
        jar=jar,
        helper=helper_ent,
        temptation=temptation,
        safe=helper,
        predicted_spill=predict_mess(world),
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", mood="quiet morning", affords={"reach"}),
    "living_room": Setting(place="the living room", mood="slow afternoon", affords={"reach"}),
    "hallway": Setting(place="the hallway", mood="rainy pause", affords={"reach"}),
}

TEMPTATIONS = {
    "cookies": Temptation(
        id="cookies",
        label="the cookie jar",
        phrase="a glass cookie jar",
        verb="reach the cookie jar",
        reason="cookies smell sweet",
        danger="the jar could spill",
        zone="reach",
        tags={"reach", "glass", "spill", "curiosity"},
    ),
    "stickers": Temptation(
        id="stickers",
        label="the sticker tin",
        phrase="a bright sticker tin",
        verb="open the sticker tin",
        reason="new stickers are fun",
        danger="the chair could wobble",
        zone="reach",
        tags={"reach", "tin", "spill", "curiosity"},
    ),
    "marbles": Temptation(
        id="marbles",
        label="the marble bowl",
        phrase="a little bowl of marbles",
        verb="peek at the marble bowl",
        reason="the marbles shine like beads",
        danger="the bowl could tip",
        zone="reach",
        tags={"reach", "bowl", "spill", "curiosity"},
    ),
}

HELPERS = {
    "step_stool": Helper(
        id="step_stool",
        label="the step stool",
        phrase="a sturdy step stool",
        use="reach the shelf without wobbling",
        tags={"reach"},
    ),
    "broom": Helper(
        id="broom",
        label="the broom",
        phrase="a broom with a long handle",
        use="pull the jar closer without climbing",
        tags={"reach"},
    ),
    "asking": Helper(
        id="asking",
        label="a helping hand",
        phrase="a helping hand from the caregiver",
        use="take the jar down safely",
        tags={"reach"},
    ),
}

GIRL_NAMES = ["Mina", "Ada", "Lia", "Nora", "Iris", "June"]
BOY_NAMES = ["Owen", "Theo", "Milo", "Eli", "Noah", "Finn"]
TRAITS = ["curious", "gentle", "thoughtful", "restless", "careful"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for s in SETTINGS:
        for t in TEMPTATIONS:
            for h in HELPERS:
                if valid_pair(_safe_lookup(TEMPTATIONS, t), _safe_lookup(HELPERS, h)):
                    combos.append((s, t, h))
    return combos


@dataclass
class StoryParams:
    setting: str
    temptation: str
    helper: str
    name: str
    gender: str
    caregiver: str
    trait: str
    seed: Optional[int] = None
    samples: list = field(default_factory=list)
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about curiosity, caution, and a safer way to reach.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--temptation", choices=TEMPTATIONS)
    ap.add_argument("--helper", choices=HELPERS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--caregiver", choices=["mother", "father"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "temptation", None) is None or c[1] == getattr(args, "temptation", None))
              and (getattr(args, "helper", None) is None or c[2] == getattr(args, "helper", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, temptation, helper = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    caregiver = getattr(args, "caregiver", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting, temptation, helper, name, gender, caregiver, trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a gentle slice-of-life story for a 3-to-5-year-old where {f["child"].id} feels curious about {f["temptation"].label} on a shelf, but a caregiver gives a cautionary warning.',
        f"Tell a short story about a child named {f['child'].id} who gets a little reckless, remembers a flashback, and chooses {f['safe'].label} instead.",
        f'Write a small household story that includes curiosity, a flashback, and the word "{f["temptation"].label}".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caregiver = f["caregiver"]
    temp = f["temptation"]
    helper = f["safe"]
    jar = f["jar"]
    return [
        QAItem(
            question=f"What did {child.id} notice in {world.setting.place}?",
            answer=f"{child.id} noticed {jar.phrase} on the shelf. It looked interesting and made {child.id} feel curious.",
        ),
        QAItem(
            question=f"Why did {caregiver.id} warn {child.id} about reaching for {jar.label} the reckless way?",
            answer=f"{caregiver.id} warned {child.id} because the chair was not stable, and {temp.danger}. The warning was careful and kind.",
        ),
        QAItem(
            question=f"What did the flashback help {child.id} remember?",
            answer=f"The flashback reminded {child.id} of the last wobble, so {child.id} remembered to slow down. That memory helped {child.id} choose a safer way.",
        ),
        QAItem(
            question=f"How did {child.id} finally get near {jar.label}?",
            answer=f"{child.id} used {helper.phrase} with {caregiver.id}. That let {child.id} reach safely without a risky climb.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does curious mean?",
            answer="Curious means wanting to know more or wanting to look closely at something interesting.",
        ),
        QAItem(
            question="What does reckless mean?",
            answer="Reckless means doing something without enough care, even when it might be unsafe.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is when the story remembers something that happened before, so the reader can understand why a character feels worried or careful now.",
        ),
    ]


ASP_RULES = r"""
curious(C) :- person(C).
reckless(C) :- curious(C), tempted(T), reaches(C,T), not safe_help(C).
warned(C) :- caregiver(G), child(C), warning(G,C).
flashback(C) :- wobble_memory(C).
safer(C) :- warned(C), flashback(C), safe_help(C).
ending(safe) :- safer(C).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
    for t, temp in TEMPTATIONS.items():
        lines.append(asp.fact("tempted", t))
        lines.append(asp.fact("danger", t, temp.danger))
        lines.append(asp.fact("zone", t, temp.zone))
    for h in HELPERS:
        lines.append(asp.fact("helper", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(TEMPTATIONS, params.temptation), _safe_lookup(HELPERS, params.helper), params.name, params.gender, params.caregiver)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.stable is not None:
            bits.append(f"stable={e.stable}")
        if e.helpful:
            bits.append("helpful=True")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False, header: str = "") -> None:
    if header:
        print(header)
    print(sample.story)
    if trace and sample.world is not None:
        print(dump_trace(sample.world))
    if qa:
        print()
        for section, items in (("Prompts", sample.prompts), ("Story Q&A", sample.story_qa), ("World Q&A", sample.world_qa)):
            print(f"== {section} ==")
            if section == "Prompts":
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")
            print()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    print("only in python:", sorted(py - cl))
    print("only in asp:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(c)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = []
    if getattr(args, "all", None):
        samples = [generate(StoryParams(*c, name="Mina", gender="girl", caregiver="mother", trait="curious")) for c in CURATED]
    else:
        seen = set()
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
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=(f"### variant {i+1}" if len(samples) > 1 else ""))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


CURATED = [
    ("kitchen", "cookies", "step_stool"),
    ("living_room", "stickers", "broom"),
    ("hallway", "marbles", "asking"),
]


if __name__ == "__main__":
    main()
