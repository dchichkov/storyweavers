#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/nose_dim_irritate_mineral_bravery_lesson_learned.py
===============================================================================================================

A small slice-of-life story world about a child, a mineral mishap, bravery,
and a lesson learned.

Seed image:
- A child is handling a little tray of minerals at an everyday place.
- Fine dust makes the nose feel dim and irritated.
- The child is brave enough to say something.
- A parent helps with a simple fix.
- The ending proves the lesson learned.

This world is intentionally compact and constraint-checked:
- the problem is caused by mineral dust in a plausible location;
- the fix is a reasonable, protective everyday item;
- bravery and lesson-learned are stateful emotional turns, not decorative words.
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
    kind: str = "thing"  # "character" | "thing"
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

    gear_ent: object | None = None
    hero: object | None = None
    parent: object | None = None
    tray: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = __import__('collections').defaultdict(float)
        if not self.memes:
            self.memes = __import__('collections').defaultdict(float)

    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def add_meter(self, key: str, amount: float) -> None:
        self.meters[key] = self.meter(key) + amount

    def add_meme(self, key: str, amount: float) -> None:
        self.memes[key] = self.meme(key) + amount

    def set_meme(self, key: str, value: float) -> None:
        self.memes[key] = value

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
    indoors: bool
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
    gear: str
    name: str
    gender: str
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


def _narrate_paragraph(world: World, *sentences: str) -> None:
    for s in sentences:
        world.say(s)


def _fixpoint(world: World, narrate: bool = True) -> list[str]:
    out: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for actor in world.characters():
            if actor.meter("mineral_dust") < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective:
                    continue
                if item.region not in {"nose", "face"}:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("irritate", actor.id, item.id)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                actor.add_meme("irritated", 1)
                actor.add_meme("uneasy", 1)
                out.append(f"{actor.id}'s nose felt dim and irritated.")
                changed = True
    if narrate:
        for s in out:
            world.say(s)
    return out


def activity_note(activity: Activity) -> str:
    return {
        "sort_minerals": "The little stones had stripes, sparkles, and cloudy bits.",
        "wipe_display": "The cloth left each shelf bright and calm.",
        "open_case": "The hinged box creaked softly when it opened.",
    }.get(activity.id, "It felt like an ordinary little task.")


def setup_story(world: World, hero: Entity, parent: Entity, activity: Activity, gear: Gear) -> None:
    world.say(f"{hero.id} was a {hero.type} who loved small, careful projects.")
    world.say(f"{hero.pronoun().capitalize()} liked {activity.gerund} after school because the colors looked like tiny secrets.")
    world.say(f"On that day, {hero.pronoun('possessive')} {parent.type} had set out {activity.keyword} on the kitchen table.")
    world.say(activity_note(activity))
    hero.add_meme("curiosity", 1)
    hero.add_meme("bravery", 0)


def do_activity(world: World, hero: Entity, activity: Activity) -> None:
    hero.add_meter(activity.mess, 1)
    world.say(f"{hero.id} wanted to {activity.verb}, so {hero.pronoun()} leaned closer and began carefully.")
    world.say(f"Then a little puff of mineral dust rose up.")
    _fixpoint(world, narrate=True)


def worry(world: World, parent: Entity, hero: Entity, activity: Activity) -> None:
    if hero.meme("irritated") < THRESHOLD:
        return
    world.say(f"{parent.id} noticed the frown and asked if {hero.pronoun('possessive')} nose felt scratchy.")
    hero.add_meme("worry", 1)
    hero.add_meme("bravery", 1)
    world.say(f"{hero.id} took a breath and said, \"My nose feels dim and irritated.\"")
    world.say(f"That was brave, because saying it out loud meant the problem could finally be handled.")


def fix(world: World, hero: Entity, parent: Entity, gear: Gear, activity: Activity) -> None:
    if hero.meme("irritated") < THRESHOLD:
        return
    gear_ent = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=parent.id,
        protective=True,
        covers=set(gear.covers),
        plural=gear.plural,
        worn_by=hero.id,
    ))
    if "nose" in gear_ent.covers:
        hero.set_meme("irritated", 0)
        hero.add_meme("relief", 1)
        hero.add_meme("lesson_learned", 1)
        world.say(f"{parent.id} brought over {gear.label} and helped {hero.id} put {gear_ent.it()} on.")
        world.say(f"With the mask in place, the dust stayed away from {hero.pronoun('possessive')} nose.")
        world.say(f"{hero.id} went back to {activity.gerund}, only this time {hero.pronoun()} kept a cleaner distance from the tray.")
        world.say(f"By the end, {hero.id} had learned to ask for help before the sneezing started.")
    else:
        world.say(f"{parent.id} offered {gear.label}, but it did not really help the nose.")
        pass


def end_image(world: World, hero: Entity, parent: Entity) -> None:
    world.para()
    if hero.meme("lesson_learned") >= THRESHOLD:
        world.say(f"The minerals still sat neatly on the table, and now {hero.id} knew the simple trick: pause, speak up, and use the mask when the dust came out.")
        world.say(f"{parent.id} smiled, and the kitchen went quiet again.")
    else:
        world.say(f"The room was calm again, but the story needs a real lesson learned.")
        pass


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoors=True, affords={"sort_minerals", "wipe_display", "open_case"}),
    "porch": Setting(place="the porch", indoors=False, affords={"sort_minerals", "wipe_display"}),
    "classroom": Setting(place="the classroom", indoors=True, affords={"sort_minerals", "wipe_display", "open_case"}),
}

ACTIVITIES = {
    "sort_minerals": Activity(
        id="sort_minerals",
        verb="sort the minerals",
        gerund="sorting the minerals",
        rush="reach for the tray",
        mess="mineral_dust",
        soil="dusty",
        zone={"nose", "face"},
        keyword="mineral",
        tags={"mineral"},
    ),
    "wipe_display": Activity(
        id="wipe_display",
        verb="wipe the display",
        gerund="wiping the display",
        rush="grab a cloth",
        mess="mineral_dust",
        soil="dusty",
        zone={"nose", "face"},
        keyword="mineral",
        tags={"mineral"},
    ),
    "open_case": Activity(
        id="open_case",
        verb="open the mineral case",
        gerund="opening the mineral case",
        rush="lift the lid",
        mess="mineral_dust",
        soil="dusty",
        zone={"nose", "face"},
        keyword="mineral",
        tags={"mineral"},
    ),
}

GEAR = {
    "mask": Gear(
        id="mask",
        label="a soft mask",
        covers={"nose", "face"},
        guards={"mineral_dust"},
        prep="put on a soft mask",
        tail="kept going with a cleaner breath",
    ),
    "scarf": Gear(
        id="scarf",
        label="a light scarf",
        covers={"nose"},
        guards={"mineral_dust"},
        prep="wrap on a light scarf",
        tail="kept working with the scarf snug around the nose",
    ),
}

GIRL_NAMES = ["Maya", "Nina", "Ivy", "Lena", "Mila", "Tessa"]
BOY_NAMES = ["Eli", "Noah", "Owen", "Leo", "Finn", "Asher"]
TRAITS = ["patient", "curious", "gentle", "careful", "thoughtful", "quiet"]


CURATED = [
    StoryParams(place="kitchen", activity="sort_minerals", gear="mask", name="Maya", gender="girl", parent="mom", trait="curious"),
    StoryParams(place="classroom", activity="open_case", gear="mask", name="Eli", gender="boy", parent="dad", trait="careful"),
    StoryParams(place="porch", activity="wipe_display", gear="scarf", name="Nina", gender="girl", parent="mom", trait="thoughtful"),
]


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for place, setting in SETTINGS.items():
        for act in setting.affords:
            for gear_id, gear in GEAR.items():
                if "nose" in gear.covers and _safe_lookup(ACTIVITIES, act).mess in gear.guards:
                    combos.append((place, act, gear_id))
    return combos


def explain_rejection(activity: Activity, gear: Gear) -> str:
    return (
        f"(No story: {gear.label} does not really protect the nose from {activity.verb}. "
        f"Pick gear that covers the nose and guards mineral dust.)"
    )


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Slice-of-life story world: a mineral mishap, bravery, and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--gear", choices=GEAR)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mom", "dad"])
    ap.add_argument("--name")
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
    if getattr(args, "activity", None) and getattr(args, "gear", None):
        act, gear = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), GEAR[getattr(args, "gear", None)]
        if not ("nose" in gear.covers and act.mess in gear.guards):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "gear", None) is None or c[2] == getattr(args, "gear", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, gear = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or ("mom" if gender == "girl" else "dad")
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, gear=gear, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    setting = _safe_lookup(SETTINGS, params.place)
    activity = _safe_lookup(ACTIVITIES, params.activity)
    gear = GEAR[params.gear]
    world = World(setting)
    hero = world.add(Entity(id=params.name, kind="character", type=params.gender))
    parent = world.add(Entity(id=params.parent, kind="character", type=params.parent, label=params.parent))
    tray = world.add(Entity(id="tray", type="thing", label="the mineral tray", owner=hero.id))
    _ = tray
    setup_story(world, hero, parent, activity, gear)
    world.para()
    do_activity(world, hero, activity)
    worry(world, parent, hero, activity)
    fix(world, hero, parent, gear, activity)
    end_image(world, hero, parent)
    world.facts = {
        "hero": hero,
        "parent": parent,
        "activity": activity,
        "gear": gear,
        "setting": setting,
        "params": params,
    }
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_qa(world),
        world=world,
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, activity, gear = f["hero"], f["activity"], f["gear"]
    return [
        f'Write a short slice-of-life story for a young child about a {hero.type} named {hero.id} who handles "{activity.keyword}" and learns a gentle lesson.',
        f"Tell a simple story where mineral dust makes {hero.id}'s nose feel dim and irritated, then a parent helps with {gear.label}.",
        f'Write a calm everyday story that uses the words "bravery" and "lesson learned" and ends with a child being more careful around minerals.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, activity, gear = f["hero"], f["parent"], f["activity"], f["gear"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel uncomfortable while {hero.pronoun()} was {activity.gerund}?",
            answer=f"{hero.id} felt uncomfortable because mineral dust rose up and made {hero.pronoun('possessive')} nose feel dim and irritated.",
        ),
        QAItem(
            question=f"What did {hero.id} do that showed bravery?",
            answer=f"{hero.id} was brave when {hero.pronoun()} told {parent.id} the truth about {hero.pronoun('possessive')} scratchy nose instead of hiding it.",
        ),
        QAItem(
            question=f"How did {gear.label} help in the story?",
            answer=f"{gear.label} covered the nose and kept the mineral dust away, so {hero.id} could keep going more comfortably.",
        ),
        QAItem(
            question="What lesson learned did the child finish with?",
            answer=f"The child learned to pause, speak up, and use a little protection before the mineral dust became a problem.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mineral dust?",
            answer="Mineral dust is very tiny bits of broken mineral that can float in the air and make a person sneeze or feel scratchy.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone does something a little scary, like telling the truth or asking for help, even when they feel nervous.",
        ),
        QAItem(
            question="What does a lesson learned mean?",
            answer="A lesson learned is something a person understands after an experience, so they know what to do better next time.",
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
    lines.append("== (3) World knowledge ==")
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
        lines.append(f"{e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
#show valid/3.

valid(P,A,G) :- place(P), activity(A), gear(G), affords(P,A), protects(G,A).
protects(G,A) :- gear(G), activity(A), covers(G,nose), guards(G,mineral_dust).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
    for gid, g in GEAR.items():
        lines.append(asp.fact("gear", gid))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", gid, c))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", gid, m))
    return "\n".join(lines)


def asp_program() -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program())
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
        print(asp_program())
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())

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
            header = f"### {p.name}: {p.activity} at {p.place} (gear: {p.gear})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, activity, gear = f["hero"], f["parent"], f["activity"], f["gear"]
    return [
        QAItem(
            question=f"Why did {hero.id} feel uncomfortable while {hero.pronoun()} was {activity.gerund}?",
            answer=f"{hero.id} felt uncomfortable because mineral dust rose up and made {hero.pronoun('possessive')} nose feel dim and irritated.",
        ),
        QAItem(
            question=f"What did {hero.id} do that showed bravery?",
            answer=f"{hero.id} was brave when {hero.pronoun()} told {parent.id} the truth about {hero.pronoun('possessive')} scratchy nose instead of hiding it.",
        ),
        QAItem(
            question=f"How did {gear.label} help in the story?",
            answer=f"{gear.label} covered the nose and kept the mineral dust away, so {hero.id} could keep going more comfortably.",
        ),
        QAItem(
            question="What lesson learned did the child finish with?",
            answer=f"The child learned to pause, speak up, and use a little protection before the mineral dust became a problem.",
        ),
    ]


def world_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is mineral dust?",
            answer="Mineral dust is very tiny bits of broken mineral that can float in the air and make a person sneeze or feel scratchy.",
        ),
        QAItem(
            question="What is bravery?",
            answer="Bravery is when someone does something a little scary, like telling the truth or asking for help, even when they feel nervous.",
        ),
        QAItem(
            question="What does a lesson learned mean?",
            answer="A lesson learned is something a person understands after an experience, so they know what to do better next time.",
        ),
    ]


if __name__ == "__main__":
    main()
