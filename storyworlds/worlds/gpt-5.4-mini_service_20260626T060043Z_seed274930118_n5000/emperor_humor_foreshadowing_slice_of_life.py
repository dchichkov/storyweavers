#!/usr/bin/env python3
"""
storyworlds/worlds/emperor_humor_foreshadowing_slice_of_life.py
===============================================================

A tiny slice-of-life storyworld about an emperor's everyday wishes, with
humor, gentle foreshadowing, and a small practical compromise.

Initial story sketch:
---
An emperor liked to spend quiet mornings in his palace garden. He tried to
look grand, but he was also very curious and a little silly. One day he wanted
to help serve tea and carry fresh plum buns himself, even though his long robe
could catch crumbs and spill tea. His adviser warned him that the tray looked
wobbly and that the robe was too fine for kitchen work.

The emperor insisted at first, then noticed a small crack in the tray and a
stain on the sleeve from earlier tea practice. That little detail foreshadowed
what might happen next. The adviser smiled and offered a short apron and a
round serving tray with a steadier rim. The emperor laughed at how un-grand he
looked, put them on anyway, and served tea without any trouble.

World model:
---
- The emperor has physical state in meters: clean, mess, steadiness, effort.
- The emperor has emotional state in memes: pride, curiosity, delight, relief,
  worry, amusement.
- A risky activity can dirty or wet a worn prize in the wrong body region.
- A compatible gear item can cover the at-risk region and prevent the mess.
- Foreshadowing is encoded as small observed clues before the turn.

Narrative instruments:
---
- Humor: the emperor is dignified but slightly ridiculous in daily life.
- Foreshadowing: a tiny clue points toward the coming mishap.
- Slice of life: the scene stays small, concrete, and domestic.
"""

from __future__ import annotations

import argparse
import copy
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
MESS_KINDS = {"wet", "crumbed", "inked", "sticky"}



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

    attendant: object | None = None
    emperor: object | None = None
    gear: object | None = None
    prize: object | None = None
    def __post_init__(self) -> None:
        for key in ["clean", "mess", "steadiness", "effort"]:
            self.meters.setdefault(key, 0.0)
        for key in ["pride", "curiosity", "delight", "relief", "worry", "amusement"]:
            self.memes.setdefault(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"emperor", "man", "father", "boy"}:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        if self.type in {"empress", "woman", "mother", "girl"}:
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
    keyword: str
    humor: str
    foreshadow: str
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
    genders: set[str] = field(default_factory=lambda: {"emperor", "empress"})
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
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
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

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = copy.deepcopy(self.facts)
        return clone


def _r_soak(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters.get(mess, 0.0) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("soak", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["mess"] += 1
                out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got {mess}.")
    return out


def _r_relief(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes.get("worry", 0.0) < THRESHOLD:
            continue
        if actor.memes.get("relief", 0.0) < THRESHOLD:
            continue
        sig = ("relief", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["worry"] = 0.0
        out.append(f"{actor.pronoun().capitalize()} felt much better after the safer plan.")
    return out


CAUSAL_RULES = [_r_soak, _r_relief]


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


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "soiled": bool(prize.meters.get("mess", 0.0) >= THRESHOLD),
        "worry": sim.get(actor.id).memes.get("worry", 0.0),
    }


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.meters["effort"] += 1
    actor.memes["delight"] += 1
    propagate(world, narrate=narrate)


def intro(world: World, emperor: Entity) -> None:
    world.say(
        f"{emperor.id} was the sort of emperor who could look solemn while carrying two biscuits and a teapot."
    )


def habit(world: World, emperor: Entity, activity: Activity) -> None:
    emperor.memes["curiosity"] += 1
    world.say(
        f"{emperor.pronoun().capitalize()} liked quiet mornings, {activity.gerund}, and pretending the palace corridor was a grand parade."
    )
    world.say(activity.humor)


def buy(world: World, attendant: Entity, emperor: Entity, prize: Entity) -> None:
    world.say(
        f"One day, {emperor.pronoun('possessive')} attendant brought {emperor.pronoun('object')} {prize.phrase} for tea duty."
    )


def wear_prize(world: World, emperor: Entity, prize: Entity) -> None:
    emperor.memes["pride"] += 1
    prize.worn_by = emperor.id
    world.say(
        f"{emperor.id} admired {emperor.pronoun('possessive')} {prize.label} and wore {prize.it()} with as much dignity as a crown."
    )


def arrive(world: World, emperor: Entity, attendant: Entity) -> None:
    world.say(
        f"After breakfast, {emperor.id} and {emperor.pronoun('possessive')} attendant went to {world.setting.place}."
    )
    world.say(
        f"{emperor.pronoun().capitalize()} noticed a small clue: {world.facts['foreshadow']}."
    )


def want(world: World, emperor: Entity, activity: Activity) -> None:
    emperor.memes["desire"] = emperor.memes.get("desire", 0.0) + 1
    world.say(
        f"{emperor.id} wanted to {activity.verb}, even if {emperor.pronoun('possessive')} sleeves tried to behave like very serious curtains."
    )


def warn(world: World, attendant: Entity, emperor: Entity, activity: Activity, prize: Entity) -> None:
    pred = predict_mess(world, emperor, activity, prize.id)
    if not pred["soiled"]:
        return
    emperor.memes["worry"] += 1
    world.facts["warning"] = True
    world.say(
        f'"Careful," {attendant.id} said. "If you {activity.verb}, {emperor.pronoun('possessive')} {prize.label} may get {activity.soil}."'
    )


def hesitate(world: World, emperor: Entity, activity: Activity) -> None:
    emperor.memes["worry"] += 1
    world.say(
        f"{emperor.id} tried to keep a straight face, but {emperor.pronoun('possessive')} gaze kept dropping to the tray."
    )
    world.say(
        f"{emperor.pronoun().capitalize()} almost {activity.rush}, then paused."
    )


def compromise(world: World, attendant: Entity, emperor: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id,
        type="gear",
        label=gear_def.label,
        owner=emperor.id,
        caretaker=attendant.id,
        protective=True,
        covers=set(gear_def.covers),
        plural=gear_def.plural,
    ))
    gear.worn_by = emperor.id
    if predict_mess(world, emperor, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    emperor.memes["relief"] += 1
    world.say(
        f'{attendant.id} smiled. "How about we {gear_def.prep}?"'
    )
    return gear_def


def accept(world: World, emperor: Entity, attendant: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    emperor.memes["amusement"] += 1
    emperor.memes["relief"] += 1
    world.say(
        f"{emperor.id} laughed at how un-grand {gear_def.label} looked, but put it on anyway."
    )
    world.say(
        f"Then {emperor.id} served tea {activity.gerund}, {prize.label} stayed clean, and the tiny wobble turned into a very tidy success."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, emperor_name: str = "Emperor Jun", attendant_name: str = "Mina") -> World:
    world = World(setting)
    emperor = world.add(Entity(id=emperor_name, kind="character", type="emperor"))
    attendant = world.add(Entity(id=attendant_name, kind="character", type="attendant", label="attendant"))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=emperor.id,
        caretaker=attendant.id,
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    world.facts["foreshadow"] = activity.foreshadow

    intro(world, emperor)
    habit(world, emperor, activity)
    buy(world, attendant, emperor, prize)
    wear_prize(world, emperor, prize)

    world.para()
    arrive(world, emperor, attendant)
    want(world, emperor, activity)
    warn(world, attendant, emperor, activity, prize)
    hesitate(world, emperor, activity)

    world.para()
    gear_def = compromise(world, attendant, emperor, activity, prize)
    if gear_def:
        accept(world, emperor, attendant, activity, prize, gear_def)

    world.facts.update(
        emperor=emperor,
        attendant=attendant,
        prize=prize,
        activity=activity,
        setting=setting,
        gear=gear_def,
        resolved=gear_def is not None,
    )
    return world


SETTINGS = {
    "palace_garden": Setting(place="the palace garden", indoor=False, affords={"tea", "buns", "paper"}),
    "teahouse": Setting(place="the small teahouse", indoor=True, affords={"tea", "buns", "paper"}),
    "courtyard": Setting(place="the quiet courtyard", indoor=False, affords={"tea", "buns"}),
}


ACTIVITIES = {
    "tea": Activity(
        id="tea",
        verb="serve tea",
        gerund="serving tea",
        rush="lift the tray",
        mess="wet",
        soil="splashed and wet",
        zone={"torso"},
        keyword="tea",
        humor="He stood very straight, even though his tea spoon was slightly too large for such serious posture.",
        foreshadow="the teapot lid clicked once whenever the tray tipped",
        tags={"tea", "wet"},
    ),
    "buns": Activity(
        id="buns",
        verb="carry the plum buns",
        gerund="carrying plum buns",
        rush="hurry with the basket",
        mess="crumbed",
        soil="full of crumbs",
        zone={"torso"},
        keyword="buns",
        humor="The emperor tried to look formal while a bun crumb sat on his sleeve like a tiny grain of evidence.",
        foreshadow="one bun had already left a crumb trail on the counter",
        tags={"food", "crumbs"},
    ),
    "paper": Activity(
        id="paper",
        verb="paint labels for the herb jars",
        gerund="painting labels",
        rush="reach for the ink brush",
        mess="inked",
        soil="spotted with ink",
        zone={"torso", "hands"},
        keyword="paper",
        humor="His brush was so small that he held it as carefully as if it were a royal toothpick.",
        foreshadow="there was already one blue dot on the draft page",
        tags={"paper", "ink"},
    ),
}


GEAR = [
    Gear(
        id="apron",
        label="a short apron",
        covers={"torso"},
        guards={"wet", "crumbed", "inked"},
        prep="put on a short apron first",
        tail="wore the apron and handled the tray with much less splashing",
    ),
    Gear(
        id="tray",
        label="a steadier tray with a raised rim",
        covers={"torso", "hands"},
        guards={"wet", "crumbed"},
        prep="switch to a steadier tray with a raised rim",
        tail="used the steadier tray and kept the tea where it belonged",
    ),
    Gear(
        id="sleeves",
        label="cloth sleeves tied back with ribbon",
        covers={"hands"},
        guards={"inked"},
        prep="tie back the sleeves with ribbon",
        tail="kept the ink off the cuffs and finished the labels neatly",
    ),
]


PRIZES = {
    "robe": Prize(
        label="robe",
        phrase="a fine gold-trimmed robe",
        type="robe",
        region="torso",
    ),
    "sash": Prize(
        label="sash",
        phrase="a bright ceremonial sash",
        type="sash",
        region="torso",
    ),
    "sleeves": Prize(
        label="sleeves",
        phrase="long embroidered sleeves",
        type="sleeves",
        region="hands",
        plural=True,
    ),
}


EMPEROR_NAMES = ["Jun", "Hao", "Ren", "Ming", "Tao", "Wei"]
ATTENDANT_NAMES = ["Mina", "Lian", "Bo", "Suri", "Nia", "Kai"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    emperor_name: str
    attendant_name: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone or ("hands" in activity.zone and prize.region == "hands")


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not actually threaten {prize.label}, so there is no honest problem to solve.)"
    return f"(No story: nothing in the gear catalog reasonably protects {prize.label} from {activity.gerund}.)"


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    act = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")
    emperor = _safe_fact(world, f, "emperor")
    return [
        f'Write a short slice-of-life story for a child about an emperor who wants to {act.verb} while wearing {prize.phrase}.',
        f"Tell a gentle funny story about {emperor.id} in {world.setting.place} where a tiny clue hints that {prize.label} might get ruined.",
        f'Write a story with humor and foreshadowing that includes the word "{act.keyword}" and ends with a safer way to do the chore.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    emperor = _safe_fact(world, f, "emperor")
    attendant = _safe_fact(world, f, "attendant")
    prize = _safe_fact(world, f, "prize")
    activity = _safe_fact(world, f, "activity")
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {emperor.id}, an emperor who wanted to {activity.verb} while keeping {prize.label} clean.",
        ),
        QAItem(
            question=f"What small clue foreshadowed the problem?",
            answer=f"The clue was that {activity.foreshadow.lower()}. That hinted the tray or sleeves might cause trouble later.",
        ),
        QAItem(
            question=f"Why did {attendant.id} worry about {prize.label}?",
            answer=f"{attendant.id} worried because {activity.verb} could leave {prize.label} {activity.soil}.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did the emperor solve the problem?",
                answer=f"They used {gear.label} first, so {emperor.id} could {activity.verb} without ruining {prize.label}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    activity = _safe_fact(world, f, "activity")
    out: list[QAItem] = []
    knowledge = {
        "tea": (
            "Why do people pour tea carefully?",
            "People pour tea carefully so it does not spill and so each cup gets the right amount.",
        ),
        "buns": (
            "What are plum buns?",
            "Plum buns are soft sweet buns, and crumbs can fall when you carry them.",
        ),
        "paper": (
            "Why do ink dots spread on paper?",
            "Ink can spread on paper because the paper soaks it up a little bit.",
        ),
        "wet": (
            "What does wet mean?",
            "Wet means covered with water or something that feels damp.",
        ),
        "crumbs": (
            "What are crumbs?",
            "Crumbs are tiny pieces that break off bread or buns.",
        ),
        "ink": (
            "What is ink used for?",
            "Ink is used for writing and drawing on paper.",
        ),
    }
    for tag, qa in knowledge.items():
        if tag in activity.tags:
            out.append(QAItem(question=qa[0], answer=qa[1]))
    out.append(QAItem(
        question="What is an emperor?",
        answer="An emperor is a ruler, often imagined as someone who takes care of a whole kingdom.",
    ))
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== (1) Generation prompts ==", *[f"{i}. {p}" for i, p in enumerate(sample.prompts, 1)], ""]
    lines.append("== (2) Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== (3) World questions ==")
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
        lines.append(f"  {e.id:12} ({e.type:9}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="palace_garden", activity="tea", prize="robe", emperor_name="Jun", attendant_name="Mina"),
    StoryParams(place="courtyard", activity="buns", prize="sash", emperor_name="Hao", attendant_name="Lian"),
    StoryParams(place="teahouse", activity="paper", prize="sleeves", emperor_name="Ren", attendant_name="Bo"),
]


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if setting.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
        if prize.plural:
            lines.append(asp.fact("prize_plural", pid))
    for gid, gear in [(g.id, g) for g in GEAR]:
        lines.append(asp.fact("gear", gid))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gid, m))
        for r in sorted(gear.covers):
            lines.append(asp.fact("covers", gid, r))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- gear(G), prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R), splashes(A,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_stories() -> list[tuple[str, str, str]]:
    return sorted(valid_combos())


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_stories())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python gate ({len(py)} combos).")
        return 0
    print("MISMATCH:")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in ASP:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Story world: an emperor's humorous slice-of-life dilemma.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--emperor-name")
    ap.add_argument("--attendant-name")
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
    emperor_name = getattr(args, "emperor_name", None) or f"Emperor {rng.choice(EMPEROR_NAMES)}"
    attendant_name = getattr(args, "attendant_name", None) or rng.choice(ATTENDANT_NAMES)
    return StoryParams(place=place, activity=activity, prize=prize, emperor_name=emperor_name, attendant_name=attendant_name)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.emperor_name, params.attendant_name)
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
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible combos:\n")
        for place, act, prize in triples:
            print(f"  {place:14} {act:8} {prize:8}")
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
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.emperor_name}: {p.activity} at {p.place} (prize: {p.prize})"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
