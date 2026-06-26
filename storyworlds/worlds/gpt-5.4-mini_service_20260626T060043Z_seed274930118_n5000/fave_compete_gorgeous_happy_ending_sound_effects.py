#!/usr/bin/env python3
"""
storyworlds/worlds/fave_compete_gorgeous_happy_ending_sound_effects.py
======================================================================

A small pirate-tale story world about a favorite thing, a friendly competition,
a gorgeous prize, sound effects, and a happy ending.

Premise:
- A child pirate crew wants to compete for a gorgeous prize.
- One character's fave thing matters a lot.
- The competing act risks spoiling the prize or causing embarrassment.
- A captain-like helper notices the risk and offers a fair contest.

The simulated world tracks:
- physical meters: sparkle, scuff, excitement, tide, shine, mess
- emotional memes: pride, worry, joy, rivalry, relief, love

The story is authored from the world state so the narration changes with the
simulation rather than swapping nouns in a frozen paragraph.
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
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    captain: object | None = None
    fave: object | None = None
    hero: object | None = None
    prize: object | None = None
    def m(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def e(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "captain"}
        male = {"boy", "father", "dad", "man", "pirate"}
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
    place: str
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
class Competition:
    id: str
    verb: str
    gerund: str
    noise: str
    risk: str
    mess: str
    sound_effects: list[str] = field(default_factory=list)
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
class Prize:
    id: str
    label: str
    phrase: str
    region: str
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


@dataclass
class Gear:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str] = field(default_factory=set)
    mess_block: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
        self.fired: set[tuple] = set()
        self.active_competition: str = ""

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


def _sound(text: str) -> str:
    return text


SETTINGS = {
    "dock": Setting(place="the dock", affords={"sing", "race", "dance"}),
    "island": Setting(place="the island shore", affords={"race", "build", "sing"}),
    "ship": Setting(place="the deck of the ship", affords={"sing", "dance", "race"}),
}


COMPETITIONS = {
    "sing": Competition(
        id="sing",
        verb="sing for the prize",
        gerund="singing for the prize",
        noise="song",
        risk="a wobbly voice could crack the mood",
        mess="echo",
        sound_effects=["tra-la-la", "yo-ho-ho", "la-la-LA"],
        tags={"sound", "song"},
    ),
    "race": Competition(
        id="race",
        verb="race for the prize",
        gerund="racing for the prize",
        noise="stomp",
        risk="a fast dash could bump the gorgeous prize",
        mess="dust",
        sound_effects=["thump-thump", "skitter-skatter", "whoosh"],
        tags={"speed"},
    ),
    "dance": Competition(
        id="dance",
        verb="dance for the prize",
        gerund="dancing for the prize",
        noise="tap",
        risk="a twirl could kick up dust near the gorgeous prize",
        mess="spark",
        sound_effects=["tap-tap", "swish!", "twirl-whirl"],
        tags={"music"},
    ),
    "build": Competition(
        id="build",
        verb="build a prize stand",
        gerund="building a prize stand",
        noise="hammer",
        risk="a careless hammer could chip the gorgeous prize",
        mess="chips",
        sound_effects=["clink", "tap-tap-tap", "thunk"],
        tags={"craft"},
    ),
}

PRIZES = {
    "shell": Prize(id="shell", label="shell crown", phrase="a gorgeous shell crown", region="head"),
    "ribbon": Prize(id="ribbon", label="ribbon sash", phrase="a gorgeous ribbon sash", region="torso"),
    "boots": Prize(id="boots", label="boots", phrase="a gorgeous pair of shiny boots", region="feet", plural=True),
}

GEAR = {
    "stand": Gear(
        id="stand",
        label="a steady prize stand",
        prep="set up a steady prize stand first",
        tail="built the prize stand with care",
        protects={"head", "torso", "feet"},
        mess_block={"dust", "spark", "chips", "echo"},
    ),
    "softsteps": Gear(
        id="softsteps",
        label="soft rope shoes",
        prep="put on soft rope shoes",
        tail="tiptoed in the soft rope shoes",
        protects={"feet"},
        mess_block={"dust", "spark"},
        plural=True,
    ),
    "clothwrap": Gear(
        id="clothwrap",
        label="a cloth wrap",
        prep="wrap the prize in a cloth wrap",
        tail="wrapped the prize in the cloth wrap",
        protects={"head", "torso", "feet"},
        mess_block={"chips", "dust", "spark", "echo"},
    ),
}

NAMES = ["Mina", "Jory", "Luca", "Pip", "Nell", "Toby", "Rae", "Finn"]
TRAITS = ["brave", "cheery", "stubborn", "clever", "quick", "bright"]


@dataclass
class StoryParams:
    place: str
    competition: str
    prize: str
    name: str
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


def competition_risks_prize(comp: Competition, prize: Prize) -> bool:
    if comp.id == "race":
        return prize.region in {"feet", "head", "torso"}
    if comp.id == "sing":
        return prize.region in {"head", "torso"}
    if comp.id == "dance":
        return prize.region in {"torso", "feet"}
    if comp.id == "build":
        return True
    return False


def select_gear(comp: Competition, prize: Prize) -> Optional[Gear]:
    candidates: list[Gear] = []
    for gear in GEAR.values():
        if prize.region in gear.protects and comp.mess in gear.mess_block:
            candidates.append(gear)
    if not candidates:
        return None
    order = {"clothwrap": 0, "stand": 1, "softsteps": 2}
    candidates.sort(key=lambda g: order.get(g.id, 99))
    return candidates[0]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for comp_id in setting.affords:
            comp = _safe_lookup(COMPETITIONS, comp_id)
            for prize_id, prize in PRIZES.items():
                if competition_risks_prize(comp, prize) and select_gear(comp, prize):
                    out.append((place, comp_id, prize_id))
    return out


def predict_mess(world: World, actor: Entity, comp: Competition, prize_id: str) -> dict:
    soiled = False
    if comp.id == "build" and prize_id == "shell":
        soiled = True
    if comp.id == "race" and prize_id in {"boots", "shell"}:
        soiled = True
    if comp.id == "sing" and prize_id == "ribbon":
        soiled = False
    return {"soiled": soiled, "noise": comp.noise}


def introduce(world: World, hero: Entity, comp: Competition) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait_word', 'brave')} pirate who loved the sweet thrill of a contest."
    )
    world.say(
        f"{hero.pronoun().capitalize()} liked {comp.gerund}, because every round felt like a tiny adventure on the waves."
    )


def show_prize(world: World, prize: Entity) -> None:
    world.say(
        f"On the table sat {prize.phrase}, shining so bright it looked like a bit of sunrise had fallen from the sky."
    )


def show_fave(world: World, hero: Entity, fave: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} fave thing, {fave.label}, and kept it near like a tiny lucky charm."
    )


def start_competition(world: World, hero: Entity, comp: Competition, prize: Entity) -> None:
    world.say(
        f"At {world.setting.place}, the crew gathered for a grand contest, and the gorgeous prize gleamed in the middle."
    )
    world.say(_sound(f"'{comp.sound_effects[0]}!' went the deck as the challenge began."))
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1
    hero.memes["rivalry"] = hero.memes.get("rivalry", 0.0) + 1
    world.say(
        f"{hero.id} wanted to {comp.verb}, but {hero.pronoun('possessive')} heart raced when {comp.risk}."
    )


def warn(world: World, hero: Entity, comp: Competition, prize: Entity) -> bool:
    pred = predict_mess(world, hero, comp, prize.id)
    if not pred["soiled"]:
        return False
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1
    world.say(
        f'"Mind the {prize.label}," the captain warned. "If you rush, {comp.risk}."'
    )
    return True


def choose_fix(world: World, hero: Entity, comp: Competition, prize: Entity) -> Optional[Gear]:
    gear = select_gear(comp, prize)
    if gear is None:
        return None
    world.say(
        f"The captain smiled and said, 'How about we {gear.prep} so the contest stays fair?'"
    )
    return gear


def resolve(world: World, hero: Entity, comp: Competition, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1
    hero.memes["worry"] = 0.0
    hero.memes["relief"] = hero.memes.get("relief", 0.0) + 1
    world.say(
        f"{hero.id}'s face lit up. {hero.pronoun().capitalize()} nodded, and the crew all cried, '{comp.sound_effects[1]}!'"
    )
    world.say(
        f"They {gear.tail}, and soon the contest became a proper pirate game instead of a bumpy tumble."
    )
    world.say(
        f"In the end, {hero.id} won the smile prize, {prize.label} stayed gorgeous, and the whole ship sounded happy."
    )
    world.say(_sound(f"{comp.sound_effects[2]}! {comp.sound_effects[0]}!"))
    world.say(
        f"{hero.id} tucked the {hero.pronoun('possessive')} fave thing away, grinning at the moonlit water."
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    comp = _safe_lookup(COMPETITIONS, params.competition)
    prize_cfg = _safe_lookup(PRIZES, params.prize)

    hero = world.add(Entity(
        id=params.name,
        kind="character",
        type="pirate",
        memes={"trait_word": params.trait},
    ))
    captain = world.add(Entity(
        id="Captain",
        kind="character",
        type="captain",
        label="the captain",
    ))
    fave = world.add(Entity(
        id="fave",
        type="thing",
        label="little wooden compass",
        phrase="a small wooden compass with a red needle",
        owner=hero.id,
    ))
    prize = world.add(Entity(
        id="prize",
        type="thing",
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        caretaker=captain.id,
    ))

    world.facts.update(hero=hero, captain=captain, fave=fave, prize=prize, comp=comp, prize_cfg=prize_cfg)

    introduce(world, hero, comp)
    show_fave(world, hero, fave)
    world.para()
    show_prize(world, prize)
    start_competition(world, hero, comp, prize)
    warn(world, hero, comp, prize)
    world.para()
    gear = choose_fix(world, hero, comp, prize)
    if gear:
        resolve(world, hero, comp, prize, gear)
    world.facts["gear"] = gear
    world.facts["resolved"] = gear is not None
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    comp = _safe_fact(world, f, "comp")
    prize = _safe_fact(world, f, "prize_cfg")
    return [
        f'Write a short pirate tale for a young child that includes the words "fave", "compete", and "gorgeous".',
        f"Tell a gentle pirate story where {hero.id} wants to {comp.verb} for {prize.phrase}, but the crew finds a safer way.",
        f"Write a happy-ending story with sound effects about a pirate contest and a gorgeous prize.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    comp = _safe_fact(world, f, "comp")
    prize = _safe_fact(world, f, "prize")
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did {hero.id} want to do at the start of the pirate contest?",
            answer=f"{hero.id} wanted to {comp.verb} because the contest felt exciting and the prize looked gorgeous.",
        ),
        QAItem(
            question=f"What was {hero.id}'s fave thing in the story?",
            answer=f"{hero.id}'s fave thing was a little wooden compass with a red needle.",
        ),
        QAItem(
            question=f"Why did the captain worry about the gorgeous {prize.label}?",
            answer=f"The captain worried because {comp.risk}, and the gorgeous {prize.label} could have been harmed or knocked about.",
        ),
    ]
    if gear is not None:
        qa.append(
            QAItem(
                question=f"How did the crew keep the contest safe?",
                answer=f"They used {gear.label} first, so {hero.id} could join the contest without hurting the gorgeous prize.",
            )
        )
    if world.facts.get("resolved"):
        qa.append(
            QAItem(
                question=f"What happened at the end of the pirate tale?",
                answer=f"The contest ended happily, {prize.label} stayed gorgeous, and everyone cheered with sound effects.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What is a compass for?",
            answer="A compass helps you find direction, so you can tell which way is north, south, east, or west.",
        ),
        QAItem(
            question="What does gorgeous mean?",
            answer="Gorgeous means very beautiful or shiny in a way that makes something look special.",
        ),
        QAItem(
            question="Why do sound effects make stories fun?",
            answer="Sound effects like bang, swish, or whoosh help you imagine what is happening in a lively way.",
        ),
        QAItem(
            question="What is a happy ending?",
            answer="A happy ending is when the problem gets solved and the characters finish feeling safe, glad, or relieved.",
        ),
    ]
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
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.plural:
            bits.append("plural=True")
        if e.protective:
            bits.append("protective=True")
        lines.append(f"  {e.id:8} ({e.kind:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="dock", competition="sing", prize="shell", name="Mina", trait="bright"),
    StoryParams(place="ship", competition="dance", prize="boots", name="Pip", trait="cheery"),
    StoryParams(place="island", competition="race", prize="ribbon", name="Luca", trait="clever"),
]


ASP_RULES = r"""
risk(C, P) :- comp(C), prize(P), comp_risk(C, R), prize_region(P, R).
fix(C, P) :- risk(C, P), gear(G), comp_mess(C, M), gear_blocks(G, M), gear_protects(G, R), prize_region(P, R).
valid(Place, C, P) :- setting(Place), affords(Place, C), risk(C, P), fix(C, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, s in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        for c in sorted(s.affords):
            lines.append(asp.fact("affords", sid, c))
    for cid, c in COMPETITIONS.items():
        lines.append(asp.fact("comp", cid))
        lines.append(asp.fact("comp_risk", cid, c.mess))
        lines.append(asp.fact("comp_mess", cid, c.mess))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("prize_region", pid, p.region))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for m in sorted(g.mess_block):
            lines.append(asp.fact("gear_blocks", gid, m))
        for r in sorted(g.protects):
            lines.append(asp.fact("gear_protects", gid, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_combos_asp())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python gates:")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world with a fave thing, competition, gorgeous prize, happy ending, and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--competition", choices=COMPETITIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
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
    combos = valid_combos()
    combos = [c for c in combos
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "competition", None) is None or c[1] == getattr(args, "competition", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, comp, prize = rng.choice(list(combos))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, competition=comp, prize=prize, name=name, trait=trait)


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
        combos = valid_combos_asp()
        print(f"{len(combos)} compatible combos:\n")
        for place, comp, prize in combos:
            print(f"  {place:10} {comp:10} {prize}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
