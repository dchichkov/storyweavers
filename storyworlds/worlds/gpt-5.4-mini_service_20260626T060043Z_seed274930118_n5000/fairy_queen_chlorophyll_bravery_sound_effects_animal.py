#!/usr/bin/env python3
"""
storyworlds/worlds/fairy_queen_chlorophyll_bravery_sound_effects_animal.py
===========================================================================

A small animal-story world with a fairy queen, chlorophyll, bravery, and
sound-effect narration.

Premise used to build the world model:
---
A tiny animal friend wants to help the fairy queen save a wilting moon-garden.
The queen explains that the garden's green glow comes from chlorophyll, but the
little helper is nervous about the dark path to the leaf spring. The queen
suggests a brave, careful trip with cheerful sound effects, and the helper
finds courage when the garden begins to shine again.

This world is built in the style of an Animal Story:
- simple animal characters
- a gentle problem
- a worried parent/leader figure
- a brave action
- a clear, happy change at the end
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gear: object | None = None
    helper: object | None = None
    prize: object | None = None
    queen: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"queen", "fairy", "cat", "mouse", "rabbit", "fox", "owl"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
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
    indoors: bool = False
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
class Prize:
    label: str
    phrase: str
    type: str
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


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    hero: str
    helper: str
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
        w = World(self.setting)
        w.entities = copy.deepcopy(self.entities)
        w.fired = set(self.fired)
        w.zone = set(self.zone)
        w.paragraphs = [[]]
        return w

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]


def _r_cold(self: World) -> list[str]:
    return []


def propagate(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for actor in world.characters():
            if actor.meters.get("brave", 0) < THRESHOLD:
                continue
            if actor.meters.get("glow", 0) < THRESHOLD:
                continue
    if narrate:
        for s in out:
            world.say(s)
    return out


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def activity_sound(activity: Activity) -> str:
    return {
        "leafspring": "swish-swish",
        "moonpath": "tip-tap",
        "pondsong": "plip-plip",
    }.get(activity.id, "soft little sounds")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.place == "the moon garden":
        return "The moon garden slept in silver light, and the leaf spring hummed under the roots."
    if setting.place == "the fern grove":
        return "Tall ferns leaned together, and the green path slipped between them."
    return f"{setting.place.capitalize()} waited quietly for a small brave step."


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": bool(prize.meters.get("dirty", 0) >= THRESHOLD)}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        pass
    world.zone = set(activity.zone)
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0) + 1
    actor.memes["joy"] = actor.memes.get("joy", 0) + 1
    for item in world.worn_items(actor):
        if item.protective:
            continue
        if activity.mess in {"wet", "green"} and item.label in {"leaf cloak", "leaf gloves"}:
            continue
        item.meters["dirty"] = item.meters.get("dirty", 0) + 1
    if narrate:
        world.say(f"{activity_sound(activity)}. {actor.id} went on with the brave little task.")


def introduce(world: World, hero: Entity, helper: Entity) -> None:
    world.say(
        f"{hero.id} was a fairy queen who watched over the animals in the {world.setting.place}."
    )
    world.say(
        f"{helper.id} was a small {helper.type} who loved {helper.meters.get('love', 0) and 'helping' or 'helping'} her."
    )


def wants(world: World, helper: Entity, activity: Activity, prize: Entity) -> None:
    helper.memes["want"] = helper.memes.get("want", 0) + 1
    world.say(
        f"{helper.id} wanted to {activity.verb}, but {helper.pronoun('possessive')} paws trembled when {helper.pronoun()} looked at {prize.phrase}."
    )


def warn(world: World, queen: Entity, helper: Entity, activity: Activity, prize: Entity) -> None:
    pred = predict_mess(world, helper, activity, prize.id)
    if pred["soiled"]:
        world.say(
            f'"If you rush into that path, your {prize.label} will get messy," {queen.id} said.'
        )


def defy(world: World, helper: Entity, activity: Activity) -> None:
    helper.memes["fear"] = helper.memes.get("fear", 0) + 1
    world.say(
        f"{helper.id} took one nervous step anyway: tap-tap, then a shaky hop toward the dark green path."
    )
    helper.memes["bravery"] = helper.memes.get("bravery", 0) + 1


def offer_gear(world: World, queen: Entity, helper: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        protective=True,
        plural=gear_def.plural,
        owner=helper.id,
    ))
    gear.worn_by = helper.id
    if predict_mess(world, helper, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{queen.id} smiled. "How about we wear {gear_def.label} first, then go with the swish-swish sounds?"'
    )
    return gear


def accept(world: World, queen: Entity, helper: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    helper.memes["bravery"] = helper.memes.get("bravery", 0) + 2
    helper.memes["joy"] = helper.memes.get("joy", 0) + 1
    world.say(
        f"{helper.id} nodded, and {helper.pronoun()} stood taller in {gear.label}."
    )
    world.say(
        f"Together they followed the tip-tap path, found the leaf spring, and the garden's green glow came back."
    )
    world.say(
        f"At the end, {helper.id} was {activity.gerund}, {prize.phrase} stayed clean, and the moon garden shimmered like a song."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, helper_name: str) -> World:
    world = World(setting)
    queen = world.add(Entity(id=hero_name, kind="character", type="queen"))
    helper = world.add(Entity(id=helper_name, kind="character", type="mouse"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, caretaker=queen.id))
    prize.worn_by = helper.id

    introduce(world, queen, helper)
    world.say(f"{queen.id} carried a little lesson about chlorophyll, the green shine inside leaves.")
    world.say(f"{helper.id} listened, because the story sounded like {activity_sound(activity)} in the dark.")

    world.para()
    world.say(setting_detail(setting, activity))
    wants(world, helper, activity, prize)
    warn(world, queen, helper, activity, prize)
    defy(world, helper, activity)

    world.para()
    gear = offer_gear(world, queen, helper, activity, prize)
    if gear:
        accept(world, queen, helper, activity, prize, gear)

    world.facts.update(
        queen=queen,
        helper=helper,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear,
        resolved=gear is not None,
    )
    return world


SETTINGS = {
    "moon_garden": Setting(place="the moon garden", affords={"leafspring", "moonpath"}),
    "fern_grove": Setting(place="the fern grove", affords={"leafspring", "pondsong"}),
    "hollow_lane": Setting(place="the hollow lane", affords={"moonpath"}),
}

ACTIVITIES = {
    "leafspring": Activity(
        id="leafspring",
        verb="carry a basket of leaf-water",
        gerund="carrying the leaf-water basket",
        rush="dash through the wet roots",
        mess="green",
        soil="smeared green",
        zone={"hands", "tail"},
        keyword="chlorophyll",
        tags={"chlorophyll", "green"},
    ),
    "moonpath": Activity(
        id="moonpath",
        verb="walk the moon path",
        gerund="walking the moon path",
        rush="run down the dark path",
        mess="dusty",
        soil="dusty and scuffed",
        zone={"paws", "feet"},
        keyword="bravery",
        tags={"bravery", "night"},
    ),
    "pondsong": Activity(
        id="pondsong",
        verb="listen for the pond song",
        gerund="listening to the pond song",
        rush="hop to the pond",
        mess="wet",
        soil="wet and muddy",
        zone={"feet", "tail"},
        keyword="sound effects",
        tags={"sound effects", "water"},
    ),
}

PRIZES = {
    "leaf_cloak": Prize(
        label="leaf cloak",
        phrase="a soft leaf cloak",
        type="cloak",
        region="hands",
        genders={"girl", "boy"},
    ),
    "moon_crown": Prize(
        label="moon crown",
        phrase="a tiny moon crown",
        type="crown",
        region="head",
    ),
    "berry_bag": Prize(
        label="berry bag",
        phrase="a bright berry bag",
        type="bag",
        region="tail",
        plural=False,
    ),
}

GEAR = [
    Gear(
        id="gloves",
        label="leaf gloves",
        covers={"hands"},
        guards={"green"},
        prep="put on leaf gloves",
        tail="wore the leaf gloves",
    ),
    Gear(
        id="boots",
        label="soft boots",
        covers={"feet"},
        guards={"dusty", "wet"},
        prep="put on soft boots",
        tail="slipped into the soft boots",
    ),
    Gear(
        id="rainhood",
        label="a rain hood",
        covers={"head"},
        guards={"wet"},
        prep="tie on a rain hood",
        tail="tied on the rain hood",
    ),
]

CURATED = [
    StoryParams(place="moon_garden", activity="leafspring", prize="leaf_cloak", hero="Queen Luma", helper="Pip"),
    StoryParams(place="fern_grove", activity="pondsong", prize="berry_bag", hero="Queen Luma", helper="Milo"),
    StoryParams(place="moon_garden", activity="moonpath", prize="moon_crown", hero="Queen Luma", helper="Nib"),
]


KNOWLEDGE = {
    "chlorophyll": [
        ("What is chlorophyll?", "Chlorophyll is the green stuff in leaves that helps plants use sunlight to make food."),
    ],
    "bravery": [
        ("What does bravery mean?", "Bravery means doing something even when you feel scared, because it is the right thing to do."),
    ],
    "sound effects": [
        ("What are sound effects?", "Sound effects are special sounds, like tap-tap or swish-swish, that help tell a story."),
    ],
    "leaf": [
        ("Why are leaves green?", "Many leaves are green because they have chlorophyll inside them."),
    ],
}


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Animal-story world about a fairy queen, chlorophyll, bravery, and sound effects.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--hero")
    ap.add_argument("--helper")
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
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize = rng.choice(list(combos))
    hero = getattr(args, "hero", None) or "Queen Luma"
    helper = getattr(args, "helper", None) or rng.choice(["Pip", "Milo", "Nib", "Toto"])
    return StoryParams(place=place, activity=activity, prize=prize, hero=hero, helper=helper)


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short animal story about a fairy queen, chlorophyll, and bravery that includes "{f["activity"].keyword}".',
        f"Tell a gentle story where {f['helper'].id} wants to {f['activity'].verb} but worries about {f['prize'].phrase}.",
        f"Write a small story with tap-tap and swish-swish sound effects, ending with a happy green glow.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    queen, helper, prize, activity = f["queen"], f["helper"], f["prize"], f["activity"]
    return [
        QAItem(
            question=f"Who was the fairy queen in the story?",
            answer=f"The fairy queen was {queen.id}. She watched over the animals in {world.setting.place}.",
        ),
        QAItem(
            question=f"What did {helper.id} want to do?",
            answer=f"{helper.id} wanted to {activity.verb}, but first needed to be brave enough to try the dark little path.",
        ),
        QAItem(
            question=f"Why did {queen.id} mention chlorophyll?",
            answer="She explained that chlorophyll is what helps leaves stay green and bright, so the moon garden could glow again.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in items)
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts -- asks that would produce this story ==",]
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
        lines.append(f"  {e.id:12} ({e.type}) meters={e.meters} memes={e.memes}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), gear(G), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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
        for r in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    print("  only in clingo:", sorted(clingo_set - python_set))
    print("  only in python:", sorted(python_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.hero, params.helper)
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
        print(asp_valid_combos())
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(getattr(args, "n", None) * 50, 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            if sample.story in seen:
                i += 1
                continue
            seen.add(sample.story)
            samples.append(sample)
            i += 1

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
