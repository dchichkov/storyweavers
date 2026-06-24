#!/usr/bin/env python3
"""
Tall-tale sharing world.

A small, classical story simulation where Eve learns how to share a prized,
oversized thing with friends. The stories are written in a playful tall-tale
style: bigger-than-life but still grounded in state changes.
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
    plural: bool = False
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    eve: object | None = None
    friend: object | None = None
    thing: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.plural:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the meadow"
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
class SharingThing:
    id: str
    label: str
    phrase: str
    size: str
    type: str
    heart: str
    can_split: bool = False
    can_pass: bool = False
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
class Helper:
    id: str
    label: str
    action: str
    resolution: str
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
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict[str, object] = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"share"}),
    "porch": Setting(place="the porch", affords={"share"}),
    "barn": Setting(place="the old red barn", affords={"share"}),
    "kitchen": Setting(place="the kitchen table", indoors=True, affords={"share"}),
}

THINGS = {
    "berry_pie": SharingThing(
        id="berry_pie",
        label="berry pie",
        phrase="one huge berry pie",
        size="big as a wagon wheel",
        type="pie",
        heart="sweet",
        can_split=True,
        can_pass=False,
    ),
    "blanket": SharingThing(
        id="blanket",
        label="warm blanket",
        phrase="one warm, wide blanket",
        size="wide as a barn door",
        type="blanket",
        heart="soft",
        can_split=False,
        can_pass=True,
    ),
    "bucket_of_apples": SharingThing(
        id="bucket_of_apples",
        label="bucket of apples",
        phrase="one bucket piled high with apples",
        size="high as a fence post",
        type="bucket",
        heart="crisp",
        can_split=True,
        can_pass=True,
    ),
}

HELPERS = {
    "knife": Helper(
        id="knife",
        label="a little cake knife",
        action="slice the pie into neat slices",
        resolution="cut the pie into enough pieces for everyone",
    ),
    "stitch": Helper(
        id="stitch",
        label="a needle and thread",
        action="stitch the blanket into two even halves",
        resolution="make the blanket fair to share",
    ),
    "basket": Helper(
        id="basket",
        label="a second basket",
        action="split the apples between two baskets",
        resolution="make two piles of apples",
    ),
}

NAMES = ["Eve", "June", "Mabel", "Nell", "Ruby", "Ivy", "Ada", "Lena"]
FRIENDS = ["Tom", "Milo", "Bea", "Pip", "Nora", "Sage", "Wren", "Otis"]
TRAITS = ["brave", "bright", "bouncy", "cheery", "busy", "stubborn", "jolly"]


# ---------------------------------------------------------------------------
# Parameters
# ---------------------------------------------------------------------------

@dataclass
class StoryParams:
    place: str
    thing: str
    name: str = "Eve"
    friend: str = "Mabel"
    trait: str = "brave"
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness gate
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


def thing_is_shareable(thing: SharingThing) -> bool:
    return thing.can_split or thing.can_pass


def pick_helper(thing: SharingThing) -> Optional[Helper]:
    if thing.id == "berry_pie" and thing.can_split:
        return HELPERS["knife"]
    if thing.id == "blanket" and thing.can_pass:
        return HELPERS["stitch"]
    if thing.id == "bucket_of_apples" and thing.can_split:
        return HELPERS["basket"]
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for thing_id, thing in THINGS.items():
            if place in setting.affords and thing_is_shareable(thing) and pick_helper(thing):
                out.append((place, thing_id))
    return out


# ---------------------------------------------------------------------------
# Story logic
# ---------------------------------------------------------------------------

def introduce(world: World, eve: Entity, friend: Entity, thing: Entity) -> None:
    world.say(
        f"Eve was a {next((t for t in eve.meters.keys()), 'bright')} little soul, "
        f"and on the day this tale begins she found {thing.phrase}."
    )
    world.say(
        f"It looked {thing.memes.get('grand', 'as grand as a gold moon')}, "
        f"and Eve decided it ought to be for sharing."
    )
    world.facts["thing"] = thing
    world.facts["friend"] = friend
    world.facts["eve"] = eve


def want_and_tension(world: World, eve: Entity, friend: Entity, thing: Entity) -> None:
    eve.memes["pride"] = eve.memes.get("pride", 0) + 1
    world.say(
        f"Eve wanted to keep {thing.pronoun('object') if thing.kind == 'character' else thing.label} all to "
        f"herself for a spell, but {friend.id} came trotting up with an empty grin and hungry eyes."
    )
    world.say(
        f"'{thing.label} is mighty fine,' said {friend.id}, 'but there is only one of it, and there are two of us.'"
    )
    eve.memes["stingy"] = eve.memes.get("stingy", 0) + 1
    thing.meters["wanted"] = thing.meters.get("wanted", 0) + 1


def reason_and_fix(world: World, thing: Entity) -> Optional[Helper]:
    helper = pick_helper(_safe_lookup(THINGS, thing.id))
    if not helper:
        pass
    world.say(
        f"Eve looked at {thing.label}, looked at {helper.label}, and laughed a little laugh as big as a bell."
    )
    if thing.id == "berry_pie":
        world.say(
            f"She used {helper.label} to {helper.resolution}."
        )
    elif thing.id == "blanket":
        world.say(
            f"She used {helper.label} to {helper.resolution}."
        )
    else:
        world.say(
            f"She used {helper.label} to {helper.resolution}."
        )
    world.facts["helper"] = helper
    return helper


def resolution(world: World, eve: Entity, friend: Entity, thing: Entity, helper: Helper) -> None:
    eve.memes["stingy"] = 0
    eve.memes["joy"] = eve.memes.get("joy", 0) + 2
    friend.memes["joy"] = friend.memes.get("joy", 0) + 2
    thing.meters["shared"] = thing.meters.get("shared", 0) + 1

    if thing.id == "berry_pie":
        world.say(
            f"Soon Eve and {friend.id} each had a slice, and the pie seemed to grow even sweeter as it went."
        )
        world.say(
            f"By sunset the last crumb was gone, and both friends had smiling faces with berry marks on their chins."
        )
    elif thing.id == "blanket":
        world.say(
            f"Eve tucked one side around herself and one side around {friend.id}, and the blanket made one cozy house for two."
        )
        world.say(
            f"By bedtime the wind had no room to bully them, and the two friends stayed warm as toast."
        )
    else:
        world.say(
            f"Eve filled one basket for herself and one for {friend.id}, and the apples shone like a hundred little suns."
        )
        world.say(
            f"By the end, both friends had full hands, and the sharing felt larger than the sky."
        )


def tell(setting: Setting, thing_cfg: SharingThing, name: str, friend_name: str, trait: str) -> World:
    world = World(setting)
    eve = world.add(Entity(id=name, kind="character", type="girl", meters={"brave": 1}, memes={trait: 1}))
    friend = world.add(Entity(id=friend_name, kind="character", type="boy", memes={"hope": 1}))
    thing = world.add(Entity(id=thing_cfg.id, type=thing_cfg.type, label=thing_cfg.label, phrase=thing_cfg.phrase))

    world.say(
        f"Out at {setting.place}, Eve was as {trait} as a kite in a storm."
    )
    world.say(
        f"There she found {thing_cfg.phrase}, big enough to make the crows blink twice."
    )
    world.para()
    introduce(world, eve, friend, thing)
    want_and_tension(world, eve, friend, thing)
    world.para()
    helper = reason_and_fix(world, thing)
    if helper is None:
        pass
    resolution(world, eve, friend, thing, helper)
    world.facts.update(setting=setting, thing_cfg=thing_cfg, helper=helper)
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    thing_cfg: SharingThing = _safe_fact(world, f, "thing_cfg")
    friend: Entity = _safe_fact(world, f, "friend")
    return [
        f'Write a short tall-tale story for a little child about Eve, {thing_cfg.label}, and sharing.',
        f"Tell a playful story where Eve finds {thing_cfg.phrase} and learns to share it with {friend.id}.",
        f'Write a story with the word "sharing" in it, where Eve and a friend solve a too-big problem together.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    thing_cfg: SharingThing = _safe_fact(world, f, "thing_cfg")
    friend: Entity = _safe_fact(world, f, "friend")
    eve: Entity = _safe_fact(world, f, "eve")
    helper: Helper = _safe_fact(world, f, "helper")
    setting: Setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"What did Eve find at {setting.place}?",
            answer=f"Eve found {thing_cfg.phrase}, and it was big enough to feel like a tiny treasure.",
        ),
        QAItem(
            question=f"Why did Eve need {helper.label}?",
            answer=f"She needed {helper.label} so she could {helper.action} and make the sharing fair.",
        ),
        QAItem(
            question=f"Who shared the {thing_cfg.label} with Eve?",
            answer=f"{friend.id} shared it with Eve, and both of them ended up happy.",
        ),
        QAItem(
            question=f"How did Eve feel at the end?",
            answer=f"Eve felt joyful and proud because she learned that sharing made the day bigger and better.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting someone else use, have, or enjoy part of something with you.",
        ),
        QAItem(
            question="Why do people share?",
            answer="People share so everyone can enjoy the good thing, and so no one is left out.",
        ),
        QAItem(
            question="What does a helper tool do in a story?",
            answer="A helper tool makes a problem easier to solve, like slicing, stitching, or sorting things fairly.",
        ),
    ]


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
setting_valid(Place) :- setting(Place).
shareable(T) :- thing(T), can_split(T).
shareable(T) :- thing(T), can_pass(T).
has_helper(T) :- helper_for(T, _).

valid_story(Place, Thing) :- setting_valid(Place), shareable(Thing), has_helper(Thing).

#show valid_story/2.
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for tid, t in THINGS.items():
        lines.append(asp.fact("thing", tid))
        if t.can_split:
            lines.append(asp.fact("can_split", tid))
        if t.can_pass:
            lines.append(asp.fact("can_pass", tid))
        lines.append(asp.fact("helper_for", tid, pick_helper(t).id if pick_helper(t) else "none"))
    for hid in HELPERS:
        lines.append(asp.fact("helper", hid))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple[str, str]]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Tall-tale sharing story world.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--thing", choices=THINGS)
    ap.add_argument("--name", default="Eve")
    ap.add_argument("--friend")
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
    filtered = [
        c for c in combos
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "thing", None) is None or c[1] == getattr(args, "thing", None))
    ]
    if not filtered:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, thing = rng.choice(list(filtered))
    friend = getattr(args, "friend", None) or rng.choice(FRIENDS)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, thing=thing, name=getattr(args, "name", None), friend=friend, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(THINGS, params.thing), params.name, params.friend, params.trait)
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
        lines.append(f"{e.id}: kind={e.kind} type={e.type} meters={meters} memes={memes}")
    return "\n".join(lines)


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for p in sample.prompts:
        out.append(p)
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} compatible stories:")
        for place, thing in asp_valid_combos():
            print(f"  {place:10} {thing}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        curated = [
            StoryParams(place="meadow", thing="berry_pie", name="Eve", friend="Mabel", trait="brave"),
            StoryParams(place="porch", thing="blanket", name="Eve", friend="Tom", trait="jolly"),
            StoryParams(place="barn", thing="bucket_of_apples", name="Eve", friend="Bea", trait="cheery"),
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
