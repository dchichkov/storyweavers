#!/usr/bin/env python3
"""
storyworlds/worlds/stow_happy_ending_tall_tale.py
=================================================

A small storyworld about a tall-tale child helping to stow an enormous thing
before weather turns rough, then finding a cheerful fix that makes everyone
smile.

The world is built from a simple seed tale:
- someone has something big and beloved
- it must be stowed somewhere safe
- the first plan is too awkward, too risky, or too stiff
- a clever helper finds a better way
- the ending proves the change with a safe, happy image

The prose leans into tall-tale flavor: broad skies, big objects, strong winds,
and confident, folksy narration.

This file is standalone and uses only the stdlib plus the shared Storyweavers
result containers, with optional ASP verification support.
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
    stored_in: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    helper: object | None = None
    hero: object | None = None
    item: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "mom"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "dad"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

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
class Place:
    id: str
    label: str
    cover: str
    spacious: bool = False
    dry: bool = True
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


@dataclass
class Stowable:
    id: str
    label: str
    phrase: str
    size: str
    fits_in: set[str]
    needs_cover: bool = False
    weather_risk: set[str] = field(default_factory=set)
    plural: bool = False
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
class Gear:
    id: str
    label: str
    phrase: str
    helps_with: set[str]
    prep: str
    tail: str
    plural: bool = False
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


class World:
    def __init__(self, place: Place) -> None:
        self.place = place
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.weather: str = ""
        self.facts: dict = {}

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
        import copy as _copy

        clone = World(self.place)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


@dataclass
class StoryParams:
    place: str
    item: str
    hero: str
    hero_type: str
    helper: str
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


PLACES = {
    "barn": Place(id="barn", label="the old barn", cover="roof", spacious=True, dry=True),
    "loft": Place(id="loft", label="the high loft", cover="roof", spacious=False, dry=True),
    "shed": Place(id="shed", label="the shed", cover="roof", spacious=False, dry=True),
    "porch": Place(id="porch", label="the porch", cover="awning", spacious=False, dry=False),
}

STOWABLES = {
    "kite": Stowable(
        id="kite",
        label="kite",
        phrase="a giant patchwork kite with ribbon tails",
        size="long",
        fits_in={"barn", "loft", "shed"},
        needs_cover=True,
        weather_risk={"wind", "rain"},
        tags={"wind", "cloth"},
    ),
    "trunk": Stowable(
        id="trunk",
        label="trunk",
        phrase="a big cedar trunk with brass corners",
        size="boxy",
        fits_in={"barn", "loft", "shed"},
        needs_cover=True,
        weather_risk={"rain"},
        tags={"wood", "rain"},
    ),
    "ladder": Stowable(
        id="ladder",
        label="ladder",
        phrase="a very long ladder that could tickle the clouds",
        size="long",
        fits_in={"barn", "shed"},
        needs_cover=False,
        weather_risk={"wind"},
        tags={"wood", "tall"},
    ),
    "banner": Stowable(
        id="banner",
        label="banner",
        phrase="a parade banner as wide as a bedtime story",
        size="wide",
        fits_in={"barn", "loft", "shed"},
        needs_cover=True,
        weather_risk={"rain", "wind"},
        tags={"cloth", "celebration"},
    ),
}

GEAR = {
    "rope": Gear(
        id="rope",
        label="rope loops",
        phrase="a handful of rope loops",
        helps_with={"long", "wide"},
        prep="loop the thing up neat and tight",
        tail="looped the thing up neat and tight",
    ),
    "tarpaulin": Gear(
        id="tarpaulin",
        label="a tarpaulin",
        phrase="a big tarpaulin",
        helps_with={"cloth", "wood"},
        prep="wrap it in a tarpaulin first",
        tail="wrapped it in a tarpaulin first",
    ),
    "cart": Gear(
        id="cart",
        label="a wagon cart",
        phrase="a wagon cart with wooden wheels",
        helps_with={"long", "boxy", "wide"},
        prep="set it on a wagon cart and wheel it slow",
        tail="set it on a wagon cart and wheeled it slow",
        plural=False,
    ),
}

HEROES = ["Mabel", "Ruby", "Sally", "Nell", "June", "Annie"]
HELPERS = ["Grandpa", "Aunt May", "Uncle Ben", "Mom", "Dad", "Old Ezra"]
HERO_TYPES = ["girl", "boy"]
HELPER_TYPES = ["father", "mother", "man", "woman"]


def _fits(place: Place, item: Stowable) -> bool:
    return place.id in item.fits_in


def _reasonable(place: Place, item: Stowable) -> bool:
    return _fits(place, item)


def select_gear(item: Stowable) -> Optional[Gear]:
    for gear in (GEAR["cart"], GEAR["tarpaulin"], GEAR["rope"]):
        if item.size in gear.helps_with:
            if gear.id == "tarpaulin" and not item.needs_cover:
                continue
            return gear
    return None


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for iid, item in STOWABLES.items():
            if _reasonable(place, item) and select_gear(item):
                combos.append((pid, iid))
    return combos


def _stow_risk(item: Stowable, weather: str) -> bool:
    return bool(item.weather_risk & {weather})


def predict(world: World, item: Stowable, weather: str) -> dict:
    clone = world.copy()
    clone.weather = weather
    hero = clone.get(clone.facts["hero"].id)
    obj = clone.get(clone.facts["item"].id)
    hero.memes["want"] += 1
    if _stow_risk(item, weather):
        obj.meters["risk"] += 1
    return {"risky": obj.meters.get("risk", 0) >= THRESHOLD}


def setup(world: World, hero: Entity, helper: Entity, item: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} with a heart big as a thunderhead, "
        f"and {helper.id} was the sort who could lift a laugh right off the ground."
    )
    world.say(
        f"Together they loved {item.phrase}, though it was so large it seemed to have "
        f"been stitched out of sunset and barn rafters."
    )


def weather_turn(world: World, item: Entity) -> None:
    world.para()
    if world.weather == "wind":
        world.say(
            f"One windy afternoon, the air came whistling down the lane like a curious fiddle player."
        )
    elif world.weather == "rain":
        world.say(
            f"One rainy afternoon, the clouds rolled in low enough to brush the fence posts."
        )
    else:
        world.say(
            f"One bright afternoon, the sky stayed clear, but the day still felt like it might change its mind."
        )
    world.say(
        f"{item.id.capitalize()} needed stowing before the weather could get any saucier."
    )


def wants_to_stow(world: World, hero: Entity, item: Entity, place: Place) -> None:
    hero.memes["desire"] += 1
    world.say(
        f"{hero.id} wanted to stow {hero.pronoun('possessive')} {item.label} in {place.label}, "
        f"safe and sound, where no wind could make a toy of it."
    )


def warn(world: World, helper: Entity, hero: Entity, item: Entity) -> bool:
    item_cfg: Stowable = _safe_fact(world, world.facts, "item_cfg")
    if not _stow_risk(item_cfg, world.weather):
        return False
    helper.memes["worry"] += 1
    world.say(
        f'"If we leave it out, that {item.label} could get tossed and tumbled," '
        f"{helper.id} said. \"Let's be smart before the sky gets rowdy.\""
    )
    return True


def try_bad_stow(world: World, hero: Entity, item: Entity, place: Place) -> None:
    hero.memes["stubborn"] += 1
    world.say(
        f"{hero.id} tried to shove the {item.label} into {place.label} the quick way, "
        f"but it was so long and awkward it nearly tickled the rafters."
    )


def offer_fix(world: World, helper: Entity, hero: Entity, item: Entity, gear: Gear) -> None:
    hero.memes["hope"] += 1
    world.say(
        f"Then {helper.id} grinned and said, \"Let's {gear.prep}.\""
    )


def accept_fix(world: World, hero: Entity, helper: Entity, item: Entity, gear: Gear) -> None:
    hero.memes["joy"] += 1
    helper.memes["joy"] += 1
    world.say(
        f"{hero.id} nodded, and they {gear.tail}."
    )


def resolve(world: World, hero: Entity, helper: Entity, item: Entity, place: Place, gear: Gear) -> None:
    item.stored_in = place.id
    item.meters["safe"] += 1
    world.say(
        f"Before long, the {item.label} was tucked away in {place.label}, snug as a kitten in a quilt box."
    )
    world.say(
        f"The wind could stomp outside all it liked, but inside, {hero.id} and {helper.id} "
        f"stood smiling by the stowed-up treasure, proud as peacocks at a county fair."
    )


def tell(place: Place, item_cfg: Stowable, hero_name: str, hero_type: str, helper_name: str, helper_type: str) -> World:
    world = World(place)
    weather = "wind" if "wind" in item_cfg.weather_risk else "rain"
    world.weather = weather

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    item = world.add(Entity(id=item_cfg.label, type=item_cfg.label, label=item_cfg.label, phrase=item_cfg.phrase))

    world.facts.update(hero=hero, helper=helper, item=item, item_cfg=item_cfg, place=place)

    setup(world, hero, helper, item)
    weather_turn(world, item)
    wants_to_stow(world, hero, item, place)
    warn(world, helper, hero, item)
    try_bad_stow(world, hero, item, place)
    gear = select_gear(item_cfg)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
    world.para()
    offer_fix(world, helper, hero, item, gear)
    accept_fix(world, hero, helper, item, gear)
    resolve(world, hero, helper, item, place, gear)
    world.facts["gear"] = gear
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    item = _safe_fact(world, f, "item_cfg")
    place = _safe_fact(world, f, "place")
    return [
        f'Write a tall-tale style story for a young child about {hero.id} trying to stow {item.phrase} in {place.label}.',
        f'Write a happy-ending story where {helper.id} helps {hero.id} stow a {item.label} before rough weather comes.',
        f'Create a short, folksy story that includes the word "stow" and ends with the big thing safely put away.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    helper: Entity = _safe_fact(world, f, "helper")
    item: Entity = _safe_fact(world, f, "item")
    item_cfg: Stowable = _safe_fact(world, f, "item_cfg")
    place: Place = _safe_fact(world, f, "place")
    gear: Gear = _safe_fact(world, f, "gear")

    return [
        QAItem(
            question=f"What did {hero.id} want to do with the {item.label}?",
            answer=f"{hero.id} wanted to stow the {item_cfg.phrase} in {place.label} so it would stay safe.",
        ),
        QAItem(
            question=f"Why did {helper.id} worry about leaving it out?",
            answer=f"{helper.id} worried because the weather could toss the {item.label} around before it was safely stowed.",
        ),
        QAItem(
            question=f"What helped {hero.id} and {helper.id} finish the job?",
            answer=f"{gear.label.capitalize()} helped them manage the big {item.label}, and that made the plan work.",
        ),
        QAItem(
            question=f"How did the story end for the {item.label}?",
            answer=f"It ended with the {item.label} tucked away in {place.label}, safe and snug.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["item_cfg"].tags)
    gear: Gear = _safe_fact(world, world.facts, "gear")
    if gear.id == "tarpaulin":
        tags.add("cloth")
    if gear.id == "cart":
        tags.add("wagon")
    out: list[QAItem] = []
    if "wind" in tags:
        out.append(
            QAItem(
                question="What is wind?",
                answer="Wind is moving air. It can rattle leaves, push flags, and tug at things left outside.",
            )
        )
    if "cloth" in tags:
        out.append(
            QAItem(
                question="What does a tarpaulin do?",
                answer="A tarpaulin is a big cover that helps keep rain, dust, and wind off things.",
            )
        )
    if "wagon" in tags:
        out.append(
            QAItem(
                question="What is a wagon cart for?",
                answer="A wagon cart helps carry heavy or long things from one place to another.",
            )
        )
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
        if e.stored_in:
            bits.append(f"stored_in={e.stored_in}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(place: Place, item: Stowable) -> str:
    return (
        f"(No story: {item.phrase} doesn't fit well with {place.label} for this tall-tale setup. "
        f"Choose a place that can reasonably stow it.)"
    )


def valid_story_combos() -> list[tuple[str, str]]:
    combos = []
    for pid, place in PLACES.items():
        for iid, item in STOWABLES.items():
            if _reasonable(place, item):
                combos.append((pid, iid))
    return combos


@dataclass
class ASPStub:
    pass
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


ASP_RULES = r"""
stowable(P,I) :- place(P), item(I), fits_in(I,P).
valid(P,I) :- stowable(P,I), has_fix(I).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, place in PLACES.items():
        lines.append(asp.fact("place", pid))
        if place.spacious:
            lines.append(asp.fact("spacious", pid))
        if place.dry:
            lines.append(asp.fact("dry", pid))
    for iid, item in STOWABLES.items():
        lines.append(asp.fact("item", iid))
        for p in sorted(item.fits_in):
            lines.append(asp.fact("fits_in", iid, p))
        for r in sorted(item.weather_risk):
            lines.append(asp.fact("risk", iid, r))
    for gid, gear in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for s in sorted(gear.helps_with):
            lines.append(asp.fact("helps_with", gid, s))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/2."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_story_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_story_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and python combo gates:")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Tall-tale storyworld: stow a big thing, find a clever fix, end happy."
    )
    ap.add_argument("--place", choices=sorted(PLACES))
    ap.add_argument("--item", choices=sorted(STOWABLES))
    ap.add_argument("--hero")
    ap.add_argument("--hero-type", choices=["girl", "boy"])
    ap.add_argument("--helper")
    ap.add_argument("--helper-type", choices=["mother", "father", "man", "woman"])
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
    if getattr(args, "place", None) and getattr(args, "item", None):
        if (getattr(args, "place", None), getattr(args, "item", None)) not in valid_story_combos():
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        (p, i) for p, i in valid_story_combos()
        if (getattr(args, "place", None) is None or p == getattr(args, "place", None))
        and (getattr(args, "item", None) is None or i == getattr(args, "item", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place_id, item_id = rng.choice(list(combos))
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    helper_type = getattr(args, "helper_type", None) or rng.choice(HELPER_TYPES)
    hero = getattr(args, "hero", None) or rng.choice(HEROES)
    helper = getattr(args, "helper", None) or rng.choice(HELPERS)
    return StoryParams(
        place=place_id,
        item=item_id,
        hero=hero,
        hero_type=hero_type,
        helper=helper,
        helper_type=helper_type,
    )


def generate(params: StoryParams) -> StorySample:
    place = _safe_lookup(PLACES, params.place)
    item_cfg = _safe_lookup(STOWABLES, params.item)
    world = tell(place, item_cfg, params.hero, params.hero_type, params.helper, params.helper_type)
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
    StoryParams(place="barn", item="kite", hero="Mabel", hero_type="girl", helper="Grandpa", helper_type="father"),
    StoryParams(place="shed", item="banner", hero="Ruby", hero_type="girl", helper="Aunt May", helper_type="woman"),
    StoryParams(place="loft", item="trunk", hero="Nell", hero_type="girl", helper="Dad", helper_type="father"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/2."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible (place, item) combos:\n")
        for place, item in combos:
            print(f"  {place:8} {item}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.hero}: stow {p.item} in {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
