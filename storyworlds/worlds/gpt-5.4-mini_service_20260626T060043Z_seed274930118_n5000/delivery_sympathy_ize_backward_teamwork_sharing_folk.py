#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/delivery_sympathy_ize_backward_teamwork_sharing_folk.py
===============================================================================================

A small folk-tale storyworld about a village delivery, a backward turn, and
the kindness of sympathy-izing and sharing through teamwork.

Premise seed:
- delivery
- sympathy-ize
- backward

Narrative instruments:
- Teamwork
- Sharing

Style:
- Folk tale
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
    kind: str = "thing"  # character | thing
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    helper: object | None = None
    helper_item: object | None = None
    hero: object | None = None
    parcel: object | None = None
    def __post_init__(self) -> None:
        if not self.meters:
            self.meters = {"damage": 0.0, "delay": 0.0}
        if not self.memes:
            self.memes = {"worry": 0.0, "kindness": 0.0, "joy": 0.0, "shared": 0.0, "teamwork": 0.0}

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "grandmother", "aunt"}
        male = {"boy", "man", "father", "grandfather", "uncle"}
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
    place: str = "the village lane"
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
class Delivery:
    id: str
    verb: str
    gerund: str
    backward_move: str
    risk: str
    spoil: str
    tags: set[str] = field(default_factory=set)
    keyword: str = "delivery"
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
class Parcel:
    label: str
    phrase: str
    type: str
    region: str
    plural: bool = False
    recipients: set[str] = field(default_factory=lambda: {"grandmother", "mother", "father"})
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
    prep: str
    tail: str
    covers: set[str] = field(default_factory=set)
    guards: set[str] = field(default_factory=set)
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
        self.facts: dict = {}
        self.route: str = ""
        self.weather: str = ""

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
        import copy as _copy
        c = World(self.setting)
        c.entities = _copy.deepcopy(self.entities)
        c.fired = set(self.fired)
        c.route = self.route
        c.weather = self.weather
        c.paragraphs = [[]]
        return c

    def worn_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.worn_by == actor.id]

    def covered(self, actor: Entity, region: str) -> bool:
        return any(item.protective and region in item.covers for item in self.worn_items(actor))


def prize_at_risk(delivery: Delivery, parcel: Parcel) -> bool:
    return parcel.region in {"hands", "back"} and delivery.id in {"muddy_road", "windy_hill", "river_path"}


def select_helper(delivery: Delivery, parcel: Parcel) -> Optional[Helper]:
    for helper in HELPERS:
        if delivery.risk in helper.guards and parcel.region in helper.covers:
            return helper
    return None


def explain_rejection(delivery: Delivery, parcel: Parcel) -> str:
    return (
        f"(No story: this delivery does not honestly threaten {parcel.label}. "
        f"Try a parcel carried on the back, or a risk that can be fixed by a helper.)"
    )


def explain_gender(parcel_id: str, gender: str) -> str:
    return f"(No story: this parcel is not a typical {gender}'s thing here.)"


def activity_delight(delivery: Delivery) -> str:
    return {
        "muddy_road": "the road was full of sticky mud and little ruts",
        "windy_hill": "the hill whispered and tugged at cloaks and baskets",
        "river_path": "the path beside the river shone and slipped underfoot",
    }.get(delivery.id, "the road was full of old folk-tale trouble")


def predict_delivery(world: World, actor: Entity, delivery: Delivery, parcel_id: str) -> dict:
    sim = world.copy()
    _do_delivery(sim, sim.get(actor.id), delivery, narrate=False)
    parcel = sim.entities.get(parcel_id)
    return {
        "damaged": bool(parcel and parcel.meters["damage"] >= THRESHOLD),
        "delay": sum(e.meters["delay"] for e in sim.characters()),
    }


def _do_delivery(world: World, actor: Entity, delivery: Delivery, narrate: bool = True) -> None:
    if delivery.id not in world.setting.affords:
        return
    actor.meters["delay"] += 1
    if narrate:
        world.say(f"{actor.id} went on with the {delivery.keyword}, one careful step at a time.")


def _r_damage(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["delay"] < THRESHOLD:
            continue
        if actor.memes.get("carrying", 0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.protective:
                continue
            if item.meters["damage"] >= THRESHOLD:
                continue
            sig = ("damage", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["damage"] += 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got bumped and scuffed.")
    return out


def _r_teamwork(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["teamwork"] < THRESHOLD:
            continue
        sig = ("teamwork", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["joy"] += 1
        out.append(f"With teamwork, the road felt less long.")
    return out


def _r_sharing(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.memes["shared"] < THRESHOLD:
            continue
        sig = ("share", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["kindness"] += 1
        out.append(f"Sharing made the basket lighter in the heart.")
    return out


CAUSAL_RULES = [_r_damage, _r_teamwork, _r_sharing]


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


def tell(setting: Setting, delivery: Delivery, parcel_cfg: Parcel,
         hero_name: str = "Mara", hero_type: str = "girl",
         helper_name: str = "Ned", helper_type: str = "boy") -> World:
    world = World(setting)
    world.route = delivery.id

    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    parcel = world.add(Entity(
        id="parcel",
        type=parcel_cfg.type,
        label=parcel_cfg.label,
        phrase=parcel_cfg.phrase,
        owner=hero.id,
        caretaker=helper.id,
        region=parcel_cfg.region,
        plural=parcel_cfg.plural,
    ))
    parcel.worn_by = hero.id

    hero.memes["carrying"] = 1
    helper.memes["teamwork"] = 1

    world.say(
        f"In a little village by the lane, {hero.id} was the sort of child who never "
        f"passed a doorstep without greeting it."
    )
    world.say(
        f"One morning, {hero.id} was sent on a {delivery.keyword} with {parcel.phrase} for the old house at the hill."
    )
    world.say(
        f"{hero.id} loved the work, for folk-tale roads can make a messenger feel very brave."
    )

    world.para()
    world.say(
        f"But the road was {activity_delight(delivery)}, and {hero.id} soon had to {delivery.backward_move}."
    )

    predicted = predict_delivery(world, hero, delivery, parcel.id)
    if predicted["damaged"]:
        hero.memes["worry"] += 1
        world.say(
            f"{hero.id} worried that {parcel.label} might be harmed if the journey went on that way."
        )
    helper.memes["shared"] = 1
    hero.memes["teamwork"] = 1
    world.say(
        f"Then {helper.id} came along, and together they listened to the wind and chose a gentler path."
    )
    world.say(
        f"{helper.id} and {hero.id} began to share the load, one side for each hand, so the parcel would stay safe."
    )
    propagate(world, narrate=True)

    world.para()
    helper_def = select_helper(delivery, parcel_cfg)
    if helper_def:
        helper_item = world.add(Entity(
            id=helper_def.id,
            type="thing",
            label=helper_def.label,
            owner=hero.id,
            caretaker=helper.id,
            protective=True,
            covers=set(helper_def.covers),
        ))
        helper_item.worn_by = hero.id
        world.say(
            f"{hero.id}'s {helper.label if helper.label else 'helper'} smiled and said, "
            f'"{helper_def.prep}."'
        )
        world.say(
            f"So they went on together, and by the time they reached the old house, "
            f"{parcel.label} was still sound."
        )
        hero.memes["joy"] += 1
        hero.memes["kindness"] += 1
    else:
        world.say(
            f"They found another safe way by sharing the watch and turning back from the worst mud."
        )

    world.say(
        f"At the end, {hero.id} delivered the {parcel.label}, and the old house answered with warm thanks."
    )

    world.facts.update(
        hero=hero,
        helper=helper,
        parcel=parcel,
        parcel_cfg=parcel_cfg,
        delivery=delivery,
        setting=setting,
        resolved=True,
    )
    return world


SETTINGS = {
    "village": Setting(place="the village lane", affords={"muddy_road", "windy_hill", "river_path"}),
    "hill": Setting(place="the hill road", affords={"windy_hill", "river_path"}),
    "river": Setting(place="the river path", affords={"river_path", "muddy_road"}),
}

DELIVERIES = {
    "muddy_road": Delivery(
        id="muddy_road",
        verb="carry the parcel across the mud",
        gerund="carrying parcels across mud",
        backward_move="walk backward a little to keep balance",
        risk="mud",
        spoil="muddy and worn",
        tags={"delivery", "mud"},
        keyword="delivery",
    ),
    "windy_hill": Delivery(
        id="windy_hill",
        verb="deliver the bundle over the hill",
        gerund="delivering bundles over hills",
        backward_move="step backward when the wind pushed too hard",
        risk="wind",
        spoil="tumbled and bent",
        tags={"delivery", "wind"},
        keyword="delivery",
    ),
    "river_path": Delivery(
        id="river_path",
        verb="bring the gift along the river path",
        gerund="bringing gifts along the river path",
        backward_move="backward-step over the slick stones",
        risk="water",
        spoil="damp and splashed",
        tags={"delivery", "water"},
        keyword="delivery",
    ),
}

PARCELS = {
    "bread": Parcel(label="bread", phrase="a round loaf of bread", type="bread", region="hands"),
    "soup": Parcel(label="soup", phrase="a warm bowl of soup", type="soup", region="hands"),
    "blanket": Parcel(label="blanket", phrase="a soft blanket", type="blanket", region="back"),
}

HELPERS = [
    Helper(id="rope", label="a rope", prep="use the rope to share the weight", tail="tied the bundle steadier", covers={"back"}, guards={"wind"}),
    Helper(id="basket_cloth", label="a cloth wrap", prep="wrap the parcel in a cloth", tail="wrapped the parcel safe and snug", covers={"hands"}, guards={"mud", "water", "wind"}),
    Helper(id="straw_shawl", label="a straw shawl", prep="borrow the straw shawl for shelter", tail="walked on under the straw shawl", covers={"back", "hands"}, guards={"wind", "mud"}),
]

GIRL_NAMES = ["Mara", "Lina", "Tess", "Nell", "Rina"]
BOY_NAMES = ["Ned", "Pip", "Oren", "Finn", "Toma"]


@dataclass
class StoryParams:
    place: str
    delivery: str
    parcel: str
    name: str
    gender: str
    helper_name: str
    helper_gender: str
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
        for delivery_id in setting.affords:
            delivery = _safe_lookup(DELIVERIES, delivery_id)
            for parcel_id, parcel in PARCELS.items():
                if prize_at_risk(delivery, parcel) and select_helper(delivery, parcel):
                    out.append((place, delivery_id, parcel_id))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f"Write a short folk tale about a village {f['delivery'].keyword} that uses the word 'delivery'.",
        f"Tell a gentle story where {f['hero'].id} must go backward on the road, but teamwork and sharing help.",
        f"Write a child-friendly folk tale about {f['hero'].id}, {f['helper'].id}, and a precious {f['parcel'].label}.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    helper = _safe_fact(world, f, "helper")
    parcel = _safe_fact(world, f, "parcel")
    delivery = _safe_fact(world, f, "delivery")
    place = _safe_fact(world, f, "setting").place
    return [
        QAItem(
            question=f"Who had to make the delivery on the village road?",
            answer=f"{hero.id} had to make the delivery, and {helper.id} helped along the way.",
        ),
        QAItem(
            question=f"What made {hero.id} move backward during the trip?",
            answer=f"{activity_delight(delivery).capitalize()}, so {hero.id} had to keep moving backward to stay balanced.",
        ),
        QAItem(
            question=f"How did teamwork and sharing help with the {parcel.label}?",
            answer=(
                f"They shared the load and walked together, which kept {parcel.label} safe "
                f"on the way to {place}."
            ),
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is teamwork?",
            answer="Teamwork means people work together to do a job better than one person could alone.",
        ),
        QAItem(
            question="What is sharing?",
            answer="Sharing means giving part of what you have or helping another person use it too.",
        ),
        QAItem(
            question="Why can a muddy road be hard for a delivery?",
            answer="A muddy road can make feet slip and make a parcel dirty or slow to carry.",
        ),
    ]


def format_qa(sample: StorySample) -> str:
    out = ["== prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        out.append(f"{i}. {p}")
    out.append("")
    out.append("== story qa ==")
    for q in sample.story_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    out.append("")
    out.append("== world qa ==")
    for q in sample.world_qa:
        out.append(f"Q: {q.question}")
        out.append(f"A: {q.answer}")
    return "\n".join(out)


def dump_trace(world: World) -> str:
    lines = ["--- world trace ---"]
    for e in list(world.entities.values()):
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        parts = []
        if meters:
            parts.append(f"meters={meters}")
        if memes:
            parts.append(f"memes={memes}")
        if e.protective:
            parts.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id} ({e.type}) {' '.join(parts)}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Folk-tale delivery world with teamwork and sharing.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--delivery", choices=DELIVERIES)
    ap.add_argument("--parcel", choices=PARCELS)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper-gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--helper-name")
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
    combos = valid_combos()
    if getattr(args, "place", None):
        combos = [c for c in combos if c[0] == getattr(args, "place", None)]
    if getattr(args, "delivery", None):
        combos = [c for c in combos if c[1] == getattr(args, "delivery", None)]
    if getattr(args, "parcel", None):
        combos = [c for c in combos if c[2] == getattr(args, "parcel", None)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, delivery_id, parcel_id = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    helper_gender = getattr(args, "helper_gender", None) or ("boy" if gender == "girl" else "girl")
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper_name = getattr(args, "helper_name", None) or rng.choice(BOY_NAMES if helper_gender == "boy" else GIRL_NAMES)
    return StoryParams(place=place, delivery=delivery_id, parcel=parcel_id, name=name, gender=gender, helper_name=helper_name, helper_gender=helper_gender)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(DELIVERIES, params.delivery), _safe_lookup(PARCELS, params.parcel), params.name, params.gender, params.helper_name, params.helper_gender)
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
at_risk(D, P) :- delivery(D), parcel(P), risky_region(D, R), parcel_region(P, R).
good_fix(D, P) :- at_risk(D, P), helper(H), fixes(H, D), covers(H, R), parcel_region(P, R).
valid_story(Place, D, P) :- affords(Place, D), at_risk(D, P), good_fix(D, P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for d in sorted(s.affords):
            lines.append(asp.fact("affords", pid, d))
    for did, d in DELIVERIES.items():
        lines.append(asp.fact("delivery", did))
        lines.append(asp.fact("risky_region", did, d.risk))
    for pid, p in PARCELS.items():
        lines.append(asp.fact("parcel", pid))
        lines.append(asp.fact("parcel_region", pid, p.region))
    for h in HELPERS:
        lines.append(asp.fact("helper", h.id))
        for c in sorted(h.covers):
            lines.append(asp.fact("covers", h.id, c))
        for g in sorted(h.guards):
            lines.append(asp.fact("fixes", h.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/3."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    python_set = set(valid_combos())
    clingo_set = set(asp_valid_combos())
    if python_set == clingo_set:
        print(f"OK: clingo gate matches valid_combos() ({len(python_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    return 1


CURATED = [
    StoryParams(place="village", delivery="muddy_road", parcel="bread", name="Mara", gender="girl", helper_name="Ned", helper_gender="boy"),
    StoryParams(place="hill", delivery="windy_hill", parcel="blanket", name="Lina", gender="girl", helper_name="Oren", helper_gender="boy"),
    StoryParams(place="river", delivery="river_path", parcel="soup", name="Tess", gender="girl", helper_name="Finn", helper_gender="boy"),
]


def build_sample(params: StoryParams) -> StorySample:
    return generate(params)


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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
        return

    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [build_sample(p) for p in CURATED]
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
            sample = build_sample(params)
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
            header = f"### {p.name}: {p.delivery} at {p.place}"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
