#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/pretty_daycare_room_foreshadowing_happy_ending_fairy.py
============================================================================================================

A small fairy-tale storyworld set in a daycare room, with pretty things,
foreshadowing, and a happy ending.

Initial seed tale, imagined into a world model:
---
Once upon a time, in a bright daycare room, a little child loved a pretty thing
that made the whole room feel magical. The child wanted to play right away, but
a careful teacher noticed tiny signs that trouble might come: a tipped cup, a
shiny trail on the floor, a stack of blocks wobbling near the play rug. The
teacher gently warned the child and offered a safer way to keep the pretty thing
and the play together. At first the child frowned, then tried the teacher's idea,
and soon the room was calm, the pretty thing was safe, and everyone smiled.

World model:
---
- The daycare room can host a few indoor activities.
- Some activities would spoil a treasured pretty item.
- The teacher can foresee the likely trouble from small clues.
- A compatible protective item or tidying step can make the play safe.
- The ending should show that the child still gets joy, while the pretty item
  stays safe and the room ends peaceful.

Narrative instruments:
---
- Foreshadowing: small observed clues hint at the coming mess.
- Happy Ending: the child and teacher find a gentle solution and end in joy.
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
    gear: object | None = None
    prize: object | None = None
    teacher: object | None = None
    def __post_init__(self) -> None:
        self.meters = __import__('collections').defaultdict(float, self.meters)
        self.memes = __import__('collections').defaultdict(float, self.memes)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman", "teacher"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    place: str = "the daycare room"
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
    gear_def: object | None = None
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

    def copy(self) -> "World":
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.facts = dict(self.facts)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        return clone


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in ("painted", "sticky"):
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soil", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] = item.meters.get(mess, 0.0) + 1
                item.meters["dirty"] = item.meters.get("dirty", 0.0) + 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got messy.")
    return out


def _r_work(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("dirty", 0.0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["work"] = carer.memes.get("work", 0.0) + 1
        out.append(f"That would mean more work for {carer.label}.")
    return out


def _r_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("warned", 0.0) < THRESHOLD or actor.memes.get("stubborn", 0.0) < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = actor.memes.get("worry", 0.0) + 1
        return ["__conflict__"]
    return []


def propagate(world: World, narrate: bool = True) -> None:
    changed = True
    produced: list[str] = []
    while changed:
        changed = False
        for rule in (_r_soil, _r_work, _r_conflict):
            out = rule(world)
            if out:
                changed = True
                produced.extend(x for x in out if x != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)


def foreshadow(world: World, teacher: Entity, child: Entity, activity: Activity, prize: Entity) -> bool:
    clues = world.facts.get("clues", [])
    if not clues:
        return False
    world.say(
        f"{teacher.label} noticed {clues[0]} and then another small sign, "
        f"so {teacher.pronoun()} knew trouble could come."
    )
    world.say(
        f'"If {child.id} {activity.verb}, {child.pronoun("possessive")} {prize.label} may not stay pretty," '
        f"{teacher.label} said softly."
    )
    child.memes["warned"] = child.memes.get("warned", 0.0) + 1
    return True


def try_activity(world: World, child: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        pass
    world.zone = set(activity.zone)
    child.meters[activity.mess] = child.meters.get(activity.mess, 0.0) + 1
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    propagate(world, narrate=narrate)


def predict_mess(world: World, child: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    try_activity(sim, sim.get(child.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": prize.meters.get("dirty", 0.0) >= THRESHOLD}


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def story_opening(world: World, child: Entity) -> None:
    world.say(
        f"Once upon a time in {world.setting.place}, there was a little {child.type} named {child.id} "
        f"who loved pretty things and gentle play."
    )


def love_prize(world: World, child: Entity, prize: Entity) -> None:
    child.memes["love"] = child.memes.get("love", 0.0) + 1
    prize.worn_by = child.id
    world.say(
        f"{child.id} loved {child.pronoun('possessive')} pretty {prize.label} and wore {prize.it()} everywhere in the room."
    )


def desire(world: World, child: Entity, activity: Activity) -> None:
    child.memes["desire"] = child.memes.get("desire", 0.0) + 1
    world.say(
        f"{child.id} wanted to {activity.verb}, because {activity.gerund} felt like fairy-tale fun."
    )


def warning(world: World, teacher: Entity, child: Entity, activity: Activity, prize: Entity) -> None:
    pred = predict_mess(world, child, activity, prize.id)
    if not pred["soiled"]:
        return
    teacher.memes["care"] = teacher.memes.get("care", 0.0) + 1
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you go now, your {prize.label} could get {activity.soil}," {teacher.label} said.'
    )


def accept_and_fix(world: World, teacher: Entity, child: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, Prize(prize.label, prize.phrase, prize.type, prize.region, prize.plural))
    if gear_def is None:
        return None
    if predict_mess(world, child, activity, prize.id)["soiled"]:
        gear = world.add(Entity(
            id=gear_def.id,
            type="gear",
            label=gear_def.label,
            owner=child.id,
            caretaker=teacher.id,
            protective=True,
            covers=set(gear_def.covers),
            plural=gear_def.plural,
        ))
        gear.worn_by = child.id
        if predict_mess(world, child, activity, prize.id)["soiled"]:
            gear.worn_by = None
            del world.entities[gear.id]
            return None
    world.say(
        f"{teacher.label} smiled and said, \"How about we {gear_def.prep} first?\""
    )
    return world.get(gear_def.id) if gear_def.id in world.entities else world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=child.id,
        caretaker=teacher.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))


def resolution(world: World, teacher: Entity, child: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1
    child.memes["worry"] = 0.0
    child.memes["stubborn"] = 0.0
    world.say(
        f"{child.id} nodded, then smiled wide and hugged {teacher.pronoun('object')}. "
        f'"Yes, let\'s do it!" {child.pronoun()} said.'
    )
    world.say(
        f"They {gear.tail}. Soon {child.id} was {activity.gerund}, "
        f"and {child.pronoun('possessive')} pretty {prize.label} stayed clean and bright."
    )


SETTINGS = {
    "daycare": Setting(place="the daycare room", affords={"paint", "stickers", "playdough"}),
}

ACTIVITIES = {
    "paint": Activity(
        id="paint",
        verb="paint a little picture",
        gerund="painting little castles",
        rush="run for the paint pots",
        mess="painted",
        soil="spattered with paint",
        zone={"torso"},
        keyword="pretty",
        tags={"paint", "pretty"},
    ),
    "stickers": Activity(
        id="stickers",
        verb="make a sticker crown",
        gerund="sticking shiny stars",
        rush="dash for the sticker basket",
        mess="sticky",
        soil="stuck with sticky glue",
        zone={"torso", "hands"},
        keyword="pretty",
        tags={"stickers", "pretty"},
    ),
    "playdough": Activity(
        id="playdough",
        verb="shape a little dragon",
        gerund="squishing soft playdough",
        rush="grab the playdough tray",
        mess="sticky",
        soil="smudged with dough",
        zone={"hands", "lap"},
        keyword="pretty",
        tags={"playdough", "pretty"},
    ),
}

PRIZES = {
    "dress": Prize("dress", "a pretty dress", "dress", "torso"),
    "shirt": Prize("shirt", "a pretty shirt", "shirt", "torso"),
    "crown": Prize("crown", "a pretty paper crown", "crown", "torso"),
}

GEAR = [
    Gear("smock", "a smock", {"torso"}, {"painted"}, "put on a smock", "went to get the smock"),
    Gear("apron", "an apron", {"torso"}, {"sticky"}, "put on an apron", "went to get the apron"),
]

NAMES = ["Mira", "Lily", "Nora", "Elsa", "Ruby", "Ivy"]
TRAITS = ["kind", "bright-eyed", "cheerful", "curious"]


@dataclass
class StoryParams:
    place: str
    activity: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for aid in setting.affords:
            act = _safe_lookup(ACTIVITIES, aid)
            for pid, prize in PRIZES.items():
                if prize.region in act.zone and select_gear(act, prize):
                    combos.append((place, aid, pid))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A fairy-tale daycare room storyworld with foreshadowing and a happy ending.")
    ap.add_argument("--place", choices=SETTINGS.keys())
    ap.add_argument("--activity", choices=ACTIVITIES.keys())
    ap.add_argument("--prize", choices=PRIZES.keys())
    ap.add_argument("--name")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("-n", type=int, default=1)
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
    return StoryParams(
        place=place,
        activity=activity,
        prize=prize,
        name=getattr(args, "name", None) or rng.choice(NAMES),
        trait=rng.choice(TRAITS),
    )


def tell(params: StoryParams) -> World:
    world = World(_safe_lookup(SETTINGS, params.place))
    child = world.add(Entity(id=params.name, kind="character", type="girl", label=params.name))
    teacher = world.add(Entity(id="Teacher", kind="character", type="teacher", label="the teacher"))
    prize = world.add(Entity(
        id="prize",
        type=_safe_lookup(PRIZES, params.prize).type,
        label=_safe_lookup(PRIZES, params.prize).label,
        phrase=_safe_lookup(PRIZES, params.prize).phrase,
        owner=child.id,
        caretaker=teacher.id,
        region=_safe_lookup(PRIZES, params.prize).region,
        plural=_safe_lookup(PRIZES, params.prize).plural,
    ))
    world.facts["clues"] = ["a tipped cup", "a shiny trail on the floor"]

    story_opening(world, child)
    world.say(f"{child.id} was {params.trait}, and {child.id} especially loved {prize.phrase}.")
    love_prize(world, child, prize)

    world.para()
    foreshadow(world, teacher, child, _safe_lookup(ACTIVITIES, params.activity), prize)
    desire(world, child, _safe_lookup(ACTIVITIES, params.activity))
    warning(world, teacher, child, _safe_lookup(ACTIVITIES, params.activity), prize)

    child.memes["stubborn"] = 1.0
    world.say(f"{child.id} almost rushed ahead, but the teacher held out a gentle hand.")
    gear = accept_and_fix(world, teacher, child, _safe_lookup(ACTIVITIES, params.activity), prize)
    if gear:
        world.para()
        resolution(world, teacher, child, _safe_lookup(ACTIVITIES, params.activity), prize, gear)

    world.facts.update(child=child, teacher=teacher, prize=prize, activity=_safe_lookup(ACTIVITIES, params.activity), gear=gear)
    return world


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    child, act, prize = f["child"], f["activity"], f["prize"]
    return [
        f'Write a short fairy tale for a child in a daycare room about "{child.id}", '
        f'a {prize.label}, and the word "pretty".',
        f"Tell a gentle story where {child.id} wants to {act.verb} but a teacher worries "
        f"about {prize.phrase}, then helps with a safer plan.",
        f"Write a happy-ending story set in a daycare room with a little foreshadowing clue "
        f"and a pretty treasure that stays safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, teacher, prize, act = f["child"], f["teacher"], f["prize"], f["activity"]
    gear = f.get("gear")
    out = [
        QAItem(
            question=f"Who was the fairy-tale child in the daycare room?",
            answer=f"The story was about {child.id}, a {child.memes.get('love', 0) and 'loving' or 'kind'} little child in the daycare room.",
        ),
        QAItem(
            question=f"What pretty thing did {child.id} care about?",
            answer=f"{child.id} cared about {prize.phrase}, and it stayed safe in the end.",
        ),
        QAItem(
            question=f"What did {child.id} want to do before the teacher helped?",
            answer=f"{child.id} wanted to {act.verb}.",
        ),
    ]
    if gear is not None:
        out.append(
            QAItem(
                question=f"How did the teacher help keep the pretty {prize.label} safe?",
                answer=f"The teacher helped by suggesting {gear.label} first, so {child.id} could still {act.verb} without ruining {prize.label}.",
            )
        )
    return out


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a daycare room?",
            answer="A daycare room is a place where young children play, learn, and spend time with caring adults.",
        ),
        QAItem(
            question="What is foreshadowing in a story?",
            answer="Foreshadowing is when a story gives little clues that something important may happen later.",
        ),
        QAItem(
            question="Why is a happy ending nice in a fairy tale?",
            answer="A happy ending is nice because the trouble gets solved and the characters finish the story feeling safe and glad.",
        ),
    ]


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:7}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and python.")
    print("only in python:", sorted(py - cl))
    print("only in clingo:", sorted(cl - py))
    return 1


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


CURATED = [
    StoryParams(place="daycare", activity="paint", prize="shirt", name="Mira", trait="cheerful"),
    StoryParams(place="daycare", activity="stickers", prize="crown", name="Lily", trait="curious"),
    StoryParams(place="daycare", activity="playdough", prize="dress", name="Nora", trait="kind"),
]


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        print(asp_program("#show valid/3."))
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 50):
            params = resolve_params(args, random.Random(base_seed + i))
            params.seed = base_seed + i
            sample = generate(params)
            i += 1
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
        header = f"### variant {idx + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if idx < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
