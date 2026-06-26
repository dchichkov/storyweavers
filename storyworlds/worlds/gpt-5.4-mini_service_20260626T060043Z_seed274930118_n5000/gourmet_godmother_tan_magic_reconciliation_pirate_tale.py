#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/gourmet_godmother_tan_magic_reconciliation_pirate_tale.py
==========================================================================================================

A small, standalone Storyweavers world: a pirate tale about gourmet wishes,
a godmother, tan keepsakes, a little magic, and a reconciliation that makes
the crew whole again.

The seed image:
- A young pirate loves a gourmet feast.
- A godmother worries that a magic trick may spoil a tan treasure.
- The child sulks, the godmother steadies the moment, and they reconcile by
  choosing a safer spell and sharing the result with the crew.

This script models that premise as a tiny simulated world with physical meters
and emotional memes, plus an ASP twin for the reasonableness gate.
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
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    gear_ent: object | None = None
    godmother: object | None = None
    hero: object | None = None
    prize: object | None = None
    def meter(self, key: str) -> float:
        return self.meters.get(key, 0.0)

    def meme(self, key: str) -> float:
        return self.memes.get(key, 0.0)

    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "godmother"}
        male = {"boy", "man", "father", "pirate"}
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
    indoor: bool
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
    name: str
    gender: str
    godmother: str
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

    def say(self, text: str) -> None:
        if text:
            self.paragraphs[-1].append(text)

    def para(self) -> None:
        if self.paragraphs[-1]:
            self.paragraphs.append([])

    def render(self) -> str:
        return "\n\n".join(" ".join(p) for p in self.paragraphs if p)


def _r_soil(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("magic", 0.0) < THRESHOLD:
            continue
        for item in world.worn_items(actor):
            if item.region not in world.zone:
                continue
            sig = ("soil", actor.id, item.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            item.meters["soiled"] = item.meters.get("soiled", 0.0) + 1.0
            out.append(f"{actor.id}'s spell sent a little glitter and soot onto the {item.label}.")
    return out


def _r_worry(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("soiled", 0.0) < THRESHOLD:
            continue
        if not item.caretaker:
            continue
        sig = ("worry", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0.0) + 1.0
        out.append(f"That made {carer.id} worry about the work ahead.")
    return out


def _r_reconcile(world: World) -> list[str]:
    child = world.entities.get("hero")
    godmother = world.entities.get("godmother")
    if not child or not godmother:
        return []
    if child.memes.get("stubborn", 0.0) < THRESHOLD:
        return []
    if godmother.memes.get("worry", 0.0) < THRESHOLD:
        return []
    sig = ("reconcile",)
    if sig in world.fired:
        return []
    world.fired.add(sig)
    child.memes["hurt"] = 0.0
    child.memes["joy"] = child.memes.get("joy", 0.0) + 1.0
    child.memes["love"] = child.memes.get("love", 0.0) + 1.0
    godmother.memes["warmth"] = godmother.memes.get("warmth", 0.0) + 1.0
    return ["__reconcile__"]


def propagate(world: World, narrate: bool = True) -> list[str]:
    lines: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in (_r_soil, _r_worry, _r_reconcile):
            produced = rule(world)
            if produced:
                changed = True
                lines.extend([x for x in produced if x != "__reconcile__"])
    if narrate:
        for line in lines:
            world.say(line)
    return lines


def prize_at_risk(activity: Activity, prize: Prize) -> bool:
    return prize.region in activity.zone


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str]]:
    out: list[tuple[str, str]] = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIVITIES, act_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(act, prize) and select_gear(act, prize):
                    out.append((place, act_id, prize_id))
    return out


def activity_flavor(activity: Activity) -> str:
    return {
        "magic_cooking": "the galley smelled of cinnamon, salt, and a little moonlight",
        "magic_glow": "the lanterns shone gold against the ship's dark wood",
        "magic_map": "the parchment trembled like it wanted to sing",
    }.get(activity.id, "the air felt full of pirate wonder")


def setting_detail(setting: Setting, activity: Activity) -> str:
    if setting.place == "the galley":
        return "The galley was snug, with pots hanging close and a warm stove in the corner."
    if setting.place == "the deck":
        return "The deck was wide and salty, with ropes, rails, and a stripe of tan canvas overhead."
    return f"{setting.place.capitalize()} looked ready for mischief and songs."


def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.type} pirate with a {hero.label} smile and a taste for grand surprises."
    )


def loves(world: World, hero: Entity, activity: Activity, prize: Entity) -> None:
    hero.memes["delight"] = hero.memes.get("delight", 0.0) + 1.0
    world.say(
        f"{hero.pronoun().capitalize()} loved {activity.gerund}, especially when it led to {prize.phrase}."
    )
    world.say(activity_flavor(activity) + ".")


def gift(world: World, godmother: Entity, hero: Entity, prize: Entity) -> None:
    world.say(
        f"One bright tide-turn, {hero.id}'s {godmother.label} brought {hero.pronoun('object')} {prize.phrase}."
    )


def prize_love(world: World, hero: Entity, prize: Entity) -> None:
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    prize.worn_by = hero.id
    world.say(
        f"{hero.id} loved {hero.pronoun('possessive')} {prize.label} and wore {prize.it()} with great pride."
    )


def arrive(world: World, hero: Entity, godmother: Entity, activity: Activity) -> None:
    world.say(f"One day, {hero.id} and {hero.pronoun('possessive')} {godmother.label} went to {world.setting.place}.")
    world.say(setting_detail(world.setting, activity))


def wants(world: World, hero: Entity, godmother: Entity, activity: Activity) -> None:
    hero.memes["wanting"] = hero.memes.get("wanting", 0.0) + 1.0
    world.say(f"{hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {godmother.label} lifted a careful brow.")


def warn(world: World, godmother: Entity, hero: Entity, activity: Activity, prize: Entity) -> None:
    if not prize_at_risk(activity, prize):
        return
    godmother.memes["worry"] = godmother.memes.get("worry", 0.0) + 1.0
    world.facts["predicted_soil"] = activity.soil
    world.say(
        f'"If you use that magic, your {prize.label} may get {activity.soil}," '
        f"{godmother.id} said. \"Then we'd both have a mess to mend.\""
    )


def defy(world: World, hero: Entity, activity: Activity) -> None:
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 1.0
    world.say(f"{hero.id} puffed up and tried to {activity.rush} anyway.")


def argue(world: World, hero: Entity, godmother: Entity) -> None:
    world.say(f"The little pirate crossed {hero.pronoun('possessive')} arms, and the deck felt too quiet.")
    world.say(f"{godmother.id} did not scold; {godmother.pronoun()} only waited, kind as a lantern in fog.")


def offer_reconciliation(world: World, godmother: Entity, hero: Entity, activity: Activity, prize: Entity, gear: Gear) -> Gear:
    hero.memes["hurt"] = hero.memes.get("hurt", 0.0) + 1.0
    hero.memes["stubborn"] = hero.memes.get("stubborn", 0.0) + 0.0
    world.say(
        f"At last, {godmother.id} smiled and said, "
        f"\"How about we {gear.prep} and do the magic together?\""
    )
    return gear


def accept(world: World, hero: Entity, godmother: Entity, activity: Activity, prize: Entity, gear: Gear) -> None:
    hero.memes["joy"] = hero.memes.get("joy", 0.0) + 1.0
    hero.memes["love"] = hero.memes.get("love", 0.0) + 1.0
    hero.memes["stubborn"] = 0.0
    godmother.memes["warmth"] = godmother.memes.get("warmth", 0.0) + 1.0
    gear_ent = world.add(Entity(
        id=gear.id,
        type="gear",
        label=gear.label,
        owner=hero.id,
        caretaker=godmother.id,
        plural=gear.plural,
    ))
    gear_ent.worn_by = hero.id
    world.say(
        f"{hero.id}'s face softened, and {hero.id} nodded. "
        f"Together they {gear.tail}."
    )
    world.say(
        f"The new spell stayed gentle, {hero.id} got {activity.gerund}, and {prize.label} stayed safe and bright."
    )
    world.say(
        f"By supper-time, the crew was laughing, the tan canvas still shone, and the little pirate and {godmother.id} were friends in full again."
    )


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, hero_name: str, hero_type: str, godmother_name: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id="hero", kind="character", type=hero_type, label=trait, meters={}, memes={}))
    hero.id = hero_name
    world.entities[hero_name] = world.entities.pop("hero")
    hero = world.get(hero_name)

    godmother = world.add(Entity(id="godmother", kind="character", type="godmother", label=godmother_name, meters={}, memes={}))
    prize = world.add(Entity(
        id="prize",
        type=prize_cfg.label,
        label=prize_cfg.label,
        phrase=prize_cfg.phrase,
        owner=hero.id,
        caretaker="godmother",
        region=prize_cfg.region,
        plural=prize_cfg.plural,
    ))
    world.facts.update(hero=hero, godmother=godmother, prize=prize, activity=activity, setting=setting, prize_cfg=prize_cfg)

    introduce(world, hero)
    loves(world, hero, activity, prize)
    gift(world, godmother, hero, prize)
    prize_love(world, hero, prize)

    world.para()
    arrive(world, hero, godmother, activity)
    wants(world, hero, godmother, activity)
    warn(world, godmother, hero, activity, prize)
    defy(world, hero, activity)
    argue(world, hero, godmother)

    world.para()
    gear = select_gear(activity, prize)
    if gear is None:
        gear = next(iter(globals().get("GEARS", globals().get("GEAR", []))))
    offer_reconciliation(world, godmother, hero, activity, prize, gear)
    accept(world, hero, godmother, activity, prize, gear)

    world.facts["gear"] = gear
    world.facts["resolved"] = True
    return world


SETTINGS = {
    "galley": Setting(place="the galley", indoor=True, affords={"magic_cooking", "magic_glow"}),
    "deck": Setting(place="the deck", indoor=False, affords={"magic_glow", "magic_map"}),
}


ACTIVITIES = {
    "magic_cooking": Activity(
        id="magic_cooking",
        verb="stir the gourmet soup with a magic spoon",
        gerund="stirring gourmet soup with a magic spoon",
        rush="dash to the pot and swirl the spoon",
        mess="sparkling",
        soil="speckled with soot",
        zone={"torso"},
        keyword="gourmet",
        tags={"magic", "gourmet"},
    ),
    "magic_glow": Activity(
        id="magic_glow",
        verb="call up a magic glow over the supper",
        gerund="calling up a magic glow over supper",
        rush="raise the charm above the table",
        mess="glitter",
        soil="dusted with glitter",
        zone={"torso"},
        keyword="magic",
        tags={"magic"},
    ),
    "magic_map": Activity(
        id="magic_map",
        verb="trace a magic route on the map",
        gerund="tracing a magic route on the map",
        rush="tap the chart three times",
        mess="glitter",
        soil="dusted with glitter",
        zone={"torso"},
        keyword="magic",
        tags={"magic"},
    ),
}


PRIZES = {
    "tan_cloak": Prize(
        label="tan cloak",
        phrase="a tan cloak with neat silver stitching",
        region="torso",
    ),
    "tan_hat": Prize(
        label="tan hat",
        phrase="a tan hat with a clever feather",
        region="torso",
    ),
    "gourmet_pie": Prize(
        label="gourmet pie",
        phrase="a gourmet pie with a buttery crust",
        region="torso",
    ),
}


GEAR = [
    Gear(
        id="apron",
        label="a clean apron",
        covers={"torso"},
        guards={"sparkling"},
        prep="tie on a clean apron first",
        tail="tied on the apron and stirred the spell together",
    ),
    Gear(
        id="lantern_shield",
        label="a lantern shield",
        covers={"torso"},
        guards={"glitter"},
        prep="set up a lantern shield first",
        tail="set up the lantern shield and raised the charm together",
    ),
    Gear(
        id="salt_cloth",
        label="a salt cloth",
        covers={"torso"},
        guards={"sparkling", "glitter"},
        prep="lay down a salt cloth and work beside it",
        tail="laid down the salt cloth and made the charm together",
        plural=False,
    ),
]


GIRL_NAMES = ["Mira", "Nina", "Luna", "Pearl", "Tia", "Isla", "June"]
BOY_NAMES = ["Rowan", "Finn", "Milo", "Beck", "Tomas", "Jett", "Kai"]
TRAITS = ["brave", "bright", "restless", "cheerful", "daring", "curious"]


KNOWLEDGE = {
    "magic": [
        ("What is magic?", "Magic is a pretend power in stories that can make unusual things happen in a surprising way.")
    ],
    "gourmet": [
        ("What does gourmet mean?", "Gourmet means fancy and extra tasty, often made with special care.")
    ],
    "tan": [
        ("What does tan mean?", "Tan is a light brown color, like sand, leather, or sun-warmed cloth.")
    ],
    "pirate": [
        ("What is a pirate?", "A pirate is a seafaring character from stories who sails ships and looks for treasure or adventure.")
    ],
    "reconciliation": [
        ("What is reconciliation?", "Reconciliation means making peace again after a disagreement so people feel close once more.")
    ],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero, godmother, act, prize = f["hero"], f["godmother"], f["activity"], f["prize_cfg"]
    return [
        'Write a short pirate tale for a young child that includes gourmet food, a godmother, and a tan treasure.',
        f"Tell a gentle pirate story where {hero.id} wants to {act.verb} but {godmother.id} worries about {prize.phrase}, and they reconcile.",
        f'Write a story about a pirate who loves the word "{act.keyword}" and ends with a peaceful shared supper.',
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, godmother, prize, act = f["hero"], f["godmother"], f["prize"], f["activity"]
    qa: list[QAItem] = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a little pirate who loved {act.gerund}.",
        ),
        QAItem(
            question=f"Why did {godmother.id} worry about the {prize.label}?",
            answer=f"{godmother.id} worried because the magic could leave the {prize.label} {f.get('predicted_soil', act.soil)}.",
        ),
        QAItem(
            question=f"What did {hero.id} and {godmother.id} do at the end?",
            answer=f"They reconciled, used {f['gear'].label}, and shared the gourmet result with the crew.",
        ),
        QAItem(
            question=f"What stayed safe by the end of the story?",
            answer=f"The {prize.label} stayed safe and bright, and the tan canvas on the ship was not ruined.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    tags.add("pirate")
    tags.add("reconciliation")
    out: list[QAItem] = []
    for key in ("magic", "gourmet", "tan", "pirate", "reconciliation"):
        if key in tags or key in ("pirate", "reconciliation"):
            out.extend(QAItem(question=q, answer=a) for q, a in KNOWLEDGE[key])
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.region:
            bits.append(f"region={e.region}")
        lines.append(f"  {e.id:10} ({e.type:10}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for (n, *_) in world.fired})}")
    return "\n".join(lines)


CURATED = [
    StoryParams(place="galley", activity="magic_cooking", prize="gourmet_pie", name="Mira", gender="girl", godmother="Aunt Sel", trait="bright"),
    StoryParams(place="deck", activity="magic_glow", prize="tan_cloak", name="Rowan", gender="boy", godmother="Aunt Pearl", trait="daring"),
    StoryParams(place="deck", activity="magic_map", prize="tan_hat", name="Luna", gender="girl", godmother="Aunt Rowe", trait="curious"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if not prize_at_risk(activity, prize):
        return f"(No story: {activity.gerund} does not reach the {prize.label}, so there is no honest worry to reconcile.)"
    return f"(No story: there is no compatible gear that can protect the {prize.label} from {activity.gerund}.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: {_safe_lookup(PRIZES, prize_id).label} is not a typical {gender}'s prize here; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A,P) :- splashes(A,R), worn_on(P,R).
protects(G,A,P) :- prize_at_risk(A,P), mess_of(A,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(A,P) :- protects(_,A,P).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
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
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        for g in sorted(p.genders):
            lines.append(asp.fact("wears", g, pid))
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
    print("MISMATCH between clingo and valid_combos():")
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    if py - cl:
        print("  only in python:", sorted(py - cl))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny pirate tale world with gourmet magic and reconciliation.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--godmother")
    ap.add_argument("--name")
    ap.add_argument("--trait", choices=TRAITS)
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
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, activity, prize_id = rng.choice(list(combos))
    prize = _safe_lookup(PRIZES, prize_id)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    godmother = getattr(args, "godmother", None) or rng.choice(["Aunt Pearl", "Aunt Sel", "Aunt Rowe", "Aunt Mira"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    return StoryParams(place=place, activity=activity, prize=prize_id, name=name, gender=gender, godmother=godmother, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIVITIES, params.activity), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.godmother, params.trait)
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
        import asp
        triples = asp_valid_combos()
        print(f"{len(triples)} compatible (place, activity, prize) combos:\n")
        for place, act, prize in triples:
            print(f"  {place:9} {act:14} {prize}")
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
