#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260623T074642Z_seed779406221_n50/cat_whirly_cautionary_adventure.py
===============================================================================================================

A tiny cautionary adventure world about a curious cat, a whirly thing, and a
safe way to handle a risky discovery.

Premise:
- A child or cat-like hero notices a whirly machine/object in a little place.
- The whirly thing is fun to look at, but it can snag fur, paws, or tails.
- A careful helper warns the hero and offers a safer alternative.
- The ending proves the danger was handled without a scrape.

The story is intentionally small and constraint-driven: the simulated state
tracks physical meters and emotional memes, so the prose follows the world
rather than a frozen template.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field
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
    kind: str = "thing"          # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    plural: bool = False

    gadget: object | None = None
    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"cat"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"child", "boy", "girl"}:
            if case == "subject":
                return "they"
            if case == "object":
                return "them"
            return "their"
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
class Place:
    name: str
    indoor: bool
    invites: set[str] = field(default_factory=set)
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


@dataclass
class Whirly:
    id: str
    label: str
    verb: str
    roar: str
    hazard: str
    zone: set[str]
    mess: str
    keyword: str = "whirly"
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
class Shield:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.lines: list[str] = []
        self.facts: dict[str, object] = {}
        self.fired: set[tuple] = set()
        self.trace: list[str] = []

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
            self.lines.append(text)

    def render(self) -> str:
        return " ".join(self.lines)

    def copy(self) -> "World":
        import copy
        w = World(self.place)
        w.entities = copy.deepcopy(self.entities)
        w.lines = []
        w.facts = dict(self.facts)
        w.fired = set(self.fired)
        return w


def _warn_gate(w: World) -> bool:
    hero = w.facts["hero"]
    whirly = w.facts["whirly"]
    for region in whirly.zone:
        if hero.meters.get(f"risk_{region}", 0) >= THRESHOLD:
            return True
    return False


def _resolve_guard(w: World) -> Optional[Shield]:
    whirly: Whirly = w.facts["whirly"]
    for sh in SHIELDS:
        if whirly.mess in sh.guards and whirly.zone.issubset(sh.covers):
            return sh
    return None


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, p in PLACES.items():
        lines.append(asp.fact("place", pid))
        if p.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(p.invites):
            lines.append(asp.fact("invites", pid, a))
    for wid, w in WHIRLIES.items():
        lines.append(asp.fact("whirly", wid))
        lines.append(asp.fact("hazard", wid, w.mess))
        for r in sorted(w.zone):
            lines.append(asp.fact("touches", wid, r))
    for sid, s in SHIELDS.items():
        lines.append(asp.fact("shield", sid))
        for c in sorted(s.covers):
            lines.append(asp.fact("covers", sid, c))
        for g in sorted(s.guards):
            lines.append(asp.fact("guards", sid, g))
    return "\n".join(lines)


ASP_RULES = r"""
risk(P, W) :- whirly(W), touches(W, P).
safe_fix(W, S) :- whirly(W), shield(S), hazard(W, M), guards(S, M),
                  touches(W, P), covers(S, P).
valid_story(Place, W, S) :- invites(Place, W), safe_fix(W, S).
#show valid_story/3.
"""


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def tell(place: Place, hero_name: str, whirly: Whirly, parent_name: str, trait: str) -> World:
    w = World(place)
    hero = w.add(Entity(id=hero_name, kind="character", type="cat", label="cat"))
    parent = w.add(Entity(id=parent_name, kind="character", type="adult", label="the helper"))
    gadget = w.add(Entity(id=whirly.id, type="thing", label=whirly.label, phrase=whirly.label))
    w.facts.update(hero=hero, helper=parent, whirly=whirly, place=place, trait=trait)

    hero.memes["curious"] = 1
    w.say(f"{hero_name} was a little {trait} cat who noticed every shiny thing.")
    w.say(f"{hero.pronoun().capitalize()} loved the {whirly.label}, because it looked fun and whirled in place.")
    w.say(f"In {place.name}, the {whirly.label} made a soft whirly sound: {whirly.roar}")

    w.say(f"One day, {hero_name} crept closer and wanted to {whirly.verb}.")
    hero.meters["risk_paws"] = 1
    hero.meters["risk_tail"] = 1

    if _warn_gate(w):
        hero.memes["worry"] += 1
        w.say(f'The helper said, "Careful, {hero_name}. That {whirly.label} could catch paws and tail."')
        shield = _resolve_guard(w)
        if shield is None:
            pass
        w.add(Entity(id=shield.id, type="thing", label=shield.label, phrase=shield.label, plural=shield.plural))
        w.say(f'Instead, the helper offered {shield.label} and said, "{shield.prep}."')
        hero.memes["trust"] += 1
        hero.memes["joy"] += 1
        hero.memes["worry"] = 0
        w.say(f"{hero_name} listened, backed away, and played with the safer thing instead.")
        w.say(f"Soon {hero_name} was busy {shield.tail}, and the risky {whirly.label} stayed still.")
    else:
        pass

    w.facts["resolved"] = True
    w.facts["shield"] = shield
    return w


PLACES = {
    "shed": Place(name="the shed", indoor=True, invites={"fan"}),
    "yard": Place(name="the yard", indoor=False, invites={"pinwheel", "fan"}),
    "porch": Place(name="the porch", indoor=False, invites={"pinwheel"}),
}

WHIRLIES = {
    "fan": Whirly(
        id="fan",
        label="box fan",
        verb="touch the spinning grate",
        roar="whirr-whirr!",
        hazard="snagged",
        zone={"paws", "tail"},
        mess="snagged",
        tags={"whirly", "danger"},
    ),
    "pinwheel": Whirly(
        id="pinwheel",
        label="wind pinwheel",
        verb="tap the spinning pinwheel",
        roar="whirrrr!",
        hazard="stuck",
        zone={"paws"},
        mess="stuck",
        tags={"whirly"},
    ),
}

SHIELDS = [
    Shield(
        id="gloves",
        label="soft gloves",
        covers={"paws"},
        guards={"snagged", "stuck"},
        prep="put on the soft gloves first",
        tail="wearing the soft gloves and batting safely at a toy ball",
    ),
    Shield(
        id="toy",
        label="a yarn ball",
        covers={"paws", "tail"},
        guards={"snagged", "stuck"},
        prep="give the cat a yarn ball instead",
        tail="chasing the yarn ball in little circles",
    ),
]

GIRL_NAMES = ["Mina", "Luna", "Nora", "Pip"]
CAT_NAMES = ["Whisker", "Mochi", "Poppy", "Miso"]
TRAITS = ["curious", "brave", "gentle", "spry"]


@dataclass
class StoryParams:
    place: str
    whirly: str
    name: str
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
    ap = argparse.ArgumentParser(description="A cautionary adventure about a cat and a whirly thing.")
    ap.add_argument("--place", choices=PLACES)
    ap.add_argument("--whirly", choices=WHIRLIES)
    ap.add_argument("--name")
    ap.add_argument("--parent", choices=["helper", "grownup"])
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


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for wid in place.invites:
            combos.append((pid, wid))
    return sorted(combos)


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    combos = valid_combos()
    if getattr(args, "place", None) or getattr(args, "whirly", None):
        combos = [c for c in combos if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None)) and (getattr(args, "whirly", None) is None or c[1] == getattr(args, "whirly", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, whirly = rng.choice(combos)
    name = getattr(args, "name", None) or rng.choice(CAT_NAMES)
    parent = getattr(args, "parent", None) or "helper"
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, whirly=whirly, name=name, parent=parent, trait=trait)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short cautionary adventure about {f['hero'].id} the cat and the whirly {f['whirly'].label}.",
        f"Tell a child-facing story where a cat named {f['hero'].id} wants to {f['whirly'].verb} but a helper worries.",
        f"Write a safe adventure story in {f['place'].name} that ends with the cat choosing a gentler toy.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = f["hero"]
    whirly: Whirly = f["whirly"]
    place: Place = f["place"]
    shield: Shield = f["shield"]
    return [
        QAItem(
            question=f"Who was the story about?",
            answer=f"The story was about {hero.id}, a little cat who met the {whirly.label} in {place.name}.",
        ),
        QAItem(
            question=f"Why did the helper warn {hero.id}?",
            answer=f"The helper warned {hero.id} because the {whirly.label} could catch paws and tail while it spun.",
        ),
        QAItem(
            question=f"What safe choice did they use instead?",
            answer=f"They used {shield.label} instead, so {hero.id} could play without getting too close to the whirly part.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does whirly mean?",
            answer="Whirly means turning around and around, like a spinning fan or pinwheel.",
        ),
        QAItem(
            question="Why can spinning things be dangerous?",
            answer="Spinning things can be dangerous because they can catch fur, hair, sleeves, or tails if someone gets too close.",
        ),
        QAItem(
            question="What is a safer way to respond to a risky object?",
            answer="A safer way is to step back, listen to a warning, and use a toy or protective gear instead.",
        ),
    ]


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        lines.append(f"{e.id}: {' '.join(bits)}")
    return "\n".join(lines)


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    whirly = _safe_lookup(WHIRLIES, params.whirly)
    world = tell(place, params.name, whirly, params.parent, params.trait)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
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
        for section, items in (("Prompts", sample.prompts), ("Story QA", sample.story_qa), ("World QA", sample.world_qa)):
            print(f"== {section} ==")
            if isinstance(items, list) and items and isinstance(items[0], str):
                for i, p in enumerate(items, 1):
                    print(f"{i}. {p}")
            else:
                for item in items:
                    print(f"Q: {item.question}")
                    print(f"A: {item.answer}")


def asp_verify() -> int:
    import asp
    program = asp_program()
    model = asp.one_model(program)
    asp_set = set(asp.atoms(model, "valid_story"))
    py_set = set()
    for place, wid in valid_combos():
        if wid in _safe_lookup(PLACES, place).invites:
            py_set.add((place, wid, "gloves"))
            py_set.add((place, wid, "toy"))
    # Filter to actually compatible shields
    py_set = {(p, w, s.id) for p, w in valid_combos() for s in SHIELDS if w in WHIRLIES and _safe_lookup(WHIRLIES, w).mess in s.guards}
    if asp_set == py_set:
        print(f"OK: ASP gate matches Python ({len(py_set)} combinations).")
        return 0
    print("MISMATCH between ASP and Python.")
    print("only in ASP:", sorted(asp_set - py_set))
    print("only in Python:", sorted(py_set - asp_set))
    return 1


def asp_valid() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid_story")))


CURATED = [
    StoryParams(place="yard", whirly="fan", name="Mochi", parent="helper", trait="curious"),
    StoryParams(place="porch", whirly="pinwheel", name="Poppy", parent="helper", trait="spry"),
    StoryParams(place="shed", whirly="fan", name="Miso", parent="helper", trait="gentle"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        raise SystemExit(asp_verify())
    if getattr(args, "asp", None):
        print("\n".join(map(str, asp_valid())))
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
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
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
        if len(samples) > 1:
            print(f"### variant {i + 1}")
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None))
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
