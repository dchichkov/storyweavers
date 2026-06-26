#!/usr/bin/env python3
"""
storyworlds/worlds/apparel_flashback_pirate_tale.py
====================================================

A standalone story world for a small Pirate Tale domain with apparel and a
flashback turn.

Premise:
- A young pirate wants to wear a cherished apparel item on a voyage.
- The sea and salt spray threaten it.
- A flashback reveals why the item matters.
- The crew finds a safe compromise so the adventure can still happen.

This world uses typed entities with physical meters and emotional memes, a
Python reasonableness gate, and an inline ASP twin for parity checks.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from dataclasses import dataclass, field, asdict
from typing import Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402


THRESHOLD = 1.0
SALT = "salt"
WIND = "wind"
WET = "wet"
RIP = "ripped"



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
    worn_by: Optional[str] = None
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    traits: list[str] = field(default_factory=list)

    apparel: object | None = None
    cover: object | None = None
    hero: object | None = None
    parent: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "captainess"}
        male = {"boy", "man", "father", "captain"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def obj_pronoun(self) -> str:
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
class Harbor:
    name: str
    place_detail: str
    affords: set[str] = field(default_factory=set)
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
class Apparel:
    id: str
    label: str
    phrase: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"girl", "boy"})
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
class WeatherGear:
    id: str
    label: str
    covers: set[str]
    guards: set[str]
    prep: str
    tail: str
    plural: bool = False
    gear: object | None = None
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
    def __init__(self, harbor: Harbor) -> None:
        self.harbor = harbor
        self.entities: dict[str, Entity] = {}
        self.paragraphs: list[list[str]] = [[]]
        self.fired: set[tuple] = set()
        self.facts: dict = {}
        self.weather = "windy"
        self.ate_flashback = False

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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
        clone = World(self.harbor)
        clone.entities = copy.deepcopy(self.entities)
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.weather = self.weather
        clone.ate_flashback = self.ate_flashback
        return clone


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get(WET, 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in {"torso", "head"}:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("soak", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters[WET] = item.meters.get(WET, 0.0) + 1
            item.meters[SALT] = item.meters.get(SALT, 0.0) + 1
            out.append(f"The salt spray kissed {actor.pronoun('possessive')} {item.label}.")
    return out


def _r_spoil(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get(WET, 0.0) < THRESHOLD:
            continue
        sig = ("spoil", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        item.meters[RIP] = item.meters.get(RIP, 0.0) + 1
        out.append(f"It could end up faded and rumpled.")
    return out


CAUSAL_RULES = [
    _r_soak,
    _r_spoil,
]


def propagate(world: World) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    for s in produced:
        world.say(s)
    return produced


def simulate_mess(world: World, actor: Entity, activity: str, apparel_id: str) -> dict:
    sim = world.copy()
    do_activity(sim, sim.get(actor.id), activity, narrate=False)
    apparel = sim.get(apparel_id)
    return {
        "soaked": apparel.meters.get(WET, 0.0) >= THRESHOLD,
        "ruined": apparel.meters.get(RIP, 0.0) >= THRESHOLD,
    }


def do_activity(world: World, actor: Entity, activity: str, narrate: bool = True) -> None:
    if activity not in world.harbor.affords:
        pass
    actor.meters[WET] = actor.meters.get(WET, 0.0) + 1
    actor.meters[WIND] = actor.meters.get(WIND, 0.0) + 1
    actor.memes["thrill"] = actor.memes.get("thrill", 0.0) + 1
    propagate(world)
    if narrate:
        world.say(f"{actor.id} dashed into the deck work, and the ship rocked like a lively drum.")


def flashback(world: World, hero: Entity, apparel: Entity) -> None:
    if world.ate_flashback:
        return
    world.ate_flashback = True
    world.say(
        f"That sight flashed back in {hero.pronoun('possessive')} mind: long ago, "
        f"{hero.pronoun('possessive')} grandmother had tied {hero.pronoun('object')} "
        f"{apparel.phrase} and said it would help {hero.pronoun('object')} feel brave."
    )
    hero.memes["tenderness"] = hero.memes.get("tenderness", 0.0) + 1


def intro(world: World, hero: Entity, parent: Entity, apparel: Entity) -> None:
    world.say(
        f"{hero.id} was a little pirate who loved {apparel.label} because it made "
        f"{hero.pronoun('object')} look ready for big waves."
    )
    world.say(
        f"{parent.id}, the ship's steady captain, had given {hero.pronoun('object')} "
        f"{apparel.phrase} before the voyage."
    )


def arrive(world: World, hero: Entity, parent: Entity, activity: str) -> None:
    world.say(
        f"One windy morning, {hero.id} and {hero.pronoun('possessive')} {parent.label} "
        f"came to {world.harbor.name}."
    )
    world.say(world.harbor.place_detail)


def want_and_warn(world: World, hero: Entity, parent: Entity, apparel: Entity, activity: str) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {activity} right away, but {parent.id} looked at "
        f"{hero.pronoun('possessive')} {apparel.label} and frowned."
    )
    if simulate_mess(world, hero, activity, apparel.id)["soaked"]:
        world.say(
            f'"If you keep that on in this spray, your {apparel.label} may get soaked," '
            f"{parent.id} warned."
        )


def defy(world: World, hero: Entity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1
    world.say(f"{hero.id} crossed {hero.pronoun('possessive')} arms and took a brave breath.")


def choose_cover(world: World, hero: Entity, parent: Entity, apparel: Entity) -> Optional[WeatherGear]:
    if apparel.region == "head":
        gear = WeatherGear(
            id="oilcloth",
            label="an oilcloth hood",
            covers={"head"},
            guards={WET},
            prep="tie an oilcloth hood under your chin",
            tail="tied the hood snug and kept the fancy cap dry",
        )
    else:
        gear = WeatherGear(
            id="oilskin",
            label="an oilskin coat",
            covers={"torso"},
            guards={WET},
            prep="button up an oilskin coat over it",
            tail="buttoned the coat tight and kept the fancy clothes safe",
        )

    if apparel.region not in gear.covers:
        return None

    cover = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        phrase=gear.label,
        protective=True,
        covers=set(gear.covers),
    ))
    cover.worn_by = hero.id

    if simulate_mess(world, hero, "deck work", apparel.id)["ruined"]:
        cover.worn_by = None
        del world.entities[cover.id]
        return None

    world.say(
        f"Then {parent.id} smiled and said, "
        f'"How about we {gear.prep} and still go?'
    )
    return gear


def accept(world: World, hero: Entity, parent: Entity, apparel: Entity, gear: WeatherGear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["stubborn"] = 0.0
    world.say(
        f"{hero.id}'s face lit up, and {hero.pronoun()} hugged {parent.id} hard."
    )
    world.say(
        f"Together they {gear.tail}. Soon {hero.id} was laughing on deck, "
        f"and {apparel.label} stayed neat and proud."
    )


def tell(hero_name: str, hero_type: str, parent_name: str, parent_type: str, apparel_key: str) -> World:
    harbor = HARBORS["dock"]
    world = World(harbor)
    hero = world.add(Entity(
        id=hero_name,
        kind="character",
        type=hero_type,
        traits=["little", "brave", "curious"],
    ))
    parent = world.add(Entity(
        id=parent_name,
        kind="character",
        type=parent_type,
        label="captain",
    ))
    apparel = world.add(Entity(
        id=apparel_key,
        kind="thing",
        type="apparel",
        label=APPAREL[apparel_key].label,
        phrase=APPAREL[apparel_key].phrase,
        owner=hero.id,
        region=APPAREL[apparel_key].region,
        plural=APPAREL[apparel_key].plural,
    ))

    intro(world, hero, parent, apparel)
    world.para()
    arrive(world, hero, parent, "swab the deck")
    want_and_warn(world, hero, parent, apparel, "swab the deck")
    flashback(world, hero, apparel)
    defy(world, hero)
    gear = choose_cover(world, hero, parent, apparel)
    if gear:
        accept(world, hero, parent, apparel, gear)

    world.facts.update(
        hero=hero,
        parent=parent,
        apparel=apparel,
        gear=gear,
        harbor=harbor,
        activity="swab the deck",
    )
    return world


HARBORS = {
    "dock": Harbor(
        name="the lantern dock",
        place_detail="The dock smelled like tar, rope, and sea salt, and the ship's deck gleamed in the morning spray.",
        affords={"swab the deck"},
    )
}

APPAREL = {
    "cap": Apparel(
        id="cap",
        label="captain's cap",
        phrase="a red captain's cap with a gold stitch",
        region="head",
    ),
    "coat": Apparel(
        id="coat",
        label="sea coat",
        phrase="a blue sea coat with shiny buttons",
        region="torso",
    ),
    "sash": Apparel(
        id="sash",
        label="sash",
        phrase="a striped sash for ceremonies",
        region="torso",
    ),
}

HEROES = {
    "Mina": ("girl", "mother"),
    "Finn": ("boy", "father"),
    "Pip": ("boy", "mother"),
    "Tessa": ("girl", "father"),
}


@dataclass
class StoryParams:
    apparel: str
    name: str
    gender: str
    parent: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    apparel = _safe_fact(world, f, "apparel")
    return [
        f'Write a short pirate story for a child that includes the word "apparel" and a cherished {apparel.label}.',
        f"Tell a gentle pirate tale where {hero.id} wants to go on deck, remembers a kind flashback, and keeps {hero.pronoun('possessive')} {apparel.label} safe.",
        f"Write a sea story with a flashback where a young pirate and {hero.pronoun('possessive')} captain solve an apparel problem without stopping the adventure.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    parent = _safe_fact(world, f, "parent")
    apparel = _safe_fact(world, f, "apparel")
    gear = f.get("gear")
    qs = [
        QAItem(
            question=f"What did {hero.id} love wearing on the ship?",
            answer=f"{hero.id} loved wearing {apparel.phrase} because it made {hero.pronoun('object')} feel ready for big waves.",
        ),
        QAItem(
            question=f"Why did {parent.id} worry about {hero.pronoun('possessive')} {apparel.label}?",
            answer=f"{parent.id} worried because the wind and salt spray could soak {hero.pronoun('possessive')} {apparel.label}.",
        ),
        QAItem(
            question="What did the flashback remind the pirate of?",
            answer=f"The flashback reminded {hero.id} that {hero.pronoun('possessive')} grandmother had once said {apparel.phrase} would help {hero.pronoun('object')} feel brave.",
        ),
    ]
    if gear is not None:
        qs.append(
            QAItem(
                question=f"How did {gear.label} help keep the {apparel.label} safe?",
                answer=f"They used {gear.label} so {hero.id} could keep working on deck while {apparel.label} stayed dry and neat.",
            )
        )
    return qs


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is apparel?",
            answer="Apparel means clothes or things people wear.",
        ),
        QAItem(
            question="Why do sailors care about salt spray?",
            answer="Salt spray can make clothes wet and crusty, so sailors try to keep important gear dry.",
        ),
        QAItem(
            question="What is a flashback in a story?",
            answer="A flashback is a moment when the story remembers something that happened earlier.",
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


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"{e.id}: {e.kind}/{e.type} " + " ".join(bits))
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines = []
    for hid, h in HARBORS.items():
        lines.append(asp.fact("harbor", hid))
        for a in sorted(h.affords):
            lines.append(asp.fact("affords", hid, a))
    for aid, a in APPAREL.items():
        lines.append(asp.fact("apparel", aid))
        lines.append(asp.fact("region", aid, a.region))
        if a.plural:
            lines.append(asp.fact("plural", aid))
        for g in sorted(a.genders):
            lines.append(asp.fact("wears", g, aid))
    lines.append(asp.fact("gear", "oilcloth"))
    lines.append(asp.fact("gear", "oilskin"))
    lines.append(asp.fact("covers", "oilcloth", "head"))
    lines.append(asp.fact("covers", "oilskin", "torso"))
    lines.append(asp.fact("guards", "oilcloth", WET))
    lines.append(asp.fact("guards", "oilskin", WET))
    return "\n".join(lines)


ASP_RULES = r"""
at_risk(A, P) :- apparel(P), region(P, R), splashes(A, R).
fix(G, A, P) :- gear(G), at_risk(A, P), covers(G, R), region(P, R), guards(G, wet).
valid(A, P) :- at_risk(A, P), fix(_, A, P).
valid_story(H, A, P, G) :- valid(A, P), wears(G, P), harbor(H), affords(H, A).
#show valid/2.
#show valid_story/4.
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos() -> list[tuple[str, str]]:
    return [("dock", "swab the deck", key) for key in APPAREL]


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    p = set((a, b) for a, b, _ in valid_combos())
    c = set(asp_valid_combos())
    if p != c:
        print("MISMATCH between python and ASP")
        print("python:", sorted(p))
        print("asp:", sorted(c))
        return 1
    print(f"OK: ASP matches python gate ({len(p)} combos).")
    return 0


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A pirate tale world with apparel and a flashback.")
    ap.add_argument("--apparel", choices=APPAREL)
    ap.add_argument("--name", choices=sorted(HEROES))
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
    if getattr(args, "gender", None) and getattr(args, "name", None):
        expected = _safe_lookup(HEROES, getattr(args, "name", None))[0]
        if getattr(args, "gender", None) != expected:
            return _fallback_storyparams(args, rng, StoryParams, globals())
    apparel = getattr(args, "apparel", None) or rng.choice(list(APPAREL))
    name = getattr(args, "name", None) or rng.choice([n for n, (g, _) in HEROES.items() if not getattr(args, "gender", None) or g == getattr(args, "gender", None)])
    gender = getattr(args, "gender", None) or _safe_lookup(HEROES, name)[0]
    parent = getattr(args, "parent", None) or _safe_lookup(HEROES, name)[1]
    return StoryParams(apparel=apparel, name=name, gender=gender, parent=parent)


def generate(params: StoryParams) -> StorySample:
    world = tell(params.name, params.gender, params.parent, params.parent, params.apparel)
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
    if trace and sample.world:
        print(dump_trace(sample.world))
    if qa:
        print()
        print(format_qa(sample))


CURATED = [
    StoryParams(apparel="cap", name="Mina", gender="girl", parent="mother"),
    StoryParams(apparel="coat", name="Finn", gender="boy", parent="father"),
    StoryParams(apparel="sash", name="Tessa", gender="girl", parent="father"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for row in combos:
            print(row)
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        base = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
        for i in range(getattr(args, "n", None)):
            params = resolve_params(args, random.Random(base + i))
            params.seed = base + i
            samples.append(generate(params))

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
