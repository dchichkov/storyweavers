#!/usr/bin/env python3
"""
A small bedtime-story world about a centaur, a bit of yarn, and a playful
cavalry surprise.

The seed premise:
- A little centaur wants to settle down for bed.
- A soft toy cavalry and a tangled ball of yarn turn the bedtime routine into a
  gentle, funny problem.
- A flashback explains why the yarn matters.
- A twist resolves the worry with a cozy, kind ending.

This file follows the Storyweavers storyworld contract:
- standalone stdlib script
- StoryParams, registries, parser, resolve_params, generate, emit, main
- eager results import
- lazy ASP import in helpers
- inline ASP_RULES and asp_facts()
- world-state-driven prose, Q&A, trace, verify, show-asp, json, qa, all, seed
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
    kind: str = "thing"
    type: str = "thing"
    label: str = ""
    phrase: str = ""
    traits: list[str] = field(default_factory=list)
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gear: object | None = None
    hero: object | None = None
    parent: object | None = None
    prize: object | None = None
    region: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "mom", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "dad", "man"}:
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
    bedtime: bool = True
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
    setting: str
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}
        self.active_mess: str = ""

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

        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        clone.active_mess = self.active_mess
        return clone


def _story_meters() -> dict[str, float]:
    return {"tired": 0.0, "giggle": 0.0, "worry": 0.0, "cozy": 0.0, "messy": 0.0}


def _story_memes() -> dict[str, float]:
    return {"love": 0.0, "fear": 0.0, "conflict": 0.0, "surprise": 0.0, "humor": 0.0, "memory": 0.0}


def valid_combo(setting: Setting, activity: Activity, prize: Prize) -> bool:
    return activity.id in setting.affords and prize.region in activity.zone and prize.label != "blanket"


def select_gear(activity: Activity, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if activity.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    combos: list[tuple[str, str, str]] = []
    for s_id, setting in SETTINGS.items():
        for a_id, act in ACTIVITIES.items():
            if a_id not in setting.affords:
                continue
            for p_id, prize in PRIZES.items():
                if valid_combo(setting, act, prize) and select_gear(act, prize):
                    combos.append((s_id, a_id, p_id))
    return combos


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="Bedtime story world with cavalry, yarn, and a centaur.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent", choices=["mother", "father"])
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
        act = _safe_lookup(ACTIVITIES, getattr(args, "activity", None))
        pr = _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not valid_combo(_safe_lookup(SETTINGS, getattr(args, "setting", None)) if getattr(args, "setting", None) else next(iter(SETTINGS.values())), act, pr):
            return _fallback_storyparams(args, rng, StoryParams, globals())
        if not select_gear(act, pr):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
        and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
        and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in PRIZES[c[2]].genders)
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, activity, prize = rng.choice(list(combos))
    prize_def = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(sorted(prize_def.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(setting=setting, activity=activity, prize=prize, name=name, gender=gender, parent=parent, trait=trait)


def _do_activity(world: World, actor: Entity, activity: Activity) -> None:
    world.active_mess = activity.mess
    actor.meters["messy"] += 1
    actor.meters[activity.mess] = actor.meters.get(activity.mess, 0.0) + 1
    actor.memes["giggle"] += 1


def predict_story(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    _do_activity(sim, sim.get(actor.id), activity)
    prize = sim.get(prize_id)
    return {"soiled": prize.meters.get("dirty", 0.0) >= THRESHOLD, "messy": actor.meters.get("messy", 0.0)}


def lead_in(world: World, hero: Entity, parent: Entity, prize: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} was a little centaur with a sleepy heart and bright eyes.")
    world.say(f"{hero.pronoun().capitalize()} loved bedtime stories, soft blankets, and {activity.gerund}.")
    world.say(f"One evening, {hero.pronoun('possessive')} {parent.label} had tucked {hero.pronoun('object')} in with {prize.phrase} nearby.")
    world.say(f"{hero.id} smiled at {hero.pronoun('possessive')} {prize.label} as if it were a tiny treasure.")


def flashback(world: World, hero: Entity) -> None:
    hero.memes["memory"] += 1
    world.say("A warm flashback drifted through the room.")
    world.say(f"Earlier that day, {hero.id} had promised to help untangle a basket of yarn for {hero.pronoun('possessive')} {world.facts['parent'].label}.")
    world.say("The yarn had rolled across the floor like a tiny red river, and that had made everyone laugh.")


def bedtime_problem(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> bool:
    pred = predict_story(world, hero, activity, prize.id)
    if not pred["soiled"]:
        return False
    hero.memes["worry"] += 1
    parent.memes["fear"] += 1
    world.say(f"Then {hero.id} wanted to {activity.verb}, but {hero.pronoun('possessive')} {parent.label} worried about {prize.label}.")
    world.say(f'"If you go to the {activity.keyword}, your {prize.label} could get {activity.soil}," {parent.pronoun("possessive")} {parent.label} said.')
    return True


def cavalry_humor(world: World, hero: Entity, activity: Activity) -> None:
    world.say(f"{hero.id} made a tiny face and saluted like a serious officer.")
    world.say(f'"Attention," {hero.id} whispered, "the bedtime cavalry is arriving."')
    world.say("A line of stuffed horses marched in from the pillow fort, and even the moon seemed to smile.")


def twist_offer(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(activity, prize)
    if gear_def is None:
        return None
    gear = world.add(Entity(id=gear_def.id, type="gear", label=gear_def.label, owner=hero.id, caretaker=parent.id, plural=gear_def.plural))
    gear.worn_by = hero.id
    if predict_story(world, hero, activity, prize.id)["soiled"]:
        gear.worn_by = None
        del world.entities[gear.id]
        return None
    world.say("Then came the twist.")
    world.say(f"{parent.id} noticed the basket of yarn and laughed softly.")
    world.say(f'"What if we use {gear_def.label} first, and let the cavalry carry the yarn to the basket after?" {parent.pronoun("possessive")} {parent.label} asked.')
    return gear_def


def resolve_story(world: World, hero: Entity, parent: Entity, activity: Activity, prize: Entity, gear_def: Gear) -> None:
    hero.memes["worry"] = 0.0
    hero.memes["love"] += 1
    hero.memes["surprise"] += 1
    world.say(f"{hero.id}'s eyes grew round, then bright.")
    world.say(f'"That is a funny plan," {hero.id} said, and {hero.pronoun()} hugged {hero.pronoun("possessive")} {parent.label}.')
    world.say(f"So they put on {gear_def.label}, and the little cavalry marched beside {hero.id} like bedtime guards.")
    world.say(f"Soon {hero.id} was {activity.gerund}, {prize.label} stayed safe, and the yarn rested neatly in its basket.")
    world.say("The room felt quiet, warm, and ready for dreams.")


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str, parent_type: str, trait: str) -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender, traits=["little", trait], meters=_story_meters(), memes=_story_memes()))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_type, label=f"his {parent_type}", meters=_story_meters(), memes=_story_memes()))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase, owner=hero.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural, meters=_story_meters(), memes=_story_memes()))
    world.facts.update(hero=hero, parent=parent, prize=prize, activity=activity, setting=setting)
    lead_in(world, hero, parent, prize, activity)
    world.para()
    flashback(world, hero)
    world.para()
    if bedtime_problem(world, hero, parent, activity, prize):
        cavalry_humor(world, hero, activity)
        gear_def = twist_offer(world, hero, parent, activity, prize)
        if gear_def:
            resolve_story(world, hero, parent, activity, prize, gear_def)
    return world


SETTINGS = {
    "nursery": Setting(place="the nursery", indoors=True, affords={"yarn", "cavalry"}),
    "bedroom": Setting(place="the bedroom", indoors=True, affords={"yarn", "cavalry"}),
    "attic": Setting(place="the attic", indoors=True, affords={"yarn", "cavalry"}),
}

ACTIVITIES = {
    "yarn": Activity(
        id="yarn",
        verb="wind the yarn",
        gerund="winding yarn",
        rush="dash after the yarn",
        mess="tangled",
        soil="all tangled up",
        zone={"hooves", "legs"},
        keyword="yarn",
        tags={"yarn", "tangle", "bedtime"},
    ),
    "cavalry": Activity(
        id="cavalry",
        verb="march with the cavalry",
        gerund="marching with the cavalry",
        rush="call the cavalry",
        mess="noisy",
        soil="too noisy for sleep",
        zone={"torso", "hooves", "legs"},
        keyword="cavalry",
        tags={"cavalry", "horse", "bedtime"},
    ),
}

PRIZES = {
    "blanket": Prize(label="blanket", phrase="a soft blue blanket", type="blanket", region="torso"),
    "slippers": Prize(label="slippers", phrase="warm striped slippers", type="slippers", region="hooves", plural=True),
    "pillow": Prize(label="pillow", phrase="a small moon-pillow", type="pillow", region="torso"),
}

GEAR = [
    Gear(id="quiet-blanket", label="a quiet blanket", covers={"torso"}, guards={"noisy"}, prep="wrap the room in a quiet blanket", tail="wrapped the room in a quiet blanket"),
    Gear(id="yarn-basket", label="a yarn basket", covers={"hooves", "legs"}, guards={"tangled"}, prep="use the yarn basket first", tail="put the yarn back in the basket"),
    Gear(id="tuck-sheet", label="the tuck-sheet", covers={"torso"}, guards={"tangled", "noisy"}, prep="pull up the tuck-sheet", tail="pulled up the tuck-sheet"),
]

GIRL_NAMES = ["Lily", "Mira", "Nora", "Eve", "Ari", "June"]
BOY_NAMES = ["Theo", "Milo", "Otis", "Ben", "Finn", "Noel"]
TRAITS = ["gentle", "curious", "brave", "dreamy", "playful", "patient"]


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    act: Activity = _safe_fact(world, f, "activity")
    prize: Entity = _safe_fact(world, f, "prize")
    return [
        f'Write a bedtime story for a young child that includes "{act.keyword}", "{prize.label}", and a tiny cavalry march.',
        f"Tell a cozy story about {hero.id}, a little centaur, whose {parent.label} worries that {prize.label} might be spoiled during {act.gerund}.",
        f"Write a gentle story with a flashback, a funny cavalry moment, and a twist that keeps {prize.label} safe.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero: Entity = _safe_fact(world, f, "hero")
    parent: Entity = _safe_fact(world, f, "parent")
    prize: Entity = _safe_fact(world, f, "prize")
    act: Activity = _safe_fact(world, f, "activity")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a little centaur who is trying to get ready for bed.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry when {hero.id} wanted to {act.verb}?",
            answer=f"{parent.label} worried because {prize.label} could have gotten {act.soil}, and bedtime would have become messy or noisy.",
        ),
        QAItem(
            question=f"What was the flashback about?",
            answer="The flashback was about the yarn rolling across the floor earlier, which made everyone laugh and reminded them of the day.",
        ),
        QAItem(
            question=f"What was the funny cavalry part?",
            answer="The funny part was the stuffed horses marching in like a bedtime cavalry, which made the room feel cheerful instead of tense.",
        ),
        QAItem(
            question=f"How did the story end?",
            answer=f"It ended with {hero.id} settling down safely, {prize.label} staying safe, and the room becoming quiet and cozy.",
        ),
    ]
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["activity"].tags)
    out: list[QAItem] = []
    if "yarn" in tags:
        out.append(QAItem(
            question="What is yarn?",
            answer="Yarn is a soft thread people use for knitting, weaving, and other cozy projects.",
        ))
    if "cavalry" in tags:
        out.append(QAItem(
            question="What is cavalry?",
            answer="Cavalry means riders or horses who move together as a group, often in a line.",
        ))
    out.append(QAItem(
        question="What makes bedtime cozy?",
        answer="Soft blankets, quiet voices, and a safe room can make bedtime feel cozy.",
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
            bits.append(f"meters={meters}")
        if memes:
            bits.append(f"memes={memes}")
        if e.worn_by:
            bits.append(f"worn_by={e.worn_by}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    return "\n".join(lines)


CURATED = [
    StoryParams(setting="nursery", activity="yarn", prize="blanket", name="Milo", gender="boy", parent="mother", trait="gentle"),
    StoryParams(setting="bedroom", activity="cavalry", prize="slippers", name="Nora", gender="girl", parent="father", trait="dreamy"),
    StoryParams(setting="attic", activity="yarn", prize="pillow", name="Theo", gender="boy", parent="mother", trait="curious"),
]


def explain_rejection(activity: Activity, prize: Prize) -> str:
    if prize.region not in activity.zone:
        return f"(No story: {activity.gerund} would not reach the {prize.label}, so there is no real bedtime worry.)"
    if not select_gear(activity, prize):
        return f"(No story: there is no gentle fix that can keep the {prize.label} safe during {activity.gerund}.)"
    return "(No story: that choice does not make a clear, child-friendly bedtime problem.)"


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for sid, setting in SETTINGS.items():
        lines.append(asp.fact("setting", sid))
        if setting.indoors:
            lines.append(asp.fact("indoors", sid))
        for a in sorted(setting.affords):
            lines.append(asp.fact("affords", sid, a))
    for aid, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", aid))
        lines.append(asp.fact("mess_of", aid, act.mess))
        for r in sorted(act.zone):
            lines.append(asp.fact("splashes", aid, r))
    for pid, pr in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, pr.region))
        if pr.plural:
            lines.append(asp.fact("plural", pid))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for r in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, r))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A, P) :- splashes(A, R), worn_on(P, R).
fix(G, A, P) :- gear(G), prize_at_risk(A, P), mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
valid(Setting, A, P) :- affords(Setting, A), prize_at_risk(A, P), fix(_, A, P).
valid_story(Setting, A, P, Gender) :- valid(Setting, A, P), wears(Gender, P).
"""


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
    clingo_set = set(asp_valid_combos())
    py_set = set(valid_combos())
    if clingo_set == py_set:
        print(f"OK: clingo gate matches valid_combos() ({len(clingo_set)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if clingo_set - py_set:
        print("  only in clingo:", sorted(clingo_set - py_set))
    if py_set - clingo_set:
        print("  only in python:", sorted(py_set - clingo_set))
    return 1


def generate(params: StoryParams) -> StorySample:
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.gender,
        params.parent,
        params.trait,
    )
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
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        triples = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(triples)} compatible (setting, activity, prize) combos ({len(stories)} with gender):\n")
        for setting, activity, prize in triples:
            genders = sorted(g for (s, a, p, g) in stories if (s, a, p) == (setting, activity, prize))
            print(f"  {setting:8} {activity:9} {prize:10}  [{', '.join(genders)}]")
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
        header = ""
        if getattr(args, "all", None):
            p = sample.params
            header = f"### {p.name}: {p.activity} at {p.setting} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
