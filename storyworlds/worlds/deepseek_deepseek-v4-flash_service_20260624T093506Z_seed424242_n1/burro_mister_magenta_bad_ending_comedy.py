#!/usr/bin/env python3
"""
storyworlds/worlds/burro_mister_magenta_bad_ending_comedy.py
=============================================================

A standalone comedy story world where a hungry burro keeps trying to eat a
magenta hat that Mister treasures.  The ending is always bad: the burro either
ruins the hat or gets a tummy ache, and Mister is left sad.

Based on the seed words: burro, mister, magenta.
"""

from __future__ import annotations

import argparse
import copy
import json
import os
import random
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Callable, Optional

_storyworlds_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if not os.path.exists(os.path.join(_storyworlds_dir, "results.py")):
    _storyworlds_dir = os.path.dirname(_storyworlds_dir)
sys.path.insert(0, _storyworlds_dir)
from results import QAItem, StoryError, StorySample  # noqa: E402

THRESHOLD = 1.0
MESS_KINDS = {"chewed", "slobbered", "stained"}
REGIONS = {"mouth", "head", "neck"}



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
    region: str = ""
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: defaultdict(float))

    burro: object | None = None
    gear: object | None = None
    mister: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"mare", "nanny"}
        male = {"burro", "mister", "boy", "man"}
        if self.type in female:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in male:
            return {"subject": "he", "object": "him", "possessive": "his"}[case]
        return {"subject": "it", "object": "it", "possessive": "its"}[case]

    def it(self) -> str:
        return "them" if self.plural else "it"

    @property
    def label_word(self) -> str:
        return self.type
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
    place: str = "the meadow"
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
    weather: str = ""
    keyword: str = ""
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
    genders: set[str] = field(default_factory=lambda: {"burro", "mister"})
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
        self.weather: str = ""
        self.facts: dict = {}
        self.bad_ending: bool = False

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
        chunks = [" ".join(p) for p in self.paragraphs if p]
        return "\n\n".join(chunks)

    def copy(self) -> "World":
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.weather = self.weather
        clone.paragraphs = [[]]
        return clone


@dataclass
class Rule:
    name: str
    tag: str
    apply: Callable[[World], list[str]]
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


def _r_chew(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        if actor.type != "burro":
            continue
        for mess in MESS_KINDS:
            if actor.meters[mess] < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.region not in world.zone:
                    continue
                if world.covered(actor, item.region):
                    continue
                sig = ("chew", item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                item.meters[mess] += 1
                item.meters["ruined"] += 1
                out.append(
                    f"{actor.pronoun('possessive').capitalize()} {item.label} "
                    f"got {mess} and ruined."
                )
                world.bad_ending = True
                break
    return out


def _r_sadness(world: World) -> list[str]:
    out = []
    for item in list(world.entities.values()):
        if item.meters["ruined"] < THRESHOLD or not item.caretaker:
            continue
        sig = ("sad", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["sadness"] += 1
        out.append(f"That made {carer.label_word} very sad.")
    return out


def _r_grab_conflict(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes["grabbed_by"] < THRESHOLD or actor.memes["defiance"] < THRESHOLD:
            continue
        sig = ("conflict", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["conflict"] += 1
        return ["__conflict__"]
    return []


CAUSAL_RULES: list[Rule] = [
    Rule(name="chew", tag="physical", apply=_r_chew),
    Rule(name="sadness", tag="social", apply=_r_sadness),
    Rule(name="grab_conflict", tag="social", apply=_r_grab_conflict),
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(s for s in sents if s != "__conflict__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity, narrate=False)
    prize = sim.entities.get(prize_id)
    return {
        "ruined": bool(prize and prize.meters["ruined"] >= THRESHOLD),
        "sadness": sum(e.memes["sadness"] for e in sim.characters()),
    }


def activity_delight(activity: Activity) -> str:
    return {
        "snacking": "the crunchy flowers made a funny noise inside his mouth",
        "digging": "the soft earth flew up and tickled his nose",
    }.get(activity.id, "it felt very silly")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.indoor:
        return f"The {setting.place.removeprefix('the ')} was warm and full of hay."
    return f"The {setting.place.removeprefix('the ')} looked bright and full of snacks."


def _do_activity(world: World, actor: Entity, activity: Activity, narrate: bool = True) -> None:
    if activity.id not in world.setting.affords:
        return
    world.zone = set(activity.zone)
    actor.meters[activity.mess] += 1
    actor.memes["joy"] += 1
    propagate(world, narrate=narrate)


def snack_phrase(prize: Entity | Prize) -> str:
    return f"snack on the magenta {prize.label}"


def introduce(world: World, burro: Entity) -> None:
    trait = next((t for t in burro.traits if t != "little"), "silly")
    world.say(f"{burro.id} was a small, {trait} burro with big ears and a love for snacks.")


def loves_activity(world: World, burro: Entity, activity: Activity) -> None:
    burro.memes["love_play"] += 1
    world.say(f"He loved {activity.gerund}; {activity_delight(activity)}.")


def mister_appears(world: World, mister: Entity, prize: Entity) -> None:
    world.say(f"One day, {mister.id} came to {world.setting.place} wearing {prize.phrase}.")
    world.say(f"The {prize.label} was bright magenta, and {mister.id} was very proud of it.")


def burro_notices(world: World, burro: Entity, prize: Entity) -> None:
    world.say(f"{burro.id} saw the magenta {prize.label} and forgot all about flowers. He wanted that {prize.label}.")


def warns(world: World, mister: Entity, burro: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_mess(world, burro, activity, prize.id)
    if not pred["ruined"]:
        return False
    world.facts["predicted_ruin"] = activity.soil
    world.facts["predicted_sadness"] = pred["sadness"]
    clause = f"You'll chew my {prize.label} and ruin it"
    if pred["sadness"] >= THRESHOLD:
        clause += ", and I'll be very sad"
    world.say(f'"{clause}," said {mister.id}. "Please eat flowers instead."')
    return True


def defies(world: World, burro: Entity, activity: Activity) -> None:
    burro.memes["defiance"] += 1
    prize = world.facts.get("prize")
    prize_label = prize.label if prize is not None else "prize"
    desire = snack_phrase(prize) if prize is not None else activity.verb
    world.say(f"{burro.id} twitched his ears and looked at the {prize_label} again. He really wanted to {desire}.")
    world.say(f"He crept closer, trying to {activity.rush},")


def grab_hand(world: World, mister: Entity, burro: Entity) -> None:
    burro.memes["grabbed_by"] += 1
    propagate(world, narrate=False)
    prize = world.facts.get("prize")
    prize_label = prize.label if prize is not None else "prize"
    world.say(f"but {mister.id} grabbed his halter and said, 'No, {burro.id}! That {prize_label} is not a snack.'")


def pout(world: World, burro: Entity) -> None:
    if burro.memes["conflict"] >= THRESHOLD:
        world.say(f"{burro.id} stomped his little hooves and let out a sad 'Hee-haw!'")


def compromise(world: World, mister: Entity, burro: Entity, activity: Activity,
               prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(
        id=gear_def.id, type="gear", label=gear_def.label,
        owner=burro.id, caretaker=mister.id, protective=True,
        covers=set(gear_def.covers), plural=gear_def.plural,
    ))
    gear.worn_by = burro.id
    if predict_mess(world, burro, activity, prize.id)["ruined"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say(
        f'{mister.id} sighed, then smiled. "How about we {gear_def.prep} '
        f'and you can {snack_phrase(prize)}?"'
    )
    return gear_def


def bad_ending(world: World, burro: Entity, mister: Entity, prize: Entity,
               gear_def: Optional[Gear]) -> None:
    if not world.bad_ending:
        # Simulate a bad ending anyway: burro chews the prize despite gear.
        world.bad_ending = True
        gear_label = gear_def.label if gear_def is not None else f"{mister.id}'s warning"
        world.say(f"But {burro.id} was too clever. He wiggled past {gear_label} and grabbed the {prize.label}.")
        world.facts["gear_failed"] = True
    else:
        world.say(f"But {burro.id} was too fast. Before {mister.id} could stop him, he grabbed the {prize.label}.")
    world.say(f"He chewed the magenta {prize.label} until it was a soggy, ruined mess.")
    world.say(f"{mister.id} stared at the shreds of his {prize.label}. His heart felt heavy.")
    mister.memes["sadness"] += 1
    burro.memes["conflict"] = 0.0
    burro.memes["sadness"] += 0.5
    world.say(f"{burro.id} let out a small 'Hee-haw' — but this time it wasn't happy.")
    world.say(f"He learned that some things are not snacks, but the lesson came with a very sad {mister.id}.")


# Actual tell function
def tell(setting: Setting, activity: Activity, prize_cfg: Prize,
         hero_name: str = "Burrito", hero_type: str = "burro",
         hero_traits: Optional[list[str]] = None,
         mister_name: str = "Mister", parent_type: str = "mister") -> World:
    world = World(setting)
    world.weather = "" if setting.indoor else activity.weather

    burro = world.add(Entity(
        id=hero_name, kind="character", type=hero_type,
        traits=["little"] + (hero_traits or ["silly", "stubborn"]),
    ))
    mister = world.add(Entity(
        id=mister_name, kind="character", type=parent_type,
        label=mister_name, traits=["kind", "proud"],
    ))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label,
        phrase=prize_cfg.phrase, owner=mister.id, caretaker=mister.id,
        region=prize_cfg.region, plural=prize_cfg.plural,
    ))
    world.facts["prize"] = prize

    # Act 1
    introduce(world, burro)
    loves_activity(world, burro, activity)
    mister_appears(world, mister, prize)
    burro_notices(world, burro, prize)

    # Act 2
    world.para()
    warns(world, mister, burro, activity, prize)
    defies(world, burro, activity)
    grab_hand(world, mister, burro)

    # Act 3 - bad ending
    world.para()
    pout(world, burro)
    gear_def = compromise(world, mister, burro, activity, prize)
    if gear_def:
        # Gear might not work because we always force bad ending:
        bad_ending(world, burro, mister, prize, gear_def)
    else:
        # No gear possible: direct bad ending
        bad_ending(world, burro, mister, prize, None)

    world.facts.update(
        burro=burro, mister=mister, prize=prize, prize_cfg=prize_cfg,
        activity=activity, setting=setting,
        bad_ending=True,
    )
    return world


# --- Registries ---
SETTINGS = {
    "meadow": Setting(place="the meadow", affords={"snacking"}),
    "garden": Setting(place="the garden", affords={"snacking"}),
    "barn": Setting(place="the barn", indoor=True, affords={"snacking"}),
}

ACTIVITIES = {
    "snacking": Activity(
        id="snacking",
        verb="snack on the magenta hat",
        gerund="snacking on magenta flowers",
        rush="sneak a bite",
        mess="chewed",
        soil="chewed up",
        zone={"mouth"},
        weather="sunny",
        keyword="snack",
        tags={"snack", "chew"},
    ),
}

PRIZES = {
    "hat": Prize(
        label="hat",
        phrase="a bright magenta hat with a little feather",
        type="hat",
        region="mouth",
        genders={"burro", "mister"},
    ),
    "scarf": Prize(
        label="scarf",
        phrase="a long magenta scarf that fluttered in the breeze",
        type="scarf",
        region="mouth",
        genders={"burro", "mister"},
    ),
}

GEAR = [
    Gear(
        id="flower_basket",
        label="a basket of yellow flowers",
        covers={"mouth"},
        guards={"chewed"},
        prep="fill your basket with flowers instead",
        tail="fetched a basket of yellow flowers",
    ),
    Gear(
        id="muzzle",
        label="a soft muzzle",
        covers={"mouth"},
        guards={"chewed"},
        prep="put on this soft muzzle",
        tail="put the soft muzzle on Burrito",
    ),
]

BURRO_NAMES = ["Burrito", "Dusty", "Pablo", "Chico"]
MISTER_NAMES = ["Mr. Mango", "Mr. Magenta", "Sir Snacks"]
TRAITS = ["silly", "stubborn", "hungry", "playful"]


def valid_combos() -> list[tuple[str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    activity: str
    prize: str
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


KNOWLEDGE = {
    "snack": [("What is a snack?", "A snack is a small, tasty bit of food you eat between meals.")],
    "chew": [("Why do animals chew things?",
              "Animals chew to eat, but sometimes they chew things because they are curious or hungry.")],
    "burro": [("What is a burro?", "A burro is a small donkey with long ears, often very friendly and a bit stubborn.")],
    "magenta": [("What color is magenta?",
                 "Magenta is a bright pinkish-purple color, like a sunset mixed with a flower.")],
    "hat": [("Why do people wear hats?",
             "People wear hats to protect their head from the sun, or to look fancy.")],
    "sadness": [("What happens when someone is sad?",
                 "When someone is sad, they might feel heavy inside, and sometimes they cry or stay quiet.")],
}
KNOWLEDGE_ORDER = ["snack", "chew", "burro", "magenta", "hat", "sadness"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    burro, mister, act, prize = f["burro"], f["mister"], f["activity"], f["prize_cfg"]
    return [
        f'Write a short, funny story about a burro and a mister and a magenta {prize.label}, '
        f'with a bad ending where the {prize.label} gets ruined.',
        f'A silly burro named {burro.id} meets {mister.id} who has a {prize.label}. '
        f'The burro wants to {snack_phrase(prize)}, but the ending is not happy.',
        f'Make a comedy about a hungry burro, a proud mister, and a bright magenta prize.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    burro, mister, prize, act = f["burro"], f["mister"], f["prize"], f["activity"]
    sub, obj, pos = (burro.pronoun("subject"), burro.pronoun("object"),
                     burro.pronoun("possessive"))
    place = world.setting.place
    trait = next((t for t in burro.traits if t != "little"), burro.type)
    qa = [
        QAItem(
            question=f"Who is the story about when {burro.id} goes to {place}?",
            answer=f"It is about a silly {trait} burro named {burro.id} and {mister.id}. "
                   f"They meet in {place} where {mister.id} wears {prize.phrase}."
        ),
        QAItem(
            question=f"What did {trait} {burro.id} want to do with {pos} {prize.label}?",
            answer=f"{trait.capitalize()} {burro.id} wanted to {snack_phrase(prize)}. "
                   f"He thought the {prize.label} looked like a tasty snack."
        ),
        QAItem(
            question=f"Why did {mister.id} warn {burro.id} about the {prize.label}?",
            answer=f"{mister.id} warned because he knew {burro.id} would {act.rush} "
                   f"and ruin the {prize.label}, making him sad."
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"The story ended badly: {burro.id} ate the {prize.label} and ruined it, "
                   f"and {mister.id} was very sad. It was a funny but sad ending."
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    f = world.facts
    tags = set(f["activity"].tags)
    out = []
    for tag in globals().get("KNOWLEDGE_ORDER", sorted(globals().get("KNOWLEDGE", []))):
        if tag in tags:
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[tag])
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        elif e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:7}) {' '.join(bits)}")
    lines.append(f"  bad_ending={world.bad_ending}")
    lines.append(f"  fired rules: {sorted(set(n for n, *_ in world.fired))}")
    return "\n".join(lines)


CURATED = [
    StoryParams(
        place="meadow",
        activity="snacking",
        prize="hat",
        name="Burrito",
        gender="burro",
        parent="mister",
        trait="silly",
    ),
    StoryParams(
        place="garden",
        activity="snacking",
        prize="scarf",
        name="Dusty",
        gender="burro",
        parent="mister",
        trait="hungry",
    ),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    noun = prize.label if prize.plural else f"a {prize.label}"
    verb = "sit" if prize.plural else "sits"
    if not prize_at_risk(activity, prize):
        return (f"(No story: {activity.gerund} affects {sorted(activity.zone)}, "
                f"but {noun} {verb} on the {prize.region} -- it wouldn't get ruined. "
                f"Try a prize worn on {sorted(activity.zone)}.)")
    return (f"(No story: no gear in the catalog protects {noun} "
            f"({prize.region}) from {activity.gerund}. The compromise must actually "
            f"cover the at-risk region.)")


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P),
                     mess_of(A, M), guards(G, M),
                     covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp as _asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(_asp.fact("setting", pid))
        if s.indoor:
            lines.append(_asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(_asp.fact("affords", pid, a))
    for aid, a in ACTIVITIES.items():
        lines.append(_asp.fact("activity", aid))
        lines.append(_asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(_asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(_asp.fact("prize", pid))
        lines.append(_asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(_asp.fact("prize_plural", pid))
        for g in sorted(pr.genders):
            lines.append(_asp.fact("wears", g, pid))
    for g in GEAR:
        lines.append(_asp.fact("gear", g.id))
        for m in sorted(g.guards):
            lines.append(_asp.fact("guards", g.id, m))
        for r in sorted(g.covers):
            lines.append(_asp.fact("covers", g.id, r))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_valid_stories() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    clingo_set, python_set = set(asp_valid_combos()), set(valid_combos())
    if clingo_set == python_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - python_set:
        print("  only in clingo:", sorted(clingo_set - python_set))
    if python_set - clingo_set:
        print("  only in python:", sorted(python_set - clingo_set))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(
        description="Comedy story world: a burro, a mister, a magenta prize (bad ending).")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["burro", "mister"])
    ap.add_argument("--parent", choices=["mister"])
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
    place, activity, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = "burro"
    name = getattr(args, "name", None) or rng.choice(BURRO_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(MISTER_NAMES)
    trait = rng.choice(TRAITS)
    return StoryParams(
        place=place, activity=activity, prize=prize_id,
        name=name, gender=gender, parent=parent, trait=trait,
    )


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity),
                 _safe_lookup(PRIZES, params.prize), params.name, params.gender,
                 [params.trait, "stubborn"], params.parent)
    return StorySample(
        params=params,
        story=world.render(),
        prompts=generation_prompts(world),
        story_qa=story_qa(world),
        world_qa=world_knowledge_qa(world),
        world=world,
    )


def emit(sample: StorySample, *, trace: bool = False, qa: bool = False,
         header: str = "") -> None:
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples, stories = asp_valid_combos(), asp_valid_stories()
        print(f"{len(triples)} compatible (place, activity, prize) combos "
              f"({len(stories)} with gender):\n")
        for place, act, prize in triples:
            genders = sorted(g for (pl, a, pr, g) in stories
                             if (pl, a, pr) == (place, act, prize))
            print(f"  {place:9} {act:8} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)

    samples = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen = set()
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
            header = f"### {p.name}: {p.activity} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
