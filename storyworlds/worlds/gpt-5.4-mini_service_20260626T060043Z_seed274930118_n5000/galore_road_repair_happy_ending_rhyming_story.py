#!/usr/bin/env python3
"""
storyworlds/worlds/galore_road_repair_happy_ending_rhyming_story.py
====================================================================

A small story world about a road repair day with galore amounts of tools,
cones, signs, tar, and a happy ending. The prose is built from a simulated
state so the ending changes because the road gets fixed, not because the nouns
were swapped.

Seed tale premise:
---
A little road by the sleepy town had a big pothole galore. The repair crew came
with cones, signs, a roller, and a bucket of tar. At first, the road was shut
and cars had to wait. Then the crew fixed the hole, opened the lane, and the
town could roll home again with smiles galore.

Style notes:
- Rhyming Story cadence: short, clear, sing-song lines and paired sounds.
- Happy Ending: the road ends smooth, open, and safe.
- Road repair setting: typed entities, meters for physical state, memes for mood.
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sys
from collections import defaultdict
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
    kind: str = "thing"  # "character" | "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    region: str = ""
    plural: bool = False
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    cones: object | None = None
    driver: object | None = None
    foreman: object | None = None
    prize_ent: object | None = None
    road: object | None = None
    roller: object | None = None
    sign: object | None = None
    tar: object | None = None
    worker: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.kind == "character" and self.type in {"worker", "foreman", "driver", "kid"}:
            return {"subject": "they", "object": "them", "possessive": "their"}[case]
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
    place: str = "the road"
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
    id: str
    label: str
    phrase: str
    region: str
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
        return any(item.protective and region in item.covers for item in self.worn_items(actor))

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
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def rhyme(a: str, b: str) -> str:
    return f"{a} {b}".strip()


def article(noun: str) -> str:
    return "an" if noun[:1].lower() in "aeiou" else "a"


def pred_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in _safe_lookup(ACTIVITY_ZONES, activity.id)


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if pred_risk(act, prize) and select_gear(act, prize):
                    out.append((place, prize_id))
    return sorted(out)


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        pass
    actor.meters[activity.mess] += 1
    actor.memes["busy"] += 1
    if narrate:
        world.say(f"{actor.label} got to work, with {activity.gerund} in the air.")


def propagate(world: World, narrate: bool = True) -> None:
    produced = []
    for actor in world.characters():
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region != "road":
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("mess", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["damage"] += 1
                produced.append(f"The {item.label} got {mess} and needed care.")
    if narrate:
        for s in produced:
            world.say(s)


def inspect(world: World, foreman: Entity, road: Entity) -> None:
    if road.meters["damage"] >= THRESHOLD:
        world.say(
            f"{foreman.label} saw the pothole and gave a kind little call: "
            f"'This road needs fixin' before traffic can run.'"
        )
        world.facts["needs_fix"] = True


def block(world: World, foreman: Entity) -> None:
    world.say(f"Cones lined the lane, neat as a row, and the stop sign blinked, slow and slow.")
    for e in list(world.entities.values()):
        if e.label == "cones" or e.label == "stop sign":
            e.meters["block"] += 1


def warn_cars(world: World, driver: Entity) -> None:
    world.say(f"{driver.label} rolled up, then sighed with a 'oh-no' sigh.")
    driver.memes["patient"] += 1


def repair(world: World, crew: Entity, road: Entity) -> None:
    world.say("The crew poured tar, dark and hot, and packed the hole just right on the spot.")
    road.meters["damage"] = max(0.0, road.meters["damage"] - 1.0)
    road.meters["smooth"] += 1
    road.memes["hope"] += 1


def roll_flat(world: World, roller: Entity, road: Entity) -> None:
    world.say("The roller went round with a humming sound, making the patch firm and sound.")
    road.meters["smooth"] += 1
    road.meters["damage"] = max(0.0, road.meters["damage"] - 0.5)


def open_road(world: World, foreman: Entity, road: Entity) -> None:
    if road.meters["smooth"] >= THRESHOLD and road.meters["damage"] < THRESHOLD:
        world.say("At last, the lane was open again, and every wheel could ease like rain.")
        world.say("Cars could go zoom, the town wore smiles, and the day felt bright for many miles.")
        world.facts["opened"] = True


def tell(setting: Setting, activity: Activity, prize: Prize, name: str, role: str, seed: int | None = None) -> World:
    world = World(setting)
    road = world.add(Entity(id="road", kind="thing", type="road", label="the road", region="road"))
    road.meters["damage"] = 1.0
    road.memes["worry"] = 1.0

    worker = world.add(Entity(id=name, kind="character", type=role, label=name))
    foreman = world.add(Entity(id="foreman", kind="character", type="foreman", label="Mira"))
    driver = world.add(Entity(id="driver", kind="character", type="driver", label="Jules"))
    cones = world.add(Entity(id="cones", kind="thing", type="cones", label="cones", plural=True, protective=True))
    sign = world.add(Entity(id="stop", kind="thing", type="sign", label="stop sign", protective=True))
    tar = world.add(Entity(id="tar", kind="thing", type="tar", label="tar bucket"))
    roller = world.add(Entity(id="roller", kind="thing", type="roller", label="road roller"))
    prize_ent = world.add(Entity(id="pothole", kind="thing", type="hole", label=prize.label, region="road"))

    world.facts.update(worker=worker, foreman=foreman, driver=driver, road=road, prize=prize_ent, activity=activity)

    world.say(f"{worker.label} came early by the road, where the pothole sat like a grumpy toad.")
    world.say(f"The hole was there in a big galore, and tires would bounce if they crossed once more.")
    world.say(f"{foreman.label} brought cones and a stop sign bright, to keep the cars safe and tight.")

    world.para()
    inspect(world, foreman, road)
    block(world, foreman)
    warn_cars(world, driver)
    world.say(f"{worker.label} loved the job and the busy buzz, with {activity.gerund} and hammering as it was.")

    world.para()
    world.say(f"{worker.label} wanted to {activity.verb}, and the crew said yes, with careful cheer.")
    _do_activity(world, worker, activity, narrate=True)
    world.say(f"The tar went in with a sticky spin, to fill the crack and tuck it in.")
    repair(world, worker, road)
    roll_flat(world, roller, road)
    open_road(world, foreman, road)

    world.para()
    if world.facts.get("opened"):
        world.say(f"{driver.label} waved and whispered, 'Hooray!' as the road shone smooth in the light of day.")
        world.say(f"The crew went home with mud on shoes, but happy hearts and good repair news.")
    else:
        world.say("The road was still not ready, so the crew kept at it steady and steady.")

    return world


SETTINGS = {
    "main_road": Setting(place="the main road", affords={"patch", "pave"}),
    "lane": Setting(place="the lane", affords={"patch"}),
    "bridge_approach": Setting(place="the bridge approach", affords={"patch"}),
}

ACTIVITIES = {
    "patch": Activity(
        id="patch",
        verb="patch the pothole",
        gerund="patching potholes",
        rush="rush to the pothole",
        mess="dirty",
        soil="patched and neat",
        keyword="galore",
        tags={"repair", "road", "galore"},
    ),
    "pave": Activity(
        id="pave",
        verb="pave the road",
        gerund="paving the road",
        rush="rush to the lane",
        mess="dusty",
        soil="paved and smooth",
        keyword="galore",
        tags={"repair", "road"},
    ),
}

ACTIVITY_ZONES = {
    "patch": {"road"},
    "pave": {"road"},
}

PRIZES = {
    "pothole": Prize(id="pothole", label="pothole", phrase="a big pothole", region="road"),
    "crack": Prize(id="crack", label="crack", phrase="a deep crack", region="road"),
}

GEAR = [
    Gear(id="cones", label="cones", covers={"road"}, guards={"dirty", "dusty"}, prep="set out the cones first", tail="set out the cones"),
    Gear(id="sign", label="stop sign", covers={"road"}, guards={"dirty", "dusty"}, prep="raise the stop sign first", tail="raised the stop sign"),
    Gear(id="roller", label="road roller", covers={"road"}, guards={"dirty", "dusty"}, prep="bring the road roller in", tail="brought the road roller in"),
]

MESS_KINDS = {"dirty", "dusty"}

NAMES = ["Mira", "Jun", "Pip", "Tess", "Rory", "Nina"]
ROLES = ["worker", "kid", "worker"]


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
    name: str
    role: str
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
        f'Write a rhyming story about road repair with the word "{f["activity"].keyword}".',
        f"Tell a happy ending story where {f['worker'].label} helps fix {f['prize'].label} on {world.setting.place}.",
        f"Write a small child-friendly tale about cones, tar, and a road that gets smooth again.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    road: Entity = _safe_fact(world, f, "road")
    return [
        QAItem(
            question="What was wrong with the road at the start?",
            answer="The road had a big pothole, so the cars could not roll through safely.",
        ),
        QAItem(
            question=f"Who helped fix the road?",
            answer=f"{f['worker'].label} helped with the repair crew, along with Mira, the foreman.",
        ),
        QAItem(
            question="How did the story end?",
            answer="The road got smooth again, the lane opened, and everybody was happy.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What are cones used for on a road repair day?",
            answer="Cones help warn people and keep cars away from a spot that is being fixed.",
        ),
        QAItem(
            question="What does tar do in road repair?",
            answer="Tar fills holes and cracks so the road can become strong and smooth again.",
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
            bits.append(f"meters={dict(meters)}")
        if memes:
            bits.append(f"memes={dict(memes)}")
        if e.covers:
            bits.append(f"covers={sorted(e.covers)}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


def explain_rejection(place: Optional[str], activity: Optional[str], prize: Optional[str]) -> str:
    if activity and prize:
        act = _safe_lookup(ACTIVITIES, activity)
        pr = _safe_lookup(PRIZES, prize)
        if not pred_risk(act, pr):
            return f"(No story: {pr.label} is not at risk in {act.gerund}.)"
        if not select_gear(act, pr):
            return f"(No story: no gear can fairly fix {pr.label} during {act.gerund}.)"
    return "(No story: the requested choices do not make a clean repair tale.)"


def asp_facts() -> str:
    import asp

    lines = []
    for pid, setting in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(_safe_lookup(ACTIVITY_ZONES, aid)):
            lines.append(asp.fact("splashes", aid, r))
    for pr_id, pr in PRIZES.items():
        lines.append(asp.fact("prize", pr_id))
        lines.append(asp.fact("worn_on", pr_id, pr.region))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
        for g in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, g))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
"""


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp

    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    import asp

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
    ap = argparse.ArgumentParser(description="A rhyming road-repair story world with a happy ending.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--name", choices=NAMES)
    ap.add_argument("--role", choices=["worker", "kid"])
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
        if not (pred_risk(_safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))) and select_gear(_safe_lookup(ACTIVITIES, getattr(args, "activity", None)), _safe_lookup(PRIZES, getattr(args, "prize", None)))):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "prize", None) is None or c[1] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, prize = rng.choice(combos)
    activity = getattr(args, "activity", None) or rng.choice(list(ACTIVITIES))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    role = getattr(args, "role", None) or rng.choice(ROLES)
    return StoryParams(place=place, activity=activity, prize=prize, name=name, role=role)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.role, params.seed)
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
    StoryParams(place="main_road", activity="patch", prize="pothole", name="Mira", role="worker"),
    StoryParams(place="lane", activity="patch", prize="crack", name="Jun", role="worker"),
    StoryParams(place="bridge_approach", activity="patch", prize="pothole", name="Tess", role="worker"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid/3."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        for row in asp_valid_combos():
            print(row)
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
        header = f"### variant {i + 1}" if len(samples) > 1 else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
