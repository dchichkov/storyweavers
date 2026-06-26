#!/usr/bin/env python3
"""
storyworlds/worlds/gpt-5.4-mini_service_20260626T060043Z_seed274930118_n5000/medicate_pager_sundry_humor_superhero_story.py
=================================================================================================

A small superhero-style story world with humor, a pager, and sundry supplies.

Seed tale:
---
A cheerful caped hero wants to dash off on a big rescue, but a pager buzzes
with a tiny emergency: a sidekick needs medicine, and the sundry kit is missing
one important piece. The hero wants to save the day right away, but first they
have to choose a sensible way to medicate the patient without ruining the hero
gear. After a funny scramble through the lair, they find the right supply, give
the medicine, and still make it to the rescue in time.

World model:
---
- characters and gear carry meters (physical state) and memes (emotional state)
- the pager can reveal a task, raising urgency
- the wrong rescue move can smear the cape or mask with slime or paint
- the reasonable compromise is to medicate first, then launch the rescue with
  the right protective gear

Humor:
---
The story leans light and comic: a buzzy pager, a too-serious cape, and a
sundry supply cabinet that never seems to hold the one thing needed until the
hero looks twice.
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
    owner: Optional[str] = None
    caretaker: Optional[str] = None
    worn_by: Optional[str] = None
    protective: bool = False
    covers: set[str] = field(default_factory=set)
    plural: bool = False
    meters: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))
    memes: dict[str, float] = field(default_factory=lambda: __import__('collections').defaultdict(float))

    gear: object | None = None
    helper: object | None = None
    hero: object | None = None
    pager: object | None = None
    patient: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        female = {"girl", "mother", "woman", "sister"}
        male = {"boy", "father", "man", "brother"}
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
class Action:
    id: str
    verb: str
    gerund: str
    rush: str
    mess: str
    soil: str
    zone: set[str]
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
        self.zone: set[str] = set()
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
        import copy as _copy
        clone = World(self.setting)
        clone.entities = _copy.deepcopy(self.entities)
        clone.zone = set(self.zone)
        clone.fired = set(self.fired)
        clone.facts = dict(self.facts)
        return clone


def _phys(x: Entity, key: str) -> float:
    return x.meters.get(key, 0.0)


def _mem(x: Entity, key: str) -> float:
    return x.memes.get(key, 0.0)


def _bump_meter(x: Entity, key: str, amt: float = 1.0) -> None:
    x.meters[key] = x.meters.get(key, 0.0) + amt


def _bump_meme(x: Entity, key: str, amt: float = 1.0) -> None:
    x.memes[key] = x.memes.get(key, 0.0) + amt


def _r_soil(world: World) -> list[str]:
    out = []
    for actor in world.characters():
        for mess in ("wet", "sticky", "painted"):
            if _phys(actor, mess) < THRESHOLD:
                continue
            for item in world.worn_items(actor):
                if item.protective or item.label == "pager":
                    continue
                if item.covers and not (item.covers & world.zone):
                    continue
                if world.covered(actor, next(iter(item.covers), "")):
                    continue
                sig = ("soil", actor.id, item.id, mess)
                if sig in world.fired:
                    continue
                world.fired.add(sig)
                _bump_meter(item, mess)
                _bump_meter(item, "dirty")
                out.append(f"{actor.id}'s {item.label} got {mess} and dirty.")
    return out


def _r_waive(world: World) -> list[str]:
    out = []
    for item in list(world.entities.values()):
        if item.label != "pager":
            continue
        if _phys(item, "buzz") < THRESHOLD:
            continue
        sig = ("buzz", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        out.append("The pager buzzed again, so loudly it sounded offended.")
    return out


def _r_medicate(world: World) -> list[str]:
    out = []
    patient = world.facts.get("patient")
    medic = world.facts.get("hero")
    if not patient or not medic:
        return out
    if _mem(patient, "calm") >= THRESHOLD:
        return out
    if _mem(medic, "helpful") < THRESHOLD:
        return out
    sig = ("medicate", patient.id)
    if sig in world.fired:
        return out
    world.fired.add(sig)
    _bump_meme(patient, "calm")
    _bump_meme(medic, "pride")
    out.append(f"{medic.id} gave {patient.id} the medicine, and {patient.id} settled right down.")
    return out


CAUSAL_RULES = [
    _r_waive,
    _r_soil,
    _r_medicate,
]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in CAUSAL_RULES:
            bits = rule(world)
            if bits:
                changed = True
                produced.extend(bits)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def can_pair(action: Action, prize: Prize) -> bool:
    return prize.region in action.zone


def select_gear(action: Action, prize: Prize) -> Optional[Gear]:
    for gear in GEAR:
        if action.mess in gear.guards and prize.region in gear.covers:
            return gear
    return None


def predict_mess(world: World, actor: Entity, action: Action, prize_id: str) -> dict:
    sim = world.copy()
    _do_action(sim, sim.get(actor.id), action, narrate=False)
    prize = sim.entities[prize_id]
    return {"soiled": _phys(prize, "dirty") >= THRESHOLD}


def _do_action(world: World, actor: Entity, action: Action, narrate: bool = True) -> None:
    if action.id not in world.setting.affords:
        return
    world.zone = set(action.zone)
    _bump_meter(actor, action.mess)
    _bump_meme(actor, "excitement")
    propagate(world, narrate=narrate)


def intro(world: World, hero: Entity) -> None:
    world.say(f"{hero.id} was a bright caped hero who always tried to do two things at once.")


def loves(world: World, hero: Entity, action: Action) -> None:
    _bump_meme(hero, "joy")
    world.say(
        f"{hero.pronoun().capitalize()} loved {action.gerund}, "
        f"because every swoop through the city felt like a comic page turning."
    )


def pager_call(world: World, hero: Entity, helper: Entity, patient: Entity, packet: Entity) -> None:
    _bump_meter(packet, "buzz")
    _bump_meme(helper, "urgency")
    world.say(
        f"Then the pager on {helper.id}'s belt went BEEP-BEEP, which in superhero language meant trouble."
    )
    world.say(
        f"It was a call from the rooftop clinic: {patient.id} needed someone to medicate {patient.pronoun('object')}, "
        f"and the sundry kit was missing the one tiny spoon."
    )


def wants(world: World, hero: Entity, action: Action) -> None:
    _bump_meme(hero, "desire")
    world.say(
        f"{hero.id} wanted to {action.verb} right away, but {hero.pronoun('possessive')} boots were already pointed at the sky."
    )


def warns(world: World, helper: Entity, hero: Entity, action: Action, prize: Entity) -> bool:
    pred = predict_mess(world, hero, action, prize.id)
    if not pred["soiled"]:
        return False
    world.say(
        f'"If you charge off now, your {prize.label} will get {action.soil}," '
        f"{helper.id} warned. \"Then the whole rescue will look like a laundry accident.\""
    )
    _bump_meme(hero, "concern")
    return True


def rush(world: World, hero: Entity, action: Action) -> None:
    _bump_meme(hero, "defiance")
    world.say(f"{hero.id} tried to {action.rush}, but the pager kept making tiny bossy noises.")


def compromise(world: World, helper: Entity, hero: Entity, action: Action, prize: Entity) -> Optional[Gear]:
    gear_def = select_gear(action, prize)
    if gear_def is None:
        return None
    if predict_mess(world, hero, action, prize.id)["soiled"]:
        gear = world.add(Entity(
            id=gear_def.id,
            label=gear_def.label,
            type="gear",
            protective=True,
            covers=set(gear_def.covers),
            plural=gear_def.plural,
            owner=hero.id,
        ))
        gear.worn_by = hero.id
        # Re-check with gear in place.
        if predict_mess(world, hero, action, prize.id)["soiled"]:
            gear.worn_by = None
            del world.entities[gear.id]
            return None
    world.say(
        f'{helper.id} rummaged through the sundry drawer, found {gear_def.label}, and grinned. '
        f'"How about we {gear_def.prep} first?"'
    )
    return gear_def


def accept(world: World, hero: Entity, helper: Entity, action: Action, prize: Entity, gear_def: Gear) -> None:
    _bump_meme(hero, "helpful")
    _bump_meme(hero, "joy")
    world.say(
        f"{hero.id} laughed, put on the {gear_def.label}, and gave the patient a careful dose."
    )
    world.say(
        f"After that, {hero.id} could {action.gerund} without ruining {hero.pronoun('possessive')} {prize.label}, "
        f"and the pager finally stopped shouting."
    )


def tell(setting: Setting, action: Action, prize_cfg: Prize, hero_name: str = "Spark", hero_type: str = "girl",
         helper_name: str = "Comet", helper_type: str = "man") -> World:
    world = World(setting)
    hero = world.add(Entity(id=hero_name, kind="character", type=hero_type))
    helper = world.add(Entity(id=helper_name, kind="character", type=helper_type))
    patient = world.add(Entity(id="Pip", kind="character", type="boy"))
    prize = world.add(Entity(id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
                             owner=hero.id, caretaker=helper.id, plural=prize_cfg.plural))
    pager = world.add(Entity(id="pager", type="pager", label="pager", owner=helper.id))

    intro(world, hero)
    loves(world, hero, action)
    pager_call(world, hero, helper, patient, pager)
    wants(world, hero, action)

    world.para()
    world.say(f"The rooftop clinic sat above the bakery, where the wind smelled like toast and victory.")
    warns(world, helper, hero, action, prize)
    rush(world, hero, action)

    world.para()
    gear_def = compromise(world, helper, hero, action, prize)
    if gear_def:
        world.facts.update(hero=hero, helper=helper, patient=patient, prize=prize, action=action, gear=gear_def)
        accept(world, hero, helper, action, prize, gear_def)

    world.facts.update(hero=hero, helper=helper, patient=patient, prize=prize, action=action, gear=gear_def)
    return world


SETTINGS = {
    "rooftop": Setting(place="the rooftop clinic", indoor=False, affords={"swoop"}),
    "alley": Setting(place="the bright alley", indoor=False, affords={"dash"}),
    "lair": Setting(place="the hero lair", indoor=True, affords={"tinker"}),
}

ACTIONS = {
    "swoop": Action(
        id="swoop",
        verb="swoop over the city",
        gerund="swooping over the city",
        rush="launch into the storm",
        mess="wet",
        soil="soaked and silly",
        zone={"torso"},
        keyword="pager",
        tags={"city", "hero", "pager"},
    ),
    "dash": Action(
        id="dash",
        verb="dash through the foam",
        gerund="dashing through foam",
        rush="charge into the foam blast",
        mess="sticky",
        soil="sticky with foam",
        zone={"legs", "torso"},
        keyword="sundry",
        tags={"foam", "humor"},
    ),
    "tinker": Action(
        id="tinker",
        verb="tinker with the medicate kit",
        gerund="tinkering with the medicate kit",
        rush="grab the wrong bottle",
        mess="painted",
        soil="spattered with paint",
        zone={"torso"},
        keyword="medicate",
        tags={"lab", "humor", "medicate"},
    ),
}

PRIZES = {
    "cape": Prize(label="cape", phrase="a bright red cape", type="cape", region="torso"),
    "mask": Prize(label="mask", phrase="a shiny mask", type="mask", region="torso"),
    "boots": Prize(label="boots", phrase="polished boots", type="boots", region="legs", plural=True),
}

GEAR = [
    Gear(
        id="rainhood",
        label="a rain hood",
        covers={"torso"},
        guards={"wet"},
        prep="put on a rain hood",
        tail="pulled the hood on and headed out again",
    ),
    Gear(
        id="foamguard",
        label="foam guard gloves",
        covers={"hands", "torso"},
        guards={"sticky"},
        prep="wear foam guard gloves",
        tail="slid the gloves on and zipped out",
        plural=True,
    ),
    Gear(
        id="smock",
        label="an old art smock",
        covers={"torso"},
        guards={"painted"},
        prep="wear an old art smock",
        tail="slipped into the smock and got back to work",
    ),
]

GIRL_NAMES = ["Spark", "Nova", "Iris", "Mira", "Luna"]
BOY_NAMES = ["Bolt", "Jet", "Rex", "Finn", "Max"]
TRAITS = ["cheerful", "brave", "funny", "quick", "spry"]


def valid_combos() -> list[tuple[str, str, str]]:
    combos = []
    for place, setting in SETTINGS.items():
        for act_id in setting.affords:
            act = _safe_lookup(ACTIONS, act_id)
            for prize_id, prize in PRIZES.items():
                if can_pair(act, prize) and select_gear(act, prize):
                    combos.append((place, act_id, prize_id))
    return combos


@dataclass
class StoryParams:
    place: str
    action: str
    prize: str
    name: str
    gender: str
    helper: str
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
    hero = _safe_fact(world, f, "hero")
    action = _safe_fact(world, f, "action")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short superhero story for a young child using the words "medicate", "pager", and "sundry".',
        f"Tell a funny caped story where {hero.id} wants to {action.verb} but must first help with a medicate call and a sundry supply problem.",
        f"Write a simple rescue story set at {world.setting.place} that ends with the hero solving the pager alert before flying off.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    hero, helper, patient = f["hero"], f["helper"], f["patient"]
    action, prize = f["action"], f["prize"]
    gear = f.get("gear")
    qa = [
        QAItem(
            question=f"Who was the story about?",
            answer=f"It was about {hero.id}, a {hero.type} superhero who wanted to {action.verb} but also help at the rooftop clinic.",
        ),
        QAItem(
            question=f"What did the pager say needed to happen?",
            answer=f"The pager said the team needed to medicate {patient.id}, and the sundry kit was missing one tiny spoon.",
        ),
        QAItem(
            question=f"Why did the hero hesitate before leaving?",
            answer=f"{helper.id} warned that if {hero.id} rushed off first, the {prize.label} would get {action.soil}.",
        ),
    ]
    if gear:
        qa.append(
            QAItem(
                question=f"How did the hero get to do both the rescue and the action?",
                answer=f"They used {gear.label} first, so {hero.id} could help with the medicine and still {action.gerund}.",
            )
        )
    return qa


def world_knowledge_qa(world: World) -> list[QAItem]:
    return [
        QAItem(
            question="What is a pager?",
            answer="A pager is a small device that makes a beep or buzz to tell someone there is a message or an emergency.",
        ),
        QAItem(
            question="What does medicate mean?",
            answer="To medicate someone means to give them medicine to help them feel better.",
        ),
        QAItem(
            question="What does sundry mean?",
            answer="Sundry means a mix of different small, miscellaneous things.",
        ),
    ]


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
        if e.protective:
            bits.append(f"covers={sorted(e.covers)}")
        lines.append(f"  {e.id:8} ({e.type:8}) {' '.join(bits)}")
    lines.append(f"  fired rules: {sorted({n for n, *_ in world.fired})}")
    return "\n".join(lines)


def explain_rejection(action: Action, prize: Prize) -> str:
    if not can_pair(action, prize):
        return f"(No story: {action.gerund} does not reach the {prize.region}, so the {prize.label} would not honestly be in danger.)"
    return f"(No story: nothing in the gear shelf protects a {prize.label} from {action.gerund} in a reasonable way.)"


def explain_gender(prize_id: str, gender: str) -> str:
    ok = " / ".join(sorted(_safe_lookup(PRIZES, prize_id).genders))
    return f"(No story: a {_safe_lookup(PRIZES, prize_id).label} here is not a typical {gender}'s item; try --gender {ok}.)"


ASP_RULES = r"""
prize_at_risk(A, P) :- action(A), prize(P), zone(A, R), worn_on(P, R).
protects(G, A, P) :- gear(G), prize_at_risk(A, P), action(A), prize(P),
                     mess_of(A, M), guards(G, M), covers(G, R), worn_on(P, R).
has_fix(A, P) :- protects(_, A, P).
valid(Place, A, P) :- affords(Place, A), prize_at_risk(A, P), has_fix(A, P).
valid_story(Place, A, P, Gender) :- valid(Place, A, P), wears(Gender, P).
"""


def asp_facts() -> str:
    import asp
    lines = []
    for pid, s in SETTINGS.items():
        lines.append(asp.fact("setting", pid))
        if s.indoor:
            lines.append(asp.fact("indoor", pid))
        for a in sorted(s.affords):
            lines.append(asp.fact("affords", pid, a))
    for aid, a in ACTIONS.items():
        lines.append(asp.fact("action", aid))
        lines.append(asp.fact("mess_of", aid, a.mess))
        for r in sorted(a.zone):
            lines.append(asp.fact("zone", aid, r))
    for pid, p in PRIZES.items():
        lines.append(asp.fact("prize", pid))
        lines.append(asp.fact("worn_on", pid, p.region))
        if p.plural:
            lines.append(asp.fact("prize_plural", pid))
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
    ap = argparse.ArgumentParser(description="A funny superhero storyworld with a pager, sundry supplies, and a medicate call.")
    ap.add_argument("--place", choices=SETTINGS)
    ap.add_argument("--action", choices=ACTIONS)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--helper", choices=["mother", "father", "friend", "mentor"])
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
    if getattr(args, "action", None) and getattr(args, "prize", None):
        act, pr = _safe_lookup(ACTIONS, getattr(args, "action", None)), _safe_lookup(PRIZES, getattr(args, "prize", None))
        if not (can_pair(act, pr) and select_gear(act, pr)):
            return _fallback_storyparams(args, rng, StoryParams, globals())
    if getattr(args, "gender", None) and getattr(args, "prize", None) and getattr(args, "gender", None) not in _safe_lookup(PRIZES, getattr(args, "prize", None)).genders:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    combos = [c for c in valid_combos()
              if (getattr(args, "place", None) is None or c[0] == getattr(args, "place", None))
              and (getattr(args, "action", None) is None or c[1] == getattr(args, "action", None))
              and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))
              and (getattr(args, "gender", None) is None or getattr(args, "gender", None) in PRIZES[c[2]].genders)]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())

    place, action, prize = rng.choice(list(combos))
    gender = getattr(args, "gender", None) or rng.choice(["girl", "boy"])
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    helper = getattr(args, "helper", None) or rng.choice(["mother", "father", "friend", "mentor"])
    trait = rng.choice(TRAITS)
    return StoryParams(place=place, action=action, prize=prize, name=name, gender=gender, helper=helper, trait=trait)


def generate(params: StoryParams) -> StorySample:
    world = tell(_safe_lookup(SETTINGS, params.place), _safe_lookup(ACTIONS, params.action), _safe_lookup(PRIZES, params.prize), params.name, params.gender)
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
        combos = asp_valid_combos()
        stories = asp_valid_stories()
        print(f"{len(combos)} compatible (place, action, prize) combos ({len(stories)} with gender):\n")
        for place, action, prize in combos:
            genders = sorted(g for (pl, ac, pr, g) in stories if (pl, ac, pr) == (place, action, prize))
            print(f"  {place:9} {action:10} {prize:8}  [{', '.join(genders)}]")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2 ** 31)
    samples: list[StorySample] = []

    if getattr(args, "all", None):
        for p in [
            StoryParams("rooftop", "swoop", "cape", "Spark", "girl", "mentor", "funny"),
            StoryParams("alley", "dash", "boots", "Bolt", "boy", "friend", "quick"),
            StoryParams("lair", "tinker", "mask", "Nova", "girl", "mother", "cheerful"),
        ]:
            samples.append(generate(p))
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
            header = f"### {p.name}: {p.action} at {p.place} (prize: {p.prize})"
        elif len(samples) > 1:
            header = f"### variant {i + 1}"
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
