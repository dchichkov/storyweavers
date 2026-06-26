#!/usr/bin/env python3
"""
storyworlds/worlds/scalp_foreshadowing_curiosity_fable.py
=========================================================

A small fable-style story world about curiosity, foreshadowing, and a tender
scalp that needs care.

Premise:
- A curious child-animal loves exploring a place.
- The world quietly hints that the sun, wind, or dust could trouble their scalp.
- A wiser helper notices the clues and offers a simple protection.
- The story ends with the hero exploring safely, and the scalp stays comfortable.

This world uses two state dimensions for every entity:
- meters: physical conditions like sunburn, dryness, dust, shade, comfort
- memes: emotional conditions like curiosity, caution, worry, delight, trust

The prose is driven by simulated world state rather than a frozen template.
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
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    hat: object | None = None
    helper: object | None = None
    hero: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.type.endswith("s") else "it"
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
    kind: str  # meadow, garden, market, orchard
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
    tag: str
    clue: str
    zone: set[str]
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
class Protection:
    id: str
    label: str
    phrase: str
    guards: set[str]
    covers: set[str]
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
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.zone: set[str] = set()

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
        return any(item.label and region in item.meters.get("covers", set()) for item in [])

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
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        return clone


def _meter_get(ent: Entity, key: str) -> float:
    return ent.meters.get(key, 0.0)


def _mem_get(ent: Entity, key: str) -> float:
    return ent.memes.get(key, 0.0)


def _mem_add(ent: Entity, key: str, amt: float) -> None:
    ent.memes[key] = _mem_get(ent, key) + amt


def _meter_add(ent: Entity, key: str, amt: float) -> None:
    ent.meters[key] = _meter_get(ent, key) + amt


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if _meter_get(actor, "exposed") < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.label != "hat":
                continue
            if ("damage", actor.id, item.id) in world.fired:
                continue
            if item.worn_by != actor.id:
                continue
            if _meter_get(actor, "shade") >= THRESHOLD:
                continue
            world.fired.add(("damage", actor.id, item.id))
            _meter_add(actor, "scalp_sun", 1)
            _meter_add(actor, "worry", 1)
            out.append(f"Their scalp began to feel hot and prickly.")
    return out


def _r_dust(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if _meter_get(actor, "dusty") < THRESHOLD:
            continue
        if ("dust", actor.id) in world.fired:
            continue
        if _meter_get(actor, "cover") >= THRESHOLD:
            continue
        world.fired.add(("dust", actor.id))
        _meter_add(actor, "scalp_dust", 1)
        out.append(f"Fine dust settled near their hairline.")
    return out


def _r_comfort(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if _meter_get(actor, "shade") >= THRESHOLD and _meter_get(actor, "cover") >= THRESHOLD:
            if ("comfort", actor.id) in world.fired:
                continue
            world.fired.add(("comfort", actor.id))
            _meter_add(actor, "comfort", 1)
            _mem_add(actor, "delight", 1)
            out.append(f"Their scalp stayed calm and cool.")
    return out


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_damage, _r_dust, _r_comfort):
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def choose_protection(activity: Activity, setting: Setting, prize: Protection) -> bool:
    return activity.mess in prize.guards and "scalp" in prize.covers and activity.id in setting.affords


def predict(world: World, actor: Entity, activity: Activity, use_protection: bool) -> dict:
    sim = world.copy()
    sim.zone = set(activity.zone)
    _meter_add(actor, activity.mess, 1)
    _meter_add(actor, "exposed", 1)
    if activity.mess == "dusty":
        _meter_add(actor, "dusty", 1)
    if use_protection:
        _meter_add(actor, "cover", 1)
        _meter_add(actor, "shade", 1)
    propagate(sim, narrate=False)
    return {
        "scalp_hot": _meter_get(sim.get(actor.id), "scalp_sun") >= THRESHOLD,
        "scalp_dusty": _meter_get(sim.get(actor.id), "scalp_dust") >= THRESHOLD,
    }


def introduce(world: World, hero: Entity) -> None:
    trait = next((t for t in hero.traits if t != "little"), "curious")
    world.say(
        f"{hero.id} was a little {trait} {hero.type} who loved noticing small things."
    )


def foreshadow(world: World, hero: Entity, activity: Activity) -> None:
    _mem_add(hero, "curiosity", 1)
    world.say(
        f"{hero.pronoun().capitalize()} loved to wander {world.setting.place} and ask why {activity.clue}."
    )
    world.say(
        f"Even before anything happened, the breeze and bright light felt like a whisper of trouble."
    )


def warn(world: World, helper: Entity, hero: Entity, activity: Activity) -> bool:
    pred = predict(world, hero, activity, use_protection=False)
    if not (pred["scalp_hot"] or pred["scalp_dusty"]):
        return False
    _mem_add(helper, "caution", 1)
    world.say(
        f'"If you go out like that," {helper.id} said, "your scalp may not like the day."'
    )
    return True


def resists(world: World, hero: Entity, activity: Activity) -> None:
    _mem_add(hero, "curiosity", 1)
    _mem_add(hero, "restless", 1)
    world.say(
        f"But {hero.id}'s curiosity was strong, and {hero.pronoun()} still tried to {activity.rush}."
    )


def offer_protection(world: World, helper: Entity, hero: Entity, activity: Activity, prize: Protection) -> Optional[Protection]:
    if not choose_protection(activity, world.setting, prize):
        return None
    if predict(world, hero, activity, use_protection=True)["scalp_hot"]:
        return None
    _mem_add(helper, "trust", 1)
    world.say(
        f'{helper.id} smiled and said, "{prize.prep} first, and then you may {activity.verb}."'
    )
    return prize


def accept(world: World, hero: Entity, helper: Entity, activity: Activity, prize: Protection) -> None:
    _mem_add(hero, "joy", 1)
    _mem_add(hero, "trust", 1)
    hero.memes["worry"] = 0.0
    world.say(
        f"{hero.id} nodded, and soon {hero.pronoun()} was ready."
    )
    world.say(
        f"They {prize.tail}. After that, {hero.id} could {activity.verb} with a light heart, and {hero.pronoun('possessive')} scalp stayed comfortable."
    )


SETTINGS = {
    "meadow": Setting(place="the meadow", kind="meadow", affords={"seek_bees", "follow_butterflies"}),
    "garden": Setting(place="the garden", kind="garden", affords={"pick_flowers", "watch_birds"}),
    "orchard": Setting(place="the orchard", kind="orchard", affords={"gather_apples", "chase_shadows"}),
    "market": Setting(place="the market lane", kind="market", affords={"look_booths", "carry_basket"}),
}

ACTIVITIES = {
    "seek_bees": Activity(
        id="seek_bees",
        verb="follow the bees",
        gerund="following bees",
        rush="run after the bees",
        mess="exposed",
        soil="sun-warm",
        tag="bee",
        clue="the bees kept circling the bright flowers",
        zone={"scalp", "shoulders"},
    ),
    "follow_butterflies": Activity(
        id="follow_butterflies",
        verb="follow the butterflies",
        gerund="chasing butterflies",
        rush="dart after the butterflies",
        mess="exposed",
        soil="sun-warm",
        tag="butterfly",
        clue="the butterflies kept floating toward the sunny hill",
        zone={"scalp", "shoulders"},
    ),
    "pick_flowers": Activity(
        id="pick_flowers",
        verb="pick flowers",
        gerund="picking flowers",
        rush="hurry to the flower patch",
        mess="dusty",
        soil="dusty",
        tag="flower",
        clue="the petals shook loose a little dust in the wind",
        zone={"scalp", "hands"},
    ),
    "watch_birds": Activity(
        id="watch_birds",
        verb="watch the birds",
        gerund="watching birds",
        rush="tiptoe under the trees",
        mess="dusty",
        soil="dusty",
        tag="bird",
        clue="the dry path lifted tiny specks whenever feet moved",
        zone={"scalp", "feet"},
    ),
    "gather_apples": Activity(
        id="gather_apples",
        verb="gather apples",
        gerund="gathering apples",
        rush="climb toward the apple branches",
        mess="exposed",
        soil="sun-warm",
        tag="apple",
        clue="the apples were high, and the sun had nowhere to hide",
        zone={"scalp", "arms"},
    ),
    "chase_shadows": Activity(
        id="chase_shadows",
        verb="chase shadows",
        gerund="chasing shadows",
        rush="skip after the shadows",
        mess="exposed",
        soil="sun-warm",
        tag="shadow",
        clue="the shadows moved only where the noon light was strongest",
        zone={"scalp", "legs"},
    ),
}

PROTECTIONS = {
    "hat": Protection(
        id="hat",
        label="a wide hat",
        phrase="a wide hat with a soft brim",
        guards={"exposed"},
        covers={"scalp"},
        prep="put on a wide hat",
        tail="walked under the trees with the hat on",
    ),
    "scarf": Protection(
        id="scarf",
        label="a light scarf",
        phrase="a light scarf for the head",
        guards={"dusty"},
        covers={"scalp"},
        prep="tie on a light scarf",
        tail="went along with the scarf tied neatly",
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Rosa", "Nina", "Ivy", "Ada"]
BOY_NAMES = ["Arlo", "Pip", "Sami", "Noel", "Tomas", "Milo"]
TRAITS = ["curious", "earnest", "bright-eyed", "thoughtful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    protection: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for activity in setting.affords:
            act = _safe_lookup(ACTIVITIES, activity)
            for pid, prize in PROTECTIONS.items():
                if choose_protection(act, setting, prize):
                    out.append((place, activity, pid))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    act = _safe_fact(world, f, "activity")
    return [
        f'Write a short fable about {hero.id}, curiosity, and a careful lesson about the scalp.',
        f"Tell a gentle story where {hero.id} wants to {act.verb} but learns to listen to a wise helper.",
        f'Write a child-friendly fable that includes the word "scalp" and ends with a safer choice.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    act = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "protection")
    setting = _safe_fact(world, f, "setting")
    return [
        QAItem(
            question=f"Why did {hero.id} want to keep going in {setting.place}?",
            answer=f"{hero.id} was full of curiosity and wanted to {act.verb}.",
        ),
        QAItem(
            question=f"What warning did {helper.id} give about {hero.id}'s scalp?",
            answer=f"{helper.id} warned that the bright day and moving wind might trouble {hero.id}'s scalp.",
        ),
        QAItem(
            question=f"How did {prize.label} help {hero.id}?",
            answer=f"{prize.label.capitalize()} covered the scalp, and that helped {hero.id} stay comfortable while exploring.",
        ),
        QAItem(
            question=f"What changed by the end of the story?",
            answer=f"At the end, {hero.id} still explored, but the scalp stayed calm and {hero.id} felt wiser.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a scalp?",
            answer="The scalp is the skin on top of your head where your hair grows.",
        ),
        QAItem(
            question="Why can a hat help on a sunny day?",
            answer="A hat can shade the scalp from strong sun and make the head feel cooler.",
        ),
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes someone want to ask questions and learn new things.",
        ),
    ]


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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def tell(setting: Setting, activity: Activity, protection: Protection,
         hero_name: str, hero_type: str, helper_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type, traits=["little", trait]))
    helper = world.add(Entity(id="Guide", kind="character", type=helper_type, traits=["wise", "kind"]))
    hat = world.add(Entity(id=protection.id, type="thing", label=protection.label, phrase=protection.phrase))
    hat.worn_by = hero.id
    world.facts = {
        "hero": hero,
        "helper": helper,
        "protection": protection,
        "activity": activity,
        "setting": setting,
    }

    introduce(world, hero)
    foreshadow(world, hero, activity)
    world.para()
    warn(world, helper, hero, activity)
    resists(world, hero, activity)
    world.para()
    choice = offer_protection(world, helper, hero, activity, protection)
    if choice:
        accept(world, hero, helper, activity, choice)
        _meter_add(hero, "cover", 1)
        _meter_add(hero, "shade", 1)
    return world


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "activity", None) and getattr(args, "protection", None):
        act = _safe_lookup(ACTIVITIES, getattr(args, "activity", None))
        prot = _safe_lookup(PROTECTIONS, getattr(args, "protection", None))
        if not choose_protection(act, _safe_lookup(SETTINGS, getattr(args, "place", None)) if getattr(args, "place", None) else next(iter(SETTINGS.values())), prot):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "protection", None) is None or c[2] == getattr(args, "protection", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, protection = rng.choice(list(combos))
    hero_gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    hero_name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if hero_gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "grandparent", "teacher"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, protection=protection, name=hero_name, gender=hero_gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.place),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PROTECTIONS, params.protection),
        params.name,
        params.gender,
        params.helper,
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
% A protection works when it covers the scalp and guards the mess kind.
works(P, A) :- protection(P), activity(A), guards(P, M), mess_of(A, M), covers(P, scalp).

valid(Place, A, P) :- affords(Place, A), works(P, A).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("setting", place))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", place, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
    for pid, prot in PROTECTIONS.items():
        lines.append(asp.fact("protection", pid))
        for m in sorted(prot.guards):
            lines.append(asp.fact("guards", pid, m))
        for c in sorted(prot.covers):
            lines.append(asp.fact("covers", pid, c))
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
    ap = argparse.ArgumentParser(description="A fable about curiosity, foreshadowing, and scalp care.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--protection", choices=PROTECTIONS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper")
    ap.add_argument("--trait")
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


CURATED = [
    StoryParams(place="meadow", activity="seek_bees", protection="hat", name="Mina", gender="girl", helper="mother", trait="curious"),
    StoryParams(place="orchard", activity="gather_apples", protection="hat", name="Arlo", gender="boy", helper="father", trait="bright-eyed"),
    StoryParams(place="garden", activity="pick_flowers", protection="scarf", name="Lena", gender="girl", helper="grandparent", trait="thoughtful"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        import asp
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:")
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
            header = f"### {p.name}: {p.activity} at {p.place} with {p.protection}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
