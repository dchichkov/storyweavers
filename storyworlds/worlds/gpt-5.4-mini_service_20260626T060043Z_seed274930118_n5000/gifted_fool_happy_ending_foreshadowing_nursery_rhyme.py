#!/usr/bin/env python3
"""
Standalone storyworld: gifted fool, foreshadowing, happy ending, nursery-rhyme style.

A small, classical simulation about a clever-looking fool who is gifted with
something useful, but must learn to use it kindly and carefully. The story is
built from a stateful world model so the ending changes because the world
changes.
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

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def __post_init__(self) -> None:
        for k in ["care", "wear", "share", "pride", "conflict", "joy", "wisdom", "giftedness", "foolishness"]:
            self.meters.setdefault(k, 0.0)
            self.memes.setdefault(k, 0.0)

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
class Place:
    name: str
    indoors: bool = True
    features: set[str] = field(default_factory=set)
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
class Gift:
    id: str
    label: str
    phrase: str
    kind: str
    fragile: bool = False
    helps: set[str] = field(default_factory=set)
    risk: set[str] = field(default_factory=set)
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
class StoryParams:
    place: str
    gift: str
    hero_name: str
    hero_type: str
    helper_name: str
    helper_type: str
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.events: list[str] = []
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
            self.events.append(text)

    def render(self) -> str:
        return " ".join(self.events)

    def copy(self) -> "World":
        import copy

        clone = World(self.place)
        clone.entities = copy.deepcopy(self.entities)
        clone.events = []
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _narrate_nursery(lines: list[str]) -> str:
    return " ".join(lines)


# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------

PLACES = {
    "village": Place("the village green", indoors=False, features={"bells", "market", "grass"}),
    "cottage": Place("the little cottage", indoors=True, features={"hearth", "stool", "shelf"}),
    "mill": Place("the old mill", indoors=True, features={"wheel", "flour", "loft"}),
}

GIFTS = {
    "lantern": Gift(
        id="lantern",
        label="lantern",
        phrase="a bright little lantern",
        kind="light",
        fragile=True,
        helps={"dark"},
        risk={"rough"},
    ),
    "seedbag": Gift(
        id="seedbag",
        label="seed bag",
        phrase="a small bag of silver seeds",
        kind="seeds",
        fragile=False,
        helps={"garden"},
        risk={"spill"},
    ),
    "bell": Gift(
        id="bell",
        label="little bell",
        phrase="a tiny silver bell on a red string",
        kind="sound",
        fragile=False,
        helps={"signal"},
        risk={"drop"},
    ),
}

HEROES = [
    ("Pip", "boy"),
    ("Mina", "girl"),
    ("Nell", "girl"),
    ("Toby", "boy"),
]

HELPERS = [
    ("Gran", "woman"),
    ("Papa", "man"),
    ("Aunt May", "woman"),
    ("Uncle Tom", "man"),
]

TRAITS = ["gifted", "quick", "bright", "small", "cheery"]


def story_setup_lines(hero: Entity, helper: Entity, gift: Gift, place: Place) -> list[str]:
    return [
        f"Little {hero.id} was a gifted fool with a grin so wide it almost twinkled.",
        f"{hero.id} loved {gift.phrase} and carried {(getattr(gift, 'it')() if callable(getattr(gift, 'it', None)) else getattr(gift, 'it', 'it'))} everywhere, though {hero.pronoun('possessive')} feet were often in a muddle.",
        f"At {place.name}, {helper.id} kept watch, and everyone knew a kind heart can guide a funny head.",
    ]


def foreshadow_lines(hero: Entity, gift: Gift, place: Place) -> list[str]:
    if gift.fragile:
        return [
            f"But a whisper went through the beams: if {hero.id} tripped in the dim, the lantern might dim as well.",
            f"The floor at {place.name} had one loose board that liked to tap and tease.",
        ]
    if gift.kind == "seeds":
        return [
            f"Yet the little bag jingled softly, and each jingle warned that a careless spin could spill a silver trail.",
            f"At {place.name}, the wind knew the cracks and could sneak through like a cat.",
        ]
    return [
        f"Still, the bell could slip from a grasping hand and tumble under a stool.",
        f"One clink on stone was enough to make the day uneasy.",
    ]


def resolve_lines(hero: Entity, helper: Entity, gift: Gift, place: Place) -> list[str]:
    return [
        f"{helper.id} laughed, then showed {hero.id} the gentle way: hold {(getattr(gift, 'it')() if callable(getattr(gift, 'it', None)) else getattr(gift, 'it', 'it'))} with both hands and take three tiny steps.",
        f"{hero.id} tried again, slow as a snail, and the gifted fool proved not so foolish after all.",
        f"At {place.name}, the little gift did its good work, and the two of them sang a nursery tune all the way home.",
    ]


def build_world(params: StoryParams) -> World:
    place = _safe_lookup(PLACES, params.place)
    gift = _safe_lookup(GIFTS, params.gift)
    world = World(place)

    hero = world.add(Entity(id=params.hero_name, kind="character", type=params.hero_type))
    helper = world.add(Entity(id=params.helper_name, kind="character", type=params.helper_type))
    item = world.add(Entity(
        id=gift.id,
        type=gift.kind,
        label=gift.label,
        phrase=gift.phrase,
        owner=hero.id,
        caretaker=helper.id,
    ))
    item.worn_by = hero.id

    hero.memes["giftedness"] += 1
    hero.memes["foolishness"] += 1
    hero.memes["joy"] += 1

    world.say(_narrate_nursery(story_setup_lines(hero, helper, gift, place)))
    world.say(_narrate_nursery(foreshadow_lines(hero, gift, place)))

    # A small stateful turn: the hero mishandles the gift.
    if gift.fragile:
        hero.meters["care"] += 1
        hero.memes["conflict"] += 1
        world.say(f"{hero.id} nearly bumped the lantern on the sill, and the room held its breath.")
    elif gift.kind == "seeds":
        hero.meters["care"] += 1
        hero.memes["conflict"] += 1
        world.say(f"{hero.id} gave the bag a foolish shake, and a few seeds pattered to the floor.")
    else:
        hero.meters["care"] += 1
        hero.memes["conflict"] += 1
        world.say(f"{hero.id} nearly let the bell slip, and it gave one worried little clink.")

    # Happy ending: helper guides the gifted fool into careful use.
    hero.memes["joy"] += 1
    hero.memes["conflict"] = 0.0
    hero.memes["wisdom"] += 1
    world.say(_narrate_nursery(resolve_lines(hero, helper, gift, place)))

    world.facts.update(
        hero=hero,
        helper=helper,
        gift=item,
        place=place,
        gift_def=gift,
        resolved=True,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------

def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    gift: Gift = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gift_def")
    return [
        f"Write a nursery-rhyme style story about {hero.id}, a gifted fool, and {gift.phrase}.",
        f"Tell a short gentle tale where {helper.id} helps {hero.id} use {gift.label} carefully.",
        f"Make a child-friendly story with foreshadowing, a small mistake, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "hero")
    helper: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "helper")
    gift: Entity = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gift")
    place: Place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "place")
    gift_def: Gift = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), f, "gift_def")

    return [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about little {hero.id}, a gifted fool who carried {gift_def.phrase} to {place.name}.",
        ),
        QAItem(
            question=f"What warning was hinted at before the mistake?",
            answer=f"The story hinted that {gift_def.label} might be dropped or damaged if {hero.id} was careless at {place.name}.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily when {helper.id} showed {hero.id} a careful way to hold {gift.label}, and the gift was used well.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    gift: Gift = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "gift_def")
    place: Place = _safe_fact((globals().get("world") or locals().get("world") or locals().get("mw") or locals().get("w")), world.facts, "place")
    items = [
        QAItem(
            question="What is a foreshadowing clue in a story?",
            answer="A foreshadowing clue is a small hint that tells readers something important may happen later.",
        ),
        QAItem(
            question="What makes a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters finish in a good place.",
        ),
        QAItem(
            question=f"What is {gift.label} usually for?",
            answer=f"A {gift.label} is used for {gift.kind} things, and in this story it helped the hero in a careful way.",
        ),
        QAItem(
            question="What is a village green?",
            answer="A village green is an open grassy place in a town where people can walk, gather, or play.",
        ),
    ]
    return items


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


def dump_trace(world: World) -> str:
    lines = ["--- trace ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"{e.id}: {e.type} " + " ".join(bits))
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------

ASP_RULES = r"""
#show valid/2.
#show foreshadow/2.
#show happy/1.

valid(H, G) :- hero(H), gift(G), helps(G,_).

foreshadow(H, G) :- hero(H), gift(G), fragile(G).
foreshadow(H, G) :- hero(H), gift(G), risk(G,_).

happy(H) :- valid(H,G), hero(H), gift(G).
happy(H) :- hero(H), gift(G), helps(G,_).
"""


def asp_facts() -> str:
    import storyworlds.asp as asp

    lines: list[str] = []
    for name, place in PLACES.items():
        lines.append(asp.fact("place", name))
        if place.indoors:
            lines.append(asp.fact("indoors", name))
        for feat in sorted(place.features):
            lines.append(asp.fact("feature", name, feat))
    for gid, gift in GIFTS.items():
        lines.append(asp.fact("gift", gid))
        lines.append(asp.fact("kind", gid, gift.kind))
        if gift.fragile:
            lines.append(asp.fact("fragile", gid))
        for h in sorted(gift.helps):
            lines.append(asp.fact("helps", gid, h))
        for r in sorted(gift.risk):
            lines.append(asp.fact("risk", gid, r))
    # Generic hero constants for parity checks
    for h, _t in HEROES:
        lines.append(asp.fact("hero", h))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_pairs() -> list[tuple[str, str]]:
    import storyworlds.asp as asp

    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set((h, g) for h, g in valid_pairs())
    cl = set(asp_valid_pairs())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} valid pairs).")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in ASP:", sorted(cl - py))
    print(" only in Python:", sorted(py - cl))
    return 1


# ---------------------------------------------------------------------------
# Reasonableness gate
# ---------------------------------------------------------------------------

def valid_pairs() -> list[tuple[str, str]]:
    pairs = []
    for h, _ in HEROES:
        for g in GIFTS:
            pairs.append((h, g))
    return pairs


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "gift", None) and getattr(args, "gift", None) not in GIFTS:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "place", None) and getattr(args, "place", None) not in PLACES:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place = getattr(args, "place", None) or rng.choice(list(PLACES))
    gift = getattr(args, "gift", None) or rng.choice(list(GIFTS))
    hero_name, hero_type = (getattr(args, "hero_name", None), getattr(args, "hero_type", None)) if getattr(args, "hero_name", None) and getattr(args, "hero_type", None) else rng.choice(HEROES)
    helper_name, helper_type = rng.choice(HELPERS)

    if gift == "lantern" and place == "village":
        pass

    return StoryParams(
        place=place,
        gift=gift,
        hero_name=hero_name,
        hero_type=hero_type,
        helper_name=helper_name,
        helper_type=helper_type,
    )


# ---------------------------------------------------------------------------
# Generation
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Gifted fool storyworld in a nursery-rhyme style.")
    ap.add_argument("--place", choices=list(PLACES))
    ap.add_argument("--gift", choices=list(GIFTS))
    ap.add_argument("--hero-name")
    ap.add_argument("--hero-type", choices=["boy", "girl"])
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


CURATED = [
    StoryParams(place="village", gift="lantern", hero_name="Pip", hero_type="boy", helper_name="Gran", helper_type="woman"),
    StoryParams(place="cottage", gift="seedbag", hero_name="Mina", hero_type="girl", helper_name="Papa", helper_type="man"),
    StoryParams(place="mill", gift="bell", hero_name="Toby", hero_type="boy", helper_name="Aunt May", helper_type="woman"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2.\n#show foreshadow/2.\n#show happy/1."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(f"{a} {b}" for a, b in asp_valid_pairs()))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

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
            header = f"### {p.hero_name} / {p.gift} / {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
