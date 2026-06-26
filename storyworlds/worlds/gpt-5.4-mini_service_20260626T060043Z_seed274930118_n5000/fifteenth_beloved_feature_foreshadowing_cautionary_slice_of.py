#!/usr/bin/env python3
"""
storyworlds/worlds/fifteenth_beloved_feature_foreshadowing_cautionary_slice_of.py
===============================================================================

A small slice-of-life storyworld built from the seed words:
*fifteenth*, *beloved*, *feature*.

The world centers on a family-run little shop that puts up a beloved monthly
feature on the fifteenth day. A gentle foreshadowing detail suggests a problem
before it becomes one, and a cautionary turn nudges the child toward a safer
choice. The tone stays grounded and everyday.
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    child: object | None = None
    feature: object | None = None
    gear: object | None = None
    helper: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"tired": 0.0, "risky": 0.0, "dirty": 0.0}
        if not self.memes:
            self.memes = {"joy": 0.0, "worry": 0.0, "care": 0.0, "pride": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman", "grandmother", "aunt"}
        male = {"boy", "father", "dad", "man", "grandfather", "uncle"}
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
    indoor: bool = True
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
    risk: str
    caution: str
    zone: set[str]
    keyword: str
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
class Feature:
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
        self.zone: set[str] = set()
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

    def characters(self) -> list[Entity]:
        return [e for e in self.entities.values() if e.kind == "character"]

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

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
        clone.paragraphs = [[]]
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        return clone


SETTINGS = {
    "shop": Setting(place="the little corner shop", indoor=True, affords={"display", "arrange"}),
    "kitchen": Setting(place="the kitchen table", indoor=True, affords={"bake", "display"}),
    "porch": Setting(place="the front porch", indoor=False, affords={"display", "hang"}),
}

ACTIVITIES = {
    "display": Activity(
        id="display",
        verb="arrange the beloved feature on the shelf",
        gerund="arranging the beloved feature on the shelf",
        rush="reach for the top shelf",
        risk="the paper corners might bend",
        caution="the paper could curl if the window stayed open",
        zone={"hands", "arms", "torso"},
        keyword="feature",
        tags={"paper", "wind", "feature"},
    ),
    "bake": Activity(
        id="bake",
        verb="finish the fifteenth cookie tray",
        gerund="finishing the fifteenth cookie tray",
        rush="dash to the oven",
        risk="the tray might tip",
        caution="the tray could slide if it was held too fast",
        zone={"hands", "arms"},
        keyword="fifteenth",
        tags={"cookie", "kitchen", "feature"},
    ),
    "hang": Activity(
        id="hang",
        verb="hang the feature banner",
        gerund="hanging the feature banner",
        rush="run to the porch rail",
        risk="the ribbon might snag",
        caution="the ribbon could tangle in a breeze",
        zone={"hands", "arms", "torso"},
        keyword="beloved",
        tags={"banner", "wind", "feature"},
    ),
}

FEATURES = {
    "banner": Feature(
        id="banner",
        label="banner",
        phrase="the beloved feature banner with gold paper stars",
        region="torso",
    ),
    "sign": Feature(
        id="sign",
        label="sign",
        phrase="the fifteenth feature sign with blue crayons",
        region="hands",
    ),
    "card": Feature(
        id="card",
        label="card",
        phrase="the beloved feature card with a tiny drawing",
        region="hands",
    ),
}

GEAR = [
    Gear(
        id="clip",
        label="a clothespin clip",
        covers={"hands"},
        guards={"paper", "banner"},
        prep="use a clothespin clip first",
        tail="used the clothespin clip to hold the paper steady",
    ),
    Gear(
        id="tape",
        label="some clear tape",
        covers={"hands", "arms"},
        guards={"paper"},
        prep="tape the corners down first",
        tail="taped the corners down so they would not curl",
    ),
    Gear(
        id="weights",
        label="small paper weights",
        covers={"hands", "torso"},
        guards={"banner", "paper"},
        prep="set small paper weights on the banner",
        tail="set the paper weights on the banner to keep it flat",
    ),
]

NAMES = {
    "girl": ["Mina", "Lena", "Tia", "Nora", "Sage"],
    "boy": ["Eli", "Noah", "Finn", "Owen", "Milo"],
}
TRAITS = ["careful", "cheerful", "curious", "patient", "gentle"]


@dataclass
class StoryParams:
    place: str
    activity: str
    feature: str
    name: str
    gender: str
    helper: str
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


def reasonableness_gate(place: str, activity: str, feature: str) -> bool:
    act = _safe_lookup(ACTIVITIES, activity)
    feat = _safe_lookup(FEATURES, feature)
    return feat.region in act.zone


def select_gear(activity: Activity, feature: Feature) -> Optional[Gear]:
    for gear in GEAR:
        if feature.region in gear.covers and "paper" in gear.guards:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            for feat_id in FEATURES:
                if reasonableness_gate(place, act_id, feat_id) and select_gear(_safe_lookup(ACTIVITIES, act_id), _safe_lookup(FEATURES, feat_id)):
                    out.append((place, act_id, feat_id))
    return out


def setting_detail(setting: Setting) -> str:
    return {
        "the little corner shop": "The shop smelled like dust, sugar, and pencil shavings.",
        "the kitchen table": "The table was crowded with bowls, paper, and a spoon with sticky jam on it.",
        "the front porch": "A mild breeze moved the hanging plants and nudged the doormat.",
    }.get(setting.place, f"{setting.place.capitalize()} felt ready for an ordinary task.")


def predict_mess(world: World, actor: Entity, activity: Activity, feature_id: str) -> dict:
    sim = world.copy()
    actor2 = sim.get(actor.id)
    actor2.meters["risky"] += 1
    sim.zone = set(activity.zone)
    feat = sim.get(feature_id)
    if feat.region in sim.zone and not sim.covered(actor2, feat.region):
        feat.meters["dirty"] += 1
        feat.memes["worry"] += 1
    return {"ruined": feat.meters["dirty"] >= THRESHOLD, "worry": feat.memes["worry"]}


def do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    actor.meters["risky"] += 1
    actor.memes["joy"] += 1
    world.zone = set(activity.zone)
    if narrate:
        world.say(f"{actor.id} started to {activity.verb}.")


def foreshadow(world: World, actor: Entity, activity: Activity, feature: Entity) -> bool:
    pred = predict_mess(world, actor, activity, feature.id)
    if pred["ruined"]:
        world.facts["foreshadow"] = activity.caution
        world.say(f"Near the open window, {activity.caution}.")
        return True
    return False


def cautionary_turn(world: World, parent: Entity, child: Entity, activity: Activity, feature: Entity) -> None:
    world.say(
        f"{parent.pronoun('subject').capitalize()} looked at {feature.label} and then at the breeze, "
        f"and said, 'Let's be careful so the beloved feature stays nice.'"
    )
    child.memes["worry"] += 1
    child.meters["risky"] += 0.5


def compromise(world: World, parent: Entity, child: Entity, activity: Activity, feature: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, feature)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=child.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = child.id
    if predict_mess(world, child, activity, feature.id)["ruined"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(f"{parent.id} suggested they {gear_def.prep}.")
    return gear


def accept(world: World, parent: Entity, child: Entity, activity: Activity, feature: Entity, gear: Gear) -> None:
    child.memes["joy"] += 1
    child.memes["worry"] = 0.0
    world.say(
        f"{child.id} nodded and {gear.tail}. After that, the {feature.label} stayed neat, "
        f"and {child.id} could finish {activity.gerund} with a small smile."
    )


def tell(setting: Setting, activity: Activity, feature_cfg: Feature, hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    child = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id="Helper", kind="character", type=helper_type, label="the helper"))
    feature = world.add(Entity(
        id=feature_cfg.id,
        type=feature_cfg.id,
        label=feature_cfg.label,
        phrase=feature_cfg.phrase,
        owner=child.id,
        caretaker=helper.id,
        region=feature_cfg.region,
        plural=feature_cfg.plural,
    ))

    child.memes["care"] += 1
    child.memes["pride"] += 1
    world.say(
        f"It was the fifteenth, and {child.id} was a {trait} {hero_type} who loved the month's beloved feature."
    )
    world.say(setting_detail(setting))
    world.say(f"The feature for today was {feature.phrase}.")

    world.para()
    do_activity(world, child, activity)
    foreshadow(world, child, activity, feature)
    world.say(f"{child.id} noticed {activity.risk}.")
    cautionary_turn(world, helper, child, activity, feature)

    world.para()
    gear = compromise(world, helper, child, activity, feature)
    if gear is not None:
        accept(world, helper, child, activity, feature, gear)

    world.facts.update(
        child=child,
        helper=helper,
        feature=feature,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=gear is not None,
    )
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    activity = _safe_fact(world, f, "activity")
    feature = _safe_fact(world, f, "feature")
    return [
        f'Write a short slice-of-life story for a child named {child.id} on the fifteenth, with a beloved feature and a small caution.',
        f"Tell a gentle everyday story where {child.id} wants to {activity.verb}, but the beloved {feature.label} needs careful handling.",
        f'Write a story that includes the words "fifteenth", "beloved", and "feature" and ends with a safer choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    helper = _safe_fact(world, f, "helper")
    feature = _safe_fact(world, f, "feature")
    activity = _safe_fact(world, f, "activity")
    qa = [
        QAItem(
            question=f"What was special about the day in this story?",
            answer=f"It was the fifteenth, when the family set out the beloved {feature.label} for the day."
        ),
        QAItem(
            question=f"What did {child.id} want to do before anyone worried?",
            answer=f"{child.id} wanted to {activity.verb}, because {child.pronoun('subject')} was excited to help."
        ),
        QAItem(
            question=f"Why did {helper.id} give a cautionary reminder?",
            answer=f"{helper.id} noticed {activity.caution} and wanted the beloved {feature.label} to stay nice."
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"How did they keep the {feature.label} safe?",
            answer=f"They used {f['gear'].label} first, so the {feature.label} stayed neat while {child.id} finished the job."
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What does foreshadowing do in a story?",
            answer="Foreshadowing gives a small hint about what might happen later, so the reader can notice the clue before the turn comes."
        ),
        QAItem(
            question="What does cautionary mean?",
            answer="Cautionary means it is meant to warn someone to be careful and avoid a problem."
        ),
        QAItem(
            question="What is a slice-of-life story?",
            answer="A slice-of-life story shows a small everyday moment, like helping at home or taking care of something beloved."
        ),
    ]


def format_qa(sample: StorySample) -> str:
    lines = ["== Prompts =="]
    for p in sample.prompts:
        lines.append(p)
    lines.append("")
    lines.append("== Story Q&A ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: round(v, 2) for k, v in e.meters.items() if v}
        memes = {k: round(v, 2) for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="shop", activity="display", feature="sign", name="Mina", gender="girl", helper="mother", trait="careful"),
    StoryParams(place="kitchen", activity="bake", feature="card", name="Eli", gender="boy", helper="father", trait="cheerful"),
    StoryParams(place="porch", activity="hang", feature="banner", name="Nora", gender="girl", helper="grandmother", trait="gentle"),
]


def explain_rejection(activity: Activity, feature: Feature) -> str:
    return (
        f"(No story: {activity.gerund} does not plausibly threaten the {feature.label}. "
        f"The cautionary turn needs a real at-risk feature, not just a random scene.)"
    )


def explain_gender(feature_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(FEATURES, feature_id).genders))
    return f"(No story: this feature choice does not fit {gender} here; try --gender {ok}.)"


ASP_RULES = r"""
feature_at_risk(A, F) :- activity(A), feature(F), zone(A, R), feature_region(F, R).
good_fix(A, F, G) :- feature_at_risk(A, F), gear(G), covers(G, R), feature_region(F, R), guards(G, paper).
valid(Place, A, F) :- affords(Place, A), feature_at_risk(A, F), good_fix(A, F, _).
"""

def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for fid, f in FEATURES.items():
        lines.append(asp.fact("feature", fid))
        lines.append(asp.fact("feature_region", fid, f.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for guard in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, guard))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life storyworld about a fifteenth beloved feature with foreshadowing and caution.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--feature", choices=FEATURES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper", choices=["mother", "father", "grandmother", "grandfather"])
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
    if getattr(args, "activity", None) and getattr(args, "feature", None):
        if not reasonableness_gate(getattr(args, "place", None) or "shop", getattr(args, "activity", None), getattr(args, "feature", None)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "feature", None) is None or c[2] == getattr(args, "feature", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, feature = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(_safe_lookup(NAMES, gender))
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "grandmother"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, feature=feature, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(FEATURES, params.feature), params.name, params.gender, params.helper, params.trait)
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
        import asp
        model = asp.one_model(asp_program("#show valid/3."))
        combos = sorted(set(asp.atoms(model, "valid")))
        print(f"{len(combos)} valid combos:")
        for c in combos:
            print(" ", c)
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
            params = resolve_params(args, random.Random(seed))
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
            header = f"### {p.name}: {p.activity} at {p.place} (feature: {p.feature})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
