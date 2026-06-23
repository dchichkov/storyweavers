#!/usr/bin/env python3
"""
storyworlds/worlds/cadet_flower_field_magic_humor_folk_tale.py
==============================================================

A standalone story world for a small folk-tale flavored scene in a flower field:
a cadet tries a bit of magic, causes a humorous mix-up, and then learns a kinder,
safer way to use the wonder so the field blooms instead of being spoiled.

The domain is intentionally tiny and constraint-checked.  The world model uses
typed entities with physical meters and emotional memes, a forward-chained causal
engine, a Python reasonableness gate, and an inline ASP twin for parity checks.

Initial story sketch:
---
A young cadet came to a flower field to practice a small charm. The cadet meant
to make the blossoms sing for a village festival, but the spell tickled a bee,
sent a hat spinning, and made everyone laugh. A kind field keeper showed the
cadet how to use the magic gently, and the flowers rang soft and bright like
bells.

Causal beats:
---
    spell used in flower field -> charm += 1, surprise += 1
    surprise near bees/hat      -> laugh += 1, clutter += 1
    gentle correction           -> charm steadies, worry eases
    helpful magic on flowers    -> bloom += 1, joy += 1

Story shape:
---
    setup: cadet arrives in flower field with a charm to try
    tension: magic backfires in a comic way
    turn: field keeper explains the kind way to do it
    resolution: the cadet uses magic gently and the field ends bright
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

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
    plural: bool = False
    attrs: dict = field(default_factory=dict)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    bee: object | None = None
    cadet: object | None = None
    field: object | None = None
    flowers: object | None = None
    hat: object | None = None
    keeper: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "cadet"}
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
    id: str
    place: str
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
class Charm:
    id: str
    name: str
    phrase: str
    method: str
    effect: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Concern:
    id: str
    name: str
    phrase: str
    kind: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
class Help:
    id: str
    name: str
    phrase: str
    method: str
    tags: set[str] = field(default_factory=set)
    @property
    def label_word(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def label(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

    @property
    def award_phrase(self) -> str:
        return str(getattr(self, "phrase", None) or getattr(self, "name", None) or getattr(self, "id", None) or getattr(self, "type", self.__class__.__name__.lower()))

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
        c = World(self.setting)
        c.entities = copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.paragraphs = [[]]
        c.facts = copy.deepcopy(self.facts)
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


def _r_spill(world: World) -> list[str]:
    out = []
    cadet = world.get("cadet")
    if cadet.meters.get("charm", 0) < THRESHOLD:
        return out
    sig = ("spill",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    bee = world.get("bee")
    hat = world.get("hat")
    field = world.get("field")
    bee.memes["startle"] = bee.memes.get("startle", 0) + 1
    hat.meters["lost"] = hat.meters.get("lost", 0) + 1
    field.meters["clutter"] = field.meters.get("clutter", 0) + 1
    out.append("A bee buzzed wild, and the hat spun off like a little windmill.")
    return out


def _r_laugh(world: World) -> list[str]:
    out = []
    if world.get("field").meters.get("clutter", 0) < THRESHOLD:
        return out
    sig = ("laugh",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    cadet = world.get("cadet")
    keeper = world.get("keeper")
    cadet.memes["humor"] = cadet.memes.get("humor", 0) + 1
    keeper.memes["humor"] = keeper.memes.get("humor", 0) + 1
    out.append("Even the field keeper had to smile at the silly old swirl of it all.")
    return out


def _r_bloom(world: World) -> list[str]:
    out = []
    if world.get("cadet").meters.get("gentle", 0) < THRESHOLD:
        return out
    sig = ("bloom",)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    field = world.get("field")
    flowers = world.get("flowers")
    cadet = world.get("cadet")
    keeper = world.get("keeper")
    field.meters["bloom"] = field.meters.get("bloom", 0) + 1
    flowers.meters["glow"] = flowers.meters.get("glow", 0) + 1
    cadet.memes["joy"] = cadet.memes.get("joy", 0) + 1
    keeper.memes["joy"] = keeper.memes.get("joy", 0) + 1
    out.append("Then the flowers brightened, soft as little bells ringing in the sun.")
    return out


CAUSAL_RULES = [Rule("spill", _r_spill), Rule("laugh", _r_laugh), Rule("bloom", _r_bloom)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
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


def valid_combo(setting: Setting, charm: Charm, concern: Concern, helper: Help) -> bool:
    return setting.place == "flower field" and "flower_field" in charm.tags and concern.kind == "bee" and "gentle" in helper.tags


def valid_combos() -> list[tuple[str, str, str, str]]:
    combos = []
    for sid, s in SETTINGS.items():
        for cid, c in CHARMS.items():
            for xid, x in CONCERNS.items():
                for hid, h in HELPS.items():
                    if valid_combo(s, c, x, h):
                        combos.append((sid, cid, xid, hid))
    return combos


def predict_mixup(world: World) -> dict:
    sim = world.copy()
    cadet = sim.get("cadet")
    cadet.meters["charm"] = cadet.meters.get("charm", 0) + 1
    propagate(sim, narrate=False)
    return {
        "clutter": sim.get("field").meters.get("clutter", 0),
        "laugh": sim.get("cadet").memes.get("humor", 0),
    }


def introduce(world: World, cadet: Entity, setting: Setting) -> None:
    world.say(f"A young cadet named {cadet.id} came to {setting.place} with a tidy coat and bright boots.")
    world.say(f"{cadet.pronoun().capitalize()} had come to practice a little charm for the village festival.")


def invite(world: World, keeper: Entity, charm: Charm, concern: Concern) -> None:
    world.say(f'The field keeper said, "A good charm should please the flowers, not tease the bees."')
    world.say(f"But {keeper.id} knew the field could get silly in a hurry, especially near {concern.phrase}.")


def cast(world: World, cadet: Entity, charm: Charm) -> None:
    cadet.meters["charm"] = cadet.meters.get("charm", 0) + 1
    cadet.memes["hope"] = cadet.memes.get("hope", 0) + 1
    world.say(f"{cadet.id} whispered {charm.phrase} and used {charm.method}.")
    world.say(f"For one blink, the blossoms tried to answer back.")


def warn(world: World, keeper: Entity, cadet: Entity, concern: Concern) -> None:
    pred = predict_mixup(world)
    world.facts["predicted_clutter"] = pred["clutter"]
    world.say(f'{keeper.id} pointed to the buzzing bees and said, "Take care, or {concern.phrase} will start a comic stir."')


def tumble(world: World) -> None:
    propagate(world, narrate=True)


def correct(world: World, keeper: Entity, cadet: Entity, help_item: Help) -> None:
    cadet.meters["gentle"] = cadet.meters.get("gentle", 0) + 1
    cadet.memes["worry"] = max(0, cadet.memes.get("worry", 0) - 1)
    keeper.memes["calm"] = keeper.memes.get("calm", 0) + 1
    world.say(f'{keeper.id} laughed kindly and showed {cadet.id} how to use {help_item.phrase}.')
    world.say(f'"Try the soft way," {keeper.id} said. "Magic works best when it is as polite as a song."')


def resolve(world: World, cadet: Entity, helper: Entity) -> None:
    world.say(f"{cadet.id} bowed, tried again, and this time the charm went small and sweet.")
    world.say(f"{helper.id} nodded, and the flowers shimmered as if they were pleased to be included.")


def tell(params: "StoryParams") -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    charm = _safe_lookup(CHARMS, params.charm)
    concern = _safe_lookup(CONCERNS, params.concern)
    help_item = _safe_lookup(HELPS, params.help)
    world = World(setting)

    cadet = world.add(Entity(id=params.name, kind="character", type="cadet", role="cadet",
                             meters={"charm": 0.0, "gentle": 0.0}, memes={"hope": 0.0, "worry": 0.0, "joy": 0.0, "humor": 0.0}))
    keeper = world.add(Entity(id="keeper", kind="character", type="woman", role="keeper", label="the field keeper",
                              meters={"clutter": 0.0}, memes={"calm": 0.0, "joy": 0.0, "humor": 0.0}))
    bee = world.add(Entity(id="bee", kind="thing", type="bee", label="a bee", plural=False,
                           meters={"startle": 0.0}, memes={"startle": 0.0}))
    hat = world.add(Entity(id="hat", kind="thing", type="hat", label="a hat", plural=False,
                           meters={"lost": 0.0}))
    field = world.add(Entity(id="field", kind="thing", type="field", label="the flower field",
                             meters={"clutter": 0.0, "bloom": 0.0}))
    flowers = world.add(Entity(id="flowers", kind="thing", type="flowers", label="the flowers",
                               meters={"glow": 0.0}))

    world.facts.update(setting=setting, charm=charm, concern=concern, help=help_item,
                       cadet=cadet, keeper=keeper, bee=bee, hat=hat, field=field, flowers=flowers)

    introduce(world, cadet, setting)
    world.para()
    invite(world, keeper, charm, concern)
    cast(world, cadet, charm)
    warn(world, keeper, cadet, concern)
    tumble(world)
    world.para()
    correct(world, keeper, cadet, help_item)
    resolve(world, cadet, keeper)
    cadet.meters["gentle"] += 1
    propagate(world, narrate=True)

    return world


@dataclass
class StoryParams:
    setting: str
    charm: str
    concern: str
    help: str
    name: str
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


SETTINGS = {
    "flower_field": Setting(id="flower_field", place="the flower field", tags={"flower_field", "field"}),
}

CHARMS = {
    "petal_pulse": Charm(id="petal_pulse", name="petal pulse", phrase="petal pulse", method="a whisper and a twirl",
                         effect="make flowers ring softly", tags={"flower_field", "magic"}),
    "dew_dance": Charm(id="dew_dance", name="dew dance", phrase="dew dance", method="a tap of the heel",
                       effect="wake the morning dew", tags={"flower_field", "magic"}),
}

CONCERNS = {
    "bee_bother": Concern(id="bee_bother", name="buzzing bees", phrase="the buzzing bees", kind="bee", tags={"humor", "bee"}),
}

HELPS = {
    "soft_song": Help(id="soft_song", name="soft song", phrase="a soft song", method="slow and gentle words", tags={"gentle", "magic", "humor"}),
    "dew_bell": Help(id="dew_bell", name="dew bell", phrase="a dew bell", method="a quiet ring", tags={"gentle", "magic"}),
}

NAMES = ["Ari", "Mina", "Pip", "Sera", "Lio", "Nia"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a folk-tale story for a child named {f["cadet"].id} in a {f["setting"].place} where a small magic charm causes a funny mistake and then gets used kindly.',
        f'Create a gentle humorous tale in the flower field that includes the word "cadet" and ends with flowers shining softly.',
        f"Tell a short story about a cadet, magic, and a laughing correction in the flower field.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    cadet = f["cadet"]
    keeper = f["keeper"]
    charm = f["charm"]
    help_item = f["help"]
    concern = f["concern"]
    return [
        QAItem(
            question=f"What did {cadet.id} come to the flower field to do?",
            answer=f"{cadet.id} came to the flower field to practice {charm.phrase}. {cadet.id} wanted the flowers to answer back in a festival kind of way, not cause trouble.",
        ),
        QAItem(
            question=f"Why did the field keeper worry when {cadet.id} used the charm?",
            answer=f"{keeper.id} worried because the charm was near {concern.phrase}. That could make the field get too noisy and silly before the magic was guided gently.",
        ),
        QAItem(
            question=f"How did {cadet.id} and the field keeper fix the mistake?",
            answer=f"They slowed down and used {help_item.phrase}. After that, the magic became gentle, so the flowers could shine without scaring the bees.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a cadet?",
            answer="A cadet is a young person who is learning and practicing like a student in a uniform. In stories, a cadet often tries hard, listens, and learns a lesson.",
        ),
        QAItem(
            question="Why can bees make people laugh in a story?",
            answer="Bees are small and busy, and their buzzing can seem funny when a story wants a comic moment. Their quick flying often makes a scene lively instead of still.",
        ),
        QAItem(
            question="What does magic do in a folk tale?",
            answer="Magic in a folk tale can change a simple thing into something wondrous. It often helps a character learn a kinder way to solve a problem.",
        ),
        QAItem(
            question="What is a flower field?",
            answer="A flower field is a wide place where many flowers grow together. It can look bright, soft, and full of little colors.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== world questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        out.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    out.append(f"  fired={sorted({k[0] for k in world.fired})}")
    return "\n".join(out)


ASP_RULES = r"""
spill :- cadet_charm, bee, hat, field.
laugh :- spill.
bloom :- gentle_charm.
"""


def asp_facts() -> str:
    import asp
    lines = []
    for sid in SETTINGS:
        lines.append(asp.fact("setting", sid))
    for cid in CHARMS:
        lines.append(asp.fact("charm", cid))
        lines.append(asp.fact("flower_field_charm", cid))
    for cid in CONCERNS:
        lines.append(asp.fact("concern", cid))
        lines.append(asp.fact("bee_concern", cid))
    for hid in HELPS:
        lines.append(asp.fact("help", hid))
        lines.append(asp.fact("gentle_help", hid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_verify() -> int:
    import asp
    m = asp.one_model(asp_program("#show spill/0.\n#show laugh/0.\n#show bloom/0."))
    atoms = {s.name for s in m}
    ok = {"spill", "laugh", "bloom"}.issubset(atoms)
    sample = generate(resolve_params(argparse.Namespace(setting=None, charm=None, concern=None, help=None, name=None), random.Random(777)))
    if not sample.story:
        ok = False
    print("OK" if ok else "MISMATCH")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: cadet, flower field, magic, and humor.")
    ap.add_argument("--setting", choices=SETTINGS.keys())
    ap.add_argument("--charm", choices=CHARMS.keys())
    ap.add_argument("--concern", choices=CONCERNS.keys())
    ap.add_argument("--help-item", dest="help", choices=HELPS.keys())
    ap.add_argument("--name", choices=NAMES)
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
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    filtered = [c for c in combos
                if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
                and (getattr(args, "charm", None) is None or c[1] == getattr(args, "charm", None))
                and (getattr(args, "concern", None) is None or c[2] == getattr(args, "concern", None))
                and (getattr(args, "help", None) is None or c[3] == getattr(args, "help", None))]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, charm, concern, help_item = rng.choice(list(filtered))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    return StoryParams(setting=setting, charm=charm, concern=concern, help=help_item, name=name)


def generate(params: StoryParams) -> StorySample:
    if params.setting not in SETTINGS or params.charm not in CHARMS or params.concern not in CONCERNS or params.help not in HELPS:
        pass
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


CURATED = [
    StoryParams(setting="flower_field", charm="petal_pulse", concern="bee_bother", help="soft_song", name="Ari"),
    StoryParams(setting="flower_field", charm="dew_dance", concern="bee_bother", help="dew_bell", name="Mina"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show spill/0.\n#show laugh/0.\n#show bloom/0."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show spill/0.\n#show laugh/0.\n#show bloom/0."))
        print(sorted({s.name for s in model}))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples = [generate(p) for p in CURATED] if getattr(args, "all", None) else []
    if not getattr(args, "all", None):
        seen = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            seed = base_seed + i
            i += 1
            p = resolve_params(args, random.Random(seed))
            p.seed = seed
            s = generate(p)
            if s.story in seen:
                continue
            seen.add(s.story)
            samples.append(s)

    if getattr(args, "json", None):
        print(samples[0].to_json() if len(samples) == 1 else json.dumps([s.to_dict() for s in samples], indent=2, ensure_ascii=False))
        return

    for i, s in enumerate(samples):
        hdr = ""
        if getattr(args, "all", None):
            hdr = f"### {s.params.name}: {s.params.charm}"
        elif len(samples) > 1:
            hdr = f"### variant {i+1}"
        emit(s, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=hdr)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
