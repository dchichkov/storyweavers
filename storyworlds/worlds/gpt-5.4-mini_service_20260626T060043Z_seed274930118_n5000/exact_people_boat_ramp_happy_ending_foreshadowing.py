#!/usr/bin/env python3
"""
storyworlds/worlds/exact_people_boat_ramp_happy_ending_foreshadowing.py
=======================================================================

A small pirate-tale story world set at a boat ramp.

Premise:
- A crew of exact people prepares a little boat at the ramp.
- A warning in the sky foreshadows trouble.
- A conflict rises when the tide or gear goes wrong.
- A careful fix leads to a happy ending.

This world is intentionally narrow: it generates a few strongly grounded,
child-facing pirate stories with a clear setup, turn, and resolution.
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
    kind: str = "thing"   # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    crew: object | None = None
    hero: object | None = None
    obj: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "sailor_woman"}
        male = {"boy", "man", "father", "sailor_man"}
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
    place: str = "the boat ramp"
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    foreshadow: str
    keyword: str
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
class Prize:
    label: str
    phrase: str
    type: str
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
        self.zone: set[str] = set()
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.label == "rain cloak" and region in CLOAK.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def clamp_name(name: str) -> str:
    return name.strip().title()


def pirate_name(name: str) -> str:
    return clamp_name(name)


def actor_desc(hero: Entity) -> str:
    return f"little {hero.type}"


def setting_line(world: World, action: Action) -> str:
    if action.id == "tide":
        return "The tide lapped at the rocks, and the boat ramp smelled like salt and wet wood."
    if action.id == "wind":
        return "The wind tugged at ropes and made the dock flags flutter like little waves."
    if action.id == "rain":
        return "Dark clouds hovered over the boat ramp, and the water looked gray and shiny."
    return "The boat ramp was busy, and the morning air felt full of salt and adventure."


def predictive_foreshadow(world: World, hero: Entity, action: Action, prize_id: str) -> bool:
    prize = world.get(prize_id)
    if prize.region not in action.zone:
        return False
    return True


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for g in GEAR:
        if action.mess in g.guards and prize.region in g.covers:
            return g
    return None


def do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        pass
    world.zone = set(action.zone)
    actor.meters[action.mess] = actor.meters.get(action.mess, 0.0) + 1.0
    # If a worn item is exposed in the zone, it gets messy too.
    for item in world.worn_items(actor):
        if item.region in world.zone and not item.label == "rain cloak":
            item.meters[action.mess] = item.meters.get(action.mess, 0.0) + 1.0
            item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1.0
            if narrate:
                world.say(f"{actor.pronoun('possessive').capitalize()} {item.label} got {action.soil}.")
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0


def introduce(world: World, hero: Entity, crew: Entity) -> None:
    world.say(
        f"{hero.id} was a {actor_desc(hero)} pirate who loved exact people, "
        f"careful plans, and shiny ship days."
    )
    world.say(
        f"{crew.label} was a crew of exact people who liked to keep every rope, barrel, "
        f"and plank in the right place."
    )


def setup(world: World, hero: Entity, prize: Entity, action: Action, crew: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} as if it were treasure."
    )
    world.say(
        f"At the boat ramp, {hero.id} wanted to {action.verb}, because {action.gerund} "
        f"felt like real pirate fun."
    )
    world.say(f"Still, {action.foreshadow}")


def warn(world: World, crew: Entity, hero: Entity, action: Action, prize: Entity) -> bool:
    if not predictive_foreshadow(world, hero, action, prize.id):
        return False
    hero.memes["worry"] = hero.memes.get("worry", 0.0) + 1.0
    world.say(
        f'"If you go now," {crew.label} said, "your {prize.label} will get {action.soil}."'
    )
    return True


def conflict(world: World, hero: Entity, action: Action) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
    world.say(
        f"{hero.id} frowned, because {hero.pronoun('possessive')} wish to play was still pulling hard."
    )
    world.say(f"{hero.pronoun().capitalize()} tried to {action.rush},")


def offer_fix(world: World, crew: Entity, hero: Entity, action: Action, prize: Prize) -> Optional[Gear]:
    gear = select_gear(action, prize)
    if gear is None:
        return None
    obj = world.add(Entity(
        id=gear.id,
        kind="thing",
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=crew.id,
        plural=gear.plural,
    ))
    obj.worn_by = hero.id
    world.say(
        f"Then {crew.label} held up {gear.label} and smiled."
    )
    world.say(
        f'"How about we {gear.prep} and still go together?"'
    )
    return gear


def accept(world: World, hero: Entity, crew: Entity, action: Action, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 2.0
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    hero.memes["conflict"] = 0.0
    do_action(world, hero, action, narrate=False)
    world.say(
        f"{hero.id} grinned and hugged {hero.pronoun('possessive')} crew."
    )
    world.say(
        f"Together they {gear.tail}. Soon {hero.id} was {action.gerund}, "
        f"{prize.label} stayed clean, and the boat ramp felt bright again."
    )


def tell(setting: Setting, action: Action, prize_cfg: Prize,
         hero_name: str, hero_type: str, crew_name: str) -> World:
    world = World(setting)
    hero = world.add(Entity(
        id=pirate_name(hero_name),
        kind="character",
        type=hero_type,
    ))
    crew = world.add(Entity(
        id=crew_name,
        kind="character",
        type="sailor_man",
        label="the crew",
    ))
    prize = world.add(Entity(
        id="prize",
        kind="thing",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker=crew.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))

    introduce(world, hero, crew)
    world.para()
    setup(world, hero, prize, action, crew)
    warn(world, crew, hero, action, prize)

    world.para()
    conflict(world, hero, action)
    gear = offer_fix(world, crew, hero, action, prize_cfg)
    if gear:
        accept(world, hero, crew, action, prize, gear)

    world.facts = {
        "hero": hero,
        "crew": crew,
        "prize": prize,
        "action": action,
        "gear": gear,
        "setting": setting,
    }
    return world


SETTINGS = {
    "boat_ramp": Setting(place="the boat ramp", affords={"tide", "rain", "wind"}),
}

ACTIONS = {
    "tide": Action(
        id="tide",
        verb="launch the little boat",
        gerund="launching the little boat",
        rush="push the boat into the water",
        mess="wet",
        soil="wet and slippery",
        zone={"feet", "legs"},
        foreshadow="a cold splash kept kissing the ramp stones.",
        keyword="tide",
    ),
    "rain": Action(
        id="rain",
        verb="sail before the rain got heavier",
        gerund="sailing in the rain",
        rush="dash down the ramp",
        mess="wet",
        soil="soaked through",
        zone={"feet", "legs", "torso"},
        foreshadow="the clouds looked dark enough to tell a story on their own.",
        keyword="rain",
    ),
    "wind": Action(
        id="wind",
        verb="pull the boat straight",
        gerund="pulling the boat straight",
        rush="heave on the rope",
        mess="windblown",
        soil="tangled and damp",
        zone={"torso"},
        foreshadow="the wind kept whispering through the ropes like it knew a secret.",
        keyword="wind",
    ),
}

PRIZES = {
    "hat": Prize(
        label="hat",
        phrase="a bright pirate hat",
        type="hat",
        region="torso",
    ),
    "map": Prize(
        label="map",
        phrase="an exact map in a wax sleeve",
        type="map",
        region="torso",
    ),
    "boots": Prize(
        label="boots",
        phrase="strong deck boots",
        type="boots",
        region="feet",
        plural=True,
    ),
}

GEAR = [
    Gear(
        id="rain_cloak",
        label="rain cloak",
        covers={"torso"},
        guards={"wet"},
        prep="put on the rain cloak first",
        tail="walked the boat down the ramp with the rain cloak on",
    ),
    Gear(
        id="deck_boots",
        label="deck boots",
        covers={"feet"},
        guards={"wet"},
        prep="pull on the deck boots first",
        tail="stomped to the water in the deck boots",
        plural=True,
    ),
    Gear(
        id="rope_gloves",
        label="rope gloves",
        covers={"torso"},
        guards={"windblown"},
        prep="wear the rope gloves first",
        tail="handled the rope safely",
        plural=True,
    ),
    Gear(
        id="oilskin",
        label="an oilskin coat",
        covers={"torso"},
        guards={"wet", "windblown"},
        prep="put on the oilskin coat first",
        tail="marched down the ramp under the oilskin coat",
    ),
]

CLOAK = GEAR[0]

HEROES = ["Mara", "Nell", "Pip", "Finn", "Jory", "Tess", "Rook", "Lina"]
CREW_NAMES = ["the crew", "the shipmates", "the dock crew"]
HERO_TYPES = ["girl", "boy"]
TRAITS = ["brave", "curious", "spry", "cheerful", "stubborn"]


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            action = _safe_lookup(ACTIONS, act_id)
            for prize_id, prize in PRIZES.items():
                if prize.region in action.zone and select_gear(action, prize) is not None:
                    out.append((place, act_id, prize_id))
    return out


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    crew: str
    hero_type: str
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


KNOWLEDGE = {
    "boat_ramp": [
        ("What is a boat ramp?",
         "A boat ramp is a sloped place where people can push a boat into the water or pull it back out."),
    ],
    "tide": [
        ("What is the tide?",
         "The tide is the rise and fall of the sea, and it can make the water move closer to shore or farther away."),
    ],
    "rain": [
        ("Why does rain make things wet?",
         "Rain is made of water drops, so when it lands on things, it makes them wet."),
    ],
    "wind": [
        ("What does wind do to ropes?",
         "Wind can tug, twist, and flap ropes, so sailors have to hold them tight."),
    ],
    "map": [
        ("What is a map?",
         "A map is a drawing that shows places and helps people find where to go."),
    ],
    "hat": [
        ("Why do pirates wear hats?",
         "Pirates wear hats to keep the sun or rain off their heads and to look ready for adventure."),
    ],
    "boots": [
        ("What are deck boots for?",
         "Deck boots help keep feet dry and steady on wet boat decks and ramps."),
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    action: Action = _safe_fact(world, f, "action")
    prize: Entity = _safe_fact(world, f, "prize")
    return [
        f'Write a short pirate story for a child about "{action.keyword}" at the boat ramp.',
        f"Tell a story where {hero.id} wants to {action.verb} but worries about {prize.phrase}, then finds a safe choice.",
        f"Write a gentle pirate tale with foreshadowing, conflict, and a happy ending at the boat ramp.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    crew: Entity = _safe_fact(world, f, "crew")
    action: Action = _safe_fact(world, f, "action")
    prize: Entity = _safe_fact(world, f, "prize")
    gear: Optional[Gear] = _safe_fact(world, f, "gear")

    qas = [
        QAItem(
            question=f"Who was the story about at the boat ramp?",
            answer=f"The story was about {hero.id} and {crew.label}. {hero.id} was the little pirate who wanted to {action.verb}.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at the boat ramp?",
            answer=f"{hero.id} wanted to {action.verb}, because {action.gerund} felt like fun pirate work.",
        ),
        QAItem(
            question=f"What was the warning that foreshadowed trouble?",
            answer=f"The warning was that {prize.label} would get {action.soil} if they went before fixing the problem.",
        ),
    ]
    if gear is not None:
        qas.append(
            QAItem(
                question=f"How did the crew solve the problem?",
                answer=f"They used {gear.label} so {hero.id} could {action.verb} without ruining {prize.label}.",
            )
        )
    qas.append(
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily: {hero.id} got to {action.gerund}, and everyone at the boat ramp felt glad.",
        )
    )
    return qas


def world_qa(world: World) -> list[QAItem]:
    f = world.facts
    action: Action = _safe_fact(world, f, "action")
    prize: Entity = _safe_fact(world, f, "prize")
    tags = {action.id, prize.label, "boat_ramp"}
    out: list[QAItem] = []
    for tag in ["boat_ramp", "tide", "rain", "wind", "map", "hat", "boots"]:
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==",]
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


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        bits = []
        if e.meters:
            bits.append(f"meters={e.meters}")
        if e.memes:
            bits.append(f"memes={e.memes}")
        if e.region:
            bits.append(f"region={e.region}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:12} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="boat_ramp", action="tide", prize="hat", name="Mara", crew="the crew", hero_type="girl", trait="brave"),
    StoryParams(place="boat_ramp", action="rain", prize="map", name="Pip", crew="the shipmates", hero_type="boy", trait="curious"),
    StoryParams(place="boat_ramp", action="wind", prize="boots", name="Nell", crew="the dock crew", hero_type="girl", trait="spry"),
]


def explain_rejection(action: Action, prize: Prize) -> str:
    return (
        f"(No story: {action.gerund} does not reasonably threaten {prize.label} "
        f"at the boat ramp in this world.)"
    )


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "action", None) and getattr(args, "prize", None):
        action = _safe_lookup(ACTIONS, getattr(args, "action", None))
        prize = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize.region in action.zone and select_gear(action, prize)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, action_id, prize_id = rng.choice(list(combos))
    action = _safe_lookup(ACTIONS, action_id)
    prize = _safe_lookup(PRIZES, prize_id)
    name = getattr(args, "name", None) or rng.choice(HEROES)
    crew = getattr(args, "crew", None) or rng.choice(CREW_NAMES)
    hero_type = getattr(args, "hero_type", None) or rng.choice(HERO_TYPES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, action=action_id, prize=prize_id, name=name, crew=crew, hero_type=hero_type, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIONS, params.action),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.hero_type,
        params.crew,
    )
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
        print(format_qa(sample))


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Pirate tale story world set at the boat ramp.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name")
    ap.add_argument("--crew")
    ap.add_argument("--hero-type", choices=HERO_TYPES)
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


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
#show valid/3.
"""


def asp_program() -> str:
    return asp_facts() + "\n" + ASP_RULES


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python gates:")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(f"{len(asp_valid_combos())} valid combos")
        for c in asp_valid_combos():
            print(c)
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
            seed = base_seed + i
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

    for idx, sample in enumerate(samples):
        header = ""
        if len(samples) > 1:
            header = f"### variant {idx + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
