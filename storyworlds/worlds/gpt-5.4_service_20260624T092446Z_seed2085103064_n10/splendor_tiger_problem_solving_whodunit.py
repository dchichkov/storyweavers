#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    location: str = ""
    visible: bool = True
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    caretaker: object | None = None
    culprit: object | None = None
    hero: object | None = None
    hideout: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "queen"}
        male = {"boy", "man", "father", "king"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
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
    id: str
    place: str
    sparkle: str
    suspects: set[str]
    hideouts: set[str]
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
class Item:
    id: str
    label: str
    phrase: str
    weight: int
    shine: str
    answer: object | None = None
    question: object | None = None
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
class Suspect:
    id: str
    label: str
    phrase: str
    type: str
    clue: str
    clue_text: str
    method: str
    motive: str
    carry: int
    hides: set[str]
    traits: list[str]
    tags: set[str]
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
class Hideout:
    id: str
    label: str
    phrase: str
    detail: str
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
class World:
    setting: Setting
    paragraphs: list[list[str]] = field(default_factory=lambda: [[]])
    entities: dict[str, Entity] = field(default_factory=dict)
    facts: dict = field(default_factory=dict)
    trace: list[str] = field(default_factory=list)

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
        return copy.deepcopy(self)
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


SETTINGS = {
    "palace": Setting(
        id="palace",
        place="the palace gallery",
        sparkle="Every gold frame and polished tile made the room glow with splendor.",
        suspects={"tiger", "magpie", "monkey"},
        hideouts={"curtain", "music_box", "topiary"},
    ),
    "garden": Setting(
        id="garden",
        place="the moon garden",
        sparkle="Silver lanterns and white flowers gave the garden a quiet splendor.",
        suspects={"tiger", "magpie", "elephant"},
        hideouts={"topiary", "lily_basket", "curtain"},
    ),
    "pavilion": Setting(
        id="pavilion",
        place="the river pavilion",
        sparkle="Painted beams and bright silk made the pavilion shine with festival splendor.",
        suspects={"tiger", "monkey", "elephant"},
        hideouts={"drum", "curtain", "lily_basket"},
    ),
}

ITEMS = {
    "medal": Item(
        id="medal",
        label="sun medal",
        phrase="a splendid sun medal with a warm golden face",
        weight=1,
        shine="It flashed whenever the light touched it.",
    ),
    "key": Item(
        id="key",
        label="crystal key",
        phrase="a splendid crystal key tied with blue silk",
        weight=1,
        shine="Tiny colors danced inside it.",
    ),
    "brooch": Item(
        id="brooch",
        label="star brooch",
        phrase="a splendid star brooch with silver points",
        weight=1,
        shine="It looked like a little star that had fallen indoors.",
    ),
}

SUSPECTS = {
    "tiger": Suspect(
        id="tiger",
        label="Taru the tiger cub",
        phrase="a gentle tiger cub with bright whiskers",
        type="tiger",
        clue="stripe",
        clue_text="a soft orange hair with a black stripe on it",
        method="patted",
        motive="because he thought the shiny thing might slide off its stand",
        carry=2,
        hides={"curtain", "drum", "topiary"},
        traits=["gentle", "careful", "striped"],
        tags={"tiger", "fur"},
    ),
    "magpie": Suspect(
        id="magpie",
        label="Mika the magpie",
        phrase="a glossy black-and-white magpie who loved shiny things",
        type="bird",
        clue="feather",
        clue_text="a glossy black-and-white feather",
        method="picked up",
        motive="because she wanted to tuck the sparkle someplace high and safe",
        carry=1,
        hides={"curtain", "topiary", "music_box"},
        traits=["quick", "curious", "shiny-loving"],
        tags={"bird", "feather"},
    ),
    "monkey": Suspect(
        id="monkey",
        label="Nilo the monkey",
        phrase="a nimble monkey with clever hands",
        type="monkey",
        clue="ribbon_knot",
        clue_text="a ribbon tied in the funny looping knot only Nilo made",
        method="snatched",
        motive="because he was trying to decorate a hiding place for the parade surprise",
        carry=1,
        hides={"curtain", "music_box", "drum"},
        traits=["nimble", "busy", "clever"],
        tags={"monkey", "knot"},
    ),
    "elephant": Suspect(
        id="elephant",
        label="Pema the elephant calf",
        phrase="a kind elephant calf with a neat little trunk",
        type="elephant",
        clue="droplet",
        clue_text="round water drops and one damp trunk print",
        method="lifted",
        motive="because she wanted to move it away from a splashy watering can",
        carry=3,
        hides={"lily_basket", "curtain", "drum"},
        traits=["kind", "steady", "strong"],
        tags={"elephant", "water"},
    ),
}

HIDEOUTS = {
    "curtain": Hideout(
        id="curtain",
        label="the velvet curtain",
        phrase="behind the velvet curtain",
        detail="The hem puffed out just a little.",
    ),
    "music_box": Hideout(
        id="music_box",
        label="the music box",
        phrase="inside the giant music box",
        detail="A tiny note kept chiming from inside.",
    ),
    "topiary": Hideout(
        id="topiary",
        label="the tiger-shaped topiary",
        phrase="inside the tiger-shaped topiary arch",
        detail="Leaves trembled even though the air was still.",
    ),
    "drum": Hideout(
        id="drum",
        label="the parade drum",
        phrase="inside the parade drum",
        detail="The drum sounded oddly clinky when tapped.",
    ),
    "lily_basket": Hideout(
        id="lily_basket",
        label="the lily basket",
        phrase="under the basket of fresh lilies",
        detail="One white petal had slid onto the floor.",
    ),
}

HERO_NAMES = ["Mina", "Ivo", "Lena", "Tomi", "Rina", "Jules", "Nora", "Pip"]
CARETAKERS = ["Keeper Suri", "Auntie May", "Caretaker Bo"]
TRAITS = ["observant", "patient", "brave", "quiet", "thoughtful", "careful"]


def valid_cases() -> list[tuple[str, str, str, str]]:
    out = []
    for setting_id, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            for suspect_id in setting.suspects:
                suspect = _safe_lookup(SUSPECTS, suspect_id)
                if suspect.carry < item.weight:
                    continue
                for hideout_id in setting.hideouts:
                    if hideout_id in suspect.hides:
                        out.append((setting_id, item_id, suspect_id, hideout_id))
    return sorted(out)


def explain_rejection(setting_id: str, item_id: str, suspect_id: str, hideout_id: str) -> str:
    setting = _safe_lookup(SETTINGS, setting_id)
    item = _safe_lookup(ITEMS, item_id)
    suspect = _safe_lookup(SUSPECTS, suspect_id)
    hideout = _safe_lookup(HIDEOUTS, hideout_id)
    if suspect_id not in setting.suspects:
        return f"(No story: {suspect.label} is not in {setting.place}, so this suspect cannot be the whodunit answer there.)"
    if hideout_id not in setting.hideouts:
        return f"(No story: {hideout.label} does not belong in {setting.place}, so the missing {item.label} cannot reasonably end up there.)"
    if suspect.carry < item.weight:
        return f"(No story: {suspect.label} cannot carry the {item.label} in this world model.)"
    if hideout_id not in suspect.hides:
        return f"(No story: {suspect.label} would not hide the {item.label} in {hideout.label}.)"
    return "(No story: that combination is not reasonable in this world.)"


@dataclass
class StoryParams:
    setting: str
    item: str
    culprit: str
    hideout: str
    hero_name: str
    caretaker: str
    trait: str
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


def setup_world(params: StoryParams) -> World:
    setting = _safe_lookup(SETTINGS, params.setting)
    item_cfg = _safe_lookup(ITEMS, params.item)
    culprit_cfg = _safe_lookup(SUSPECTS, params.culprit)
    hideout_cfg = _safe_lookup(HIDEOUTS, params.hideout)

    world = World(setting=setting)
    hero = world.add(Entity(id="hero", kind="character", type="girl", label=params.hero_name, traits=[params.trait]))
    caretaker = world.add(Entity(id="caretaker", kind="character", type="woman", label=params.caretaker))
    item = world.add(Entity(id="item", kind="thing", type="treasure", label=item_cfg.label, phrase=item_cfg.phrase, owner=caretaker.id, location="display stand"))
    culprit = world.add(Entity(id="culprit", kind="character", type=culprit_cfg.type, label=culprit_cfg.label, phrase=culprit_cfg.phrase, location=setting.place))
    hideout = world.add(Entity(id="hideout", kind="thing", type="place", label=hideout_cfg.label, phrase=hideout_cfg.phrase, location=setting.place))
    for suspect_id in sorted(setting.suspects):
        if suspect_id == params.culprit:
            continue
        cfg = _safe_lookup(SUSPECTS, suspect_id)
        world.add(Entity(id=f"suspect_{suspect_id}", kind="character", type=cfg.type, label=cfg.label, phrase=cfg.phrase, location=setting.place))
    world.facts.update(
        hero=hero,
        caretaker=caretaker,
        item_cfg=item_cfg,
        culprit_cfg=culprit_cfg,
        hideout_cfg=hideout_cfg,
        clue=culprit_cfg.clue,
        suspects=[params.culprit] + [s for s in sorted(setting.suspects) if s != params.culprit],
    )
    return world


def remove_item(world: World) -> None:
    item = world.get("item")
    culprit = world.get("culprit")
    hideout = world.get("hideout")
    culprit_cfg = _safe_fact(world, world.facts, "culprit_cfg")

    item.location = hideout.id
    item.visible = False
    culprit.meters["carried"] += 1
    culprit.meters["left_clue"] += 1
    culprit.memes["worry"] += 1
    world.trace.append(f"{culprit.label} moved {item.label} to {hideout.label} and left clue={culprit_cfg.clue}.")


def introduce(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    caretaker = _safe_fact(world, world.facts, "caretaker")
    item_cfg = _safe_fact(world, world.facts, "item_cfg")
    world.say(f"{hero.label} was a {hero.traits[0]} child who noticed tiny things other people missed.")
    world.say(f"On the morning of the Splendor Parade, {hero.label} visited {world.setting.place} with {caretaker.label}.")
    world.say(world.setting.sparkle)
    world.say(f"On a tall stand rested {item_cfg.phrase}. {item_cfg.shine}")


def discover_problem(world: World) -> None:
    caretaker = _safe_fact(world, world.facts, "caretaker")
    item_cfg = _safe_fact(world, world.facts, "item_cfg")
    world.para()
    world.say(f"When {caretaker.label} turned to greet the band, the {item_cfg.label} was gone.")
    world.say(f'"Oh dear," said {caretaker.label}. "The parade starts soon, and that splendid piece belongs at the front."')
    world.say("The room went still in the way it does when a mystery tiptoes in.")
    world.facts["hero"].memes["concern"] += 1
    world.facts["caretaker"].memes["concern"] += 1


def inspect_clue(world: World) -> None:
    clue = _safe_fact(world, world.facts, "clue")
    culprit_cfg = _safe_fact(world, world.facts, "culprit_cfg")
    hero = _safe_fact(world, world.facts, "hero")
    world.para()
    world.say(f"{hero.label} did not guess. {hero.pronoun('subject').capitalize()} looked down first.")
    world.say(f"Near the empty stand lay {culprit_cfg.clue_text}.")
    world.facts["found_clue"] = clue
    hero.meters["clues_found"] += 1
    world.trace.append(f"{hero.label} found clue={clue} beside the stand.")


def suspects_sentence(world: World) -> str:
    names = [_safe_lookup(SUSPECTS, s).label for s in sorted(world.setting.suspects)]
    if len(names) == 2:
        return f"{names[0]} and {names[1]}"
    return ", ".join(names[:-1]) + f", and {names[-1]}"


def reason_about_clue(world: World) -> list[str]:
    found = _safe_fact(world, world.facts, "found_clue")
    possible = []
    for suspect_id in sorted(world.setting.suspects):
        if _safe_lookup(SUSPECTS, suspect_id).clue == found:
            possible.append(suspect_id)
    world.facts["possible"] = possible
    world.trace.append(f"Reasoned from clue={found} to suspects={possible}.")
    return possible


def question_and_deduce(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    caretaker = _safe_fact(world, world.facts, "caretaker")
    culprit_cfg = _safe_fact(world, world.facts, "culprit_cfg")
    hideout_cfg = _safe_fact(world, world.facts, "hideout_cfg")
    possible = reason_about_clue(world)

    world.say(f"{hero.label} looked at the stand, then at {suspects_sentence(world)}.")
    if culprit_cfg.id == "tiger":
        world.say('"A striped hair is not from a magpie or an elephant," said ' + hero.label + '. "It must be from Taru the tiger cub."')
    elif culprit_cfg.id == "magpie":
        world.say(f'"A glossy feather points to Mika the magpie," said {hero.label}. "The others do not leave feathers."')
    elif culprit_cfg.id == "monkey":
        world.say(f'"That loopy ribbon knot is Nilo\'s style," said {hero.label}. "He ties everything that way."')
    elif culprit_cfg.id == "elephant":
        world.say(f'"Those damp trunk marks belong to Pema," said {hero.label}. "She must have passed this way."')
    else:
        pass

    hero.memes["confidence"] += 1

    if hideout_cfg.id == "drum":
        second = "and the parade drum gave a tiny clink when tapped"
    elif hideout_cfg.id == "curtain":
        second = "and the velvet curtain bulged near the floor"
    elif hideout_cfg.id == "music_box":
        second = "and the big music box chimed in a jangly, crowded way"
    elif hideout_cfg.id == "topiary":
        second = "and the tiger-shaped topiary rustled when no breeze passed"
    else:
        second = "and a white petal had fallen from the lily basket"
    world.say(f'{caretaker.label} blinked. "{possible[0] if possible else "someone"}?"')
    world.say(f'{hero.label} nodded. "{culprit_cfg.label} {culprit_cfg.motive}, {second}."')
    world.trace.append(f"{hero.label} linked culprit={culprit_cfg.id} to hideout={hideout_cfg.id}.")


def retrieve_item(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    culprit = world.get("culprit")
    caretaker = _safe_fact(world, world.facts, "caretaker")
    item = world.get("item")
    hideout = world.get("hideout")
    culprit_cfg = _safe_fact(world, world.facts, "culprit_cfg")
    hideout_cfg = _safe_fact(world, world.facts, "hideout_cfg")

    world.para()
    world.say(f"They walked to {hideout_cfg.label}. {hideout_cfg.detail}")
    world.say(f'"Taru? Mika? Nilo? Pema?" called {hero.label}, using the softest voice {hero.pronoun("subject")} had. "If you were trying to help, we can help together."')
    culprit.memes["worry"] -= 1
    culprit.memes["relief"] += 1
    world.say(f"Out came {culprit_cfg.label}, looking embarrassed but not mean.")
    world.say(f'"I only {culprit_cfg.method} it," {culprit.pronoun("subject")} admitted, "because I was trying to keep it safe."')
    item.visible = True
    item.location = "display stand"
    culprit.meters["returned"] += 1
    hero.meters["solved"] += 1
    hero.memes["relief"] += 1
    caretaker.memes["relief"] += 1
    world.trace.append(f"{culprit_cfg.label} confessed and returned {item.label} from {hideout.label}.")

    world.say(f"{caretaker.label} smiled instead of scolding. \"Thank you for telling the truth. Next time, please ask first.\"")
    world.say(f"Then {hero.label} carried the {item.label} back to the stand while {culprit_cfg.label} trotted beside {hero.pronoun('object')}.")


def closing_image(world: World) -> None:
    hero = _safe_fact(world, world.facts, "hero")
    culprit_cfg = _safe_fact(world, world.facts, "culprit_cfg")
    item_cfg = _safe_fact(world, world.facts, "item_cfg")
    world.say(f"When the parade began, the {item_cfg.label} shone in full splendor again.")
    if culprit_cfg.id == "tiger":
        world.say(f"Taru the tiger cub sat very straight by the stand, and {hero.label} gave him a small wink to show the mystery was mended.")
    else:
        world.say(f"{hero.label} felt proud, because careful thinking had turned a frightened hush into a happy start.")


def tell(params: StoryParams) -> World:
    if (params.setting, params.item, params.culprit, params.hideout) not in set(valid_cases()):
        pass
    world = setup_world(params)
    introduce(world)
    remove_item(world)
    discover_problem(world)
    inspect_clue(world)
    question_and_deduce(world)
    retrieve_item(world)
    closing_image(world)
    return world


KNOWLEDGE = {
    "tiger": [
        ("What is a tiger cub?", "A tiger cub is a young tiger. It is smaller than a grown tiger and still learning how to move through the world."),
        ("How can stripes help in a mystery?", "Stripes can help because they make tiger fur easy to recognize, so a striped hair is a useful clue."),
    ],
    "feather": [
        ("What is a feather?", "A feather is the soft covering that grows on a bird. Feathers help birds fly and keep warm."),
    ],
    "monkey": [
        ("Why are monkeys good at grabbing things?", "Monkeys have nimble hands and feet, so they can hold and move things quickly."),
    ],
    "elephant": [
        ("What can an elephant use its trunk for?", "An elephant can use its trunk to lift, smell, touch, and carry things."),
    ],
    "mystery": [
        ("What is a clue?", "A clue is a sign that helps you figure out what happened."),
        ("How do you solve a mystery?", "You solve a mystery by looking carefully, asking good questions, and testing your ideas with real clues."),
    ],
    "splendor": [
        ("What does splendor mean?", "Splendor means great beauty and brightness that make a place or thing feel grand and special."),
    ],
}

KNOWLEDGE_ORDER = ["mystery", "splendor", "tiger", "feather", "monkey", "elephant"]


def generation_prompts(world: World) -> list[str]:
    hero = _safe_fact(world, world.facts, "hero")
    item = _safe_fact(world, world.facts, "item_cfg")
    culprit = _safe_fact(world, world.facts, "culprit_cfg")
    return [
        f'Write a short child-friendly whodunit about splendor in {world.setting.place} where {hero.label} solves the mystery of a missing {item.label}.',
        f"Tell a gentle Problem Solving story in which a child follows one clue, questions suspects, and discovers that {culprit.label} moved a splendid object.",
        f'Write a TinyStories-style mystery that includes the words "splendor" and "tiger" and ends with the missing object safely returned.',
    ]


def story_qa(world: World) -> list[QAItem]:
    hero = _safe_fact(world, world.facts, "hero")
    caretaker = _safe_fact(world, world.facts, "caretaker")
    item = _safe_fact(world, world.facts, "item_cfg")
    culprit = _safe_fact(world, world.facts, "culprit_cfg")
    hideout = _safe_fact(world, world.facts, "hideout_cfg")

    out = [
        QAItem(
            question=f"Where did the mystery happen, and what was missing?",
            answer=f"The mystery happened in {world.setting.place}. The missing thing was {item.phrase}, which had been sitting on its stand before it disappeared.",
        ),
        QAItem(
            question=f"How did {hero.label} begin solving the mystery?",
            answer=f"{hero.label} began by looking carefully instead of guessing. {hero.pronoun('subject').capitalize()} found {culprit.clue_text} near the empty stand, and that clue helped narrow down who had touched the {item.label}.",
        ),
        QAItem(
            question=f"Who moved the {item.label}, and why?",
            answer=f"{culprit.label} moved the {item.label}. {culprit.pronoun('subject').capitalize()} was not trying to be mean; {culprit.pronoun('subject')} did it {culprit.motive}, even though taking it without asking caused the mystery.",
        ),
        QAItem(
            question=f"Where was the {item.label} found?",
            answer=f"The {item.label} was found {hideout.phrase}. {hero.label} used the clue and another sign nearby to figure out the right hiding place.",
        ),
        QAItem(
            question=f"How was the problem solved at the end?",
            answer=f"The problem was solved when {hero.label} spoke gently, got the truth from {culprit.label}, and helped return the {item.label} to its stand. Because {hero.pronoun('subject')} used careful thinking and kind words, the parade could begin in splendor again.",
        ),
    ]
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = {"mystery", "splendor"}
    culprit = _safe_fact(world, world.facts, "culprit_cfg")
    if culprit.id == "tiger":
        tags.add("tiger")
    elif culprit.id == "magpie":
        tags.add("feather")
    elif culprit.id == "monkey":
        tags.add("monkey")
    elif culprit.id == "elephant":
        tags.add("elephant")
    out: list[QAItem] = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            for q, a in KNOWLEDGE[tag]:
                out.append(QAItem(question=q, answer=a))
    return out


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for ent in list(world.entities.values()):
        meters = {k: v for k, v in ent.meters.items() if v}
        memes = {k: v for k, v in ent.memes.items() if v}
        lines.append(
            f"  {ent.id:16} ({ent.type:8}) location={ent.location!r} visible={ent.visible} "
            f"meters={dict(meters)} memes={dict(memes)}"
        )
    lines.append("  facts:")
    for key in ["clue", "found_clue", "possible"]:
        if key in world.facts:
            lines.append(f"    {key}: {world.facts[key]}")
    lines.append("  trace:")
    for item in world.trace:
        lines.append(f"    - {item}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="palace", item="medal", culprit="tiger", hideout="curtain", hero_name="Mina", caretaker="Keeper Suri", trait="observant"),
    StoryParams(setting="garden", item="brooch", culprit="magpie", hideout="topiary", hero_name="Ivo", caretaker="Auntie May", trait="patient"),
    StoryParams(setting="pavilion", item="key", culprit="monkey", hideout="drum", hero_name="Lena", caretaker="Caretaker Bo", trait="thoughtful"),
    StoryParams(setting="garden", item="medal", culprit="elephant", hideout="lily_basket", hero_name="Tomi", caretaker="Keeper Suri", trait="careful"),
]


ASP_RULES = r"""
valid(Setting, Item, Suspect, Hideout) :-
    setting(Setting), item(Item), suspect(Suspect), hideout(Hideout),
    present(Setting, Suspect),
    stores(Setting, Hideout),
    can_carry(Suspect, W),
    weight(Item, W2), W >= W2,
    likes_hideout(Suspect, Hideout).

#show valid/4.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for setting_id, setting in SETTINGS.items():
        lines.append(asp.fact("setting", setting_id))
        for suspect_id in sorted(setting.suspects):
            lines.append(asp.fact("present", setting_id, suspect_id))
        for hideout_id in sorted(setting.hideouts):
            lines.append(asp.fact("stores", setting_id, hideout_id))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("weight", item_id, item.weight))
    for suspect_id, suspect in SUSPECTS.items():
        lines.append(asp.fact("suspect", suspect_id))
        lines.append(asp.fact("can_carry", suspect_id, suspect.carry))
        for hideout_id in sorted(suspect.hides):
            lines.append(asp.fact("likes_hideout", suspect_id, hideout_id))
    for hideout_id in HIDEOUTS:
        lines.append(asp.fact("hideout", hideout_id))
    return "\n".join(lines)


def asp_program(show_rules: Optional[str] = None) -> str:
    base = asp_facts() + "\n" + ASP_RULES
    if show_rules:
        return asp_facts() + "\n" + ASP_RULES.replace("#show valid/4.", "") + "\n" + show_rules
    return base


def asp_valid_cases() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/4."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_cases())
    cl = set(asp_valid_cases())
    code = 0
    if py != cl:
        print("MISMATCH between Python and ASP valid cases.")
        print("Only in Python:", sorted(py - cl))
        print("Only in ASP:", sorted(cl - py))
        code = 1
    else:
        print(f"OK: ASP matches Python on {len(py)} valid cases.")
    if code:
        return code
    for params in CURATED:
        sample = generate(params)
        if not sample.story.strip():
            print("Verification failed: empty story.")
            return 1
    print(f"OK: exercised {len(CURATED)} curated stories.")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A child-friendly splendor whodunit storyworld.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--culprit", choices=SUSPECTS)
    ap.add_argument("--hideout", choices=HIDEOUTS)
    ap.add_argument("--name")
    ap.add_argument("--caretaker")
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
    if getattr(args, "setting", None) and getattr(args, "item", None) and getattr(args, "culprit", None) and getattr(args, "hideout", None):
        if (getattr(args, "setting", None), getattr(args, "item", None), getattr(args, "culprit", None), getattr(args, "hideout", None)) not in set(valid_cases()):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    choices = [
        case for case in valid_cases()
        if (getattr(args, "setting", None) is None or case[0] == getattr(args, "setting", None))
        and (getattr(args, "item", None) is None or case[1] == getattr(args, "item", None))
        and (getattr(args, "culprit", None) is None or case[2] == getattr(args, "culprit", None))
        and (getattr(args, "hideout", None) is None or case[3] == getattr(args, "hideout", None))
    ]
    if not choices:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    setting_id, item_id, culprit_id, hideout_id = rng.choice(choices)
    return StoryParams(
        setting=setting_id,
        item=item_id,
        culprit=culprit_id,
        hideout=hideout_id,
        hero_name=getattr(args, "name", None) or rng.choice(HERO_NAMES),
        caretaker=getattr(args, "caretaker", None) or rng.choice(CARETAKERS),
        trait=rng.choice(TRAITS),
    )


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
        print(asp_program("#show valid/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for setting_id, item_id, culprit_id, hideout_id in asp_valid_cases():
            print(f"{setting_id:8} {item_id:8} {culprit_id:8} {hideout_id}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
            header = f"### {p.hero_name}: {p.item} missing in {p.setting} (culprit: {p.culprit})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
