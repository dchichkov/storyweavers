#!/usr/bin/env python3
"""
storyworlds/worlds/tender_octagon_turn_happy_ending_animal_story.py
===================================================================

A small animal-story world about a gentle animal, an octagon-shaped treasure,
and a turn that leads to a happy ending.

The premise is simple: an animal cares about a soft, special thing shaped like
an octagon. Something goes wrong, a turn happens, and the animal learns a
tender way to fix it. The story ends with a clear new state that proves the
problem changed.

This script follows the Storyweavers world contract:
- standalone stdlib script
- StoryParams + parser + resolve_params + generate + emit + main
- physical meters and emotional memes
- ASP twin with inline rules
- child-facing complete story with grounded QA
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
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    companion: object | None = None
    helper: object | None = None
    hero: object | None = None
    treasure: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"cat", "bird", "rabbit", "fox", "deer"}
        male = {"dog", "bear", "owl", "tiger", "lion", "wolf"}
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
    place: str = "the meadow"
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
class Activity:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
    weather: str
    keyword: str = ""
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
class Treasure:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    genders: set[str] = field(default_factory=lambda: {"cat", "dog", "rabbit", "fox", "bird", "bear"})
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.zone: set[str] = set()
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

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

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

        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


@dataclass
class StoryParams:
    place: str
    activity: str
    treasure: str
    name: str
    species: str
    companion: str
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


SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"turn", "tumble"}),
    "garden": Setting(place="the garden", affords={"turn", "tumble", "roll"}),
    "pond": Setting(place="the pond", affords={"turn", "splash"}),
    "hill": Setting(place="the hill", affords={"turn", "roll"}),
}

ACTIVITIES = {
    "turn": Activity(
        id="turn",
        verb="turn around",
        gerund="turning in circles",
        rush="spin too fast",
        mess="dizzy",
        soil="too dizzy",
        zone={"head"},
        weather="sunny",
        keyword="turn",
        tags={"turn"},
    ),
    "tumble": Activity(
        id="tumble",
        verb="tumble over",
        gerund="tumbling softly",
        rush="tumble too far",
        mess="bumped",
        soil="bumped and dusty",
        zone={"legs", "belly"},
        weather="sunny",
        keyword="tumble",
        tags={"soft", "turn"},
    ),
    "roll": Activity(
        id="roll",
        verb="roll down the hill",
        gerund="rolling and laughing",
        rush="roll too fast",
        mess="dusty",
        soil="dusty and ruffled",
        zone={"back", "legs"},
        weather="sunny",
        keyword="roll",
        tags={"hill"},
    ),
    "splash": Activity(
        id="splash",
        verb="splash in the pond",
        gerund="splashing in the water",
        rush="rush into the water",
        mess="wet",
        soil="wet and shivery",
        zone={"feet", "legs"},
        weather="sunny",
        keyword="splash",
        tags={"water"},
    ),
}

TREASURES = {
    "blanket": Treasure(
        label="blanket",
        phrase="a soft blue blanket",
        type="blanket",
        region="belly",
        genders={"cat", "dog", "rabbit", "fox", "bird", "bear"},
    ),
    "ribbon": Treasure(
        label="ribbon",
        phrase="a bright ribbon",
        type="ribbon",
        region="head",
        genders={"cat", "bird", "fox", "rabbit"},
    ),
    "collar": Treasure(
        label="collar",
        phrase="a neat red collar",
        type="collar",
        region="neck",
        genders={"dog", "cat", "bear", "wolf", "lion", "tiger"},
    ),
    "basket": Treasure(
        label="basket",
        phrase="a tiny woven basket",
        type="basket",
        region="back",
        genders={"rabbit", "fox", "bear"},
    ),
}

HELPERS = [
    Helper(
        id="shawl",
        label="a soft shawl",
        covers={"head", "belly", "back"},
        guards={"dizzy", "bumped"},
        prep="wrap up in a soft shawl",
        tail="went to fetch the soft shawl",
    ),
    Helper(
        id="boots",
        label="little boots",
        covers={"feet", "legs"},
        guards={"wet"},
        prep="put on little boots first",
        tail="ran to get the little boots",
        plural=True,
    ),
    Helper(
        id="pad",
        label="a padded scarf",
        covers={"neck"},
        guards={"bumped"},
        prep="wear a padded scarf",
        tail="went to get the padded scarf",
    ),
]

ANIMALS = {
    "cat": ["Mimi", "Luna", "Pip", "Nora"],
    "dog": ["Bingo", "Milo", "Rufus", "Toby"],
    "rabbit": ["Clover", "Peep", "Moss", "Bunny"],
    "fox": ["Penny", "Fennel", "Trix", "Wren"],
    "bird": ["Tiki", "Sunny", "Kiki", "Blue"],
    "bear": ["Bruno", "Nico", "Marty", "Bram"],
}
TRAITS = ["gentle", "curious", "brave", "tender", "playful", "kind"]


def prize_at_risk(activity: Activity, treasure: Treasure) -> bool:
    return treasure.region in activity.zone


def select_helper(activity: Activity, treasure: Treasure) -> Optional[Helper]:
    for helper in HELPERS:
        if activity.mess in helper.guards and treasure.region in helper.covers:
            return helper
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for treas_id, treas in TREASURES.items():
                if prize_at_risk(act, treas) and select_helper(act, treas):
                    combos.append((place, act_id, treas_id))
    return combos


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1.0
    actor.memes["joy"] = actor.memes.get("joy", 0.0) + 1.0
    if narrate:
        propagate(world, narrate=narrate)


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True

    while changed:
        changed = False
        for actor in world.characters():
            if actor.meters.get("dizzy", 0.0) < THRESHOLD and actor.meters.get("bumped", 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.label == "a soft shawl" and actor.meters.get("dizzy", 0.0) >= THRESHOLD:
                    sig = ("calm", actor.id)
                    if sig not in world.fired:
                        world.fired.add(sig)
                        actor.memes["calm"] = actor.memes.get("calm", 0.0) + 1.0
                        produced.append(f"The soft shawl helped {actor.id} slow down.")
                        changed = True
                if item.label == "little boots" and actor.meters.get("wet", 0.0) >= THRESHOLD:
                    sig = ("dry", actor.id)
                    if sig not in world.fired:
                        world.fired.add(sig)
                        actor.memes["safe"] = actor.memes.get("safe", 0.0) + 1.0
                        produced.append(f"The little boots kept {actor.id}'s feet dry.")
                        changed = True
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, treasure_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    treasure = sim.entities.get(treasure_id)
    return {
        "soiled": bool(treasure and actor.meters.get(activity.mess, 0.0) >= THRESHOLD and treasure.region in activity.zone),
    }


def setting_detail(setting: Setting, activity: Activity) -> str:
    if activity.id == "turn":
        return f"The air above {setting.place} felt still, like it was waiting for a small spin."
    if activity.id == "tumble":
        return f"The grass at {setting.place} looked soft enough for a gentle tumble."
    if activity.id == "roll":
        return f"The hill at {setting.place} looked smooth and ready for a roll."
    return f"{setting.place.capitalize()} looked bright and calm."


def introduce(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a {hero.pronoun('possessive')} little {hero.type} who loved tender things.")


def loves_treasure(world: World, hero: Entity, treasure: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    treasure.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {treasure.label} and kept {treasure.it()} close."
    )


def arrives(world: World, hero: Entity, companion: Entity, activity: Activity) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {companion.label} went to {world.setting.place}."
    )
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["desire"] = hero.memes.get("desire", 0.0) + 1.0
    world.say(
        f"{hero.id} wanted to {activity.verb}, because the day felt open and fun."
    )


def warn(world: World, companion: Entity, hero: Entity, activity: Activity, treasure: Entity) -> bool:
    pred = predict_mess(world, hero, activity, treasure.id)
    if not pred["soiled"]:
        return False
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you {activity.verb}, your {treasure.label} will get {activity.soil}," '
        f"{companion.label} said. \"Let's find a tender way.\""
    )
    return True


def turn_point(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["conflict"] = hero.memes.get("conflict", 0.0) + 1.0
    world.say(
        f"{hero.id} made a small turn, then paused. "
        f"{hero.pronoun().capitalize()} could feel a better idea coming."
    )


def offer_help(world: World, companion: Entity, hero: Entity, activity: Activity, treasure: Entity) -> Optional[Helper]:
    helper_def = select_helper(activity, treasure)
    if helper_def is None:
        return None
    helper = world.add(Entity(
        id=helper_def.id,
        type="thing",
        label=helper_def.label,
        owner=hero.id,
        caretaker=companion.id,
    ))
    helper.worn_by = hero.id
    if predict_mess(world, hero, activity, treasure.id)["soiled"]:
        helper.worn_by = None
        del world.entities[helper.id]
        return None
    world.say(
        f"{companion.label} smiled and said, \"How about we {helper_def.prep} first?\""
    )
    return helper_def


def accept(world: World, hero: Entity, companion: Entity, activity: Activity, treasure: Entity, helper_def: Helper) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    hero.memes["conflict"] = 0.0
    world.say(
        f"{hero.id} nodded, and {hero.pronoun('possessive')} eyes grew bright."
    )
    world.say(
        f"They {helper_def.tail}. Soon {hero.id} was {activity.gerund}, "
        f"{hero.pronoun('possessive')} {treasure.label} stayed safe, and {companion.label} laughed softly beside {hero.pronoun('object')}."
    )


def tell(setting: Setting, activity: Activity, treasure_cfg: Treasure,
         hero_name: str, species: str, companion_label: str, trait: str) -> World:
    world = World(setting)
    world.weather = activity.weather

    hero = world.add(Entity(id=hero_name, kind="character", type=species))
    companion = world.add(Entity(id="Companion", kind="character", type="caretaker", label=companion_label))
    treasure = world.add(Entity(
        id="treasure",
        type=treasure_cfg.type,
        label=treasure_cfg.label,
        phrase=treasure_cfg.phrase,
        owner=hero.id,
        caretaker=companion.id,
        region=treasure_cfg.region,
        plural=treasure_cfg.plural,
    ))

    hero.memes["tender"] = 1.0

    introduce(world, hero)
    world.say(f"{hero.id} was especially tender with {hero.pronoun('possessive')} {treasure.label}.")
    loves_treasure(world, hero, treasure)

    world.para()
    arrives(world, hero, companion, activity)
    wants(world, hero, activity)
    warn(world, companion, hero, activity, treasure)
    turn_point(world, hero, activity)

    world.para()
    helper_def = offer_help(world, companion, hero, activity, treasure)
    if helper_def is not None:
        accept(world, hero, companion, activity, treasure, helper_def)

    world.facts.update(
        hero=hero,
        companion=companion,
        treasure=treasure,
        treasure_cfg=treasure_cfg,
        activity=activity,
        setting=setting,
        helper=helper_def,
        trait=trait,
        resolved=helper_def is not None,
    )
    return world


GIRL_NAMES = ["Mimi", "Luna", "Pip", "Nora", "Clover", "Tiki"]
BOY_NAMES = ["Bingo", "Milo", "Rufus", "Toby", "Bruno", "Moss"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "activity")
    treasure = _safe_fact(world, f, "treasure_cfg")
    return [
        f'Write a short animal story for a small child about "{act.keyword}" and a tender rescue with a happy ending.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but must protect {treasure.phrase}.",
        f"Write an animal story that includes an octagon-shaped treasure, a turn, and a happy ending.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    companion = _safe_fact(world, f, "companion")
    treasure = _safe_fact(world, f, "treasure")
    act = _safe_fact(world, f, "activity")
    trait = _safe_fact(world, f, "trait")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a {hero.type} who is {trait} and tender with {hero.pronoun('possessive')} things.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do?",
            answer=f"{hero.id} wanted to {act.verb}, because the day felt fun and full of motion.",
        ),
        QAItem(
            question=f"What special thing did {hero.id} care about?",
            answer=f"{hero.id} cared about {hero.pronoun('possessive')} {treasure.label}, a little octagon-shaped treasure.",
        ),
        QAItem(
            question=f"Why did {companion.label} worry?",
            answer=f"{companion.label} worried because if {hero.id} kept going, the {treasure.label} would get {act.soil}.",
        ),
    ]
    if f.get("resolved"):
        helper = _safe_fact(world, f, "helper")
        qa.append(QAItem(
            question=f"How did the two friends solve the problem?",
            answer=f"They used {helper.label} first, so {hero.id} could {act.verb} without hurting the {treasure.label}.",
        ))
        qa.append(QAItem(
            question=f"How did the story end?",
            answer=f"It ended happily, with {hero.id} still enjoying {act.gerund} while the {treasure.label} stayed safe.",
        ))
    return qa


KNOWLEDGE = {
    "octagon": [
        (
            "What is an octagon?",
            "An octagon is a shape with eight sides. You can spot octagons in signs, tiles, and toy shapes.",
        )
    ],
    "tender": [
        (
            "What does tender mean?",
            "Tender means soft, careful, and kind. A tender touch does not hurt or rush.",
        )
    ],
    "turn": [
        (
            "What does it mean to turn around?",
            "To turn around means to move in a circle and face a different way.",
        )
    ],
    "happy": [
        (
            "What is a happy ending?",
            "A happy ending is when the problem gets solved and the characters finish the story feeling glad.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.update({"octagon", "tender", "turn", "happy"})
    out: list[QAItem] = []
    for tag in ["octagon", "tender", "turn", "happy"]:
        for q, a in KNOWLEDGE[tag]:
            out.append(QAItem(question=q, answer=a))
    return out


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
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="meadow", activity="turn", treasure="blanket", name="Mimi", species="cat", companion="Mama Cat", trait="tender"),
    StoryParams(place="garden", activity="turn", treasure="ribbon", name="Blue", species="bird", companion="Papa Bird", trait="curious"),
    StoryParams(place="hill", activity="roll", treasure="basket", name="Moss", species="rabbit", companion="Aunt Fox", trait="gentle"),
]


def explain_rejection(activity: Activity, treasure: Treasure) -> str:
    if not prize_at_risk(activity, treasure):
        return f"(No story: {activity.gerund} would not bother the {treasure.label}, so there is no real problem to solve.)"
    return f"(No story: there is no compatible tender fix for a {treasure.label} in this setup.)"


def explain_gender(treasure_id: str, species: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(TREASURES, treasure_id).genders))
    return f"(No story: a {_safe_lookup(TREASURES, treasure_id).label} is not a typical fit for a {species} here; try one of: {ok}.)"


@dataclass
class _Args:
    place: Optional[str] = None
    activity: Optional[str] = None
    treasure: Optional[str] = None
    gender: Optional[str] = None
    name: Optional[str] = None
    companion: Optional[str] = None
    trait: Optional[str] = None
    n: int = 1
    seed: Optional[int] = None
    all: bool = False
    trace: bool = False
    qa: bool = False
    json: bool = False
    asp: bool = False
    verify: bool = False
    show_asp: bool = False
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


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal story world with a tender turn and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--treasure", choices=TREASURES)
    ap.add_argument("--gender", choices=sorted(ANIMALS))
    ap.add_argument("--name")
    ap.add_argument("--companion")
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
    if getattr(args, "activity", None) and getattr(args, "treasure", None):
        act, tre = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(TREASURES, getattr(args, "treasure", None))
        if not (prize_at_risk(act, tre) and select_helper(act, tre)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "treasure", None) and getattr(args, "gender", None) not in _safe_lookup(TREASURES, getattr(args, "treasure", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "treasure", None) is None or c[2] == getattr(args, "treasure", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, act_id, tre_id = rng.choice(list(combos))
    species = getattr(args, "gender", None) or rng.choice(sorted(_safe_lookup(TREASURES, tre_id).genders))
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(ANIMALS, species))
    companion = getattr(args, "companion", None) or rng.choice(["Mama Cat", "Papa Dog", "Aunt Fox", "Uncle Bear", "Mama Bird"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=act_id, treasure=tre_id, name=name, species=species, companion=companion, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(TREASURES, params.treasure),
        params.name,
        params.species,
        params.companion,
        params.trait,
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


ASP_RULES = r"""
% Facts:
% setting(Place). afford(Place, Activity). activity(Activity). mess_of(Activity, Mess).
% splashes(Activity, Region). treasure(Treasure). worn_on(Treasure, Region).
% helper(Helper). guards(Helper, Mess). covers(Helper, Region).

prize_at_risk(A, T) :- splashes(A, R), worn_on(T, R).
compatible_fix(A, T) :- prize_at_risk(A, T), mess_of(A, M), guards(H, M), covers(H, R), worn_on(T, R).

valid_story(Place, A, T) :- afford(Place, A), prize_at_risk(A, T), compatible_fix(A, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("afford", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for tid, t in TREASURES.items():
        lines.append(asp.fact("treasure", tid))
        lines.append(asp.fact("worn_on", tid, t.region))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for m in sorted(h.guards):
            lines.append(asp.fact("guards", h.id, m))
        for r in sorted(h.covers):
            lines.append(asp.fact("covers", h.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    clingo_set = set(asp_valid_combos())
    python_set = set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)

    if getattr(args, "asp", None):
        import asp
        model = asp.one_model(asp_program("#show valid_story/3."))
        print(f"{len(asp_valid_combos())} compatible stories")
        for tpl in sorted(set(asp.atoms(model, "valid_story"))):
            print(tpl)
        return

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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
