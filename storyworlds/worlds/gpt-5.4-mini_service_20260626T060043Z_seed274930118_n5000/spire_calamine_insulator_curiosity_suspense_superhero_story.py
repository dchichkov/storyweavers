#!/usr/bin/env python3
"""
A tiny superhero story world about a curious young hero, a worrying glitch, and
a safe rescue plan. The seed words here are spire, calamine, and insulator.
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


# ---------------------------------------------------------------------------
# World model
# ---------------------------------------------------------------------------

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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    region: str = ""
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    partner: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "woman", "mother", "mom", "heroine"}
        male = {"boy", "man", "father", "dad", "hero"}
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
class Trial:
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


class World:
    def __init__(self, setting: Setting) -> None:
        self.setting = setting
        self.entities: dict[str, Entity] = {}
        self.zone: set[str] = set()
        self.fired: set[tuple] = set()
        self.paragraphs: list[list[str]] = [[]]
        self.facts: dict = {}

    def add(self, e: Entity) -> Entity:
        self.entities[e.id] = e
        return e

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


THRESHOLD = 1.0
MESS_KINDS = {"spark", "slime", "dust"}

# ---------------------------------------------------------------------------
# Registries
# ---------------------------------------------------------------------------
SETTINGS = {
    "rooftop": Setting(place="the rooftop", indoors=False, affords={"glare", "storm"}),
    "lab": Setting(place="the lab", indoors=True, affords={"spark", "glow"}),
    "alley": Setting(place="the alley", indoors=False, affords={"slime", "storm"}),
    "tower": Setting(place="the tower spire", indoors=False, affords={"glow", "storm"}),
}

TRIALS = {
    "spark": Trial(
        id="spark",
        verb="chase the crackling sparks",
        gerund="chasing crackling sparks",
        rush="dash toward the sparking panel",
        mess="spark",
        soil="scorched and jittery",
        zone={"torso", "hands"},
        keyword="spark",
        tags={"spark", "electric"},
    ),
    "slime": Trial(
        id="slime",
        verb="track down the green slime",
        gerund="tracking down green slime",
        rush="spring after the slime trail",
        mess="slime",
        soil="sticky and slimed",
        zone={"feet", "hands"},
        keyword="slime",
        tags={"slime", "messy"},
    ),
    "glow": Trial(
        id="glow",
        verb="inspect the glowing spire",
        gerund="inspecting the glowing spire",
        rush="climb up to the glowing ledge",
        mess="dust",
        soil="dusty",
        zone={"torso", "hands"},
        keyword="spire",
        tags={"spire", "glow"},
    ),
    "storm": Trial(
        id="storm",
        verb="rush into the storm",
        gerund="racing through the storm",
        rush="run out into the storm",
        mess="spark",
        soil="wet and zapped",
        zone={"torso", "hands", "feet"},
        keyword="storm",
        tags={"storm", "rain"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright red cape", type="cape", region="torso"),
    "gloves": Prize(label="gloves", phrase="soft hero gloves", type="gloves", region="hands", plural=True),
    "boots": Prize(label="boots", phrase="shiny boots", type="boots", region="feet", plural=True),
    "mask": Prize(label="mask", phrase="a smooth silver mask", type="mask", region="face"),
}

GEAR = [
    Gear(
        id="insulator",
        label="an insulator suit",
        covers={"torso", "hands"},
        guards={"spark", "dust"},
        prep="put on an insulator suit",
        tail="followed the safe insulated path",
    ),
    Gear(
        id="shieldboots",
        label="shield boots",
        covers={"feet"},
        guards={"slime", "spark"},
        prep="pull on shield boots",
        tail="stomped back in shield boots",
        plural=True,
    ),
    Gear(
        id="calamine",
        label="calamine balm",
        covers={"hands", "face"},
        guards={"slime", "dust"},
        prep="smear on a little calamine balm",
        tail="finished the mission with calamine balm on hand",
    ),
]

HERO_NAMES = ["Nova", "Aria", "Milo", "Tess", "Juno", "Kai", "Ivy", "Ezra"]
TRAITS = ["curious", "brave", "quick", "steady", "clever"]


@dataclass
class StoryParams:
    place: str
    trial: str
    prize: str
    name: str
    gender: str
    trait: str
    partner: str
    seed: Optional[int] = None


# ---------------------------------------------------------------------------
# Reasonableness
# ---------------------------------------------------------------------------
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


def prize_at_risk(trial: Trial, prize: Prize) -> bool:
    return prize.region in trial.zone


def select_gear(trial: Trial, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if trial.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for trial_id in setting.affords:
            trial = _safe_lookup(TRIALS, trial_id)
            for prize_id, prize in PRIZES.items():
                if prize_at_risk(trial, prize) and select_gear(trial, prize):
                    out.append((place, trial_id, prize_id))
    return out


def explain_rejection(trial: Trial, prize: Prize) -> str:
    return (
        f"(No story: {trial.gerund} would not reasonably threaten {prize.label}, "
        f"or no compatible helper gear exists. The superhero compromise must solve "
        f"the actual risk.)"
    )


# ---------------------------------------------------------------------------
# Story actions
# ---------------------------------------------------------------------------
def introduce(world: World, hero: Entity) -> None:
    world.say(
        f"{hero.id} was a little {hero.memes.get('trait', 'curious')} {hero.type} "
        f"who loved solving problems."
    )


def setup(world: World, hero: Entity, partner: Entity, prize: Entity, trial: Trial) -> None:
    world.say(
        f"{hero.id} wore {hero.pronoun('possessive')} {prize.label} like real hero gear, "
        f"while {partner.label} kept watch."
    )


def arrive(world: World, hero: Entity, partner: Entity, trial: Trial) -> None:
    world.say(
        f"One day, {hero.id} and {hero.pronoun('possessive')} {partner.label} went to {world.setting.place}."
    )
    world.say(
        f"{world.setting.place.capitalize()} felt full of suspense, and {hero.id} noticed "
        f"a clue near the {trial.keyword}."
    )


def want_and_warn(world: World, hero: Entity, partner: Entity, prize: Entity, trial: Trial) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    world.say(
        f"{hero.id} wanted to {trial.verb}, but {partner.label} pointed at {hero.pronoun('possessive')} {prize.label}."
    )
    world.say(
        f'"If you go now, your {prize.label} may get {trial.soil}," '
        f'{partner.label} warned.'
    )


def defy(world: World, hero: Entity, trial: Trial) -> None:
    hero.memes["suspense"] = hero.memes.get("suspense", 0) + 1
    world.say(f"{hero.id} gulped and tried to {trial.rush}.")


def apply_trial(world: World, hero: Entity, trial: Trial) -> None:
    hero.meters[trial.mess] = hero.meters.get(trial.mess, 0) + 1
    for item in world.worn_items(hero):
        if item.protective or item.region not in trial.zone:
            continue
        if world.covered(hero, item.region):
            continue
        item.meters[trial.mess] = item.meters.get(trial.mess, 0) + 1
        item.meters["dirty"] = item.meters.get("dirty", 0) + 1
        world.say(f"{hero.pronoun('possessive').capitalize()} {item.label} got {trial.soil}.")


def offer_fix(world: World, hero: Entity, partner: Entity, trial: Trial, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(trial, prize)
    if gear_def is None:
        return None
    gear = world.add(
        Entity(
            id=gear_def.id,
            kind="thing",
            type="gear",
            label=gear_def.label,
            owner=hero.id,
            protective=True,
            covers=set(gear_def.covers),
            plural=gear_def.plural,
        )
    )
    gear.worn_by = hero.id
    if prize_at_risk(trial, prize):
        world.say(
            f"{partner.label} smiled and said, "
            f'"How about we {gear_def.prep} first?"'
        )
        return gear_def
    return None


def resolve(world: World, hero: Entity, partner: Entity, prize: Entity, trial: Trial, gear_def: Gear) -> None:
    hero.memes["curiosity"] = hero.memes.get("curiosity", 0) + 1
    hero.memes["suspense"] = 0
    world.say(
        f"{hero.id} nodded, and the two of them {gear_def.tail}."
    )
    world.say(
        f"At last, {hero.id} could {trial.verb} while {hero.pronoun('possessive')} {prize.label} stayed safe."
    )
    world.say(
        f"The spire still glowed in the distance, but now the hero looked calm and proud."
    )


def tell(setting: Setting, trial: Trial, prize_cfg: Prize, hero_name: str, gender: str, trait: str, partner_type: str) -> World:
    world = World(setting)
    hero = world.add(
        Entity(
            id=hero_name,
            kind="character",
            type=gender,
            label=hero_name,
            meters={},
            memes={"trait": trait, "curiosity": 1.0, "suspense": 0.0},
        )
    )
    partner = world.add(Entity(id="Partner", kind="character", type=partner_type, label="partner"))
    prize = world.add(
        Entity(
            id="prize",
            type=prize_cfg.type,
            label=prize_cfg.label,
            phrase=prize_cfg.phrase,
            owner=hero.id,
            region=prize_cfg.region,
            plural=prize_cfg.plural,
        )
    )
    prize.worn_by = hero.id

    introduce(world, hero)
    setup(world, hero, partner, prize, trial)
    world.para()
    arrive(world, hero, partner, trial)
    want_and_warn(world, hero, partner, prize, trial)
    defy(world, hero, trial)
    apply_trial(world, hero, trial)
    gear_def = offer_fix(world, hero, partner, trial, prize)
    world.para()
    if gear_def:
        resolve(world, hero, partner, prize, trial, gear_def)

    world.facts.update(
        hero=hero,
        partner=partner,
        prize=prize,
        trial=trial,
        gear=gear_def,
        resolved=gear_def is not None,
    )
    return world


# ---------------------------------------------------------------------------
# Q&A
# ---------------------------------------------------------------------------
def generation_prompts(world: World) -> list[str]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    trial = _safe_fact(world, f, "trial")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short superhero story for a young child that includes the word "{trial.keyword}".',
        f"Tell a suspenseful but gentle story where {hero.id} wants to {trial.verb} and keep {hero.pronoun('possessive')} {prize.label} safe.",
        f"Write a curious superhero adventure with a spire, a warning, and a safe helper plan.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero = _safe_fact(world, f, "hero")
    partner = _safe_fact(world, f, "partner")
    prize = _safe_fact(world, f, "prize")
    trial = _safe_fact(world, f, "trial")
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"The story is about {hero.id}, a {hero.memes.get('trait', 'curious')} young hero, and {hero.pronoun('possessive')} {partner.label}."
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {world.setting.place}?",
            answer=f"{hero.id} wanted to {trial.verb}, but the risk was that {hero.pronoun('possessive')} {prize.label} could get {trial.soil}."
        ),
        QAItem(
            question=f"Why did {partner.label} warn {hero.id}?",
            answer=f"{partner.label} warned {hero.id} because the {trial.keyword} trouble could ruin the {prize.label} and make the mission harder."
        ),
    ]
    if f.get("resolved") and f.get("gear"):
        gear = _safe_fact(world, f, "gear")
        qa.append(
            QAItem(
                question=f"How did {gear.label} help?",
                answer=f"{gear.label.capitalize()} helped by protecting the right places, so {hero.id} could finish the mission safely."
            )
        )
        qa.append(
            QAItem(
                question=f"What changed at the end?",
                answer=f"At the end, {hero.id} was calmer and the danger was handled with a safe superhero plan."
            )
        )
    return qa


WORLD_KNOWLEDGE = {
    "spire": [
        QAItem(
            question="What is a spire?",
            answer="A spire is a tall, narrow tower or pointed top on a building.",
        )
    ],
    "calamine": [
        QAItem(
            question="What is calamine used for?",
            answer="Calamine is a soothing lotion or balm that can help calm itchy skin.",
        )
    ],
    "insulator": [
        QAItem(
            question="What does an insulator do?",
            answer="An insulator helps keep electricity, heat, or cold from moving through something quickly.",
        )
    ],
    "curiosity": [
        QAItem(
            question="What is curiosity?",
            answer="Curiosity is the feeling that makes you want to learn more, look closely, and ask questions.",
        )
    ],
    "suspense": [
        QAItem(
            question="What is suspense in a story?",
            answer="Suspense is the tense feeling that makes you wonder what will happen next.",
        )
    ],
}


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["trial"].tags)
    if world.facts.get("gear"):
        tags.add(world.facts["gear"].id)
    tags.update({"curiosity", "suspense", "spire", "calamine", "insulator"})
    out: list[QAItem] = []
    for key in ["spire", "calamine", "insulator", "curiosity", "suspense"]:
        if key in tags:
            out.extend(WORLD_KNOWLEDGE[key])
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts =="]
    for i, p in enumerate(sample.prompts, 1):
        lines.append(f"{i}. {p}")
    lines.append("")
    lines.append("== Story questions ==")
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World-knowledge questions ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def dump_trace(world: World) -> str:
    lines = ["--- world model state ---"]
    for e in list(world.entities.values()):
        parts = []
        if e.meters:
            parts.append(f"meters={e.meters}")
        if e.memes:
            parts.append(f"memes={e.memes}")
        if e.protective:
            parts.append(f"covers={sorted(e.covers)}")
        if e.region:
            parts.append(f"region={e.region}")
        lines.append(f"  {e.id}: {' '.join(parts)}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# ASP twin
# ---------------------------------------------------------------------------
ASP_RULES = r"""
prize_at_risk(T,P) :- splashes(T,R), worn_on(P,R).
protects(G,T,P) :- gear(G), prize_at_risk(T,P), mess_of(T,M), guards(G,M), covers(G,R), worn_on(P,R).
has_fix(T,P) :- protects(_,T,P).
valid(Place,T,P) :- affords(Place,T), prize_at_risk(T,P), has_fix(T,P).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for place, setting in SETTINGS.items():
        lines.append(asp.fact("affords_place", place))
        for trial_id in sorted(setting.affords):
            lines.append(asp.fact("affords", place, trial_id))
    for tid, trial in TRIALS.items():
        lines.append(asp.fact("trial", tid))
        lines.append(asp.fact("mess_of", tid, trial.mess))
        for r in sorted(trial.zone):
            lines.append(asp.fact("splashes", tid, r))
    for pid, prize in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, prize.region))
        if prize.plural:
            lines.append(asp.fact("prize_plural", pid))
        for g in sorted(prize.genders):
            lines.append(asp.fact("wears", g, pid))
    for gear in GEAR:
        lines.append(asp.fact("gear", gear.id))
        for m in sorted(gear.guards):
            lines.append(asp.fact("guards", gear.id, m))
        for c in sorted(gear.covers):
            lines.append(asp.fact("covers", gear.id, c))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid/3."))
    return sorted(set(asp.atoms(model, "valid")))


def asp_verify() -> int:
    py = set(valid_combos())
    ac = set(asp_valid_combos())
    if py == ac:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between ASP and Python:")
    if py - ac:
        print("  only in python:", sorted(py - ac))
    if ac - py:
        print("  only in ASP:", sorted(ac - py))
    return 1


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
CURATED = [
    StoryParams(place="tower", trial="glow", prize="cape", name="Nova", gender="girl", trait="curious", partner="mentor"),
    StoryParams(place="lab", trial="spark", prize="gloves", name="Milo", gender="boy", trait="brave", partner="guard"),
    StoryParams(place="alley", trial="slime", prize="boots", name="Tess", gender="girl", trait="clever", partner="captain"),
]


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A superhero story world with curiosity, suspense, and a safe fix.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--name")
    ap.add_argument("--partner", choices=["mentor", "guard", "captain", "parent"])
    ap.add_argument("--trait", choices=TRAITS)
    ap.add_argument("-n", type=int, default=1)
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--seed", type=int, default=None)
    ap.add_argument("--trace", action="store_true")
    ap.add_argument("--qa", action="store_true")
    ap.add_argument("--json", action="store_true")
    ap.add_argument("--asp", action="store_true")
    ap.add_argument("--verify", action="store_true")
    ap.add_argument("--show-asp", action="store_true")
    return ap


def resolve_params(args: argparse.Namespace, rng: random.Random) -> StoryParams:
    if getattr(args, "trial", None) and getattr(args, "prize", None):
        tr, pr = _safe_lookup(TRIALS, getattr(args, "trial", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (prize_at_risk(tr, pr) and select_gear(tr, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [
        c for c in valid_combos()
        if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
        and (getattr(args, "trial", None) is None or c[1] == getattr(args, "trial", None))
        and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
    ]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, trial, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(HERO_NAMES)
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    partner = getattr(args, "partner", None) or rng.choice(["mentor", "guard", "captain", "parent"])
    return StoryParams(place=place, trial=trial, prize=prize, name=name, gender=gender, trait=trait, partner=partner)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TRIALS, params.trial), _safe_lookup(PRIZES, params.prize), params.name, params.gender, params.trait, params.partner)
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
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible combos:\n")
        for place, trial, prize in combos:
            print(f"  {place:8} {trial:8} {prize:8}")
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
            header = f"### {p.name}: {p.trial} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
