#!/usr/bin/env python3
"""
storyworlds/worlds/earl_repetition_heartwarming.py
===================================================

A small heartwarming story world centered on Earl, repetition, and a gentle
careful craft.

Premise:
- Earl wants to make a repeated pattern gift for someone he loves.
- The activity can splash paint onto a worn prize.
- The grown-up warns him, Earl gets frustrated, then they choose protective gear
  and keep the warm, repeated rhythm anyway.

The story is intentionally compact and state-driven:
- physical meters track mess, cleanliness, and completed craft
- emotional memes track joy, worry, pride, and comfort
- repeated actions build the ending image of a finished gift
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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    earl: object | None = None
    grownup: object | None = None
    item: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        for k in ("wet", "painted", "dirty", "finished", "full"):
            self.meters.setdefault(k, 0.0)
        for k in ("joy", "worry", "pride", "comfort", "patience", "impatience", "delight"):
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "woman", "mother", "grandmother"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "man", "father", "grandfather"}:
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
    affords: set[str]
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
        return any(g.protective and region in g.covers for g in self.worn_items(actor))

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_paint(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["painted"] < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective or item.region not in world.zone:
                continue
            if world.covered(actor, item.region):
                continue
            sig = ("paint", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["painted"] += 1
            item.meters["dirty"] += 1
            out.append(f"{actor.id}'s {item.label} got speckled with paint.")
    return out


def _r_finish(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["finished"] >= THRESHOLD:
            continue
        if item.meters["painted"] >= 2 and item.worn_by:
            sig = ("finish", item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["finished"] += 1
            out.append(f"The little pattern on {item.label} looked finished at last.")
    return out


def _r_caretaker(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["dirty"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("work", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        caretaker = world.get(item.caretaker)
        caretaker.memes["worry"] += 0.5
        out.append(f"That would mean more washing for {caretaker.id}.")
    return out


CAUSAL_RULES = [_r_paint, _r_finish, _r_caretaker]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = World(world.setting)
    sim.entities = {
        k: Entity(**{
            "id": v.id, "kind": v.kind, "type": v.type, "label": v.label,
            "phrase": v.phrase, "owner": v.owner, "caretaker": v.caretaker,
            "worn_by": v.worn_by, "region": v.region, "protective": v.protective,
            "covers": set(v.covers), "plural": v.plural,
            "meters": dict(v.meters), "memes": dict(v.memes)
        }) for k, v in world.entities.items()
    }
    sim.zone = set(world.zone)
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters["dirty"] >= THRESHOLD, "painted": prize.meters["painted"]}


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        pass
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    actor.memes["patience"] += 0.5
    propagate(world, narrate=narrate)


def setting_detail(setting: Setting) -> str:
    if setting.place == "the kitchen":
        return "The kitchen smelled like warm sugar and clean wood."
    if setting.place == "the porch":
        return "The porch was bright, and the afternoon light landed in soft squares."
    return f"{setting.place.capitalize()} was calm and ready for a small project."


def introduce(world: World, earl: Entity) -> None:
    world.say(
        f"Earl was a little {earl.type} who liked quiet, careful jobs and happy endings."
    )


def love_repetition(world: World, earl: Entity, activity: Activity) -> None:
    earl.memes["comfort"] += 1
    world.say(
        f"He loved doing things again and again, because each try made his hands steadier."
    )
    world.say(f"He liked {activity.gerund}, {activity.gerund}, and {activity.gerund} some more.")


def gift_setup(world: World, earl: Entity, prize: Entity) -> None:
    world.say(
        f"That afternoon, Earl wore {prize.phrase} for a gift, because he wanted it to feel extra special."
    )


def arrive(world: World, earl: Entity, grownup: Entity, activity: Activity) -> None:
    world.say(f"One day, Earl and {grownup.id} sat down at {world.setting.place}.")
    world.say(setting_detail(world.setting))


def wants(world: World, earl: Entity, activity: Activity) -> None:
    world.say(
        f"Earl wanted to {activity.verb}, nice and slow, and then do it again until the pattern looked just right."
    )


def warn(world: World, grownup: Entity, earl: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, earl, activity, prize.id)
    if not pred["soiled"]:
        return False
    grownup.memes["worry"] += 1
    world.facts["predicted_paint"] = pred["painted"]
    world.say(
        f'"Careful," {grownup.id} said. "If you {activity.verb}, {prize.label} will get paint on it."'
    )
    return True


def repeat_try(world: World, earl: Entity, activity: Activity) -> None:
    earl.memes["impatience"] += 1
    world.say(
        f"Earl tried once, then again, then one more time. The first dots were wobbly, but he kept going."
    )
    world.say(f"Each time he paused, took a breath, and tried to {activity.verb} a little neater.")


def offer_gear(world: World, grownup: Entity, earl: Entity, prize: Entity, activity: Activity) -> Optional[Gear]:
    gear = None
    for g in GEAR:
        if activity.mess in g.guards and prize.region in g.covers:
            gear = g
            break
    if gear is None:
        return None
    if predict_mess(world, earl, activity, prize.id)["soiled"]:
        return None
    item = world.add(Entity(
        id=gear.id, type="thing", label=gear.label, protective=True,
        covers=set(gear.covers), plural=gear.plural
    ))
    item.worn_by = earl.id
    world.say(
        f'{grownup.id} smiled and said, "How about we {gear.prep}?"'
    )
    return item


def accept(world: World, earl: Entity, grownup: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    earl.memes["joy"] += 1
    earl.memes["pride"] += 1
    earl.memes["impatience"] = 0
    world.say(
        f"Earl nodded, grinned, and put on the {gear.label}. Then the repeating pattern felt easy again."
    )
    world.say(
        f"He {gear.tail}, and soon {prize.label} stayed clean while the paint made a tiny row of hearts across it."
    )
    world.say(
        f"Earl's smile grew bigger with every careful repeat, and {grownup.id} laughed beside him."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str = "Earl",
         hero_type: str = "boy", parent_type: str = "grandmother") -> World:
    world = World(setting)
    earl = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    grownup = world.add(Entity(id="Grandma", kind="character", type=parent_type))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=earl.id, caretaker=grownup.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    introduce(world, earl)
    love_repetition(world, earl, activity)
    gift_setup(world, earl, prize)

    world.para()
    arrive(world, earl, grownup, activity)
    wants(world, earl, activity)
    warn(world, grownup, earl, activity, prize)
    repeat_try(world, earl, activity)

    world.para()
    gear = offer_gear(world, grownup, earl, prize, activity)
    if gear is not None:
        accept(world, earl, grownup, activity, prize, GEAR_BY_ID[gear.id])

    world.facts.update(
        earl=earl, grownup=grownup, prize=prize, activity=activity,
        setting=setting, gear=gear, resolved=gear is not None
    )
    return world


SETTINGS = {
    "kitchen": Setting(place="the kitchen", indoor=True, affords={"paint"}),
    "porch": Setting(place="the porch", indoor=False, affords={"paint"}),
    "craft_table": Setting(place="the craft table", indoor=True, affords={"paint"}),
}

ACTIVITIES = {
    "paint_hearts": Activity(
        id="paint_hearts",
        verb="paint a row of hearts",
        gerund="painting tiny hearts",
        rush="paint too fast",
        mess="painted",
        soil="speckled with paint",
        zone={"torso"},
        keyword="hearts",
        tags={"paint", "heart", "repetition"},
    ),
    "paint_stars": Activity(
        id="paint_stars",
        verb="paint little stars",
        gerund="painting little stars",
        rush="paint too fast",
        mess="painted",
        soil="speckled with paint",
        zone={"torso"},
        keyword="stars",
        tags={"paint", "stars", "repetition"},
    ),
}

PRIZES = {
    "shirt": Prize(
        label="shirt",
        phrase="a clean white shirt",
        type="shirt",
        region="torso",
    ),
    "scarf": Prize(
        label="scarf",
        phrase="a soft blue scarf",
        type="scarf",
        region="torso",
    ),
}

GEAR = [
    Gear(
        id="smock",
        label="an old smock",
        covers={"torso"},
        guards={"painted"},
        prep="put on an old smock first",
        tail="walked back to the table with the smock on",
    ),
    Gear(
        id="apron",
        label="a little apron",
        covers={"torso"},
        guards={"painted"},
        prep="tie on a little apron first",
        tail="tied the apron on and went back to the craft table",
    ),
]

GEAR_BY_ID = {g.id: g for g in GEAR}

EarlNames = ["Earl"]
TRAITS = ["careful", "patient", "gentle", "hopeful"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str = "Earl"
    gender: str = "boy"
    parent: str = "grandmother"
    trait: str = "patient"
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
                if prize.region in act.zone:
                    if any(g for g in GEAR if act.mess in g.guards and prize.region in g.covers):
                        combos.append((place, aid, pid))
    return combos


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def explain_rejection(activity: Activity, prize: Prize) -> str:
    return f"(No story: {activity.verb} would not honestly threaten {prize.label}, so there is no heartwarming problem to solve.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming story world: Earl, repetition, and a gentle craft.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["grandmother"])
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
    if getattr(args, "activity", None) and getattr(args, "prize", None):
        act, pr = _safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(act, pr) and select_gear(act, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
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
        name=getattr(args, "name", None) or "Earl",
        gender="boy",
        parent="grandmother",
        trait=rng.choice(TRAITS),
    )


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act, prize = f["activity"], f["prize"]
    return [
        f'Write a heartwarming story about Earl who likes to repeat {act.keyword} patterns and needs help keeping {prize.label} clean.',
        f"Tell a gentle story where Earl wants to {act.verb} while wearing {prize.phrase}, and a grown-up offers a safer way.",
        f'Write a small cozy story that uses the word "{act.keyword}" and ends with Earl feeling proud after a repeated craft.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    earl, grownup, prize, act = f["earl"], f["grownup"], f["prize"], f["activity"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"What did Earl want to do again and again at {world.setting.place}?",
            answer=f"Earl wanted to {act.verb} at {world.setting.place}, slowly and carefully, so the pattern would look neat.",
        ),
        QAItem(
            question=f"Why did {grownup.id} worry about {prize.label}?",
            answer=f"{grownup.id} worried because {prize.label} could get {act.soil} if Earl painted without protection.",
        ),
        QAItem(
            question=f"What kind of gift was Earl making?",
            answer=f"He was making a repeated painted pattern on {prize.phrase}, and he wanted it to look warm and special.",
        ),
    ]
    if gear:
        qa.append(QAItem(
            question=f"How did the {gear.label} help Earl?",
            answer=f"The {gear.label} covered the part of Earl that could get messy, so he could keep repeating the painting without ruining {prize.label}.",
        ))
        qa.append(QAItem(
            question=f"How did Earl feel at the end?",
            answer=f"Earl felt proud and happy, because the careful repeating work turned into a lovely gift and his grown-up was smiling beside him.",
        ))
    return qa


KNOWLEDGE = {
    "paint": [
        ("Why do people wear a smock when they paint?",
         "People wear a smock so paint does not splash onto their clothes."),
    ],
    "heart": [
        ("What does a heart shape usually mean in a picture?",
         "A heart shape usually stands for love or kindness."),
    ],
    "stars": [
        ("What are stars?",
         "Stars are huge glowing balls of gas far away in the sky."),
    ],
    "repetition": [
        ("What is repetition?",
         "Repetition means doing the same thing again and again."),
    ],
}
KNOWLEDGE_ORDER = ["repetition", "paint", "heart", "stars"]


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    out: list[QAItem] = []
    for key in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if key in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:8} ({e.type:10}) {' '.join(bits)}")
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
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
        for r in sorted(a.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(asp.fact("guards", g.id, m))
        for c in sorted(g.covers):
            lines.append(asp.fact("covers", g.id, c))
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
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name)
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
    StoryParams(place="kitchen", activity="paint_hearts", prize="shirt"),
    StoryParams(place="craft_table", activity="paint_stars", prize="scarf"),
    StoryParams(place="porch", activity="paint_hearts", prize="scarf"),
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for t in triples:
            print("  ", t)
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
