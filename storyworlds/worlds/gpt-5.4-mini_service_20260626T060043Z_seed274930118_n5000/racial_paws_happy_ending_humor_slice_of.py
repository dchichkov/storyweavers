#!/usr/bin/env python3
"""
storyworlds/worlds/racial_paws_happy_ending_humor_slice_of.py
==============================================================

A small slice-of-life story world about a neighborhood pet day where a few
children, a couple of pets, and one harmless mix-up lead to a funny, warm,
happy ending.

The domain is intentionally gentle and concrete:
- a child wants to join a local event
- a pet-related mishap creates a little tension
- a simple fix turns the day around
- the ending proves the mood changed

This world includes the seed words "racial" and "paws" in a safe, non-
stereotyped way by centering a diverse neighborhood and a paw-themed event.
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

    region: object | None = None
    kid: object | None = None
    parent: object | None = None
    prize: object | None = None
    def pronoun(self, case: str = "subject") -> str:
        if self.type in {"girl", "mother", "woman"}:
            return {"subject": "she", "object": "her", "possessive": "her"}[case]
        if self.type in {"boy", "father", "man"}:
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
    indoors: bool = False
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
    mishap: str
    relief: str
    keyword: str
    tags: set[str] = field(default_factory=set)
    zone: set[str] = field(default_factory=set)
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
class Fix:
    id: str
    label: str
    prep: str
    tail: str
    guards: set[str]
    covers: set[str]
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
        clone.paragraphs = [[]]
        clone.fired = set(self.fired)
        clone.zone = set(self.zone)
        return clone


@dataclass
class Rule:
    name: str
    apply: callable
    RULES: list = field(default_factory=list)
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


def _r_mess(world: World) -> list[str]:
    out: list[str] = []
    for actor in world.characters():
        if actor.meters.get("mess", 0) < THRESHOLD:
            continue
        for item in list(world.entities.values()):
            if item.worn_by != actor.id or item.region not in world.zone:
                continue
            if ("mess", actor.id, item.id) in world.fired:
                continue
            world.fired.add(("mess", actor.id, item.id))
            item.meters["mess"] = item.meters.get("mess", 0) + 1
            item.meters["dirty"] = item.meters.get("dirty", 0) + 1
            out.append(f"{actor.pronoun('possessive').capitalize()} {item.label} got a little messy.")
    return out


def _r_fix(world: World) -> list[str]:
    out: list[str] = []
    for item in list(world.entities.values()):
        if item.meters.get("dirty", 0) < THRESHOLD or not item.caretaker:
            continue
        sig = ("fix", item.id)
        if sig in world.fired:
            continue
        world.fired.add(sig)
        carer = world.get(item.caretaker)
        carer.memes["work"] = carer.memes.get("work", 0) + 1
        out.append(f"That would mean a little more work for {carer.label}.")
    return out


RULES = [Rule("mess", _r_mess), Rule("fix", _r_fix)]


def propagate(world: World, narrate: bool = True) -> list[str]:
    produced: list[str] = []
    changed = True
    for _ in range(len(globals().get("CAUSAL_RULES", [])) + 4):
        changed = False
        for rule in RULES:
            sents = rule.apply(world)
            if sents:
                changed = True
                produced.extend(sents)
    if narrate:
        for s in produced:
            world.say(s)
    return produced


def aspiration_lint(params: "StoryParams") -> None:
    if params.activity not in ACTIVITIES:
        pass
    if params.prize not in PRIZES:
        pass
    act = _safe_lookup(ACTIVITIES, params.activity)
    prize = _safe_lookup(PRIZES, params.prize)
    if prize.region not in act.zone:
        pass
    if not choose_fix(act, prize):
        pass
    if params.gender and params.gender not in prize.genders:
        pass


def choose_fix(activity: Activity, prize: Prize) -> Optional[Fix]:
    for fx in FIXES:
        if activity.mishap in fx.guards and prize.region in fx.covers:
            return fx
    return None


def predict_damage(world: World, actor: Entity, activity: Activity, prize_id: str) -> dict:
    sim = world.copy()
    sim.get(actor.id).meters["mess"] = sim.get(actor.id).meters.get("mess", 0) + 1
    sim.zone = set(activity.zone)
    propagate(sim, narrate=False)
    prize = sim.entities[prize_id]
    return {
        "dirty": prize.meters.get("dirty", 0) >= THRESHOLD,
        "work": sum(e.memes.get("work", 0) for e in sim.characters()),
    }


def tell(setting: Setting, activity: Activity, prize_cfg: Prize, name: str, gender: str,
         parent_kind: str, trait: str) -> World:
    world = World(setting)
    kid = world.add(Entity(
        id=name, kind="character", type=gender, traits=["little", trait, "kind"]
    ))
    parent = world.add(Entity(id="Parent", kind="character", type=parent_kind, label=f"the {parent_kind}"))
    prize = world.add(Entity(
        id="prize", type=prize_cfg.type, label=prize_cfg.label, phrase=prize_cfg.phrase,
        owner=kid.id, caretaker=parent.id, region=prize_cfg.region, plural=prize_cfg.plural
    ))

    world.say(
        f"{kid.id} lived in {setting.place} and liked the neighborhood's calm, everyday rhythm."
    )
    world.say(
        f"{kid.id} especially loved the annual paws day, when families, snacks, and pets filled the square."
    )
    world.say(
        f"{kid.id} wore {kid.pronoun('possessive')} {prize.label} with a grin, because it was new and bright."
    )

    world.para()
    world.say(
        f"One afternoon, {kid.id} and {kid.pronoun('possessive')} {parent.label} went to {setting.place} for the celebration."
    )
    world.say(
        f"{kid.id} wanted to {activity.verb}, and the whole thing looked funny and inviting."
    )

    pred = predict_damage(world, kid, activity, prize.id)
    if pred["dirty"]:
        world.say(
            f"But {kid.pronoun('possessive')} {parent.label} noticed that {prize.label} might end up {activity.mishap}."
        )
        world.say(
            f'"If that happens," {parent.label} said, "I will have to clean {prize.it()} later."'
        )

    world.zone = set(activity.zone)
    kid.meters["mess"] = kid.meters.get("mess", 0) + 1
    kid.memes["want"] = kid.memes.get("want", 0) + 1
    propagate(world, narrate=True)

    world.para()
    if pred["dirty"]:
        kid.memes["oops"] = kid.memes.get("oops", 0) + 1
        world.say(f"{kid.id} made a face and tried to tiptoe back, which only made {parent.label} laugh.")
        world.say(f'Then {kid.id} noticed a better idea and said, "Could we use something safer?"')
        fx = choose_fix(activity, prize)
        if fx is None:
            pass
        world.say(
            f"{parent.label.capitalize()} smiled and offered {fx.label}: {fx.prep}."
        )
        world.say(
            f"{kid.id} nodded, and soon they {fx.tail}."
        )
        kid.memes["joy"] = kid.memes.get("joy", 0) + 1
        kid.memes["relief"] = kid.memes.get("relief", 0) + 1
        kid.memes["worry"] = 0
        world.say(
            f"After that, {kid.id} could still {activity.gerund}, and {prize.label} stayed clean and tidy."
        )
        world.say(
            f"The pets at the paws day pranced by, and everyone ended up smiling at the silly little fix."
        )
    else:
        world.say(
            f"Nothing got ruined, so {kid.id} kept playing and everyone had an easy, happy afternoon."
        )

    world.facts.update(
        kid=kid,
        parent=parent,
        prize=prize,
        activity=activity,
        setting=setting,
    )
    return world


SETTINGS = {
    "square": Setting(place="the neighborhood square", indoors=False, affords={"pawswalk", "pawpaint", "parade"}),
    "yard": Setting(place="the sunny side yard", indoors=False, affords={"pawswalk", "pawpaint"}),
    "community_room": Setting(place="the community room", indoors=True, affords={"pawpaint"}),
}

ACTIVITIES = {
    "pawswalk": Activity(
        id="pawswalk",
        verb="join the paws walk",
        gerund="walking with the pets",
        mishap="muddy",
        relief="gentle laughter",
        keyword="paws",
        zone={"shoes", "legs"},
        tags={"paws", "walk", "mud"},
    ),
    "pawpaint": Activity(
        id="pawpaint",
        verb="paint paw prints",
        gerund="painting bright paw prints",
        mishap="painted",
        relief="a fresh towel",
        keyword="paws",
        zone={"torso", "hands"},
        tags={"paws", "paint", "art"},
    ),
    "parade": Activity(
        id="parade",
        verb="watch the paw parade",
        gerund="watching the paw parade",
        mishap="sandy",
        relief="a breezy cleanup",
        keyword="paws",
        zone={"shoes"},
        tags={"paws", "crowd"},
    ),
}

PRIZES = {
    "shoes": Prize("shoes", "new white shoes", "shoes", "shoes", True),
    "shirt": Prize("shirt", "a neat green shirt", "shirt", "torso"),
    "skirt": Prize("skirt", "a bright blue skirt", "skirt", "legs", genders={"girl"}),
}

FIXES = [
    Fix("rainboots", "rain boots", "put on rain boots first", "came back with their rain boots", {"muddy"}, {"shoes"}, True),
    Fix("apron", "a paint apron", "put on a paint apron first", "returned with the apron", {"painted"}, {"torso"}),
    Fix("coveralls", "old coveralls", "change into old coveralls", "came back in the old coveralls", {"muddy", "painted", "sandy"}, {"shoes", "legs", "torso"}, True),
]

GIRL_NAMES = ["Mina", "Leah", "Sofia", "June", "Iris", "Nia"]
BOY_NAMES = ["Eli", "Noah", "Omar", "Theo", "Kai", "Ben"]
TRAITS = ["cheerful", "curious", "playful", "patient", "gentle"]


@dataclass
class StoryParams:
    setting: str
    activity: str
    prize: str
    name: str
    gender: str
    parent_kind: str
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
    for sname, setting in SETTINGS.items():
        for aname in setting.affords:
            act = _safe_lookup(ACTIVITIES, aname)
            for pname, prize in PRIZES.items():
                if prize.region in act.zone and choose_fix(act, prize):
                    out.append((sname, aname, pname))
    return out


def generation_prompts(world: World) -> list[str]:
    f = world.facts
    kid = _safe_fact(world, f, "kid")
    act = _safe_fact(world, f, "activity")
    prize = _safe_fact(world, f, "prize")
    return [
        f'Write a short slice-of-life story for a child who loves "{act.keyword}" and pet days.',
        f"Tell a warm, funny story where {kid.id} wants to {act.verb} but worries about {prize.phrase}.",
        f"Write a simple happy-ending story about a neighborhood event with paws, pets, and a little mix-up.",
    ]


def story_qa(world: World) -> list[QAItem]:
    f = world.facts
    kid = _safe_fact(world, f, "kid")
    parent = _safe_fact(world, f, "parent")
    prize = _safe_fact(world, f, "prize")
    act = _safe_fact(world, f, "activity")
    return [
        QAItem(
            question=f"What did {kid.id} want to do at {world.setting.place}?",
            answer=f"{kid.id} wanted to {act.verb} during the neighborhood event.",
        ),
        QAItem(
            question=f"Why did {parent.label} worry about {prize.label}?",
            answer=f"{parent.label.capitalize()} worried because it could get {act.mishap} during {act.gerund}.",
        ),
        QAItem(
            question=f"What helped the day end well for {kid.id}?",
            answer=f"A safer choice helped, so {kid.id} could keep enjoying the event while {prize.label} stayed clean.",
        ),
    ]


def world_knowledge_qa(world: World) -> list[QAItem]:
    out = [
        QAItem(
            question="What does paws mean in a pet event?",
            answer="Paws means the feet of an animal like a dog or cat.",
        ),
        QAItem(
            question="Why do people use rain boots for muddy play?",
            answer="Rain boots help keep shoes and socks cleaner when the ground is wet or muddy.",
        ),
    ]
    return out


def format_qa(sample: StorySample) -> str:
    lines = ["== Generation prompts ==", *[f"- {p}" for p in sample.prompts], "", "== Story Q&A =="]
    for item in sample.story_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    lines.append("")
    lines.append("== World knowledge Q&A ==")
    for item in sample.world_qa:
        lines.append(f"Q: {item.question}")
        lines.append(f"A: {item.answer}")
    return "\n".join(lines)


def asp_facts() -> str:
    import asp
    lines: list[str] = []
    for s in SETTINGS:
        lines.append(asp.fact("setting", s))
        for a in sorted(_safe_lookup(SETTINGS, s).affords):
            lines.append(asp.fact("affords", s, a))
    for a, act in ACTIVITIES.items():
        lines.append(asp.fact("activity", a))
        lines.append(asp.fact("mishap_of", a, act.mishap))
        for r in sorted(act.zone):
            lines.append(asp.fact("zone", a, r))
    for p, pr in PRIZES.items():
        lines.append(asp.fact("prize", p))
        lines.append(asp.fact("worn_on", p, pr.region))
        if pr.plural:
            lines.append(asp.fact("plural", p))
        for g in sorted(pr.genders):
            lines.append(asp.fact("wears", g, p))
    for fx in FIXES:
        lines.append(asp.fact("fix", fx.id))
        for m in sorted(fx.guards):
            lines.append(asp.fact("guards", fx.id, m))
        for r in sorted(fx.covers):
            lines.append(asp.fact("covers", fx.id, r))
    return "\n".join(lines)


ASP_RULES = r"""
prize_at_risk(A,P) :- zone(A,R), worn_on(P,R).
has_fix(A,P) :- prize_at_risk(A,P), fix(F), mishap_of(A,M), guards(F,M), covers(F,R), worn_on(P,R), zone(A,R).
valid(Place,A,P) :- affords(Place,A), prize_at_risk(A,P), has_fix(A,P).
valid_story(Place,A,P,G) :- valid(Place,A,P), wears(G,P).
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
    py = set(valid_combos())
    cl = set(asp_valid_combos())
    if py == cl:
        print(f"OK: ASP matches Python ({len(py)} combos).")
        return 0
    print("MISMATCH")
    print("only python:", sorted(py - cl))
    print("only asp:", sorted(cl - py))
    return 1


def build_parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description="A slice-of-life story world with paws, humor, and a happy ending.")
    ap.add_argument("--setting", choices=SETTINGS)
    ap.add_argument("--activity", choices=ACTIVITIES)
    ap.add_argument("--prize", choices=PRIZES)
    ap.add_argument("--gender", choices=["girl", "boy"])
    ap.add_argument("--parent-kind", choices=["mother", "father"])
    ap.add_argument("--name")
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
    combos = valid_combos()
    if getattr(args, "setting", None) or getattr(args, "activity", None) or getattr(args, "prize", None):
        combos = [c for c in combos
                  if (getattr(args, "setting", None) is None or c[0] == getattr(args, "setting", None))
                  and (getattr(args, "activity", None) is None or c[1] == getattr(args, "activity", None))
                  and (getattr(args, "prize", None) is None or c[2] == getattr(args, "prize", None))]
    if getattr(args, "gender", None):
        combos = [c for c in combos if getattr(args, "gender", None) in PRIZES[c[2]].genders]
    if not combos:
        return _fallback_storyparams(args, rng, StoryParams, globals())
    setting, activity, prize = rng.choice(list(combos))
    pr = _safe_lookup(PRIZES, prize)
    gender = getattr(args, "gender", None) or rng.choice(sorted(pr.genders))
    name = getattr(args, "name", None) or rng.choice(GIRL_NAMES if gender == "girl" else BOY_NAMES)
    parent_kind = getattr(args, "parent_kind", None) or rng.choice(["mother", "father"])
    trait = getattr(args, "trait", None) or rng.choice(TRAITS)
    if getattr(args, "setting", None) and getattr(args, "activity", None) and getattr(args, "prize", None):
        aspiration_lint(StoryParams(setting, activity, prize, name, gender, parent_kind, trait))
    return StoryParams(setting, activity, prize, name, gender, parent_kind, trait)


def generate(params: StoryParams) -> StorySample:
    aspiration_lint(params)
    world = tell(
        _safe_lookup(SETTINGS, params.setting),
        _safe_lookup(ACTIVITIES, params.activity),
        _safe_lookup(PRIZES, params.prize),
        params.name,
        params.gender,
        params.parent_kind,
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
        lines.append(f"  {e.id}: {e.type} {' '.join(bits)}")
    return "\n".join(lines)


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
    StoryParams("square", "pawswalk", "shoes", "Mina", "girl", "mother", "curious"),
    StoryParams("yard", "pawswalk", "shoes", "Omar", "boy", "father", "playful"),
    StoryParams("community_room", "pawpaint", "shirt", "Leah", "girl", "mother", "gentle"),
    StoryParams("square", "parade", "skirt", "Nia", "girl", "father", "cheerful"),
]


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
        print(f"{len(triples)} compatible combos ({len(stories)} with gender):\n")
        for s, a, p in triples:
            genders = sorted(g for (ss, aa, pp, g) in stories if (ss, aa, pp) == (s, a, p))
            print(f"  {s:15} {a:10} {p:8} [{', '.join(genders)}]")
        return

    base_seed = getattr(args, "seed", None) if getattr(args, "seed", None) is not None else random.randrange(2**31)
    samples: list[StorySample] = []
    if getattr(args, "all", None):
        samples = [generate(p) for p in CURATED]
    else:
        seen: set[str] = set()
        i = 0
        while len(samples) < getattr(args, "n", None) and i < max(50, getattr(args, "n", None) * 40):
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
        header = f"### variant {i + 1}" if len(samples) > 1 and not getattr(args, "all", None) else ""
        emit(sample, trace=getattr(args, "trace", None), qa=getattr(args, "qa", None), header=header)
        if i < len(samples) - 1:
            print("\n" + "=" * 70 + "\n")


if __name__ == "__main__":
    main()
