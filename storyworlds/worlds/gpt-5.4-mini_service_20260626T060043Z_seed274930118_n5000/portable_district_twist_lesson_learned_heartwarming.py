#!/usr/bin/env python3
"""
storyworlds/worlds/portable_district_twist_lesson_learned_heartwarming.py
===========================================================================

A compact storyworld about a child, a portable treasure, and a district outing
that turns into a heartwarming lesson learned with a small twist.

Seed tale:
---
In a busy district, a child loved a portable little lantern that their grandmother
had packed in a cloth bag. One evening, the child wanted to hurry to the district
square to show it off. Grandmother worried the lantern would get bumped or dimmed.
The child tried to rush anyway, but the lantern slipped and flickered. Then the
twist: the lantern was not meant for showing off at all. It was meant to help the
neighbors find their way home after dark. The child slowed down, listened, and
carried it carefully. In the end, the lantern lit the path for everyone, and the
child learned that gentle care can be its own kind of kindness.
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
    carried_by: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    portable: bool = False
    fragile: bool = False
    help_role: str = ""
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    aid: object | None = None
    child: object | None = None
    helper: object | None = None
    item: object | None = None
    def __post_init__(self) -> None:
        for k in ["spilled", "dimmed", "tired", "care"]:
            self.meters.setdefault(k, 0.0)
        for k in ["joy", "worry", "pride", "tenderness", "impatience", "relief", "lesson"]:
            self.memes.setdefault(k, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "grandmother", "woman"}
        male = {"boy", "father", "grandfather", "man"}
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
    district: str
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
    pace: str
    risk: str
    zone: set[str]
    keyword: str
    twist: str
    lesson: str
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
class Aid:
    id: str
    label: str
    prep: str
    tail: str
    protects: set[str]
    helps: set[str]
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

    def carried_items(self, actor: Entity) -> list[Entity]:
        return [e for e in self.entities.values() if e.carried_by == actor.id]

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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


def _r_spill(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters["rushing"] < THRESHOLD:
            continue
        for item in world.carried_items(actor):
            if not item.fragile:
                continue
            sig = ("spill", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["spilled"] += 1
            item.meters["dimmed"] += 1
            actor.memes["worry"] += 1
            out.append(f"{item.label.capitalize()} slipped and looked sad.")
    return out


def _r_care(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters["spilled"] < THRESHOLD and item.meters["dimmed"] < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("care", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["tenderness"] += 1
        carer.meters["care"] += 1
        out.append(f"{carer.label.capitalize()} took a careful breath and helped.")
    return out


CAUSAL_RULES = [_r_spill, _r_care]


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


def subject_name(entity: Entity) -> str:
    return entity.label or entity.id


def predict_spill(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["rushing"] += 1
    sim.zone = set(activity.zone)
    propagate(sim, narrate=False)
    prize = sim.entities[prize_id]
    return {"spoiled": prize.meters["spilled"] >= THRESHOLD, "care": sum(e.meters["care"] for e in sim.characters())}


def activity_detail(activity: Activity) -> str:
    return {
        "lantern": "The little light gave the alley a warm silver glow.",
        "basket": "The basket smelled like bread and oranges and home.",
        "birdhouse": "The painted birdhouse had tiny flowers on the roof.",
    }.get(activity.id, "It made the afternoon feel bright.")


def setting_detail(setting: Setting) -> str:
    return f"In the {setting.district}, {setting.place} sat between kind faces and familiar shop windows."


def intro(world: World, child: Entity) -> None:
    trait = next((t for t in child.traits if t != "little"), "kind")
    world.say(
        f"{child.id} was a little {trait} {child.type} who loved careful things."
    )


def love_item(world: World, child: Entity, item: Entity) -> None:
    child.memes["joy"] += 1
    item.carried_by = child.id
    world.say(
        f"{child.id} loved {item.phrase} and carried {item.it()} everywhere as if it were a tiny treasure."
    )


def arrival(world: World, child: Entity, helper: Entity, activity: Activity) -> None:
    world.say(
        f"One evening, {child.id} went to {world.setting.place} with {helper.label}. "
        f"{setting_detail(world.setting)}"
    )
    world.say(activity_detail(activity))


def wants(world: World, child: Entity, activity: Activity) -> None:
    child.memes["impatience"] += 1
    world.say(
        f"{child.id} wanted to {activity.verb}, because {activity.twist.lower()}"
    )


def warn(world: World, helper: Entity, child: Entity, item: Entity, activity: Activity) -> bool:
    pred = predict_spill(world, child, activity, item.id)
    if not pred["spoiled"]:
        return False
    world.facts["predicted_care"] = pred["care"]
    world.say(
        f'"Slow down," {helper.label} said. "If you rush, {item.label} might get {activity.risk}."'
    )
    helper.memes["worry"] += 1
    return True


def rush(world: World, child: Entity, activity: Activity) -> None:
    child.meters["rushing"] += 1
    child.memes["impatience"] += 1
    world.say(f"{child.id} tried to {activity.rush}, even though the warning was still warm in {child.pronoun('possessive')} ears.")


def twist_turn(world: World, helper: Entity, child: Entity, item: Entity, activity: Activity) -> None:
    world.say(
        f"Then came the twist: {activity.twist}."
    )
    world.say(
        f"{helper.label} explained that {item.label} was not just for {child.id}; it was meant to help other people in the {world.setting.district} too."
    )
    child.memes["lesson"] += 1
    helper.memes["pride"] += 1


def choose_gentle(world: World, child: Entity, helper: Entity, item: Entity, activity: Activity, aid: Aid) -> None:
    world.say(
        f'{helper.label} smiled and said, "{aid.prep}."'
    )
    world.say(
        f"{child.id} nodded, loosened {child.pronoun('possessive')} hurried hands, and carried {item.label} more gently."
    )


def resolve(world: World, child: Entity, helper: Entity, item: Entity, activity: Activity, aid: Aid) -> None:
    child.memes["joy"] += 1
    child.memes["relief"] += 1
    helper.memes["tenderness"] += 1
    item.carried_by = child.id
    world.say(
        f"They {aid.tail}. Soon {child.id} was {activity.gerund}, and {item.label} stayed safe and bright."
    )
    world.say(
        f"That made the whole {world.setting.district} feel a little warmer."
    )
    world.say(
        f"In the end, {child.id} learned that being careful can be a way to care for everyone."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, aid_def: Aid,
         child_name: str = "Mina", child_type: str = "girl",
         child_traits: Optional[list[str]] = None) -> World:
    world = World(setting)
    child = world.add(Entity(
        id=child_name,
        kind="character",
        type=child_type,
        label=child_name,
        traits=["little"] + (child_traits or ["gentle", "curious"]),
    ))
    helper = world.add(Entity(
        id="Helper",
        kind="character",
        type="grandmother",
        label="Grandmother",
    ))
    item = world.add(Entity(
        id="item",
        type=prize_cfg.type,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=child.id,
        caretaker=helper.id,
        fragile=True,
        portable=True,
    ))
    aid = world.add(Entity(
        id=aid_def.id,
        type="aid",
        label=aid_def.label,
        portable=True,
        fragile=False,
    ))
    aid.carried_by = child.id

    intro(world, child)
    love_item(world, child, item)
    world.para()
    arrival(world, child, helper, activity)
    wants(world, child, activity)
    warn(world, helper, child, item, activity)
    rush(world, child, activity)
    propagate(world)
    world.para()
    twist_turn(world, helper, child, item, activity)
    choose_gentle(world, child, helper, item, activity, aid_def)
    resolve(world, child, helper, item, activity, aid_def)
    world.facts.update(child=child, helper=helper, item=item, aid=aid_def, activity=activity, setting=setting)
    return world


SETTINGS = {
    "square": Setting(place="the district square", district="district", affords={"lantern", "basket", "birdhouse"}),
    "lane": Setting(place="the little lane", district="district", affords={"lantern", "basket"}),
    "garden": Setting(place="the pocket garden", district="district", affords={"lantern", "birdhouse"}),
}

ACTIVITIES = {
    "lantern": Activity(
        id="lantern",
        verb="show the lantern to the neighbors",
        gerund="showing the lantern to the neighbors",
        rush="run to the corner market",
        pace="walk slowly",
        risk="dimmed",
        zone={"hands"},
        keyword="portable",
        twist="the lantern was meant to light the way home for everyone in the district",
        lesson="careful hands can help a whole neighborhood",
        tags={"portable", "light"},
    ),
    "basket": Activity(
        id="basket",
        verb="bring the basket to the bakery",
        gerund="bringing the basket along gently",
        rush="run toward the bakery door",
        pace="walk carefully",
        risk="spilled",
        zone={"hands"},
        keyword="portable",
        twist="the basket held little rolls for a neighbor who had stayed home sick",
        lesson="sharing is sweeter when nothing gets lost",
        tags={"portable", "food"},
    ),
    "birdhouse": Activity(
        id="birdhouse",
        verb="carry the birdhouse to the porch",
        gerund="carrying the birdhouse carefully",
        rush="dash across the patio",
        pace="step softly",
        risk="scratched",
        zone={"hands"},
        keyword="portable",
        twist="the birdhouse was a welcome gift for the kind family next door",
        lesson="gentle care is a gift all by itself",
        tags={"portable", "home"},
    ),
}

PRIZES = {
    "lantern": Prize(label="lantern", phrase="a small portable lantern", type="lantern", region="hands"),
    "basket": Prize(label="basket", phrase="a woven portable basket", type="basket", region="hands"),
    "birdhouse": Prize(label="birdhouse", phrase="a little portable birdhouse", type="birdhouse", region="hands"),
}

AIDS = {
    "cloth": Aid(
        id="cloth",
        label="soft cloth strap",
        prep="let's use the soft cloth strap and walk slowly",
        tail="walked slowly and kept the lantern steady",
        protects={"hands"},
        helps={"dimmed", "spilled", "scratched"},
    ),
    "tray": Aid(
        id="tray",
        label="flat carrying tray",
        prep="let's set it on the flat carrying tray first",
        tail="took careful steps with the tray",
        protects={"hands"},
        helps={"spilled", "scratched"},
    ),
    "box": Aid(
        id="box",
        label="sturdy little box",
        prep="let's place it in the sturdy little box",
        tail="carried the box like a treasure",
        protects={"hands"},
        helps={"dimmed", "spilled", "scratched"},
    ),
}

GIRL_NAMES = ["Mina", "Lena", "Tia", "Nora", "Iris"]
BOY_NAMES = ["Owen", "Eli", "Sam", "Noah", "Finn"]
TRAITS = ["gentle", "curious", "careful", "bright", "shy"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize.region in act.zone:
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    gender: str
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


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a heartwarming story about a child named {f["child"].id} carrying a portable {f["item"].label} through the district.',
        f"Tell a story where {f['child'].id} wants to {f['activity'].verb} but learns to go slowly after {f['helper'].label} worries about the {f['item'].label}.",
        f'Write a gentle story with the words "portable", "district", "twist", and "lesson learned".',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    child, helper, item, activity = f["child"], f["helper"], f["item"], f["activity"]
    return [
        QAItem(
            question=f"What did {child.id} love to carry through the district?",
            answer=f"{child.id} loved carrying {item.phrase}. It felt like a tiny treasure in {child.pronoun('possessive')} hands.",
        ),
        QAItem(
            question=f"Why did {helper.label} tell {child.id} to slow down?",
            answer=f"{helper.label} worried that if {child.id} rushed, the {item.label} might get {activity.risk}. She wanted the little treasure to stay safe.",
        ),
        QAItem(
            question=f"What was the twist in the story?",
            answer=f"The twist was that {item.label} was not only for showing off. It was meant to help people in the {world.setting.district} too.",
        ),
        QAItem(
            question=f"What lesson learned did {child.id} end up with?",
            answer=f"{child.id} learned that gentle care can be a kind of helping, and that slowing down can keep everyone happier.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    act = _safe_fact(world, f, "activity")
    out = [
        QAItem(
            question="What does portable mean?",
            answer="Portable means something is easy to carry from one place to another.",
        ),
        QAItem(
            question="What is a district?",
            answer="A district is a part of a town or city, like a neighborhood with its own streets and places.",
        ),
    ]
    if "portable" in act.tags:
        out.append(QAItem(
            question="Why can a portable thing still need careful hands?",
            answer="A portable thing can still be fragile, so careful hands help it stay safe while it is being carried.",
        ))
    return out


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
        meters = {k: v for k, v in e.meters.items() if v}
        memes = {k: v for k, v in e.memes.items() if v}
        bits = []
        if meters:
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.portable:
            bits.append("portable=True")
        if e.fragile:
            bits.append("fragile=True")
        if e.carried_by:
            bits.append(f"carried_by={e.carried_by}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="square", activity="lantern", prize="lantern", name="Mina", gender="girl", trait="gentle"),
    StoryParams(place="lane", activity="basket", prize="basket", name="Owen", gender="boy", trait="curious"),
    StoryParams(place="garden", activity="birdhouse", prize="birdhouse", name="Lena", gender="girl", trait="careful"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Heartwarming portable district storyworld with a twist and a lesson learned.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--parent")  # accepted for interface symmetry; unused
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
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, gender=gender, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), AIDS["cloth"], params.name, params.gender, [params.trait])
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
valid(Place,Act,Prize) :- affords(Place,Act), at_risk(Act,Prize).
valid_story(Place,Act,Prize,Gender) :- valid(Place,Act,Prize), wears(Gender,Prize).
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
            lines.append(asp.fact("at_risk_zone", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_combos_asp() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    cl = set(valid_combos_asp())
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


def main() -> None:
    args = build_parser().parse_args()

    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = valid_combos_asp()
        print(f"{len(combos)} compatible (place, activity, prize) combos:")
        for p, a, pr in combos:
            print(f"  {p:7} {a:10} {pr}")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
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
