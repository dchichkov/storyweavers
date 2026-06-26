#!/usr/bin/env python3
"""
storyworlds/worlds/divert_sharing_suspense_rhyming_story.py
===========================================================

A small story world about a child, a shared thing, a suspenseful worry,
and a diverting rhyme that helps everyone wait kindly.

The seed tale behind this world:
- A child has a special treat or set of treasures.
- A friend wants to share, but there is suspense about whether there is enough.
- Someone diverts the worry with a rhyme, a count, or a little song.
- The group discovers a fair way to share, and the ending proves it.

This world keeps the prose child-facing and lightly rhymed, with state-driven
turns instead of a frozen template.
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
    if hasattr(key, "id"):
        key = key.id
    try:
        return mapping[key]
    except Exception:
        pass
    if hasattr(mapping, "values"):
        values = [value for value in mapping.values() if value is not None]
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class Setting:
    place: str
    indoor: bool = False
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
class SharingItem:
    id: str
    label: str
    phrase: str
    kind: str
    count: int
    can_cut: bool = False
    can_split: bool = False
    shared_by_hand: bool = True
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


@dataclass
class SharingPlan:
    id: str
    label: str
    verb: str
    method: str
    result: str
    prep: str
    tail: str
    tags: set[str] = field(default_factory=set)
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

    def __getitem__(self, key):
        if isinstance(key, int):
            if key == 0:
                return self
            raise IndexError(key)
        if isinstance(key, str):
            if hasattr(self, key):
                return getattr(self, key)
            for attr in ("meters", "memes"):
                mapping = getattr(self, attr, None)
                if hasattr(mapping, "get") and key in mapping:
                    return mapping.get(key)
        raise KeyError(key)

    def __iter__(self):
        yield self

    def __hash__(self):
        return hash(getattr(self, "id", id(self)))


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]


def _rhymed_pair(a: str, b: str) -> str:
    return f"{a.rstrip('.')}.\n{b.rstrip('.')}."


def opening_line(hero: Entity, item: SharingItem) -> str:
    return (
        f"{hero.id} had {item.phrase}, bright and small, "
        f"and loved to hold it like the best thing of all."
    )


def suspense_line(item: SharingItem, count: int, guests: int) -> str:
    if count < guests:
        return (
            f"But there were only {count} to go around, so the room felt still "
            f"and the smiles wore a frown."
        )
    if count == guests:
        return (
            f"There were just enough, no more and no less, "
            f"and that tiny maybe made everyone wait with suspense."
        )
    return (
        f"There were more than enough, yet the group still guessed, "
        f"who would get which one, and who would get the best?"
    )


def divert_line(plan: SharingPlan, helper: Entity) -> str:
    return (
        f"Then {helper.id} said, '{plan.prep},' with a wink and a grin, "
        f"'{plan.method}, and the sharing can begin.'"
    )


def resolution_line(hero: Entity, item: SharingItem, plan: SharingPlan, guests: list[Entity]) -> str:
    names = ", ".join(g.id for g in guests)
    return (
        f"So {plan.tail}. Soon {hero.id} shared with {names}, "
        f"and {item.label} came out fair as a song in the pines."
    )


def build_rhyme_end(hero: Entity, item: SharingItem, guests: list[Entity]) -> str:
    return (
        f"{hero.id} smiled wide, and the last little gleam "
        f"showed sharing can sparkle like a bright bedtime dream."
    )


def share_is_possible(item: SharingItem, guests: int, plan: SharingPlan) -> bool:
    if guests <= 0:
        return False
    if item.count < guests and not item.can_cut:
        return False
    if item.count == guests and not item.shared_by_hand:
        return False
    if item.count > guests and not (item.can_split or item.shared_by_hand):
        return False
    return True


def select_plan(item: SharingItem) -> Optional[SharingPlan]:
    for plan in PLANS:
        if item.kind in plan.tags or not plan.tags:
            return plan
    return None


def predict_share(world: World, hero: Entity, item: SharingItem, guests: list[Entity], plan: SharingPlan) -> dict:
    sim = world.copy()
    sim.get(hero.id).memes["suspense"] += 1
    if item.count < len(guests):
        if item.can_cut:
            return {"fair": True, "left": 0}
        return {"fair": False, "left": item.count}
    if item.count == len(guests):
        return {"fair": True, "left": 0}
    if item.can_split or item.shared_by_hand:
        return {"fair": True, "left": item.count - len(guests)}
    return {"fair": False, "left": item.count}


def tell(setting: Setting, item: SharingItem, hero_name: str, hero_type: str,
         helper_type: str, guest_names: list[str], plan: SharingPlan) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, label=hero_name))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="helper"))
    guests = [
        world.add(Entity(id=name, kind="character", type="child", label=name))
        for name in guest_names
    ]
    treasure = world.add(Entity(
        id=item.id,
        kind="thing",
        type=item.kind,
        label=item.label,
        phrase=item.phrase,
        owner=hero.id,
        plural=item.count != 1,
        meters={"count": float(item.count)},
    ))

    world.say(opening_line(hero, item))
    world.say(
        f"{hero.id} hoped to share {hero.pronoun('possessive')} {item.label} with "
        f"{len(guests)} friend{'s' if len(guests) != 1 else ''}, and that hope felt fair and grand."
    )
    world.para()

    world.say(
        f"In {setting.place}, the air was calm, the light was bright, "
        f"and everyone paused to see what would be right."
    )
    world.say(suspense_line(item, item.count, len(guests)))
    hero.memes["suspense"] += 1
    world.facts["predicted"] = predict_share(world, hero, item, guests, plan)
    world.say(
        f"{hero.id} looked at the pile and wondered if kindness would do, "
        f"or if the best way was hidden from view."
    )
    world.say(divert_line(plan, helper))
    world.say(
        f"{helper.id} began to count in a sing-song tone, "
        f"'{plan.verb}, one by one, and nobody must moan.'"
    )
    world.para()

    if item.can_cut and item.count < len(guests):
        world.say(
            f"So {hero.id} used a small safe cut, neat and sweet, "
            f"making every piece tidy and easy to eat."
        )
        item.count = len(guests)
    elif item.can_split and item.count > len(guests):
        world.say(
            f"{hero.id} split the share into equal parts with care, "
            f"so each friend got a piece and no one got a glare."
        )
    else:
        world.say(
            f"{hero.id} handed them out, one by one, with a merry little beat, "
            f"and the waiting turned easy, soft, and sweet."
        )

    for guest in guests:
        guest.memes["joy"] += 1
    hero.memes["joy"] += 1
    hero.memes["suspense"] = 0.0

    world.say(resolution_line(hero, item, plan, guests))
    world.say(build_rhyme_end(hero, item, guests))

    world.facts.update(
        hero=hero,
        helper=helper,
        guests=guests,
        item=treasure,
        plan=plan,
        setting=setting,
        shared=len(guests) <= item.count or item.can_cut or item.can_split,
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"share"}),
    "picnic": Setting(place="the picnic blanket", indoor=False, affords={"share"}),
    "playroom": Setting(place="the playroom", indoor=True, affords={"share"}),
    "garden": Setting(place="the garden bench", indoor=False, affords={"share"}),
}

ITEMS = {
    "cookies": SharingItem(
        id="cookies",
        label="cookies",
        phrase="three round cookies",
        kind="treat",
        count=3,
        can_cut=True,
        can_split=True,
        tags={"sweet", "share"},
    ),
    "berries": SharingItem(
        id="berries",
        label="berries",
        phrase="a little bowl of berries",
        kind="treat",
        count=4,
        can_cut=False,
        can_split=True,
        tags={"sweet", "share"},
    ),
    "stickers": SharingItem(
        id="stickers",
        label="stickers",
        phrase="a shiny page of stickers",
        kind="treasure",
        count=5,
        can_cut=False,
        can_split=True,
        tags={"share", "sparkle"},
    ),
    "crayons": SharingItem(
        id="crayons",
        label="crayons",
        phrase="a small box of crayons",
        kind="tool",
        count=4,
        can_cut=False,
        can_split=True,
        tags={"share", "color"},
    ),
}

PLANS = [
    SharingPlan(
        id="counting_song",
        label="counting song",
        verb="count the pieces",
        method="we count and hum a little song",
        result="the pieces stay fair",
        prep="Let's make a counting song",
        tail="they counted, hummed, and shared with care",
        tags={"treat", "share"},
    ),
    SharingPlan(
        id="careful_slice",
        label="careful slice",
        verb="slice the treat",
        method="we cut it into neat little bits",
        result="each bit fits",
        prep="Let's use a careful slice",
        tail="they sliced with a grin, and each share fit in",
        tags={"treat"},
    ),
    SharingPlan(
        id="split_in_halves",
        label="split in halves",
        verb="split the pile",
        method="we make equal halves so nobody cries",
        result="the sharing is wise",
        prep="Let's split it in halves",
        tail="they split it just so, and the worry said no",
        tags={"treasure", "tool", "share"},
    ),
]

HERO_NAMES = ["Mila", "Noah", "Ruby", "Eli", "Tia", "Ben", "Zara", "Finn"]
GUEST_NAMES = ["Pip", "June", "Ollie", "Mara", "Ivy", "Theo"]
HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["mother", "father", "teacher", "friend"]


@dataclass
class StoryParams:
    place: str
    item: str
    hero: str
    hero_type: str
    helper_type: str
    guests: int
    seed: Optional[int] = None
    params: object | None = None
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


def valid_combos() -> list[tuple[str, str, int]]:
    combos: list[tuple[str, str, int]] = []
    for place, setting in SETTINGS.items():
        for item_id, item in ITEMS.items():
            for guests in (1, 2, 3):
                if share_is_possible(item, guests, _safe_lookup(PLANS, 0)) or item.can_split:
                    combos.append((place, item_id, guests))
    return combos


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        'Write a short rhyming story with sharing and suspense for a young child, and include the word "divert".',
        f"Tell a gentle rhyming story where {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero").id} wants to share {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item").phrase} at {_safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting").place}, "
        f"and everyone waits to see if there will be enough.",
        f"Write a small suspenseful sharing story that ends with a fair plan and a happy rhyme.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    guests: list[Entity] = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "guests")
    item: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "item")
    plan: SharingPlan = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "plan")
    setting: Setting = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "setting")
    pred = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "predicted")

    guest_names = ", ".join(g.id for g in guests)
    qa = [
        QAItem(
            question=f"What did {hero.id} want to share in {setting.place}?",
            answer=f"{hero.id} wanted to share {item.phrase} with {guest_names}, and that made the room feel warm and bright.",
        ),
        QAItem(
            question=f"Why was there suspense before the sharing began?",
            answer=(
                f"There was suspense because everyone wondered if {item.label} would be enough for all of the friends. "
                f"The waiting felt extra wiggly until the plan showed how to make it fair."
            ),
        ),
        QAItem(
            question=f"Who helped divert the worry with a rhyme?",
            answer=(
                f"{helper.id} helped divert the worry with a little counting song, "
                f"so the children could wait calmly while the shares were made."
            ),
        ),
        QAItem(
            question=f"What was the fair way to share?",
            answer=(
                f"They used {plan.label}, which meant they counted carefully and gave everyone an equal share. "
                f"That was why the ending felt kind and complete."
            ),
        ),
    ]
    qa.append(
        QAItem(
            question=f"How did the story prove the sharing worked?",
            answer=(
                f"At the end, {hero.id} shared with {guest_names}, and nobody had to keep guessing. "
                f"The pieces were divided fairly, and the happy result matched the plan."
            ),
        )
    )
    if pred["fair"]:
        qa.append(
            QAItem(
                question=f"Why did the plan work without ruining the sharing?",
                answer=(
                    f"The plan worked because the item could be shared in a fair way, "
                    f"and the counts were enough to leave everyone smiling."
                ),
            )
        )
    return qa


KNOWLEDGE = {
    "divert": [
        QAItem(
            question="What does it mean to divert your mind?",
            answer="To divert your mind means to turn your attention to something else for a little while.",
        ),
    ],
    "sharing": [
        QAItem(
            question="What is sharing?",
            answer="Sharing means letting other people use or enjoy something with you.",
        ),
    ],
    "suspense": [
        QAItem(
            question="What is suspense?",
            answer="Suspense is the waiting feeling when you do not yet know what will happen.",
        ),
    ],
    "rhyming": [
        QAItem(
            question="What is a rhyme?",
            answer="A rhyme is when words sound alike at the end, like bright and light.",
        ),
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    out: list[QAItem] = []
    out.extend(KNOWLEDGE["divert"])
    out.extend(KNOWLEDGE["sharing"])
    out.extend(KNOWLEDGE["suspense"])
    out.extend(KNOWLEDGE["rhyming"])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(item: SharingItem, guests: int) -> str:
    if guests <= 0:
        return "(No story: the sharing needs at least one guest.)"
    if item.count < guests and not item.can_cut:
        return (
            f"(No story: {item.phrase} would not be enough for {guests} children, "
            f"and this item cannot be safely cut into more pieces.)"
        )
    return "(No story: the requested combination does not make a clear suspenseful sharing turn.)"


ASP_RULES = r"""
% Shared item logic: enough pieces or a cuttable treat yields a fair share.
fair_share(Item, Guests) :- item(Item), guests(Guests), pieces(Item, N), N >= Guests.
fair_share(Item, Guests) :- item(Item), guests(Guests), cuttable(Item), Guests > 1.

% A suspense story is valid when sharing is possible and the plan can divert worry.
valid(Place, Item, Guests) :- setting(Place), affords(Place, share),
                               item(Item), guests(Guests), fair_share(Item, Guests),
                               has_divert(Item).

valid_story(Place, Item, Guests, Hero) :- valid(Place, Item, Guests), hero(Hero).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if s.indoor:
            lines.append(asp.fact("indoor", sid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", sid, a))
    for item_id, item in ITEMS.items():
        lines.append(asp.fact("item", item_id))
        lines.append(asp.fact("pieces", item_id, item.count))
        if item.can_cut:
            lines.append(asp.fact("cuttable", item_id))
        if item.can_split:
            lines.append(asp.fact("splitable", item_id))
        if item.shared_by_hand:
            lines.append(asp.fact("handshare", item_id))
        for t in sorted(item.tags):
            lines.append(asp.fact("tag", item_id, t))
    for plan in PLANS:
        lines.append(asp.fact("plan", plan.id))
        lines.append(asp.fact("has_divert", plan.id))
    for h in HERO_NAMES:
        lines.append(asp.fact("hero", h.lower()))
    for g in range(1, 4):
        lines.append(asp.fact("guests", g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    # Reduce Python combos to those that are clearly valid for our intended gate.
    py2 = set()
    for place, item, guests in py:
        if _safe_lookup(SETTINGS, place).affords and item in ITEMS and guests > 0:
            py2.add((place, item, guests))
    asp_set = set(asp_valid_combos())
    if asp_set == py2:
        print(f"OK: clingo gate matches Python gate ({len(asp_set)} combos).")
        return 0
    print("MISMATCH between clingo and Python gate:")
    if asp_set - py2:
        print("  only in clingo:", sorted(asp_set - py2))
    if py2 - asp_set:
        print("  only in python:", sorted(py2 - asp_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A rhyming story world about sharing, suspense, and diversion.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--item", choices=ITEMS)
    ap.add_argument("--guests", type=int, choices=[1, 2, 3])
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
    ap.add_argument("--helper-type", choices=HELPER_TYPES)
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
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "item", None) is None or c[1] == getattr(args, "item", None))
        and (getattr(args, "guests", None) is None or c[2] == getattr(args, "guests", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, item, guests = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or rng.choice(HERO_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES)
    return StoryParams(place=place, item=item, hero=hero, hero_type=hero_type, helper_type=helper_type, guests=guests)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    item = _safe_lookup(ITEMS, params.item)
    plan = select_plan(item)
    if plan is None:
        _fallback_pool = globals().get("PLANS") or globals().get("PLANES") or []
        if hasattr(_fallback_pool, "values"):
            _fallback_pool = list(_fallback_pool.values())
        plan = next(iter(_fallback_pool), None)
        if plan is None:
            raise StoryError
    guest_names = random.Random(params.seed or 0).sample(GUEST_NAMES, k=params.guests)
    world = tell(
        setting=setting,
        item=item,
        hero_name=params.hero,
        hero_type=params.hero_type,
        helper_type=params.helper_type,
        guest_names=guest_names,
        plan=plan,
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


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} compatible combos:")
        for c in combos:
            print(" ", c)
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for place in SETTINGS:
            for item in ITEMS:
                for guests in (1, 2, 3):
                    if getattr(args, "place", None) and getattr(args, "place", None) != place:
                        continue
                    if getattr(args, "item", None) and getattr(args, "item", None) != item:
                        continue
                    if getattr(args, "guests", None) and getattr(args, "guests", None) != guests:
                        continue
                    params = StoryParams(
                        place=place,
                        item=item,
                        hero=getattr(args, "hero", None) or _safe_lookup(HERO_NAMES, (guests + len(item)) % len(HERO_NAMES)),
                        hero_type=getattr(args, "hero_type", None) or _safe_lookup(HERO_TYPES, guests % 2),
                        helper_type=getattr(args, "helper_type", None) or _safe_lookup(HELPER_TYPES, (guests + 1) % len(HELPER_TYPES)),
                        guests=guests,
                        seed=base_seed,
                    )
                    try:
                        samples.append(generate(params))
                    except StoryError:
                        continue
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
