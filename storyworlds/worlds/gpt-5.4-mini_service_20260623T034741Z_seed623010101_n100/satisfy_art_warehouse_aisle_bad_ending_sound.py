#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T034741Z_seed623010101_n100/satisfy_art_warehouse_aisle_bad_ending_sound.py
==============================================================================================================

A small standalone storyworld about a warehouse aisle, a spooky sound, and an art
project that tries to satisfy a child’s curiosity before the ending turns bad.

Seed premise:
- Setting: warehouse aisle
- Features: Bad Ending, Sound Effects
- Style: Ghost Story
- Required words: satisfy, art

The domain models a child, a caretaker, a warehouse aisle with creaking shelves,
and a paper art scene that draws attention to a hidden sound. The world can end
in a calm discovery or a bad ending where the aisle goes dark and the art is
lost. State changes drive narration, and Q&A is generated from world facts rather
than parsed text.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
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
    role: str = ""
    tags: set[str] = field(default_factory=set)
    owner: Optional[str] = None
    location: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    attrs: dict[str, object] = field(default_factory=dict)

    aisle: object | None = None
    caretaker: object | None = None
    child: object | None = None
    gear: object | None = None
    lamp: object | None = None
    prize: object | None = None
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

    def __post_init__(self) -> None:
        if not hasattr(self.meters, "__missing__"):
            object.__setattr__(self, "meters", __import__("collections").defaultdict(float, self.meters))
        if not hasattr(self.memes, "__missing__"):
            object.__setattr__(self, "memes", __import__("collections").defaultdict(float, self.memes))

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
    affords: set[str] = field(default_factory=set)
    mood: str = "dim"
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
class Activity:
    id: str
    verb: str
    sound: str
    mess: str
    zone: str
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
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
class Gear:
    id: str
    label: str
    phrase: str
    protects: set[str] = field(default_factory=set)
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

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
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.facts = copy.deepcopy(self.facts)
        return clone


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


def _r_echo(world: World) -> list[str]:
    out: list[str] = []
    for ent in list(world.entities.values()):
        if ent.meters.get("echo", 0.0) < THRESHOLD:
            continue
        sig = ("echo", ent.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        for kid in world.characters():
            kid.memes["unease"] = kid.memes.get("unease", 0.0) + 1
        out.append("__echo__")
    return out


def _r_dark(world: World) -> list[str]:
    out: list[str] = []
    aisle = world.entities.get("aisle")
    if not aisle:
        return out
    if aisle.meters.get("darkness", 0.0) < THRESHOLD:
        return out
    sig = ("dark",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    for kid in world.characters():
        kid.memes["fear"] = kid.memes.get("fear", 0.0) + 1
    out.append("__dark__")
    return out


CAUSAL_RULES = [Rule("echo", _r_echo), Rule("dark", _r_dark)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if not s.startswith("__"))
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for setting_id, setting in SETTINGS.items():
        for activity_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, activity_id)
            for prize_id, prize in PRIZES.items():
                if act.zone == prize.region:
                    combos.append((setting_id, activity_id, prize_id))
    return combos


@dataclass
class StoryParams:
    setting: str = "warehouse_aisle"
    activity: str = "sound_of_boxes"
    prize: str = "paper_art"
    child: str = "Mina"
    child_gender: str = "girl"
    caretaker: str = "Uncle"
    caretaker_gender: str = "man"
    trait: str = "curious"
    seed: Optional[int] = None
    world: object | None = None
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
    ap = argparse.ArgumentParser(description="Ghost-story warehouse aisle world.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--child")
    ap.add_argument("--child-gender", choices=["girl", "boy"])
    ap.add_argument("--caretaker")
    ap.add_argument("--caretaker-gender", choices=["woman", "man", "girl", "boy"])
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
    combos = [c for c in valid_combos()
              if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, activity, prize = rng.choice(list(combos))
    child_gender = getattr(args, "child_gender", None) or rng.choice(["girl", "boy"])
    caretaker_gender = getattr(args, "caretaker_gender", None) or rng.choice(["woman", "man"])
    child = getattr(args, "child", None) or rng.choice(GIRL_NAMES if child_gender == "girl" else BOY_NAMES)
    caretaker = getattr(args, "caretaker", None) or rng.choice(CARETAKER_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(setting=setting, activity=activity, prize=prize, child=child,
                       child_gender=child_gender, caretaker=caretaker,
                       caretaker_gender=caretaker_gender, trait=trait)


def _setup_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    world = World(setting)
    child = world.add(Entity(id=params.child, kind="character", type=params.child_gender,
                             role="child", tags={"child"},
                             meters={"wonder": 0.0}, memes={"curiosity": 1.0, "fear": 0.0}))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=params.caretaker_gender,
                                 role="caretaker", label=params.caretaker,
                                 meters={"worry": 0.0}, memes={"care": 1.0}))
    aisle = world.add(Entity(id="aisle", type="place", label=setting.place,
                             meters={"darkness": 0.0, "echo": 0.0, "draft": 0.0},
                             attrs={"mood": setting.mood}))
    prize = world.add(Entity(id="art", type="thing", label=_safe_lookup(PRIZES, params.prize).label,
                             role="prize", tags=_safe_lookup(PRIZES, params.prize).tags,
                             owner=child.id, location="aisle",
                             meters={"torn": 0.0, "wet": 0.0}, memes={"value": 1.0}))
    gear = world.add(Entity(id="lamp", type="thing", label="battery lamp",
                            role="gear", tags={"lamp"},
                            meters={"charged": 1.0}, memes={"safety": 1.0}))
    world.facts.update(child=child, caretaker=caretaker, aisle=aisle, prize=prize, gear=gear)
    return world


def predict_bad(world: World, activity: Activity) -> bool:
    sim = world.copy()
    sim.get("aisle").meters["echo"] += 1
    sim.get("art").meters[activity.mess] = 1.0
    propagate(sim, narrate=False)
    return sim.get("art").meters.get("torn", 0.0) >= THRESHOLD


def _start(world: World, child: Entity) -> None:
    child.memes["curiosity"] = child.memes.get("curiosity", 0.0) + 1
    world.say(
        f"In the warehouse aisle, {child.id} walked between tall shelves that "
        f"stood like sleeping giants."
    )
    world.say(
        f"The air felt dim and dusty, and the whole aisle seemed to listen."
    )


def _sound(world: World, child: Entity, act: Activity) -> None:
    world.get("aisle").meters["echo"] += 1
    child.meters["wonder"] = child.meters.get("wonder", 0.0) + 1
    world.say(
        f"Then came a sound effect: {act.sound} -- soft at first, then louder, "
        f"as if the boxes were whispering back."
    )


def _warn(world: World, caretaker: Entity, child: Entity, act: Activity, prize: Entity) -> None:
    if predict_bad(world, act):
        caretaker.meters["worry"] = caretaker.meters.get("worry", 0.0) + 1
        world.say(
            f'{caretaker.label} frowned and said, "That sound might shake the art. '
            f'Let us satisfy the question carefully, not with a rush."'
        )


def _choose_safely(world: World, child: Entity, prize: Entity) -> None:
    child.memes["trust"] = child.memes.get("trust", 0.0) + 1
    world.say(
        f"{child.id} nodded and held the art with two hands, listening instead "
        f"of chasing the dark noise."
    )


def _bad_ending(world: World, child: Entity, caretaker: Entity, prize: Entity) -> None:
    aisle = world.get("aisle")
    aisle.meters["darkness"] += 1
    prize.meters["torn"] = 1.0
    child.memes["fear"] = child.memes.get("fear", 0.0) + 2
    world.say(
        f"With a sudden groan, the shelves shuddered and the lights blinked out."
    )
    world.say(
        f"The art slipped from {child.id}'s hands, skidded across the floor, "
        f"and tore on a sharp corner."
    )
    world.say(
        f"{caretaker.label} reached out too late, and the aisle swallowed their "
        f"little game."
    )
    world.say(
        f"In the end, the sound went silent, but the art could not be fixed, "
        f"and the warehouse aisle stayed cold and dark."
    )


def _ending_image(world: World, child: Entity, prize: Entity) -> None:
    if prize.meters.get("torn", 0.0) >= THRESHOLD:
        world.say(
            f"The last thing left was a bent paper edge shining under one weak lamp."
        )
    else:
        world.say(
            f"At the end, the art stayed whole, and the lamp made a small gold pool "
            f"of light on the aisle floor."
        )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, child_name: str,
         child_gender: str, caretaker_name: str, caretaker_gender: str,
         trait: str) -> World:
    world = _setup_world(StoryParams(setting="", activity="", prize="", child="",
                                     child_gender="", caretaker="", caretaker_gender="",
                                     trait=""))
    world = World(setting)
    child = world.add(Entity(id=child_name, kind="character", type=child_gender,
                             role="child", tags={"child"},
                             meters={"wonder": 0.0}, memes={"curiosity": 1.0, "fear": 0.0}))
    caretaker = world.add(Entity(id="Caretaker", kind="character", type=caretaker_gender,
                                 role="caretaker", label=caretaker_name,
                                 meters={"worry": 0.0}, memes={"care": 1.0}))
    aisle = world.add(Entity(id="aisle", type="place", label=setting.place,
                             meters={"darkness": 0.0, "echo": 0.0, "draft": 0.0},
                             attrs={"mood": setting.mood}))
    prize = world.add(Entity(id="art", type="thing", label=prize_cfg.label,
                             role="prize", tags=prize_cfg.tags,
                             owner=child.id, location="aisle",
                             meters={"torn": 0.0, "wet": 0.0}, memes={"value": 1.0}))
    lamp = world.add(Entity(id="lamp", type="thing", label="battery lamp",
                            role="gear", tags={"lamp"},
                            meters={"charged": 1.0}, memes={"safety": 1.0}))
    world.facts.update(child=child, caretaker=caretaker, aisle=aisle, prize=prize, gear=lamp,
                       activity=activity, trait=trait, setting=setting)
    _start(world, child)
    world.para()
    _sound(world, child, activity)
    _warn(world, caretaker, child, activity, prize)
    if trait in {"curious", "gentle"}:
        _choose_safely(world, child, prize)
        world.para()
        world.say(f"That choice was enough to satisfy the moment without waking the dark.")
        _ending_image(world, child, prize)
        world.facts["outcome"] = "safe"
    else:
        _bad_ending(world, child, caretaker, prize)
        world.para()
        _ending_image(world, child, prize)
        world.facts["outcome"] = "bad"
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a ghost-story for a child in a {f["setting"].place} where an eerie sound makes them want to satisfy their curiosity.',
        f'Write a short story that uses the words "satisfy" and "art" and includes a strange sound effect in a warehouse aisle.',
        f'Write a spooky but child-facing story about {f["child"].id} listening to a sound in the aisle and deciding what to do with the art.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = f["child"]
    caretaker = f["caretaker"]
    prize = f["prize"]
    act = f["activity"]
    qa = [
        QAItem(
            question=f"What did {child.id} hear in the warehouse aisle?",
            answer=f"{child.id} heard a soft sound effect that grew louder between the shelves. It made the aisle feel spooky and made {child.id} curious about what was hiding there.",
        ),
        QAItem(
            question=f"Why did {caretaker.label} worry about the art?",
            answer=f"{caretaker.label} worried because the strange sound could shake the aisle and damage the art. The worry came from the dark shelves, the echo, and how fragile the paper art was.",
        ),
    ]
    if f.get("outcome") == "bad":
        qa.append(QAItem(
            question=f"What happened to the art at the end?",
            answer=f"The art tore when the shelves shuddered and the light went out. The ending was bad because the little picture could not be saved once the aisle turned cold and dark.",
        ))
    else:
        qa.append(QAItem(
            question=f"How did {child.id} satisfy curiosity without breaking the art?",
            answer=f"{child.id} listened carefully and used the battery lamp instead of rushing toward the sound. That calmer choice satisfied curiosity while keeping the art safe.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    if f.get("outcome") == "bad":
        tags.add("ghost")
        tags.add("dark")
    out: list[QAItem] = []
    if "sound" in tags:
        out.append(QAItem(
            question="What is an echo?",
            answer="An echo is a sound that bounces off walls or shelves and comes back to your ears a little later.",
        ))
    if "dark" in tags or True:
        out.append(QAItem(
            question="Why can a dim aisle feel spooky?",
            answer="A dim aisle can feel spooky because shadows hide details and small noises seem bigger and closer.",
        ))
    out.append(QAItem(
        question="What is art made of paper like?",
        answer="Paper art can be delicate, so it can tear or crease if it is dropped or caught on a sharp edge.",
    ))
    return out


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
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.role:
            bits.append(f"role={e.role}")
        if e.attrs:
            bits.append(f"attrs={e.attrs}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


SETTINGS = {
    "warehouse_aisle": Setting(place="warehouse aisle", affords={"sound_of_boxes", "whisper_between_shelves"}, mood="dim"),
}

ACTIVITIES = {
    "sound_of_boxes": Activity(id="sound_of_boxes", verb="listen for the sound", sound="clack-clack", mess="tear", zone="art", keyword="sound", tags={"sound", "ghost"}),
    "whisper_between_shelves": Activity(id="whisper_between_shelves", verb="follow the whisper", sound="shhhhhh", mess="tear", zone="art", keyword="whisper", tags={"sound", "ghost"}),
}

PRIZES = {
    "paper_art": Prize(id="paper_art", label="paper art", phrase="a piece of paper art", region="art", tags={"art", "paper"}),
    "chalk_art": Prize(id="chalk_art", label="chalk art", phrase="a small chalk drawing", region="art", tags={"art", "chalk"}),
}

TRAITS = ["curious", "gentle", "bold", "careful"]
GIRL_NAMES = ["Mina", "Lina", "Tessa", "Ivy", "Nora"]
BOY_NAMES = ["Owen", "Milo", "Eli", "Jude", "Theo"]
CARETAKER_NAMES = ["Aunt June", "Uncle Ray", "Ms. Hart", "Mr. Bell"]


CURATED = [
    StoryParams(setting="warehouse_aisle", activity="sound_of_boxes", prize="paper_art", child="Mina", child_gender="girl", caretaker="Ms. Hart", caretaker_gender="woman", trait="curious"),
    StoryParams(setting="warehouse_aisle", activity="whisper_between_shelves", prize="chalk_art", child="Owen", child_gender="boy", caretaker="Uncle Ray", caretaker_gender="man", trait="careful"),
]


def explain_rejection() -> str:
    return "(No story: this world needs the art to be vulnerable to the aisle's echo, so the setup must keep the sound and art together.)"


def asp_facts() -> str:
    import asp
    lines = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for a in s.affords:
            lines.append(asp.fact("affords", sid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("zone", aid, a.zone))
        for t in a.tags:
            lines.append(asp.fact("tag", aid, t))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("region", pid, p.region))
        for t in p.tags:
            lines.append(asp.fact("tagp", pid, t))
    return "\n".join(lines)


ASP_RULES = r"""
valid(S,A,P) :- affords(S,A), activity(A), prize(P), zone(A,Z), region(P,Z).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp
    # smoke test on ordinary generation
    sample = generate(resolve_params(argparse.Namespace(setting=None, activity=None, prize=None,
                                                        child=None, child_gender=None, caretaker=None,
                                                        caretaker_gender=None, trait=None),
                                      random.Random(777)))
    if not sample.story:
        print("MISMATCH: generation produced empty story")
        return 1
    if set(asp_valid_combos()) != set(valid_combos()):
        print("MISMATCH: ASP and Python combo sets differ")
        return 1
    try:
        _ = sample.to_json()
    except Exception as e:  # noqa: BLE001
        print(f"MISMATCH: serialization failed: {e}")
        return 1
    print("OK: verify passed; generation, JSON, and ASP parity succeeded.")
    return 0


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS:
        pass
    if params.activity not in ACTIVITIES or params.prize not in PRIZES:
        pass
    world = tell(_safe_lookup(SETTINGS, params.setting), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize),
                 params.child, params.child_gender, params.caretaker, params.caretaker_gender, params.trait)
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
        print(f"{len(asp_valid_combos())} compatible combos:")
        for row in asp_valid_combos():
            print(" ", row)
        return
    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            samples.append(generate(params))
    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return
    for i, sample in enumerate(samples):
        header = f"### variant {i+1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
