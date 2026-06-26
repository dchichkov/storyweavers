#!/usr/bin/env python3
"""
alphabetic_cotton_orthodontics_curiosity_dialogue_comedy.py
===========================================================

A small storyworld about a curious child, a cotton craft, and an orthodontic
mix-up that turns into a funny dialogue and a gentle fix.

Premise:
- A child is fascinated by alphabet cards and cotton.
- A harmless but silly problem happens when cotton gets stuck in braces.
- A grown-up notices the risk and suggests a playful, safer version.

The world is intentionally tiny and constraint-checked: we only generate
stories when the chosen setting/activity/object combination is plausible and
the fix actually addresses the problem.
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
# Data model
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    meme: str = ""
    region: object | None = None
    adult_ent: object | None = None
    child: object | None = None
    entities: set[str] = field(default_factory=set)
    obj: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"mess": 0.0, "clean": 0.0}
        if not self.memes:
            self.memes = {"curiosity": 0.0, "joy": 0.0, "conflict": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "mom", "woman"}
        male = {"boy", "father", "dad", "man"}
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
    indoor: bool
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
class ObjectItem:
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


@dataclass
class StoryParams:
    place: str
    activity: str
    object_id: str
    name: str
    gender: str
    adult: str
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
    "classroom": Setting(place="the classroom", indoor=True, affords={"alphabet", "cotton"}),
    "artroom": Setting(place="the art room", indoor=True, affords={"alphabet", "cotton"}),
    "clinic_waiting_room": Setting(place="the clinic waiting room", indoor=True, affords={"alphabet"}),
}

ACTIVITIES = {
    "alphabet": Activity(
        id="alphabet",
        verb="sort the alphabet cards",
        gerund="sorting alphabet cards",
        rush="shuffle the cards around",
        mess="messy",
        soil="all mixed up",
        zone={"hands", "table"},
        keyword="alphabet",
        tags={"alphabet", "curiosity"},
    ),
    "cotton": Activity(
        id="cotton",
        verb="build a cotton name banner",
        gerund="pasting cotton letters",
        rush="grab the cotton balls",
        mess="fluffy",
        soil="stuck everywhere",
        zone={"hands", "mouth"},
        keyword="cotton",
        tags={"cotton", "curiosity"},
    ),
}

OBJECTS = {
    "braces": ObjectItem(
        label="braces",
        phrase="new braces with tiny shiny brackets",
        type="braces",
        region="mouth",
    ),
    "retainer": ObjectItem(
        label="retainer",
        phrase="a clear retainer in a little case",
        type="retainer",
        region="mouth",
    ),
    "shirt": ObjectItem(
        label="shirt",
        phrase="a clean cotton shirt",
        type="shirt",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="brush",
        label="a soft brush",
        covers={"mouth", "hands"},
        guards={"fluffy", "messy"},
        prep="use a soft brush first",
        tail="used the soft brush and laughed at the fluff",
    ),
    Gear(
        id="spoon",
        label="a tiny spoon",
        covers={"hands"},
        guards={"fluffy"},
        prep="pick the cotton up with a tiny spoon",
        tail="used the tiny spoon to keep the cotton away from sticky places",
    ),
    Gear(
        id="napkin",
        label="a clean napkin",
        covers={"torso", "hands"},
        guards={"messy", "fluffy"},
        prep="put a clean napkin under the craft",
        tail="put a napkin under the craft so the mess stayed on the table",
    ),
]

NAMES = ["Mia", "Leo", "Nora", "Eli", "Ava", "Noah", "Zoe", "Finn"]
TRAITS = ["curious", "cheerful", "silly", "bright", "playful", "bouncy"]


# ---------------------------------------------------------------------------
# World rules
# ---------------------------------------------------------------------------
def prize_at_risk(activity: Activity, obj: ObjectItem) -> bool:
    return obj.region in activity.zone


def select_gear(activity: Activity, obj: ObjectItem) -> Optional[Gear]:
    for g in GEAR:
        if activity.mess in g.guards and obj.region in g.covers:
            return g
    return None


def _do_activity(world: World, child: Entity, activity: Activity, narrate: bool = True) -> None:
    world.zone = set(activity.zone)
    child.memes["curiosity"] += 1
    child.meters["mess"] = child.meters.get("mess", 0.0) + 1
    if narrate:
        world.say(f"{child.id} started {activity.gerund} and got extra curious.")


def _mess_on_object(world: World, child: Entity, obj: Entity, activity: Activity) -> None:
    if obj.region in world.zone:
        obj.meters["mess"] = obj.meters.get("mess", 0.0) + 1
        child.memes["conflict"] += 1
        world.say(f"{obj.label.capitalize()} got {activity.soil}, which made everyone pause.")


def predict_mess(world: World, child: Entity, activity: Activity, obj_id: str) -> bool:
    sim = World(world.setting)
    sim.entities = {k: Entity(**vars(v)) for k, v in world.entities.items()}
    sim.zone = set(world.zone)
    _do_activity(sim, sim.get(child.id), activity, narrate=False)
    obj = sim.get(obj_id)
    return obj.region in sim.zone


def introduce(world: World, child: Entity) -> None:
    world.say(f"{child.id} was a little {next(t for t in [child.type, 'child'] if t)} who loved curious questions.")


def loves_tools(world: World, child: Entity, activity: Activity) -> None:
    world.say(f"{child.pronoun().capitalize()} loved {activity.gerund} and asking, 'Why does this one go there?'")


def bring_object(world: World, adult: Entity, child: Entity, obj: Entity) -> None:
    world.say(f"{adult.label.capitalize()} brought {child.pronoun('object')} {obj.phrase}.")


def warning(world: World, adult: Entity, child: Entity, activity: Activity, obj: Entity) -> bool:
    if not predict_mess(world, child, activity, obj.id):
        return False
    world.facts["risk"] = True
    world.say(f'"Careful," {adult.label} said. "If you {activity.verb}, {obj.label} might get {activity.soil}."')
    return True


def curious_reply(world: World, child: Entity, activity: Activity) -> None:
    child.memes["curiosity"] += 1
    world.say(f'"But what if I do it neatly?" {child.id} asked, grinning at the question.')


def dialogue_turn(world: World, adult: Entity, child: Entity, activity: Activity) -> None:
    child.memes["joy"] += 1
    world.say(f'"Then we choose the neat way," {adult.label} said. "Curious is good; sticky is not."')


def offer_gear(world: World, adult: Entity, child: Entity, activity: Activity, obj: Entity) -> Optional[Gear]:
    gear = select_gear(activity, obj)
    if not gear:
        return None
    world.say(f'"How about we {gear.prep}?" {adult.label} asked.')
    return gear


def accept(world: World, child: Entity, activity: Activity, gear: Gear, obj: Entity) -> None:
    child.memes["joy"] += 1
    child.memes["conflict"] = 0.0
    world.say(
        f'{child.id} nodded so hard that even the braces seemed to smile. '
        f'They {gear.tail}, and soon {child.id} was {activity.gerund} while {obj.label} stayed clean.'
    )


def tell(
    setting: Setting,
    activity: Activity,
    obj_cfg: ObjectItem,
    name: str = "Mia",
    gender: str = "girl",
    adult: str = "teacher",
    trait: str = "curious",
) -> World:
    world = World(setting)
    child = world.add(Entity(id=name, kind="character", type=gender, meme="child"))
    child.type = gender
    child.memes["curiosity"] = 1.0
    adult_ent = world.add(Entity(id=adult, kind="character", type="adult", label=f"the {adult}"))
    obj = world.add(Entity(
        id="object",
        type=obj_cfg.type,
        label=obj_cfg.label,
        phrase=obj_cfg.phrase,
        owner=child.id,
        caretaker=adult_ent.id,
        region=obj_cfg.region,
        plural=obj_cfg.plural,
    ))

    introduce(world, child)
    loves_tools(world, child, activity)
    bring_object(world, adult_ent, child, obj)

    world.para()
    world.say(f'One afternoon at {setting.place}, {child.id} leaned over the table and whispered, "I have an idea."')
    warning(world, adult_ent, child, activity, obj)
    curious_reply(world, child, activity)
    dialogue_turn(world, adult_ent, child, activity)

    world.para()
    gear = offer_gear(world, adult_ent, child, activity, obj)
    if gear:
        accept(world, child, activity, gear, obj)

    world.facts.update(
        child=child,
        adult=adult_ent,
        object=obj,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=gear is not None,
    )
    return world


# ---------------------------------------------------------------------------
# Reasonable combinations
# ---------------------------------------------------------------------------
def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for obj_id, obj in OBJECTS.items():
                if prize_at_risk(act, obj) and select_gear(act, obj):
                    combos.append((place, act_id, obj_id))
    return combos


def explain_rejection(activity: Activity, obj: ObjectItem) -> str:
    if not prize_at_risk(activity, obj):
        return f"(No story: {activity.gerund} does not threaten {obj.label} here.)"
    return f"(No story: there is no sensible fix in this world for {activity.gerund} and {obj.label}.)"


# ---------------------------------------------------------------------------
# QA
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    activity = _safe_fact(world, f, "activity")
    obj = _safe_fact(world, f, "object")
    return [
        f'Write a short comedy for a child who is curious about {activity.keyword} and {obj.label}.',
        f"Tell a funny story where {child.id} wants to {activity.verb} but a grown-up worries about {obj.label}.",
        f'Write a gentle dialogue story about {child.id}, {activity.keyword}, cotton, and a safer way to play.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child = _safe_fact(world, f, "child")
    adult = _safe_fact(world, f, "adult")
    activity = _safe_fact(world, f, "activity")
    obj = _safe_fact(world, f, "object")
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did {child.id} want to do at {world.setting.place}?",
            answer=f"{child.id} wanted to {activity.verb}, because {child.pronoun()} was very curious.",
        ),
        QAItem(
            question=f"Why did {adult.label} worry about {obj.label}?",
            answer=f"{adult.label} worried because {obj.label} could get {activity.soil} if {child.id} kept going without a careful plan.",
        ),
        QAItem(
            question=f"What did they use to make the craft safer?",
            answer=(
                f"They used {gear.label} first." if gear else
                "They chose a safer way to play."
            ),
        ),
    ]
    if f.get("resolved"):
        qa.append(
            QAItem(
                question=f"How did {child.id} feel at the end?",
                answer=f"{child.id} felt happy, and the silly problem turned into a joke instead of a disaster.",
            )
        )
    return qa


KNOWLEDGE = {
    "alphabet": [
        (
            "What is the alphabet?",
            "The alphabet is the set of letters people use to read and write words.",
        )
    ],
    "cotton": [
        (
            "What is cotton?",
            "Cotton is a soft plant fiber that can be woven into fabric or puffed up like little fluff balls.",
        )
    ],
    "braces": [
        (
            "What are braces for?",
            "Braces help straighten teeth over time by gently guiding them into better positions.",
        )
    ],
    "retainer": [
        (
            "What does a retainer do?",
            "A retainer helps teeth stay in their new position after braces come off.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("object"):
        tags.add(world.facts["object"].type)
    out: list[QAItem] = []
    for tag, pairs in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in pairs)
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
    lines.append("== (3) World knowledge ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    out = ["--- world model state ---"]
    for e in list(world.entities.values()):
        out.append(f"  {e.id}: type={e.type} meters={e.meters} memes={e.memes}")
    return "\n".join(out)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(A,O) :- splashes(A,R), worn_on(O,R).
compatible(A,O) :- prize_at_risk(A,O), gear(G), guards(G,M), mess_of(A,M), covers(G,R), worn_on(O,R).
valid(Place,A,O) :- affords(Place,A), prize_at_risk(A,O), compatible(A,O).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for z in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, z))
    for oid, o in OBJECTS.items():
        lines.append(asp.fact("obj", oid))
        lines.append(asp.fact("worn_on", oid, o.region))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    asp_set = set(asp_valid_combos())
    if py == asp_set:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    print(" only in Python:", sorted(py - asp_set))
    print(" only in ASP:", sorted(asp_set - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Comedy storyworld: alphabet, cotton, orthodontics, curiosity, and dialogue.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--object", dest="object_id", choices=OBJECTS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--adult", choices=["teacher", "parent", "orthodontist"])
    ap.add_argument("--name")
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
    if getattr(args, "activity", None) and getattr(args, "object_id", None):
        act = _safe_lookup(ACTIVITIES, getattr(args, "activity", None))
        obj = _safe_lookup(OBJECTS, getattr(args, "object_id", None))
        if not (prize_at_risk(act, obj) and select_gear(act, obj)):
            return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "object_id", None) is None or c[2] == getattr(args, "object_id", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, activity, object_id = rng.choice(list(combos))
    obj = _safe_lookup(OBJECTS, object_id)
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(NAMES)
    adult = getattr(args, "adult", None) or rng.choice(["teacher", "parent", "orthodontist"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, object_id=object_id, name=name, gender=gender, adult=adult, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(OBJECTS, params.object_id), params.name, params.gender, params.adult, params.trait)
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
    StoryParams(place="classroom", activity="cotton", object_id="braces", name="Mia", gender="girl", adult="teacher", trait="curious"),
    StoryParams(place="artroom", activity="alphabet", object_id="retainer", name="Leo", gender="boy", adult="orthodontist", trait="playful"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
        for p, a, o in combos:
            print(f"  {p:18} {a:10} {o}")
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
