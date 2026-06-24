#!/usr/bin/env python3
"""
storyworlds/worlds/gravel_char_flashback_myth.py
=================================================

A small mythic story world about gravel, char, and a flashback that changes
what the hero chooses to do.

The domain is intentionally tiny:
- a hero once made a promise beside a fire
- the promise is remembered in a flashback
- gravel can grind a fragile ember to ash
- char can either be a ruin or a sign that something sacred was burned clean

The story turns when the hero remembers the old vow and uses that memory to
choose a safer, truer path.
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
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    region: object | None = None
    hero: object | None = None
    hood: object | None = None
    parent: object | None = None
    relic: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "queen", "goddess"}
        male = {"boy", "father", "man", "king", "god"}
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
    peril: str
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
class Relic:
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
class Ward:
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
        import copy
        clone = World(self.setting)
        clone.entities = copy.deepcopy(self.entities)
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        clone.paragraphs = [[]]
        clone.facts = dict(self.facts)
        return clone


def _r_grind(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("travel", 0) < THRESHOLD:
            continue
        for relic in list(world.entities.values()):
            if relic.worn_by != actor.id:
                continue
            if relic.region not in world.zone:
                continue
            if world.covered(actor, relic.region):
                continue
            sig = ("grind", actor.id, relic.id)
            if sig in world.fired:
                continue
            world.fired.add(sig)
            relic.meters["ruin"] = relic.meters.get("ruin", 0) + 1
            relic.meters["char"] = relic.meters.get("char", 0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {relic.label} was ground with grit and char.")
    return out


def _r_weight(world: World) -> list[str]:
    out: list[str] = []
    for relic in list(world.entities.values()):
        if relic.meters.get("ruin", 0) < THRESHOLD or not relic.caretaker:
            continue
        sig = ("weight", relic.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(relic.caretaker)
        carer.memes["worry"] = carer.memes.get("worry", 0) + 1
        out.append(f"That would weigh on {carer.label}'s heart.")
    return out


def _r_flashback(world: World) -> list[str]:
    for actor in world.characters():
        if actor.memes.get("memory", 0) < THRESHOLD:
            continue
        sig = ("flashback", actor.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        actor.memes["resolve"] = actor.memes.get("resolve", 0) + 1
        return ["__flashback__"]
    return []


RULES = [
    _r_flashback,
    _r_grind,
    _r_weight,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            out = rule(world)
            if out:
                changed = True
                produced.extend(s for s in out if s != "__flashback__")
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def trial_risk(trial: Trial, relic: Relic) -> bool:
    return relic.region in trial.zone


def select_ward(trial: Trial, relic: Relic) -> Optional[Ward]:
    for ward in WARDS:
        if trial.keyword in ward.guards and relic.region in ward.covers:
            return ward
    return None


def predict_risk(world: World, actor: Entity, trial: Trial, relic_id: str) -> dict:
    sim = world.copy()
    _do_trial(sim, sim.get(actor.id), trial, narrate=False)
    relic = sim.entities.get(relic_id)
    return {
        "ruined": bool(relic and relic.meters.get("ruin", 0) >= THRESHOLD),
        "worry": sum(e.memes.get("worry", 0) for e in sim.characters()),
    }


def _do_trial(world: World, actor: Entity, trial: Trial, narrate: bool = True) -> None:
    if trial.id not in world.setting.affords:
        return
    world.zone = set(trial.zone)
    actor.meters["travel"] = actor.meters.get("travel", 0) + 1
    propagate(world, narrate=narrate)


def tell(setting: Setting, trial: Trial, relic_cfg: Relic,
         name: str = "Ari", gender: str = "girl",
         parent_type: str = "mother", trait: str = "wise") -> World:
    world = World(setting)
    hero = world.add(Entity(id=name, kind="character", type=gender))
    parent = world.add(Entity(id="parent", kind="character", type=parent_type, label="the elder"))
    relic = world.add(Entity(
        id="relic", type=relic_cfg.type, label=relic_cfg.label, phrase=relic_cfg.phrase,
        caretaker=parent.id, owner=hero.id, region=relic_cfg.region, plural=relic_cfg.plural
    ))

    hero.memes["love"] = 1
    hero.memes["memory"] = 1

    world.say(f"{hero.id} was a {trait} child who loved old paths and old promises.")
    world.say(f"{hero.pronoun().capitalize()} kept {hero.pronoun('possessive')} {relic.label} close, because it had once been given with honor.")
    world.say(f"At {world.setting.place}, the stones lay rough and gray, and the road waited like a test.")

    world.para()
    world.say(f"{hero.id} wanted to {trial.verb}, but the gravel there could mar what {hero.pronoun('possessive')} {relic.label} held.")
    pred = predict_risk(world, hero, trial, relic.id)
    if pred["ruined"]:
        world.say(f'"If you go on like that, your {relic.label} will be {trial.peril}," {parent.label_word if hasattr(parent, "label_word") else "the elder"} said.')

    hero.memes["desire"] = 1
    _do_trial(world, hero, trial, narrate=True)

    world.para()
    if pred["ruined"]:
        hero.memes["memory"] += 1
        world.say(f"Then a flashback came like firelight: the same road, the same gravel, and a younger voice swearing not to let vanity break a sacred thing.")
        world.say(f"{hero.id} remembered the vow and stopped rushing.")
        ward = select_ward(trial, relic)
        if ward is not None:
            hood = world.add(Entity(
                id=ward.id, type="ward", label=ward.label, owner=hero.id,
                protective=True, covers=set(ward.covers), plural=ward.plural
            ))
            hood.worn_by = hero.id
            world.say(f"{hero.pronoun('possessive').capitalize()} {ward.label} was tied on before the next step.")
            world.zone = set()
            hero.meters["travel"] += 1
            world.say(f"They took the safer way, and {hero.id} walked on without grinding the holy thing to char.")
            world.say(f"In the end, {relic.label} stayed whole, and the road kept its silence.")
            world.facts["ward"] = ward
            world.facts["resolved"] = True
        else:
            world.say("But there was no true ward to help, so the tale stayed broken.")
            world.facts["ward"] = None
            world.facts["resolved"] = False
    else:
        world.say(f"{hero.id} crossed the stones lightly, and nothing sacred was harmed.")
        world.say(f"{relic.label} stayed bright, with only a little dust on its edge.")
        world.facts["ward"] = None
        world.facts["resolved"] = True

    world.facts.update(hero=hero, parent=parent, relic=relic, trial=trial, setting=setting)
    return world


SETTINGS = {
    "shrine_road": Setting(place="the shrine road", affords={"cross_gravel"}),
    "river_path": Setting(place="the river path", affords={"cross_gravel"}),
    "hill_gate": Setting(place="the hill gate", affords={"cross_gravel"}),
}

TRIALS = {
    "cross_gravel": Trial(
        id="cross_gravel",
        verb="cross the gravel road",
        gerund="crossing the gravel road",
        rush="stride across the stones",
        peril="charred and battered",
        zone={"feet", "legs"},
        keyword="gravel",
        tags={"gravel", "char"},
    ),
}

RELICS = {
    "ember_crown": Relic(
        label="ember crown",
        phrase="a small ember crown",
        type="crown",
        region="head",
    ),
    "char_cloak": Relic(
        label="char cloak",
        phrase="a dark cloak of char cloth",
        type="cloak",
        region="torso",
    ),
    "char_lamp": Relic(
        label="char lamp",
        phrase="a lamp that held a little charred coal",
        type="lamp",
        region="hands",
    ),
}

WARDS = [
    Ward(id="sandals", label="soft sandals", covers={"feet"}, guards={"gravel"}, prep="slip on soft sandals", tail="slid into the soft sandals"),
    Ward(id="cloakwrap", label="a woven cloak", covers={"torso"}, guards={"gravel"}, prep="wrap a woven cloak around the shoulders", tail="wrapped themselves in the woven cloak"),
]

GENDERS = ["girl", "boy"]
NAMES = ["Ari", "Mira", "Tala", "Jon", "Ivo", "Kora"]
TRAITS = ["wise", "quiet", "brave", "patient", "gentle"]


@dataclass
class StoryParams:
    place: str
    trial: str
    relic: str
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


def valid_combos() -> list[tuple[str, str, str]]:
    out = []
    for place, setting in SETTINGS.items():
        for trial_id in setting.affords:
            trial = _safe_lookup(TRIALS, trial_id)
            for relic_id, relic in RELICS.items():
                if trial_risk(trial, relic) and select_ward(trial, relic):
                    out.append((place, trial_id, relic_id))
    return out


KNOWLEDGE = {
    "gravel": [("What is gravel?", "Gravel is made of tiny stones. It crunches under your feet when you walk on it.")],
    "char": [("What is char?", "Char is the black, burned part left after fire touches wood or cloth.")],
    "flashback": [("What is a flashback?", "A flashback is a memory scene that shows something from before, as if it briefly returned to the mind.")],
    "sandals": [("What are sandals for?", "Sandals are light shoes that help protect your feet while keeping them cool.")],
    "cloak": [("What is a cloak?", "A cloak is a loose outer garment you wear over your clothes to cover and warm you.")],
}


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    return [
        f'Write a short myth for a young child that includes the words "gravel" and "char".',
        f"Tell a gentle myth about {f['hero'].id} who wants to {f['trial'].verb} at {f['setting'].place} but remembers an older vow.",
        f"Write a story in a mythic style where a flashback helps a child choose a safer way before {f['relic'].label} is ruined.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, parent, relic, trial = f["hero"], f["parent"], f["relic"], f["trial"]
    qa = [
        QAItem(
            question=f"Who is the story about?",
            answer=f"It is about {hero.id}, a {hero.type} who carries {hero.pronoun('possessive')} {relic.label} and learns from an old memory.",
        ),
        QAItem(
            question=f"What did {hero.id} want to do at {f['setting'].place}?",
            answer=f"{hero.id} wanted to {trial.verb}. The road had gravel, so the choice mattered.",
        ),
        QAItem(
            question=f"Why was the old road hard for {hero.id}?",
            answer=f"The gravel could rub the {relic.label} and leave it charred and battered.",
        ),
    ]
    if f.get("resolved"):
        qa.append(QAItem(
            question=f"What helped {hero.id} choose the safer way?",
            answer=f"A flashback to an older promise helped {hero.id} remember to slow down and use protection before crossing the stones.",
        ))
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    tags = set(world.facts["trial"].tags)
    if world.facts.get("ward"):
        tags.add(world.facts["ward"].id)
    out: list[QAItem] = []
    for tag, items in KNOWLEDGE.items():
        if tag in tags or tag == "flashback":
            out.extend(QAItem(question=q, answer=a) for q, a in items)
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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:10} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(trial: Trial, relic: Relic) -> str:
    noun = relic.label if relic.plural else f"a {relic.label}"
    if not trial_risk(trial, relic):
        return f"(No story: {trial.gerund} does not threaten {noun}, so there is no honest mythic warning.)"
    return f"(No story: nothing in the ward set truly protects {noun} from {trial.gerund}.)"


def explain_gender(relic_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(RELICS, relic_id).genders))
    return f"(No story: {_safe_lookup(RELICS, relic_id).label} is not a typical {gender}'s relic here; try --gender {ok}.)"


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A tiny mythic world of gravel, char, and flashback.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--trial", choices=TRIALS)
    ap.add_argument("--relic", choices=RELICS)
    ap.add_argument("--gender", choices=GENDERS)
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
    if getattr(args, "trial", None) and getattr(args, "relic", None):
        tr, re = _safe_lookup(TRIALS, getattr(args, "trial", None)), _safe_lookup(RELICS, getattr(args, "relic", None))
        if not (trial_risk(tr, re) and select_ward(tr, re)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "relic", None) and getattr(args, "gender", None) not in _safe_lookup(RELICS, getattr(args, "relic", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "trial", None) is None or c[1] == getattr(args, "trial", None))
              and (getattr(args, "relic", None) is None or c[2] == getattr(args, "relic", None))
              and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in RELICS[c[2]].genders)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    place, trial, relic = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(GENDERS)
    if relic not in RELICS or gender not in _safe_lookup(RELICS, relic).genders:
        gender = rng.choice(sorted(_safe_lookup(RELICS, relic).genders))
    name = getattr(args, "name", None) or rng.choice(NAMES)
    parent = getattr(args, "parent", None) or rng.choice(["mother", "father"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, trial=trial, relic=relic, name=name, gender=gender, parent=parent, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(TRIALS, params.trial), _safe_lookup(RELICS, params.relic),
                 params.name, params.gender, params.parent, params.trait)
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
trial_risk(T, R) :- zone(T, Z), relic_region(R, Z).
ward_ok(W, T, R) :- ward(W), trial_risk(T, R), guards(W, K), trial_tag(T, K), covers(W, Z), relic_region(R, Z).
valid_story(P, T, R, G) :- place(P), trial(T), relic(R), trial_risk(T, R), ward_ok(_, T, R), gender_ok(R, G), affords(P, T).
"""


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("place", pid))
        for t in sorted(s.affords):
            lines.append(asp.fact("affords", pid, t))
    for tid, t in TRIALS.items():
        lines.append(asp.fact("trial", tid))
        for z in sorted(t.zone):
            lines.append(asp.fact("zone", tid, z))
        for tag in sorted(t.tags):
            lines.append(asp.fact("trial_tag", tid, tag))
    for rid, r in RELICS.items():
        lines.append(asp.fact("relic", rid))
        lines.append(asp.fact("relic_region", rid, r.region))
        for g in sorted(r.genders):
            lines.append(asp.fact("gender_ok", rid, g))
    for w in WARDS:
        lines.append(asp.fact("ward", w.id))
        for c in sorted(w.covers):
            lines.append(asp.fact("covers", w.id, c))
        for g in sorted(w.guards):
            lines.append(asp.fact("guards", w.id, g))
    return "\n".join(lines)


def asp_program(show: str) -> str:
    return f"{asp_facts()}\n{ASP_RULES}\n{show}\n"


def valid_story_triples() -> list[tuple]:
    return valid_combos()


def asp_valid_combos() -> list[tuple]:
    import asp
    model = asp.one_model(asp_program("#show valid_story/4."))
    return sorted(set(asp.atoms(model, "valid_story")))


def asp_verify() -> int:
    import asp
    py = set(valid_story_triples())
    model = asp.one_model(asp_program("#show valid_story/4."))
    cl = set(asp.atoms(model, "valid_story"))
    if py == cl:
        print(f"OK: clingo gate matches valid_combos() ({len(py)} combos).")
        return 0
    print("MISMATCH between clingo and valid_combos():")
    if py - cl:
        print("  only in python:", sorted(py - cl))
    if cl - py:
        print("  only in clingo:", sorted(cl - py))
    return 1


CURATED = [
    StoryParams(place="shrine_road", trial="cross_gravel", relic="ember_crown", name="Ari", gender="girl", parent="mother", trait="wise"),
    StoryParams(place="river_path", trial="cross_gravel", relic="char_cloak", name="Jon", gender="boy", parent="father", trait="patient"),
    StoryParams(place="hill_gate", trial="cross_gravel", relic="char_lamp", name="Kora", gender="girl", parent="mother", trait="brave"),
]


def main() -> None:
    args = build_parser().parse_args()
    if getattr(args, "show_asp", None):
        print(asp_program("#show valid_story/4."))
        return
    if getattr(args, "verify", None):
        sys.exit(asp_verify())
    if getattr(args, "asp", None):
        combos = asp_valid_combos()
        print(f"{len(combos)} compatible stories:")
        for c in combos:
            print(" ", c)
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
